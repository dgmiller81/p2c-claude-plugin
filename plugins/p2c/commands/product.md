---
description: Product-only scope — discovery, validation, requirements, scope, success metrics. No tech, design, or build work.
argument-hint: [optional brief or context]
---

# /p2c:product — Product Lane Only

The user wants only the **product** scope. Activate the `p2c` skill scoped to phases 1, 2, and 8 (post-launch measurement framework).

## Active phases

- **Phase 1:** Discovery & Validation — JTBD, Lean Canvas, Mom Test interview design, smoke-test landing page brief, go/no-go memo.
- **Phase 2:** Requirements & Scope — story map, 1-page PRD, BRD, RTM, MoSCoW, NFR worksheet, Definition of Done.
- **Phase 8 (framework only):** define the activation event, north star, AARRR funnel, weekly cadence — without building it yet.

## Active agents

- **product-owner** (lead)
- **business-analyst**
- **research-marketing** (for competitive scan + segment definition)

Do **not** dispatch lead-architect, lead-developer, lead-qa-coordinator, or scrum-master in this scope. Note implications for them in the deliverables (e.g., NFR has compliance constraints, story map is ready for sprint planning) so they can pick up cleanly later.

## Entry sequence

1. Read `skills/p2c/references/01-discovery-and-validation.md`, `02-requirements-and-scope.md`, `08-measure-and-iterate.md`.
2. Ingest existing context (`$ARGUMENTS`, README, docs/).
3. Offer the visual server with the discovery / story-map / journey views enabled.
4. Run phases 1, 2, then the phase-8 framework definition.
5. At every phase boundary, run the traceability checker and report its output
   as described under "The phase-boundary ritual" in `skills/p2c/SKILL.md`.
   Open findings, staleness and gaps are named in the phase summary every time.
   The checker is advisory — it never blocks a phase from advancing, but a
   phase may not advance without its output being reported.

## Final output

`p2c-workspace/PRODUCT-SUMMARY.md` linking PRD, BRD, RTM, story map, success metrics framework, and noting what's next (design, architecture, etc.) for whoever picks it up.
