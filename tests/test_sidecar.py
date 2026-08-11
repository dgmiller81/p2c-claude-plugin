from __future__ import annotations

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
