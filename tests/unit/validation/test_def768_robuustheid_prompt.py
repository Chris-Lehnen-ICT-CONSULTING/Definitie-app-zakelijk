"""DEF-768 robuustheidsronde, punt 3a — interpretatieprompt `/5` (tekstcontrole).

Besluit Chris 29-09: buiten_kern alleen uit de bedoelde betekenis of bronnen van
het doelbegrip; zonder die bronnen leeg; nooit kenmerken uit de beschrijving van
een verwant begrip of uit eigen kennis. Bewijst niets over modelgedrag; het
vangnet in code (bewijsregels /7) doet dat wel voor de gevolgen.
"""

from __future__ import annotations

import pytest

from services.validation import ess05_bewijsregel_service as bs

pytestmark = [pytest.mark.unit]


def test_versies_prompt_5_en_bewijsregels_7():
    identiteit = bs.Ess05BewijsregelService.contractidentiteit()
    assert identiteit["interpretation_prompt_version"] == "ess05-interpretatie-prompt/5"
    assert identiteit["bewijsregel_version"] == "ess05-bewijsregels/7"
    assert identiteit["interpretation_schema_version"] == "ess05-interpretatie/3"
    assert identiteit["render_version"] == "ess05-bewijsregels-render/2"


def test_buiten_kern_alleen_uit_doelbetekenis_of_bron():
    system = bs.interpretatiesysteemprompt()
    assert (
        "2. buiten_kern: alleen kenmerken die de bedoelde betekenis of een bron van "
        "het doelbegrip aan het begrip toekent en die de definitie niet uitdrukt, "
        "ook niet anders geformuleerd."
    ) in system
    assert (
        "Is er geen bedoelde betekenis en geen bron van het doelbegrip, dan is "
        "buiten_kern leeg."
    ) in system
    assert (
        "Neem nooit kenmerken over uit de beschrijving van een verwant begrip of "
        "uit eigen kennis."
    ) in system


def test_oude_formulering_is_weg():
    system = bs.interpretatiesysteemprompt()
    assert (
        "volgens de bedoelde betekenis of een bron bij het begrip horen" not in system
    )


def test_systeemprompthash_hoort_bij_de_nieuwe_prompt():
    identiteit = bs.Ess05BewijsregelService.contractidentiteit()
    assert identiteit["interpretation_system_prompt_sha256"] != (
        "a18e2e07978cfb1abf25cef1faa518c45c516ac268e8c8f8048572eb52acd465"
    )
