"""DEF-620 — het bronnenblok staat vóór de definitieopdracht, niet als bijlage achteraan.

Alleen de positie verandert: de inhoud van het blok en de kwitantie (DEF-743)
blijven gelijk. Zonder opdrachtkop (onverwachte promptvorm) blijft het oude
gedrag: achteraan.
"""

from __future__ import annotations

import uuid
from copy import deepcopy

import pytest

from services.interfaces import GenerationRequest
from services.prompts import prompt_service_v2 as psv2
from services.prompts.modules.definition_task_module import (
    OPDRACHT_KOP,
    DefinitionTaskModule,
)
from services.prompts.prompt_service_v2 import PromptServiceV2

pytestmark = [pytest.mark.unit]

SLOT = "✏️ Geef nu de definitie van het begrip **onttrekking** in één enkele zin."

WEB = {
    "provider": "overheid",
    "source_label": "Overheid.nl",
    "title": "Regeling melding bijzondere voorvallen jeugdigen, art. 1",
    "url": "https://repository.officiele-overheidspublicaties.nl/bwb/BWBR0012739",
    "snippet": (
        "ontvluchting: onttrekking van een jeugdige aan het op hem uitgeoefende "
        "toezicht vanuit een gesloten gebouw"
    ),
    "score": 1.0,
    "used_in_prompt": True,
    "retrieved_at": "2026-10-04",
    "legal": {},
}


class _Bouwer:
    def __init__(self, tekst: str):
        self.tekst = tekst

    def build_prompt(self, begrip, context):
        return self.tekst


MET_KOP = (
    "REGELS\n\n#### BRONNEN INSTRUCTIE (CON-02):\nuitleg\n\n"
    f"{OPDRACHT_KOP}\nFormuleer nu de definitie.\n\nCONSTRUCTIE\n\n{SLOT}\n\nMETADATA"
)
ZONDER_KOP = f"REGELS\n\n{SLOT}\n\nMETADATA"


def _service(monkeypatch, tekst: str) -> PromptServiceV2:
    def _cfg():
        return {
            "web_lookup": {
                "prompt_augmentation": {
                    "enabled": True,
                    "max_snippets": 5,
                    "max_tokens_per_snippet": 300,
                    "total_token_budget": 1500,
                    "prioritize_juridical": True,
                }
            }
        }

    monkeypatch.setattr(psv2, "load_web_lookup_config", _cfg)
    svc = PromptServiceV2()
    svc.prompt_generator = _Bouwer(tekst)
    return svc


def _request() -> GenerationRequest:
    return GenerationRequest(
        id=str(uuid.uuid4()), begrip="onttrekking", ontologische_categorie="proces"
    )


def _context(web=None) -> dict:
    return {"web_lookup": {"sources": deepcopy(web or []), "top_k": len(web or [])}}


def _blok(tekst: str) -> str:
    begin = tekst.index("<bronnen>\n")
    eind = tekst.index("</bronnen>", begin) + len("</bronnen>")
    return tekst[begin:eind]


@pytest.mark.asyncio
async def test_bronnenblok_staat_voor_de_opdracht_en_voor_de_slotzin(monkeypatch):
    svc = _service(monkeypatch, MET_KOP)
    res = await svc.build_generation_prompt(_request(), context=_context([WEB]))

    tekst = res.text
    blok = tekst.index("<bronnen>\n")
    assert blok < tekst.index(OPDRACHT_KOP)
    assert blok < tekst.index(SLOT)
    assert tekst.index("#### BRONNEN INSTRUCTIE") < blok
    assert not tekst.rstrip().endswith("</bronnen>")


@pytest.mark.asyncio
async def test_inhoud_en_kwitantie_veranderen_niet_alleen_de_positie(monkeypatch):
    voor = await _service(monkeypatch, MET_KOP).build_generation_prompt(
        _request(), context=_context([WEB])
    )
    achter = await _service(monkeypatch, ZONDER_KOP).build_generation_prompt(
        _request(), context=_context([WEB])
    )

    assert _blok(voor.text) == _blok(achter.text)
    kw_voor = voor.metadata["source_receipt"]
    kw_achter = achter.metadata["source_receipt"]
    assert kw_voor["sources"] == kw_achter["sources"]
    assert kw_voor["channels"] == kw_achter["channels"]
    assert len(kw_voor["sources"]) == 1


@pytest.mark.asyncio
async def test_zonder_opdrachtkop_blijft_het_blok_achteraan(monkeypatch):
    svc = _service(monkeypatch, ZONDER_KOP)
    res = await svc.build_generation_prompt(_request(), context=_context([WEB]))

    assert res.text.startswith(ZONDER_KOP)
    assert res.text.rstrip().endswith("</bronnen>")


@pytest.mark.asyncio
async def test_zonder_bronnen_verandert_de_prompt_niet(monkeypatch):
    svc = _service(monkeypatch, MET_KOP)
    res = await svc.build_generation_prompt(_request(), context=_context([]))

    assert res.text == MET_KOP


def test_instructie_kondigt_bronnen_voor_de_opdracht_aan():
    tekst = DefinitionTaskModule()._build_bronnen_instructie()

    assert "direct vóór de definitieopdracht" in tekst
    assert "na de opdracht" not in tekst
    assert "Baseer de definitie zoveel mogelijk op de passende passages" in tekst


def test_opdrachtkop_is_de_gedeelde_constante():
    opdracht = DefinitionTaskModule()._build_task_assignment("onttrekking")

    assert opdracht.startswith(OPDRACHT_KOP + "\n")
