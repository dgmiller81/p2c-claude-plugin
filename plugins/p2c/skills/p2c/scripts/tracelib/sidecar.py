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
    # "utf-8-sig" strips a leading BOM if one is present and decodes a
    # BOM-less file identically to "utf-8". Without it a BOM'd sidecar's
    # first line reads U+FEFF followed by "---", fails the delimiter
    # test, and the file is misreported as missing its frontmatter.
    # _has_frontmatter must use the same codec, or a BOM'd file passes the
    # probe and then fails here.
    text = path.read_text(encoding="utf-8-sig")
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
    with leading whitespace is not frontmatter in either place, and matches
    its codec ("utf-8-sig"), so a BOM'd sidecar is seen as frontmatter here
    and parses there. A BOM used to make a valid sidecar vanish from the
    graph silently; findings are graph leaves, so a vanished finding
    produces no gap and no signal at all.
    """
    try:
        with path.open(encoding="utf-8-sig") as handle:
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
