---
description: Build a working local POC (proof of concept). NOT production-ready — runs on the local machine, demonstrates the validated MVP slice end-to-end.
argument-hint: [optional stack hint, e.g. "use Next.js + Postgres" or "match the existing repo"]
---

# /p2c:tech-build — Local Working POC

The user wants the **POC actually built** on their local machine. Activate the `p2c` skill scoped to phase 5 in POC mode.

## Critical guardrails

- This produces a **working local prototype**, **not** production-ready software.
- Confirm with the user before:
  - Installing global packages or system dependencies
  - Opening ports beyond loopback
  - Running long builds or generating large trees
- All POC code goes under `p2c-workspace/poc/`.
- Include a clear `production-gap.md` listing every shortcut.

## Prerequisites

- A validated PRD (`p2c-workspace/02-requirements/prd.md`)
- Architecture brief — at minimum a stack choice in `p2c-workspace/04-architecture/`. If none exists, get a quick architect pass first.

## Active phase

- **Phase 5 (POC mode):** walking skeleton + the smallest set of vertical slices that demonstrate the validated job end-to-end.

## Active agents

- **lead-developer** (lead — actually writes the code)
- **lead-architect** (only for stack confirmation and any new ADR triggered by build reality)
- **scrum-master** (POC backlog ordering, demo script)

## Entry sequence

1. Read `skills/p2c/references/05-build-mvp.md` and the lead-developer agent's POC-mode rules.
2. Confirm stack with user (default if no preference: Vite + React + TS + Tailwind + shadcn/ui front; FastAPI or Node Fastify back; SQLite for POC).
3. Build in this order:
   1. Repo skeleton + `make dev` / `npm run dev` works
   2. Walking skeleton: one trivial page hitting one trivial endpoint hitting the DB
   3. Auth (hardcoded user OK for POC — note the gap)
   4. Vertical slice for the validated golden path
   5. Sample data seed
   6. README + DEMO.md
   7. production-gap.md

## Deliverables

- `p2c-workspace/poc/` — the working code
- `p2c-workspace/poc/README.md` — setup, run, what's demonstrated, what's not
- `p2c-workspace/poc/DEMO.md` — 2-minute click-through script
- `p2c-workspace/poc/production-gap.md` — every shortcut taken and what's needed for prod

## Final output

A working `cd p2c-workspace/poc && <single command> && open http://localhost:<port>` flow, plus the production-gap doc that the user can hand off for the prod sprint plan.
