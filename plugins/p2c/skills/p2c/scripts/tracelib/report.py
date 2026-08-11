from __future__ import annotations

import json
from pathlib import Path

from tracelib.errors import Gap, StaleEntry
from tracelib.graph import Graph


def _chain_for(graph: Graph, req_id: str) -> dict[str, list[str]]:
    chain: dict[str, list[str]] = {
        "persona": [],
        "journey_step": [],
        "screen": [],
        "component": [],
        "story": [],
        "test": [],
    }
    for node_id in sorted(graph.downstream(req_id)):
        node_type = graph.nodes[node_id].type
        if node_type in chain:
            chain[node_type].append(node_id)
    screens = chain["screen"]
    for screen_id in screens:
        fm = graph.nodes[screen_id].frontmatter
        for persona in fm.get("personas") or []:
            if persona not in chain["persona"]:
                chain["persona"].append(str(persona))
        for step in fm.get("journey_steps") or []:
            if step not in chain["journey_step"]:
                chain["journey_step"].append(str(step))
    return chain


def write_rtm(
    graph: Graph, gaps: list[Gap], stale: list[StaleEntry], out_path: Path
) -> None:
    stale_subjects = {e.subject for e in stale}
    gap_subjects = {g.subject for g in gaps}

    lines = [
        "# Requirements Traceability Matrix",
        "",
        "| Req | Kind | Surface | Personas | Journey steps | Screens | Components | Stories | Tests | Status |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]

    for req in sorted(graph.by_type("requirement"), key=lambda s: s.id):
        chain = _chain_for(graph, req.id)
        if req.id in stale_subjects:
            status = "STALE"
        elif req.id in gap_subjects:
            status = "GAP"
        else:
            status = "ok"
        lines.append(
            "| {id} | {kind} | {surface} | {p} | {j} | {s} | {c} | {u} | {t} | {st} |".format(
                id=req.id,
                kind=req.frontmatter.get("kind", ""),
                surface=req.frontmatter.get("surface", "—"),
                p=", ".join(chain["persona"]) or "—",
                j=", ".join(chain["journey_step"]) or "—",
                s=", ".join(chain["screen"]) or "—",
                c=", ".join(chain["component"]) or "—",
                u=", ".join(chain["story"]) or "—",
                t=", ".join(chain["test"]) or "—",
                st=status,
            )
        )

    lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")


def write_index(
    graph: Graph, gaps: list[Gap], stale: list[StaleEntry], out_path: Path
) -> None:
    stale_by_subject = {e.subject: e for e in stale}
    nodes: dict[str, dict] = {}

    for node_id, sc in sorted(graph.nodes.items()):
        entry = stale_by_subject.get(node_id)
        nodes[node_id] = {
            "type": sc.type,
            "title": sc.frontmatter.get("title", ""),
            "path": str(sc.path),
            "declared_status": sc.frontmatter.get("status", ""),
            "effective_status": "stale" if entry else sc.frontmatter.get("status", ""),
            "traces_to": sorted(graph.out.get(node_id, set())),
            # Direct incoming edges only. `Graph.downstream()` is transitive —
            # the names are deliberately different to keep that distinction.
            "traced_by": sorted(graph.inc.get(node_id, set())),
        }

    payload = {
        "nodes": nodes,
        "gaps": [
            {"kind": g.kind, "subject": g.subject, "message": g.message} for g in gaps
        ],
        "stale": [
            {
                "subject": e.subject,
                "reason": e.reason,
                "changed_upstream": e.changed_upstream,
                "signoff_voided": e.signoff_voided,
            }
            for e in stale
        ],
        "summary": {
            "nodes": len(nodes),
            "gaps": len(gaps),
            "stale": len(stale),
            "dangling": len(graph.dangling),
        },
    }
    out_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def write_gaps(gaps: list[Gap], stale: list[StaleEntry], out_path: Path) -> None:
    lines = ["# Traceability gaps", ""]

    if not gaps:
        lines += ["## Gaps", "", "No gaps found.", ""]
    else:
        lines += ["## Gaps", "", "| Kind | Subject | Detail |", "|---|---|---|"]
        for gap in sorted(gaps, key=lambda g: (g.kind, g.subject)):
            lines.append(f"| {gap.kind} | {gap.subject} | {gap.message} |")
        lines.append("")

    if not stale:
        lines += ["## Staleness", "", "No stale artifacts.", ""]
    else:
        lines += [
            "## Staleness",
            "",
            "| Artifact | Reason | Changed upstream | Sign-off |",
            "|---|---|---|---|",
        ]
        for entry in sorted(stale, key=lambda e: e.subject):
            signoff = "sign-off voided" if entry.signoff_voided else "—"
            lines.append(
                f"| {entry.subject} | {entry.reason} | "
                f"{', '.join(entry.changed_upstream) or '—'} | {signoff} |"
            )
        lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")


def write_all(
    graph: Graph,
    gaps: list[Gap],
    stale: list[StaleEntry],
    traceability_dir: Path,
) -> list[Path]:
    traceability_dir.mkdir(parents=True, exist_ok=True)
    rtm = traceability_dir / "rtm.md"
    index = traceability_dir / "index.json"
    gaps_path = traceability_dir / "gaps.md"

    write_rtm(graph, gaps, stale, rtm)
    write_index(graph, gaps, stale, index)
    write_gaps(gaps, stale, gaps_path)
    return [rtm, index, gaps_path]
