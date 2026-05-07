# Sprint Plan — <Product Name>

**Cadence:** 2-week sprints | **Team:** <names / roles>
**Total sprints:** <N> | **Target launch:** <date>

> The cost estimator (`scripts/estimate_cost.py`) reads the YAML blocks below.
> Hours are productive (post-focus-factor) hours. See `references/sprint-estimation-model.md`.

## Sprint 1 — Walking Skeleton
**Goal:** <one sentence — the demo at the end of this sprint>
**Demo:** <what stakeholders will see>

### Stories
| ID | Story | Component(s) | Owner role | Est. hrs |
|----|------|--------------|------------|----------|
| US-001 | | | | |

### Risks / Dependencies
- <risk> — mitigation
- <dep> — owner

### Definition of Done
- [ ] All stories meet team DoD
- [ ] Demo recorded
- [ ] Telemetry verified
- [ ] Behind feature flag in prod

```yaml
- sprint: 1
  goal: "Walking skeleton + auth + telemetry"
  hours_by_role:
    tech_lead: 40
    full_stack: 80
    qa_engineer: 24
    devops: 16
    scrum_master: 12
    business_analyst: 8
```

---

## Sprint 2 — <Slice name>
**Goal:** <…>
**Demo:** <…>

### Stories
| ID | Story | Component(s) | Owner role | Est. hrs |
|----|------|--------------|------------|----------|

```yaml
- sprint: 2
  goal: "First validated slice — <name>"
  hours_by_role:
    tech_lead: 30
    full_stack: 110
    qa_engineer: 32
    devops: 8
    scrum_master: 12
```

---

## Sprint 3 — <…>

```yaml
- sprint: 3
  goal: "<…>"
  hours_by_role:
    tech_lead: 30
    full_stack: 110
    qa_engineer: 32
    devops: 8
    scrum_master: 12
```

---

## Hardening Sprint (perf + security)
**Goal:** Meet perf budgets and OWASP Top 10. No new feature work.

```yaml
- sprint: H1
  goal: "Hardening — perf, security, a11y"
  hours_by_role:
    tech_lead: 30
    full_stack: 60
    qa_engineer: 80
    devops: 24
    scrum_master: 12
```

---

## Launch Sprint
**Goal:** Soft launch + gradual rollout, comms shipped.

```yaml
- sprint: L1
  goal: "Launch + comms + monitoring"
  hours_by_role:
    tech_lead: 24
    full_stack: 40
    qa_engineer: 32
    devops: 24
    scrum_master: 16
    business_analyst: 12
```

---

## Notes
- Add or remove sprints as the story map evolves.
- Run `python skills/p2c/scripts/estimate_cost.py --plan p2c-workspace/plan/sprint-plan.md --output p2c-workspace/plan/cost-estimate.md` after every change.
