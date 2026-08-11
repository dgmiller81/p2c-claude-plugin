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
