# Phase 2 — SDD+TDD Hand-off (speckit)

Invoke **`speckit-custom-plan-tdd-sdd`** skill and drive its workflow, seeded with Spec Brief, approved mock (if any), and Phase 1 architecture:

1. `/speckit.constitution` — declare test-first (TDD) and spec-first (SDD) non-negotiable.
2. `/speckit.specify` — generate `spec.md` and create feature branch. (≤3 `[NEEDS CLARIFICATION]`).
3. `/speckit.clarify` — resolve remaining ambiguities.
4. `/speckit.checklist` — generate domain checklists.
5. `/speckit.plan` — technical blueprint honoring Phase 1 modular architecture.
6. `/speckit.tasks` — dependency-ordered, TDD-structured task list (`tasks.md`), sliced by user story with tests first in every slice.

_(Fallback if speckit unavailable: run equivalent SDD+TDD steps inline, or `/to-spec` + `/to-tickets`)._

`tasks.md` on disk closes the phase. Update `.deep-plan/state.md` and execute `/compact` before Phase 3.
