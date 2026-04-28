#!/usr/bin/env python3
"""
update_models.py — LiteLLM multi-provider model maintenance script.

Tests all chat-capable models across configured providers and optionally
updates the model_list in ~/litellm/config.yaml with only verified working
models. Uses a persistent failure cache to skip known-bad models on
subsequent runs, making routine executions fast (seconds, not minutes).

Providers supported:
  - Local vLLM (DGX Spark)
  - Groq
  - NVIDIA NIM (build.nvidia.com)
  - OpenRouter (free tier only)

Files written to ~/litellm/:
  config.yaml          — updated in-place (atomic rename, backup first)
  model_cache.json     — persistent failure cache
  update_models.log    — appended when run with --update or --fallback
  backups/             — timestamped config backups before every write

Usage:
  python3 ~/litellm/update_models.py                    # dry-run: test and report
  python3 ~/litellm/update_models.py --show             # print generated model_list block
  python3 ~/litellm/update_models.py --update           # update model_list + fallbacks, prompt
  python3 ~/litellm/update_models.py --update --yes     # apply without prompt (cron)
  python3 ~/litellm/update_models.py --fallback         # validate/prune fallbacks only, prompt
  python3 ~/litellm/update_models.py --fallback --yes   # prune fallbacks without prompt
  python3 ~/litellm/update_models.py --providers nvidia # test one provider only
  python3 ~/litellm/update_models.py --retest-failed    # ignore cache, retest all
  python3 ~/litellm/update_models.py --show-cache       # print failure cache contents
  python3 ~/litellm/update_models.py --clear-cache nvidia  # clear cache for one provider
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path


# ── Paths ─────────────────────────────────────────────────────────────────────

LITELLM_DIR  = Path.home() / 'litellm'
CONFIG_FILE  = LITELLM_DIR / 'config.yaml'
ENV_FILE     = LITELLM_DIR / '.env'
BACKUP_DIR   = LITELLM_DIR / 'backups'
LOG_FILE     = LITELLM_DIR / 'update_models.log'
CACHE_FILE   = LITELLM_DIR / 'model_cache.json'

CACHE_SCHEMA_VERSION = 1


# ── Provider configuration ────────────────────────────────────────────────────

NVIDIA_EXCLUDE = [
    'embed', 'rerank', 'whisper', 'riva', 'vision', 'vlm', 'ocr',
    'grounding', 'segmentation', 'classification', 'guardrail',
    'reward', 'bionemo', 'fourcastnet', 'proteina', 'neva', 'vila',
    'deplot', 'fuyu', 'kosmos', 'nvclip', 'parse', 'detector',
    'chatqa', 'starcoder', 'recurrentgemma', 'ising', 'safety',
    'guard', 'lora', 'retriev',
]

OPENROUTER_EXCLUDE = [
    'lyria', 'ocr', 'clip', 'vl-',
]

GROQ_EXCLUDE = [
    'whisper', 'guard', 'tts', 'speech', 'allam', 'orpheus', 'prompt-guard',
]

PROVIDER_RPM = {
    'groq':       28,
    'nvidia':     40,
    'openrouter': 18,
    'vllm':       None,
}

# Known Groq per-model rate limits (rpm, tpm). Falls back to PROVIDER_RPM.
GROQ_LIMITS = {
    'llama-3.3-70b-versatile':                   (28, 11000),
    'llama-3.1-8b-instant':                      (28,  5500),
    'meta-llama/llama-4-scout-17b-16e-instruct': (28, 28000),
    'qwen/qwen3-32b':                            (58,  5500),
}

DEFAULT_CTX = {
    'groq':       128000,
    'nvidia':     32768,
    'openrouter': 131072,
}

# Probe concurrency per provider (keep NVIDIA low — strict 40 RPM)
PROVIDER_CONCURRENCY = {
    'groq':       4,
    'nvidia':     3,
    'openrouter': 4,
    'vllm':       2,
}

# HTTP codes that indicate permanent failure — worth caching.
# 429, 5xx are transient and NOT cached.
PERMANENT_FAILURE_CODES = {403, 404, 422}

# Substrings in error bodies that indicate permanent account restrictions.
PERMANENT_FAILURE_STRINGS = [
    'not found for account',
    'not found',
    'model not found',
    'does not exist',
    'no longer available',
    'deprecated',
]


# ── Logging ───────────────────────────────────────────────────────────────────

_log_fh = None

def log(msg: str, to_file: bool = False) -> None:
    print(msg)
    if to_file and _log_fh:
        _log_fh.write(msg + '\n')
        _log_fh.flush()

def open_log() -> None:
    global _log_fh
    LITELLM_DIR.mkdir(parents=True, exist_ok=True)
    _log_fh = open(LOG_FILE, 'a')
    _log_fh.write(f'\n{"="*65}\n')
    _log_fh.write(f'update_models.py  {datetime.now().isoformat()}\n')
    _log_fh.write(f'{"="*65}\n')

def close_log() -> None:
    if _log_fh:
        _log_fh.close()


# ── .env loader ───────────────────────────────────────────────────────────────

def load_env(path: Path) -> dict:
    env = {}
    if not path.exists():
        return env
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, _, value = line.partition('=')
        env[key.strip()] = value.strip().strip('"').strip("'")
    return env

def get_key(name: str, env: dict) -> str | None:
    return os.environ.get(name) or env.get(name)


# ── Failure cache ─────────────────────────────────────────────────────────────

def load_cache() -> dict:
    """Load persistent failure cache. Returns empty structure if missing or corrupt."""
    empty = {
        'schema_version': CACHE_SCHEMA_VERSION,
        'failed': {p: {} for p in ['groq', 'nvidia', 'openrouter', 'vllm']},
    }
    if not CACHE_FILE.exists():
        return empty
    try:
        data = json.loads(CACHE_FILE.read_text())
        if data.get('schema_version') != CACHE_SCHEMA_VERSION:
            return empty
        for p in ['groq', 'nvidia', 'openrouter', 'vllm']:
            data['failed'].setdefault(p, {})
        return data
    except Exception:
        return empty

def save_cache(cache: dict) -> None:
    LITELLM_DIR.mkdir(parents=True, exist_ok=True)
    tmp = CACHE_FILE.with_suffix('.json.tmp')
    try:
        tmp.write_text(json.dumps(cache, indent=2))
        tmp.rename(CACHE_FILE)
    except Exception as e:
        tmp.unlink(missing_ok=True)
        print(f"WARNING: Could not save cache: {e}")

def is_permanent_failure(http_code: int, reason: str) -> bool:
    """Return True if this failure should be permanently cached."""
    if http_code in PERMANENT_FAILURE_CODES:
        return True
    reason_lower = reason.lower()
    return any(s in reason_lower for s in PERMANENT_FAILURE_STRINGS)

def cache_failure(cache: dict, provider: str, model_id: str,
                  http_code: int, reason: str) -> None:
    now      = datetime.now().isoformat(timespec='seconds')
    existing = cache['failed'][provider].get(model_id)
    if existing:
        existing['last_seen']  = now
        existing['http_code']  = http_code
        existing['reason']     = reason[:120]
        existing['skip_count'] = existing.get('skip_count', 0) + 1
    else:
        cache['failed'][provider][model_id] = {
            'reason':     reason[:120],
            'http_code':  http_code,
            'first_seen': now,
            'last_seen':  now,
            'skip_count': 0,
        }

def is_cached_failure(cache: dict, provider: str, model_id: str) -> bool:
    return model_id in cache['failed'].get(provider, {})

def print_cache(cache: dict) -> None:
    print("\n── Failure cache ────────────────────────────────────────────")
    total = 0
    for provider, entries in sorted(cache['failed'].items()):
        if not entries:
            continue
        print(f"\n  {provider} ({len(entries)} cached failures):")
        for mid, info in sorted(entries.items()):
            print(f"    {mid}")
            print(f"      HTTP {info['http_code']}  {info['reason'][:70]}")
            print(f"      first: {info['first_seen']}  "
                  f"last: {info['last_seen']}  "
                  f"skipped: {info.get('skip_count', 0)}×")
        total += len(entries)
    if total == 0:
        print("  (empty)")
    print(f"\n  Total: {total} cached failures across all providers")


# ── HTTP helpers ──────────────────────────────────────────────────────────────

# Cloudflare (used by Groq and others) blocks Python's default urllib User-Agent.
# Set a neutral but non-bot-flagged string on every outbound request.
_BASE_HEADERS = {'User-Agent': 'litellm-update-models/2.0'}

def http_get(url: str, headers: dict, timeout: int = 15) -> dict:
    req = urllib.request.Request(url, headers={**_BASE_HEADERS, **headers})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())

def http_post(url: str, headers: dict, body: dict, timeout: int = 20) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode(),
        headers={**_BASE_HEADERS, **headers, 'Content-Type': 'application/json'},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())

def probe_model(url: str, headers: dict,
                model_id: str) -> tuple[bool, int, str]:
    """
    Send a minimal chat completion request.
    Returns (success, http_code, detail).
    http_code is 0 on non-HTTP errors (network, timeout).
    """
    try:
        d = http_post(url, headers, {
            'model':    model_id,
            'messages': [{'role': 'user', 'content': 'hi'}],
            'max_tokens': 5,
        })
        choices = d.get('choices') or []
        if choices:
            msg  = choices[0].get('message', {})
            text = (msg.get('content')
                    or msg.get('reasoning_content')
                    or '(thinking/empty)')
        else:
            text = '(no choices in response)'
        return True, 200, text[:60]
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try:
            detail = json.loads(body)
            reason = (detail.get('detail')
                      or detail.get('title')
                      or (detail.get('error') or {}).get('message')
                      or str(detail))
        except Exception:
            reason = body
        return False, e.code, reason[:120]
    except urllib.error.URLError as e:
        return False, 0, f'URLError: {e.reason}'[:120]
    except Exception as e:
        return False, 0, str(e)[:120]


def probe_batch(
    url: str,
    headers: dict,
    model_ids: list[str],
    cache: dict,
    provider: str,
    log_to_file: bool,
    concurrency: int,
    inter_batch_delay: float = 0.3,
) -> tuple[list[str], list[tuple[str, int, str]]]:
    """
    Probe a list of model IDs concurrently, skipping cached failures.

    Returns:
        working    — model IDs that responded successfully
        perm_fails — (model_id, http_code, reason) for permanent failures to cache
    """
    to_test = []
    skipped = 0
    for mid in model_ids:
        if is_cached_failure(cache, provider, mid):
            skipped += 1
        else:
            to_test.append(mid)

    if skipped:
        log(f"  Skipping {skipped} cached failure(s)  "
            f"(--retest-failed to override)", log_to_file)
    log(f"  Testing {len(to_test)} model(s)  (concurrency={concurrency})",
        log_to_file)

    results: dict[str, tuple[bool, int, str]] = {}

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = {
            pool.submit(probe_model, url, headers, mid): mid
            for mid in to_test
        }
        completed = 0
        for future in as_completed(futures):
            mid = futures[future]
            try:
                results[mid] = future.result()
            except Exception as e:
                results[mid] = (False, 0, str(e)[:120])
            completed += 1
            # Brief pause every batch to stay under RPM limits
            if completed % concurrency == 0:
                time.sleep(inter_batch_delay)

    working    = []
    perm_fails = []

    for mid in to_test:
        ok, code, detail = results.get(mid, (False, 0, 'no result'))
        if ok:
            log(f"  ✓  {mid}", log_to_file)
            working.append(mid)
        else:
            log(f"  ✗  {mid:<55}  HTTP {code}  {detail}", log_to_file)
            if is_permanent_failure(code, detail):
                perm_fails.append((mid, code, detail))
            else:
                log(f"       (transient — not cached)", log_to_file)

    return working, perm_fails


# ── YAML helpers ──────────────────────────────────────────────────────────────

def parse_yaml_model_list(text: str) -> list[str]:
    names = []
    for line in text.splitlines():
        m = re.match(r'\s+model_name:\s+"?([^"#\n]+)"?\s*$', line)
        if m:
            names.append(m.group(1).strip())
    return names

def split_config(text: str) -> tuple[str, str, str]:
    lines = text.splitlines(keepends=True)
    start = end = None
    for i, line in enumerate(lines):
        if re.match(r'^model_list\s*:', line):
            start = i
        elif start is not None and end is None:
            if re.match(r'^[a-zA-Z]', line) and not line.startswith(' '):
                end = i
                break
    if start is None:
        raise ValueError("Could not find 'model_list:' in config.yaml")
    if end is None:
        end = len(lines)
    before = ''.join(lines[:start])
    middle = ''.join(lines[start:end])
    after  = ''.join(lines[end:])
    return before, middle, after

def validate_yaml(text: str) -> bool:
    try:
        import yaml
        yaml.safe_load(text)
        return True
    except ImportError:
        pass
    except Exception as e:
        log(f"  YAML parse error: {e}")
        return False
    depth = 0
    for line in text.splitlines():
        depth += line.count('{') - line.count('}')
    return depth == 0

def show_diff(old_names: list[str], new_names: list[str],
              log_to_file: bool) -> None:
    old_set = set(old_names)
    new_set = set(new_names)
    added   = sorted(new_set - old_set)
    removed = sorted(old_set - new_set)
    kept    = sorted(old_set & new_set)
    preview = ', '.join(kept[:4]) + ('...' if len(kept) > 4 else '')
    log(f"  Kept    ({len(kept):>3}):  {preview}", log_to_file)
    if added:
        log(f"  Added   ({len(added):>3}):", log_to_file)
        for m in added:
            log(f"    + {m}", log_to_file)
    if removed:
        log(f"  Removed ({len(removed):>3}):", log_to_file)
        for m in removed:
            log(f"    - {m}", log_to_file)
    if not added and not removed:
        log("  No changes to model list.", log_to_file)


# ── Model entry builders ──────────────────────────────────────────────────────

def groq_entry(model_id: str, rpm: int, tpm: int | None, ctx: int) -> str:
    rpm_line = f'      rpm: {rpm}\n' if rpm else ''
    tpm_line = f'      tpm: {tpm}\n' if tpm else ''
    name     = f'groq/{model_id.split("/")[-1]}'
    return (
        f'  - model_name: "{name}"\n'
        f'    litellm_params:\n'
        f'      model: "groq/{model_id}"\n'
        f'      api_key: "os.environ/GROQ_API_KEY"\n'
        f'{rpm_line}'
        f'{tpm_line}'
        f'    model_info:\n'
        f'      description: "ctx={ctx}"\n'
    )

def nvidia_entry(model_id: str, rpm: int) -> str:
    short = model_id.split('/')[-1]
    name  = f'nvidia/{short}'
    return (
        f'  - model_name: "{name}"\n'
        f'    litellm_params:\n'
        f'      model: "nvidia_nim/{model_id}"\n'
        f'      api_key: "os.environ/NVIDIA_NIM_API_KEY"\n'
        f'      rpm: {rpm}\n'
        f'    model_info:\n'
        f'      description: "{short}"\n'
    )

def openrouter_entry(model_id: str, rpm: int, ctx: int) -> str:
    short = model_id.replace(':free', '').split('/')[-1]
    name  = f'openrouter/{short}'
    return (
        f'  - model_name: "{name}"\n'
        f'    litellm_params:\n'
        f'      model: "openrouter/{model_id}"\n'
        f'      api_key: "os.environ/OPENROUTER_API_KEY"\n'
        f'      rpm: {rpm}\n'
        f'    model_info:\n'
        f'      description: "ctx={ctx}"\n'
    )

def vllm_entry(model_id: str, api_base: str) -> str:
    return (
        f'  - model_name: "local/qwen"\n'
        f'    litellm_params:\n'
        f'      model: "hosted_vllm/{model_id}"\n'
        f'      api_base: "{api_base}"\n'
        f'      api_key: "none"\n'
        f'    model_info:\n'
        f'      description: "Local vLLM on DGX Spark — primary, unlimited"\n'
    )

def build_model_list_block(entries: list[str]) -> str:
    parts = ['model_list:\n\n']
    for entry in entries:
        parts.append(entry)
        parts.append('\n')
    return ''.join(parts)


# ── Provider probes ───────────────────────────────────────────────────────────

def probe_vllm(api_base: str, cache: dict,
               log_to_file: bool) -> tuple[list[str], dict]:
    log("\n── Local vLLM ───────────────────────────────────────────────",
        log_to_file)
    entries = []
    try:
        data      = http_get(f'{api_base}/models', headers={})
        model_ids = [m['id'] for m in data.get('data', [])]
        if not model_ids:
            log("  No models returned.", log_to_file)
            return entries, cache
        working, perm_fails = probe_batch(
            f'{api_base}/chat/completions', {},
            model_ids, cache, 'vllm', log_to_file,
            concurrency=PROVIDER_CONCURRENCY['vllm'],
        )
        for mid, code, reason in perm_fails:
            cache_failure(cache, 'vllm', mid, code, reason)
        for mid in working:
            entries.append(vllm_entry(mid, api_base))
        log(f"  → {len(working)} working", log_to_file)
    except Exception as e:
        log(f"  ERROR: {e}", log_to_file)
    return entries, cache


def probe_groq(api_key: str, cache: dict,
               log_to_file: bool) -> tuple[list[str], dict]:
    log("\n── Groq ─────────────────────────────────────────────────────",
        log_to_file)
    entries = []
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type':  'application/json',   # required — 403 without it
    }
    try:
        data   = http_get('https://api.groq.com/openai/v1/models', headers)
        models = sorted(data.get('data', []), key=lambda x: x['id'])
    except Exception as e:
        log(f"  ERROR fetching models: {e}", log_to_file)
        return entries, cache

    candidates = [m for m in models
                  if not any(x in m['id'].lower() for x in GROQ_EXCLUDE)]
    ctx_map    = {m['id']: m.get('context_window', DEFAULT_CTX['groq'])
                  for m in candidates}
    model_ids  = [m['id'] for m in candidates]
    log(f"  Found {len(model_ids)} candidate models", log_to_file)

    working, perm_fails = probe_batch(
        'https://api.groq.com/openai/v1/chat/completions',
        headers, model_ids, cache, 'groq', log_to_file,
        concurrency=PROVIDER_CONCURRENCY['groq'],
        inter_batch_delay=0.4,
    )
    for mid, code, reason in perm_fails:
        cache_failure(cache, 'groq', mid, code, reason)
    for mid in working:
        rpm, tpm = GROQ_LIMITS.get(mid, (PROVIDER_RPM['groq'], None))
        entries.append(groq_entry(
            mid, rpm, tpm, ctx_map.get(mid, DEFAULT_CTX['groq'])
        ))
    log(f"  → {len(working)} working", log_to_file)
    return entries, cache


def probe_nvidia(api_key: str, cache: dict,
                 log_to_file: bool) -> tuple[list[str], dict]:
    log("\n── NVIDIA NIM ───────────────────────────────────────────────",
        log_to_file)
    entries = []
    headers = {'Authorization': f'Bearer {api_key}'}
    try:
        data   = http_get('https://integrate.api.nvidia.com/v1/models', headers)
        models = data.get('data', [])
    except Exception as e:
        log(f"  ERROR fetching models: {e}", log_to_file)
        return entries, cache

    seen = set()
    candidates = []
    for m in sorted(models, key=lambda x: x['id']):
        mid = m['id']
        if mid not in seen and not any(x in mid.lower() for x in NVIDIA_EXCLUDE):
            seen.add(mid)
            candidates.append(mid)
    log(f"  Found {len(candidates)} candidate models", log_to_file)

    working, perm_fails = probe_batch(
        'https://integrate.api.nvidia.com/v1/chat/completions',
        headers, candidates, cache, 'nvidia', log_to_file,
        concurrency=PROVIDER_CONCURRENCY['nvidia'],
        inter_batch_delay=0.5,
    )
    for mid, code, reason in perm_fails:
        cache_failure(cache, 'nvidia', mid, code, reason)
    for mid in working:
        entries.append(nvidia_entry(mid, PROVIDER_RPM['nvidia']))
    log(f"  → {len(working)} working", log_to_file)
    return entries, cache


def probe_openrouter(api_key: str, cache: dict,
                     log_to_file: bool) -> tuple[list[str], dict]:
    log("\n── OpenRouter ───────────────────────────────────────────────",
        log_to_file)
    entries = []
    headers = {'Authorization': f'Bearer {api_key}'}
    try:
        data   = http_get('https://openrouter.ai/api/v1/models', headers)
        models = data.get('data', [])
    except Exception as e:
        log(f"  ERROR fetching models: {e}", log_to_file)
        return entries, cache

    free = sorted([
        m for m in models
        if m.get('pricing', {}).get('prompt') == '0'
        and m.get('pricing', {}).get('completion') == '0'
        and not any(x in m['id'].lower() for x in OPENROUTER_EXCLUDE)
    ], key=lambda x: x['id'])

    ctx_map   = {m['id']: m.get('context_length', DEFAULT_CTX['openrouter'])
                 for m in free}
    model_ids = [m['id'] for m in free]
    log(f"  Found {len(model_ids)} genuinely free chat models", log_to_file)

    working, perm_fails = probe_batch(
        'https://openrouter.ai/api/v1/chat/completions',
        headers, model_ids, cache, 'openrouter', log_to_file,
        concurrency=PROVIDER_CONCURRENCY['openrouter'],
        inter_batch_delay=0.4,
    )
    for mid, code, reason in perm_fails:
        cache_failure(cache, 'openrouter', mid, code, reason)
    for mid in working:
        entries.append(openrouter_entry(
            mid, PROVIDER_RPM['openrouter'],
            ctx_map.get(mid, DEFAULT_CTX['openrouter'])
        ))
    log(f"  → {len(working)} working", log_to_file)
    return entries, cache


# ── Fallback management ───────────────────────────────────────────────────────

def parse_fallbacks(config_text: str) -> list[tuple[str, list[str]]]:
    """
    Extract fallback chains from the router_settings.fallbacks block.
    Returns a list of (source_model, [fallback_model, ...]) tuples
    in the order they appear in the config.

    Handles the LiteLLM format:
      fallbacks:
        - {"model_a": ["model_b", "model_c"]}
        - {"model_d": ["model_e"]}
    """
    chains = []
    in_fallbacks = False
    for line in config_text.splitlines():
        stripped = line.strip()
        if re.match(r'fallbacks\s*:', stripped):
            in_fallbacks = True
            continue
        if in_fallbacks:
            # End of fallbacks block: next same-or-lower-indented key
            if stripped and not stripped.startswith('-') and not stripped.startswith('{') \
                    and not stripped.startswith('"') and not stripped.startswith('#') \
                    and re.match(r'^[a-zA-Z]', stripped):
                break
            # Match: - {"source": ["fb1", "fb2", ...]}
            m = re.search(
                r'\{["\']([^"\']+)["\']\s*:\s*\[([^\]]*)\]', stripped
            )
            if m:
                source = m.group(1).strip()
                raw    = m.group(2)
                targets = [
                    t.strip().strip('"').strip("'")
                    for t in raw.split(',')
                    if t.strip().strip('"').strip("'")
                ]
                chains.append((source, targets))
    return chains

def validate_fallbacks(
    chains: list[tuple[str, list[str]]],
    working_names: set[str],
    log_to_file: bool,
) -> tuple[list[tuple[str, str]], list[str]]:
    """
    Cross-reference every model ID in fallback chains against working_names.

    Returns:
        stale   — list of (source, stale_target) pairs
        unlinked — working models not referenced in any fallback chain
    """
    log("\n── Fallback validation ──────────────────────────────────────",
        log_to_file)

    all_referenced: set[str] = set()
    stale: list[tuple[str, str]] = []

    for source, targets in chains:
        all_referenced.add(source)
        for target in targets:
            all_referenced.add(target)
            source_ok = source in working_names
            target_ok = target in working_names
            src_tag   = '' if source_ok else ' [STALE]'
            tgt_tag   = '' if target_ok else ' [STALE]'
            status    = '✓' if (source_ok and target_ok) else '✗'
            log(f"  {status}  {source}{src_tag} → {target}{tgt_tag}",
                log_to_file)
            if not target_ok:
                stale.append((source, target))
        if not source_ok:
            stale.append((source, ''))   # source itself is stale

    # Deduplicate stale sources
    stale = list({(s, t) for s, t in stale})

    # Models in working set not in any fallback chain
    unlinked = sorted(working_names - all_referenced)

    if not stale:
        log("  All fallback references are valid.", log_to_file)
    else:
        stale_targets = sorted({t for _, t in stale if t})
        log(f"\n  {len(stale_targets)} stale model reference(s) found:",
            log_to_file)
        for ref in stale_targets:
            log(f"    - {ref}", log_to_file)

    if unlinked:
        log(f"\n  {len(unlinked)} working model(s) not in any fallback chain:",
            log_to_file)
        for m in unlinked:
            log(f"    + {m}", log_to_file)
        log("  Consider adding these to your fallbacks block manually.",
            log_to_file)

    return stale, unlinked

def prune_fallbacks(config_text: str,
                    stale: list[tuple[str, str]],
                    log_to_file: bool) -> str:
    """
    Remove stale model references from the fallbacks block.

    Strategy:
    - If a fallback target is stale, remove it from the list for that chain.
    - If removing the target leaves an empty list [], remove the whole chain line.
    - If a source model is stale (no longer working), remove the whole chain line.
    - All other lines are preserved exactly, including comments and formatting.

    Returns the modified config text.
    """
    stale_targets = {t for _, t in stale if t}
    stale_sources = {s for s, t in stale if not t}

    lines     = config_text.splitlines(keepends=True)
    out_lines = []
    in_fallbacks = False

    for line in lines:
        stripped = line.strip()

        if re.match(r'fallbacks\s*:', stripped):
            in_fallbacks = True
            out_lines.append(line)
            continue

        if in_fallbacks:
            if stripped and not stripped.startswith('-') \
                    and not stripped.startswith('{') \
                    and not stripped.startswith('"') \
                    and not stripped.startswith('#') \
                    and re.match(r'^[a-zA-Z]', stripped):
                in_fallbacks = False
                out_lines.append(line)
                continue

            m = re.search(
                r'(\{["\']([^"\']+)["\']\s*:\s*\[)([^\]]*)(\].*)', stripped
            )
            if m:
                source = m.group(2).strip()
                if source in stale_sources:
                    log(f"  Removed chain: {source} (source no longer working)",
                        log_to_file)
                    continue   # drop the whole line

                raw_targets = m.group(3)
                targets = [
                    t.strip() for t in raw_targets.split(',')
                    if t.strip().strip('"').strip("'")
                ]
                kept = [
                    t for t in targets
                    if t.strip('"').strip("'") not in stale_targets
                ]
                removed = [
                    t.strip('"').strip("'") for t in targets
                    if t.strip('"').strip("'") in stale_targets
                ]
                for r in removed:
                    log(f"  Removed: {source} → {r}", log_to_file)

                if not kept:
                    log(f"  Removed chain: {source} (all targets stale)",
                        log_to_file)
                    continue   # drop the whole line

                # Reconstruct the line with kept targets only
                kept_str  = ', '.join(kept)
                new_inner = f'{m.group(1)}{kept_str}{m.group(4)}'
                indent    = line[: len(line) - len(line.lstrip())]
                out_lines.append(f'{indent}- {new_inner}\n')
                continue

        out_lines.append(line)

    return ''.join(out_lines)

def update_fallbacks(config_text: str, working_names: set[str],
                     yes: bool, log_to_file: bool) -> tuple[str, bool]:
    """
    Validate fallback chains and optionally prune stale entries.

    Returns (updated_config_text, was_changed).
    """
    chains = parse_fallbacks(config_text)
    if not chains:
        log("\n  No fallbacks block found in config.yaml.", log_to_file)
        return config_text, False

    stale, unlinked = validate_fallbacks(chains, working_names, log_to_file)

    stale_targets = [t for _, t in stale if t]
    if not stale_targets:
        return config_text, False

    if not yes:
        try:
            answer = input(
                f"\nRemove {len(stale_targets)} stale fallback reference(s)? [y/N] "
            ).strip().lower()
        except (EOFError, KeyboardInterrupt):
            log("\nFallback pruning skipped.", log_to_file)
            return config_text, False
        if answer != 'y':
            log("Fallback chains unchanged.", log_to_file)
            return config_text, False

    log("\n── Pruning stale fallback entries ───────────────────────────",
        log_to_file)
    new_text = prune_fallbacks(config_text, stale, log_to_file)
    return new_text, True


def backup_config(config_path: Path) -> Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    ts   = datetime.now().strftime('%Y%m%d-%H%M%S')
    dest = BACKUP_DIR / f'config.yaml.bak.{ts}'
    dest.write_text(config_path.read_text())
    return dest

def update_config(entries: list[str], yes: bool, log_to_file: bool,
                  do_fallbacks: bool = False) -> bool:
    """
    Replace the model_list block in config.yaml with entries.
    If do_fallbacks=True, also validate and prune stale fallback chains.
    Returns True if the config was updated.
    """
    if not CONFIG_FILE.exists():
        log(f"\nERROR: {CONFIG_FILE} not found.", log_to_file)
        return False
    original = CONFIG_FILE.read_text()
    try:
        before, old_middle, after = split_config(original)
    except ValueError as e:
        log(f"\nERROR parsing config: {e}", log_to_file)
        return False

    old_names  = parse_yaml_model_list(old_middle)
    new_block  = build_model_list_block(entries)
    new_names  = parse_yaml_model_list(new_block)
    new_config = before + new_block + after

    log(f"\n── Config diff ──────────────────────────────────────────────",
        log_to_file)
    log(f"  Current:  {len(old_names)} entries", log_to_file)
    log(f"  Proposed: {len(new_names)} entries", log_to_file)
    show_diff(old_names, new_names, log_to_file)

    # Fallback validation against the new working set
    fb_changed = False
    if do_fallbacks:
        working_names = set(new_names)
        new_config, fb_changed = update_fallbacks(
            new_config, working_names, yes, log_to_file
        )

    if not validate_yaml(new_config):
        log("\nERROR: Generated config failed validation. Aborting.", log_to_file)
        return False

    model_list_changed = set(old_names) != set(new_names)
    if not model_list_changed and not fb_changed:
        log("\nNo changes to apply.", log_to_file)
        return True   # success — nothing to do

    if not yes:
        try:
            answer = input("\nApply all changes to config.yaml? [y/N] ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            log("\nAborted.", log_to_file)
            return False
        if answer != 'y':
            log("No changes made.", log_to_file)
            return False

    backup_path = backup_config(CONFIG_FILE)
    log(f"\n  Backup: {backup_path}", log_to_file)

    tmp = CONFIG_FILE.with_suffix('.yaml.tmp')
    try:
        tmp.write_text(new_config)
        tmp.rename(CONFIG_FILE)
    except Exception as e:
        log(f"  ERROR writing config: {e}", log_to_file)
        tmp.unlink(missing_ok=True)
        return False

    log(f"  ✓ {CONFIG_FILE} updated.", log_to_file)
    log(f"  Restart: docker compose -f ~/litellm/docker-compose.yml restart",
        log_to_file)
    return True


def fallback_only(yes: bool, log_to_file: bool) -> bool:
    """
    Validate and prune fallback chains without touching the model_list.
    Uses the current model_list in config.yaml as the working set.
    Returns True if completed without error.
    """
    if not CONFIG_FILE.exists():
        log(f"\nERROR: {CONFIG_FILE} not found.", log_to_file)
        return False

    config_text = CONFIG_FILE.read_text()

    # Working set = whatever is currently in the model_list
    try:
        _, middle, _ = split_config(config_text)
        working_names = set(parse_yaml_model_list(middle))
    except ValueError as e:
        log(f"\nERROR parsing config: {e}", log_to_file)
        return False

    log(f"  Using {len(working_names)} models from current model_list "
        f"as working set", log_to_file)

    new_config, changed = update_fallbacks(
        config_text, working_names, yes, log_to_file
    )

    if not changed:
        return True

    if not validate_yaml(new_config):
        log("\nERROR: Modified config failed validation. Aborting.", log_to_file)
        return False

    backup_path = backup_config(CONFIG_FILE)
    log(f"\n  Backup: {backup_path}", log_to_file)

    tmp = CONFIG_FILE.with_suffix('.yaml.tmp')
    try:
        tmp.write_text(new_config)
        tmp.rename(CONFIG_FILE)
    except Exception as e:
        log(f"  ERROR writing config: {e}", log_to_file)
        tmp.unlink(missing_ok=True)
        return False

    log(f"  ✓ {CONFIG_FILE} updated.", log_to_file)
    log(f"  Restart: docker compose -f ~/litellm/docker-compose.yml restart",
        log_to_file)
    return True


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description='Test and update LiteLLM provider models.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        '--update', action='store_true',
        help='Update model_list and validate/prune fallback chains',
    )
    parser.add_argument(
        '--fallback', action='store_true',
        help='Validate and prune stale fallback chains only (no model_list update)',
    )
    parser.add_argument(
        '--yes', '-y', action='store_true',
        help='Apply all changes without prompting (cron mode)',
    )
    parser.add_argument(
        '--show', action='store_true',
        help='Print generated model_list block to stdout',
    )
    parser.add_argument(
        '--providers', nargs='+',
        choices=['vllm', 'groq', 'nvidia', 'openrouter'],
        default=['vllm', 'groq', 'nvidia', 'openrouter'],
        help='Providers to probe (default: all)',
    )
    parser.add_argument(
        '--vllm-base', default=None,
        help='vLLM API base URL (overrides auto-detection from config.yaml)',
    )
    parser.add_argument(
        '--retest-failed', action='store_true',
        help='Clear failure cache for selected providers and retest all models',
    )
    parser.add_argument(
        '--show-cache', action='store_true',
        help='Print failure cache contents and exit',
    )
    parser.add_argument(
        '--clear-cache', metavar='PROVIDER',
        choices=['groq', 'nvidia', 'openrouter', 'vllm', 'all'],
        help='Clear failure cache for a provider (or "all") and exit',
    )
    args = parser.parse_args()

    # ── Cache-only commands ───────────────────────────────────────────────────
    if args.show_cache:
        print_cache(load_cache())
        return

    if args.clear_cache:
        cache = load_cache()
        if args.clear_cache == 'all':
            for p in cache['failed']:
                cache['failed'][p] = {}
            print("Cleared failure cache for all providers.")
        else:
            count = len(cache['failed'].get(args.clear_cache, {}))
            cache['failed'][args.clear_cache] = {}
            print(f"Cleared {count} cached failures for {args.clear_cache}.")
        save_cache(cache)
        return

    # ── Normal run ────────────────────────────────────────────────────────────
    log_to_file = args.update or args.fallback or args.yes
    if log_to_file:
        open_log()

    log(f"update_models.py  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        log_to_file)
    log(f"Providers: {', '.join(args.providers)}", log_to_file)

    cache = load_cache()
    if args.retest_failed:
        log("--retest-failed: clearing failure cache for selected providers.",
            log_to_file)
        for p in args.providers:
            cache['failed'][p] = {}

    env  = load_env(ENV_FILE)
    keys = {
        'groq':       get_key('GROQ_API_KEY', env),
        'nvidia':     get_key('NVIDIA_NIM_API_KEY', env),
        'openrouter': get_key('OPENROUTER_API_KEY', env),
    }

    # Auto-detect vLLM base URL from config.yaml
    vllm_base = args.vllm_base
    if 'vllm' in args.providers and not vllm_base and CONFIG_FILE.exists():
        for line in CONFIG_FILE.read_text().splitlines():
            m = re.search(r'api_base:\s+"?(http[^"\s]+)"?', line)
            if m and '8000' in m.group(1):
                vllm_base = m.group(1).rstrip('/').removesuffix('/v1')
                log(f"Auto-detected vLLM base: {vllm_base}", log_to_file)
                break
    if 'vllm' in args.providers and not vllm_base:
        log("WARNING: Could not auto-detect vLLM base URL. "
            "Skipping vLLM. Use --vllm-base to specify.", log_to_file)

    for provider in ['groq', 'nvidia', 'openrouter']:
        if provider in args.providers and not keys[provider]:
            log(f"WARNING: No API key for {provider} "
                f"(checked env + {ENV_FILE}). Skipping.", log_to_file)

    # ── Run probes ────────────────────────────────────────────────────────────
    t_start     = time.monotonic()
    all_entries: list[str] = []

    if 'vllm' in args.providers and vllm_base:
        entries, cache = probe_vllm(f'{vllm_base}/v1', cache, log_to_file)
        all_entries.extend(entries)

    if 'groq' in args.providers and keys['groq']:
        entries, cache = probe_groq(keys['groq'], cache, log_to_file)
        all_entries.extend(entries)

    if 'nvidia' in args.providers and keys['nvidia']:
        entries, cache = probe_nvidia(keys['nvidia'], cache, log_to_file)
        all_entries.extend(entries)

    if 'openrouter' in args.providers and keys['openrouter']:
        entries, cache = probe_openrouter(keys['openrouter'], cache, log_to_file)
        all_entries.extend(entries)

    elapsed = time.monotonic() - t_start

    # Always save cache — even dry runs update skip counts
    save_cache(cache)

    if not all_entries:
        log("\nNo working models found. Check API keys and network connectivity.",
            log_to_file)
        close_log()
        sys.exit(1)

    total_cached = sum(len(v) for v in cache['failed'].values())
    log(f"\n{'='*65}", log_to_file)
    log(f"Working models  : {len(all_entries)}", log_to_file)
    log(f"Elapsed         : {elapsed:.1f}s", log_to_file)
    log(f"Cached failures : {total_cached} models will be skipped on next run",
        log_to_file)

    # ── Output ────────────────────────────────────────────────────────────────
    if args.show:
        print('\n# ── Generated model_list block ──────────────────────────────')
        print(build_model_list_block(all_entries))
        close_log()
        return

    if args.fallback and not args.update:
        # Validate/prune fallbacks using current config model_list as working set.
        # Probing was still run so the working set is fresh, but we use config
        # names rather than probe results so manual entries are preserved.
        ok = fallback_only(args.yes, log_to_file)
        close_log()
        sys.exit(0 if ok else 1)

    if args.update:
        updated = update_config(
            all_entries, args.yes, log_to_file,
            do_fallbacks=True,    # always validate fallbacks on --update
        )
        close_log()
        sys.exit(0 if updated else 1)

    log("\nRun with --show          to print the generated model_list block.",
        log_to_file)
    log("Run with --update        to update model_list + prune fallbacks.",
        log_to_file)
    log("Run with --fallback      to validate/prune fallbacks only.",
        log_to_file)
    log("Run with --update --yes  or --fallback --yes for cron mode.",
        log_to_file)
    close_log()


if __name__ == '__main__':
    main()