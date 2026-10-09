# Phase 0 — Adopt a planned project

Runs when `.deep-plan/` holds deep-plan history (ledgers, spec briefs) but no `epic.json`. The project becomes an epic whose milestones are its past and planned deep-plan runs. The existing files stay as they are.

1. **Find the runs:** every `state*.md` under `.deep-plan/`, plus runs recorded only inside another ledger's archive section. Name each run from its ledger's title line; filenames can lie.
2. **Inventory** with `Explore` subagents, about five runs each, in parallel, quoting paths:
   - the product brief: the newest top-level spec brief and its numbered items. An older, shipped product brief becomes the first milestone;
   - every milestone: id, title, status, brief, spec folder, ledger, branch, landing commit, ship date, the brief items it covers, and its dependencies, stated or implied by order and shared code;
   - each shipped milestone's stories and their commits (see Messy history);
   - gate results from each `findings-phase-3.md` / `findings-phase-4.md`, or the ledger's gate line;
   - open items: a draft brief's open questions, park reasons, brief items no milestone covers.
3. **Map statuses:** landed in git → `done`, whatever the brief's header says; brief written but not signed off → `draft`; parked → `parked`; named for later → `later`; built, then removed by the owner → `dropped` (a milestone or a story).
4. **Write `epic.json`** with `active: null` and every milestone: its stories (`status: "done"`, `commits` with sha, subject and `--shortstat`, `tasks`), `quality.gate`, `covers`, `open`, `note`, plus the epic's `uncovered` items. Compute shas, stats and timestamps with a script, never by hand. Each implied dependency and each guess goes into that milestone's `note`, in words.
5. **Backfill `events.jsonl`** from git, sorted by time, with `milestone` (and `story`) set: `planned`, `commit` per story commit, `landed`, and `status` for a park or drop date.
6. **Start the Podium and the watcher** (SKILL.md, Podium). Tell the user in one message: the link, how many milestones landed, what is next (draft, parked, later), the uncovered brief items, and how many commits belonged to no run.

## Messy history

Git wins over a ledger that disagrees with it; say so in the milestone's `note`.

- **Ids:** the run's own name from its ledger title (`v1`, `M3a`, `M005`; a bare `2b` or `005` gets an `M`). Spec-folder and branch numbers that differ, and renumbering mid-run, go in `note`. Work a ledger calls "later" or "a separate feature" with no name gets `L1`, `L2`, …. Order milestones by first commit, unstarted ones last.
- **No brief or ledger:** the milestone's `brief` is whatever plan or decision document exists.
- **Stories**, in this order of sources: `tasks.md` headings (`## S<n>`, `## Slice N`, speckit `## Phase N: User Story K`); without a `tasks.md`, the slice table in `plan.md` or the architecture file, then ledger lines, then git subjects. Ledger lines outside the slices (post-gate fixes, iterations, on-watch rounds) become one story each, id from the line (`P4`, `It1`, …), depending on the last slice. A slice not shipped inside a shipped milestone keeps `todo` with a `note` saying what waits; only the active milestone's stories can be dispatched.
- **Story `deps`:** from `tasks.md` where it states them, otherwise each story depends on the previous one.
- **Commits:** list a merged run's commits with `git log <merge>^1..<merge>^2` (no `--first-parent`, so merged sub-branches count). A run with no merge lands at its last commit or its ledger-close commit; `note` says which. A commit two stories share is listed on both, with `--shortstat` on the first only. A later commit that amends a landed run becomes story `F<n>` there; any other commit outside a run stays out of the epic and is counted in the step 6 report.
- **`quality.gate`:** `null` when no gate ran. Counts come from the status line of `findings-phase-3.md`, else the ledger or the gate commit (`file` names it); counts nobody stated are tallied and `gate.note` says so. Phase 4's result goes in `gate.note`.
- **`covers`:** the brief items a run touches, possibly none. A run that reverses a brief non-goal says so in `note`.
- **`uncovered`:** brief items no milestone covers, parked and later ones included. Items the owner cut belong in the `note` of the milestone that cut them.
- **Events:** `planned` at the earlier of the commit adding the milestone's brief and its first story commit (several milestones may share one), none for a milestone without commits. A landing commit gets `landed` instead of `commit`.

Done when every run the ledgers name has a milestone, every shipped story has its commits, and the user has the link. A `REQUEST plan <id>` then starts Phase 1 for that milestone.
