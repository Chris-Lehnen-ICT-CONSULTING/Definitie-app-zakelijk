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
RAG-collectieselectie (als collectienamen; geen selectie ≡ de standaard-
collectie die de orchestrator zelf doorzoekt, zie
`rag_selectie_voor_vingerafdruk`). Wijzigt één daarvan, dan hoort een eerder
antwoord niet meer bij de actuele invoer en vervalt het met een melding. Geen
nieuwe opslag: alles is sessiestaat.

Een verduidelijking is gebruikersbedoeling — een keuze van de bedoelde
betekenislaag — geen bewezen bronfeit en geen ESS-02-oordeel.

DEF-821: een door het model gemelde ontbrekende betekenisgrond (ESS-04) is
een tweede soort open verzoek (`soort`), met `ontbrekende_grond` en `vraag`
in plaats van lezingen. Het antwoord — de door de gebruiker aangevulde grond
— loopt via precies hetzelfde gebonden en eenmalige mechanisme.

DEF-821 correctieronde 1: `KEY_KETEN` bewaart de reeds toegepaste antwoorden
van één invoergebonden verduidelijkingsketen (met de vraag van het model),
zodat een vervolgvraag eerdere antwoorden niet laat verdwijnen. Zie
`bereid_verduidelijking_voor` en `sluit_keten_af`.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

__all__ = [
    "HERSTELBARE_VERDUIDELIJKINGSFOUTEN",
    "KEY_AFWIJZING",
    "KEY_INVOER",
    "KEY_KETEN",
    "KEY_OPEN",
    "KEY_RAG_NAMEN",
    "KEY_VERZONDEN",
    "MAX_KETEN_ANTWOORDEN",
    "RAG_STANDAARDCOLLECTIE",
    "SOORT_CONFLICT",
    "SOORT_ONTBREKENDE_GROND",
    "Ketenvoorbereiding",
    "bereid_verduidelijking_voor",
    "invoer_vingerafdruk",
    "open_conflict_uit",
    "rag_selectie_voor_vingerafdruk",
    "sluit_keten_af",
    "verduidelijking_uit_keten",
    "verzend_verduidelijking",
    "verzonden_verduidelijking_voor",
]

KEY_OPEN = "betekenisconflict_open"
KEY_INVOER = "betekenisverduidelijking_invoer"
KEY_VERZONDEN = "betekenisverduidelijking_verzonden"
#: Door de RAG-collectieselector gezet: {collectie-id: collectienaam} van de
#: op dat moment getoonde collecties. De vingerafdruk bindt de RAG-selectie
#: aan stabiele collectienamen (UNIQUE in `rag_collections`), niet aan de
#: toevallige id's of aan "alles geselecteerd".
KEY_RAG_NAMEN = "rag_collection_names"
#: De collectie die de orchestrator zonder selectie zelf aanmaakt en doorzoekt
#: (`DefinitionOrchestratorV2.create_definition`: `_ensure_collection(...)`).
#: Browserbevinding 17-09-2026: de eerste generatie maakt haar aan, waarna de
#: selector bij de volgende rerun verschijnt en haar als selectie wegschrijft
#: (None → [id]). Dat is de enige bewezen automatische initialisatie: zonder
#: selectie is de zoekscope precies deze collectie, dus geen wijziging.
RAG_STANDAARDCOLLECTIE = "user_documents"
#: De melding waarmee de generatie een verzonden antwoord weigerde
#: (reviewcorrectie 1): het conflict blijft open, het antwoord blijft
#: verzonden, de gebruiker past het aan en verzendt opnieuw.
KEY_AFWIJZING = "betekenisverduidelijking_afwijzing"

#: Orchestrator-`error_type`s waarbij een verzonden antwoord níét vervalt: de
#: generatie is vóór het model geweigerd om het antwoord zelf of het
#: promptbudget, en de gebruiker moet het antwoord kunnen aanpassen.
HERSTELBARE_VERDUIDELIJKINGSFOUTEN = frozenset(
    {"verduidelijking_te_lang", "verduidelijking_niet_in_prompt", "prompt_te_lang"}
)

#: DEF-821: soort open verzoek — gelijk aan de sleutel in het UI-resultaat.
SOORT_CONFLICT = "betekenisconflict"
SOORT_ONTBREKENDE_GROND = "betekenisgrond_ontbreekt"

#: DEF-821 correctieronde 1: de invoergebonden keten van reeds toegepaste
#: antwoorden: {"vingerafdruk": ..., "antwoorden": [{"vraag", "antwoord"}]}.
#: Zolang de invoer gelijk blijft en het model om verduidelijking blijft
#: vragen, gaan alle antwoorden (met de vraag van het model als context)
#: opnieuw mee; een definitie, een andere uitkomst of een invoerwijziging
#: beëindigt de keten. Begrensd — geen globale conversatiegeschiedenis.
KEY_KETEN = "betekenisverduidelijking_keten"
MAX_KETEN_ANTWOORDEN = 5


def verduidelijking_uit_keten(antwoorden: Iterable[dict[str, Any]]) -> str:
    """Eén regel met alle vraag-antwoordparen, genummerd en in volgorde.

    De vraag is de melding van het model (context, geen bronfeit); het
    antwoord is de bedoeling van de gebruiker. Geen afkap: het budget wordt
    ná escaping in de orchestrator bewaakt (`verduidelijking_te_lang`).
    """
    delen = []
    for nr, paar in enumerate(antwoorden, start=1):
        vraag = " ".join(str(paar.get("vraag") or "").split())
        antwoord = " ".join(str(paar.get("antwoord") or "").split())
        delen.append(
            f"({nr}) Vraag van het model: {vraag} Antwoord van de gebruiker: {antwoord}"
        )
    return " ".join(delen)


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


def rag_selectie_voor_vingerafdruk(sm: Any) -> list[str] | None:
    """De effectieve RAG-zoekscope als stabiele collectienamen, voor de vingerafdruk.

    Geen selectie (geen selector getoond, of niets geselecteerd) betekent dat
    de generatie de standaardcollectie aanmaakt en doorzoekt; een selectie met
    uitsluitend die collectie is dezelfde scope en levert daarom ook None.
    Elke andere selectie telt concreet, per naam: een werkelijke uitbreiding
    of deselectie wijzigt de scope, een nieuw beschikbare maar niet
    geselecteerde collectie niet. Alleen de vingerafdruk leest dit; wat de
    generatie werkelijk doorzoekt (`rag_selected_collection_ids`) verandert
    hier niet.
    """
    ids = sm.get_value("rag_selected_collection_ids", None) or []
    if not ids:
        return None
    namen = sm.get_value(KEY_RAG_NAMEN, None) or {}
    scope = [str(namen.get(i) or namen.get(str(i)) or i) for i in ids]
    if scope == [RAG_STANDAARDCOLLECTIE]:
        return None
    return scope


def _open_melding_uit(agent_result: dict[str, Any]) -> tuple[str, dict] | None:
    """(soort, melding) uit een UI-resultaat; conflict gaat vóór (DEF-821)."""
    conflict = agent_result.get(SOORT_CONFLICT)
    if isinstance(conflict, dict) and conflict.get("vraag"):
        return SOORT_CONFLICT, conflict
    grond = agent_result.get(SOORT_ONTBREKENDE_GROND)
    if (
        isinstance(grond, dict)
        and grond.get("vraag")
        and grond.get("ontbrekende_grond")
    ):
        return SOORT_ONTBREKENDE_GROND, grond
    return None


def open_conflict_uit(agent_result: Any, vingerafdruk: str) -> dict[str, Any] | None:
    """Het open verzoek (conflict of ontbrekende grond) uit een UI-resultaat, of None."""
    if not isinstance(agent_result, dict):
        return None
    gevonden = _open_melding_uit(agent_result)
    if gevonden is None:
        return None
    soort, melding = gevonden
    generation_id = melding.get("generation_id") or (
        agent_result.get("metadata") or {}
    ).get("generation_id")
    if not generation_id:
        return None
    open_verzoek: dict[str, Any] = {
        "generation_id": str(generation_id),
        "vingerafdruk": vingerafdruk,
        "soort": soort,
        "vraag": str(melding["vraag"]),
        "lezingen": [dict(lz) for lz in melding.get("lezingen") or []],
        "begrip": str(melding.get("begrip") or ""),
    }
    if soort == SOORT_ONTBREKENDE_GROND:
        open_verzoek["ontbrekende_grond"] = str(melding["ontbrekende_grond"])
    return open_verzoek


def verzend_verduidelijking(
    sm: Any, open_conflict: dict[str, Any] | None, tekst: Any
) -> str | None:
    """Leg een expliciet verzonden antwoord vast; geeft de afwijsreden of None.

    Leeg is geen antwoord; zonder open conflict is er niets om aan te binden.
    """
    if not isinstance(open_conflict, dict) or not open_conflict.get("generation_id"):
        return (
            "Er is geen open verduidelijkingsvraag (betekenisconflict of "
            "ontbrekende betekenisgrond) om te beantwoorden; genereer opnieuw."
        )
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
    # Een nieuw verzonden antwoord vervangt een eerdere afwijzing.
    sm.clear_value(KEY_AFWIJZING)
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
            "Verduidelijking niet toegepast: zij hoorde bij een eerdere "
            "verduidelijkingsvraag, niet bij de huidige."
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


@dataclass(frozen=True)
class Ketenvoorbereiding:
    """Wat de generatie aan verduidelijking meestuurt (correctieronde 1).

    `tekst` is de volledige ketenregel (of None), `antwoorden` de keten
    inclusief een nieuw toegepast antwoord, `meldingen` vaste teksten voor
    de gebruiker, `weigering` een reden om níét te genereren.
    """

    tekst: str | None
    antwoorden: tuple[dict[str, str], ...]
    meldingen: tuple[str, ...] = ()
    weigering: str | None = None


def _geldige_keten(sm: Any, vingerafdruk: str) -> tuple[list[dict[str, str]], bool]:
    """(antwoorden, vervallen): de keten voor déze invoer; een keten voor
    andere invoer wordt gewist en telt als vervallen."""
    keten = sm.get_value(KEY_KETEN)
    if not isinstance(keten, dict):
        return [], False
    antwoorden = [
        {"vraag": str(a.get("vraag") or ""), "antwoord": str(a.get("antwoord") or "")}
        for a in keten.get("antwoorden") or []
        if isinstance(a, dict) and a.get("antwoord")
    ]
    if keten.get("vingerafdruk") != vingerafdruk:
        sm.clear_value(KEY_KETEN)
        return [], bool(antwoorden)
    return antwoorden, False


def bereid_verduidelijking_voor(sm: Any, vingerafdruk: str) -> Ketenvoorbereiding:
    """Bepaal de verduidelijking voor déze generatie (DEF-821 correctieronde 1).

    Een expliciet verzonden antwoord wordt, met de vraag van het open verzoek
    als context, achter de eerder toegepaste antwoorden van dezelfde
    invoerketen gezet; de hele keten gaat mee. Wijzigt de invoer, dan
    vervalt de keten als geheel. Boven `MAX_KETEN_ANTWOORDEN` wordt niet
    gegenereerd (het antwoord blijft verzonden). De keten zelf wordt pas in
    `sluit_keten_af` bijgewerkt, na de uitkomst van de generatie.
    """
    open_verzoek = sm.get_value(KEY_OPEN)
    vraag = (
        str(open_verzoek.get("vraag") or "") if isinstance(open_verzoek, dict) else ""
    )
    antwoord, afwijsreden = verzonden_verduidelijking_voor(sm, vingerafdruk)
    antwoorden, vervallen = _geldige_keten(sm, vingerafdruk)
    meldingen: list[str] = [afwijsreden] if afwijsreden else []
    if vervallen:
        meldingen.append(
            "Eerdere verduidelijkingen niet toegepast: begrip, context, "
            "categorie, documentselectie of RAG-selectie is gewijzigd."
        )
    if antwoord:
        antwoorden = [*antwoorden, {"vraag": vraag, "antwoord": antwoord}]
    if len(antwoorden) > MAX_KETEN_ANTWOORDEN:
        return Ketenvoorbereiding(
            tekst=None,
            antwoorden=tuple(antwoorden),
            meldingen=tuple(meldingen),
            weigering=(
                f"Er zijn al {MAX_KETEN_ANTWOORDEN} verduidelijkingen voor deze "
                "invoer gegeven (maximum); er is niet gegenereerd. Pas begrip, "
                "context of bronnen aan om opnieuw te beginnen."
            ),
        )
    return Ketenvoorbereiding(
        tekst=verduidelijking_uit_keten(antwoorden) if antwoorden else None,
        antwoorden=tuple(antwoorden),
        meldingen=tuple(meldingen),
    )


def sluit_keten_af(
    sm: Any,
    vingerafdruk: str,
    antwoorden: Iterable[dict[str, str]],
    *,
    nieuw_verzoek: bool,
) -> None:
    """Keten bijwerken na de generatie: vraagt het model opnieuw om
    verduidelijking, dan blijft de keten (met het toegepaste antwoord)
    staan; elke andere uitkomst beëindigt haar."""
    lijst = [dict(a) for a in antwoorden]
    if nieuw_verzoek and lijst:
        sm.set_value(KEY_KETEN, {"vingerafdruk": vingerafdruk, "antwoorden": lijst})
    else:
        sm.clear_value(KEY_KETEN)
