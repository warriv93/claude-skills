# Phase 4 — Hand back to deep-plan

1. Set the milestone `phase: "gate"` and append a `phase` event.
2. **Run deep-plan from its Phase 3 quality gate** (read `../deep-plan/phase-3-exec.md`, section "Quality gate") and on through its Phases 4, 5 and 6. deep-plan keeps `phase` and `needsYou` current.
3. After the gate, write the milestone `quality.gate` (`findings`, `fixed`, `skipped`, `file`). After Phase 4, set each `quality.criteria[].pass`.
4. deep-plan lands it → the milestone `status: "done"`, `landedSha`, `shippedAt`, `active: null`, and a `landed` event. Its box turns gray; with every milestone done, so does the banner.
5. Keep the Podium and watcher running for the next `REQUEST plan`; stop both when the user ends the session.

Done when the milestone is `done` and deep-plan's ledger is closed.
