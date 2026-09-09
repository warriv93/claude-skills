# Phase A & B — Product Framing & Platform Interview

## Phase A — Frame the Product

1. Restate idea in two lines: target user, primary job.
2. **Grill product frame (`/grilling`):**
   - Who is first user and primary job?
   - What does v1 do — and **what does v1 deliberately NOT do**?
   - One measurable success signal.
   - Competitors/existing alternatives and why they aren't used.
3. **Cut into milestones:** M0 walking skeleton, then 1 milestone per deployable capability.
4. Write `.deep-plan/project.md`. Get explicit sign-off on v1 scope. **Do not proceed without confirmation.**

---

## Phase B — Platform Interview (One-Way Doors)

Settled before architecture. Skip anything user already stated. Ask remaining questions in **one batched pass** (`AskUserQuestion`) with recommended defaults:

- **Home:** GitHub/GitLab, public/private, org, licence (MIT default).
- **Hosting:** Pages / Workers / Vercel / Railway / Supabase / Firebase.
- **Database:** Postgres / SQLite / D1 / Firestore. Backups & migration path.
- **Auth:** Email+Password / Provider OAuth / Managed (Clerk, Supabase Auth).
- **Environments & CI:** GitHub Actions workflow running verification contract on push/PR.
- **Auto-deploy trigger:** Platform git integration vs GitHub Actions CLI deploy. Rollback mechanism.
- **Domain & Secrets:** DNS holder, env var storage & access.
- **Spend Policy:** Build-time (free/allowed), Runtime (free/allowed), Hosting ceiling ($ cap).
- **Reality Check & Observability:** Expected scale, solo/team, lifespan, error tracking.

Record answers as ADRs via `/domain-modeling` and in `.deep-plan/project.md`. Get confirmation before Phase C.
