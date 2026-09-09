# Phase C & D — Genesis & Walking Skeleton

## Phase C — Genesis (Repo, Scaffold, Tooling)

1. **Create repo** on chosen host with license & README holding Phase A frame.
2. **Scaffold stack** with ecosystem CLI tool (`create-*`, `cargo new`, `uv init`).
3. **Pin verification contract:** install, test, single-test-file, typecheck, lint, format, build, e2e, deploy. Run each now to confirm clean 0 exit code.
4. Tooling enforcement: **`/setup-pre-commit`** and `git-guardrails-claude-code`.
5. **CI & Deploy Pipeline:** GitHub Actions workflow running verification contract on push/PR, plus deploy job on green.
6. **Seed agent docs (`/writing-for-agents`):** `CLAUDE.md` (terse, unwritten conventions) and `CONTEXT.md` (ADRs).

---

## Phase D — Walking Skeleton (M0)

Deploy thinnest end-to-end slice to **production** before building feature code:

1. Thinnest real path: client -> server -> DB -> back.
2. Wire deploy: env vars set on platform, DB migrations running, push to main triggers live deploy.
3. **Prove outside access:** hit live URL, verify DB round-trip in prod. Prove rollback path.
4. Commit & tag M0. Record live URL in `.deep-plan/project.md`.

**Gate:** No milestone starts until M0 is live in production.
