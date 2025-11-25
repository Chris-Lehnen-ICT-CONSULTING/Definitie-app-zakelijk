"""Example formatting utilities.

Pure functions for transforming and canonicalizing examples (voorbeelden).
Moved from ui/helpers/examples.py to fix layer separation (DEF-173).
"""

from __future__ import annotations

import re
from typing import Any


def _to_list(val: Any) -> list[str]:
    """Convert various input types to a list of strings.

    Args:
        val: Input value (list, string, or other)

    Returns:
        List of stripped, non-empty strings
    """
    if isinstance(val, list):
        return [str(x).strip() for x in val if str(x).strip()]
    if isinstance(val, str):
        s = val.strip()
        if not s:
            return []
        # Support diverse scheiders: komma, puntkomma, pipe, nieuwe regel,
        # en bullet/asterisk/hyphen varianten met spaties eromheen
        parts = re.split(r"(?:,|;|\||\r?\n|\s+[•*\--—]\s+)+", s)
        out: list[str] = []
        for p in parts:
            t = str(p).strip().lstrip("*•--— ")
            if t:
                out.append(t)
        return out
    return []


def canonicalize_examples(raw: dict[str, Any] | None) -> dict[str, Any]:
    """Map diverse voorbeeld-type keys naar de canonieke UI-sleutels.

    This is a pure function with no UI/Streamlit dependencies.

    Args:
        raw: Dictionary with various example key names

    Returns:
        Dict met keys: voorbeeldzinnen, praktijkvoorbeelden, tegenvoorbeelden,
        synoniemen, antoniemen, toelichting.
    """
    data = raw or {}
    out: dict[str, Any] = {
        "voorbeeldzinnen": [],
        "praktijkvoorbeelden": [],
        "tegenvoorbeelden": [],
        "synoniemen": [],
        "antoniemen": [],
        "toelichting": "",
    }

    # Key aliases per categorie
    aliases = {
        "voorbeeldzinnen": {
            "voorbeeldzinnen",
            "zinnen",
            "voorbeeldzin",
            "sentences",
            "sentence",
            "example_sentences",
        },
        "praktijkvoorbeelden": {
            "praktijkvoorbeelden",
            "praktijk",
            "praktijkvoorbeeld",
            "practical_examples",
            "practical",
        },
        "tegenvoorbeelden": {
            "tegenvoorbeelden",
            "tegen",
            "counterexamples",
            "counter",
        },
        "synoniemen": {"synoniemen", "synonym", "synonyms"},
        "antoniemen": {"antoniemen", "antonym", "antonyms"},
        "toelichting": {"toelichting", "uitleg", "notes", "comment", "explanation"},
    }

    # Lower-case keys for robust matching
    lower_map = {str(k).strip().lower(): v for k, v in (data or {}).items()}

    # Collect lists
    for canon, keys in aliases.items():
        if canon == "toelichting":
            continue
        items: list[str] = []
        for k in keys:
            if k in lower_map:
                items.extend(_to_list(lower_map[k]))
        # de-dup preserve order
        seen: set[str] = set()
        deduped: list[str] = []
        for it in items:
            if it not in seen:
                seen.add(it)
                deduped.append(it)
        out[canon] = deduped

    # Toelichting als string (neem eerste uit lijst indien nodig)
    for k in aliases["toelichting"]:
        if k in lower_map:
            val = lower_map[k]
            if isinstance(val, list):
                out["toelichting"] = str(val[0]).strip() if val else ""
            elif isinstance(val, str):
                out["toelichting"] = val.strip()
            break

    return out
