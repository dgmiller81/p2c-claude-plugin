# p2c Feasibility Feedback Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Connect the existing `trace.py` traceability engine to the p2c orchestrator, and add a finding artifact so architecture and development feasibility problems force requirements and UX artifacts to be revisited rather than going stale.

**Architecture:** Findings become first-class sidecar nodes (`FND-NNN`) that `traces_to` the requirement they challenge, making them consumers in the existing graph — so editing the requirement automatically marks the finding stale and forces re-confirmation. Enforcement is advisory: `trace.py` reports, the orchestrator surfaces the report as a mandatory part of every phase-boundary summary, nothing hard-blocks.

**Tech Stack:** Python 3.12, PyYAML, pytest. No new runtime dependencies.

**Spec:** `docs/superpowers/specs/2026-08-18-p2c-traceability-feedback-loop-design.md`

## Global Constraints

- **Advisory only.** No change may cause the orchestrator to refuse to advance a phase. New gap kinds are reported, never blocking. `trace.py` keeps its exit codes (`0` clean, `1` gaps or staleness, `2` schema or parse error).
- **Hash format:** quoted 6-character lowercase hex, matching `schema.py:HASH_PATTERN` (`^[0-9a-f]{6}$`). Unquoted YAML scalars such as `000000` parse as octal integers and lose padding — every new hash-bearing field must reject them with that explanation.
- **A finding traces to exactly one requirement.**
- **No new runtime dependencies.** PyYAML only.
- **Repo layout:** the plugin lives under `plugins/p2c/`. Engine code is at `plugins/p2c/skills/p2c/scripts/`. Tests live at repo-root `tests/`, governed by `pytest.ini` (`testpaths = tests`).
- **Test command, from the repo root:** `conda run -n 312 python -m pytest tests/ -q`
- **Baseline:** 145 tests pass on `main` before this plan starts. The suite must be green at the end of every task — never leave a task with a red suite for a later task to fix.
- **House test conventions, follow them:** `tests/conftest.py` already puts the scripts dir on `sys.path` and exposes a `fixtures_root` fixture. Stage tests use on-disk fixture workspaces under `tests/fixtures/<name>/` via the `gaps_for(fixtures_root, name, stage)` helper in `tests/test_stages.py`. Add tests to the existing per-module file (`test_sidecar.py`, `test_ids.py`, `test_schema.py`, `test_stages.py`, `test_report.py`) rather than creating parallel files.
- Existing behaviour must not regress. `parse_sidecar` stays strict. `graph.py`, `hashing.py`, `staleness.py` and `errors.py` are not modified by this plan.

---

## File Structure

**New:**
- `tests/fixtures/finding-open/` — clean workspace + an open finding
- `tests/fixtures/finding-unfounded/` — clean workspace + a finding resolved against an unmoved requirement
- `tests/fixtures/finding-resolved/` — clean workspace + a legitimately resolved finding
- `plugins/p2c/skills/p2c/templates/finding-template.md`

**Modified:**
- `plugins/p2c/skills/p2c/scripts/tracelib/sidecar.py` — prose skip
- `plugins/p2c/skills/p2c/scripts/tracelib/ids.py` — `FND` prefix
- `plugins/p2c/skills/p2c/scripts/tracelib/schema.py` — finding schema, `history`, `signoff`
- `plugins/p2c/skills/p2c/scripts/tracelib/stages.py` — three new checks
- `plugins/p2c/skills/p2c/scripts/tracelib/report.py` — findings table, findings in index
- `plugins/p2c/skills/p2c/templates/{requirement,screen,component,persona,journey}-template.md`
- `plugins/p2c/skills/p2c/SKILL.md`
- `plugins/p2c/agents/*.md` (all eight)
- `plugins/p2c/commands/*.md` (eight; `help.md` excluded)
- `plugins/p2c/skills/p2c/references/visual-standards.md`
- `tests/fixtures/clean/03-design/mockups/SCR-004.md` + four new mockup HTML files
- `tests/{test_sidecar,test_ids,test_schema,test_stages,test_report,test_templates}.py`

**Unchanged:** `graph.py`, `hashing.py`, `staleness.py`, `errors.py`, `trace.py`.

---

### Task 1: Skip prose files in the loader

`load_workspace` parses every `.md` outside `SKIP_DIRS`, and `parse_sidecar` raises on any file lacking frontmatter — so `trace.py` exits 2 on the first prose file (`prd.md`, `jtbd.md`, an ADR) in a real p2c workspace. Nothing else in this plan works until this is fixed.

**Files:**
- Modify: `plugins/p2c/skills/p2c/scripts/tracelib/sidecar.py:63-71`
- Test: `tests/test_sidecar.py` (append)

**Interfaces:**
- Consumes: nothing
- Produces: `tracelib.sidecar._has_frontmatter(path: Path) -> bool`. `load_workspace(root: Path) -> list[Sidecar]` keeps its signature but now skips prose.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_sidecar.py`:

```python
def test_prose_file_is_skipped_not_an_error(tmp_path):
    (tmp_path / "prd.md").write_text(
        "# PRD\n\nProblem: dispatchers cannot resolve exceptions.\n",
        encoding="utf-8",
    )
    (tmp_path / "FR-001.md").write_text(
        "---\n"
        "id: FR-001\n"
        "type: requirement\n"
        "kind: functional\n"
        "surface: ui\n"
        "title: Roster sync\n"
        "statement: The roster syncs across devices.\n"
        "acceptance_criteria:\n"
        "  - Sync completes within the budget.\n"
        "priority: must\n"
        "status: draft\n"
        "---\nbody\n",
        encoding="utf-8",
    )
    assert [sc.id for sc in load_workspace(tmp_path)] == ["FR-001"]


def test_malformed_yaml_still_raises(tmp_path):
    (tmp_path / "bad.md").write_text(
        "---\nid: FR-002\n  bad: [unclosed\n---\nbody\n", encoding="utf-8"
    )
    with pytest.raises(SidecarError):
        load_workspace(tmp_path)


def test_unterminated_frontmatter_still_raises(tmp_path):
    (tmp_path / "bad.md").write_text(
        "---\nid: FR-003\ntype: requirement\n", encoding="utf-8"
    )
    with pytest.raises(SidecarError):
        load_workspace(tmp_path)
```

Check the imports at the top of `tests/test_sidecar.py` — if `pytest`, `SidecarError` or `load_workspace` are not already imported there, add them.

- [ ] **Step 2: Run tests to verify the first one fails**

```bash
conda run -n 312 python -m pytest tests/test_sidecar.py -q
```
Expected: `test_prose_file_is_skipped_not_an_error` FAILS with `SidecarError: ...prd.md: missing YAML frontmatter opening delimiter`. The other two PASS already — they are regression guards.

- [ ] **Step 3: Add the frontmatter probe**

In `plugins/p2c/skills/p2c/scripts/tracelib/sidecar.py`, add above `load_workspace`:

```python
def _has_frontmatter(path: Path) -> bool:
    """True if the file opens with a YAML frontmatter delimiter.

    A p2c workspace holds prose (prd.md, jtbd.md, ADRs, runbooks) alongside
    sidecars. Prose is not a malformed sidecar, and letting it raise takes
    the whole run down with an exit-2 before a single check can run. A file
    that *does* open with the delimiter is still parsed strictly, so a
    corrupted sidecar remains an error rather than being silently skipped.

    Matches parse_sidecar's own comparison (`lines[0].rstrip()`), so a line
    with leading whitespace is not frontmatter in either place.
    """
    try:
        with path.open(encoding="utf-8") as handle:
            first = handle.readline()
    except (OSError, UnicodeDecodeError):
        return False
    return first.rstrip() == DELIMITER
```

- [ ] **Step 4: Use the probe in `load_workspace`**

```python
def load_workspace(root: Path) -> list[Sidecar]:
    found: list[Sidecar] = []
    for path in sorted(root.rglob("*.md")):
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        if not _has_frontmatter(path):
            continue
        # SidecarError propagates deliberately: an unparseable sidecar is an
        # exit-2 condition, not something to skip past.
        found.append(parse_sidecar(path))
    return found
```

- [ ] **Step 5: Run the full suite**

```bash
conda run -n 312 python -m pytest tests/ -q
```
Expected: 148 passed (145 baseline + 3 new).

- [ ] **Step 6: Commit**

```bash
git add plugins/p2c/skills/p2c/scripts/tracelib/sidecar.py tests/test_sidecar.py
git commit -m "fix: skip prose markdown in load_workspace instead of exiting 2"
```

---

### Task 2: Add the FND id prefix

**Files:**
- Modify: `plugins/p2c/skills/p2c/scripts/tracelib/ids.py:5-20`
- Test: `tests/test_ids.py` (append)

**Interfaces:**
- Consumes: nothing
- Produces: `id_type("FND-001") == "finding"`. Every later task depends on this string being exactly `"finding"`.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_ids.py`:

```python
def test_fnd_id_resolves_to_finding():
    assert id_type("FND-001") == "finding"
    assert is_valid_id("FND-001")


@pytest.mark.parametrize("bad", ["FND-1", "FND-0001", "FND001", "fnd-001"])
def test_malformed_fnd_ids_are_invalid(bad):
    assert id_type(bad) is None
    assert not is_valid_id(bad)
```

Check the imports at the top of the file and add `pytest`, `id_type`, `is_valid_id` if absent.

- [ ] **Step 2: Run test to verify it fails**

```bash
conda run -n 312 python -m pytest tests/test_ids.py -q
```
Expected: `test_fnd_id_resolves_to_finding` FAILS — `id_type` returns `None`.

- [ ] **Step 3: Register the prefix**

In `ids.py`, add `"FND": "finding",` to `PREFIX_TO_TYPE` after the `"TC"` entry, and add `FND` to the three-digit alternation:

```python
_THREE_DIGIT = re.compile(r"^(BR|FR|NFR|SCR|ARC|US|TC|FND)-\d{3}\Z")
```

- [ ] **Step 4: Run the full suite**

```bash
conda run -n 312 python -m pytest tests/ -q
```
Expected: 153 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/p2c/skills/p2c/scripts/tracelib/ids.py tests/test_ids.py
git commit -m "feat: add FND id prefix for finding artifacts"
```

---

### Task 3: Validate the finding schema

**Files:**
- Modify: `plugins/p2c/skills/p2c/scripts/tracelib/schema.py`
- Test: `tests/test_schema.py` (append)

**Interfaces:**
- Consumes: `id_type("FND-001") == "finding"` from Task 2
- Produces: findings validate through `validate(sc) -> list[SchemaError]`. Required fields: `traces_to` (exactly one), `history` (non-empty list of quoted 6-hex), `raised_by`, `nature`, `disposition`. Optional: `severity`, `signoff` (mapping with `by` and `at`).

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_schema.py`. Reuse the file's existing `make(...)` helper — read the top of the file to match its exact signature before writing:

```python
VALID_FINDING = {
    "id": "FND-001",
    "type": "finding",
    "title": "Roster sync cannot meet the 200ms p95 budget",
    "traces_to": ["FR-007"],
    "source_hash": {"FR-007": "a3f9c1"},
    "history": ["a3f9c1"],
    "raised_by": "lead-architect",
    "nature": "infeasible",
    "severity": "blocking",
    "disposition": "open",
    "status": "draft",
}


def _finding(**overrides):
    fm = dict(VALID_FINDING)
    for key, value in overrides.items():
        if value is None:
            fm.pop(key, None)
        else:
            fm[key] = value
    return fm


def _fields(errors):
    return {e.field_name for e in errors}


def test_valid_finding_has_no_errors():
    assert validate(make(_finding())) == []


def test_finding_missing_disposition_is_an_error():
    assert "disposition" in _fields(validate(make(_finding(disposition=None))))


def test_finding_unknown_disposition_is_an_error():
    assert "disposition" in _fields(validate(make(_finding(disposition="maybe"))))


def test_finding_unknown_nature_is_an_error():
    assert "nature" in _fields(validate(make(_finding(nature="vibes"))))


def test_finding_unquoted_history_entry_is_an_error():
    errors = validate(make(_finding(history=[0])))
    assert "history" in _fields(errors)
    assert any("padding" in e.message for e in errors)


def test_finding_empty_history_is_an_error():
    assert "history" in _fields(validate(make(_finding(history=[]))))


def test_finding_with_two_targets_is_an_error():
    assert "traces_to" in _fields(
        validate(make(_finding(traces_to=["FR-007", "FR-008"])))
    )


def test_signoff_missing_by_is_an_error():
    assert "signoff" in _fields(
        validate(make(_finding(signoff={"date": "2026-08-18"})))
    )


def test_valid_signoff_is_accepted():
    assert validate(
        make(_finding(signoff={"by": "lead-architect", "date": "2026-08-18"}))
    ) == []
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
conda run -n 312 python -m pytest tests/test_schema.py -q
```
Expected: several FAIL — `REQUIRED_BY_TYPE` has no `finding` key, so no type-specific validation runs.

- [ ] **Step 3: Register the finding type and enums**

In `schema.py`, add to `REQUIRED_BY_TYPE` after the `"test"` entry:

```python
    "finding": ("traces_to", "history", "raised_by", "nature", "disposition"),
```

and add to `ENUMS`:

```python
    "nature": ("infeasible", "cost", "conflict", "risk"),
    "severity": ("blocking", "material", "minor"),
    "disposition": ("open", "accepted", "rejected", "resolved"),
```

- [ ] **Step 4: Add the three validators**

In `schema.py`, after `_source_hash_errors`:

```python
def _history_errors(
    fm: dict[str, Any], path: Path, subject: str
) -> list[SchemaError]:
    """`history` is the finding's raise log: one hash per raise.

    len(history) is the review-iteration count, and history[-1] is what the
    finding-unfounded check compares the requirement's current hash against,
    so an unquoted entry silently breaks the check the same way an unquoted
    source_hash does.
    """
    if "history" not in fm:
        return []

    value = fm.get("history")
    if not isinstance(value, (list, tuple)) or not value:
        return [
            SchemaError(
                path,
                subject,
                "history",
                "'history' must be a non-empty list of quoted 6-character "
                "hex hashes, oldest raise first",
            )
        ]

    errors: list[SchemaError] = []
    for entry in value:
        if not isinstance(entry, str):
            errors.append(
                SchemaError(
                    path,
                    subject,
                    "history",
                    f"history entry {entry!r} must be a quoted 6-character hex "
                    "string; unquoted values like 000000 are parsed as numbers "
                    "by YAML and lose their padding",
                )
            )
        elif not HASH_PATTERN.match(entry):
            errors.append(
                SchemaError(
                    path,
                    subject,
                    "history",
                    "history entry must be a quoted 6-character lowercase hex "
                    f"string, got {entry!r}",
                )
            )
    return errors


def _finding_target_errors(
    fm: dict[str, Any], path: Path, subject: str
) -> list[SchemaError]:
    """A finding challenges exactly one requirement.

    `history` and the finding-unfounded check both assume a single target; a
    conflict between two requirements is filed as two findings.
    """
    targets = fm.get("traces_to")
    if isinstance(targets, str):
        targets = [targets]
    if not isinstance(targets, (list, tuple)) or len(targets) != 1:
        return [
            SchemaError(
                path,
                subject,
                "traces_to",
                "a finding must trace to exactly one requirement",
            )
        ]
    return []


def _signoff_errors(
    fm: dict[str, Any], path: Path, subject: str
) -> list[SchemaError]:
    """`signoff` records who reviewed this artifact and when.

    The reviewed-against hash is deliberately not stored here: it would
    duplicate `source_hash`, and staleness.apply_status strips signoff the
    moment source_hash goes stale, so a present signoff already means
    "reviewed against the currently recorded hashes".
    """
    if "signoff" not in fm:
        return []

    value = fm.get("signoff")
    if not isinstance(value, dict):
        return [
            SchemaError(
                path,
                subject,
                "signoff",
                "'signoff' must be a mapping with 'by' and 'date'",
            )
        ]

    return [
        SchemaError(path, subject, "signoff", f"signoff is missing '{name}'")
        for name in ("by", "date")
        if not value.get(name)
    ]
```

- [ ] **Step 5: Wire them into `validate`**

Replace the tail of `validate()` with:

```python
    errors.extend(_states_errors(fm, sc.path, subject))
    errors.extend(_source_hash_errors(fm, sc.path, subject))
    errors.extend(_history_errors(fm, sc.path, subject))
    errors.extend(_signoff_errors(fm, sc.path, subject))
    if declared == "finding":
        errors.extend(_finding_target_errors(fm, sc.path, subject))

    return errors
```

- [ ] **Step 6: Run the full suite**

```bash
conda run -n 312 python -m pytest tests/ -q
```
Expected: 162 passed.

- [ ] **Step 7: Commit**

```bash
git add plugins/p2c/skills/p2c/scripts/tracelib/schema.py tests/test_schema.py
git commit -m "feat: validate finding sidecars, history hashes and signoff"
```

---

### Task 4: The two finding checks

**Files:**
- Modify: `plugins/p2c/skills/p2c/scripts/tracelib/stages.py`
- Create: `tests/fixtures/finding-open/`, `tests/fixtures/finding-unfounded/`, `tests/fixtures/finding-resolved/`
- Test: `tests/test_stages.py` (append)

**Interfaces:**
- Consumes: finding schema from Task 3
- Produces: gap kinds `unresolved-finding` and `finding-unfounded` from `_check_findings(graph: Graph) -> list[Gap]`, called unconditionally from `check()`.

**Fixture note:** `FR-012` in the `clean` fixture has normative hash `1076e4` — that is why the clean fixture's `SCR-004.md` and `ARC-002.md` both record `source_hash: {FR-012: '1076e4'}`. The three new fixtures are copies of `clean` plus one findings file, so they inherit that hash.

- [ ] **Step 1: Create the three fixtures**

```bash
cd tests/fixtures
for name in finding-open finding-unfounded finding-resolved; do
  cp -r clean "$name"
  mkdir -p "$name/findings"
done
```

`tests/fixtures/finding-open/findings/FND-001.md` — open finding, so `unresolved-finding` fires:

```markdown
---
id: FND-001
type: finding
title: Exception resolution cannot meet the queue latency budget
traces_to: [FR-012]
source_hash: {FR-012: '1076e4'}
history: ['1076e4']
raised_by: lead-architect
nature: infeasible
severity: blocking
disposition: open
proposed_resolution: relax the queue budget, or resolve exceptions asynchronously
status: draft
---

Evidence body for agents.
```

`tests/fixtures/finding-unfounded/findings/FND-001.md` — identical except the
last two frontmatter lines before `status`, so `finding-unfounded` fires
(resolved, but `history[-1]` still equals FR-012's current hash):

```markdown
---
id: FND-001
type: finding
title: Exception resolution cannot meet the queue latency budget
traces_to: [FR-012]
source_hash: {FR-012: '1076e4'}
history: ['1076e4']
raised_by: lead-architect
nature: infeasible
severity: blocking
disposition: resolved
status: draft
---

Evidence body for agents.
```

`tests/fixtures/finding-resolved/findings/FND-001.md` — resolved after a real
edit: `history` records the hash the finding was raised against, which is no
longer FR-012's hash, so neither check fires:

```markdown
---
id: FND-001
type: finding
title: Exception resolution cannot meet the queue latency budget
traces_to: [FR-012]
source_hash: {FR-012: '1076e4'}
history: ['aaaaaa']
raised_by: lead-architect
nature: infeasible
severity: blocking
disposition: resolved
status: draft
---

Evidence body for agents.
```

- [ ] **Step 2: Write the failing tests**

Append to `tests/test_stages.py` (the file already defines `gaps_for`):

```python
def test_open_finding_is_reported_as_unresolved(fixtures_root):
    gaps = gaps_for(fixtures_root, "finding-open", "design")
    assert any(g.kind == "unresolved-finding" and g.subject == "FND-001"
               for g in gaps)


def test_findings_are_checked_at_every_stage(fixtures_root):
    for stage in ("requirements", "design", "handoff", "build"):
        gaps = gaps_for(fixtures_root, "finding-open", stage)
        assert any(g.kind == "unresolved-finding" for g in gaps), stage


def test_resolved_finding_against_unmoved_requirement_is_unfounded(fixtures_root):
    gaps = gaps_for(fixtures_root, "finding-unfounded", "design")
    assert any(g.kind == "finding-unfounded" and g.subject == "FND-001"
               for g in gaps)
    assert all(g.kind != "unresolved-finding" for g in gaps)


def test_resolved_finding_after_a_real_edit_is_clean(fixtures_root):
    gaps = gaps_for(fixtures_root, "finding-resolved", "design")
    assert all(g.kind not in ("unresolved-finding", "finding-unfounded")
               for g in gaps)
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
conda run -n 312 python -m pytest tests/test_stages.py -q
```
Expected: the three new gap-kind assertions FAIL — no such kinds exist yet.

- [ ] **Step 4: Implement the check**

In `stages.py`, after `_check_unhashed_links`:

```python
def _check_findings(graph: Graph) -> list[Gap]:
    """Report findings still open, and closures that changed nothing.

    `unresolved-finding` fires for open and accepted findings at every
    stage: an unresolved challenge to a requirement is an open question
    regardless of which stage is being validated.

    `finding-unfounded` fires when a finding claims `resolved` but the
    requirement's normative text has not moved since the finding was last
    raised — someone closed the challenge without anything changing.
    `rejected` is deliberately exempt: closing because the cost was accepted
    is a legitimate close with no requirement edit.
    """
    gaps: list[Gap] = []

    for finding in sorted(graph.by_type("finding"), key=lambda s: s.id):
        fm = finding.frontmatter
        disposition = fm.get("disposition")

        targets = fm.get("traces_to") or []
        if isinstance(targets, str):
            targets = [targets]
        target_id = str(targets[0]) if targets else None

        if disposition in ("open", "accepted"):
            gaps.append(
                Gap(
                    "unresolved-finding",
                    finding.id,
                    f"{disposition} {fm.get('nature', 'unspecified')} finding "
                    f"against {target_id or 'no requirement'} is unresolved",
                )
            )
            continue

        if disposition != "resolved" or target_id is None:
            continue

        history = fm.get("history") or []
        upstream = graph.nodes.get(target_id)
        if not history or upstream is None:
            continue

        if normative_hash(upstream) == str(history[-1]):
            gaps.append(
                Gap(
                    "finding-unfounded",
                    finding.id,
                    f"marked resolved but {target_id} has not changed since "
                    f"the finding was last raised (still {history[-1]})",
                )
            )

    return gaps
```

`normative_hash` and `Gap` are already imported at the top of `stages.py`.

- [ ] **Step 5: Call it from `check`**

```python
def check(graph: Graph, stage: str, workspace_root: Path) -> list[Gap]:
    index = _stage_index(stage)
    gaps = _check_requirements_stage(graph)
    gaps.extend(_check_findings(graph))
    if index >= STAGES.index("design"):
        gaps.extend(_check_design_stage(graph, workspace_root))
        gaps.extend(_check_unhashed_links(graph))
    if index >= STAGES.index("handoff"):
        gaps.extend(_check_handoff_stage(graph))
    if index >= STAGES.index("build"):
        gaps.extend(_check_build_stage(graph))
    return gaps
```

- [ ] **Step 6: Run the full suite**

```bash
conda run -n 312 python -m pytest tests/ -q
```
Expected: 166 passed.

- [ ] **Step 7: Commit**

```bash
git add plugins/p2c/skills/p2c/scripts/tracelib/stages.py tests/test_stages.py tests/fixtures/finding-open tests/fixtures/finding-unfounded tests/fixtures/finding-resolved
git commit -m "feat: report unresolved and unfounded findings at every stage"
```

---

### Task 5: The undeclared-state check, and the fixtures it breaks

Makes Absolute Rule 2 (mockups covering default, empty, loading, error and success) machine-checkable.

**This task changes existing fixtures and a shipped template on purpose.** Every fixture screen currently declares one state out of five, and `tests/test_stages.py`, `tests/test_cli.py` assert the `clean` fixture produces zero gaps. Adding the check without repairing `clean` breaks four existing tests. The `clean` fixture is meant to represent a *clean* workspace; under the new rule a screen with one state is not clean, so the fixture is what's wrong, not the assertion.

**Files:**
- Modify: `plugins/p2c/skills/p2c/scripts/tracelib/stages.py`
- Modify: `plugins/p2c/skills/p2c/templates/screen-template.md`
- Modify: `tests/fixtures/clean/03-design/mockups/SCR-004.md`
- Create: `tests/fixtures/clean/03-design/mockups/SCR-004-{empty,loading,error,success}.html`
- Modify: the three `finding-*` fixtures from Task 4 (they are copies of `clean`)
- Test: `tests/test_stages.py` (append)

**Interfaces:**
- Consumes: nothing from earlier tasks
- Produces: gap kind `undeclared-state`, module constant `REQUIRED_STATES: frozenset[str]`. Distinct from `missing-state`, which means "declared file not found on disk".

- [ ] **Step 1: Write the failing test**

Append to `tests/test_stages.py`:

```python
def test_screen_missing_canonical_states_is_reported(fixtures_root):
    # The undeclared-state fixture declares only default and error.
    gaps = gaps_for(fixtures_root, "undeclared-state", "design")
    undeclared = [g for g in gaps if g.kind == "undeclared-state"]
    assert len(undeclared) == 1
    assert undeclared[0].subject == "SCR-004"
    for missing in ("empty", "loading", "success"):
        assert missing in undeclared[0].message


def test_clean_fixture_declares_all_canonical_states(fixtures_root):
    gaps = gaps_for(fixtures_root, "clean", "design")
    assert all(g.kind != "undeclared-state" for g in gaps)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
conda run -n 312 python -m pytest tests/test_stages.py -q
```
Expected: `test_screen_missing_canonical_states_is_reported` FAILS — `undeclared` is empty.

- [ ] **Step 3: Add the constant**

In `stages.py`, below `_MOCKUP_DIR`:

```python
# The five states Absolute Rule 2 requires of every key screen. Reported,
# never blocked: some screens legitimately have no empty state, so this is a
# prompt to justify the omission rather than a hard requirement.
REQUIRED_STATES: frozenset[str] = frozenset(
    {"default", "empty", "loading", "error", "success"}
)
```

- [ ] **Step 4: Add the check**

In `_check_design_stage`, immediately after the `if not isinstance(states, dict): ... continue` block and before the `for state_name, filename in sorted(states.items()):` loop:

```python
        undeclared = sorted(REQUIRED_STATES - set(states))
        if undeclared:
            gaps.append(
                Gap(
                    "undeclared-state",
                    screen.id,
                    "declares no " + ", ".join(undeclared) + " state; Absolute "
                    "Rule 2 expects default, empty, loading, error and success",
                )
            )
```

- [ ] **Step 5: Repair the clean fixture**

Replace the `states:` block in `tests/fixtures/clean/03-design/mockups/SCR-004.md` with:

```yaml
states:
  default: SCR-004.html
  empty: SCR-004-empty.html
  loading: SCR-004-loading.html
  error: SCR-004-error.html
  success: SCR-004-success.html
```

Create the four new mockup files next to the existing `SCR-004.html`, each with the same placeholder content style as that file:

```bash
cd tests/fixtures/clean/03-design/mockups
for s in empty loading error success; do
  printf '<!doctype html>\n<title>SCR-004 %s</title>\n' "$s" > "SCR-004-$s.html"
done
```

Apply the identical change to the three `finding-*` fixtures created in Task 4 — they are copies of `clean` and will otherwise report `undeclared-state` and `missing-state`:

```bash
cd tests/fixtures
for name in finding-open finding-unfounded finding-resolved; do
  cp clean/03-design/mockups/SCR-004.md "$name/03-design/mockups/SCR-004.md"
  cp clean/03-design/mockups/SCR-004-*.html "$name/03-design/mockups/"
done
```

- [ ] **Step 6: Update the screen template to declare all five states**

In `plugins/p2c/skills/p2c/templates/screen-template.md`, replace the `states:` block with:

```yaml
states:
  default: {{ID}}.html
  empty: {{ID}}-empty.html
  loading: {{ID}}-loading.html
  error: {{ID}}-error.html
  success: {{ID}}-success.html
```

`tests/test_templates.py::test_workspace_built_from_templates_reports_exactly_the_authoring_gaps` asserts the template-built workspace reports exactly `{"missing-state"}`. That still holds: all five declared files are missing rather than one, and no `undeclared-state` fires because all five are declared. Do not change that assertion.

A second test in the same file is also coupled to this change and **must** be
updated: `test_template_workspace_passes_once_the_author_fills_it_in` builds the
mockup the screen declares and then asserts a clean exit 0. With five states
declared, the author's work is five mockup files, not one, so that test must
write all five. Replace its single `SCR-001.html` write with a loop over
`SCR-001.html`, `SCR-001-empty.html`, `SCR-001-loading.html`,
`SCR-001-error.html`, `SCR-001-success.html`. Keep the `== 0` assertion — the
test's premise (author completes their work, workspace passes) is unchanged;
only the definition of "their work" grew.

- [ ] **Step 7: Run the full suite**

```bash
conda run -n 312 python -m pytest tests/ -q
```
Expected: 168 passed, none failed. If `test_clean_fixture_passes_pre_build_stages`, `test_clean_workspace_exits_zero`, `test_clean_workspace_exits_zero_at_handoff` or `test_schema_error_overwrites_gaps_report` fail, the Step 5 fixture repair is incomplete — those four assert the clean fixture produces zero gaps.

- [ ] **Step 8: Commit**

```bash
git add plugins/p2c/skills/p2c/scripts/tracelib/stages.py plugins/p2c/skills/p2c/templates/screen-template.md tests/
git commit -m "feat: report screens missing canonical mockup states"
```

---

### Task 6: Render findings in the reports

**Files:**
- Modify: `plugins/p2c/skills/p2c/scripts/tracelib/report.py`
- Test: `tests/test_report.py` (append)

**Interfaces:**
- Consumes: finding nodes from Task 3, fixtures from Task 4
- Produces: a `## Findings` section in `gaps.md`, a `findings` array in `index.json`, module constant `ESCALATION_THRESHOLD = 3`.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_report.py` (match the file's existing import style):

```python
def test_findings_render_in_gaps_md(tmp_path, fixtures_root):
    graph = build_graph(load_workspace(fixtures_root / "finding-open"))
    write_all(graph, [], [], tmp_path)
    gaps_md = (tmp_path / "gaps.md").read_text(encoding="utf-8")
    assert "## Findings" in gaps_md
    assert "FND-001" in gaps_md
    assert "FR-012" in gaps_md


def test_findings_recorded_in_index(tmp_path, fixtures_root):
    graph = build_graph(load_workspace(fixtures_root / "finding-open"))
    write_all(graph, [], [], tmp_path)
    data = json.loads((tmp_path / "index.json").read_text(encoding="utf-8"))
    entry = data["findings"][0]
    assert entry["id"] == "FND-001"
    assert entry["challenges"] == ["FR-012"]
    assert entry["nature"] == "infeasible"
    assert entry["disposition"] == "open"
    assert entry["iterations"] == 1


def test_no_findings_renders_placeholder(tmp_path, fixtures_root):
    graph = build_graph(load_workspace(fixtures_root / "clean"))
    write_all(graph, [], [], tmp_path)
    gaps_md = (tmp_path / "gaps.md").read_text(encoding="utf-8")
    assert "No findings recorded." in gaps_md


def test_escalation_flag_appears_at_threshold(tmp_path, fixtures_root):
    graph = build_graph(load_workspace(fixtures_root / "finding-open"))
    graph.nodes["FND-001"].frontmatter["history"] = ["1076e4", "aaaaaa", "bbbbbb"]
    write_all(graph, [], [], tmp_path)
    gaps_md = (tmp_path / "gaps.md").read_text(encoding="utf-8")
    assert "escalate" in gaps_md.lower()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
conda run -n 312 python -m pytest tests/test_report.py -q
```
Expected: FAIL — `## Findings` absent, `data["findings"]` raises `KeyError`.

- [ ] **Step 3: Add the threshold and the renderer**

In `report.py`, below `_NEWLINE_RE`:

```python
# Iterations after which a finding stops being a normal loop and becomes a
# decision the human has to force. See spec section 5.4.
ESCALATION_THRESHOLD = 3
```

Above `write_gaps`:

```python
def _findings_section(graph: Graph | None) -> list[str]:
    """Render the findings table.

    Iterations is len(history) — the number of times this finding has been
    raised against successive versions of the requirement. At or above
    ESCALATION_THRESHOLD the loop is not converging and the orchestrator must
    put the decision back to the user.
    """
    if graph is None:
        return []

    findings = sorted(graph.by_type("finding"), key=lambda s: s.id)
    if not findings:
        return ["## Findings", "", "No findings recorded.", ""]

    lines = [
        "## Findings",
        "",
        "| Finding | Challenges | Nature | Severity | Disposition | Iterations | Escalate |",
        "|---|---|---|---|---|---|---|",
    ]
    for sc in findings:
        fm = sc.frontmatter
        targets = fm.get("traces_to") or []
        if isinstance(targets, str):
            targets = [targets]
        iterations = len(fm.get("history") or [])
        escalate = "escalate" if iterations >= ESCALATION_THRESHOLD else "—"
        lines.append(
            f"| {_cell(sc.id)} | "
            f"{_cell(', '.join(str(t) for t in targets) or '—')} | "
            f"{_cell(fm.get('nature', '—'))} | "
            f"{_cell(fm.get('severity', '—'))} | "
            f"{_cell(fm.get('disposition', '—'))} | "
            f"{_cell(iterations)} | {_cell(escalate)} |"
        )
    lines.append("")
    return lines
```

- [ ] **Step 4: Append the section in `write_gaps`**

Replace the final line of `write_gaps` with:

```python
    lines += _findings_section(graph)

    out_path.write_text("\n".join(lines), encoding="utf-8")
```

Note `write_all` already passes `graph=graph` to `write_gaps`.

- [ ] **Step 5: Add findings to `index.json`**

In `write_index`, add to `payload` between `"stale"` and `"summary"`:

```python
        "findings": [
            {
                "id": sc.id,
                "challenges": sorted(graph.out.get(sc.id, set())),
                "nature": sc.frontmatter.get("nature", ""),
                "severity": sc.frontmatter.get("severity", ""),
                "disposition": sc.frontmatter.get("disposition", ""),
                "iterations": len(sc.frontmatter.get("history") or []),
            }
            for sc in sorted(graph.by_type("finding"), key=lambda s: s.id)
        ],
```

- [ ] **Step 6: Run the full suite**

```bash
conda run -n 312 python -m pytest tests/ -q
```
Expected: 172 passed.

- [ ] **Step 7: Commit**

```bash
git add plugins/p2c/skills/p2c/scripts/tracelib/report.py tests/test_report.py
git commit -m "feat: render findings table and escalation flag in reports"
```

---

### Task 7: Templates

**Files:**
- Create: `plugins/p2c/skills/p2c/templates/finding-template.md`
- Modify: `plugins/p2c/skills/p2c/templates/{requirement,screen,component,persona,journey}-template.md`
- Modify: `tests/test_templates.py`

**Interfaces:**
- Consumes: the schema from Task 3
- Produces: `templates/finding-template.md`, referenced by the agent files in Tasks 9–10

- [ ] **Step 1: Create the finding template**

`plugins/p2c/skills/p2c/templates/finding-template.md`:

````markdown
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
````

- [ ] **Step 2: Register it in the template test**

In `tests/test_templates.py`, add to `SUBSTITUTIONS`:

```python
    "finding-template.md": {
        "{{ID}}": "FND-001", "{{TITLE}}": "Example finding",
        "{{REQ_ID}}": "FR-001", "{{AGENT}}": "lead-architect",
        "{{NATURE}}": "infeasible", "{{SEVERITY}}": "blocking",
        "{{RESOLUTION}}": "relax the budget to 500ms",
    },
```

Do **not** add it to `E2E_LAYOUT` — the end-to-end template test asserts an
exact gap-kind set, and a finding would add `unresolved-finding` to it.

- [ ] **Step 3: Add the sign-off block to the five sidecar templates**

Append this identical block to `requirement-template.md`, `screen-template.md`, `component-template.md`, `persona-template.md` and `journey-template.md`:

````markdown
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
````

Use a literal `<agent>` and `<YYYY-MM-DD>`, not `{{AGENT}}` tokens —
`test_filled_template_passes_schema` asserts no `{{TOKEN}}` survives
substitution, and these five templates' substitution maps do not define them.

- [ ] **Step 4: Run the full suite**

```bash
conda run -n 312 python -m pytest tests/ -q
```
Expected: 174 passed (the two new template tests are parametrized over the new SUBSTITUTIONS entry).

- [ ] **Step 5: Commit**

```bash
git add plugins/p2c/skills/p2c/templates/ tests/test_templates.py
git commit -m "docs: add finding template and document signoff on sidecar templates"
```

---

### Task 8: Wire the orchestrator

**Files:**
- Modify: `plugins/p2c/skills/p2c/SKILL.md`

**Interfaces:**
- Consumes: the CLI contract of `trace.py`, gap kinds from Tasks 4–5
- Produces: the phase-boundary ritual that Tasks 9–11 reference

- [ ] **Step 1: Add the new directories to the workspace layout**

In the workspace tree under "Workspace conventions", after the `08-measure/` line:

```
├── findings/                # FND-NNN feasibility findings (sidecars)
├── traceability/            # generated: rtm.md, index.json, gaps.md — do not hand-edit
```

- [ ] **Step 2: Add the traceability section**

Insert immediately before "## Coverage discipline":

````markdown
## Traceability and the feasibility loop

Artifacts in `p2c-workspace/` come in two forms. **Prose** (`prd.md`,
`jtbd.md`, ADRs, runbooks) is read by humans. **Sidecars** are markdown files
with YAML frontmatter that form a traceability graph: requirements
(`BR-`/`FR-`/`NFR-`), personas (`P-`), journeys (`J-`), screens (`SCR-`),
components (`ARC-`), stories (`US-`), tests (`TC-`) and findings (`FND-`).
Templates for each live in `templates/`.

Each downstream sidecar records `source_hash` — the hash of each upstream
requirement as it read when the artifact was authored. When a requirement's
`statement` or `acceptance_criteria` changes, every artifact tracing to it is
marked `status: stale` and its `signoff` is stripped. That is how requirements
and UX artifacts are prevented from silently going out of date.

### When an agent finds something infeasible

Any agent that discovers a requirement cannot be built as written files a
finding sidecar in `p2c-workspace/findings/` using
`templates/finding-template.md`. Raiser, decider and editor are three
different parties:

- **Raiser** (lead-architect, lead-developer, lead-qa-coordinator,
  lead-ux-designer) writes the finding. They hold the evidence.
- **You, the orchestrator,** surface it to the user. You never resolve a
  finding and never edit a requirement.
- **product-owner** decides: `accepted` (valid, the requirement should
  change) or `rejected` (the requirement stands, the architecture absorbs
  the cost).
- **business-analyst** is the sole writer of requirement sidecars and applies
  the edit, bumping `version`.

After the edit, everything downstream goes stale and each owning agent
re-works its artifact. The raiser re-reads the changed requirement and either
sets `disposition: resolved` or keeps the finding open with a new entry
appended to `history` — that second entry is iteration 2.

At `len(history) >= 3`, stop looping and escalate to the user: this
requirement and this architecture have failed to reconcile across three
revisions, and the next move is a scope change or a constraint change, not
another cycle.

### The phase-boundary ritual (mandatory)

You already stop and ask the user at every phase boundary. At each of those
stops you **must**:

1. Run the checker:

   ```bash
   python skills/p2c/scripts/trace.py --workspace p2c-workspace --stage <stage> --apply-status
   ```

   Stage mapping: phase 2 → `requirements`, phase 3 → `design`, phase 4 →
   `handoff`, phase 5 and later → `build`. Always pass `--stage` explicitly.

2. Include in the phase summary — not optional, not summarised away:
   - open-finding count, with IDs and the requirement each challenges
   - every staleness entry, naming which artifacts lost sign-off
   - the gap list grouped by kind
   - any finding at `len(history) >= 3`, flagged for escalation

3. Never write `status: delivered` into `status.json` while the checker's
   most recent run reported any gaps or staleness — exit code 1, or a
   Gaps/Staleness table in `traceability/gaps.md` with rows in it — without
   naming those gaps in the summary. Note `gaps.md` always exists and is
   never byte-empty: a clean run writes "No gaps found." into it, so judge
   by the exit code or the table rows, never by file size. Advancing is permitted — this is advisory — but advancing
   *quietly* is not.

The checker reports; it never blocks. Exit code 1 means gaps or staleness
exist, not that the phase cannot advance. Teams wanting hard enforcement wire
the exit code into CI.

When the user signs a gate, record it in `p2c-workspace/config.json`:

```json
{"gates": {"gate1": {"status": "signed"}}}
```

`gate1` → design, `gate2` → handoff, `gate3` → build. `status.json` remains
your phase tracker; `config.json` is only the gate record.
````

- [ ] **Step 3: Add sidecar ownership after the dispatch table**

````markdown
**Sidecar ownership.** Each agent writes only its own artifact types:

| Agent | Owns |
|---|---|
| business-analyst | `BR-`, `FR-`, `NFR-` — **sole writer of requirement sidecars** |
| product-owner | none — decides disposition and priority; the BA applies the edit |
| lead-ux-designer | `P-`, `J-`, `SCR-` |
| lead-architect | `ARC-` |
| scrum-master | `US-` |
| lead-qa-coordinator | `TC-` |
| lead-developer | none new — consumes `ARC-`/`SCR-`/`US-`; raises findings |
| research-marketing | none — prose only |

Requirement sidecars have exactly one writer because `version` integrity and
hash stability depend on it. The product owner still owns the PRD as prose and
still owns every decision.
````

- [ ] **Step 4: Verify and run the suite**

```bash
grep -c "trace.py" plugins/p2c/skills/p2c/SKILL.md
conda run -n 312 python -m pytest tests/ -q
```
Expected: non-zero count; 174 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/p2c/skills/p2c/SKILL.md
git commit -m "docs: wire the traceability checker and feasibility loop into the orchestrator"
```

---

### Task 9: Requirement-owning agent contracts

**Files:**
- Modify: `plugins/p2c/agents/business-analyst.md`, `plugins/p2c/agents/product-owner.md`

**Interfaces:**
- Consumes: ownership table from Task 8
- Produces: the sole-writer rule and disposition split Task 10 depends on

- [ ] **Step 1: Add the sole-writer section to the business-analyst**

Insert before "## Working with other agents":

````markdown
## Requirement sidecars (you are the sole writer)

Every requirement exists twice: as prose in the BRD, and as a sidecar in
`p2c-workspace/02-requirements/` built from `templates/requirement-template.md`.
You are the only agent that writes requirement sidecars. Nobody else edits
`BR-`, `FR-` or `NFR-` files — not the product owner, not the architect.

Only `statement` and `acceptance_criteria` are normative: changing them moves
the requirement's hash and marks every downstream artifact stale. Changing
`priority`, `source`, `version` or the prose body does not. That is
deliberate — re-prioritising a requirement should not invalidate a screen.

When the product owner accepts a finding and rules that a requirement must
change:

1. Edit `statement` and/or `acceptance_criteria`.
2. Bump `version` by one.
3. Report the requirement ID and its new hash back to the orchestrator.

The orchestrator runs the checker, everything downstream goes stale, and each
owning agent re-works its artifact. Do not edit a requirement to make a gap
disappear — an edit that changes nothing normative moves no hash and repairs
nothing.
````

- [ ] **Step 2: Add the disposition section to the product-owner**

Insert before "## Working with other agents":

````markdown
## Ruling on findings

When an agent finds a requirement cannot be built as written, it files a
finding sidecar in `p2c-workspace/findings/`. You rule on it. You do not edit
the requirement yourself — the business-analyst is the sole writer of
requirement sidecars.

Set `disposition` to one of:

- **`accepted`** — the finding is valid and the requirement must change. Tell
  the orchestrator what the requirement should now say; the business-analyst
  applies the edit and bumps `version`.
- **`rejected`** — the requirement stands. Either you are accepting the cost
  or risk the finding describes, or the finding is withdrawn as mistaken. If
  you are accepting a cost, say so explicitly so the architect records it in
  an ADR.

You do not set `resolved`. That belongs to the agent that raised the finding,
after it re-reads the edited requirement and confirms the change actually
addresses the problem. A finding marked `resolved` against a requirement whose
hash never moved is reported as `finding-unfounded`.

If a finding reaches three iterations (`len(history) >= 3`), stop ruling on it
and take a scope decision instead: the requirement and the architecture are
not reconciling, and a fourth cycle will not fix that.
````

- [ ] **Step 3: Add the return-contract bullets to both files**

In each file's "## Output to orchestrator" section, add:

```markdown
- Sidecars written/updated (with new hashes where a normative field changed)
- Findings raised, or ruled on with the disposition set
- Stale artifacts repaired, with the new `source_hash` recorded
- Artifacts left stale, and why
```

- [ ] **Step 4: Verify**

```bash
grep -l "sole writer" plugins/p2c/agents/business-analyst.md
grep -l "disposition" plugins/p2c/agents/product-owner.md
```
Expected: both files listed.

- [ ] **Step 5: Commit**

```bash
git add plugins/p2c/agents/business-analyst.md plugins/p2c/agents/product-owner.md
git commit -m "docs: give the BA sole ownership of requirement sidecars and the PO finding dispositions"
```

---

### Task 10: Raiser and remaining agent contracts

**Files:**
- Modify: `plugins/p2c/agents/{lead-architect,lead-developer,lead-qa-coordinator,lead-ux-designer,scrum-master,research-marketing}.md`

**Interfaces:**
- Consumes: disposition split from Task 9, `templates/finding-template.md` from Task 7
- Produces: nothing later tasks depend on

**Insert anchors differ per file — check before inserting:**

| File | Anchor |
|---|---|
| `lead-architect.md` | before `## Working with other agents` |
| `lead-developer.md` | before `## Working with other agents` |
| `lead-qa-coordinator.md` | before `## Working with other agents` |
| `lead-ux-designer.md` | before `## Working with other agents` |
| `scrum-master.md` | before `## Output to orchestrator` — **this file has no "Working with other agents" section** |

- [ ] **Step 1: Add the finding-filing protocol to the four raiser agents**

Insert into `lead-architect.md`, `lead-developer.md`, `lead-qa-coordinator.md` and `lead-ux-designer.md`, replacing `<YOUR-AGENT-NAME>` with the file's own agent name:

````markdown
## Filing a feasibility finding

When you conclude a requirement cannot be met as written — infeasible,
unaffordable, in conflict with another requirement, or carrying unacceptable
risk — do not silently reinterpret it and do not fix it yourself. File a
finding.

1. Copy `templates/finding-template.md` to
   `p2c-workspace/findings/FND-NNN.md`, next number in sequence.
2. `traces_to` takes exactly one requirement — the one that must change.
3. `history` gets one entry: that requirement's current normative hash. The
   checker prints it; the `unhashed-link` gap message also carries it.
4. Set `raised_by: <YOUR-AGENT-NAME>`, `nature`, `severity`, and a concrete
   `proposed_resolution`. "This won't work" is not a finding; "relax p95 to
   500ms, or drop to 5s polling" is.
5. Put the evidence in the body: the numbers, the spike, the ADR.
6. Leave `disposition: open`. The product owner rules on it, not you.

Report the finding ID to the orchestrator in your return payload.

**Closing a finding.** After the business-analyst edits the requirement, your
artifact goes stale and the finding does too. Re-read the requirement as it
now reads. If the change addresses the problem, set `disposition: resolved`.
If it does not, leave it open and append the requirement's new hash to
`history` — that is iteration 2, and the orchestrator escalates to the user at
three.

Only you can set `resolved` — it is a factual confirmation that only the party
holding the evidence can make. Never set it without re-reading the edited
requirement; a `resolved` finding against a requirement whose hash never moved
is reported as `finding-unfounded`.
````

- [ ] **Step 2: Add the sidecar-ownership sections**

To `lead-architect.md`:

````markdown
## Component sidecars

Every container in your C4 Level 2 diagram gets a sidecar in
`p2c-workspace/04-architecture/` from `templates/component-template.md`, with
an `ARC-NNN` id. `traces_to` lists every requirement the component serves, and
`source_hash` needs one quoted entry per requirement listed there — an
unrecorded requirement can be rewritten from top to bottom without this
component ever being flagged.

A requirement with no component owning it is reported as `broken-chain` at the
handoff stage. A component tracing to nothing is reported as `orphan-artifact`
— architecture nobody asked for.
````

To `lead-ux-designer.md`:

````markdown
## Persona, journey and screen sidecars

Alongside the mockups, write sidecars into `p2c-workspace/03-design/` from
`templates/persona-template.md`, `journey-template.md` and
`screen-template.md`.

Screen sidecars carry the `states` mapping, and this is how the mandatory
mockup rule is enforced mechanically:

```yaml
states:
  default: SCR-004.html
  empty: SCR-004-empty.html
  loading: SCR-004-loading.html
  error: SCR-004-error.html
  success: SCR-004-success.html
```

Every declared file is resolved against `03-design/mockups/` and reported as
`missing-state` if absent. A screen that does not declare all five canonical
states is reported as `undeclared-state`. Both are advisory — if a screen
genuinely has no empty state, say so when you report to the orchestrator
rather than declaring a file that does not exist.

Each screen also needs `personas`, `journey_steps`, and a `source_hash` entry
for every requirement in `traces_to`.
````

To `lead-qa-coordinator.md`:

````markdown
## Test sidecars

Each test case in the plan gets a sidecar in
`p2c-workspace/06-test-and-harden/` with a `TC-NNN` id, tracing to the
requirements it asserts. Non-functional and system-surface requirements with
no test asserting them are reported as `broken-chain` at the handoff stage —
that check is the reason NFRs stop being decorative.
````

To `scrum-master.md`:

````markdown
## Story sidecars

Every story gets a sidecar in `p2c-workspace/02-requirements/stories/` with a
`US-NNN` id, tracing to the requirements it implements, plus a `source_hash`
entry for each. A requirement with no story implementing it is reported as
`broken-chain` at the build stage; a story tracing to nothing is reported as
`orphan-artifact` — scope creep.
````

- [ ] **Step 3: Add the return-contract bullets**

To the "## Output to orchestrator" section of the five sidecar-owning files in this task:

```markdown
- Sidecars written/updated
- Findings raised (or: none)
- Stale artifacts repaired, with the new `source_hash` recorded
- Artifacts left stale, and why
```

To `research-marketing.md`, which owns no sidecars, add only:

```markdown
- Findings raised (or: none)
```

- [ ] **Step 4: Verify every agent file carries the return contract**

```bash
grep -L "Findings raised" plugins/p2c/agents/*.md
```
Expected: no output — all eight files match.

- [ ] **Step 5: Commit**

```bash
git add plugins/p2c/agents/
git commit -m "docs: add finding-filing protocol and sidecar ownership to agent contracts"
```

---

### Task 11: Commands and visual standards

**Files:**
- Modify: `plugins/p2c/commands/{full,product,design,tech-scope,tech-build,tech-prod,poc,launch}.md`
- Modify: `plugins/p2c/skills/p2c/references/visual-standards.md`

**Interfaces:**
- Consumes: the ritual from Task 8
- Produces: nothing later tasks depend on

- [ ] **Step 1: Add the ritual reference to the eight command files**

`commands/help.md` is deliberately excluded — it prints the command map and runs no phases. Add to each file's "## Stop conditions" section, or at the end of its entry sequence if it has none:

```markdown
- At every phase boundary, run the traceability checker and report its output
  as described under "The phase-boundary ritual" in `skills/p2c/SKILL.md`.
  Open findings, staleness and gaps are named in the phase summary every time.
  The checker is advisory — it never blocks a phase from advancing, but a
  phase may not advance without its output being reported.
```

- [ ] **Step 2: Point Absolute Rule 2 at the check**

Append to the phase-3 gate section of `references/visual-standards.md` (around line 121, where `status.json` and mockups are discussed):

````markdown
This rule is also checked mechanically. Screen sidecars declare their states:

```yaml
states:
  default: SCR-004.html
  empty: SCR-004-empty.html
  loading: SCR-004-loading.html
  error: SCR-004-error.html
  success: SCR-004-success.html
```

`trace.py` resolves each declared file against `03-design/mockups/` and
reports `missing-state` when a declared file is absent, and
`undeclared-state` when a screen does not declare all five canonical states.
Both are advisory: they report, they do not block. The prose gate above
remains the binding rule — the checks exist so a gap is visible immediately
rather than in phase 5.
````

- [ ] **Step 3: Verify**

```bash
grep -L "phase-boundary ritual" plugins/p2c/commands/*.md | grep -v "help.md"
```
Expected: no output.

- [ ] **Step 4: Commit**

```bash
git add plugins/p2c/commands/ plugins/p2c/skills/p2c/references/visual-standards.md
git commit -m "docs: reference the phase-boundary ritual from every command"
```

---

### Task 12: End-to-end cycle test

Proves spec §5.3: editing a requirement cascades staleness to the screen, component **and the finding itself**, stripping sign-off from each.

**Files:**
- Create: `tests/test_finding_cycle.py`

**Interfaces:**
- Consumes: everything from Tasks 1–6
- Produces: nothing

- [ ] **Step 1: Write the test**

`tests/test_finding_cycle.py`:

```python
from __future__ import annotations

import shutil

import pytest
import yaml

from tracelib.graph import build_graph
from tracelib.hashing import normative_hash
from tracelib.sidecar import load_workspace
from tracelib.staleness import apply_status, detect


@pytest.fixture
def cycle_ws(tmp_path, fixtures_root):
    ws = tmp_path / "ws"
    shutil.copytree(fixtures_root / "finding-open", ws)
    # Sign off every sidecar so the cascade has something to strip.
    for rel in (
        "03-design/mockups/SCR-004.md",
        "04-architecture/components/ARC-002.md",
        "findings/FND-001.md",
    ):
        path = ws / rel
        text = path.read_text(encoding="utf-8")
        head, front, body = text.split("---", 2)
        fm = yaml.safe_load(front)
        fm["signoff"] = {"by": "an-agent", "date": "2026-08-18"}
        path.write_text(
            "---\n"
            + yaml.safe_dump(fm, sort_keys=False, allow_unicode=True).strip()
            + "\n---"
            + body,
            encoding="utf-8",
        )
    return ws


def _front(path):
    return yaml.safe_load(path.read_text(encoding="utf-8").split("---")[1])


def test_clean_before_the_edit(cycle_ws):
    graph = build_graph(load_workspace(cycle_ws))
    assert detect(graph) == []


def test_editing_the_requirement_stales_everything_including_the_finding(cycle_ws):
    fr012 = cycle_ws / "02-requirements" / "register" / "FR-012.md"
    before = normative_hash(build_graph(load_workspace(cycle_ws)).nodes["FR-012"])

    text = fr012.read_text(encoding="utf-8")
    fr012.write_text(
        text.replace(
            "A dispatcher can view and resolve unresolved exceptions.",
            "A dispatcher can view, triage and resolve unresolved exceptions.",
        ),
        encoding="utf-8",
    )

    graph = build_graph(load_workspace(cycle_ws))
    assert normative_hash(graph.nodes["FR-012"]) != before

    entries = detect(graph)
    subjects = {e.subject for e in entries}
    assert {"SCR-004", "ARC-002", "FND-001"} <= subjects
    assert all(
        e.signoff_voided
        for e in entries
        if e.subject in {"SCR-004", "ARC-002", "FND-001"}
    )

    apply_status(entries, graph)

    for rel in (
        "03-design/mockups/SCR-004.md",
        "04-architecture/components/ARC-002.md",
        "findings/FND-001.md",
    ):
        fm = _front(cycle_ws / rel)
        assert fm["status"] == "stale", rel
        assert "signoff" not in fm, rel
```

- [ ] **Step 2: Run the test**

```bash
conda run -n 312 python -m pytest tests/test_finding_cycle.py -q
```
Expected: 2 passed. If `FND-001` is missing from `subjects`, the finding is not joining the graph — check that Task 2 registered `FND` and that the finding records `source_hash` for `FR-012`.

- [ ] **Step 3: Run the full suite**

```bash
conda run -n 312 python -m pytest tests/ -q
```
Expected: 176 passed.

- [ ] **Step 4: Commit**

```bash
git add tests/test_finding_cycle.py
git commit -m "test: cover the full requirement-edit cascade including the finding"
```

---

## Spec Coverage

| Spec section | Task |
|---|---|
| §4.1 findings directory | 4 (fixtures), 8 (layout) |
| §4.2 finding schema | 3, 7 |
| §4.3 disposition not status | 3, 9 |
| §4.4 history | 3, 7 |
| §4.5 traces_to edge | 2, 12 |
| §4.6 unresolved-finding, finding-unfounded | 4 |
| §4.6 undeclared-state | 5 |
| §5.1 raiser/decider/editor | 9, 10 |
| §5.2 four closes | 9, 10 |
| §5.3 worked cycle | 12 |
| §5.4 convergence rule | 6, 8, 9, 10 |
| §5.5 phase-boundary ritual | 8, 11 |
| §6.1 signoff | 3, 7 |
| §6.2 ownership | 8, 9, 10 |
| §6.3 return contract | 9, 10 |
| §6.4 mockup gate | 5, 10, 11 |
| §7 engine changes | 1, 2, 3, 4, 5, 6 |
| §8 state model | 8 |
| §11 testing | 1–6, 12 |

**Deliberately not implemented:** `deferred-with-live-consumers` (§9.1),
multi-target findings (§9.2), `baselined` semantics (§9.5).
