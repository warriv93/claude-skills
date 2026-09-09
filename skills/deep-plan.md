---
description: Builds one feature end to end in a project that already exists: reads the codebase, GRILLS the user until the spec is unambiguous, puts a clickable UI mock in front of them to sign off, then runs SDD+TDD implementation through context-isolated subagents with quality gates, a verification loop, and a final review before the PR. Resumable across sessions; free by default. Use for "/deep-plan", "plan and build feature X", or a rigorous end-to-end feature build. For a brand-new product with no repo or host yet, use /deep-app-plan.
argument-hint: <feature description>
---

# /deep-plan — Recon → Grill → Mock → Spec → SDD+TDD → Review → Verify → Review → HITL → Land

You are an AI software engineer. Your job is to take a feature idea and drive it to a
**verified, spec-conformant implementation** — built with deep modular architecture,
specification-driven development (SDD), and test-driven development (TDD).

**Scope:** this skill builds **one feature into a project that already exists** (or at least
has its stack and platform decided). Starting a whole product from nothing — no repo, no
host, no database, no pipeline — is `/deep-app-plan`, which settles that once and then calls
this skill per feature. When in doubt: is there a repo with a deploy target? Yes → here.

**Cost discipline:** free by default — local tooling and the running session only, no paid
external LLM/API calls. The one thing that can lift this is an explicit spend policy in
`.deep-plan/project.md` (set by `/deep-app-plan`); absent that, assume free. When you
delegate to subagents, prefer the **cheapest capable model** (e.g. Haiku) for
well-scoped, context-isolated work; reserve the strong model for architecture and review.

This skill is an **orchestrator** that composes other installed skills rather than
re-implementing them. It adds the connective tissue (cheap-subagent slicing, the ledger,
the commit / verification / HITL loop) and delegates the heavy lifting:

| Job                                        | Skill it calls                                             |
| ------------------------------------------ | ---------------------------------------------------------- |
| Chart work too big for one session         | `/wayfinder` (Phase R)                                     |
| Grill the spec + build the domain model    | `/grill-with-docs` (runs `/grilling` + `/domain-modeling`) |
| Research unknowns against primary sources  | `/research`                                                |
| Throwaway UI mock for the user to react to | `/prototype` + `frontend-design` (+ `dataviz` for charts)  |
| Deep-modular architecture vocabulary       | `/codebase-design`                                         |
| Write subagent prompts / agent-read docs   | `/writing-for-agents` (Phases R, 3, 6)                     |
| Tooling-enforced quality on a new repo     | `/setup-pre-commit`, `git-guardrails-claude-code`          |
| The full SDD+TDD spec→plan→tasks engine    | `speckit-custom-plan-tdd-sdd`                              |
| Red→green→refactor discipline per slice    | `/tdd`                                                     |
| Code quality gate (anti-patterns + spec)   | Matt Pocock's `code-review` (see Phase 3 gate)             |
| Cheap cleanup pass                         | `/simplify`                                                |
| Security pass                              | `/security-review`                                         |
| Drive the real app and look at it          | `/run`                                                     |
| Diagnose failures in the verification loop | `/diagnosing-bugs`                                         |

If any skill above isn't installed, do that phase's work inline instead — never block on a
missing skill, and never install/pay for anything.

Execute the phases in order. Do not skip ahead. Each phase gates the next.

Be extremely concise. Sacrifice grammar for the sake of concision.

---

## The run ledger — `.deep-plan/state.md` and `state-findings.md`

A full run outlives a context window. Compaction, a crash, or tomorrow morning must not
lose the thread. **First action of every invocation:** read `.deep-plan/state.md`.

- **It exists** → summarise where the run stopped, confirm with the user, resume at the
  first incomplete phase. Do **not** restart from Phase R.
- **It doesn't** → create it, then start at Phase R.

**Strict size cap:** `.deep-plan/state.md` MUST remain under **60 lines total**. It is a
high-level status ledger, not a diary. Each slice gets exactly 1 line (`- [x] <slice> — <sha> — PASS`).

**Split detailed findings to `state-findings.md`:** Write verbose quality gate findings,
defect discussions, error tracebacks, and security review notes to `.deep-plan/state-findings.md`
(append-only). Never paste multi-paragraph finding reports into `state.md`. `state.md` carries only
high-level pass/fail statuses and points to `state-findings.md` for details (read during Phase 5 debrief).

Rewrite `state.md` at every phase boundary and every gate — before the phase's work, not after
you've forgotten.

```markdown
# deep-plan: <feature>

Branch: <feature branch> | Started: <date> | Phase: <current> | Status: <in progress|blocked|done>

## Verification contract (Phase 1 — the definition of green)

test: <cmd> | typecheck: <cmd> | lint: <cmd> | build: <cmd> | e2e: <cmd>

## Platform (from recon, or set by `/deep-app-plan`)

repo: <host/org, visibility> | hosting: <target> | db: <choice> | auth: <choice> | ci: <choice>

## Artifacts

Spec Brief: <path> | spec.md: <path> | tasks.md: <path> | Mock: <URL> | Recon Note: <path> | Findings: .deep-plan/state-findings.md

## Phases

- [x] R recon — <one line>
- [ ] 0 grill … (one line each through Phase 6)

## Slices (Phase 3)

- [x] <slice> — <commit sha> — PASS

## Open findings / deferred

- <finding> — <why deferred> (see state-findings.md for details)

## Loop budget

Phase 4 attempts on current failure: <n>/3

## Resume

Next action: <the one thing the next session does first>
```

---

## Conducting — thin window + phase-boundary compaction

Phases 0 and 0.5 are an interactive conversation with the user. Once the mock is signed off, Phase 1 starts.

To prevent context accumulation and token spikes, follow these rules:

1. **`/clear` after Phase 0.5 mock sign-off (Lever 5):** The grill and mock conversation is disposable once sign-off is achieved. `/clear` resets the window before starting Phase 1. All agreed decisions live on disk in `spec-brief.md`, `recon-note.md`, and `CONTEXT.md`.
2. **Execute Phase 3 slices sequentially inline (Lever 2):** Slices are executed inline in the main window using `/tdd`. This avoids context duplication from spawning full-context subagents per slice. Each slice commits immediately on pass.
3. **Reserve subagents for read-only & isolated gates (Lever 2):** Use subagents ONLY for tasks that produce heavy logs/images or independent reviews:
   - Phase R recon fan-out (`Explore` subagent)
   - Phase 3 & 4 Code Quality Gates (`code-review` subagents on strong model)
   - Phase 4 Verification & Screenshot comparison (keeps images/DOM dumps out of main window)
   - Phase 4 Security Pass (`/security-review`)
   - `/diagnosing-bugs` loop when stuck
4. **Cap the ledger & split findings (Lever 3):** Keep `state.md` ≤60 lines (1 line per slice). Append detailed findings and logs to `.deep-plan/state-findings.md`.
5. **Automated `/compact` at phase boundaries (Lever 1):** Execute `/compact` at every phase transition (after R, Phase 0, Phase 1, Phase 2, Phase 3, Phase 4). Disk files (`state.md`, `state-findings.md`, `spec.md`, `tasks.md`) preserve state across compactions.

**Subagent Dispatch Table** — cheapest capable model unless row specifies otherwise:

| Unit                             | Gets                               | Returns (≤10 lines)            |
| -------------------------------- | ---------------------------------- | ------------------------------ |
| Phase R recon fan-out            | the repo                           | Recon Note path, stack, risks  |
| Each quality gate (strong model) | branch point, `spec.md`, standards | findings summary, fixes, skips |
| Phase 4 contract + e2e + `/run`  | contract, `spec.md`, mock URL      | pass/fail verdict per story    |
| Phase 4 security pass            | the feature diff                   | findings by severity           |
| A `/diagnosing-bugs` loop        | the failure, the contract          | cause, fix, result             |

Screenshots and full test logs must never be loaded into the main window — subagents evaluate them and return a ≤10-line verdict.

**Unattended to Phase 5.** After the mock gate, run to completion without waiting on the user.
Park at the Phase 5 debrief, or earlier at a loop-budget escalation — those are the only two
places a finished-feature run stops. If a session ends mid-run anyway, the ledger resumes it
cold; that is what it is for.

---

## Phase R — Recon (before you grill)

Never ask the user what the repository can already tell you, and never let a cheap
subagent reinvent a module that already exists.

1. **Read the ground.** `CLAUDE.md` and `~/.claude/rules`, `README`, `CONTEXT.md`, ADRs,
   package manifests + lockfile, directory layout, the test setup, CI config. Fan the
   search out to a cheap **`Explore`** subagent; you want conclusions, not file dumps.
2. **Write a Recon Note** (≤1 page, into `.deep-plan/`): stack and versions; the module
   map; the **reuse list** — existing utilities, components, services and patterns this
   feature must use instead of rebuilding; naming and layering conventions; danger zones
   (untested code, known-fragile areas, generated files). This note is quoted into Phase 3
   subagent prompts, so write it for a stranger.
3. **Greenfield?** Say "greenfield — no prior art" in one line and move on; the stack
   decision belongs to the grill.
4. **Size the work.** If the effort is too big for one agent session — many unknowns, the
   route to the destination genuinely foggy, multi-week scope — **run `/wayfinder`** to
   chart it as a map of investigation tickets on the repo's issue tracker and resolve them
   one at a time until the way is clear. Each resolved ticket feeds Phase 0; re-enter
   `/deep-plan` per buildable chunk the map exposes. (`/wayfinder` wants an issue tracker —
   `/setup-matt-pocock-skills` once, else it falls back to local markdown.) If the work
   fits one run, say so and go straight to Phase 0.
5. Carry the Recon Note into the grill: every question it already answers is a question
   you do not ask.
6. Update `.deep-plan/state.md` and execute `/compact` (Lever 1) before starting Phase 0.

---

## Phase 0 — Grill the user until the spec is unambiguous

**Goal:** Get onto the exact same page before a single line of spec is written. Do not be
agreeable. Interrogate assumptions. You are not done until you could hand the spec to a
stranger and get back the thing the user actually wants.

1. Restate the request in your own words and list what you believe the objective is.
2. **Confirm the platform in one line — don't interview for it.** Repo host, hosting target,
   database, and auth constrain Phase 1, so they must be settled before it — but on a feature
   they already are. Take them from the Recon Note, `.deep-plan/project.md`, or the ADRs,
   state them back for a yes/no, and move on. If the project genuinely has no platform yet
   (brand-new codebase, nothing deployed), stop and run **`/deep-app-plan`** instead — that
   wrapper owns the platform interview and the walking skeleton, then hands back here for
   each feature.

3. **Run the `/grill-with-docs` skill** to drive the interrogation. It runs a `/grilling`
   session (relentless, one question at a time, with your recommended answer for each) while
   `/domain-modeling` captures the ubiquitous language and any ADRs into `CONTEXT.md` /
   `docs/adr/` as decisions crystallise. If `/grill-with-docs` isn't installed, grill inline
   instead. Either way, keep going until there are **zero blocking ambiguities**; where the
   user is unsure, propose a sensible default, state it explicitly, and get a yes/no.
   The grilling must cover:
   - **Objectives & success criteria** — what does "done" measurably look like?
   - **Users & primary flows** — who uses it, what are the P1/P2/P3 journeys?
   - **Scope boundaries** — explicit non-goals and out-of-scope items.
   - **Constraints** — language/stack, existing code to respect, performance, security,
     data, compliance, deadlines.
   - **Interfaces & dependencies** — external services, APIs, schemas, auth.
   - **Edge cases & failure modes** — what must never happen; how errors are handled.
   - **Unknowns** — anything you're guessing at. Force a decision or a documented default.
4. **Resolve factual unknowns with `/research`.** When a question is a _fact_ (library
   behavior, API shape, existing code) rather than a _decision_, run the `/research` skill
   to investigate primary sources and capture findings in the repo — don't make the user
   answer what you can look up. _(Optional: if the `openspec` CLI exists — `which openspec` —
   `openspec explore` can surface spec structure/gaps too. Never install or pay for it.)_
5. Produce a short **Spec Brief**: objectives, features, constraints, non-goals, open
   decisions (now resolved), and success criteria. Get explicit user sign-off on the Brief
   before Phase 1. **Do not proceed without confirmation.** Update `.deep-plan/state.md`.
   If there is no UI surface, execute `/compact` (Lever 1) before Phase 1.

---

## Phase 0.5 — Mock the UI (frontend work only)

**Applies when** the feature has any user-facing interface — web, mobile, desktop, browser
extension, or a TUI with real layout. **Skip** for pure backend / CLI / library / data work:
say "no UI surface — skipping mock" in one line and go to Phase 1. Words are a terrible
medium for arguing about a screen; put a thing in front of the user instead.

1. **Build a throwaway mock** of the P1 flows agreed in Phase 0. **Run the `/prototype`
   skill** (it exists exactly for "explore what a UI should look like") and pull visual
   quality from the **`frontend-design`** skill; use **`dataviz`** for any chart, dashboard,
   or stat tile. If those aren't installed, hand-roll a single self-contained HTML file.
   - Static and fake: hardcoded data, no backend, no auth, no real API calls.
   - Cover every P1 screen **plus the states that get forgotten** — empty, loading, error,
     permission-denied, long-content overflow, and mobile width.
   - Clickable where the flow matters (screen → screen), so the user can walk the journey.
   - Throwaway means throwaway. This code is **not** the implementation and must never be
     promoted into it; Phases 2–3 rebuild for real, test-first.
   - Keep the markup out of the window: write it to a file, iterate with targeted edits,
     and let the published Artifact — not a re-read of the file — be what you both look at.
2. **Put it in front of the user.** Publish the mock with the **Artifact** tool (private
   page, real URL, works on their phone) — or run it locally via the `/run` skill if the
   stack demands it. A file path they have to open themselves is not good enough.
3. **Drive the discussion.** Walk it screen by screen and interrogate, same posture as the
   grill — don't just ask "looks good?". Push on:
   - Information hierarchy — is the most important thing on each screen actually the biggest?
   - Flow — where does the journey take more steps than the user expected?
   - Naming — do the labels match the ubiquitous language in `CONTEXT.md`?
   - Missing screens/states you had to invent, and the ones they hadn't thought about.
   - What can be **cut** — a mock is the cheapest place to discover a non-goal.
4. **Iterate on the same Artifact URL** until the user signs off. Every round trip here is
   orders of magnitude cheaper than one in Phase 3.
5. **Fold the outcome back into the spec.** Amend the Spec Brief and `CONTEXT.md` / ADRs with
   what the mock settled: screen inventory, states, flows, terminology, newly-agreed
   non-goals. Keep the mock URL as the visual reference for Phases 1–3. Update `.deep-plan/state.md`.

**Gate:** no Phase 1 until the user has signed off on the mock. **Do not proceed without
confirmation.**

**Post-mock clear directive (Lever 5):** Immediately after user sign-off on the mock, execute `/clear`. The grill and mock conversation has served its purpose. Phase 1 starts fresh, re-reading `.deep-plan/state.md`, `.deep-plan/recon-note.md`, and `spec-brief.md` from disk.

---

## Phase 1 — Deep modular architecture + the verification contract

**Run the `/codebase-design` skill** and use its deep-module vocabulary and principles as
the basis for this phase (fall back to the principles below if it isn't installed). The aim
is a lot of behaviour behind small interfaces, placed at clean seams, testable through those
interfaces — designed for **testability, robustness, and understandability**:

- Decompose into deep modules with single responsibilities and narrow, explicit
  interfaces (accept interfaces / return concretes; keep interfaces 1–3 methods).
- Push dependencies to the edges; inject them via constructors so the core is pure and
  unit-testable without mocks-of-mocks.
- Define the seams that let each slice be built and tested **in isolation** — this is what
  makes context-free subagent execution possible in Phase 3.
- Note where a cheap subagent can own a whole module vs. where cross-cutting design needs
  the strong model.
- Honour the platform confirmed in Phase 0 — the target runtime is a design constraint, not a
  deployment detail (edge = no Node APIs and no long-running work; serverless = cold starts
  and no local state; document store = no joins). Keep it at the edges so the core stays
  portable, and say so out loud if the platform and the architecture are fighting.

Reuse the `CONTEXT.md` / ADRs that `/domain-modeling` produced in Phase 0, and the reuse
list from the Recon Note, so names and seams speak the project's language. If Phase 0.5 ran,
treat the signed-off mock as the authority on screens, states, and flows — derive the
view/state seams from it, and keep rendering at the edge so the core stays pure. Capture the
result as an architecture sketch feeding directly into the spec/plan.

**Then pin the verification contract.** "Run the tests" is folklore; subagents need literal
commands. Write the exact invocations into the ledger — install, test, single-test-file,
typecheck, lint, format, build, e2e — and **run each one now** to prove it works on a clean
tree. From here on, **green means every contract command exits 0**, nothing looser, and the
contract block is quoted verbatim into every Phase 3 subagent prompt.

Greenfield or a repo missing pieces: create them before Phase 2, and make the tooling
enforce quality rather than the model remembering to — **`/setup-pre-commit`** (lint-staged,
typecheck, tests on commit) and **`git-guardrails-claude-code`** (blocks destructive git).

Update `.deep-plan/state.md` and execute `/compact` (Lever 1) before Phase 2.

---

## Phase 2 — Hand off to the SDD+TDD engine (call the speckit skill)

Invoke the **`speckit-custom-plan-tdd-sdd`** skill (via the Skill tool) and drive its
nine-command workflow, seeding it with the signed-off Spec Brief, the approved mock (if
any), and the architecture from Phases R–1:

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
_(Lightweight alternative when full speckit is overkill: `/to-spec` to synthesize a spec
from this conversation and `/to-tickets` to break it into tracer-bullet slices. These need
`/setup-matt-pocock-skills` run once to know your issue tracker.)_

`tasks.md` on disk closes the phase. Update `.deep-plan/state.md` and execute `/compact` (Lever 1) before starting Phase 3.

---

## Phase 3 — Sequential inline execution + quality gates (Lever 2 & Lever 3)

Execute `tasks.md` **slice by slice sequentially inline** in the main window to maximize cache hit rates and avoid subagent context duplication:

- Execute each slice using the `/tdd` skill's discipline: write failing tests first (RED), implement minimum code to pass (GREEN), refactor (IMPROVE).
- **After a slice passes all its tests, commit it individually** on the feature branch with a clear conventional-commit message. One passing slice = one commit.
- **Update `.deep-plan/state.md` with 1 line per slice** (`- [x] <slice> — <sha> — PASS`). Keep `state.md` under **60 lines total** (Lever 3).
- Halt on any test failure; fix before moving on. Never commit red.
- If context grows large during multi-slice execution, run `/compact` mid-phase.

**Last step of Phase 3 — code quality gate.** All slices committed and green ≠ done. Review
the whole feature diff for anti-patterns and standards drift before Phase 4:

1. **Run Matt Pocock's dual-axis `code-review` skill** — Standards (repo standards + the
   Fowler code-smell baseline) and Spec (does the diff do what `spec.md` asked?), using **subagents on the strong model** (Lever 2).
   Resolution order:
   - the `code-review` skill if installed → else read and follow
     `~/.claude/vendor/mattpocock-skills/skills/engineering/code-review/SKILL.md` → else
     fetch `github.com/mattpocock/skills`, `skills/engineering/code-review/SKILL.md`.
   - **Not** the built-in `/code-review ultra` — that is billed and breaks cost discipline.
2. Fixed point = the branch point (`git merge-base main HEAD`, i.e. the commit before slice 1).
   Spec axis ← `spec.md` + Spec Brief. Standards axis ← `CONTEXT.md`, ADRs, the Recon Note's
   conventions, and any `CODING_STANDARDS.md` / `CONTRIBUTING.md` / rules files in the repo.
3. **Fix what it finds:** every hard standards violation, every missing/partial spec
   requirement, every scope-creep addition, and every judgement-call smell you agree with.
   Refactor under green tests (`/tdd` IMPROVE step); commit as `refactor:` / `fix:`.
   **Write detailed finding notes and explanations of skipped findings to `.deep-plan/state-findings.md`** (Lever 3).
   In `state.md`, record only the high-level gate status line (`Quality gate: PASS with N findings in state-findings.md`).
4. Re-run the contract. Phase 3 closes only when it is green **after** the fixes.
   Update `.deep-plan/state.md` and execute `/compact` (Lever 1) before Phase 4.

---

## Phase 4 — Verification loop (budgeted, until spec is met)

A dedicated final verification gate:

1. Run the **full verification contract** plus **e2e / integration tests** appropriate to the
   stack (Playwright for web flows; equivalent otherwise) to validate the implementation
   **against the spec**, not just against the unit tests. Send long output to a file and
   read the failures out of it — a green suite needs one line, not its log.
2. **Run the actual app** — `/run` it. Tests passing is not the same as the thing working.
   Drive the P1 journeys end to end. For UI work, screenshot each built screen and compare
   against the approved mock via a **read-only verification subagent** (Lever 2). Screenshots are expensive; subagents judge them and return a verdict so images never load into the main window.
3. **Security pass.** Run **`/security-review`** via a subagent over the feature diff (Lever 2).
   Anything touching auth, user input, secrets, file paths, SQL, or external calls gets
   scrutiny; treat criticals as blocking, not as debrief material. Log detailed findings into `.deep-plan/state-findings.md`.
4. If anything fails or a requirement is unmet, loop back: fix, re-test, re-commit. For any
   hard failure or performance regression, **run the `/diagnosing-bugs` skill** to run a
   disciplined diagnosis loop instead of guessing.
5. **Loop budget — the escape hatch.** Track attempts per distinct failure in `state.md`.
   **Three failed attempts on the same failure and you stop**: no fourth guess. Report to
   the user what you tried, what `/diagnosing-bugs` established, your best hypothesis, and
   the options — with a recommendation. Same rule for gate churn: if fixing review findings
   keeps breaking tests, stop after two rounds and escalate. A fix-break-fix cycle can eat a
   whole session; the budget is what makes the loop terminate.
6. **Keep looping** (within budget) until every success criterion in the Spec Brief and
   every acceptance scenario passes.
7. **Second code quality gate — after the loop is green.** Re-run the `code-review` subagents
   exactly as in the Phase 3 gate.
   - Fix findings, re-run contract + e2e, re-commit. Log findings to `.deep-plan/state-findings.md`.
   - Feature is "done" only when contract is green **and** code-review comes back clean.
8. Update `.deep-plan/state.md` and execute `/compact` (Lever 1) before Phase 5 debrief.

---

## Phase 5 — Human-in-the-loop review (report to the user)

Do not silently declare victory. Give the user a clear debrief (compiled from `state.md`, `state-findings.md`, and `git log`):

- **What was accomplished** — features delivered, mapped back to the Spec Brief.
- **Compromises made** — where reality diverged from the ideal, and why. Include the
  code-review findings you consciously skipped (from `state-findings.md`).
- **Potential weak points** — fragile areas, thin test coverage, assumptions that could bite.
- **Inputs needed from you** — API keys, secrets, env vars, accounts, or manual setup the
  feature requires to actually run. List them explicitly.
- **Future improvements** — concrete next steps and ideas to make the feature more useful.

End by asking the user how they want to proceed (merge, iterate, or park).

---

## Phase 6 — Land it (docs, write-back, PR)

Runs once the user has answered Phase 5 with merge or iterate. This is the phase that makes
the _next_ feature cheaper than this one.

1. **Docs true again.** Update `CONTEXT.md` and the glossary with terms this work
   introduced, add an ADR for any architectural decision taken during Phases 1–4 that isn't
   yet recorded, refresh the README / usage docs for behaviour a user can now see.
2. **Write back to `CLAUDE.md`.** Fold in the conventions this run established or discovered
   — the verification contract commands, layering rules, patterns to follow, traps to avoid.
   This is the compounding step: it is how the codebase gets better rather than just bigger.
   Keep it terse and additive; don't restate what the code already says.
3. **Close the ledger** — final status, commits, deferred findings. Archive or delete
   `.deep-plan/state.md` and `.deep-plan/state-findings.md`; do not leave stale ledgers to confuse the next run.
4. **PR, only when the user asks for it.** On explicit go-ahead: push the branch and open a
   PR whose body is the Phase 5 debrief plus a test plan. Never push unprompted.

---

## Guardrails

- Free by default: no paid API/LLM calls unless the project spend policy explicitly allows
  it. Say what something costs before spending it.
- Read `.deep-plan/state.md` first, write it at every gate, resume rather than restart.
- Strictly cap `.deep-plan/state.md` to ≤60 lines total (1 line per slice). Detailed findings, gate reports, and trace logs go into `.deep-plan/state-findings.md` (Lever 3).
- Execute `/clear` immediately after Phase 0.5 mock sign-off before starting Phase 1 (Lever 5).
- Execute `/compact` at every phase boundary (after R, Phase 0, Phase 1, Phase 2, Phase 3, Phase 4) (Lever 1).
- Execute Phase 3 implementation slices sequentially inline using `/tdd`; reserve subagents exclusively for independent read-only tasks (recon fan-out, code quality gates, security review, verification/screenshot review) (Lever 2).
- A decision that exists only in the conversation is lost — write it to its file first.
- Never write production code before the Spec Brief is signed off (Phase 0), the mock is
  approved if there's a UI (Phase 0.5), and tasks exist (Phase 2). The Phase 0.5 mock is the
  one exception — it's throwaway, and it never gets promoted into the implementation.
- Compose, don't reimplement: prefer the mapped skills (`/wayfinder`, `/grill-with-docs`,
  `/research`, `/prototype`, `frontend-design`, `/codebase-design`,
  `speckit-custom-plan-tdd-sdd`, `/tdd`, `code-review`, `/simplify`, `/security-review`,
  `/run`, `/diagnosing-bugs`) over redoing their work inline; fall back to inline only when
  one isn't installed.
- Platform decisions (repo host, hosting target, database, auth) belong to `/deep-app-plan`
  or to recon — confirm them in Phase 0, never re-interview, never re-litigate later.
- Green is the verification contract exiting 0 — not "the test I remembered to run".
- Two code quality gates, both mandatory: end of Phase 3 and end of Phase 4. Green tests are
  not a quality signal — anti-patterns pass tests.
- Three strikes on one failure, or two rounds of gate churn, and you stop and escalate.
- Reuse before you build: the Recon Note's reuse list beats a fresh implementation.
- No new runtime dependency without saying so and why; subagents may not add one unasked.
- One commit per passing slice; never commit failing tests; never push without being asked.
- Prefer the cheapest capable model for isolated subagents; strong model for design + review.
