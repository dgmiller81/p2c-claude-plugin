# Traceability Core (Increment 1) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `trace.py` and its supporting library so that a p2c workspace of YAML-frontmatter sidecars can be validated, graphed, and reported on — proving no requirement is lost between stages.

**Architecture:** A thin CLI (`trace.py`) over a package of eight single-responsibility modules (`tracelib/`). Sidecars are Markdown files with YAML frontmatter; the library parses them into a bidirectional graph, enforces stage-appropriate chain rules, detects staleness by comparing recorded hashes of upstream normative text, and emits three report files. The checker is read-only by default — mutation of sidecar status is opt-in via `--apply-status`.

**Tech Stack:** Python 3.12 (conda env `312`), PyYAML 6.0.2, pytest 8.3.4. No other third-party dependencies.

## Global Constraints

- Python 3.12; activate with `conda activate 312` before any command.
- PyYAML is the only third-party runtime dependency. `trace.py` must exit 2 with an actionable install message if it is absent.
- All modules start with `from __future__ import annotations`, matching `estimate_cost.py`.
- `main() -> int` returns the exit code; `sys.exit(main())` at the bottom. Matches `estimate_cost.py`.
- Exit codes are contractual: `0` clean, `1` gaps found, `2` schema or parse error.
- ID prefixes are fixed: `BR-###`, `FR-###`, `NFR-###`, `P-##`, `J-##`, `J-##.#`, `SCR-###`, `ARC-###`, `US-###`, `TC-###`.
- Hashes are the first 6 hex characters of SHA-256 over normalized normative text.
- Repo `H:\dev\skills\p2c-claude-plugin`, branch `feature/gated-review-traceability`.
- Library path: `plugins/p2c/skills/p2c/scripts/tracelib/`. CLI: `plugins/p2c/skills/p2c/scripts/trace.py`.
- Tests live at repo root `tests/`. Run with `python -m pytest tests/ -v`.

## Deviation from spec (deliberate)

The spec lists "sign-off voiding" as a `trace.py` responsibility. Writing to sidecars on every gate run would let a checker corrupt state mid-review. This plan makes `trace.py` **read-only by default**: it computes and reports effective status in `gaps.md` and `index.json`, and only writes `status: stale` / strips `signoff` when `--apply-status` is passed. Gate checks use the read-only path.

## Fixture scope

The spec lists 12 fixtures across both increments. Increment 1 owns 8; the other 4 (`dead-link`, `unreachable-page`, `dead-end`, `placeholder-content`) belong to `linkcheck.py` in Increment 2.

Increment 1 fixtures: `clean`, `orphan-requirement`, `orphan-screen`, `broken-chain`, `stale-hash`, `undeclared-state`, `nfr-chain`, `bad-schema`.

## File Structure

| File | Responsibility |
|---|---|
| `scripts/trace.py` | CLI: argparse, stage resolution, orchestration, exit codes |
| `scripts/tracelib/__init__.py` | Package marker, version |
| `scripts/tracelib/errors.py` | `SidecarError`, `SchemaError`, `Gap`, `StaleEntry` dataclasses |
| `scripts/tracelib/ids.py` | ID patterns, type resolution, journey-step parsing |
| `scripts/tracelib/sidecar.py` | Frontmatter parse, `Sidecar` dataclass, workspace load |
| `scripts/tracelib/schema.py` | Per-type required-field validation |
| `scripts/tracelib/hashing.py` | Normative text extraction and hashing |
| `scripts/tracelib/graph.py` | Bidirectional graph, transitive downstream |
| `scripts/tracelib/stages.py` | Staged chain enforcement |
| `scripts/tracelib/staleness.py` | Hash comparison, cascade, sign-off voiding |
| `scripts/tracelib/report.py` | `rtm.md`, `index.json`, `gaps.md` emitters |
| `tests/conftest.py` | `sys.path` wiring, fixture-root helper |
| `tests/fixtures/<name>/` | 8 workspace fixtures |
| `tests/test_*.py` | One test module per library module, plus `test_cli.py` |

---

### Task 1: Package scaffolding, errors, and sidecar parsing

**Files:**
- Create: `plugins/p2c/skills/p2c/scripts/tracelib/__init__.py`
- Create: `plugins/p2c/skills/p2c/scripts/tracelib/errors.py`
- Create: `plugins/p2c/skills/p2c/scripts/tracelib/sidecar.py`
- Create: `tests/conftest.py`
- Create: `tests/test_sidecar.py`
- Create: `pytest.ini`

**Interfaces:**
- Consumes: nothing.
- Produces: `Sidecar(path: Path, frontmatter: dict[str, Any], body: str)` with properties `.id -> str`, `.type -> str`; `parse_sidecar(path: Path) -> Sidecar`; `load_workspace(root: Path) -> list[Sidecar]`; `SidecarError(path: Path, message: str)`.

- [ ] **Step 1: Create pytest config and conftest**

`pytest.ini` at repo root:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
addopts = -q
```

`tests/conftest.py`:

```python
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "plugins" / "p2c" / "skills" / "p2c" / "scripts"

if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


@pytest.fixture
def fixtures_root() -> Path:
    return Path(__file__).resolve().parent / "fixtures"
```

- [ ] **Step 2: Write the failing test**

`tests/test_sidecar.py`:

```python
from __future__ import annotations

import pytest

from tracelib.errors import SidecarError
from tracelib.sidecar import Sidecar, load_workspace, parse_sidecar

SAMPLE = """---
id: FR-012
type: requirement
title: Dispatcher resolves a shipment exception
statement: >
  A dispatcher can view unresolved exceptions.
acceptance_criteria:
  - Assignment removes it from the queue.
status: baselined
---

Prose body for agents.
"""


def test_parse_sidecar_splits_frontmatter_and_body(tmp_path):
    path = tmp_path / "FR-012.md"
    path.write_text(SAMPLE, encoding="utf-8")

    sc = parse_sidecar(path)

    assert sc.id == "FR-012"
    assert sc.type == "requirement"
    assert sc.frontmatter["acceptance_criteria"] == [
        "Assignment removes it from the queue."
    ]
    assert sc.body.strip() == "Prose body for agents."


def test_parse_sidecar_rejects_missing_frontmatter(tmp_path):
    path = tmp_path / "bad.md"
    path.write_text("no frontmatter here", encoding="utf-8")

    with pytest.raises(SidecarError) as exc:
        parse_sidecar(path)

    assert "frontmatter" in str(exc.value).lower()


def test_parse_sidecar_rejects_malformed_yaml(tmp_path):
    path = tmp_path / "bad.md"
    path.write_text("---\nid: [unclosed\n---\nbody\n", encoding="utf-8")

    with pytest.raises(SidecarError):
        parse_sidecar(path)


def test_load_workspace_finds_nested_sidecars_and_skips_generated(tmp_path):
    (tmp_path / "02-requirements" / "register").mkdir(parents=True)
    (tmp_path / "02-requirements" / "register" / "FR-012.md").write_text(
        SAMPLE, encoding="utf-8"
    )
    (tmp_path / "traceability").mkdir()
    (tmp_path / "traceability" / "rtm.md").write_text(SAMPLE, encoding="utf-8")

    found = load_workspace(tmp_path)

    assert [sc.id for sc in found] == ["FR-012"]
```

- [ ] **Step 3: Run test to verify it fails**

```bash
conda activate 312 && cd /h/dev/skills/p2c-claude-plugin && python -m pytest tests/test_sidecar.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'tracelib'`

- [ ] **Step 4: Write the package marker and errors module**

`tracelib/__init__.py`:

```python
"""tracelib — requirements traceability for p2c workspaces."""

from __future__ import annotations

__version__ = "0.1.0"
```

`tracelib/errors.py`:

```python
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


class SidecarError(Exception):
    """Raised when a sidecar file cannot be parsed."""

    def __init__(self, path: Path, message: str) -> None:
        super().__init__(f"{path}: {message}")
        self.path = path
        self.message = message


@dataclass(frozen=True)
class SchemaError:
    path: Path
    subject: str
    field_name: str
    message: str


@dataclass(frozen=True)
class Gap:
    kind: str
    subject: str
    message: str


@dataclass(frozen=True)
class StaleEntry:
    subject: str
    reason: str
    changed_upstream: list[str] = field(default_factory=list)
    signoff_voided: bool = False
```

- [ ] **Step 5: Write the sidecar module**

`tracelib/sidecar.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tracelib.errors import SidecarError

try:
    import yaml
except ModuleNotFoundError as exc:  # pragma: no cover - environment guard
    raise SystemExit(
        "trace.py requires PyYAML. Install it with:  python -m pip install pyyaml"
    ) from exc

DELIMITER = "---"
SKIP_DIRS = {"traceability", "reviews", ".git", "__pycache__"}


@dataclass(frozen=True)
class Sidecar:
    path: Path
    frontmatter: dict[str, Any]
    body: str

    @property
    def id(self) -> str:
        return str(self.frontmatter.get("id", ""))

    @property
    def type(self) -> str:
        return str(self.frontmatter.get("type", ""))


def parse_sidecar(path: Path) -> Sidecar:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    if not lines or lines[0].strip() != DELIMITER:
        raise SidecarError(path, "missing YAML frontmatter opening delimiter")

    try:
        end = next(
            i for i in range(1, len(lines)) if lines[i].strip() == DELIMITER
        )
    except StopIteration:
        raise SidecarError(path, "unterminated YAML frontmatter") from None

    raw = "\n".join(lines[1:end])
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise SidecarError(path, f"malformed YAML frontmatter: {exc}") from exc

    if not isinstance(data, dict):
        raise SidecarError(path, "frontmatter must be a YAML mapping")

    return Sidecar(
        path=path, frontmatter=data, body="\n".join(lines[end + 1 :])
    )


def load_workspace(root: Path) -> list[Sidecar]:
    found: list[Sidecar] = []
    for path in sorted(root.rglob("*.md")):
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        try:
            found.append(parse_sidecar(path))
        except SidecarError:
            raise
    return found
```

- [ ] **Step 6: Run tests to verify they pass**

```bash
python -m pytest tests/test_sidecar.py -v
```

Expected: 4 passed

- [ ] **Step 7: Commit**

```bash
git add pytest.ini tests/conftest.py tests/test_sidecar.py \
  plugins/p2c/skills/p2c/scripts/tracelib/
git commit -m "feat(trace): sidecar frontmatter parsing and workspace loading"
```

---

### Task 2: ID scheme

**Files:**
- Create: `plugins/p2c/skills/p2c/scripts/tracelib/ids.py`
- Create: `tests/test_ids.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `id_type(artifact_id: str) -> str | None`; `is_valid_id(artifact_id: str) -> bool`; `journey_step_parent(step_id: str) -> str | None`; `PREFIX_TO_TYPE: dict[str, str]`.

- [ ] **Step 1: Write the failing test**

`tests/test_ids.py`:

```python
from __future__ import annotations

import pytest

from tracelib.ids import id_type, is_valid_id, journey_step_parent


@pytest.mark.parametrize(
    "artifact_id,expected",
    [
        ("BR-005", "requirement"),
        ("FR-012", "requirement"),
        ("NFR-003", "requirement"),
        ("P-02", "persona"),
        ("J-01", "journey"),
        ("J-01.4", "journey_step"),
        ("SCR-004", "screen"),
        ("ARC-002", "component"),
        ("US-031", "story"),
        ("TC-004", "test"),
    ],
)
def test_id_type_resolves_known_prefixes(artifact_id, expected):
    assert id_type(artifact_id) == expected


@pytest.mark.parametrize(
    "artifact_id",
    ["FR-12", "FR-0012", "XX-001", "P-2", "J-01.", "SCR004", "", "FR-abc"],
)
def test_invalid_ids_rejected(artifact_id):
    assert is_valid_id(artifact_id) is False
    assert id_type(artifact_id) is None


def test_journey_step_parent():
    assert journey_step_parent("J-01.4") == "J-01"
    assert journey_step_parent("J-01") is None
    assert journey_step_parent("SCR-004") is None
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_ids.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'tracelib.ids'`

- [ ] **Step 3: Write the implementation**

`tracelib/ids.py`:

```python
from __future__ import annotations

import re

PREFIX_TO_TYPE: dict[str, str] = {
    "BR": "requirement",
    "FR": "requirement",
    "NFR": "requirement",
    "P": "persona",
    "J": "journey",
    "SCR": "screen",
    "ARC": "component",
    "US": "story",
    "TC": "test",
}

_THREE_DIGIT = re.compile(r"^(BR|FR|NFR|SCR|ARC|US|TC)-\d{3}$")
_TWO_DIGIT = re.compile(r"^(P|J)-\d{2}$")
_JOURNEY_STEP = re.compile(r"^J-\d{2}\.\d+$")


def id_type(artifact_id: str) -> str | None:
    if _JOURNEY_STEP.match(artifact_id):
        return "journey_step"
    match = _THREE_DIGIT.match(artifact_id) or _TWO_DIGIT.match(artifact_id)
    if match:
        return PREFIX_TO_TYPE[match.group(1)]
    return None


def is_valid_id(artifact_id: str) -> bool:
    return id_type(artifact_id) is not None


def journey_step_parent(step_id: str) -> str | None:
    if not _JOURNEY_STEP.match(step_id):
        return None
    return step_id.split(".", 1)[0]
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_ids.py -v
```

Expected: 19 passed (10 + 8 parametrized cases, plus 1)

- [ ] **Step 5: Commit**

```bash
git add plugins/p2c/skills/p2c/scripts/tracelib/ids.py tests/test_ids.py
git commit -m "feat(trace): ID scheme validation and type resolution"
```

---

### Task 3: Schema validation

**Files:**
- Create: `plugins/p2c/skills/p2c/scripts/tracelib/schema.py`
- Create: `tests/test_schema.py`

**Interfaces:**
- Consumes: `Sidecar` (Task 1), `is_valid_id`/`id_type` (Task 2), `SchemaError` (Task 1).
- Produces: `validate(sc: Sidecar) -> list[SchemaError]`; `validate_all(sidecars: list[Sidecar]) -> list[SchemaError]`.

- [ ] **Step 1: Write the failing test**

`tests/test_schema.py`:

```python
from __future__ import annotations

from pathlib import Path

from tracelib.schema import validate, validate_all
from tracelib.sidecar import Sidecar


def make(fm: dict, body: str = "body") -> Sidecar:
    return Sidecar(path=Path("x.md"), frontmatter=fm, body=body)


VALID_REQ = {
    "id": "FR-012",
    "type": "requirement",
    "title": "Resolve exception",
    "status": "baselined",
    "kind": "functional",
    "surface": "ui",
    "statement": "A dispatcher resolves an exception.",
    "acceptance_criteria": ["It leaves the queue."],
    "priority": "must",
}


def test_valid_requirement_has_no_errors():
    assert validate(make(VALID_REQ)) == []


def test_missing_required_common_field_reported():
    fm = dict(VALID_REQ)
    del fm["title"]
    errors = validate(make(fm))
    assert [e.field_name for e in errors] == ["title"]


def test_requirement_missing_kind_reported():
    fm = dict(VALID_REQ)
    del fm["kind"]
    assert any(e.field_name == "kind" for e in validate(make(fm)))


def test_bad_enum_value_reported():
    fm = dict(VALID_REQ, surface="mobile")
    errors = validate(make(fm))
    assert any("surface" == e.field_name for e in errors)


def test_id_must_match_declared_type():
    fm = dict(VALID_REQ, id="SCR-004")
    assert any(e.field_name == "id" for e in validate(make(fm)))


def test_screen_requires_traces_to_and_states():
    fm = {
        "id": "SCR-004",
        "type": "screen",
        "title": "Queue",
        "status": "draft",
        "traces_to": ["FR-012"],
        "states": {"default": "SCR-004.html"},
    }
    assert validate(make(fm)) == []
    del fm["states"]
    assert any(e.field_name == "states" for e in validate(make(fm)))


def test_validate_all_flags_duplicate_ids():
    a = make(VALID_REQ)
    b = make(dict(VALID_REQ))
    errors = validate_all([a, b])
    assert any("duplicate" in e.message.lower() for e in errors)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_schema.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'tracelib.schema'`

- [ ] **Step 3: Write the implementation**

`tracelib/schema.py`:

```python
from __future__ import annotations

from collections import Counter

from tracelib.errors import SchemaError
from tracelib.ids import id_type, is_valid_id
from tracelib.sidecar import Sidecar

REQUIRED_COMMON = ("id", "type", "title", "status")

REQUIRED_BY_TYPE: dict[str, tuple[str, ...]] = {
    "requirement": ("kind", "statement", "acceptance_criteria", "priority"),
    "persona": (),
    "journey": ("persona", "steps"),
    "screen": ("traces_to", "states"),
    "component": ("traces_to",),
    "story": ("traces_to",),
    "test": ("traces_to",),
}

ENUMS: dict[str, tuple[str, ...]] = {
    "kind": ("functional", "non-functional", "business"),
    "surface": ("ui", "system"),
    "priority": ("must", "should", "could", "wont"),
    "status": ("draft", "in-review", "approved", "stale", "baselined"),
}


def validate(sc: Sidecar) -> list[SchemaError]:
    errors: list[SchemaError] = []
    fm = sc.frontmatter
    subject = sc.id or str(sc.path.name)

    for name in REQUIRED_COMMON:
        if not fm.get(name):
            errors.append(
                SchemaError(sc.path, subject, name, f"missing required field '{name}'")
            )

    declared = sc.type
    if sc.id and not is_valid_id(sc.id):
        errors.append(
            SchemaError(sc.path, subject, "id", f"'{sc.id}' is not a well-formed ID")
        )
    elif sc.id and declared and id_type(sc.id) != declared:
        errors.append(
            SchemaError(
                sc.path,
                subject,
                "id",
                f"ID '{sc.id}' implies type '{id_type(sc.id)}' but type is '{declared}'",
            )
        )

    for name in REQUIRED_BY_TYPE.get(declared, ()):
        if not fm.get(name):
            errors.append(
                SchemaError(
                    sc.path, subject, name, f"'{declared}' requires field '{name}'"
                )
            )

    if declared == "requirement" and fm.get("kind") == "functional":
        if not fm.get("surface"):
            errors.append(
                SchemaError(
                    sc.path,
                    subject,
                    "surface",
                    "functional requirements require 'surface' (ui|system)",
                )
            )

    for name, allowed in ENUMS.items():
        value = fm.get(name)
        if value is not None and value not in allowed:
            errors.append(
                SchemaError(
                    sc.path,
                    subject,
                    name,
                    f"'{value}' not one of {', '.join(allowed)}",
                )
            )

    return errors


def validate_all(sidecars: list[Sidecar]) -> list[SchemaError]:
    errors: list[SchemaError] = []
    for sc in sidecars:
        errors.extend(validate(sc))

    counts = Counter(sc.id for sc in sidecars if sc.id)
    for artifact_id, count in sorted(counts.items()):
        if count > 1:
            offender = next(sc for sc in sidecars if sc.id == artifact_id)
            errors.append(
                SchemaError(
                    offender.path,
                    artifact_id,
                    "id",
                    f"duplicate ID '{artifact_id}' used {count} times",
                )
            )
    return errors
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_schema.py -v
```

Expected: 7 passed

- [ ] **Step 5: Commit**

```bash
git add plugins/p2c/skills/p2c/scripts/tracelib/schema.py tests/test_schema.py
git commit -m "feat(trace): per-type sidecar schema validation"
```

---

### Task 4: Normative hashing

**Files:**
- Create: `plugins/p2c/skills/p2c/scripts/tracelib/hashing.py`
- Create: `tests/test_hashing.py`

**Interfaces:**
- Consumes: `Sidecar` (Task 1).
- Produces: `normative_text(sc: Sidecar) -> str`; `normative_hash(sc: Sidecar) -> str` (6 hex chars).

- [ ] **Step 1: Write the failing test**

`tests/test_hashing.py`:

```python
from __future__ import annotations

from pathlib import Path

from tracelib.hashing import normative_hash, normative_text
from tracelib.sidecar import Sidecar


def req(**over) -> Sidecar:
    fm = {
        "id": "FR-012",
        "type": "requirement",
        "title": "Resolve exception",
        "statement": "A dispatcher resolves an exception.",
        "acceptance_criteria": ["It leaves the queue."],
        "priority": "must",
        "source": {"type": "stakeholder", "ref": "Ops lead"},
    }
    fm.update(over)
    return Sidecar(path=Path("FR-012.md"), frontmatter=fm, body="notes")


def test_hash_is_six_hex_chars():
    value = normative_hash(req())
    assert len(value) == 6
    assert all(c in "0123456789abcdef" for c in value)


def test_hash_stable_across_whitespace_only_changes():
    a = req(statement="A dispatcher resolves an exception.")
    b = req(statement="A  dispatcher   resolves\n an exception.")
    assert normative_hash(a) == normative_hash(b)


def test_hash_ignores_non_normative_fields():
    a = req()
    b = req(priority="should", source={"type": "regulator", "ref": "GDPR"})
    assert normative_hash(a) == normative_hash(b)


def test_hash_changes_when_statement_changes():
    assert normative_hash(req()) != normative_hash(req(statement="Different."))


def test_hash_changes_when_acceptance_criteria_change():
    other = req(acceptance_criteria=["It leaves the queue.", "Reason required."])
    assert normative_hash(req()) != normative_hash(other)


def test_non_requirement_hashes_title_and_body():
    a = Sidecar(Path("P-02.md"), {"id": "P-02", "type": "persona",
                                  "title": "Dispatcher"}, "Body one.")
    b = Sidecar(Path("P-02.md"), {"id": "P-02", "type": "persona",
                                  "title": "Dispatcher"}, "Body two.")
    assert normative_hash(a) != normative_hash(b)
    assert "Dispatcher" in normative_text(a)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_hashing.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'tracelib.hashing'`

- [ ] **Step 3: Write the implementation**

`tracelib/hashing.py`:

```python
from __future__ import annotations

import hashlib
import re

from tracelib.sidecar import Sidecar

HASH_LENGTH = 6
_WHITESPACE = re.compile(r"\s+")


def _normalize(text: str) -> str:
    return _WHITESPACE.sub(" ", text).strip()


def normative_text(sc: Sidecar) -> str:
    fm = sc.frontmatter
    if sc.type == "requirement":
        criteria = fm.get("acceptance_criteria") or []
        parts = [str(fm.get("statement", ""))] + [str(c) for c in criteria]
    else:
        parts = [str(fm.get("title", "")), sc.body]
    return "\n".join(_normalize(p) for p in parts)


def normative_hash(sc: Sidecar) -> str:
    digest = hashlib.sha256(normative_text(sc).encode("utf-8")).hexdigest()
    return digest[:HASH_LENGTH]
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_hashing.py -v
```

Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add plugins/p2c/skills/p2c/scripts/tracelib/hashing.py tests/test_hashing.py
git commit -m "feat(trace): normative-field hashing for staleness detection"
```

---

### Task 5: Graph construction

**Files:**
- Create: `plugins/p2c/skills/p2c/scripts/tracelib/graph.py`
- Create: `tests/test_graph.py`

**Interfaces:**
- Consumes: `Sidecar` (Task 1), `journey_step_parent` (Task 2).
- Produces: `Graph` with `.nodes: dict[str, Sidecar]`, `.out: dict[str, set[str]]` (node → upstream it traces to), `.inc: dict[str, set[str]]` (node → downstream that trace to it), `.dangling: list[tuple[str, str]]`; `build_graph(sidecars) -> Graph`; `Graph.downstream(node_id) -> set[str]`; `Graph.by_type(type_name) -> list[Sidecar]`.

Edge direction: a screen's `traces_to: [FR-012]` produces `out["SCR-004"] = {"FR-012"}` and `inc["FR-012"] = {"SCR-004"}`. Staleness cascades along `inc`.

- [ ] **Step 1: Write the failing test**

`tests/test_graph.py`:

```python
from __future__ import annotations

from pathlib import Path

from tracelib.graph import build_graph
from tracelib.sidecar import Sidecar


def sc(fm: dict) -> Sidecar:
    return Sidecar(path=Path(f"{fm['id']}.md"), frontmatter=fm, body="")


def sample() -> list[Sidecar]:
    return [
        sc({"id": "FR-012", "type": "requirement", "title": "R"}),
        sc({"id": "P-02", "type": "persona", "title": "P"}),
        sc({"id": "J-01", "type": "journey", "title": "J", "persona": "P-02",
            "steps": [{"id": "J-01.4", "label": "Resolve", "screen": "SCR-004"}]}),
        sc({"id": "SCR-004", "type": "screen", "title": "S",
            "traces_to": ["FR-012"], "personas": ["P-02"],
            "journey_steps": ["J-01.4"], "states": {"default": "SCR-004.html"}}),
        sc({"id": "ARC-002", "type": "component", "title": "C",
            "traces_to": ["SCR-004"]}),
    ]


def test_nodes_indexed_by_id():
    g = build_graph(sample())
    assert set(g.nodes) >= {"FR-012", "P-02", "J-01", "SCR-004", "ARC-002"}


def test_journey_steps_become_nodes():
    g = build_graph(sample())
    assert "J-01.4" in g.nodes
    assert g.out["J-01.4"] == {"J-01", "SCR-004"}


def test_edges_are_bidirectional():
    g = build_graph(sample())
    assert "FR-012" in g.out["SCR-004"]
    assert "SCR-004" in g.inc["FR-012"]


def test_screen_links_persona_and_journey_step():
    g = build_graph(sample())
    assert {"P-02", "J-01.4"} <= g.out["SCR-004"]


def test_downstream_is_transitive():
    g = build_graph(sample())
    assert {"SCR-004", "ARC-002"} <= g.downstream("FR-012")


def test_downstream_survives_cycles():
    nodes = [
        sc({"id": "FR-001", "type": "requirement", "title": "A",
            "traces_to": ["FR-002"]}),
        sc({"id": "FR-002", "type": "requirement", "title": "B",
            "traces_to": ["FR-001"]}),
    ]
    g = build_graph(nodes)
    # In a cycle each node is downstream of itself; the assertion proves the
    # traversal terminates rather than recursing forever.
    assert g.downstream("FR-001") == {"FR-001", "FR-002"}


def test_dangling_references_recorded():
    nodes = [
        sc({"id": "SCR-004", "type": "screen", "title": "S",
            "traces_to": ["FR-999"], "states": {"default": "x.html"}})
    ]
    g = build_graph(nodes)
    assert ("SCR-004", "FR-999") in g.dangling


def test_by_type_filters():
    g = build_graph(sample())
    assert [s.id for s in g.by_type("screen")] == ["SCR-004"]
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_graph.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'tracelib.graph'`

- [ ] **Step 3: Write the implementation**

`tracelib/graph.py`:

```python
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from tracelib.ids import journey_step_parent
from tracelib.sidecar import Sidecar

LINK_FIELDS = ("traces_to", "personas", "journey_steps")


@dataclass
class Graph:
    nodes: dict[str, Sidecar] = field(default_factory=dict)
    out: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))
    inc: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))
    dangling: list[tuple[str, str]] = field(default_factory=list)

    def downstream(self, node_id: str) -> set[str]:
        seen: set[str] = set()
        stack = list(self.inc.get(node_id, set()))
        while stack:
            current = stack.pop()
            if current in seen:
                continue
            seen.add(current)
            stack.extend(self.inc.get(current, set()))
        return seen

    def by_type(self, type_name: str) -> list[Sidecar]:
        return [
            sc for sc in self.nodes.values() if sc.type == type_name
        ]


def _synthesize_journey_steps(sc: Sidecar) -> list[Sidecar]:
    steps = sc.frontmatter.get("steps") or []
    synthesized: list[Sidecar] = []
    for step in steps:
        if not isinstance(step, dict) or not step.get("id"):
            continue
        fm = {
            "id": step["id"],
            "type": "journey_step",
            "title": step.get("label", step["id"]),
            "status": sc.frontmatter.get("status", "draft"),
            "traces_to": [sc.id] + ([step["screen"]] if step.get("screen") else []),
        }
        synthesized.append(Sidecar(path=sc.path, frontmatter=fm, body=""))
    return synthesized


def build_graph(sidecars: list[Sidecar]) -> Graph:
    graph = Graph()

    expanded: list[Sidecar] = []
    for sc in sidecars:
        expanded.append(sc)
        if sc.type == "journey":
            expanded.extend(_synthesize_journey_steps(sc))

    for sc in expanded:
        if sc.id:
            graph.nodes.setdefault(sc.id, sc)

    for sc in expanded:
        if not sc.id:
            continue
        targets: set[str] = set()
        for name in LINK_FIELDS:
            value = sc.frontmatter.get(name) or []
            if isinstance(value, str):
                value = [value]
            targets.update(str(v) for v in value)

        parent = journey_step_parent(sc.id)
        if parent:
            targets.add(parent)

        for target in sorted(targets):
            if target not in graph.nodes:
                graph.dangling.append((sc.id, target))
                continue
            graph.out[sc.id].add(target)
            graph.inc[target].add(sc.id)

    return graph
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_graph.py -v
```

Expected: 8 passed

- [ ] **Step 5: Commit**

```bash
git add plugins/p2c/skills/p2c/scripts/tracelib/graph.py tests/test_graph.py
git commit -m "feat(trace): bidirectional traceability graph with transitive downstream"
```

---

### Task 6: Staged chain enforcement

**Files:**
- Create: `plugins/p2c/skills/p2c/scripts/tracelib/stages.py`
- Create: `tests/test_stages.py`
- Create: `tests/fixtures/clean/`, `tests/fixtures/orphan-requirement/`, `tests/fixtures/orphan-screen/`, `tests/fixtures/broken-chain/`, `tests/fixtures/undeclared-state/`, `tests/fixtures/nfr-chain/`

**Interfaces:**
- Consumes: `Graph` (Task 5), `Gap` (Task 1).
- Produces: `STAGES: tuple[str, ...]`; `check(graph: Graph, stage: str, workspace_root: Path) -> list[Gap]`.

Gap kinds: `dangling-ref`, `undecomposed-br`, `orphan-requirement`, `orphan-artifact`, `broken-chain`, `missing-state`.

- [ ] **Step 1: Build the `clean` fixture**

```bash
mkdir -p tests/fixtures/clean/02-requirements/register
mkdir -p tests/fixtures/clean/03-design/personas
mkdir -p tests/fixtures/clean/03-design/journeys
mkdir -p tests/fixtures/clean/03-design/mockups
mkdir -p tests/fixtures/clean/04-architecture/components
```

`tests/fixtures/clean/02-requirements/register/FR-012.md`:

```markdown
---
id: FR-012
type: requirement
kind: functional
surface: ui
title: Dispatcher resolves a shipment exception
statement: A dispatcher can view and resolve unresolved exceptions.
acceptance_criteria:
  - Assignment removes the exception from the unassigned queue.
priority: must
status: baselined
---

Normative requirement body.
```

`tests/fixtures/clean/03-design/personas/P-02.md`:

```markdown
---
id: P-02
type: persona
title: Dispatcher
status: approved
---

Manages exceptions across a regional fleet.
```

`tests/fixtures/clean/03-design/journeys/J-01.md`:

```markdown
---
id: J-01
type: journey
title: Resolve an exception
persona: P-02
status: approved
steps:
  - id: J-01.4
    label: Open the exception queue
    screen: SCR-004
---

Journey body.
```

`tests/fixtures/clean/03-design/mockups/SCR-004.md`:

```markdown
---
id: SCR-004
type: screen
title: Shipment Exceptions Queue
status: approved
traces_to: [FR-012]
personas: [P-02]
journey_steps: [J-01.4]
mockup: SCR-004.html
states:
  default: SCR-004.html
terminal: false
source_hash: {}
---

Screen body for agents.
```

Create the referenced HTML so state checks pass:

```bash
echo '<html><body>Queue</body></html>' > tests/fixtures/clean/03-design/mockups/SCR-004.html
```

`tests/fixtures/clean/04-architecture/components/ARC-002.md`:

```markdown
---
id: ARC-002
type: component
title: Exception service
status: approved
traces_to: [FR-012, SCR-004]
---

Component body.
```

- [ ] **Step 2: Build the five failure fixtures**

Each starts as a copy of `clean` with one defect.

```bash
for f in orphan-requirement orphan-screen broken-chain undeclared-state nfr-chain; do
  cp -r tests/fixtures/clean "tests/fixtures/$f"
done
```

`orphan-requirement` — add a UI requirement no screen serves:

```bash
cat > tests/fixtures/orphan-requirement/02-requirements/register/FR-014.md <<'EOF'
---
id: FR-014
type: requirement
kind: functional
surface: ui
title: Bulk reassign exceptions
statement: A dispatcher can reassign many exceptions at once.
acceptance_criteria:
  - Selecting rows enables a bulk reassign action.
priority: must
status: baselined
---

Nothing traces to this.
EOF
```

`orphan-screen` — add a screen tracing to nothing:

```bash
cat > tests/fixtures/orphan-screen/03-design/mockups/SCR-009.md <<'EOF'
---
id: SCR-009
type: screen
title: Unrequested settings page
status: draft
traces_to: []
personas: [P-02]
journey_steps: [J-01.4]
mockup: SCR-009.html
states:
  default: SCR-009.html
terminal: false
---

Scope creep.
EOF
echo '<html><body>Settings</body></html>' > tests/fixtures/orphan-screen/03-design/mockups/SCR-009.html
```

`broken-chain` — strip the persona link from the screen:

```bash
python - <<'EOF'
from pathlib import Path
p = Path("tests/fixtures/broken-chain/03-design/mockups/SCR-004.md")
p.write_text(p.read_text(encoding="utf-8").replace("personas: [P-02]\n", ""),
             encoding="utf-8")
EOF
```

`undeclared-state` — declare an error state whose file is absent:

```bash
python - <<'EOF'
from pathlib import Path
p = Path("tests/fixtures/undeclared-state/03-design/mockups/SCR-004.md")
p.write_text(
    p.read_text(encoding="utf-8").replace(
        "  default: SCR-004.html\n",
        "  default: SCR-004.html\n  error: SCR-004-error.html\n",
    ),
    encoding="utf-8",
)
EOF
```

`nfr-chain` — an NFR served by a component and a test, with no screen:

```bash
cat > tests/fixtures/nfr-chain/02-requirements/register/NFR-003.md <<'EOF'
---
id: NFR-003
type: requirement
kind: non-functional
title: Queue loads within two seconds
statement: The exception queue renders within 2s at p95.
acceptance_criteria:
  - p95 render time under 2000ms with 10k rows.
priority: must
status: baselined
---

Performance requirement.
EOF
mkdir -p tests/fixtures/nfr-chain/06-test-and-harden
cat > tests/fixtures/nfr-chain/06-test-and-harden/TC-004.md <<'EOF'
---
id: TC-004
type: test
title: Queue render performance
status: approved
traces_to: [NFR-003]
---

Load test.
EOF
python - <<'EOF'
from pathlib import Path
p = Path("tests/fixtures/nfr-chain/04-architecture/components/ARC-002.md")
p.write_text(p.read_text(encoding="utf-8").replace(
    "traces_to: [FR-012, SCR-004]", "traces_to: [FR-012, SCR-004, NFR-003]"),
    encoding="utf-8")
EOF
```

- [ ] **Step 3: Write the failing test**

`tests/test_stages.py`:

```python
from __future__ import annotations

from tracelib.graph import build_graph
from tracelib.sidecar import load_workspace
from tracelib.stages import check


def gaps_for(fixtures_root, name, stage):
    root = fixtures_root / name
    graph = build_graph(load_workspace(root))
    return check(graph, stage, root)


def test_clean_fixture_passes_pre_build_stages(fixtures_root):
    # `build` is excluded deliberately: the clean fixture has no stories yet,
    # which test_build_stage_requires_a_story asserts separately.
    for stage in ("requirements", "design", "handoff"):
        assert gaps_for(fixtures_root, "clean", stage) == []


def test_orphan_requirement_detected_at_design(fixtures_root):
    gaps = gaps_for(fixtures_root, "orphan-requirement", "design")
    assert any(g.kind == "orphan-requirement" and g.subject == "FR-014"
               for g in gaps)


def test_orphan_requirement_not_flagged_at_requirements_stage(fixtures_root):
    gaps = gaps_for(fixtures_root, "orphan-requirement", "requirements")
    assert all(g.kind != "orphan-requirement" for g in gaps)


def test_orphan_screen_detected(fixtures_root):
    gaps = gaps_for(fixtures_root, "orphan-screen", "design")
    assert any(g.kind == "orphan-artifact" and g.subject == "SCR-009"
               for g in gaps)


def test_broken_chain_detected_when_screen_has_no_persona(fixtures_root):
    gaps = gaps_for(fixtures_root, "broken-chain", "design")
    assert any(g.kind == "broken-chain" and g.subject == "SCR-004"
               for g in gaps)


def test_missing_state_file_detected(fixtures_root):
    gaps = gaps_for(fixtures_root, "undeclared-state", "design")
    assert any(g.kind == "missing-state" and "error" in g.message
               for g in gaps)


def test_nfr_passes_design_without_a_screen(fixtures_root):
    gaps = gaps_for(fixtures_root, "nfr-chain", "design")
    assert all(g.subject != "NFR-003" for g in gaps)


def test_nfr_satisfies_handoff_via_component_and_test(fixtures_root):
    gaps = gaps_for(fixtures_root, "nfr-chain", "handoff")
    assert all(g.subject != "NFR-003" for g in gaps)


def test_build_stage_requires_a_story(fixtures_root):
    gaps = gaps_for(fixtures_root, "clean", "build")
    assert any(g.kind == "broken-chain" and g.subject == "FR-012"
               for g in gaps)
```

- [ ] **Step 4: Run test to verify it fails**

```bash
python -m pytest tests/test_stages.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'tracelib.stages'`

- [ ] **Step 5: Write the implementation**

`tracelib/stages.py`:

```python
from __future__ import annotations

from pathlib import Path

from tracelib.errors import Gap
from tracelib.graph import Graph

STAGES: tuple[str, ...] = ("requirements", "design", "handoff", "build")

_MOCKUP_DIR = Path("03-design") / "mockups"


def _stage_index(stage: str) -> int:
    if stage not in STAGES:
        raise ValueError(f"unknown stage '{stage}'; expected one of {STAGES}")
    return STAGES.index(stage)


def _requirements(graph: Graph) -> list:
    return [sc for sc in graph.by_type("requirement")]


def _consumers_of_type(graph: Graph, req_id: str, type_name: str) -> list[str]:
    return [
        node_id
        for node_id in graph.downstream(req_id)
        if graph.nodes[node_id].type == type_name
    ]


def _check_requirements_stage(graph: Graph) -> list[Gap]:
    gaps: list[Gap] = []

    for source, target in graph.dangling:
        gaps.append(
            Gap("dangling-ref", source, f"references unknown artifact '{target}'")
        )

    for req in _requirements(graph):
        if req.frontmatter.get("kind") != "business":
            continue
        children = [
            node_id
            for node_id in graph.inc.get(req.id, set())
            if graph.nodes[node_id].type == "requirement"
        ]
        if not children:
            gaps.append(
                Gap(
                    "undecomposed-br",
                    req.id,
                    "business requirement decomposes into no FR or NFR",
                )
            )
    return gaps


def _check_design_stage(graph: Graph, root: Path) -> list[Gap]:
    gaps: list[Gap] = []

    for req in _requirements(graph):
        fm = req.frontmatter
        if fm.get("kind") != "functional" or fm.get("surface") != "ui":
            continue
        screens = _consumers_of_type(graph, req.id, "screen")
        if not screens:
            gaps.append(
                Gap(
                    "orphan-requirement",
                    req.id,
                    "UI requirement is not served by any screen",
                )
            )

    for screen in graph.by_type("screen"):
        fm = screen.frontmatter
        if not fm.get("traces_to"):
            gaps.append(
                Gap(
                    "orphan-artifact",
                    screen.id,
                    "screen traces to no requirement (scope creep)",
                )
            )
        if not fm.get("personas"):
            gaps.append(
                Gap("broken-chain", screen.id, "screen declares no persona")
            )
        if not fm.get("journey_steps"):
            gaps.append(
                Gap("broken-chain", screen.id, "screen declares no journey step")
            )

        states = fm.get("states") or {}
        for state_name, filename in sorted(states.items()):
            if not (root / _MOCKUP_DIR / str(filename)).is_file():
                gaps.append(
                    Gap(
                        "missing-state",
                        screen.id,
                        f"declared state '{state_name}' file '{filename}' not found",
                    )
                )

    for type_name, label in (("persona", "persona"), ("journey", "journey map")):
        for node in graph.by_type(type_name):
            if not graph.inc.get(node.id):
                gaps.append(
                    Gap("orphan-artifact", node.id, f"{label} is referenced by nothing")
                )

    return gaps


def _check_handoff_stage(graph: Graph) -> list[Gap]:
    gaps: list[Gap] = []
    for req in _requirements(graph):
        if req.frontmatter.get("kind") == "business":
            continue
        if not _consumers_of_type(graph, req.id, "component"):
            gaps.append(
                Gap("broken-chain", req.id, "no architecture component owns this")
            )
        headless = (
            req.frontmatter.get("kind") == "non-functional"
            or req.frontmatter.get("surface") == "system"
        )
        if headless and not _consumers_of_type(graph, req.id, "test"):
            gaps.append(Gap("broken-chain", req.id, "no test asserts this"))
    return gaps


def _check_build_stage(graph: Graph) -> list[Gap]:
    gaps: list[Gap] = []
    for req in _requirements(graph):
        if req.frontmatter.get("kind") == "business":
            continue
        if not _consumers_of_type(graph, req.id, "story"):
            gaps.append(Gap("broken-chain", req.id, "no story implements this"))
    return gaps


def check(graph: Graph, stage: str, workspace_root: Path) -> list[Gap]:
    index = _stage_index(stage)
    gaps = _check_requirements_stage(graph)
    if index >= STAGES.index("design"):
        gaps.extend(_check_design_stage(graph, workspace_root))
    if index >= STAGES.index("handoff"):
        gaps.extend(_check_handoff_stage(graph))
    if index >= STAGES.index("build"):
        gaps.extend(_check_build_stage(graph))
    return gaps
```

- [ ] **Step 6: Run tests to verify they pass**

```bash
python -m pytest tests/test_stages.py -v
```

Expected: 9 passed

- [ ] **Step 7: Commit**

```bash
git add plugins/p2c/skills/p2c/scripts/tracelib/stages.py tests/test_stages.py \
  tests/fixtures/
git commit -m "feat(trace): staged chain enforcement with six workspace fixtures"
```

---

### Task 7: Staleness cascade and sign-off voiding

**Files:**
- Create: `plugins/p2c/skills/p2c/scripts/tracelib/staleness.py`
- Create: `tests/test_staleness.py`
- Create: `tests/fixtures/stale-hash/`

**Interfaces:**
- Consumes: `Graph` (Task 5), `normative_hash` (Task 4), `StaleEntry` (Task 1).
- Produces: `detect(graph: Graph) -> list[StaleEntry]`; `apply_status(entries, graph) -> list[Path]`.

- [ ] **Step 1: Build the `stale-hash` fixture**

```bash
cp -r tests/fixtures/clean tests/fixtures/stale-hash
```

Give `SCR-004` a sign-off and a stale hash, then change the requirement:

```bash
python - <<'EOF'
from pathlib import Path

screen = Path("tests/fixtures/stale-hash/03-design/mockups/SCR-004.md")
screen.write_text(
    screen.read_text(encoding="utf-8")
    .replace("source_hash: {}", "source_hash: {FR-012: 000000}")
    .replace(
        "terminal: false",
        "terminal: false\nsignoff: {by: user, date: 2026-08-10, gate: gate2}",
    ),
    encoding="utf-8",
)

req = Path("tests/fixtures/stale-hash/02-requirements/register/FR-012.md")
req.write_text(
    req.read_text(encoding="utf-8").replace(
        "statement: A dispatcher can view and resolve unresolved exceptions.",
        "statement: A dispatcher can view, resolve, and escalate exceptions.",
    ),
    encoding="utf-8",
)
EOF
```

- [ ] **Step 2: Write the failing test**

`tests/test_staleness.py`:

```python
from __future__ import annotations

from tracelib.graph import build_graph
from tracelib.sidecar import load_workspace, parse_sidecar
from tracelib.staleness import apply_status, detect


def graph_for(fixtures_root, name):
    root = fixtures_root / name
    return build_graph(load_workspace(root)), root


def test_clean_fixture_has_no_staleness(fixtures_root):
    graph, _ = graph_for(fixtures_root, "clean")
    assert detect(graph) == []


def test_hash_mismatch_marks_direct_consumer_stale(fixtures_root):
    graph, _ = graph_for(fixtures_root, "stale-hash")
    entries = detect(graph)
    direct = [e for e in entries if e.subject == "SCR-004"]
    assert direct
    assert direct[0].changed_upstream == ["FR-012"]
    assert direct[0].signoff_voided is True


def test_staleness_cascades_transitively(fixtures_root):
    graph, _ = graph_for(fixtures_root, "stale-hash")
    subjects = {e.subject for e in detect(graph)}
    assert "ARC-002" in subjects


def test_cascaded_entry_records_transitive_reason(fixtures_root):
    graph, _ = graph_for(fixtures_root, "stale-hash")
    arc = next(e for e in detect(graph) if e.subject == "ARC-002")
    assert arc.reason == "transitive"


def test_signoff_not_voided_when_absent(fixtures_root):
    graph, _ = graph_for(fixtures_root, "stale-hash")
    arc = next(e for e in detect(graph) if e.subject == "ARC-002")
    assert arc.signoff_voided is False


def test_detect_is_read_only(fixtures_root):
    root = fixtures_root / "stale-hash"
    before = (root / "03-design" / "mockups" / "SCR-004.md").read_text(
        encoding="utf-8"
    )
    graph, _ = graph_for(fixtures_root, "stale-hash")
    detect(graph)
    after = (root / "03-design" / "mockups" / "SCR-004.md").read_text(
        encoding="utf-8"
    )
    assert before == after


def test_apply_status_writes_stale_and_strips_signoff(tmp_path, fixtures_root):
    import shutil

    root = tmp_path / "ws"
    shutil.copytree(fixtures_root / "stale-hash", root)
    graph = build_graph(load_workspace(root))

    written = apply_status(detect(graph), graph)

    screen = parse_sidecar(root / "03-design" / "mockups" / "SCR-004.md")
    assert screen.frontmatter["status"] == "stale"
    assert "signoff" not in screen.frontmatter
    assert any(p.name == "SCR-004.md" for p in written)
```

- [ ] **Step 3: Run test to verify it fails**

```bash
python -m pytest tests/test_staleness.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'tracelib.staleness'`

- [ ] **Step 4: Write the implementation**

`tracelib/staleness.py`:

```python
from __future__ import annotations

from pathlib import Path

import yaml

from tracelib.errors import StaleEntry
from tracelib.graph import Graph
from tracelib.hashing import normative_hash


def detect(graph: Graph) -> list[StaleEntry]:
    direct: dict[str, list[str]] = {}

    for node_id, sc in graph.nodes.items():
        recorded = sc.frontmatter.get("source_hash") or {}
        if not isinstance(recorded, dict):
            continue
        changed: list[str] = []
        for upstream_id, expected in recorded.items():
            upstream = graph.nodes.get(str(upstream_id))
            if upstream is None:
                continue
            if normative_hash(upstream) != str(expected):
                changed.append(str(upstream_id))
        if changed:
            direct[node_id] = sorted(changed)

    entries: list[StaleEntry] = []
    seen: set[str] = set()

    for node_id in sorted(direct):
        entries.append(
            StaleEntry(
                subject=node_id,
                reason="upstream-changed",
                changed_upstream=direct[node_id],
                signoff_voided=bool(graph.nodes[node_id].frontmatter.get("signoff")),
            )
        )
        seen.add(node_id)

    for node_id in sorted(direct):
        for affected in sorted(graph.downstream(node_id)):
            if affected in seen:
                continue
            seen.add(affected)
            entries.append(
                StaleEntry(
                    subject=affected,
                    reason="transitive",
                    changed_upstream=direct[node_id],
                    signoff_voided=bool(
                        graph.nodes[affected].frontmatter.get("signoff")
                    ),
                )
            )

    return entries


def apply_status(entries: list[StaleEntry], graph: Graph) -> list[Path]:
    written: list[Path] = []
    for entry in entries:
        sc = graph.nodes.get(entry.subject)
        if sc is None:
            continue
        updated = dict(sc.frontmatter)
        updated["status"] = "stale"
        updated.pop("signoff", None)

        front = yaml.safe_dump(updated, sort_keys=False, allow_unicode=True).strip()
        sc.path.write_text(
            f"---\n{front}\n---\n{sc.body}", encoding="utf-8"
        )
        written.append(sc.path)
    return written
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
python -m pytest tests/test_staleness.py -v
```

Expected: 7 passed

- [ ] **Step 6: Commit**

```bash
git add plugins/p2c/skills/p2c/scripts/tracelib/staleness.py \
  tests/test_staleness.py tests/fixtures/stale-hash/
git commit -m "feat(trace): staleness cascade with opt-in sign-off voiding"
```

---

### Task 8: Report emitters

**Files:**
- Create: `plugins/p2c/skills/p2c/scripts/tracelib/report.py`
- Create: `tests/test_report.py`

**Interfaces:**
- Consumes: `Graph` (Task 5), `Gap` (Task 1), `StaleEntry` (Task 1).
- Produces: `write_rtm(graph, gaps, stale, out_path) -> None`; `write_index(graph, gaps, stale, out_path) -> None`; `write_gaps(gaps, stale, out_path) -> None`; `write_all(graph, gaps, stale, traceability_dir) -> list[Path]`.

- [ ] **Step 1: Write the failing test**

`tests/test_report.py`:

```python
from __future__ import annotations

import json

from tracelib.errors import Gap, StaleEntry
from tracelib.graph import build_graph
from tracelib.report import write_all
from tracelib.sidecar import load_workspace


def test_write_all_emits_three_files(tmp_path, fixtures_root):
    graph = build_graph(load_workspace(fixtures_root / "clean"))
    out = tmp_path / "traceability"

    written = write_all(graph, [], [], out)

    names = sorted(p.name for p in written)
    assert names == ["gaps.md", "index.json", "rtm.md"]
    assert all(p.is_file() for p in written)


def test_rtm_lists_each_requirement_with_its_chain(tmp_path, fixtures_root):
    graph = build_graph(load_workspace(fixtures_root / "clean"))
    write_all(graph, [], [], tmp_path)

    rtm = (tmp_path / "rtm.md").read_text(encoding="utf-8")
    assert "FR-012" in rtm
    assert "SCR-004" in rtm
    assert "P-02" in rtm


def test_index_json_round_trips(tmp_path, fixtures_root):
    graph = build_graph(load_workspace(fixtures_root / "clean"))
    write_all(graph, [], [], tmp_path)

    data = json.loads((tmp_path / "index.json").read_text(encoding="utf-8"))
    assert data["nodes"]["FR-012"]["type"] == "requirement"
    assert "SCR-004" in data["nodes"]["FR-012"]["traced_by"]
    assert data["summary"]["gaps"] == 0


def test_gaps_md_reports_gaps_and_staleness(tmp_path, fixtures_root):
    graph = build_graph(load_workspace(fixtures_root / "clean"))
    gaps = [Gap("orphan-requirement", "FR-014", "not served by any screen")]
    stale = [
        StaleEntry("SCR-004", "upstream-changed", ["FR-012"], signoff_voided=True)
    ]

    write_all(graph, gaps, stale, tmp_path)
    text = (tmp_path / "gaps.md").read_text(encoding="utf-8")

    assert "FR-014" in text
    assert "not served by any screen" in text
    assert "SCR-004" in text
    assert "sign-off voided" in text.lower()


def test_gaps_md_states_clean_when_empty(tmp_path, fixtures_root):
    graph = build_graph(load_workspace(fixtures_root / "clean"))
    write_all(graph, [], [], tmp_path)
    assert "No gaps" in (tmp_path / "gaps.md").read_text(encoding="utf-8")
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_report.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'tracelib.report'`

- [ ] **Step 3: Write the implementation**

`tracelib/report.py`:

```python
from __future__ import annotations

import json
from pathlib import Path

from tracelib.errors import Gap, StaleEntry
from tracelib.graph import Graph


def _chain_for(graph: Graph, req_id: str) -> dict[str, list[str]]:
    chain: dict[str, list[str]] = {
        "persona": [],
        "journey_step": [],
        "screen": [],
        "component": [],
        "story": [],
        "test": [],
    }
    for node_id in sorted(graph.downstream(req_id)):
        node_type = graph.nodes[node_id].type
        if node_type in chain:
            chain[node_type].append(node_id)
    screens = chain["screen"]
    for screen_id in screens:
        fm = graph.nodes[screen_id].frontmatter
        for persona in fm.get("personas") or []:
            if persona not in chain["persona"]:
                chain["persona"].append(str(persona))
        for step in fm.get("journey_steps") or []:
            if step not in chain["journey_step"]:
                chain["journey_step"].append(str(step))
    return chain


def write_rtm(
    graph: Graph, gaps: list[Gap], stale: list[StaleEntry], out_path: Path
) -> None:
    stale_subjects = {e.subject for e in stale}
    gap_subjects = {g.subject for g in gaps}

    lines = [
        "# Requirements Traceability Matrix",
        "",
        "| Req | Kind | Surface | Personas | Journey steps | Screens | Components | Stories | Tests | Status |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]

    for req in sorted(graph.by_type("requirement"), key=lambda s: s.id):
        chain = _chain_for(graph, req.id)
        if req.id in stale_subjects:
            status = "STALE"
        elif req.id in gap_subjects:
            status = "GAP"
        else:
            status = "ok"
        lines.append(
            "| {id} | {kind} | {surface} | {p} | {j} | {s} | {c} | {u} | {t} | {st} |".format(
                id=req.id,
                kind=req.frontmatter.get("kind", ""),
                surface=req.frontmatter.get("surface", "—"),
                p=", ".join(chain["persona"]) or "—",
                j=", ".join(chain["journey_step"]) or "—",
                s=", ".join(chain["screen"]) or "—",
                c=", ".join(chain["component"]) or "—",
                u=", ".join(chain["story"]) or "—",
                t=", ".join(chain["test"]) or "—",
                st=status,
            )
        )

    lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")


def write_index(
    graph: Graph, gaps: list[Gap], stale: list[StaleEntry], out_path: Path
) -> None:
    stale_by_subject = {e.subject: e for e in stale}
    nodes: dict[str, dict] = {}

    for node_id, sc in sorted(graph.nodes.items()):
        entry = stale_by_subject.get(node_id)
        nodes[node_id] = {
            "type": sc.type,
            "title": sc.frontmatter.get("title", ""),
            "path": str(sc.path),
            "declared_status": sc.frontmatter.get("status", ""),
            "effective_status": "stale" if entry else sc.frontmatter.get("status", ""),
            "traces_to": sorted(graph.out.get(node_id, set())),
            # Direct incoming edges only. `Graph.downstream()` is transitive —
            # the names are deliberately different to keep that distinction.
            "traced_by": sorted(graph.inc.get(node_id, set())),
        }

    payload = {
        "nodes": nodes,
        "gaps": [
            {"kind": g.kind, "subject": g.subject, "message": g.message} for g in gaps
        ],
        "stale": [
            {
                "subject": e.subject,
                "reason": e.reason,
                "changed_upstream": e.changed_upstream,
                "signoff_voided": e.signoff_voided,
            }
            for e in stale
        ],
        "summary": {
            "nodes": len(nodes),
            "gaps": len(gaps),
            "stale": len(stale),
            "dangling": len(graph.dangling),
        },
    }
    out_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def write_gaps(gaps: list[Gap], stale: list[StaleEntry], out_path: Path) -> None:
    lines = ["# Traceability gaps", ""]

    if not gaps:
        lines += ["## Gaps", "", "No gaps found.", ""]
    else:
        lines += ["## Gaps", "", "| Kind | Subject | Detail |", "|---|---|---|"]
        for gap in sorted(gaps, key=lambda g: (g.kind, g.subject)):
            lines.append(f"| {gap.kind} | {gap.subject} | {gap.message} |")
        lines.append("")

    if not stale:
        lines += ["## Staleness", "", "No stale artifacts.", ""]
    else:
        lines += [
            "## Staleness",
            "",
            "| Artifact | Reason | Changed upstream | Sign-off |",
            "|---|---|---|---|",
        ]
        for entry in sorted(stale, key=lambda e: e.subject):
            signoff = "sign-off voided" if entry.signoff_voided else "—"
            lines.append(
                f"| {entry.subject} | {entry.reason} | "
                f"{', '.join(entry.changed_upstream) or '—'} | {signoff} |"
            )
        lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")


def write_all(
    graph: Graph,
    gaps: list[Gap],
    stale: list[StaleEntry],
    traceability_dir: Path,
) -> list[Path]:
    traceability_dir.mkdir(parents=True, exist_ok=True)
    rtm = traceability_dir / "rtm.md"
    index = traceability_dir / "index.json"
    gaps_path = traceability_dir / "gaps.md"

    write_rtm(graph, gaps, stale, rtm)
    write_index(graph, gaps, stale, index)
    write_gaps(gaps, stale, gaps_path)
    return [rtm, index, gaps_path]
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_report.py -v
```

Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add plugins/p2c/skills/p2c/scripts/tracelib/report.py tests/test_report.py
git commit -m "feat(trace): rtm.md, index.json, and gaps.md emitters"
```

---

### Task 9: CLI wiring and end-to-end fixtures

**Files:**
- Create: `plugins/p2c/skills/p2c/scripts/trace.py`
- Create: `tests/test_cli.py`
- Create: `tests/fixtures/bad-schema/`

**Interfaces:**
- Consumes: everything from Tasks 1–8.
- Produces: `main(argv: list[str] | None = None) -> int`; `resolve_stage(workspace: Path, requested: str | None) -> str`.

Stage default: read `config.json` `gates`, pick the stage matching the highest signed gate (`gate1` → `design`, `gate2` → `handoff`, `gate3` → `build`); with no signed gates or no config, default `requirements`.

- [ ] **Step 1: Build the `bad-schema` fixture**

```bash
cp -r tests/fixtures/clean tests/fixtures/bad-schema
python - <<'EOF'
from pathlib import Path
p = Path("tests/fixtures/bad-schema/02-requirements/register/FR-012.md")
p.write_text(p.read_text(encoding="utf-8").replace(
    "title: Dispatcher resolves a shipment exception\n", ""), encoding="utf-8")
EOF
```

- [ ] **Step 2: Write the failing test**

`tests/test_cli.py`:

```python
from __future__ import annotations

import json
import shutil

import pytest

import trace as trace_cli


@pytest.fixture
def workspace(tmp_path, fixtures_root):
    def _make(name: str):
        dest = tmp_path / name
        shutil.copytree(fixtures_root / name, dest)
        return dest

    return _make


def test_clean_workspace_exits_zero(workspace, capsys):
    ws = workspace("clean")
    assert trace_cli.main(["--workspace", str(ws), "--stage", "design"]) == 0


def test_clean_workspace_writes_reports(workspace):
    ws = workspace("clean")
    trace_cli.main(["--workspace", str(ws), "--stage", "design"])
    for name in ("rtm.md", "index.json", "gaps.md"):
        assert (ws / "traceability" / name).is_file()


def test_orphan_requirement_exits_one(workspace):
    ws = workspace("orphan-requirement")
    assert trace_cli.main(["--workspace", str(ws), "--stage", "design"]) == 1


def test_orphan_requirement_named_in_output(workspace, capsys):
    ws = workspace("orphan-requirement")
    trace_cli.main(["--workspace", str(ws), "--stage", "design"])
    assert "FR-014" in capsys.readouterr().out


def test_bad_schema_exits_two(workspace):
    ws = workspace("bad-schema")
    assert trace_cli.main(["--workspace", str(ws), "--stage", "requirements"]) == 2


def test_unparseable_sidecar_exits_two(workspace):
    ws = workspace("clean")
    (ws / "02-requirements" / "register" / "FR-013.md").write_text(
        "no frontmatter", encoding="utf-8"
    )
    assert trace_cli.main(["--workspace", str(ws), "--stage", "requirements"]) == 2


def test_stale_hash_exits_one_and_reports(workspace):
    ws = workspace("stale-hash")
    code = trace_cli.main(["--workspace", str(ws), "--stage", "design"])
    gaps = (ws / "traceability" / "gaps.md").read_text(encoding="utf-8")
    assert code == 1
    assert "SCR-004" in gaps


def test_apply_status_flag_mutates_sidecars(workspace):
    ws = workspace("stale-hash")
    trace_cli.main(["--workspace", str(ws), "--stage", "design", "--apply-status"])
    text = (ws / "03-design" / "mockups" / "SCR-004.md").read_text(encoding="utf-8")
    assert "status: stale" in text
    assert "signoff" not in text


def test_stage_defaults_from_signed_gates(workspace):
    ws = workspace("clean")
    (ws / "config.json").write_text(
        json.dumps({"gates": {"gate1": {"status": "signed"}}}), encoding="utf-8"
    )
    assert trace_cli.resolve_stage(ws, None) == "design"


def test_stage_defaults_to_requirements_without_config(workspace):
    ws = workspace("clean")
    assert trace_cli.resolve_stage(ws, None) == "requirements"


def test_explicit_stage_overrides_config(workspace):
    ws = workspace("clean")
    (ws / "config.json").write_text(
        json.dumps({"gates": {"gate3": {"status": "signed"}}}), encoding="utf-8"
    )
    assert trace_cli.resolve_stage(ws, "requirements") == "requirements"


def test_missing_workspace_exits_two(tmp_path):
    assert trace_cli.main(["--workspace", str(tmp_path / "nope")]) == 2
```

- [ ] **Step 3: Run test to verify it fails**

```bash
python -m pytest tests/test_cli.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'trace'` resolving to the library, or `AttributeError: module 'trace' has no attribute 'main'`

> Note: Python ships a stdlib module named `trace`. `conftest.py` inserts the scripts directory at `sys.path[0]`, so ours shadows it. Keep that `insert(0, ...)` — appending would import the stdlib module instead.

- [ ] **Step 4: Write the implementation**

`plugins/p2c/skills/p2c/scripts/trace.py`:

```python
#!/usr/bin/env python3
"""
trace.py — Requirements traceability checker for p2c workspaces.

Reads:
  - Every `*.md` sidecar under the workspace (excluding traceability/ and reviews/)
  - `config.json` for signed-gate state, to pick a default stage

Writes:
  - traceability/rtm.md    human-readable matrix
  - traceability/index.json machine-readable graph
  - traceability/gaps.md   orphans, broken chains, staleness

Usage:
  python trace.py --workspace p2c-workspace
  python trace.py --workspace p2c-workspace --stage design
  python trace.py --workspace p2c-workspace --stage design --apply-status

Exit codes:
  0  clean
  1  gaps or staleness found
  2  schema or parse error
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from tracelib.errors import SidecarError
from tracelib.graph import build_graph
from tracelib.report import write_all
from tracelib.schema import validate_all
from tracelib.sidecar import load_workspace
from tracelib.stages import STAGES, check
from tracelib.staleness import apply_status, detect

GATE_TO_STAGE = {"gate1": "design", "gate2": "handoff", "gate3": "build"}


def resolve_stage(workspace: Path, requested: str | None) -> str:
    if requested:
        return requested

    config_path = workspace / "config.json"
    if not config_path.is_file():
        return "requirements"

    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return "requirements"

    stage = "requirements"
    for gate, mapped in GATE_TO_STAGE.items():
        gate_state = (config.get("gates") or {}).get(gate) or {}
        if gate_state.get("status") == "signed":
            if STAGES.index(mapped) > STAGES.index(stage):
                stage = mapped
    return stage


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate requirements traceability in a p2c workspace."
    )
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--stage", choices=STAGES, default=None)
    parser.add_argument(
        "--apply-status",
        action="store_true",
        help="write status: stale and strip signoff on affected sidecars",
    )
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    workspace: Path = args.workspace
    if not workspace.is_dir():
        print(f"error: workspace not found: {workspace}", file=sys.stderr)
        return 2

    try:
        sidecars = load_workspace(workspace)
    except SidecarError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    schema_errors = validate_all(sidecars)
    if schema_errors:
        for err in schema_errors:
            print(
                f"schema error: {err.subject} [{err.field_name}] {err.message} "
                f"({err.path})",
                file=sys.stderr,
            )
        return 2

    stage = resolve_stage(workspace, args.stage)
    graph = build_graph(sidecars)
    gaps = check(graph, stage, workspace)
    stale = detect(graph)

    write_all(graph, gaps, stale, workspace / "traceability")

    if args.apply_status and stale:
        for path in apply_status(stale, graph):
            if not args.quiet:
                print(f"marked stale: {path}")

    if not args.quiet:
        print(f"stage: {stage}")
        for gap in sorted(gaps, key=lambda g: (g.kind, g.subject)):
            print(f"gap [{gap.kind}] {gap.subject}: {gap.message}")
        for entry in sorted(stale, key=lambda e: e.subject):
            print(f"stale [{entry.reason}] {entry.subject}")
        print(
            f"{len(gaps)} gap(s), {len(stale)} stale artifact(s) — "
            f"reports in {workspace / 'traceability'}"
        )

    return 1 if (gaps or stale) else 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 5: Run the full suite**

```bash
python -m pytest tests/ -v
```

Expected: all tests pass (12 in `test_cli.py`)

- [ ] **Step 6: Run the CLI against a real fixture to confirm the contract**

```bash
python plugins/p2c/skills/p2c/scripts/trace.py \
  --workspace tests/fixtures/orphan-requirement --stage design; echo "exit=$?"
```

Expected: prints `gap [orphan-requirement] FR-014: ...` and `exit=1`

- [ ] **Step 7: Commit**

```bash
git add plugins/p2c/skills/p2c/scripts/trace.py tests/test_cli.py \
  tests/fixtures/bad-schema/
git commit -m "feat(trace): CLI with staged defaults and contractual exit codes"
```

---

### Task 10: Artifact templates

**Files:**
- Create: `plugins/p2c/skills/p2c/templates/requirement-template.md`
- Create: `plugins/p2c/skills/p2c/templates/persona-template.md`
- Create: `plugins/p2c/skills/p2c/templates/journey-template.md`
- Create: `plugins/p2c/skills/p2c/templates/screen-template.md`
- Create: `plugins/p2c/skills/p2c/templates/component-template.md`
- Create: `tests/test_templates.py`

**Interfaces:**
- Consumes: `parse_sidecar` (Task 1), `validate` (Task 3).
- Produces: five templates that pass schema validation once their `{{PLACEHOLDER}}` tokens are replaced.

- [ ] **Step 1: Write the failing test**

`tests/test_templates.py`:

```python
from __future__ import annotations

import re
from pathlib import Path

import pytest

from tracelib.schema import validate
from tracelib.sidecar import parse_sidecar

# Anchored to the repo root, not the CWD, so the suite passes from any
# working directory.
REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = REPO_ROOT / "plugins" / "p2c" / "skills" / "p2c" / "templates"

SUBSTITUTIONS = {
    "requirement-template.md": {
        "{{ID}}": "FR-001", "{{TITLE}}": "Example requirement",
        "{{KIND}}": "functional", "{{SURFACE}}": "ui",
        "{{STATEMENT}}": "A user can do the thing.",
        "{{CRITERION}}": "The thing is done.",
        "{{PRIORITY}}": "must", "{{SOURCE_TYPE}}": "stakeholder",
        "{{SOURCE_REF}}": "Interview 2026-08-01",
    },
    "persona-template.md": {"{{ID}}": "P-01", "{{TITLE}}": "Example persona"},
    "journey-template.md": {
        "{{ID}}": "J-01", "{{TITLE}}": "Example journey",
        "{{PERSONA_ID}}": "P-01", "{{STEP_ID}}": "J-01.1",
        "{{STEP_LABEL}}": "Open the app", "{{SCREEN_ID}}": "SCR-001",
    },
    "screen-template.md": {
        "{{ID}}": "SCR-001", "{{TITLE}}": "Example screen",
        "{{REQ_ID}}": "FR-001", "{{PERSONA_ID}}": "P-01",
        "{{STEP_ID}}": "J-01.1",
    },
    "component-template.md": {
        "{{ID}}": "ARC-001", "{{TITLE}}": "Example component",
        "{{REQ_ID}}": "FR-001",
    },
}


@pytest.mark.parametrize("name", sorted(SUBSTITUTIONS))
def test_template_exists(name):
    assert (TEMPLATES / name).is_file()


@pytest.mark.parametrize("name", sorted(SUBSTITUTIONS))
def test_filled_template_passes_schema(tmp_path, name):
    text = (TEMPLATES / name).read_text(encoding="utf-8")
    for token, value in SUBSTITUTIONS[name].items():
        text = text.replace(token, value)

    assert not re.search(r"\{\{[A-Z_]+\}\}", text), "unsubstituted token remains"

    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    assert validate(parse_sidecar(path)) == []
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_templates.py -v
```

Expected: FAIL — `assert False` on `test_template_exists`

- [ ] **Step 3: Write the five templates**

`templates/requirement-template.md`:

```markdown
---
id: {{ID}}
type: requirement
kind: {{KIND}}
surface: {{SURFACE}}
title: {{TITLE}}
statement: {{STATEMENT}}
acceptance_criteria:
  - {{CRITERION}}
source: {type: {{SOURCE_TYPE}}, ref: {{SOURCE_REF}}}
priority: {{PRIORITY}}
version: 1
status: draft
---

## Context

Why this requirement exists and what happens without it.

## Notes

Open questions, constraints, and links. Nothing here affects the hash —
only `statement` and `acceptance_criteria` are normative.
```

`templates/persona-template.md`:

```markdown
---
id: {{ID}}
type: persona
title: {{TITLE}}
status: draft
---

## Who they are

Role, context, and the environment they work in.

## Goals

What they are trying to achieve.

## Frustrations

What gets in their way today.

## Scenarios

The situations in which they use this product.
```

`templates/journey-template.md`:

```markdown
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
```

`templates/screen-template.md`:

```markdown
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
```

`templates/component-template.md`:

```markdown
---
id: {{ID}}
type: component
title: {{TITLE}}
traces_to: [{{REQ_ID}}]
status: draft
---

## Responsibility

What this component owns, and what it explicitly does not.

## Interface

Inputs, outputs, and the contract consumers depend on.

## Dependencies

What it calls and what calls it.
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_templates.py -v
```

Expected: 10 passed

- [ ] **Step 5: Run the complete suite**

```bash
python -m pytest tests/ -v
```

Expected: all tests pass, zero failures

- [ ] **Step 6: Commit**

```bash
git add plugins/p2c/skills/p2c/templates/ tests/test_templates.py
git commit -m "feat(trace): artifact templates validated against the sidecar schema"
```

---

## Definition of done

- [ ] `python -m pytest tests/ -v` passes with zero failures
- [ ] `trace.py --workspace tests/fixtures/clean --stage design` exits 0
- [ ] `trace.py --workspace tests/fixtures/orphan-requirement --stage design` exits 1 and names `FR-014`
- [ ] `trace.py --workspace tests/fixtures/bad-schema` exits 2 and names the missing field
- [ ] All 8 Increment-1 fixtures exist and are exercised by tests
- [ ] All five templates pass schema validation when filled

## Self-review notes

**Spec coverage.** Every Increment-1 item in the spec maps to a task: sidecar
schema → Tasks 1/3; ID scheme → Task 2; hashing → Task 4; graph → Task 5;
staged enforcement → Task 6; staleness cascade and sign-off voiding → Task 7;
`rtm.md`/`index.json`/`gaps.md` → Task 8; CLI and exit codes → Task 9;
templates → Task 10; fixtures → Tasks 6, 7, 9.

**Two corrections made while writing.** The stdlib already owns the module name
`trace`, so `conftest.py` must `sys.path.insert(0, ...)` rather than append —
called out in Task 9. And journey steps are declared inline inside a journey's
`steps` list rather than as standalone files, so `build_graph` synthesizes
`journey_step` nodes (Task 5); without that, every `journey_steps: [J-01.4]`
reference on a screen would register as dangling.

**Deferred to Increment 2.** `linkcheck.py` and its four fixtures
(`dead-link`, `unreachable-page`, `dead-end`, `placeholder-content`), the
ProdReq template port, and `index.html` generation.
