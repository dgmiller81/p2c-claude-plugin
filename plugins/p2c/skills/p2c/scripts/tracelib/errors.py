from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


class SidecarError(Exception):
    """Raised when a sidecar file cannot be parsed."""

    def __init__(self, path: Path, message: str) -> None:
        super().__init__(f"{path}: {message}")
        self.path = path
        self.message = message


@dataclass(frozen=True)
class SchemaError:
    path: Path
    subject: str
    field_name: str
    message: str


@dataclass(frozen=True)
class Gap:
    kind: str
    subject: str
    message: str


@dataclass(frozen=True)
class StaleEntry:
    subject: str
    reason: str
    changed_upstream: list[str] = field(default_factory=list)
    signoff_voided: bool = False
    # Upstream ID -> freshly computed normative_hash, for entries whose
    # reason is "upstream-changed". Lets a repairer see what value to write
    # into source_hash without hand-running normative_hash() themselves.
    # Left empty for "transitive" entries, whose repair follows from their
    # upstream's own direct entry. Kept last so existing positional
    # constructions of StaleEntry(subject, reason, changed_upstream,
    # signoff_voided) still work unchanged.
    current_hashes: dict[str, str] = field(default_factory=dict)
