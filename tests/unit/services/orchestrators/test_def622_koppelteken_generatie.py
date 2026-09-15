"""DEF-622 reviewbevinding 1 — samenstelling overleeft de echte generatieroute.

Op de echte `DefinitionOrchestratorV2` (harnas uit `test_def622_generatiegrens`,
echte cleaner, echte regelset, synthetische opslag) met bevroren modeluitvoer
"Controle- en toezichtshandeling …" bij begrip "controle": de opgeslagen en
teruggelezen tekst begint met de volledige samentrekking, en het meegereisde
generatiebewijs laat zien dat de nabewerking het betekenisdeel niet heeft
aangeraakt.
"""

from __future__ import annotations

import pytest

from tests.unit.services.orchestrators.test_def622_generatiegrens import (
    _orchestrator,
    _request,
)

pytestmark = [pytest.mark.unit, pytest.mark.asyncio]

SAMENTREKKING = "Controle- en toezichtshandeling die een bevoegd ambtenaar verricht."
SAMENSTELLING = "Controle-handeling die een bevoegd ambtenaar verricht."


@pytest.fixture(autouse=True)
def _geen_voorbeelden(monkeypatch):
    from voorbeelden import unified_voorbeelden

    async def _leeg(*_a, **_k):
        return {}

    monkeypatch.setattr(unified_voorbeelden, "genereer_alle_voorbeelden_async", _leeg)


@pytest.mark.parametrize(
    "modeltekst", [SAMENTREKKING, SAMENSTELLING], ids=["samentrekking", "samenstelling"]
)
async def test_samenstelling_met_begrip_blijft_heel_tot_en_met_readback(
    tmp_path, modeltekst
):
    orch, provider, repo = _orchestrator(tmp_path, modeltekst)

    antwoord = await orch.create_definition(
        _request(begrip="controle", org=["Team Koper"])
    )

    assert antwoord.definition is not None, antwoord.error
    assert antwoord.definition.definitie == modeltekst
    meta = antwoord.definition.metadata
    assert meta["definitie_kern_geextraheerd"] == modeltekst
    assert meta["definitie_eindtekst"] == modeltekst
    # Niets aangeraakt: geen melding "tekst na generatie aangepast".
    assert meta["tekst_na_generatie_aangepast"] is False

    gelezen = repo.get(antwoord.definition.id)
    assert gelezen.definitie == modeltekst
    assert not gelezen.definitie.lower().startswith(("en ", "handeling "))
