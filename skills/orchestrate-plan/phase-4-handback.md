# Phase 4 — Hand back to deep-plan

1. Stop the watcher. Set `phase: "gate"` and append a `phase` event.
2. **Run deep-plan from its Phase 3 quality gate** (read `../deep-plan/phase-3-exec.md`, section "Quality gate") and on through its Phases 4, 5 and 6. deep-plan keeps `phase` and `needsYou` current.
3. After the gate, write `quality.gate` (`findings`, `fixed`, `skipped`, `file`). After Phase 4, set each `quality.criteria[].pass`.
4. Phase 4 passes → `completed: true`, `completedAt`, and a `phase` event. The banner turns gray.
5. When deep-plan's Phase 6 closes the ledger, stop the dashboard server.

Done when `completed` is true, deep-plan's ledger is closed, and the server is stopped.
