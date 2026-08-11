from __future__ import annotations

from pathlib import Path

from tracelib.schema import validate, validate_all
from tracelib.sidecar import Sidecar


def make(fm: dict, body: str = "body", path: Path = Path("x.md")) -> Sidecar:
    return Sidecar(path=path, frontmatter=fm, body=body)


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


def test_screen_with_empty_traces_to_passes_schema():
    fm = {
        "id": "SCR-004",
        "type": "screen",
        "title": "Queue",
        "status": "draft",
        "traces_to": [],
        "states": {"default": "SCR-004.html"},
    }
    assert validate(make(fm)) == []


def test_screen_missing_traces_to_key_is_an_error():
    fm = {
        "id": "SCR-004",
        "type": "screen",
        "title": "Queue",
        "status": "draft",
        "states": {"default": "SCR-004.html"},
    }
    assert any(e.field_name == "traces_to" for e in validate(make(fm)))


def test_empty_title_is_an_error():
    fm = dict(VALID_REQ, title="")
    assert any(e.field_name == "title" for e in validate(make(fm)))


def test_duplicate_id_error_names_every_offending_path():
    a = make(VALID_REQ, path=Path("a.md"))
    b = make(dict(VALID_REQ), path=Path("b.md"))
    errors = validate_all([a, b])
    paths = {e.path.name for e in errors}
    assert {"a.md", "b.md"} <= paths
