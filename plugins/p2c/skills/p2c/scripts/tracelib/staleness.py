from __future__ import annotations

from pathlib import Path

import yaml

from tracelib.errors import StaleEntry
from tracelib.graph import Graph
from tracelib.hashing import normative_hash


def detect(graph: Graph) -> list[StaleEntry]:
    direct: dict[str, list[str]] = {}

    for node_id, sc in graph.nodes.items():
        recorded = sc.frontmatter.get("source_hash") or {}
        if not isinstance(recorded, dict):
            continue
        changed: list[str] = []
        for upstream_id, expected in recorded.items():
            upstream = graph.nodes.get(str(upstream_id))
            if upstream is None:
                continue
            if normative_hash(upstream) != str(expected):
                changed.append(str(upstream_id))
        if changed:
            direct[node_id] = sorted(changed)

    entries: list[StaleEntry] = []
    seen: set[str] = set()

    for node_id in sorted(direct):
        entries.append(
            StaleEntry(
                subject=node_id,
                reason="upstream-changed",
                changed_upstream=direct[node_id],
                signoff_voided=bool(graph.nodes[node_id].frontmatter.get("signoff")),
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


def apply_status(entries: list[StaleEntry], graph: Graph) -> list[Path]:
    written: list[Path] = []
    for entry in entries:
        sc = graph.nodes.get(entry.subject)
        if sc is None:
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
