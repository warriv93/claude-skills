---
name: orchestrate-deep-plans
description: Plan a feature or product as epics with /deep-plan, break each milestone into stories, and build them in parallel, one agent per story, driven from the Podium, a live localhost dashboard; adopts a project already planned with /deep-plan. Use for "/orchestrate-deep-plans", "orchestrate this feature", a feature with several independent stories, or a half-done /deep-plan project.
argument-hint: <feature description, or a milestone id, or nothing to adopt>
---

# /orchestrate-deep-plans

A **project** holds **epics**. An epic is a product brief, or a theme that groups related runs. Its **milestones** are the `/deep-plan` runs that deliver it, and a milestone's **stories** are the user-story slices of its `tasks.md`. This skill plans the active milestone through deep-plan, breaks it into stories, dispatches one agent per story into its own worktree, merges each back, and hands the milestone to deep-plan's quality gate. The **Podium**, a live localhost dashboard, shows all of it and is where the user plans milestones and assigns stories.

Outside Claude Code (Antigravity, Gemini): activate the `claude-tool-map` skill first and translate every tool, model and command through it.

Start every turn by syncing, then reading deep-plan's ledger (`.deep-plan/state.md`) and `podium.py status`, and resume from them. **Sync:** `git fetch`; the base branch behind its origin → fast-forward it, and any milestone that landed there since `podium.json` last saw it is recorded `done` with its stories and commits (Phase 0's steps for those runs). Say in one line what landed elsewhere. `podium.json` is untracked, so it never syncs between machines. `.deep-plan/` holds deep-plan history but no `podium/podium.json` → Phase 0.

**Map first, work on a start.** A bare `/orchestrate-deep-plans` only maps: sync, adopt or reconcile `podium.json` (Phase 0 when there is none), start the Podium and the watcher, and report in one message the link, what is active, done, draft, parked and later, what waits on the user, and any requests queued in `requests.jsonl` before this session. Then end the turn. Work starts only on a **start**: a Podium request that arrives while the watcher runs (plan, assign, build all), or the user naming the work, e.g. `/orchestrate-deep-plans M2` or a feature to plan. Queued requests from before the session are listed, never acted on. A milestone already mid-build resumes its merges and running agents, and dispatches nothing new.

## Run state — `.deep-plan/`

deep-plan's ledger and files stay deep-plan's. This skill keeps its own files in the run dir's `podium/` folder; paths below, and every path inside `podium.json`, are relative to the run dir:

| File | Written by |
| --- | --- |
| `podium/podium.json` | the orchestrator (this session) |
| `podium/events.jsonl` | the orchestrator, append-only |
| `podium/requests.jsonl` | the Podium server, append-only |
| `podium/human.json` | the Podium server, from its availability toggle |
| `podium/handoffs.json` | the Podium server, from its copy button |
| `podium/watcher.json` | the watcher, its heartbeat; the Podium refuses requests without it |
| `podium/stories/<milestone>/<id>.md` — the story's **brief** | the orchestrator, at breakdown |
| `podium/stories/<milestone>/<id>.progress` | that story's agent, append-only |

**Single writer:** every file has exactly one writer, so parallel agents never race.

**`podium.py`** (`python3 <this skill>/podium/podium.py`; run it bare for its commands) is the orchestrator's only way into `podium.json` and `events.jsonl`: `status` and `get` to read, `set` to change, `commits`, `merge` and `backfill` for git, `prs` for pull-request state. It writes atomically and keeps the file, which grows to hundreds of kilobytes, out of context. Give every change a person would want to see an `--event`.

[`podium/sample/`](podium/sample/) is the reference run: copy the shapes of `podium/podium.json`, `podium/events.jsonl` and `podium/stories/*` from it. Field values:

- `epics[]`: `id`, `title`, `summary`, `spec` (its brief, if any), `milestones`, `uncovered`. Milestone ids are unique across the project.
- `active`: `{epic, milestone}` for the one milestone being planned or built, or `null`.
- `milestones[].status`: `done` `working` `todo` `draft` `parked` `later` `dropped`.
- `milestones[].phase`: `recon` `spec` `mock` `architecture` `stories` `build` `gate` `verify` `land`.
- `stories[].status`: `todo` `working` `approval` `done` `failed` `blocked` `dropped`. The Podium derives ready / waiting from `deps`.
- `deps`: ids it is blocked by (milestones among milestones, stories within a milestone). `stories[].overlapAfter`: ids it shares files with, which must merge first.
- `needsYou`: `{reason, story?}` while the run waits on the user, otherwise `null`.
- `milestones[].pr`: `{number, url, state}` once its PR is open; `state` is `draft` `open` `merged` `closed`.
- `mock` (an epic's or a milestone's): `{path, url}` of its UI mock. `path` is relative to the run dir, which the Podium hosts (`../` reaches the repo, hosted under `/repo/`); `url` is a published copy, such as a claude.ai artifact. A milestone artifact with `phase: "mock"` counts as its mock. The Podium shows a 🎨 link on the card, the page title and the sheet.
- Progress lines: `<ISO time> <STAGE> <note>`, STAGE one of `STARTED` `RED` `GREEN` `REFACTOR` `CONTRACT` `COMMITTED` `FAILED`.

## Podium

- **Start:** run `python3 <this skill>/podium/server.py --dir .deep-plan` in the background. It prints its URL (port 8765, or the next free one). Record `podium: <url>` in the ledger and give the user the link: the URL in your reply, with a sentence on what it shows (the pipeline stepper; the epic, milestone and story maps with live status; the activity feed; the buttons to plan a milestone, assign stories or build all; the Available/Away toggle). **Open it in Paseo's browser** when its MCP tools are available: `browser_list_tabs`; a tab already on the URL → leave it; otherwise `browser_new_tab` with the URL, then check its title with `browser_evaluate`. A `browser_timeout` can still open the tab, so list the tabs again before retrying. A tab whose title isn't the Podium's (Paseo's agent-opened tabs can fail to reach local servers) → `browser_close_tab` it. No working tab, or no Paseo → the link is enough.
- **Resume:** `curl -s <url>/info`; no answer → start it again.
- **Watch:** run `python3 <this skill>/podium/watch.py --dir .deep-plan` (add `--paseo <paseo binary>` when Paseo dispatches) under `Monitor`. Each line it prints is an event to act on; [phase-3-build.md](phase-3-build.md) says how.

## The human

The user is **available** or **unavailable**; `podium.py human` says which and until when. Their hours decide (`human.hours` in `podium.json`, `{days: "Mon-Fri", from: "07:00", to: "17:00"}` by default, local time) unless the Podium's toggle overrides them until the next change of hours. The user invoking `/orchestrate-deep-plans` themselves makes them available for the session, whatever their hours: flip the toggle to `available` (a watcher event or an agent finishing is not an invocation). The user says in the terminal they're leaving or back → flip the toggle for them: `curl -s -X POST <podium>/human/<unavailable|available|auto>`, plus `?until=HH:MM` for another end. The watcher prints `HUMAN <mode>` on every flip; append a `human` event (`set . --event human mode=<mode>`).

- **Available:** ask as each phase says.
- **Unavailable:** keep the run moving on your own judgement. Every question a phase or deep-plan would put to the user, sign-off gates and the grill included, becomes an **assumption**: take the option you'd recommend, record it with `podium.py assume "<question>" "<choice>" "<why>" [--story <id>]`, and carry on. Skip a context reset deep-plan would ask for.
- **Landing while unavailable:** once the milestone passes verify, open its PR through `/create-pr` without `--ready`. A draft PR is the one push the run makes on its own; the Podium lists every draft PR under Needs you.
- **Waits for the user either way:** everything else that leaves the machine or can't be undone: merging, marking a PR ready, deleting. Set `needsYou` for it and go on with the work that doesn't depend on it; when none is left, wait for `HUMAN available`.
- **`HUMAN available`:** run `podium.py prs`, link the draft PRs, and put the open assumptions (`podium.py assumptions`) to the user in `AskUserQuestion` rounds, your choice as the recommended option. Settle each with `set . assumptions.<n>.status=<confirmed|reversed> --event settled question=… status=…`. A reversal is rework: amend the planning file it touched, and send a story it shaped back to `todo` with the answer in its brief.

## Dispatcher

Paseo when its MCP tools (`create_workspace`, `create_agent`) are available; otherwise background `Agent` subagents with worktree isolation. Record the choice in `podium.json` `dispatcher`.

## Phases

Run in order. On entering a phase, read its file:

| Phase | File | Done when |
| --- | --- | --- |
| 0 (adopting only) | [phase-0-adopt.md](phase-0-adopt.md) | every run in an epic in `podium.json`, history backfilled; the user has the link |
| 1 | [phase-1-plan.md](phase-1-plan.md) | the active milestone reached deep-plan's Phase 2 checkpoint; Podium live |
| 2 | [phase-2-breakdown.md](phase-2-breakdown.md) | every story has a brief, deps, files and model; the user has the Podium link |
| 3 | [phase-3-build.md](phase-3-build.md) | every story merged with the contract green, or the run stopped on a failure and the user was asked |
| 4 | [phase-4-handback.md](phase-4-handback.md) | deep-plan's quality gate, verify and landing done; the milestone `done` |
