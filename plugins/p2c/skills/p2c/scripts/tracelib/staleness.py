from __future__ import annotations

from pathlib import Path

import yaml

from tracelib.errors import StaleEntry
from tracelib.graph import Graph
from tracelib.hashing import normative_hash


def detect(graph: Graph) -> list[StaleEntry]:
    direct: dict[str, list[str]] = {}
    # Upstream ID -> freshly computed hash, per node with a direct mismatch.
    # Populated alongside `direct` so the repairer-facing report can show
    # what the correct source_hash value now is, not just that it's wrong.
    direct_current_hashes: dict[str, dict[str, str]] = {}

    for node_id, sc in graph.nodes.items():
        recorded = sc.frontmatter.get("source_hash") or {}
        if not isinstance(recorded, dict):
            continue
        changed: list[str] = []
        current_for_node: dict[str, str] = {}
        for upstream_id, expected in recorded.items():
            upstream = graph.nodes.get(str(upstream_id))
            if upstream is None:
                continue
            current_hash = normative_hash(upstream)
            if current_hash != str(expected):
                changed.append(str(upstream_id))
                current_for_node[str(upstream_id)] = current_hash
        if changed:
            direct[node_id] = sorted(changed)
            direct_current_hashes[node_id] = current_for_node

    entries: list[StaleEntry] = []
    seen: set[str] = set()

    for node_id in sorted(direct):
        entries.append(
            StaleEntry(
                subject=node_id,
                reason="upstream-changed",
                changed_upstream=direct[node_id],
                signoff_voided=bool(graph.nodes[node_id].frontmatter.get("signoff")),
                current_hashes=direct_current_hashes.get(node_id, {}),
            )
        )
        seen.add(node_id)

    for node_id in sorted(direct):
        for affected in sorted(graph.downstream(node_id)):
            if affected in seen:
                continue
            seen.add(affected)
            entries.append(
                StaleEntry(
                    subject=affected,
                    reason="transitive",
                    changed_upstream=direct[node_id],
                    signoff_voided=bool(
                        graph.nodes[affected].frontmatter.get("signoff")
                    ),
                )
            )

    return entries


def _is_synthesized(sc) -> bool:
    """True for graph nodes that have no file of their own.

    `graph._synthesize_journey_steps` mints a node per journey step and
    hands it the OWNING JOURNEY's path with an empty body. Writing such a
    node back would overwrite the journey's file with the step's
    frontmatter, destroying the journey's persona, steps, title and prose.
    Staleness of a step is repaired by its owning journey, so these nodes
    are reported but never written.
    """
    return sc.type == "journey_step" or "_owner" in sc.frontmatter


def apply_status(entries: list[StaleEntry], graph: Graph) -> list[Path]:
    written: list[Path] = []
    for entry in entries:
        sc = graph.nodes.get(entry.subject)
        if sc is None:
            continue
        if _is_synthesized(sc):
            continue
        updated = dict(sc.frontmatter)
        updated["status"] = "stale"
        updated.pop("signoff", None)

        front = yaml.safe_dump(updated, sort_keys=False, allow_unicode=True).strip()
        sc.path.write_text(
            f"---\n{front}\n---\n{sc.body}", encoding="utf-8"
        )
        written.append(sc.path)
    return written
