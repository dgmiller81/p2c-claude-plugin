#!/usr/bin/env python3
"""
trace.py — Requirements traceability checker for p2c workspaces.

Reads:
  - Every `*.md` sidecar under the workspace (excluding traceability/ and reviews/)
  - `config.json` for signed-gate state, to pick a default stage

Writes:
  - traceability/rtm.md    human-readable matrix
  - traceability/index.json machine-readable graph
  - traceability/gaps.md   orphans, broken chains, staleness

Usage:
  python trace.py --workspace p2c-workspace
  python trace.py --workspace p2c-workspace --stage design
  python trace.py --workspace p2c-workspace --stage design --apply-status

Exit codes:
  0  clean
  1  gaps or staleness found
  2  schema or parse error
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from tracelib.errors import SidecarError
from tracelib.graph import build_graph
from tracelib.report import write_all
from tracelib.schema import validate_all
from tracelib.sidecar import load_workspace
from tracelib.stages import STAGES, check
from tracelib.staleness import apply_status, detect

GATE_TO_STAGE = {"gate1": "design", "gate2": "handoff", "gate3": "build"}


def _write_validation_failure(workspace: Path, heading: str, errors: list[str]) -> None:
    """Overwrite traceability/gaps.md with a validation-failure report.

    Runs on the two exit-2 paths that happen *before* gap analysis
    (parse errors, schema errors). Without this, a reviewer who opens
    gaps.md instead of checking the exit code sees whatever a previous
    successful run left behind — e.g. "No gaps found" for a workspace
    that is currently broken. Deliberately does NOT touch rtm.md or
    index.json: fabricating a matrix from unvalidated data would be
    worse than leaving stale-but-honest ones in place.
    """
    traceability_dir = workspace / "traceability"
    traceability_dir.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Traceability gaps",
        "",
        f"## {heading}",
        "",
        "Validation failed before gap analysis could run. The requirements "
        "matrix (rtm.md) and index (index.json) were NOT regenerated for "
        "this run — they reflect a previous run (or nothing, if there was "
        "none) and must not be trusted until validation passes.",
        "",
    ]
    if errors:
        lines.append("## Errors")
        lines.append("")
        for err in errors:
            lines.append(f"- {err}")
        lines.append("")

    (traceability_dir / "gaps.md").write_text("\n".join(lines), encoding="utf-8")


def resolve_stage(workspace: Path, requested: str | None) -> str:
    if requested:
        return requested

    config_path = workspace / "config.json"
    if not config_path.is_file():
        return "requirements"

    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return "requirements"

    # A syntactically valid JSON document need not be an object — `[]`,
    # `42`, `null`, `"x"` all parse cleanly but have no `.get()`. Treat any
    # of those exactly like a malformed config rather than letting
    # `.get("gates")` raise and take the whole gate down with a traceback.
    if not isinstance(config, dict):
        return "requirements"

    gates = config.get("gates")
    if not isinstance(gates, dict):
        gates = {}

    stage = "requirements"
    for gate, mapped in GATE_TO_STAGE.items():
        gate_state = gates.get(gate)
        if not isinstance(gate_state, dict):
            gate_state = {}
        if gate_state.get("status") == "signed":
            if STAGES.index(mapped) > STAGES.index(stage):
                stage = mapped
    return stage


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate requirements traceability in a p2c workspace."
    )
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--stage", choices=STAGES, default=None)
    parser.add_argument(
        "--apply-status",
        action="store_true",
        help="write status: stale and strip signoff on affected sidecars",
    )
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    workspace: Path = args.workspace
    if not workspace.is_dir():
        print(f"error: workspace not found: {workspace}", file=sys.stderr)
        return 2

    try:
        sidecars = load_workspace(workspace)
    except SidecarError as exc:
        print(f"error: {exc}", file=sys.stderr)
        _write_validation_failure(workspace, "Parse error", [str(exc)])
        return 2

    schema_errors = validate_all(sidecars)
    if schema_errors:
        messages = []
        for err in schema_errors:
            message = (
                f"schema error: {err.subject} [{err.field_name}] {err.message} "
                f"({err.path})"
            )
            print(message, file=sys.stderr)
            messages.append(message)
        _write_validation_failure(workspace, "Schema errors", messages)
        return 2

    stage = resolve_stage(workspace, args.stage)
    graph = build_graph(sidecars)
    gaps = check(graph, stage, workspace)
    stale = detect(graph)

    write_all(graph, gaps, stale, workspace / "traceability", root=workspace)

    if args.apply_status and stale:
        for path in apply_status(stale, graph):
            if not args.quiet:
                print(f"marked stale: {path}")

    if not args.quiet:
        print(f"stage: {stage}")
        for gap in sorted(gaps, key=lambda g: (g.kind, g.subject)):
            print(f"gap [{gap.kind}] {gap.subject}: {gap.message}")
        for entry in sorted(stale, key=lambda e: e.subject):
            print(f"stale [{entry.reason}] {entry.subject}")
        print(
            f"{len(gaps)} gap(s), {len(stale)} stale artifact(s) — "
            f"reports in {workspace / 'traceability'}"
        )

    return 1 if (gaps or stale) else 0


if __name__ == "__main__":
    sys.exit(main())
