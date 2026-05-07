# The Essential Stack for Measure & Iterate

Post-launch is where most products quietly die — not from one bug, but from drift. Keep what creates a tight loop between user reality and what you build next.

## The "Best of" Shortlist
- **AARRR / Pirate Metrics** — the only funnel framework you actually need
- **Activation metric** — the single most predictive number for retention
- **Cohort retention curves** — flatten or die
- **Qualitative + quantitative loop** — numbers tell you what, users tell you why
- **Continuous discovery (Teresa Torres)** — weekly user touchpoints, not quarterly research
- **RICE / ICE for prioritization** — same scoring you used in discovery
- **Tech debt budget** — explicit % of capacity, not "when we have time"

Everything else is dashboard theater.

## How to Structure the Process

### Phase 1: Define What "Working" Means (Week 1 post-launch)
- Pick **one North Star metric** that captures product value delivered
  - SaaS: weekly active users completing primary job
  - Marketplace: matched transactions per week
  - Content: time-to-value or completion rate
- Define the **AARRR funnel** with concrete events:
  - **A**cquisition — visit, signup
  - **A**ctivation — completed key action that proves value
  - **R**etention — returns within N days/weeks
  - **R**eferral — invites or shares
  - **R**evenue — paid conversion / expansion
- Set **baseline targets** for each stage based on industry benchmarks

### Phase 2: Instrument Once, Properly (Week 1)
- Define a **tracking plan** before adding code (event names, properties, identity model)
- Use **a single analytics tool** for product events (PostHog, Mixpanel, Amplitude)
- Standardize **event naming** (`object_action` — `report_created`, `invite_sent`)
- Identify the **activation event** explicitly — instrument it first
- Wire **server-side events** for anything tied to revenue (don't trust the browser)

### Phase 3: Build the Feedback Loop (Ongoing)
- **Weekly user calls** — minimum 3, ideally 5
  - Mix of: new signups, active users, churned users
  - Talk for 20 min, watch them use the product for 10
- **In-app feedback widget** — low-friction, routed to one inbox
- **Support ticket triage** — read tickets weekly, tag themes
- **NPS or PMF survey** — Sean Ellis "how disappointed would you be" works
- **Session replays** for activation and key drop-off points (PostHog, FullStory, Hotjar)

### Phase 4: Run the Weekly Rhythm (Continuous)
- **Monday**: review metrics + last week's experiments — what moved, what didn't
- **Tuesday/Wednesday**: user research — interviews, replays, support themes
- **Thursday**: prioritize next bets using **RICE** or **ICE**
- **Friday**: ship the smallest experiment that tests the highest-confidence bet
- Repeat. The cadence is the magic — not any single ritual.

### Phase 5: Prioritize Honestly (Continuous)
- Score every meaningful idea with **RICE** (Reach × Impact × Confidence ÷ Effort)
- Be brutal on **Confidence** — most ideas are 30%, not 90%
- Maintain explicit buckets:
  - **Now** — in flight (≤3 items)
  - **Next** — committed for next cycle
  - **Later** — backlog with rationale
  - **Never** — explicit graveyard so they stop coming back
- Reserve **20–30% capacity** for tech debt, security patches, and small bug fixes

### Phase 6: Run Experiments, Not Opinions (Continuous)
- Frame each bet as a **hypothesis**:
  - *"If we [change X], then [metric Y] will [direction] because [reason]"*
- Define **success threshold** before shipping
- A/B test where statistically meaningful traffic exists; otherwise use **before/after with cohort comparison**
- Document the **outcome** — wins and losses both teach
- Kill or scale based on data, not pride

### Phase 7: Quarterly Strategy Check (Every 90 days)
- Are we hitting the **North Star**? If not, why?
- Has the **target user** shifted? The job?
- Which **persona/segment** is retaining best? Double down there.
- What should we **stop doing**?
- Update the **roadmap** — Now/Next/Later — based on what you learned

## The Metrics Hierarchy
```
NORTH STAR (one)
└── INPUT METRICS (3–5) — things we can directly influence
    └── EVENTS (the instrumented actions)
        └── PROPERTIES (the dimensions to slice by)
```
If a metric isn't either the North Star, an input to it, or a guardrail (error rate, latency, support volume), question why you're tracking it.

## The Minimum Viable Toolset
- **Product analytics** — PostHog (open + free tier), Mixpanel, or Amplitude
- **Session replay** — PostHog, FullStory, or Hotjar
- **Feedback** — Canny, in-app widget (Featurebase, Frill), or a Tally form
- **User interviews** — Calendly + Zoom + Otter.ai (or Grain)
- **Surveys** — Typeform or Tally
- **Roadmap** — Linear or Productboard
- **Experimentation** — PostHog (built-in), GrowthBook, Statsig

Five to seven tools, mostly with free tiers. Pick one per category — overlap is wasted budget.

## The Mental Model
Iteration is **a learning loop, not a feature factory**. The shortlist optimizes for:

1. **Know what to look at** (North Star + AARRR + activation)
2. **Hear users continuously** (weekly research, replays, support themes)
3. **Bet small and often** (RICE → hypothesis → ship → measure → decide)

The teams that win post-launch aren't shipping more features — they're **closing the loop faster between user reality and product change**. If your weekly cycle has all three (data, voice of customer, decisive prioritization), you'll out-iterate competitors who only do one or two.

The product is never finished. The loop is the product.
