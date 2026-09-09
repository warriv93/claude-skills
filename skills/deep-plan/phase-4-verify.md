# Phase 4 — Verification Loop & Security Gate

1. Run **full verification contract + e2e tests**. Direct output to `.deep-plan/contract.log` (`<cmd> > .deep-plan/contract.log 2>&1`) and inspect failures via `tail -n 40 .deep-plan/contract.log`.
2. **Drive the real app (`/run`)**: check P1 journeys. For UI work, screenshot built screens and compare against mock via read-only subagent (**Cheap Model**).
3. **Security pass:** Run **`/security-review`** via subagent (**Cheap Model**) over feature diff. Treat criticals as blocking. Log findings to `.deep-plan/state-findings.md`.
4. **Fix Loop & Stash Safety Net:** If anything fails or requirement is unmet, fix, re-test, re-commit.
   - **Safety Net:** If a fix attempt fails or breaks tests, execute `git reset --hard` back to the last passing slice commit before trying another hypothesis. Never layer fixes on top of broken attempts.
   - For hard failures or regressions, run **`/diagnosing-bugs`** on **Strong Model**.
5. **Loop Budget (Escape Hatch):** Track attempts per failure in `state.md`. Stop after **3 failed attempts** on same failure or 2 rounds of gate churn, and report to user.
6. Keep looping within budget until all success criteria pass.
7. **Second Code Quality Gate (Diff-scoped):** Re-run `code-review` subagents on **Strong Model**, strictly scoped to diff introduced during Phase 4 fixes (`git diff <phase-3-end-sha>..HEAD`). Log findings to `.deep-plan/state-findings.md`.
8. Update `.deep-plan/state.md` and execute `/compact` before Phase 5.
