# claude-skills

Personal [Claude Code](https://claude.com/claude-code) skills, version-controlled so they're easy to edit, update, and share.

## Skills

| Skill | What it does |
| --- | --- |
| [`/deep-plan`](skills/deep-plan/SKILL.md) | Builds one feature into an existing codebase: recon, **grill** to lock the spec, a throwaway clickable **mock** for UI work, deep-modular architecture, SDD+TDD slices (one commit per green slice), two code-review gates, a looping verification + security gate, and a human-in-the-loop debrief. Phase instructions load on demand. |
| [`/deep-app-plan`](skills/deep-app-plan/SKILL.md) | Builds a whole app from nothing: product frame, one-way platform decisions, scaffold + CI, an M0 walking skeleton live in prod, then each milestone through `/deep-plan`, ending on a launch-readiness checklist. |

## Layout

Each skill is a folder: `skills/<name>/SKILL.md` is the entry point (frontmatter + phase router) and the sibling `phase-*.md` files are read only when the agent enters that phase. Links between them are relative, so the folder works wherever it is linked from.

## Install (symlink — live editing)

```bash
git clone git@github.com:warriv93/claude-skills.git
cd claude-skills
./install.sh
```

`install.sh` symlinks every `skills/<name>/` folder to `~/.claude/skills/<name>` (idempotent). Edits in the repo are live immediately.

`./install.sh --global` also links [`global/CLAUDE.md`](global/CLAUDE.md), my personal instructions, to `~/.claude/CLAUDE.md`, backing up any existing file to `CLAUDE.md.bak`. Leave the flag off to install only the skills.

**Antigravity / Gemini:** if `~/.gemini/config/` exists, `install.sh` also links the skills into `~/.gemini/config/skills/`, together with [`claude-tool-map`](gemini/claude-tool-map/SKILL.md), which translates the Claude Code tools, model tiers and slash commands the skills mention into their Antigravity equivalents. Each skill tells a non-Claude agent to load it first.

## Editing

- **Body or phase-file change** → picked up the next time the skill runs.
- **New skill, or a changed `description:`** → start a fresh Claude Code session so it's re-discovered.

Skill writing follows the [`writing-for-agents`](https://github.com/mattpocock/skills/tree/main/skills/productivity/writing-for-agents) reference; [CLAUDE.md](CLAUDE.md) tells Claude to load it and lists this repo's conventions.

## Creating a new skill

1. Create `skills/<name>/SKILL.md`:

   ```markdown
   ---
   name: <name>
   description: <What it does, leading word first>. Use for "/<name>", <each distinct trigger>.
   argument-hint: <what to type after the command>
   ---

   # /<name>

   <steps, each ending on a completion criterion>
   ```

   For a skill only you fire by hand, add `disable-model-invocation: true` and make the description a one-line human summary; it then costs no context.

2. `./install.sh`, restart the session, type `/<name>`.

## Dependencies

- **`/deep-plan`** calls `speckit-custom-plan-tdd-sdd` (SDD+TDD engine) and `code-review` (Matt Pocock's dual-axis). It also uses these when present: `/wayfinder`, `/grill-with-docs`, `/research`, `/prototype`, `frontend-design`, `dataviz`, `/codebase-design`, `/setup-pre-commit`, `git-guardrails-claude-code`, `/tdd`, `/security-review`, `/run`, `/diagnosing-bugs`, `/to-spec`, `/to-tickets`.
- **`/deep-app-plan`** calls `/deep-plan`, plus `/grilling`, `/domain-modeling`, `/writing-for-agents` and `/security-review`.
