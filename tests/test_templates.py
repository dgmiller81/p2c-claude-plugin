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
    "finding-template.md": {
        "{{ID}}": "FND-001", "{{TITLE}}": "Example finding",
        "{{REQ_ID}}": "FR-001", "{{AGENT}}": "lead-architect",
        "{{NATURE}}": "infeasible", "{{SEVERITY}}": "blocking",
        "{{RESOLUTION}}": "relax the budget to 500ms",
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

    # 1. Build the mockups the screen declares -- all five canonical states.
    for name in (
        "SCR-001.html",
        "SCR-001-empty.html",
        "SCR-001-loading.html",
        "SCR-001-error.html",
        "SCR-001-success.html",
    ):
        (ws / "03-design" / "mockups" / name).write_text(
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


# The finding is deliberately NOT in E2E_LAYOUT. That dict feeds two tests
# with exact-set assertions on gap kinds and on stale subjects, plus an
# exit-0 assertion, and a finding perturbs all three for reasons unrelated
# to what those tests check.
def _place_finding(ws: Path) -> Path:
    """Fill finding-template.md into the workspace, placeholders intact."""
    text = (TEMPLATES / "finding-template.md").read_text(encoding="utf-8")
    for token, value in SUBSTITUTIONS["finding-template.md"].items():
        text = text.replace(token, value)
    path = ws / "findings" / "FND-001.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _requirement_hash(ws: Path) -> str:
    from tracelib.hashing import normative_hash

    return normative_hash(
        parse_sidecar(ws / "02-requirements" / "register" / "FR-001.md")
    )


def _gap_kinds_for(ws: Path, subject: str) -> set[str]:
    index = json.loads(
        (ws / "traceability" / "index.json").read_text(encoding="utf-8")
    )
    return {g["kind"] for g in index["gaps"] if g["subject"] == subject}


def _stale_subjects(ws: Path) -> set[str]:
    index = json.loads(
        (ws / "traceability" / "index.json").read_text(encoding="utf-8")
    )
    return {e["subject"] for e in index["stale"]}


def test_documented_finding_procedure_produces_a_valid_finding(tmp_path):
    """Do exactly what the finding template and the raiser agents now say.

    Step 3 of "Filing a feasibility finding" tells the raiser to set BOTH
    `source_hash` and `history`'s single entry to the challenged
    requirement's current normative hash. Nothing checked before that this
    procedure yields a working artifact -- and it did not: the shipped
    guidance pointed the raiser at an `unhashed-link` message that can
    never appear, because the template supplies a `source_hash` key and
    that check only inspects keys.
    """
    import trace as trace_cli

    ws = tmp_path / "ws"
    _fill_templates(ws)
    finding = _place_finding(ws)

    current = _requirement_hash(ws)
    finding.write_text(
        finding.read_text(encoding="utf-8").replace("'aaaaaa'", f"'{current}'"),
        encoding="utf-8",
    )
    filled = parse_sidecar(finding)
    assert filled.frontmatter["source_hash"] == {"FR-001": current}
    assert filled.frontmatter["history"] == [current]

    # Exit 1 because the rest of the template workspace is still unfilled
    # (no mockups, placeholder hashes on SCR-001/ARC-001) -- not because of
    # the finding.
    assert trace_cli.main(["--workspace", str(ws), "--stage", "design"]) == 1

    # The finding is baselined against the requirement it challenges, so it
    # is not stale from birth.
    assert "FND-001" not in _stale_subjects(ws)

    kinds = _gap_kinds_for(ws, "FND-001")
    assert "finding-unfounded" not in kinds
    # ...and the finding is visible: disposition is `open`.
    assert "unresolved-finding" in kinds


def test_placeholder_hash_leaves_the_finding_stale_from_birth(tmp_path):
    """The failure mode the template's Notes now warn about."""
    import trace as trace_cli

    ws = tmp_path / "ws"
    _fill_templates(ws)
    _place_finding(ws)  # 'aaaaaa' left exactly as shipped

    trace_cli.main(["--workspace", str(ws), "--stage", "design"])

    assert "FND-001" in _stale_subjects(ws)
    # And no unhashed-link prompt to tell the author what went wrong: the
    # template supplied the KEY, which is all that check looks at.
    assert "unhashed-link" not in _gap_kinds_for(ws, "FND-001")


def test_real_hash_arms_finding_unfounded_and_the_placeholder_disables_it(
    tmp_path,
):
    """Closing a finding without the requirement moving must be caught.

    `finding-unfounded` compares the requirement's current normative hash
    against `history[-1]`. With the real hash recorded, resolving without
    an edit fires it. With `'aaaaaa'` left in place it can never fire --
    which is the whole reason the placeholder guidance mattered.
    """
    import trace as trace_cli

    for placeholder_left, expected in ((False, True), (True, False)):
        ws = tmp_path / ("kept" if placeholder_left else "filled")
        _fill_templates(ws)
        finding = _place_finding(ws)

        text = finding.read_text(encoding="utf-8")
        if not placeholder_left:
            text = text.replace("'aaaaaa'", f"'{_requirement_hash(ws)}'")
        # Close it without anyone editing FR-001.
        text = text.replace("disposition: open", "disposition: resolved")
        finding.write_text(text, encoding="utf-8")

        trace_cli.main(["--workspace", str(ws), "--stage", "design"])
        fired = "finding-unfounded" in _gap_kinds_for(ws, "FND-001")
        assert fired is expected, (
            f"placeholder_left={placeholder_left}: expected "
            f"finding-unfounded fired={expected}"
        )
