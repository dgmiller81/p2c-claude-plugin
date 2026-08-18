from __future__ import annotations

import codecs

import pytest

from tracelib.errors import SidecarError
from tracelib.sidecar import Sidecar, load_workspace, parse_sidecar

SAMPLE = """---
id: FR-012
type: requirement
title: Dispatcher resolves a shipment exception
statement: >
  A dispatcher can view unresolved exceptions.
acceptance_criteria:
  - Assignment removes it from the queue.
status: baselined
---

Prose body for agents.
"""


def test_parse_sidecar_splits_frontmatter_and_body(tmp_path):
    path = tmp_path / "FR-012.md"
    path.write_text(SAMPLE, encoding="utf-8")

    sc = parse_sidecar(path)

    assert sc.id == "FR-012"
    assert sc.type == "requirement"
    assert sc.frontmatter["acceptance_criteria"] == [
        "Assignment removes it from the queue."
    ]
    assert sc.body.strip() == "Prose body for agents."


def test_parse_sidecar_rejects_missing_frontmatter(tmp_path):
    path = tmp_path / "bad.md"
    path.write_text("no frontmatter here", encoding="utf-8")

    with pytest.raises(SidecarError) as exc:
        parse_sidecar(path)

    assert "frontmatter" in str(exc.value).lower()


def test_parse_sidecar_rejects_malformed_yaml(tmp_path):
    path = tmp_path / "bad.md"
    path.write_text("---\nid: [unclosed\n---\nbody\n", encoding="utf-8")

    with pytest.raises(SidecarError):
        parse_sidecar(path)


def test_indented_delimiter_inside_block_scalar_does_not_truncate(tmp_path):
    path = tmp_path / "FR-012.md"
    path.write_text(
        "---\n"
        "id: FR-012\n"
        "type: requirement\n"
        "title: Example\n"
        "statement: >\n"
        "  First line.\n"
        "  ---\n"
        "  Second line.\n"
        "status: draft\n"
        "---\n"
        "\n"
        "Body.\n",
        encoding="utf-8",
    )

    sc = parse_sidecar(path)

    assert sc.frontmatter["status"] == "draft"
    assert "Second line." in sc.frontmatter["statement"]


def test_load_workspace_finds_nested_sidecars_and_skips_generated(tmp_path):
    (tmp_path / "02-requirements" / "register").mkdir(parents=True)
    (tmp_path / "02-requirements" / "register" / "FR-012.md").write_text(
        SAMPLE, encoding="utf-8"
    )
    (tmp_path / "traceability").mkdir()
    (tmp_path / "traceability" / "rtm.md").write_text(SAMPLE, encoding="utf-8")

    found = load_workspace(tmp_path)

    assert [sc.id for sc in found] == ["FR-012"]


def test_prose_file_is_skipped_not_an_error(tmp_path):
    (tmp_path / "prd.md").write_text(
        "# PRD\n\nProblem: dispatchers cannot resolve exceptions.\n",
        encoding="utf-8",
    )
    (tmp_path / "FR-001.md").write_text(
        "---\n"
        "id: FR-001\n"
        "type: requirement\n"
        "kind: functional\n"
        "surface: ui\n"
        "title: Roster sync\n"
        "statement: The roster syncs across devices.\n"
        "acceptance_criteria:\n"
        "  - Sync completes within the budget.\n"
        "priority: must\n"
        "status: draft\n"
        "---\nbody\n",
        encoding="utf-8",
    )
    assert [sc.id for sc in load_workspace(tmp_path)] == ["FR-001"]


def test_malformed_yaml_still_raises(tmp_path):
    (tmp_path / "bad.md").write_text(
        "---\nid: FR-002\n  bad: [unclosed\n---\nbody\n", encoding="utf-8"
    )
    with pytest.raises(SidecarError):
        load_workspace(tmp_path)


def test_unterminated_frontmatter_still_raises(tmp_path):
    (tmp_path / "bad.md").write_text(
        "---\nid: FR-003\ntype: requirement\n", encoding="utf-8"
    )
    with pytest.raises(SidecarError):
        load_workspace(tmp_path)


BOM_SIDECAR = """---
id: FND-001
type: finding
title: The budget cannot be met
traces_to: [FR-012]
history: ['1076e4']
raised_by: lead-architect
nature: infeasible
disposition: open
status: draft
---

Evidence body.
"""


def test_bom_prefixed_sidecar_is_parsed_not_skipped(tmp_path):
    """A UTF-8 BOM must not make a valid sidecar invisible.

    Written with encoding="utf-8-sig" so the file really starts with the
    BOM bytes. Both _has_frontmatter and parse_sidecar read with
    "utf-8-sig", so the delimiter test sees "---" in both places; if they
    disagreed the probe would pass and the parse would raise.
    """
    path = tmp_path / "FND-001.md"
    path.write_text(BOM_SIDECAR, encoding="utf-8-sig")
    assert path.read_bytes()[:3] == codecs.BOM_UTF8

    sc = parse_sidecar(path)
    assert sc.id == "FND-001"
    assert sc.type == "finding"

    # ...and it reaches the graph, rather than being skipped as prose.
    from tracelib.graph import build_graph

    found = load_workspace(tmp_path)
    assert [s.id for s in found] == ["FND-001"]
    assert "FND-001" in build_graph(found).nodes
