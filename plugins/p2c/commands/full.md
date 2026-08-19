---
description: Full Product-to-Customer orchestration. Walk an idea through phases 1–8 end-to-end with the full agent team, producing every deliverable from JTBD through post-launch growth experiments.
argument-hint: [optional context — pasted brief, link to existing docs, or "use existing workspace"]
---

# /p2c:full — Full Orchestration

The user has invoked the **full p2c flow**. Activate the `p2c` skill and run all eight phases sequentially:

1. Discovery & Validation
2. Requirements & Scope
3. Design
4. Technical Architecture
5. Build (MVP)
6. Test & Harden
7. Launch
8. Measure & Iterate

## Entry sequence

1. Confirm or create `p2c-workspace/` in CWD.
2. Read `skills/p2c/SKILL.md` (loaded already once the skill triggers) and the relevant phase references.
3. Ingest existing context:
   - Any text the user passed as `$ARGUMENTS`
   - `README.md`, `CLAUDE.md`, `docs/**`, `package.json`, `pyproject.toml` if present
   - Existing files in `p2c-workspace/` if resuming
4. Briefly summarize what you found and propose where to start (resume vs. start fresh).
5. Offer to start the visual server (`scripts/start_visual_server.py`).
6. Begin Phase 1 with the **product-owner** + **business-analyst** + **research-marketing** agents.
7. At Phase 3, dispatch the **lead-ux-designer** as the lead — they own the mockups, tokens, components, accessibility, and brand application. The orchestrator does not advance to Phase 4 until the UX designer signs off and the user has approved the mockups.

## Absolute rules

Inherited from `SKILL.md` and `references/visual-standards.md` — apply across the whole run:

1. **Every section of every phase must be completed** unless the user explicitly skips an item with a recorded reason in `status.json`. Silent gaps are a process failure.
2. **Mockups are mandatory at phase 3.** Do not advance to phase 4 (architecture) without enterprise-grade mockups for every MVP screen on file. Match the user's brand if provided, otherwise apply the Enterprise Default Style.

## Stop conditions

- After every phase, summarize deliverables, update `status.json`, and ask the user whether to proceed.
- Do not silently cross phase boundaries.
- **Do not advance past phase 3 without mockups.** This is a hard gate.
- If the user pauses, ensure `status.json` reflects exactly where to resume.
- At every phase boundary, run the traceability checker and report its output
  as described under "The phase-boundary ritual" in `skills/p2c/SKILL.md`.
  Open findings, staleness and gaps are named in the phase summary every time.
  The checker is advisory — it never blocks a phase from advancing, but a
  phase may not advance without its output being reported.

## Final output

When all 8 phases are delivered (or explicitly skipped), produce a final program summary at `p2c-workspace/PROGRAM-SUMMARY.md` with:
- Links to every deliverable
- Decisions log
- Sprint plan + cost estimate
- Recommended next 90 days
