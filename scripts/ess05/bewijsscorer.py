"""DEF-768 — scorer voor een ESS-05-interpretatieproef (alleen evaluatie, geen productiepad).

Leest één ruwe interpretatie plus het vooraf vastgelegde orakel van het geval en
meet vier dingen apart (oorzakenonderzoek-ess05-v1.md §6):

- M-a: geldigheid per bewijsitem (`bewijsregels.bewijsdiagnose`, stopt niet bij de eerste fout);
- M-b: draagt elk genoemd bewijs het feit volgens het orakel (eenheidtekst-prefixen);
- M-c: juiste toestand op de dragende kenmerken;
- M-d: deterministische uitkomst van `bepaal` (vóór semantische controles).

Kenmerken worden op kernwoord gevonden (het model nummert K1… per run anders):
het modelkenmerk waarvan het definitiecitaat het kernwoord bevat.

Plan `docs/plans/2026-09-28-DEF-768-ess05-bewijseenheden-plan-v1.md`, taak B1;
de plancode is overgenomen, met deze afwijkingen:

- Nooit een exception bij ongeldige modeluitvoer (opdracht): elke structuur
  die niet het verwachte type heeft, telt als niet-dragend en niet-juist; een
  exception uit `bepaal` zelf wordt `m_d.fout = "exception:<type>"`.
- M-b (aanvulling C3 op het plan, Codex-review B3/B4): het orakel scheidt per
  feit `vereist` (minstens één genoemde eenheid begint met zo'n prefix) van
  `toegestaan` (context die erbij mag staan); elke genoemde eenheid valt onder
  een van beide, anders draagt het feit niet. Alleen context zonder vereiste
  eenheid draagt niet; zonder antwoord of zonder bewijs ook niet (in de
  plancode vacuüm waar). Het oude veld `eenheden` is een orakelfout.
- Voorwaarde (aanvulling v4 op het plan, Codex-hercontrole v3, besluit optie
  2 van Chris): na vier rondes lexicale regels met telkens een nieuw lek krijgt
  een orakel met `voorwaarde` (casus E) nooit een automatische
  voorwaardestatus. De score zegt altijd `handmatig_beoordelen`; een E-run
  met `error/buiten_bereik` wacht op het oordeel van Chris, een E-run met een
  andere uitkomst is automatisch niet geslaagd (strenger, deterministisch).
  De lexicale signalen (markeringen, formuleringslijst, vermeldingen) zijn
  verwijderd, niet als hint bewaard: Chris beoordeelt de volledige uitvoer.
  `eindoordeel` combineert het proefoordeel met het oordeelbestand van Chris.
- F7 apart (deel C: niet geslaagd, niet kritiek): `m_b_dragend_ok_zonder_f7`
  en `m_c_dragend_ok_zonder_f7` laten de feiten met een F7-afwijking buiten
  beschouwing; de plansleutels blijven streng.

Een ongeldig orakel is geen modeluitvoer maar een invoerfout: `controleer_orakel`
weigert het vóór elke aanroep (`OrakelfoutError`).

Acceptatie volgens deel C van het plan (taak B3): `runoordeel` deelt één run
in (geslaagd, kritiek, handmatig_beoordelen, f7, niet_geslaagd,
geen_interpretatie), `proefoordeel` telt de runs van een interpretatieproef en
geeft het automatische oordeel; met E-runs is dat nooit `geslaagd`.
`eindoordeel` past het oordeel van Chris toe (aanvulling v4, `EINDREGEL`) en
weigert eerst elke runverzameling die niet precies `PROEFSLEUTELS` is of
E-metadata draagt die niet bij de sleutel past (`controleer_runs`, aanvulling
v5, Codex-hercontrole v4 B5/B6).
"""

from __future__ import annotations

import dataclasses
import datetime
import re
from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Any

from domain.ess05 import bewijsregels as br

__all__ = [
    "BUURBESCHRIJVING",
    "EINDREGEL",
    "E_OORDEELSCHEMA",
    "E_OORDELEN",
    "HANDMATIG_E",
    "PROEFSLEUTELS",
    "OordeelfoutError",
    "OrakelfoutError",
    "controleer_orakel",
    "controleer_runs",
    "eindoordeel",
    "proefoordeel",
    "runoordeel",
    "scoor",
]

BUURBESCHRIJVING = "<buurbeschrijving>"
_ORAKELVELDEN = frozenset({"kenmerken", "dragend", "uitkomst"})
_ORAKELOPTIONEEL = frozenset({"voorwaarde", "toelichting"})
#: Aanvulling C3: per feit verplicht bewijs (`vereist`) apart van context (`toegestaan`).
_FEITVELDEN = frozenset({"toestand", "vereist", "toegestaan"})
_FEITOPTIONEEL = frozenset({"f7"})


class OrakelfoutError(ValueError):
    """Een orakel dat niet op de invoer past: invoerfout, nooit een score."""


class OordeelfoutError(ValueError):
    """Een oordeelbestand of callrecord dat niet op de proef past: nooit een oordeel."""


def _lijst(waarde: Any) -> list[Any]:
    return waarde if isinstance(waarde, list) else []


def _objecten(ruw: Any, veld: str) -> list[Mapping[str, Any]]:
    if not isinstance(ruw, Mapping):
        return []
    return [a for a in _lijst(ruw.get(veld)) if isinstance(a, Mapping)]


def _tekst(waarde: Any) -> str | None:
    return waarde if isinstance(waarde, str) else None


def _eenheidtekst(invoer: br.Vergelijkingsinvoer, uid: Any) -> str | None:
    if not isinstance(uid, str):
        return None
    ref = invoer.eenheden().get(uid)
    if ref is None:
        return None
    if ref.material_id.startswith("neighbour:"):
        return BUURBESCHRIJVING
    return invoer.materiaal[ref.material_id][ref.start : ref.end]


def _kenmerk_id(ruw: Any, kernwoord: str) -> str | None:
    kern = ruw.get("kern") if isinstance(ruw, Mapping) else None
    treffers = [
        k.get("id")
        for k in _objecten(kern, "kenmerken")
        if kernwoord.casefold() in (_tekst(k.get("citaat")) or "").casefold()
    ]
    if len(treffers) == 1 and isinstance(treffers[0], str):
        return treffers[0]
    return None


def _onderwerp(invoer: br.Vergelijkingsinvoer, naam: str) -> str:
    if naam == "doel":
        return br.DOEL
    per_term = {t: b for b, t in invoer.buren}
    if naam not in per_term:
        msg = f"orakel noemt onderwerp {naam!r}; de invoer kent {sorted(per_term)}"
        raise OrakelfoutError(msg)
    return per_term[naam]


#: Aanvulling v4 (besluit optie 2): het voorwaardeoordeel bij E is altijd van Chris.
HANDMATIG_E = "E: voorwaardeoordeel door Chris (aanvulling v4)"
E_OORDEELSCHEMA = "def768-ess05-e-oordeel/1"
#: De statussen die Chris per E-run kan geven.
E_OORDELEN = ("behouden", "ontkend", "weggevallen")
_OORDEELVELDEN = frozenset(
    {"run", "e_uitvoer_sha256", "status", "beoordelaar", "datum"}
)
KRITIEK_WEGGEVALLEN = "E: voorwaarde weggevallen (oordeel Chris)"
KRITIEK_ONTKEND = "E: voorwaarde ontkend of opgeheven (oordeel Chris)"
#: De vooraf vastgelegde beslisregel (aanvulling v4).
EINDREGEL = (
    "geslaagd alleen als alle automatische criteria van deel C slagen (M-d ≥ 11, "
    "M-c en M-b 12/12, geen kritieke run) én Chris elke E-run 'behouden' oordeelt; "
    "een E-run telt pas als behouden bij dat oordeel én uitkomst error/buiten_bereik"
)


def _draagt(
    teksten: Sequence[str | None], vereist: Sequence[str], toegestaan: Sequence[str]
) -> bool:
    """M-b per feit (aanvulling C3): elke genoemde eenheid valt onder `vereist`
    of `toegestaan`, en bij een niet-lege `vereist` begint minstens één genoemde
    eenheid met een vereist prefix. Beide leeg: alleen zonder bewijs draagt het."""

    def past(t: str | None, prefixen: Sequence[str]) -> bool:
        return t is not None and any(t.startswith(p) for p in prefixen)

    alle = [*vereist, *toegestaan]
    if not all(past(t, alle) for t in teksten):
        return False
    return not vereist or any(past(t, vereist) for t in teksten)


def _uitkomst(
    ruw: Any, invoer: br.Vergelijkingsinvoer
) -> tuple[str | None, str | None]:
    """(uitkomst, foutsoort) van `bepaal`; een exception daaruit wordt een foutsoort."""
    try:
        uitkomst = br.bepaal(ruw, invoer)
    except Exception as exc:  # de scorer geeft nooit een exception
        return None, f"exception:{type(exc).__name__}"
    return uitkomst.uitkomst, uitkomst.fout.soort if uitkomst.fout else None


def _uitkomst_toegestaan(
    uitkomst: str | None, fout: str | None, toegestaan: Any
) -> bool:
    """Orakelwaarde 'pass' of 'error/buiten_bereik' (uitkomst plus foutsoort)."""
    if uitkomst is None:
        return False
    gekregen = f"{uitkomst}/{fout}" if fout is not None else uitkomst
    return gekregen in toegestaan


def _diagnose(ruw: Any, invoer: br.Vergelijkingsinvoer) -> list[dict[str, str]]:
    try:
        return [dataclasses.asdict(d) for d in br.bewijsdiagnose(ruw, invoer)]
    except Exception as exc:  # de scorer geeft nooit een exception
        return [
            {
                "pad": "interpretatie",
                "soort": f"exception:{type(exc).__name__}",
                "melding": "",
            }
        ]


def _tekstlijst(waarde: Any) -> bool:
    return isinstance(waarde, list) and all(isinstance(w, str) and w for w in waarde)


def _controleer_feit(pad: str, verwacht: Any) -> None:
    """Aanvulling C3: {toestand, vereist, toegestaan[, f7]}, elk een lijst tekst."""
    if not isinstance(verwacht, Mapping):
        msg = f"{pad}: geen object"
        raise OrakelfoutError(msg)
    anders = sorted((set(verwacht) - _FEITOPTIONEEL) ^ _FEITVELDEN)
    if anders:
        msg = f"{pad}: onbekende of ontbrekende velden {anders}"
        raise OrakelfoutError(msg)
    for veld in sorted(set(verwacht)):
        if not _tekstlijst(verwacht[veld]):
            msg = f"{pad}.{veld}: geen lijst van teksten"
            raise OrakelfoutError(msg)
    if not verwacht["toestand"]:
        msg = f"{pad}.toestand: leeg"
        raise OrakelfoutError(msg)
    dubbel = sorted(set(verwacht["vereist"]) & set(verwacht["toegestaan"]))
    if dubbel:
        msg = f"{pad}: prefix zowel vereist als toegestaan: {dubbel}"
        raise OrakelfoutError(msg)


def controleer_orakel(orakel: Any, invoer: br.Vergelijkingsinvoer) -> None:
    """Het orakel past op de invoer (vóór elke aanroep); anders `OrakelfoutError`."""
    if not isinstance(orakel, Mapping):
        raise OrakelfoutError("orakel is geen object")
    anders = sorted((set(orakel) - _ORAKELOPTIONEEL) ^ _ORAKELVELDEN)
    if anders:
        msg = f"orakel: onbekende of ontbrekende velden {anders}"
        raise OrakelfoutError(msg)
    kenmerken = orakel["kenmerken"]
    if not isinstance(kenmerken, Mapping):
        raise OrakelfoutError("orakel.kenmerken is geen object")
    for kernwoord, per_onderwerp in kenmerken.items():
        if not isinstance(per_onderwerp, Mapping) or not per_onderwerp:
            msg = f"orakel.kenmerken.{kernwoord}: geen onderwerpen"
            raise OrakelfoutError(msg)
        for naam, verwacht in per_onderwerp.items():
            _onderwerp(invoer, naam)
            _controleer_feit(f"orakel.kenmerken.{kernwoord}.{naam}", verwacht)
    if not set(orakel["dragend"]) <= set(kenmerken):
        raise OrakelfoutError("orakel.dragend noemt een onbekend kernwoord")
    if not orakel["uitkomst"]:
        raise OrakelfoutError("orakel.uitkomst is leeg")
    if "voorwaarde" in orakel and not (
        isinstance(orakel["voorwaarde"], str) and orakel["voorwaarde"]
    ):
        raise OrakelfoutError("orakel.voorwaarde is geen tekst")


def scoor(
    ruw: Any, invoer: br.Vergelijkingsinvoer, orakel: Mapping[str, Any]
) -> dict[str, Any]:
    """Alle maten voor één run; geen exception bij slechte modeluitvoer."""
    alle = _objecten(ruw, "antwoorden")
    positief = [a for a in alle if a.get("toestand") != "onbesproken"]
    uitkomst, fout = _uitkomst(ruw, invoer)
    feiten: list[dict[str, Any]] = []
    f7: list[str] = []
    for kernwoord, per_onderwerp in orakel["kenmerken"].items():
        kid = _kenmerk_id(ruw, kernwoord)
        dragend = kernwoord in orakel.get("dragend", [])
        for naam, verwacht in per_onderwerp.items():
            onderwerp = _onderwerp(invoer, naam)
            antwoorden = [
                a
                for a in alle
                if kid
                and a.get("kenmerk_id") == kid
                and a.get("onderwerp") == onderwerp
            ]
            toestanden = sorted(
                {
                    t if isinstance(t, str) else repr(t)
                    for t in (a.get("toestand") for a in antwoorden)
                }
            )
            teksten = [
                _eenheidtekst(invoer, u) if isinstance(a.get("citaten"), list) else None
                for a in antwoorden
                for u in (
                    a["citaten"] if isinstance(a.get("citaten"), list) else [None]
                )
            ]
            draagt = kid is not None and _draagt(
                teksten, verwacht["vereist"], verwacht["toegestaan"]
            )
            juist = bool(toestanden) and set(toestanden) <= set(verwacht["toestand"])
            is_f7 = not juist and bool(set(toestanden) & set(verwacht.get("f7", [])))
            if is_f7:
                f7.append(f"{kernwoord}/{naam}: {toestanden}")
            feiten.append(
                {
                    "kernwoord": kernwoord,
                    "onderwerp": naam,
                    "kenmerk_id": kid,
                    "dragend": dragend,
                    "toestanden": toestanden,
                    "toestand_juist": juist,
                    "eenheden": teksten,
                    "draagt": draagt,
                    "f7": is_f7,
                }
            )
    dragende = [f for f in feiten if f["dragend"]]
    zonder_f7 = [f for f in dragende if not f["f7"]]
    voorwaarde = orakel.get("voorwaarde")
    return {
        "m_a": {"items": len(positief), "fouten": _diagnose(ruw, invoer)},
        "m_b_dragend_ok": all(f["draagt"] for f in dragende),
        "m_c_dragend_ok": all(f["toestand_juist"] for f in dragende),
        "m_b_dragend_ok_zonder_f7": all(f["draagt"] for f in zonder_f7),
        "m_c_dragend_ok_zonder_f7": all(f["toestand_juist"] for f in zonder_f7),
        "m_d": {
            "uitkomst": uitkomst,
            "fout": fout,
            "verwacht": list(orakel["uitkomst"]),
            "ok": _uitkomst_toegestaan(uitkomst, fout, orakel["uitkomst"]),
        },
        # Aanvulling v4: nooit automatisch behouden; het oordeel is van Chris.
        "voorwaarde_behouden": False if voorwaarde else None,
        "voorwaarde_status": "handmatig_beoordelen" if voorwaarde else None,
        "f7_afwijkingen": f7,
        "feiten": feiten,
    }


# --- acceptatie per run en per proef (deel C) ------------------------------------------------

#: Deel C, bij 12 runs: geslaagd vanaf 11 juiste M-d, afgekeurd bij 8 of minder.
RUNS_VERWACHT, M_D_MIN, M_D_AFKEUR = 12, 11, 8
#: Aanvulling v5 (Codex-hercontrole v4, B5): de vaste runverzameling van R18A,
#: A/C/D/E × herhaling 1–3; E is de casus met de voorwaarde.
PROEFITEMS, E_ITEM, HERHALINGEN = ("A", "C", "D", "E"), "E", 3
PROEFSLEUTELS = tuple(
    f"interpretatie|{n}|{h}" for n in PROEFITEMS for h in range(1, HERHALINGEN + 1)
)
E_SLEUTELS = tuple(s for s in PROEFSLEUTELS if s.split("|")[1] == E_ITEM)
_GRENS = (
    "11/12 geeft een ondergrens van circa 66% (95%, eenzijdig); dit is geen "
    "productiebetrouwbaarheid"
)


def runoordeel(
    score: Mapping[str, Any] | None, orakel: Mapping[str, Any]
) -> dict[str, Any]:
    """Eén run volgens deel C; `score` is None als er geen interpretatie was.

    - Kritiek: `pass`/`fail` terwijl M-c of M-b op de dragende kenmerken onwaar
      is (F7-feiten buiten beschouwing).
    - E (orakel met `voorwaarde`, aanvulling v4): nooit automatisch geslaagd en
      nooit een lexicale status. Met een juiste uitkomst wacht de run op het
      oordeel van Chris (`handmatig_beoordelen`, `HANDMATIG_E`; niet kritiek,
      stopt niet, M-d telt pas na dat oordeel); anders is hij automatisch
      niet geslaagd. Wat de score over de voorwaarde zegt, telt niet.
    - F7: apart, niet geslaagd en niet kritiek.
    - Volgorde: kritiek > handmatig_beoordelen > f7 > geslaagd > niet_geslaagd.
    """
    voorwaarde = orakel.get("voorwaarde")
    if score is None:
        return {
            "categorie": "geen_interpretatie",
            "gekregen": None,
            "m_d_telt": False,
            "m_b_dragend_ok": False,
            "m_c_dragend_ok": False,
            "voorwaarde_behouden": False if voorwaarde else None,
            "voorwaarde_status": None,
            "kritiek": [],
            "handmatig": [],
            "f7": [],
        }
    md = score["m_d"]
    gekregen = (
        md["uitkomst"] if md["fout"] is None else f"{md['uitkomst']}/{md['fout']}"
    )
    # E: M-d telt pas na het oordeel van Chris (`eindoordeel`).
    m_d_telt = bool(md["ok"]) and not voorwaarde
    kritiek, handmatig = [], []
    if md["uitkomst"] in ("pass", "fail"):
        if not score["m_c_dragend_ok_zonder_f7"]:
            kritiek.append("pass/fail bij M-c onwaar")
        if not score["m_b_dragend_ok_zonder_f7"]:
            kritiek.append("pass/fail bij M-b onwaar")
    if voorwaarde and md["ok"] and not kritiek:
        handmatig.append(HANDMATIG_E)
    f7 = list(score["f7_afwijkingen"])
    if kritiek:
        categorie = "kritiek"
    elif handmatig:
        categorie = "handmatig_beoordelen"
    elif f7:
        categorie = "f7"
    elif m_d_telt and score["m_b_dragend_ok"] and score["m_c_dragend_ok"]:
        categorie = "geslaagd"
    else:
        categorie = "niet_geslaagd"
    return {
        "categorie": categorie,
        "gekregen": gekregen,
        "m_d_telt": m_d_telt,
        "m_b_dragend_ok": bool(score["m_b_dragend_ok"]),
        "m_c_dragend_ok": bool(score["m_c_dragend_ok"]),
        "voorwaarde_behouden": False if voorwaarde else None,
        "voorwaarde_status": "handmatig_beoordelen" if voorwaarde else None,
        "kritiek": kritiek,
        "handmatig": handmatig,
        "f7": f7,
    }


def proefoordeel(runs: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Oordeel over de runs (elk een `runoordeel` plus `sleutel`), deel C.

    Afgekeurd bij één kritieke run of M-d ≤ 8, ook met de ontbrekende runs en
    de handmatig te beoordelen runs erbij (die kunnen juist blijken);
    onvolledig onder 12 runs; geslaagd bij M-d ≥ 11, M-c en M-b 12/12, geen
    run die op beoordeling wacht en elke E-run met behouden voorwaarde — dat
    laatste zet alleen `eindoordeel` na het oordeel van Chris (aanvulling v4),
    dus automatisch is een proef met E-runs nooit geslaagd. Anders wacht de
    proef op de handmatige beoordeling (als 11 dan nog haalbaar is) of op het
    F7-besluit van Chris, of is het tussengebied (analyseren, geen nieuwe
    ronde zonder besluit).
    """
    n = len(runs)
    m_d = sum(1 for r in runs if r["m_d_telt"])
    m_c = sum(1 for r in runs if r["m_c_dragend_ok"])
    m_b = sum(1 for r in runs if r["m_b_dragend_ok"])
    e_runs = [r for r in runs if r["voorwaarde_behouden"] is not None]
    e_ok = sum(1 for r in e_runs if r["voorwaarde_behouden"] is True)
    kritiek = [
        {"sleutel": r["sleutel"], "redenen": list(r["kritiek"])}
        for r in runs
        if r["kritiek"]
    ]
    handmatig = [
        {"sleutel": r["sleutel"], "redenen": list(r["handmatig"])}
        for r in runs
        if r["handmatig"]
    ]
    f7 = [
        {"sleutel": r["sleutel"], "afwijkingen": list(r["f7"])} for r in runs if r["f7"]
    ]
    # Onder 12 runs telt M-d ≤ 8 pas als ook de ontbrekende runs dat niet redden.
    haalbaar = m_d + max(0, RUNS_VERWACHT - n) + len(handmatig)
    if kritiek or haalbaar <= M_D_AFKEUR:
        oordeel = "afgekeurd"
    elif n < RUNS_VERWACHT:
        oordeel = "onvolledig"
    elif (
        m_d >= M_D_MIN
        and m_c == n
        and m_b == n
        and e_ok == len(e_runs)
        and not handmatig
    ):
        oordeel = "geslaagd"
    elif handmatig and m_d + len(handmatig) >= M_D_MIN:
        oordeel = "wacht_op_handmatige_beoordeling"
    elif f7:
        oordeel = "wacht_op_f7_besluit"
    else:
        oordeel = "tussengebied"
    return {
        "oordeel": oordeel,
        "runs": n,
        "runs_verwacht": RUNS_VERWACHT,
        "m_d_juist": m_d,
        "m_c_dragend": m_c,
        "m_b_dragend": m_b,
        "e_voorwaarde_behouden": [e_ok, len(e_runs)],
        "kritiek": kritiek,
        "handmatig_beoordelen": handmatig,
        "f7": f7,
        "categorieen": dict(sorted(Counter(r["categorie"] for r in runs).items())),
        "grens": _GRENS,
    }


# --- eindoordeel: proefoordeel plus het oordeel van Chris bij E (aanvulling v4) ---------------


def _is_datum(waarde: Any) -> bool:
    if not (isinstance(waarde, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", waarde)):
        return False
    try:
        datetime.date.fromisoformat(waarde)
    except ValueError:
        return False
    return True


def _controleer_oordelen(data: Any, te_beoordelen: Mapping[str, str]) -> dict[str, str]:
    """{run: status} uit het oordeelbestand; weigert elk oordeel dat niet precies
    past: onbekende velden, dubbel, onbekende run, afwijkende hash, ongeldige
    status/beoordelaar/datum, of een ontbrekend oordeel."""
    if not isinstance(data, Mapping) or set(data) != {"schema", "oordelen"}:
        raise OordeelfoutError("oordeelbestand: precies de velden schema en oordelen")
    if data["schema"] != E_OORDEELSCHEMA:
        msg = f"oordeelbestand: schema is niet {E_OORDEELSCHEMA}"
        raise OordeelfoutError(msg)
    if not isinstance(data["oordelen"], list):
        raise OordeelfoutError("oordeelbestand: oordelen is geen lijst")
    statussen: dict[str, str] = {}
    for i, o in enumerate(data["oordelen"]):
        pad = f"oordelen[{i}]"
        if not isinstance(o, Mapping) or set(o) != _OORDEELVELDEN:
            msg = f"{pad}: onbekende of ontbrekende velden (verwacht {sorted(_OORDEELVELDEN)})"
            raise OordeelfoutError(msg)
        run = o["run"]
        if run in statussen:
            raise OordeelfoutError(f"{pad}: dubbel oordeel voor {run!r}")
        if run not in te_beoordelen:
            raise OordeelfoutError(f"{pad}: onbekende run {run!r}")
        if o["e_uitvoer_sha256"] != te_beoordelen[run]:
            msg = f"{pad}: e_uitvoer_sha256 wijkt af van de E-uitvoer van {run}"
            raise OordeelfoutError(msg)
        if o["status"] not in E_OORDELEN:
            msg = f"{pad}: status {o['status']!r} is niet een van {list(E_OORDELEN)}"
            raise OordeelfoutError(msg)
        if not (isinstance(o["beoordelaar"], str) and o["beoordelaar"].strip()):
            raise OordeelfoutError(f"{pad}: beoordelaar ontbreekt")
        if not _is_datum(o["datum"]):
            raise OordeelfoutError(f"{pad}: datum is geen geldige JJJJ-MM-DD")
        statussen[run] = o["status"]
    ontbrekend = sorted(set(te_beoordelen) - set(statussen))
    if ontbrekend:
        raise OordeelfoutError(f"oordeel ontbreekt voor {ontbrekend}")
    return statussen


def _met_oordeel(run: Mapping[str, Any], status: str | None) -> dict[str, Any]:
    """De run na het oordeel van Chris; alleen strenger dan automatisch, behalve
    dat een wachtende run (juiste uitkomst) met 'behouden' kan slagen. De regels
    van C2 blijven, nu op dat oordeel: weggevallen is kritiek; ontkend is
    kritiek tenzij de uitkomst error/buiten_bereik is."""
    if status is None:
        return dict(run)
    kritiek = list(run["kritiek"])
    if status == "weggevallen":
        kritiek.append(KRITIEK_WEGGEVALLEN)
    elif status == "ontkend" and run["gekregen"] != "error/buiten_bereik":
        kritiek.append(KRITIEK_ONTKEND)
    behouden = status == "behouden" and run["categorie"] == "handmatig_beoordelen"
    if kritiek:
        categorie = "kritiek"
    elif run["f7"]:
        categorie = "f7"
    elif behouden and run["m_b_dragend_ok"] and run["m_c_dragend_ok"]:
        categorie = "geslaagd"
    else:
        categorie = "niet_geslaagd"
    return {
        **run,
        "categorie": categorie,
        "m_d_telt": behouden,
        "voorwaarde_behouden": behouden,
        "voorwaarde_status": status,
        "kritiek": kritiek,
        "handmatig": [],
    }


_SHA256 = re.compile(r"[0-9a-f]{64}")


def _strijdig_e(run: Mapping[str, Any]) -> str | None:
    """Waarom de metadata van een E-run niet bij E past (None als ze past).

    Automatisch is een E-run nooit geslaagd en nooit behouden; wie op het
    oordeel wacht, heeft de hash van zijn beoordeelde uitvoer.
    """
    wacht = run.get("categorie") == "handmatig_beoordelen"
    if run.get("voorwaarde_behouden") is not False:
        return "voorwaarde_behouden is niet False"
    if run.get("categorie") == "geslaagd" or run.get("m_d_telt") is not False:
        return "automatisch geslaagd of M-d telt"
    if run.get("voorwaarde_status") not in ("handmatig_beoordelen", None):
        return f"voorwaarde_status {run.get('voorwaarde_status')!r}"
    if wacht != (run.get("handmatig") == [HANDMATIG_E]):
        return "handmatig past niet bij de categorie"
    sha = run.get("e_uitvoer_sha256")
    if wacht and not (isinstance(sha, str) and _SHA256.fullmatch(sha)):
        return "wacht op het oordeel zonder e_uitvoer_sha256"
    return None


def _strijdig_niet_e(run: Mapping[str, Any]) -> str | None:
    """Waarom een niet-E-run E-metadata draagt (None als hij die niet draagt)."""
    for veld in ("voorwaarde_behouden", "voorwaarde_status", "e_uitvoer_sha256"):
        if run.get(veld) is not None:
            return f"{veld} is gezet"
    if HANDMATIG_E in (run.get("handmatig") or []):
        return "wacht op het E-oordeel"
    return None


def controleer_runs(runs: Any) -> None:
    """Aanvulling v5 (Codex-hercontrole v4, B5/B6): weigert tenzij `runs` precies
    de runverzameling `PROEFSLEUTELS` is — unieke sleutels, geen onbekende of
    ontbrekende run — en de metadata van elke run past bij zijn casus (E uit de
    sleutel, niet uit de metadata). Duplicaten worden vóór elke dict-omzetting
    geteld."""
    if not isinstance(runs, (list, tuple)):
        raise OordeelfoutError("runs: geen lijst")
    for i, r in enumerate(runs):
        if not isinstance(r, Mapping) or not isinstance(r.get("sleutel"), str):
            raise OordeelfoutError(f"runs[{i}]: geen run met een sleutel")
    telling = Counter(r["sleutel"] for r in runs)
    dubbel = sorted(s for s, n in telling.items() if n > 1)
    if dubbel:
        raise OordeelfoutError(f"dubbele runs {dubbel}")
    onbekend = sorted(set(telling) - set(PROEFSLEUTELS))
    if onbekend:
        raise OordeelfoutError(f"onbekende runs {onbekend}")
    ontbrekend = [s for s in PROEFSLEUTELS if s not in telling]
    if ontbrekend:
        raise OordeelfoutError(f"ontbrekende runs {ontbrekend}")
    for r in runs:
        reden = (_strijdig_e if r["sleutel"] in E_SLEUTELS else _strijdig_niet_e)(r)
        if reden:
            raise OordeelfoutError(f"{r['sleutel']}: strijdige metadata ({reden})")


def eindoordeel(runs: Sequence[Mapping[str, Any]], oordelen: Any) -> dict[str, Any]:
    """Aanvulling v4/v5: het proefoordeel na het oordeel van Chris over elke E-run.

    `runs`: precies `PROEFSLEUTELS` (`controleer_runs`), elk een `runoordeel`
    plus `sleutel` en, voor E, `e_uitvoer_sha256` (de sha256 van de ruwe
    modeluitvoer die Chris beoordeelde; `None` zonder gescoorde uitvoer). Elke
    E-run met uitvoer heeft precies één oordeel nodig (`OordeelfoutError`
    anders); geslaagd vereist dus drie afzonderlijke oordelen 'behouden', elk
    aan de hash van de eigen uitvoer gebonden. Beslisregel: `EINDREGEL`.
    """
    controleer_runs(runs)
    te_beoordelen = {
        r["sleutel"]: r["e_uitvoer_sha256"]
        for r in runs
        if r["sleutel"] in E_SLEUTELS and r["e_uitvoer_sha256"] is not None
    }
    statussen = _controleer_oordelen(oordelen, te_beoordelen)
    na = [_met_oordeel(r, statussen.get(r["sleutel"])) for r in runs]
    return {
        **proefoordeel(na),
        "e_oordelen": [
            {"run": run, "status": s, "e_uitvoer_sha256": te_beoordelen[run]}
            for run, s in statussen.items()
        ],
        "regel": EINDREGEL,
    }
