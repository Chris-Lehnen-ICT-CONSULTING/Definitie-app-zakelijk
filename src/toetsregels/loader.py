"""
Toetsregels loader - vervangt de oude config_loader.

Deze module laadt toetsregels uit individuele JSON bestanden
in plaats van het monolithische toetsregels.json.
"""

import logging
from typing import Dict

from .manager import get_toetsregel_manager

logger = logging.getLogger(__name__)


def load_toetsregels() -> Dict[str, Dict]:
    """
    Laadt alle toetsregels uit individuele JSON bestanden.

    Dit is een vervanging voor de oude laad_toetsregels() functie
    die het monolithische toetsregels.json gebruikte.

    Returns:
        Dictionary met alle toetsregels, key is regel ID
    """
    manager = get_toetsregel_manager()

    # Haal alle beschikbare regel IDs op
    regel_ids = manager.get_available_regels()

    # Laad elke regel
    toetsregels = {}
    for regel_id in regel_ids:
        regel_data = manager.load_regel(regel_id)
        if regel_data:
            # Zorg dat ID in de data zit voor backward compatibility
            regel_data["id"] = regel_id
            toetsregels[regel_id] = regel_data

    logger.info(f"Geladen {len(toetsregels)} toetsregels uit individuele bestanden")

    return {"regels": toetsregels}  # Wrap in "regels" voor compatibility


def get_toetsregels() -> Dict[str, Dict]:
    """
    Alias voor load_toetsregels voor backward compatibility.

    Returns:
        Dictionary met alle toetsregels
    """
    return load_toetsregels()


# Voor backward compatibility
laad_toetsregels = load_toetsregels
