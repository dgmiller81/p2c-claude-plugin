# The Essential Stack for Test & Harden

Testing isn't about coverage numbers — it's about confidence to ship on a Friday. Keep what catches real bugs, drop what just feels rigorous.

## The "Best of" Shortlist
- **Testing pyramid** — many unit, fewer integration, fewest E2E
- **Critical-path E2E tests** — the 3–5 flows that must never break
- **Contract testing at boundaries** — APIs, queues, third-party integrations
- **OWASP Top 10 review** — covers ~80% of real-world web vulns
- **Dependency scanning** — automated, on every PR
- **Performance budgets** — measurable, not vibes
- **Accessibility automated checks (axe)** — catches ~30% of a11y issues for free

Everything else is supporting cast.

## How to Structure the Process

### Phase 1: Lock the Pyramid (Week 1)
- **Unit tests** for logic, pure functions, edge cases — fast, run on every save
- **Integration tests** for boundaries (DB, API handlers, message consumers) — run in CI
- **E2E tests** only for the critical paths — slow, run before deploy
- Target ratio: **~70/20/10** — invert it and your test suite becomes a tax

### Phase 2: Cover the Critical Paths (Week 1)
- List the **3–5 flows** where a regression = revenue loss or trust loss
  - e.g., signup, checkout, primary task, data export
- Write **E2E tests** for each (Playwright or Cypress)
- Run them on every deploy to staging; gate production on green
- These are the only tests allowed to be slow

### Phase 3: Test the Boundaries (Week 2)
- **API contract tests** — request/response shapes pinned (Pact, Schemathesis, or just JSON schema)
- **Database tests** — migrations apply cleanly forward and back
- **Third-party integrations** — record/replay (VCR, MSW, WireMock)
- **Auth flows** — every role × every protected resource

### Phase 4: Security Hardening (Week 2)
- Walk the **OWASP Top 10** against your app:
  - Broken access control, crypto failures, injection, insecure design, misconfig, vulnerable deps, auth failures, integrity failures, logging gaps, SSRF
- Run **automated scans**:
  - **SAST** (Semgrep, CodeQL) — code-level
  - **SCA** (Dependabot, Snyk, Trivy) — dependencies
  - **DAST** (OWASP ZAP) — running app
  - **Secret scanning** (gitleaks, TruffleHog) — git history
- Fix **critical/high** before launch; track medium/low as issues

### Phase 5: Performance Check (Week 3)
- Define **performance budgets**:
  - Page load (LCP <2.5s, INP <200ms, CLS <0.1)
  - API p95 latency targets per endpoint
  - Bundle size ceiling
- Run **load tests** against staging (k6, Locust, Artillery)
  - Test 2–3× expected peak traffic
  - Watch for memory leaks, connection pool exhaustion, DB lock contention
- Profile the slow paths (flame graphs, EXPLAIN ANALYZE)

### Phase 6: Accessibility Pass (Week 3)
- Run **axe-core** in tests and CI — catches the easy 30%
- **Manual keyboard nav** through every flow — Tab, Enter, Esc work as expected
- **Screen reader spot check** (VoiceOver, NVDA) on critical screens
- **Contrast check** at all states (default, hover, focus, disabled, error)
- WCAG 2.1 AA as the bar

### Phase 7: Pre-Launch Hardening (Final week)
- **Chaos test** the critical paths: kill a DB connection, drop network, fill the disk
- **Backup + restore drill** — proven, not theoretical
- **Incident runbook** — top 5 likely failures, response steps
- **Rate limiting** on public endpoints
- **Input validation** on every external boundary
- **Error pages** for 404, 500, maintenance — branded, helpful

## The Test Plan Checklist
```
Critical paths covered by E2E:    [list]
API contracts pinned:             [yes/no]
SAST + SCA + secrets scan:        [in CI]
OWASP Top 10 reviewed:            [date, owner]
Performance budgets defined:      [yes/no]
Load test results:                [link]
Accessibility scan + manual:      [date, owner]
Backup restore tested:            [date]
Runbook written:                  [link]
```

## The Minimum Viable Toolset
- **Unit + integration**: native to your stack (Vitest/Jest, Pytest, Go test)
- **E2E**: Playwright (preferred) or Cypress
- **API contract**: Pact, Schemathesis, or JSON schema validation
- **Load**: k6 (developer-friendly, scripts in JS)
- **SAST**: Semgrep or CodeQL
- **SCA**: Dependabot + Snyk or Trivy
- **Secret scanning**: gitleaks in CI + GitHub native
- **Accessibility**: axe-core (Playwright integration) + manual VoiceOver/NVDA
- **Sentry**: error tracking with release tagging

Most are free or have generous free tiers. The cost is configuration time, not licenses.

## The Mental Model
Hardening is **buying insurance against the failures most likely to actually happen**. The shortlist is built around three questions:

1. **Will this regress silently?** → tests on the critical paths
2. **Will this get exploited?** → OWASP + scans + boundary validation
3. **Will this fall over under load?** → budgets + load tests + observability

The goal isn't 100% coverage or zero vulnerabilities — it's **confidence proportional to the risk**. A pre-launch product with 80% confidence and a fast feedback loop beats a 99% confident product that takes a week to deploy a fix.
