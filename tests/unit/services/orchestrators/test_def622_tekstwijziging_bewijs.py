"""DEF-622 besluit tekstvergelijking — het bewijs reist mee vanaf de generatie.

Op de echte `DefinitionOrchestratorV2` (harnas uit `test_def622_generatiegrens`):
de geëxtraheerde definitiekern vóór nabewerking, de uiteindelijke tekst en de
wijzigingsvlag komen in de definitiemetadata, worden via de bestaande
`generation_prompt_data` per record bewaard (geen schemawijziging), komen bij
readback terug en bereiken de UI-adapter (`ServiceAdapter.to_ui_response`).
Het al opgeschoonde `definitie_origineel` is géén vóórtekst.
"""

from __future__ import annotations

import pytest

from tests.unit.services.orchestrators.test_def622_generatiegrens import (
    NEUTRAAL,
    _orchestrator,
    _request,
)

pytestmark = [pytest.mark.unit, pytest.mark.asyncio]

RUW_GPT = "Ontologische categorie: type\nde controle die op dossiers wordt uitgevoerd"
KERN_RUW = "de controle die op dossiers wordt uitgevoerd"
EIND = "Controle die op dossiers wordt uitgevoerd."


@pytest.fixture(autouse=True)
def _geen_voorbeelden(monkeypatch):
    from voorbeelden import unified_voorbeelden

    async def _leeg(*_a, **_k):
        return {}

    monkeypatch.setattr(unified_voorbeelden, "genereer_alle_voorbeelden_async", _leeg)


async def test_kern_voor_nabewerking_eindtekst_en_vlag_in_metadata(tmp_path):
    orch, provider, repo = _orchestrator(tmp_path, RUW_GPT)

    antwoord = await orch.create_definition(_request(org=["Team Koper"]))

    assert antwoord.success is True, antwoord.error
    meta = antwoord.definition.metadata
    # De echte kern vóór nabewerking: alleen de GPT-kop is eraf, niets gewist.
    assert meta["definitie_kern_geextraheerd"] == KERN_RUW
    assert meta["definitie_eindtekst"] == EIND == antwoord.definition.definitie
    assert meta["tekst_na_generatie_aangepast"] is True
    # Het bestaande, al opgeschoonde 'origineel' is niet de vóórtekst.
    assert meta["definitie_origineel"] == EIND
    assert meta["definitie_origineel"] != meta["definitie_kern_geextraheerd"]


async def test_ongewijzigde_tekst_draagt_vlag_false(tmp_path):
    orch, provider, repo = _orchestrator(tmp_path, NEUTRAAL + ".")

    antwoord = await orch.create_definition(_request(org=["Team Koper"]))

    meta = antwoord.definition.metadata
    assert meta["definitie_kern_geextraheerd"] == NEUTRAAL + "."
    assert (
        meta["definitie_eindtekst"] == NEUTRAAL + "." == antwoord.definition.definitie
    )
    assert meta["tekst_na_generatie_aangepast"] is False


async def test_bewijs_wordt_per_record_bewaard_en_teruggelezen(tmp_path):
    """Readback via de bestaande generation_prompt_data (geen schemawijziging);
    een record zonder dat bewijs (historisch) blijft eerlijk zonder vóórtekst."""
    orch, provider, repo = _orchestrator(tmp_path, RUW_GPT)
    antwoord = await orch.create_definition(_request(org=["Team Koper"]))

    gelezen = repo.get(antwoord.definition.id)
    bewijs = gelezen.metadata["generation_prompt_data"]
    assert bewijs["definitie_kern_geextraheerd"] == KERN_RUW
    assert bewijs["definitie_eindtekst"] == EIND
    assert bewijs["tekst_na_generatie_aangepast"] is True
    assert bewijs["prompt"]  # de bestaande promptregistratie blijft

    # Historisch record (eigen begrip, zodat de duplicaatgrens niet in beeld
    # komt): geen bewijsvelden, geen verzonnen vóórtekst.
    from database.definitie_repository import DefinitieRecord

    historisch = repo.legacy_repo.create_definitie(
        DefinitieRecord(
            begrip="waarmerk",
            definitie="Historische definitie.",
            categorie="type",
            organisatorische_context='["Team Koper"]',
        )
    )
    oud = repo.get(historisch)
    # DEF-770: de registratie draagt nu altijd de INT-01-uitkomst, maar geen
    # generatiebewijs en dus geen vóórtekst.
    from ui.components.tekstwijziging import tekstwijziging_uit_bewijs

    registratie = oud.metadata.get("generation_prompt_data") or {}
    assert set(registratie) <= {"int01_beoordeling", "int01_beoordeling_history"}
    assert tekstwijziging_uit_bewijs(registratie, "Historische definitie.") is None


async def test_adapter_geeft_het_bewijs_door_aan_de_ui(tmp_path):
    from unittest.mock import MagicMock

    from services.container import ServiceContainer
    from services.service_factory import ServiceAdapter

    orch, provider, repo = _orchestrator(tmp_path, RUW_GPT)
    antwoord = await orch.create_definition(_request(org=["Team Koper"]))

    container = MagicMock(spec=ServiceContainer)
    container.orchestrator.return_value = MagicMock()
    container.web_lookup.return_value = MagicMock()
    ui = ServiceAdapter(container).to_ui_response(antwoord)

    assert ui["definitie_gecorrigeerd"] == EIND
    assert ui["metadata"]["definitie_kern_geextraheerd"] == KERN_RUW
    assert ui["metadata"]["definitie_eindtekst"] == EIND
    assert ui["metadata"]["tekst_na_generatie_aangepast"] is True
