from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from tracelib.ids import journey_step_parent
from tracelib.sidecar import Sidecar

LINK_FIELDS = ("traces_to", "personas", "journey_steps")


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


def _synthesize_journey_steps(sc: Sidecar) -> list[Sidecar]:
    steps = sc.frontmatter.get("steps") or []
    synthesized: list[Sidecar] = []
    for step in steps:
        if not isinstance(step, dict) or not step.get("id"):
            continue
        fm = {
            "id": step["id"],
            "type": "journey_step",
            "title": step.get("label", step["id"]),
            "status": sc.frontmatter.get("status", "draft"),
            "traces_to": [sc.id] + ([step["screen"]] if step.get("screen") else []),
            "_owner": sc.id,
        }
        synthesized.append(Sidecar(path=sc.path, frontmatter=fm, body=""))
    return synthesized


def build_graph(sidecars: list[Sidecar]) -> Graph:
    graph = Graph()

    expanded: list[Sidecar] = []
    for sc in sidecars:
        expanded.append(sc)
        if sc.type == "journey":
            expanded.extend(_synthesize_journey_steps(sc))

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
