# Scoped re-review prompt (再审)

Use after a fix wave. **Not** a fresh full review.

## Controller rules

- Scope = prior findings list + **fix diff only** (`FIX_BASE..HEAD` or plan-section/file slice)
- Out-of-scope notes → residual/deferred **Minor** — they do **not** extend the loop
- This re-review counts as **one** of `max_fix_rounds` (default **3** per theme)
- After a full review pass: at most **one** fix wave and **one** of these re-reviews

## Worker prompt (paste)

```text
You are re-reviewing a fix round — not doing a full re-audit.

## Scope
- Findings under verification (verbatim):
  [FINDINGS]
- Changed slice / fix range: [PATHS or FIX_BASE..HEAD]
- Prior baseline (optional): [BASELINE]

## Rules
1. Verdict each finding: ADDRESSED | NOT ADDRESSED (with path/line evidence).
2. Inspect only the fix/changed slice for new Critical/Important breakage.
3. Do NOT re-review untouched plan sections, files, or the whole repo.
4. Out-of-scope observations: list as non-blocking Minor only.
5. Production-dependent severity without live evidence → UNVERIFIED, not P0.
6. Return a short structured summary only.

## Output
- finding_verdicts: [{id, verdict, evidence}]
- new_breakage_in_slice: [...] or none
- out_of_scope_minor: [...] or none
- open_critical_important: [...]
- conclusion: ≤500 chars
```
