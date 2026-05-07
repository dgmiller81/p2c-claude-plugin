---
description: Technical scoping — architecture, ADRs, threat model, data model, observability plan, plus sprint scope and cost estimates. No code yet.
argument-hint: [optional context — PRD path, scale targets, budget envelope]
---

# /p2c:tech-scope — Technical Scope (Architecture + Cost)

The user wants the **technical scope and cost** — how to properly design and build, with cost estimates. Activate the `p2c` skill scoped to phase 4 plus the planning slice of phases 5–6.

## Prerequisites

- `p2c-workspace/02-requirements/prd.md` — required
- `p2c-workspace/02-requirements/story-map.*` and stories — strongly recommended
- NFR worksheet — strongly recommended

If any are missing, capture a quick version with the user before architecting.

## Active phase

- **Phase 4 (full):** Technical Architecture — C4 (Context + Container), stack pick (with cost ranges), data model, threat model, observability plan, ADRs.
- **Phases 5–6 (planning slice only):** vertical-slice plan, walking-skeleton scope, test strategy outline. Enough to size the work — no code, no infra build.
- **Sprint plan + cost estimate.**

## Active agents

- **lead-architect** (lead)
- **lead-developer** (vertical-slice plan, build practice scope)
- **lead-qa-coordinator** (test strategy outline for sizing)
- **scrum-master** (sprint plan, role-hour breakdown)

## Entry sequence

1. Read `skills/p2c/references/04-technical-architecture.md`, `05-build-mvp.md` (planning), `06-test-and-harden.md` (planning).
2. Read PRD, story map, NFRs.
3. Offer the visual server with the architecture diagram and cost-estimate views.
4. Run the 7-phase architecture workflow + a planning pass.

## Cost-estimate output

Run `python skills/p2c/scripts/estimate_cost.py --plan p2c-workspace/plan/sprint-plan.md --output p2c-workspace/plan/cost-estimate.md` once the sprint plan is drafted.

## Deliverables

- `p2c-workspace/04-architecture/c4-context.md`
- `p2c-workspace/04-architecture/c4-containers.md`
- `p2c-workspace/04-architecture/data-model.md`
- `p2c-workspace/04-architecture/threat-model.md`
- `p2c-workspace/04-architecture/observability.md`
- `p2c-workspace/04-architecture/adr/ADR-NNN-*.md` (for every real decision)
- `p2c-workspace/05-build/slice-plan.md`
- `p2c-workspace/06-test-and-harden/test-strategy.md`
- `p2c-workspace/plan/sprint-plan.md`
- `p2c-workspace/plan/cost-estimate.md`

## Final output

`p2c-workspace/TECH-SCOPE-SUMMARY.md` with architecture posture, total cost (AI-assisted + standard rates), top risks, and recommended path forward (POC vs. straight-to-prod).
