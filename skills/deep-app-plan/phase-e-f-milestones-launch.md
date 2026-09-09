# Phase E & F — Milestones & Launch Readiness

## Phase E — Build Milestones (Call `/deep-plan`)

For each milestone in order:

1. Hand milestone frame and platform block to **`/deep-plan`**.
2. Run `/deep-plan` in its own context. Receive Phase 5 debrief.
3. Deploy milestone to prod before starting next milestone.
4. Update project ledger `.deep-plan/project.md` and `CLAUDE.md` with lessons learned.

---

## Phase F — Launch Readiness

Walk checklist before calling app real:

1. **Security audit:** run `/security-review` over full codebase (auth, ACL, secrets, SQL).
2. **Data sanity:** migrations run clean from empty, backups tested, free tier ceiling defined.
3. **Operations:** custom domain & TLS, error tracking receiving events, rollback path ready.
4. **Cold-start test:** clone into clean dir, follow README, verify local run.
5. **Handover debrief:** what shipped vs frame, non-goals, weak points, user inputs needed, recurring costs.
