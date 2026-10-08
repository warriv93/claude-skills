# Phase R, 0 & 0.5 — Recon, Grill, UI Mock

## Phase R — Recon

The repo answers first; the user answers only what the repo cannot.

1. **Read the ground:** `.deep-plan/project.md` (present when `/deep-app-plan` handed this milestone over — its Platform and contract blocks are settled), `CLAUDE.md`, README, `CONTEXT.md`, ADRs, package manifests, layout, test setup. Fan the search out to a cheap `Explore` subagent and take back conclusions.
2. **Write `.deep-plan/recon-note.md`** (≤1 page): stack and versions, module map, **reuse list** (existing utilities and services the feature must build on), conventions, danger zones. Greenfield → one line: "greenfield — no prior art".
3. **Size the work.** Too big for one session → run `/wayfinder` to chart it into tickets and stop there. One buildable chunk → continue.
4. Checkpoint.

## Phase 0 — Grill until the spec is unambiguous

1. **Open the spec page:** copy [spec-page.html](spec-page.html) to `.deep-plan/spec.html`, serve `.deep-plan/` on localhost (`python3 -m http.server 8766 --bind 127.0.0.1 -d .deep-plan` in the background; an orchestrated run's dashboard server already serves it), `open` the page and give the user the link. It renders `.deep-plan/questions.json` (shape: [questions.example.json](questions.example.json)) and `spec-brief.md` live.
2. Restate the request and the objective as you understand it.
3. **Confirm the platform in one line** — repo host, hosting target, DB, auth — for a yes/no.
4. **Grill in proportion to scope**, skipping everything the recon note already answers:
   - **Small (1–3 files):** 1–2 targeted questions, or proposed defaults to confirm.
   - **Medium (3–10 files):** 3–5 questions covering the main flow and edge cases.
   - **Large / cross-cutting:** full `/grill-with-docs` (`/grilling` + `/domain-modeling`).

   Write every round to `questions.json` as well as the chat: options as cards with one marked `recommended`, a `range` for any numeric choice, answered questions moved to `decided`. The user answers in the terminal or pastes the page's Copy answers text. **UI questions** (layout, placement, hierarchy, visual treatment) go to `uiQuestions` and are answered over the mock in Phase 0.5.

   While the user answers a round, run a background subagent on the work off the critical path: deepen `recon-note.md` where the questions touch it, and draft `.deep-plan/architecture.draft.md` for the modules the settled answers already fix, listing each assumption.
5. Resolve factual unknowns with `/research` on primary sources.
6. **Write `.deep-plan/spec-brief.md`:** objectives, features, constraints, non-goals, resolved decisions, success criteria.
7. **Gate:** the user explicitly signs off the Spec Brief. Then checkpoint.

## Phase 0.5 — Mock the UI (frontend work only)

No UI surface → one line, "no UI surface — skipping mock", and go to Phase 1.

1. **Build a throwaway mock** of the P1 flows with `/prototype` + `frontend-design` (+ `dataviz` for charts), Apple-style: fake data; P1 screens plus empty, loading, error and mobile states. Write it to `.deep-plan/mock/index.html` and iterate with targeted edits.
2. **Build the open UI questions in as live alternatives:** every `uiQuestions` entry, and every UI choice that comes up while mocking, gets a control in a floating Alternatives panel (segmented control, slider or toggle, recommended choice marked) that switches the mock between variants in place, plus a Copy choices button.
3. **Serve and open it:** the spec page's server already serves `.deep-plan/`, so `open <url>/mock/` and give the user the link.
4. **Walk it screen by screen** with the user: hierarchy, flow, naming, each alternative; cut non-goals. Iterate on the same file until the user signs off.
5. **Fold the outcome back:** each alternative's chosen variant becomes a decision in `spec-brief.md`; amend `CONTEXT.md` and ADRs; record `.deep-plan/mock/` in `spec-brief.md` as the visual reference.
6. **Gate:** the user signs off the mock. Then checkpoint.

Grill and mock context is disposable. After the last sign-off of this file, ask the user to run `/clear` and re-invoke `/deep-plan`; Phase 1 starts from the ledger, `recon-note.md` and `spec-brief.md`.
