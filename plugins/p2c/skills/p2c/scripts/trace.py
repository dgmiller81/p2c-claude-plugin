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

    stage = "requirements"
    for gate, mapped in GATE_TO_STAGE.items():
        gate_state = (config.get("gates") or {}).get(gate) or {}
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
        return 2

    schema_errors = validate_all(sidecars)
    if schema_errors:
        for err in schema_errors:
            print(
                f"schema error: {err.subject} [{err.field_name}] {err.message} "
                f"({err.path})",
                file=sys.stderr,
            )
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
