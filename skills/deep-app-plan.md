---
description: Front-door orchestrator for building a whole application from nothing. Frames the product and its smallest lovable v1, interrogates the platform decisions that can't be undone later (repo host and visibility, hosting target, database, auth, CI/CD, secrets, spend policy, lifespan), creates the repo and scaffolds the stack, then ships a walking skeleton to production before any feature code exists — so the pipeline is proven on day one. Then drives each milestone through /deep-plan (grill → mock → SDD+TDD → quality gates → verify), and finishes with launch readiness: domain, secrets, backups, observability, whole-app security review, and onboarding docs. Resumable across sessions. Free by default — spend is asked for, never assumed. Use when the user says "build me an app", "new project", "/deep-app-plan", or starts something with no repo yet.
argument-hint: <what the app is, in a sentence>
---

# /deep-app-plan — Frame → Platform → Genesis → Skeleton → Milestones → Launch

You are the technical founder of a new codebase. Your job is to take "I want an app that
does X" and turn it into a **deployed, maintainable product** — with the decisions that are
expensive to reverse made deliberately at the start, and every feature built through
`/deep-plan`.

**This skill is a wrapper.** It owns exactly what `/deep-plan` cannot: the product frame,
the platform decisions, repo genesis, the deploy pipeline, and launch. Everything else it
delegates. Do **not** re-implement `/deep-plan`'s grill, mock, SDD+TDD, quality gates, or
verification loop here — call it, once per milestone.

**Cost policy — ask, don't assume.** Money is a Phase B question, not a house rule. Until
it is answered, behave as if the answer is "free only": local tooling and the running
session, no paid external LLM/API calls, free tiers everywhere. Once the user has set a
spend policy, honour it — and **always say plainly what a choice costs** before making it.

| Job                                        | Where it happens                                    |
| ------------------------------------------ | --------------------------------------------------- |
| Product frame + v1 scope                   | Phase A (here), sharpened with `/grilling`           |
| Platform decisions + ADRs                  | Phase B (here) + `/domain-modeling`                  |
| Repo, scaffold, tooling, CI                | Phase C (here) + `/setup-pre-commit`, git guardrails |
| Walking skeleton deployed to prod          | Phase D (here) + `/run`                              |
| Every actual feature                       | **`/deep-plan`**, once per milestone (Phase E)       |
| Launch readiness + handover                | Phase F (here) + `/security-review`                  |

Execute the phases in order. Each gates the next. Be extremely concise; sacrifice grammar
for concision.

---

## The project ledger — `.deep-plan/project.md`

Projects outlive sessions by weeks. **First action of every invocation:** read
`.deep-plan/project.md`. If it exists, summarise where the project stands, confirm, and
resume at the first incomplete phase — never restart. If it doesn't, create it in Phase A.

It is the file `/deep-plan`'s Phase R recon reads to learn the platform, so keep it true.
Distinct from `/deep-plan`'s own `.deep-plan/state.md`, which tracks one feature run and is
closed when that feature lands.

```markdown
# project: <name>

Status: <phase> | Started: <date> | Repo: <url> | Live: <url>

## What it is

<two lines: who it's for, what it does, what v1 deliberately isn't>

## Platform (Phase B — one-way doors)

repo: <host/org, visibility, licence> | hosting: <target> | db: <choice> | auth: <choice>
ci: <choice> | envs: <prod|preview|staging> | domain: <name, DNS holder>
deploy: <platform git integration | actions workflow> on <push to main|tag|manual> | rollback: <how>
secrets: <where they live> | observability: <choice>
spend: build-time <free|allowed: what> | runtime <free|allowed: what> | hosting <ceiling>

## Verification contract

test: <cmd> | typecheck: <cmd> | lint: <cmd> | build: <cmd> | e2e: <cmd> | deploy: <cmd>

## Milestones

- [x] M0 walking skeleton — <deployed url, commit>
- [ ] M1 <feature> — <status, or /deep-plan state file path>

## Decisions & deferrals

- <decision or deferred thing> — <why>
```

---

## Phase A — Frame the product

Before platforms, before code: what is this, and what is the smallest version worth
deploying?

1. Restate the idea in two lines: who it's for, what it does for them.
2. **Grill the product frame** — run `/grilling` (or grill inline) on the questions that
   decide scope, one at a time, each with your recommended answer:
   - Who is the first user, and what is the one job they hire this app to do?
   - What does v1 do — and, harder, **what does v1 deliberately not do**? Push for a v1 that
     is embarrassingly small and actually shippable.
   - How will you know it worked? One measurable signal, not five.
   - What already exists that does this, and why isn't the user using that?
3. **Cut it into milestones.** M0 is always the walking skeleton (Phase D). Then one
   milestone per user-visible capability, ordered so each is independently deployable and
   the app is usable after each. A milestone that can't ship alone is two milestones or none.
4. Write `.deep-plan/project.md` with the frame and the milestone list. Get sign-off on the
   v1 scope. **Do not proceed without confirmation.**

---

## Phase B — Platform interview (the one-way doors)

Where the code lives and where it runs constrains the architecture — edge runtime vs.
long-running process, SQL vs. document store, serverless cold starts — so it is settled
here, before any architecture exists. **Skip anything the user already stated.** Ask the
rest in **one batched pass** (`AskUserQuestion`), each with your recommended default so they
can accept the lot in a single reply. Recommend from the app's shape; never ask blind.

- **Home** — GitHub or GitLab? Private or public? Which account/org? Public needs a licence
  (MIT unless they say otherwise).
- **Hosting** — static site / SPA → **Cloudflare Pages**; full-stack JS with SSR →
  **Vercel** or **Cloudflare Workers**; backend + database + background jobs → **Railway**
  (or Fly / Render); mobile or realtime-heavy → **Firebase** / **Supabase**; already-owned
  infra → use it. The cheapest right answer is usually the platform they're already logged
  into — ask which accounts they have before recommending a new one.
- **Database** — Postgres on Railway / Neon / Supabase, SQLite or D1 at the edge, Firestore
  if they went Firebase. Include how migrations run and where backups live; "we'll figure
  out backups later" is a decision to write down, not a gap to leave silent.
- **Auth** — none / email+password / OAuth provider / managed (Clerk, Supabase Auth). The
  most expensive thing to retrofit in the list. Force the decision even for v1.
- **Environments & CI** — prod only, or preview/staging too? A GitHub Actions workflow
  running the verification contract on every push and PR (default yes, from the first
  commit)?
- **Auto-deploy on push** — should pushing to `main` put it live automatically? Ask
  explicitly; don't assume either way. Two mechanisms, and the difference matters:
  - **The platform's own git integration** — Cloudflare Pages/Workers, Vercel, Railway,
    Firebase App Hosting all connect to the repo and build on push. Zero config, free
    per-PR preview URLs, nothing to maintain. But it deploys **whether or not the tests
    pass** — CI and deploy are separate pipelines that don't know about each other.
  - **A GitHub Actions workflow that deploys** — runs the verification contract first and
    only deploys on green, via the platform CLI (`wrangler deploy`, `vercel deploy --prod`,
    `flyctl deploy`, `firebase deploy`) with an API token in repo secrets. More setup, one
    pipeline, red code can't reach production. **Recommended for anything with real users.**

  Then settle the rest of it: preview deploy per PR? deploy on merge to `main` or only on a
  tag/release? a manual approval step before prod? and how a bad deploy gets rolled back —
  platform instant-rollback, or revert-and-redeploy? Whichever is chosen, Phase D wires it
  and proves it works before feature code exists.
- **Domain** — custom domain or platform subdomain, who owns the DNS, and whether that
  needs buying today.
- **Secrets** — where env vars live (platform dashboard, `.env.local`, a password manager)
  and who can reach them. This becomes the "inputs needed from you" list you hand back.
- **Spend policy** — three separate answers, and the default to every one is _free only_:
  - **Build-time** — must the agent stay on free local tooling, or may it call paid
    services (a paid model API, a paid research or scraping service) while building?
  - **Runtime** — may the app itself depend on paid services (an LLM API key, Stripe,
    email delivery, a paid tier of a managed DB)? Free tiers and self-hosted alternatives
    exist for most of these — name them before spending.
  - **Hosting ceiling** — free tier only, or a monthly cap in real money? This is what
    actually picks the host.

  Name the cost of anything that isn't free, per month, before committing to it. If a
  requirement can't be met free, say so as a tradeoff — "this needs $X/mo, or v1 drops
  the feature" — and let the user choose.
- **Reality check** — expected scale (10 users or 100k), solo or a team, real users' PII or
  compliance/region constraints, and **lifespan**: throwaway spike, side project, or
  something maintained for years.
- **Observability** — error tracking / analytics, or deliberately nothing?

**Calibrate to the answers.** If it's a spike or a weekend toy, say so and offer to run a
stripped pipeline (skip speckit, one quality gate, no staging) rather than ceremonially
over-building. If it's long-lived or handles real users' data, the full `/deep-plan` rigour
is the point.

Record every answer as an ADR via `/domain-modeling` and in the project ledger. **Do not
proceed without confirmation** — these are the expensive ones.

---

## Phase C — Genesis (repo, scaffold, tooling)

1. **Create the repo** on the chosen host with the chosen visibility, licence, and a README
   holding the Phase A frame. Ask before creating anything under the user's account; never
   push to a remote unprompted.
2. **Scaffold the stack** with the ecosystem's own tool (`create-*`, `cargo new`, `uv init`,
   the framework CLI) rather than hand-rolling a tree. Take the platform's supported
   template where one exists — deploying is easier when you started from what it expects.
3. **Pin the verification contract** — install, test, single-test-file, typecheck, lint,
   format, build, e2e, deploy. Run each one now to prove it works on the empty project.
   Write it into the ledger; this is what "green" means for every later milestone.
4. **Make tooling enforce quality** — `/setup-pre-commit` (lint-staged, typecheck, tests on
   commit) and `git-guardrails-claude-code`. Cheaper than remembering.
5. **CI and the deploy path chosen in Phase B** — a workflow running the contract on every
   push and PR, from the first commit, while it takes thirty seconds to write. Then wire the
   deploy: an Actions job that deploys only after the contract passes (platform CLI + API
   token in repo secrets), or the platform's git integration connected to the repo. If it's
   the git-integration route, protect `main` — required status checks, no direct pushes —
   or the platform will happily deploy red code.
6. **Seed the agent docs** — `CLAUDE.md` with the stack, the contract commands, and the
   conventions chosen; `CONTEXT.md` seeded from the Phase A/B ADRs. Future `/deep-plan` runs
   read these in recon, so this is what makes feature #1 cheap.

---

## Phase D — Walking skeleton (M0: deploy before you build)

The single highest-value hour in a new project. Ship the thinnest possible end-to-end slice
to **production** before any feature exists: one page or endpoint, touching every layer the
architecture claims — client → server → database → back — with a real deploy behind it.

1. Build the thinnest real path. No features, no styling debates, no auth flows.
2. Wire the deploy end to end: env vars set on the platform, secrets in place, migrations
   running, CI green, and the Phase B trigger actually firing — push to `main` (or tag, or
   approve) and watch it reach production by itself.
3. **Prove it from the outside** — hit the live URL, `/run` it locally too, confirm the
   database round-trips in prod, not just on the laptop. Then **prove the rollback**: break
   something trivially, deploy it, roll back. A rollback path you've never run isn't one.
4. Commit and tag M0. Record the live URL in the ledger.

**Gate:** no milestone starts until something is live. If deploying turns out to be painful
or the platform fights the stack, you have discovered it while there is nothing to lose —
revisit Phase B now, not after ten features are written against it.

---

## Phase E — Build the milestones (call `/deep-plan`)

For each milestone in order: **run the `/deep-plan` skill**, seeded with the ledger's
platform block (including the spend policy — it inherits, it does not re-ask), the ADRs,
and that milestone's frame. It handles the rest — recon, grill,
UI mock, deep-modular architecture, SDD+TDD execution by cheap subagents, both quality
gates, the budgeted verification loop, HITL review, docs and PR.

- **One milestone at a time.** Finish and deploy before starting the next; a half-landed
  milestone in a fresh project is how apps become unshippable.
- `/deep-plan` keeps its own `.deep-plan/state.md` per feature. When it lands, tick the
  milestone here and let it close its state file.
- Between milestones, **update the project ledger and `CLAUDE.md`** with what was learned —
  new conventions, new contract commands, decisions taken. Each pass makes the next
  milestone cheaper.
- If a milestone turns out to be too big for one `/deep-plan` run, that's `/wayfinder`
  territory — `/deep-plan`'s own Phase R will say so.
- Re-open Phase B only when a milestone proves a platform decision wrong. Say so out loud,
  write the ADR that supersedes the old one, and count the cost honestly.

---

## Phase F — Launch readiness

Before calling the app real, walk the list nobody remembers under deadline:

1. **Security across the whole app**, not just the last diff — run `/security-review` over
   the codebase: auth flows, authorization on every endpoint, secrets not committed, input
   validation, dependency advisories. Criticals block launch.
2. **Data** — migrations run cleanly from empty, backups actually exist and have been
   restored once, and you know what happens when the free tier fills up.
3. **Operations** — custom domain and TLS, error tracking receiving events, uptime visible,
   and a known way to roll back a bad deploy.
4. **The cold-start test** — clone the repo into a clean directory, follow the README, and
   get it running. Whatever you had to know but the README didn't say, add it.
5. **Handover debrief** — what shipped vs. the Phase A frame; what v1 deliberately doesn't
   do; weak points and thin coverage; **every input needed from the user** (accounts, keys,
   DNS, billing); recurring costs, named; the next three milestones worth doing.

End by asking how they want to proceed. Then close or archive the ledger.

---

## Guardrails

- Spend follows the Phase B spend policy — build-time, runtime, and hosting each answered
  separately. Until it is answered, free only. State costs in real money before incurring
  them, and never quietly upgrade a free tier.
- Read `.deep-plan/project.md` first; resume, never restart.
- Phase B before any architecture. Platform decisions are one-way doors, and `/deep-plan`
  reads them rather than re-asking.
- Something is deployed before feature work starts. M0 is not optional.
- Delegate features to `/deep-plan` — never re-implement its phases here.
- One milestone at a time; each one independently shippable.
- Never create a remote repo, buy a domain, provision paid infrastructure, or push without
  explicit go-ahead.
- Scale the ceremony to the lifespan answer: a spike gets a stripped pipeline, a product
  gets the full rigour.
