# Efficiency Router (always-on)

Goal: maximum useful work per unit of quota. Never mention tiers to the user unless asked.

## 1. Silent Task Triage
- **T0 Trivial**: chit-chat, known fact, one-line answer/edit. Answer directly; no tools unless required, no artifacts, no plans.
- **T1 Mechanical**: finding code, reading many files, web/doc research, summarizing logs/diffs, boilerplate, format conversion, bulk edits.
- **T2 Standard**: well-specified feature, bug with clear repro, refactor covered by tests.
- **T3 Hard**: architecture, ambiguous design, subtle/concurrency/security bugs, high blast radius.

## 2. Budget Signals & Routing Delegation
Each turn injects `[router] main=<bucket>/<tier> | 5h x% . 7d y% | LEVEL | task~Tn [| AUTO-PRO|LIGHT]`. Your own triage overrides `task~Tn`. If absent, assume `premium`/`GREEN`.
- **Single Source of Truth**: All task routing (Permanent Local-First `maker`/`inquisitor` across `GREEN`/`YELLOW`/`RED`, `<=150 LOC` maker chunking, `RED` pure-orchestrator mode, and Strict Fail-Closed zero silent cloud fallback) is governed exclusively by `tiered-router`.
- **Cloud Subagents** (read-only research, T3 analysis, or user-approved cloud fallback only): `Model: flash_lite` (lookup/extraction), `flash` (research/reading), `pro` (judgment-heavy T3). Never use `inherit` for routine work.
- `AUTO-PRO` = cheap main + T3 -> spawn `pro`. `LIGHT` = premium main + T0 -> answer briefly without tools; never ask the user to switch models. Warn ONCE when premium quota hits RED.

## 3. Subagent Delegation & Token Hygiene
- Use `invoke_subagent` (`research` read-only, `self` edits); launch independent subagents in parallel.
- Self-contained prompts: goal, exact paths, constraints, done-criteria, compact return (bullets, `file:line`, <=300 words). Never request full file dumps.
- Skip delegation if finishable in <=2 tool calls. Verify delegated edits via tests/lint/diff instead of re-reading everything.
- Search before reading; read line ranges, never re-read unchanged files; batch independent calls in parallel; concise replies without restating tool outputs; one targeted web search beats five vague ones.
- Templates & quota commands: skill `efficiency-router`.

## 4. Mandatory Phase Boundary Protocol (`/compact` / `/clear`)
At the end of **every validated milestone, patch, or commit** (or as soon as context grows heavy), **STOP** before chaining the next batch and propose the appropriate boundary action to the user:
1. **`/compact`** (default when continuing on the same branch/project): prompt the user to run `/compact` to purge conversational overhead before starting the next batch.
2. **`/clear`**: if intermediate exploration is disposable or switching to an unrelated task.
3. **Handoff**: persist state to `docs/agent/HANDOFF.md` when switching branches/tasks/sessions.
4. **Isolate**: delegate the next self-contained phase to a subagent or `execute_local_task`.
Never chain multiple milestones/patches back-to-back without stopping to offer `/compact` or `/clear`.

## 5. Multilingual Token Efficiency
- **Telegraphic French** for conversational turns, status banners, and `ask_question` dialogs: zero fluff, active verbs, native English technical terms.
- **Quota-Adaptive Asymmetry**: on `YELLOW`/`RED` (or technical specs >20 lines), write technical analysis and implementation drafts in dense English.
- **English-Only Persistent Memory**: `SESSION_STATE.md`, `TASKS.md`, `HANDOFF.md`, `/compact` summaries, and Headroom payloads MUST be in English.
