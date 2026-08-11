from __future__ import annotations

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


def test_screen_template_documents_quoted_source_hash():
    text = (TEMPLATES / "screen-template.md").read_text(encoding="utf-8")
    for token, value in SUBSTITUTIONS["screen-template.md"].items():
        text = text.replace(token, value)

    assert "source_hash: {FR-001: 'a3f9c1'}" in text
    assert "quoted" in text.lower()
