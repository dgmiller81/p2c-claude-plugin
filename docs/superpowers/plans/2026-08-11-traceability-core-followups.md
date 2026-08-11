# Traceability Core — deferred follow-ups

Findings raised during Increment 1 that were reviewed, ruled deferrable, and
deliberately not fixed. Recorded here because the SDD ledger is scratch and gets
deleted; these are the real residue.

Nothing here is a correctness defect in shipped behaviour. Each was verified as
either unreachable, mitigated elsewhere, or a coverage gap rather than a bug.

## Worth doing early in Increment 2

**`requirement-template.md` has no traceability guidance.** The screen and
component templates gained a `## Traceability` note and a `source_hash` example
during the final fix wave; the requirement template did not. A business
requirement decomposed into an FR produces a requirement→requirement link, which
now correctly raises `unhashed-link` — but an author copying the template gets no
hint that `traces_to` and `source_hash` belong there. Same failure shape as the
Critical the fix wave closed: the template leads the author into the gap.

**No orphan-artifact check reaches personas or journeys at `handoff`/`build`.**
Screens are checked at `design`, components at `handoff`, stories and tests at
`build`. Personas and journeys are only checked at `design`. Harmless today
because nothing prunes them later, but the asymmetry is unstated.

**`apply_status` leaves the owning journey's `status` untouched** when only one of
its steps is stale. Intentional — steps are synthesized and repair belongs to the
journey — but the journey file itself never records that it needs attention. The
gate still exits 1, so nothing is silently lost.

## Test-coverage gaps (behaviour verified correct by hand)

- No test for an unfilled template dropped into a workspace. Behaviour is a clean
  `SidecarError` → exit 2, but the YAML error points at the first flow-mapping
  token rather than the first placeholder, which could mislead a debugging agent.
- `sidecar.py` parse branches for an empty file and non-dict frontmatter are
  untested; both were hand-traced as correct.
- `SKIP_DIRS` matching is case-sensitive. Fails closed — an unmatched
  `Traceability/` yields exit 2, not a false pass.
- No case-sensitivity case (`"fr-012"`) in the invalid-ID list. Correctly
  rejected; just unasserted.
- `test_rewriting_a_requirement_statement_fails_the_gate` and
  `test_template_workspace_passes_once_the_author_fills_it_in` were green against
  pre-fix source — the fixture and template data changes alone satisfy them. Valid
  forward regression guards, but not red-first evidence.

## Implicit couplings — document or guard if either side changes

- `hashing.HASH_LENGTH = 6` and the hardcoded `{6}` in `schema.HASH_PATTERN` must
  agree. Changing one silently makes every workspace exit 2.
- `apply_status` writes `status: "stale"`, which is legal only because
  `schema.ENUMS["status"]` happens to list it.
- `report._chain_for`'s key set silently omits any artifact type later added to
  `ids.PREFIX_TO_TYPE` — a new type would vanish from the matrix rather than error.
- `schema.MAY_BE_EMPTY` containing `traces_to` is load-bearing: schema errors
  return 2 before gap analysis runs, so removing it regresses `orphan-screen` from
  exit 1 to exit 2. Guarded by `test_orphan_screen_exits_one_not_two`.

## Ruled not-defects (with reasoning, in case someone re-raises them)

- **6-hex-char hash is only 24 bits.** The birthday bound does not apply: each
  hash is compared against the one upstream ID it was recorded for, never against
  a pool. Fixed-pair collision is ~1/16.7M.
- **Set iteration is `PYTHONHASHSEED`-dependent.** Every consumer sorts before
  emission, and `load_workspace` sorts `rglob`, so node insertion order is
  deterministic too. Verified identical output across three seeds.
- **`normative_text` silently falls to the non-requirement branch on a bad
  `type`.** Unreachable via the CLI — schema rejects both a missing and a
  misspelled type and returns 2 before hashing. Documented as a caller contract.
- **`_chain_for` collects transitively.** Correct by construction; an artifact
  shared by two requirements legitimately appears in both chains.
- **`_MOCKUP_DIR` hardcodes `03-design/mockups`.** Correct for the canonical
  workspace layout this increment targets.
