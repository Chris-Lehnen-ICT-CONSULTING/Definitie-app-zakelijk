"""
Toetsregels loader - vervangt de oude config_loader.

Deze module laadt toetsregels uit individuele JSON bestanden
in plaats van het monolithische toetsregels.json.

Gebruikt CachedToetsregelManager voor optimale performance (US-202).
"""

import logging

from .cached_manager import get_cached_toetsregel_manager

logger = logging.getLogger(__name__)


def load_toetsregels() -> dict[str, dict]:
    """
    Laadt alle toetsregels uit individuele JSON bestanden (GECACHED).

    Dit is een vervanging voor de oude laad_toetsregels() functie
    die het monolithische toetsregels.json gebruikte.

    Gebruikt nu CachedToetsregelManager die RuleCache gebruikt voor
    snelle bulk loading (1x i.p.v. 10x).

    Returns:
        Dictionary met alle toetsregels, key is regel ID
    """
    # Gebruik gecachte manager voor optimale performance
    manager = get_cached_toetsregel_manager()

    # get_all_regels() is GECACHED - laadt slechts 1x per sessie
    toetsregels = manager.get_all_regels()

    logger.info(f"Geladen {len(toetsregels)} toetsregels uit cache")

    return {"regels": toetsregels}  # Wrap in "regels" voor compatibility


def get_toetsregels() -> dict[str, dict]:
    """
    Alias voor load_toetsregels voor backward compatibility.

    Returns:
        Dictionary met alle toetsregels
    """
    return load_toetsregels()


# Voor backward compatibility
laad_toetsregels = load_toetsregels
