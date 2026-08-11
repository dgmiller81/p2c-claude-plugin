from __future__ import annotations

from collections import Counter

from tracelib.errors import SchemaError
from tracelib.ids import id_type, is_valid_id
from tracelib.sidecar import Sidecar

REQUIRED_COMMON = ("id", "type", "title", "status")

REQUIRED_BY_TYPE: dict[str, tuple[str, ...]] = {
    "requirement": ("kind", "statement", "acceptance_criteria", "priority"),
    "persona": (),
    "journey": ("persona", "steps"),
    "screen": ("traces_to", "states"),
    "component": ("traces_to",),
    "story": ("traces_to",),
    "test": ("traces_to",),
}

ENUMS: dict[str, tuple[str, ...]] = {
    "kind": ("functional", "non-functional", "business"),
    "surface": ("ui", "system"),
    "priority": ("must", "should", "could", "wont"),
    "status": ("draft", "in-review", "approved", "stale", "baselined"),
}


def validate(sc: Sidecar) -> list[SchemaError]:
    errors: list[SchemaError] = []
    fm = sc.frontmatter
    subject = sc.id or str(sc.path.name)

    for name in REQUIRED_COMMON:
        if not fm.get(name):
            errors.append(
                SchemaError(sc.path, subject, name, f"missing required field '{name}'")
            )

    declared = sc.type
    if sc.id and not is_valid_id(sc.id):
        errors.append(
            SchemaError(sc.path, subject, "id", f"'{sc.id}' is not a well-formed ID")
        )
    elif sc.id and declared and id_type(sc.id) != declared:
        errors.append(
            SchemaError(
                sc.path,
                subject,
                "id",
                f"ID '{sc.id}' implies type '{id_type(sc.id)}' but type is '{declared}'",
            )
        )

    for name in REQUIRED_BY_TYPE.get(declared, ()):
        if not fm.get(name):
            errors.append(
                SchemaError(
                    sc.path, subject, name, f"'{declared}' requires field '{name}'"
                )
            )

    if declared == "requirement" and fm.get("kind") == "functional":
        if not fm.get("surface"):
            errors.append(
                SchemaError(
                    sc.path,
                    subject,
                    "surface",
                    "functional requirements require 'surface' (ui|system)",
                )
            )

    for name, allowed in ENUMS.items():
        value = fm.get(name)
        if value is not None and value not in allowed:
            errors.append(
                SchemaError(
                    sc.path,
                    subject,
                    name,
                    f"'{value}' not one of {', '.join(allowed)}",
                )
            )

    return errors


def validate_all(sidecars: list[Sidecar]) -> list[SchemaError]:
    errors: list[SchemaError] = []
    for sc in sidecars:
        errors.extend(validate(sc))

    counts = Counter(sc.id for sc in sidecars if sc.id)
    for artifact_id, count in sorted(counts.items()):
        if count > 1:
            offender = next(sc for sc in sidecars if sc.id == artifact_id)
            errors.append(
                SchemaError(
                    offender.path,
                    artifact_id,
                    "id",
                    f"duplicate ID '{artifact_id}' used {count} times",
                )
            )
    return errors
