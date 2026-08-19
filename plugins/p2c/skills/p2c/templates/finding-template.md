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

`source_hash` records the challenged requirement's normative hash as it read
when this finding was filed. The shipped `'aaaaaa'` is a **deliberate
placeholder**. Replace it with that requirement's real normative hash in
**both** `source_hash` and the single `history` entry before this finding
means anything. Leave the placeholder in and two things go wrong at once: the
finding reports as `stale` from birth, because `source_hash` records a value
the requirement never had; and `finding-unfounded` — the check that exists to
catch a finding closed without anything changing — is disabled for this
finding permanently, because it compares the requirement's current hash
against the last `history` entry and `'aaaaaa'` can never match.

Getting the value is not the same here as it is for a screen or a component.
Because this template already supplies a `source_hash` **key** for the
requirement, the `unhashed-link` check will **not** prompt you — it asks only
whether a key is present, never what the value is. Take the hash from the
Staleness table in `traceability/gaps.md` instead: its `recorded → current`
column prints `{{REQ_ID}}: aaaaaa → <the real hash>` for this finding. Never
invent a value.

## Sign-off

When this finding has been ruled on and the ruling confirmed, add:

```yaml
status: approved
signoff: {by: <agent>, date: <YYYY-MM-DD>}
```

`by` is the agent whose call the sign-off attests to: the product owner for
`accepted` or `rejected`, the raiser for `resolved`. `gate` is omitted — a
finding is not gate-scoped.

Do not record the reviewed-against hash here — it would duplicate
`source_hash`, and `trace.py --apply-status` strips `signoff` the moment
`source_hash` goes stale. A present `signoff` therefore already means
"reviewed against the hash currently recorded in this file".

When the challenged requirement changes, this finding is set to
`status: stale` and its `signoff` is removed. Re-working it means: re-read the
amended requirement, write the new hash into `source_hash`, then either set
`disposition: resolved` (leaving `history` alone — the old entry is what
proves the requirement moved) or leave it open and append the new hash to
`history` as the next iteration. Then set `status: in-review` then `approved`
and re-sign. Skipping the `source_hash` update leaves this finding
permanently stale, and `status: stale` gets rewritten onto it at every phase
boundary even after it is resolved.
