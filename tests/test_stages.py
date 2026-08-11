from __future__ import annotations

from tracelib.graph import build_graph
from tracelib.sidecar import Sidecar, load_workspace
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


def test_duplicate_journey_step_reported_at_requirements_stage(tmp_path):
    journey_a = Sidecar(
        path=tmp_path / "J-01.md",
        frontmatter={
            "id": "J-01",
            "type": "journey",
            "title": "Resolve an exception",
            "persona": "P-02",
            "status": "approved",
            "steps": [
                {"id": "J-01.4", "label": "Open the exception queue", "screen": "SCR-004"},
            ],
        },
        body="",
    )
    journey_b = Sidecar(
        path=tmp_path / "J-02.md",
        frontmatter={
            "id": "J-02",
            "type": "journey",
            "title": "A different journey that copy-pasted a step id",
            "persona": "P-02",
            "status": "approved",
            "steps": [
                {"id": "J-01.4", "label": "Duplicated step id", "screen": "SCR-004"},
            ],
        },
        body="",
    )
    graph = build_graph([journey_a, journey_b])
    gaps = check(graph, "requirements", tmp_path)
    assert any(g.kind == "duplicate-step" and g.subject == "J-01.4" for g in gaps)
