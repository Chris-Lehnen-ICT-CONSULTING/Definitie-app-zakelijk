"""
Context options (business knowledge) extracted from UI components.

Keeping these lists centralized avoids scattering domain knowledge across the UI.
Rechtsgebieden komen uit services.rag.constants (single source of truth, DEF-376).
"""

from typing import Final

from services.rag.constants import RECHTSGEBIEDEN

# Organizations in the Dutch justice domain (ASTRA-aligned examples)
ORGANIZATIONS: Final[list[str]] = [
    "Openbaar Ministerie",
    "Rechtspraak",
    "Reclassering Nederland",
    "DJI",
    "Nationale Politie",
    "Koninklijke Marechaussee",
    "IND",
    "CJIB",
    "Justid",
    "NFI",
    "Raad voor de Kinderbescherming",
]

# Legal domains — afgeleid uit de centrale RECHTSGEBIEDEN waardelijst
LEGAL_DOMAINS: Final[list[str]] = list(RECHTSGEBIEDEN.values())

# Common laws frequently referenced
COMMON_LAWS: Final[list[str]] = [
    "Wetboek van Strafrecht (Sr)",
    "Wetboek van Strafvordering (Sv)",
    "Algemene wet bestuursrecht (Awb)",
    "Burgerlijk Wetboek (BW)",
    "Wet justitiële en strafvorderlijke gegevens (Wjsg)",
    "Penitentiaire beginselenwet (Pbw)",
    "Beginselenwet justitiële jeugdinrichtingen (Bjj)",
]

__all__ = ["COMMON_LAWS", "LEGAL_DOMAINS", "ORGANIZATIONS"]

# Alias-mapping om UI-afkortingen naar canonieke namen te vertalen
# Gebruik in de Edit-tab voor automatische prefill.
ORG_ALIASES: Final[dict[str, str]] = {
    "OM": "Openbaar Ministerie",
    "NP": "Nationale Politie",
    "KMAR": "Koninklijke Marechaussee",
    "ZM": "Rechtspraak",
    "Reclassering": "Reclassering Nederland",
}

__all__.append("ORG_ALIASES")
