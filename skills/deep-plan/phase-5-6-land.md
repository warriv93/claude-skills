# Phase 5 & 6 — Debrief & Landing

## Phase 5 — Human-in-the-loop debrief

Compile from the ledger, `findings-phase-3.md`, `findings-phase-4.md` and `git log`:

- **Accomplished:** delivered features mapped to the Spec Brief.
- **Compromises:** divergence from the ideal; every skipped code-review finding.
- **Weak points:** fragile areas, thin test coverage.
- **Inputs needed:** API keys, env vars, secrets, accounts required to run it.
- **Next steps:** concrete follow-ups.

Ask the user: merge, iterate, or park.

## Phase 6 — Land it

Runs when the user answers merge or iterate:

1. **Docs true again:** `CONTEXT.md`, glossary, ADRs, README.
2. **Write back to `CLAUDE.md`:** add new contract commands and layering conventions, tersely. Existing rules are hard-won bug traps — keep every one; edit only lines the shipped code contradicts. When the file grows unwieldy, move domain-specific rules into `.claude/rules/`.
3. **Close the ledger:** mark the final status, then archive or delete this feature's `.deep-plan/` files. `project.md` belongs to `/deep-app-plan` and stays.
4. **PR:** push and open it when the user asks for it.
