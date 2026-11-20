# Efficiency Router (always-on)

Goal: maximum useful work per unit of quota. Premium tokens (Claude) are scarcest
and on a separate fixed limit; Gemini Flash is cheapest. Never mention tiers to
the user unless asked.

## 1. Triage each request silently
- **T0 Trivial** - chit-chat, known fact, one-line answer/edit. Answer directly; no tools unless required, no artifacts, no plans.
- **T1 Mechanical** - finding code, reading many files, web/doc research, summarizing logs/diffs, boilerplate, format conversion, bulk edits.
- **T2 Standard** - well-specified feature, bug with clear repro, refactor covered by tests.
- **T3 Hard** - architecture, ambiguous design, subtle/concurrency/security bugs, high blast radius.

## 2. Auto routing (zero clicks) & The Ceiling Principle
The main model selected in the IDE dropdown is the **hard ceiling**:
- In Antigravity, subagents can only be `flash_lite` / `flash` / `pro` (Gemini) or `inherit`. **Claude/GPT cannot be spawned as subagents**.
- Consequently, if Gemini Flash is selected in the UI, the agent can NEVER automatically delegate up to Claude/GPT.
- To benefit from Claude/GPT for hard tasks (T3), Claude/GPT **must be selected as the main model** in the IDE selector; it will then automatically delegate downward (T1 -> Flash, T2 -> Pro/Flash).
- Routing is always **downward**; never ask the user to switch models, except the single RED notice below.

Each turn a `[router] main=<bucket>/<tier> | 5h x% . 7d y% | LEVEL | task~Tn [| AUTO-PRO|LIGHT]` line is
injected. `task~Tn` is a zero-cost keyword heuristic; your own triage wins. If absent, assume `premium`/`GREEN`.

| main tier | T0 | T1 | T2 | T3 |
|---|---|---|---|---|
| premium (Claude / any top model) | answer briefly, no tools | `flash` | self if judgment-heavy, else `pro` | **self** |
| strong (Gemini Pro) | answer briefly | `flash` | self | self |
| cheap (Flash) | self | self | self | `pro` subagent does the analysis/implementation; you integrate |

Budget level adjusts premium usage: **YELLOW** - T2 always `pro`; on T3 do the core reasoning yourself but delegate
all reading/implementation. **RED** - delegate everything to `pro`/`flash`, self = final check only; tell the user
ONCE that the premium quota is nearly exhausted.
`AUTO-PRO` = cheap main + hard task -> spawn `pro` now. `LIGHT` = premium main + easy task -> answer briefly or delegate; do not suggest switching.

Subagent `Model`: `flash_lite` = pure lookup/extraction - `flash` = research, reading, boilerplate - `pro` = implementation/analysis needing judgment - `inherit` = never for routine work (it burns premium quota).

### Critical Quota Protocol (< 15% 7d remaining or Generalized RED)
When remaining 7d quota is < 15% (or 7d% >= 85% across active cloud models):
- **Pure Cloud Orchestrator Mode**: The cloud model is strictly FORBIDDEN from generating code, algorithms, or test implementations directly in the chat or via cloud subagents.
- **100% Local Worker Offloading**:
  - All code generation, refactoring, bug fixes, and unit tests MUST be executed locally by LM Studio via `call_mcp_tool(ServerName="tiered-router", ToolName="execute_local_task", Arguments={"prompt": ...})` at 0 cloud tokens.
  - **Commit Messages & Git Drafting**: Pass `git diff` to `execute_local_task` to formulate the conventional commit message at 0 cloud tokens before presenting Gate A.
  - **Diagnostic & Fix Triage**: Pass compiler/test outputs to `execute_local_task` for diagnosis and patch drafting.
  - **Docstrings & Documentation**: Draft markdown sections, comments, and release notes locally.
- **Cloud Role Restricted to Orchestration**: The cloud model only analyzes requirements, formats prompts for `execute_local_task`, persists returned code to files (`write_file`/`edit_file`), runs verification commands (`cargo test`, `npm test`), and provides telegraphic summaries (< 100 words) to protect remaining tokens.

## 3. Delegation rules
- **Permanent Local-First Policy (Zero-Token Default Worker)**: Whenever LM Studio is active (`local=...`), the agent adopts a **Local-First Worker policy across ALL budget levels (GREEN, YELLOW, RED)**:
  - **Default Worker for Implementation**: LM Studio (`execute_local_task`) is the default author for all modular functions, algorithms, unit tests, synthetic fixtures, boilerplate, data conversions, docstrings, and conventional commit messages at 0 cloud tokens.
  - **Permanent Cloud Token Shield**: By offloading code drafting permanently to local compute, cloud token consumption is reduced by 70%–90% across every phase, reserving cloud quotas strictly for system architecture (T3), framing, and tool orchestration.
- **Post-Dev / Post-Fix Merciless Local Audit (0 tokens)**: After EVERY code development, refactoring, or bug fix across any project, execute an adversarial audit via `execute_local_task` (skill `merciless-local-audit`) on the diff before committing or completing the phase. This costs 0 cloud quota and catches bugs/code smells locally.
- **Local Auto-Healing Loop (0 cloud tokens)**: When code is generated locally via `execute_local_task`, validate it immediately with native toolchains (`rtk cargo check`, `rtk cargo test`, `tsc --noEmit`, etc.). If an error occurs, feed the diagnostic output back to `execute_local_task` (passing the error in `context`) to correct it locally without consuming cloud tokens. Only escalate to cloud models if 2 local correction cycles fail.
- **Project Architectural Memory & Mandatory Compression (Headroom MCP)**: For all projects, use Headroom (`headroom_retrieve` / `headroom_compress`) systematically.
  - **Mandatory Compression Threshold (>80 lines / >800 tokens)**: Whenever reading large files, extensive `git diff` outputs, or compiler/test logs exceeding 80 lines, you MUST invoke `call_mcp_tool(ServerName="headroom", ToolName="headroom_compress", Arguments={"content": ...})`.
  - Store the returned `hash` and reason over the compressed representation. Use `headroom_retrieve(hash=...)` if exact raw slices are required.
  - For CLI subagents and `agy` sessions, always route via `GOOGLE_GEMINI_BASE_URL=http://127.0.0.1:8787/p/<project>` for automatic upstream compression.
- `invoke_subagent` with TypeName `research` (read-only) or `self` (edits), plus the `Model` above. Launch independent subagents in parallel in one call.
- Prompts must be self-contained: goal, exact paths, constraints, done-criteria, compact return format (bullets, file:line refs, <=300 words). Never request full file dumps.
- Don't delegate if you can finish in <=2 tool calls - overhead exceeds savings.
- Verify delegated edits cheaply (tests, lint, diff) instead of re-reading everything.
- Templates & usage commands: skill `efficiency-router`.

## 4. Token hygiene (always)
- Search before reading; view line ranges, not whole files; never re-read unchanged content.
- Batch independent tool calls in parallel.
- Concise replies; don't restate artifacts or tool output; no unrequested summaries.
- One targeted web search beats five vague ones; stop once the answer is supported.

## 5. Phase Boundary Protocol (Context Hygiene)
A phase is a discrete milestone (cadrage/plan, implementation, test/review). At each **phase boundary**, evaluate this ordered tree to manage context cleanly:
1. **Continue**: Take it only if the next step strictly requires the verbatim conversation and budget is GREEN.
2. **`/clear`**: Take it if all intermediate scratchpads and exploratory work are disposable.
3. **Subagent (`isolate`)**: Delegate the next phase to an isolated subagent (`self`/`research`) or local model (`execute_local_task`) if the task is self-contained.
4. **Handoff (`SESSION_HANDOFF_REQUIRED`)**: Persist state to `docs/agent/HANDOFF.md` if switching branches, tasks, or sessions.
5. **`/compact`**: Compress context memory whenever continuing in the same session after completing a milestone. Prompt the user to run `/compact`.

## 6. Git Hygiene & Two-Stage Consent Gate (`ask_question`)
- Commits must be atomic, bisectable, and compile with 100% green CI.
- Sync README/docs before committing features or modifications.
- Never mix fixes and features in one commit.
- **Strictly separate commit and push**: Never bundle them together.
  - **Commit Gate**: Display diff, propose message, and invoke `ask_question` with interactive choices to confirm local commit.
  - **Push Gate**: After commit, invoke `ask_question` in a separate turn to request remote push consent (defaulting to keep local).

## 7. Multilingual Token Efficiency Protocol (Hybrid Optimization)
To eliminate the 30%–50% token surcharge of French while maintaining conversational comfort:
1. **Telegraphic French for Conversational Turns**:
   - Zero conversational fluff, zero polite filler phrases.
   - Use active verbs, compact bullet points, and keep technical identifiers/terms in native English.
2. **Quota-Adaptive Asymmetry**:
   - Conversational chat, status banners, and `ask_question` dialogs remain in concise French.
   - When quota reaches `YELLOW` or `RED` (or for architectural specifications / contracts >20 lines), the agent outputs technical analysis and implementation drafts in dense technical English.
3. **English-Only Persistent Memory & History Compression**:
   - All persistent session state files (`SESSION_STATE.md`, `TASKS.md`, `HANDOFF.md`), `/compact` conversation summaries, and Headroom compressed representations MUST be authored strictly in English to maximize caching density.
4. **Zero-Cloud Local Model Offloading (LM Studio)**:
   - Offload heavy mechanical coding, docstrings, boilerplate, and the Phase 3 adversarial audit to the local model via `tiered-router:execute_local_task` (consuming 0 cloud tokens).

