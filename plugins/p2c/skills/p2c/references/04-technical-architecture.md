# The Essential Stack for Technical Architecture

Architecture is where over-engineering kills startups. Keep what scales the team's decision-making, not the diagram count.

## The "Best of" Shortlist
- **C4 model** — diagrams that scale from 1-page overview to detailed components
- **ADRs (Architecture Decision Records)** — short, versioned, append-only decision log
- **Threat modeling (STRIDE)** — security baked in, not bolted on
- **12-Factor App principles** — battle-tested defaults for cloud apps
- **Boring tech by default** — Postgres, a major cloud, a popular framework
- **Observability from day one** — logs, metrics, traces, errors

Everything else is premature.

## How to Structure the Process

### Phase 1: Define the Constraints (Days 1–2)
- Capture **non-negotiables**: compliance, latency, scale, team skills, budget
- Identify **integrations** (auth, payments, email, analytics) — buy vs. build per item
- List **load assumptions** (peak users, data volume, request rate) — round generously

### Phase 2: Sketch the System (Days 3–5)
- Draw a **C4 Level 1 (Context)** — your system + external actors/systems
- Draw a **C4 Level 2 (Containers)** — apps, services, databases, queues
- Skip Level 3/4 until they're needed (they almost never are at MVP)
- Use **Excalidraw or Mermaid** — checked into the repo, not trapped in a SaaS

### Phase 3: Pick the Stack (Days 5–7)
- Default choices unless you have a strong reason otherwise:
  - **Database**: Postgres (managed: Supabase, Neon, RDS)
  - **Backend**: a framework your team knows (Next.js, Django, Rails, FastAPI, .NET)
  - **Frontend**: React or the framework matching your backend
  - **Hosting**: Vercel, Fly, Render, Railway, or AWS/GCP/Azure
  - **Auth**: Clerk, Auth0, Supabase Auth, or Cognito — don't roll your own
  - **Payments**: Stripe — full stop
- Document the choice in an **ADR** with reasoning + alternatives considered

### Phase 4: Model the Data (Week 2)
- Draw the **ER diagram** for core entities (5–10 tables for an MVP)
- Define **ownership boundaries** — which service owns which data
- Pick the **ID strategy** (UUIDv7 or ULID for most cases)
- Plan **migrations** from the start (Prisma, Alembic, Flyway, etc.)

### Phase 5: Security & Trust Boundaries (Week 2)
- Run a **STRIDE pass** on each container:
  - **S**poofing, **T**ampering, **R**epudiation, **I**nformation disclosure, **D**oS, **E**levation of privilege
- Define **authn vs. authz** model (who can do what to which resource)
- Classify data: **public / internal / sensitive / regulated**
- Plan **secrets management** (cloud KMS, Doppler, 1Password — never .env in git)

### Phase 6: Operability Baseline (Week 3)
- **Logging**: structured JSON, request IDs, no secrets
- **Metrics**: RED (Rate, Errors, Duration) for every service
- **Tracing**: OpenTelemetry from day one
- **Errors**: Sentry or equivalent, alerting wired up
- **Uptime**: define SLO, instrument SLI, set error budget
- **Backups**: automated, tested restore procedure

### Phase 7: Document Just Enough (Week 3)
- **README.md** — how to run it locally in <10 minutes
- **ARCHITECTURE.md** — C4 diagrams + key flows
- **ADR/** folder — decisions over time
- **runbook.md** — what to do when X breaks

## The 1-Page ADR Template
```
# ADR-NNN: [Decision title]
Date: YYYY-MM-DD
Status: Proposed | Accepted | Superseded

## Context
[The forces at play, the problem, the constraints]

## Decision
[What we're doing]

## Alternatives considered
[What we rejected and why]

## Consequences
[Trade-offs, risks, follow-ups]
```

If a decision matters in 6 months, it deserves an ADR. If it doesn't, skip it.

## The Minimum Viable Toolset
- **Excalidraw or Mermaid** — diagrams as code, in the repo
- **A managed Postgres** — Supabase, Neon, RDS (don't self-host at MVP)
- **A PaaS** — Vercel, Fly, Render, Railway (Kubernetes is rarely the right answer at MVP)
- **Sentry + a log/metrics stack** — Better Stack, Datadog, Grafana Cloud, or cloud-native (CloudWatch)
- **A secrets manager** — cloud KMS, Doppler, or 1Password CLI
- **GitHub** — code, CI, projects, issues

Six things. Most are managed. You should be writing product code, not platform code.

## The Mental Model
Architecture at MVP is about **reversibility**, not perfection. The shortlist optimizes for:

1. **Boring choices** that don't surprise you at 3am
2. **Clear boundaries** so you can swap pieces later
3. **Decisions on record** so the next engineer knows why

You will throw parts of this away as you learn. Make sure the parts you keep — data model, trust boundaries, observability — are the ones that are expensive to change later.
