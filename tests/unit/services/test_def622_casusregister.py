"""DEF-622 — de 26 casus-ID's van het CON-01 G/T/H-register op de huidige code.

Bron: `casusregister-generatie-v2.md` (kopie en hash in
`reports/def622/vervolg/onderzoeksbron/manifest.json`). Ieder ID heeft hier
zijn eigen herkenbare invoer en uitkomst op echte productiegrenzen (echte
regelset, echte orchestrator met bevroren modeluitvoer, echte cleaner,
echte promptbouw, synthetische opslag). Waar een casus expliciet uitgestelde
scope betreft (automatisch tekstherstel, DEF-638) bewijst de proef precies
wat besloten is: nul herstelcalls en handmatige opvolging.

Oude onderzoeksproeven (92b870d8 / d68a98a9) zijn geen uitvoeringsbewijs;
alles hieronder draait op de implementatiecommit.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from domain.context.contract import beoordeel_context
from opschoning.opschoning import opschonen
from services.null_repository import NullDefinitionRepository
from services.validation.modular_validation_service import ModularValidationService
from tests.unit.services.orchestrators.test_def622_generatiegrens import (
    _orchestrator,
    _request,
)
from toetsregels.manager import get_toetsregel_manager

pytestmark = [pytest.mark.unit]

KOPER_ZIN = "Controle die binnen Team Koper wordt uitgevoerd op dossiers."
NEUTRAAL = "Controle waarbij wordt vastgesteld of alle vereiste velden zijn ingevuld."
ZILVER = "Kwaliteitskeurmerk dat uitsluitend door Stichting Zilver wordt verleend."
DJI_META = "Controle, in de context van DJI, op de naleving van huisregels."
OM_ZIN = (
    "Handeling die door een toezichthouder wordt verricht om naleving vast te stellen."
)


@pytest.fixture(autouse=True)
def _geen_voorbeelden(monkeypatch):
    from voorbeelden import unified_voorbeelden

    async def _leeg(*_a: Any, **_k: Any) -> dict[str, Any]:
        return {}

    monkeypatch.setattr(unified_voorbeelden, "genereer_alle_voorbeelden_async", _leeg)


def _validator() -> ModularValidationService:
    return ModularValidationService(
        toetsregel_manager=get_toetsregel_manager(),
        repository=NullDefinitionRepository(),
    )


async def _toets(begrip: str, tekst: str, context: dict[str, Any]) -> dict[str, Any]:
    return await _validator().validate_definition(
        begrip=begrip, text=tekst, context=context
    )


def _con01(resultaat: dict[str, Any]) -> dict[str, Any]:
    return resultaat["rule_results"]["CON-01"]


def _review(
    detail: dict[str, Any], functie: str, actor: str = "expert"
) -> dict[str, Any]:
    naam = next(p for p in detail["parts"] if p.get("evidence"))
    return {
        "fingerprint": detail["fingerprint"],
        "actor": actor,
        "decisions": {naam["id"]: {"function": functie, "reason": "Casusbeoordeling."}},
    }


# ----------------------------------------------------------- G: generatie


@pytest.mark.asyncio
async def test_CON_GT_001_CW_GEN_05_lege_context_vraagt_context_en_start_geen_model(
    tmp_path,
):
    """Alle contextlijsten leeg: eerst context vragen, geen modelaanroep,
    geen concept. (Batch 1, generatiegrens.)"""
    orch, provider, repo = _orchestrator(tmp_path, NEUTRAAL)
    antwoord = await orch.create_definition(_request(org=[], jur=[], wet=[]))
    assert antwoord.success is False and provider.oproepen == []
    assert "minimaal één contextwaarde" in (antwoord.error or "").lower()


@pytest.mark.asyncio
async def test_CON_GT_002_neutrale_kern_met_koper_in_context():
    """D1 positief, D2 geen vermelding binnen het gecontroleerde bereik,
    metadata behouden; geen automatische vaststelling (status blijft concept
    in de generatiecasussen hieronder)."""
    resultaat = await _toets(
        "controle", NEUTRAAL, {"organisatorische_context": ["Team Koper"]}
    )
    detail = _con01(resultaat)
    assert resultaat["rule_statuses"]["CON-01"] == "pass"
    assert detail["parts"][0]["id"] == "context_aanwezig"
    assert not [p for p in detail["parts"] if p.get("evidence")]


@pytest.mark.asyncio
async def test_CON_GT_003_gegenereerde_koper_vermelding_is_signaal_dan_afkeur(tmp_path):
    """Gegenereerd: 'controle die binnen Team Koper wordt uitgevoerd' → eerst
    signaal (open) op de echte generatieroute; met vastgelegde
    registratiebeoordeling → Voldoet niet. Zelfde norm als CON-GT-008."""
    orch, provider, repo = _orchestrator(tmp_path, KOPER_ZIN)
    antwoord = await orch.create_definition(
        _request(begrip="controle", org=["Team Koper"])
    )
    assert antwoord.success is True, antwoord.error
    assert antwoord.validation_result["rule_statuses"]["CON-01"] == "review_required"
    detail = _con01(antwoord.validation_result)
    assert any(p.get("evidence") == "Team Koper" for p in detail["parts"])
    # De aangeleverde route met dezelfde tekst en beoordeling: afkeur.
    beoordeeld = await _toets(
        "controle",
        antwoord.definition.definitie,
        {
            "organisatorische_context": ["Team Koper"],
            "context_review": _review(detail, "registration"),
        },
    )
    assert beoordeeld["rule_statuses"]["CON-01"] == "fail"


@pytest.mark.asyncio
async def test_CON_GT_008_aangeleverde_koper_vermelding_zelfde_norm():
    """Aangeleverd (geen generatie): identieke norm — signaal, na
    registratiebeoordeling afkeur; het origineel wordt niet gewijzigd."""
    context = {"organisatorische_context": ["Team Koper"]}
    open_ = await _toets("controle", KOPER_ZIN, context)
    assert open_["rule_statuses"]["CON-01"] == "review_required"
    context["context_review"] = _review(_con01(open_), "registration")
    afkeur = await _toets("controle", KOPER_ZIN, context)
    assert afkeur["rule_statuses"]["CON-01"] == "fail"
    deel = next(p for p in _con01(afkeur)["parts"] if p.get("evidence"))
    assert deel["status"] == "fail" and "registratiecontext" in deel["reason"].lower()


@pytest.mark.asyncio
@pytest.mark.parametrize("ingang", ["gegenereerd", "aangeleverd"])
async def test_CW_GEN_02_CW_GEN_07_meta_frase_geen_automatische_exceptie(
    tmp_path, ingang
):
    """'in de context van DJI': eerst signaal/open, daarna afkeur indien
    registratievermelding vastgesteld — géén automatische meta-frase-exceptie."""
    context: dict[str, Any] = {"organisatorische_context": ["DJI"]}
    if ingang == "gegenereerd":
        orch, provider, repo = _orchestrator(tmp_path, DJI_META)
        antwoord = await orch.create_definition(
            _request(begrip="controle", org=["DJI"])
        )
        resultaat, tekst = antwoord.validation_result, antwoord.definition.definitie
    else:
        tekst = DJI_META
        resultaat = await _toets("controle", tekst, context)
    assert resultaat["rule_statuses"]["CON-01"] == "review_required"
    context["context_review"] = _review(_con01(resultaat), "registration")
    assert (await _toets("controle", tekst, context))["rule_statuses"][
        "CON-01"
    ] == "fail"


@pytest.mark.asyncio
async def test_CON_GT_004_CW_GEN_01_noodzakelijke_naam_behouden_en_toegestaan(tmp_path):
    """Zilverkeurmerk: de naam blijft behouden door generatie, opschoning en
    readback; eerst signaal, na geldige beoordeling toegestaan (Voldoet)."""
    orch, provider, repo = _orchestrator(tmp_path, ZILVER)
    antwoord = await orch.create_definition(
        _request(begrip="Zilverkeurmerk", org=["Stichting Zilver"])
    )
    assert antwoord.success is True, antwoord.error
    opgeslagen = repo.legacy_repo.get_definitie(antwoord.definition.id)
    assert "Stichting Zilver" in opgeslagen.get_definitie_tekst()
    assert antwoord.validation_result["rule_statuses"]["CON-01"] == "review_required"
    context = {
        "organisatorische_context": ["Stichting Zilver"],
        "context_review": _review(_con01(antwoord.validation_result), "necessary"),
    }
    assert (await _toets("Zilverkeurmerk", opgeslagen.get_definitie_tekst(), context))[
        "rule_statuses"
    ]["CON-01"] == "pass"


@pytest.mark.asyncio
async def test_CON_GT_005_naamtreffer_zonder_grond_blijft_open_en_blokkeert(tmp_path):
    """Dezelfde naamtreffer zonder onderbouwing: Nog te beoordelen; de
    vaststelgate blokkeert; geen grond wordt verzonnen."""
    from database.definitie_repository import DefinitieRecord, DefinitieStatus
    from services.definition_repository import DefinitionRepository
    from services.definition_workflow_service import DefinitionWorkflowService
    from services.workflow_service import WorkflowService

    repo = DefinitionRepository(str(tmp_path / "gt005.db"))
    did = repo.legacy_repo.create_definitie(
        DefinitieRecord(
            begrip="Zilverkeurmerk",
            definitie=ZILVER,
            categorie="type",
            organisatorische_context='["Stichting Zilver"]',
            status=DefinitieStatus.REVIEW.value,
            validation_score=0.9,
        )
    )
    gate = DefinitionWorkflowService(WorkflowService(), repo).preview_gate(did)
    assert gate["status"] == "blocked"
    assert any("nog te beoordelen" in r.lower() for r in gate["reasons"])


@pytest.mark.asyncio
async def test_CON_GT_006_CW_GEN_12_gewoon_woord_om_is_geen_naamafkeur():
    """'om' met OM in de context: geen inhoudelijke afkeur op letters alleen.
    Het naamsignaal blijft — bewust zonder acroniemuitzondering (B-04) —
    een open beoordeling, nooit 'Voldoet niet'; de cleaner vervormt de taal niet."""
    assert opschonen(OM_ZIN, "toezicht") == OM_ZIN
    resultaat = await _toets("toezicht", OM_ZIN, {"organisatorische_context": ["OM"]})
    assert resultaat["rule_statuses"]["CON-01"] != "fail"
    assert not any(v.get("code") == "CON-01" for v in resultaat["violations"])
    # Zonder OM in de context is er niets te beoordelen: Voldoet.
    zonder = await _toets(
        "toezicht", OM_ZIN, {"organisatorische_context": ["Team Koper"]}
    )
    assert zonder["rule_statuses"]["CON-01"] == "pass"


def test_CW_GEN_03_bovenbegrip_blijft_na_nabewerking():
    """'Handeling die … om …' met context Team Zilver: bovenbegrip en
    grammatica blijven; geen teksthergeneratie als 'oplossing' voor een
    cleanerfout (batch 1)."""
    assert opschonen(OM_ZIN, "controle") == OM_ZIN


@pytest.mark.asyncio
async def test_CW_GEN_04_actieve_prompt_bevat_de_naamuitzondering():
    """Promptopbouw DJI/strafrecht/Sv: de actieve instructie bevat de
    noodzakelijke-naamuitzondering in alle drie bronnen; geen conflict."""
    from services.prompts.prompt_service_v2 import PromptServiceV2

    prompt = (
        await PromptServiceV2().build_generation_prompt(
            _request(
                org=["DJI"], jur=["strafrecht"], wet=["Wetboek van Strafvordering"]
            )
        )
    ).text
    assert "vermeld de registratiecontext niet in de definitiezin" in prompt
    assert "hoort bij het record, niet in de definitiezin" in prompt
    assert "Context impliciet verwerkt: de registratiecontext niet in de zin" in prompt
    assert "zonder expliciete benoeming" not in prompt


@pytest.mark.asyncio
async def test_CON_GT_007_CW_GEN_11_naam_alleen_in_toelichting(tmp_path):
    """Naam alleen in de toelichting: kern en toelichting blijven gescheiden bij
    de domeinreader én de legacy recordreader; CON-01 toetst alleen de kern."""
    from database.definitie_repository import DefinitieRecord
    from database.models import TOELICHTING_SCHEIDING
    from services.definition_repository import DefinitionRepository

    repo = DefinitionRepository(str(tmp_path / "gt007.db"))
    did = repo.legacy_repo.create_definitie(
        DefinitieRecord(
            begrip="controle",
            definitie=f"{NEUTRAAL}{TOELICHTING_SCHEIDING} Team Koper voert dit uit.",
            categorie="proces",
            organisatorische_context='["Team Koper"]',
        )
    )
    domein = repo.get(did)
    assert domein.definitie == NEUTRAAL and "Team Koper" in (domein.toelichting or "")
    record = repo.get_definitie(did)
    assert record.get_definitie_tekst() == NEUTRAAL
    uitkomst = beoordeel_context(
        "controle", record.get_definitie_tekst(), record.get_contextlijsten()
    )
    assert uitkomst.status == "pass" and not uitkomst.naamsignalen


@pytest.mark.asyncio
async def test_CON_GT_009_CW_GEN_08_context_bereikt_de_evaluator(tmp_path):
    """Ingevulde context bereikt de evaluator via de echte transportroute
    (record → orchestrator → evaluator); geen gebruikersomissie en geen
    verzonnen context."""
    from database.definitie_repository import DefinitieRecord
    from services.definition_repository import DefinitionRepository
    from services.orchestrators.validation_orchestrator_v2 import (
        ValidationOrchestratorV2,
    )

    repo = DefinitionRepository(str(tmp_path / "gt009.db"))
    did = repo.legacy_repo.create_definitie(
        DefinitieRecord(
            begrip="controle",
            definitie=KOPER_ZIN,
            categorie="proces",
            organisatorische_context='["Team Koper"]',
        )
    )
    resultaat = await ValidationOrchestratorV2(_validator()).validate_definition(
        repo.get(did)
    )
    detail = _con01(resultaat)
    assert detail["parts"][0]["status"] == "pass"  # D1: context aanwezig
    assert any(p.get("evidence") == "Team Koper" for p in detail["parts"])  # D2 gezien


@pytest.mark.asyncio
async def test_CON_GT_010_CW_GEN_09_naamverlies_geen_behoudbewijs_en_geen_erfenis():
    """Onderscheidende uitgever verwijderd ('kwaliteitskeurmerk' naast
    Koperkeurmerk / 'de organisatie').

    Bewezen binnen de besloten scope: (1) de nabewerking zelf verwijdert de
    noodzakelijke naam niet (bescherming); (2) een kandidaat zonder de naam
    erft de eerdere 'noodzakelijk'-beoordeling niet (vingerafdruk) — geen
    treffer is een D2-deeloordeel met beperkt bereik, geen behoudbewijs.
    Bewijsgrens: of het onderscheid verloren is, is een oordeel van
    ESS-05/INT-03/04 en van de expert; CON-01 blokkeert een naamloze
    kandidaat niet en dit vervolg beslist geen buurregelnorm. Het afwijzen
    van zo'n kandidaat bij betekenisverlies is herstelscope (DEF-638)."""
    # (1) Bescherming door de cleaner: de naam blijft staan.
    assert "Stichting Zilver" in opschonen(ZILVER, "Zilverkeurmerk")
    # (2) Geen erfenis van de eerdere beoordeling.
    context = {"organisatorische_context": ["Stichting Zilver"]}
    met_naam = await _toets("Zilverkeurmerk", ZILVER, context)
    beoordeling = _review(_con01(met_naam), "necessary")
    for tekst in (
        "Kwaliteitskeurmerk dat wordt verleend.",
        "Keurmerk dat de organisatie verleent.",
    ):
        resultaat = await _toets(
            "Zilverkeurmerk", tekst, {**context, "context_review": beoordeling}
        )
        detail = _con01(resultaat)
        assert not [p for p in detail["parts"] if p.get("evidence")]
        assert detail["review"]["applied"] is False  # oude beoordeling telt niet
        assert detail["parts"][0]["id"] == "context_aanwezig"
        assert resultaat["rule_statuses"]["CON-01"] == "pass"  # D2: geen treffer


def test_CON_GT_011_CW_GEN_06_zelfde_begrip_en_context_toont_bestaande_en_drie_keuzes(
    tmp_path,
):
    """Zelfde begrip/volledige context met actieve leidende definitie: de
    checker vindt het record (D3), de drie keuzes blijven (B-09) en een nieuw
    concept archiveert niets (B-10 alleen bij bewuste vaststelling)."""
    from database.definitie_repository import (
        DefinitieRecord,
        DefinitieRepository,
        DefinitieStatus,
    )
    from domain.ontological_categories import OntologischeCategorie
    from integration.definitie_checker import DefinitieChecker

    repo = DefinitieRepository(str(tmp_path / "gt011.db"))
    did = repo.create_definitie(
        DefinitieRecord(
            begrip="keurmerk",
            definitie=NEUTRAAL,
            categorie="type",
            organisatorische_context='["Stichting Zilver"]',
            juridische_context='["privaatrecht"]',
            status=DefinitieStatus.ESTABLISHED.value,
        )
    )
    uitkomst = DefinitieChecker(repo).check_before_generation(
        begrip="keurmerk",
        organisatorische_context='["stichting zilver"]',
        juridische_context='["Privaatrecht"]',
        categorie=OntologischeCategorie.TYPE,
    )
    assert uitkomst.existing_definitie is not None
    assert uitkomst.existing_definitie.id == did
    # Nieuw concept ernaast (bewuste keuze met reden) laat het leidende record staan.
    nieuw = repo.create_definitie(
        DefinitieRecord(
            begrip="keurmerk",
            definitie=ZILVER,
            categorie="type",
            organisatorische_context='["Stichting Zilver"]',
            juridische_context='["privaatrecht"]',
        ),
        allow_duplicate=True,
        duplicate_reason="Casus CON-GT-011: bewust nieuw concept",
    )
    assert repo.get_definitie(did).status == DefinitieStatus.ESTABLISHED.value
    assert repo.get_definitie(nieuw).status == DefinitieStatus.DRAFT.value


@pytest.mark.asyncio
async def test_CON_GT_012_CW_GEN_10_nul_herstelcalls_en_technische_fout_apart(tmp_path):
    """Uitgestelde herstelscope (DEF-638): op de huidige code vindt geen enkele
    herstelcall plaats — ook niet met enhancement aan — bij een open
    naamfunctie én bij een technische evaluatorfout; beide blijven apart
    herkenbaar en vragen handmatige opvolging."""
    # Proefgrond: begrip 'dossiercheck' staat niet letterlijk in de zin, zodat
    # de generieke circulariteitsheuristiek (geen CON-01) de geïsoleerde
    # CON-proef niet vertroebelt; de gemengde-regelroute is apart bewezen.
    # Twee generaties van hetzelfde begrip/context in één opslag zouden
    # terecht op de duplicaatgrens (B-03) stuiten; daarom elk geval zijn eigen
    # tijdelijke repository — de gedeelde enhancement-teller is de proef.
    enhancement = SimpleNamespace(enhance_definition=AsyncMock(return_value="x"))
    (tmp_path / "open").mkdir()
    (tmp_path / "storing").mkdir()
    orch_open, provider_open, _ = _orchestrator(
        tmp_path / "open", KOPER_ZIN, enhancement=enhancement, alleen_con01=True
    )
    open_ = await orch_open.create_definition(
        _request(begrip="dossiercheck", org=["Team Koper"])
    )
    assert open_.success is True, open_.error
    assert open_.validation_result["rule_statuses"]["CON-01"] == "review_required"

    orch_storing, provider_storing, _ = _orchestrator(
        tmp_path / "storing", KOPER_ZIN, enhancement=enhancement, alleen_con01=True
    )
    with patch(
        "services.validation.evaluators.context_metadata."
        "ContextMetadataEvaluator.evaluate",
        side_effect=RuntimeError("synthetische storing"),
    ):
        storing = await orch_storing.create_definition(
            _request(begrip="dossiercheck", org=["Team Koper"])
        )
    assert storing.success is True, storing.error
    assert storing.validation_result["rule_statuses"]["CON-01"] == "error"
    enhancement.enhance_definition.assert_not_called()
    # Twee generaties (elk één modelaanroep), nul herstelcalls.
    assert len(provider_open.oproepen) == 1 and len(provider_storing.oproepen) == 1


@pytest.mark.asyncio
async def test_CON_GT_013_alle_automatische_controles_groen_blijft_concept(tmp_path):
    """Alle actieve automatische controles groen vervangen geen expert: het
    concept blijft concept; vaststellen is een handmatige actie.

    Bewijsgrens (echte evaluator): de proefset is de echte CON-01-evaluator
    met de overige regels buiten de set en een begrip dat de generieke
    heuristieken niet raakt. 'Groen' is hier: elke actieve regel pass en geen
    violations. De gate is dan dicht — uitsluitend door onbeschikbare scores
    (totaalscore en categoriescores zonder cijfer), niet door een gefaalde
    controle. Dit is géén claim dat alle 53 regels groen zijn."""
    orch, provider, repo = _orchestrator(tmp_path, NEUTRAAL, alleen_con01=True)
    antwoord = await orch.create_definition(
        _request(begrip="dossiercheck", org=["Team Koper"])
    )
    validatie = antwoord.validation_result
    assert validatie["rule_statuses"] and set(validatie["rule_statuses"].values()) == {
        "pass"
    }
    assert validatie["violations"] == []
    gefaald = validatie["acceptance_gate"]["gates_failed"]
    assert "overall_score_unavailable" in gefaald
    assert all(g.endswith("_unavailable") for g in gefaald), gefaald
    rij = repo.legacy_repo.get_definitie(antwoord.definition.id)
    assert rij.status == "draft"


@pytest.mark.asyncio
async def test_CON_GT_013_volledig_positieve_automatische_toetsing_maakt_niet_vastgesteld(
    tmp_path,
):
    """Gecontroleerd all-green antwoord aan de orchestratorgrens (vervanger
    voor de validatieservice, apart van de echte-evaluatorproef hierboven):
    ook een volledig positieve automatische beoordeling (is_acceptable True,
    alles pass, gate open) maakt de status nooit 'vastgesteld' — het concept
    wordt als concept opgeslagen en vaststellen blijft een handmatige actie."""
    orch, provider, repo = _orchestrator(tmp_path, NEUTRAAL)
    positief = {
        "version": "1.3.0",
        "overall_score": 1.0,
        "is_acceptable": True,
        "violations": [],
        "passed_rules": ["CON-01", "ARAI-01"],
        "rule_statuses": {"CON-01": "pass", "ARAI-01": "pass"},
        "rule_results": {},
        "detailed_scores": {},
        "acceptance_gate": {"acceptable": True, "gates_failed": []},
        "system": {},
        "validation_status": "validated",
    }
    orch._validation_service = SimpleNamespace(
        validate_definition=AsyncMock(return_value=positief)
    )

    antwoord = await orch.create_definition(
        _request(begrip="dossiercheck", org=["Team Koper"])
    )

    assert antwoord.success is True, antwoord.error
    assert antwoord.validation_result["is_acceptable"] is True
    rij = repo.legacy_repo.get_definitie(antwoord.definition.id)
    assert rij.status == "draft"
    assert rij.approved_by is None


@pytest.mark.asyncio
async def test_CON_GT_014_gewijzigde_kern_maakt_oude_naambeoordeling_niet_actueel():
    """Kern of context gewijzigd na een naambeoordeling: het oude oordeel is
    geen actuele toestemming (vingerafdruk); opnieuw beoordelen."""
    context = {"organisatorische_context": ["Stichting Zilver"]}
    eerste = await _toets("Zilverkeurmerk", ZILVER, context)
    context["context_review"] = _review(_con01(eerste), "necessary")
    assert (await _toets("Zilverkeurmerk", ZILVER, context))["rule_statuses"][
        "CON-01"
    ] == "pass"
    gewijzigd = await _toets("Zilverkeurmerk", ZILVER + " Aan leden.", context)
    assert gewijzigd["rule_statuses"]["CON-01"] == "review_required"
    andere_context = {
        **context,
        "organisatorische_context": ["Stichting Zilver", "Stichting Goud"],
    }
    assert (await _toets("Zilverkeurmerk", ZILVER, andere_context))["rule_statuses"][
        "CON-01"
    ] == "review_required"
