# Phase R, 0 & 0.5 — Recon, Grill, and UI Mock

## Phase R — Recon (before you grill)

Never ask the user what the repository can already tell you, and never let a cheap subagent reinvent a module that already exists.

1. **Read the ground.** `CLAUDE.md`, `README`, `CONTEXT.md`, ADRs, package manifests, layout, test setup. Fan search out to a cheap **`Explore`** subagent (**Cheap Model**); want conclusions, not file dumps.
2. **Write Recon Note** (≤1 page into `.deep-plan/`): stack, versions, module map, **reuse list** (existing utilities/services to reuse), conventions, danger zones.
3. **Greenfield?** Say "greenfield — no prior art" in one line and move on.
4. **Size work.** If too big for one session, run **`/wayfinder`** to chart issue tickets. If buildable chunk, proceed.
5. Carry Recon Note into grill: do not ask answered questions.
6. Update `.deep-plan/state.md` and execute `/compact` before starting Phase 0.

---

## Phase 0 — Grill the user until the spec is unambiguous

1. Restate request and belief of objective.
2. **Confirm platform in one line.** State repo host, hosting target, DB, auth back for yes/no. (If brand-new app with no repo, call `/deep-app-plan`).
3. **Proportional Grilling:** Calibrate interrogation depth to feature complexity:
   - **Small Scope (1–3 files):** Ask 1–2 target questions max or state explicit proposed defaults for confirmation.
   - **Medium Scope (3–10 files):** Ask 3–5 key questions covering main flow and edge cases.
   - **Large / Cross-Cutting Scope:** Run full **`/grill-with-docs`** interrogation (`/grilling` + `/domain-modeling`).
4. **Resolve factual unknowns with `/research`** on primary sources.
5. Produce short **Spec Brief**: objectives, features, constraints, non-goals, resolved decisions, success criteria. Get explicit user sign-off. **Do not proceed without confirmation.**
6. Update `.deep-plan/state.md`. If no UI surface, execute `/compact` before Phase 1.

---

## Phase 0.5 — Mock the UI (frontend work only)

Skip for backend/CLI/data work ("no UI surface — skipping mock").

1. **Build throwaway mock** of P1 flows. Run **`/prototype`** + **`frontend-design`** (+ **`dataviz`** for charts).
   - Static/fake data, cover P1 screens + empty/loading/error/mobile states.
   - Write markup to file; iterate with targeted edits; render via Artifact tool.
2. **Publish via Artifact tool** (or local `/run`).
3. **Drive discussion:** walk screen-by-screen, interrogate hierarchy, flow, naming, cut non-goals.
4. **Iterate on same Artifact URL** until user signs off.
5. **Fold outcome back into spec:** amend Spec Brief & `CONTEXT.md` / ADRs. Keep mock URL as visual reference. Update `.deep-plan/state.md`.

**Gate:** User sign-off mandatory before Phase 1.

**Post-mock clear directive (Lever 5):** Immediately upon user sign-off, execute `/clear`. Grill and mock context is disposable. Phase 1 starts fresh, re-reading `.deep-plan/state.md`, `recon-note.md`, and `spec-brief.md` from disk.
