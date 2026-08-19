from __future__ import annotations

import json
import re
from pathlib import Path

from tracelib.errors import Gap, StaleEntry
from tracelib.graph import Graph

_NEWLINE_RE = re.compile(r"[\r\n]+")

# Iterations after which a finding stops being a normal loop and becomes a
# decision the human has to force. See spec section 5.4.
ESCALATION_THRESHOLD = 3


def _cell(value: object) -> str:
    """Stringify a value for safe interpolation into a Markdown table cell.

    Escapes `|` so it can't be mistaken for a column delimiter, and collapses
    any run of newlines/carriage returns to a single space so a value can
    never split a row across multiple lines.
    """
    text = str(value)
    text = text.replace("|", "\\|")
    text = _NEWLINE_RE.sub(" ", text)
    return text


# Dispositions that mean the challenge to a requirement is still live.
# `resolved` and `rejected` are both closed: the requirement has already
# been amended, or it stands as written.
OPEN_DISPOSITIONS = frozenset({"open", "accepted"})


def _challenged_requirements(graph: Graph) -> set[str]:
    """Requirement ids with a live finding against them.

    The `unresolved-finding` gap's subject is the FINDING's id, not the
    requirement's, so a challenged requirement never lands in
    `gap_subjects` and its RTM row would otherwise read `ok` while its
    feasibility is actively disputed.
    """
    challenged: set[str] = set()
    for finding in graph.by_type("finding"):
        if finding.frontmatter.get("disposition") not in OPEN_DISPOSITIONS:
            continue
        targets = finding.frontmatter.get("traces_to") or []
        if isinstance(targets, str):
            targets = [targets]
        for target in targets:
            node = graph.nodes.get(str(target))
            if node is not None and node.type == "requirement":
                challenged.add(str(target))
    return challenged


def _status_for(
    req_id: str,
    chain: dict[str, list[str]],
    gap_subjects: set[str],
    stale_subjects: set[str],
    challenged: frozenset[str] | set[str] = frozenset(),
) -> str:
    """Worst-first: STALE > CHALLENGED > GAP > unverified > ok.

    CHALLENGED outranks GAP because a requirement under a live finding may
    still be rewritten: closing its downstream gaps before the product
    owner rules on the finding is work that may have to be redone.
    """
    if req_id in stale_subjects:
        return "STALE"
    if req_id in challenged:
        return "CHALLENGED"
    if req_id in gap_subjects:
        return "GAP"
    if not any(chain.values()):
        return "unverified"
    return "ok"


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
    challenged = _challenged_requirements(graph)

    lines = [
        "# Requirements Traceability Matrix",
        "",
        "| Req | Kind | Surface | Personas | Journey steps | Screens | Components | Stories | Tests | Status |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]

    for req in sorted(graph.by_type("requirement"), key=lambda s: s.id):
        chain = _chain_for(graph, req.id)
        status = _status_for(
            req.id, chain, gap_subjects, stale_subjects, challenged
        )
        lines.append(
            "| {id} | {kind} | {surface} | {p} | {j} | {s} | {c} | {u} | {t} | {st} |".format(
                id=_cell(req.id),
                kind=_cell(req.frontmatter.get("kind", "")),
                surface=_cell(req.frontmatter.get("surface", "—")),
                p=_cell(", ".join(chain["persona"]) or "—"),
                j=_cell(", ".join(chain["journey_step"]) or "—"),
                s=_cell(", ".join(chain["screen"]) or "—"),
                c=_cell(", ".join(chain["component"]) or "—"),
                u=_cell(", ".join(chain["story"]) or "—"),
                t=_cell(", ".join(chain["test"]) or "—"),
                st=_cell(status),
            )
        )

    lines.append("")
    lines.append(
        "Status legend (worst wins): `STALE` = flagged by the staleness "
        "detector; `CHALLENGED` = an open or accepted finding disputes this "
        "requirement, so it may still be rewritten — see the Findings table "
        "below; `GAP` = flagged by the gap detector; `unverified` = nothing "
        "downstream traces to this requirement; `ok` = has a downstream chain "
        "and was not flagged."
    )
    lines.append("")
    lines += _findings_section(graph)
    out_path.write_text("\n".join(lines), encoding="utf-8")


def write_index(
    graph: Graph,
    gaps: list[Gap],
    stale: list[StaleEntry],
    out_path: Path,
    *,
    root: Path | None = None,
) -> None:
    stale_by_subject = {e.subject: e for e in stale}
    nodes: dict[str, dict] = {}

    for node_id, sc in sorted(graph.nodes.items()):
        entry = stale_by_subject.get(node_id)
        if root is not None:
            try:
                path_str = sc.path.relative_to(root).as_posix()
            except ValueError:
                path_str = sc.path.as_posix()
        else:
            path_str = sc.path.as_posix()
        nodes[node_id] = {
            "type": sc.type,
            "title": sc.frontmatter.get("title", ""),
            "path": path_str,
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
            {"kind": g.kind, "subject": g.subject, "message": g.message}
            for g in sorted(gaps, key=lambda g: (g.kind, g.subject))
        ],
        "stale": [
            {
                "subject": e.subject,
                "reason": e.reason,
                "changed_upstream": e.changed_upstream,
                "signoff_voided": e.signoff_voided,
            }
            for e in sorted(stale, key=lambda e: e.subject)
        ],
        "findings": [
            {
                "id": sc.id,
                "challenges": sorted(graph.out.get(sc.id, set())),
                "nature": sc.frontmatter.get("nature", ""),
                "severity": sc.frontmatter.get("severity", ""),
                "disposition": sc.frontmatter.get("disposition", ""),
                "iterations": len(sc.frontmatter.get("history") or []),
            }
            for sc in sorted(graph.by_type("finding"), key=lambda s: s.id)
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


def _hash_transition_cell(graph: Graph | None, entry: StaleEntry) -> str:
    """Render "<id>: <recorded> -> <current>" for each changed upstream.

    "Recorded" is the value currently sitting in the stale artifact's own
    `source_hash` frontmatter (the value that no longer matches); "current"
    is `entry.current_hashes[id]`, the freshly computed hash a repairer
    should write instead. Renders "—" when there's nothing to show, which
    is always the case for "transitive" entries — their `current_hashes`
    is intentionally left empty since repair follows from the direct entry.
    """
    if graph is None or not entry.current_hashes:
        return "—"

    subject_node = graph.nodes.get(entry.subject)
    recorded_map: dict = {}
    if subject_node is not None:
        raw = subject_node.frontmatter.get("source_hash") or {}
        if isinstance(raw, dict):
            recorded_map = raw

    parts = []
    for upstream_id in entry.changed_upstream:
        current = entry.current_hashes.get(upstream_id)
        if current is None:
            continue
        recorded = recorded_map.get(upstream_id, "?")
        parts.append(f"{upstream_id}: {recorded} → {current}")

    return ", ".join(parts) if parts else "—"


def _findings_section(graph: Graph | None) -> list[str]:
    """Render the findings table.

    Iterations is len(history) — the number of times this finding has been
    raised against successive versions of the requirement. At or above
    ESCALATION_THRESHOLD the loop is not converging and the orchestrator must
    put the decision back to the user.
    """
    if graph is None:
        return []

    findings = sorted(graph.by_type("finding"), key=lambda s: s.id)
    if not findings:
        return ["## Findings", "", "No findings recorded.", ""]

    lines = [
        "## Findings",
        "",
        "| Finding | Challenges | Nature | Severity | Disposition | Iterations | Escalate |",
        "|---|---|---|---|---|---|---|",
    ]
    for sc in findings:
        fm = sc.frontmatter
        targets = fm.get("traces_to") or []
        if isinstance(targets, str):
            targets = [targets]
        iterations = len(fm.get("history") or [])
        escalate = "escalate" if iterations >= ESCALATION_THRESHOLD else "—"
        lines.append(
            f"| {_cell(sc.id)} | "
            f"{_cell(', '.join(str(t) for t in targets) or '—')} | "
            f"{_cell(fm.get('nature', '—'))} | "
            f"{_cell(fm.get('severity', '—'))} | "
            f"{_cell(fm.get('disposition', '—'))} | "
            f"{_cell(iterations)} | {_cell(escalate)} |"
        )
    lines.append("")
    return lines


def write_gaps(
    gaps: list[Gap],
    stale: list[StaleEntry],
    out_path: Path,
    *,
    graph: Graph | None = None,
) -> None:
    lines = ["# Traceability gaps", ""]

    if not gaps:
        lines += ["## Gaps", "", "No gaps found.", ""]
    else:
        lines += ["## Gaps", "", "| Kind | Subject | Detail |", "|---|---|---|"]
        for gap in sorted(gaps, key=lambda g: (g.kind, g.subject)):
            lines.append(
                f"| {_cell(gap.kind)} | {_cell(gap.subject)} | {_cell(gap.message)} |"
            )
        lines.append("")

    if not stale:
        lines += ["## Staleness", "", "No stale artifacts.", ""]
    else:
        lines += [
            "## Staleness",
            "",
            "| Artifact | Reason | Changed upstream | Recorded → current | Sign-off |",
            "|---|---|---|---|---|",
        ]
        for entry in sorted(stale, key=lambda e: e.subject):
            signoff = "sign-off voided" if entry.signoff_voided else "—"
            lines.append(
                f"| {_cell(entry.subject)} | {_cell(entry.reason)} | "
                f"{_cell(', '.join(entry.changed_upstream) or '—')} | "
                f"{_cell(_hash_transition_cell(graph, entry))} | {_cell(signoff)} |"
            )
        lines.append("")

    lines += _findings_section(graph)

    out_path.write_text("\n".join(lines), encoding="utf-8")


def write_all(
    graph: Graph,
    gaps: list[Gap],
    stale: list[StaleEntry],
    traceability_dir: Path,
    *,
    root: Path | None = None,
) -> list[Path]:
    traceability_dir.mkdir(parents=True, exist_ok=True)
    rtm = traceability_dir / "rtm.md"
    index = traceability_dir / "index.json"
    gaps_path = traceability_dir / "gaps.md"

    write_rtm(graph, gaps, stale, rtm)
    write_index(graph, gaps, stale, index, root=root)
    write_gaps(gaps, stale, gaps_path, graph=graph)
    return [rtm, index, gaps_path]
