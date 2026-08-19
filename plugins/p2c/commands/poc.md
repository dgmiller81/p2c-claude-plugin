---
description: All-in-one POC — build full working POC + validate it + produce production-ready design specs + planned production sprint plan + detailed cost estimates including all sprints to develop, test (perf/security/QA), and build out the production system.
argument-hint: [optional brief, target audience, scale targets, budget envelope]
---

# /p2c:poc — Full POC + Production Plan + Cost Estimate

This is the **flagship all-in-one** command. The user wants:

1. A working POC built and validated locally.
2. Production-ready design specs.
3. A planned production development effort with sprint breakdown.
4. Detailed cost estimates for full production build, test, hardening, and launch.

Activate the `p2c` skill in full-orchestration mode but with a **POC-first** posture: phases 1–4 are condensed (assume validated unless missing), phase 5 splits into POC build + production sprint plan, phases 6–8 are planned (not executed).

## Absolute rules for this command

These are inherited from `SKILL.md` and `references/visual-standards.md` — repeated here because they govern this command:

1. **Every phase listed in the active flow below must be completed** unless the user explicitly skips an item with a recorded reason in `status.json`. There are no silent gaps.
2. **Mockups are mandatory before any code is written.** Phase 3 is **not** marked `delivered` without high-fidelity mockups for every key MVP screen. The build leg of this command does not start until those mockups exist.
3. **Mockups must be enterprise-grade** — match the user's brand if provided, otherwise apply the Enterprise Default Style from `references/visual-standards.md`.
4. **Production design specs in the final package include the mockups** (Figma link or `mockups/` folder), not just architecture diagrams.

## Active flow

| Step | Phase | Posture |
|---|---|---|
| 1 | 1. Discovery | Validate or import — short pass |
| 2 | 2. Requirements | PRD + story map (validated MVP slice) |
| 3 | 3. Design | **Enterprise-grade mockups required** for every MVP screen; design system + a11y |
| 4 | 4. Architecture | Full ADRs, threat model, data model |
| 5a | 5. Build (POC) | **Actually build** in `p2c-workspace/poc/`, against the mockups |
| 5b | 5. Validate POC | Test the validated job end-to-end with real data |
| 5c | 5. Production gap | Document every gap from POC → prod |
| 6a | 5–7. Plan prod build | Full sprint plan covering build + test + hardening + launch |
| 6b | Cost | Detailed cost estimate using AI-assisted rate card |
| 7 | 8. Measure framework | Define activation, north star, AARRR — to be instrumented in prod |

## Active agents

All eight, in this rough sequence:

1. **research-marketing** + **business-analyst** + **product-owner** — discovery, market scan, PRD, BRD
2. **product-owner** + **scrum-master** — story map, MoSCoW
3. **lead-ux-designer** — mockups (mandatory before build), tokens, components, brand application, handoff
4. **lead-architect** — architecture, ADRs, threat model
5. **lead-developer** — POC build, against the mockups
6. **lead-qa-coordinator** — POC validation + prod test plan
7. **scrum-master** — full prod sprint plan
8. (back to **product-owner** + **scrum-master**) — final cost estimate review

## Cost estimate must include

- **Total cost (AI-assisted rates)** and **total cost (standard rates)**
- **Per-sprint breakdown** with hours per role
- **Per-role total** so the user can see headcount cost concentration
- **Categories:**
  - Development sprints (vertical slices)
  - Test sprints (or test allocation per sprint)
  - Performance testing
  - Security testing (SAST, SCA, DAST, pen test budget)
  - QA / regression
  - Production build-out (infra, CI/CD, observability)
  - Launch sprint(s)
- **Assumptions** clearly stated (sprint length, team mix, allocations, focus factor)
- **Sensitivity analysis:** ±1 sprint, ±1 engineer, AI-assist on/off

Run `python skills/p2c/scripts/estimate_cost.py --plan p2c-workspace/plan/sprint-plan.md --output p2c-workspace/plan/cost-estimate.md` and render in the visual server's `/cost` view.

## Final output

`p2c-workspace/POC-PACKAGE.md` containing:

1. **Executive summary** — what we built, what we validated, what production looks like
2. **POC** — link to `p2c-workspace/poc/` + DEMO.md + production-gap.md
3. **Production design specs** — links to architecture, design, BRD, PRD
4. **Production plan** — sprint plan with N sprints and the goal per sprint
5. **Cost estimate** — totals, breakdown, sensitivity
6. **Recommended next 30 / 60 / 90 days**
7. **Open risks and decisions**

## Stop conditions

- **Pause before starting any build code** until phase 3 mockups exist and the user has approved them.
- Confirm with the user before any code execution beyond local Node/Python project scaffolding.
- Confirm before installing global tooling.
- Pause after the POC works locally for the user to validate before producing the prod plan.
- Pause after the cost estimate is generated for the user to review before locking the package.
- At every phase boundary, run the traceability checker and report its output
  as described under "The phase-boundary ritual" in `skills/p2c/SKILL.md`.
  Open findings, staleness and gaps are named in the phase summary every time.
  The checker is advisory — it never blocks a phase from advancing, but a
  phase may not advance without its output being reported.
