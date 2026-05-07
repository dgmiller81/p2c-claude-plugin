# Sprint Estimation Model

How the `scrum-master` agent and the `estimate_cost.py` script compute sprint plans and cost estimates.

## Defaults

| Parameter | Default | Notes |
|---|---|---|
| Sprint length | 2 weeks (10 working days) | Tunable |
| Hours per work day | 8 | Tunable |
| Focus factor | 0.70 | Standard scrum factor — adjusts for ceremonies, context switching, interruptions |
| Sprint capacity per role | `allocation% × 80h × 0.70` | E.g., 100% allocation = 56 productive hours per sprint |
| Default team mix | See below | Tunable per project |

## Default team mix (production sprint)

Adjust per project; this is the starting point.

| Role | Allocation | Productive hrs / sprint |
|---|---|---:|
| Scrum Master | 50% | 28 |
| Technical Lead | 100% | 56 |
| Business Analyst | 50% | 28 |
| Full Stack Engineer (×2) | 100% each | 112 |
| QA Engineer | 100% | 56 |
| DevOps Engineer | 50% | 28 |
| Backend Engineer | (optional, per project) | — |
| AI/ML Engineer | (optional, per project) | — |
| Data Engineer | (optional, per project) | — |

**Total default productive capacity per sprint:** ~308 hrs.

## Default team mix (POC sprint)

Slimmer team during POC; adjust per project.

| Role | Allocation | Productive hrs / sprint |
|---|---|---:|
| Technical Lead | 100% | 56 |
| Full Stack Engineer | 100% | 56 |
| Business Analyst | 25% | 14 |
| QA Engineer | 25% | 14 |

**Total:** ~140 hrs. POC is meant to be small.

## Sprint sequencing rules

1. **Sprint 0 / Sprint 1: Walking skeleton.** Always. Auth, deploy, observability, one trivial feature end-to-end. Do not skip — discovering infra problems mid-build is expensive.
2. **Risk-first slice ordering.** The riskiest assumption gets the next slice.
3. **One vertical slice per slot of capacity.** Don't try to fit multiple slices in one sprint unless they're truly independent.
4. **Reserve 20–30% capacity per sprint for tech debt + unplanned bugs.** Capture this in the plan, not in vibes.
5. **Test sprints aren't separate sprints.** QA capacity is *inside* every sprint. The exceptions are dedicated **hardening sprints** before launch (perf load, security pen test, a11y manual pass) — those *are* their own sprints.

## How to estimate sprints from a story map

1. Sum the estimated hours per role across all Must-have stories.
2. Add overhead: 15% for code review + integration, 10% for unforeseen scope.
3. Add hardening: 1–2 dedicated hardening sprints before launch.
4. Add a launch sprint.
5. Number of dev sprints = `ceil((total_dev_hours) / sprint_capacity_per_team)`.
6. Total sprints = dev + hardening + launch.

## Example: 12-story MVP, default prod team

- Story-level dev hours: 600 (FullStack), 200 (Backend), 100 (TechLead), 200 (QA), 80 (DevOps), 60 (BA)
- Add 15% review overhead: ×1.15 → ~1430 hrs
- Add 10% unforeseen: ×1.10 → ~1573 hrs
- Sprint capacity (productive, prod team): ~308 hrs
- Dev sprints: `ceil(1573 / 308)` = **6 sprints**
- Hardening: **2 sprints** (load + perf in 1, security + a11y in the other)
- Launch: **1 sprint**
- **Total: 9 sprints (~18 weeks / ~4.5 months)**

## Sensitivity

When the cost estimator output includes sensitivity, it should show:

- **±1 sprint** (what happens if scope grows or shrinks by ~1 sprint of work)
- **±1 engineer** (what removing or adding a Full Stack Engineer at default allocation does)
- **AI-assist on/off** (compare AI-assisted vs. standard rates totals)
- **Focus factor 0.6 vs. 0.7 vs. 0.8** (more conservative vs. more aggressive capacity assumption)

## Inputs to `estimate_cost.py`

The script accepts a sprint plan in this YAML-or-Markdown structure (Markdown with table per sprint is fine; the script uses regex to parse). Minimum fields per sprint:

```yaml
sprint: 1
goal: "Walking skeleton + auth"
hours_by_role:
  tech_lead: 40
  full_stack: 80
  qa_engineer: 24
  devops: 16
  scrum_master: 12
  business_analyst: 8
```

Output includes per-sprint cost (standard + AI-assisted), per-role total, grand total, and the sensitivity table.
