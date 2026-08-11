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
terminal: false
source_hash: {}
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
screen was built. Values MUST be quoted:

    source_hash: {FR-001: 'a3f9c1'}

Unquoted values that are all digits with a leading zero are parsed by YAML as
numbers and lose their padding, which reports this screen as stale when nothing
has changed. Run `trace.py` to see the current hash for each requirement — the
gaps report prints `recorded → current` for every stale artifact.
