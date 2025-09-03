"""
Provenance helpers to project lookup results into definition metadata (Epic 3).
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Any, Optional


def build_provenance(results: Iterable[dict[str, Any]], extract_legal: bool = False) -> list[dict[str, Any]]:
    """Build a list of simplified source dicts for UI/storage.

    Retains essential fields and sorts by score descending.
    Optionally extracts legal metadata for juridical sources.
    """
    simplified: list[dict[str, Any]] = []
    for r in results or []:
        source_dict = {
            "provider": r.get("provider"),
            "source_label": _get_provider_label(r.get("provider", "")),
            "title": r.get("title"),
            "url": r.get("url"),
            "snippet": r.get("snippet"),
            "score": float(r.get("score", 0.0) or 0.0),
            "used_in_prompt": bool(r.get("used_in_prompt", False)),
            "retrieved_at": r.get("retrieved_at"),
            "is_authoritative": _is_authoritative_source(r.get("provider", "")),
        }
        
        # Extract legal metadata if requested and source is legal
        if extract_legal and r.get("provider") in ["rechtspraak", "overheid"]:
            legal_meta = _extract_legal_metadata_from_dict(r)
            if legal_meta:
                source_dict["legal"] = legal_meta
        
        simplified.append(source_dict)

    simplified.sort(key=lambda x: x.get("score", 0.0), reverse=True)
    return simplified


def _get_provider_label(provider: str) -> str:
    """Get human-friendly label for provider."""
    labels = {
        "wikipedia": "Wikipedia NL",
        "overheid": "Overheid.nl",
        "rechtspraak": "Rechtspraak.nl",
        "wiktionary": "Wiktionary NL",
    }
    return labels.get(provider, provider.replace("_", " ").title())


def _is_authoritative_source(provider: str) -> bool:
    """Check if source is considered authoritative."""
    return provider in ["rechtspraak", "overheid"]


def _extract_legal_metadata(result) -> Optional[dict[str, Any]]:
    """Extract juridical metadata from legal sources.
    
    This version works with objects that have attributes.
    """
    if not hasattr(result, 'provider') or result.provider not in ["overheid", "rechtspraak"]:
        return None
    
    legal = {}
    metadata = result.metadata if hasattr(result, 'metadata') else {}
    
    # Parse ECLI for rechtspraak
    if "dc_identifier" in metadata:
        ecli_match = re.search(r"ECLI:[A-Z:0-9]+", metadata["dc_identifier"])
        if ecli_match:
            legal["ecli"] = ecli_match.group()
    
    # Parse artikel/wet uit title/subject
    title = metadata.get("dc_title", "")
    if match := re.search(r"(?:artikel|art\.?)\s+(\d+(?::\d+)?[a-z]?)", title, re.I):
        legal["article"] = match.group(1)
    if match := re.search(r"(Wetboek van \w+|Wv\w+|Burgerlijk Wetboek|BW|EVRM)", title):
        legal["law"] = match.group(1)
    
    # Generate citation_text
    if legal.get("ecli"):
        legal["citation_text"] = legal["ecli"]
    elif legal.get("article") and legal.get("law"):
        legal["citation_text"] = f"art. {legal['article']} {legal['law']}"
    
    return legal if legal else None


def _extract_legal_metadata_from_dict(result_dict: dict[str, Any]) -> Optional[dict[str, Any]]:
    """Extract juridical metadata from legal sources in dict format."""
    provider = result_dict.get("provider", "")
    if provider not in ["overheid", "rechtspraak"]:
        return None
    
    legal = {}
    metadata = result_dict.get("metadata", {})
    title = result_dict.get("title", "")
    
    # Try to extract from metadata first, then from title
    identifier = metadata.get("dc_identifier", "") or title
    
    # Parse ECLI for rechtspraak
    if provider == "rechtspraak" and identifier:
        ecli_match = re.search(r"ECLI:[A-Z:0-9]+", identifier)
        if ecli_match:
            legal["ecli"] = ecli_match.group()
            legal["citation_text"] = legal["ecli"]
            return legal
    
    # Parse artikel/wet for overheid sources
    if provider == "overheid":
        # Try to extract article number
        if match := re.search(r"(?:artikel|art\.?)\s+(\d+(?::\d+)?[a-z]?)", title, re.I):
            legal["article"] = match.group(1)
        
        # Try to extract law name
        if match := re.search(r"(Wetboek van \w+|Burgerlijk Wetboek|BW|Wetboek van Strafrecht|Sr|EVRM)", title):
            legal["law"] = match.group(1)
        
        # Generate citation if we have both
        if legal.get("article") and legal.get("law"):
            # Abbreviate common laws
            law_abbr = legal["law"]
            if "Burgerlijk" in law_abbr:
                law_abbr = "BW"
            elif "Strafrecht" in law_abbr:
                law_abbr = "Sr"
            legal["citation_text"] = f"art. {legal['article']} {law_abbr}"
    
    return legal if legal else None