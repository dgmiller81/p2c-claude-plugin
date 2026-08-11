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

    if not lines or lines[0].strip() != DELIMITER:
        raise SidecarError(path, "missing YAML frontmatter opening delimiter")

    try:
        end = next(
            i for i in range(1, len(lines)) if lines[i].strip() == DELIMITER
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


def load_workspace(root: Path) -> list[Sidecar]:
    found: list[Sidecar] = []
    for path in sorted(root.rglob("*.md")):
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        try:
            found.append(parse_sidecar(path))
        except SidecarError:
            raise
    return found
