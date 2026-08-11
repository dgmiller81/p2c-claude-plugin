from __future__ import annotations

import json
import re
from pathlib import Path

from tracelib.errors import Gap, StaleEntry
from tracelib.graph import Graph, build_graph
from tracelib.report import write_all
from tracelib.sidecar import Sidecar, load_workspace


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


def test_requirement_with_empty_chain_is_unverified_not_ok(tmp_path):
    sc = Sidecar(
        path=Path("REQ-1.md"),
        frontmatter={
            "id": "REQ-1",
            "type": "requirement",
            "kind": "business",
            "surface": "internal",
            "status": "draft",
            "title": "Lonely requirement",
        },
        body="",
    )
    graph = Graph(nodes={"REQ-1": sc})

    write_all(graph, [], [], tmp_path)
    rtm = (tmp_path / "rtm.md").read_text(encoding="utf-8")
    row = next(line for line in rtm.splitlines() if line.startswith("| REQ-1"))

    assert "unverified" in row
    assert "ok" not in row


def test_stale_takes_precedence_over_gap(tmp_path, fixtures_root):
    graph = build_graph(load_workspace(fixtures_root / "clean"))
    gaps = [Gap("orphan-requirement", "FR-012", "flagged as a gap too")]
    stale = [StaleEntry("FR-012", "upstream-changed", [], signoff_voided=False)]

    write_all(graph, gaps, stale, tmp_path)
    rtm = (tmp_path / "rtm.md").read_text(encoding="utf-8")
    row = next(line for line in rtm.splitlines() if line.startswith("| FR-012"))

    assert "STALE" in row
    assert "GAP" not in row


def test_index_paths_are_relative_posix_when_root_given(tmp_path, fixtures_root):
    root = fixtures_root / "clean"
    graph = build_graph(load_workspace(root))

    write_all(graph, [], [], tmp_path, root=root)

    data = json.loads((tmp_path / "index.json").read_text(encoding="utf-8"))
    assert data["nodes"]["SCR-004"]["path"] == "03-design/mockups/SCR-004.md"


def test_index_and_gaps_agree_on_ordering(tmp_path, fixtures_root):
    graph = build_graph(load_workspace(fixtures_root / "clean"))
    gaps = [
        Gap("orphan-requirement", "FR-099", "z message"),
        Gap("dangling-reference", "AAA-001", "a message"),
        Gap("dangling-reference", "BBB-002", "b message"),
    ]

    write_all(graph, gaps, [], tmp_path)

    data = json.loads((tmp_path / "index.json").read_text(encoding="utf-8"))
    index_order = [(g["kind"], g["subject"]) for g in data["gaps"]]

    gaps_md = (tmp_path / "gaps.md").read_text(encoding="utf-8")
    table_rows = [
        line
        for line in gaps_md.splitlines()
        if line.startswith("| ") and "Kind" not in line and "---" not in line
    ]
    md_order = []
    for row in table_rows:
        cells = [c.strip() for c in row.strip("|").split("|")]
        md_order.append((cells[0], cells[1]))

    assert index_order == md_order
    assert index_order == sorted(index_order)


def test_pipe_in_gap_message_does_not_break_the_table(tmp_path, fixtures_root):
    graph = build_graph(load_workspace(fixtures_root / "clean"))
    gaps = [Gap("dangling-reference", "FR-099", "target a | b not found")]

    write_all(graph, gaps, [], tmp_path)
    text = (tmp_path / "gaps.md").read_text(encoding="utf-8")

    row = next(
        line for line in text.splitlines() if line.startswith("| dangling-reference")
    )
    assert "a \\| b" in row

    cells = re.split(r"(?<!\\)\|", row)
    real_cells = [c for c in cells if c.strip() != ""]
    assert len(real_cells) == 3
