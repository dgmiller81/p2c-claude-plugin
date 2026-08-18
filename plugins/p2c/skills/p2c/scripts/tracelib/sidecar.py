from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tracelib.errors import SidecarError

try:
    import yaml
except ModuleNotFoundError as exc:  # pragma: no cover - environment guard
    raise SystemExit(
        "trace.py requires PyYAML. Install it with:  python -m pip install pyyaml"
    ) from exc

DELIMITER = "---"
SKIP_DIRS = {"traceability", "reviews", ".git", "__pycache__"}


@dataclass(frozen=True)
class Sidecar:
    path: Path
    frontmatter: dict[str, Any]
    body: str

    @property
    def id(self) -> str:
        return str(self.frontmatter.get("id", ""))

    @property
    def type(self) -> str:
        return str(self.frontmatter.get("type", ""))


def parse_sidecar(path: Path) -> Sidecar:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    if not lines or lines[0].rstrip() != DELIMITER:
        raise SidecarError(path, "missing YAML frontmatter opening delimiter")

    try:
        end = next(
            i for i in range(1, len(lines)) if lines[i].rstrip() == DELIMITER
        )
    except StopIteration:
        raise SidecarError(path, "unterminated YAML frontmatter") from None

    raw = "\n".join(lines[1:end])
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise SidecarError(path, f"malformed YAML frontmatter: {exc}") from exc

    if not isinstance(data, dict):
        raise SidecarError(path, "frontmatter must be a YAML mapping")

    return Sidecar(
        path=path, frontmatter=data, body="\n".join(lines[end + 1 :])
    )


def _has_frontmatter(path: Path) -> bool:
    """True if the file opens with a YAML frontmatter delimiter.

    A p2c workspace holds prose (prd.md, jtbd.md, ADRs, runbooks) alongside
    sidecars. Prose is not a malformed sidecar, and letting it raise takes
    the whole run down with an exit-2 before a single check can run. A file
    that *does* open with the delimiter is still parsed strictly, so a
    corrupted sidecar remains an error rather than being silently skipped.

    Matches parse_sidecar's own comparison (`lines[0].rstrip()`), so a line
    with leading whitespace is not frontmatter in either place.
    """
    try:
        with path.open(encoding="utf-8") as handle:
            first = handle.readline()
    except (OSError, UnicodeDecodeError):
        return False
    return first.rstrip() == DELIMITER


def load_workspace(root: Path) -> list[Sidecar]:
    found: list[Sidecar] = []
    for path in sorted(root.rglob("*.md")):
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        if not _has_frontmatter(path):
            continue
        # SidecarError propagates deliberately: an unparseable sidecar is an
        # exit-2 condition, not something to skip past.
        found.append(parse_sidecar(path))
    return found
