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

## Stop conditions

- After every phase, summarize deliverables, update `status.json`, and ask the user whether to proceed.
- Do not silently cross phase boundaries.
- If the user pauses, ensure `status.json` reflects exactly where to resume.

## Final output

When all 8 phases are delivered (or explicitly skipped), produce a final program summary at `p2c-workspace/PROGRAM-SUMMARY.md` with:
- Links to every deliverable
- Decisions log
- Sprint plan + cost estimate
- Recommended next 90 days
