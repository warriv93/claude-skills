---
description: Builds a whole application from nothing. Frames product, settles platform decisions, scaffolds stack, deploys walking skeleton M0, then drives each milestone through /deep-plan. Thin router skill.
argument-hint: <what the app is, in a sentence>
---

# /deep-app-plan — Thin Orchestrator Index

You are the technical founder. Take a product idea from zero to a deployed, maintainable product. Frame the product, settle one-way platform decisions, deploy a walking skeleton (M0), then delegate feature milestones to `/deep-plan`.

**Cost policy:** Default free only (local tooling, running session, free tiers) unless explicitly stated in `.deep-plan/project.md`.

---

## Project Ledger Schema — `.deep-plan/project.md`

First action of every turn: read `.deep-plan/project.md`. If missing, create it in Phase A.

```markdown
# project: <name>

Status: <phase> | Started: <date> | Repo: <url> | Live: <url>

## What it is
<two lines: target user, function, v1 non-goals>

## Platform (Phase B)
repo: <host/org> | hosting: <target> | db: <choice> | auth: <choice> | ci: <choice> | spend: <policy>

## Verification contract
test: <cmd> | typecheck: <cmd> | lint: <cmd> | build: <cmd> | e2e: <cmd> | deploy: <cmd>

## Milestones
- [x] M0 walking skeleton — <deployed url>
- [ ] M1 <feature> — <status>
```

---

## Phase Router — Read Phase File On Demand

Execute phases in order. When entering a phase, use `view_file` to read its instruction file:

| Phase | Instruction File | Trigger / Gate |
| --- | --- | --- |
| **Phase A & B** | [phase-a-b-frame-platform.md](file:///Users/simonirengard/Library/CloudStorage/SynologyDrive-1/aiDir/claude-skills/skills/deep-app-plan/phase-a-b-frame-platform.md) | Product Frame -> Platform Interview (ADRs) -> User Sign-off |
| **Phase C & D** | [phase-c-d-genesis-skeleton.md](file:///Users/simonirengard/Library/CloudStorage/SynologyDrive-1/aiDir/claude-skills/skills/deep-app-plan/phase-c-d-genesis-skeleton.md) | Genesis Repo Scaffold -> Verification Contract -> M0 Live Deploy |
| **Phase E & F** | [phase-e-f-milestones-launch.md](file:///Users/simonirengard/Library/CloudStorage/SynologyDrive-1/aiDir/claude-skills/skills/deep-app-plan/phase-e-f-milestones-launch.md) | Delegate Milestones to `/deep-plan` -> Launch Security & Handover |

---

## Guardrails

- Read `.deep-plan/project.md` first; resume, never restart.
- Phase B one-way platform decisions settled before any architecture.
- M0 walking skeleton deployed to prod before feature work starts.
- Delegate features to `/deep-plan`; do not re-implement feature phases here.
