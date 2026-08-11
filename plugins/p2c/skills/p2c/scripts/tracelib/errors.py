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
