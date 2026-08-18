# p2c — Feasibility Feedback Loop and Traceability Enforcement

**Date:** 2026-08-18
**Status:** Design approved, pending implementation
**Target repo:** `dgmiller81/p2c-claude-plugin`

---

## 1. Problem

The p2c orchestrator runs phases 1–8 as a forward-only pipeline. Every agent-to-agent handoff in `agents/*.md` is written as "hand X to Y." When architecture (phase 4) or development (phase 5) discovers that a requirement cannot be built as written, there is no route back: no agent is instructed to file the finding, no artifact records it, and nothing detects that the requirements and UX artifacts upstream have become inaccurate.

The result is silent drift. Requirements and mockups continue to describe a product that the architecture has already established is not buildable, and the divergence surfaces late — typically during build, at the point where it is most expensive to correct.

The only backward escalation written anywhere in the plugin today is `agents/lead-developer.md:48` (feasibility issues on mockups, developer → UX designer). There is no return path from the architect to UX, to the business analyst, or to the product owner.

## 2. Current state: the engine already exists and is not connected

`skills/p2c/scripts/trace.py` (179 lines) plus `skills/p2c/scripts/tracelib/` (1,243 lines) implement a complete requirements-traceability and staleness system. It is fully written and, as far as the documented workflow is concerned, entirely unused.

### 2.1 What it already does

- **Sidecar artifacts.** Any `.md` under the workspace with YAML frontmatter is a graph node: `id`, `type`, `title`, `status`, plus type-specific fields. IDs are typed and pattern-validated (`ids.py`): `BR|FR|NFR` → requirement, `P` → persona, `J` → journey, `J-NN.n` → journey step, `SCR` → screen, `ARC` → component, `US` → story, `TC` → test.
- **Normative hashing** (`hashing.py`). `normative_hash` is `sha256(normative_text)[:6]`. For a requirement, normative text is `statement` + `acceptance_criteria` only — editing priority, notes, source or version deliberately does not move the hash. For every other type it is `title` + prose body.
- **Staleness cascade** (`staleness.py`). Each artifact records `source_hash: {FR-001: 'a3f9c1'}` — the hash of each upstream requirement as it read when the artifact was authored. `detect()` recomputes upstream hashes, reports direct mismatches as `upstream-changed`, then walks the transitive closure via `graph.downstream()` and reports everything below as `transitive`.
- **Sign-off voiding.** `apply_status()` writes `status: stale` and strips the `signoff` field from every affected artifact. Synthesized journey-step nodes are correctly excluded from writes (`_is_synthesized`), since they have no file of their own.
- **Staged gap checks** (`stages.py`), cumulative across `requirements → design → handoff → build`: `dangling-ref`, `duplicate-step`, `malformed-step`, `undecomposed-br`, `orphan-requirement` (a UI requirement no screen serves), `orphan-artifact` (a screen/component/story/test that traces to nothing — scope creep), `broken-chain` (no component owns this / no test asserts this NFR / no story implements this), `missing-state`, and `unhashed-link`.
- **`unhashed-link` is the anti-opt-out.** Its docstring states the reasoning plainly: staleness detection iterates only what is recorded in `source_hash`, so an absent map means no detection at all, permanently and silently. The check exists so that omission is not a valid escape.
- **Reports.** `traceability/rtm.md`, `traceability/index.json`, `traceability/gaps.md`. Exit codes: `0` clean, `1` gaps or staleness, `2` schema or parse error. The exit-2 paths deliberately overwrite `gaps.md` with a validation-failure report so a reviewer cannot read a previous run's "no gaps found" for a workspace that is currently broken.

Five templates (`requirement-`, `screen-`, `component-`, `persona-`, `journey-template.md`) are already in sidecar format and reference `trace.py` by name.

### 2.2 What is missing

1. **Nothing references the engine.** `SKILL.md`, all eight `agents/*.md`, all nine `commands/*.md`, and all eight `references/*.md` contain zero mentions of `trace.py`, `source_hash`, sidecars, or the stage model. No agent is told to write a sidecar; no orchestrator step runs the checker.
2. **Nothing ever sets `signoff`.** The engine strips it on staleness (`staleness.py:94`) and reads it as truthy (`:46`), but no template writes it, no agent sets it, and no document defines it. The void-on-change half of re-review is built; the grant-on-review half does not exist.
3. **No trigger and no routing for feasibility findings.** `trace.py` detects staleness only *after* somebody edits a requirement. Nothing causes an architect's "this cannot be built" to *become* that edit.
4. **The loader rejects a real p2c workspace.** See §7 — this is a hard blocker, not a nuance.
5. **Two competing state models.** `trace.py:resolve_stage` reads `config.json` → `gates.gate1|gate2|gate3.status == "signed"`, mapping to `design|handoff|build`. `SKILL.md` documents `status.json` with per-phase `status`/`files`/`skipped_items`. Neither file knows about the other.

## 3. Design decisions

**Enforcement posture: advisory.** `trace.py` reports; the orchestrator surfaces; nothing is hard-blocked. This is a deliberate choice. The mitigation that makes it work is §5.5: the report is a mandatory, non-elidable component of the orchestrator's phase-boundary output, not an optional step in a list. Teams wanting hard enforcement already have it for free — `trace.py` exits 1 on gaps, so wiring it into CI requires no change to this design.

**Approach: findings as first-class sidecars, plus the full orchestration wiring.** The wiring is mandatory regardless of approach — the engine is unused because no agent knows it exists, and only rewritten agent contracts and `SKILL.md` fix that. Modelling findings as graph nodes is the increment that makes them machine-visible instead of prose that can be ignored.

## 4. The finding node

### 4.1 Location

New top-level `p2c-workspace/findings/`. Deliberately **not** under `traceability/`, which is in `sidecar.py:SKIP_DIRS` and would never be loaded. Phase-neutral, because findings originate in phases 3, 4, 5 and 6 alike.

### 4.2 Schema

```yaml
---
id: FND-001
type: finding
title: Real-time roster sync cannot meet the 200ms p95 budget
traces_to: [FR-007]                 # exactly one requirement (see §9)
source_hash: {FR-007: '7d2e04'}     # engine field: hash at last review
history: ['a3f9c1', '7d2e04']       # one entry per raise; len() = iteration count
raised_by: lead-architect
nature: infeasible                  # infeasible | cost | conflict | risk
severity: blocking                  # blocking | material | minor  (optional)
disposition: open                   # open | accepted | rejected | resolved
proposed_resolution: relax p95 to 500ms, or drop live sync to 5s polling
status: draft
---

## Evidence

Why it cannot be built as written: the ADR, the spike, the measured numbers.
```

### 4.3 Why `disposition` and not `status`

`schema.py:ENUMS` validates `status` against `draft|in-review|approved|stale|baselined` for **every** node type. A finding carrying `status: open` would fail schema validation outright.

Two options were considered: make the `status` enum type-aware, or give findings a separate disposition field. This design takes the second. The two concepts are orthogonal — `status` is engine-managed freshness, `disposition` is human-managed judgement — and conflating them means a finding that goes stale loses its disposition when `apply_status` overwrites `status`. Keeping them separate also avoids touching validation semantics shared by every other node type.

A finding therefore carries both: `status` follows the standard lifecycle like any other node, and `disposition` records the judgement.

| `disposition` | Meaning | Set by |
|---|---|---|
| `open` | Raised, not yet triaged. | raiser, at filing |
| `accepted` | Triaged and judged valid; requirement edit pending. | product-owner |
| `resolved` | Requirement was changed and the raiser has confirmed the change addresses the finding. | raiser, after re-reading the edited requirement |
| `rejected` | Closed with no requirement change — either the PO accepted the cost, or the finding was withdrawn. | product-owner (cost accepted) or raiser (withdrawn) |

The split matters: the product-owner owns the *judgement* calls (`accepted`, `rejected`), because those are scope decisions. The raiser owns `resolved`, because that is a factual confirmation that the edited requirement is now buildable — a judgement only the party holding the evidence can make. An agent cannot mark its own finding `accepted`, and the PO cannot declare a finding `resolved` on the raiser's behalf.

### 4.4 `history` replaces a separate `raised_against` field

An earlier draft carried both an immutable `raised_against` hash and a mutable `source_hash`. `history` subsumes it: `history[0]` is the original raise, `history[-1]` is the most recent one, and `len(history)` is the review-iteration count that makes "has this been reviewed a second, third time?" an answerable question rather than a judgement call.

`history` entries obey the same quoting rule as `source_hash` values: quoted 6-character lowercase hex. Unquoted YAML scalars such as `000000` parse as octal integers and lose their padding, which silently breaks comparison — `schema.py:HASH_PATTERN` already guards this for `source_hash` and the same guard applies here.

### 4.5 `traces_to` is the correct edge, and the cascade is free

Edges are built as `sc --traces_to--> target`, populating `out[sc] += target` and `inc[target] += sc`; `downstream()` walks `inc` transitively (`graph.py:30-39`). Pointing a finding at `FR-007` therefore makes the finding a *consumer* of `FR-007`. Three consequences follow without new code:

1. **When the requirement is edited, the finding itself goes stale.** The raiser is forced to re-confirm the finding against the new wording. This is the second and third review, and it falls directly out of the existing cascade.
2. `_consumers_of_type` is type-filtered (`stages.py:25-34`), so findings cannot contaminate the screen/component/story/test checks, and `_orphan_artifacts` is never invoked on them.
3. Findings are leaves — nothing traces to a finding — so the transitive walk terminates.

A further benefit: because `_check_unhashed_links` demands a `source_hash` entry for every requirement in `traces_to`, findings are automatically enrolled in staleness detection by a check that already exists. No new enforcement is required.

### 4.6 New checks

**`unresolved-finding`** — any finding whose `disposition` is `open` or `accepted`. Reported at every stage, unconditionally (placed in `_check_requirements_stage`, which `check()` runs for all stages). An open finding is an open question about the requirements regardless of which stage is being validated.

**`finding-unfounded`** — `disposition: resolved` but `normative_hash(target) == history[-1]`, meaning the requirement has not moved since the finding was last raised. This catches an agent closing a finding to clear the gap without anything actually changing. `rejected` is deliberately exempt: closing because the PO accepted the cost is a legitimate close with no requirement edit.

**`undeclared-state`** — see §6.4. A distinct kind from the existing `missing-state`, which means "declared file not found on disk."

## 5. The loop protocol

### 5.1 Raiser, decider and editor are three different parties

| Role | Agent | Responsibility |
|---|---|---|
| Raiser | lead-architect (ph. 4), lead-developer (ph. 5), lead-qa-coordinator (ph. 6), lead-ux-designer (ph. 3) | Writes the `FND-NNN` sidecar. They hold the evidence. |
| Router | orchestrator | Surfaces the finding. Never resolves it, never edits a requirement. |
| Decider | product-owner | Owns scope, therefore owns the `accepted`/`rejected` judgement (§4.3). |
| Editor | business-analyst | Sole writer of requirement sidecars; applies the edit and bumps `version`. |

Separating raiser from decider prevents an agent dissolving a requirement it finds inconvenient. Separating decider from editor gives requirement sidecars a single writer, which `version` integrity and hash stability both depend on.

### 5.2 The four ways a finding closes

1. **Requirement changed** — BA edits `statement` and/or `acceptance_criteria`, bumps `version`; hash moves; cascade fires; `disposition: resolved`.
2. **Requirement stands** — PO accepts the cost or risk; the architecture absorbs it; `disposition: rejected`, with an ADR recording what was absorbed. No hash change, which is why `rejected` is exempt from `finding-unfounded`.
3. **Deferred** — `priority: wont`. This does *not* fire the cascade, because priority is not normative. See §9 for the consequence.
4. **Withdrawn** — the raiser was wrong; `disposition: rejected` with a note.

### 5.3 A worked cycle

```
FND-001 written, disposition: open, history: ['a3f9c1']
  -> orchestrator surfaces it at the phase-4 boundary
  -> PO decides: relax the budget to 500ms
  -> BA edits FR-007, version 1 -> 2, hash a3f9c1 -> 7d2e04
  -> trace.py --apply-status cascades:
        SCR-004  status: stale, signoff stripped   (screen)
        ARC-002  status: stale, signoff stripped   (component)
        US-013   status: stale, signoff stripped   (story)
        TC-05    status: stale, signoff stripped   (test)
        FND-001  status: stale                     (the finding itself)
  -> each owning agent re-works its artifact, records source_hash 7d2e04,
     sets status: in-review then approved, re-signs
  -> raiser re-reads FR-007 at 7d2e04:
        still infeasible?  no  -> disposition: resolved
                           yes -> stays open, history gains '7d2e04'
                                  == ITERATION 2
```

Iteration 2 is not special-cased. It is the same machinery running again, which is why it also supports a third and fourth pass without additional code.

### 5.4 Convergence rule

At `len(history) >= 3` the orchestrator must escalate to the user as a decision-forcing item, in these terms: *this requirement and this architecture have failed to reconcile across three revisions; the next move is a scope change or a constraint change, not another cycle.*

Three is a judgement call. It is a single constant so it can be tuned.

### 5.5 The phase-boundary ritual

`commands/full.md` already mandates a stop-and-ask at every phase boundary. The protocol attaches to that existing hook. At each boundary the orchestrator **must**:

1. Run `python skills/p2c/scripts/trace.py --workspace p2c-workspace --stage <stage> --apply-status`
2. Include in the phase summary — not optional, not summarised away:
   - open-finding count, with IDs and the requirement each challenges
   - every staleness entry, naming which artifacts lost sign-off
   - the gap list grouped by kind
   - any finding at `len(history) >= 3`, flagged per §5.4
3. Never write `status: delivered` into `status.json` while the checker's most recent run reported any gaps or staleness — exit code 1, or a Gaps/Staleness table in `traceability/gaps.md` with rows in it — without naming those gaps in the summary. Note `gaps.md` always exists and is never byte-empty: a clean run writes "No gaps found." into it, so the condition is the exit code or the table contents, never file size. Advancing is permitted — this is advisory — but advancing *quietly* is not.

Phase-to-stage mapping: phase 2 → `requirements`, phase 3 → `design`, phase 4 → `handoff`, phase 5 and later → `build`.

Point 3 is what makes advisory mode viable. "Report and let the human decide" only holds if the report is structurally impossible to skip, so it is specified as a hard constraint on the orchestrator's *output* rather than as a step in a procedure it might drift past.

## 6. Agent contracts

### 6.1 `signoff`

```yaml
status: approved
signoff: {by: lead-ux-designer, date: 2026-08-10, gate: gate2}
```

This is the shape already used by `tests/fixtures/stale-hash/`, introduced by the commit that added sign-off voiding. `by` and `date` are required; `gate` is optional and ties the sign-off to the gate model in `config.json`. The hash is deliberately omitted. It would duplicate `source_hash`, and because sign-off is stripped the moment `source_hash` goes stale, a present `signoff` already means "reviewed against the currently-recorded hashes."

Lifecycle: `draft → in-review → approved` + `signoff` → *(upstream edit)* → `stale`, signoff stripped → `in-review` → `approved` + new `signoff` + updated `source_hash`.

`baselined` exists in the enum but nothing in the engine reads it. This design does not assign it behaviour; it is reserved for gate-signed.

### 6.2 Sidecar ownership

| Agent | Owns | Notes |
|---|---|---|
| business-analyst | `BR-`, `FR-`, `NFR-` | **Sole writer of requirement sidecars.** Bumps `version` on every normative edit. |
| product-owner | none | Decides disposition and priority; the BA applies the edit. |
| lead-ux-designer | `P-`, `J-`, `SCR-` | Research-marketing feeds persona content; UX writes the sidecar. |
| lead-architect | `ARC-` | |
| scrum-master | `US-` | |
| lead-qa-coordinator | `TC-` | |
| lead-developer | none new | Consumes ARC/SCR/US; raises findings. |
| research-marketing | none | Prose only. |

The product-owner row is the largest departure from the plugin as it stands. Today the PO writes `prd.md` and the BA writes `rtm.md` independently, and both may describe the same requirement. Under this design the PO still owns the PRD as prose and still owns every decision, but the machine-readable requirement has exactly one writer. Two writers on a hashed artifact produces racing `version` bumps and hashes nobody can trust.

### 6.3 Return contract, added to all eight agents

Every agent's "Output to orchestrator" section gains four lines:

```
- Sidecars written/updated:  [FR-007 v2, SCR-004]
- Findings raised:           [FND-001]   (or: none)
- Stale artifacts repaired:  [SCR-004 -> source_hash 7d2e04]
- Left stale, and why:       [ARC-002 - blocked on FND-001]
```

The final line prevents staleness being quietly abandoned mid-cycle, which is the main failure mode available under advisory enforcement.

Raiser agents additionally receive the finding-filing protocol (§5). The BA receives the sole-writer rule and the version-bump duty. Every artifact-owning agent receives the re-baseline duty: *if your artifact is `stale`, re-read the changed upstream, re-work the artifact, record the new `source_hash`, re-sign.*

### 6.4 The mockup gate becomes machine-checkable

`schema.py:REQUIRED_BY_TYPE` already requires `states` on every screen, and `_check_design_stage` (`stages.py:166-190`) resolves each declared state file against `03-design/mockups/`, reporting `missing-state` when it is absent. It also rejects absolute paths and `..` traversal before touching the filesystem (`_is_unsafe_state_path`).

Absolute Rule 3 of the plugin — mockups with working empty/loading/error/success states for every key screen (Rule 2 requires only that mockups exist) — currently exists only as prose in `references/visual-standards.md`, enforced by an agent remembering to care. With screen sidecars it becomes:

```yaml
states: {default: SCR-004.html, empty: SCR-004-empty.html,
         loading: SCR-004-loading.html, error: SCR-004-error.html,
         success: SCR-004-success.html}
```

Add `REQUIRED_STATES = {"default", "empty", "loading", "error", "success"}` and a new `undeclared-state` gap for any screen not declaring all five. Advisory, consistent with §3 — some screens legitimately have no empty state, so this reports rather than blocks.

## 7. Engine changes, module by module

### `tracelib/sidecar.py`

In `load_workspace`, read the first line of each candidate file and skip it if it is not `---`. A file with no opening delimiter is prose, not a malformed sidecar. `parse_sidecar` itself stays strict and unchanged, so a file that *has* frontmatter but malformed YAML remains an exit-2 condition and direct callers keep the current contract.

This is the §2.2 blocker. `load_workspace` currently parses every `.md` outside `SKIP_DIRS`, and `parse_sidecar` raises on any file lacking frontmatter. A workspace built by the documented flow is almost entirely prose — `prd.md`, `jtbd.md`, `lean-canvas.md`, `go-no-go.md`, `adr/ADR-001-*.md`, `runbook.md` — so `trace.py` exits 2 on the first file it reaches. Nothing else in this design can work until this is fixed.

Residual risk, accepted: a sidecar that loses its entire frontmatter block becomes invisible to the graph rather than erroring. It is still detected indirectly — the artifact vanishes and its requirement reports as `orphan-requirement`.

### `tracelib/ids.py`

Add `"FND": "finding"` to `PREFIX_TO_TYPE` and `FND` to the `_THREE_DIGIT` alternation.

### `tracelib/schema.py`

- `REQUIRED_BY_TYPE["finding"] = ("traces_to", "history", "raised_by", "nature", "disposition")`
- `ENUMS["nature"] = ("infeasible", "cost", "conflict", "risk")`
- `ENUMS["disposition"] = ("open", "accepted", "rejected", "resolved")`
- `ENUMS["severity"] = ("blocking", "material", "minor")`
- New `_history_errors`: `history` must be a non-empty list of quoted 6-character lowercase hex strings, reusing `HASH_PATTERN` and the existing unquoted-octal error message.
- New rule: a finding's `traces_to` must contain exactly one entry.
- Optional `signoff` validation: when present, must be a mapping carrying `by` and `date` — the pair named in section 6.1 and used by `tests/fixtures/stale-hash/`. (`at` was a typo in an earlier draft of this section.)

### `tracelib/graph.py`

No change. `traces_to` is already in `LINK_FIELDS`, so findings join the graph as consumers automatically, and `by_type("finding")` works as-is.

### `tracelib/stages.py`

- New `_check_findings(graph)` emitting `unresolved-finding` and `finding-unfounded`; called from the unconditional block in `check()`.
- `REQUIRED_STATES` and the `undeclared-state` gap in `_check_design_stage`.

### `tracelib/report.py`

Render an open-findings table in `rtm.md` and `gaps.md`, carrying the requirement challenged, `nature`, `severity`, `disposition`, and iteration count `len(history)`, with rows at `len(history) >= 3` flagged for escalation. Exact column layout is implementation detail and should follow the existing `_hash_transition_cell` conventions.

### `scripts/trace.py`

No change required. `resolve_stage` and the CLI surface are already sufficient; the orchestrator passes `--stage` explicitly (§8).

## 8. State model reconciliation

`config.json` and `status.json` both survive; neither is retired.

- `status.json` remains the orchestrator's phase tracker, exactly as documented in `SKILL.md`.
- `config.json` gains the gate block that `resolve_stage` already expects: `{"gates": {"gate1": {"status": "signed"}, ...}}`, written by the orchestrator when the user signs a gate. `gate1 → design`, `gate2 → handoff`, `gate3 → build`.
- The orchestrator **always passes `--stage` explicitly** rather than relying on gate inference. `resolve_stage` returns the stage of the *highest signed* gate, which is ambiguous at a boundary — after signing gate1 the resolved stage is `design`, not the `handoff` work that follows it. Passing `--stage` removes the ambiguity without changing existing behaviour for other callers.

## 9. Known limitations, accepted deliberately

1. **Deferral does not cascade.** Setting `priority: wont` does not move the hash, because priority is not normative. This is correct — deferring a requirement does not invalidate a screen already designed for it — but it leaves live downstream artifacts serving an out-of-scope requirement, and nothing reports that. A `deferred-with-live-consumers` check is the obvious follow-up; out of scope for v1.
2. **A finding targets exactly one requirement.** A genuine conflict *between* two requirements must be filed as two findings that cross-reference each other in prose, or filed against whichever one should change. Multi-target findings would make `history` and `finding-unfounded` materially more complex for a case that is rare in practice.
3. **Advisory only.** Nothing blocks. Drift is detected and surfaced, not prevented. `trace.py` exit code 1 is available to any team that wants CI enforcement.
4. **Prose-skip residual risk.** Documented in §7 under `sidecar.py`.
5. **`baselined` remains unused.** Reserved, not defined.

## 10. Rollout

The change is additive and inert until agents begin writing sidecars. An existing workspace containing only prose produces zero nodes, zero gaps and exit 0 once the §7 `sidecar.py` fix lands. Adoption can therefore be incremental: requirement sidecars first (enabling `undecomposed-br` and the hash baseline), then screens (enabling the mockup-state checks), then components, stories and tests.

## 11. Testing

The installed plugin cache ships no test suite; the upstream repo's test setup was not verifiable from the cache and should be confirmed before implementation. Tests this design requires:

- **`sidecar.py`**: a prose `.md` is skipped; a file with an opening `---` and malformed YAML still raises; a file with frontmatter but no closing delimiter still raises.
- **`ids.py`**: `FND-001` resolves to `finding`; `FND-1` and `FND-0001` are invalid.
- **`schema.py`**: each required finding field missing is an error; unquoted `history` entries produce the octal-padding error; a two-target `traces_to` on a finding is an error; a valid finding validates clean.
- **`stages.py`**: `unresolved-finding` fires for `open` and `accepted` and not for `resolved`/`rejected`; `finding-unfounded` fires for `resolved` with an unmoved hash and not for `rejected`; `undeclared-state` fires for a screen declaring four of the five canonical states.
- **`staleness.py` integration**: editing a requirement's `statement` marks the finding that traces to it stale and strips its sign-off, alongside the screen, component, story and test.
- **End-to-end**: a fixture workspace exercising the full §5.3 cycle, asserting the artifact set that goes stale and the sign-off fields that are stripped.

## 12. Files changed

| File | Change |
|---|---|
| `skills/p2c/SKILL.md` | Workspace layout (`findings/`, `traceability/`), phase-boundary ritual, sidecar ownership in the dispatch table |
| `agents/business-analyst.md` | Sole-writer rule, version bumps, re-baseline duty, return contract |
| `agents/product-owner.md` | Decider role on findings, no longer writes requirement sidecars, return contract |
| `agents/lead-architect.md` | Finding-filing protocol, `ARC-` ownership, return contract |
| `agents/lead-ux-designer.md` | `P-`/`J-`/`SCR-` ownership, `states` declaration, finding-filing, return contract |
| `agents/lead-developer.md` | Finding-filing protocol, return contract |
| `agents/lead-qa-coordinator.md` | `TC-` ownership, finding-filing, return contract |
| `agents/scrum-master.md` | `US-` ownership, return contract |
| `agents/research-marketing.md` | Return contract only |
| `commands/*.md` | Reference the phase-boundary ritual at each stop condition |
| `templates/finding-template.md` | New |
| `templates/{requirement,screen,component,persona,journey}-template.md` | Add `signoff`, add `history` where applicable |
| `references/visual-standards.md` | Point the states rule at the `undeclared-state` check |
| `skills/p2c/scripts/tracelib/{sidecar,ids,schema,stages,report}.py` | Per §7 |
