# Status File Template

`status.json` is the single coverage tracker for the p2c run. Below is a **commented reference** — the actual file is JSON without comments.

```jsonc
{
  // Which command kicked off the current scope (e.g., "/p2c:full", "/p2c:tech-scope").
  "current_command": "/p2c:full",

  // The phase you are actively working on (1–8).
  "current_phase": 4,

  // Phase-by-phase coverage. Status is one of:
  //   "pending"      — not started
  //   "in_progress"  — work begun, not yet delivered
  //   "delivered"    — agreed-upon deliverables exist in `files`
  //   "skipped"      — explicit user instruction; record what was skipped and why
  "phases": {
    "1": {
      "status": "delivered",
      "files": [
        "01-discovery/jtbd.md",
        "01-discovery/lean-canvas.md",
        "01-discovery/market-research.md",
        "01-discovery/go-no-go.md"
      ],
      "skipped_items": []
    },
    "2": {
      "status": "delivered",
      "files": [
        "02-requirements/prd.md",
        "02-requirements/brd.md",
        "02-requirements/story-map.json",
        "02-requirements/rtm.md",
        "02-requirements/nfrs.md"
      ],
      "skipped_items": ["service-blueprint (deferred to phase 3)"]
    },
    "3": { "status": "in_progress", "files": ["03-design/wireframes/"], "skipped_items": [] },
    "4": { "status": "pending", "files": [], "skipped_items": [] },
    "5": { "status": "pending", "files": [], "skipped_items": [] },
    "6": { "status": "pending", "files": [], "skipped_items": [] },
    "7": { "status": "pending", "files": [], "skipped_items": [] },
    "8": { "status": "pending", "files": [], "skipped_items": [] }
  },

  // Append-only decision log. Captures any decision the user makes that
  // changes scope, budget, direction, or technology.
  "decisions_log": [
    {
      "date": "2026-05-07",
      "decision": "Confirm Postgres on Supabase for MVP",
      "rationale": "Team familiarity + budget under $100/mo at MVP scale",
      "reverses": null,
      "links": ["04-architecture/adr/ADR-001-database.md"]
    }
  ]
}
```

The orchestrator updates `status.json` after every deliverable lands or every decision is recorded. When the user asks "where are we?", read this file.
