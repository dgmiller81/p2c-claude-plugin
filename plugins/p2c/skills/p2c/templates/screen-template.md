---
id: {{ID}}
type: screen
title: {{TITLE}}
traces_to: [{{REQ_ID}}]
personas: [{{PERSONA_ID}}]
journey_steps: [{{STEP_ID}}]
mockup: {{ID}}.html
states:
  default: {{ID}}.html
  empty: {{ID}}-empty.html
  loading: {{ID}}-loading.html
  error: {{ID}}-error.html
  success: {{ID}}-success.html
terminal: false
source_hash: {{{REQ_ID}}: 'aaaaaa'}
status: draft
---

## Purpose

What this screen is for, in one sentence.

## Primary action

The single thing the persona came here to do.

## Secondary actions

Everything else available, and when it appears.

## States

What each declared state shows and how the user leaves it.

## Open questions

Anything a developer would otherwise have to guess.

## Traceability

`source_hash` records the hash of each upstream requirement as it read when this
screen was built. **Every requirement in `traces_to` must have an entry here.**
A missing entry is not "no staleness" — it is *no staleness detection*, forever:
`trace.py` compares only what is recorded, so an unrecorded requirement can be
rewritten from top to bottom and this screen will still report `ok`. `trace.py`
reports a missing entry as an `unhashed-link` gap and fails the gate.

The shipped placeholder `'aaaaaa'` is **deliberately wrong**. Replace it with the
requirement's current hash, which `trace.py` prints for you: the `unhashed-link`
gap says `current hash is <value>`, and for an already-recorded requirement the
gaps report's Staleness table prints `recorded → current`. Never invent a value.

Values MUST be quoted:

    source_hash: {FR-001: 'a3f9c1'}

Unquoted values that are all digits with a leading zero are parsed by YAML as
numbers and lose their padding, which reports this screen as stale when nothing
has changed.
