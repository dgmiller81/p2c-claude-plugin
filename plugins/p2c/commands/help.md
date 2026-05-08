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
| **lead-ux-designer** | **Mockups (mandatory)**, wireframes, prototypes, design tokens, component library, brand application, accessibility, design handoff |
| **lead-developer** | Walking skeleton, vertical slices, code structure, CI, **POC implementation**, wiring design tokens into the codebase |
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

### Absolute rules (every command)

These apply across all p2c commands:

1. **Every section of every active phase must be completed** unless you explicitly skip it. There are no silent gaps.
2. **Mockups are mandatory.** Phase 3 will not be marked complete, and build commands will not start, without high-fidelity mockups of every key screen — covering default, empty, loading, error, and success states.
3. **Mockups must look enterprise-grade.** Real-feeling sample data, polished visuals. Match your brand if you've provided one; otherwise the orchestrator applies the Enterprise Default Style described in `references/visual-standards.md`.

### Quick start

1. Run `/p2c:full` for the full journey, or pick a scoped command above for one lane.
2. Paste a brief, link to existing docs, or just describe the idea. **If you have brand assets** (logo, palette, typography, brand book) share them up front — the mockups will pick them up.
3. The orchestrator reads your inputs, does background research, and starts asking the first cluster of phase questions.
4. Approve / push back on the deliverables as they land. Mockups in particular need explicit approval before the orchestrator will move to architecture or code.

### Updating the plugin

To force a refresh from the source repo and pull the latest plugin version:

```
/plugin marketplace update p2c-marketplace
/plugin install p2c@p2c-marketplace
```

The first line refreshes marketplace metadata from `dgmiller81/p2c-claude-plugin`. The second re-installs the plugin from that refreshed marketplace, picking up any new commits.

To enable auto-update so this happens at startup: open `/plugin`, go to the **Marketplaces** tab, and toggle **Enable auto-update** on `p2c-marketplace`.

---

After printing this, ask: "Which scope would you like to start with?"
