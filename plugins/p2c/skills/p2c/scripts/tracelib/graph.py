from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from tracelib.ids import journey_step_parent
from tracelib.sidecar import Sidecar

LINK_FIELDS = ("traces_to", "personas", "persona", "journey_steps")


@dataclass
class Graph:
    nodes: dict[str, Sidecar] = field(default_factory=dict)
    out: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))
    inc: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))
    dangling: list[tuple[str, str]] = field(default_factory=list)
    # Synthesized journey-step IDs that collided with an already-registered
    # node. First definition wins the slot in `nodes`; later ones are
    # recorded here as (duplicate_id, losing_owner_id) rather than dropped
    # silently.
    collisions: list[tuple[str, str]] = field(default_factory=list)
    # Journey steps that could not be synthesized into a node, as
    # (journey_id, 1-based position). A step with no `id`, or one that is
    # not a mapping at all, has no identity to hang a node on — but
    # dropping it silently means a step of the journey exists in the
    # author's head and in no check.
    malformed_steps: list[tuple[str, int]] = field(default_factory=list)

    def downstream(self, node_id: str) -> set[str]:
        seen: set[str] = set()
        stack = list(self.inc.get(node_id, set()))
        while stack:
            current = stack.pop()
            if current in seen:
                continue
            seen.add(current)
            stack.extend(self.inc.get(current, set()))
        return seen

    def by_type(self, type_name: str) -> list[Sidecar]:
        return [
            sc for sc in self.nodes.values() if sc.type == type_name
        ]


def _synthesize_journey_steps(sc: Sidecar) -> tuple[list[Sidecar], list[int]]:
    """Mint one node per journey step.

    Returns the synthesized nodes and the 1-based positions of steps that
    could not be synthesized (not a mapping, or no `id`). Callers must
    surface those positions: a step with no identity is still a step the
    author declared, and dropping it silently removes it from every check.

    Note the synthesized node carries the OWNING JOURNEY's path and an
    empty body. It has no file of its own, so nothing may write to it —
    see staleness._is_synthesized.
    """
    steps = sc.frontmatter.get("steps") or []
    if isinstance(steps, dict) or not isinstance(steps, (list, tuple)):
        steps = [steps]

    synthesized: list[Sidecar] = []
    malformed: list[int] = []
    for position, step in enumerate(steps, start=1):
        if not isinstance(step, dict) or not step.get("id"):
            malformed.append(position)
            continue
        screen = step.get("screen")
        fm = {
            "id": step["id"],
            "type": "journey_step",
            "title": step.get("label", step["id"]),
            "status": sc.frontmatter.get("status", "draft"),
            "traces_to": [sc.id] + ([screen] if screen else []),
            # Recorded so stages can ask "does this step declare a screen?"
            # without reparsing the journey. Not a LINK_FIELD: the edge is
            # already carried by traces_to.
            "screen": screen,
            "_owner": sc.id,
        }
        synthesized.append(Sidecar(path=sc.path, frontmatter=fm, body=""))
    return synthesized, malformed


def build_graph(sidecars: list[Sidecar]) -> Graph:
    graph = Graph()

    expanded: list[Sidecar] = []
    for sc in sidecars:
        expanded.append(sc)
        if sc.type == "journey":
            steps, malformed = _synthesize_journey_steps(sc)
            expanded.extend(steps)
            graph.malformed_steps.extend((sc.id, pos) for pos in malformed)

    for sc in expanded:
        if not sc.id:
            continue
        if sc.id in graph.nodes:
            if sc.type == "journey_step":
                owner = str(sc.frontmatter.get("_owner", ""))
                graph.collisions.append((sc.id, owner))
            # File-backed duplicates are schema's job; not reported here.
            continue
        graph.nodes[sc.id] = sc

    for sc in expanded:
        if not sc.id:
            continue
        targets: set[str] = set()
        for name in LINK_FIELDS:
            value = sc.frontmatter.get(name) or []
            if isinstance(value, str):
                value = [value]
            targets.update(str(v) for v in value)

        parent = journey_step_parent(sc.id)
        if parent:
            targets.add(parent)

        for target in sorted(targets):
            if target not in graph.nodes:
                graph.dangling.append((sc.id, target))
                continue
            graph.out[sc.id].add(target)
            graph.inc[target].add(sc.id)

    return graph
