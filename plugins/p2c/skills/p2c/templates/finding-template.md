---
id: {{ID}}
type: finding
title: {{TITLE}}
traces_to: [{{REQ_ID}}]
source_hash: {{{REQ_ID}}: 'aaaaaa'}
history: ['aaaaaa']
raised_by: {{AGENT}}
nature: {{NATURE}}
severity: {{SEVERITY}}
disposition: open
proposed_resolution: {{RESOLUTION}}
status: draft
---

## Evidence

Why the requirement cannot be met as written. Link the ADR, the spike, the
measured numbers. This is the case the product owner rules on.

## Notes

`traces_to` takes exactly one requirement. A conflict *between* two
requirements is filed as two findings that cross-reference each other here.

`history` is the raise log: one quoted 6-character hash per raise, oldest
first, recording the requirement's normative hash at the moment the finding
was filed or re-filed. `len(history)` is the review-iteration count. Quote
every entry — an unquoted `000000` is parsed by YAML as an octal integer and
loses its padding, which silently breaks the `finding-unfounded` check.

`nature` is one of `infeasible`, `cost`, `conflict`, `risk`.
`severity` is one of `blocking`, `material`, `minor`.

`disposition` moves `open` → `accepted` → `resolved`, or closes at
`rejected`. The product owner sets `accepted` and `rejected`; the agent that
raised the finding sets `resolved`, after re-reading the edited requirement
and confirming the change addresses it.
