---
description: Front-door orchestrator for building a feature the right way. First GRILLS the user with an interview to lock the specification, then drives deep-modular, spec-driven (SDD) + test-driven (TDD) implementation in context-isolated phases runnable by cheap subagents, one commit per passing phase, a looping verification gate, and a final human-in-the-loop review. Free — no paid API/LLM calls. Use when the user says "plan and build feature X", "/deep-plan", or wants a rigorous end-to-end plan+build.
argument-hint: <feature or project description>
---

# /deep-plan — Grill → Spec → Deep-Modular SDD+TDD → Verify → HITL Review

You are an AI software engineer. Your job is to take a feature/project idea and drive it
to a **verified, spec-conformant implementation** — built with deep modular architecture,
specification-driven development (SDD), and test-driven development (TDD).

**Cost discipline (non-negotiable):** Use only local tooling and the running session.
Do **not** call any paid external LLM/API service. Everything here is free. When you
delegate to subagents, prefer the **cheapest capable model** (e.g. Haiku) for
well-scoped, context-isolated work; reserve the strong model for architecture and review.

This skill is an **orchestrator**. It adds the parts that pure SDD/TDD tooling lacks
(the grilling interview, upfront research, cheap-subagent slicing, human review) and then
**calls the `speckit-custom-plan-tdd-sdd` skill** to run the actual SDD+TDD engine.

Execute the phases in order. Do not skip ahead. Each phase gates the next.

---

## Phase 0 — Grill the user until the spec is unambiguous

**Goal:** Get onto the exact same page before a single line of spec is written. Do not be
agreeable. Interrogate assumptions. You are not done until you could hand the spec to a
stranger and get back the thing the user actually wants.

1. Restate the request in your own words and list what you believe the objective is.
2. **Interview / grill the user.** Ask focused questions — a few at a time, not a wall —
   covering:
   - **Objectives & success criteria** — what does "done" measurably look like?
   - **Users & primary flows** — who uses it, what are the P1/P2/P3 journeys?
   - **Scope boundaries** — explicit non-goals and out-of-scope items.
   - **Constraints** — language/stack, existing code to respect, performance, security,
     data, compliance, deadlines.
   - **Interfaces & dependencies** — external services, APIs, schemas, auth.
   - **Edge cases & failure modes** — what must never happen; how errors are handled.
   - **Unknowns** — anything you're guessing at. Force a decision or a documented default.
   Keep grilling until there are **zero blocking ambiguities**. Where the user is unsure,
   propose a sensible default, state it explicitly, and get a yes/no.
3. **Optional research boosters (only if available — never install/pay):**
   - If the `openspec` CLI exists (`which openspec`), use `openspec explore` to surface
     spec structure and gaps for this problem domain.
   - If a `grill-with-docs` skill/command is installed (Matt Pocock's docs-grounded
     interrogation), invoke it to pressure-test the design against real library docs.
   - If neither is present, skip silently and do the grounding yourself from local docs
     and the codebase. Do not block on these.
4. Produce a short **Spec Brief**: objectives, features, constraints, non-goals, open
   decisions (now resolved), and success criteria. Get explicit user sign-off on the Brief
   before Phase 1. **Do not proceed without confirmation.**

---

## Phase 1 — Deep modular architecture

Before any tasks, design for **testability, robustness, and understandability**:

- Decompose into small modules with single responsibilities and narrow, explicit
  interfaces (accept interfaces / return concretes; keep interfaces 1–3 methods).
- Push dependencies to the edges; inject them via constructors so the core is pure and
  unit-testable without mocks-of-mocks.
- Define the seams that let each slice be built and tested **in isolation** — this is what
  makes context-free subagent execution possible in Phase 3.
- Note where a cheap subagent can own a whole module vs. where cross-cutting design needs
  the strong model.

Capture this as an architecture sketch feeding directly into the spec/plan.

---

## Phase 2 — Hand off to the SDD+TDD engine (call the speckit skill)

Invoke the **`speckit-custom-plan-tdd-sdd`** skill (via the Skill tool) and drive its
nine-command workflow, seeding it with the signed-off Spec Brief and architecture from
Phases 0–1:

1. `/speckit.constitution` — ensure the constitution declares **test-first (TDD)** and
   **spec-first (SDD)** as non-negotiable (add deep-modularity + cost-discipline principles).
2. `/speckit.specify` — turn the Brief into `spec.md`. This **creates the feature branch**.
   Carry over resolved decisions so there are ≤3 `[NEEDS CLARIFICATION]` markers.
3. `/speckit.clarify` — resolve any remaining ambiguity (should be minimal after Phase 0).
4. `/speckit.checklist` — generate requirement-quality checklists for the relevant domains.
5. `/speckit.plan` — technical blueprint honoring the Phase 1 modular architecture.
6. `/speckit.tasks` — produce the dependency-ordered, **TDD-structured** task list, sliced
   by user-story phase with tests placed FIRST in every slice.

If speckit is somehow unavailable, fall back to running the equivalent SDD+TDD steps
inline — but the preferred path is to call the skill so there is no duplication.

---

## Phase 3 — Context-isolated phased execution (cheap subagents, commit per phase)

Execute `tasks.md` **phase by phase / slice by slice**, engineered so each slice can be
run by a **subagent with no prior conversation context** — maximizing token efficiency:

- Each slice's task text carries everything the subagent needs (exact file paths,
  interfaces, acceptance tests). No hidden context.
- Dispatch each independent, well-scoped slice to a **cheap-model subagent** (e.g. Haiku).
  Keep architecture/integration decisions on the strong model.
- Enforce TDD inside each slice: write the failing tests first (RED), implement the minimum
  to pass (GREEN), refactor (IMPROVE).
- **After a slice passes all its tests, commit it individually** on the feature branch with
  a clear conventional-commit message. One passing slice = one commit.
- Halt on any non-parallel failure; fix before moving on. Never commit red.

---

## Phase 4 — Verification loop (until spec is met)

A dedicated final verification gate:

1. Run the full test suite plus **e2e / integration tests** appropriate to the stack
   (Playwright for web flows; equivalent otherwise) to validate the implementation
   **against the spec**, not just against the unit tests.
2. If anything fails or a requirement is unmet, loop back: fix, re-test, re-commit.
3. **Keep looping** until every success criterion in the Spec Brief and every acceptance
   scenario passes. Only then is the feature "done".

---

## Phase 5 — Human-in-the-loop review (report to the user)

Do not silently declare victory. Give the user a clear debrief:

- **What was accomplished** — features delivered, mapped back to the Spec Brief.
- **Compromises made** — where reality diverged from the ideal, and why.
- **Potential weak points** — fragile areas, thin test coverage, assumptions that could bite.
- **Inputs needed from you** — API keys, secrets, env vars, accounts, or manual setup the
  feature requires to actually run. List them explicitly.
- **Future improvements** — concrete next steps and ideas to make the feature more useful.

End by asking the user how they want to proceed (merge, iterate, or park).

---

## Guardrails

- Free only: no paid API/LLM calls at any point.
- Never write code before the Spec Brief is signed off (Phase 0) and tasks exist (Phase 2).
- Prefer calling `speckit-custom-plan-tdd-sdd` over reimplementing SDD/TDD logic.
- One commit per passing slice; never commit failing tests.
- Prefer the cheapest capable model for isolated slices; strong model for design + review.
