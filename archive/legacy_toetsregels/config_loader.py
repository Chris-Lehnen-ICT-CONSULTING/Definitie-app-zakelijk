"""Configuratie loader voor toetsregels en verboden woorden.

Dit module biedt legacy functionaliteit voor het laden van
configuratiebestanden zoals toetsregels en verboden woorden.
"""

import json  # JSON bestand verwerking
import os  # Besturingssysteem interface voor paden
from typing import Dict  # Type hints

# ✅ Bepaal basis-dir, zodat we altijd vanaf de module-locatie werken
def _get_base_dir() -> str:
    return os.path.dirname(__file__)

# ✅ Standaard paden, kunnen overriden voor tests
_BASE_DIR = _get_base_dir()
_TOETSREGELS_PATH = os.path.join(_BASE_DIR, 'toetsregels.json')
_VERBODEN_WOORDEN_PATH = os.path.join(_BASE_DIR, 'verboden_woorden.json')


def laad_toetsregels(path: str = _TOETSREGELS_PATH) -> dict[str, dict]:
    """
    Laadt toetsregels uit JSON en verrijkt elke regel met z’n eigen ID.
    Werkt met UTF-8 en gooit FileNotFoundError / JSONDecodeError bij fouten.
    """
    # 1) Laad hele JSON bestand in het geheugen
    with open(path, 'r', encoding='utf-8') as f:  # Open bestand met UTF-8 encoding voor speciale karakters
        raw = json.load(f)  # Parse JSON naar Python dictionary

    # 2) pak het sub-dict onder "regels" (fallback op root voor backward compat)
    regels_dict = raw.get("regels", raw)

    verrijkt = {}
    for regel_id, data in regels_dict.items():
        # 3) injecteer de sleutel 'id' zodat elk dict z’n eigen key kent
        data['id'] = regel_id

        # 4) val meteen af als er geen 'uitleg' aanwezig is
        if 'uitleg' not in data:
            raise KeyError(f"Toetsregel {regel_id} mist de sleutel 'uitleg' in {path!r}")

        verrijkt[regel_id] = data

    return verrijkt

def laad_verboden_woorden(path: str = _VERBODEN_WOORDEN_PATH) -> dict:
    """
    Laadt verboden woorden uit JSON.

    Returns:
        De volledige JSON-structuur (bijv. {'verboden_woorden': [...]})
    """
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_repository(path: str) -> Dict[str, str]:
    """
    Laadt alle begrips-definities uit een JSON-bestand.
    JSON-structuur: { "object": "Definitie van object", ... }
    """
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return {term.lower(): defi for term, defi in data.items()}