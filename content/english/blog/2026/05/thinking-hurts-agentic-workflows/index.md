---
title: "Is Thinking Mode Affecting Your Agentic Workflows?"
meta_title: "Agentic Workflows and Reasoning Models: Thinking Mode Pitfalls and Local LLM Surprises"
description: "Discover how reasoning mode in local LLMs like Qwen3 and Gemma can impact agentic workflows, causing silent failures and unexpected token usage. Learn how cloud APIs hide this behavior and how to properly configure your local model serving setup to avoid common pitfalls."
image: "featured_image.webp"
date: 2026-05-07T10:00:00-06:00
categories: ["AI"]
author: "Steve Scargall"
tags: ["local LLM", "agent runtime", "reasoning models", "thinking mode", "max_tokens", "Qwen3", "Gemma3", "GLM-4.7", "DeepSeek-R1", "Hermes-Agent", "ZeroClaw", "OpenClaw", "LangGraph", "AutoGen", "CrewAI", "vLLM", "SGLang", "llama.cpp", "OpenAI-compatible API", "DGX Spark", "GB10", "model serving", "LiteLLM"]
draft: false
reading_time: 8
---

I jumped on the trend of running local LLMs and agents and was having a lot of fun until my agents kept failing, timing out, and just stopping without any obvious reason. I tried PaperClip + ZeroClaw, PaperClip + Hermes-Agent, and Hermes-Agent + Hermes-Workspace with Qwen 3.6 and Gemma 4 models (various sizes and quantization levels). All of them failed in the same way at some point in the workflow with almost nothing reported in the logs to indicate what was happening. Some tasks completed without any problem, but most did not, often leaving me to wonder what was going on. After many hours of debugging and reading many forums, I finally found that this was a model serving configuration trap that catches many people the first time they self-host a reasoning model.

YouTube influencers who show you how to install and run these agents in under 5 minutes never mention this problem, because they only show you the happy path and use cloud APIs (OpenAI, Anthropic, Google, etc.) where the reasoning (and the associated token usage) is hidden from you.

If you are running local agents with locally hosted models and noticed your agents or tasks timing out after a minute or so with `null` content, partial content, or your agents hanging mid-loop — you're not alone. It's not a bug in your agent. It's more likely a model serving configuration trap that catches almost everyone who self-hosts reasoning/thinking models. The same problem rarely surfaces on cloud APIs (OpenAI, Anthropic, Google, etc.), but the reasons for *that* are interesting too, and I'll get to them.

This post is about what's actually happening inside your model server while your agent stares at a blank string, why the failure mode is *silent* rather than loud, and what you can do about it without giving up reasoning capability altogether.

## TL;DR

Reasoning-capable models — Qwen3 family, Gemma, GLM-4.5/4.6/4.7, DeepSeek-R1, gpt-oss, and others — produce hidden internal "thinking" blocks before emitting any user-visible content. These blocks are commonly stripped from the final response (the `content` field) by reasoning parsers and routed into a separate `reasoning_content` field. However, each user or agent input prompt received by the LLM has a token limit. If this limit (`max_tokens` or `max_model_len`) is consumed *during* the thinking phase, you get a successful HTTP 200 with `content: null` and `finish_reason: "length"` — and your agent has no idea why. Depending on the agent it may give up, accept the empty response, retry, or throw an error. All of which can leave you scratching your head for hours wondering what on earth is going on. If you have LLM proxies, such as LiteLLM, they can also have their own retry or fallback logic that can make it even harder to determine what is going on. In my case, LiteLLM's retry and fallback logic caused it to retry the request, which made the problem even harder to debug, as the error was only reported after all retries were exhausted - up to 10 minutes later! 

The fix is two parts: (1) control thinking at the agent or proxy layer, not at the server, and (2) size `max_tokens` based on whether thinking is on for that specific call.

A simple `curl` command may be all it takes to confirm the issue, in your own environment.

```bash
time curl -s http://192.168.1.251:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen3.6-27B-FP8",
    "messages": [{"role": "user", "content": "Write a 500-word essay about how ai agents can change the world."}]
  }' | jq '.choices[0]'
```

Let's dive in...

**This is not a model, agent, or framework specific problem**

I want to be direct about scope before going further, because it's tempting to read symptoms as model-specific or framework-specific quirks. They aren't.

Anything where the model server config includes a `--reasoning-parser` flag, or where the model card mentions "thinking mode," "reasoning mode," "deliberation tokens," or "internal monologue," is in scope. 

In my case, I was running [Qwen3.6 27B FP8](https://huggingface.co/Qwen/Qwen3.6-27B), but I had previously seen identical behavior with Gemma4 and stopped using it before doing the deep investigation. Different model, same trap.

Affected agents and harnesses include any framework that wraps an OpenAI-compatible API, including:

- ZeroClaw, OpenClaw, Hermes-Agent, PaperClip
- Custom agents written against an OpenAI-compatible API

The trap isn't in the agent code. It's in the gap between *what the model produced* (which the API correctly reports as "successful but truncated") and *what the agent expected* (a non-empty string in the `content` field).

## My observations

I'm going to try and explain what is happening and show you examples of what I saw. I will also suggest how you can avoid the problem. I'll negate all the debugging, OpenTelemetry, and other observability tools, as they add significant overhead and are not needed to understand and solve this problem. But they were fun to setup and use to help me understand the internals of the various components. I'll link to some of those posts in the future!

The following examples demonstrate the difference, run against a local vLLM server using Qwen3.6-27B-FP8, same hardware, same container — only `enable_thinking` changes.

**With thinking off, `2+2` finishes in under a second:**

The following command sends a simple chat completion request to a locally hosted vLLM server with thinking explicitly disabled, then pipes the response through `jq` to extract only the first choice. `time` measures total wall-clock duration, making it easy to compare response latency between the two modes.

```bash
$ time curl -s http://192.168.1.251:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen3.6-27B-FP8",
    "messages": [{"role": "user", "content": "What is 2+2?"}],
    "chat_template_kwargs": {"enable_thinking": false},
    "max_tokens": 50
  }' | jq '.choices[0]'
{
  "index": 0,
  "message": {
    "role": "assistant",
    "content": "2 + 2 = 4",
    "refusal": null,
    "annotations": null,
    "audio": null,
    "function_call": null,
    "tool_calls": [],
    "reasoning": null
  },
  "logprobs": null,
  "finish_reason": "stop",
  "stop_reason": null,
  "token_ids": null
}

real	0m0.876s
user	0m0.003s
sys	0m0.012s
```

Here's the breakdown of the command:    

- **`time`** — wraps the entire command and reports elapsed wall-clock time once it finishes.
- **`curl -s`** — calls the API silently, suppressing curl's built-in progress meter so only the JSON response is printed.
- **`http://192.168.1.251:8000/v1/chat/completions`** — the OpenAI-compatible chat completions endpoint on the locally hosted vLLM server.
- **`-H "Content-Type: application/json"`** — tells the server the request body is JSON.
- **`-d '{...}'`** — the JSON request body containing the model name, messages, and generation parameters.
- **`"model": "Qwen3.6-27B-FP8"`** — selects the specific model to use for inference.
- **`"messages": [...]`** — the conversation history; here a single user message asking "What is 2+2?".
- **`"chat_template_kwargs": {"enable_thinking": false}`** — overrides the model's default and explicitly disables the internal reasoning/thinking phase for this request.
- **`"max_tokens": 50`** — caps the response at 50 tokens, which is more than enough for a direct factual answer when thinking is off.
- **`| jq '.choices[0].message'`** — pipes the raw JSON response to `jq`, which extracts and pretty-prints only the `message` object from the first choice.

**With thinking on, the same 50-token budget is exhausted entirely by the internal reasoning block — the model never produces an answer:**

```bash
$ time curl -s http://192.168.1.251:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen3.6-27B-FP8",
    "messages": [{"role": "user", "content": "What is 2+2?"}],
    "chat_template_kwargs": {"enable_thinking": true},
    "max_tokens": 50
  }' | jq '.choices[0]'
{
  "index": 0,
  "message": {
    "role": "assistant",
    "content": null,
    "refusal": null,
    "annotations": null,
    "audio": null,
    "function_call": null,
    "tool_calls": [],
    "reasoning": "Here's a thinking process:\n\n1.  **Analyze User Input:** The user asks \"What is 2+2?\"\n2.  **Identify Core Task:** This is a basic arithmetic question.\n3.  **Perform"
  },
  "logprobs": null,
  "finish_reason": "length",
  "stop_reason": null,
  "token_ids": null
}

real	0m3.735s
user	0m0.005s
sys	0m0.009s
```

Both requests used the **exact same `max_tokens: 50` budget**, the same model, the same hardware, and the same prompt. The only change was `enable_thinking`. With thinking off, 50 tokens was more than enough — the model answered in under a second with `finish_reason: "stop"` and a correct answer in `content`. With thinking on, all 50 tokens were consumed by the internal reasoning block before the model produced a single character of actual output. In fact, you'll notice the `reasioning` field is truncated, indicating the model wasn't even done with its reasoning when it hit the token limit. The result is `content: null`, `finish_reason: "length"`, and an HTTP 200 that looks like success to every layer of your stack — but contains nothing useful for your agent.

For a trivial question like "What is 2+2?", this is merely wasteful. For the moderately complex prompts your agents actually send — system prompts, tool definitions, file contents, conversation history — the model reasons proportionally longer, and the same token ceiling is hit far more reliably.

## Why cloud-hosted frontier models don't seem to have this problem

The short answer: cloud providers control the entire serving stack. When you call OpenAI, Anthropic, or Google without specifying `max_tokens`, they default to something close to the model's full context window minus your prompt — tuned by engineers who get paged when truncation rates spike. They also run silent server-side recovery loops that detect malformed tool calls or truncated reasoning and retry before you ever see the response. Your local vLLM, SGLang, or llama.cpp instance does none of that; it gives you exactly what the model produced and leaves recovery to your agent layer. The rest of this post is about building that recovery layer yourself.

## The symptoms

If any of these sound familiar, welcome to the club.

**The canonical failure:** A direct API call returns HTTP 200. The response parses cleanly. But `choices[0].message.content` is `null` and `finish_reason` is `"length"`. From the agent's perspective the LLM "returned an empty answer," which triggers a retry that hits the same wall. You may see this as a hard timeout (60–120 s), as flakiness that tracks with prompt complexity, or as a task that always fails at the same step — it's the same root cause, just observed from different distances.

## What "thinking mode" actually does

Reasoning-capable models support two output modes via a chat template kwarg (`enable_thinking`, `reasoning_effort`, `thinking_budget` — exact name varies). With thinking **off**, `content` contains the answer. With thinking **on**, the model emits an internal monologue inside `<think>…</think>` tags *before* the answer; the reasoning parser strips those tags into `reasoning_content` and puts the answer in `content`. The server default is set by the chat template at launch time, but agents can override it per request.

## How agents fall into the trap

The trap springs when:

1. The model server defaults to thinking-on (a reasonable default for getting peak quality out of the model).
2. The agent doesn't override thinking-mode per request — it just sends prompts with whatever default.
3. The agent passes through its own `max_tokens` ceiling, which was sized for a non-thinking model.
4. The model receives a moderately complex prompt — anything with files attached, multiple instructions, or reference to capability files like `SOUL.md`, `AGENT.md`, `CLAUDE.md`, skill folders, or MCP server definitions — and decides it needs to think for a while before answering.
5. The model burns through 3000 of its 4000 token budget inside the thinking block, hits the limit, and gets cut off mid-thought.
6. The reasoning parser strips the (incomplete) thinking block. There's nothing left to put in `content`.
7. The server returns `{"content": null, "finish_reason": "length"}`. HTTP 200. The agent receives "successful" empty output.

And here's the part that makes it really painful: **the agent's retry logic re-sends the same prompt with the same settings.** Same outcome. Maybe the agent retries 3 times, taking several minutes total, before giving up and reporting failure. To the user, the system "is broken." To you, looking at logs, every component is "working correctly."

The bigger your agent's context (lots of tools defined, big system prompt with skills referenced, recent message history), the more the model decides it needs to think — and the higher the chance of truncation. **Agents with rich context profiles are *more* susceptible, not less.** This is why frameworks like LangGraph, AutoGen, and CrewAI — which encourage detailed agent specifications, multi-tool orchestration, and rich state tracking — surface this problem more often than minimal stacks.

## How to detect if this is hitting you

Three checks, in order of effort.

### 1. Inspect a failing response directly

The fastest test. Pick a prompt that's been failing in your agent and replay it against your model server with the same parameters, but use `jq` to look at the full message object and the finish reason:

```bash
curl -s http://YOUR_SERVER:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "YOUR_MODEL",
    "messages": [...],
    "max_tokens": YOUR_AGENT_MAX_TOKENS
  }' | jq '.choices[0]'
```

Look at three fields:

- **`finish_reason`** — if this is `"length"` rather than `"stop"`, truncation is in play.
- **`message.content`** — if `null` or empty string, no user-facing output was produced.
- **`message.reasoning` or `message.reasoning_content`** — if this is a long string, all your tokens went into thinking.

If you see `finish_reason: "length"` + `content: null` + `reasoning: "..."` filled with content, you're looking directly at the failure mode. This response, served as 200 OK, is what your agent is getting back.

### 2. Watch your model server's metrics

vLLM, SGLang, and most production model servers export Prometheus metrics. The relevant one for vLLM is:

```
vllm:request_success_total{finished_reason="length"}
```

If your `length` rate is more than ~5% of your total request volume, something is consistently truncating. For interactive agent workloads with thinking off, this should be near zero — agents typically request specific token amounts and rarely overflow. A high `length` rate with sustained agent traffic is a strong signal that thinking is consuming token budgets you weren't planning for.

## How to fix it without losing reasoning capability

You don't want to disable thinking globally. For complex problems, such as code development, the reasoning is genuinely a feature. The fix is to put control in the right place.

### Step 1: Set the server default to thinking-OFF

The model server default *should* be the more conservative mode. For vLLM:

```bash
--default-chat-template-kwargs '{"enable_thinking": false}'
```

This makes "no thinking" the default for any request that doesn't explicitly opt in. Most agent traffic — tool calls, structured output, code generation — works perfectly with thinking off and runs 5–10× faster.

### Step 2: Have agents opt-in per request

When an agent *does* want reasoning, it sends:

```json
{
  "model": "YOUR_MODEL",
  "messages": [...],
  "chat_template_kwargs": {"enable_thinking": true},
  "max_tokens": 16000
}
```

Note the much higher `max_tokens`. With thinking on, you need 4–6× the budget to leave room for both the thinking block and the actual answer. For a typical reasoning model on a moderate prompt, plan on 1500–3000 tokens of thinking overhead.

### Step 3: Use LiteLLM aliases to make this trivial

The cleanest pattern, if you're already running LiteLLM as a proxy: define two model entries pointing at the same backend, with different `chat_template_kwargs`:

```yaml
- model_name: "local/llm"  # default, fast
  litellm_params:
    model: "hosted_vllm/YOUR_MODEL"
    api_base: "http://YOUR_SERVER:8000/v1"
    extra_body:
      chat_template_kwargs:
        enable_thinking: false

- model_name: "local/llm-thinking"  # for hard problems
  litellm_params:
    model: "hosted_vllm/YOUR_MODEL"
    api_base: "http://YOUR_SERVER:8000/v1"
    extra_body:
      chat_template_kwargs:
        enable_thinking: true
```

Now your agents pick model names instead of fiddling with kwargs. Tool-routing agents use `local/llm`. Reasoning agents use `local/llm-thinking` and bump their `max_tokens` accordingly. The model is the same; the alias is the toggle. This pattern works regardless of which agent framework you're using, since they all consume model names.

### Step 4: Defensive retry logic — your local equivalent of cloud-side recovery

Even with the right defaults, occasional truncation is possible if your prompts grow unpredictably. This is where you implement the recovery layer that frontier providers handle for you. Wrap your LLM call in a retry-with-fallback:

```python
def call_llm(messages, prefer_thinking=False):
    max_tokens = 6000 if prefer_thinking else 1500
    for attempt in range(3):
        response = client.chat_completion(
            messages=messages,
            chat_template_kwargs={"enable_thinking": prefer_thinking},
            max_tokens=max_tokens,
        )
        choice = response.choices[0]

        # Got a real response — return it
        if choice.finish_reason == "stop" and choice.message.content:
            return choice.message.content

        # Truncated mid-thinking — fall back to thinking-off
        if prefer_thinking and choice.finish_reason == "length":
            prefer_thinking = False
            max_tokens = 1500
            continue

        # Generic truncation — bump budget and retry
        max_tokens *= 2

    raise RuntimeError(f"No usable response after 3 attempts")
```

This pattern catches the null-content case explicitly, falls back gracefully when thinking blew the budget, and gives you a clear error rather than silent failure. **It's the local equivalent of what OpenAI's and Anthropic's serving layers do invisibly inside their APIs.** You're just doing it on the client side because nobody else is going to do it for you.

If you're running LiteLLM as a proxy, you can also implement this as a `custom_callback` or `pre_call_hook` so every agent in your stack gets the recovery behavior automatically without modifying agent code.



## When to leave thinking on

Thinking mode is a feature, not a bug. Keep it on for multi-step research, architecture decisions, math/proof work, and hard tool selection — tasks where deliberation genuinely improves the answer. Turn it off for routine tool calls, code generation from a clear spec, summarization, and classification. Those tasks make up most of an agent's workload, provide little benefit from thinking, and carry the most truncation risk.

## What this means for your model serving setup

If you're running any reasoning-capable model behind a local agent stack, audit these three things this week:

1. **Server default for thinking mode.** It should be off, with agents opting in.
2. **Agent `max_tokens` defaults vs prompt size.** If your agent has rich context (skills, MCP, big system prompt) and a low `max_tokens`, you're in the trap. Either disable thinking by default or raise the budget significantly.
3. **Your `length` finish-reason rate.** Anything above 5% on agent traffic warrants investigation.

The pattern of "HTTP 200 with null content" is uniquely insidious because every layer of the stack reports success. Logs look clean, metrics look fine, the API contract is honored — and yet the user-facing outcome is failure. The only way to find it is to know to look for it.

This isn't a permanent gap between cloud and local. The fixes I've described — server-side default switching, proxy-layer aliasing, and client-side retry-with-fallback — close most of it. What you don't get from a local setup is the ability to silently extend a token budget mid-generation when the cluster has spare capacity, but you can mostly route around that with conservative defaults and good detection.

If this post helped you find a silent failure in your stack, consider running the diagnostic commands and saving them somewhere you'll find them again. The next time someone in your team or on Discord describes the symptom — "my agent just hangs and returns nothing" — you'll know exactly which question to ask first.

## Related reading

- [vLLM reasoning parsers documentation](https://docs.vllm.ai/en/latest/features/reasoning_outputs.html)
- [SGLang reasoning support](https://docs.sglang.ai/) — same trap, different config flags
- [LiteLLM proxy `extra_body` configuration](https://docs.litellm.ai/docs/proxy/configs)
- [Anthropic's extended thinking documentation](https://docs.claude.com/en/docs/build-with-claude/extended-thinking) — useful comparison to see how the cloud side handles this

## Appendix: How `max_model_len` and `max_tokens` interact in vLLM

When you query the vLLM models endpoint (`GET /v1/models`), the response includes a `max_model_len` field:

```bash
$ curl -s http://192.168.1.251:8000/v1/models | jq '.data[] | {id, max_model_len}'
{
  "id": "Qwen3.6-27B-FP8",
  "max_model_len": 131072
}
```

### What `max_model_len` means

`max_model_len` is the **total context window** for the model — the combined budget for both the input prompt tokens and the generated output tokens. It is set at server launch time (via `--max-model-len` or derived automatically from the model config) and acts as a hard ceiling that cannot be exceeded by any single request.

Formally, vLLM enforces:

```
prompt_tokens + max_tokens ≤ max_model_len
```

The [vLLM `ModelConfig` documentation](https://docs.vllm.ai/en/latest/api/vllm/config/model) states:

> *The `max_model_len` defines the model's context length (prompt + output). If unspecified, it's derived from the model config.*

For my Qwen3.6-27B-FP8, `max_model_len: 131072` means the model supports a 128K token context window shared across input and output.

### What happens when you omit `max_tokens`

If a request arrives at vLLM **without a `max_tokens` field**, vLLM calculates the available output budget automatically. From the [vLLM v1 input processor source](https://docs.vllm.ai/en/latest/api/vllm/v1/engine/input_processor):

```python
if sampling_params.max_tokens is None:
    sampling_params.max_tokens = self.model_config.max_model_len - seq_len
```

In plain terms: if you omit `max_tokens`, vLLM sets it to `max_model_len − prompt_length`. For a small prompt against a 128K context window, that's effectively unlimited output — you are very unlikely to trigger truncation from vLLM's own default.

### Why the truncation trap isn't vLLM's fault

The problem is not vLLM's default. It's the agent framework's default.

Every agent framework (LangGraph, AutoGen, CrewAI, ZeroClaw, Hermes-Agent, etc.) constructs the API request body itself. Some send `max_tokens` with a hardcoded value; others omit it and defer to the provider or server. The table in the appendix below summarises what each framework actually does — and why "no default" is not the same as "safe."

The failure chain:

| Layer | Token budget in effect |
|---|---|
| vLLM default (no `max_tokens` sent) | ~131,000 (128K − prompt) |
| Agent sends `"max_tokens": 4096` | 4,096 — this wins |
| Model uses 3,800 tokens for reasoning | 296 tokens left for actual answer |
| Model hits limit mid-thought | `content: null`, `finish_reason: "length"` |

This is why calling your vLLM server directly with `curl` (without specifying `max_tokens`) usually succeeds — you're benefiting from vLLM's liberal default. The moment your agent wraps that same call, it may silently enforce a much tighter budget.

### Framework and agent `max_tokens` defaults

| Framework / Agent | Default `max_tokens` behaviour | Source / Notes |
|---|---|---|
| **OpenAI Python SDK** | `None` — omits the field; server decides | [openai-python source](https://github.com/openai/openai-python); when omitted, OpenAI uses model's max output limit |
| **LangChain `ChatOpenAI`** | `None` — omits the field; passes nothing to API | [LangChain docs](https://python.langchain.com/docs/integrations/chat/openai/) — developer must set explicitly |
| **LangGraph** | Inherits from whichever `ChatModel` is bound to the node — no LangGraph-level default | [LangGraph docs](https://langchain-ai.github.io/langgraph/) — configure on the model, not the graph |
| **AutoGen** | `None` — omits `max_tokens` unless set in `llm_config`; defers to provider | [AutoGen docs](https://microsoft.github.io/autogen/stable/) — no library-level default |
| **CrewAI** | `None` — delegates to LiteLLM, which defers to the provider | [CrewAI LLM docs](https://docs.crewai.com/concepts/llms) — set explicitly on `LLM(max_tokens=...)` |
| **LiteLLM** | `None` — does not impose a default; passes request to provider as-is | [LiteLLM completion docs](https://docs.litellm.ai/docs/completion/input) |
| **Anthropic SDK** | **Required** — `max_tokens` is a mandatory field; no default exists | [Anthropic Messages API](https://docs.anthropic.com/en/api/messages) — omitting it causes a 400 error |
| **ZeroClaw** | Historically **65,536** (hardcoded); configurable per-route in recent versions | [GitHub issue #1502](https://github.com/getcursor/cursor/issues/1502) — caused 402 errors on OpenRouter; fixed via `config.toml` `max_tokens` field |
| **Hermes-Agent** | `None` by default — does not send `max_tokens` unless set in `~/.hermes/config.yaml` | [Hermes-Agent docs](https://blakecrosley.com) — recommended to leave unset or set ≥16K for thinking models |

> **Why "None" can still cause problems:** When the framework omits `max_tokens`, the **local vLLM server** applies its own default: `max_model_len − prompt_tokens` (often 100K+). That's fine. But if the same framework is used with a cloud provider that has a lower default output limit, or if the developer adds a `max_tokens` value to their config without accounting for thinking overhead, the trap snaps shut.

**References:**
- [vLLM `ModelConfig` — `max_model_len`](https://docs.vllm.ai/en/latest/api/vllm/config/model)
- [vLLM v1 input processor — `max_tokens` default calculation](https://docs.vllm.ai/en/latest/api/vllm/v1/engine/input_processor)
- [vLLM reasoning outputs — server-level default chat template kwargs](https://docs.vllm.ai/en/latest/features/reasoning_outputs.html#server-level-default-chat-template-kwargs)
- [vLLM engine arguments reference](https://docs.vllm.ai/en/latest/configuration/engine_args/)
- [OpenAI Python SDK — chat completions](https://github.com/openai/openai-python)
- [LangChain `ChatOpenAI` integration](https://python.langchain.com/docs/integrations/chat/openai/)
- [AutoGen `llm_config` documentation](https://microsoft.github.io/autogen/stable/)
- [CrewAI LLM configuration](https://docs.crewai.com/concepts/llms)
- [LiteLLM completion parameters](https://docs.litellm.ai/docs/completion/input)
- [Anthropic Messages API — `max_tokens` required](https://docs.anthropic.com/en/api/messages)