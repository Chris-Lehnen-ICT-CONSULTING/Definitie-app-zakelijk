"""Sessiehulp voor een door het model gemeld betekenisconflict (DEF-751 stap 2).

Drie sessiesleutels, allemaal via `SessionStateManager`:

* `KEY_OPEN` — het open conflict van de laatste generatie: generation_id,
  vraag, lezingen én de vingerafdruk van de invoer waarvoor het gold.
* `KEY_INVOER` — het widget-veld (key-only `st.text_area`) waarin de gebruiker
  antwoordt. Wordt door de code nooit gewist of gezet (Streamlit-veilig).
* `KEY_VERZONDEN` — het expliciet verzonden antwoord, gebonden aan het
  conflict (generation_id) én aan de invoer (vingerafdruk). Eenmalig: de
  handler wist het bij de eerstvolgende generatie, toegepast of niet.

De vingerafdruk dekt alles wat de generatie stuurt: begrip, de drie
contextlijsten, de categorie-invoer (override of voorstel, of géén), de
documentselectie (document-id's zijn inhoudshashes, dus ook de inhoud) en de
RAG-collectieselectie. Wijzigt één daarvan, dan hoort een eerder antwoord niet
meer bij de actuele invoer en vervalt het met een melding. Geen nieuwe opslag:
alles is sessiestaat.

Een verduidelijking is gebruikersbedoeling — een keuze van de bedoelde
betekenislaag — geen bewezen bronfeit en geen ESS-02-oordeel.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from typing import Any

__all__ = [
    "KEY_INVOER",
    "KEY_OPEN",
    "KEY_VERZONDEN",
    "invoer_vingerafdruk",
    "open_conflict_uit",
    "verzend_verduidelijking",
    "verzonden_verduidelijking_voor",
]

KEY_OPEN = "betekenisconflict_open"
KEY_INVOER = "betekenisverduidelijking_invoer"
KEY_VERZONDEN = "betekenisverduidelijking_verzonden"


def _lijst(waarden: Iterable[Any] | None) -> list[str]:
    return sorted({str(w).strip() for w in (waarden or []) if str(w).strip()})


def invoer_vingerafdruk(
    *,
    begrip: str,
    organisatorische_context: Iterable[Any] | None,
    juridische_context: Iterable[Any] | None,
    wettelijke_basis: Iterable[Any] | None,
    categorie: str | None,
    document_ids: Iterable[Any] | None,
    rag_collection_ids: Iterable[Any] | None,
) -> str:
    """Stabiele hash van de volledige generatie-invoer (volgorde-onafhankelijk)."""
    canoniek = {
        "begrip": " ".join(str(begrip).split()).casefold(),
        "org": _lijst(organisatorische_context),
        "jur": _lijst(juridische_context),
        "wet": _lijst(wettelijke_basis),
        "categorie": (str(categorie).strip().lower() or None) if categorie else None,
        "documenten": _lijst(document_ids),
        "rag": _lijst(rag_collection_ids) if rag_collection_ids else [],
    }
    return hashlib.sha256(
        json.dumps(canoniek, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()


def open_conflict_uit(agent_result: Any, vingerafdruk: str) -> dict[str, Any] | None:
    """Het open conflict voor de sessie uit een UI-resultaat, of None."""
    if not isinstance(agent_result, dict):
        return None
    conflict = agent_result.get("betekenisconflict")
    if not isinstance(conflict, dict) or not conflict.get("vraag"):
        return None
    generation_id = conflict.get("generation_id") or (
        agent_result.get("metadata") or {}
    ).get("generation_id")
    if not generation_id:
        return None
    return {
        "generation_id": str(generation_id),
        "vingerafdruk": vingerafdruk,
        "vraag": str(conflict["vraag"]),
        "lezingen": [dict(lz) for lz in conflict.get("lezingen") or []],
        "begrip": str(conflict.get("begrip") or ""),
    }


def verzend_verduidelijking(
    sm: Any, open_conflict: dict[str, Any] | None, tekst: Any
) -> str | None:
    """Leg een expliciet verzonden antwoord vast; geeft de afwijsreden of None.

    Leeg is geen antwoord; zonder open conflict is er niets om aan te binden.
    """
    if not isinstance(open_conflict, dict) or not open_conflict.get("generation_id"):
        return "Er is geen open betekenisconflict om te beantwoorden; genereer opnieuw."
    antwoord = " ".join(str(tekst or "").split())
    if not antwoord:
        return "Een leeg antwoord is geen verduidelijking."
    sm.set_value(
        KEY_VERZONDEN,
        {
            "generation_id": str(open_conflict["generation_id"]),
            "vingerafdruk": str(open_conflict.get("vingerafdruk") or ""),
            "tekst": antwoord,
        },
    )
    return None


def verzonden_verduidelijking_voor(
    sm: Any, vingerafdruk: str
) -> tuple[str | None, str | None]:
    """Het toe te passen antwoord voor déze generatie: (tekst, afwijsreden).

    Wist het verzonden antwoord altijd (eenmalig). Toepassen alleen als het
    bij het open conflict hoort (generation_id) én bij de actuele invoer
    (vingerafdruk). (None, None) als er niets verzonden was.
    """
    verzonden = sm.get_value(KEY_VERZONDEN)
    if not verzonden:
        return None, None
    sm.clear_value(KEY_VERZONDEN)
    if not isinstance(verzonden, dict):
        return None, "Verduidelijking niet toegepast: onbruikbare sessiestaat."
    open_conflict = sm.get_value(KEY_OPEN)
    open_id = (
        open_conflict.get("generation_id") if isinstance(open_conflict, dict) else None
    )
    if not open_id or verzonden.get("generation_id") != open_id:
        return None, (
            "Verduidelijking niet toegepast: zij hoorde bij een eerder "
            "betekenisconflict, niet bij het huidige."
        )
    if verzonden.get("vingerafdruk") != vingerafdruk:
        return None, (
            "Verduidelijking niet toegepast: begrip, context, categorie, "
            "documentselectie of RAG-selectie is gewijzigd sinds de vraag. "
            "Beantwoord de vraag opnieuw als het model haar opnieuw stelt."
        )
    tekst = " ".join(str(verzonden.get("tekst") or "").split())
    if not tekst:
        return None, "Verduidelijking niet toegepast: het antwoord was leeg."
    return tekst, None
