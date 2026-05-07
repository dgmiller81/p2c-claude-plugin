# Rollback Plan — <Product Name>

**Owner:** <name>
**Last rehearsed:** YYYY-MM-DD (must be within 7 days of launch)

> Decision criteria, not panic. If any criterion is hit, roll back without debate.

## When to roll back

Roll back if **any** of these are true after a release:

- Error rate (5xx) > <X>% sustained over 5 min
- p95 latency > <Y>ms sustained over 5 min
- Conversion drop > <Z>% vs. last 7-day baseline
- Critical user flow E2E fails 2 consecutive runs
- A security finding rated High or Critical surfaces

## How to roll back

### Option A — Feature flag (preferred, ~30 seconds)
- Flag(s): `<name>` → set to `OFF` in <PostHog/LaunchDarkly>
- Verify: <metric / event> should return to baseline within 2 minutes

### Option B — Deploy revert (~5 minutes)
1. `git revert <commit>` and push to `main`, OR
2. Re-deploy previous release tag: `<tag>`
3. Verify health: <link to dashboard>

### Option C — DB rollback (last resort)
- Most recent backup: <retention policy>
- Restore procedure: `<runbook link>` (rehearsed YYYY-MM-DD)
- **Note:** restoring loses data written since the backup. Require explicit decision-maker approval.

## Pre-launch rehearsal record

| Date | Rehearsed by | Result | Notes |
|------|--------------|--------|-------|
| | | Pass / Fail | |

## Comms during rollback

1. Status page: post "investigating" within 5 min, "identified" within 15 min, "resolved" once metrics return.
2. Internal Slack: `#incident-<date>`.
3. If user-impacting >30 min: customer email (template in `comms-kit/`).
