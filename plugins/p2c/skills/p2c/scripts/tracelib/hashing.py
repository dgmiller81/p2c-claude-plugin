from __future__ import annotations

import hashlib
import re

from tracelib.sidecar import Sidecar

HASH_LENGTH = 6
_WHITESPACE = re.compile(r"\s+")


def _normalize(text: str) -> str:
    return _WHITESPACE.sub(" ", text).strip()


def normative_text(sc: Sidecar) -> str:
    """Extract the normative text from a sidecar for hashing.

    Normative fields are those whose changes should trigger a hash change
    (indicating staleness in downstream artifacts).

    Type-dispatch contract:
    - For type "requirement": only statement and acceptance_criteria are
      normative. Changes to priority, source, version, or any other fields
      do NOT change the hash.
    - For every other type: title and the prose body are normative.
    - An unrecognized or absent type falls into the non-requirement branch
      (title + body). Callers MUST run tracelib.schema.validate() first to
      ensure schema correctness. The trace.py CLI does this and returns
      exit code 2 on schema errors before any hashing occurs.

    Args:
        sc: A Sidecar artifact with frontmatter and body.

    Returns:
        Whitespace-normalized normative text, with parts joined by newlines.
    """
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
