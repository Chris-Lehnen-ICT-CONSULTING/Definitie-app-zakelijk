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
    generatiegebonden = generation_id is not None
    event: dict[str, Any] = {
        "schema": CATEGORY_CHOICE_SCHEMA,
        "value": waarde,
        "origin": herkomst,
        "actor": actor_tekst or None,
        "actor_source": actor_source if actor_tekst else None,
        "recorded_at": recorded_at or datetime.now(UTC).isoformat(),
        # Informatief: de recordversie op het moment van schrijven. Wordt
        # nooit bijgewerkt; de binding loopt via de vingerafdrukken en de
        # persistente keuzestaat (`bouw_keuzestaat`).
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
        # Tekstbasis voor álle keuzes (reviewbevinding 5): de tekst waarvoor
        # de keuze gold, ook bij een editor-/toepassen-keuze.
        "text_fingerprint": (
            bereken_tekstvingerafdruk(definitie_tekst)
            if definitie_tekst is not None
            else None
        ),
        "reasoning": reasoning if isinstance(reasoning, str) and reasoning else None,
        "scores": dict(scores) if isinstance(scores, Mapping) and scores else None,
    }
    return event


KEUZESTAAT_SCHEMA = "def751-keuzestaat/1"


def bouw_keuzestaat(record_version: int | None) -> dict[str, Any]:
    """De persistente toepassingsstaat van het actuele keuze-event.

    Het event zelf is onveranderlijk; deze staat legt blijvend vast of de
    keuze nog geldt (`current`) en of de tekst sindsdien is gewijzigd. Zij
    wordt in dezelfde transactie bijgewerkt als de wijziging die haar raakt
    (reviewbevinding 1) en alleen door een nieuwe bewuste keuze vervangen:
    term, context of categorie terugzetten maakt een vervallen keuze nooit
    opnieuw actueel.
    """
    return {
        "schema": KEUZESTAAT_SCHEMA,
        "current": True,
        "recorded_on_version": record_version,
        "invalidated_at": None,
        "invalidated_on_version": None,
        "invalidation_reason": None,
        "text_changed": False,
        "text_changed_at": None,
        "text_changed_on_version": None,
    }


def markeer_keuze_vervallen(
    staat: Mapping[str, Any] | None, *, reden: str, version: int, at: str
) -> dict[str, Any]:
    """Nieuwe staat waarin de keuze blijvend vervallen is (eerste reden wint)."""
    basis = dict(staat) if isinstance(staat, Mapping) else bouw_keuzestaat(None)
    if not basis.get("current", True):
        return basis
    basis.update(
        {
            "current": False,
            "invalidated_at": at,
            "invalidated_on_version": version,
            "invalidation_reason": reden,
        }
    )
    return basis


def markeer_tekst_gewijzigd(
    staat: Mapping[str, Any] | None, *, version: int, at: str
) -> dict[str, Any]:
    """Nieuwe staat waarin vastligt dat de tekst na de keuze is gewijzigd."""
    basis = dict(staat) if isinstance(staat, Mapping) else bouw_keuzestaat(None)
    if basis.get("text_changed"):
        return basis
    basis.update(
        {
            "text_changed": True,
            "text_changed_at": at,
            "text_changed_on_version": version,
        }
    )
    return basis


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


def _leeg_resultaat(status: str, reden: str) -> dict[str, Any]:
    return {
        "status": status,
        "binding": None,
        "text_unchanged": None,
        "text_changed_on_version": None,
        "invalidated_on_version": None,
        "underlying": None,
        "reason": reden,
    }


def bepaal_keuzestatus(
    event: Any,
    *,
    categorie: str | None,
    begrip: str,
    contexten: Mapping[str, Any] | None,
    definitie_tekst: str | None = None,
    staat: Mapping[str, Any] | None = None,
    claim: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Status van de opgeslagen keuze tegenover de actuele recordstaat.

    Leidend is de persistente keuzestaat (`staat`, reviewbevinding 1): een
    vervallen keuze blijft `stale`, ook als term, context of categorie
    later worden teruggezet. De vingerafdrukvergelijkingen blijven als
    vangnet (bv. een record dat buiten de schrijfroute om is gewijzigd).
    `text_unchanged` (reviewbevinding 5) is False zodra de tekst na de keuze
    is gewijzigd — blijvend, ook na terugzetten. Niets wordt herschreven.
    """
    if event is None:
        if isinstance(claim, Mapping) and claim.get("origin"):
            # Herreview 2: een aangeleverde handmatige claim zonder keuzeactie
            # is aanvraaginformatie, geen bevestiging en geen event.
            return _leeg_resultaat(
                "unconfirmed_claim",
                f"categorie {categorie!r} volgens de aanvraag als "
                f"{claim.get('origin')!r} opgegeven; geen keuzeactie vastgelegd, "
                "niet bevestigd",
            )
        if categorie is None:
            return _leeg_resultaat("absent", "geen categorie en geen keuze-event")
        return _leeg_resultaat(
            "unknown_origin",
            f"categorie {categorie!r} zonder keuze-event: herkomst onbekend "
            "(bestaand record)",
        )
    if not is_categoriekeuze(event):
        return _leeg_resultaat("invalid", "keuze-event heeft niet de verwachte vorm")
    basis = _basisstatus(event)
    binding = event.get("binding")
    staat = staat if isinstance(staat, Mapping) else None

    tekst_ongewijzigd: bool | None = None
    tekst_versie = staat.get("text_changed_on_version") if staat else None
    if staat and staat.get("text_changed"):
        tekst_ongewijzigd = False
    elif isinstance(event.get("text_fingerprint"), str):
        tekst_ongewijzigd = event["text_fingerprint"] == bereken_tekstvingerafdruk(
            definitie_tekst
        )

    redenen: list[str] = []
    vervallen_versie = None
    if staat and not staat.get("current", True):
        vervallen_versie = staat.get("invalidated_on_version")
        redenen.append(
            f"{staat.get('invalidation_reason') or 'keuze vervallen'} "
            f"(versie {vervallen_versie}); alleen een nieuwe keuze herstelt dit"
        )
    if event["candidate"]["fingerprint"] != bereken_kandidaatvingerafdruk(
        begrip, contexten
    ):
        redenen.append("term of context wijkt af van de keuze")
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
            "text_changed_on_version": tekst_versie,
            "invalidated_on_version": vervallen_versie,
            "underlying": basis,
            "reason": "; ".join(redenen),
        }
    reden = {
        "manual_confirmed": (
            f"handmatig gekozen door {event.get('actor')!r} (opgegeven naam, "
            "niet geverifieerd)"
        ),
        "manual_unattributed": (
            "handmatige keuze volgens de aanvraag; door niemand bevestigd"
        ),
        "model_suggestion": "voorstel van het classificatiemodel, niet bevestigd",
        "imported": "overgenomen uit importbron",
        "imported_missing": "importbron had geen categorie",
        "default": "door de code toegepaste default, geen keuze",
    }[basis]
    if tekst_ongewijzigd is False:
        reden += (
            "; de tekst is sindsdien gewijzigd"
            + (f" (versie {tekst_versie})" if tekst_versie is not None else "")
            + " — de keuze gold voor de tekst van toen"
        )
    return {
        "status": basis,
        "binding": binding,
        "text_unchanged": tekst_ongewijzigd,
        "text_changed_on_version": tekst_versie,
        "invalidated_on_version": None,
        "underlying": None,
        "reason": reden,
    }
