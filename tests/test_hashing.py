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


def test_unrecognized_type_uses_the_non_requirement_branch():
    """Unrecognized type falls back to title+body, ignoring requirement fields.

    This characterization test locks in the documented fallback behavior.
    An unrecognized type (e.g., "Requirement" with wrong case) must use the
    non-requirement branch, proving that statement and acceptance_criteria
    are ignored and title+body are normative.
    """
    # Build a sidecar with unrecognized type "Requirement" (wrong case)
    # carrying both statement/acceptance_criteria AND a distinct title/body.
    same_title_and_body = Sidecar(
        Path("X-01.md"),
        {
            "id": "X-01",
            "type": "Requirement",  # Wrong case: not recognized as requirement
            "title": "The Title",
            "statement": "This is the statement field.",
            "acceptance_criteria": ["First criterion", "Second criterion"],
        },
        "The body text."
    )

    # Build an identical non-requirement sidecar with same title/body
    # but different statement and criteria.
    same_title_and_body_different_requirements = Sidecar(
        Path("X-01.md"),
        {
            "id": "X-01",
            "type": "Requirement",  # Same wrong case
            "title": "The Title",
            "statement": "Completely different statement.",
            "acceptance_criteria": ["Different criteria"],
        },
        "The body text."
    )

    # Both should have the same hash because the unrecognized type
    # uses the non-requirement branch, which only cares about title+body.
    assert normative_hash(same_title_and_body) == normative_hash(
        same_title_and_body_different_requirements
    )


def test_reordering_acceptance_criteria_changes_the_hash():
    """Acceptance criteria order is meaningful and must not be sorted away.

    This characterization test prevents a future refactor from "tidying"
    the implementation with sorted() or other ordering changes.
    """
    criteria_ab = req(acceptance_criteria=["a", "b"])
    criteria_ba = req(acceptance_criteria=["b", "a"])

    # Hashes must differ because order matters by design.
    assert normative_hash(criteria_ab) != normative_hash(criteria_ba)
