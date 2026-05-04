---
title: "How To Run ZeroClaw in Docker with local LLMs (Qwen3 on an NVIDIA DGX Spark)"
meta_title: "ZeroClaw + LiteLLM + vLLM in Docker: Local Agent Setup"
description: "Step-by-step guide to running ZeroClaw in Docker against local LLMs served by vLLM and routed through LiteLLM. Includes the docker-compose.yml, the config.toml fixes for ZeroClaw issue #6123 (default_model fallback), and a troubleshooting / FAQ section."
image: "featured_image.webp"
date: 2026-05-01T15:00:00-06:00
categories: ["AI"]
author: "Steve Scargall"
tags: ["ZeroClaw", "LiteLLM", "vLLM", "Qwen3", "Qwen3.6", "DGX Spark", "GB10", "Docker", "Docker Compose", "local LLM", "agent runtime", "OpenAI-compatible", "Firecrawl"]
draft: false
reading_time: 8
---

[ZeroClaw](https://github.com/zeroclaw-labs/zeroclaw) is an open-source agent runtime. By default it expects a frontier model API key such as Claude, OpenAI, etc. This guide shows how to use a **local Qwen3.6** model served by **vLLM** on an NVIDIA DGX Spark, routed through **LiteLLM**, with ZeroClaw and Firecrawl running in Docker on a separate host.

It also documents the onboarding bug I hit on a fresh install in v0.7.4 — ZeroClaw issue [#6123](https://github.com/zeroclaw-labs/zeroclaw/issues/6123) — and the config-only workaround.

## Topology

Here is my environment.

The `AIDev` host runs Ubuntu Linux 25.10 with Docker. I configured [LiteLLM](https://litellm.ai/) to route `local/qwen` to the `Qwen3.6-35B-A3B-NVFP4` model running in [vLLM](https://github.com/vllm-project/vllm) on the DGX Spark. LiteLLM also offers many models via NVIDIA, OpenRouter, and Groq, for other uses. [Firecrawl](https://firecrawl.dev/) is a web crawler that can be used to crawl websites and extract information from them, and can also be run in Docker.

```
DGX Spark (dgx-spark)                          AIDev (Docker host)
┌───────────────────────────────┐             ┌──────────────────────────----─────-─┐
│ vLLM :8000                    │ ◄── LAN ──► │ LiteLLM :4000  (model: local/qwen)  │
│   Qwen3.6-35B-A3B-NVFP4       │             │ ZeroClaw :42617                     │
└───────────────────────────────┘             │ Firecrawl :3002                     │
                                              └─────────────────────────────────────┘
```

Why this layout: LiteLLM is the single place where model names, API keys, and endpoints are mapped. ZeroClaw speaks the OpenAI Chat Completions wire format, so it only needs one URL (`http://host.docker.internal:4000/v1`) and one model (`local/qwen`)  in the config file. I can quickly and easily switch models provided by LiteLLM or use other models directly.

## Prerequisites

- vLLM already serving on the LAN (any OpenAI-compatible model)
- LiteLLM already running and exposing your model under an alias (e.g. `local/qwen`)
- Docker + Docker Compose on the host that will run ZeroClaw
- A working directory (e.g. `~/zeroclaw`)
- A LiteLLM API key
- A Firecrawl API key

A quick host-side sanity check:

Note: Replace `<your-litellm-api-key>` with your actual LiteLLM API key, and replace `local/qwen` with the target model name in LiteLLM.

```bash
curl -s http://localhost:4000/v1/chat/completions \
  -H "Authorization: Bearer <your-litellm-api-key>" \
  -H "Content-Type: application/json" \
  -d '{"model":"local/qwen","messages":[{"role":"user","content":"Say OK"}]}'
```

You should get a normal `chat.completion` response that says "OK". If not, fix the LiteLLM setup first.

## Step 1

Create a file named `.env` in the same directory as `docker-compose.yml` with the following contents.

```bash
# .env
LITELLM_BASE_URL_CONTAINER=http://host.docker.internal:4000/v1
LITELLM_API_KEY=<your-litellm-api-key>
FIRECRAWL_API_KEY=<your-firecrawl-api-key>
```

`host.docker.internal` is how a container reaches a service running on the host. Combined with `extra_hosts: ["host.docker.internal:host-gateway"]` in compose, this works on Linux without exposing your container to the public LAN.

## Step 2

Create a file named `docker-compose.yml` in the same directory as `.env` with the following contents.

```yaml
services:
  zeroclaw:
    image: ghcr.io/zeroclaw-labs/zeroclaw:latest
    container_name: zeroclaw
    restart: unless-stopped
    ports: ["42617:42617"]
    environment:
      ZEROCLAW_ALLOW_PUBLIC_BIND: "1"
      ZEROCLAW_PROVIDER: litellm
      ZEROCLAW_MODEL: "local/qwen"
      ZEROCLAW_API_KEY: "${LITELLM_API_KEY}"
      FIRECRAWL_API_URL: "http://host.docker.internal:3002"
      FIRECRAWL_API_KEY: "${FIRECRAWL_API_KEY:-}"
    volumes:
      - ./zeroclaw-data:/zeroclaw-data
    extra_hosts: ["host.docker.internal:host-gateway"]
```

The three `ZEROCLAW_*` env vars are not strictly required once `config.toml` is correct, but they survive a re-run of `zeroclaw onboard` (which on a fresh install can write a broken config — see the bug section).

## Step 3

Run the following commands to bring up the container and run the onboard wizard:

```bash
docker compose up -d
docker compose exec zeroclaw zeroclaw onboard
```

Walk through the wizard. When asked about a provider, pick something OpenAI-compatible and point it at `http://host.docker.internal:4000/v1` with the `LITELLM_API_KEY` value. Pick `local/qwen` as the model.

The wizard currently has rough edges with custom OpenAI-compatible endpoints (issue [#6206](https://github.com/zeroclaw-labs/zeroclaw/issues/6206)). It's fine — we hand-correct the config in the next step.

## Step 4

The ZeroClaw container image is distroless (no `cat`, no `sh`). To read or edit the config from the host, use a helper container:

```bash
# read
docker run --rm -v $(pwd)/zeroclaw-data:/data alpine \
  cat /data/.zeroclaw/config.toml

# write back (preserve ownership)
docker run --rm -v $(pwd)/zeroclaw-data:/data -v /tmp/config.toml:/in/config.toml:ro \
  alpine sh -c "cp /in/config.toml /data/.zeroclaw/config.toml \
                && chown 65534:65534 /data/.zeroclaw/config.toml \
                && chmod 600 /data/.zeroclaw/config.toml"
```

Make the `[providers]` section look like this:

```toml
[providers]
fallback = "litellm"

[providers.models]

[providers.models.litellm]
api_key = "enc2:..."                                        # leave whatever onboard wrote
max_tokens = 4096
temperature = 0.7
timeout_secs = 120
base_url = "http://host.docker.internal:4000/v1"
name = "LiteLLM-AIDev"
wire_api = "chat_completions"
model = "local/qwen"

[providers.models.vllm]
api_key = "enc2:..."
max_tokens = 4096
temperature = 0.7
timeout_secs = 120
wire_api = "chat_completions"
model = "Qwen3.6-35B-A3B-NVFP4"
name = "vLLM-DGX"
base_url = "http://dgx-spark:8000/v1"
```

Things to delete if onboard wrote them: a `[providers.models.default]` block (orphan), and any `api_url = "http://:host.docker.internal4000/v1"` line (a known typo bug — the field name is `base_url`).

While you're in there, enable Firecrawl. The following example shows how to enable it with an API key from an environment variable for a locally hosted Firecrawl server at `http://host.docker.internal:3002`. You can replace the environment variable with an actual API key if you have one, or you can remove the `api_key_env` line to use an API key from your `.env` file. For more information about Firecrawl, see [Enable web scraping](https://docs.zeroclaw.com/features/web-browsing).

```toml
[web_fetch]
allowed_private_hosts = ["host.docker.internal"]

[web_fetch.firecrawl]
enabled = true
api_key_env = "FIRECRAWL_API_KEY"
api_url = "http://host.docker.internal:3002/v1"
mode = "scrape"
```

Recreate the container so env changes take effect, then restart for config reload:

```bash
docker compose up -d --force-recreate zeroclaw
```

## Step 5

This will check the configuration and ensure that the provider is set up correctly by running `zeroclaw doctor` within the container.

```bash
docker compose exec zeroclaw zeroclaw doctor
```

Expected highlights:

```
[config]
  ✅ provider "litellm" is valid
  ✅ API key configured
  ✅ default model: local/qwen
```

Then a real round-trip:

```bash
docker compose exec zeroclaw zeroclaw agent -m "Reply OK and nothing else."
# → OK
```

If you see `OK`, ZeroClaw is talking to your local Qwen via LiteLLM. Congratulations! You now have a local Qwen-powered agent running in Docker that can crawl the web.

## The bug: ZeroClaw issue #6123 (open at time of writing)

Symptom on a fresh install — even with `ZEROCLAW_PROVIDER` and the right config — the agent fails with:

```
provider=openai model=anthropic/claude-sonnet-4 attempt 1/3: non_retryable;
error=OpenAI API error (401 Unauthorized): Incorrect API key provided ...
```

Root cause is in `crates/zeroclaw-runtime/src/agent/loop_.rs` (~lines 2248-2257): when no `-M` flag is passed and the resolved fallback provider has no `model` field set in `config.providers.models`, ZeroClaw silently falls through to a **hardcoded `"anthropic/claude-sonnet-4"`** string. Combined with the wrong fallback provider being picked, requests go to the wrong endpoint with the wrong model name.

Tracking:

- [#6123](https://github.com/zeroclaw-labs/zeroclaw/issues/6123) — *default_model issue on fresh install* (P1, milestone v0.7.5)
- [#6206](https://github.com/zeroclaw-labs/zeroclaw/issues/6206) — *Onboarding fails for custom OpenAI-compatible provider*
- [#6092](https://github.com/zeroclaw-labs/zeroclaw/pull/6092), [#6099](https://github.com/zeroclaw-labs/zeroclaw/pull/6099), [#6155](https://github.com/zeroclaw-labs/zeroclaw/pull/6155), [#6215](https://github.com/zeroclaw-labs/zeroclaw/pull/6215) — fixes in flight

Workaround (this guide): set both `[providers] fallback = "litellm"` **and** `[providers.models.litellm].model = "local/qwen"` in `config.toml`, and keep `ZEROCLAW_PROVIDER` / `ZEROCLAW_MODEL` in compose as belt-and-braces in case onboard rewrites the config. Once v0.7.5 ships you can drop the env vars.

## Troubleshooting

**`401 Unauthorized` from `api.openai.com`.** ZeroClaw is sending requests to the real OpenAI. The fallback resolved to `openai`, not `litellm`. Verify with `docker inspect zeroclaw --format '{{.Config.Env}}'` that `ZEROCLAW_PROVIDER=litellm` is actually set on the running container, then check `[providers] fallback` in `config.toml`. Recreate the container after editing compose: `docker compose up -d --force-recreate zeroclaw`.

**`model 'anthropic/claude-sonnet-4' not found`.** You hit issue #6123. Make sure `[providers.models.<your-fallback-provider>].model` is set in `config.toml`.

**`exec failed: cat / sh: not found`.** Image is distroless. Use a helper alpine container as shown in step 4, not `docker compose exec`.

**`zeroclaw doctor` shows `live model listing is not supported`.** Cosmetic. The doctor cannot enumerate models from local OpenAI-compatible endpoints. If `agent -m` works, you're fine.

**`zeroclaw doctor` shows a phantom `custom:http://host.docker.internal:4000/v1` provider.** Cosmetic. Doctor synthesizes a `custom:<url>` entry from the litellm `base_url`.

**Container can't reach LiteLLM.** Confirm `extra_hosts: ["host.docker.internal:host-gateway"]` is set, then from a debug container:

```bash
docker run --rm --add-host=host.docker.internal:host-gateway curlimages/curl \
  -sS http://host.docker.internal:4000/v1/models -H "Authorization: Bearer <your-litellm-api-key>"
```

**Hostname for vLLM doesn't resolve from container.** If your DNS doesn't serve `*.localdomain` to containers, use the IP in `[providers.models.vllm].base_url` or add an `extra_hosts` entry.

## FAQ

**Why route through LiteLLM instead of pointing ZeroClaw at vLLM directly?**
LiteLLM gives you one stable URL and one alias (`local/qwen`) regardless of how many models or backends you swap in. ZeroClaw and any other OpenAI-compatible client all use the same config. Easier to operate, easier to log, easier to rate-limit.

**Can I skip LiteLLM and point ZeroClaw at vLLM directly?**
Yes — set `[providers.models.litellm].base_url = "http://dgx-spark:8000/v1"` and use whatever model name vLLM serves (e.g. `Qwen3.6-35B-A3B-NVFP4`). You lose central routing.

**Why is the API key encrypted as `enc2:...` in `config.toml`?**
ZeroClaw encrypts secrets at rest using a per-install key in `.zeroclaw/.secret_key`. The plaintext `LITELLM_API_KEY` env var is the override path, which is why we still set `ZEROCLAW_API_KEY` in compose.

**Does ZeroClaw need a real OpenAI key or Anthropic key?**
No. The `[providers.models.openai]` block left over from onboarding is harmless as long as `[providers] fallback` does not point at `openai`.

**Can I use Ollama or llama.cpp instead of vLLM?**
Yes. Either expose them as a model in LiteLLM, or wire them as a custom OpenAI-compatible provider directly. Be aware of issues #6180 (llama.cpp) and #6206 (custom-OpenAI onboarding).

**How do I add Firecrawl for web scraping?**
Set `[web_fetch.firecrawl] enabled = true`, point `api_url` at your local Firecrawl (`http://host.docker.internal:3002/v1`), and set `FIRECRAWL_API_KEY` in compose (empty string is fine for self-hosted Firecrawl with no auth).

**When can I drop the `ZEROCLAW_PROVIDER` / `ZEROCLAW_MODEL` env-var workaround?**
After ZeroClaw v0.7.5 ships with the fix for #6123. Until then, keep them in compose so a fresh `onboard` can't strand you on the hardcoded fallback.
