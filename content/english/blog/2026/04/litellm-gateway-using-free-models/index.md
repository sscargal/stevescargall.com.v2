---
title: "Run Free LLMs at Scale: LiteLLM Gateway with Groq, NVIDIA NIM, OpenRouter, and Local vLLM"
meta_title: "LiteLLM Gateway: Free Cloud & Local LLMs with Automatic Fallback | Groq, NVIDIA NIM, OpenRouter, vLLM"
description: "Step-by-step guide to deploying a LiteLLM proxy gateway with free-tier cloud providers (Groq, NVIDIA NIM, OpenRouter) and local vLLM on DGX Spark. Covers Docker Compose setup, rate-limit handling, 24-hour cooldown fallbacks, and a model-maintenance script to keep your config current."
image: "featured_image.webp"
date: 2026-04-26T12:00:00-06:00
categories: ["AI", "HowTo"]
author: "Steve Scargall"
tags: ["LiteLLM", "LLM Gateway", "free LLM API", "Groq", "NVIDIA NIM", "OpenRouter", "vLLM", "DGX Spark", "Hermes Agent", "OpenWebUI", "Docker", "Docker Compose", "rate limiting", "LLM fallback", "local LLM", "AI infrastructure"]
draft: false
reading_time: 30
---

## Introduction

Running large language models is increasingly affordable — but "affordable" rarely means "free, all the time, for every request." Cloud providers each come with their own rate limits, daily quotas, and occasional model deprecations. Local hardware is fast and private, but not always available (DGX Spark powered down, model being updated, VRAM needed elsewhere). Somewhere between "I have an API key" and "my agents work reliably at scale" is a configuration problem that most guides skip over entirely.

This guide solves that configuration problem end-to-end.

By the end, you will have a single OpenAI-compatible endpoint at `localhost:4000/v1` that routes requests intelligently across:

- **Local vLLM on DGX Spark** — your primary, unlimited, privacy-preserving backend
- **Groq** — LPU-accelerated cloud inference; free within rate limits, no credit card required
- **NVIDIA NIM** — access to large frontier models via monthly free credits
- **OpenRouter** — the largest catalog of genuinely free (zero-cost) models, with independent rate-limit budgets per model

Every consuming application — Hermes Agent, OpenWebUI, Paperclip, or your own Python code — talks to one URL with one API key. When your local model is unavailable, LiteLLM falls back to the cloud. When a cloud provider's daily quota is exhausted, LiteLLM cools that model down for 24 hours and routes to the next provider in the chain. Free models come and go; the `update_models.py` script (see [Appendix A](#appendix-a-update_modelspy--automated-model-maintenance)) probes all configured providers, removes stale entries, and prunes broken fallback chains so your config stays accurate without manual bookkeeping.

The architecture below shows the final result:

---

## Architecture Overview

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│                               Your Linux Server                                    │
│                                                                                    │
│   ┌─────────┐   ┌──────────┐   ┌────────────┐   ┌───────┐                          │
│   │ Hermes  │   │OpenWebUI │   │ Paperclip  │   │YourApp│                          │
│   └────┬────┘   └────┬─────┘   └─────┬──────┘   └───┬───┘                          │
│        └─────────────┴────────────┬──┴──────────────┘                              │
│                                   │                                                │
│                  ┌────────────────▼────────────────┐                               │
│                  │          LiteLLM Proxy          │                               │
│                  │       localhost:4000/v1         │                               │
│                  │                                 │                               │
│                  │  • rpm/tpm declared per model   │                               │
│                  │  • 24h cooldown on daily 429    │                               │
│                  │  • ordered fallback chain       │                               │
│                  │  • failure cache (model_cache)  │                               │
│                  └────┬──────────┬─────────┬───────┴─────────────────────────┐     │
└───────────────────────┼──────────┼─────────┼─────────────────────────────────┼──-──┘
                        │          │         │                                 │
                        │          │         │                                 │
          ┌─────────────┘          │         └──────────┐                      │
          │                        │                    │                      │
          │                ┌───────┘                    │                      │
          │                │                            │                      │
┌─────────▼────-──────┐ ┌──▼─────────────┐ ┌────────────▼─────────┐ ┌──────────▼──────────────────┐
│    NVIDIA NIM       │ │     Groq       │ │      OpenRouter      │ │      Local DGX Spark        │
│  build.nvidia.com   │ │  (LPU fast     │ │   (:free models,     │ │  vLLM  DGX_IP:8000/v1       │
│  (credit-based)     │ │   inference)   │ │    zero-cost)        │ │  Primary — unlimited,       │
└─────────────────────┘ └────────────────┘ └──────────────────────┘ │  private, no API key        │
                                                                    └─────────────────────────────┘
◄────────────────── Cloud Hosted Model Providers ──────────────────► ◄──── Local ────►
```
---

## Table of Contents

- [Introduction](#introduction)
- [Architecture Overview](#architecture-overview)
- [Free Provider Rate Limits Reference](#free-provider-rate-limits-reference)
  - [Groq](#groq)
  - [NVIDIA NIM](#nvidia-nim-buildnvidiacom)
  - [OpenRouter](#openrouter)
- [How LiteLLM Handles Rate Limits](#how-litellm-handles-rate-limits)
  - [What LiteLLM does automatically](#what-litellm-does-automatically)
  - [What LiteLLM does NOT do automatically](#what-litellm-does-not-do-automatically)
  - [The core problem with daily limits](#the-core-problem-with-daily-limits)
- [Step 1: Verify vLLM Is Running Correctly](#step-1-verify-vllm-is-running-correctly)
- [Step 2: Get API Keys](#step-2-get-api-keys)
  - [NVIDIA NIM](#nvidia-nim-buildnvidiacom--free)
  - [OpenRouter](#openrouter-free-tier)
  - [Groq](#groq-rate-limited-free-access--no-credit-card-required)
- [Step 3: Deploy LiteLLM with Docker Compose](#step-3-deploy-litellm-with-docker-compose)
  - [3.1 Prerequisites](#31-prerequisites)
  - [3.2 Create the deployment directory](#32-create-the-deployment-directory)
  - [3.3 Create the environment file](#33-create-the-environment-file)
  - [3.4 Create docker-compose.yml](#34-create-docker-composeyml)
  - [3.5 Create config.yaml](#35-create-configyaml)
  - [3.6 Start the container](#36-start-the-container)
  - [3.7 Manage the container](#37-manage-the-container)
- [Step 4: Verify the Endpoints](#step-4-verify-the-endpoints)
  - [Test that fallbacks and cooldown work correctly](#test-that-fallbacks-and-cooldown-work-correctly)
- [Step 5: Monitor Rate Limit Status](#step-5-monitor-rate-limit-status)
  - [Check which models are healthy](#check-which-models-are-healthy)
  - [Inspect response headers to see remaining quota](#inspect-response-headers-to-see-remaining-quota)
- [Step 6: Ensure LiteLLM Starts on Boot](#step-6-ensure-litellm-starts-on-boot)
- [Step 7: Configure Hermes Agent](#step-7-configure-hermes-agent)
- [Step 8: Configure OpenWebUI](#step-8-configure-openwebui)
- [Step 9: Configure Paperclip](#step-9-configure-paperclip)
- [Step 10: Use LiteLLM in Your Own Applications](#step-10-use-litellm-in-your-own-applications)
- [Checking and Updating Free Model Catalogs](#checking-and-updating-free-model-catalogs)
- [Other Free API Providers](#other-free-api-providers)
  - [Google AI Studio (Gemini API)](#google-ai-studio-gemini-api)
  - [Cerebras Inference](#cerebras-inference)
  - [Mistral AI (La Plateforme)](#mistral-ai-la-plateforme)
  - [Together AI](#together-ai)
  - [Hugging Face Inference API](#hugging-face-inference-api)
  - [Cloudflare Workers AI](#cloudflare-workers-ai)
  - [Adding Any Provider to LiteLLM](#adding-any-provider-to-litellm)
- [Appendix A: update_models.py — Automated Model Maintenance](#appendix-a-update_modelspy--automated-model-maintenance)
  - [How the failure cache works](#how-the-failure-cache-works)
  - [Usage](#usage)
  - [What it does per provider](#what-it-does-per-provider)
  - [Fallback validation](#fallback-validation)
  - [Files written](#files-written)
  - [Optional: run on a schedule with cron](#optional-run-on-a-schedule-with-cron)
  - [Caveats](#caveats)
- [Troubleshooting](#troubleshooting)
- [Frequently Asked Questions](#frequently-asked-questions)
  - [General](#general)
  - [Rate Limits and Fallbacks](#rate-limits-and-fallbacks)
  - [Model Management](#model-management)
  - [OpenRouter Specifics](#openrouter-specifics)
  - [NVIDIA NIM Specifics](#nvidia-nim-specifics)
  - [vLLM and Local Model](#vllm-and-local-model)
  - [For AI Agents](#for-ai-agents)
- [Quick Reference](#quick-reference)
- [Summary and Conclusion](#summary-and-conclusion)

---

## Free Provider Rate Limits Reference

Check these pages directly when you need the current limits — they change without notice.

### Groq
- **Rate limits page:** https://console.groq.com/docs/rate-limits
- **Your usage dashboard:** https://console.groq.com/dashboard
- **Limit type:** Per model, per organization (not per API key)
- **Reset:** Uses a **rolling window**, not a fixed midnight reset. Capacity trickles back continuously as older requests age out of the window.

**Free tier access:** Groq is a paid service (see https://groq.com/pricing), but accounts without a credit card attached get rate-limited access at no charge. The pricing page lists per-token costs that apply only once you add billing and exceed the free limits. For agent workloads within the limits below, Groq costs nothing.

**List all available models:**

```bash
curl https://api.groq.com/openai/v1/models \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  | python3 -m json.tool
```

The response includes all chat, speech, and moderation models. To extract just the IDs for the models relevant to chat completion:

```bash
curl -s https://api.groq.com/openai/v1/models \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  | python3 -c "
import json, sys
models = json.load(sys.stdin)['data']
for m in sorted(models, key=lambda x: x['id']):
    print(f\"{m['id']:<55} ctx={m.get('context_window','?')}\")"
```

You can verify your actual rate limits at any time with a minimal inference call — using `max_tokens: 1` keeps the token cost negligible even if billing is eventually applied:

```bash
# Check llama-3.1-8b-instant limits
curl -s -o /dev/null -v \
  https://api.groq.com/openai/v1/chat/completions \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"llama-3.1-8b-instant","messages":[{"role":"user","content":"hi"}],"max_tokens":1}' \
  2>&1 | grep -i "x-ratelimit\|x-groq"
```

Expected output:
```
< x-groq-region: dls
< x-ratelimit-limit-requests: 14400
< x-ratelimit-limit-tokens: 6000
< x-ratelimit-remaining-requests: 14399
< x-ratelimit-remaining-tokens: 5963
< x-ratelimit-reset-requests: 6s
< x-ratelimit-reset-tokens: 370ms
```

```bash
# Check llama-3.3-70b-versatile limits
curl -s -o /dev/null -v \
  https://api.groq.com/openai/v1/chat/completions \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"llama-3.3-70b-versatile","messages":[{"role":"user","content":"hi"}],"max_tokens":1}' \
  2>&1 | grep -i "x-ratelimit\|x-groq"
```

Expected output:
```
< x-groq-region: dls
< x-ratelimit-limit-requests: 1000
< x-ratelimit-limit-tokens: 12000
< x-ratelimit-remaining-requests: 999
< x-ratelimit-remaining-tokens: 11963
< x-ratelimit-reset-requests: 1m26.4s
< x-ratelimit-reset-tokens: 185ms
```

Reading the headers:

- `x-ratelimit-limit-requests` — your total request budget for the window (14,400 for 8B; 1,000 for 70B)
- `x-ratelimit-remaining-requests` — how many requests remain before a 429
- `x-ratelimit-reset-requests` — time until the **next slot** opens in the rolling window, not a full reset. For 8B (`6s`), capacity is trickling back every few seconds. For 70B (`1m26s`), each of the 1,000 daily slots opens approximately every 86 seconds throughout the day.
- `x-groq-region` — which LPU datacenter served the request (`dls` = Dallas)

**Free tier limits confirmed from the above output:**

| Model ID | Request limit | TPM | Reset behaviour |
|---|---|---|---|
| `llama-3.1-8b-instant` | 14,400 / day | 6,000 | Rolling — slot opens every ~6s |
| `llama-3.3-70b-versatile` | 1,000 / day | 12,000 | Rolling — slot opens every ~86s |
| `meta-llama/llama-4-scout-17b-16e-instruct` | 1,000 / day | 30,000 | Rolling |
| `qwen/qwen3-32b` | 1,000 / day | 6,000 | Rolling |

Key points: limits are per-model independently (exhausting the 70B daily budget does not affect the 8B budget), no credit card required for access within these limits, cached tokens do not count against TPM.

### NVIDIA NIM (build.nvidia.com)
- **Model catalog and limits:** https://build.nvidia.com/explore/discover
- **Free hosted endpoints (Preview tier):** https://build.nvidia.com/models?filters=nimType%3Anim_type_preview&pageSize=96
- **API reference:** https://docs.api.nvidia.com/nim/reference/
- Free credit allocation (1,000 credits on signup, up to 5,000 by request) resets monthly. All models accessible via your API key consume from this credit allocation — there is no separate paid/free distinction in the API response itself.

**Note on filtering for free models programmatically:** The `/v1/models` response schema contains only `id`, `object`, `created`, `owned_by`, `root`, `parent`, `max_model_len`, and a `permission` array — no pricing or tier information. The `nim_type_preview` classification exists only in the website UI. The only reliable approach is to test each model directly and discover which ones are accessible on your account.

The `update_models.py` script (see Appendix A) automates this: it fetches the full model list, filters out non-chat models, probes each one, and updates your config with only verified working models. Run it whenever NVIDIA adds or removes models from the catalog.

**Quick manual check — list chat-capable models and test one:**

```bash
# List all candidate chat models (filtered, deduplicated)
curl -s https://integrate.api.nvidia.com/v1/models \
  -H "Authorization: Bearer $NVIDIA_NIM_API_KEY" \
  | python3 -c "
import json, sys
models = json.load(sys.stdin)['data']
EXCLUDE = ['embed','rerank','whisper','riva','vision','vlm','ocr','grounding',
           'segmentation','classification','guardrail','reward','bionemo',
           'fourcastnet','proteina','neva','vila','deplot','fuyu','kosmos',
           'nvclip','parse','detector','chatqa','starcoder','recurrentgemma',
           'ising','safety','guard']
seen = set()
for m in sorted(models, key=lambda x: x['id']):
    mid = m['id']
    if mid not in seen and not any(x in mid.lower() for x in EXCLUDE):
        seen.add(mid)
        print(mid)"
```

### OpenRouter
- **Free models list (UI):** https://openrouter.ai/models?max_price=0
- **Your usage dashboard:** https://openrouter.ai/activity
- **Limit type:** Per model, per API key
- Genuinely free models have `pricing.prompt == "0"` and `pricing.completion == "0"` in the API response. Default rate limit is ~200 RPD per free model; a one-time credit purchase of $10 or more raises that to 1,000 RPD for all free models permanently.
- **Important:** With a $0 credit balance, OpenRouter routes all free model requests through a single backend provider (Venice). Venice rate-limits aggressively and OpenRouter misreports these 429s as 401 "User not found" errors. Adding a minimum $5 credit balance unlocks additional backend providers and resolves this. Your free models remain zero-cost — the credit balance is only consumed if you use paid models.

**List genuinely free models (both prompt and completion cost zero):**

```bash
curl -s https://openrouter.ai/api/v1/models \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  | python3 -c "
import json, sys
models = json.load(sys.stdin)['data']
# Filter: both prompt and completion must be zero-cost
# Also exclude non-chat models (audio, OCR, image-only) that would fail inference calls
EXCLUDE = {'lyria', 'ocr', 'clip', 'vl-'}
free = [m for m in models
        if m.get('pricing', {}).get('prompt') == '0'
        and m.get('pricing', {}).get('completion') == '0'
        and not any(x in m['id'] for x in EXCLUDE)]
print(f'{len(free)} genuinely free chat models (prompt=0, completion=0):\n')
for m in sorted(free, key=lambda x: x['id']):
    ctx = m.get('context_length', '?')
    print(f\"{m['id']:<60}  ctx={ctx}\")"
```

Note: the `EXCLUDE` list filters out models that would fail standard chat completion calls:
- `lyria` — audio/music generation models (not chat)
- `ocr` — OCR models (not chat)
- `clip` — image classification models (not chat)
- `vl-` — vision-language models that require image input (will fail on text-only requests)

Remove any entry from `EXCLUDE` if you specifically want those model types.

**Dump full metadata for all free models:**

```bash
curl -s https://openrouter.ai/api/v1/models \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  | python3 -c "
import json, sys
models = json.load(sys.stdin)['data']
free = [m for m in models
        if m.get('pricing', {}).get('prompt') == '0'
        and m.get('pricing', {}).get('completion') == '0']
# Print schema from first model
print('=== Schema (first free model) ===')
print(json.dumps(free[0], indent=2))
print()
print(f'=== All {len(free)} free models (full metadata) ===')
for m in sorted(free, key=lambda x: x['id']):
    print(json.dumps(m, indent=2))"
```

Unlike NVIDIA NIM, OpenRouter's pricing metadata is included directly in the API response — `pricing.prompt == "0"` and `pricing.completion == "0"` together are the reliable programmatic filter for models that will never incur a charge. The `?free_only=true` query parameter is **not** a reliable filter — it returns models with any free routing path, including paid frontier models. Always use the pricing field filter. The free catalog changes frequently; re-run the listing command periodically to stay current.

---

## How LiteLLM Handles Rate Limits

Understanding what LiteLLM does and doesn't do automatically is essential before setting up the config.

### What LiteLLM does automatically

When a provider returns a `429 Too Many Requests`, LiteLLM:

1. **Retries** the same model up to `num_retries` times (with a delay between each)
2. **Falls back** to the next model in your `fallbacks` chain if retries are exhausted
3. **Puts the model in cooldown** if it fails more than `allowed_fails` times in a window, skipping it for `cooldown_time` seconds on subsequent requests

The fallback and cooldown behavior is documented at:
https://docs.litellm.ai/docs/proxy/reliability

### What LiteLLM does NOT do automatically

- It does **not** read `x-ratelimit-remaining-requests` response headers to proactively skip a model before hitting the limit
- It does **not** have a concept of "daily limit reached — skip until midnight"
- Without Redis, cooldown state is **in-memory only** and resets if LiteLLM restarts

### The core problem with daily limits

A `cooldown_time` of 60 seconds is useless against a request budget cap. Once Groq's 1,000-request budget for `llama-3.3-70b-versatile` is exhausted, LiteLLM will cool down for 60 seconds, try again, get another 429, cool down again, and repeat — burning retries and adding latency on every request.

Note that Groq uses a **rolling window**, not a fixed midnight reset. For `llama-3.3-70b-versatile`, each of the 1,000 daily slots opens approximately every 86 seconds throughout the day (`x-ratelimit-reset-requests: 1m26.4s` as seen in the real output above). This means capacity gradually returns rather than all at once — but it also means a `cooldown_time` shorter than the slot interval is still wasteful.

The solution is two-part:

1. **Declare `rpm` and `tpm` per model** — LiteLLM's router tracks these in-memory and pre-emptively avoids models approaching their per-minute limits before a 429 ever occurs
2. **Set `cooldown_time: 86400`** (24 hours) with a low `allowed_fails` — once a model hits its daily wall and fails a few times in a row, it gets skipped for the rest of the day

LiteLLM's routing and load balancing documentation:
https://docs.litellm.ai/docs/routing

---

## Step 1: Verify vLLM Is Running Correctly

From your Linux server, confirm the DGX Spark endpoint is accessible:

```bash
# Replace DGX_IP with the actual IP of your DGX Spark
curl http://DGX_IP:8000/v1/models
```

Note the exact model name in the response — you'll need it in config.

**If vLLM was started without tool-calling support**, restart it on the DGX Spark:

```bash
vllm serve <your-qwen-model-name> \
  --port 8000 \
  --host 0.0.0.0 \
  --max-model-len 32768 \
  --enable-auto-tool-choice \
  --tool-call-parser hermes
```

The `--tool-call-parser hermes` flag is required for Hermes Agent's tool calling to work with Qwen/Hermes-family models.

---

## Step 2: Get API Keys

### NVIDIA NIM (build.nvidia.com — free)

1. Go to https://build.nvidia.com and sign in or create a free account
2. Navigate to **API Keys** in your account settings
3. Create a key — copy it immediately (shown once)
4. The env var name is `NVIDIA_NIM_API_KEY` (not `NVIDIA_API_KEY`)
   - LiteLLM docs: https://docs.litellm.ai/docs/providers/nvidia_nim

### OpenRouter (free tier)

1. Go to https://openrouter.ai → create account → **Keys** → **Create Key**
2. Copy the key (starts with `sk-or-v1-...`)
3. Browse https://openrouter.ai/models?supported_parameters=free for `:free` models
   - LiteLLM docs: https://docs.litellm.ai/docs/providers/openrouter

### Groq (rate-limited free access — no credit card required)

1. Go to https://console.groq.com and sign up with email or Google
2. Go to **API Keys** → **Create API Key**
3. Copy the key (starts with `gsk_...`)
4. No credit card required — free forever within rate limits
   - LiteLLM docs: https://docs.litellm.ai/docs/providers/groq

---

## Step 3: Deploy LiteLLM with Docker Compose

We use the **Docker Hardened Image** from Docker Hub rather than the standard LiteLLM image. Hardened Images are built to zero-known-CVE standards, include signed provenance, and ship with a complete Software Bill of Materials (SBOM).

- **Image catalog:** https://hub.docker.com/hardened-images/catalog/dhi/litellm
- **Images list:** https://hub.docker.com/hardened-images/catalog/dhi/litellm/images
- **LiteLLM Docker quickstart:** https://docs.litellm.ai/docs/proxy/docker_quick_start

The image runs as non-root user uid 65532, limiting blast radius if any component is ever exploited. The tag `dhi.io/litellm:1` is a floating tag that tracks the latest `1.x` patch release.

### 3.1 Prerequisites

Ensure Docker Engine and Docker Compose plugin are installed:

```bash
# Check versions
docker --version
docker compose version

# If not installed, follow: https://docs.docker.com/engine/install/
```

### 3.2 Create the deployment directory

All LiteLLM files live together so Docker Compose can find them:

```bash
mkdir -p ~/litellm
cd ~/litellm
```

### 3.3 Create the environment file

Create the `.env` file in the `~/litellm` directory using the following content:

```bash
nano ~/litellm/.env
chmod 600 ~/litellm/.env
```

```bash
# ~/litellm/.env
# LiteLLM gateway master key — used by all apps to authenticate to the proxy
# Change this to something unique before first use
LITELLM_MASTER_KEY=sk-litellm-local

# NVIDIA NIM — IMPORTANT: variable name is NVIDIA_NIM_API_KEY, not NVIDIA_API_KEY
# Docs: https://docs.litellm.ai/docs/providers/nvidia_nim
NVIDIA_NIM_API_KEY=nvapi-YOUR_KEY_HERE

# OpenRouter — free :free models need no special flag in the key itself
# Docs: https://docs.litellm.ai/docs/providers/openrouter
OPENROUTER_API_KEY=sk-or-v1-YOUR_KEY_HERE

# Groq — rate-limited free access, no credit card required within limits
# Get key: https://console.groq.com/keys
# Docs: https://docs.litellm.ai/docs/providers/groq
GROQ_API_KEY=gsk_YOUR_KEY_HERE
```

### 3.4 Create `docker-compose.yml`

Create the `docker-compose.yml` file in the `~/litellm` directory using the following content:

```bash
nano ~/litellm/docker-compose.yml
```

```yaml
# ~/litellm/docker-compose.yml
# LiteLLM Multi-Provider Gateway — Docker Hardened Image
# Image: https://hub.docker.com/hardened-images/catalog/dhi/litellm
# LiteLLM proxy docs: https://docs.litellm.ai/docs/proxy/docker_quick_start

services:
  litellm:
    image: dhi.io/litellm:1          # Production hardened image, non-root user 65532
    # image: dhi.io/litellm:1.82.3   # Pin to a specific patch version for reproducibility
    container_name: litellm
    restart: unless-stopped           # Daemonized: auto-restarts on crash or reboot

    ports:
      - "4000:4000"                   # Expose proxy on host port 4000

    volumes:
      # Mount the config file read-only into the container path LiteLLM expects
      # LiteLLM docs use /app/config.yaml as the canonical container path
      - ./config.yaml:/app/config.yaml:ro

    env_file:
      - .env                          # Injects all keys from .env into the container

    command:
      - "--config=/app/config.yaml"
      - "--port=4000"
      - "--host=0.0.0.0"

    # The hardened image runs as non-root uid 65532.
    # The config file must be readable by that user — :ro mount is sufficient
    # since the file is owned by your host user and world-readable by default.
    # If you tighten permissions (chmod 600 config.yaml), add:
    #   user: "YOUR_UID:YOUR_GID"
    # where YOUR_UID matches the file owner on the host.

    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:4000/health/liveliness"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 20s

    logging:
      driver: "json-file"
      options:
        max-size: "50m"
        max-file: "5"
```

### 3.5 Create `config.yaml`

The config file lives alongside `docker-compose.yml` so the volume mount resolves correctly. Create it now — the container will not start without it.

```bash
nano ~/litellm/config.yaml
```

Key design decisions in this config:

- `rpm` and `tpm` declared on every free-tier model — LiteLLM tracks these in-memory and avoids scheduling requests that would immediately exceed per-minute limits
- `allowed_fails: 3` with `cooldown_time: 86400` — after 3 consecutive failures LiteLLM skips that model for 24 hours, covering daily quota exhaustion
- Fallback chains ordered by daily durability — `groq/llama-3.1-8b` (14,400 RPD) appears before `groq/llama-3.3-70b` (1,000 RPD) so the higher-budget model absorbs the overflow when the cap is hit
- `background_health_checks` with `enable_health_check_routing` — proactively removes failing deployments from the pool before user requests land on them

```yaml
# ~/litellm/config.yaml  →  mounted into container as /app/config.yaml
# LiteLLM Multi-Provider Gateway
# Providers: local vLLM, NVIDIA NIM, OpenRouter, Groq
#
# Rate-limit strategy:
#   - rpm/tpm declared per model → LiteLLM tracks usage in-memory, avoids pre-minute cap
#   - allowed_fails + cooldown_time: 86400 → skip exhausted models for 24 hours
#   - fallback chain → automatic provider hopping when a model is rate-limited
#
# LiteLLM routing docs: https://docs.litellm.ai/docs/routing
# LiteLLM fallback docs: https://docs.litellm.ai/docs/proxy/reliability


model_list:

  # ── LOCAL vLLM on DGX Spark ──────────────────────────────────────────────
  # Use hosted_vllm/ prefix — canonical LiteLLM route for OpenAI-compatible vLLM
  # LiteLLM vLLM docs: https://docs.litellm.ai/docs/providers/vllm
  - model_name: "local/qwen"
    litellm_params:
      model: "hosted_vllm/YOUR_QWEN_MODEL_NAME"  # e.g. hosted_vllm/Qwen/Qwen2.5-72B-Instruct
      api_base: "http://DGX_IP:8000/v1"           # Replace DGX_IP with actual IP
      api_key: "none"
    model_info:
      description: "Local Qwen on DGX Spark — primary, unlimited"

  # ── GROQ — fastest inference, LPU hardware ───────────────────────────────
  # Free tier limits (per model, per org, no credit card needed):
  # Rate limits page:  https://console.groq.com/docs/rate-limits
  # Live org limits:   https://console.groq.com/settings/limits
  # LiteLLM docs:      https://docs.litellm.ai/docs/providers/groq
  #
  # IMPORTANT: rpm/tpm declared here so LiteLLM tracks in-memory and
  # avoids scheduling requests that would immediately 429.
  # Set rpm slightly under the real limit as a buffer (e.g. 28 of 30).
  # tpm set conservatively — actual TPM limit for llama-3.3-70b is 12,000.

  - model_name: "groq/llama-3.3-70b"
    litellm_params:
      model: "groq/llama-3.3-70b-versatile"
      api_key: "os.environ/GROQ_API_KEY"
      rpm: 28        # Real limit: 30 RPM — buffer of 2 to avoid edge-case 429s
      tpm: 11000     # Real limit: 12,000 TPM
    model_info:
      description: "Groq Llama 3.3 70B — fast cloud fallback, 1K RPD daily cap"

  - model_name: "groq/llama-3.1-8b"
    litellm_params:
      model: "groq/llama-3.1-8b-instant"
      api_key: "os.environ/GROQ_API_KEY"
      rpm: 28        # Real limit: 30 RPM
      tpm: 5500      # Real limit: 6,000 TPM
    model_info:
      description: "Groq Llama 3.1 8B — high daily budget (14,400 RPD), best Groq fallback"

  - model_name: "groq/llama-4-scout"
    litellm_params:
      model: "groq/meta-llama/llama-4-scout-17b-16e-instruct"
      api_key: "os.environ/GROQ_API_KEY"
      rpm: 28        # Real limit: 30 RPM
      tpm: 28000     # Real limit: 30,000 TPM — good for long contexts
    model_info:
      description: "Groq Llama 4 Scout — high TPM, 1K RPD"

  - model_name: "groq/qwen3-32b"
    litellm_params:
      model: "groq/qwen/qwen3-32b"
      api_key: "os.environ/GROQ_API_KEY"
      rpm: 58        # Real limit: 60 RPM — highest RPM on free tier
      tpm: 5500      # Real limit: 6,000 TPM
    model_info:
      description: "Groq Qwen3 32B — highest RPM of free models"

  # ── NVIDIA NIM — large capable models ────────────────────────────────────
  # Free tier: credit allocation, limits vary per model.
  # Model catalog + limits: https://build.nvidia.com/explore/discover
  # API reference:          https://docs.api.nvidia.com/nim/reference/
  # LiteLLM docs:           https://docs.litellm.ai/docs/providers/nvidia_nim
  # IMPORTANT: env var is NVIDIA_NIM_API_KEY, not NVIDIA_API_KEY
  # Default API base:       https://integrate.api.nvidia.com/v1/

  - model_name: "nvidia/llama-3.3-70b"
    litellm_params:
      model: "nvidia_nim/meta/llama-3.3-70b-instruct"
      api_key: "os.environ/NVIDIA_NIM_API_KEY"
      rpm: 40        # Approximate — check your model's page at build.nvidia.com
    model_info:
      description: "NVIDIA NIM Llama 3.3 70B — check build.nvidia.com for exact limits"

  - model_name: "nvidia/llama-3.1-70b"
    litellm_params:
      model: "nvidia_nim/meta/llama-3.1-70b-instruct"
      api_key: "os.environ/NVIDIA_NIM_API_KEY"
      rpm: 40
    model_info:
      description: "NVIDIA NIM Llama 3.1 70B"

  - model_name: "nvidia/mistral-nemo"
    litellm_params:
      model: "nvidia_nim/mistralai/mistral-nemo-12b-instruct"
      api_key: "os.environ/NVIDIA_NIM_API_KEY"
      rpm: 40
    model_info:
      description: "NVIDIA NIM Mistral NeMo 12B"

  # ── OPENROUTER — genuinely free models (prompt=0, completion=0) ──────────
  # Free models list (UI): https://openrouter.ai/models?max_price=0
  # Your usage:            https://openrouter.ai/activity
  # LiteLLM docs:          https://docs.litellm.ai/docs/providers/openrouter
  # Refresh free model list — see the Free Provider Rate Limits Reference section
  # for the curl command to regenerate this list from the API.
  # Limits: ~20 RPM, ~200 RPD per free model (1,000 RPD with any credit purchase).

  # ── Large / high-capability ───────────────────────────────────────────────
  - model_name: "openrouter/hermes-3-405b"
    litellm_params:
      model: "openrouter/nousresearch/hermes-3-llama-3.1-405b:free"
      api_key: "os.environ/OPENROUTER_API_KEY"
      rpm: 18
    model_info:
      description: "Hermes 3 405B — same family as local agent, 131K ctx"

  - model_name: "openrouter/nemotron-super-120b"
    litellm_params:
      model: "openrouter/nvidia/nemotron-3-super-120b-a12b:free"
      api_key: "os.environ/OPENROUTER_API_KEY"
      rpm: 18
    model_info:
      description: "NVIDIA Nemotron Super 120B — 262K ctx"

  - model_name: "openrouter/llama-3.3-70b"
    litellm_params:
      model: "openrouter/meta-llama/llama-3.3-70b-instruct:free"
      api_key: "os.environ/OPENROUTER_API_KEY"
      rpm: 18
    model_info:
      description: "Meta Llama 3.3 70B — 65K ctx"

  - model_name: "openrouter/qwen3-next-80b"
    litellm_params:
      model: "openrouter/qwen/qwen3-next-80b-a3b-instruct:free"
      api_key: "os.environ/OPENROUTER_API_KEY"
      rpm: 18
    model_info:
      description: "Qwen3 Next 80B MoE — 262K ctx"

  - model_name: "openrouter/qwen3-coder"
    litellm_params:
      model: "openrouter/qwen/qwen3-coder:free"
      api_key: "os.environ/OPENROUTER_API_KEY"
      rpm: 18
    model_info:
      description: "Qwen3 Coder — 262K ctx, strong for code tasks"

  - model_name: "openrouter/gpt-oss-120b"
    litellm_params:
      model: "openrouter/openai/gpt-oss-120b:free"
      api_key: "os.environ/OPENROUTER_API_KEY"
      rpm: 18
    model_info:
      description: "OpenAI GPT OSS 120B — 131K ctx"

  - model_name: "openrouter/gpt-oss-20b"
    litellm_params:
      model: "openrouter/openai/gpt-oss-20b:free"
      api_key: "os.environ/OPENROUTER_API_KEY"
      rpm: 18
    model_info:
      description: "OpenAI GPT OSS 20B — 131K ctx"

  # ── Medium models ─────────────────────────────────────────────────────────
  - model_name: "openrouter/deepseek-r1"
    litellm_params:
      model: "openrouter/deepseek/deepseek-r1:free"
      api_key: "os.environ/OPENROUTER_API_KEY"
      rpm: 18
    model_info:
      description: "DeepSeek R1 — reasoning model, 64K ctx"

  - model_name: "openrouter/minimax-m2.5"
    litellm_params:
      model: "openrouter/minimax/minimax-m2.5:free"
      api_key: "os.environ/OPENROUTER_API_KEY"
      rpm: 18
    model_info:
      description: "MiniMax M2.5 — 196K ctx"

  - model_name: "openrouter/nemotron-nano-30b"
    litellm_params:
      model: "openrouter/nvidia/nemotron-3-nano-30b-a3b:free"
      api_key: "os.environ/OPENROUTER_API_KEY"
      rpm: 18
    model_info:
      description: "NVIDIA Nemotron Nano 30B MoE — 256K ctx"

  - model_name: "openrouter/gemma-4-31b"
    litellm_params:
      model: "openrouter/google/gemma-4-31b-it:free"
      api_key: "os.environ/OPENROUTER_API_KEY"
      rpm: 18
    model_info:
      description: "Google Gemma 4 31B — 262K ctx"

  - model_name: "openrouter/gemma-4-26b"
    litellm_params:
      model: "openrouter/google/gemma-4-26b-a4b-it:free"
      api_key: "os.environ/OPENROUTER_API_KEY"
      rpm: 18
    model_info:
      description: "Google Gemma 4 26B MoE — 262K ctx"

  - model_name: "openrouter/gemma-3-27b"
    litellm_params:
      model: "openrouter/google/gemma-3-27b-it:free"
      api_key: "os.environ/OPENROUTER_API_KEY"
      rpm: 18
    model_info:
      description: "Google Gemma 3 27B — 131K ctx"

  - model_name: "openrouter/glm-4.5-air"
    litellm_params:
      model: "openrouter/z-ai/glm-4.5-air:free"
      api_key: "os.environ/OPENROUTER_API_KEY"
      rpm: 18
    model_info:
      description: "GLM 4.5 Air — 131K ctx"

  - model_name: "openrouter/hy3-preview"
    litellm_params:
      model: "openrouter/tencent/hy3-preview:free"
      api_key: "os.environ/OPENROUTER_API_KEY"
      rpm: 18
    model_info:
      description: "Tencent HY3 Preview — 262K ctx"

  - model_name: "openrouter/ling-flash"
    litellm_params:
      model: "openrouter/inclusionai/ling-2.6-flash:free"
      api_key: "os.environ/OPENROUTER_API_KEY"
      rpm: 18
    model_info:
      description: "InclusionAI Ling 2.6 Flash — 262K ctx"

  - model_name: "openrouter/dolphin-mistral-24b"
    litellm_params:
      model: "openrouter/cognitivecomputations/dolphin-mistral-24b-venice-edition:free"
      api_key: "os.environ/OPENROUTER_API_KEY"
      rpm: 18
    model_info:
      description: "Dolphin Mistral 24B Venice — 32K ctx"

  # ── Smaller / lighter ─────────────────────────────────────────────────────
  - model_name: "openrouter/nemotron-nano-9b"
    litellm_params:
      model: "openrouter/nvidia/nemotron-nano-9b-v2:free"
      api_key: "os.environ/OPENROUTER_API_KEY"
      rpm: 18
    model_info:
      description: "NVIDIA Nemotron Nano 9B — 128K ctx, fast"

  - model_name: "openrouter/llama-3.2-3b"
    litellm_params:
      model: "openrouter/meta-llama/llama-3.2-3b-instruct:free"
      api_key: "os.environ/OPENROUTER_API_KEY"
      rpm: 18
    model_info:
      description: "Meta Llama 3.2 3B — 131K ctx, lightweight fallback"



# ── ROUTER SETTINGS ──────────────────────────────────────────────────────────
# Full routing docs: https://docs.litellm.ai/docs/routing
# Fallback docs:     https://docs.litellm.ai/docs/proxy/reliability

router_settings:
  # simple-shuffle is the recommended default. It uses the declared rpm/tpm values
  # above to weight routing decisions and skip over-capacity deployments.
  # If rpm/tpm are declared, it will avoid scheduling requests that would exceed them.
  routing_strategy: "simple-shuffle"

  num_retries: 2         # Retry the same model this many times before falling back
  retry_after: 5         # Seconds to wait between retries

  # Cooldown: after allowed_fails consecutive failures, skip the model for
  # cooldown_time seconds. Set to 86400 (24 hours) so a model that has hit
  # its daily request cap gets skipped for the rest of the day.
  # LiteLLM cooldown docs: https://docs.litellm.ai/docs/proxy/reliability#advanced
  allowed_fails: 3       # Trigger cooldown after 3 consecutive failures
  cooldown_time: 86400   # 24 hours in seconds — covers daily rate limit resets

  # Fallback chains — tried in order when a model fails after all retries.
  # Fallback docs: https://docs.litellm.ai/docs/proxy/reliability
  fallbacks:
    # Primary: local fails → try Groq high-RPD first, then NVIDIA, then OpenRouter
    - {"local/qwen":         ["groq/llama-3.1-8b", "groq/llama-3.3-70b", "nvidia/llama-3.3-70b", "openrouter/hermes-3-405b"]}
    # Groq 70B hits daily cap → high-RPD Groq models first, then NVIDIA
    - {"groq/llama-3.3-70b": ["groq/llama-3.1-8b", "groq/llama-4-scout", "nvidia/llama-3.3-70b", "openrouter/hermes-3-405b"]}
    - {"groq/qwen3-32b":     ["groq/llama-3.1-8b", "nvidia/llama-3.3-70b"]}
    # NVIDIA fails → OpenRouter free tier
    - {"nvidia/llama-3.3-70b": ["openrouter/hermes-3-405b", "openrouter/llama-3.3-70b", "openrouter/deepseek-r1"]}
    # OpenRouter hits daily cap → try other free OpenRouter models
    - {"openrouter/hermes-3-405b": ["openrouter/nemotron-super-120b", "openrouter/llama-3.3-70b", "openrouter/qwen3-next-80b"]}
    - {"openrouter/llama-3.3-70b":  ["openrouter/qwen3-next-80b", "openrouter/gemma-4-31b", "openrouter/gpt-oss-120b"]}

  # Default fallback for any model not listed above

  # Context window fallbacks: if a request exceeds the model's context window,
  # automatically fall back to a model with a larger window.
  context_window_fallbacks:
    - {"groq/llama-3.1-8b":   ["groq/llama-3.3-70b", "nvidia/llama-3.3-70b"]}

# ── HEALTH CHECK SETTINGS ────────────────────────────────────────────────────
# Health check docs: https://docs.litellm.ai/docs/proxy/health_check_routing
general_settings:
  master_key: "sk-litellm-local"    # Change this — used by apps to authenticate
  store_model_in_db: false

  # Background health checks — pings each model on an interval and removes
  # failing deployments from the routing pool before a user request hits them.
  background_health_checks: true
  health_check_interval: 300        # Ping every 5 minutes (300 seconds)
  enable_health_check_routing: true

# ── LITELLM SETTINGS ─────────────────────────────────────────────────────────
litellm_settings:
  drop_params: true        # Silently drop params unsupported by a given provider
  set_verbose: false
  request_timeout: 120     # Seconds before a request is considered failed
```

### 3.6 Start the container

Docker Hardened Images are served from a private registry at `dhi.io` that requires authentication before you can pull. You need a Docker Personal Access Token (PAT) to log in.

**Create a PAT:**
1. Go to https://app.docker.com/settings and log in
2. Navigate to **Personal access tokens** → **Generate new token**
3. Give it a name (e.g. `hermes-server`) and copy the token — it is shown only once

**Authenticate to the registry:**

```bash
docker login dhi.io
# Username: your Docker Hub username
# Password: your PAT (not your Docker Hub password)
```

A successful login stores credentials in `~/.docker/config.json` and persists across reboots — you only need to do this once per machine.

**Pull the image and start the container:**

```bash
cd ~/litellm

# Pull the hardened image using Docker Compose
# (reads the image name from docker-compose.yml automatically)
docker compose pull

# Start daemonized (detached)
docker compose up -d

# Confirm it's running
docker compose ps
docker compose logs -f          # Follow logs; Ctrl+C to detach
```

Expected output from `docker compose ps`:
```
NAME       IMAGE            COMMAND                  SERVICE    CREATED         STATUS                   PORTS
litellm    dhi.io/litellm:1 "litellm --config=..."   litellm    5 seconds ago   Up 4 seconds (healthy)   0.0.0.0:4000->4000/tcp
```

Check the logs to confirm all models loaded cleanly:

```bash
docker compose logs litellm | grep -A 20 "Proxy initialized"
```

A clean startup looks like this - all configured models listed, no warnings (count will vary if you customise the model list):

```
LiteLLM: Proxy initialized with Config, Set models:
    local/qwen
    groq/llama-3.3-70b
    groq/llama-3.1-8b
    groq/llama-4-scout
    groq/qwen3-32b
    nvidia/llama-3.3-70b
    nvidia/llama-3.1-70b
    nvidia/mistral-nemo
    openrouter/hermes-3-405b
    ...
    openrouter/glm-4.5-air
    openrouter/hy3-preview
    openrouter/ling-flash
    openrouter/dolphin-mistral-24b
    openrouter/nemotron-nano-9b
    openrouter/llama-3.2-3b
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:4000 (Press CTRL+C to quit)
```

If you see a warning about an unrecognised key, check the section below on config placement errors.

### 3.7 Manage the container

```bash
# Stop
docker compose down

# Restart after editing config.yaml or .env
docker compose restart

# View logs (last 100 lines)
docker compose logs --tail=100 litellm

# Follow live logs
docker compose logs -f litellm

# Pull a newer image version and redeploy
docker compose pull
docker compose up -d --force-recreate

# Check image vulnerability scan
# Visit: https://hub.docker.com/hardened-images/catalog/dhi/litellm/images
```

> **Note on cooldown and restarts:** Cooldown state is held in-memory inside the container. A container restart clears it. Since you're not restarting frequently, this is fine. If you later need persistent cooldown state, add Redis as a second service to `docker-compose.yml`. Redis docs: https://docs.litellm.ai/docs/routing

---

## Step 4: Verify the Endpoints

With the container running (`docker compose ps` should show `healthy`), test each provider:

```bash
# Local vLLM
curl http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-litellm-local" \
  -d '{"model": "local/qwen", "messages": [{"role": "user", "content": "Say hello."}], "max_tokens": 20}'

# Groq (should be fastest response)
curl http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-litellm-local" \
  -d '{"model": "groq/llama-3.3-70b", "messages": [{"role": "user", "content": "Say hello."}], "max_tokens": 20}'

# NVIDIA NIM
curl http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-litellm-local" \
  -d '{"model": "nvidia/llama-3.3-70b", "messages": [{"role": "user", "content": "Say hello."}], "max_tokens": 20}'

# OpenRouter
curl http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-litellm-local" \
  -d '{"model": "openrouter/hermes-3-405b", "messages": [{"role": "user", "content": "Say hello."}], "max_tokens": 20}'

# List all available models (and see which are in cooldown)
curl http://localhost:4000/v1/models \
  -H "Authorization: Bearer sk-litellm-local"
```

### Test that fallbacks and cooldown work correctly

LiteLLM has a built-in mechanism to trigger a fallback without actually needing a real failure. The `mock_testing_fallbacks` parameter causes LiteLLM to simulate a failure on the requested model and route to the first entry in its fallback chain. The fallback model runs a real inference call — only the primary failure is mocked.

```bash
# Force a fallback to verify the chain works
curl http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-litellm-local" \
  -d '{
    "model": "groq/llama-3.3-70b",
    "messages": [{"role": "user", "content": "test"}],
    "mock_testing_fallbacks": true
  }'
```

Expected response — note `"model"` in the body shows which fallback was used (`llama-3.1-8b-instant` = `groq/llama-3.1-8b`, the first entry in the fallback chain for `groq/llama-3.3-70b`):

```json
{
  "id": "chatcmpl-9647b0b7-c0ef-4237-bf32-024359087e20",
  "created": 1777331716,
  "model": "llama-3.1-8b-instant",
  "object": "chat.completion",
  "choices": [{
    "finish_reason": "stop",
    "index": 0,
    "message": {
      "content": "Your response appears to be a test. How can I assist you today?",
      "role": "assistant"
    }
  }],
  "usage": {
    "completion_tokens": 16,
    "prompt_tokens": 36,
    "total_tokens": 52
  }
}
```

The `"model"` field in the response body is the clearest confirmation — it shows the actual model that handled the request, not the one you asked for. The real token usage confirms the fallback model ran a genuine completion, not a stub.

---

## Step 5: Monitor Rate Limit Status

### Check which models are healthy

The `/health` endpoint pings every configured model and reports which are reachable. Use the human-readable version for day-to-day checks:

```bash
curl -s http://localhost:4000/health \
  -H "Authorization: Bearer sk-litellm-local" \
  | python3 -c "
import json, sys
h = json.load(sys.stdin)
print(f'Healthy ({h[\"healthy_count\"]}):')
for e in h['healthy_endpoints']:
    print(f'  ✓  {e[\"model\"]}')
print(f'\nUnhealthy ({h[\"unhealthy_count\"]}):')
for e in h['unhealthy_endpoints']:
    err = e.get('error','?').split('\n')[0]
    print(f'  ✗  {e[\"model\"]}')
    print(f'     {err}')
"
```

Expected output with a fully working config:

```
Healthy (27):
  ✓  hosted_vllm/Qwen3.6-35B-A3B-NVFP4
  ✓  groq/llama-3.3-70b-versatile
  ✓  groq/llama-3.1-8b-instant
  ✓  groq/meta-llama/llama-4-scout-17b-16e-instruct
  ✓  groq/qwen/qwen3-32b
  ✓  nvidia_nim/meta/llama-3.3-70b-instruct
  ✓  nvidia_nim/meta/llama-3.1-70b-instruct
  ✓  openrouter/nousresearch/hermes-3-llama-3.1-405b:free
  ✓  openrouter/nvidia/nemotron-3-super-120b-a12b:free
  ✓  openrouter/meta-llama/llama-3.3-70b-instruct:free
  ✓  openrouter/qwen/qwen3-next-80b-a3b-instruct:free
  ✓  openrouter/qwen/qwen3-coder:free
  ✓  openrouter/openai/gpt-oss-120b:free
  ✓  openrouter/openai/gpt-oss-20b:free
  ✓  openrouter/deepseek/deepseek-r1:free
  ✓  openrouter/minimax/minimax-m2.5:free
  ✓  openrouter/nvidia/nemotron-3-nano-30b-a3b:free
  ✓  openrouter/google/gemma-4-31b-it:free
  ✓  openrouter/google/gemma-4-26b-a4b-it:free
  ✓  openrouter/google/gemma-3-27b-it:free
  ✓  openrouter/z-ai/glm-4.5-air:free
  ✓  openrouter/tencent/hy3-preview:free
  ✓  openrouter/inclusionai/ling-2.6-flash:free
  ✓  openrouter/cognitivecomputations/dolphin-mistral-24b-venice-edition:free
  ✓  openrouter/nvidia/nemotron-nano-9b-v2:free
  ✓  openrouter/meta-llama/llama-3.2-3b-instruct:free

Unhealthy (0):
```

If any models appear under `Unhealthy`, the error message on the line below each model name identifies the cause — see the Troubleshooting section for common errors.

The raw JSON response is also available for applications or scripts that need to parse the full endpoint metadata:

```bash
# Raw JSON — for applications and scripts
curl -s http://localhost:4000/health \
  -H "Authorization: Bearer sk-litellm-local"

# Liveness check only — lightweight ping, no per-model inference calls
curl -s http://localhost:4000/health/liveliness \
  -H "Authorization: Bearer sk-litellm-local"
```

### Inspect response headers to see remaining quota

Every Groq response includes rate limit headers whether the request succeeds or fails — you don't need to wait for a 429 to check your remaining budget. Query directly against the Groq API (bypassing LiteLLM) to see the raw headers most clearly, using `max_tokens: 1` to keep token cost negligible:

```bash
# Check llama-3.1-8b-instant quota
curl -s -o /dev/null -v \
  https://api.groq.com/openai/v1/chat/completions \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"llama-3.1-8b-instant","messages":[{"role":"user","content":"hi"}],"max_tokens":1}' \
  2>&1 | grep -i "x-ratelimit\|x-groq"
```

```
< x-groq-region: dls
< x-ratelimit-limit-requests: 14400
< x-ratelimit-limit-tokens: 6000
< x-ratelimit-remaining-requests: 14399
< x-ratelimit-remaining-tokens: 5963
< x-ratelimit-reset-requests: 6s
< x-ratelimit-reset-tokens: 370ms
```

```bash
# Check llama-3.3-70b-versatile quota
curl -s -o /dev/null -v \
  https://api.groq.com/openai/v1/chat/completions \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"llama-3.3-70b-versatile","messages":[{"role":"user","content":"hi"}],"max_tokens":1}' \
  2>&1 | grep -i "x-ratelimit\|x-groq"
```

```
< x-groq-region: dls
< x-ratelimit-limit-requests: 1000
< x-ratelimit-limit-tokens: 12000
< x-ratelimit-remaining-requests: 999
< x-ratelimit-remaining-tokens: 11963
< x-ratelimit-reset-requests: 1m26.4s
< x-ratelimit-reset-tokens: 185ms
```

Groq uses a **rolling window**, not a fixed daily reset at midnight. The `x-ratelimit-reset-requests` value shows when the next slot opens — not when the entire budget resets. For `llama-3.1-8b-instant` the slot interval is ~6 seconds (14,400 slots spread across 86,400 seconds). For `llama-3.3-70b-versatile` it's ~86 seconds (1,000 slots across 86,400 seconds). Capacity trickles back continuously throughout the day.

When `x-ratelimit-remaining-requests` reaches 0, the next request returns a 429. With `cooldown_time: 86400` in your LiteLLM config, LiteLLM will then skip that model for 24 hours and the fallback chain takes over automatically. The 24-hour cooldown is conservative — because the window is rolling, some capacity will return within minutes — but it prevents LiteLLM from hammering a nearly-exhausted model all day.

You can also pipe the headers through LiteLLM directly. LiteLLM passes upstream rate limit headers through on responses:

```bash
curl -s -o /dev/null -v http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-litellm-local" \
  -d '{"model": "groq/llama-3.3-70b", "messages": [{"role": "user", "content": "hi"}], "max_tokens": 1}' \
  2>&1 | grep -i "x-ratelimit\|x-groq"
```

---

## Step 6: Ensure LiteLLM Starts on Boot

Docker Compose with `restart: unless-stopped` already handles daemonization — there's no systemd unit file to write. The container will restart automatically after a crash and after a system reboot, as long as the Docker daemon itself is set to start on boot (which is the default on any system installed with `apt` or the official Docker install script).

Verify Docker is enabled at boot:

```bash
sudo systemctl is-enabled docker
# Expected: enabled
```

If not enabled:

```bash
sudo systemctl enable docker
```

With that in place, the full lifecycle is:

```bash
# Start daemonized
docker compose -f ~/litellm/docker-compose.yml up -d

# Stop (does not remove the container)
docker compose -f ~/litellm/docker-compose.yml down

# Restart after editing config.yaml or .env
docker compose -f ~/litellm/docker-compose.yml restart

# Follow live logs from anywhere
docker compose -f ~/litellm/docker-compose.yml logs -f litellm

# View last 100 lines
docker compose -f ~/litellm/docker-compose.yml logs --tail=100 litellm
```

Add a shell alias to your `~/.bashrc` for convenience:

```bash
echo "alias litellm-logs='docker compose -f ~/litellm/docker-compose.yml logs -f litellm'" >> ~/.bashrc
echo "alias litellm-restart='docker compose -f ~/litellm/docker-compose.yml restart'" >> ~/.bashrc
source ~/.bashrc
```

> **Note on cooldown and restarts:** As noted in Step 3.7, cooldown state is in-memory inside the container. A container restart clears it. Since you're not restarting frequently, this is fine. If you later need persistent cooldown state across restarts, add Redis as a second service to `docker-compose.yml`. Redis docs: https://docs.litellm.ai/docs/routing

---

## Step 7: Configure Hermes Agent

### Option A: Interactive setup

```bash
hermes model
# → "Custom endpoint (self-hosted / VLLM / etc.)"
# → URL: http://localhost:4000/v1
# → API key: sk-litellm-local
# → Model: local/qwen
```

### Option B: Edit config.yaml directly

```bash
nano ~/.hermes/config.yaml
```

```yaml
# ~/.hermes/config.yaml

model:
  provider: custom
  base_url: "http://localhost:4000/v1"
  api_key: "sk-litellm-local"
  default: "local/qwen"
  context_length: 32768    # Set explicitly — LiteLLM doesn't always report this
  max_tokens: 4096

custom_providers:
  - name: litellm
    base_url: "http://localhost:4000/v1"
    api_key: "sk-litellm-local"
    models:
      local/qwen:
        context_length: 32768
      groq/llama-3.3-70b:
        context_length: 128000
      groq/llama-3.1-8b:
        context_length: 128000
      nvidia/llama-3.3-70b:
        context_length: 128000
      openrouter/hermes-3-405b:
        context_length: 131072
      openrouter/deepseek-r1:
        context_length: 64000

# Hermes fallback: if the current model fails mid-session, switch to this
# LiteLLM handles provider-level fallbacks; this is Hermes's own session-level fallback
fallback_model:
  provider: custom
  model: "groq/llama-3.3-70b"
  base_url: "http://localhost:4000/v1"
  key_env: LITELLM_KEY
```

```bash
# Add to ~/.hermes/.env
LITELLM_KEY=sk-litellm-local
FIRECRAWL_API_URL=http://localhost:3002    # Your self-hosted Firecrawl
```

### Switching models inside Hermes sessions

```bash
/model local/qwen              # Local DGX Spark — primary
/model groq/llama-3.3-70b      # Groq 70B (fastest, 1K RPD)
/model groq/llama-3.1-8b       # Groq 8B (fastest, 14.4K RPD — most durable)
/model groq/qwen3-32b          # Groq Qwen3 (60 RPM — highest RPM)
/model nvidia/llama-3.3-70b    # NVIDIA NIM
/model openrouter/hermes-3-405b   # OpenRouter — Hermes 3 405B
/model openrouter/deepseek-r1     # OpenRouter — reasoning model
```

---

## Step 8: Configure OpenWebUI

1. Open OpenWebUI → **Settings** → **Connections** (or **Admin Panel** → **Settings** → **Connections**)
2. Add OpenAI API connection:
   - **API Base URL:** `http://localhost:4000/v1`
   - **API Key:** `sk-litellm-local`
3. **Verify Connection** — all your LiteLLM models will appear in the dropdown

> If OpenWebUI runs in Docker: use `http://host.docker.internal:4000/v1` instead of `localhost`

---

## Step 9: Configure Paperclip

Look for "Custom API", "OpenAI-compatible endpoint", or "API settings":

- **API Base URL:** `http://localhost:4000/v1`
- **API Key:** `sk-litellm-local`
- **Model:** any model name from your LiteLLM config

---

## Step 10: Use LiteLLM in Your Own Applications

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:4000/v1",
    api_key="sk-litellm-local",
)

# Route to any configured provider by model name
for model in ["local/qwen", "groq/llama-3.3-70b", "nvidia/llama-3.1-70b"]:
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": "Hello!"}],
        max_tokens=50,
    )
    print(f"{model}: {response.choices[0].message.content}")
```

For streaming:

```python
stream = client.chat.completions.create(
    model="groq/llama-3.3-70b",    # Groq is fastest for streaming
    messages=[{"role": "user", "content": "Explain CXL memory in 3 sentences."}],
    stream=True,
)
for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

To read upstream rate limit headers from your own code:

```python
# Use the raw response to inspect Groq rate limit headers
response = client.chat.completions.with_raw_response.create(
    model="groq/llama-3.3-70b",
    messages=[{"role": "user", "content": "Hello"}],
    max_tokens=10,
)
remaining = response.headers.get("x-ratelimit-remaining-requests")
reset_in  = response.headers.get("x-ratelimit-reset-requests")
print(f"Groq RPD remaining: {remaining}, resets in: {reset_in}")
completion = response.parse()
```

---

## Checking and Updating Free Model Catalogs

Free-tier model availability changes without notice across all providers. The `update_models.py` script (see Appendix A) handles this automatically across all providers. For quick manual checks:

**OpenRouter** — list genuinely free models:
```bash
curl -s "https://openrouter.ai/api/v1/models" \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  | python3 -c "
import json, sys
models = json.load(sys.stdin)['data']
free = [m for m in models
        if m.get('pricing',{}).get('prompt')=='0'
        and m.get('pricing',{}).get('completion')=='0']
print(f'{len(free)} free models:')
for m in sorted(free, key=lambda x: x['id']):
    print(f'  {m["id"]:<60}  ctx={m.get("context_length","?")}')
"
```

**Groq** — model list and rate limits: https://console.groq.com/docs/models

**NVIDIA NIM** — free endpoints catalog: https://build.nvidia.com/models?filters=nimType%3Anim_type_preview&pageSize=96

---

## Other Free API Providers

The providers configured in this guide were chosen for their combination of model quality, rate limit generosity, and reliability. The following providers also offer free tiers and can be added to your LiteLLM config using the same pattern. None are wired in by default — treat this as a menu to pick from as your needs evolve.

### Google AI Studio (Gemini API)
- **Free tier:** https://ai.google.dev/pricing
- **LiteLLM docs:** https://docs.litellm.ai/docs/providers/gemini
- **Models:** Gemini 2.0 Flash, Gemini 1.5 Flash, Gemma 3
- **Limits:** 15 RPM, 1,500 RPD, 1M TPD on Gemini 2.0 Flash — one of the most generous free tiers available
- **Key:** `GEMINI_API_KEY` from https://aistudio.google.com/apikey
- **Model prefix:** `gemini/gemini-2.0-flash`

### Cerebras Inference
- **Free tier:** https://cerebras.ai/pricing
- **LiteLLM docs:** https://docs.litellm.ai/docs/providers/cerebras
- **Models:** Llama 3.3 70B, Llama 3.1 8B, Qwen3 32B
- **Limits:** Free tier with rate limits; Wafer-Scale Engine hardware delivers inference speeds competitive with Groq
- **Key:** `CEREBRAS_API_KEY` from https://cloud.cerebras.ai
- **Model prefix:** `cerebras/llama3.3-70b`

### Mistral AI (La Plateforme)
- **Free tier:** https://mistral.ai/technology/#pricing
- **LiteLLM docs:** https://docs.litellm.ai/docs/providers/mistral
- **Models:** Mistral Small, Mistral 7B Instruct (free Experiment tier)
- **Limits:** Experimental/free tier available; credit allowance for new accounts
- **Key:** `MISTRAL_API_KEY` from https://console.mistral.ai
- **Model prefix:** `mistral/mistral-small-latest`

### Together AI
- **Free tier:** https://www.together.ai/pricing
- **LiteLLM docs:** https://docs.litellm.ai/docs/providers/togetherai
- **Models:** Llama 4 Scout/Maverick, Qwen3 235B, DeepSeek R1, and many more
- **Limits:** $1 free credit for new accounts; some models have a perpetual free tier. Large and frequently updated catalog.
- **Key:** `TOGETHER_API_KEY` from https://api.together.xyz/settings/api-keys
- **Model prefix:** `together_ai/meta-llama/Llama-4-Scout-17B-16E-Instruct`

### Hugging Face Inference API
- **Free tier:** https://huggingface.co/pricing
- **LiteLLM docs:** https://docs.litellm.ai/docs/providers/huggingface
- **Models:** Hundreds of open models on shared inference endpoints
- **Limits:** Rate-limited free tier; latency can be high under load on shared endpoints
- **Key:** `HUGGINGFACE_API_KEY` from https://huggingface.co/settings/tokens
- **Model prefix:** `huggingface/meta-llama/Llama-3.1-8B-Instruct`

### Cloudflare Workers AI
- **Free tier:** https://developers.cloudflare.com/workers-ai/platform/pricing/
- **LiteLLM docs:** https://docs.litellm.ai/docs/providers/cloudflare_workers
- **Models:** Llama 3.3 70B, Qwen 2.5 Coder, Mistral, Phi, and others
- **Limits:** 10,000 Neurons/day (resets 00:00 UTC). A typical chat request costs 1–5 Neurons. Generous RPM but the daily Neuron budget is the binding constraint.
- **Key:** Cloudflare API token + Account ID (from https://dash.cloudflare.com/profile/api-tokens)
- **Model prefix:** `cloudflare/@cf/meta/llama-3.3-70b-instruct-fp8-fast` with `api_base: https://api.cloudflare.com/client/v4/accounts/YOUR_ACCOUNT_ID/ai/v1`

### Adding Any Provider to LiteLLM

The pattern is identical for every provider. Add an entry to `~/litellm/config.yaml`, add the API key to `~/litellm/.env`, then restart:

```yaml
# Example: Google Gemini 2.0 Flash
- model_name: "gemini/flash-2.0"
  litellm_params:
    model: "gemini/gemini-2.0-flash"
    api_key: "os.environ/GEMINI_API_KEY"
    rpm: 14        # buffer under the 15 RPM free limit
  model_info:
    description: "Google Gemini 2.0 Flash — 1,500 RPD free tier"
```

```bash
# Add the key
echo "GEMINI_API_KEY=your-key-here" >> ~/litellm/.env

# Restart to pick up the new key and model entry
docker compose -f ~/litellm/docker-compose.yml restart

# Verify the model appears
curl http://localhost:4000/v1/models -H "Authorization: Bearer sk-litellm-local" | python3 -m json.tool | grep gemini
```

---

## Appendix A: update_models.py — Automated Model Maintenance

The `update_models.py` script tests all chat-capable models across all configured providers and optionally updates `config.yaml` with only verified working models. It lives in `~/litellm/` alongside your other configuration files.

Download [update_models.py](./update_models.py)

- **Location:** `~/litellm/update_models.py`
- **Keys:** Read automatically from `~/litellm/.env` — no manual `export` needed
- **Safety:** Writes a timestamped backup to `~/litellm/backups/` before any config change; validates YAML before writing; uses atomic rename to avoid partial writes
- **Logs:** Appends to `~/litellm/update_models.log` when run with `--update`
- **Cache:** Persists known-failing models to `~/litellm/model_cache.json` so subsequent runs skip them — keeps routine runs fast (seconds not minutes)

### How the failure cache works

On first run the script tests every model from every provider. Each model that fails with a *permanent* error (HTTP 404 "not found", 403 "access denied", or response body indicating the model is deprecated or unavailable on your account) is written to `model_cache.json`. On every subsequent run those models are skipped entirely.

**What gets cached:** 404, 403, 422 responses and errors containing phrases like "not found", "does not exist", "deprecated", or "not found for account".

**What does NOT get cached:** 429 rate limit errors, 5xx server errors, network timeouts. These are transient — a model that 429s today works fine tomorrow and should never be permanently excluded.

This means the typical weekly cron run tests only genuinely new models (ones that appeared in the provider's list since the last run) plus any that previously returned transient errors.

### Usage

```bash
# Dry run — test new/unknown models, report results, no config changes
python3 ~/litellm/update_models.py

# Test only specific providers
python3 ~/litellm/update_models.py --providers nvidia openrouter

# Print the generated model_list block to stdout (copy-paste ready)
python3 ~/litellm/update_models.py --show

# Show diff and prompt before applying (updates model_list AND prunes fallbacks)
python3 ~/litellm/update_models.py --update

# Apply without prompting (cron mode)
python3 ~/litellm/update_models.py --update --yes

# Validate and prune stale fallback chains only — no model_list changes
python3 ~/litellm/update_models.py --fallback

# Prune fallbacks without prompting
python3 ~/litellm/update_models.py --fallback --yes

# Override vLLM base URL if auto-detection fails
python3 ~/litellm/update_models.py --vllm-base http://192.168.1.100:8000

# Inspect the failure cache
python3 ~/litellm/update_models.py --show-cache

# Clear cache for one provider and retest from scratch (e.g. after account upgrade)
python3 ~/litellm/update_models.py --clear-cache nvidia

# Clear all caches
python3 ~/litellm/update_models.py --clear-cache all

# Ignore cache entirely for this run without clearing it
python3 ~/litellm/update_models.py --retest-failed
```

### What it does per provider

| Provider | List source | Filter | Test method | Concurrency |
|---|---|---|---|---|
| Local vLLM | `GET /v1/models` | None | `POST /v1/chat/completions` | 2 |
| Groq | `GET /openai/v1/models` | Excludes whisper, guard, TTS, speech | `POST /openai/v1/chat/completions` | 4 |
| NVIDIA NIM | `GET /v1/models` | Excludes embed, vision, OCR, safety, etc. | `POST /v1/chat/completions` | 3 |
| OpenRouter | `GET /api/v1/models` | `pricing.prompt == "0"` AND `pricing.completion == "0"`, excludes audio/OCR/vision | `POST /api/v1/chat/completions` | 4 |

Concurrency means multiple models are probed in parallel within each provider. NVIDIA is kept lower (3) to respect its stricter 40 RPM limit.

### Fallback validation

The script parses the `fallbacks` block in `router_settings` and cross-references every model ID against the confirmed working set. Output looks like this:

```
── Fallback validation ──────────────────────────────────────
  ✓  local/qwen → groq/llama-3.1-8b              (working)
  ✓  local/qwen → groq/llama-3.3-70b              (working)
  ✗  local/qwen → openrouter/llama-4-scout         [STALE]
  ✗  nvidia/llama-3.3-70b → openrouter/deepseek-r1 [STALE]

  2 stale model reference(s) found:
    - openrouter/llama-4-scout
    - openrouter/deepseek-r1

  3 working model(s) not in any fallback chain:
    + openrouter/hermes-3-405b
    + openrouter/nemotron-super-120b
    + nvidia/deepseek-v3.2
  Consider adding these to your fallbacks block manually.
```

When stale entries are removed, the chain line is rewritten in-place. If removing a stale target leaves a chain with no remaining targets, the entire chain line is dropped. The rest of the config — comments, formatting, spacing — is preserved exactly.

**What the script does NOT do with fallbacks:**
- Reorder existing chains
- Generate new chains from scratch
- Add newly discovered models to chains automatically

Cross-provider fallback order and priority are editorial decisions that belong to you. The script only removes entries that are provably broken.

### Files written

| File | Purpose |
|---|---|
| `~/litellm/config.yaml` | Updated in-place (atomic rename) |
| `~/litellm/model_cache.json` | Persistent failure cache |
| `~/litellm/update_models.log` | Appended on `--update` runs |
| `~/litellm/backups/config.yaml.bak.YYYYMMDD-HHMMSS` | Backup before every write |

### Optional: run on a schedule with cron

Add a weekly cron job to keep your model list current automatically. The `--update --yes` flags apply changes without prompting; results are logged to `~/litellm/update_models.log`. Thanks to the failure cache, weekly runs complete in seconds rather than minutes.

```bash
# Open your crontab
crontab -e
```

Add one of these lines:

```cron
# Weekly: Monday 08:00 — update model_list, prune fallbacks, restart LiteLLM
0 8 * * 1 python3 ~/litellm/update_models.py --update --yes >> ~/litellm/update_models.log 2>&1 && docker compose -f ~/litellm/docker-compose.yml restart >> ~/litellm/update_models.log 2>&1

# Monthly: 1st of month 02:00 — full retest (clears failure cache first)
0 2 1 * * python3 ~/litellm/update_models.py --retest-failed --update --yes >> ~/litellm/update_models.log 2>&1 && docker compose -f ~/litellm/docker-compose.yml restart >> ~/litellm/update_models.log 2>&1

# Fallback-only check: daily at 06:00 — fast, no probing needed
0 6 * * * python3 ~/litellm/update_models.py --fallback --yes >> ~/litellm/update_models.log 2>&1 && docker compose -f ~/litellm/docker-compose.yml restart >> ~/litellm/update_models.log 2>&1
```

The monthly job uses `--retest-failed` to clear the cache first — a good practice to catch models that became available on your account since the last full scan. The daily `--fallback` job is very fast (no API probing) and catches stale fallback references between weekly model-list updates.

Verify the cron job is registered:
```bash
crontab -l
```

Check the log after a run:
```bash
tail -50 ~/litellm/update_models.log
```

> **Note:** The cron job restarts LiteLLM only if `update_models.py` exits with code 0, meaning at least one working model was found. If all providers fail (e.g. network outage), the config is not touched and the restart is skipped.

### Caveats

- **Fallback chains are validated but not generated.** The script removes stale entries (models no longer in the working set) but does not generate new chains or reorder existing ones. After the script removes a stale entry, review the log and manually add replacement models to maintain your intended fallback depth.
- **New models default to the provider's standard `rpm` value.** If a newly discovered model has known different limits, add an override to `GROQ_LIMITS` in the script or manually edit the entry after the run.
- **OpenRouter Venice rate-limiting** causes all OpenRouter models to appear as failed during the probe if your account has a $0 credit balance — see the Troubleshooting section. These failures are reported as 401 and would be cached. If this happens, add $5 credit first, then run `--clear-cache openrouter` before the next probe.
- **NVIDIA account tier** determines which models are accessible. Models restricted to higher tiers return 404 "not found for account" and are cached permanently. If you upgrade your NVIDIA account, run `--clear-cache nvidia` to discover newly available models.
- **Cloudflare bot detection.** Groq (and potentially other providers) sit behind Cloudflare, which blocks Python's default `User-Agent` (`Python-urllib/3.x`) with HTTP 403 error code 1010. The script sets `User-Agent: litellm-update-models/2.0` on every request to avoid this. If you see `HTTP Error 403: Forbidden` from a provider that works fine with `curl`, this is the cause — verify with `curl -A "Python-urllib/3.13" https://api.groq.com/openai/v1/models` which should also return 403.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `IsADirectoryError: [Errno 21] Is a directory: '/app/config.yaml'` | `config.yaml` didn't exist on the host when `docker compose up` first ran — Docker auto-created it as a directory | `docker compose down`, `sudo rm -rf ~/litellm/config.yaml`, create the file, then `docker compose up -d` |
| `WARNING: Key 'X' is not a valid argument for Router.__init__()` | A setting is in `router_settings` that belongs in `general_settings` (e.g. `enable_health_check_routing`) | Move the flagged key to `general_settings` in `config.yaml`, then `docker compose restart` |
| `update_models.py` returns `HTTP Error 403: Forbidden` with `error code: 1010` for Groq | Cloudflare bot detection blocking Python's default `User-Agent` | Ensure you are running the latest `update_models.py` which sets `User-Agent: litellm-update-models/2.0`. Verify with `curl -A "Python-urllib/3.13" https://api.groq.com/openai/v1/models` — it should also 403 |
| `Connection refused` to vLLM | DGX IP wrong or vLLM not bound to `0.0.0.0` | Add `--host 0.0.0.0` to vLLM startup; verify DGX_IP |
| Tool calls appear as raw JSON | vLLM missing tool-call flags | Restart vLLM with `--enable-auto-tool-choice --tool-call-parser hermes` |
| NVIDIA returns 401 | Wrong env var name | Must be `NVIDIA_NIM_API_KEY`, not `NVIDIA_API_KEY` |
| NVIDIA model 404 in `/health` | Model ID removed or renamed by NVIDIA | Run the NVIDIA model listing command to find the current ID; remove the stale entry from `config.yaml` and restart |
| OpenRouter 401 "User not found" on direct API call | Invalid or revoked key | Regenerate at https://openrouter.ai/settings/keys, update `~/litellm/.env`, restart container |
| OpenRouter 401 "User not found" via LiteLLM `/health` but direct API works | Key in `~/litellm/.env` differs from shell `$OPENROUTER_API_KEY` | Run `grep OPENROUTER_API_KEY ~/litellm/.env` and `echo $OPENROUTER_API_KEY` to compare; copy the working value into `.env` and restart |
| OpenRouter 401 "User not found" via LiteLLM but direct `curl` returns 429 with `provider_name: Venice` | OpenRouter is misreporting a backend 429 as a 401 — your key is valid but all free requests are being routed to Venice which is rate-limiting your account | This is an OpenRouter backend routing issue, not an auth failure. **Add a minimum $5 credit balance** at https://openrouter.ai/settings/credits — with $0 balance, OpenRouter routes all free model requests through Venice exclusively; any credit balance unlocks additional backend providers and resolves the rate-limiting |
| All OpenRouter free models fail even after adding credits | Credits not yet reflected or container not restarted | Wait a few minutes for OpenRouter to recognise the new balance, then restart the container: `docker compose -f ~/litellm/docker-compose.yml restart` |
| OpenRouter 429 | Free model per-provider rate limit hit | Multiple free models in config act as independent fallbacks; LiteLLM will route around the rate-limited model automatically |
| OpenWebUI can't reach LiteLLM | Docker network isolation | Use `http://host.docker.internal:4000/v1` |
| `Context limit: 4096` in Hermes | Auto-detection wrong | Set `context_length` explicitly in `~/.hermes/config.yaml` |
| LiteLLM container won't start | Config path wrong or permissions | Check `docker compose logs litellm`; ensure `config.yaml` exists at `~/litellm/config.yaml` and is readable |
| Config changes not picked up | Container not restarted | Run `docker compose restart` after editing `config.yaml` or `.env` |
| Model in cooldown longer than expected | `cooldown_time: 86400` active | Expected behavior — model hit daily limit; it resets after 24h or on LiteLLM restart |

---

## Frequently Asked Questions

### General

**Q: What is LiteLLM and why use it as a gateway?**  
A: LiteLLM is an open-source proxy that translates any OpenAI-compatible API call into provider-specific formats. It gives every application a single, stable endpoint regardless of which backend model actually handles the request. You get unified auth, fallback routing, rate-limit tracking, and health checks without modifying your application code.

**Q: Do I need a credit card or spending budget to follow this guide?**  
A: Not for Groq or OpenRouter free models. Groq provides rate-limited access with no card required. OpenRouter's free models (those with `pricing.prompt == "0"` and `pricing.completion == "0"`) are genuinely zero-cost. NVIDIA NIM gives you 1,000 free credits on signup (up to 5,000 by request). The only cost to consider is Docker Hub Hardened Image access (requires a Docker Hub account) and an optional $5 minimum credit balance on OpenRouter to unlock additional backend providers and avoid Venice-specific rate limiting.

**Q: I don't have a DGX Spark or local GPU. Can I still follow this guide?**  
A: Yes. The local vLLM backend is optional. Remove the `local/qwen` entry from `model_list` and adjust the fallback chains to start with Groq or NVIDIA NIM as the primary. Everything else in the guide applies unchanged.

**Q: Can I add providers not listed here (Google Gemini, Cerebras, Together AI, etc.)?**  
A: Yes — see the [Other Free API Providers](#other-free-api-providers) section. The pattern is the same: add a `model_list` entry with the correct prefix and API key environment variable, add the key to `.env`, and restart. See also the [Adding Any Provider to LiteLLM](#adding-any-provider-to-litellm) subsection for a worked example.

---

### Rate Limits and Fallbacks

**Q: How does LiteLLM know when a model has hit its daily limit?**  
A: It doesn't read provider headers proactively. Instead, when a model returns a 429 after retries, LiteLLM triggers its cooldown mechanism. With `allowed_fails: 3` and `cooldown_time: 86400` in `router_settings`, after three consecutive failures the model is skipped for 24 hours and the fallback chain takes over automatically.

**Q: Why set `cooldown_time: 86400` (24 hours)?**  
A: Free-tier daily limits don't reset at a predictable minute — Groq uses a rolling window. A short cooldown (e.g. 60 seconds) causes LiteLLM to retry an exhausted model repeatedly, burning retries and adding latency. 24 hours is conservative and safe: it guarantees the model is skipped for the entire day. Because the window is rolling, some capacity trickles back within minutes — but the conservative cooldown prevents the proxy from hammering a nearly-exhausted endpoint all day.

**Q: What happens if all fallback models are also exhausted?**  
A: LiteLLM returns a 429 to the caller. The `update_models.py` script's multi-provider setup is designed to make this scenario very unlikely — you have independent rate-limit budgets across Groq, NVIDIA NIM, OpenRouter, and local vLLM. Exhausting all of them simultaneously would require sustained high traffic across all providers simultaneously.

**Q: Does cooldown state survive a container restart?**  
A: No. Cooldown is held in-memory and resets on restart. This is acceptable for most use cases — a restart clears the slate and lets all models be tried again. If you need persistent cooldown state, add Redis as a second service in `docker-compose.yml`. See the [LiteLLM routing docs](https://docs.litellm.ai/docs/routing) for Redis configuration.

**Q: How do I test that fallbacks are working without waiting for a real failure?**  
A: Use the `mock_testing_fallbacks` parameter in your request body. LiteLLM simulates a failure on the requested model and routes to the first entry in the fallback chain. The fallback model runs a real inference call. See [Step 4](#step-4-verify-the-endpoints) for the exact `curl` command and expected response.

---

### Model Management

**Q: Free-tier models keep disappearing. How do I keep my config current?**  
A: Run `update_models.py --update` periodically. It probes every configured model, removes stale entries from `model_list`, and prunes broken references from your fallback chains. A failure cache ensures subsequent runs skip permanently-failed models and complete in seconds. Set up the optional cron jobs in [Appendix A](#appendix-a-update_modelspy--automated-model-maintenance) to run this automatically.

**Q: What does `update_models.py` do to my fallback chains?**  
A: It removes model references that are no longer in the working set (stale entries). It does **not** reorder chains, generate new chains, or automatically add newly discovered models to chains. Fallback ordering is an editorial decision left to you. After any automated run, review the log and manually add replacement models if needed to maintain your intended fallback depth.

**Q: How do I discover new free models on OpenRouter?**  
A: Run the `curl` command in the [OpenRouter rate limits section](#openrouter) to list all models where `pricing.prompt == "0"` and `pricing.completion == "0"`. The `update_models.py --show` command also prints the full generated `model_list` block for copy-paste. Re-run either command periodically — the free catalog changes frequently.

**Q: Why does `update_models.py` use its own User-Agent header?**  
A: Groq (and some other providers) sit behind Cloudflare, which blocks Python's default `User-Agent` (`Python-urllib/3.x`) with HTTP 403. The script sets `User-Agent: litellm-update-models/2.0` on every request to avoid this. If you see `HTTP Error 403: Forbidden` from Groq in the script but `curl` works fine, verify with `curl -A "Python-urllib/3.13" https://api.groq.com/openai/v1/models` — it should also return 403, confirming the cause.

---

### OpenRouter Specifics

**Q: OpenRouter returns 401 "User not found" but my API key is valid. What is happening?**  
A: With a $0 credit balance, OpenRouter routes all free model requests through a single backend provider (Venice). Venice rate-limits aggressively and OpenRouter misreports these 429s as 401 errors. Add a minimum $5 credit balance at https://openrouter.ai/settings/credits — this unlocks additional backend providers. Your free models remain zero-cost; the credit balance is only consumed if you use paid models.

**Q: What is the `?free_only=true` query parameter on OpenRouter's API? Should I use it?**  
A: No. Despite its name, `?free_only=true` returns models with *any* free routing path, including paid frontier models that have a free community-contributed route. The reliable filter is `pricing.prompt == "0"` AND `pricing.completion == "0"` on each model object. Always use the pricing field filter.

---

### NVIDIA NIM Specifics

**Q: Why does NVIDIA NIM return no pricing metadata in the `/v1/models` response?**  
A: The NVIDIA NIM API schema includes only `id`, `object`, `created`, `owned_by`, `root`, `parent`, `max_model_len`, and a `permission` array. There is no pricing or tier field. The "Preview" (free) classification exists only in the website UI. The only reliable way to determine which models are accessible on your account is to probe each one — which is exactly what `update_models.py` does.

**Q: The NVIDIA model env var isn't working. What's the correct name?**  
A: The variable must be `NVIDIA_NIM_API_KEY`. Using `NVIDIA_API_KEY` (without `_NIM_`) will result in 401 errors. This is a common mistake documented in the [Troubleshooting](#troubleshooting) table.

---

### vLLM and Local Model

**Q: Why do tool calls appear as raw JSON text instead of being executed?**  
A: vLLM must be started with `--enable-auto-tool-choice --tool-call-parser hermes`. Without these flags, tool call responses are returned as text rather than parsed into the OpenAI function-calling schema that Hermes Agent expects. Restart vLLM on your DGX Spark with these flags and reconnect.

**Q: How do I find the exact model name to use in `config.yaml`?**  
A: Query the vLLM `/v1/models` endpoint: `curl http://DGX_IP:8000/v1/models`. The `id` field in the response is the value to use as `hosted_vllm/<id>` in `litellm_params.model`.

**Q: LiteLLM can't reach my vLLM instance. What should I check?**  
A: Confirm vLLM was started with `--host 0.0.0.0` (not `127.0.0.1`), verify the IP address in `config.yaml` matches your DGX Spark's actual IP, and confirm port 8000 is not firewalled between the two machines.

---

### For AI Agents

**Q: What is the single endpoint URL and auth method for this gateway?**  
A: `http://localhost:4000/v1` with `Authorization: Bearer sk-litellm-local`. The interface is fully OpenAI-compatible — use the standard `openai` Python client with `base_url="http://localhost:4000/v1"` and `api_key="sk-litellm-local"`.

**Q: How should an agent select a model for a given task?**  
A: Use `local/qwen` as the primary. It is unlimited, private, and lowest-latency. For tasks requiring a larger context window or higher throughput, use `groq/llama-3.3-70b` (fast, 128K context) or `nvidia/llama-3.3-70b` (frontier class). For reasoning-heavy tasks, `openrouter/deepseek-r1` is available. For code, `openrouter/qwen3-coder` is optimized for that workload. LiteLLM's fallback chains ensure that if your requested model is unavailable, the next best option is tried automatically without any change to your request.

**Q: How does an agent know which models are currently available?**  
A: `GET http://localhost:4000/v1/models` with `Authorization: Bearer sk-litellm-local` returns the full list of configured models. `GET http://localhost:4000/health` returns healthy and unhealthy endpoints with error details.

**Q: What error codes should an agent handle when talking to this proxy?**  
A: - `401` — Invalid or missing `Authorization` header. Check the bearer token matches `LITELLM_MASTER_KEY` in `.env`.  
- `429` — All models in the fallback chain are exhausted or in cooldown. Retry after a delay or switch to a different model name.  
- `503` — LiteLLM proxy is not running. Check `docker compose ps` and restart if needed.  
- `504` — Upstream timeout (>120 seconds). The model is too slow or the request is too large. Reduce `max_tokens` or switch to a faster provider.

**Q: Does the proxy support streaming responses?**  
A: Yes. Pass `"stream": true` in the request body. LiteLLM forwards Server-Sent Events (SSE) from the upstream provider. All configured providers support streaming.

---

## Quick Reference

| Component | URL / Location | Key |
|---|---|---|
| LiteLLM proxy | `http://localhost:4000/v1` | `sk-litellm-local` |
| Docker Compose file | `~/litellm/docker-compose.yml` | — |
| LiteLLM config | `~/litellm/config.yaml` (host) → `/app/config.yaml` (container) | — |
| LiteLLM env | `~/litellm/.env` | — |
| LiteLLM image | `dhi.io/litellm:1` (Docker Hub Hardened) | — |
| Image catalog | https://hub.docker.com/hardened-images/catalog/dhi/litellm | — |
| LiteLLM routing docs | https://docs.litellm.ai/docs/routing | — |
| LiteLLM fallback docs | https://docs.litellm.ai/docs/proxy/reliability | — |
| LiteLLM health check docs | https://docs.litellm.ai/docs/proxy/health_check_routing | — |
| Hermes config | `~/.hermes/config.yaml` | — |
| Hermes env | `~/.hermes/.env` | — |
| vLLM (DGX Spark) | `http://DGX_IP:8000/v1` | none |
| Firecrawl | `http://localhost:3002` | none |
| NVIDIA NIM API | `https://integrate.api.nvidia.com/v1/` | `NVIDIA_NIM_API_KEY` |
| NVIDIA model catalog | https://build.nvidia.com/explore/discover | — |
| NVIDIA API docs | https://docs.api.nvidia.com/nim/reference/ | — |
| OpenRouter API | `https://openrouter.ai/api/v1` | `OPENROUTER_API_KEY` |
| OpenRouter free models | https://openrouter.ai/models?supported_parameters=free | — |
| OpenRouter usage | https://openrouter.ai/activity | — |
| Groq API | `https://api.groq.com/openai/v1` | `GROQ_API_KEY` |
| Groq rate limits doc | https://console.groq.com/docs/rate-limits | — |
| Groq usage dashboard | https://console.groq.com/dashboard | — |

---

## Summary and Conclusion

You now have a production-ready, four-provider LiteLLM gateway with intelligent rate-limit awareness and automatic fallback:

1. **Local vLLM on DGX Spark** — unlimited, zero cost, maximum privacy. Always the primary destination.
2. **Groq** — the fastest cloud inference available (LPU hardware). Free within rolling rate limits, no credit card required. `llama-3.1-8b-instant` carries 14,400 requests/day — the most durable individual fallback in this stack.
3. **NVIDIA NIM** — frontier-class models accessible via a monthly free credit allocation. A strong option when request quality matters more than throughput.
4. **OpenRouter** — the widest catalog of genuinely free (zero-cost) models. With dozens of `:free` models each carrying an independent daily budget, this tier provides the deepest fallback coverage.

Rate-limit behavior is managed through three coordinated mechanisms:
- `rpm` and `tpm` declared per model so LiteLLM preemptively avoids over-scheduling before a 429 is issued
- `cooldown_time: 86400` so any model that hits its daily wall is skipped for 24 hours rather than retried continuously
- Ordered fallback chains that prefer high daily-budget models first within each provider tier

All upstream API keys are isolated in `~/litellm/.env`. Every consuming application — Hermes Agent, OpenWebUI, Paperclip, or your own code — uses a single URL (`http://localhost:4000/v1`) with a single local key. Adding a new provider or model is a one-line `config.yaml` edit and a container restart.

The `update_models.py` script provides a maintenance loop: probe providers for working models, remove stale config entries, prune broken fallback references, and optionally restart. Configured as a weekly cron job, it keeps your model list accurate without manual effort — even as free-tier catalogs change without notice.

The architecture is intentionally minimal. There is no database, no persistent external state, and no proprietary tooling. If you outgrow the free tiers or want to consolidate spending, adding a paid provider follows the identical pattern as every free provider in this guide.
