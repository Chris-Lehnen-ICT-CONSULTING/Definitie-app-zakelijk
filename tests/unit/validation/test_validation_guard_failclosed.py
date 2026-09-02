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
from services.validation.readiness import bepaal_readiness, veilige_degradatiereden
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


# De zeven interne vangnetregels. Zij zijn óók contractregels, en dat maakt ze
# gevaarlijk: `_bouw_snapshot` voegde ze onvoorwaardelijk toe aan de lijst
# waarover readiness werd bepaald, dus vulde de service precies die gaten zelf
# op die zij moest signaleren.
BASELINE_IDS = (
    "CON-CIRC-001",
    "ESS-CONT-001",
    "STR-ORG-001",
    "STR-TERM-001",
    "VAL-EMP-001",
    "VAL-LEN-001",
    "VAL-LEN-002",
)


@pytest.mark.parametrize("ontbrekend", BASELINE_IDS)
@pytest.mark.asyncio
async def test_ontbrekende_baselineregel_wordt_niet_gemaskeerd(
    alle_regels: dict[str, dict[str, Any]],
    monkeypatch: pytest.MonkeyPatch,
    ontbrekend: str,
) -> None:
    """Readiness mag niet worden bepaald over een door de service opgevulde lijst.

    De baseline-append draaide vóór `bepaal_readiness`. Ontbrak uitsluitend
    een van deze zeven regels, dan vulde de append het gat en gold
    `set(codes) == set(contract_ids)`: readiness `ready`, status `validated`,
    en een score over 52 regels alsof het er 53 waren. De guard delegeerde
    zijn eigen invariant daarmee aan de laag die hij juist moest controleren.

    De manager hier valideert bewust niet zelf — dat is precies het
    injectiepunt waar de guard alleen op zichzelf kan terugvallen.
    """
    assert ontbrekend in alle_regels, "opzetfout: baseline-ID is geen contractregel"
    onvolledig = {k: v for k, v in alle_regels.items() if k != ontbrekend}
    assert len(onvolledig) == len(alle_regels) - 1

    service = _service(onvolledig, ECHTE_REGELS)

    for methode in (
        "_evaluate_rule",
        "_calculate_category_scores",
        "_evaluate_acceptance_gates",
    ):
        monkeypatch.setattr(
            ModularValidationService,
            methode,
            lambda *a, _m=methode, **kw: pytest.fail(
                f"{_m} aangeroepen terwijl {ontbrekend} ontbreekt"
            ),
        )

    resultaat = await _valideer(service)

    assert resultaat["validation_status"] == VALIDATION_STATUS_UNKNOWN, resultaat
    assert resultaat["unknown_reason"] == UNKNOWN_REASON_RULESET_INCOMPLETE
    assert resultaat["is_acceptable"] is False
    assert ontbrekend in resultaat["validation_readiness"]["missing_rule_ids"]

    snapshot = service._snapshot
    assert snapshot.rules_loaded_count == 52, snapshot.rules_loaded_count
    assert ontbrekend in snapshot.readiness.missing_rule_ids
    # De vangnetten blijven wél in de uitvoervolgorde staan; alleen readiness
    # mag er niet op steunen.
    assert ontbrekend in snapshot.internal_rules


def test_lege_manager_telt_nul_geladen_regels(
    alle_regels: dict[str, dict[str, Any]],
) -> None:
    """Interne defaults zijn geen geladen regels.

    Zonder regels valt `_bouw_snapshot` terug op een interne default-set. Die
    telt niet als lading: `rules_loaded_count` hoort nul te zijn, anders
    rapporteert `system.rules_loaded` en `get_health_status` een aantal dat
    nooit van schijf kwam.
    """
    service = _service({}, ECHTE_REGELS)
    snapshot = service._snapshot

    assert snapshot.rules_loaded_count == 0, snapshot.rules_loaded_count
    assert snapshot.readiness.ready is False
    assert f"0/{len(snapshot.contract_rule_ids)}" in (
        snapshot.degradation_reason or ""
    ), snapshot.degradation_reason


def test_readiness_eist_ook_cardinaliteit(
    alle_regels: dict[str, dict[str, Any]],
) -> None:
    """Twee schrijfwijzen van hetzelfde ID zijn samen één regel te veel.

    `_index` klapt `ARAI-01` en `ARAI_01` samen tot één canonieke sleutel,
    dus een zuivere verzamelingsvergelijking ziet 53 == 53 terwijl er 54
    ID's zijn en niemand weet welke van de twee geldt. `rule_cache.get_stats`
    kreeg die cardinaliteitseis al; readiness hoort dezelfde definitie van
    volledigheid te hanteren.
    """
    verwacht = sorted(alle_regels)
    alias = next(rid for rid in verwacht if "-" in rid).replace("-", "_")
    geladen = [*verwacht, alias]

    readiness = bepaal_readiness(verwacht, geladen)

    assert readiness.ready is False, readiness
    assert readiness.reason == UNKNOWN_REASON_RULESET_INCOMPLETE


def test_readiness_verwerkt_generators(
    alle_regels: dict[str, dict[str, Any]],
) -> None:
    """De cardinaliteitseis mag een eenmalig itereerbare bron niet slopen.

    `bepaal_readiness` accepteert `Iterable`; wie een generator meegeeft, mag
    niet stil een lege verzameling terugkrijgen doordat de invoer twee keer
    wordt doorlopen.
    """
    verwacht = sorted(alle_regels)

    readiness = bepaal_readiness((r for r in verwacht), (r for r in verwacht))

    assert readiness.ready is True, readiness
    assert readiness.missing_rule_ids == ()
    assert readiness.unexpected_rule_ids == ()


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
    # DEF-621 commit 4: de service leest de policy vers uit `ROOT_SSOT_PAD` en
    # niet langer via het met `lru_cache` afgedekte `root_contract_policy()`.
    # De naad verhuist mee; de stub accepteert het padargument.
    monkeypatch.setattr(
        "services.validation.modular_validation_service.load_root_contract_policy",
        lambda *a, **kw: (_ for _ in ()).throw(
            RuleContractError("root-SSOT onleesbaar")
        ),
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


@pytest.mark.parametrize(
    ("naam", "readiness"),
    [
        ("ontbreekt", None),
        ("expliciet None", {"validation_readiness": None}),
        ("lege dict", {"validation_readiness": {}}),
        ("zonder tellingen", {"validation_readiness": {"ready": False}}),
        ("string", {"validation_readiness": "kapot"}),
        ("lijst", {"validation_readiness": [1, 2]}),
        ("None-tellingen", {"validation_readiness": {"loaded_total": None}}),
    ],
)
def test_ui_stopt_ook_bij_misvormde_readiness(
    monkeypatch: pytest.MonkeyPatch, naam: str, readiness: dict[str, Any] | None
) -> None:
    """De stop mag nooit afhangen van de vorm van het readiness-object.

    De guard is het vangnet; klapt hij zelf, dan valt de UI terug op het
    afvangpad van de aanroeper. De Edit-tab slikt zo-n exceptie stil en laat
    dan de hele Kwaliteitstoetsing verdwijnen - geen score, maar ook geen
    melding dat er niets is getoetst. De telling is optioneel; de stop is dat
    niet.
    """
    from ui.components import validation_view

    getoond = _vang_uitvoer(monkeypatch, validation_view)
    for helper in ("_calculate_validation_stats", "_build_detailed_assessment"):
        monkeypatch.setattr(
            validation_view,
            helper,
            lambda *a, _n=helper, **kw: pytest.fail(f"{_n} aangeroepen bij unknown"),
        )

    validation_view.render_validation_detailed_list(
        _resultaat(
            VALIDATION_STATUS_UNKNOWN,
            unknown_reason=UNKNOWN_REASON_RULESET_INCOMPLETE,
            **(readiness or {}),
        ),
        key_prefix=f"misvormd_{naam}",
        show_toggle=True,
        gate={"status": "pass", "acceptable": True, "reasons": []},
    )

    assert any("niet te bepalen" in t.lower() for t in getoond), (naam, getoond)
    assert not any("overall score" in t.lower() for t in getoond), (naam, getoond)
    assert not any(
        merker in t.lower() for t in getoond for merker in ("gate:", "gates:", "%")
    ), (naam, getoond)


def test_ui_toont_de_telling_alleen_wanneer_die_klopt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Een bruikbare telling hoort erbij; een onbruikbare mag niet verzonnen worden."""
    from ui.components import validation_view

    getoond = _vang_uitvoer(monkeypatch, validation_view)
    validation_view.render_validation_detailed_list(
        _resultaat(
            VALIDATION_STATUS_UNKNOWN,
            validation_readiness={"loaded_total": 7, "expected_total": 53},
        ),
        key_prefix="telling",
        show_toggle=False,
    )

    assert any("7" in t and "53" in t for t in getoond), getoond


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

    tweede = service._bouw_snapshot("andere-fingerprint", root_contract_policy())

    assert tweede.pattern_cache is not eerste.pattern_cache
    assert "MARKER" not in tweede.pattern_cache


# ------------------------------------------- degradatiereden: geen padlek


@pytest.mark.parametrize(
    ("oorzaak", "verwachte_bestandsnaam"),
    [
        pytest.param(
            FileNotFoundError(
                2,
                "No such file or directory",
                "/Users/iemand/Projecten/Definitie-app/src/toetsregels/regels/ARAI-01.json",
            ),
            "ARAI-01.json",
            id="ontbrekend_regelbestand",
        ),
        pytest.param(
            RuleContractError(
                "contract onleesbaar: "
                "/Users/iemand/Projecten/Definitie-app/config/toetsregels/"
                "toetsregels_config.yaml"
            ),
            "toetsregels_config.yaml",
            id="onleesbaar_contract",
        ),
        pytest.param(
            PermissionError(
                13,
                "Permission denied",
                "/Users/iemand/.config/definitie-app/regels/STR-ORG-001.json",
            ),
            "STR-ORG-001.json",
            id="geen_leesrechten",
        ),
    ],
)
def test_degradatiereden_toont_geen_filesystem_pad(
    alle_regels: dict[str, dict[str, Any]],
    oorzaak: BaseException,
    verwachte_bestandsnaam: str,
) -> None:
    """De reden landt in de UI, dus een ruw pad hoort er niet in.

    `definition_generator_tab._render_degraded_banner` zet
    `degradation_reason` letterlijk in de expander Technische details. Een
    OS-fout draagt het volledige pad mee, inclusief de accountnaam van wie de
    app draait. In de log mag dat pad blijven staan: DEF-580 heeft paden daar
    bewust buiten de redactie gehouden om tracebacks leesbaar te houden. Naar
    het scherm mag het niet.

    De bestandsnaam blijft wel staan. Dat is de diagnostiek waar iemand iets
    aan heeft; de mapstructuur eronder is alleen ruis met een accountnaam
    erin. Geparametriseerd over drie foutsoorten, want alle drie de
    aanroepplekken van `_lege_snapshot` geven een willekeurige exceptie door.
    """
    service = _service(alle_regels, ECHTE_REGELS)

    snapshot = service._lege_snapshot(fingerprint=None, oorzaak=oorzaak)
    reden = snapshot.degradation_reason or ""

    assert "/Users/" not in reden, reden
    assert "iemand" not in reden, reden
    assert verwachte_bestandsnaam in reden, reden


# ------------------------------- A-1: bekende verwachting niet weggooien


@pytest.mark.asyncio
async def test_kapot_regelrecord_behoudt_de_bekende_contractverwachting(
    monkeypatch: pytest.MonkeyPatch, alle_regels: dict[str, dict[str, Any]]
) -> None:
    """Een leesbare root-SSOT hoort de verwachting te blijven dragen.

    Dit is het kernscenario van DEF-621: de contract-SSOT is prima leesbaar,
    maar een regelrecord deugt niet en `build_rule_records` faalt. De
    verwachte ID-set is op dat moment al bekend, want `_bouw_snapshot` laadt
    de policy vóór de records.

    Ging die verwachting verloren, dan meldt de UI letterlijk 0 van 0 en is
    `missing_rule_ids` leeg, precies daar waar deze story juist wilde
    vertellen wat er ontbreekt. Fail-closed blijft overeind, maar de
    diagnostiek verdampt.
    """
    verwacht_aantal = len(root_contract_policy().rule_ids)
    assert verwacht_aantal > 0, "opzetfout: contract levert geen ID-s"

    monkeypatch.setattr(
        "services.validation.modular_validation_service.build_rule_records",
        lambda *a, **kw: (_ for _ in ()).throw(
            RuleContractError("regelrecord mist een bekende evaluator")
        ),
    )

    resultaat = await _valideer(_service(alle_regels, ECHTE_REGELS))
    readiness = resultaat["validation_readiness"]

    assert resultaat["validation_status"] == VALIDATION_STATUS_UNKNOWN
    assert resultaat["unknown_reason"] == UNKNOWN_REASON_RULESET_INCOMPLETE
    assert readiness["ready"] is False
    assert readiness["loaded_total"] == 0, readiness
    assert readiness["expected_total"] == verwacht_aantal, readiness
    assert len(readiness["missing_rule_ids"]) == verwacht_aantal, readiness


@pytest.mark.asyncio
async def test_onleesbare_root_ssot_houdt_de_verwachting_wel_leeg(
    monkeypatch: pytest.MonkeyPatch, alle_regels: dict[str, dict[str, Any]]
) -> None:
    """De keerzijde: zonder leesbaar contract is de verwachting echt onbekend.

    Hier hoort `expected_total` nul te zijn en `missing_rule_ids` leeg. Een
    verwachting verzinnen zou dezelfde tautologie herhalen die deze story
    bestrijdt. Deze test borgt dat de reparatie voor het kapotte record die
    grens niet meesleept.
    """
    monkeypatch.setattr(
        "services.validation.modular_validation_service.load_root_contract_policy",
        lambda *a, **kw: (_ for _ in ()).throw(
            RuleContractError("root-SSOT onleesbaar")
        ),
    )

    resultaat = await _valideer(_service(alle_regels, ECHTE_REGELS))
    readiness = resultaat["validation_readiness"]

    assert resultaat["validation_status"] == VALIDATION_STATUS_UNKNOWN
    assert readiness["ready"] is False
    assert readiness["expected_total"] == 0, readiness
    assert readiness["missing_rule_ids"] == [], readiness


# ------------------- S-1: fingerprint en snapshot, dezelfde brontoestand


def _wijzig_bronomvang(pad: Path, regel: dict[str, Any], spaties: int) -> None:
    """Wijzig de bestandsgrootte zonder de JSON ongeldig te maken.

    De fingerprint kijkt naar `(pad, grootte, mtime_ns)`. Sturen op grootte
    is deterministisch; sturen op mtime zou van klokresolutie afhangen en
    daarmee precies de flakiness introduceren die deze suite vermijdt.
    """
    pad.write_text(json.dumps(regel) + " " * spaties, encoding="utf-8")


@pytest.mark.asyncio
async def test_bronwijziging_tijdens_opbouw_publiceert_geen_ready_snapshot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, alle_regels: dict[str, Any]
) -> None:
    """De fingerprint hoort dezelfde generatie te beschrijven als de inhoud.

    De fingerprint wordt vóór de lock gemeten, maar `_bouw_snapshot` leest de
    schijf pas daarna. Wijzigen de bronnen daartussen, dan draagt een ready
    snapshot het label van een andere brontoestand. Verdwijnt een regel later
    opnieuw en levert dat exact dezelfde fingerprint op, dan ziet de service
    die overgang nooit meer - precies wat de fingerprint moest voorkomen.

    Tweede helft van het bewijs: na zo-n botsing mag de service niet
    vastzitten. De eerstvolgende validatie hoort gewoon opnieuw te bouwen.
    """
    regels_dir = tmp_path / "regels"
    regels_dir.mkdir()
    for naam, regel in alle_regels.items():
        (regels_dir / f"{naam}.json").write_text(json.dumps(regel), encoding="utf-8")

    service = ModularValidationService(
        toetsregel_manager=ToetsregelManager(base_dir=regels_dir.parent)
    )
    assert service._snapshot.readiness.ready is True, "opzetfout: start niet ready"

    eerste = sorted(alle_regels)[0]
    slachtoffer = regels_dir / f"{eerste}.json"

    # Stap 1: een echte bronwijziging, zodat er een herbouw volgt.
    _wijzig_bronomvang(slachtoffer, alle_regels[eerste], 1)

    # Stap 2: tijdens die herbouw wijzigt de bron nog een keer. Eenmalig,
    # zodat de tweede validatie een schone meting doet.
    echte_bouw = service._bouw_snapshot
    nog_muteren = {"actief": True}

    def bouw_en_muteer(fingerprint: str | None, policy: Any) -> Any:
        gebouwd = echte_bouw(fingerprint, policy)
        if nog_muteren["actief"]:
            nog_muteren["actief"] = False
            _wijzig_bronomvang(slachtoffer, alle_regels[eerste], 2)
        return gebouwd

    monkeypatch.setattr(service, "_bouw_snapshot", bouw_en_muteer)

    await _valideer(service)

    gepubliceerd = service._snapshot
    assert gepubliceerd.readiness.ready is False, (
        "een ready snapshot is gepubliceerd terwijl de bronnen tijdens de "
        f"opbouw wijzigden; fingerprint={gepubliceerd.fingerprint}"
    )

    # De service mag hier niet blijven hangen: de bronnen zijn nu stabiel,
    # dus de volgende validatie hoort een gewoon oordeel op te leveren.
    tweede = await _valideer(service)

    assert service._snapshot.readiness.ready is True, "service zit vast"
    assert tweede["validation_status"] == VALIDATION_STATUS_VALIDATED, tweede


@pytest.mark.asyncio
async def test_tweede_policyleesfout_verliest_de_eerste_verwachting_niet(
    monkeypatch: pytest.MonkeyPatch, alle_regels: dict[str, dict[str, Any]]
) -> None:
    """Een eenmaal gelezen verwachting mag niet van een herlezing afhangen.

    De opbouw leest de contractpolicy en struikelt daarna over de records. Op
    dat moment is de verwachte ID-set al bekend. Reconstrueert het foutpad
    haar door de root-SSOT opnieuw te lezen, dan hangt de diagnostiek af van
    een tweede lezing die net zo goed kan mislukken - en juist een onleesbaar
    contract is een realistische reden waarom de eerste opbouw faalde.

    Hier faalt elke lezing ná de eerste. De generatie hoort de verwachting uit
    die eerste, geslaagde lezing te blijven dragen.
    """
    echte_policy = root_contract_policy()
    verwacht_aantal = len(echte_policy.rule_ids)
    assert verwacht_aantal > 0, "opzetfout: contract levert geen ID-s"

    leesbeurten = {"aantal": 0}

    def alleen_de_eerste_lezing_lukt(*_args: Any, **_kwargs: Any) -> Any:
        leesbeurten["aantal"] += 1
        if leesbeurten["aantal"] == 1:
            return echte_policy
        raise RuleContractError("root-SSOT onleesbaar bij herlezen")

    monkeypatch.setattr(
        "services.validation.modular_validation_service.load_root_contract_policy",
        alleen_de_eerste_lezing_lukt,
    )
    monkeypatch.setattr(
        "services.validation.modular_validation_service.build_rule_records",
        lambda *a, **kw: (_ for _ in ()).throw(
            RuleContractError("regelrecord mist een bekende evaluator")
        ),
    )

    service = _service(alle_regels, ECHTE_REGELS)
    resultaat = await _valideer(service)
    readiness = resultaat["validation_readiness"]

    assert resultaat["validation_status"] == VALIDATION_STATUS_UNKNOWN
    assert resultaat["unknown_reason"] == UNKNOWN_REASON_RULESET_INCOMPLETE
    assert readiness["ready"] is False
    assert readiness["loaded_total"] == 0, readiness
    assert readiness["expected_total"] == verwacht_aantal, readiness
    assert len(readiness["missing_rule_ids"]) == verwacht_aantal, readiness
    assert service._snapshot.contract_rule_ids == tuple(echte_policy.rule_ids)


# ---------------- DEF-709: generatieconsistentie van de runtimesnapshot


@pytest.mark.asyncio
async def test_teruggekeerde_bron_tijdens_opbouw_levert_geen_ready_snapshot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, alle_regels: dict[str, Any]
) -> None:
    """A naar B naar A: gelijke fingerprints, ongelijke werkelijkheid.

    De vorige reparatie vergeleek de fingerprint vóór en ná de opbouw. Dat
    vangt een gewone wijziging, maar niet een bron die terugkeert naar exact
    dezelfde toestand: dan zijn beide metingen identiek en glipt een ready
    generatie er alsnog doorheen.

    Concreet: een regelbestand ontbreekt, komt terug terwijl de opbouw leest,
    en verdwijnt weer. De opbouw las 53 regels, de schijf heeft er 52, en de
    fingerprint van vóór en ná is dezelfde. Erger nog dan een eenmalige
    misser: de fast path matcht daarna op die fingerprint, dus de service
    blijft een oordeel geven over een set die niet meer bestaat.

    De invariant is dus niet dat de fingerprint gelijk bleef, maar dat de
    gebouwde inhoud past bij wat er op schijf staat.
    """
    regels_dir = tmp_path / "regels"
    regels_dir.mkdir()
    for naam, regel in alle_regels.items():
        (regels_dir / f"{naam}.json").write_text(json.dumps(regel), encoding="utf-8")

    service = ModularValidationService(
        toetsregel_manager=ToetsregelManager(base_dir=regels_dir.parent)
    )
    assert service._snapshot.readiness.ready is True, "opzetfout: start niet ready"

    eerste = sorted(alle_regels)[0]
    slachtoffer = regels_dir / f"{eerste}.json"
    bewaard = slachtoffer.read_text(encoding="utf-8")

    # Toestand B: het bestand ontbreekt. Dit is wat de fingerprint meet.
    slachtoffer.unlink()

    echte_bouw = service._bouw_snapshot
    eenmalig = {"actief": True}

    def bouw_met_terugkeer(fingerprint: str | None, policy: Any) -> Any:
        if not eenmalig["actief"]:
            return echte_bouw(fingerprint, policy)
        eenmalig["actief"] = False
        slachtoffer.write_text(bewaard, encoding="utf-8")
        gebouwd = echte_bouw(fingerprint, policy)
        slachtoffer.unlink()
        return gebouwd

    monkeypatch.setattr(service, "_bouw_snapshot", bouw_met_terugkeer)

    resultaat = await _valideer(service)
    snap = service._snapshot

    assert len(list(regels_dir.glob("*.json"))) == 52, "opzetfout: bron is compleet"
    assert snap.readiness.ready is False, (
        f"ready gepubliceerd terwijl de bron 52 bestanden telt; de snapshot "
        f"draagt {snap.rules_loaded_count} regels onder fingerprint "
        f"{snap.fingerprint}"
    )
    assert resultaat["validation_status"] == VALIDATION_STATUS_UNKNOWN


@pytest.mark.asyncio
async def test_wachten_op_de_lock_verdringt_geen_geldige_generatie(
    monkeypatch: pytest.MonkeyPatch, alle_regels: dict[str, Any]
) -> None:
    """Een fingerprint van vóór de lock beschrijft de generatie niet meer.

    De meting gebeurt buiten de lock. Wie daar wacht terwijl een andere
    thread intussen een geldige generatie publiceert, hervat met een
    verouderd label: hij bouwt actuele inhoud, hangt er de oude fingerprint
    aan, en de publicatiecontrole ziet dan een verschil dat er in
    werkelijkheid niet is. Gevolg is een fail-closed snapshot bovenop een
    complete regelset - fail-closed in de veilige richting, maar wel een
    onterechht validation_unknown.

    Hier gemodelleerd met een fingerprintreeks in plaats van echte threads:
    de eerste meting geeft de oude waarde, elke volgende de nieuwe. Wordt er
    binnen de lock opnieuw gemeten, dan bouwt en publiceert de service op de
    actuele waarde en blijft de uitkomst een gewoon oordeel.
    """
    service = _service(alle_regels, ECHTE_REGELS)
    assert service._snapshot.readiness.ready is True, "opzetfout: start niet ready"

    # De actieve generatie draagt geen fingerprint, zodat de fast path niet
    # meteen returnt en het herlaadpad daadwerkelijk wordt gelopen.
    service._snapshot = service._lege_snapshot(
        fingerprint=None,
        oorzaak=None,
        contract_ids=tuple(root_contract_policy().rule_ids),
    )

    metingen = {"aantal": 0}

    def fingerprint_wijzigt_na_de_eerste_meting(*_a: Any, **_kw: Any) -> str:
        metingen["aantal"] += 1
        return "oud" if metingen["aantal"] == 1 else "nieuw"

    monkeypatch.setattr(
        "services.validation.modular_validation_service.bereken_fingerprint",
        fingerprint_wijzigt_na_de_eerste_meting,
    )

    resultaat = await _valideer(service)
    snap = service._snapshot

    assert snap.readiness.ready is True, (
        "een complete regelset is fail-closed weggezet omdat de fingerprint "
        f"van vóór de lock verouderd was; fingerprint={snap.fingerprint}"
    )
    assert resultaat["validation_status"] == VALIDATION_STATUS_VALIDATED


@pytest.mark.parametrize(
    ("oorzaak", "verboden", "verwacht"),
    [
        pytest.param(
            FileNotFoundError(
                2,
                "No such file or directory",
                "/Volumes/Team Share/Users/iemand/regels/ARAI-01.json",
            ),
            "iemand",
            "ARAI-01.json",
            id="pad_met_spatie",
        ),
        pytest.param(
            FileNotFoundError(
                2,
                "No such file or directory",
                "C:\\Users\\iemand\\regels\\ARAI-01.json",
            ),
            "iemand",
            "ARAI-01.json",
            id="windows_pad",
        ),
    ],
)
def test_degradatiereden_lekt_ook_bij_lastige_paden_geen_accountnaam(
    oorzaak: BaseException, verboden: str, verwacht: str
) -> None:
    """Eén spatie of één backslash mag de redactie niet uitschakelen.

    De eerste versie zocht naar POSIX-paden zonder witruimte. Een gedeelde
    schijf met een spatie in de naam brak de match halverwege, waardoor juist
    het staartstuk met de accountnaam bleef staan; een Windows-pad ontsnapte
    volledig. Beide leveren precies het lek op dat de redactie moest dichten.
    """
    reden = veilige_degradatiereden(oorzaak) or ""

    assert verboden not in reden, reden
    assert verwacht in reden, reden


def test_relatief_pad_wordt_niet_verminkt() -> None:
    """De redactie mag geen tekst weggooien die geen absoluut pad is.

    De lookbehind keek alleen naar ASCII, dus een map met een accent liet het
    volgende fragment als los pad matchen en de tekst werd stilletjes aan
    elkaar geplakt.
    """
    reden = veilige_degradatiereden(RuntimeError("kon mapé/a/b.json niet lezen")) or ""

    assert "mapéb.json" not in reden, reden
    assert "b.json" in reden, reden
