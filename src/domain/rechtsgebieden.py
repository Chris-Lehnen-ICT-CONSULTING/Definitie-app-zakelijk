"""Rechtsgebieden domeinkennis (DEF-371, DEF-377).

Standalone module zonder externe afhankelijkheden zodat zowel de config-laag
als de service-laag hieruit kunnen importeren zonder circulaire imports.
"""

from __future__ import annotations

RECHTSGEBIEDEN: dict[str, str] = {
    "strafrecht": "Strafrecht",
    "burgerlijk_recht": "Burgerlijk recht",
    "bestuursrecht": "Bestuursrecht",
    "staatsrecht": "Staatsrecht",
    "belastingrecht": "Belastingrecht",
    "ondernemingsrecht": "Ondernemingsrecht",
    "arbeidsrecht": "Arbeidsrecht",
    "europees_recht": "Europees recht",
    "internationaal_recht": "Internationaal recht",
    "migratierecht": "Migratierecht",
    "jeugdrecht": "Jeugdrecht",
    "vreemdelingenrecht": "Vreemdelingenrecht",
    "sanctierecht": "Sanctierecht",
    "penitentiair_recht": "Penitentiair recht",
    "familierecht": "Familierecht",
}


def _register_alias(lookup: dict[str, str], alias: str, key: str) -> None:
    """Registreer een lookup-alias met collision-detectie."""
    existing = lookup.get(alias)
    if existing is not None and existing != key:
        raise RuntimeError(
            f"Rechtsgebied lookup collision: '{alias}' mapt naar zowel "
            f"'{existing}' als '{key}'"
        )
    lookup[alias] = key


def _build_lookup() -> dict[str, str]:
    """Bouw de reverse-lookup dict; gebruikt een functie om NameError te vermijden."""
    lookup: dict[str, str] = {}
    for key, label in RECHTSGEBIEDEN.items():
        _register_alias(lookup, key, key)
        _register_alias(lookup, label.lower(), key)
    # Extra aliassen voor gangbare varianten
    _register_alias(lookup, "civiel recht", "burgerlijk_recht")
    _register_alias(lookup, "civiel_recht", "burgerlijk_recht")
    _register_alias(lookup, "privaatrecht", "burgerlijk_recht")
    return lookup


_RECHTSGEBIED_LOOKUP: dict[str, str] = _build_lookup()


def normaliseer_rechtsgebied(invoer: str | None) -> str | None:
    """Normaliseer vrije tekst naar een gestandaardiseerde rechtsgebied-key.

    Returns None als de invoer leeg is of het rechtsgebied niet herkend wordt.
    """
    if not invoer or not invoer.strip():
        return None
    return _RECHTSGEBIED_LOOKUP.get(invoer.strip().lower())
