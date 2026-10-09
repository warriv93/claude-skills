---
name: deep-plan
description: Build one feature end to end in an existing codebase — recon, grill the spec, UI mock sign-off, deep-modular architecture, SDD+TDD slices, quality gates, verification loop, PR. Use for "/deep-plan", "plan and build feature X", or a milestone handed over by /deep-app-plan.
argument-hint: <feature description>
---

# /deep-plan

Drive one feature into an existing project, from idea to a verified, spec-conformant implementation, using deep modular architecture, SDD and TDD. A brand-new app with no repo or deploy target belongs to `/deep-app-plan`.

Outside Claude Code (Antigravity, Gemini): activate the `claude-tool-map` skill first and translate every tool, model and command through it.

## Ledger — `.deep-plan/`

The **ledger** is `.deep-plan/state.md`: current phase, pinned contract commands, one line per slice (`- [x] <slice> — <sha> — PASS`), attempt counts, gate status lines. Keep it ≤60 lines; verbose output goes to sibling files:

| File | Written in |
| --- | --- |
| `recon-note.md` | Phase R |
| `spec-brief.md` | Phase 0 (amended by 0.5) |
| `mock/` | Phase 0.5 |
| `architecture.draft.md` | Phase 0, background (optional) |
| `architecture.md` | Phase 1 |
| `contract.log` | every contract run (overwritten) |
| `findings-phase-3.md`, `findings-phase-4.md` | the gate of that phase |

Start every turn by reading the ledger and resuming from it; create it if missing.

**Checkpoint** = every artifact of the phase is on disk and the ledger names the next phase, so a fresh context can resume from disk alone. End each phase on a checkpoint.

## Orchestrated runs

`.deep-plan/podium/podium.json` exists → `/orchestrate-deep-plans` owns this run:

- Change `podium.json` and `events.jsonl` only through `python3 <this skill>/../orchestrate-deep-plans/podium/podium.py`. At every checkpoint: `set milestone: phase=<phase> artifacts+=<{name, path, phase}> --event phase phase=<phase>`, one `artifacts+=` per new planning file.
- Before every question to the user and every sign-off gate, run `podium.py human`. Unavailable → orchestrate-deep-plans' rule for an unavailable user (its SKILL.md, The human) replaces asking.
- While a sign-off gate waits on the user, `set . needsYou=<{reason}>`; `set . needsYou=null` on sign-off.
- Wherever a phase asks the user to re-invoke `/deep-plan`, name `/orchestrate-deep-plans` instead.
- After Phase 2's checkpoint, return to `/orchestrate-deep-plans`. It builds the slices as stories and re-enters Phase 3 at its quality gate.

## Shared rules

- **Contract runs:** `<cmd> > .deep-plan/contract.log 2>&1`; on failure read only `tail -n 40 .deep-plan/contract.log`.
- **Subagent routing:** *cheap subagent* (`haiku`) for recon search, security pass, screenshot comparison; *strong subagent* (`opus`) for code-review gates and `/diagnosing-bugs`. Architecture is decided in the main context; a background draft is input to it.
- **Subagent protocol:** static rules at the top of the prompt, diff at the bottom (prompt-cache prefix); demand `NO_PREAMBLE` — the reply is the raw findings table only. Subagents run `git diff --stat` before pulling full diffs.
- **Commits:** one commit per green slice, conventional message. Pushing and opening the PR happen only on the user's explicit request.

## Phases

Run in order. On entering a phase, read its file (sibling of this `SKILL.md`):

| Phase | File | Done when |
| --- | --- | --- |
| R, 0, 0.5 | [phase-0-grill.md](phase-0-grill.md) | Spec Brief (and mock, if UI) signed off by the user |
| 1 | [phase-1-arch.md](phase-1-arch.md) | `architecture.md` written; every contract command exits 0 |
| 2 | [phase-2-sdd.md](phase-2-sdd.md) | `spec.md` + `tasks.md` on disk |
| 3 | [phase-3-exec.md](phase-3-exec.md) | every slice committed green; Phase 3 gate passed |
| 4 | [phase-4-verify.md](phase-4-verify.md) | every success criterion passes, or loop budget spent and reported |
| 5, 6 | [phase-5-6-land.md](phase-5-6-land.md) | debrief given; docs true; ledger closed |
