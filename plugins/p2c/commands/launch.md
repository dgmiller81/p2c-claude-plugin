---
description: Launch strategy and all launch documentation — soft launch, gradual rollout, rollback, runbooks, status page, comms kit, support FAQ.
argument-hint: [optional target launch date, audience, channels]
---

# /p2c:launch — Launch Strategy + Documentation

The user wants the **launch strategy and all launch documentation**. Activate the `p2c` skill scoped to phase 7 plus the comms slice of research/marketing.

## Prerequisites

- A product that is technically ready (or imminently ready) — confirm with user.
- QA sign-off in progress or complete (`p2c-workspace/07-launch/qa-signoff.md`).
- Architecture and observability live (`p2c-workspace/04-architecture/observability.md`).

## Active phase

- **Phase 7 (full):** soft launch, gradual rollout, rollback, on-call, runbooks, status page, comms.

## Active agents

- **scrum-master** (launch sprint cadence, war-room ops)
- **research-marketing** (comms kit, GTM plan, channel sequencing)
- **lead-qa-coordinator** (gates, rollback rehearsal)
- **lead-architect** (rollback feasibility, observability spot-check)
- **product-owner** (go/no-go, scope of launch, success criteria)

## Entry sequence

1. Read `skills/p2c/references/07-launch.md` in full.
2. Pull current state from `p2c-workspace/06-test-and-harden/` (perf, security, a11y status) and `04-architecture/observability.md`.
3. Run the launch-readiness checklist gate-by-gate; flag every red.
4. Build the soft-launch cohort plan with product-owner.
5. Build the comms kit with research-marketing.
6. Run a **rollback rehearsal** in staging before launch day.

## Deliverables

- `p2c-workspace/07-launch/launch-readiness.md` — the full checklist with evidence
- `p2c-workspace/07-launch/rollback-plan.md` — decision criteria + steps + rehearsal record
- `p2c-workspace/07-launch/runbook.md` — top 5 failure modes, response steps
- `p2c-workspace/07-launch/oncall-rotation.md`
- `p2c-workspace/07-launch/status-page-setup.md`
- `p2c-workspace/07-launch/comms-kit/` — landing page brief, launch email, social posts, support FAQ, internal brief
- `p2c-workspace/07-launch/gtm-plan.md`
- `p2c-workspace/07-launch/launch-day-runbook.md` — the war-room playbook for go-live

## Final output

`p2c-workspace/LAUNCH-PACKAGE.md` — a single linked document the launch team uses on go-live day.
