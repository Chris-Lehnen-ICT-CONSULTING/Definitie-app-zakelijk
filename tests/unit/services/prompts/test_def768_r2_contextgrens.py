"""DEF-768 R2-ontwikkelcorrectie: contextmechanismen voegen geen rol toe.

Ontwikkelronde R2 (reports/DEF-768-AI-20260924-R2/ontwikkeling-inhoud-v1.md,
G4): de strafoplegging bleef behouden, maar een persoonsrol werd toegevoegd die
de synthetische bron niet noemt. Herleide aanwijzing: het contextblok
`IMPLICIT_CONTEXT_MECHANISMS` (vocabulaire/scope/relaties, met voorbeelden als
"persoon" → een strafrechtelijke rolterm en "refereer context-specifieke
verbanden") zonder grens tegen het toevoegen van partijen of rollen. Dit is een
hypothese over de oorzaak; bewezen is alleen de constructie.

Geen woordverbod: een rolterm mag als bron of bedoelde betekenis hem draagt.
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import pytest

from services.interfaces import GenerationRequest
from services.prompts.modules.context_awareness_module import (
    ContextAwarenessModule,
)
from services.prompts.prompt_service_v2 import PromptServiceV2
from tests.unit.services.prompts.test_def768_r2_g_betekenisbehoud import (
    BRON_OMVANG,
    BRON_RELATIE,
    ESS05_GEEN_UITSLUITING,
    ESS05_RELATIE,
    KOP_GEEN_UITSLUITING,
)
from toetsregels.rule_cache import get_rule_cache

pytestmark = [pytest.mark.unit]

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "scripts" / "ess05"))

import proefinvoer as pi

G_INVOER = ROOT / "tests" / "fixtures" / "ess05" / "g_invoer_v2.json"

GRENS = (
    "⚠️ GRENS: deze mechanismen bepalen welke domeinterm je kiest voor wat de "
    "definitie toch moet noemen. Voeg er geen partij, persoon, ontvanger of rol- "
    "of statuskwalificatie mee toe die bron en bedoelde betekenis niet noemen."
)
MECHANISMEN = ("MECHANISME 1 - VOCABULAIRE", "MECHANISME 3 - RELATIES", "🧪 TEST")


@pytest.fixture(autouse=True)
def _verse_regelcache():
    get_rule_cache().clear_cache()


def test_mechanismenblok_draagt_de_grens_voor_de_test():
    blok = ContextAwarenessModule.IMPLICIT_CONTEXT_MECHANISMS
    assert blok.count(GRENS) == 1
    for kop in MECHANISMEN:
        assert kop in blok, kop  # mechanismen blijven, alleen begrensd
    assert blok.index("MECHANISME 3") < blok.index(GRENS) < blok.index("🧪 TEST")


def test_geen_woordverbod_en_geen_gevalswoorden():
    laag = GRENS.lower()
    for woord in (
        "veroordeel",
        "geldboete",
        "rechter",
        "geldbedrag",
        "staat",
        "hoofdstraf",
    ):
        assert woord not in laag, woord


def test_echte_prompt_met_strafrechtcontext_draagt_de_grens_een_keer():
    request = GenerationRequest(
        id="def768-r2-contextgrens",
        begrip="testbegrip",
        ontologische_categorie="type",
        organisatorische_context=["Synthetische Dienst"],
        juridische_context=["strafrecht"],
        actor="test_user",
    )
    prompt = asyncio.run(PromptServiceV2().build_generation_prompt(request)).text
    assert prompt.count(GRENS) == 1


def test_g4_proefprompt_draagt_grens_en_eerdere_g_verbeteringen():
    data = json.loads(G_INVOER.read_text(encoding="utf-8"))
    invoer = next(i for i in data["invoeren"] if i["id"] == "G4-meerdere-buren")
    prompt = asyncio.run(pi.bouw_g_prompt(invoer))
    assert prompt.count(GRENS) == 1
    for zin in (
        ESS05_RELATIE,
        ESS05_GEEN_UITSLUITING,
        BRON_RELATIE,
        BRON_OMVANG,
        KOP_GEEN_UITSLUITING,
    ):
        assert prompt.count(zin) == 1, zin
    pi.controleer_promptlengte(invoer["id"], "actueel", prompt)
