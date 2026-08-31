"""DEF-621: een incomplete regelset levert nooit een validatieoordeel.

Vandaag loopt een validatie met een half geladen regelset gewoon door: er
wordt geëvalueerd, gescoord en een acceptance-gate bepaald over de regels die
toevallig geladen zijn. Het resultaat is dan niet fout maar misleidend — een
score over 7 van 53 regels ziet er hetzelfde uit als een score over 53.

Deze suite eist een guard aan het enige chokepoint
(`ModularValidationService.validate_definition`) die vóór evaluatie, scoring
en acceptability stopt en `validation_unknown` retourneert met reden
`ruleset_incomplete`.

Het scherpste bewijs staat in `test_geen_evaluatie_scoring_of_gate_bij_...`:
de drie vervolgstappen worden vervangen door een `AssertionError`. Slaagt die
test, dan is bewezen dat de guard ervóór returnt — niet dat de uitkomst
toevallig klopt.

De runtimegrens is bewust asymmetrisch: de directe loader blijft hard falen
op een kapotte set, terwijl de service beschikbaar blijft. Beide helften staan
naast elkaar in `test_directe_loader_blijft_gooien_maar_service_construeert`.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from services.validation.interfaces import (
    UNKNOWN_REASON_RULESET_INCOMPLETE,
    VALIDATION_STATUS_UNKNOWN,
    VALIDATION_STATUS_VALIDATED,
)
from services.validation.modular_validation_service import ModularValidationService
from toetsregels.manager import ToetsregelManager
from toetsregels.runtime_contract import RuleContractError, root_contract_policy

pytestmark = [pytest.mark.unit]


ECHTE_REGELS = Path(__file__).resolve().parents[3] / "src" / "toetsregels" / "regels"


@pytest.fixture(scope="module")
def alle_regels() -> dict[str, dict[str, Any]]:
    """De échte 53 regelrecords, per bestandsnaam-ID."""
    return {
        pad.stem: json.loads(pad.read_text(encoding="utf-8"))
        for pad in sorted(ECHTE_REGELS.glob("*.json"))
    }


class NepManager:
    """Minimale manager die exact de meegegeven regelset teruggeeft."""

    def __init__(self, regels: dict[str, dict[str, Any]], regels_dir: Path) -> None:
        self._regels = dict(regels)
        self.regels_dir = regels_dir
        self.clear_calls = 0

    def get_all_regels(self) -> dict[str, dict[str, Any]]:
        return dict(self._regels)

    def clear_cache(self) -> None:
        self.clear_calls += 1


def _service(regels: dict[str, dict[str, Any]], dir_: Path) -> ModularValidationService:
    return ModularValidationService(toetsregel_manager=NepManager(regels, dir_))


async def _valideer(service: ModularValidationService) -> dict[str, Any]:
    return await service.validate_definition(
        begrip="besluit",
        text="besluit: een schriftelijke beslissing van een bestuursorgaan",
    )


# ------------------------------------------------------- guard: hoofdgedrag


@pytest.mark.asyncio
async def test_volledige_set_levert_een_gewoon_validatieoordeel(
    alle_regels: dict[str, dict[str, Any]],
) -> None:
    resultaat = await _valideer(_service(alle_regels, ECHTE_REGELS))

    assert resultaat["validation_status"] == VALIDATION_STATUS_VALIDATED
    assert "unknown_reason" not in resultaat
    assert isinstance(resultaat["overall_score"], float)


@pytest.mark.parametrize(
    "variant",
    ["52_van_53", "7_van_53", "leeg", "geen_manager"],
)
@pytest.mark.asyncio
async def test_incomplete_set_levert_validation_unknown(
    alle_regels: dict[str, dict[str, Any]], variant: str
) -> None:
    """Elke onvolledige uitgangssituatie geeft dezelfde machineleesbare uitkomst."""
    ids = sorted(alle_regels)
    if variant == "geen_manager":
        service = ModularValidationService(toetsregel_manager=None)
    else:
        subset = {
            "52_van_53": {k: alle_regels[k] for k in ids[:-1]},
            "7_van_53": {k: alle_regels[k] for k in ids[:7]},
            "leeg": {},
        }[variant]
        service = _service(subset, ECHTE_REGELS)

    resultaat = await _valideer(service)

    assert resultaat["validation_status"] == VALIDATION_STATUS_UNKNOWN, variant
    assert resultaat["unknown_reason"] == UNKNOWN_REASON_RULESET_INCOMPLETE, variant
    # Compatibiliteitsplaceholders: fail-closed, geen kwaliteitsoordeel.
    assert resultaat["overall_score"] == 0.0, variant
    assert resultaat["is_acceptable"] is False, variant
    assert resultaat["validation_readiness"]["ready"] is False, variant
    # Geen schijn van een uitgevoerde beoordeling.
    assert resultaat["passed_rules"] == [], variant
    assert "acceptance_gate" not in resultaat, variant


@pytest.mark.asyncio
async def test_geen_evaluatie_scoring_of_gate_bij_incomplete_set(
    alle_regels: dict[str, dict[str, Any]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """De guard returnt vóór alle drie de vervolgstappen.

    Zonder deze test bewijst een correcte uitkomst nog niets: die kan ook
    ontstaan doordat de evaluatie draait en achteraf wordt overschreven.
    """
    ids = sorted(alle_regels)
    service = _service({k: alle_regels[k] for k in ids[:7]}, ECHTE_REGELS)

    for methode in (
        "_evaluate_rule",
        "_calculate_category_scores",
        "_evaluate_acceptance_gates",
    ):
        monkeypatch.setattr(
            ModularValidationService,
            methode,
            lambda *a, _m=methode, **kw: pytest.fail(
                f"{_m} aangeroepen ondanks incomplete regelset"
            ),
        )

    resultaat = await _valideer(service)
    assert resultaat["validation_status"] == VALIDATION_STATUS_UNKNOWN


# --------------------------------------------------- runtimegrens vs loader


@pytest.mark.asyncio
async def test_directe_loader_blijft_gooien_maar_service_construeert(
    tmp_path: Path, alle_regels: dict[str, dict[str, Any]]
) -> None:
    """Asymmetrie is het punt: CI blijft rood, de app blijft beschikbaar.

    De directe lader moet op een kapotte set hard blijven falen — anders
    verdwijnt de repositorygate. Alleen `ModularValidationService` vertaalt
    diezelfde fout naar een beschikbare, maar onbepaalde validatie.
    """
    regels_dir = tmp_path / "regels"
    regels_dir.mkdir()
    for naam in sorted(alle_regels)[:5]:
        (regels_dir / f"{naam}.json").write_text(
            json.dumps(alle_regels[naam]), encoding="utf-8"
        )

    # a) de directe lader faalt hard
    manager = ToetsregelManager(base_dir=regels_dir.parent)
    with pytest.raises(RuleContractError):
        manager.get_all_regels()

    # b) de runtime-service construeert en levert validation_unknown
    service = ModularValidationService(toetsregel_manager=manager)
    resultaat = await _valideer(service)
    assert resultaat["validation_status"] == VALIDATION_STATUS_UNKNOWN
    assert resultaat["unknown_reason"] == UNKNOWN_REASON_RULESET_INCOMPLETE


@pytest.mark.asyncio
async def test_onleesbare_root_ssot_geeft_dezelfde_machineleesbare_reden(
    monkeypatch: pytest.MonkeyPatch, alle_regels: dict[str, dict[str, Any]]
) -> None:
    """Ook zonder bekende verwachte ID-set blijft de reden exact `ruleset_incomplete`.

    De onderliggende oorzaak hoort in het log, niet in het contract: een
    consumer moet op één reden kunnen matchen.
    """
    monkeypatch.setattr(
        "services.validation.modular_validation_service.root_contract_policy",
        lambda: (_ for _ in ()).throw(RuleContractError("root-SSOT onleesbaar")),
    )
    service = _service(alle_regels, ECHTE_REGELS)
    resultaat = await _valideer(service)

    assert resultaat["validation_status"] == VALIDATION_STATUS_UNKNOWN
    assert resultaat["unknown_reason"] == UNKNOWN_REASON_RULESET_INCOMPLETE


# ------------------------------------------------------------ readiness-API


@pytest.mark.parametrize("compleet", [True, False], ids=["ready", "unready"])
def test_health_status_draagt_readiness(
    alle_regels: dict[str, dict[str, Any]], compleet: bool
) -> None:
    ids = sorted(alle_regels)
    regels = alle_regels if compleet else {k: alle_regels[k] for k in ids[:7]}
    health = _service(regels, ECHTE_REGELS).get_health_status()

    assert health["validation_ready"] is compleet
    assert (health["validation_unknown_reason"] is None) is compleet
    assert health["rules_expected"] == len(root_contract_policy().rule_ids)


# ------------------------------------------------------------------- UI-stop


def test_ui_stopt_voor_elke_score_of_gateweergave(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """De gedeelde renderer mag bij unknown geen score of gate tonen.

    `render_validation_detailed_list` is het enige renderpad van alle drie de
    tabs; stopt hij hier niet, dan toont de UI 0% als kwaliteitsoordeel.
    """
    from ui.components import validation_view

    getoond: list[str] = []
    monkeypatch.setattr(
        validation_view.st,
        "markdown",
        lambda tekst, *a, **kw: getoond.append(str(tekst)),
    )
    monkeypatch.setattr(
        validation_view.st,
        "progress",
        lambda *a, **kw: pytest.fail(
            "score-weergave aangeroepen bij validation_unknown"
        ),
    )
    monkeypatch.setattr(
        validation_view.st,
        "metric",
        lambda *a, **kw: pytest.fail(
            "metric-weergave aangeroepen bij validation_unknown"
        ),
    )

    validation_view.render_validation_detailed_list(
        {
            "version": "1.2.0",
            "validation_status": VALIDATION_STATUS_UNKNOWN,
            "unknown_reason": UNKNOWN_REASON_RULESET_INCOMPLETE,
            "validation_readiness": {
                "ready": False,
                "expected_total": 53,
                "loaded_total": 7,
                "missing_rule_ids": ["REG-08"],
                "unexpected_rule_ids": [],
            },
            "overall_score": 0.0,
            "is_acceptable": False,
            "violations": [],
            "passed_rules": [],
            "detailed_scores": {},
            "system": {"correlation_id": "3f8c1a2e-0000-4000-8000-000000000000"},
        },
        key_prefix="test",
    )

    assert any("niet te bepalen" in t.lower() for t in getoond), getoond
