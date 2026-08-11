from __future__ import annotations

import json
import shutil

import pytest

import trace as trace_cli


@pytest.fixture
def workspace(tmp_path, fixtures_root):
    def _make(name: str):
        dest = tmp_path / name
        shutil.copytree(fixtures_root / name, dest)
        return dest

    return _make


def test_clean_workspace_exits_zero(workspace, capsys):
    ws = workspace("clean")
    assert trace_cli.main(["--workspace", str(ws), "--stage", "design"]) == 0


def test_clean_workspace_writes_reports(workspace):
    ws = workspace("clean")
    trace_cli.main(["--workspace", str(ws), "--stage", "design"])
    for name in ("rtm.md", "index.json", "gaps.md"):
        assert (ws / "traceability" / name).is_file()


def test_clean_workspace_exits_zero_at_handoff(workspace):
    # The fixtures now record a source_hash for every requirement they trace
    # to, so the new unhashed-link check must not fire on them.
    ws = workspace("clean")
    assert trace_cli.main(["--workspace", str(ws), "--stage", "handoff"]) == 0


def test_rewriting_a_requirement_statement_fails_the_gate(workspace):
    # Regression: with source_hash unrecorded, gutting FR-012 used to exit 0
    # with "0 stale artifact(s)" and rtm.md reporting `ok` -- a false PASS
    # that lets an unimplemented requirement reach engineering.
    ws = workspace("clean")
    fr012 = ws / "02-requirements" / "register" / "FR-012.md"
    fr012.write_text(
        fr012.read_text(encoding="utf-8").replace(
            "statement: A dispatcher can view and resolve unresolved exceptions.",
            "statement: The system prints the annual tax ledger in triplicate.",
        ),
        encoding="utf-8",
    )
    assert trace_cli.main(["--workspace", str(ws), "--stage", "handoff"]) == 1


def test_screen_recording_no_source_hash_fails_the_gate(workspace):
    ws = workspace("clean")
    screen = ws / "03-design" / "mockups" / "SCR-004.md"
    screen.write_text(
        screen.read_text(encoding="utf-8").replace(
            "source_hash: {FR-012: '1076e4'}", "source_hash: {}"
        ),
        encoding="utf-8",
    )
    assert trace_cli.main(["--workspace", str(ws), "--stage", "design"]) == 1
    gaps = (ws / "traceability" / "gaps.md").read_text(encoding="utf-8")
    assert "unhashed-link" in gaps
    assert "1076e4" in gaps


def test_orphan_requirement_exits_one(workspace):
    ws = workspace("orphan-requirement")
    assert trace_cli.main(["--workspace", str(ws), "--stage", "design"]) == 1


def test_orphan_requirement_named_in_output(workspace, capsys):
    ws = workspace("orphan-requirement")
    trace_cli.main(["--workspace", str(ws), "--stage", "design"])
    assert "FR-014" in capsys.readouterr().out


def test_bad_schema_exits_two(workspace):
    ws = workspace("bad-schema")
    assert trace_cli.main(["--workspace", str(ws), "--stage", "requirements"]) == 2


def test_unparseable_sidecar_exits_two(workspace):
    ws = workspace("clean")
    (ws / "02-requirements" / "register" / "FR-013.md").write_text(
        "no frontmatter", encoding="utf-8"
    )
    assert trace_cli.main(["--workspace", str(ws), "--stage", "requirements"]) == 2


def test_stale_hash_exits_one_and_reports(workspace):
    ws = workspace("stale-hash")
    code = trace_cli.main(["--workspace", str(ws), "--stage", "design"])
    gaps = (ws / "traceability" / "gaps.md").read_text(encoding="utf-8")
    assert code == 1
    assert "SCR-004" in gaps


def test_apply_status_flag_mutates_sidecars(workspace):
    ws = workspace("stale-hash")
    trace_cli.main(["--workspace", str(ws), "--stage", "design", "--apply-status"])
    text = (ws / "03-design" / "mockups" / "SCR-004.md").read_text(encoding="utf-8")
    assert "status: stale" in text
    assert "signoff" not in text


def test_stage_defaults_from_signed_gates(workspace):
    ws = workspace("clean")
    (ws / "config.json").write_text(
        json.dumps({"gates": {"gate1": {"status": "signed"}}}), encoding="utf-8"
    )
    assert trace_cli.resolve_stage(ws, None) == "design"


def test_stage_defaults_to_requirements_without_config(workspace):
    ws = workspace("clean")
    assert trace_cli.resolve_stage(ws, None) == "requirements"


def test_explicit_stage_overrides_config(workspace):
    ws = workspace("clean")
    (ws / "config.json").write_text(
        json.dumps({"gates": {"gate3": {"status": "signed"}}}), encoding="utf-8"
    )
    assert trace_cli.resolve_stage(ws, "requirements") == "requirements"


def test_missing_workspace_exits_two(tmp_path):
    assert trace_cli.main(["--workspace", str(tmp_path / "nope")]) == 2


def test_orphan_screen_exits_one_not_two(workspace):
    ws = workspace("orphan-screen")
    code = trace_cli.main(["--workspace", str(ws), "--stage", "design"])
    gaps = (ws / "traceability" / "gaps.md").read_text(encoding="utf-8")
    assert code == 1, "empty traces_to is a gap, not a schema error"
    assert "SCR-009" in gaps


def test_index_json_uses_relative_posix_paths(workspace):
    import json

    ws = workspace("clean")
    trace_cli.main(["--workspace", str(ws), "--stage", "design"])
    data = json.loads((ws / "traceability" / "index.json").read_text(encoding="utf-8"))
    paths = [n["path"] for n in data["nodes"].values()]
    assert paths, "expected at least one node"
    assert all("\\" not in p for p in paths)
    assert "02-requirements/register/FR-012.md" in paths


@pytest.mark.parametrize("raw", ["[]", "42", "null", '"x"'])
def test_non_object_config_does_not_crash(workspace, raw):
    ws = workspace("clean")
    (ws / "config.json").write_text(raw, encoding="utf-8")
    assert trace_cli.resolve_stage(ws, None) == "requirements"
    code = trace_cli.main(["--workspace", str(ws)])
    assert code in {0, 1, 2}


def test_non_dict_gates_does_not_crash(workspace):
    # `{"gates": []}` did not exercise the guard: the pre-fix code did
    # `gates or {}`, and an empty list is already falsy, so it passed with
    # or without the isinstance check. A non-empty non-mapping is what
    # actually reaches `.get()` and raises AttributeError.
    ws = workspace("clean")
    (ws / "config.json").write_text(
        json.dumps({"gates": "oops"}), encoding="utf-8"
    )
    assert trace_cli.resolve_stage(ws, None) == "requirements"


def test_schema_error_overwrites_gaps_report(workspace):
    ws = workspace("clean")
    code1 = trace_cli.main(["--workspace", str(ws), "--stage", "design"])
    assert code1 == 0
    gaps_before = (ws / "traceability" / "gaps.md").read_text(encoding="utf-8")
    assert "No gaps found" in gaps_before

    fr012 = ws / "02-requirements" / "register" / "FR-012.md"
    fr012.write_text(
        fr012.read_text(encoding="utf-8").replace(
            "title: Dispatcher resolves a shipment exception\n", ""
        ),
        encoding="utf-8",
    )

    code2 = trace_cli.main(["--workspace", str(ws), "--stage", "design"])
    assert code2 == 2

    gaps_after = (ws / "traceability" / "gaps.md").read_text(encoding="utf-8")
    assert "No gaps found" not in gaps_after
    assert "title" in gaps_after
