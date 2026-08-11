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
