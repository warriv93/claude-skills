---
description: Builds one feature end to end in a project that already exists: reads codebase, GRILLS user, UI mock sign-off, SDD+TDD execution, quality gates, verification loop, and PR. Thin router skill; phase details loaded on demand. Use for "/deep-plan", "plan and build feature X".
argument-hint: <feature description>
---

# /deep-plan — Thin Orchestrator Index

You are an AI software engineer. Drive a feature idea to a verified, spec-conformant implementation using deep modular architecture, SDD, and TDD.

**Scope:** Builds one feature into an existing project. (For brand-new apps with no repo/deploy target, call `/deep-app-plan`).

**Cost discipline & Subagent Model Routing Matrix:**
- **Cheap Model (`haiku` / `flash`):** Recon search (`Explore`), Security pass (`/security-review`), file finding, UI screenshot verification.
- **Strong Model (`opus` / `pro`):** Phase 1 architecture, Phase 3 & 4 Code Quality Gates (`code-review`), and `/diagnosing-bugs`.

## Mapped Skills

| Job | Skill Called |
| --- | --- |
| Sizing / Foggy roadmap | `/wayfinder` |
| Grill & Domain Model | `/grill-with-docs` (`/grilling` + `/domain-modeling`) |
| Fact Research | `/research` |
| UI Prototype Mock | `/prototype` + `frontend-design` + `dataviz` |
| Deep Modular Architecture | `/codebase-design` |
| Agent Docs & Prompts | `/writing-for-agents` |
| Quality Enforcement | `/setup-pre-commit`, `git-guardrails-claude-code` |
| SDD+TDD Engine | `speckit-custom-plan-tdd-sdd` |
| Red-Green-Refactor | `/tdd` |
| Code Quality Gate | `code-review` (Matt Pocock) |
| Security Scan | `/security-review` |
| App Runtime Drive | `/run` |
| Bug Diagnosis | `/diagnosing-bugs` |

---

## Ledger Schema — `.deep-plan/state.md` & Per-Phase Findings

First action of every turn: read `.deep-plan/state.md`. If missing, create it.
- **Strict Cap:** `.deep-plan/state.md` MUST stay **≤60 lines total**. (1 line per slice: `- [x] <slice> — <sha> — PASS`).
- **Per-Phase Findings Split:** Write verbose findings to phase-isolated files: `.deep-plan/findings-phase-3.md` and `.deep-plan/findings-phase-4.md`. Never merge all findings into a single global file.

---

## Phase Router — Read Phase File On Demand

Execute phases in order. When entering a phase, use `view_file` to read its instruction file:

| Phase | Instruction File | Trigger / Gate |
| --- | --- | --- |
| **Phase R, 0, 0.5** | [phase-0-grill.md](file:///Users/simonirengard/Library/CloudStorage/SynologyDrive-1/aiDir/claude-skills/skills/deep-plan/phase-0-grill.md) | Recon -> Proportional Grill -> UI Mock -> User Sign-off -> `/clear` |
| **Phase 1** | [phase-1-arch.md](file:///Users/simonirengard/Library/CloudStorage/SynologyDrive-1/aiDir/claude-skills/skills/deep-plan/phase-1-arch.md) | Architecture -> Verification Contract -> `/compact` |
| **Phase 2** | [phase-2-sdd.md](file:///Users/simonirengard/Library/CloudStorage/SynologyDrive-1/aiDir/claude-skills/skills/deep-plan/phase-2-sdd.md) | speckit SDD -> `spec.md` + `tasks.md` -> `/compact` |
| **Phase 3** | [phase-3-exec.md](file:///Users/simonirengard/Library/CloudStorage/SynologyDrive-1/aiDir/claude-skills/skills/deep-plan/phase-3-exec.md) | Inline TDD slices -> Quality Gate (Strong) -> `/compact` |
| **Phase 4** | [phase-4-verify.md](file:///Users/simonirengard/Library/CloudStorage/SynologyDrive-1/aiDir/claude-skills/skills/deep-plan/phase-4-verify.md) | Contract + `/run` + Security (Cheap) -> Safety Net -> `/compact` |
| **Phase 5 & 6** | [phase-5-6-land.md](file:///Users/simonirengard/Library/CloudStorage/SynologyDrive-1/aiDir/claude-skills/skills/deep-plan/phase-5-6-land.md) | HITL Debrief -> Docs True -> PR -> Close Ledger |

---

## Guardrails

- Read `state.md` first; resume, never restart.
- Execute `/clear` immediately after Phase 0.5 mock sign-off.
- Execute `/compact` at phase boundaries and every 3-4 slices in Phase 3.
- Subagent dispatches: static rules at TOP prefix (prompt cache alignment) + mandate `NO_PREAMBLE`.
- Pipe contract command outputs to `.deep-plan/contract.log`; read only `tail -n 40` on failure.
- Extract only current slice task lines from `tasks.md` in Phase 3; do not load full file.
- `git reset --hard` to last passing slice if a Phase 4 fix attempt fails or breaks tests.
- Scope Phase 4 second code-review gate strictly to `git diff <phase-3-end-sha>..HEAD`.
- Preserve hard-won rules in `CLAUDE.md`; correct contradicted lines during Phase 6 landing (do not arbitrarily prune active rules).
- One commit per passing slice; never commit red code; never push unasked.
