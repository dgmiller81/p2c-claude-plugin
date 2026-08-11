from __future__ import annotations

from pathlib import Path, PurePosixPath, PureWindowsPath

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

    for journey_id, position in graph.malformed_steps:
        gaps.append(
            Gap(
                "malformed-step",
                journey_id,
                f"step #{position} has no usable 'id', so it exists in no "
                "graph node and no check can see it; give it an id of the "
                f"form {journey_id}.<n>",
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


def _is_unsafe_state_path(value: str) -> bool:
    """True if a declared state file could resolve outside the mockups dir.

    Absoluteness is platform-shaped: `Path("/etc/passwd").is_absolute()` is
    False on Windows (no drive) and `Path("C:/Windows/win.ini")` is not
    absolute on POSIX. A host-platform-only check leaves the other form
    unguarded on the CI that actually runs it, so both syntaxes are tested
    with both flavours of PurePath regardless of where we are running.
    """
    if value.startswith(("/", "\\")):
        return True
    if PureWindowsPath(value).drive or PurePosixPath(value).is_absolute():
        return True
    parts = set(PureWindowsPath(value).parts) | set(PurePosixPath(value).parts)
    return ".." in parts


def _orphan_artifacts(graph: Graph, type_name: str) -> list[Gap]:
    """Artifacts of `type_name` that trace to nothing.

    The spec's orphan-artifact case is "a screen OR COMPONENT tracing to
    nothing" — work nobody asked for. schema.MAY_BE_EMPTY deliberately lets
    an empty `traces_to` through for screen, component, story and test,
    because it is a traceability gap rather than a structural defect — but
    that only holds if something downstream actually reports it.
    """
    return [
        Gap(
            "orphan-artifact",
            node.id,
            f"{type_name} traces to nothing; no requirement asked for it "
            "(scope creep)",
        )
        for node in sorted(graph.by_type(type_name), key=lambda s: s.id)
        if not node.frontmatter.get("traces_to")
    ]


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

    gaps.extend(_orphan_artifacts(graph, "screen"))

    for screen in graph.by_type("screen"):
        fm = screen.frontmatter
        if not fm.get("personas"):
            gaps.append(
                Gap("broken-chain", screen.id, "screen declares no persona")
            )
        if not fm.get("journey_steps"):
            gaps.append(
                Gap("broken-chain", screen.id, "screen declares no journey step")
            )

        states = fm.get("states") or {}
        if not isinstance(states, dict):
            # schema.validate rejects this and the CLI exits 2 before ever
            # reaching here; the guard keeps a direct library caller from
            # getting an AttributeError instead of a gap list.
            gaps.append(
                Gap(
                    "missing-state",
                    screen.id,
                    "'states' is not a mapping of state name to file, so no "
                    "state could be checked",
                )
            )
            continue
        for state_name, filename in sorted(states.items()):
            filename_str = str(filename)
            # `root / _MOCKUP_DIR / candidate` silently discards `root` when
            # `candidate` is absolute (pathlib joining semantics), and `..`
            # segments can walk the join outside the mockups directory
            # entirely. Reject both before ever touching the filesystem.
            if _is_unsafe_state_path(filename_str):
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
            if not (root / _MOCKUP_DIR / Path(filename_str)).is_file():
                gaps.append(
                    Gap(
                        "missing-state",
                        screen.id,
                        f"declared state '{state_name}' file '{filename_str}' not found",
                    )
                )

    # The spec's functional+ui chain lists "journey step has no screen" as
    # an explicit failure condition. The journey-level orphan check below
    # asks only whether SOME step is used by SOME screen, so it cannot see
    # a journey whose other steps lead nowhere. Both checks are kept: they
    # catch different things.
    for step in sorted(graph.by_type("journey_step"), key=lambda s: s.id):
        if not step.frontmatter.get("screen"):
            gaps.append(
                Gap(
                    "broken-chain",
                    step.id,
                    "journey step declares no screen, so the persona has "
                    "nowhere to perform it",
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
    gaps: list[Gap] = _orphan_artifacts(graph, "component")
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
    gaps: list[Gap] = _orphan_artifacts(graph, "story") + _orphan_artifacts(
        graph, "test"
    )
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
