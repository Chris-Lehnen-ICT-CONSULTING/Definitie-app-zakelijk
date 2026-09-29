"""Q1 (DEF-835): in-memory mutatiecontrole, v3 (anker na Black; v2 ongebruikt).

Pytest-plugin: na collectie wordt de al geladen runnermodule opnieuw
uitgevoerd met één tekstmutatie in haar eigen namespace. Het bronbestand
in de repository wordt niet gewijzigd. Gebruik:

    Q1_MUTATIE=<naam> python -m pytest <testbestand> -p q1_mutatie ...

met deze map op PYTHONPATH (bestandsnaam dan als module q1_mutatie).
"""

import os
import sys
from pathlib import Path

MUTATIES = {
    # Tokenmeting zonder duurzame reservering vooraf.
    "geen_telreservering": (
        "self._registreer(\n"
        '            {"gebeurtenis": "tel_reservering", "tel": self.telverzoeken + 1}\n'
        "        )",
        "pass",
    ),
    # Nieuwe run begint weer bij nul (administratie reset).
    "stand_niet_overnemen": (
        '        self.inferenties = stand["inferenties"]\n'
        '        self.telverzoeken = stand["telverzoeken"]\n'
        '        self.besteed_usd = stand["besteed_usd"]',
        "        return",
    ),
    # Kritieke false-pass stopt de fase niet.
    "geen_false_pass_stop": (
        'if stopreden is None and evaluatie["kritieke_false_pass"]:',
        "if False:",
    ),
    # Fasevolgorde niet afgedwongen.
    "geen_fasevolgorde": (
        'if any(stand["fasen"].get(v) is not True for v in FASEN[: FASEN.index(fase)]):',
        "if False:",
    ),
    # Geen cumulatieve ruimtecontrole vóór de fase.
    "geen_ruimtecontrole": (
        '    """Resterende calls, budget en looptijd dekken de hele fase vooraf."""\n',
        '    """Resterende calls, budget en looptijd dekken de hele fase vooraf."""\n'
        "    return\n",
    ),
    # Labels niet in de identiteit.
    "label_niet_in_identiteit": (
        '"label_sha256": hash_json(g.label),',
        '"label_sha256": None,',
    ),
    # Testfixture mag echt live.
    "testfixture_live": (
        'if binnen is None and identiteit["gevallenmanifest"]["technische_testfixture"]:',
        "if False:",
    ),
    # Hold-out-minima per label genegeerd.
    "geen_labelminima": (
        'for status, minimum in criteria["min_juist_per_label"].items():',
        "for status, minimum in {}.items():",
    ),
    # Onzekere call gratis in plaats van volle reservering.
    "onzekere_call_gratis": (
        "b if (b := kosten.get(c)) is not None else r",
        "b if (b := kosten.get(c)) is not None else 0.0",
    ),
    # Oud driecallakkoordtype toegestaan.
    "oud_akkoordtype": (
        'and akkoord["soort"] == KWALIFICATIE_AKKOORD_SOORT',
        'and akkoord["soort"] in (KWALIFICATIE_AKKOORD_SOORT, AKKOORD_SOORT)',
    ),
    # Freeze niet vereist.
    "freeze_niet_vereist": (
        'if not _bevroren(data.get("freeze")):',
        "if False:",
    ),
}


def pytest_collection_finish(session):
    naam = os.environ["Q1_MUTATIE"]
    module = sys.modules["def835_int02_modelproef"]
    bron = Path(module.__file__).read_text("utf-8")
    oud, nieuw = MUTATIES[naam]
    assert bron.count(oud) == 1, f"mutatie {naam}: ankertekst niet uniek"
    exec(compile(bron.replace(oud, nieuw), module.__file__, "exec"), module.__dict__)
