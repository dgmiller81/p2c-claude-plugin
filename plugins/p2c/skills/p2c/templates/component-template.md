---
id: {{ID}}
type: component
title: {{TITLE}}
traces_to: [{{REQ_ID}}]
source_hash: {{{REQ_ID}}: 'aaaaaa'}
status: draft
---

## Responsibility

What this component owns, and what it explicitly does not.

## Interface

Inputs, outputs, and the contract consumers depend on.

## Dependencies

What it calls and what calls it.

## Traceability

`source_hash` needs one quoted entry per requirement in `traces_to` — a missing
entry means this component is never checked for staleness, so the requirement
can be rewritten underneath it without anyone noticing. `trace.py` reports the
omission as an `unhashed-link` gap. The shipped `'aaaaaa'` is deliberately
wrong; replace it with the `current hash is <value>` that gap prints.

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
