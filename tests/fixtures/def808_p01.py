"""Vaste P01-casus (CON-02, dossier 16/17 september 2026) als testfixture.

Begrip *besluit*, de exacte Awb-definitie, context Bestuursrecht/Awb en de
geüploade fixture `awb-1-3-20260815.txt` als documentbron met twee
termpassages van hetzelfde document — precies de vorm waarin de generatie
documentbronnen vastlegt (DEF-743). Zonder opgegeven metadata draagt de bron
geen url, versie of vindplaats (DEF-808).

`bouw_documentbeoordeling` levert een contractconforme AI-beoordeling voor
exact deze invoer met een geverifieerd citaat uit de eerste documentpassage.
Zij oordeelt alle drie onderdelen positief; de kern beslist zelf of dat
overeind blijft (zonder bruikbare hyperlink blijft de verwijskwaliteit open,
DEF-806). Synthetische stand-in voor de beoordelingsdienst; geen model.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from domain.sources.contract import CONTRACTVERSIE, bereken_bronvingerafdruk
from domain.sources.normalisatie import canoniseer_bronnen

BEGRIP = "besluit"
P01_TEKST = (
    "schriftelijke beslissing van een bestuursorgaan, inhoudende een "
    "publiekrechtelijke rechtshandeling"
)
GEGENEREERDE_TEKST = (
    "Resultaat van een besluitvormingsproces van een bestuursorgaan in de vorm van "
    "een schriftelijke beslissing die een publiekrechtelijke rechtshandeling inhoudt."
)
JUR = ["Bestuursrecht"]
WET = ["Algemene wet bestuursrecht"]
CONTEXTEN: dict[str, list[str]] = {
    "organisatorische_context": [],
    "juridische_context": list(JUR),
    "wettelijke_basis": list(WET),
}
P01_URL = (
    "https://wetten.overheid.nl/BWBR0005537/2026-08-15/0?g=2026-09-14&z=2026-09-14"
    "#Hoofdstuk1_Titeldeel1.1_Artikel1:3"
)
P01_VERSIE = "2026-08-15"
P01_VINDPLAATS = "artikel 1:3 lid 1 Awb"
DOC_ID = "01e121c20018eed2"
BESTANDSNAAM = "awb-1-3-20260815.txt"
PASSAGE_1 = (
    "Algemene wet bestuursrecht Artikel 1:3 1. Onder besluit wordt verstaan: een "
    "schriftelijke beslissing van een bestuursorgaan, inhoudende een "
    "publiekrechtelijke rechtshandeling. 2. Onder beschikki"
)
PASSAGE_2 = (
    "hriftelijke beslissing van een bestuursorgaan, inhoudende een publiekrechtelijke "
    "rechtshandeling. 2. Onder beschikking wordt verstaan: een besluit dat niet van "
    "algemene strekking is, met inbegrip van de afwijzing van een aanvraag daarvan."
)
CITAAT = (
    "Onder besluit wordt verstaan: een schriftelijke beslissing van een "
    "bestuursorgaan, inhoudende een publiekrechtelijke rechtshandeling."
)


def _documentbron(passage: str) -> dict[str, Any]:
    return {
        "provider": "documents",
        "filename": BESTANDSNAAM,
        "selection_basis": "term_match",
        "title": BESTANDSNAAM,
        "url": None,
        "snippet": passage,
        "score": 1.0,
        "used_in_prompt": True,
        "doc_id": DOC_ID,
        "source_label": "Geüpload document",
    }


DOCUMENTBRONNEN: list[dict[str, Any]] = [
    _documentbron(PASSAGE_1),
    _documentbron(PASSAGE_2),
]


def bouw_documentbeoordeling(
    tekst: str,
    bronnen_ruw: Any,
    *,
    begrip: str = BEGRIP,
    contexten: dict[str, list[str]] | None = None,
    peildatum: str | None = None,
    assessed_at: str = "2026-09-17T21:16:46+00:00",
) -> dict[str, Any]:
    """Een positieve, gebonden beoordeling voor exact deze kandidaat en bronset."""
    contexten = CONTEXTEN if contexten is None else contexten
    canoniek = canoniseer_bronnen(bronnen_ruw)
    vingerafdruk = bereken_bronvingerafdruk(
        begrip, tekst, contexten, canoniek, peildatum=peildatum
    )
    dragend = next(b for b in canoniek if CITAAT in b.passage)
    bewijs = [
        {"source_id": dragend.source_id, "quote": CITAAT, "locator": dragend.locator}
    ]
    return {
        "contract_version": CONTRACTVERSIE,
        "prompt_version": "con02-assess/2",
        "fingerprint": vingerafdruk,
        "status": "assessed",
        "error": None,
        "assessed_at": assessed_at,
        "attribution": {
            "provider": "fake",
            "model": "fake-beoordelaar",
            "task_type": "validation",
            "cached": False,
            "tokens_used": 0,
        },
        "peildatum": peildatum,
        "sources": [b.als_dict() for b in canoniek],
        "parts": {
            "source_authority": {
                "status": "pass",
                "reason": "Wettekst Awb artikel 1:3 is de authentieke bron.",
                "uncertainty": None,
                "evidence": deepcopy(bewijs),
                "sources": [
                    {
                        "source_id": dragend.source_id,
                        "profile": "wet_regelgeving",
                        "applicable": True,
                        "reason": "Awb art. 1:3 lid 1 definieert het begrip.",
                    }
                ],
            },
            "semantic_support": {
                "status": "pass",
                "reason": "De bron geeft exact dezelfde bepalende kenmerken.",
                "uncertainty": None,
                "evidence": deepcopy(bewijs),
                "claims": [
                    {
                        "aspect": "kenmerk",
                        "text": kenmerk,
                        "supported": True,
                        "source_id": dragend.source_id,
                    }
                    for kenmerk in (
                        "schriftelijke beslissing",
                        "van een bestuursorgaan",
                        "inhoudende een publiekrechtelijke rechtshandeling",
                    )
                ],
            },
            "reference_quality": {
                "status": "pass",
                "reason": "Artikel 1:3 lid 1 Awb is exact terugvindbaar.",
                "uncertainty": None,
                "evidence": deepcopy(bewijs),
                "sources": [
                    {
                        "source_id": dragend.source_id,
                        "locatable": True,
                        "reason": "artikel en lid aanwezig",
                    }
                ],
            },
        },
        "rejected": [],
        "raw_response_sha256": None,
        "assessment_receipt": None,
    }
