"""De toetsing van de kandidaat loopt gelijktijdig met de voorbeeldengeneratie.

`DefinitionOrchestratorV2.create_definition` genereerde eerst de voorbeelden
(gemeten ±23 s) en toetste daarna de kandidaat (±44 s, CON-02 de traagste).
Beide hangen niet van elkaar af: de voorbeelden krijgen de ruwe modeltekst
en de requestcontext, de toetsing de opgeschoonde kandidaat en de bronset;
de voorbeelden worden pas gebruikt bij het samenstellen van het
Definition-object. Gelijktijdig is de duur het maximum, niet de som, zodat
CON-02 meer van het generatiebudget (120 s) overhoudt.

Alleen de gelijktijdigheid verandert. Deze tests leggen vast dat:

* de duur ≈ het maximum is en beide stappen werkelijk overlappen;
* de uitkomst (definitie, voorbeelden, validatieresultaat, opgeslagen
  record) bij beide afrondvolgordes gelijk is aan een echt sequentiële
  referentie (voorbeelden klaar vóór opschoning en toetsing, als 146c9d1ec),
  en de verwachte inhoud expliciet klopt: voorbeelden per type in de
  response, niet in het door `create_definition` opgeslagen record;
* de voorbeelden — zoals nu — de ruwe modeltekst krijgen, ook als de
  toetsing de kandidaattekst wijzigt;
* een fout in de voorbeelden de generatie niet raakt (lege voorbeelden) en
  een fout in de toetsing dezelfde foutrespons geeft, zonder hangende taak;
* annulering van buitenaf (budget op) beide takken opruimt;
* de generatiedeadline (ContextVar) in beide takken geldt.
"""

from __future__ import annotations

import asyncio
import time
import uuid
from types import SimpleNamespace
from typing import Any

import pytest

from services.cleaning_service import CleaningConfig, CleaningService
from services.definition_repository import DefinitionRepository
from services.interfaces import GenerationRequest, OrchestratorConfig, PromptResult
from services.null_repository import NullDefinitionRepository
from services.orchestrators.definition_orchestrator_v2 import DefinitionOrchestratorV2
from services.orchestrators.validation_orchestrator_v2 import ValidationOrchestratorV2
from services.validation.modular_validation_service import ModularValidationService
from toetsregels.manager import get_toetsregel_manager
from utils.generatie_deadline import generatie_deadline, huidige_generatie_deadline

pytestmark = [pytest.mark.unit, pytest.mark.asyncio]

MODELTEKST = "Controle waarbij wordt vastgesteld of alle vereiste velden zijn ingevuld"
VOORBEELDEN = {
    "voorbeeldzinnen": ["De controle liep."],
    "synoniemen": ["toets"],
    "toelichting": "Uitleg.",
}
DUUR = 1.0


class BevrorenProvider:
    async def generate_definition(self, prompt: str, **kwargs: Any) -> Any:
        return SimpleNamespace(
            text=MODELTEKST, model="bevroren", tokens_used=7, metadata={}
        )


class VastePrompt:
    async def build_generation_prompt(self, request, **kwargs: Any) -> PromptResult:
        return PromptResult(
            text=f"Definieer {request.begrip}",
            token_count=3,
            components_used=("bevroren",),
            feedback_integrated=False,
            optimization_applied=False,
            metadata={},
        )


class Logboek:
    """Tijdlijn van beide takken: start, einde, annulering, deadline, invoer."""

    def __init__(self) -> None:
        self.gebeurtenissen: list[tuple[str, float]] = []
        self.deadlines: dict[str, float | None] = {}
        self.voorbeelden_invoer: list[dict[str, Any]] = []
        self.geannuleerd: set[str] = set()

    def noteer(self, wat: str) -> None:
        self.gebeurtenissen.append((wat, time.monotonic()))

    def tijd(self, wat: str) -> float:
        for w, t in self.gebeurtenissen:
            if w == wat:
                return t
        opgetreden = [w for w, _ in self.gebeurtenissen]
        raise AssertionError(f"{wat!r} niet opgetreden; wel: {opgetreden}")


def _voorbeeldentak(
    monkeypatch,
    logboek: Logboek,
    *,
    duur: float | None,
    fout: Exception | None = None,
) -> None:
    """Bevroren voorbeeldengenerator; ``duur=None`` suspendeert nooit."""
    from voorbeelden import unified_voorbeelden

    async def _genereer(
        begrip: str, definitie: str, context_dict: dict[str, list[str]]
    ) -> dict[str, Any]:
        logboek.noteer("voorbeelden_start")
        logboek.deadlines["voorbeelden"] = huidige_generatie_deadline()
        logboek.voorbeelden_invoer.append(
            {"begrip": begrip, "definitie": definitie, "context": context_dict}
        )
        try:
            if duur is not None:
                await asyncio.sleep(duur)
        except asyncio.CancelledError:
            logboek.geannuleerd.add("voorbeelden")
            raise
        logboek.noteer("voorbeelden_einde")
        if fout is not None:
            raise fout
        return {
            k: (list(v) if isinstance(v, list) else v) for k, v in VOORBEELDEN.items()
        }

    monkeypatch.setattr(
        unified_voorbeelden, "genereer_alle_voorbeelden_async", _genereer
    )


def _orchestrator(
    tmp_path,
    logboek: Logboek,
    *,
    duur: float,
    fout: Exception | None = None,
    wijzig_tekst: str | None = None,
) -> tuple[DefinitionOrchestratorV2, DefinitionRepository]:
    cleaning = CleaningService(CleaningConfig())
    service = ModularValidationService(
        toetsregel_manager=get_toetsregel_manager(),
        repository=NullDefinitionRepository(),
    )
    validatie = ValidationOrchestratorV2(service, cleaning_service=cleaning)
    echt = validatie.validate_definition
    pogingen = {"n": 0}

    async def _toets(definition, context=None, **kwargs: Any) -> Any:
        pogingen["n"] += 1
        logboek.noteer(f"toetsing_start_{pogingen['n']}")
        logboek.deadlines["toetsing"] = huidige_generatie_deadline()
        try:
            await asyncio.sleep(duur)
        except asyncio.CancelledError:
            logboek.geannuleerd.add("toetsing")
            raise
        if fout is not None:
            raise fout
        resultaat = await echt(definition=definition, context=context, **kwargs)
        if wijzig_tekst is not None and pogingen["n"] == 1:
            # De mutatieguard (DEF-622/747): de validatie wijzigt de tekst.
            definition.definitie = wijzig_tekst
        logboek.noteer(f"toetsing_einde_{pogingen['n']}")
        return resultaat

    validatie.validate_definition = _toets  # type: ignore[method-assign]
    repo = DefinitionRepository(str(tmp_path / "generatie.db"))
    orch = DefinitionOrchestratorV2(
        prompt_service=VastePrompt(),
        ai_service=BevrorenProvider(),
        validation_service=validatie,
        cleaning_service=cleaning,
        repository=repo,
        config=OrchestratorConfig(enable_feedback_loop=False, enable_enhancement=False),
    )
    return orch, repo


def _request(
    begrip: str = "controle", request_id: str | None = None
) -> GenerationRequest:
    return GenerationRequest(
        id=request_id or str(uuid.uuid4()),
        begrip=begrip,
        ontologische_categorie="proces",
        organisatorische_context=["Team Toets"],
        juridische_context=["bestuursrecht"],
        wettelijke_basis=["Awb"],
    )


def _andere_taken() -> list[asyncio.Task]:
    huidig = asyncio.current_task()
    return [t for t in asyncio.all_tasks() if t is not huidig and not t.done()]


_TIJDVELDEN = {
    "generation_time",
    "generated_at",
    "duration",
    "created_at",
    "assessed_at",
    "recorded_at",
}


def _zonder_tijd(waarde: Any) -> Any:
    if isinstance(waarde, dict):
        return {k: _zonder_tijd(v) for k, v in waarde.items() if k not in _TIJDVELDEN}
    if isinstance(waarde, list):
        return [_zonder_tijd(v) for v in waarde]
    return waarde


def _uitkomst(response: Any, repo: DefinitionRepository) -> dict[str, Any]:
    definitie = response.definition
    opgeslagen = repo.get(definitie.id)
    return {
        "success": response.success,
        "definitie": definitie.definitie,
        "metadata": _zonder_tijd(dict(definitie.metadata or {})),
        "validatie": _zonder_tijd(response.validation_result),
        "opgeslagen_id": definitie.id,
        "opgeslagen_definitie": opgeslagen.definitie,
        "opgeslagen_categorie": opgeslagen.ontologische_categorie,
        "opgeslagen_metadata": _zonder_tijd(dict(opgeslagen.metadata or {})),
        "opgeslagen_voorbeelden": repo.get_voorbeelden_by_type(definitie.id),
    }


def _controleer_verwachte_inhoud(uitkomst: dict[str, Any]) -> None:
    """De verwachte inhoud, los van elke vergelijking tussen runs.

    Zoals op 146c9d1ec: de response draagt de voorbeelden (per type); het
    record dat `create_definition` opslaat draagt ze niet — de UI bewaart ze
    later uit de response (`voorbeelden_renderer.py`, `examples_block.py`).
    Getoond = opgeslagen geldt voor de definitietekst.
    """
    assert uitkomst["success"]
    voorbeelden = uitkomst["metadata"]["voorbeelden"]
    assert set(voorbeelden) == set(VOORBEELDEN)
    for soort, waarde in VOORBEELDEN.items():
        assert voorbeelden[soort] == waarde, soort
    assert uitkomst["opgeslagen_definitie"] == uitkomst["definitie"]
    assert "voorbeelden" not in uitkomst["opgeslagen_metadata"]
    assert uitkomst["opgeslagen_voorbeelden"] == {}


async def _genereer_run(
    pad, monkeypatch, *, v_duur: float | None, t_duur: float, eager: bool = False
) -> tuple[dict[str, Any], Logboek]:
    """Eén generatie met identieke bevroren invoer (vast request-id), eigen DB."""
    pad.mkdir()
    logboek = Logboek()
    _voorbeeldentak(monkeypatch, logboek, duur=v_duur)
    orch, repo = _orchestrator(pad, logboek, duur=t_duur)
    loop = asyncio.get_running_loop()
    oude_fabriek = loop.get_task_factory()
    if eager:
        loop.set_task_factory(asyncio.eager_task_factory)
    try:
        response = await orch.create_definition(_request(request_id=VAST_ID))
    finally:
        loop.set_task_factory(oude_fabriek)
    return _uitkomst(response, repo), logboek


VAST_ID = "00000000-0000-4000-8000-0000000000aa"


# ------------------------------------------------------------------ duur


async def test_duur_is_maximum_en_takken_overlappen(tmp_path, monkeypatch):
    logboek = Logboek()
    _voorbeeldentak(monkeypatch, logboek, duur=DUUR)
    orch, _ = _orchestrator(tmp_path, logboek, duur=DUUR)

    start = time.monotonic()
    response = await orch.create_definition(_request())
    duur = time.monotonic() - start

    assert response.success
    # Sequentieel ≥ 2 × DUUR; gelijktijdig ≈ DUUR (+ echte validatie/opslag).
    assert duur < 1.5 * DUUR, f"duur {duur:.2f}s is de som, niet het maximum"
    assert logboek.tijd("toetsing_start_1") < logboek.tijd("voorbeelden_einde")
    assert logboek.tijd("voorbeelden_start") < logboek.tijd("toetsing_einde_1")


# ------------------------------------------------------- uitkomst gelijk


async def test_uitkomst_en_opslag_gelijk_aan_sequentiele_referentie(
    tmp_path, monkeypatch
):
    """Parallel (beide afrondvolgordes) == sequentieel (gedrag van 146c9d1ec).

    Referentie: met de eager task factory voert `create_task` de
    voorbeeldentaak meteen uit tot de eerste suspensie. De bevroren
    voorbeeldentak suspendeert niet (`duur=None`), dus de taak is volledig
    klaar vóór `create_task` terugkeert — vóór opschoning en toetsing, precies
    als het oude `voorbeelden = await genereer_alle_voorbeelden_async(...)`.
    """
    referentie, ref_logboek = await _genereer_run(
        tmp_path / "referentie", monkeypatch, v_duur=None, t_duur=0.0, eager=True
    )
    # Echt sequentieel: de voorbeelden waren klaar vóórdat de toetsing begon.
    assert ref_logboek.tijd("voorbeelden_einde") < ref_logboek.tijd("toetsing_start_1")
    _controleer_verwachte_inhoud(referentie)

    for naam, (v_duur, t_duur), voorbeelden_eerst in [
        ("voorbeelden_eerst", (0.1, 0.4), True),
        ("toetsing_eerst", (0.6, 0.0), False),
    ]:
        uitkomst, logboek = await _genereer_run(
            tmp_path / naam, monkeypatch, v_duur=v_duur, t_duur=t_duur
        )
        # Parallel: de toetsing begon vóór de voorbeelden klaar waren, en de
        # afrondvolgorde is de bedoelde.
        assert logboek.tijd("toetsing_start_1") < logboek.tijd("voorbeelden_einde")
        assert (
            logboek.tijd("voorbeelden_einde") < logboek.tijd("toetsing_einde_1")
        ) is voorbeelden_eerst, naam
        _controleer_verwachte_inhoud(uitkomst)
        verschillen = _verschillen(_zonder_ids(referentie), _zonder_ids(uitkomst))
        assert not verschillen, f"{naam}:\n" + "\n".join(verschillen)


def _verschillen(a: Any, b: Any, pad: str = "") -> list[str]:
    """Paden waarop a en b verschillen (leesbaar bij grote geneste dicts)."""
    if isinstance(a, dict) and isinstance(b, dict):
        return [
            p
            for k in sorted(set(a) | set(b), key=str)
            for p in _verschillen(a.get(k), b.get(k), f"{pad}.{k}")
        ]
    if isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        return [
            p
            for i, (x, y) in enumerate(zip(a, b, strict=True))
            for p in _verschillen(x, y, f"{pad}[{i}]")
        ]
    return [] if a == b else [f"{pad}: {a!r} != {b!r}"]


def _zonder_ids(waarde: Any) -> Any:
    if isinstance(waarde, dict):
        return {
            k: _zonder_ids(v)
            for k, v in waarde.items()
            if k
            not in {"generation_id", "correlation_id", "system", "generation_identity"}
        }
    if isinstance(waarde, list):
        return [_zonder_ids(v) for v in waarde]
    return waarde


async def test_voorbeelden_krijgen_ruwe_modeltekst_ook_als_toetsing_wijzigt(
    tmp_path, monkeypatch
):
    """Zoals nu: invoer is de ruwe modeltekst, niet de (gewijzigde) kandidaat."""
    logboek = Logboek()
    _voorbeeldentak(monkeypatch, logboek, duur=0.05)
    gewijzigd = "Gewijzigde kandidaat waarbij velden worden nagelopen"
    orch, _ = _orchestrator(tmp_path, logboek, duur=0.05, wijzig_tekst=gewijzigd)

    response = await orch.create_definition(_request())

    assert response.success
    assert response.definition.definitie == gewijzigd
    assert logboek.voorbeelden_invoer == [
        {
            "begrip": "controle",
            "definitie": MODELTEKST,
            "context": {
                "organisatorisch": ["Team Toets"],
                "juridisch": ["bestuursrecht"],
                "wettelijk": ["Awb"],
            },
        }
    ]
    assert response.definition.metadata["voorbeelden"] == VOORBEELDEN


# ---------------------------------------------------------------- fouten


@pytest.mark.parametrize("v_duur", [0.0, 0.2], ids=["fout_vroeg", "fout_laat"])
async def test_fout_in_voorbeelden_raakt_generatie_niet(tmp_path, monkeypatch, v_duur):
    logboek = Logboek()
    _voorbeeldentak(monkeypatch, logboek, duur=v_duur, fout=RuntimeError("stuk"))
    orch, repo = _orchestrator(tmp_path, logboek, duur=0.1)

    response = await orch.create_definition(_request())

    assert response.success
    assert response.definition.metadata["voorbeelden"] == {}
    assert repo.get(response.definition.id).definitie == response.definition.definitie
    assert _andere_taken() == []


async def test_fout_in_toetsing_geeft_foutrespons_zonder_hangende_taak(
    tmp_path, monkeypatch
):
    logboek = Logboek()
    _voorbeeldentak(monkeypatch, logboek, duur=5.0)
    orch, _ = _orchestrator(tmp_path, logboek, duur=0.05, fout=ValueError("kapot"))

    start = time.monotonic()
    response = await orch.create_definition(_request())

    assert not response.success
    assert response.error == "Generation failed: kapot"
    assert response.metadata["error_type"] == "ValueError"
    # De voorbeelden wachten niet door tot hun eigen einde.
    assert time.monotonic() - start < 1.0
    assert "voorbeelden" in logboek.geannuleerd
    assert _andere_taken() == []


# ------------------------------------------------- annulering en deadline


async def test_annulering_van_buitenaf_ruimt_beide_takken_op(tmp_path, monkeypatch):
    logboek = Logboek()
    _voorbeeldentak(monkeypatch, logboek, duur=5.0)
    orch, _ = _orchestrator(tmp_path, logboek, duur=5.0)

    with pytest.raises(TimeoutError):
        await asyncio.wait_for(orch.create_definition(_request()), timeout=0.2)

    assert logboek.geannuleerd == {"voorbeelden", "toetsing"}
    assert _andere_taken() == []


async def test_annulering_tijdens_wachten_op_voorbeelden(tmp_path, monkeypatch):
    """Toetsing al klaar, budget op terwijl de voorbeelden nog lopen."""
    logboek = Logboek()
    _voorbeeldentak(monkeypatch, logboek, duur=5.0)
    orch, _ = _orchestrator(tmp_path, logboek, duur=0.0)

    with pytest.raises(TimeoutError):
        await asyncio.wait_for(orch.create_definition(_request()), timeout=0.5)

    assert any(w == "toetsing_einde_1" for w, _ in logboek.gebeurtenissen)
    assert logboek.geannuleerd == {"voorbeelden"}
    assert _andere_taken() == []


async def test_generatiedeadline_geldt_in_beide_takken(tmp_path, monkeypatch):
    logboek = Logboek()
    _voorbeeldentak(monkeypatch, logboek, duur=0.05)
    orch, _ = _orchestrator(tmp_path, logboek, duur=0.05)

    with generatie_deadline(120) as deadline:
        response = await orch.create_definition(_request())

    assert response.success
    assert logboek.deadlines == {"voorbeelden": deadline, "toetsing": deadline}
