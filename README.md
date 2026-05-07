# p2c — Product-to-Customer Orchestration Plugin

A Claude Code plugin that walks a product owner/manager through every phase of taking an idea to a shipped product, using a coordinated team of specialized sub-agents and the best-practice playbook in [plugins/p2c/skills/p2c/references/](plugins/p2c/skills/p2c/references/).

## What it does

- Acts as **orchestrator and program manager** across 8 phases (Discovery → Measure & Iterate)
- Spawns **7 specialized sub-agents** for each role (PO, SM, Architect, Dev, QA, BA, Research/Marketing)
- Provides **visual guidance** via a local web server with interactive forms and progress dashboards
- Researches the web, ingests existing docs/code, and makes **educated nudges**
- Produces **specific, file-backed deliverables** for every area — nothing skipped unless explicitly told to skip
- Generates **detailed sprint plans and cost estimates** using the AI-assisted rate card

## Slash commands

| Command | Focus |
|---|---|
| `/p2c:full` | Full orchestration end-to-end (phases 1–8) |
| `/p2c:product` | Phases 1–2 + measurement framework — discovery, validation, requirements, scope |
| `/p2c:design` | Phase 3 — wireframes, prototypes, design system, a11y |
| `/p2c:tech-scope` | Phase 4 — architecture, ADRs, threat model, cost-aware design + sprint scope |
| `/p2c:tech-build` | Phase 5 (POC mode) — working local prototype, not prod-ready |
| `/p2c:tech-prod` | Phases 5–7 — production build, hardening, launch readiness |
| `/p2c:launch` | Phase 7 + comms — launch strategy and all launch documentation |
| `/p2c:poc` | All-in-one — full POC + production sprint plan + cost estimate |
| `/p2c:help` | Print the command map, agent list, and quick-start |

## Sub-agents

Each agent operates in its own lane with very specific outputs:

- **product-owner** — decisions, PRD, prioritization, kill criteria
- **scrum-master** — sprint planning, story breakdown, ceremonies, story↔component linkage
- **lead-architect** — C4 diagrams, ADRs, threat model, stack, observability plan
- **lead-developer** — vertical slices, code structure, CI, **POC implementation**
- **lead-qa-coordinator** — test plan, regression, perf, security, a11y, launch QA gate
- **business-analyst** — BRD, requirements traceability matrix, gap analysis, compliance
- **research-marketing** — market research, GTM, positioning, comms, growth experiments

## Installation

In Claude Code, install directly from this repo:

```
/plugin marketplace add dgmiller81/p2c-claude-plugin
/plugin install p2c@p2c-marketplace
```

Or, from a local clone:

```
/plugin marketplace add /path/to/p2c-claude-plugin
/plugin install p2c@p2c-marketplace
```

See [INSTALL.md](INSTALL.md) for full details, the fallback flat-command install, and the Python dependency note.

## Cost rate card

Built into [plugins/p2c/skills/p2c/scripts/estimate_cost.py](plugins/p2c/skills/p2c/scripts/estimate_cost.py). AI-assisted effective rates used by default (20% effective discount).

| Role | $/hr | AI-assisted $/hr |
|---|---:|---:|
| Scrum Master | 78 | 62.40 |
| Technical Lead | 91 | 72.80 |
| Business Analyst | 72 | 57.60 |
| Full Stack Engineer | 82 | 65.60 |
| AI/ML Engineer | 83 | 66.40 |
| Data Engineer | 81 | 64.80 |
| QA Engineer | 68 | 54.40 |
| Backend Engineer | 73 | 58.40 |
| DevOps Engineer | 77 | 61.60 |
