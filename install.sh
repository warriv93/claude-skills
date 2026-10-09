#!/usr/bin/env bash
# Symlink every skill folder in this repo into ~/.claude/skills so Claude Code
# picks it up (and exposes it as /<name>). If Antigravity is installed, also link
# the skills plus the gemini/ helpers into ~/.gemini/config/skills.
# With --global, also link global/CLAUDE.md to ~/.claude/CLAUDE.md (the repo
# owner's personal instructions; skip it to get the skills only).
# Re-run any time; it's idempotent.
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

link_all() { # <target dir> <source dir>...
  local target="$1"; shift
  mkdir -p "$target"
  for src in "$@"; do
    for d in "$src"/*/; do
      name="$(basename "$d")"
      # A same-named skill installed from elsewhere (e.g. a work-specific create-pr) wins.
      if [ -e "$target/$name" ] || [ -L "$target/$name" ]; then
        current="$(readlink "$target/$name" || true)"
        if [ "$current" != "${d%/}" ]; then
          what="a folder"; [ -n "$current" ] && what="a link to $current"
          echo "kept $target/$name (already $what)"
          continue
        fi
      fi
      ln -sfn "${d%/}" "$target/$name"
      echo "linked $name -> $target/$name"
    done
  done
}

link_all "$HOME/.claude/skills" "$repo_dir/skills"

if [ "${1:-}" = "--global" ]; then
  global_md="$HOME/.claude/CLAUDE.md"
  if [ -e "$global_md" ] && [ ! -L "$global_md" ]; then
    mv "$global_md" "$global_md.bak"
    echo "backed up existing $global_md -> $global_md.bak"
  fi
  ln -sfn "$repo_dir/global/CLAUDE.md" "$global_md"
  echo "linked global/CLAUDE.md -> $global_md"
fi

if [ -d "$HOME/.gemini/config" ]; then
  link_all "$HOME/.gemini/config/skills" "$repo_dir/skills" "$repo_dir/gemini"
fi

echo "Done. Restart Claude Code / Antigravity to pick up new skills."
