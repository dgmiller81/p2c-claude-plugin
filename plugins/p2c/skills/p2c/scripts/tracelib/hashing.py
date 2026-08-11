from __future__ import annotations

import hashlib
import re

from tracelib.sidecar import Sidecar

HASH_LENGTH = 6
_WHITESPACE = re.compile(r"\s+")


def _normalize(text: str) -> str:
    return _WHITESPACE.sub(" ", text).strip()


def normative_text(sc: Sidecar) -> str:
    fm = sc.frontmatter
    if sc.type == "requirement":
        criteria = fm.get("acceptance_criteria") or []
        parts = [str(fm.get("statement", ""))] + [str(c) for c in criteria]
    else:
        parts = [str(fm.get("title", "")), sc.body]
    return "\n".join(_normalize(p) for p in parts)


def normative_hash(sc: Sidecar) -> str:
    digest = hashlib.sha256(normative_text(sc).encode("utf-8")).hexdigest()
    return digest[:HASH_LENGTH]
