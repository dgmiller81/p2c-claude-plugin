from __future__ import annotations

from pathlib import Path

from tracelib.errors import Gap
from tracelib.graph import Graph
from tracelib.hashing import normative_hash
from tracelib.ids import journey_step_parent

STAGES: tuple[str, ...] = ("requirements", "design", "handoff", "build")

_MOCKUP_DIR = Path("03-design") / "mockups"


def _stage_index(stage: str) -> int:
    if stage not in STAGES:
        raise ValueError(f"unknown stage '{stage}'; expected one of {STAGES}")
    return STAGES.index(stage)


def _requirements(graph: Graph) -> list:
    return [sc for sc in graph.by_type("requirement")]


def _consumers_of_type(graph: Graph, req_id: str, type_name: str) -> list[str]:
    # Direct edges only. `graph.downstream` is the transitive closure, which
    # is correct for staleness cascade but wrong here: a screen that only
    # traces to a component that traces to the requirement never actually
    # named the requirement, and must not count as serving it.
    return [
        node_id
        for node_id in graph.inc.get(req_id, set())
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
            filename_str = str(filename)
            candidate = Path(filename_str)
            # `root / _MOCKUP_DIR / candidate` silently discards `root` when
            # `candidate` is absolute (pathlib joining semantics), and `..`
            # segments can walk the join outside the mockups directory
            # entirely. Reject both before ever touching the filesystem.
            if candidate.is_absolute() or ".." in candidate.parts:
                gaps.append(
                    Gap(
                        "missing-state",
                        screen.id,
                        f"declared state '{state_name}' file '{filename_str}' must be a "
                        "relative filename inside the mockups directory "
                        "(no absolute paths or '..' segments)",
                    )
                )
                continue
            if not (root / _MOCKUP_DIR / candidate).is_file():
                gaps.append(
                    Gap(
                        "missing-state",
                        screen.id,
                        f"declared state '{state_name}' file '{filename_str}' not found",
                    )
                )

    for persona in graph.by_type("persona"):
        if not graph.inc.get(persona.id):
            gaps.append(
                Gap("orphan-artifact", persona.id, "persona is referenced by nothing")
            )

    for journey in graph.by_type("journey"):
        # A journey's own synthesized steps always create an inbound edge
        # onto the journey (step --traces_to--> journey), and schema
        # requires `steps` to be non-empty, so "is anything pointing at
        # this journey" can never fire. The real question is whether any
        # SCREEN actually uses one of the journey's steps.
        step_ids = [
            sc.id
            for sc in graph.nodes.values()
            if sc.type == "journey_step" and journey_step_parent(sc.id) == journey.id
        ]
        used_by_a_screen = any(
            graph.nodes[consumer].type == "screen"
            for step_id in step_ids
            for consumer in graph.inc.get(step_id, set())
        )
        if not used_by_a_screen:
            gaps.append(
                Gap(
                    "orphan-artifact",
                    journey.id,
                    "journey has no step referenced by any screen",
                )
            )

    return gaps


def _check_unhashed_links(graph: Graph) -> list[Gap]:
    """Every traced-to requirement must be covered by the tracer's source_hash.

    Staleness detection (tracelib.staleness.detect) iterates only what is
    RECORDED in `source_hash`. An empty or absent map therefore means no
    staleness detection at all — permanently, and silently. That turns the
    spec's central promise ("changing what a requirement demands invalidates
    downstream work") into an opt-in an author gets wrong by omission.

    Only requirement targets are checked: they are the artifacts whose
    normative text downstream work is a response to. Dangling targets are
    skipped — they are already reported as `dangling-ref`, and there is no
    node to hash.
    """
    gaps: list[Gap] = []
    for node_id, sc in sorted(graph.nodes.items()):
        targets = sc.frontmatter.get("traces_to") or []
        if isinstance(targets, str):
            targets = [targets]
        if not isinstance(targets, (list, tuple, set)):
            continue

        recorded = sc.frontmatter.get("source_hash") or {}
        if not isinstance(recorded, dict):
            # schema.validate already rejects a non-mapping source_hash;
            # treat it as recording nothing rather than crashing here.
            recorded = {}

        for target in sorted(str(t) for t in targets):
            upstream = graph.nodes.get(target)
            if upstream is None or upstream.type != "requirement":
                continue
            if target in recorded:
                continue
            gaps.append(
                Gap(
                    "unhashed-link",
                    node_id,
                    f"traces to {target} but records no source_hash for it; "
                    f"current hash is {normative_hash(upstream)}",
                )
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
        gaps.extend(_check_unhashed_links(graph))
    if index >= STAGES.index("handoff"):
        gaps.extend(_check_handoff_stage(graph))
    if index >= STAGES.index("build"):
        gaps.extend(_check_build_stage(graph))
    return gaps
