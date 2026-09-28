# Phase 3 — Slice Execution & Quality Gate

## Slices

Work through `tasks.md` one slice at a time, inline in the main context:

1. Load only the current slice's task lines from `tasks.md`.
2. `/tdd`: failing tests first (RED), minimum implementation (GREEN), refactor (IMPROVE).
3. Green → commit, and add the slice's ledger line.

Every slice committed green is not yet done — the gate follows.

## Quality gate

1. Run the dual-axis `code-review` skill (Matt Pocock; Standards + Spec axes) as strong subagents under the subagent protocol, against the branch point (`git merge-base main HEAD`).
2. **Fix what it finds** — standards violations, missing spec items, scope creep, smells — refactoring under green tests (`/tdd` IMPROVE); commit as `refactor:` / `fix:`.
3. Log every finding, and the reason for each one skipped, to `.deep-plan/findings-phase-3.md`. The ledger gets one line: `Quality gate: PASS with N findings in findings-phase-3.md`.
4. Re-run the full contract until green. Record the HEAD sha in the ledger as `phase-3-end-sha`.
5. Checkpoint.
