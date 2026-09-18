"""DEF-751 stap 2 — de staart van de eindprompt overleeft de lengtekap.

De harde afkap (`PromptComponentConfig.max_prompt_length`, toegepast in
`ModularPromptAdapter.build_prompt` vóór het bronnenblok) knipt van achteren:
precies waar de eindinstructie ("in één enkele zin, zonder toelichting") en het
conflictcontract staan. Gemeten 17-09-2026: de rijke prompt (drie context-
typen, categorie type) zat op ~34,8K bij een kap van 35K, zonder document-
inhoud in het contextblok. Deze test bewaakt dat in de rijkste variant (drie
contexttypen, documentcontext, verduidelijking; per categorie) de staart en
het contract intact blijven en dat er niets is afgeknipt.
"""

from __future__ import annotations

import pytest

from services.interfaces import GenerationRequest
from services.modelantwoord import CONFLICT_SENTINEL
from services.prompts.prompt_service_v2 import PromptServiceV2
from toetsregels.rule_cache import get_rule_cache

pytestmark = [pytest.mark.unit]

EINDINSTRUCTIE = "in één enkele zin, zonder toelichting"
PROMPTMETADATA_STAART = "- Wettelijke basis: Wetboek van Strafvordering"


@pytest.fixture(autouse=True)
def _verse_regelcache():
    get_rule_cache().clear_cache()


@pytest.mark.parametrize("categorie", ["type", "proces", "resultaat", "exemplaar"])
@pytest.mark.parametrize("documenttekst", [None, "Awb art. 5:11 toezichthouder " * 700])
async def test_staart_en_conflictcontract_overleven_de_lengtekap(
    categorie, documenttekst
):
    request = GenerationRequest(
        id="def751-lengte",
        begrip="keurmerkregistratieprocedure",
        ontologische_categorie=categorie,
        organisatorische_context=["DJI", "Openbaar Ministerie"],
        juridische_context=["strafrecht", "bestuursrecht"],
        wettelijke_basis=["Wetboek van Strafvordering"],
        document_context=documenttekst,
        betekenisverduidelijking="Bedoeld is de procedure als geheel",
    )
    prompt = (await PromptServiceV2().build_generation_prompt(request)).text
    # Gemeten 17-09-2026 (na stap 2): 34,8K–35,6K; de `type`-varianten zitten
    # boven de oude kap van 35K en zouden daar hun staart verliezen.
    assert EINDINSTRUCTIE in prompt
    assert prompt.count(CONFLICT_SENTINEL) == 1
    assert "meld die opnieuw" in prompt  # laatste zin van het contract
    # De promptmetadata is het allerlaatste blok: staat die er, is niets afgeknipt.
    assert prompt.rstrip().endswith(PROMPTMETADATA_STAART), prompt[-300:]
