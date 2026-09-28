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
- M-b vraagt bij een orakel met eenheden minstens één genoemde eenheid; zonder
  antwoord of zonder bewijs draagt het feit niet (in de plancode vacuüm waar).
- `voorwaarde_behouden` telt ook een voorwaarde die het model buiten bereik
  plaatst of als kenmerklabel noemt; een voorwaardelijk doelantwoord naast een
  onvoorwaardelijk antwoord met dezelfde toestand telt niet (dan voegt de
  voorwaarde niets toe, zoals `bewijsregels._onverwerkte_voorwaarden`).
- F7 apart (deel C: niet geslaagd, niet kritiek): `m_b_dragend_ok_zonder_f7`
  en `m_c_dragend_ok_zonder_f7` laten de feiten met een F7-afwijking buiten
  beschouwing; de plansleutels blijven streng.

Een ongeldig orakel is geen modeluitvoer maar een invoerfout: `controleer_orakel`
weigert het vóór elke aanroep (`OrakelfoutError`).

Acceptatie volgens deel C van het plan (taak B3): `runoordeel` deelt één run
in (geslaagd, kritiek, f7, niet_geslaagd, geen_interpretatie), `proefoordeel`
telt de runs van een interpretatieproef en geeft het eindoordeel.
"""

from __future__ import annotations

import dataclasses
from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Any

from domain.ess05 import bewijsregels as br

__all__ = [
    "BUURBESCHRIJVING",
    "OrakelfoutError",
    "controleer_orakel",
    "proefoordeel",
    "runoordeel",
    "scoor",
]

BUURBESCHRIJVING = "<buurbeschrijving>"
_ORAKELVELDEN = frozenset({"kenmerken", "dragend", "uitkomst"})
_ORAKELOPTIONEEL = frozenset({"voorwaarde", "voorwaarde_vereist_voor", "toelichting"})


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


def _voorwaarde_behouden(ruw: Any, frase: str) -> bool:
    f = frase.casefold()
    doel = [a for a in _objecten(ruw, "antwoorden") if a.get("onderwerp") == br.DOEL]

    def opgeheven(a: Mapping[str, Any]) -> bool:
        return any(
            b.get("kenmerk_id") == a.get("kenmerk_id")
            and b.get("toestand") == a.get("toestand")
            and not _voorwaarden(b)
            for b in doel
        )

    in_doel = any(
        any(f in v.casefold() for v in _voorwaarden(a)) and not opgeheven(a)
        for a in doel
    )
    m_ids = {
        m["id"]
        for m in _objecten(ruw, "buiten_kern")
        if isinstance(m.get("id"), str)
        and any(f in (_tekst(m.get(k)) or "").casefold() for k in ("kenmerk", "waarde"))
    }
    als_kenmerk = any(
        isinstance(a.get("kenmerk_id"), str)
        and a["kenmerk_id"] in m_ids
        and a.get("toestand") == "bevestigd"
        for a in doel
    )
    buiten_bereik = any(
        any(f in (_tekst(b.get(k)) or "").casefold() for k in ("citaat", "reden"))
        for b in _objecten(ruw, "buiten_bereik")
    )
    return in_doel or als_kenmerk or buiten_bereik


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
            if not isinstance(verwacht, Mapping) or not verwacht.get("toestand"):
                msg = f"orakel.kenmerken.{kernwoord}.{naam}: geen toestand"
                raise OrakelfoutError(msg)
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
            prefixen = verwacht.get("eenheden", [])
            if prefixen:
                draagt = bool(teksten) and all(
                    t is not None and any(t.startswith(p) for p in prefixen)
                    for t in teksten
                )
            else:
                draagt = not teksten
            draagt = draagt and kid is not None
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
        "voorwaarde_behouden": (
            _voorwaarde_behouden(ruw, voorwaarde) if voorwaarde else None
        ),
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
      is (F7-feiten buiten beschouwing), of een weggevallen voorwaarde.
    - F7: apart, niet geslaagd en niet kritiek.
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
            "kritiek": [],
            "f7": [],
        }
    md = score["m_d"]
    gekregen = (
        md["uitkomst"] if md["fout"] is None else f"{md['uitkomst']}/{md['fout']}"
    )
    vereist = orakel.get(
        "voorwaarde_vereist_voor", orakel["uitkomst"] if voorwaarde else []
    )
    behouden = score["voorwaarde_behouden"]
    m_d_telt = bool(md["ok"]) and (gekregen not in vereist or behouden is True)
    kritiek = []
    if md["uitkomst"] in ("pass", "fail"):
        if not score["m_c_dragend_ok_zonder_f7"]:
            kritiek.append("pass/fail bij M-c onwaar")
        if not score["m_b_dragend_ok_zonder_f7"]:
            kritiek.append("pass/fail bij M-b onwaar")
    if voorwaarde and behouden is not True:
        kritiek.append("E: voorwaarde weggevallen")
    f7 = list(score["f7_afwijkingen"])
    if kritiek:
        categorie = "kritiek"
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
        "kritiek": kritiek,
        "f7": f7,
    }


def proefoordeel(runs: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Eindoordeel over de runs (elk een `runoordeel` plus `sleutel`), deel C.

    Afgekeurd bij één kritieke run of M-d ≤ 8 (ook met de ontbrekende runs
    erbij); onvolledig onder 12 runs;
    geslaagd bij M-d ≥ 11, M-c en M-b 12/12 en elke E-run met behouden
    voorwaarde; anders wacht een F7-afwijking op het besluit van Chris, of is
    het tussengebied (analyseren, geen nieuwe ronde zonder besluit).
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
    f7 = [
        {"sleutel": r["sleutel"], "afwijkingen": list(r["f7"])} for r in runs if r["f7"]
    ]
    # Onder 12 runs telt M-d ≤ 8 pas als ook de ontbrekende runs dat niet redden.
    if kritiek or m_d + max(0, RUNS_VERWACHT - n) <= M_D_AFKEUR:
        oordeel = "afgekeurd"
    elif n < RUNS_VERWACHT:
        oordeel = "onvolledig"
    elif m_d >= M_D_MIN and m_c == n and m_b == n and e_ok == len(e_runs):
        oordeel = "geslaagd"
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
        "f7": f7,
        "categorieen": dict(sorted(Counter(r["categorie"] for r in runs).items())),
        "grens": _GRENS,
    }
