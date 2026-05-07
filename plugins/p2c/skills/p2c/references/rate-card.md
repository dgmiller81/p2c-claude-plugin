# Rate Card (machine-readable + narrative)

This is the **single source of truth** for all p2c cost estimates. The `scripts/estimate_cost.py` script reads the JSON block below; humans read the table below that.

## Machine-readable rate card

```json
{
  "currency": "USD",
  "ai_assist_factor": 0.80,
  "rates": [
    {"role": "Scrum Master",         "key": "scrum_master",      "standard_hr": 78, "ai_assisted_hr": 62.40},
    {"role": "Technical Lead",       "key": "tech_lead",         "standard_hr": 91, "ai_assisted_hr": 72.80},
    {"role": "Business Analyst",     "key": "business_analyst",  "standard_hr": 72, "ai_assisted_hr": 57.60},
    {"role": "Full Stack Engineer",  "key": "full_stack",        "standard_hr": 82, "ai_assisted_hr": 65.60},
    {"role": "AI/ML Engineer",       "key": "ai_ml",             "standard_hr": 83, "ai_assisted_hr": 66.40},
    {"role": "Data Engineer",        "key": "data_engineer",     "standard_hr": 81, "ai_assisted_hr": 64.80},
    {"role": "QA Engineer",          "key": "qa_engineer",       "standard_hr": 68, "ai_assisted_hr": 54.40},
    {"role": "Backend Engineer",     "key": "backend",           "standard_hr": 73, "ai_assisted_hr": 58.40},
    {"role": "DevOps Engineer",      "key": "devops",            "standard_hr": 77, "ai_assisted_hr": 61.60}
  ]
}
```

## Human-readable rate card

| Role | Standard $/hr | AI-assisted $/hr |
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

## Conventions

- **AI-assist factor** is applied as `standard × 0.80 = ai_assisted` (a 20% effective-rate reduction reflecting AI productivity uplift).
- **Hours assume focused engineering time** — not calendar hours. Use the focus factor (default 0.7) when converting capacity.
- **All cost outputs MUST show both standard and AI-assisted totals** so the user can compare what an AI-assisted plan costs vs. a baseline plan.
- Update this file **only** when the user provides new rates. The script reads from here; do not duplicate rates elsewhere.
