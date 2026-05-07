#!/usr/bin/env python3
"""
estimate_cost.py — Generate cost estimates from a sprint plan.

Reads:
  - The rate card from `references/rate-card.md` (JSON block)
  - A sprint plan YAML or Markdown file with per-sprint hours-by-role

Writes:
  - A Markdown cost estimate with totals (standard + AI-assisted), per-sprint and
    per-role breakdowns, assumptions, and a sensitivity table.

Usage:
  python estimate_cost.py --plan path/to/sprint-plan.md --output path/to/cost-estimate.md
  python estimate_cost.py --plan path/to/sprint-plan.yaml --output path/to/cost-estimate.md

The plan can be plain YAML (a list of sprints) or Markdown with embedded YAML in a
fenced ```yaml block, or one fenced block per sprint. The simplest form:

```yaml
- sprint: 1
  goal: "Walking skeleton + auth"
  hours_by_role:
    tech_lead: 40
    full_stack: 80
    qa_engineer: 24
    devops: 16
    scrum_master: 12
    business_analyst: 8
- sprint: 2
  goal: "First validated slice"
  hours_by_role:
    tech_lead: 30
    full_stack: 100
    qa_engineer: 32
    devops: 8
    scrum_master: 12
```

Role keys must match the rate card. Run with --list-roles to see them.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except ImportError:
    yaml = None  # we'll handle this gracefully


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
RATE_CARD_PATH = SKILL_ROOT / "references" / "rate-card.md"


def load_rate_card(path: Path = RATE_CARD_PATH) -> dict[str, Any]:
    """Extract the JSON block from the rate card markdown file."""
    text = path.read_text(encoding="utf-8")
    match = re.search(r"```json\s*(\{.*?\})\s*```", text, flags=re.DOTALL)
    if not match:
        raise SystemExit(f"Could not find JSON block in rate card at {path}")
    data = json.loads(match.group(1))
    by_key = {r["key"]: r for r in data["rates"]}
    return {
        "currency": data.get("currency", "USD"),
        "ai_assist_factor": float(data.get("ai_assist_factor", 0.80)),
        "by_key": by_key,
        "ordered": data["rates"],
    }


def parse_plan(path: Path) -> list[dict[str, Any]]:
    """Parse a sprint plan from YAML or Markdown-with-embedded-YAML."""
    text = path.read_text(encoding="utf-8")
    if yaml is None:
        raise SystemExit(
            "PyYAML is required. Install with: pip install pyyaml\n"
            "(Or use a JSON sprint plan with --plan-format json.)"
        )

    # If it's a markdown file, pull every yaml fence and merge.
    if path.suffix.lower() in {".md", ".markdown"}:
        blocks = re.findall(r"```yaml\s*(.*?)```", text, flags=re.DOTALL)
        if not blocks:
            raise SystemExit(
                f"No ```yaml ... ``` blocks found in {path}. "
                "Add at least one block describing your sprints."
            )
        sprints: list[dict[str, Any]] = []
        for block in blocks:
            parsed = yaml.safe_load(block)
            if isinstance(parsed, list):
                sprints.extend(parsed)
            elif isinstance(parsed, dict):
                sprints.append(parsed)
        return sprints

    # Plain YAML
    parsed = yaml.safe_load(text)
    if isinstance(parsed, list):
        return parsed
    if isinstance(parsed, dict):
        return [parsed]
    raise SystemExit(f"Unexpected YAML structure in {path}")


def sprint_cost(
    hours_by_role: dict[str, float],
    rate_card: dict[str, Any],
    rate_kind: str = "ai_assisted_hr",
) -> tuple[float, dict[str, float]]:
    by_key = rate_card["by_key"]
    by_role: dict[str, float] = {}
    total = 0.0
    for role_key, hours in hours_by_role.items():
        if role_key not in by_key:
            raise SystemExit(
                f"Unknown role key '{role_key}'. "
                f"Valid keys: {sorted(by_key)}"
            )
        rate = float(by_key[role_key][rate_kind])
        cost = float(hours) * rate
        by_role[role_key] = cost
        total += cost
    return total, by_role


def fmt_money(amount: float, currency: str = "USD") -> str:
    sign = "$" if currency.upper() == "USD" else ""
    return f"{sign}{amount:,.2f}"


def render_report(
    sprints: list[dict[str, Any]],
    rate_card: dict[str, Any],
) -> str:
    currency = rate_card["currency"]
    by_key = rate_card["by_key"]
    factor = rate_card["ai_assist_factor"]

    grand_std = 0.0
    grand_ai = 0.0
    role_totals_std: dict[str, float] = {k: 0.0 for k in by_key}
    role_totals_ai: dict[str, float] = {k: 0.0 for k in by_key}
    role_total_hours: dict[str, float] = {k: 0.0 for k in by_key}
    sprint_rows = []

    for entry in sprints:
        sprint_id = entry.get("sprint", "?")
        goal = entry.get("goal", "")
        hours = {k: float(v) for k, v in (entry.get("hours_by_role") or {}).items()}
        if not hours:
            continue
        std_cost, std_by_role = sprint_cost(hours, rate_card, "standard_hr")
        ai_cost, ai_by_role = sprint_cost(hours, rate_card, "ai_assisted_hr")
        grand_std += std_cost
        grand_ai += ai_cost
        for k, h in hours.items():
            role_total_hours[k] += h
            role_totals_std[k] += std_by_role.get(k, 0.0)
            role_totals_ai[k] += ai_by_role.get(k, 0.0)
        sprint_rows.append(
            {
                "sprint": sprint_id,
                "goal": goal,
                "total_hours": sum(hours.values()),
                "std": std_cost,
                "ai": ai_cost,
            }
        )

    # Build markdown
    lines: list[str] = []
    lines.append("# Cost Estimate")
    lines.append("")
    lines.append(
        f"**Currency:** {currency}  |  "
        f"**AI-assist factor:** {factor:.2f}  |  "
        f"**Total sprints:** {len(sprint_rows)}"
    )
    lines.append("")
    lines.append("## Headline totals")
    lines.append("")
    lines.append(f"- **Total cost (AI-assisted rates):** {fmt_money(grand_ai, currency)}")
    lines.append(f"- **Total cost (standard rates):** {fmt_money(grand_std, currency)}")
    delta = grand_std - grand_ai
    if grand_std:
        pct = (delta / grand_std) * 100.0
    else:
        pct = 0.0
    lines.append(
        f"- **AI-assist savings vs. standard:** {fmt_money(delta, currency)} ({pct:.1f}%)"
    )
    lines.append("")

    lines.append("## Per-sprint breakdown")
    lines.append("")
    lines.append("| Sprint | Goal | Total hrs | Cost (AI-assisted) | Cost (standard) |")
    lines.append("|---:|---|---:|---:|---:|")
    for row in sprint_rows:
        lines.append(
            f"| {row['sprint']} | {row['goal']} | {row['total_hours']:.0f} | "
            f"{fmt_money(row['ai'], currency)} | {fmt_money(row['std'], currency)} |"
        )
    lines.append("")

    lines.append("## Per-role totals")
    lines.append("")
    lines.append("| Role | Hours | Total (AI-assisted) | Total (standard) |")
    lines.append("|---|---:|---:|---:|")
    for role_key, info in by_key.items():
        h = role_total_hours.get(role_key, 0.0)
        if h <= 0:
            continue
        ai = role_totals_ai.get(role_key, 0.0)
        std = role_totals_std.get(role_key, 0.0)
        lines.append(
            f"| {info['role']} | {h:.0f} | "
            f"{fmt_money(ai, currency)} | {fmt_money(std, currency)} |"
        )
    lines.append("")

    lines.append("## Assumptions")
    lines.append("")
    lines.append("- Hours are productive (focused engineering) hours, not calendar hours.")
    lines.append("- Default focus factor 0.70 is already baked into the per-sprint hours, not applied here again.")
    lines.append(f"- AI-assist factor: rates discounted by {(1 - factor) * 100:.0f}% from standard.")
    lines.append("- Costs do **not** include cloud/infra fees, third-party SaaS (Sentry, PostHog, etc.), licenses, or contingency.")
    lines.append("- Recommended contingency: +15–25% for unforeseen scope.")
    lines.append("")

    # Sensitivity table
    lines.append("## Sensitivity")
    lines.append("")
    avg_per_sprint_ai = grand_ai / max(len(sprint_rows), 1)
    avg_per_sprint_std = grand_std / max(len(sprint_rows), 1)

    # +1 / -1 sprint sensitivity, using the *average* sprint cost
    plus1_ai = grand_ai + avg_per_sprint_ai
    minus1_ai = max(grand_ai - avg_per_sprint_ai, 0.0)
    plus1_std = grand_std + avg_per_sprint_std
    minus1_std = max(grand_std - avg_per_sprint_std, 0.0)

    # +/-1 engineer sensitivity. Approximation: +1 Full Stack Engineer at 100% across the
    # whole project vs. -1. Uses the FSE rate card row.
    fse = by_key.get("full_stack")
    if fse is not None and len(sprint_rows) > 0:
        engineer_hours_total = 56.0 * len(sprint_rows)  # 56 productive hrs/sprint default
        delta_engineer_ai = engineer_hours_total * float(fse["ai_assisted_hr"])
        delta_engineer_std = engineer_hours_total * float(fse["standard_hr"])
    else:
        delta_engineer_ai = 0.0
        delta_engineer_std = 0.0

    lines.append("| Lever | AI-assisted total | Standard total |")
    lines.append("|---|---:|---:|")
    lines.append(
        f"| As planned | {fmt_money(grand_ai, currency)} | {fmt_money(grand_std, currency)} |"
    )
    lines.append(
        f"| +1 sprint (avg cost) | {fmt_money(plus1_ai, currency)} | {fmt_money(plus1_std, currency)} |"
    )
    lines.append(
        f"| -1 sprint (avg cost) | {fmt_money(minus1_ai, currency)} | {fmt_money(minus1_std, currency)} |"
    )
    if delta_engineer_ai > 0:
        lines.append(
            f"| +1 Full Stack Engineer (100% across project) | "
            f"{fmt_money(grand_ai + delta_engineer_ai, currency)} | "
            f"{fmt_money(grand_std + delta_engineer_std, currency)} |"
        )
        lines.append(
            f"| -1 Full Stack Engineer | "
            f"{fmt_money(max(grand_ai - delta_engineer_ai, 0), currency)} | "
            f"{fmt_money(max(grand_std - delta_engineer_std, 0), currency)} |"
        )
    lines.append("")

    lines.append("## Notes")
    lines.append("")
    lines.append("This estimate is generated by `skills/p2c/scripts/estimate_cost.py` from `references/rate-card.md`.")
    lines.append("To regenerate, update the sprint plan and rerun.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate cost estimate from a sprint plan.")
    parser.add_argument("--plan", required=False, help="Path to sprint plan (.md or .yaml/.yml)")
    parser.add_argument("--output", required=False, help="Path to write the estimate markdown")
    parser.add_argument("--rate-card", default=str(RATE_CARD_PATH), help="Path to rate card markdown")
    parser.add_argument("--list-roles", action="store_true", help="Print available role keys and exit")
    parser.add_argument("--json", action="store_true", help="Emit a JSON summary to stdout instead of markdown")
    args = parser.parse_args()

    rate_card = load_rate_card(Path(args.rate_card))

    if args.list_roles:
        print("Available role keys:")
        for r in rate_card["ordered"]:
            print(f"  {r['key']:20s}  {r['role']:25s}  std=${r['standard_hr']:.2f}/h  ai=${r['ai_assisted_hr']:.2f}/h")
        return 0

    if not args.plan:
        parser.error("--plan is required (unless using --list-roles)")
    plan_path = Path(args.plan)
    if not plan_path.exists():
        raise SystemExit(f"Plan not found: {plan_path}")

    sprints = parse_plan(plan_path)
    if not sprints:
        raise SystemExit(f"No sprints found in {plan_path}")

    if args.json:
        # Emit a structured JSON for the visual server / other tooling
        out: dict[str, Any] = {
            "currency": rate_card["currency"],
            "sprints": [],
            "totals": {"ai_assisted": 0.0, "standard": 0.0},
        }
        for entry in sprints:
            hours = {k: float(v) for k, v in (entry.get("hours_by_role") or {}).items()}
            std_cost, _ = sprint_cost(hours, rate_card, "standard_hr")
            ai_cost, _ = sprint_cost(hours, rate_card, "ai_assisted_hr")
            out["sprints"].append(
                {
                    "sprint": entry.get("sprint"),
                    "goal": entry.get("goal", ""),
                    "hours_by_role": hours,
                    "ai_assisted": ai_cost,
                    "standard": std_cost,
                }
            )
            out["totals"]["ai_assisted"] += ai_cost
            out["totals"]["standard"] += std_cost
        print(json.dumps(out, indent=2))
        return 0

    report = render_report(sprints, rate_card)

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(report, encoding="utf-8")
        print(f"Wrote {out_path}")
    else:
        sys.stdout.write(report)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
