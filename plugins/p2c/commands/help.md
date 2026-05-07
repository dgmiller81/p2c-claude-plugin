---
description: Show the p2c command map, sub-agents, and quick-start.
---

# /p2c:help

The user invoked the help command. Print the message below verbatim, then ask if they'd like you to start a specific scope.

---

## p2c — Product-to-Customer orchestration

Idea → shipped product, with a coordinated team of specialized sub-agents and a phase-by-phase playbook.

### Slash commands

| Command | Scope | Use when… |
|---|---|---|
| `/p2c:full` | Phases 1–8 end-to-end | You want the whole journey, sequenced |
| `/p2c:product` | Phases 1–2 (+8 framework) | Discovery, validation, PRD, BRD, story map, success metrics |
| `/p2c:design` | Phase 3 | Wireframes, prototype, 5-user usability tests, design system, a11y |
| `/p2c:tech-scope` | Phase 4 + planning slice of 5–6 | Architecture, ADRs, threat model, sprint scope, **cost estimates**, no code |
| `/p2c:tech-build` | Phase 5 (POC) | Build a working **local** prototype (not production-ready) |
| `/p2c:tech-prod` | Phases 5–7 | Full production build, hardening, launch readiness |
| `/p2c:launch` | Phase 7 + comms | Soft launch, gradual rollout, runbook, status page, comms kit |
| `/p2c:poc` | All-in-one | Build POC + validate + production design specs + sprint plan + cost estimate |
| `/p2c:help` | (this) | Show this map |

### Sub-agents (auto-dispatched by the orchestrator)

| Agent | Lane |
|---|---|
| **product-owner** | PRD, JTBD, prioritization, kill criteria, post-launch product calls |
| **scrum-master** | Story breakdown, sprint planning, ceremonies, velocity, link stories ↔ components |
| **lead-architect** | C4 diagrams, ADRs, stack, data model, threat model, observability |
| **lead-developer** | Walking skeleton, vertical slices, code structure, CI, **POC implementation** |
| **lead-qa-coordinator** | Test plan, regression, security, performance, a11y, launch QA gate |
| **business-analyst** | BRD, requirements traceability matrix, gap analysis, compliance |
| **research-marketing** | Market research, competitive scan, GTM, positioning, launch comms, growth experiments |

You can also invoke an agent directly via Claude Code's normal agent invocation if you want a focused pass on one lane.

### Visual guidance

Most phases offer a local web server with interactive forms (story map, journey map, sprint timeline, cost dashboard). The orchestrator will offer to start it. The bundled script lives inside the installed plugin under `skills/p2c/scripts/start_visual_server.py`; the orchestrator knows where it is and will invoke it for you.

### Cost estimation

Every plan can be costed via the AI-assisted rate card. The orchestrator runs `scripts/estimate_cost.py` against `p2c-workspace/plan/sprint-plan.md` and writes the result to `p2c-workspace/plan/cost-estimate.md`. Both AI-assisted (20% effective discount) and standard rates are produced, with per-sprint, per-role, and ±1-sprint / ±1-engineer sensitivity.

### Workspace layout

Everything lands in `p2c-workspace/` in your current directory:

```
p2c-workspace/
├── status.json
├── 01-discovery/   02-requirements/   03-design/   04-architecture/
├── 05-build/       06-test-and-harden/   07-launch/   08-measure/
├── poc/            (only with /p2c:tech-build or /p2c:poc)
├── plan/           (sprint-plan.md, cost-estimate.md)
└── research/
```

### Quick start

1. Run `/p2c:full` for the full journey, or pick a scoped command above for one lane.
2. Paste a brief, link to existing docs, or just describe the idea.
3. The orchestrator reads your inputs, does background research, and starts asking the first cluster of phase questions.
4. Approve / push back on the deliverables as they land.

---

After printing this, ask: "Which scope would you like to start with?"
