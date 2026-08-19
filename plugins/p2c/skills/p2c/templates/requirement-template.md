---
id: {{ID}}
type: requirement
kind: {{KIND}}
surface: {{SURFACE}}
title: {{TITLE}}
statement: {{STATEMENT}}
acceptance_criteria:
  - {{CRITERION}}
source: {type: {{SOURCE_TYPE}}, ref: {{SOURCE_REF}}}
priority: {{PRIORITY}}
version: 1
status: draft
---

## Context

Why this requirement exists and what happens without it.

## Notes

Open questions, constraints, and links. Nothing here affects the hash —
only `statement` and `acceptance_criteria` are normative.

## Sign-off

When this artifact has been reviewed and approved, add:

```yaml
status: approved
signoff: {by: <agent>, date: <YYYY-MM-DD>, gate: <gate1|gate2|gate3>}
```

Do not record the reviewed-against hash here — it would duplicate
`source_hash`, and `trace.py --apply-status` strips `signoff` the moment
`source_hash` goes stale. A present `signoff` therefore already means
"reviewed against the hashes currently recorded in this file".

When an upstream requirement changes, this artifact is set to `status: stale`
and its `signoff` is removed. Re-working it means: re-read the changed
requirement, update this artifact, write the new `source_hash`, set
`status: in-review` then `approved`, and re-sign.
