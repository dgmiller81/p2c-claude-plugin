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
