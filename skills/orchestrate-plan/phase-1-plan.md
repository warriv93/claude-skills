# Phase 1 — Plan the active milestone

1. **Pick the milestone:**
   - Fresh feature (no `epic.json`): write one with `epic` (`id` as a slug of the feature, `title`, one-line `summary`, `spec: "spec-brief.md"`) and a single milestone `M1` of the same title, `status: "working"`, `phase: "recon"`, empty `stories` and `artifacts`; `active: "M1"`, `needsYou: null`, `dispatcher`. Start the Podium (SKILL.md, Podium) and give the user the link.
   - `REQUEST plan <id>`, or `/orchestrate-plan <id>`: another milestone is `working` → append a `request` event saying `<id>` waits for it, and tell the user. Otherwise set `active: <id>`, its `status: "working"`, `phase: "recon"`, and append a `planned` event.
2. **Run `/deep-plan`** for the active milestone: its brief when one exists (a `draft` brief → grill its `open` questions first), otherwise the feature description. deep-plan sees `epic.json`, keeps the milestone's `phase`, `artifacts` and the epic's `needsYou` current at every checkpoint and gate, and returns here after its Phase 2 checkpoint. When deep-plan asks for a context reset, the user re-invokes `/orchestrate-plan`, and this phase resumes inside deep-plan from the ledger.
3. Set the milestone's `branch` to the feature branch speckit created, and its `spec` to the speckit folder.

Done when the ledger names Phase 3, the milestone's `spec.md` and `tasks.md` are on disk, and its `branch` is set.
