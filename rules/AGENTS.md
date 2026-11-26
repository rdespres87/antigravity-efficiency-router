# Efficiency Router (always-on)

Goal: maximum useful work per unit of quota. Never mention tiers to the user unless asked.

## 1. Silent Task Triage
- **T0 Trivial**: chit-chat, known fact, one-line answer/edit. Answer directly; no tools unless required, no artifacts, no plans.
- **T1 Mechanical**: finding code, reading many files, web/doc research, summarizing logs/diffs, boilerplate, format conversion, bulk edits.
- **T2 Standard**: well-specified feature, bug with clear repro, refactor covered by tests.
- **T3 Hard**: architecture, ambiguous design, subtle/concurrency/security bugs, high blast radius.

## 2. Auto-Routing & Budget Levels
Each turn injects `[router] main=<bucket>/<tier> | 5h x% . 7d y% | LEVEL | task~Tn [| AUTO-PRO|LIGHT]`. Your own triage overrides `task~Tn`. If absent, assume `premium`/`GREEN`. Routing is always downward (see `tiered-router` for Ceiling Principle, Local-First LM Studio, and RED offloading).

| main tier | T0 | T1 | T2 | T3 |
|---|---|---|---|---|
| premium (Claude / top model) | answer briefly, no tools | `flash` | self if judgment-heavy, else `pro` | **self** |
| strong (Gemini Pro) | answer briefly | `flash` | self | self |
| cheap (Flash) | self | self | self | `pro` subagent analyzes/implements; self integrates |

- **YELLOW**: T2 -> `pro`; on T3 keep core reasoning, delegate reading/implementation.
- **RED**: delegate all coding/tests/commits to local LM Studio (`tiered-router`) or `pro`/`flash`; self = orchestration/final check only; warn the user ONCE if premium quota is nearly exhausted.
- `AUTO-PRO` = cheap main + hard task -> spawn `pro`. `LIGHT` = premium main + easy task -> answer briefly or delegate; never ask the user to switch models.
- Subagent `Model`: `flash_lite` (lookup/extraction), `flash` (research/reading/boilerplate), `pro` (judgment-heavy implementation). Never use `inherit` for routine work.

## 3. Subagent Delegation & Token Hygiene
- Use `invoke_subagent` (`research` read-only, `self` edits); launch independent subagents in parallel.
- Self-contained prompts: goal, exact paths, constraints, done-criteria, compact return (bullets, `file:line`, <=300 words). Never request full file dumps.
- Skip delegation if finishable in <=2 tool calls. Verify delegated edits via tests/lint/diff instead of re-reading everything.
- Search before reading; read line ranges, never re-read unchanged files; batch independent calls in parallel; concise replies without restating tool outputs; one targeted web search beats five vague ones.
- Templates & quota commands: skill `efficiency-router`.

## 4. Phase Boundary Protocol
At each milestone boundary (plan, implementation, review), evaluate in order:
1. **Continue**: only if next step needs verbatim context and budget is GREEN.
2. **`/clear`**: if intermediate exploration is disposable.
3. **Isolate**: delegate next self-contained phase to subagent or `execute_local_task`.
4. **Handoff**: persist state to `docs/agent/HANDOFF.md` when switching branches/tasks/sessions.
5. **`/compact`**: compress context when continuing in the same session; prompt the user to run `/compact`.

## 5. Multilingual Token Efficiency
- **Telegraphic French** for conversational turns, status banners, and `ask_question` dialogs: zero fluff, active verbs, native English technical terms.
- **Quota-Adaptive Asymmetry**: on `YELLOW`/`RED` (or technical specs >20 lines), write technical analysis and implementation drafts in dense English.
- **English-Only Persistent Memory**: `SESSION_STATE.md`, `TASKS.md`, `HANDOFF.md`, `/compact` summaries, and Headroom payloads MUST be in English.
