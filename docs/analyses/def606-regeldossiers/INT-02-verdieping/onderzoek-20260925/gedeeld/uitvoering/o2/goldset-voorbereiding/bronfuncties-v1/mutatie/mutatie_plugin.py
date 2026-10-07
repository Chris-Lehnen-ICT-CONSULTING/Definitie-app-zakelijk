"""DEF-835 besluit 16 — mutatiecontrole op de beslisregel van contract /4.

Pytest-plugin. Met `--def835-mutant <naam>` (of `DEF835_MUTANT`) vervangt hij vóór het verzamelen
van de tests `domain.int02.contract` in `sys.modules` door een kopie waarin
precies één kernvoorwaarde door haar naïeve variant is vervangen. De
repository blijft ongewijzigd (alles in het geheugen). Zonder variabele doet
de plugin niets (nulmeting).

Gebruik (vanuit de werkboom):

    PYTHONPATH=<deze map> python -m pytest -p mutatie_plugin \
        --def835-mutant stap1_weg \
        tests/unit/domain/test_def835_int02_bronfuncties.py \
        tests/unit/domain/test_def835_int02_papertest.py

Elke mutant moet minstens één test laten falen; anders bewijzen de tests die
voorwaarde niet.
"""

from __future__ import annotations

import importlib
import os
import sys
import types
from pathlib import Path

#: naam -> (kernvoorwaarde, origineel fragment, naïeve variant)
MUTANTEN: dict[str, tuple[str, str, str]] = {
    "stap1_weg": (
        "Stap 1: een voorschrift in de kern is altijd gebrek",
        '    if kernvorm == "instruction":\n        grond = g[0] if g else None',
        "    if False:\n        grond = g[0] if g else None",
    ),
    "bedoeling_symmetrisch_1a": (
        "1B: de bedoeling beslecht een conflict alleen naar gebrek",
        '        if bedoeling in ("G", "N"):\n'
        '            return _Afgeleid("gebrek", REGEL_BEDOELING_BESLIST, gebrek, "bedoeling")',
        '        if bedoeling == "B":\n'
        '            return _Afgeleid("beschrijvend", REGEL_BEDOELING_BESLIST,'
        ' functie["bedoeling"], "bedoeling")\n'
        '        if bedoeling in ("G", "N"):\n'
        '            return _Afgeleid("gebrek", REGEL_BEDOELING_BESLIST, gebrek, "bedoeling")',
    ),
    "n_geen_conflict_6a": (
        "6A: not_a_criterion botst met criterion",
        "    if b and (g or n):",
        "    if b and g:",
    ),
    "tweede_signaal_altijd_3a": (
        "3A: één voorschrift-bron vraagt een tweede signaal",
        "        if tweede_signaal:",
        "        if True:",
    ),
    "n_geen_tweede_signaal_6a": (
        "6A: G én N samen tellen als tweede signaal",
        "            or (bool(g) and bool(n))\n",
        "",
    ),
    "alleen_o_zwijgt": (
        "Alleen 'unclear' is review, niet zwijgen",
        "    if o:\n        return _Afgeleid(",
        "    if False:\n        return _Afgeleid(",
    ),
    "beschrijvend_zonder_bedoeling_pass_5a": (
        "5A: beschrijvende kern, alles zwijgt, bedoeling onbekend is review",
        '(kernvorm == "descriptive_act" and not onbekend)',
        '(kernvorm == "descriptive_act")',
    ),
    "discretie_zonder_bedoeling_weg_b12": (
        "Besluit 12: afwegingsvorm zonder grond en bedoeling is review",
        '    if kernvorm == "discretion_form" and onbekend:  # besluit 12',
        "    if False:  # besluit 12",
    ),
    "dekkingseis_weg": (
        "Pass vereist volledige dekking",
        '    elif oordeel["coverage"] != "complete":',
        "    elif False:",
    ),
    "review_voor_gebrek": (
        "Gebrek gaat vóór review",
        "    if gebrek is not None:\n        p = dienst[gebrek]",
        "    if gebrek is not None and review is None:\n        p = dienst[gebrek]",
    ),
    "omzetting_nooit": (
        "2A: een afwijking van het modelverdict is zichtbaar (omzetting)",
        '        omgezet = uitvoering.actor == "ai" and uitkomst.status != modelstatus',
        "        omgezet = False",
    ),
    "modelverdict_beslist_2a": (
        "2A: de dienst beslist, niet het modelverdict",
        '    if uitvoering.actor == "human":\n        if verdict == "pass":',
        '    if True:\n        if verdict == "pass":',
    ),
    # Herstel na Codex-review: besluit 17 (07-10-2026).
    "onzekerheid_genegeerd_17": (
        "Besluit 17: beslissende modelonzekerheid blokkeert een afgeleide pass",
        '    if oordeel["uncertainty"] == "decisive":  # besluit 17',
        "    if False:  # besluit 17",
    ),
    # Herstel na herreview Codex: P1-rest (07-10-2026). Naïef = terug naar
    # de witruimtetoets van `_gevuld`.
    # Na herreview 2 (08-10-2026): fragment aangepast aan de nieuwe helper.
    "betekenisdragend_weg_p1rest": (
        "P1-rest: alleen tekst met een zichtbare letter draagt een oordeel",
        "    return isinstance(waarde, str) and any(map(_zichtbare_letter, waarde))",
        "    return isinstance(waarde, str) and bool(waarde.strip())",
    ),
    "passagecitaat_ongetoetst_p1rest": (
        "P1-rest: een passagecitaat zonder zichtbare letter is leeg",
        '        _citaat(_betekenisdragend(passage["quote"]), CITAAT_LEEG)\n',
        "",
    ),
    "inhoudsloze_bedoeling_bekend_p1rest": (
        "P1-rest: een bedoeling zonder zichtbare letter geldt in stap 4 als onbekend",
        "    onbekend = not _betekenisdragend(invoer.bedoeling)",
        "    onbekend = invoer.bedoeling is None",
    ),
    # Herstel na herreview 2 (08-10-2026): P1-rest 2.
    "isalnum_p1rest2": (
        "P1-rest 2: letter (L*) zonder onzichtbare letters; cijfers tellen niet",
        "    return isinstance(waarde, str) and any(map(_zichtbare_letter, waarde))",
        "    return isinstance(waarde, str) and any(t.isalnum() for t in waarde)",
    ),
    "onzichtbaar_vergeten_p1rest2": (
        "P1-rest 2: onzichtbare letters (fillers, blanco) tonen geen betekenis",
        'startswith("L") and teken not in ONZICHTBARE_LETTERS',
        'startswith("L")',
    ),
}


def _mutant(config) -> str | None:
    return config.getoption("def835_mutant") or os.environ.get("DEF835_MUTANT")


def pytest_addoption(parser) -> None:
    parser.addoption(
        "--def835-mutant",
        dest="def835_mutant",
        default=None,
        choices=sorted(MUTANTEN),
        help="DEF-835: vervang één kernvoorwaarde door haar naïeve variant",
    )


def pytest_configure(config) -> None:
    naam = _mutant(config)
    if not naam:
        return
    _, origineel, variant = MUTANTEN[naam]
    pakket = importlib.import_module("domain.int02")
    pad = Path(pakket.__file__).parent / "contract.py"
    bron = pad.read_text("utf-8")
    aantal = bron.count(origineel)
    if aantal != 1:
        msg = f"mutant {naam}: fragment {aantal}x gevonden (verwacht 1)"
        raise RuntimeError(msg)
    module = types.ModuleType("domain.int02.contract")
    module.__file__ = str(pad)
    sys.modules["domain.int02.contract"] = module
    pakket.contract = module
    exec(compile(bron.replace(origineel, variant), str(pad), "exec"), module.__dict__)
    config.addinivalue_line("markers", f"def835_mutant_{naam}: actieve mutant")


def pytest_report_header(config) -> str:
    naam = _mutant(config)
    if not naam:
        return "DEF835-mutant: geen (nulmeting)"
    return f"DEF835-mutant: {naam} — {MUTANTEN[naam][0]}"
