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
