# Phase 1 — Plan the epic

1. **Seed the run:** write `.deep-plan/epic.json` with `epic` (`id` as a slug of the feature, `title`, one-line `summary`, `spec: "spec.md"`), `phase: "recon"`, empty `stories` and `artifacts`, `needsYou: null`, and `dispatcher`.
2. **Start the dashboard** (SKILL.md, Dashboard) and give the user the link. The map shows planning artifacts until the stories exist.
3. **Run `/deep-plan <feature>`.** It sees `epic.json`, keeps `phase`, `artifacts` and `needsYou` current at every checkpoint and gate, and returns here after its Phase 2 checkpoint. When deep-plan asks for a context reset, the user re-invokes `/orchestrate-plan`, and this phase resumes inside deep-plan from the ledger.
4. Set `epic.branch` to the feature branch speckit created.

Done when the ledger names Phase 3, `spec.md` and `tasks.md` are on disk, and `epic.branch` is set.
