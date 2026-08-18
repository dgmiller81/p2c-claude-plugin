---
description: Design lane only — wireframes, clickable prototype, 5-user usability testing, design system, accessibility pass, and **mandatory enterprise-grade mockups** for every key screen.
argument-hint: [optional context — link to PRD, story map, brand assets, or existing design files]
---

# /p2c:design — Design Lane Only

The user wants only the **design** scope. Activate the `p2c` skill scoped to phase 3.

## Absolute rules for this command

These are inherited from `SKILL.md` and `references/visual-standards.md` — repeated here because they govern this command:

1. **Every section listed under "Deliverables" below must be completed** unless the user explicitly skips an item with a recorded reason in `status.json`.
2. **Mockups are mandatory.** Phase 3 is **not** marked `delivered` without high-fidelity mockups for every key screen — default state plus empty / loading / error / success states.
3. **Mockups must be enterprise-grade.** Real-feeling sample data, real copy, polished visual language. Match the user's brand if branding is provided; otherwise apply the **Enterprise Default Style** in `references/visual-standards.md`.
4. **No exit from this command** until mockups exist and are reviewed by the user.

## Prerequisites

- `p2c-workspace/02-requirements/prd.md` and `story-map.*` — strongly recommended. Design without validated product scope is wasted motion. If missing, recommend running `/p2c:product` first or capture a quick-pass version with the user.
- **Brand assets** — ask the user up front: do they have a logo, palette, typography, voice/tone, brand book, or existing design system? If yes, ingest them. If no, confirm Enterprise Default Style.

## Active phase

- **Phase 3:** Design — sketch → wireframe → clickable prototype → 5-user usability test → **enterprise mockups (mandatory)** → design system tokens + components → accessibility pass + responsive states.

## Active agents

- **lead-ux-designer** (lead — owns the mockups, tokens, component library, accessibility, brand application, and the handoff brief)
- **product-owner** — golden-path framing, copy tone, content calls
- **lead-developer** — only at handoff: confirms build feasibility, flags responsive/state edge cases, and is responsible for wiring the design tokens into the actual codebase later
- **research-marketing** — only if branding/positioning needs sharpening before mockups

## Entry sequence

1. Read `skills/p2c/references/03-design.md` **and** `skills/p2c/references/visual-standards.md`. Both are required input.
2. Confirm or collect brand assets. Record what's provided in `p2c-workspace/03-design/brand-input.md`.
3. Read PRD and story map if they exist; otherwise capture a quick-and-dirty version with the user before moving on.
4. Offer the visual server (journey map + component checklist views).
5. Walk the design workflow:
   1. **Sketch the flow** (paper / Excalidraw)
   2. **Wireframe** the critical 3–5 screens (low-fi, grayscale, no images)
   3. **Build a clickable prototype** of the golden path (or HTML equivalent)
   4. **Run 5–8 usability tests**, fix anything 2+ users hit
   5. **Generate or import high-fidelity mockups** — see "Mockup deliverables" below — *this step is the hard gate*
   6. **Lock the design system** (tokens + components)
   7. **Accessibility pass** + responsive states + per-screen states (empty / loading / error / success)
6. Get explicit user sign-off on the mockups. Do not mark phase 3 `delivered` without it.
7. At every phase boundary, run the traceability checker and report its output
   as described under "The phase-boundary ritual" in `skills/p2c/SKILL.md`.
   Open findings, staleness and gaps are named in the phase summary every time.
   The checker is advisory — it never blocks a phase from advancing, but a
   phase may not advance without its output being reported.

## Deliverables

All of the below land under `p2c-workspace/03-design/`.

- `brand-input.md` — what brand assets were provided (or "Enterprise Default Style" if none)
- `wireframes/` — Figma link or local exports of the low-fi wireframes
- `prototype.md` — link + golden-path description
- `usability-tests.md` — 5–8 user notes, fixes applied
- **`mockups/`** — **mandatory.** High-fidelity mockups of every key screen. Acceptable formats:
  - Figma file (gold standard) with frame-per-screen and the golden path connected, **or**
  - `mockups/index.html` plus per-screen HTML files using the Enterprise Default Style (or brand) — runnable via the visual server. This is the **default we generate** when no designer is in the loop.
  - PNG / SVG exports are acceptable as a complement, never as the sole deliverable.
- `mockups/coverage.md` — table listing every key screen × every required state (default, empty, loading, error, success, mobile, dark mode if applicable) with checkboxes and links
- `design-tokens.md` — color, type, spacing, radii, shadows
- `components.md` — list of locked components for MVP
- `a11y-checklist.md` — WCAG 2.1 AA pass with evidence
- `states.md` — empty / loading / error / success per screen (this is the state-coverage tracker, may overlap `mockups/coverage.md` and that is fine)

## Sign-off rule

Before declaring phase 3 complete:

- [ ] Mockups exist for every key screen
- [ ] All required states present per screen
- [ ] Brand applied (if provided) or Enterprise Default applied (if not)
- [ ] User has reviewed the mockups and given explicit approval (record date and decision in `status.json` `decisions_log`)

If any box is unchecked, phase 3 stays `in_progress` and the orchestrator does not advance.

## Final output

`p2c-workspace/03-design/SUMMARY.md` with screenshots / links to the high-fidelity flow, design system summary, brand application notes, and a handoff brief for development.
