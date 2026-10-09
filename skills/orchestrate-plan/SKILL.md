---
name: orchestrate-plan
description: Plan a feature or product as epics with /deep-plan, break each milestone into stories, and build them in parallel, one agent per story, driven from the Podium, a live localhost dashboard; adopts a project already planned with /deep-plan. Use for "/orchestrate-plan", "orchestrate this feature", a feature with several independent stories, or a half-done /deep-plan project.
argument-hint: <feature description, or a milestone id, or nothing to adopt>
---

# /orchestrate-plan

A **project** holds **epics**. An epic is a product brief, or a theme that groups related runs. Its **milestones** are the `/deep-plan` runs that deliver it, and a milestone's **stories** are the user-story slices of its `tasks.md`. This skill plans the active milestone through deep-plan, breaks it into stories, dispatches one agent per story into its own worktree, merges each back, and hands the milestone to deep-plan's quality gate. The **Podium**, a live localhost dashboard, shows all of it and is where the user plans milestones and assigns stories.

Outside Claude Code (Antigravity, Gemini): activate the `claude-tool-map` skill first and translate every tool, model and command through it.

Start every turn by reading deep-plan's ledger (`.deep-plan/state.md`) and `podium.py status`, and resume from them. `.deep-plan/` holds deep-plan history but no `podium.json` → Phase 0.

## Run state — `.deep-plan/`

deep-plan's ledger and files stay deep-plan's. This skill adds:

| File | Written by |
| --- | --- |
| `podium.json` | the orchestrator (this session) |
| `events.jsonl` | the orchestrator, append-only |
| `requests.jsonl` | the Podium server, append-only |
| `stories/<milestone>/<id>.md` — the story's **brief** | the orchestrator, at breakdown |
| `stories/<milestone>/<id>.progress` | that story's agent, append-only |

**Single writer:** every file has exactly one writer, so parallel agents never race.

**`podium.py`** (`python3 <this skill>/podium/podium.py`; run it bare for its commands) is the orchestrator's only way into `podium.json` and `events.jsonl`: `status` and `get` to read, `set` to change, `commits`, `merge` and `backfill` for git. It writes atomically and keeps the file, which grows to hundreds of kilobytes, out of context. Give every change a person would want to see an `--event`.

[`podium/sample/`](podium/sample/) is the reference run: copy the shapes of `podium.json`, `events.jsonl` and `stories/*` from it. Field values:

- `epics[]`: `id`, `title`, `summary`, `spec` (its brief, if any), `milestones`, `uncovered`. Milestone ids are unique across the project.
- `active`: `{epic, milestone}` for the one milestone being planned or built, or `null`.
- `milestones[].status`: `done` `working` `todo` `draft` `parked` `later` `dropped`.
- `milestones[].phase`: `recon` `spec` `mock` `architecture` `stories` `build` `gate` `verify` `land`.
- `stories[].status`: `todo` `working` `approval` `done` `failed` `blocked` `dropped`. The Podium derives ready / waiting from `deps`.
- `deps`: ids it is blocked by (milestones among milestones, stories within a milestone). `stories[].overlapAfter`: ids it shares files with, which must merge first.
- `needsYou`: `{reason, story?}` while the run waits on the user, otherwise `null`.
- Progress lines: `<ISO time> <STAGE> <note>`, STAGE one of `STARTED` `RED` `GREEN` `REFACTOR` `CONTRACT` `COMMITTED` `FAILED`.

## Podium

- **Start:** run `python3 <this skill>/podium/server.py --dir .deep-plan` in the background. It prints its URL (port 8765, or the next free one). Record `podium: <url>` in the ledger and give the user the link. **Open it in Paseo's browser** when its MCP tools are available: `browser_list_tabs`; a tab already on the URL → leave it; otherwise `browser_new_tab` with the URL, then check its title with `browser_evaluate`. A `browser_timeout` can still open the tab, so list the tabs again before retrying. A tab whose title isn't the Podium's (Paseo's agent-opened tabs can fail to reach local servers) → `browser_close_tab` it. No working tab, or no Paseo → `open <url>`.
- **Resume:** `curl -s <url>/info`; no answer → start it again.
- **Watch:** run `python3 <this skill>/podium/watch.py --dir .deep-plan` (add `--paseo <paseo binary>` when Paseo dispatches) under `Monitor`. Each line it prints is an event to act on; [phase-3-build.md](phase-3-build.md) says how.

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
