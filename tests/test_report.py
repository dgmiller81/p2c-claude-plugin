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


def test_gaps_md_shows_recorded_and_current_hash(tmp_path, fixtures_root):
    graph = build_graph(load_workspace(fixtures_root / "stale-hash"))
    stale = [
        StaleEntry(
            "SCR-004",
            "upstream-changed",
            ["FR-012"],
            signoff_voided=True,
            current_hashes={"FR-012": "957e03"},
        )
    ]

    write_all(graph, [], stale, tmp_path)
    text = (tmp_path / "gaps.md").read_text(encoding="utf-8")

    # "aaaaaa" is the recorded value in the stale-hash fixture's SCR-004
    # source_hash; "957e03" is the current value supplied by the entry.
    assert "aaaaaa" in text
    assert "957e03" in text


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


def test_findings_render_in_gaps_md(tmp_path, fixtures_root):
    graph = build_graph(load_workspace(fixtures_root / "finding-open"))
    write_all(graph, [], [], tmp_path)
    gaps_md = (tmp_path / "gaps.md").read_text(encoding="utf-8")
    assert "## Findings" in gaps_md
    assert "FND-001" in gaps_md
    assert "FR-012" in gaps_md


def test_findings_recorded_in_index(tmp_path, fixtures_root):
    graph = build_graph(load_workspace(fixtures_root / "finding-open"))
    write_all(graph, [], [], tmp_path)
    data = json.loads((tmp_path / "index.json").read_text(encoding="utf-8"))
    entry = data["findings"][0]
    assert entry["id"] == "FND-001"
    assert entry["challenges"] == ["FR-012"]
    assert entry["nature"] == "infeasible"
    assert entry["disposition"] == "open"
    assert entry["iterations"] == 1


def test_no_findings_renders_placeholder(tmp_path, fixtures_root):
    graph = build_graph(load_workspace(fixtures_root / "clean"))
    write_all(graph, [], [], tmp_path)
    gaps_md = (tmp_path / "gaps.md").read_text(encoding="utf-8")
    assert "No findings recorded." in gaps_md


def test_escalation_flag_appears_at_threshold(tmp_path, fixtures_root):
    graph = build_graph(load_workspace(fixtures_root / "finding-open"))
    graph.nodes["FND-001"].frontmatter["history"] = ["1076e4", "aaaaaa", "bbbbbb"]
    write_all(graph, [], [], tmp_path)
    gaps_md = (tmp_path / "gaps.md").read_text(encoding="utf-8")
    assert "escalate" in gaps_md.lower()


def test_findings_render_in_rtm_too(tmp_path, fixtures_root):
    """Spec 7 asks for the findings table in rtm.md as well as gaps.md."""
    graph = build_graph(load_workspace(fixtures_root / "finding-open"))
    write_all(graph, [], [], tmp_path)
    rtm = (tmp_path / "rtm.md").read_text(encoding="utf-8")

    assert "## Findings" in rtm
    row = next(line for line in rtm.splitlines() if line.startswith("| FND-001"))
    assert "FR-012" in row
    assert "infeasible" in row
    assert "open" in row


def test_rtm_findings_placeholder_when_there_are_none(tmp_path, fixtures_root):
    graph = build_graph(load_workspace(fixtures_root / "clean"))
    write_all(graph, [], [], tmp_path)
    assert "No findings recorded." in (tmp_path / "rtm.md").read_text(
        encoding="utf-8"
    )


def test_challenged_requirement_is_not_reported_ok(tmp_path, fixtures_root):
    """An open finding's gap subject is the FND id, not the requirement's,
    so without the CHALLENGED status this row would read `ok` while the
    requirement's feasibility is actively disputed.
    """
    graph = build_graph(load_workspace(fixtures_root / "finding-open"))
    write_all(graph, [], [], tmp_path)
    rtm = (tmp_path / "rtm.md").read_text(encoding="utf-8")

    row = next(line for line in rtm.splitlines() if line.startswith("| FR-012 "))
    assert "CHALLENGED" in row
    assert "CHALLENGED" in rtm.split("Status legend")[1]


def test_resolved_finding_leaves_the_requirement_unchallenged(
    tmp_path, fixtures_root
):
    graph = build_graph(load_workspace(fixtures_root / "finding-resolved"))
    write_all(graph, [], [], tmp_path)
    rtm = (tmp_path / "rtm.md").read_text(encoding="utf-8")

    row = next(line for line in rtm.splitlines() if line.startswith("| FR-012 "))
    assert "CHALLENGED" not in row


def test_accepted_finding_also_challenges(tmp_path, fixtures_root):
    graph = build_graph(load_workspace(fixtures_root / "finding-open"))
    graph.nodes["FND-001"].frontmatter["disposition"] = "accepted"
    write_all(graph, [], [], tmp_path)
    rtm = (tmp_path / "rtm.md").read_text(encoding="utf-8")

    row = next(line for line in rtm.splitlines() if line.startswith("| FR-012 "))
    assert "CHALLENGED" in row


def test_stale_outranks_challenged_which_outranks_gap(tmp_path, fixtures_root):
    graph = build_graph(load_workspace(fixtures_root / "finding-open"))
    gaps = [Gap("orphan-requirement", "FR-012", "also a gap")]

    write_all(graph, gaps, [], tmp_path)
    rtm = (tmp_path / "rtm.md").read_text(encoding="utf-8")
    row = next(line for line in rtm.splitlines() if line.startswith("| FR-012 "))
    assert "CHALLENGED" in row and "GAP" not in row

    stale = [StaleEntry("FR-012", "upstream-changed", [], signoff_voided=False)]
    write_all(graph, gaps, stale, tmp_path)
    rtm = (tmp_path / "rtm.md").read_text(encoding="utf-8")
    row = next(line for line in rtm.splitlines() if line.startswith("| FR-012 "))
    assert "STALE" in row and "CHALLENGED" not in row
