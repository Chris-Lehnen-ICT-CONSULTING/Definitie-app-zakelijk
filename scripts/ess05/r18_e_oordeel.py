"""DEF-768 R18A — het voorwaardeoordeel van Chris bij casus E (aanvulling v4).

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

De runs komen uit de callrecords van de fase (`<uitmap>/interpretatie-*/calls`),
alleen de geregistreerde (met `acceptatie`); de sha256 van elke ruwe
modeluitvoer wordt opnieuw berekend en moet met het record overeenkomen.

    .venv/bin/python scripts/ess05/r18_e_oordeel.py blad --calls DIR [DIR ...] --doel BLAD.md
    .venv/bin/python scripts/ess05/r18_e_oordeel.py eindoordeel --calls DIR [DIR ...] \\
        --oordeel OORDEEL.json --doel EINDOORDEEL.json

Een doel wordt nooit overschreven; geen netwerk, geen modelaanroep.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bewijsscorer as bs

__all__ = ["beoordelingsblad", "lees_runs", "main"]

CALLSCHEMA = "def768-ess05-interpretatiecall/1"
_GEEN_UITVOER = "Geen gescoorde uitvoer: geen oordeel nodig; telt als niet behouden."


def _sha(tekst: str) -> str:
    return hashlib.sha256(tekst.encode("utf-8")).hexdigest()


def _lees_records(callmappen: Sequence[Path]) -> list[tuple[Path, dict[str, Any]]]:
    """(pad, record) van elke geregistreerde interpretatierun, op volgnummer."""
    records: list[tuple[Path, dict[str, Any]]] = []
    for map_ in callmappen:
        for pad in sorted(Path(map_).glob("*.json")):
            record = json.loads(pad.read_text(encoding="utf-8"))
            if (
                record.get("schema") != CALLSCHEMA
                or record.get("fase") != "interpretatie"
            ):
                msg = f"{pad}: geen interpretatie-callrecord ({CALLSCHEMA})"
                raise bs.OordeelfoutError(msg)
            for stap in record.get("reserveringen") or []:
                tekst = stap.get("ruw_antwoord")
                if isinstance(tekst, str) and _sha(tekst) != stap.get(
                    "ruw_antwoord_sha256"
                ):
                    msg = f"{pad}: ruw_antwoord_sha256 klopt niet met de ruwe uitvoer"
                    raise bs.OordeelfoutError(msg)
            if record.get("acceptatie") is not None:
                records.append((pad, record))
    if not records:
        raise bs.OordeelfoutError(f"geen callrecords in {[str(m) for m in callmappen]}")
    gezien: set[str] = set()
    for pad, record in records:
        if record["sleutel"] in gezien:
            raise bs.OordeelfoutError(f"{pad}: dubbele run {record['sleutel']!r}")
        gezien.add(record["sleutel"])
    return sorted(records, key=lambda pr: (pr[1]["seq"] is None, pr[1]["seq"] or 0))


def _e_uitvoer(record: Mapping[str, Any]) -> str | None:
    """De beoordeelde E-uitvoer (ruwe modeltekst), alleen bij een gescoorde E-run."""
    if record["runoordeel"]["voorwaarde_behouden"] is None or record["score"] is None:
        return None
    stappen = record.get("reserveringen") or []
    tekst = stappen[0].get("ruw_antwoord") if stappen else None
    return tekst if isinstance(tekst, str) else None


def _runs(records: Sequence[tuple[Path, Mapping[str, Any]]]) -> list[dict[str, Any]]:
    runs = []
    for _, record in records:
        tekst = _e_uitvoer(record)
        runs.append(
            {
                "sleutel": record["sleutel"],
                **record["runoordeel"],
                "e_uitvoer_sha256": _sha(tekst) if tekst is not None else None,
            }
        )
    return runs


def lees_runs(callmappen: Sequence[Path]) -> list[dict[str, Any]]:
    """Elke geregistreerde run: `runoordeel`, `sleutel` en voor E `e_uitvoer_sha256`."""
    return _runs(_lees_records(callmappen))


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


def _e_sectie(pad: Path, record: Mapping[str, Any]) -> list[str]:
    run = record["runoordeel"]
    md = (record["score"] or {}).get("m_d") or {}
    dienst = record.get("dienstuitkomst") or {}
    tekst = _e_uitvoer(record)
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


def beoordelingsblad(callmappen: Sequence[Path]) -> str:
    """Het beoordelingsblad (markdown) voor de E-runs van deze callmappen."""
    records = _lees_records(callmappen)
    e_records = [
        (p, r) for p, r in records if r["runoordeel"]["voorwaarde_behouden"] is not None
    ]
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
    for pad, record in e_records:
        regels.extend(_e_sectie(pad, record))
    regels += [
        "## Oordeelbestand (sjabloon)",
        "",
        (
            "Vul per run `status` (behouden, ontkend of weggevallen), `beoordelaar` "
            "en `datum` (JJJJ-MM-DD) in; laat `run` en `e_uitvoer_sha256` ongewijzigd."
        ),
        "",
        "```json",
        json.dumps(_sjabloon(_runs(records)), ensure_ascii=False, indent=2),
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
        s.add_argument("--doel", type=Path, required=True)
    eind.add_argument("--oordeel", type=Path, required=True)
    args = p.parse_args(argv)
    if args.doel.exists():
        msg = f"doel bestaat al: {args.doel}"
        raise FileExistsError(msg)
    if args.opdracht == "blad":
        tekst = beoordelingsblad(args.calls)
    else:
        oordelen = json.loads(args.oordeel.read_text(encoding="utf-8"))
        uit = bs.eindoordeel(lees_runs(args.calls), oordelen)
        uit["oordeelbestand_sha256"] = _sha(args.oordeel.read_text(encoding="utf-8"))
        tekst = json.dumps(uit, ensure_ascii=False, indent=2) + "\n"
    _schrijf(args.doel, tekst)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
