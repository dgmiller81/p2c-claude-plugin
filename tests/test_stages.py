from __future__ import annotations

import pytest

from tracelib.graph import build_graph
from tracelib.hashing import normative_hash
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
    # The fixture is meant to isolate ONE defect (no persona declared on the
    # screen). P-02 is still reachable through J-01's singular `persona:`
    # field, so it must not also show up as an orphan artifact.
    assert not any(g.kind == "orphan-artifact" and g.subject == "P-02"
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


def test_screen_without_source_hash_for_its_requirement_is_flagged(tmp_path):
    # Staleness detection iterates only what is RECORDED in source_hash, so
    # an artifact that records nothing is permanently immune to it. Without
    # this check, changing what a requirement demands silently leaves every
    # downstream artifact reporting `ok`.
    req = Sidecar(
        path=tmp_path / "FR-012.md",
        frontmatter={
            "id": "FR-012",
            "type": "requirement",
            "kind": "functional",
            "surface": "ui",
            "title": "R",
            "statement": "A dispatcher can view and resolve unresolved exceptions.",
            "acceptance_criteria": ["Assignment removes it from the queue."],
        },
        body="",
    )
    screen = Sidecar(
        path=tmp_path / "SCR-004.md",
        frontmatter={
            "id": "SCR-004",
            "type": "screen",
            "title": "S",
            "traces_to": ["FR-012"],
            "personas": ["P-02"],
            "journey_steps": ["J-01.4"],
            "states": {},
            "source_hash": {},
        },
        body="",
    )
    graph = build_graph([req, screen])
    gaps = check(graph, "design", tmp_path)

    flagged = [g for g in gaps if g.kind == "unhashed-link"]
    assert flagged, "a screen recording no source_hash must be flagged"
    assert flagged[0].subject == "SCR-004"
    assert "FR-012" in flagged[0].message
    # The message must be actionable: it carries the CURRENT hash so the
    # author can paste it straight into source_hash.
    assert normative_hash(req) in flagged[0].message


def test_unhashed_link_not_checked_at_requirements_stage(tmp_path):
    # Screens do not exist at the requirements stage, so the check would be
    # meaningless there.
    screen = Sidecar(
        path=tmp_path / "SCR-004.md",
        frontmatter={
            "id": "SCR-004",
            "type": "screen",
            "title": "S",
            "traces_to": ["FR-012"],
            "states": {},
        },
        body="",
    )
    req = Sidecar(
        path=tmp_path / "FR-012.md",
        frontmatter={"id": "FR-012", "type": "requirement", "title": "R"},
        body="",
    )
    graph = build_graph([req, screen])
    gaps = check(graph, "requirements", tmp_path)
    assert all(g.kind != "unhashed-link" for g in gaps)


def test_recorded_source_hash_satisfies_the_link(tmp_path):
    req = Sidecar(
        path=tmp_path / "FR-012.md",
        frontmatter={
            "id": "FR-012",
            "type": "requirement",
            "title": "R",
            "statement": "A dispatcher resolves an exception.",
            "acceptance_criteria": ["It leaves the queue."],
        },
        body="",
    )
    component = Sidecar(
        path=tmp_path / "ARC-002.md",
        frontmatter={
            "id": "ARC-002",
            "type": "component",
            "title": "C",
            "traces_to": ["FR-012"],
            # Deliberately WRONG value: recording *a* hash is what the
            # unhashed-link check demands. Whether it still matches is
            # staleness's job, not this check's.
            "source_hash": {"FR-012": "aaaaaa"},
        },
        body="",
    )
    graph = build_graph([req, component])
    gaps = check(graph, "design", tmp_path)
    assert all(g.kind != "unhashed-link" for g in gaps)


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


def test_screen_tracing_only_through_a_component_does_not_serve_the_requirement(tmp_path):
    # FR-012 is only reachable from SCR-004 by going through ARC-002 (two
    # hops). No screen names FR-012 directly. `_consumers_of_type` must not
    # count this as "served" -- transitivity is for staleness cascade, not
    # for deciding whether a requirement reached design.
    req = Sidecar(
        path=tmp_path / "FR-012.md",
        frontmatter={
            "id": "FR-012",
            "type": "requirement",
            "kind": "functional",
            "surface": "ui",
            "title": "R",
        },
        body="",
    )
    component = Sidecar(
        path=tmp_path / "ARC-002.md",
        frontmatter={
            "id": "ARC-002",
            "type": "component",
            "title": "C",
            "traces_to": ["FR-012"],
        },
        body="",
    )
    screen = Sidecar(
        path=tmp_path / "SCR-004.md",
        frontmatter={
            "id": "SCR-004",
            "type": "screen",
            "title": "S",
            "traces_to": ["ARC-002"],
        },
        body="",
    )
    graph = build_graph([req, component, screen])
    gaps = check(graph, "design", tmp_path)
    assert any(g.kind == "orphan-requirement" and g.subject == "FR-012" for g in gaps)


def test_absolute_state_path_is_rejected(tmp_path):
    # A state value that is an absolute path makes `root / _MOCKUP_DIR /
    # filename` discard `root` entirely (pathlib behavior when the right
    # operand is absolute). C:/Windows/win.ini genuinely exists on this
    # machine, so an unguarded `.is_file()` check would wrongly pass.
    screen = Sidecar(
        path=tmp_path / "SCR-004.md",
        frontmatter={
            "id": "SCR-004",
            "type": "screen",
            "title": "S",
            "traces_to": ["FR-012"],
            "personas": ["P-02"],
            "journey_steps": ["J-01.4"],
            "states": {"error": "C:/Windows/win.ini"},
        },
        body="",
    )
    graph = build_graph([screen])
    gaps = check(graph, "design", tmp_path)
    assert any(g.kind == "missing-state" and g.subject == "SCR-004" for g in gaps)


def test_parent_traversal_state_path_is_rejected(tmp_path):
    # A state value containing `..` can escape the mockups directory. Plant
    # a real file two levels up from 03-design/mockups (i.e. directly under
    # the workspace root) so an unguarded `.is_file()` check would wrongly
    # resolve and pass.
    secret = tmp_path / "secret.html"
    secret.write_text("<html>leaked</html>", encoding="utf-8")
    screen = Sidecar(
        path=tmp_path / "SCR-004.md",
        frontmatter={
            "id": "SCR-004",
            "type": "screen",
            "title": "S",
            "traces_to": ["FR-012"],
            "personas": ["P-02"],
            "journey_steps": ["J-01.4"],
            "states": {"error": "../../secret.html"},
        },
        body="",
    )
    graph = build_graph([screen])
    gaps = check(graph, "design", tmp_path)
    assert any(g.kind == "missing-state" and g.subject == "SCR-004" for g in gaps)


def _artifact(tmp_path, artifact_id, type_name, traces_to):
    fm = {
        "id": artifact_id,
        "type": type_name,
        "title": "A",
        "status": "draft",
        "traces_to": traces_to,
    }
    if type_name == "screen":
        fm.update(personas=["P-02"], journey_steps=["J-01.4"], states={})
    return Sidecar(path=tmp_path / f"{artifact_id}.md", frontmatter=fm, body="")


def test_component_tracing_to_nothing_is_flagged(tmp_path):
    # schema.MAY_BE_EMPTY deliberately lets `traces_to: []` through for
    # components, stories and tests -- it is a traceability gap, not a
    # structural defect. But stages only ever checked screens, so a
    # component nobody asked for was invisible at every stage.
    component = _artifact(tmp_path, "ARC-002", "component", [])
    gaps = check(build_graph([component]), "handoff", tmp_path)
    flagged = [
        g for g in gaps if g.kind == "orphan-artifact" and g.subject == "ARC-002"
    ]
    assert flagged
    assert "component" in flagged[0].message


def test_component_tracing_to_something_is_not_flagged(tmp_path):
    req = Sidecar(
        path=tmp_path / "FR-012.md",
        frontmatter={"id": "FR-012", "type": "requirement", "title": "R"},
        body="",
    )
    component = _artifact(tmp_path, "ARC-002", "component", ["FR-012"])
    component.frontmatter["source_hash"] = {"FR-012": "aaaaaa"}
    gaps = check(build_graph([req, component]), "handoff", tmp_path)
    assert not any(
        g.kind == "orphan-artifact" and g.subject == "ARC-002" for g in gaps
    )


@pytest.mark.parametrize(
    "artifact_id,type_name", [("US-031", "story"), ("TC-004", "test")]
)
def test_story_and_test_tracing_to_nothing_are_flagged_at_build(
    tmp_path, artifact_id, type_name
):
    node = _artifact(tmp_path, artifact_id, type_name, [])
    gaps = check(build_graph([node]), "build", tmp_path)
    flagged = [
        g
        for g in gaps
        if g.kind == "orphan-artifact" and g.subject == artifact_id
    ]
    assert flagged
    assert type_name in flagged[0].message
    # Not yet checked at handoff -- stories and tests are a build-stage
    # concern.
    earlier = check(build_graph([node]), "handoff", tmp_path)
    assert not any(
        g.kind == "orphan-artifact" and g.subject == artifact_id for g in earlier
    )


def test_journey_step_without_a_screen_is_flagged(tmp_path):
    # The design spec lists "journey step has no screen" as an explicit
    # failure condition of the functional+ui chain. The journey-level check
    # only asks whether SOME step is referenced by SOME screen, so a journey
    # whose remaining steps declare no screen at all sails through.
    persona = Sidecar(
        path=tmp_path / "P-02.md",
        frontmatter={"id": "P-02", "type": "persona", "title": "P"},
        body="",
    )
    journey = Sidecar(
        path=tmp_path / "J-01.md",
        frontmatter={
            "id": "J-01",
            "type": "journey",
            "title": "J",
            "persona": "P-02",
            "steps": [
                {"id": "J-01.4", "label": "Open the queue", "screen": "SCR-004"},
                {"id": "J-01.5", "label": "Assign it"},
                {"id": "J-01.6", "label": "Record a reason"},
            ],
        },
        body="",
    )
    screen = Sidecar(
        path=tmp_path / "SCR-004.md",
        frontmatter={
            "id": "SCR-004",
            "type": "screen",
            "title": "S",
            "traces_to": [],
            "personas": ["P-02"],
            "journey_steps": ["J-01.4"],
            "states": {},
        },
        body="",
    )
    graph = build_graph([persona, journey, screen])
    gaps = check(graph, "design", tmp_path)

    flagged = {g.subject for g in gaps if g.kind == "broken-chain"}
    assert {"J-01.5", "J-01.6"} <= flagged
    # J-01.4 declares screen: SCR-004, so it must NOT be flagged -- this is
    # not a check that fires on every step.
    assert "J-01.4" not in flagged


def test_journey_step_without_a_screen_not_flagged_at_requirements_stage(tmp_path):
    journey = Sidecar(
        path=tmp_path / "J-01.md",
        frontmatter={
            "id": "J-01",
            "type": "journey",
            "title": "J",
            "persona": "P-02",
            "steps": [{"id": "J-01.5", "label": "Assign it"}],
        },
        body="",
    )
    gaps = check(build_graph([journey]), "requirements", tmp_path)
    assert all(g.subject != "J-01.5" for g in gaps)


def test_journey_step_without_an_id_is_flagged(tmp_path):
    # graph._synthesize_journey_steps used to `continue` past any step dict
    # with no `id`, so the step vanished from the graph entirely and no
    # check could ever see it.
    journey = Sidecar(
        path=tmp_path / "J-01.md",
        frontmatter={
            "id": "J-01",
            "type": "journey",
            "title": "J",
            "persona": "P-02",
            "steps": [
                {"id": "J-01.4", "label": "Open the queue", "screen": "SCR-004"},
                {"label": "Forgot the id", "screen": "SCR-004"},
                "not even a mapping",
            ],
        },
        body="",
    )
    gaps = check(build_graph([journey]), "requirements", tmp_path)
    malformed = [g for g in gaps if g.kind == "malformed-step"]
    assert len(malformed) == 2
    assert all(g.subject == "J-01" for g in malformed)
    # The message must locate the offending step for the author.
    assert any("2" in g.message for g in malformed)
    assert any("3" in g.message for g in malformed)


def test_journey_with_no_screen_referencing_its_steps_is_orphaned(tmp_path, fixtures_root):
    # J-01's own synthesized step always creates an inbound edge onto J-01
    # (step --traces_to--> journey), so the old "does anything point at
    # this journey" check can never fire. The real question is whether any
    # SCREEN references one of the journey's steps.
    persona = Sidecar(
        path=tmp_path / "P-02.md",
        frontmatter={"id": "P-02", "type": "persona", "title": "P"},
        body="",
    )
    journey = Sidecar(
        path=tmp_path / "J-01.md",
        frontmatter={
            "id": "J-01",
            "type": "journey",
            "title": "J",
            "persona": "P-02",
            "steps": [{"id": "J-01.4", "label": "Step", "screen": "SCR-004"}],
        },
        body="",
    )
    graph = build_graph([persona, journey])
    gaps = check(graph, "design", tmp_path)
    assert any(g.kind == "orphan-artifact" and g.subject == "J-01" for g in gaps)

    # Not merely inverted: the clean fixture's J-01 IS referenced (SCR-004
    # declares journey_steps: [J-01.4]) and must not be flagged.
    clean_gaps = gaps_for(fixtures_root, "clean", "design")
    assert not any(g.kind == "orphan-artifact" and g.subject == "J-01" for g in clean_gaps)
