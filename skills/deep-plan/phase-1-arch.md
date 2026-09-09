# Phase 1 — Deep Modular Architecture & Verification Contract

## Phase 1 — Deep Modular Architecture

**Run `/codebase-design` skill** to structure deep modules with small interfaces, clean seams, and high testability:

- Decompose into deep modules with single responsibilities and narrow interfaces (1–3 methods).
- Inject dependencies via constructors so core logic is pure and testable without heavy mocks.
- Define seams that enable slices to be built and tested in isolation.
- Honor platform constraints confirmed in Phase 0 (edge, serverless, document store, etc.).
- Reuse `CONTEXT.md` / ADRs and Recon Note's reuse list. Derive view/state seams from signed-off mock (if UI).
- Capture architecture sketch feeding into spec/plan.

## Pin the Verification Contract

Pin exact command strings into `.deep-plan/state.md` (install, test, single-test-file, typecheck, lint, format, build, e2e) and run each command now to confirm clean 0 exit code.

**Test Log Isolation:** Direct all contract outputs to `.deep-plan/contract.log` (e.g. `<cmd> > .deep-plan/contract.log 2>&1`). Never dump full test logs into the chat window. On failure, inspect only `tail -n 40 .deep-plan/contract.log`.

Tooling enforcement: Run **`/setup-pre-commit`** and **`git-guardrails-claude-code`** if missing.

Update `.deep-plan/state.md` and execute `/compact` before Phase 2.
