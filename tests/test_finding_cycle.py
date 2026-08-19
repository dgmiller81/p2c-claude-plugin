from __future__ import annotations

import shutil

import pytest
import yaml

from tracelib.graph import build_graph
from tracelib.hashing import normative_hash
from tracelib.sidecar import load_workspace
from tracelib.staleness import apply_status, detect


@pytest.fixture
def cycle_ws(tmp_path, fixtures_root):
    ws = tmp_path / "ws"
    shutil.copytree(fixtures_root / "finding-open", ws)
    # Sign off every sidecar so the cascade has something to strip.
    for rel in (
        "03-design/mockups/SCR-004.md",
        "04-architecture/components/ARC-002.md",
        "findings/FND-001.md",
    ):
        path = ws / rel
        text = path.read_text(encoding="utf-8")
        head, front, body = text.split("---", 2)
        fm = yaml.safe_load(front)
        fm["signoff"] = {"by": "an-agent", "date": "2026-08-18"}
        path.write_text(
            "---\n"
            + yaml.safe_dump(fm, sort_keys=False, allow_unicode=True).strip()
            + "\n---"
            + body,
            encoding="utf-8",
        )
    return ws


def _front(path):
    return yaml.safe_load(path.read_text(encoding="utf-8").split("---")[1])


def test_clean_before_the_edit(cycle_ws):
    graph = build_graph(load_workspace(cycle_ws))
    assert detect(graph) == []


def test_editing_the_requirement_stales_everything_including_the_finding(cycle_ws):
    fr012 = cycle_ws / "02-requirements" / "register" / "FR-012.md"
    before = normative_hash(build_graph(load_workspace(cycle_ws)).nodes["FR-012"])

    text = fr012.read_text(encoding="utf-8")
    fr012.write_text(
        text.replace(
            "A dispatcher can view and resolve unresolved exceptions.",
            "A dispatcher can view, triage and resolve unresolved exceptions.",
        ),
        encoding="utf-8",
    )

    graph = build_graph(load_workspace(cycle_ws))
    assert normative_hash(graph.nodes["FR-012"]) != before

    entries = detect(graph)
    subjects = {e.subject for e in entries}
    assert {"SCR-004", "ARC-002", "FND-001"} <= subjects
    assert all(
        e.signoff_voided
        for e in entries
        if e.subject in {"SCR-004", "ARC-002", "FND-001"}
    )

    apply_status(entries, graph)

    for rel in (
        "03-design/mockups/SCR-004.md",
        "04-architecture/components/ARC-002.md",
        "findings/FND-001.md",
    ):
        fm = _front(cycle_ws / rel)
        assert fm["status"] == "stale", rel
        assert "signoff" not in fm, rel
