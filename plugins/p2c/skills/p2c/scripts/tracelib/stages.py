from __future__ import annotations

from pathlib import Path

from tracelib.errors import Gap
from tracelib.graph import Graph

STAGES: tuple[str, ...] = ("requirements", "design", "handoff", "build")

_MOCKUP_DIR = Path("03-design") / "mockups"


def _stage_index(stage: str) -> int:
    if stage not in STAGES:
        raise ValueError(f"unknown stage '{stage}'; expected one of {STAGES}")
    return STAGES.index(stage)


def _requirements(graph: Graph) -> list:
    return [sc for sc in graph.by_type("requirement")]


def _consumers_of_type(graph: Graph, req_id: str, type_name: str) -> list[str]:
    return [
        node_id
        for node_id in graph.downstream(req_id)
        if graph.nodes[node_id].type == type_name
    ]


def _check_requirements_stage(graph: Graph) -> list[Gap]:
    gaps: list[Gap] = []

    for source, target in graph.dangling:
        gaps.append(
            Gap("dangling-ref", source, f"references unknown artifact '{target}'")
        )

    for duplicate_id, owner_id in graph.collisions:
        gaps.append(
            Gap(
                "duplicate-step",
                duplicate_id,
                f"journey step redefined by '{owner_id}'; first definition wins",
            )
        )

    for req in _requirements(graph):
        if req.frontmatter.get("kind") != "business":
            continue
        children = [
            node_id
            for node_id in graph.inc.get(req.id, set())
            if graph.nodes[node_id].type == "requirement"
        ]
        if not children:
            gaps.append(
                Gap(
                    "undecomposed-br",
                    req.id,
                    "business requirement decomposes into no FR or NFR",
                )
            )
    return gaps


def _check_design_stage(graph: Graph, root: Path) -> list[Gap]:
    gaps: list[Gap] = []

    for req in _requirements(graph):
        fm = req.frontmatter
        if fm.get("kind") != "functional" or fm.get("surface") != "ui":
            continue
        screens = _consumers_of_type(graph, req.id, "screen")
        if not screens:
            gaps.append(
                Gap(
                    "orphan-requirement",
                    req.id,
                    "UI requirement is not served by any screen",
                )
            )

    for screen in graph.by_type("screen"):
        fm = screen.frontmatter
        if not fm.get("traces_to"):
            gaps.append(
                Gap(
                    "orphan-artifact",
                    screen.id,
                    "screen traces to no requirement (scope creep)",
                )
            )
        if not fm.get("personas"):
            gaps.append(
                Gap("broken-chain", screen.id, "screen declares no persona")
            )
        if not fm.get("journey_steps"):
            gaps.append(
                Gap("broken-chain", screen.id, "screen declares no journey step")
            )

        states = fm.get("states") or {}
        for state_name, filename in sorted(states.items()):
            if not (root / _MOCKUP_DIR / str(filename)).is_file():
                gaps.append(
                    Gap(
                        "missing-state",
                        screen.id,
                        f"declared state '{state_name}' file '{filename}' not found",
                    )
                )

    for type_name, label in (("persona", "persona"), ("journey", "journey map")):
        for node in graph.by_type(type_name):
            if not graph.inc.get(node.id):
                gaps.append(
                    Gap("orphan-artifact", node.id, f"{label} is referenced by nothing")
                )

    return gaps


def _check_handoff_stage(graph: Graph) -> list[Gap]:
    gaps: list[Gap] = []
    for req in _requirements(graph):
        if req.frontmatter.get("kind") == "business":
            continue
        if not _consumers_of_type(graph, req.id, "component"):
            gaps.append(
                Gap("broken-chain", req.id, "no architecture component owns this")
            )
        headless = (
            req.frontmatter.get("kind") == "non-functional"
            or req.frontmatter.get("surface") == "system"
        )
        if headless and not _consumers_of_type(graph, req.id, "test"):
            gaps.append(Gap("broken-chain", req.id, "no test asserts this"))
    return gaps


def _check_build_stage(graph: Graph) -> list[Gap]:
    gaps: list[Gap] = []
    for req in _requirements(graph):
        if req.frontmatter.get("kind") == "business":
            continue
        if not _consumers_of_type(graph, req.id, "story"):
            gaps.append(Gap("broken-chain", req.id, "no story implements this"))
    return gaps


def check(graph: Graph, stage: str, workspace_root: Path) -> list[Gap]:
    index = _stage_index(stage)
    gaps = _check_requirements_stage(graph)
    if index >= STAGES.index("design"):
        gaps.extend(_check_design_stage(graph, workspace_root))
    if index >= STAGES.index("handoff"):
        gaps.extend(_check_handoff_stage(graph))
    if index >= STAGES.index("build"):
        gaps.extend(_check_build_stage(graph))
    return gaps
