"""DEF-676: elke contractinvariant heeft een schendende testcase.

`_eis_consistente_klasse` en `_eis_voorbeeldpaarbeleid` bewaken samen zeven
invarianten. De bestaande contracttests itereren over de échte 53 records,
die per definitie voldoen — een kapotte invariant zou daar niet opvallen.
Deze suite voedt `build_rule_record` juist een record dat er precies één
schendt, en eist per geval de bijbehorende foutmelding.

De assertie matcht op een uniek fragment van elke melding, niet alleen op
het type. Zonder dat zou een tweede invariant die toevallig meevuurt de
test groen houden terwijl de bedoelde regel stuk is.
"""

from __future__ import annotations

import copy
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from toetsregels.runtime_contract import (
    RuleContractError,
    build_rule_record,
    root_contract_policy,
)

pytestmark = [pytest.mark.unit]

_ECHTE_REGELS_DIR = (
    Path(__file__).resolve().parents[3] / "src" / "toetsregels" / "regels"
)

# CON-02 is een gewone declaratieve regel: deterministic, automated, scored,
# met een goed/fout-paar en een normatieve policy. Daarmee zit hij precies
# aan de goede kant van alle zeven invarianten, zodat elke mutatie hieronder
# er exact één schendt.
PROEFREGEL = "CON-02"


@pytest.fixture
def basisrecord() -> dict[str, Any]:
    pad = _ECHTE_REGELS_DIR / f"{PROEFREGEL}.json"
    return json.loads(pad.read_text(encoding="utf-8"))


def _bouw(data: dict[str, Any]):
    return build_rule_record(PROEFREGEL, data, root_contract_policy())


def test_ongemuteerd_basisrecord_bouwt_zonder_fout(basisrecord):
    """Zonder dit anker bewijst geen enkele mutatietest iets.

    Bouwde het basisrecord al niet, dan zou elke `pytest.raises` hieronder
    slagen op een fout die niets met de mutatie te maken heeft.
    """
    record = _bouw(basisrecord)

    assert record.rule_id == PROEFREGEL
    assert record.has_example_pair is True


# --- de zeven schendingen --------------------------------------------------


def _zet_contract(veld: str, waarde: Any) -> Callable[[dict[str, Any]], None]:
    def muteer(data: dict[str, Any]) -> None:
        data["runtime_contract"][veld] = waarde

    return muteer


def _verwijder_contract(veld: str) -> Callable[[dict[str, Any]], None]:
    def muteer(data: dict[str, Any]) -> None:
        data["runtime_contract"].pop(veld, None)

    return muteer


def _leeg_foute_voorbeelden(data: dict[str, Any]) -> None:
    data["foute_voorbeelden"] = []


def _review_policy_zonder_reden(data: dict[str, Any]) -> None:
    data["runtime_contract"]["example_pair_policy"] = "review_policy"
    data["runtime_contract"].pop("example_pair_reason", None)
    data["runtime_contract"]["example_pair_issue"] = "DEF-624"


def _review_policy_zonder_issue(data: dict[str, Any]) -> None:
    data["runtime_contract"]["example_pair_policy"] = "review_policy"
    data["runtime_contract"]["example_pair_reason"] = "onderbouwing voor de test"
    data["runtime_contract"]["example_pair_issue"] = "ALG-1"


SCHENDINGEN = [
    pytest.param(
        _zet_contract("executability", "not_automatable"),
        "kan niet tegelijk",
        id="1-not_automatable-en-automated",
    ),
    pytest.param(
        _zet_contract("executability", "repository"),
        "definition_repository",
        id="2-repository-zonder-repository-invoer",
    ),
    pytest.param(
        _zet_contract("automation_status", "review_required"),
        "mag de score niet raken",
        id="3-niet-automated-maar-scored",
    ),
    pytest.param(
        _leeg_foute_voorbeelden,
        "gezet terwijl het record",
        id="4-policy-zonder-voorbeeldpaar",
    ),
    pytest.param(
        _verwijder_contract("example_pair_policy"),
        "declareert",
        id="5-voorbeeldpaar-zonder-policy",
    ),
    pytest.param(
        _review_policy_zonder_reden,
        "example_pair_reason",
        id="6-afwijkende-policy-zonder-reden",
    ),
    pytest.param(
        _review_policy_zonder_issue,
        "DEF-nnn",
        id="7-afwijkende-policy-zonder-geldig-issue",
    ),
]


@pytest.mark.parametrize(("muteer", "fragment"), SCHENDINGEN)
def test_schending_wordt_geweigerd(basisrecord, muteer, fragment):
    data = copy.deepcopy(basisrecord)
    muteer(data)

    with pytest.raises(RuleContractError, match=fragment):
        _bouw(data)


def test_elke_schending_noemt_de_regel_die_hem_veroorzaakt(basisrecord):
    """Een melding zonder rule_id is in een set van 53 onbruikbaar."""
    for param in SCHENDINGEN:
        muteer, _fragment = param.values
        data = copy.deepcopy(basisrecord)
        muteer(data)

        with pytest.raises(RuleContractError) as fout:
            _bouw(data)

        assert PROEFREGEL in str(fout.value), param.id
