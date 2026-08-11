from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from tracelib.schema import validate
from tracelib.sidecar import parse_sidecar

# Anchored to the repo root, not the CWD, so the suite passes from any
# working directory.
REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = REPO_ROOT / "plugins" / "p2c" / "skills" / "p2c" / "templates"

SUBSTITUTIONS = {
    "requirement-template.md": {
        "{{ID}}": "FR-001", "{{TITLE}}": "Example requirement",
        "{{KIND}}": "functional", "{{SURFACE}}": "ui",
        "{{STATEMENT}}": "A user can do the thing.",
        "{{CRITERION}}": "The thing is done.",
        "{{PRIORITY}}": "must", "{{SOURCE_TYPE}}": "stakeholder",
        "{{SOURCE_REF}}": "Interview 2026-08-01",
    },
    "persona-template.md": {"{{ID}}": "P-01", "{{TITLE}}": "Example persona"},
    "journey-template.md": {
        "{{ID}}": "J-01", "{{TITLE}}": "Example journey",
        "{{PERSONA_ID}}": "P-01", "{{STEP_ID}}": "J-01.1",
        "{{STEP_LABEL}}": "Open the app", "{{SCREEN_ID}}": "SCR-001",
    },
    "screen-template.md": {
        "{{ID}}": "SCR-001", "{{TITLE}}": "Example screen",
        "{{REQ_ID}}": "FR-001", "{{PERSONA_ID}}": "P-01",
        "{{STEP_ID}}": "J-01.1",
    },
    "component-template.md": {
        "{{ID}}": "ARC-001", "{{TITLE}}": "Example component",
        "{{REQ_ID}}": "FR-001",
    },
}


@pytest.mark.parametrize("name", sorted(SUBSTITUTIONS))
def test_template_exists(name):
    assert (TEMPLATES / name).is_file()


@pytest.mark.parametrize("name", sorted(SUBSTITUTIONS))
def test_filled_template_passes_schema(tmp_path, name):
    text = (TEMPLATES / name).read_text(encoding="utf-8")
    for token, value in SUBSTITUTIONS[name].items():
        text = text.replace(token, value)

    assert not re.search(r"\{\{[A-Z_]+\}\}", text), "unsubstituted token remains"

    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    assert validate(parse_sidecar(path)) == []


# Where each filled template lands in a workspace, and the cross-consistent
# IDs that make the five of them one coherent chain:
#   FR-001 --served by--> SCR-001 --shown in--> J-01.1 (of J-01, persona P-01)
#   FR-001 --owned by---> ARC-001
E2E_LAYOUT = {
    "requirement-template.md": "02-requirements/register/FR-001.md",
    "persona-template.md": "03-design/personas/P-01.md",
    "journey-template.md": "03-design/journeys/J-01.md",
    "screen-template.md": "03-design/mockups/SCR-001.md",
    "component-template.md": "04-architecture/components/ARC-001.md",
}


def _fill_templates(root: Path) -> None:
    for name, rel in E2E_LAYOUT.items():
        text = (TEMPLATES / name).read_text(encoding="utf-8")
        for token, value in SUBSTITUTIONS[name].items():
            text = text.replace(token, value)
        dest = root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text, encoding="utf-8")


def test_workspace_built_from_templates_reports_exactly_the_authoring_gaps(tmp_path):
    """End-to-end: five shipped templates, one workspace, `--stage design`.

    A workspace built purely from the templates must NOT pass. Two things
    are deliberately left for the author, and both are things the checker
    is supposed to catch:

      1. no mockup HTML exists -- `states.default` names a file the UX
         designer has to build, and no template ships it;
      2. the `source_hash` placeholders are deliberately wrong, so the
         author is forced to fetch the real hashes from trace.py.

    What must NOT appear is any structural break -- a dangling reference, an
    orphan, a broken chain, an unhashed link. Those would mean the shipped
    templates do not wire up to each other.
    """
    import trace as trace_cli

    ws = tmp_path / "ws"
    _fill_templates(ws)

    assert trace_cli.main(["--workspace", str(ws), "--stage", "design"]) == 1

    index = json.loads(
        (ws / "traceability" / "index.json").read_text(encoding="utf-8")
    )
    assert {g["kind"] for g in index["gaps"]} == {"missing-state"}

    stale = {e["subject"]: e["reason"] for e in index["stale"]}
    assert stale["SCR-001"] == "upstream-changed"
    assert stale["ARC-001"] == "upstream-changed"
    # J-01.1 is the synthesized journey step; it is stale transitively
    # through SCR-001 and has no file of its own to repair -- see
    # staleness._is_synthesized.
    assert stale["J-01.1"] == "transitive"
    assert set(stale) == {"SCR-001", "ARC-001", "J-01.1"}


def test_template_workspace_passes_once_the_author_fills_it_in(tmp_path):
    """The same workspace, with only the two author-owned steps done."""
    import trace as trace_cli
    from tracelib.hashing import normative_hash
    from tracelib.sidecar import parse_sidecar

    ws = tmp_path / "ws"
    _fill_templates(ws)

    # 1. Build the mockup the screen declares.
    (ws / "03-design" / "mockups" / "SCR-001.html").write_text(
        "<html><body>Example screen</body></html>", encoding="utf-8"
    )

    # 2. Replace the deliberately-wrong placeholder with the real hash --
    #    exactly the value trace.py's unhashed-link/staleness report prints.
    current = normative_hash(
        parse_sidecar(ws / "02-requirements" / "register" / "FR-001.md")
    )
    for rel in ("03-design/mockups/SCR-001.md", "04-architecture/components/ARC-001.md"):
        path = ws / rel
        path.write_text(
            path.read_text(encoding="utf-8").replace("'aaaaaa'", f"'{current}'"),
            encoding="utf-8",
        )

    assert trace_cli.main(["--workspace", str(ws), "--stage", "design"]) == 0


def test_screen_template_documents_quoted_source_hash():
    text = (TEMPLATES / "screen-template.md").read_text(encoding="utf-8")
    for token, value in SUBSTITUTIONS["screen-template.md"].items():
        text = text.replace(token, value)

    assert "source_hash: {FR-001: 'a3f9c1'}" in text
    assert "quoted" in text.lower()
