"""DEF-768 R18A — het voorwaardeoordeel van Chris bij casus E (aanvulling v4/v5).

Besluit optie 2 (Codex-hercontrole v3): de scorer beoordeelt de voorwaarde bij
E nooit automatisch. Na de proef beoordeelt Chris elke gescoorde E-run:

1. `blad`: een beoordelingsblad (markdown) met per E-run de volledige
   modeluitvoer (antwoorden met voorwaarden en bewijseenheden, kern, buiten
   de kern, buiten bereik), de bron met eenheden, de deterministische
   uitkomst en de sha256 van de beoordeelde uitvoer; onderaan een sjabloon
   voor het oordeelbestand. Geen lexicale signalen of voorlopige status.
2. Chris vult het oordeelbestand (JSON, `bewijsscorer.E_OORDEELSCHEMA`): per
   E-run `run`, `e_uitvoer_sha256`, `status` (behouden/ontkend/weggevallen),
   `beoordelaar`, `datum`.
3. `eindoordeel`: `bewijsscorer.eindoordeel` over de runs uit de callrecords
   plus het oordeelbestand; weigert ontbrekende, dubbele, onbekende of
   hash-afwijkende oordelen (`OordeelfoutError`) en schrijft dan niets.

Aanvulling v5 (Codex-hercontrole v4, B5/B6): de runs worden niet uit de
opgeslagen metadata overgenomen. De invoer moet de gepinde R18A-invoer zijn
(`run_ess05_proef.R18_I_INVOER_SHA256`) met precies A/C/D/E × 3; E is het item
met de voorwaarde in die invoer. Elk geregistreerd callrecord (met
`acceptatie`) moet bij zijn casus passen (fase, item_id, herhaling, sleutel,
invoerhash, gevalhash, prompt, orakel, reservering) en de sha256 van zijn ruwe
uitvoer; score en runoordeel worden met de huidige scorer uit die gehashte
tekst herberekend en moeten gelijk zijn aan wat is opgeslagen. Elke afwijking,
een dubbele run of reservering en een onvolledige proef (`controleer_runs`)
geven `OordeelfoutError`.

    .venv/bin/python scripts/ess05/r18_e_oordeel.py blad --calls DIR [DIR ...] \\
        [--invoer INVOER.json] --doel BLAD.md
    .venv/bin/python scripts/ess05/r18_e_oordeel.py eindoordeel --calls DIR [DIR ...] \\
        [--invoer INVOER.json] --oordeel OORDEEL.json --doel EINDOORDEEL.json

Standaardinvoer: `bewijsregel-invoer-v5.json`. Een doel wordt nooit
overschreven; geen netwerk, geen modelaanroep.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bewijsscorer as bs
import maak_r18_bewijsregel_invoer as mk18
import run_ess05_proef as runner

from services.validation.ai_beoordeling_transport import parse_modeluitvoer
from services.validation.ess05_bewijsregel_service import (
    _ontsnap,
    bouw_interpretatieprompt,
)
from services.validation.ess05_verification_service import prompthash

__all__ = ["INVOER", "beoordelingsblad", "lees_runs", "main"]

CALLSCHEMA = "def768-ess05-interpretatiecall/1"
#: De R18A-invoer die de runner pint (`R18_I_INVOER_SHA256`).
INVOER = mk18.DOEL
_GEEN_UITVOER = "Geen gescoorde uitvoer: geen oordeel nodig; telt als niet behouden."


def _sha(tekst: str) -> str:
    return hashlib.sha256(tekst.encode("utf-8")).hexdigest()


def _json(waarde: Any) -> Any:
    """Vergelijkbare vorm (tuples als lijsten), zoals het callrecord hem opslaat."""
    return json.loads(json.dumps(waarde, ensure_ascii=False))


@dataclass(frozen=True)
class _Casus:
    """Eén item van de gepinde invoer: gevalinhoud, orakel en prompt."""

    item: Mapping[str, Any]
    vergelijking: Any
    prompt: tuple[str, str]
    is_e: bool


@dataclass(frozen=True)
class _Run:
    """Een gecontroleerd callrecord met het herberekende runoordeel."""

    pad: Path
    record: Mapping[str, Any]
    run: dict[str, Any]
    tekst: str | None


def _fout(msg: str) -> bs.OordeelfoutError:
    return bs.OordeelfoutError(msg)


def _lees_invoer(pad: Path) -> dict[str, _Casus]:
    """De gepinde R18A-invoer: hash, schema, proefstructuur en binding aan de code."""
    data_bytes = Path(pad).read_bytes()
    sha = hashlib.sha256(data_bytes).hexdigest()
    if sha != runner.R18_I_INVOER_SHA256:
        msg = (
            f"{pad}: sha256 {sha} is niet de gepinde R18A-invoer "
            f"({runner.R18_I_INVOER_SHA256})"
        )
        raise _fout(msg)
    data = json.loads(data_bytes)
    items = data.get("items") if isinstance(data, Mapping) else None
    if data.get("schema") != mk18.INVOERSCHEMA or not isinstance(items, list):
        raise _fout(f"{pad}: geen R18A-invoer met schema {mk18.INVOERSCHEMA}")
    if not all(isinstance(i, Mapping) and isinstance(i.get("orakel"), Mapping)
               for i in items):  # fmt: skip
        raise _fout(f"{pad}: items zonder orakel")
    ids = [i.get("id") for i in items]
    e_ids = [i["id"] for i in items if "voorwaarde" in i["orakel"]]
    if (
        sorted(map(str, ids)) != sorted(bs.PROEFITEMS)
        or len(set(ids)) != len(ids)
        or e_ids != [bs.E_ITEM]
        or any(i.get("herhalingen") != bs.HERHALINGEN for i in items)
    ):
        msg = (
            f"{pad}: invoer past niet op de proefstructuur (items {ids}, "
            f"E-casus {e_ids}; verwacht {list(bs.PROEFITEMS)} × {bs.HERHALINGEN}, "
            f"E = {bs.E_ITEM})"
        )
        raise _fout(msg)
    casussen = {}
    for item in items:
        vergelijking = mk18.vergelijkingsinvoer(item)
        prompt = bouw_interpretatieprompt(vergelijking)
        if prompthash(*prompt) != item.get("prompt_sha256"):
            raise _fout(f"{pad}: {item['id']}: prompt_sha256 past niet op de prompt")
        try:
            bs.controleer_orakel(item["orakel"], vergelijking)
        except bs.OrakelfoutError as exc:
            raise _fout(f"{pad}: {item['id']}: {exc}") from exc
        casussen[item["id"]] = _Casus(
            item, vergelijking, prompt, item["id"] == bs.E_ITEM
        )
    return casussen


def _controleer_record(
    pad: Path, record: Mapping[str, Any], casus: _Casus
) -> str | None:
    """Het record past bij zijn casus en de gepinde invoer; geeft de ruwe tekst."""
    sleutel, herhaling = record.get("sleutel"), record.get("herhaling")
    item = casus.item
    if (
        isinstance(herhaling, bool)
        or not isinstance(herhaling, int)
        or not 1 <= herhaling <= bs.HERHALINGEN
    ):
        raise _fout(f"{pad}: herhaling {herhaling!r} ligt niet in 1–{bs.HERHALINGEN}")
    if sleutel != f"interpretatie|{item['id']}|{herhaling}":
        msg = f"{pad}: sleutel {sleutel!r} past niet bij item_id {item['id']!r} en herhaling {herhaling}"
        raise _fout(msg)
    if record.get("invoerbestand_sha256") != runner.R18_I_INVOER_SHA256:
        raise _fout(f"{pad}: invoerbestand_sha256 is niet de gepinde R18A-invoer")
    if record.get("geval_sha256") != item["geval_sha256"]:
        raise _fout(f"{pad}: geval_sha256 past niet bij item {item['id']}")
    prompt = record.get("prompt")
    if not isinstance(prompt, Mapping) or (
        (prompt.get("system"), prompt.get("user"), prompt.get("sha256"))
        != (*casus.prompt, item["prompt_sha256"])
    ):
        raise _fout(f"{pad}: prompt past niet bij item {item['id']}")
    if _json(record.get("orakel")) != _json(item["orakel"]):
        raise _fout(f"{pad}: orakel past niet bij item {item['id']}")
    stappen = record.get("reserveringen")
    if not (isinstance(stappen, list) and len(stappen) == 1
            and isinstance(stappen[0], Mapping)):  # fmt: skip
        raise _fout(f"{pad}: niet precies één reservering")
    stap = stappen[0]
    if (stap.get("seq"), stap.get("poging")) != (record.get("seq"), sleutel):
        raise _fout(f"{pad}: reservering (seq, poging) past niet bij het record")
    tekst = stap.get("ruw_antwoord")
    if tekst is not None and (
        not isinstance(tekst, str) or _sha(tekst) != stap.get("ruw_antwoord_sha256")
    ):
        raise _fout(f"{pad}: ruw_antwoord_sha256 klopt niet met de ruwe uitvoer")
    return tekst


def _herbereken(
    pad: Path, record: Mapping[str, Any], casus: _Casus, tekst: str | None
) -> dict[str, Any]:
    """Score en runoordeel opnieuw uit de gehashte ruwe tekst, zoals de runner
    (`_i_score`: alleen als de dienst de uitvoer parste); wijkt het opgeslagen
    af, dan is de metadata strijdig."""
    registratie = record.get("interpretatie")
    if isinstance(registratie, Mapping) and "ruw_antwoord" in registratie:
        if registratie["ruw_antwoord"] != tekst:
            msg = f"{pad}: strijdige metadata: interpretatie.ruw_antwoord is niet de gehashte tekst"
            raise _fout(msg)
    score = None
    if isinstance(registratie, Mapping) and "ruw" in registratie:
        geparsed = parse_modeluitvoer(tekst)
        if geparsed is None or _json(geparsed) != _json(registratie["ruw"]):
            msg = f"{pad}: strijdige metadata: interpretatie.ruw is niet de geparste ruwe uitvoer"
            raise _fout(msg)
        try:
            score = bs.scoor(
                _ontsnap(geparsed), casus.vergelijking, casus.item["orakel"]
            )
        except Exception:  # zoals de runner: een scorerfout is geen score
            score = None
    oordeel = bs.runoordeel(score, casus.item["orakel"])
    if _json(record.get("score")) != _json(score) or _json(
        record.get("runoordeel")
    ) != _json(oordeel):
        msg = (
            f"{pad}: strijdige metadata: opgeslagen score of runoordeel wijkt af "
            "van de herberekening uit de ruwe uitvoer"
        )
        raise _fout(msg)
    return {
        "sleutel": record["sleutel"],
        **oordeel,
        "e_uitvoer_sha256": (
            _sha(tekst)
            if casus.is_e and score is not None and tekst is not None
            else None
        ),
    }


def _uniek(
    records: Sequence[tuple[Path, Mapping[str, Any]]], veld: str, wat: str
) -> None:
    telling = Counter(r.get(veld) for _, r in records if r.get(veld) is not None)
    dubbel = sorted(str(w) for w, n in telling.items() if n > 1)
    if dubbel:
        raise _fout(f"{wat} ({veld} {dubbel})")


def _lees(callmappen: Sequence[Path], invoer: Path) -> list[_Run]:
    """Elke geregistreerde run, gecontroleerd en herberekend, op volgnummer;
    daarna moet de verzameling precies de proef zijn (`controleer_runs`)."""
    casussen = _lees_invoer(invoer)
    records: list[tuple[Path, Mapping[str, Any]]] = []
    for map_ in callmappen:
        for pad in sorted(Path(map_).glob("*.json")):
            record = json.loads(pad.read_text(encoding="utf-8"))
            if (
                not isinstance(record, Mapping)
                or record.get("schema") != CALLSCHEMA
                or record.get("fase") != "interpretatie"
            ):
                msg = f"{pad}: geen interpretatie-callrecord ({CALLSCHEMA})"
                raise _fout(msg)
            if record.get("acceptatie") is not None:
                records.append((pad, record))
    if not records:
        raise _fout(f"geen callrecords in {[str(m) for m in callmappen]}")
    _uniek(records, "sleutel", "dubbele run")
    _uniek(records, "seq", "dubbele reservering")
    runs = []
    for pad, record in sorted(records, key=lambda pr: pr[1].get("seq") or 0):
        casus = casussen.get(record.get("item_id"))
        if casus is None:
            raise _fout(f"{pad}: onbekende item_id {record.get('item_id')!r}")
        tekst = _controleer_record(pad, record, casus)
        runs.append(_Run(pad, record, _herbereken(pad, record, casus, tekst), tekst))
    bs.controleer_runs([r.run for r in runs])
    return runs


def lees_runs(
    callmappen: Sequence[Path], invoer: Path = INVOER
) -> list[dict[str, Any]]:
    """Elke run van de proef, herberekend: `runoordeel`, `sleutel` en voor E
    `e_uitvoer_sha256`; weigert zoals `_lees`."""
    return [r.run for r in _lees(callmappen, invoer)]


# --- beoordelingsblad -----------------------------------------------------------------------


def _cel(tekst: str) -> str:
    return " ".join(tekst.split()).replace("|", "\\|")


def _eenheden(prompt: str) -> dict[str, str]:
    return dict(re.findall(r"^\[([^\]\s]+)\] (.+)$", prompt, re.M))


def _antwoordtabel(ruw: Any, eenheden: Mapping[str, str]) -> list[str]:
    regels = [
        "| kenmerk | onderwerp | toestand | voorwaarden | bewijseenheden |",
        "|---|---|---|---|---|",
    ]
    antwoorden = ruw.get("antwoorden") if isinstance(ruw, Mapping) else None
    for a in antwoorden if isinstance(antwoorden, list) else []:
        if not isinstance(a, Mapping):
            regels.append(f"| {_cel(json.dumps(a, ensure_ascii=False))} | | | | |")
            continue
        voorwaarden = a.get("voorwaarden")
        citaten = a.get("citaten")
        cellen = [
            str(a.get("kenmerk_id")),
            str(a.get("onderwerp")),
            str(a.get("toestand")),
            (
                "; ".join(map(str, voorwaarden))
                if isinstance(voorwaarden, list)
                else json.dumps(voorwaarden, ensure_ascii=False)
            ),
            (
                "<br>".join(
                    f"{u}: {eenheden.get(u, '(niet in de prompt)')}"
                    for u in map(str, citaten)
                )
                if isinstance(citaten, list)
                else json.dumps(citaten, ensure_ascii=False)
            ),
        ]
        regels.append("| " + " | ".join(_cel(c) for c in cellen) + " |")
    return regels


def _e_sectie(r: _Run) -> list[str]:
    pad, record, run = r.pad, r.record, r.run
    md = (record["score"] or {}).get("m_d") or {}
    dienst = record.get("dienstuitkomst") or {}
    tekst = r.tekst if run["e_uitvoer_sha256"] else None
    regels = [
        f"## {record['sleutel']}",
        "",
        f"- Callrecord: `{pad.parent.parent.name}/{pad.parent.name}/{pad.name}`",
        f"- E-uitvoer sha256: `{_sha(tekst) if tekst is not None else '—'}`",
        (
            f"- Deterministische uitkomst (`bepaal`): `{run['gekregen']}`; dienst: "
            f"`{dienst.get('uitkomst')}/{dienst.get('fout')}`; juist volgens het "
            f"orakel: `{', '.join(md.get('verwacht') or record['orakel']['uitkomst'])}`"
        ),
        f"- Automatische categorie: `{run['categorie']}`"
        + (
            " (wacht op het oordeel)"
            if run["categorie"] == "handmatig_beoordelen"
            else " (blijft niet geslaagd, ook bij 'behouden')"
        ),
        f"- Voorwaarde in de bron: \"{record['orakel'].get('voorwaarde')}\"",
        "",
    ]
    if tekst is None:
        return [*regels, _GEEN_UITVOER, ""]
    try:
        ruw = json.loads(tekst)
    except ValueError:
        ruw = None
    eenheden = _eenheden(record["prompt"]["user"])
    buiten = {
        k: ruw.get(k)
        for k in ("kern", "buiten_kern", "buurgroepen", "buiten_bereik")
        if isinstance(ruw, Mapping)
    }
    return [
        *regels,
        "### Antwoorden (voorwaarden en bewijseenheden)",
        "",
        *_antwoordtabel(ruw, eenheden),
        "",
        "### Kern, buiten de kern, buurgroepen en buiten bereik",
        "",
        "```text",
        json.dumps(buiten, ensure_ascii=False, indent=2),
        "```",
        "",
        "### Bron met eenheden (interpretatieprompt)",
        "",
        "```text",
        record["prompt"]["user"],
        "```",
        "",
        "### Volledige modeluitvoer (ruw; dit is de gehashte tekst)",
        "",
        "```text",
        tekst,
        "```",
        "",
    ]


def _sjabloon(runs: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    return {
        "schema": bs.E_OORDEELSCHEMA,
        "oordelen": [
            {
                "run": r["sleutel"],
                "e_uitvoer_sha256": r["e_uitvoer_sha256"],
                "status": "",
                "beoordelaar": "",
                "datum": "",
            }
            for r in runs
            if r["e_uitvoer_sha256"]
        ],
    }


def beoordelingsblad(callmappen: Sequence[Path], invoer: Path = INVOER) -> str:
    """Het beoordelingsblad (markdown) voor de E-runs van deze callmappen; weigert
    zoals `lees_runs` (alleen een volledige, consistente proef)."""
    records = _lees(callmappen, invoer)
    e_records = [r for r in records if r.run["sleutel"] in bs.E_SLEUTELS]
    regels = [
        "# R18A — beoordelingsblad casus E (voorwaardeoordeel van Chris)",
        "",
        (
            "Aanvulling v4 (besluit optie 2): de scorer beoordeelt de voorwaarde bij "
            "E niet. Beoordeel per E-run hieronder of de voorwaarde uit de bron in de "
            "interpretatie behouden is, met één status: `behouden`, `ontkend` of "
            "`weggevallen`. Vul daarna het sjabloon onderaan in en bereken het "
            "eindoordeel met `scripts/ess05/r18_e_oordeel.py eindoordeel`."
        ),
        "",
        f"Beslisregel: {bs.EINDREGEL}.",
        "",
        f"Runs in de callrecords: {len(records)}; E-runs: {len(e_records)}.",
        "",
    ]
    for r in e_records:
        regels.extend(_e_sectie(r))
    regels += [
        "## Oordeelbestand (sjabloon)",
        "",
        (
            "Vul per run `status` (behouden, ontkend of weggevallen), `beoordelaar` "
            "en `datum` (JJJJ-MM-DD) in; laat `run` en `e_uitvoer_sha256` ongewijzigd."
        ),
        "",
        "```json",
        json.dumps(_sjabloon([r.run for r in records]), ensure_ascii=False, indent=2),
        "```",
        "",
    ]
    return "\n".join(regels)


# --- CLI ------------------------------------------------------------------------------------


def _schrijf(doel: Path, tekst: str) -> None:
    doel.parent.mkdir(parents=True, exist_ok=True)
    with doel.open("x", encoding="utf-8") as f:
        f.write(tekst)
    sys.stdout.write(f"{doel} sha256={_sha(tekst)}\n")


def main(argv: Sequence[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="opdracht", required=True)
    blad = sub.add_parser("blad", help="schrijf het beoordelingsblad")
    eind = sub.add_parser("eindoordeel", help="proefoordeel plus het oordeel van Chris")
    for s in (blad, eind):
        s.add_argument("--calls", type=Path, nargs="+", required=True)
        s.add_argument("--invoer", type=Path, default=INVOER)
        s.add_argument("--doel", type=Path, required=True)
    eind.add_argument("--oordeel", type=Path, required=True)
    args = p.parse_args(argv)
    if args.doel.exists():
        msg = f"doel bestaat al: {args.doel}"
        raise FileExistsError(msg)
    if args.opdracht == "blad":
        tekst = beoordelingsblad(args.calls, args.invoer)
    else:
        runs = lees_runs(args.calls, args.invoer)
        oordelen = json.loads(args.oordeel.read_text(encoding="utf-8"))
        uit = bs.eindoordeel(runs, oordelen)
        uit["invoerbestand_sha256"] = runner.R18_I_INVOER_SHA256
        uit["oordeelbestand_sha256"] = _sha(args.oordeel.read_text(encoding="utf-8"))
        tekst = json.dumps(uit, ensure_ascii=False, indent=2) + "\n"
    _schrijf(args.doel, tekst)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
