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

import copy
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


class StukkeManager:
    """Manager waarvan het laden met een generieke fout klapt.

    Geen `RuleContractError` maar een gewone `RuntimeError`: dat is
    constructorpad 3 uit het plan. Dat pad zette tot nu toe stil de
    degraded-vlag en viel terug op zeven baselineregels, waarna de validatie
    gewoon doorliep en een score over die zeven presenteerde.
    """

    def __init__(self, regels_dir: Path) -> None:
        self.regels_dir = regels_dir
        self.clear_calls = 0

    def get_all_regels(self) -> dict[str, dict[str, Any]]:
        raise RuntimeError("manager onbereikbaar")

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


@pytest.mark.asyncio
async def test_generieke_managerfout_geeft_validation_unknown(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Constructorpad 3: een generieke fout mag niet stil in baseline eindigen.

    Vandaag vangt `_load_rules_from_manager` elke niet-contractuele fout af,
    zet de degraded-vlag en laadt zeven baselineregels. De validatie loopt
    daarna gewoon door en levert een score over die zeven - niet te
    onderscheiden van een score over drieenvijftig. Dat is precies de
    misleiding die deze story sluit.

    De drie vervolgstappen worden vervangen door een `pytest.fail`, zodat
    bewezen is dat de guard ervoor returnt.
    """
    service = ModularValidationService(toetsregel_manager=StukkeManager(ECHTE_REGELS))

    health = service.get_health_status()
    assert health["validation_ready"] is False
    assert health["degraded_mode"] is True
    assert health["validation_unknown_reason"] == UNKNOWN_REASON_RULESET_INCOMPLETE

    for methode in (
        "_evaluate_rule",
        "_calculate_category_scores",
        "_evaluate_acceptance_gates",
    ):
        monkeypatch.setattr(
            ModularValidationService,
            methode,
            lambda *a, _m=methode, **kw: pytest.fail(
                f"{_m} aangeroepen na een generieke managerfout"
            ),
        )

    resultaat = await _valideer(service)

    assert resultaat["validation_status"] == VALIDATION_STATUS_UNKNOWN
    assert resultaat["unknown_reason"] == UNKNOWN_REASON_RULESET_INCOMPLETE
    assert resultaat["overall_score"] == 0.0
    assert resultaat["is_acceptable"] is False
    assert resultaat["passed_rules"] == []
    assert "acceptance_gate" not in resultaat
    assert resultaat["validation_readiness"]["ready"] is False


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


def test_snapshot_is_geisoleerd_van_manager_owned_regeldata(
    alle_regels: dict[str, dict[str, Any]],
) -> None:
    """Een mutatie via de manager mag de gepubliceerde generatie niet raken.

    De snapshot kopieerde alleen de buitenste dictionaries. De geneste
    regeldictionaries bleven dezelfde objecten als die van de manager:

        managerregel is snapshot.json_rules[rid] is snapshot.rule_records[rid].data

    Daardoor sijpelde een wijziging aan de managerdata onmiddellijk door in de
    actieve generatie - buiten de fingerprint om, buiten de lock om en zonder
    statewissel. Dat holt de hele atomische publicatie uit: twee gelijktijdige
    lezers konden dan alsnog verschillende regelinhoud zien terwijl zij
    dezelfde snapshot vasthielden.

    Er wordt hier bewust met een eigen diepe kopie gewerkt; de modulefixture
    is `scope="module"` en zou anders door deze mutatie vervuild raken.
    """
    eigen_data = copy.deepcopy(alle_regels)
    regel_id = next(
        rid
        for rid, regel in eigen_data.items()
        if isinstance(regel.get("herkenbaar_patronen"), list)
        and regel["herkenbaar_patronen"]
    )

    service = _service(eigen_data, ECHTE_REGELS)
    snapshot = service._snapshot

    # Geen gedeelde identiteit meer met de bron.
    assert snapshot.json_rules[regel_id] is not eigen_data[regel_id]
    assert snapshot.rule_records[regel_id].data is not eigen_data[regel_id]

    voor_toetsvraag = snapshot.json_rules[regel_id].get("toetsvraag")
    voor_patronen = list(snapshot.json_rules[regel_id]["herkenbaar_patronen"])

    # Muteer ná de constructie via de manager-owned data: een gewijzigd veld
    # en een gewijzigde geneste lijst.
    eigen_data[regel_id]["toetsvraag"] = "GEMUTEERD-NA-CONSTRUCTIE"
    eigen_data[regel_id]["herkenbaar_patronen"].append("GEMUTEERD-PATROON")

    assert snapshot.json_rules[regel_id].get("toetsvraag") == voor_toetsvraag
    assert snapshot.json_rules[regel_id]["herkenbaar_patronen"] == voor_patronen
    assert snapshot.rule_records[regel_id].data.get("toetsvraag") == voor_toetsvraag
    assert (
        "GEMUTEERD-PATROON" not in snapshot.json_rules[regel_id]["herkenbaar_patronen"]
    )


# ------------------------------------------------------------------- UI-stop


def _resultaat(status: str, **extra: Any) -> dict[str, Any]:
    basis: dict[str, Any] = {
        "version": "1.2.0",
        "validation_status": status,
        "overall_score": 0.0,
        "is_acceptable": False,
        "violations": [],
        "passed_rules": [],
        "detailed_scores": {},
        "system": {"correlation_id": "3f8c1a2e-0000-4000-8000-000000000000"},
    }
    basis.update(extra)
    return basis


def _vang_uitvoer(monkeypatch: pytest.MonkeyPatch, view: Any) -> list[str]:
    """Vang elke tekstuitvoer van de gedeelde renderer.

    Alleen de API-s die `validation_view` werkelijk gebruikt: st.progress en
    st.metric bestaan daar niet, en een monkeypatch daarop zou alleen een
    testopzetfout opleveren.
    """
    getoond: list[str] = []
    for api in ("markdown", "info", "warning", "success", "error", "write"):
        monkeypatch.setattr(
            view.st, api, lambda t, *a, **kw: getoond.append(str(t)), raising=True
        )
    return getoond


def test_ui_stopt_voor_score_gate_en_detailrenderer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Bij validation_unknown mag de gedeelde renderer niets van een oordeel tonen.

    `render_validation_detailed_list` is het enige renderpad van alle drie de
    tabs. Stopt hij hier niet, dan verschijnt "Overall Score: 0.00" als
    kwaliteitsoordeel terwijl er juist niets is geevalueerd.

    De gate wordt hier **expliciet** meegegeven. Zonder dat argument valt
    `gate or validation_result.get("acceptance_gate") or {}` terug op een
    lege dict en wordt de hele gate-tak sowieso overgeslagen - dan bewijst een
    assertie op afwezige gatetekst niets. Met een gevulde pass-gate zou de
    renderer zonder early return aantoonbaar "Gate:" of "Gates:" tonen.

    De twee detailhelpers worden vervangen door een `pytest.fail`: dat bewijst
    dat de early return ervoor ligt, en niet dat de uitvoer achteraf toevallig
    leeg blijft.
    """
    from ui.components import validation_view

    getoond = _vang_uitvoer(monkeypatch, validation_view)
    for naam in ("_calculate_validation_stats", "_build_detailed_assessment"):
        monkeypatch.setattr(
            validation_view,
            naam,
            lambda *a, _n=naam, **kw: pytest.fail(
                f"{_n} aangeroepen bij validation_unknown"
            ),
        )

    validation_view.render_validation_detailed_list(
        _resultaat(
            VALIDATION_STATUS_UNKNOWN,
            unknown_reason=UNKNOWN_REASON_RULESET_INCOMPLETE,
            validation_readiness={
                "ready": False,
                "expected_total": 53,
                "loaded_total": 7,
                "missing_rule_ids": ["CON-01"],
                "unexpected_rule_ids": [],
            },
        ),
        key_prefix="unknown",
        show_toggle=False,
        gate={
            "status": "pass",
            "acceptable": True,
            "gates_passed": ["drempel_overall", "drempel_categorie"],
            "gates_failed": [],
            "reasons": [],
        },
    )

    assert any("niet te bepalen" in t.lower() for t in getoond), getoond
    assert not any("overall score" in t.lower() for t in getoond), getoond
    # Zowel de enkelvoudige ("Gate: toegestaan") als de meervoudige
    # ("Gates: OK") weergave moet onbereikt blijven.
    assert not any(
        merker in t.lower() for t in getoond for merker in ("gate:", "gates:")
    ), getoond


def test_ui_toont_score_bij_validated(monkeypatch: pytest.MonkeyPatch) -> None:
    """De early return mag niet alle resultaten onderdrukken.

    Zonder deze positieve regressie zou een renderer die altijd stopt de
    negatieve test ook groen maken - en dan toont de UI nooit meer een score.
    """
    from ui.components import validation_view

    getoond = _vang_uitvoer(monkeypatch, validation_view)
    bereikt: list[str] = []
    monkeypatch.setattr(
        validation_view,
        "_calculate_validation_stats",
        lambda *a, **kw: bereikt.append("stats")
        or {"passed_count": 1, "total": 1, "percentage": 100.0, "failed_count": 0},
    )
    monkeypatch.setattr(
        validation_view,
        "_build_detailed_assessment",
        lambda *a, **kw: bereikt.append("detail") or ["OK regel"],
    )

    validation_view.render_validation_detailed_list(
        _resultaat(VALIDATION_STATUS_VALIDATED, overall_score=0.82, is_acceptable=True),
        key_prefix="validated",
        show_toggle=False,
    )

    assert any("Overall Score" in t for t in getoond), getoond
    assert bereikt == ["stats", "detail"], bereikt


# ------------------------------------------------------ snapshotarchitectuur


def test_runtime_snapshot_draagt_alle_rulesetvelden(
    alle_regels: dict[str, dict[str, Any]],
) -> None:
    """Een halve snapshot is net zo onbetrouwbaar als een halve regelset.

    Het evaluatiepad leest naast `rule_records` ook internal_rules,
    default_weights, json_rules, pattern_cache, contract_rule_ids en de
    tellingen. Blijven die als losse `self._...`-velden bestaan, dan kan een
    herlaadpoging een mengsel van twee generaties opleveren: nieuwe records
    met oude gewichten. Deze test eist dat alle ruleset-afhankelijke gegevens
    in een en dezelfde gepubliceerde snapshot zitten.
    """
    service = _service(alle_regels, ECHTE_REGELS)
    snap = service._snapshot

    verwachte_velden = {
        "fingerprint",
        "readiness",
        "contract_rule_ids",
        "internal_rules",
        "rule_records",
        "json_rules",
        "default_weights",
        "pattern_cache",
        "rules_loaded_count",
        "rules_expected_count",
        "is_degraded_mode",
        "degradation_reason",
    }
    ontbreekt = {veld for veld in verwachte_velden if not hasattr(snap, veld)}
    assert not ontbreekt, ontbreekt

    # Conform projectregel 4 worden de oude velden vervangen, niet gedupliceerd:
    # een alias kan uit een andere generatie komen dan de actieve snapshot.
    verboden_aliassen = {
        "_rule_records",
        "_json_rules",
        "_internal_rules",
        "_default_weights",
        "_pattern_cache",
        "_contract_rule_ids",
        "_rules_loaded_count",
        "_rules_expected_count",
    }
    achtergebleven = {a for a in verboden_aliassen if hasattr(service, a)}
    assert not achtergebleven, achtergebleven


def test_snapshotcollecties_zijn_onveranderlijk(
    alle_regels: dict[str, dict[str, Any]],
) -> None:
    """Een frozen dataclass maakt geneste dicts niet immutable.

    Zonder alleen-lezen views kan een evaluator de gepubliceerde generatie
    onder een gelijktijdige lezer uit muteren.
    """
    snap = _service(alle_regels, ECHTE_REGELS)._snapshot

    assert isinstance(snap.internal_rules, tuple)
    assert isinstance(snap.contract_rule_ids, tuple)

    for naam in ("rule_records", "json_rules", "default_weights"):
        collectie = getattr(snap, naam)
        with pytest.raises(TypeError):
            collectie["NIEUW-01"] = {}  # type: ignore[index]


def test_elke_generatie_krijgt_een_eigen_pattern_cache(
    alle_regels: dict[str, dict[str, Any]],
) -> None:
    """Een herbouwde regelset mag geen patronen van de vorige generatie erven.

    Anders blijft een gecompileerd patroon van een inmiddels verdwenen regel
    in gebruik.
    """
    service = _service(alle_regels, ECHTE_REGELS)
    eerste = service._snapshot
    eerste.pattern_cache["MARKER"] = object()

    tweede = service._bouw_snapshot("andere-fingerprint")

    assert tweede.pattern_cache is not eerste.pattern_cache
    assert "MARKER" not in tweede.pattern_cache
