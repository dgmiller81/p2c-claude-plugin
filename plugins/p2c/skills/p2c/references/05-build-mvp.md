# The Essential Stack for Build (MVP)

The build phase is where discipline beats heroics. Keep the practices that compound, drop the ones that just look professional.

## The "Best of" Shortlist
- **Trunk-based development** — short-lived branches, frequent merges
- **Vertical slicing** — ship one feature end-to-end before starting the next
- **CI on every push** — lint, test, build, deploy preview
- **Conventional Commits** — readable history, automated changelogs
- **Pull requests with small diffs** — <400 lines, reviewed within hours
- **Feature flags** — decouple deploy from release
- **Pre-commit hooks** — formatters and linters before code leaves the laptop

Everything else is ceremony.

## How to Structure the Process

### Phase 1: Set Up the Foundation (Days 1–2)
- Initialize repo with **README, LICENSE, .gitignore, CODEOWNERS**
- Configure **branch protection** on `main` (PRs required, CI must pass)
- Wire **CI/CD** — GitHub Actions, preview environments per PR
- Add **pre-commit hooks** (Husky + lint-staged, or pre-commit framework)
- Stand up **Sentry, analytics, and structured logging** before the first feature

### Phase 2: Build the Walking Skeleton (Week 1)
- Ship the **thinnest end-to-end slice** through every layer:
  - UI → API → DB → back to UI, deployed to staging
- Includes auth, deployment, monitoring, one trivial feature
- **No feature work** until the skeleton is deployed and observable
- This is the moment to discover infra problems — cheaply

### Phase 3: Slice the Backlog (Week 1)
- Break each MVP story into **1–3 day vertical slices**
- Order by risk: highest-risk slice first (riskiest assumption test)
- Each slice = one PR, one deploy, one observable change in production
- Avoid horizontal slicing ("build all the APIs first") — it hides integration risk

### Phase 4: Develop with Discipline (Weeks 2–N)
- One **feature branch** per slice, lifespan <2 days
- **Test as you go**: TDD where it fits, otherwise tests in the same PR
- Open a **draft PR early** — invites review, runs CI continuously
- Self-review the diff before requesting review — catches half the issues
- Use **Conventional Commits**: `feat:`, `fix:`, `chore:`, `docs:`, etc.

### Phase 5: Review & Merge (Daily)
- PRs should be **small** (<400 lines), **focused** (one concern), **reviewed in hours**
- Reviewer checks: correctness, tests, security, naming, edge cases
- Use **suggested changes** for nitpicks, comments for discussion
- **Squash merge** to keep `main` history clean
- Delete the branch on merge

### Phase 6: Ship Behind Flags (Continuous)
- Wrap risky or incomplete features in **feature flags** (LaunchDarkly, PostHog, ConfigCat, or homegrown)
- Deploy to production continuously; release to users on your own schedule
- Use flags for:
  - Internal-only previews
  - Gradual rollouts (1% → 10% → 100%)
  - Kill switches for misbehaving features

### Phase 7: Keep the House Clean (Continuous)
- **Refactor inside the slice** that touches the code — boy scout rule
- Track tech debt as **explicit issues**, not vibes
- **Dependency updates weekly** (Renovate or Dependabot)
- **No broken `main`** — if CI is red, drop everything and fix it

## The PR Checklist (paste in template)
```
- [ ] Linked to issue / story
- [ ] Tests added or updated
- [ ] Docs updated (README, ADR, runbook if needed)
- [ ] No new warnings, no skipped tests
- [ ] Feature flagged if user-visible
- [ ] Telemetry added if it's a new flow
- [ ] Self-reviewed the diff
```

## The Minimum Viable Toolset
- **GitHub** — code, PRs, Actions (CI/CD), Projects
- **Renovate or Dependabot** — automated dependency PRs
- **A formatter + linter** — Prettier + ESLint, Black + Ruff, gofmt, etc.
- **A testing framework** native to your stack — Vitest/Jest, Pytest, Go test
- **Sentry** — error tracking from PR #1
- **A feature flag service** — PostHog (free), LaunchDarkly, or ConfigCat
- **Preview deploys** — Vercel, Netlify, Render, or per-PR environments

Seven things. Set them up once on day 1; they pay rent every day after.

## The Mental Model
The build phase is **a series of small, reversible bets**. The shortlist optimizes for:

1. **Short feedback loops** (CI, preview deploys, small PRs)
2. **Always-shippable main** (trunk-based + flags)
3. **Visible state** (telemetry, flags, error tracking)

The teams that ship fast aren't faster typists — they have **shorter cycles between idea and feedback**. Every practice above is in service of shrinking that cycle.

If a process doesn't make the next slice easier to ship, cut it.
