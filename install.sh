#!/usr/bin/env bash
# Symlink every skill in this repo into ~/.claude so Claude Code picks them up
# as both skills and slash commands. Re-run any time; it's idempotent.
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "$HOME/.claude/skills" "$HOME/.claude/commands"

for f in "$repo_dir"/skills/*.md; do
  name="$(basename "$f")"
  ln -sf "$f" "$HOME/.claude/skills/$name"
  ln -sf "$f" "$HOME/.claude/commands/$name"
  echo "linked $name -> skills/ and commands/"
done

echo "Done. Type /${name%.md} in Claude Code (restart the session to pick up new skills)."
