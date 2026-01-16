"""Pure formatter functions extracted from definition_generator_tab.py.

These are stateless utility functions for formatting definition-related data
for display in the UI. No session state access, no side effects.
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from database.definitie_repository import DefinitieRecord

logger = logging.getLogger(__name__)


def format_record_context(def_record: DefinitieRecord) -> tuple[str, str, str]:
    """Format context fields from DefinitieRecord for display.

    DefinitieRecord stores org/jur as TEXT; for V2 this may be JSON arrays.
    This helper safely parses and creates a short display string.

    Args:
        def_record: The definition record to format

    Returns:
        Tuple of (org_display, jur_display, wet_display) as comma-separated strings
    """

    def _parse(val: str | list[str] | None) -> list[str]:
        """Parse context value to list of strings.

        Handles JSON arrays, plain strings, or existing lists.
        """
        if val is None or val == "":
            return []

        # Already a list - ensure all items are strings
        if isinstance(val, list):
            return [str(item) for item in val if item is not None]

        # String value - try JSON parse if it looks like an array
        if isinstance(val, str):
            stripped = val.strip()
            if stripped.startswith("["):
                try:
                    parsed = json.loads(stripped)
                    if isinstance(parsed, list):
                        return [str(item) for item in parsed if item is not None]
                    # JSON parsed to non-list (e.g., number), return as string
                    logger.warning(
                        f"Expected JSON array, got {type(parsed).__name__}: {val!r}"
                    )
                    return [str(parsed)]
                except json.JSONDecodeError as e:
                    logger.warning(f"Invalid JSON in context field: {e}")
                    return [val]  # Return raw string as fallback
            # Plain string, not JSON
            return [val]

        # Unexpected type - log and return empty
        logger.error(f"Unexpected type in _parse: {type(val).__name__}")
        return []

    org_list = _parse(getattr(def_record, "organisatorische_context", None))
    jur_list = _parse(getattr(def_record, "juridische_context", None))
    wet_list: list[str] = []
    if hasattr(def_record, "get_wettelijke_basis_list"):
        wet_list = def_record.get_wettelijke_basis_list() or []
    return ", ".join(org_list), ", ".join(jur_list), ", ".join(wet_list)


def get_provider_label(provider: str) -> str:
    """Get human-friendly label for web lookup provider.

    Args:
        provider: Provider key (e.g., 'wikipedia', 'overheid')

    Returns:
        Human-readable label (e.g., 'Wikipedia NL', 'Overheid.nl')
    """
    labels = {
        "wikipedia": "Wikipedia NL",
        "overheid": "Overheid.nl",
        "rechtspraak": "Rechtspraak.nl",
        "wiktionary": "Wiktionary NL",
    }
    return labels.get(provider, provider.replace("_", " ").title())


def get_category_display_name(category: str) -> str:
    """Get user-friendly display name for ontological/UFO category.

    Args:
        category: Category key (e.g., 'type', 'proces', 'ENT')

    Returns:
        Display name with emoji (e.g., 'Type/Klasse', 'Entiteit')
    """
    category_names = {
        # Ontological categories
        "type": "Type/Klasse",
        "proces": "Proces/Activiteit",
        "resultaat": "Resultaat/Uitkomst",
        "exemplaar": "Exemplaar/Instantie",
        # UFO categories
        "ENT": "Entiteit",
        "ACT": "Activiteit",
        "REL": "Relatie",
        "ATT": "Attribuut",
        "AUT": "Autorisatie",
        "STA": "Status",
        "OTH": "Overig",
    }
    return category_names.get(category, category)


def extract_definition_from_result(generation_result: dict[str, Any]) -> str:
    """Extract definition text from generation result, regardless of format.

    Handles both V2 dict format and legacy object format.

    Args:
        generation_result: Complete generation result dict

    Returns:
        The final definition text, or empty string if not found
    """
    agent_result = generation_result.get("agent_result")
    if not agent_result:
        return ""

    # V2 dict format (new service)
    if isinstance(agent_result, dict):
        result = agent_result.get(
            "definitie_gecorrigeerd", agent_result.get("definitie", "")
        )
        return result if isinstance(result, str) else ""

    # Legacy object format
    legacy_result = getattr(agent_result, "final_definitie", "")
    return legacy_result if isinstance(legacy_result, str) else ""
