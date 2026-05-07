# The Essential Stack for Launch

Launch isn't a day — it's a controlled rollout. Keep what reduces blast radius, drop the marketing theater that distracts from operability.

## The "Best of" Shortlist
- **Soft launch / closed beta** — real users, contained risk
- **Feature flags + gradual rollout** — 1% → 10% → 50% → 100%
- **Pre-written rollback plan** — decision criteria, not panic
- **Status page** — public-facing, builds trust during incidents
- **On-call rotation + runbook** — someone is always responsible
- **Day-1 baseline metrics** — you can't detect drift without a starting line
- **Launch communications plan** — users, support, internal stakeholders

Everything else is press-release cosplay.

## How to Structure the Process

### Phase 1: Pre-Launch Readiness (Week before)
- Run a **launch-readiness review** — checklist below
- **Freeze risky changes** 48 hours before launch (no schema migrations, no infra moves)
- **Verify backups** restored cleanly within the last 7 days
- **Confirm on-call** for the first 72 hours
- **Test the rollback** — actually execute it in staging end-to-end

### Phase 2: Soft Launch / Beta (Days 1–7)
- Open access to a **small, friendly cohort** (10–100 users)
  - Personal network, waitlist signups, design partners
- Watch **error rates, latency, conversion** like a hawk
- **Daily standup** focused on launch issues only
- Collect feedback through one channel (in-app form, Slack, email — not all three)
- Fix anything that breaks the core job; defer everything else

### Phase 3: Gradual Rollout (Week 2)
- Use **feature flags** to expand access:
  - Day 1 of public: **1%** of new traffic / signups allowed in
  - Day 3: **10%** if metrics hold
  - Day 7: **50%** if metrics hold
  - Day 14: **100%**
- Define **stop conditions** before each step:
  - Error rate >X
  - p95 latency >Y
  - Conversion drop >Z%
- Hitting any = roll back, don't debate

### Phase 4: Public Launch Day
- **Comms ready** — landing page live, email queued, social posts drafted, support brief sent
- **War room open** — engineering, support, comms in one channel for the day
- **Monitoring on big screens** — error rate, latency, signups, revenue
- **Status page primed** — incident template ready to publish
- **Capacity headroom verified** — autoscaling tested, DB connections sized

### Phase 5: First 72 Hours
- **Active triage** — respond to bugs in hours, not days
- **Daily metrics review** — activation, error rate, support volume
- **Hotfix flow** ready — small PRs, fast review, behind a flag if possible
- Resist the urge to **add features** — stabilize first

### Phase 6: Post-Launch Review (Week 2)
- Run a **launch retrospective**:
  - What went well?
  - What broke?
  - What surprised us?
  - What would we do differently?
- Capture **action items** with owners and dates
- Update **runbook** with anything you learned the hard way

## The Launch-Readiness Checklist
```
INFRASTRUCTURE
- [ ] Production environment provisioned and load-tested
- [ ] Autoscaling configured and verified
- [ ] Database backups automated, restore tested in last 7 days
- [ ] Secrets managed, rotated where required
- [ ] DNS, SSL, CDN configured

OBSERVABILITY
- [ ] Error tracking live (Sentry) with alerts to on-call
- [ ] Metrics dashboards (RED + business KPIs)
- [ ] Logs structured, searchable, retained per policy
- [ ] Traces enabled for critical paths
- [ ] Status page set up

SECURITY
- [ ] OWASP Top 10 review complete
- [ ] Pen test or scan done (if applicable)
- [ ] Rate limiting on public endpoints
- [ ] PII handling reviewed against compliance scope

OPERATIONS
- [ ] On-call rotation set, escalation path documented
- [ ] Runbook for top 5 failure modes
- [ ] Rollback plan written + tested
- [ ] Feature flags for risky paths

PRODUCT
- [ ] Critical-path E2E tests green
- [ ] Onboarding flow tested with 5+ real users
- [ ] Empty/loading/error states present
- [ ] Email + in-app notifications wired

COMMUNICATIONS
- [ ] Landing page live
- [ ] Launch email/post drafted, scheduled
- [ ] Support team briefed with FAQ
- [ ] Internal stakeholders informed
- [ ] Pricing/ToS/Privacy pages published
```

If a box isn't checked, you're not ready. Don't negotiate with the checklist.

## The Minimum Viable Toolset
- **Feature flags** — PostHog, LaunchDarkly, or ConfigCat
- **Status page** — Atlassian Statuspage, Better Stack, Instatus
- **Error tracking + alerting** — Sentry + PagerDuty or Opsgenie
- **Metrics dashboards** — Grafana, Datadog, or your cloud-native equivalent
- **Comms** — Linear or Notion for the runbook, Slack for the war room
- **Customer support** — Intercom, Plain, Linear-Customer, or just email

Six tools. Most you already have from earlier phases.

## The Mental Model
Launching is **the moment your assumptions meet reality at scale**. The shortlist optimizes for:

1. **Limit blast radius** (soft launch, gradual rollout, flags)
2. **See the impact instantly** (metrics, errors, status page)
3. **React without panic** (runbook, rollback, on-call)

The teams that launch cleanly aren't lucky — they treat launch as **a series of small, observable, reversible bets**, not a binary on/off switch. If you can answer "how do we undo this in 5 minutes?" for every step, you're ready.
