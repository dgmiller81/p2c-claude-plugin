---
id: {{ID}}
type: journey
title: {{TITLE}}
persona: {{PERSONA_ID}}
status: draft
steps:
  - id: {{STEP_ID}}
    label: {{STEP_LABEL}}
    screen: {{SCREEN_ID}}
---

## Scenario

The trigger and the outcome that closes the journey.

## Step detail

For each step: what the persona does, what they think, what they feel, and
which touchpoint they use.

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
