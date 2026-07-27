---
name: orch
description: Use when multi-file work needs parallel read-only explore, exclusive per-file writes, and short digests via /orch or multi-agent orchestration. Skip trivial single-file edits.
---

# Orch

Parent schedules/locks/merges/accepts. Workers return digests. One writer per file.

**When not:** trivial single-file edit → edit directly.

**Pass (once per user turn):** `plan → read(≤2) → writes(≤20) → verify → synthesize → accept gate once → STOP`

**Hard stop (anti-loop):**
- Same goal: do not re-orch / re-Workflow because residuals, digests untrusted, or `clean=false`
- Per theme: **max_fix_rounds=3** (each = fix dispatch + scoped re-review); then park/BLOCKED and stop
- After full review: **≤1 fix wave + ≤1 scoped re-review** — no second wave
- Minor / `UNVERIFIED` / `accept_gate pending` do **not** open a new review loop
- Re-review: changed slice only — see `references/re-review-prompt.md`

**Claude:** only `workflows/main-orchestrator-mode.js` (never `/tmp` scripts).  
**Safety:** pre-write `BASE`; `scripts/accept_with_audit.py` once if writes landed; report `scheduler_accepted` / `accept_gate` / `clean`.

**Details:** `references/orchestrator-contract.md` · helpers in `scripts/`  
**Watchdog:** poll ~3m; one nudge; **one** reassign per stall.
