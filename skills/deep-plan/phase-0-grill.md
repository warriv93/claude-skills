# Phase R, 0 & 0.5 — Recon, Grill, UI Mock

## Phase R — Recon

The repo answers first; the user answers only what the repo cannot.

1. **Read the ground:** `.deep-plan/project.md` (present when `/deep-app-plan` handed this milestone over — its Platform and contract blocks are settled), `CLAUDE.md`, README, `CONTEXT.md`, ADRs, package manifests, layout, test setup. Fan the search out to a cheap `Explore` subagent and take back conclusions.
2. **Write `.deep-plan/recon-note.md`** (≤1 page): stack and versions, module map, **reuse list** (existing utilities and services the feature must build on), conventions, danger zones. Greenfield → one line: "greenfield — no prior art".
3. **Size the work.** Too big for one session → run `/wayfinder` to chart it into tickets and stop there. One buildable chunk → continue.
4. Checkpoint.

## Phase 0 — Grill until the spec is unambiguous

1. Restate the request and the objective as you understand it.
2. **Confirm the platform in one line** — repo host, hosting target, DB, auth — for a yes/no.
3. **Grill in proportion to scope**, skipping everything the recon note already answers:
   - **Small (1–3 files):** 1–2 targeted questions, or proposed defaults to confirm.
   - **Medium (3–10 files):** 3–5 questions covering the main flow and edge cases.
   - **Large / cross-cutting:** full `/grill-with-docs` (`/grilling` + `/domain-modeling`).
4. Resolve factual unknowns with `/research` on primary sources.
5. **Write `.deep-plan/spec-brief.md`:** objectives, features, constraints, non-goals, resolved decisions, success criteria.
6. **Gate:** the user explicitly signs off the Spec Brief. Then checkpoint.

## Phase 0.5 — Mock the UI (frontend work only)

No UI surface → one line, "no UI surface — skipping mock", and go to Phase 1.

1. **Build a throwaway mock** of the P1 flows with `/prototype` + `frontend-design` (+ `dataviz` for charts): fake data; P1 screens plus empty, loading, error and mobile states. Write the markup to a file and iterate with targeted edits.
2. **Publish it as an Artifact** (or serve it locally via `/run`).
3. **Walk it screen by screen** with the user: hierarchy, flow, naming; cut non-goals.
4. **Iterate on the same Artifact URL** until the user signs off.
5. **Fold the outcome back:** amend `spec-brief.md`, `CONTEXT.md` and ADRs; record the mock URL in `spec-brief.md` as the visual reference.
6. **Gate:** the user signs off the mock. Then checkpoint.

Grill and mock context is disposable. After the last sign-off of this file, ask the user to run `/clear` and re-invoke `/deep-plan`; Phase 1 starts from the ledger, `recon-note.md` and `spec-brief.md`.
