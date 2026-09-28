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
- Voorwaarde (aanvulling C2 op het plan, Codex-review B2; aanvulling v2,
  Codex-hercontrole B2-rest): geen woordzoeking maar een status. `behouden`
  alleen via het schemaveld: een doelvoorwaarde met de frase die met een
  voorwaardelijke aanhef begint (`AANHEF`), zonder markering (`MARKERINGEN`),
  niet opgeheven, én `bepaal` geeft `error/buiten_bereik`. `ontkend` bij een
  markering in een doelvoorwaarde of `buiten_kern`-kenmerk. Een
  `buiten_kern`-kenmerk (M-kenmerk) met de frase geeft nooit automatisch
  behouden maar `handmatig_beoordelen`, net als een vermelding elders of
  zonder aanhef, of een doelvoorwaarde naast een onvoorwaardelijk gelijk
  antwoord (zoals `bewijsregels._onverwerkte_voorwaarden`); `weggevallen` als
  de frase nergens staat.
- F7 apart (deel C: niet geslaagd, niet kritiek): `m_b_dragend_ok_zonder_f7`
  en `m_c_dragend_ok_zonder_f7` laten de feiten met een F7-afwijking buiten
  beschouwing; de plansleutels blijven streng.

Een ongeldig orakel is geen modeluitvoer maar een invoerfout: `controleer_orakel`
weigert het vóór elke aanroep (`OrakelfoutError`).

Acceptatie volgens deel C van het plan (taak B3): `runoordeel` deelt één run
in (geslaagd, kritiek, handmatig_beoordelen, f7, niet_geslaagd,
geen_interpretatie), `proefoordeel` telt de runs van een interpretatieproef en
geeft het eindoordeel.
"""

from __future__ import annotations

import dataclasses
import re
from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Any

from domain.ess05 import bewijsregels as br

__all__ = [
    "AANHEF",
    "BUURBESCHRIJVING",
    "MARKERINGEN",
    "VOORWAARDESTATUSSEN",
    "OrakelfoutError",
    "controleer_orakel",
    "proefoordeel",
    "runoordeel",
    "scoor",
]

BUURBESCHRIJVING = "<buurbeschrijving>"
_ORAKELVELDEN = frozenset({"kenmerken", "dragend", "uitkomst"})
_ORAKELOPTIONEEL = frozenset({"voorwaarde", "voorwaarde_vereist_voor", "toelichting"})
#: Aanvulling C3: per feit verplicht bewijs (`vereist`) apart van context (`toegestaan`).
_FEITVELDEN = frozenset({"toestand", "vereist", "toegestaan"})
_FEITOPTIONEEL = frozenset({"f7"})


class OrakelfoutError(ValueError):
    """Een orakel dat niet op de invoer past: invoerfout, nooit een score."""


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


def _voorwaarden(a: Mapping[str, Any]) -> list[str]:
    return [v for v in _lijst(a.get("voorwaarden")) if isinstance(v, str)]


#: Aanvulling C2/v2: ontkennende of opheffende markeringen (hele woorden, zonder
#: hoofdletteronderscheid) in dezelfde tekstwaarde als de voorwaardefrase.
MARKERINGEN = (
    "ook zonder",
    "ook buiten",
    "ongeacht of",
    "zonder",
    "niet",
    "geen",
    "ongeacht",
    "altijd",
    "onafhankelijk",
    "irrelevant",
    "optioneel",
)
#: Aanvulling v2 (B2-rest): de voorwaardelijke aanhef waarmee een doelvoorwaarde
#: begint (na witruimte, zonder hoofdletteronderscheid).
AANHEF = (
    "bij ",
    "alleen bij ",
    "uitsluitend bij ",
    "in geval van ",
    "als ",
    "wanneer ",
    "indien ",
    "mits ",
)
#: Aanvulling v2: alleen de onverwerkte voorwaardelijke doeleis geeft behouden.
_BEHOUDEN_UITKOMST = ("error", "buiten_bereik")
VOORWAARDESTATUSSEN = ("behouden", "ontkend", "handmatig_beoordelen", "weggevallen")


def _markeringen(tekst: str) -> list[str]:
    """Alle markeringen in de tekst (ook overlappende: 'ook zonder' en 'zonder')."""
    t = tekst.casefold()
    return sorted(
        m for m in MARKERINGEN if re.search(r"(?<!\w)" + re.escape(m) + r"(?!\w)", t)
    )


def _teksten(waarde: Any, pad: str = "") -> list[tuple[str, str]]:
    """Alle tekstwaarden in een willekeurige structuur, met hun pad."""
    if isinstance(waarde, str):
        return [(pad, waarde)]
    if isinstance(waarde, Mapping):
        return [
            t
            for k, v in waarde.items()
            for t in _teksten(v, f"{pad}.{k}" if pad else str(k))
        ]
    if isinstance(waarde, list):
        return [t for i, v in enumerate(waarde) for t in _teksten(v, f"{pad}[{i}]")]
    return []


def _voorwaardestatus(
    ruw: Any, frase: str, uitkomst: tuple[str | None, str | None]
) -> tuple[str, list[dict[str, Any]]]:
    """Aanvulling C2/v2 (Codex-review B2, hercontrole B2-rest): behouden,
    ontkend, handmatig of weggevallen.

    Behouden is alleen een doelantwoord met een voorwaarde die de frase bevat,
    met een voorwaardelijke aanhef begint (`AANHEF`), geen markering bevat en
    niet opgeheven is door een onvoorwaardelijk gelijk doelantwoord, terwijl
    `bepaal` `error/buiten_bereik` geeft. Een markering in een doelvoorwaarde
    of `buiten_kern`-kenmerk maakt de voorwaarde ontkend, ook naast een
    correcte vermelding. Een `buiten_kern`-kenmerk met de frase geeft nooit
    automatisch behouden: handmatig beoordelen (ook naast een correcte
    doelvoorwaarde; conservatief). Komt de frase elders of niet eenduidig voor:
    handmatig beoordelen; nergens: weggevallen.
    """
    f = frase.casefold()
    antwoorden = _objecten(ruw, "antwoorden")
    doel = [(i, a) for i, a in enumerate(antwoorden) if a.get("onderwerp") == br.DOEL]
    vermeldingen: list[dict[str, Any]] = []

    def vermeld(pad: str, tekst: str, plek: str) -> dict[str, Any]:
        v = {"pad": pad, "tekst": tekst, "plek": plek, "markering": _markeringen(tekst)}
        vermeldingen.append(v)
        return v

    def opgeheven(a: Mapping[str, Any]) -> bool:
        return any(
            b.get("kenmerk_id") == a.get("kenmerk_id")
            and b.get("toestand") == a.get("toestand")
            and not _voorwaarden(b)
            for _, b in doel
        )

    gezien: set[str] = set()
    a_ok = False
    for i, a in doel:
        for j, v in enumerate(_lijst(a.get("voorwaarden"))):
            if isinstance(v, str) and f in v.casefold():
                pad = f"antwoorden[{i}].voorwaarden[{j}]"
                gezien.add(pad)
                schoon = not vermeld(pad, v, "doelvoorwaarde")["markering"]
                aanhef = v.lstrip().casefold().startswith(AANHEF)
                a_ok = a_ok or (schoon and aanhef and not opgeheven(a))
    for i, m in enumerate(
        _lijst(ruw.get("buiten_kern")) if isinstance(ruw, Mapping) else []
    ):
        if not isinstance(m, Mapping):
            continue
        for k in ("kenmerk", "waarde"):
            tekst = _tekst(m.get(k))
            if tekst is not None and f in tekst.casefold():
                pad = f"buiten_kern[{i}].{k}"
                gezien.add(pad)
                vermeld(pad, tekst, "m_kenmerk")
    for pad, tekst in _teksten(ruw):
        if pad not in gezien and f in tekst.casefold():
            vermeld(pad, tekst, "elders")
    if any(v["markering"] for v in vermeldingen if v["plek"] != "elders"):
        return "ontkend", vermeldingen
    if any(v["plek"] == "m_kenmerk" for v in vermeldingen):
        return "handmatig_beoordelen", vermeldingen
    if a_ok and uitkomst == _BEHOUDEN_UITKOMST:
        return "behouden", vermeldingen
    if vermeldingen:
        return "handmatig_beoordelen", vermeldingen
    return "weggevallen", vermeldingen


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
    vereist = orakel.get("voorwaarde_vereist_voor", [])
    if vereist and not orakel.get("voorwaarde"):
        raise OrakelfoutError("orakel.voorwaarde_vereist_voor zonder voorwaarde")
    if not set(vereist) <= set(orakel["uitkomst"]):
        raise OrakelfoutError("orakel.voorwaarde_vereist_voor buiten orakel.uitkomst")


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
    status, vermeldingen = (
        _voorwaardestatus(ruw, voorwaarde, (uitkomst, fout))
        if voorwaarde
        else (None, None)
    )
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
        "voorwaarde_behouden": status == "behouden" if voorwaarde else None,
        "voorwaarde_status": status,
        "voorwaarde_vermeldingen": vermeldingen,
        "f7_afwijkingen": f7,
        "feiten": feiten,
    }


# --- acceptatie per run en per proef (deel C) ------------------------------------------------

#: Deel C, bij 12 runs: geslaagd vanaf 11 juiste M-d, afgekeurd bij 8 of minder.
RUNS_VERWACHT, M_D_MIN, M_D_AFKEUR = 12, 11, 8
_GRENS = (
    "11/12 geeft een ondergrens van circa 66% (95%, eenzijdig); dit is geen "
    "productiebetrouwbaarheid"
)


def runoordeel(
    score: Mapping[str, Any] | None, orakel: Mapping[str, Any]
) -> dict[str, Any]:
    """Eén run volgens deel C; `score` is None als er geen interpretatie was.

    - M-d telt alleen als juist met behouden voorwaarde waar het orakel dat eist
      (`voorwaarde_vereist_voor`; zonder dat veld: elke uitkomst van een orakel
      met voorwaarde, deel C bij E).
    - Kritiek: `pass`/`fail` terwijl M-c of M-b op de dragende kenmerken onwaar
      is (F7-feiten buiten beschouwing); bij E (aanvulling C2) een weggevallen
      voorwaarde, of een ontkende/opgeheven voorwaarde tenzij de uitkomst
      `error/buiten_bereik` is.
    - Handmatig beoordelen (C2): een voorwaarde die niet eenduidig behouden is;
      niet geslaagd, niet kritiek, M-d telt niet.
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
    vereist = orakel.get(
        "voorwaarde_vereist_voor", orakel["uitkomst"] if voorwaarde else []
    )
    status = score["voorwaarde_status"] if voorwaarde else None
    behouden = status == "behouden" if voorwaarde else None
    m_d_telt = bool(md["ok"]) and (gekregen not in vereist or behouden is True)
    kritiek, handmatig = [], []
    if md["uitkomst"] in ("pass", "fail"):
        if not score["m_c_dragend_ok_zonder_f7"]:
            kritiek.append("pass/fail bij M-c onwaar")
        if not score["m_b_dragend_ok_zonder_f7"]:
            kritiek.append("pass/fail bij M-b onwaar")
    if voorwaarde and status == "weggevallen":
        kritiek.append("E: voorwaarde weggevallen")
    elif voorwaarde and status == "ontkend" and gekregen != "error/buiten_bereik":
        kritiek.append("E: voorwaarde ontkend of opgeheven")
    elif voorwaarde and status == "handmatig_beoordelen":
        handmatig.append("E: voorwaarde niet eenduidig behouden")
    elif voorwaarde and status not in VOORWAARDESTATUSSEN:
        kritiek.append(f"E: onbekende voorwaardestatus {status!r}")
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
        "voorwaarde_behouden": behouden,
        "voorwaarde_status": status,
        "kritiek": kritiek,
        "handmatig": handmatig,
        "f7": f7,
    }


def proefoordeel(runs: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Eindoordeel over de runs (elk een `runoordeel` plus `sleutel`), deel C.

    Afgekeurd bij één kritieke run of M-d ≤ 8, ook met de ontbrekende runs en
    de handmatig te beoordelen runs erbij (aanvulling C2: die kunnen juist
    blijken); onvolledig onder 12 runs; geslaagd bij M-d ≥ 11, M-c en M-b
    12/12 en elke E-run met automatisch behouden voorwaarde (aanvulling v2:
    een handmatig te beoordelen run telt niet mee); anders wacht de proef op de
    handmatige beoordeling (als 11 dan nog haalbaar is) of op het F7-besluit
    van Chris, of is het tussengebied (analyseren, geen nieuwe ronde zonder
    besluit).
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
    elif m_d >= M_D_MIN and m_c == n and m_b == n and e_ok == len(e_runs):
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
