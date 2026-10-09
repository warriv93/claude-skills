# Phase 3 — Build the stories

Everything here acts on the active milestone. A story is **ready** when it is `todo`, not handed off, and every id in `deps` and `overlapAfter` is `done` (`podium.py ready`). A story is **handed off** while the user runs it in a session of their own (the Podium's copy button writes `handoffs.json`, its ✕ takes it back); that session reports through the story's progress file like any agent, so act on its lines as below. A handed-off story has no agent to stop, and when it ends (`MERGED`, or `FAILED`), release it with `curl -s -X DELETE <podium>/handoff/<id>`. A **wave** is the set of stories that are ready at the same moment.

## Watcher events

| Line | Act |
| --- | --- |
| `REQUEST assign <id>` | ready → dispatch it; otherwise append a `request` event saying what it waits on |
| `REQUEST build-all` | set `buildAll: true`, dispatch every ready story |
| `REQUEST stop` | set `buildAll: false`; running stories finish |
| `REQUEST plan <id>` | append a `request` event saying `<id>` waits for the active milestone |
| `REQUEST confirm <n>` | the user confirmed assumption `<n>` in the Podium: settle it as `confirmed` (SKILL.md, The human) |
| `REQUEST reverse <n> [note=…]` | the user reversed it: settle it as `reversed` and do the rework, the note saying what they want instead |
| `PROGRESS <id> … COMMITTED <sha>` | merge it (below) |
| `PROGRESS <id> … FAILED <why>` | a failed attempt (below) |
| `IDLE <id>`, or a subagent finished, without `COMMITTED` | a failed attempt, reason "stopped without committing" |
| `PERMISSION <id> <tool>` | unavailable and the story's first → deny it (`respond_to_permission`) with "the user is away: find another way, or log FAILED", then `set <id> denied+=1 --event denied tool=<tool>`. Otherwise flag it: `status: "approval"`, `needsYou: {reason: "<id> waits for approval: <tool>", story}`, `approval` event |
| `PERMISSION-CLEARED <id>` | `status: "working"`, `needsYou: null` |

With `buildAll` on, the next wave starts when every story of the current wave is merged.

## Dispatch

1. **Worktree on `story/<id>`**, branched from the milestone `branch`:
   - Paseo: `create_workspace` (`isolation: "worktree"`, `mode: "branch-off"`, `path`: repo root, `baseBranch`: the milestone `branch`, `branchName: "story/<id>"`), then `create_agent` (`workspaceId`, `title: "<id> · <title>"`, `provider`: the `claude/…` opus or sonnet id from `list_models`, `settings.modeId: "auto"`, `labels: {epic, story}`, `initialPrompt`: the story prompt).
   - Fallback: `Agent` with `isolation: "worktree"`, `run_in_background: true`, the story's model, and the story prompt preceded by `git switch -c story/<id>`.
2. **Record:** `podium.py set <id> status=working attempts+=1 agent=<{backend, id, workspace}> branch=story/<id> startedAt=now --event dispatched backend=… model=…`.

Story prompt, static part first (`<podium dir>` is the absolute path of the run dir's `podium/`):

```
You build one story of an epic, alone, in this worktree.
Your brief is <podium dir>/stories/<milestone>/<id>.md. Read it; it names everything you need.
Log each step by appending one line to <podium dir>/stories/<milestone>/<id>.progress:
`<ISO time> <STAGE> <note>`, STAGE one of STARTED, RED (tests written and failing), GREEN, REFACTOR, CONTRACT (contract green), COMMITTED (note = sha), FAILED (note = why).
Work test-first: RED, GREEN, REFACTOR, then run the contract.
Finish with one commit on story/<id> whose message ends with the trailer `Story: <id>`, log COMMITTED <sha>, and stop.
Stay inside the brief's files in scope and on branch story/<id>. Never push; the orchestrator merges.
```

On a retry, append: `Previous attempt failed: <reason>` and the last 40 lines of its contract output.

## Merge

`podium.py merge <id>` merges `story/<id>` into the milestone branch, runs the contract and records the outcome. Act on its first word:

- **`CONFLICT <id> 1`** → tell its agent to rebase `story/<id>` onto the milestone branch, re-run the contract and log `COMMITTED <new sha>`. **`CONFLICT <id> 2`** → a failed attempt.
- **`RED`** → the merge is undone; a failed attempt, with the printed log tail as its reason.
- **`MERGED`** → **retire** the story: Paseo `archive_workspace`, which archives its agent too; a subagent still running → `TaskStop`, then `git worktree remove`. With `buildAll` on and the wave complete, dispatch the stories it names as ready.

## Failed attempt

- **Attempt 1:** retire it, then dispatch again in a fresh worktree with the failure in the prompt; append a `retry` event.
- **Attempt 2:** stop its agent (Paseo `archive_agent`, or `TaskStop`) and keep its worktree for fixing by hand. `podium.py set <id> status=failed failure=… --event failed reason=…`, which also blocks every story that depends on it. Set `needsYou: {reason: "<id> failed — retry, skip or fix by hand?", story}`. Available → with `buildAll` on, let the current wave finish, set `buildAll: false` and ask the user in the terminal. Unavailable → keep building every story it doesn't block, and ask on `HUMAN available`.

Done when every story is `done`, or a failure has stopped the run and the user has been asked; either way, no story's agent is left running.
