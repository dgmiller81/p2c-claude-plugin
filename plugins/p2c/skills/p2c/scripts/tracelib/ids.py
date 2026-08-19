from __future__ import annotations

import re

PREFIX_TO_TYPE: dict[str, str] = {
    "BR": "requirement",
    "FR": "requirement",
    "NFR": "requirement",
    "P": "persona",
    "J": "journey",
    "SCR": "screen",
    "ARC": "component",
    "US": "story",
    "TC": "test",
    "FND": "finding",
}

_THREE_DIGIT = re.compile(r"^(BR|FR|NFR|SCR|ARC|US|TC|FND)-\d{3}\Z")
_TWO_DIGIT = re.compile(r"^(P|J)-\d{2}\Z")
_JOURNEY_STEP = re.compile(r"^J-\d{2}\.\d+\Z")


def id_type(artifact_id: str) -> str | None:
    if _JOURNEY_STEP.match(artifact_id):
        return "journey_step"
    match = _THREE_DIGIT.match(artifact_id) or _TWO_DIGIT.match(artifact_id)
    if match:
        return PREFIX_TO_TYPE[match.group(1)]
    return None


def is_valid_id(artifact_id: str) -> bool:
    return id_type(artifact_id) is not None


def journey_step_parent(step_id: str) -> str | None:
    if not _JOURNEY_STEP.match(step_id):
        return None
    return step_id.split(".", 1)[0]
