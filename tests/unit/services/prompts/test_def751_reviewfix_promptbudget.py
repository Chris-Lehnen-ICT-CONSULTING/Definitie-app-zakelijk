"""DEF-751 stap 2, reviewcorrecties 1 en 2 (Codex, head db027b894): promptbudget.

1. De verduidelijking mag nooit stil worden afgekapt en toch als toegepast
   geregistreerd: binnen het contextblok krijgt zij voorrang (eigen budget,
   ná escaping), documentinhoud wijkt; een te lang antwoord wordt vóór de
   modelaanroep zichtbaar geweigerd, en het antwoord gaat niet verloren.
2. Het budget wordt ná escaping bewaakt: het contextblok blijft ≤ 20K ná
   escaping, en de harde promptkap kapt niet meer stil af maar weigert
   expliciet (`PromptTeLangError`) vóór het model — norm- en uitvoersecties
   blijven altijd volledig. Werkelijke grensproef zonder mock-truncatie:
   een extreem lange contextlijst duwt de echte prompt over de kap.

Echte SecurityService en PromptServiceV2; het model is een fake (geen netwerk).
"""

from __future__ import annotations

import re
from unittest.mock import AsyncMock, MagicMock

import pytest

from services.interfaces import (
    AIGenerationResult,
    CleaningResult,
    GenerationRequest,
    OrchestratorConfig,
)
from services.modelantwoord import CONFLICT_SENTINEL
from services.orchestrators.definition_orchestrator_v2 import DefinitionOrchestratorV2
from services.prompts.modular_prompt_adapter import PromptTeLangError
from services.prompts.modules.context_awareness_module import (
    MAX_VERDUIDELIJKING_LEN,
    VERDUIDELIJKING_KOP,
    verduidelijking_datalijn,
)
from services.prompts.prompt_service_v2 import PromptServiceV2
from services.security_service import SecurityService
from toetsregels.rule_cache import get_rule_cache

pytestmark = [pytest.mark.unit, pytest.mark.asyncio]

EINDINSTRUCTIE = "in één enkele zin, zonder toelichting"
MARKER = "BEDOELD_IS_PROCES"
MAX_CONTEXTBLOK = 20_000


@pytest.fixture(autouse=True)
def _verse_regelcache():
    get_rule_cache().clear_cache()


def _request(**extra) -> GenerationRequest:
    basis = {
        "id": "def751-reviewfix",
        "begrip": "registratie",
        "ontologische_categorie": "proces",
        "organisatorische_context": ["Organisatie A"],
        "actor": "test",
    }
    return GenerationRequest(**{**basis, **extra})


async def _prompt(request: GenerationRequest) -> str:
    gesaniteerd = await SecurityService().sanitize_request(request)
    return (await PromptServiceV2().build_generation_prompt(gesaniteerd)).text


def _contextblok(prompt: str) -> str:
    blokken = re.findall(r"<context>(.*?)</context>", prompt, flags=re.DOTALL)
    assert len(blokken) == 1
    return blokken[0]


def _staart_intact(prompt: str) -> None:
    assert prompt.count(CONFLICT_SENTINEL) == 1
    assert EINDINSTRUCTIE in prompt
    assert "meld die opnieuw" in prompt
    assert "🆔 Promptmetadata:" in prompt


class Keten:
    """Echte SecurityService + PromptServiceV2 + orchestrator; fake model/repo."""

    def __init__(self, monkeypatch) -> None:
        from voorbeelden import unified_voorbeelden

        monkeypatch.setattr(
            unified_voorbeelden,
            "genereer_alle_voorbeelden_async",
            AsyncMock(return_value={}),
        )
        self.ai = AsyncMock()
        self.ai.generate_definition.return_value = AIGenerationResult(
            text="Een registratie is een vastlegging",
            model="fake",
            tokens_used=1,
            generation_time=0.0,
        )
        cleaning = AsyncMock()

        async def _clean(text: str, term: str) -> CleaningResult:
            return CleaningResult(
                original_text=text, cleaned_text=text, was_cleaned=False
            )

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
        self.repo = MagicMock()
        self.repo.save.return_value = 1
        self.repo.save_failed_attempt = AsyncMock()
        self.orch = DefinitionOrchestratorV2(
            prompt_service=PromptServiceV2(),
            ai_service=self.ai,
            validation_service=validation,
            cleaning_service=cleaning,
            repository=self.repo,
            security_service=SecurityService(),
            config=OrchestratorConfig(
                enable_feedback_loop=False, enable_enhancement=False
            ),
        )

    def geen_model_geen_opslag(self) -> None:
        assert not self.ai.generate_definition.called, "model aangeroepen"
        assert not self.repo.save.called, "opgeslagen"


# ------------------------------------------------------------- bevinding 1


async def test_verduidelijking_binnen_budget_staat_volledig_in_het_contextblok():
    """Reviewrepro met een antwoord binnen het antwoordbudget: documentinhoud
    (10K) + antwoord (~3,8K) > 20K; het antwoord wint, het document wijkt."""
    verduidelijking = ("a " * 1900) + MARKER
    prompt = await _prompt(
        _request(document_context="d " * 5000, betekenisverduidelijking=verduidelijking)
    )
    blok = _contextblok(prompt)
    assert len(blok) <= MAX_CONTEXTBLOK
    assert f"{VERDUIDELIJKING_KOP}: {verduidelijking}" in blok
    assert blok.rstrip().endswith(MARKER)
    assert "d d d" in blok  # het document is er nog, alleen ingekort
    _staart_intact(prompt)


async def test_te_lange_verduidelijking_wordt_voor_de_modelaanroep_geweigerd(
    monkeypatch,
):
    """Reviewrepro 1 exact: ("a " * 4990) + marker, echte securityservice."""
    keten = Keten(monkeypatch)
    response = await keten.orch.create_definition(
        _request(
            document_context="d " * 5000,
            betekenisverduidelijking=("a " * 4990) + MARKER,
        )
    )
    assert response.success is False and response.definition is None
    assert response.metadata["error_type"] == "verduidelijking_te_lang"
    assert response.metadata["max_lengte"] == MAX_VERDUIDELIJKING_LEN
    assert response.metadata.get("betekenisverduidelijking_gebruikt") is not True
    assert str(MAX_VERDUIDELIJKING_LEN) in (response.error or "")
    assert MARKER not in (response.error or "")  # het antwoord zelf reist niet mee
    keten.geen_model_geen_opslag()


async def test_gebruikt_wordt_alleen_geregistreerd_als_de_prompt_het_antwoord_draagt(
    monkeypatch,
):
    """Postconditie vóór het model: ontbreekt de volledige datalijn in de
    gebouwde prompt, dan wordt niet gegenereerd (en dus niets als toegepast
    geregistreerd). Bewezen met een promptservice die het antwoord laat vallen."""
    keten = Keten(monkeypatch)
    echte = keten.orch.prompt_service

    async def zonder_antwoord(request, **kwargs):
        kaal = GenerationRequest(
            **{**request.__dict__, "betekenisverduidelijking": None}
        )
        return await echte.build_generation_prompt(kaal, **kwargs)

    keten.orch._prompt_service = MagicMock(build_generation_prompt=zonder_antwoord)
    response = await keten.orch.create_definition(
        _request(betekenisverduidelijking="Bedoeld is de handeling " + MARKER)
    )
    assert response.success is False
    assert response.metadata["error_type"] == "verduidelijking_niet_in_prompt"
    assert MARKER not in (response.error or "")
    keten.geen_model_geen_opslag()


async def test_verduidelijking_binnen_budget_wordt_wel_gebruikt_en_geregistreerd(
    monkeypatch,
):
    keten = Keten(monkeypatch)
    verduidelijking = "Bedoeld is de handeling & niet het gegeven " + MARKER
    response = await keten.orch.create_definition(
        _request(document_context="d " * 5000, betekenisverduidelijking=verduidelijking)
    )
    assert response.success is True
    assert response.metadata["betekenisverduidelijking_gebruikt"] is True
    prompt = keten.ai.generate_definition.await_args.kwargs["prompt"]
    blok = _contextblok(prompt)
    # De securityservice escapet zelf al (`&` → `&amp;`); de datalijn wordt
    # dus op de gesaniteerde waarde bepaald — precies wat de orchestrator toetst.
    gesaniteerd = SecurityService()._sanitize_text(verduidelijking)
    assert verduidelijking_datalijn(gesaniteerd) in blok
    assert blok.rstrip().endswith(MARKER)
    assert response.definition.metadata["betekenisverduidelijking"] == gesaniteerd


# ------------------------------------------------------------- bevinding 2


async def test_contextblok_budget_geldt_na_escaping_en_staart_blijft():
    """Reviewrepro 2: document en verduidelijking elk 2000× '&' (×5 na
    escaping), categorie type. Geen stille afkap: blok ≤ 20K ná escaping,
    contract en eindinstructie volledig aanwezig."""
    prompt = await _prompt(
        _request(
            ontologische_categorie="type",
            document_context="&" * 2000,
            betekenisverduidelijking="&" * 2000,
        )
    )
    blok = _contextblok(prompt)
    assert len(blok) <= MAX_CONTEXTBLOK
    assert "&amp;" in blok and "&&" not in blok
    # Het antwoord (2000× '&' → securityservice `&amp;` → promptescaping
    # `&amp;amp;`, 18K) past in het blokbudget en staat volledig achteraan;
    # de documentinhoud krijgt het restant.
    assert blok.rstrip().endswith("&amp;amp;" * 2000)
    assert "document: " in blok
    _staart_intact(prompt)


async def test_document_alleen_wordt_na_escaping_op_het_blokbudget_gehouden():
    prompt = await _prompt(_request(document_context="&" * 30_000))
    blok = _contextblok(prompt)
    assert len(blok) <= MAX_CONTEXTBLOK
    assert "&amp;" in blok
    _staart_intact(prompt)


async def test_verduidelijkingsbudget_geldt_na_escaping(monkeypatch):
    """2000× '&' is 2000 tekens rauw maar 10K ná escaping: boven het antwoord-
    budget, dus geweigerd vóór het model (geen stille afkap)."""
    keten = Keten(monkeypatch)
    response = await keten.orch.create_definition(
        _request(
            ontologische_categorie="type",
            document_context="&" * 2000,
            betekenisverduidelijking="&" * 2000,
        )
    )
    assert response.metadata["error_type"] == "verduidelijking_te_lang"
    keten.geen_model_geen_opslag()


def _reuze_context() -> list[str]:
    # 500 unieke contextwaarden van ~120 tekens: de promptmetadata en het
    # datablok herhalen ze; de echte prompt komt ruim boven de kap.
    return [f"Organisatie {i:04d} " + ("x" * 100) for i in range(500)]


async def test_te_lange_prompt_wordt_expliciet_geweigerd_niet_stil_afgekapt():
    with pytest.raises(PromptTeLangError) as excinfo:
        await _prompt(_request(organisatorische_context=_reuze_context()))
    assert excinfo.value.lengte > excinfo.value.maximum


async def test_orchestrator_weigert_te_lange_prompt_voor_de_modelaanroep(monkeypatch):
    keten = Keten(monkeypatch)
    response = await keten.orch.create_definition(
        _request(organisatorische_context=_reuze_context())
    )
    assert response.success is False
    assert response.metadata["error_type"] == "prompt_te_lang"
    assert response.metadata["lengte"] > response.metadata["maximum"]
    keten.geen_model_geen_opslag()


async def test_normale_rijke_prompt_past_ruim_binnen_de_kap_met_vol_contextblok():
    """Zonder mocks: drie contexttypen, categorie type, vol contextblok (ná
    escaping 20K) en een antwoord op het budget — geen weigering, staart heel."""
    prompt = await _prompt(
        _request(
            ontologische_categorie="type",
            organisatorische_context=["DJI", "Openbaar Ministerie"],
            juridische_context=["strafrecht", "bestuursrecht"],
            wettelijke_basis=["Wetboek van Strafvordering"],
            document_context="<" * 30_000,
            betekenisverduidelijking="b" * MAX_VERDUIDELIJKING_LEN,
        )
    )
    assert len(_contextblok(prompt)) <= MAX_CONTEXTBLOK
    assert ("b" * MAX_VERDUIDELIJKING_LEN) in _contextblok(prompt)
    _staart_intact(prompt)
