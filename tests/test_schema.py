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


VALID_SCREEN = {
    "id": "SCR-004",
    "type": "screen",
    "title": "Queue",
    "status": "draft",
    "traces_to": ["FR-012"],
    "states": {"default": "SCR-004.html"},
}


def test_numeric_source_hash_is_rejected():
    # This is what YAML produces from an unquoted `000000` in frontmatter:
    # the leading-zero all-octal scalar is parsed as int 0, silently
    # dropping the padding. Schema validation must catch this before it
    # reaches staleness detection.
    fm = dict(VALID_SCREEN, source_hash={"FR-012": 0})
    errors = validate(make(fm))
    assert any(e.field_name == "source_hash" for e in errors)


def test_wrong_length_source_hash_is_rejected():
    fm = dict(VALID_SCREEN, source_hash={"FR-012": "abc"})
    errors = validate(make(fm))
    assert any(e.field_name == "source_hash" for e in errors)


def test_uppercase_source_hash_is_rejected():
    # normative_hash() emits lowercase hex; an uppercase recorded value
    # would never match and would produce false staleness.
    fm = dict(VALID_SCREEN, source_hash={"FR-012": "A3F9C1"})
    errors = validate(make(fm))
    assert any(e.field_name == "source_hash" for e in errors)


def test_non_mapping_states_is_a_schema_error():
    # `states: [SCR-004.html]` is present and non-empty, so the presence
    # check passes it -- and then stages._check_design_stage does
    # `sorted(states.items())` and raises AttributeError. The traceback
    # exits 1, indistinguishable from "gaps found", and dies before
    # write_all, leaving a previous run's "No gaps found" gaps.md in place.
    fm = dict(VALID_SCREEN, states=["SCR-004.html"])
    errors = validate(make(fm))
    assert any(e.field_name == "states" for e in errors)
    assert any("mapping" in e.message.lower() for e in errors if e.field_name == "states")


def test_non_mapping_states_does_not_crash_the_design_stage():
    from tracelib.graph import build_graph
    from tracelib.stages import check

    sc = make(dict(VALID_SCREEN, states=["SCR-004.html"]))
    # Must return gaps rather than raising AttributeError.
    check(build_graph([sc]), "design", Path("."))


def test_valid_source_hash_passes():
    fm = dict(VALID_SCREEN, source_hash={"FR-012": "a3f9c1"})
    assert validate(make(fm)) == []
    fm_empty = dict(VALID_SCREEN, source_hash={})
    assert validate(make(fm_empty)) == []
