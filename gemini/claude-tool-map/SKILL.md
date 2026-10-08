---
name: claude-tool-map
description: Translates Claude Code terms in a skill (tool names, haiku/opus model tiers, slash commands, subagents) into their Antigravity equivalents. Use when a running skill names a Claude Code tool, model or command.
---

# Claude Code → Antigravity

The skills in `claude-skills` are written for Claude Code. Run them as written, translating each term through this table. A term missing from your environment → do that step inline in the main conversation and say so in one line.

| Skill says | Do in Antigravity |
| --- | --- |
| read a file / `Read` / "read its file" | `view_file` on the linked path (links are relative to the skill's own folder) |
| edit / write a file | `replace_file_content` / `write_to_file` |
| `Bash`, run `<cmd>` | `run_command` |
| `Explore` subagent, file search | `grep_search` / `find_by_name`, or a subagent |
| *cheap subagent* (`haiku`) | a subagent on Gemini Flash |
| *strong subagent* (`opus`) | a subagent on Gemini Pro (or the strongest model available) |
| invoke skill `X` / `/X` | activate the skill named `X`; not installed → do the step inline |
| `AskUserQuestion` | one message with every question, each with a recommended default |
| `/clear` (asked of the user) | ask the user to start a new conversation and re-invoke the skill; it resumes from the ledger |
| `/run` | start the app with `run_command` and drive it with the browser |
| `/security-review`, `code-review` | activate if installed; otherwise run the review inline against the same diff |
| `Monitor` on a watcher script | start it with `run_command` in the background; read its new output at the start of each turn |
| `Agent` with `isolation: "worktree"`, `run_in_background` | `git worktree add -b <branch> ../<slug> <base>`, then a subagent working in that folder |
| Paseo MCP tools (`create_workspace`, `create_agent`, …) | the same tools if Paseo's MCP server is configured; otherwise the skill's fallback |
| `CLAUDE.md` | write to `CLAUDE.md` if the project has one, else `GEMINI.md` / `AGENTS.md` |
