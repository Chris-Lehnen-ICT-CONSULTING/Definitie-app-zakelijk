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
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from toetsregels.runtime_contract import (
    AutomationStatus,
    ExamplePairPolicy,
    Executability,
    RuleContractError,
    RuleRecord,
    ScorePolicy,
    build_rule_record,
    build_rule_records,
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


def _bouw(data: dict[str, Any]) -> RuleRecord:
    return build_rule_record(PROEFREGEL, data, root_contract_policy())


def test_ongemuteerd_basisrecord_bouwt_zonder_fout(basisrecord):
    """Zonder dit anker bewijst geen enkele mutatietest iets.

    Bouwde het basisrecord al niet, dan zou elke `pytest.raises` hieronder
    slagen op een fout die niets met de mutatie te maken heeft.
    """
    record = _bouw(basisrecord)

    assert record.rule_id == PROEFREGEL
    assert record.has_example_pair is True


def test_proefregel_voldoet_nog_aan_alle_precondities(basisrecord):
    """Drift in CON-02 moet luid falen, niet de suite stil uithollen.

    Elke mutatie hieronder gaat ervan uit dat het basisrecord aan de goede
    kant van alle zeven invarianten zit. Verschuift CON-02 later — bv. naar
    `review_required` — dan wordt mutatie 3 de begintoestand en bewijst zijn
    `pytest.raises` niets meer. Deze test wijst die drift aan bij de bron.
    """
    record = _bouw(basisrecord)

    assert record.executability is Executability.DETERMINISTIC
    assert record.automation_status is AutomationStatus.AUTOMATED
    assert record.score_policy is ScorePolicy.SCORED
    assert record.example_pair_policy is ExamplePairPolicy.NORMATIVE


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


def _review_policy_zonder_issueveld(data: dict[str, Any]) -> None:
    data["runtime_contract"]["example_pair_policy"] = "review_policy"
    data["runtime_contract"]["example_pair_reason"] = "onderbouwing voor de test"
    data["runtime_contract"].pop("example_pair_issue", None)


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
        "declareert geen 'example_pair_policy'",
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
        id="7-afwijkende-policy-met-verkeerde-prefix",
    ),
    pytest.param(
        _review_policy_zonder_issueveld,
        "DEF-nnn",
        id="7b-afwijkende-policy-zonder-issueveld",
    ),
]


# --- de legale uitgangen ---------------------------------------------------


def _zonder_paar_en_zonder_policy(data: dict[str, Any]) -> None:
    data["foute_voorbeelden"] = []
    data["runtime_contract"].pop("example_pair_policy", None)


def _afwijkende_policy_volledig_onderbouwd(data: dict[str, Any]) -> None:
    data["runtime_contract"]["example_pair_policy"] = "review_policy"
    data["runtime_contract"]["example_pair_reason"] = "onderbouwing voor de test"
    data["runtime_contract"]["example_pair_issue"] = "DEF-624"


@pytest.mark.parametrize(
    "muteer",
    [
        pytest.param(_zonder_paar_en_zonder_policy, id="geen-paar-en-geen-policy"),
        pytest.param(
            _afwijkende_policy_volledig_onderbouwd, id="afwijkende-policy-onderbouwd"
        ),
    ],
)
def test_legale_uitgang_wordt_toegelaten(basisrecord, muteer):
    """Te streng is net zo fout als te los.

    Alle cases hieronder toetsen dat de guard weigert. Zonder deze twee zou
    een guard die élke niet-normatieve policy afwijst — of die een record
    zónder paar alsnog een policy laat eisen — de suite gewoon groen houden.
    """
    data = copy.deepcopy(basisrecord)
    muteer(data)

    assert _bouw(data).rule_id == PROEFREGEL


# --- de zeven schendingen, per stuk ----------------------------------------


@pytest.mark.parametrize(("muteer", "fragment"), SCHENDINGEN)
def test_schending_wordt_geweigerd(basisrecord, muteer, fragment):
    data = copy.deepcopy(basisrecord)
    muteer(data)

    with pytest.raises(RuleContractError, match=fragment) as fout:
        _bouw(data)

    # Een melding zonder rule_id is in een set van 53 onbruikbaar.
    assert PROEFREGEL in str(fout.value)


# --- de route die productie werkelijk neemt --------------------------------


@pytest.mark.parametrize(("muteer", "fragment"), SCHENDINGEN)
def test_productiepad_weigert_dezelfde_schendingen(basisrecord, muteer, fragment):
    """`build_rule_records` is de entry die de laders gebruiken.

    De tests hierboven roepen de enkelvoudige `build_rule_record` aan met een
    zelfgekozen policy. Zonder deze brug is niet bewezen dat de route die
    productie neemt dezelfde invarianten afdwingt — precies het patroon
    "de test raakt het pad met het probleem niet" dat DEF-676 aankaart.
    """
    data = copy.deepcopy(basisrecord)
    muteer(data)

    with pytest.raises(RuleContractError, match=fragment):
        build_rule_records({PROEFREGEL: data})


# --- de suite handhaaft haar eigen discriminatie-eis -----------------------


def _invariant_van(param_id: str) -> str:
    """`7b-...` en `7-...` toetsen dezelfde invariant vanuit twee vormen."""
    return param_id.split("-", 1)[0].rstrip("ab")


def test_elk_fragment_onderscheidt_zijn_eigen_invariant(basisrecord):
    """De docstring belooft unieke fragmenten; deze test dwingt dat af.

    Matcht een fragment ook de melding van een ándere invariant, dan houdt de
    bijbehorende testcase groen zodra die andere invariant meevuurt — en dan
    meet je de verkeerde regel. Een fragment mag wél meerdere schendings-
    vormen van dezelfde invariant matchen; dat is geen verzwakking.
    """
    meldingen: list[tuple[str, str]] = []
    for param in SCHENDINGEN:
        muteer, _fragment = param.values
        data = copy.deepcopy(basisrecord)
        muteer(data)
        with pytest.raises(RuleContractError) as fout:
            _bouw(data)
        meldingen.append((_invariant_van(param.id), str(fout.value)))

    vervuild = []
    for param in SCHENDINGEN:
        _muteer, fragment = param.values
        eigen = _invariant_van(param.id)
        vreemd = [
            invariant
            for invariant, melding in meldingen
            if invariant != eigen and re.search(fragment, melding)
        ]
        if vreemd:
            vervuild.append((param.id, fragment, sorted(set(vreemd))))

    assert not vervuild, f"fragmenten die een andere invariant matchen: {vervuild}"
