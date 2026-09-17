"""Herkomst van een categoriekeuze (DEF-751 B2) — puur domeincontract.

Eén categoriekeuze is een onveranderlijk *event*: welke waarde, uit welke
herkomst, door wie (alleen als een lokale identiteit werkelijk bekend is),
wanneer, en voor welke kandidaat (term + drie contexten; bij generatie ook
de gegenereerde tekst). Het event wordt bewaard in de bestaande
generatieregistratie (`generation_prompt_data`) naast het bronbewijs en de
CON-02-historie; het is géén validatie-issue en géén menselijke
inhoudelijke beoordeling (ESS-02-oordeel = stap 2).

De *status* wordt bij lezen afgeleid uit het event en de actuele
recordstaat (`bepaal_keuzestatus`); er schuift nooit een versienummer of
tijd mee. Term-, context- of waardewijziging maakt de keuze `stale`; een
tekstwijziging niet — maar bij een generatiegebonden keuze wordt zichtbaar
dat de tekst niet meer de gegenereerde kandidaat is (`text_unchanged`).

Zes gevallen, zonder verzinsels:
- handmatig (`manual`/`editor`): met actor → `manual_confirmed` (actor is een
  zelf opgegeven lokale naam of sessiewaarde, geen authenticatie); zonder
  actor → `manual_unattributed`;
- modelvoorstel (`model`) → `model_suggestion`;
- bewezen default (`default`, alleen als de code die default werkelijk
  toepaste) → `default`;
- import (`import`) → `imported`, of `imported_missing` als de bron geen
  categorie had;
- geen event, wél een kolomwaarde → `unknown_origin` (historisch bewijs
  ontbreekt; nooit achteraf default of handmatig genoemd);
- geen event, geen kolomwaarde → `absent`.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

from domain.context.normalisatie import canoniseer_contextlijst
from domain.ontological_categories import OPSLAGCATEGORIEEN

CATEGORY_CHOICE_SCHEMA = "def751-categoriekeuze/1"

HERKOMST_HANDMATIG = "manual"
HERKOMST_EDITOR = "editor"
HERKOMST_MODEL = "model"
HERKOMST_IMPORT = "import"
HERKOMST_DEFAULT = "default"
HERKOMSTEN: tuple[str, ...] = (
    HERKOMST_HANDMATIG,
    HERKOMST_EDITOR,
    HERKOMST_MODEL,
    HERKOMST_IMPORT,
    HERKOMST_DEFAULT,
)
#: Herkomsten waarbij een mens de keuze maakte; alleen daar mag een actor staan.
MENSELIJKE_HERKOMSTEN: frozenset[str] = frozenset({HERKOMST_HANDMATIG, HERKOMST_EDITOR})
#: Herkomsten die een publieke invoerroute (options/metadata/payload) mag
#: aanleveren. `editor` ontstaat alleen in de opslagroute van de editor,
#: `import` alleen in de importroute, `default` alleen waar de code de default
#: werkelijk toepast — nooit uit een aangeleverd blok.
PUBLIEKE_INVOERHERKOMSTEN: frozenset[str] = frozenset(
    {HERKOMST_HANDMATIG, HERKOMST_MODEL}
)

ACTORBRONNEN: tuple[str, ...] = ("typed_name", "session_user")

BINDING_GENERATIEKANDIDAAT = "generation_candidate"
BINDING_TERM_CONTEXT = "term_context"

CONTEXTVELDEN: tuple[str, ...] = (
    "organisatorische_context",
    "juridische_context",
    "wettelijke_basis",
)


def _hash(delen: list[str]) -> str:
    return "sha256:" + hashlib.sha256("\n".join(delen).encode("utf-8")).hexdigest()


def canonieke_contexten(contexten: Mapping[str, Any] | None) -> dict[str, list[str]]:
    """De drie contextlijsten in canonieke vorm (getrimd, ontdubbeld, gesorteerd)."""
    bron = contexten or {}
    return {veld: canoniseer_contextlijst(bron.get(veld)) for veld in CONTEXTVELDEN}


def bereken_kandidaatvingerafdruk(
    begrip: str, contexten: Mapping[str, Any] | None
) -> str:
    """Bind een keuze aan term + drie contexten (schrijfwijze-/volgorde-ongevoelig)."""
    canoniek = canonieke_contexten(contexten)
    delen = [CATEGORY_CHOICE_SCHEMA, (begrip or "").strip().casefold()]
    for veld in CONTEXTVELDEN:
        delen.append(
            json.dumps([w.casefold() for w in canoniek[veld]], ensure_ascii=False)
        )
    return _hash(delen)


def bereken_tekstvingerafdruk(tekst: str | None) -> str:
    """Vingerafdruk van de exacte definitietekst waarvoor een keuze gold."""
    return _hash([CATEGORY_CHOICE_SCHEMA, tekst or ""])


def _is_opslagwaarde(waarde: Any) -> bool:
    return isinstance(waarde, str) and waarde in OPSLAGCATEGORIEEN


def bouw_categoriekeuze(
    *,
    waarde: str | None,
    herkomst: str,
    begrip: str,
    contexten: Mapping[str, Any] | None,
    actor: str | None = None,
    actor_source: str | None = None,
    recorded_at: str | None = None,
    record_version: int | None = None,
    definitie_tekst: str | None = None,
    generation_id: str | None = None,
    reasoning: str | None = None,
    scores: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Het onveranderlijke keuze-event. Weigert wat niet klopt (ValueError).

    - `waarde`: exact een opslagwaarde of None (geen label). Geen normalisatie:
      "Type" of "entiteit" wordt geweigerd, niet omgezet.
    - `actor`: alleen bij menselijke herkomst; met verplichte `actor_source`
      uit `ACTORBRONNEN` (opgegeven naam of sessiewaarde — geen authenticatie).
    - binding: met `definitie_tekst` of `generation_id` bindt de keuze aan de
      concrete generatiekandidaat (tekstvingerafdruk); anders aan term/context.
    """
    if herkomst not in HERKOMSTEN:
        msg = f"onbekende herkomst voor categoriekeuze: {herkomst!r}"
        raise ValueError(msg)
    if waarde is not None and not _is_opslagwaarde(waarde):
        msg = f"categoriekeuze {waarde!r} is geen opslagwaarde; geweigerd, niet omgezet"
        raise ValueError(msg)
    actor_tekst = actor.strip() if isinstance(actor, str) else ""
    if actor is not None and not actor_tekst:
        msg = "actor moet een niet-lege naam zijn of None"
        raise ValueError(msg)
    if actor_tekst and herkomst not in MENSELIJKE_HERKOMSTEN:
        msg = f"herkomst {herkomst!r} kent geen actor; alleen een mens kiest handmatig"
        raise ValueError(msg)
    if actor_tekst and actor_source not in ACTORBRONNEN:
        msg = (
            f"actor_source {actor_source!r} is geen bekende lokale actorbron "
            f"{ACTORBRONNEN}; een naam is geen authenticatie"
        )
        raise ValueError(msg)
    if not actor_tekst and actor_source is not None:
        msg = "actor_source zonder actor is betekenisloos"
        raise ValueError(msg)
    if record_version is not None and (
        isinstance(record_version, bool) or not isinstance(record_version, int)
    ):
        msg = "record_version moet een geheel getal zijn"
        raise ValueError(msg)
    begrip_tekst = (begrip or "").strip()
    generatiegebonden = definitie_tekst is not None or generation_id is not None
    event: dict[str, Any] = {
        "schema": CATEGORY_CHOICE_SCHEMA,
        "value": waarde,
        "origin": herkomst,
        "actor": actor_tekst or None,
        "actor_source": actor_source if actor_tekst else None,
        "recorded_at": recorded_at or datetime.now(UTC).isoformat(),
        # Informatief: de recordversie op het moment van schrijven. Wordt
        # nooit bijgewerkt; de binding loopt via de vingerafdrukken.
        "record_version_at_write": record_version,
        "candidate": {
            "begrip": begrip_tekst,
            **canonieke_contexten(contexten),
            "fingerprint": bereken_kandidaatvingerafdruk(begrip_tekst, contexten),
        },
        "binding": (
            BINDING_GENERATIEKANDIDAAT if generatiegebonden else BINDING_TERM_CONTEXT
        ),
        "generation_id": generation_id,
        "text_fingerprint": (
            bereken_tekstvingerafdruk(definitie_tekst) if generatiegebonden else None
        ),
        "reasoning": reasoning if isinstance(reasoning, str) and reasoning else None,
        "scores": dict(scores) if isinstance(scores, Mapping) and scores else None,
    }
    return event


def lees_keuze_invoer(invoer: Any) -> dict[str, Any] | None:
    """De grens voor aangeleverde keuze-invoer (options, metadata, payload).

    Alleen `origin` (manual|model), `reasoning` en `scores` worden gelezen.
    Een meegestuurde actor, tijd, status of versie wordt genegeerd: een
    aangeleverd blok kan geen menselijke bevestiging fabriceren. Herkomsten
    die alleen in een eigen opslagroute mogen ontstaan (editor, import,
    default) zijn hier ongeldig.
    """
    if not isinstance(invoer, Mapping):
        return None
    herkomst = invoer.get("origin")
    if herkomst is None:
        return None
    if herkomst not in PUBLIEKE_INVOERHERKOMSTEN:
        msg = (
            f"herkomst {herkomst!r} mag niet worden aangeleverd; alleen "
            f"{sorted(PUBLIEKE_INVOERHERKOMSTEN)} komen uit een UI-actie"
        )
        raise ValueError(msg)
    gelezen: dict[str, Any] = {"origin": herkomst}
    reasoning = invoer.get("reasoning")
    if isinstance(reasoning, str) and reasoning:
        gelezen["reasoning"] = reasoning
    scores = invoer.get("scores")
    if isinstance(scores, Mapping) and scores:
        gelezen["scores"] = dict(scores)
    return gelezen


def is_categoriekeuze(event: Any) -> bool:
    """True als `event` structureel een keuze-event van dit contract is."""
    if not isinstance(event, Mapping) or event.get("schema") != CATEGORY_CHOICE_SCHEMA:
        return False
    kandidaat = event.get("candidate")
    return (
        event.get("origin") in HERKOMSTEN
        and (event.get("value") is None or _is_opslagwaarde(event.get("value")))
        and isinstance(kandidaat, Mapping)
        and isinstance(kandidaat.get("fingerprint"), str)
    )


def _basisstatus(event: Mapping[str, Any]) -> str:
    herkomst = event.get("origin")
    if herkomst in MENSELIJKE_HERKOMSTEN:
        return "manual_confirmed" if event.get("actor") else "manual_unattributed"
    if herkomst == HERKOMST_MODEL:
        return "model_suggestion"
    if herkomst == HERKOMST_IMPORT:
        return "imported" if event.get("value") is not None else "imported_missing"
    return "default"


def bepaal_keuzestatus(
    event: Any,
    *,
    categorie: str | None,
    begrip: str,
    contexten: Mapping[str, Any] | None,
    definitie_tekst: str | None = None,
) -> dict[str, Any]:
    """Status van de opgeslagen keuze tegenover de actuele recordstaat.

    Geeft `status`, `binding`, `text_unchanged` (alleen betekenisvol bij een
    generatiegebonden keuze), `underlying` (de basisstatus achter `stale`) en
    een leesbare `reason`. Niets wordt herschreven; verouderd blijft verouderd.
    """
    if event is None:
        if categorie is None:
            return {
                "status": "absent",
                "binding": None,
                "text_unchanged": None,
                "underlying": None,
                "reason": "geen categorie en geen keuze-event",
            }
        return {
            "status": "unknown_origin",
            "binding": None,
            "text_unchanged": None,
            "underlying": None,
            "reason": (
                f"categorie {categorie!r} zonder keuze-event: herkomst onbekend "
                "(bestaand record)"
            ),
        }
    if not is_categoriekeuze(event):
        return {
            "status": "invalid",
            "binding": None,
            "text_unchanged": None,
            "underlying": None,
            "reason": "keuze-event heeft niet de verwachte vorm",
        }
    basis = _basisstatus(event)
    binding = event.get("binding")
    tekst_ongewijzigd: bool | None = None
    if binding == BINDING_GENERATIEKANDIDAAT and isinstance(
        event.get("text_fingerprint"), str
    ):
        tekst_ongewijzigd = event["text_fingerprint"] == bereken_tekstvingerafdruk(
            definitie_tekst
        )
    redenen: list[str] = []
    if event["candidate"]["fingerprint"] != bereken_kandidaatvingerafdruk(
        begrip, contexten
    ):
        redenen.append("term of context is gewijzigd sinds de keuze")
    if event.get("value") != categorie:
        redenen.append(
            f"opgeslagen categorie {categorie!r} wijkt af van de keuze "
            f"{event.get('value')!r}"
        )
    if redenen:
        return {
            "status": "stale",
            "binding": binding,
            "text_unchanged": tekst_ongewijzigd,
            "underlying": basis,
            "reason": "; ".join(redenen),
        }
    reden = {
        "manual_confirmed": (
            f"handmatig gekozen door {event.get('actor')!r} (opgegeven naam, "
            "niet geverifieerd)"
        ),
        "manual_unattributed": "handmatig gekozen; beoordelaar niet opgegeven",
        "model_suggestion": "voorstel van het classificatiemodel, niet bevestigd",
        "imported": "overgenomen uit importbron",
        "imported_missing": "importbron had geen categorie",
        "default": "door de code toegepaste default, geen keuze",
    }[basis]
    if tekst_ongewijzigd is False:
        reden += (
            "; de tekst is sindsdien gewijzigd (keuze gold voor de gegenereerde tekst)"
        )
    return {
        "status": basis,
        "binding": binding,
        "text_unchanged": tekst_ongewijzigd,
        "underlying": None,
        "reason": reden,
    }
