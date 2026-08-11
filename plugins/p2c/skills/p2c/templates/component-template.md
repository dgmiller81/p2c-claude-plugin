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
