# Phase 4 — Verification Loop & Security Gate

Done when every success criterion in `spec-brief.md` passes — or the loop budget is spent and reported.

1. **Full contract + e2e.**
2. **Drive the real app (`/run`)** through every P1 journey. UI work: screenshot the built screens and have a cheap subagent compare them against the mock.
3. **Security pass:** `/security-review` as a cheap subagent under the subagent protocol, over the feature diff. Criticals block. Log to `.deep-plan/findings-phase-4.md`.
4. **Fix loop:** for each failure or unmet requirement, fix, re-test, re-commit.
   - Each hypothesis starts from the last green slice commit: a failed attempt, or one that breaks tests, is discarded with `git reset --hard <last-green-sha>` before the next.
   - Hard failures and regressions → `/diagnosing-bugs` as a strong subagent.
   - **Loop budget:** count attempts per failure in the ledger. At 3 failed attempts on one failure, or 2 rounds of gate churn, stop and report to the user.
5. **Second code-review gate:** `code-review` strong subagents under the subagent protocol, scoped to `git diff <phase-3-end-sha>..HEAD`. Log to `.deep-plan/findings-phase-4.md`.
6. Checkpoint.
