# Phase 5 & 6 — Human-in-the-loop Debrief & Landing

## Phase 5 — Human-in-the-loop Review

Give user a clear debrief compiled from `state.md`, `.deep-plan/findings-phase-3.md`, `.deep-plan/findings-phase-4.md`, and `git log`:

- **Accomplished:** delivered features mapped to Spec Brief.
- **Compromises made:** divergence from ideal, skipped code-review findings (from `findings-phase-3.md` and `findings-phase-4.md`).
- **Potential weak points:** fragile areas, thin test coverage.
- **Inputs needed:** API keys, env vars, secrets, accounts required to run.
- **Future improvements:** next concrete steps.

Ask user how to proceed (merge, iterate, park).

---

## Phase 6 — Land it

Runs once user answers with merge or iterate:

1. **Docs true again:** update `CONTEXT.md`, glossary, ADRs, README.
2. **Write back to `CLAUDE.md`:** Update `CLAUDE.md` with new verification contract commands or new layering conventions. **Crucial rule:** Preserve existing hard-won rules and bug-prevention traps — never arbitrarily prune active rules to hit an arbitrary line count. Correct any lines that newly shipped code contradicts. Keep new additions terse and additive. If `CLAUDE.md` grows excessively large, split specialized domain rules into `.claude/rules/` rather than deleting established project knowledge.
3. **Close ledger:** mark final status in `state.md`, then archive or delete `.deep-plan/state.md` and all `.deep-plan/findings-phase-*.md` files.
4. **PR:** Push branch and open PR ONLY when explicitly requested by user.
