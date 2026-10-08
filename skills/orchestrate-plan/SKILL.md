---
name: orchestrate-plan
description: Plan a feature as an epic with /deep-plan, break it into stories, and build them in parallel, one agent per story, driven from a live localhost dashboard. Use for "/orchestrate-plan", "orchestrate this feature", or a feature with several independent stories.
argument-hint: <feature description>
---

# /orchestrate-plan

The **epic** is one feature planned by `/deep-plan`; its **stories** are the user-story slices of `tasks.md`. This skill plans the epic through deep-plan, breaks it into stories, dispatches one agent per story into its own worktree, merges each back, and hands the epic to deep-plan's quality gate. The **dashboard** shows all of it and is where the user assigns stories.

Outside Claude Code (Antigravity, Gemini): activate the `claude-tool-map` skill first and translate every tool, model and command through it.

Start every turn by reading deep-plan's ledger (`.deep-plan/state.md`) and `.deep-plan/epic.json`, and resume from them.

## Run state — `.deep-plan/`

deep-plan's ledger and files stay deep-plan's. This skill adds:

| File | Written by |
| --- | --- |
| `epic.json` | the orchestrator (this session) |
| `events.jsonl` | the orchestrator, append-only |
| `requests.jsonl` | the dashboard server, append-only |
| `stories/<id>.md` — the story's **brief** | the orchestrator, at breakdown |
| `stories/<id>.progress` | that story's agent, append-only |

**Single writer:** every file has exactly one writer, so parallel agents never race. Write `epic.json` whole (to a temp file, then `mv`) so the dashboard never reads half a file, and give every change a person would want to see one `events.jsonl` line.

[`dashboard/sample/`](dashboard/sample/) is the reference run: copy the shapes of `epic.json`, `events.jsonl` and `stories/*` from it. Field values:

- `phase`: `recon` `spec` `mock` `architecture` `stories` `build` `gate` `verify` `land`.
- `stories[].status`: `todo` `working` `approval` `done` `failed` `blocked`. The dashboard derives ready / waiting from `deps`.
- `stories[].deps`: ids it is blocked by. `stories[].overlapAfter`: ids it shares files with, which must merge first.
- `needsYou`: `{reason, story?}` while the run waits on the user, otherwise `null`.
- Progress lines: `<ISO time> <STAGE> <note>`, STAGE one of `STARTED` `RED` `GREEN` `REFACTOR` `CONTRACT` `COMMITTED` `FAILED`.

## Dashboard

- **Start:** run `python3 <this skill>/dashboard/server.py --dir .deep-plan` in the background. It prints its URL (port 8765, or the next free one). Record `dashboard: <url>` in the ledger, `open <url>`, and give the user the link.
- **Resume:** `curl -s <url>/info`; no answer → start it again.
- **Watch:** run `python3 <this skill>/dashboard/watch.py --dir .deep-plan` (add `--paseo <paseo binary>` when Paseo dispatches) under `Monitor`. Each line it prints is an event to act on; [phase-3-build.md](phase-3-build.md) says how.

## Dispatcher

Paseo when its MCP tools (`create_workspace`, `create_agent`) are available; otherwise background `Agent` subagents with worktree isolation. Record the choice in `epic.json` `dispatcher`.

## Phases

Run in order. On entering a phase, read its file:

| Phase | File | Done when |
| --- | --- | --- |
| 1 | [phase-1-plan.md](phase-1-plan.md) | deep-plan's Phase 2 checkpoint reached; dashboard live |
| 2 | [phase-2-breakdown.md](phase-2-breakdown.md) | every story has a brief, deps, files and model; the user has the dashboard link |
| 3 | [phase-3-build.md](phase-3-build.md) | every story merged with the contract green, or the run stopped on a failure and the user was asked |
| 4 | [phase-4-handback.md](phase-4-handback.md) | deep-plan's quality gate, verify and landing done; epic `completed` |
