# The Essential Stack for Requirements & Scope

Same logic as discovery — strip away the academic stuff, keep what actually ships product.

## The "Best of" Shortlist
- **Job Stories** — richer than user stories, carries the "why" forward from discovery
- **Story Mapping** — the single best tool for seeing scope and finding the MVP slice
- **1-page PRD** — forces clarity without becoming a doorstop
- **MoSCoW** — simplest prioritization that survives contact with reality
- **NFR worksheet** — the discipline that prevents 2am production fires
- **Definition of Done** — the agreement that prevents "is it shipped?" debates

Everything else is optional.

## How to Structure the Process

### Phase 1: Translate Discovery → Outcomes (Days 1–2)
- Convert validated JTBDs into **2–4 desired outcomes** (measurable user changes, not features)
- For each outcome, write a **success metric** (e.g., "user completes first task in <5 min")
- Identify the **primary user** and **primary job** for the MVP — resist adding more

### Phase 2: Map the Story (Days 3–5)
- Run a **Story Mapping** session (Miro or FigJam)
  - Horizontal axis: user's journey, left to right (the "backbone")
  - Vertical axis: depth of features under each step
- Draw a horizontal line — everything above = MVP, everything below = later
- This single artifact replaces 80% of traditional spec docs

### Phase 3: Write the Stories (Week 2)
- Convert each MVP card into a **Job Story**: *"When [situation], I want to [motivation], so I can [outcome]."*
- Add **acceptance criteria** (Given/When/Then format works well)
- Apply **INVEST** as a quality check — split anything that fails
- Keep stories small enough to ship in <3 days each

### Phase 4: Lock the Non-Functionals (Week 2)
- Fill an **NFR worksheet** with measurable targets:
  - Performance (page load, API p95)
  - Reliability (uptime SLO)
  - Security (auth model, data classification, threat model)
  - Accessibility (WCAG 2.1 AA baseline)
  - Compliance (GDPR, HIPAA, SOC2 — whatever applies)
- These are requirements, not nice-to-haves — treat them like stories

### Phase 5: Prioritize & Commit (Week 2)
- Apply **MoSCoW** to the MVP cards:
  - **Must** — MVP fails without it
  - **Should** — important but deferrable
  - **Could** — only if time allows
  - **Won't (this round)** — explicit out-of-scope list
- Write the **1-page PRD** (template below)
- Agree on **Definition of Done** as a team

### Phase 6: Sanity Check (Day ~14)
- Walk the story map end-to-end — does the MVP slice actually deliver the core job?
- Test each story against: *"If we cut this, does the job still get done?"*
- If >70% of stories are "Must," your MVP is too big — cut again

## The 1-Page PRD Template
```
Problem:        [the validated pain — link to discovery memo]
Primary user:   [one persona, not three]
Job-to-be-done: [JTBD statement]
Outcome:        [measurable user change]
Success metric: [number + timeframe]
MVP scope:      [3–7 bullets, max]
Out of scope:   [explicit "won't do" list]
NFR targets:    [link to worksheet]
Risks:          [top 3, with mitigations]
```

If it doesn't fit on one page, you don't understand it well enough yet.

## The Minimum Viable Toolset
- **Miro or FigJam** — story mapping, journey maps, workshops
- **Linear or GitHub Projects** — backlog, stories, sprints (Linear is faster for small teams)
- **Notion or Confluence** — PRDs, NFR worksheets, Definition of Done
- **Excalidraw** — quick architecture and flow sketches inside docs
- **Loom** — async walkthrough of the story map for stakeholders

Five tools. One artifact each. No tool sprawl.

## The Mental Model
Requirements work isn't about documenting everything — it's about **making the smallest set of decisions that lets the team move without ambiguity**. The shortlist above is built around three jobs:

1. **See the whole** (story map)
2. **Cut to the core** (MoSCoW + MVP line)
3. **Lock the contract** (PRD + DoD + NFRs)

Skip any of the three and you'll either over-build, under-build, or ship something that breaks in production.
