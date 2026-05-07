# Runbook — <Product Name>

**Owner:** <on-call lead>
**Last reviewed:** YYYY-MM-DD

> If you are paged and don't know what to do, start at the top.

## 0. Before you do anything
1. Acknowledge the alert in PagerDuty / Opsgenie.
2. Open the **status page** (link).
3. Open the **observability dashboard** (link).
4. Decide: is this user-impacting now? If yes → start a status update draft.

## 1. <Failure mode 1 — e.g., API 5xx spike>
**Symptoms:** <what alerts fire, what users see>
**Likely causes:** <list>
**Diagnosis:**
```bash
# commands or links to check
```
**Mitigation:**
1. <step>
2. <step>
**Rollback:**
- Feature flag <name> → `OFF`
- If deployed in last 30 min: revert to release <…>

## 2. <Failure mode 2 — e.g., DB connection saturation>
**Symptoms:** <…>
**Likely causes:** <…>
**Diagnosis:** <…>
**Mitigation:** <…>

## 3. <Failure mode 3 — e.g., third-party (Stripe / Auth) outage>
**Symptoms:** <…>
**Likely causes:** <…>
**Diagnosis:** <…>
**Mitigation:** <…>

## 4. <Failure mode 4 — e.g., latency regression>
**Symptoms:** <…>
**Diagnosis:** flame graph / EXPLAIN ANALYZE / OTel traces
**Mitigation:** <feature flag, rollback, scale up>

## 5. <Failure mode 5 — e.g., data inconsistency>
**Symptoms:** <…>
**Diagnosis:** <…>
**Mitigation:** <…>

## Post-incident
1. Write a brief incident report — even if recovery was fast.
2. Open follow-up tickets for any process gaps you hit.
3. Schedule a 30-min retro within 5 working days.
