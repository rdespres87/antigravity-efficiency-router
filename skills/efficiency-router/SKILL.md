---
name: efficiency-router
description: >-
  Use when the user asks about Antigravity usage, quota, limits, or budget status;
  when they report hitting a usage limit (calibrate budgets); or when composing a
  subagent delegation prompt under the efficiency router rules and you want the
  standard templates.
---

# Efficiency Router

Plugin root: `~/.gemini/config/plugins/efficiency-router/`
CLI: `python ~/.gemini/config/plugins/efficiency-router/scripts/router.py <cmd>`

## Usage commands

| Situation | Command |
|---|---|
| User asks "how much have I used?" / "사용량 보여줘" | `dashboard "<artifact_dir>/router_dashboard.html"` then reply with `<agent-embed src="file:///<artifact_dir>/router_dashboard.html"></agent-embed>` (forward slashes). Add at most 2 lines of commentary. |
| Text-only quick check | `status` |
| User says they just hit a limit | `calibrate <bucket> 5h` (or `7d` for the weekly cap) |
| Status shows unmapped model names | `alias "<raw name>" <claude\|gemini_pro\|gemini_flash>` |
| Manually set a budget | `set <bucket> <5h\|7d> <tokens>` |
| Start fresh | `reset` |

Numbers come directly from the **Antigravity Language Server API (real fractions)**.
Token logging and estimates are maintained as fallback and for the 7d offload ratio.
Calibration (`calibrate`) remains available as a fallback when real API quota data is unavailable.

## Delegation templates

Read-only research (`TypeName: research`, `Model: flash`):
```
Goal: <one sentence>.
Scope: <paths / URLs>. Do not modify files.
Find: <specific questions>.
Return (<=250 words): bullets with file:line refs; "NOT FOUND" if absent. No code dumps beyond 10-line snippets.
```

Implementation (default: local `execute_local_task(role="maker")`, <=150 LOC/call; cloud `TypeName: self`, `Model: pro` ONLY for T3 or explicit user-approved cloud fallback):
```
Goal: <behavior to achieve>.
Files: <exact paths>. Do not touch: <paths>.
Constraints: <style, APIs, compat>.
Done when: <tests/commands that must pass>.
Return: list of changed files + one line each, test output summary, open issues.
```

Second opinion for a cheap main model (`TypeName: research`, `Model: pro`):
```
Problem: <summary + key code refs>.
Options considered: <A/B>.
Return: recommended option, top 3 risks, what to verify. <=200 words.
```

## Choosing the ceiling model (one-time, not per question)
The agent cannot switch its own main model, and Claude cannot be a subagent. Routing is governed by `tiered-router` (Permanent Local-First `maker`/`inquisitor` across `GREEN`/`YELLOW`/`RED` + Strict Fail-Closed):
- **Auto (best quality)**: main = Claude / Gemini Pro. Main handles T3 & orchestration; code/tests/commits -> local `maker` (`<=150 LOC`/call); Phase 3 -> local `inquisitor`; read-only cloud research -> `flash`.
- **Economy**: main = Gemini Flash. Ceiling is Gemini Pro (T3 -> `pro` subagent); code/tests/audits still go to local LM Studio first.
Only mention model switching when the premium bucket hits RED (once per conversation).
New top model released: add it as a `premium` bucket in `router_config.json` (or `alias`), then select it as main.
