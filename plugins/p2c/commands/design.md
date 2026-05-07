---
description: Design lane only — wireframes, clickable prototype, 5-user usability testing, design system, accessibility pass.
argument-hint: [optional context — link to PRD, story map, or existing design files]
---

# /p2c:design — Design Lane Only

The user wants only the **design** scope. Activate the `p2c` skill scoped to phase 3.

## Prerequisites

Before starting, check whether `p2c-workspace/02-requirements/prd.md` and `story-map.*` exist. Design without validated product scope is wasted motion — if they're missing, recommend running `/p2c:product` first or accept a quick pass to capture the essentials.

## Active phase

- **Phase 3:** Design — sketch → wireframe → clickable prototype → 5-user usability test → design system tokens + components → accessibility pass + responsive states.

## Active agents

- **product-owner** (for golden-path framing and copy-tone calls)
- **lead-developer** (only at handoff: confirms feasibility, flags responsive/state edge cases)

## Entry sequence

1. Read `skills/p2c/references/03-design.md`.
2. Read PRD and story map if they exist; otherwise capture a quick-and-dirty version with the user.
3. Offer the visual server with the journey-map and component-checklist views.
4. Walk the 6-phase design workflow from the reference.

## Deliverables

- `p2c-workspace/03-design/wireframes/` — links to Figma file or local exports
- `p2c-workspace/03-design/prototype.md` — link + golden-path description
- `p2c-workspace/03-design/usability-tests.md` — 5–8 user notes, fixes applied
- `p2c-workspace/03-design/design-tokens.md` — color, type, spacing, radii, shadows
- `p2c-workspace/03-design/components.md` — list of locked components for MVP
- `p2c-workspace/03-design/a11y-checklist.md` — WCAG 2.1 AA pass with evidence
- `p2c-workspace/03-design/states.md` — empty/loading/error/success per screen

## Final output

`p2c-workspace/03-design/SUMMARY.md` with screenshots/links to the high-fidelity flow, design system summary, and a handoff brief for development.
