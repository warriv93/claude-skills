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
git clone https://github.com/warriv93/claude-skills.git ~/dev/claude-skills

for f in ~/dev/claude-skills/skills/*.md; do
  name="$(basename "$f")"
  ln -sf "$f" "$HOME/.claude/skills/$name"
  ln -sf "$f" "$HOME/.claude/commands/$name"
done
```

Then in Claude Code type `/deep-plan` (or let the skill auto-trigger from its description).

## Editing

Edit the files under `skills/`, then `git commit && git push`. Because they're symlinked,
changes are live in Claude Code with no reinstall.

## Dependencies

- **`/deep-plan`** calls the **`speckit-custom-plan-tdd-sdd`** skill for the SDD+TDD engine.
  Optional (used only if present): the `openspec` CLI and a `grill-with-docs` skill — the
  workflow degrades gracefully when they're absent.
