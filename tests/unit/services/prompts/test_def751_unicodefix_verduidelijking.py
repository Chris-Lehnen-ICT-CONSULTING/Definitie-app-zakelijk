"""DEF-751 stap 2, Unicode-correctie op bevinding 1 (Codex-delta-review, head 88dbd0c87).

NFKC-normalisatie kan tekst langer maken (ligatuur `ﬁ` U+FB01 → `fi`,
fullwidth tekens, `ﷺ` U+FDFA → 18 tekens). De sanitizer kapt af op de
genormaliseerde tekst; wie het budget of de controletekst op de lengte vóór
normalisatie baseert, kapt stil af en vergelijkt daarna een even ver
afgekapte controletekst — de volledigheidspostconditie accepteerde zo een
onvolledig antwoord. Hier: budgetten en controletekst op de volledig
genormaliseerde/geëscapete tekst; het antwoord staat altijd volledig in het
contextblok of wordt zichtbaar geweigerd. Geen ligatuur-special-case: elke
NFKC-expansie, willekeurige positie.

Actief: echte SecurityService, PromptServiceV2, orchestrator, fake model, en
een tijdelijke SQLite-readback via de echte handlerketen.
"""

from __future__ import annotations

import asyncio
import re
import unicodedata
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from database.definitie_repository import DefinitieRepository
from services.interfaces import (
    AIGenerationResult,
    CleaningResult,
    GenerationRequest,
    OrchestratorConfig,
)
from services.orchestrators.definition_orchestrator_v2 import DefinitionOrchestratorV2
from services.prompts.modules.context_awareness_module import (
    MAX_VERDUIDELIJKING_LEN,
    VERDUIDELIJKING_KOP,
    verduidelijking_datalijn,
    verduidelijking_te_lang,
)
from services.prompts.prompt_service_v2 import PromptServiceV2
from services.security_service import SecurityService
from services.service_factory import ServiceAdapter
from tests.unit.ui.handlers.test_def751_betekenisconflict_handler import FakeSM
from tests.unit.ui.test_def751_verduidelijking_keten import (
    CONTEXT as KETEN_CONTEXT,
    FakeModel,
    _keten,
)
from toetsregels.rule_cache import get_rule_cache
from ui.helpers.betekenisconflict import KEY_OPEN, verzend_verduidelijking

pytestmark = [pytest.mark.unit, pytest.mark.asyncio]

MARKER = "BEDOELD_IS_PROCES"
LIGATUUR = "ﬁ"  # ﬁ → "fi" (×2)
FULLWIDTH = "Ａ"  # Ａ → "A" (×1, ander teken)
SALLALLAHU = "ﷺ"  # ﷺ → 18 tekens
MAX_CONTEXTBLOK = 20_000


@pytest.fixture(autouse=True)
def _verse_regelcache():
    get_rule_cache().clear_cache()


def _nfkc(tekst: str) -> str:
    return unicodedata.normalize("NFKC", tekst)


def _request(**extra) -> GenerationRequest:
    basis = {
        "id": "def751-unicode",
        "begrip": "registratie",
        "ontologische_categorie": "type",
        "organisatorische_context": ["DJI", "Openbaar Ministerie"],
        "juridische_context": ["strafrecht", "bestuursrecht"],
        "wettelijke_basis": ["Wetboek van Strafvordering"],
        "document_context": "document",
        "actor": "test",
    }
    return GenerationRequest(**{**basis, **extra})


def _contextblok(prompt: str) -> str:
    blokken = re.findall(r"<context>(.*?)</context>", prompt, flags=re.DOTALL)
    assert len(blokken) == 1
    return blokken[0]


# ------------------------------------------------- eenheid: sanitizer-helper


def test_normaliseer_prompt_tekst_is_nfkc_en_geen_sanitisatie():
    from services.prompts.sanitization import normaliseer_prompt_tekst

    assert normaliseer_prompt_tekst(LIGATUUR) == "fi"
    assert len(normaliseer_prompt_tekst(SALLALLAHU)) == 18
    assert normaliseer_prompt_tekst("＜x＞") == "<x>"  # lookalikes → ASCII
    # Geen escaping: dat blijft aan de sanitize-functies (en `datablok` weigert het).
    assert "<" in normaliseer_prompt_tekst("<context>")


# ------------------------------------------------------- eenheid: datalijn


@pytest.mark.parametrize(
    "antwoord",
    [
        (LIGATUUR * 100) + " " + MARKER,  # reviewrepro: 118 tekens → 218 na NFKC
        MARKER + " " + (LIGATUUR * 100),  # expansie aan het einde
        (SALLALLAHU * 50) + " midden " + (LIGATUUR * 50) + " " + MARKER,
        (FULLWIDTH * 300) + " " + MARKER,
        "gewoon antwoord zonder expansie " + MARKER,
    ],
)
def test_datalijn_is_nooit_afgekapt_ongeacht_nfkc_expansie(antwoord):
    lijn = verduidelijking_datalijn(antwoord)
    verwacht = f"{VERDUIDELIJKING_KOP}: " + " ".join(_nfkc(antwoord).split())
    assert lijn == verwacht
    assert lijn.endswith(MARKER) or MARKER in lijn


def test_antwoordbudget_geldt_op_de_genormaliseerde_tekst():
    # 1999 ligaturen = 1999 tekens rauw, 3998 ná NFKC: past.
    assert not verduidelijking_te_lang(LIGATUUR * 1999)
    # 2001 ligaturen = 2001 tekens rauw, 4002 ná NFKC: te lang.
    assert verduidelijking_te_lang(LIGATUUR * 2001)
    # 250 × ﷺ = 250 tekens rauw, 4500 ná NFKC: te lang.
    assert verduidelijking_te_lang(SALLALLAHU * 250)
    assert not verduidelijking_te_lang("b" * MAX_VERDUIDELIJKING_LEN)
    assert verduidelijking_te_lang("b" * (MAX_VERDUIDELIJKING_LEN + 1))


# ------------------------------------------------ actief: prompt en orchestrator


async def _prompt(request: GenerationRequest) -> str:
    gesaniteerd = await SecurityService().sanitize_request(request)
    return (await PromptServiceV2().build_generation_prompt(gesaniteerd)).text


@pytest.mark.parametrize(
    "antwoord",
    [
        (LIGATUUR * 100) + " " + MARKER,
        (SALLALLAHU * 100) + " " + MARKER,
        MARKER + " " + (LIGATUUR * 1000),
    ],
)
async def test_reviewrepro_antwoord_staat_volledig_in_de_echte_prompt(antwoord):
    prompt = await _prompt(_request(betekenisverduidelijking=antwoord))
    blok = _contextblok(prompt)
    gesaniteerd = SecurityService()._sanitize_text(antwoord)
    lijn = verduidelijking_datalijn(gesaniteerd)
    assert lijn in blok
    assert MARKER in blok
    assert blok.rstrip().endswith(lijn.rstrip())
    assert len(blok) <= MAX_CONTEXTBLOK
    assert "document" in blok  # oorspronkelijke context blijft


async def test_expansie_in_documentcontext_houdt_blok_binnen_budget_en_antwoord_volledig():
    """Ook als het document zelf expandeert (30K ligaturen → 60K ná NFKC), blijft
    het blok ≤ 20K ná normalisatie/escaping en het antwoord volledig."""
    antwoord = (LIGATUUR * 100) + " " + MARKER
    prompt = await _prompt(
        _request(document_context=LIGATUUR * 30_000, betekenisverduidelijking=antwoord)
    )
    blok = _contextblok(prompt)
    assert len(blok) <= MAX_CONTEXTBLOK
    assert blok.rstrip().endswith(
        verduidelijking_datalijn(SecurityService()._sanitize_text(antwoord)).rstrip()
    )
    assert "fifi" in blok  # document (genormaliseerd) is er nog


async def test_reviewrepro_orchestrator_gebruikt_true_alleen_met_volledig_antwoord(
    monkeypatch,
):
    from voorbeelden import unified_voorbeelden

    monkeypatch.setattr(
        unified_voorbeelden,
        "genereer_alle_voorbeelden_async",
        AsyncMock(return_value={}),
    )
    ai = AsyncMock()
    ai.generate_definition.return_value = AIGenerationResult(
        text="Een registratie is een vastlegging",
        model="fake",
        tokens_used=1,
        generation_time=0.0,
    )
    cleaning = AsyncMock()

    async def _clean(text: str, term: str) -> CleaningResult:
        return CleaningResult(original_text=text, cleaned_text=text, was_cleaned=False)

    cleaning.clean_text.side_effect = _clean
    validation = AsyncMock()
    validation.validate_definition.return_value = {
        "version": "1.0.0",
        "overall_score": 0.8,
        "is_acceptable": True,
        "violations": [],
        "passed_rules": [],
        "detailed_scores": {},
        "system": {},
    }
    repo = MagicMock()
    repo.save.return_value = 1
    repo.save_failed_attempt = AsyncMock()
    orch = DefinitionOrchestratorV2(
        prompt_service=PromptServiceV2(),
        ai_service=ai,
        validation_service=validation,
        cleaning_service=cleaning,
        repository=repo,
        security_service=SecurityService(),
        config=OrchestratorConfig(enable_feedback_loop=False, enable_enhancement=False),
    )
    antwoord = (LIGATUUR * 100) + " " + MARKER
    response = await orch.create_definition(_request(betekenisverduidelijking=antwoord))
    assert response.success is True
    assert response.metadata["betekenisverduidelijking_gebruikt"] is True
    prompt = ai.generate_definition.await_args.kwargs["prompt"]
    assert MARKER in prompt
    assert (
        verduidelijking_datalijn(
            response.definition.metadata["betekenisverduidelijking"]
        )
        in prompt
    )


# ------------------------------------------------ actief: handlerketen + SQLite


def test_reviewrepro_sqlite_readback_prompt_bevat_de_keuze(tmp_path, monkeypatch):
    """Handler → adapter → orchestrator → echte PromptServiceV2 → fake model →
    echte repository: na een ligatuur-antwoord bevat de geregistreerde prompt
    de keuze, consistent met de geregistreerde verduidelijking."""
    db_path = str(tmp_path / "unicode.db")
    handler, model = _keten(db_path, monkeypatch)
    antwoord = (LIGATUUR * 100) + " " + MARKER
    # Het fake model definieert zodra de (genormaliseerde) keuze in de prompt staat.
    model_def = FakeModel.generate_definition

    async def _genereer(self, prompt: str, **kwargs):
        if MARKER in prompt:
            return AIGenerationResult(
                text="Een registratie is de handeling van het vastleggen",
                model="fake",
                tokens_used=1,
                generation_time=0.0,
            )
        return await model_def(self, prompt, **kwargs)

    monkeypatch.setattr(FakeModel, "generate_definition", _genereer)
    sm = FakeSM(determined_category="proces", category_reasoning="r")
    with patch(
        "ui.helpers.async_bridge.run_async", lambda coro, **kw: asyncio.run(coro)
    ):
        handler.handle_definition_generation(
            "registratie", KETEN_CONTEXT, _st=MagicMock(), _sm=sm
        )
        assert verzend_verduidelijking(sm, sm.data[KEY_OPEN], antwoord) is None
        handler.handle_definition_generation(
            "registratie", KETEN_CONTEXT, _st=MagicMock(), _sm=sm
        )

    did = sm.data["last_generation_result"]["saved_definition_id"]
    assert did
    registratie = (
        DefinitieRepository(db_path).get_definitie(did).get_generatieregistratie()
    )
    assert MARKER in registratie["betekenisverduidelijking"]
    assert MARKER in registratie["prompt"]
    assert (
        verduidelijking_datalijn(registratie["betekenisverduidelijking"])
        in registratie["prompt"]
    )
