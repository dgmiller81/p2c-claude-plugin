---
description: Production build path — vertical slices, hardening, CI/CD, observability, launch readiness. The full production engineering effort, not a POC.
argument-hint: [optional context — POC path, target launch date, scale targets]
---

# /p2c:tech-prod — Production Build & Hardening

The user wants the **full production build path**. Activate the `p2c` skill scoped to phases 5, 6, 7.

## Prerequisites

- Architecture artifacts in `p2c-workspace/04-architecture/`
- Story breakdown in `p2c-workspace/02-requirements/stories/`
- Sprint plan in `p2c-workspace/plan/sprint-plan.md`
- Often: a POC in `p2c-workspace/poc/` and `production-gap.md` to close

If a POC exists, the prod plan should explicitly close every gap in the gap doc before launch.

## Active phases

- **Phase 5 (full):** trunk-based dev, walking skeleton in prod, vertical slices, CI/CD, feature flags, telemetry instrumented per the obs plan.
- **Phase 6 (full):** testing pyramid filled, OWASP Top 10, perf budgets met under load, accessibility AA, dependency scanning, secret scanning.
- **Phase 7 (full):** launch readiness, soft launch, gradual rollout plan, rollback plan, runbooks, on-call set up, status page, comms.

## Active agents

- **scrum-master** (lead — drives sprint cadence)
- **lead-developer** (build)
- **lead-architect** (cross-cutting decisions, infra)
- **lead-qa-coordinator** (test plan, security, perf, a11y)
- **research-marketing** (launch comms — light involvement here, full ownership in `/p2c:launch`)

## Entry sequence

1. Read references 05, 06, 07 in full.
2. Confirm prod target: cloud, region(s), SLO, scale targets.
3. Confirm budget envelope (informs hosting tier and tooling choices).
4. Run sprint cadence — scrum-master drives, you orchestrate stop/start between sprints.
5. Run the **launch-readiness checklist** from `references/07-launch.md` before declaring ready.
6. At every phase boundary, run the traceability checker and report its output
   as described under "The phase-boundary ritual" in `skills/p2c/SKILL.md`.
   Open findings, staleness and gaps are named in the phase summary every time.
   The checker is advisory — it never blocks a phase from advancing, but a
   phase may not advance without its output being reported.

## Deliverables

- `p2c-workspace/05-build/` — full build artifacts: walking skeleton notes, slice plan executed, CI config notes, telemetry verification
- `p2c-workspace/06-test-and-harden/` — test plan, OWASP review, perf reports, a11y reports, security scan reports, backup-restore drill log
- `p2c-workspace/07-launch/` — readiness checklist, rollback plan, runbooks, on-call rotation, status page setup notes
- `p2c-workspace/plan/sprint-plan.md` updated as sprints land
- `p2c-workspace/plan/cost-estimate.md` updated based on actuals

## Final output

`p2c-workspace/PROD-READINESS.md` — green/yellow/red on every gate criterion, lead-qa-coordinator's sign-off, lead-architect's sign-off, recommended go date.
