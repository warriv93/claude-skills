# claude-skills

Personal [Claude Code](https://claude.com/claude-code) skills / slash commands, version-controlled so they're easy to edit, update, and share.

## Skills

| Skill | What it does |
|-------|--------------|
| [`/deep-plan`](skills/deep-plan.md) | Front-door orchestrator: **grills** you to lock the spec, designs a deep-modular architecture, then drives spec-driven (SDD) + test-driven (TDD) implementation in context-isolated phases run by cheap subagents, one commit per passing slice, a looping verification gate, and a final human-in-the-loop review. Free — no paid API calls. Calls the `speckit-custom-plan-tdd-sdd` skill for the SDD+TDD engine. |

## Install (symlink — live editing)

Skills in this repo are symlinked into `~/.claude/` so edits here take effect immediately.
Running Claude Code exposes a file as a **skill** when it's under `~/.claude/skills/` and as
a **slash command** when it's under `~/.claude/commands/`, so we link into both.

```bash
git clone https://github.com/warriv93/claude-skills.git "$HOME/Library/CloudStorage/SynologyDrive-1/aiDir/claude-skills"

for f in "$HOME"/Library/CloudStorage/SynologyDrive-1/aiDir/claude-skills/skills/*.md; do
  name="$(basename "$f")"
  ln -sf "$f" "$HOME/.claude/skills/$name"
  ln -sf "$f" "$HOME/.claude/commands/$name"
done
```

Then in Claude Code type `/deep-plan` (or let the skill auto-trigger from its description).

## Editing an existing skill

Edit the file under `skills/`, then `git commit && git push`. Because the file is symlinked
into `~/.claude/`, the change is already live — no reinstall.

- **Body-only tweak** to an existing skill → usually picked up the next time the skill runs.
- **New skill file, or a change to the `description:` frontmatter** → start a fresh Claude Code
  session so it's re-discovered (see [Applying changes](#applying-changes--restarting)).

## Creating a new skill

A skill is just one Markdown file with YAML frontmatter. Follow these steps.

### 1. Create the file

Create `skills/<name>.md` (the `<name>` becomes the `/<name>` slash command). Use this
template:

```markdown
---
description: One or two sentences describing WHAT the skill does and WHEN to use it. This
  text is how Claude decides to auto-trigger the skill, so include the trigger phrases /
  slash-command name and the kind of request it handles.
argument-hint: <what to type after the command, e.g. a description or path>
---

# /<name> — short title

Instructions to Claude, written as if briefing an engineer. Be explicit and ordered.

## Step 1 — ...
## Step 2 — ...
```

Guidelines:
- **`description:`** is the most important line — it drives both discovery in the skill list
  and auto-triggering. Name the `/command` and the situations it applies to.
- **`argument-hint:`** is optional; it shows a placeholder when you type the command.
- The body is plain instructions. To make one skill **call another**, tell Claude to invoke
  the other skill by name (e.g. "Invoke the `speckit-custom-plan-tdd-sdd` skill"), the way
  `/deep-plan` does.
- Keep the filename kebab-case with no spaces; `skills/my-cool-skill.md` → `/my-cool-skill`.

### 2. Install it (create the symlinks)

Run the installer once — it symlinks every file in `skills/` into both `~/.claude/skills/`
and `~/.claude/commands/` (idempotent, safe to re-run):

```bash
./install.sh
```

### 3. Apply it

Start a fresh Claude Code session (see below), then type `/<name>` — or just describe the
task and let the `description:` auto-trigger it.

### 4. Commit & share

```bash
git add -A && git commit -m "feat: add /<name> skill" && git push
```

## Applying changes / restarting

There is **no `/restart` command**. To reload skill definitions from disk:

- **CLI:** quit with `/exit` (or `Ctrl+D`), then run `claude` again.
- **VS Code extension:** close the Claude Code panel and reopen it (Command Palette →
  "Claude Code", or `Cmd+Esc` / `Ctrl+Esc`). If it's stubborn, Command Palette →
  **Developer: Reload Window**.

`/clear` resets the current conversation but does not reliably re-scan new/changed skill
files — use a full relaunch when in doubt.

## Notes on this location

This repo lives in a Synology cloud-synced folder, so saves and `.git` changes sync to the
NAS (handy for backup). If Synology ever leaves a conflict copy like
`deep-plan (conflicted).md`, delete it — the symlinks always point at the real filename.

## Dependencies

- **`/deep-plan`** calls the **`speckit-custom-plan-tdd-sdd`** skill for the SDD+TDD engine.
  Optional (used only if present): the `openspec` CLI and a `grill-with-docs` skill — the
  workflow degrades gracefully when they're absent.
