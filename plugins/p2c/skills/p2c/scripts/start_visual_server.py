#!/usr/bin/env python3
"""
start_visual_server.py — Local visual guidance server for the p2c skill.

Serves an interactive web UI at http://localhost:<port> that mirrors the p2c
phase questions and shows live status of `p2c-workspace/`. The orchestrator
points the user here whenever a phase is easier to navigate visually.

Endpoints:
  GET  /                       → dashboard (status of all phases)
  GET  /phase/<n>              → questionnaire for a phase
  GET  /storymap               → story-map canvas
  GET  /journey                → journey-map canvas
  GET  /sprint                 → sprint-plan timeline
  GET  /cost                   → cost-estimate viewer
  GET  /api/status             → JSON: workspace status
  POST /api/intake/<phase>     → save phase intake JSON
  POST /api/storymap           → save story map
  POST /api/journey            → save journey map
  GET  /api/cost               → JSON: latest cost estimate (runs estimate_cost.py)

Designed to use only Python stdlib so it runs anywhere with Python 3.10+.

Usage:
  python start_visual_server.py --workspace p2c-workspace --port 8765
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import threading
import webbrowser
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
ASSETS_DIR = SKILL_ROOT / "assets" / "visual_guide"


# Module-global state set in main()
WORKSPACE: Path | None = None
PORT: int = 8765


def workspace() -> Path:
    if WORKSPACE is None:
        raise RuntimeError("WORKSPACE not initialized")
    return WORKSPACE


def status_path() -> Path:
    return workspace() / "status.json"


def ensure_workspace() -> None:
    ws = workspace()
    ws.mkdir(parents=True, exist_ok=True)
    if not status_path().exists():
        seed = {
            "current_command": None,
            "current_phase": 1,
            "phases": {
                str(i): {"status": "pending", "files": [], "skipped_items": []}
                for i in range(1, 9)
            },
            "decisions_log": [],
        }
        status_path().write_text(json.dumps(seed, indent=2), encoding="utf-8")


def read_status() -> dict:
    ensure_workspace()
    return json.loads(status_path().read_text(encoding="utf-8"))


def write_status(data: dict) -> None:
    status_path().write_text(json.dumps(data, indent=2), encoding="utf-8")


def save_intake(phase: int, payload: dict) -> Path:
    phase_dir_map = {
        1: "01-discovery",
        2: "02-requirements",
        3: "03-design",
        4: "04-architecture",
        5: "05-build",
        6: "06-test-and-harden",
        7: "07-launch",
        8: "08-measure",
    }
    folder = phase_dir_map.get(phase)
    if not folder:
        raise ValueError(f"Unknown phase: {phase}")
    out_dir = workspace() / folder
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "intake.json"
    payload = dict(payload)
    payload["_saved_at"] = datetime.now(timezone.utc).isoformat()
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return out_path


def run_cost_estimate() -> dict:
    plan_path = workspace() / "plan" / "sprint-plan.md"
    if not plan_path.exists():
        return {"error": f"No sprint plan at {plan_path}. Generate one first."}
    cmd = [
        sys.executable,
        str(SCRIPT_DIR / "estimate_cost.py"),
        "--plan",
        str(plan_path),
        "--json",
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    except subprocess.TimeoutExpired:
        return {"error": "estimate_cost.py timed out"}
    if result.returncode != 0:
        return {"error": result.stderr or "estimate_cost.py failed"}
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        return {"error": f"Could not parse estimator JSON: {e}", "raw": result.stdout}


class Handler(BaseHTTPRequestHandler):
    server_version = "p2c-visual/0.1"

    # --- helpers ---------------------------------------------------------

    def _send(self, status: int, body: bytes, content_type: str = "text/html; charset=utf-8") -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self._send(status, body, "application/json")

    def _html_page(self, title: str, body_html: str) -> bytes:
        page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} · p2c</title>
<link rel="stylesheet" href="/static/styles.css">
</head>
<body>
<header>
  <h1><a href="/">p2c</a> <span class="muted">/ {title}</span></h1>
  <nav>
    <a href="/">Dashboard</a>
    <a href="/phase/1">1 Discovery</a>
    <a href="/phase/2">2 Requirements</a>
    <a href="/phase/3">3 Design</a>
    <a href="/phase/4">4 Architecture</a>
    <a href="/phase/5">5 Build</a>
    <a href="/phase/6">6 Test/Harden</a>
    <a href="/phase/7">7 Launch</a>
    <a href="/phase/8">8 Measure</a>
    <span class="sep">·</span>
    <a href="/storymap">Story Map</a>
    <a href="/journey">Journey</a>
    <a href="/sprint">Sprint</a>
    <a href="/cost">Cost</a>
  </nav>
</header>
<main>
{body_html}
</main>
<script src="/static/app.js"></script>
</body>
</html>"""
        return page.encode("utf-8")

    # --- routing ---------------------------------------------------------

    def do_GET(self):  # noqa: N802
        url = urlparse(self.path)
        path = url.path

        try:
            if path == "/":
                return self._send(HTTPStatus.OK, self._render_dashboard())
            if path == "/static/styles.css":
                return self._send(HTTPStatus.OK, (ASSETS_DIR / "styles.css").read_bytes(), "text/css")
            if path == "/static/app.js":
                return self._send(HTTPStatus.OK, (ASSETS_DIR / "app.js").read_bytes(), "application/javascript")
            if path.startswith("/phase/"):
                phase = int(path.split("/")[-1])
                return self._send(HTTPStatus.OK, self._render_phase(phase))
            if path == "/storymap":
                return self._send(HTTPStatus.OK, self._render_storymap())
            if path == "/journey":
                return self._send(HTTPStatus.OK, self._render_journey())
            if path == "/sprint":
                return self._send(HTTPStatus.OK, self._render_sprint())
            if path == "/cost":
                return self._send(HTTPStatus.OK, self._render_cost())

            if path == "/api/status":
                return self._json(HTTPStatus.OK, read_status())
            if path == "/api/cost":
                return self._json(HTTPStatus.OK, run_cost_estimate())

            self._send(HTTPStatus.NOT_FOUND, b"Not found")
        except FileNotFoundError as e:
            self._send(HTTPStatus.INTERNAL_SERVER_ERROR, f"Asset missing: {e}".encode())
        except Exception as e:  # noqa: BLE001
            self._send(HTTPStatus.INTERNAL_SERVER_ERROR, f"Server error: {e}".encode())

    def do_POST(self):  # noqa: N802
        url = urlparse(self.path)
        path = url.path
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b""
        try:
            payload = json.loads(raw or b"{}")
        except json.JSONDecodeError:
            return self._json(HTTPStatus.BAD_REQUEST, {"error": "invalid JSON"})

        try:
            if path.startswith("/api/intake/"):
                phase = int(path.split("/")[-1])
                out = save_intake(phase, payload)
                return self._json(HTTPStatus.OK, {"saved": str(out)})
            if path == "/api/storymap":
                ws = workspace() / "02-requirements"
                ws.mkdir(parents=True, exist_ok=True)
                out = ws / "story-map.json"
                out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
                return self._json(HTTPStatus.OK, {"saved": str(out)})
            if path == "/api/journey":
                ws = workspace() / "03-design"
                ws.mkdir(parents=True, exist_ok=True)
                out = ws / "journey-map.json"
                out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
                return self._json(HTTPStatus.OK, {"saved": str(out)})
            self._json(HTTPStatus.NOT_FOUND, {"error": "no such endpoint"})
        except Exception as e:  # noqa: BLE001
            self._json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(e)})

    # --- views -----------------------------------------------------------

    def _render_dashboard(self) -> bytes:
        s = read_status()
        phase_titles = {
            "1": "Discovery & Validation",
            "2": "Requirements & Scope",
            "3": "Design",
            "4": "Technical Architecture",
            "5": "Build (MVP)",
            "6": "Test & Harden",
            "7": "Launch",
            "8": "Measure & Iterate",
        }
        cards = []
        for k in sorted(phase_titles, key=int):
            ph = s["phases"].get(k, {"status": "pending", "files": [], "skipped_items": []})
            badge = ph.get("status", "pending")
            files = "<br>".join(f"<code>{f}</code>" for f in ph.get("files", [])) or '<span class="muted">none yet</span>'
            cards.append(f"""
              <a class="card status-{badge}" href="/phase/{k}">
                <div class="phase-no">{k}</div>
                <div class="phase-title">{phase_titles[k]}</div>
                <div class="phase-status">{badge.replace('_', ' ')}</div>
                <div class="phase-files">{files}</div>
              </a>""")
        body = f"""
        <section class="hero">
          <p>Workspace: <code>{workspace()}</code></p>
          <p>Current command: <code>{s.get('current_command') or '—'}</code> · Current phase: <strong>{s.get('current_phase')}</strong></p>
        </section>
        <section class="grid">
          {''.join(cards)}
        </section>
        """
        return self._html_page("Dashboard", body)

    def _render_phase(self, phase: int) -> bytes:
        questions = PHASE_QUESTIONS.get(phase, [])
        if not questions:
            return self._html_page(
                f"Phase {phase}", "<p>No phase questions defined.</p>"
            )
        rows = []
        for q in questions:
            qid = q["id"]
            label = q["label"]
            help_ = q.get("help", "")
            rows.append(f"""
              <label class="q">
                <span class="q-label">{label}</span>
                <small class="muted">{help_}</small>
                <textarea name="{qid}" rows="3" data-phase="{phase}" data-qid="{qid}"></textarea>
              </label>""")
        body = f"""
        <section>
          <h2>Phase {phase} intake</h2>
          <p class="muted">Answers auto-save. The orchestrator reads <code>p2c-workspace/&lt;phase-folder&gt;/intake.json</code>.</p>
          <form id="phase-form" data-phase="{phase}">
            {''.join(rows)}
          </form>
          <p><button id="save-now" type="button">Save now</button> <span id="save-status" class="muted"></span></p>
        </section>
        """
        return self._html_page(f"Phase {phase}", body)

    def _render_storymap(self) -> bytes:
        body = """
        <section>
          <h2>Story map canvas</h2>
          <p class="muted">Drag activities (top row) and tasks (below) into a backbone-and-slices grid. Submit to save as <code>p2c-workspace/02-requirements/story-map.json</code>.</p>
          <div id="storymap"></div>
          <button id="storymap-save" type="button">Save story map</button>
          <span id="storymap-status" class="muted"></span>
        </section>
        """
        return self._html_page("Story Map", body)

    def _render_journey(self) -> bytes:
        body = """
        <section>
          <h2>Journey map</h2>
          <p class="muted">Capture user journey stages and the emotion/pain at each step. Saves to <code>p2c-workspace/03-design/journey-map.json</code>.</p>
          <div id="journey"></div>
          <button id="journey-save" type="button">Save journey</button>
          <span id="journey-status" class="muted"></span>
        </section>
        """
        return self._html_page("Journey", body)

    def _render_sprint(self) -> bytes:
        body = """
        <section>
          <h2>Sprint timeline</h2>
          <p class="muted">Reads <code>p2c-workspace/plan/sprint-plan.md</code> via the cost estimator. Update the plan and refresh.</p>
          <div id="sprint"></div>
        </section>
        """
        return self._html_page("Sprint", body)

    def _render_cost(self) -> bytes:
        body = """
        <section>
          <h2>Cost estimate</h2>
          <p class="muted">Pulled live from <code>scripts/estimate_cost.py --json</code>.</p>
          <div id="cost"></div>
          <p>
            <label><input type="checkbox" id="cost-ai" checked> Show AI-assisted rates</label>
            <label><input type="checkbox" id="cost-std" checked> Show standard rates</label>
          </p>
        </section>
        """
        return self._html_page("Cost", body)

    # Quiet the default access log
    def log_message(self, format: str, *args) -> None:  # noqa: A002
        return


# Phase intake question definitions — kept short; the orchestrator handles depth.
PHASE_QUESTIONS: dict[int, list[dict]] = {
    1: [
        {"id": "jtbd", "label": "Job-to-be-Done", "help": "When [situation], I want to [motivation], so I can [outcome]."},
        {"id": "primary_user", "label": "Primary user", "help": "One persona, not three."},
        {"id": "current_workaround", "label": "Current workaround", "help": "What do they do today?"},
        {"id": "kill_criteria", "label": "Kill criteria", "help": "What evidence would tell you to stop?"},
        {"id": "competitors", "label": "Top competitors / alternatives", "help": "Including 'do nothing'."},
    ],
    2: [
        {"id": "outcome", "label": "Desired outcome", "help": "Measurable user change."},
        {"id": "success_metric", "label": "Success metric", "help": "Number + timeframe."},
        {"id": "must_haves", "label": "MoSCoW: Must", "help": "MVP fails without these."},
        {"id": "out_of_scope", "label": "Explicitly out of scope", "help": "What we won't do."},
        {"id": "nfrs", "label": "Non-functional requirements", "help": "Perf, security, compliance, a11y."},
    ],
    3: [
        {"id": "golden_path", "label": "Golden path", "help": "Click-by-click of the primary flow."},
        {"id": "critical_screens", "label": "Critical screens (3–5)", "help": "Where to focus design."},
        {"id": "states", "label": "Per-screen states", "help": "Empty, loading, error, success."},
        {"id": "design_system", "label": "Design system base", "help": "shadcn/ui, Material, Tailwind UI, etc."},
    ],
    4: [
        {"id": "scale", "label": "Load assumptions", "help": "Peak users, data volume, request rate."},
        {"id": "stack", "label": "Stack defaults", "help": "DB, framework, hosting, auth, payments."},
        {"id": "data_model", "label": "Core entities", "help": "5–10 tables for an MVP."},
        {"id": "trust_boundaries", "label": "Trust boundaries", "help": "Who can access what?"},
        {"id": "obs", "label": "Observability tooling", "help": "Sentry + logs/metrics/traces."},
    ],
    5: [
        {"id": "skeleton", "label": "Walking-skeleton scope", "help": "Smallest end-to-end slice."},
        {"id": "first_slices", "label": "First 3 vertical slices", "help": "By risk."},
        {"id": "ci", "label": "CI provider", "help": "GitHub Actions, GitLab CI, etc."},
        {"id": "feature_flags", "label": "Feature flag tool", "help": "PostHog, LaunchDarkly, ConfigCat."},
    ],
    6: [
        {"id": "critical_paths", "label": "Critical-path E2E flows", "help": "3–5 max."},
        {"id": "perf_budgets", "label": "Performance budgets", "help": "LCP, INP, CLS, API p95."},
        {"id": "security_scope", "label": "Security scope", "help": "OWASP coverage, pen test?"},
        {"id": "a11y", "label": "Accessibility target", "help": "WCAG 2.1 AA default."},
    ],
    7: [
        {"id": "soft_cohort", "label": "Soft launch cohort", "help": "10–100 users."},
        {"id": "rollout", "label": "Rollout %s", "help": "Day 1 / Day 3 / Day 7 / Day 14."},
        {"id": "rollback", "label": "Rollback decision criteria", "help": "Error rate, latency, conversion thresholds."},
        {"id": "comms", "label": "Comms channels", "help": "Landing page, email, social, support FAQ."},
        {"id": "oncall", "label": "On-call rotation", "help": "First 72 hours."},
    ],
    8: [
        {"id": "north_star", "label": "North Star metric", "help": "One metric capturing product value."},
        {"id": "activation", "label": "Activation event", "help": "Single most predictive event for retention."},
        {"id": "cadence", "label": "Weekly cadence", "help": "Mon metrics, Tue/Wed research, Thu prioritize, Fri ship."},
        {"id": "experiments", "label": "First 3 experiments", "help": "Hypothesis + metric."},
    ],
}


def main() -> int:
    global WORKSPACE, PORT
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", default="p2c-workspace", help="Path to workspace")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true", help="Don't open a browser tab")
    args = parser.parse_args()

    WORKSPACE = Path(args.workspace).resolve()
    PORT = args.port
    ensure_workspace()

    if not ASSETS_DIR.exists():
        print(f"WARNING: assets directory missing: {ASSETS_DIR}", file=sys.stderr)

    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    url = f"http://127.0.0.1:{PORT}"
    print(f"p2c visual server: {url}")
    print(f"workspace: {WORKSPACE}")
    print("Ctrl-C to stop.")

    if not args.no_browser:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nshutting down")
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
