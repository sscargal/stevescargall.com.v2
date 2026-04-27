---
title: "Building an Agentic Team for an Open Source Project with Claude Code"
meta_title: "Stand Up a Claude Code Agent Team for an Existing Repository"
description: "How I used Claude Code Agent Teams to build a 22-agent maintenance team for MemMachine after a core engineer left. Design decisions, the full roster, the /mm: command surface, the TODO-driven docs handoff, and how to reproduce this for any existing repository."
image: "featured_image.webp"
date: 2026-04-14T12:00:00-06:00
categories: ["AI"]
author: "Steve Scargall"
tags: ["Claude Code", "Agent Teams", "AI agents", "subagents", "MemMachine", "open source maintenance", "agent skills", "spec-driven development", "prompt engineering", "AI engineering"]
draft: false
reading_time: 14
---

A core engineer on [MemMachine](https://github.com/MemMachine/MemMachine) — the one who owned the Semantic Memory subsystem — left the project. The codebase didn't grow any less complex overnight, but the human attention available to maintain it did. That's a familiar shape of problem in any open source project, and it's the exact shape where a well-designed Claude Code agent team earns its keep.

This post documents what I built: a 22-agent maintenance team that lives entirely inside MemMachine's repository, coordinates via Claude Code's experimental Agent Teams runtime, and operates under a design I can reproduce for any existing repository with real code. The agents don't push code, don't sign commits, don't merge pull requests, and don't cut releases — humans still gatekeep every consequential action. What the agents *do* do is the tedious and error-prone middle of software maintenance: triage, spec drafting, implementation, QA, security review, docs, dependency and upstream tracking.

Everything lives under `.claude/` and is gitignored. None of it leaks to GitHub. Other contributors working the repo without the agent team see exactly the same project they saw before.

## The Situation

MemMachine is a long-term memory layer for AI agents — open source, published at [docs.memmachine.ai](https://docs.memmachine.ai), with a multi-package UV monorepo:

- `packages/server/` — FastAPI + FastMCP, houses **semantic_memory** and **episodic_memory** subsystems
- `packages/{client,common,ts-client,meta}/` — Python and TypeScript SDKs
- `integrations/` — nine framework bridges (crewai, langchain, langgraph, dify, fastgpt, n8n, …) plus an OpenClaw plugin
- `examples/` — runnable demos
- `evaluation/` — retrieval and episodic-memory evaluation suites, not currently in CI
- `src/memmachine/` — a legacy layout that still partially exists
- 16 GitHub Actions workflows covering pytest (Python 3.12–3.14), integration tests, lint, type check, OpenAPI generation, Docker builds, SBOM, lock-file checks, publish jobs, and docs checks

The semantic-memory subsystem — the orphaned one — had **zero tests** under its test tree. Keeping it from silently regressing was going to be someone's full-time job, but nobody had a full-time slot for it.

## What I Wanted

Concrete operator goals, written down before I built anything:

1. **Weekly releases** stay on track.
2. **Every open issue and PR** gets reviewed — stale ones closed, actionable ones scoped, outdated ones flagged.
3. **Semantic memory gets tests** before it regresses silently.
4. **Examples and integrations** stay working against the current release.
5. **OpenClaw tracking** keeps pace with its frequent upstream API changes.
6. **I approve everything.** No agent pushes, merges, publishes, or signs.

And a design constraint that turned out to be load-bearing: **everything the agent team depends on lives inside `.claude/` and is gitignored.** Other maintainers and contributors don't see it, don't have to run it, and aren't slowed down by it. If the agent team infrastructure goes away tomorrow, the project is untouched.

## Why Agent Teams, Not Subagents

Claude Code offers two ways to parallelize work: [subagents](https://code.claude.com/docs/en/sub-agents) (spawned from the main session, report back when done) and [Agent Teams](https://code.claude.com/docs/en/agent-teams) (separate Claude Code instances that coordinate via a shared task list and mailbox, currently experimental behind `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`).

For this project I chose Agent Teams for three reasons:

- **Teammates can talk to each other.** When `dev-python` and `semantic-memory-architect` need to negotiate where a fix belongs, they can exchange messages directly instead of routing every question back through me.
- **Independent context windows.** Each teammate loads only what its role needs. The context for `qa` running the CI mirror doesn't pollute the context for `architect` reviewing a spec.
- **The human stays the lead.** The session I'm typing in is the fixed team lead for its lifetime. I can't accidentally promote a teammate into a position that pushes code.

Agent Teams is explicitly experimental and has limits — `/resume` doesn't restore teammates, you can't nest teams, and token cost scales linearly with teammate count. None of those are dealbreakers for a maintenance workflow where teams are ephemeral and teammate counts stay small.

## The Design Principles

Five principles drove every subsequent decision.

**Local and gitignored.** `.claude/agents/`, `.claude/skills/`, `.claude/commands/`, `.claude/specs/`, `.claude/todos/`, `.claude/memory/`, `.claude/hooks/`, and `CLAUDE.md` at repo root are all added to `.gitignore`. `CLAUDE.md` sits at the repo root (not under `.claude/`) specifically because Agent Teams auto-loads `CLAUDE.md` from a teammate's working directory — moving it would break the auto-load.

**Humans hold the pen.** Agents stage files and write commit messages, but commits are signed by me because signing requires my password. Agents never run `git commit`, `git push`, `gh pr create`, or `gh release create`. They hand me ready-to-run commands and PR body text.

**Karpathy guardrails, enforced via skill.** The four principles — *Think Before Coding*, *Simplicity First*, *Surgical Changes*, *Goal-Driven Execution*, documented by [Andrej Karpathy](https://github.com/forrestchang/andrej-karpathy-skills) for LLM-assisted coding — go into a single `karpathy-guidelines` skill that every code-touching agent loads at spawn. No agent writes code without running through the four gates.

**Spec-driven by default.** Any task that touches more than two files, changes a public API, or touches the memory subsystems requires a markdown spec at `.claude/specs/<issue>.md` before code is written. Typos and one-liners skip this. The spec has fixed sections: Problem, Scope, Non-goals, Approach, Acceptance criteria, Test plan.

**Advisor pattern for expensive reasoning.** The `architect` role runs Claude Opus; every other role runs Claude Sonnet. Teammates consult the architect via mailbox for hard calls — tiebreaking disagreements, reviewing cross-cutting specs, weighing design tradeoffs — without every teammate paying Opus rates for routine work. This mirrors the advisor pattern described in [Anthropic's advisor blog post](https://claude.com/blog/the-advisor-strategy), which showed a 2.7 pp SWE-bench improvement and 11.9% cost reduction versus Sonnet-only agents.

## The Architecture

```
Human (operator) = team LEAD (fixed)
   │  spawns ad-hoc teammates per task from .claude/agents/*.md
   │  shared task list at ~/.claude/tasks/<team>/
   │  team config auto-written at ~/.claude/teams/<team>/config.json
   │  mailbox for teammate↔teammate messages
   └─ root CLAUDE.md auto-loaded into every teammate
```

I never pre-author team configs — Agent Teams writes them automatically at spawn time. What I *do* pre-author is the role library under `.claude/agents/*.md`. Each file defines one teammate type (its system prompt, its write scope, its model, its tools). Claude Code spawns whichever roles the current task needs.

## The Roster

Twenty-two agents after one round of refinement. Each has a strict **write scope** — a list of paths it may edit. Agents refuse edits outside that scope, which keeps `dev-python` from wandering into `semantic_memory/` and the memory architects from stepping on each other.

### Coordination

- **`pm`** — decomposes issues into tasks, proposes milestones, no code access
- **`architect`** (Opus) — cross-package tradeoffs, advisor to other teammates, spec-review, disagreement tiebreaker
- **`gh-triage`** — reads issues and PRs, classifies them, drafts labels/milestones/comments, **powers the `/mm:team <github-url>` auto-assembly feature described below**

### Code specialists

- **`semantic-memory-architect`** — owns the orphaned subsystem; first priority is backfilling missing tests
- **`episodic-memory-architect`** — the symmetric owner of episodic memory
- **`server-architect`** — FastAPI + FastMCP surface, routing, middleware, OpenAPI, Alembic migrations, settings
- **`dev-python`** — general Python glue (client, common, meta)
- **`dev-typescript`** — `packages/ts-client`

### Maintenance

- **`integrations-maintainer`** — tracks nine integrations against upstream framework changes
- **`openclaw-tracker`** — polls OpenClaw releases, diffs the API surface, drafts adapter updates
- **`examples-maintainer`** — verifies every example runs against the latest release
- **`benchmark`** — runs the orphaned `evaluation/` suites and flags regressions
- **`docs-maintainer`** — covered in detail below
- **`upstream-sync`** — compares fork to upstream, drafts merge/rebase plan

### Quality gates

- **`qa`** — runs the local CI mirror (every workflow under `.github/workflows/`)
- **`security`** — diff review, `pip-audit`, `npm audit`, SBOM, Dependabot triage

### Imported reviewer agents

Six PR-review sub-agents imported from [anthropics/claude-plugins-official](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/pr-review-toolkit): `code-reviewer`, `code-simplifier`, `comment-analyzer`, `pr-test-analyzer`, `silent-failure-hunter`, `type-design-analyzer`.

Each agent is 50–120 lines of markdown with YAML frontmatter (`name`, `description`, `model`, `tools`) followed by its system prompt.

## The Quality Gate

Claude Code's Agent Teams runtime exposes three hooks I wired directly into `settings.local.json`:

- **`TaskCreated`** — appends one line to `.claude/audit.log`
- **`TeammateIdle`** — logs when a teammate stops without output
- **`TaskCompleted`** — **blocks** completion on code-touching tasks unless `qa` and `security` have both written `SignOff	<qa|security>	<task-id>` lines to the audit log

That last one is the teeth of the whole system. An agent can't mark a code-touching task "done" until `qa` has run the local CI mirror green and `security` has cleared the diff. The hook greps literally for tab-separated sign-off lines in `.claude/audit.log`; the format is defined in the `audit-log` skill and every sign-off agent follows it exactly.

There's also a `PreToolUse` hook — imported from the [security-guidance plugin](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/security-guidance) — that fires before every `Edit`, `Write`, or `MultiEdit` and warns about risky edit patterns (command injection in GitHub Actions workflows, unsafe eval, unvalidated input).

## The `/mm:` Command Surface

Twenty-two slash commands, all namespaced with `/mm:` so they never collide with general-use Claude Code commands. The namespace comes from storing them at `.claude/commands/mm/<name>.md`.

Daily drivers:

- `/mm:bootstrap` — verifies Claude CLI version, `uv`, Node, Python, Docker, `gh`, git signing config
- `/mm:status` — current branch, open TODOs, last QA run, active team, weekly token tally per agent (parsed from the audit log)
- `/mm:triage` — `gh-triage` sweeps all open issues and PRs, produces a classification digest at `.claude/todos/triage-digest-<date>.md`
- `/mm:team <github-url>` — auto-assembles a team proposal from a GitHub issue URL (described below)
- `/mm:assemble <issue>` — confirm and spawn the proposed team
- `/mm:spawn <agent> "<prompt>"` — single teammate, scoped mandate
- `/mm:qa [branch|files]` — run the local CI mirror
- `/mm:security-scan` — static review + dep audit
- `/mm:docs-sync` — run docs-maintainer sweep

Plus specialist commands for `examples-check`, `integrations-check`, `openclaw-sync`, `upstream-sync`, `bench`, `audit-tail`, `todo-list`, `cadence`, `memory`, and two imported ones: `review-pr` and `revise-claude-md`.

## The Two Innovations Worth Stealing

Two design choices here are worth lifting for any similar project.

### 1. GitHub-URL-Driven Team Assembly

`/mm:team https://github.com/MemMachine/MemMachine/issues/1318` does this:

1. `gh-triage` pulls the issue and its thread via `gh issue view`.
2. It applies a role-selection rubric encoded in its system prompt, mapping touched paths and labels to roles:
   - `packages/server/src/memmachine_server/semantic_memory/**` → `semantic-memory-architect`
   - `packages/ts-client/**` → `dev-typescript`
   - `integrations/openclaw/**` → `openclaw-tracker`
   - labels `security` or `dependency` → `security`
   - any code change at all → `qa` and `security` added by default
3. It drafts a team proposal — which roles, what each will do, proposed branch name, whether a spec is required — and writes it as the opening section of `.claude/specs/<n>.md`.
4. It prints the proposal to me for confirmation.
5. When I run `/mm:assemble <n>`, the lead spawns each listed teammate with a scoped prompt that constrains them to their declared write scope.

The rubric is just prose in the agent's markdown file. Updating it is one edit, not a code change. The proposal is always a draft I approve — the agent never spawns unilaterally.

### 2. The `todo-docs-` Handoff

Every code-touching agent (`dev-python`, `dev-typescript`, `server-architect`, memory architects, integrations-maintainer, openclaw-tracker) emits `.claude/todos/todo-docs-<slug>.md` whenever its change affects user-facing behavior — public HTTP routes, SDK methods, settings, docker-compose services, OpenAPI shape, anything described in `docs/core_concepts/`.

`docs-maintainer` scans for that filename prefix as its work queue. When a coding team finishes a PR, I can either include `docs-maintainer` in the team or run `/mm:docs-sync` afterward; either way, the docs update happens in a clean branch, builds cleanly with the Mintlify CLI (`mint build` + `mint broken-links`), passes `docs-checks.yml` + `generate-openapi.yml` locally, and lands as a draft PR for the human documentation writer to approve and merge.

The pattern generalizes: any role that needs work from another role can queue it via a predictable-prefix TODO file, and the receiving role scans that prefix on its next invocation. It's a dumb, grep-able queue — no service, no broker, no schema. Works.

## The Phased Build

I executed the build in six phases. I'm listing them both to document what got built and to give anyone reproducing this a sequence that works.

**Phase 0 — Substrate.** Add `.claude/` and `CLAUDE.md` to `.gitignore`. Enable `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` in `settings.local.json`. Verify Claude Code version ≥ 2.1.32. Create directory skeleton. Write the three hook scripts and wire them into settings.

**Phase 1 — Foundations.** Write the five skills every agent references: `karpathy-guidelines`, `audit-log`, `spec-driven`, `branch-and-commit`, `todo-as-issue`. Write `CLAUDE.md` at repo root and `.claude/README.md` operator guide.

**Phase 2 — Triage + gates.** Write `pm`, `architect`, `gh-triage`, `qa`, `security`. Write `run-ci-locally` and `dep-audit` skills. Write the 12 daily-driver slash commands.

**Phase 3 — Core dev roles.** Write the two memory architects, `server-architect`, `dev-python`, `dev-typescript`.

**Phase 4 — Maintenance roles.** Write the six maintenance agents and their skills (`openclaw-diff`, `example-runner`, `backcompat-check`, `eval-runner`) and eight commands.

**Phase 5 — Vetted imports.** Walk three third-party repositories — [affaan-m/everything-claude-code](https://github.com/affaan-m/everything-claude-code), [anthropics/skills](https://github.com/anthropics/skills), [anthropics/claude-plugins-official](https://github.com/anthropics/claude-plugins-official) — and evaluate each candidate individually. Eleven items imported after per-item review, with a provenance manifest at `.claude/imported/README.md` documenting what came from where, when, and with what adaptations.

**Phase 6 — Validation.** Run `/mm:triage` to produce the first real issue + PR digest. Walk one real issue end-to-end through the team to validate the pipeline.

The final counts: **22 agents, 19 skills, 22 slash commands, 4 hooks, 11 seeded TODOs.** Only `.gitignore` became a tracked change. Everything else stays local.

## Can This Be Reproduced for Any Repository?

Yes, with a caveat: it works for repositories that already have code. A greenfield repository doesn't have paths to route TODOs to, workflows to mirror locally, or a release surface to protect.

What travels: the architecture (lead + teammate roles, write scopes, hook-enforced gates, TODO-driven handoffs, `/mm:` namespace), the principles (local-only, spec-driven, Karpathy guardrails, advisor pattern), the phased build sequence, and a surprising amount of the foundational skills (`karpathy-guidelines`, `audit-log`, `spec-driven`, `branch-and-commit`, `todo-as-issue` are all repo-agnostic).

What has to be re-derived per repository: the roster of specialists (MemMachine needed `semantic-memory-architect` because that subsystem was orphaned; your project won't), the write scopes (which paths belong to which role), the CI mirror command list (every repo's `.github/workflows/` is different), and the role-selection rubric inside `gh-triage`.

The natural next step is a skill — let's call it `agent-team-bootstrap` — that analyzes an existing repository and proposes a starter roster and rubric. Its procedure would be: inventory languages and workspaces (`pyproject.toml`, `package.json`, `go.mod`, `Cargo.toml`, …), identify major subsystems by directory clustering and recent-touch frequency (`git log --since=1.year --stat`), detect orphaned subsystems (low recent-touch count + high code volume + high issue-title mention rate), enumerate GitHub Actions workflows and translate each into a `run-ci-locally` command, propose a specialist role per identified subsystem, and write the role-selection rubric from what it learned. It would ask the operator three or four questions — governance (who signs commits, who merges), release cadence, which languages matter, what the human doesn't want delegated — and then render the `.claude/` tree.

The key insight is that *none of this needs to be generic*. The skill generates a project-specific agent team by reading the project. A skeleton plus a good rubric plus the foundational repo-agnostic skills gets you 70% of the way; the operator adds the last 30% (specialists for weird internal subsystems, write-scope exceptions, taste calls on cadence).

I'm going to write that skill next. When I have it, I'll post a follow-up with the script and a worked example on a different repository.

## What I'd Do Differently

- **Start the agent memory layer immediately.** I built `.claude/memory/` as plain append-only markdown per-agent. It's a great substrate, but I haven't populated it yet. The first few real tasks should surface learnings (ruff rejects pattern X, installation-test flakes on Python 3.14, etc.) that go straight into `.claude/memory/shared.md`. An empty memory layer is a missed opportunity.
- **Dogfood the product.** MemMachine *is* a memory layer. The long-term version of `.claude/memory/` should be a local MemMachine server that agents query at spawn time. That's a stretch goal, not day-one work, but it's the right arc.
- **Weekly token-cost review.** `/mm:status` shows a per-agent token tally for the week. I should read that report weekly and retire agents whose spend outpaces their value.

## Artifacts

The full plan file is at `~/.claude/plans/floating-snuggling-unicorn.md` in my local setup. Key artifacts from the build, in case you want the exact shapes:

- `settings.local.json` with the experimental flag, three hooks, and a broader permissions allowlist
- `CLAUDE.md` at repo root with repo map, commands, Karpathy guardrails, secrets hygiene, Agent Teams caveats, keybinding crib
- `.claude/agents/*.md` — 22 role definitions
- `.claude/skills/*/SKILL.md` — 19 skill packages
- `.claude/commands/mm/*.md` — 22 slash commands
- `.claude/hooks/*.sh` and `.py` — the four hooks
- `.claude/todos/todo-*.md` — 11 seeded TODOs pre-loaded so `/mm:todo-list` shows a real backlog from day one

Total token cost of the build: a few hours of interactive session, one long plan file, and a lot of trust in the Karpathy guardrails.

---

*If you're reproducing this for your own project and get stuck on a specific decision, or if you want to compare notes on writing the `agent-team-bootstrap` skill, email me. I'm happy to trade design choices.*
