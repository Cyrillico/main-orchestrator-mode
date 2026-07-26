---
name: orch
description: Main Orchestrator Mode for multi-file work — parallel reads, exclusive writes, digests, short parent context. Skip single-file edits. One pass per user turn; no nested re-review loops.
---

# Orch

**Do not use** for trivial single-file edits.

Parent **schedules / locks / merges / accepts**. Workers return digests. Parallel reads; one writer per file.

**Loop (single pass):** `plan → read (≤2) → locked writes (≤20) → verify → synthesize → accept gate once → STOP`

**Anti-loop:** do not re-orch / re-plan / nest review-of-review for the same goal because residuals remain. `clean=false` ⇒ report + named residual only (usually run accept gate once). New pass only on a **new user ask**.

**Gates:** unique ids · in-repo abs strip · empty writes serial · casefold locks · reads never write · digest ⊆ grant · deps `done|noop` only · incomplete/blocked/partial ⇒ not accepted

**Safety defaults:** skill workflow only (Claude) · pre-write `BASE` + partition · `accept_with_audit.py` once before clean · missing gate ⇒ `clean=false` but still stop

**Refs:** `references/*` · **Helpers:** `scripts/partition_write_tasks.py`, `audit_write_grant.py`, `accept_with_audit.py`

**Report:** scheduler_accepted · accept_gate · clean · files · bullets · risks · next step  
**Watchdog:** poll ~3m; one nudge; one reassign — not a full restart.

**Audit severity:** production-dependent findings without live evidence ⇒ `UNVERIFIED` (not P0/high). One pass; record the check gap and stop.
