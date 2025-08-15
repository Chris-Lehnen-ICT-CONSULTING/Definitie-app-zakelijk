"""
Legacy config loader - voor backward compatibility.

Dit bestand biedt een compatibility layer voor code die nog
de oude config_loader gebruikt. Gebruik voor nieuwe code:
    from toetsregels import load_toetsregels
"""

import warnings

from toetsregels.loader import load_toetsregels as new_load_toetsregels


# Legacy functie naam
def laad_toetsregels(path=None):
    """
    DEPRECATED: Gebruik toetsregels.loader.load_toetsregels

    Deze functie is behouden voor backward compatibility.
    """
    if path:
        warnings.warn(
            "Path parameter wordt genegeerd. Toetsregels worden nu "
            "geladen uit individuele bestanden in src/toetsregels/regels/",
            DeprecationWarning,
        )

    # Gebruik nieuwe loader, maar return alleen regels dict
    result = new_load_toetsregels()
    return result.get("regels", {})


# Voor het laden van verboden woorden (blijft in config)
def laad_verboden_woorden(path=None):
    """Laad verboden woorden uit JSON."""
    import json
    import os

    if not path:
        base_dir = os.path.dirname(__file__)
        path = os.path.join(base_dir, "verboden_woorden.json")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# Backward compatibility
load_toetsregels = laad_toetsregels
