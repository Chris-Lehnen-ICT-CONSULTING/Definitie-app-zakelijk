"""DEF-821 — de echte eindprompt: exacte G2-v5-instructie plus G2-2-route.

Bewijst de instructies, niet de modelkwaliteit:

* de ESS-04-regelkaart draagt exact de G2-tekst uit
  `instructievoorstellen-v5.md` (één keer) en niet meer de cijfergerichte
  oude instructie;
* het uitvoercontract kent twee strikt herkenbare uitzonderingen op de
  definitie-uitvoer (ESS-02-betekenisconflict, ESS-04-ontbrekende
  betekenisgrond); geen enkele formulering noemt nog één van beide de
  "enige" uitzondering, en de slotopdracht laat de melding toe;
* ontbrekend gevalsbewijs, een ontbrekende categorie en ontbrekende
  bronsteun zijn uitdrukkelijk géén reden voor de melding;
* ESS-02-tellingen (DEF-750/751) en de conflictroute blijven intact;
* in de rijkste variant overleeft de staart (incl. beide contracten) en
  blijft de prompt onder de harde kap;
* ESS-04-regelrecord (runtime_contract, patronen) is ongewijzigd (AC6).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from services.interfaces import GenerationRequest
from services.modelantwoord import CONFLICT_SENTINEL, ONTBREKENDE_GROND_SENTINEL
from services.prompts.modular_prompt_builder import PromptComponentConfig
from services.prompts.modules.context_awareness_module import VERDUIDELIJKING_KOP
from services.prompts.prompt_service_v2 import PromptServiceV2
from toetsregels.rule_cache import get_rule_cache

pytestmark = [pytest.mark.unit]

REPO = Path(__file__).resolve().parents[4]

#: Letterlijk uit docs/analyses/def606-regeldossiers/ESS-04-verdieping/
#: onderzoek-20260918/instructievoorstellen-v5.md, § G2 (blockquote).
G2_V5 = (
    "Beschrijf begripsbepalende kenmerken die in de bedoelde context navolgbaar op "
    "gevallen kunnen worden toegepast. Kwalitatieve criteria zijn toegestaan; voeg "
    "geen getal, percentage, termijn of registratienummer toe om toetsbaarheid te "
    "suggereren. Neem een kwantitatieve grens alleen over als de aangeleverde "
    "betekenisgrond haar ondersteunt en behoud relevante noemer, populatie, "
    "inclusie, startmoment en tijdsbasis, waaronder werk- of kalenderdagen wanneer "
    "dat onderscheidend is. Laat bepalende beperkingen in de definitiekern staan; "
    "methode, bewijsplaatsen en registratiecontext blijven apart. Bij ontbrekende "
    "of strijdige noodzakelijke grond: lever geen definitieve afbakening en verzin "
    "geen gegeven. Benoem de ontbrekende grond uitsluitend in een daarvoor "
    "bestemde aparte toelichting of verduidelijkingsuitkomst; voeg geen "
    "foutmelding, vraag of onzekere placeholder aan de definitiezin toe."
)
OUDE_ESS04 = "Gebruik objectief toetsbare elementen"
EINDINSTRUCTIE = "in één enkele zin, zonder toelichting"


@pytest.fixture(autouse=True)
def _verse_regelcache():
    get_rule_cache().clear_cache()


def _request(**extra) -> GenerationRequest:
    basis = {
        "id": "def821",
        "begrip": "geselecteerde partij",
        "ontologische_categorie": None,
        "organisatorische_context": ["Proefdienst"],
        "actor": "test",
    }
    return GenerationRequest(**{**basis, **extra})


async def _prompt(**extra) -> str:
    return (await PromptServiceV2().build_generation_prompt(_request(**extra))).text


def test_g2_tekst_staat_letterlijk_in_het_voorstelbestand():
    """Borg dat de test de échte v5-tekst gebruikt (niet een parafrase)."""
    bron = (
        REPO
        / "docs/analyses/def606-regeldossiers/ESS-04-verdieping/onderzoek-20260918"
        / "instructievoorstellen-v5.md"
    ).read_text(encoding="utf-8")
    assert f"> {G2_V5}" in bron


@pytest.mark.parametrize(
    "categorie", ["type", "proces", "resultaat", "exemplaar", None]
)
async def test_ess04_regelkaart_draagt_exact_g2_en_niet_meer_de_cijferinstructie(
    categorie,
):
    prompt = await _prompt(ontologische_categorie=categorie)
    assert prompt.count(G2_V5) == 1
    kaart = prompt.split("🔹 **ESS-04 - Toetsbaarheid**", 1)[1].split("🔹", 1)[0]
    assert f"- **Instructie:** {G2_V5}" in kaart
    assert OUDE_ESS04 not in prompt
    assert "(deadlines, aantallen, percentages" not in prompt


@pytest.mark.parametrize(
    "categorie", ["type", "proces", "resultaat", "exemplaar", None]
)
async def test_een_consistent_uitvoercontract_met_twee_uitzonderingen(categorie):
    prompt = await _prompt(ontologische_categorie=categorie)
    # Beide meldingen staan precies één keer beschreven, met hun JSON-vorm.
    assert prompt.count(CONFLICT_SENTINEL) == 1
    assert prompt.count(ONTBREKENDE_GROND_SENTINEL) == 1
    assert '"ontbrekende_grond"' in prompt and '"vraag"' in prompt
    # Geen resterende exclusiviteit die de nieuwe uitkomst verbiedt.
    assert "enige uitzondering" not in prompt.lower()
    # De slotopdracht laat de melding toe, zonder de definitievorm te verliezen.
    slot = prompt.split("✏️ Geef nu de definitie", 1)[1].split("🆔", 1)[0]
    assert EINDINSTRUCTIE in slot
    assert "melding" in slot
    # "Lever uitsluitend de definitiekern" blijft, maar met de uitzondering.
    categorieregel = prompt.split("📋 **Categorie is metadata:**", 1)[1].split("\n", 1)[
        0
    ]
    assert "Lever uitsluitend de definitiekern" in categorieregel
    assert "melding" in categorieregel
    # Het nieuwe contract: geen lezingen/bronnen eisen, nooit gemengd.
    contract = prompt.split(ONTBREKENDE_GROND_SENTINEL, 1)[0].rsplit("🛑", 1)[1]
    contract += prompt.split(ONTBREKENDE_GROND_SENTINEL, 1)[1].split("\n\n", 1)[0]
    assert "geen lezingen" in contract
    assert "nooit samen met" in contract.lower() or "nooit samen" in contract
    assert "géén definitie" in contract


async def test_geen_reden_voor_de_melding_gevalsbewijs_categorie_bronsteun():
    prompt = await _prompt()
    contract = prompt.split(ONTBREKENDE_GROND_SENTINEL, 1)[1].split("\n\n", 1)[0]
    for fragment in (
        "kwalitatief criterium",
        "ontbrekend bewijs voor één concreet geval",
        "ontbrekende of onzekere categorie",
        "ontbrekende bronsteun",
        "eenheidsgrens (ESS-03)",
        "één voorlopige definitiezin",
    ):
        assert fragment in contract, fragment
    # Het contract verwijst naar dezelfde verduidelijkingsregel als ESS-02.
    assert f"'{VERDUIDELIJKING_KOP}'" in contract
    assert "geen bronfeit" in contract


async def test_ess02_conflictroute_en_tellingen_blijven_intact():
    prompt = await _prompt(ontologische_categorie="proces")
    # Uit tests/unit/services/prompts/test_def751_conflict_promptnorm.py.
    assert "Nooit een definitie én deze melding samen" in prompt
    assert "minstens twee" in prompt
    assert "bron NUMMER" in prompt and "context: CONTEXTWAARDE" in prompt
    assert "keuze van de bedoelde betekenislaag door de gebruiker" in prompt
    assert "meld die opnieuw" in prompt
    assert prompt.count("kies niet stil") == 2
    assert prompt.count("eerst worden verduidelijkt") == 2
    assert len(prompt.split("geef één voorlopige kandidaat")) == 3


@pytest.mark.parametrize("categorie", ["type", "proces", "resultaat", "exemplaar"])
@pytest.mark.parametrize(
    "documenttekst",
    [None, "Awb art. 5:11 toezichthouder " * 700],
    ids=["zonder_document", "met_document"],
)
async def test_rijkste_variant_houdt_beide_contracten_en_staart(
    categorie, documenttekst
):
    request = GenerationRequest(
        id="def821-lengte",
        begrip="keurmerkregistratieprocedure",
        ontologische_categorie=categorie,
        organisatorische_context=["DJI", "Openbaar Ministerie"],
        juridische_context=["strafrecht", "bestuursrecht"],
        wettelijke_basis=["Wetboek van Strafvordering"],
        document_context=documenttekst,
        betekenisverduidelijking="Bedoeld is de procedure als geheel",
    )
    prompt = (await PromptServiceV2().build_generation_prompt(request)).text
    assert prompt.count(G2_V5) == 1
    assert prompt.count(CONFLICT_SENTINEL) == 1
    assert prompt.count(ONTBREKENDE_GROND_SENTINEL) == 1
    assert EINDINSTRUCTIE in prompt
    assert prompt.rstrip().endswith("- Wettelijke basis: Wetboek van Strafvordering")
    assert len(prompt) < PromptComponentConfig().max_prompt_length


def test_ess04_regelrecord_runtime_contract_en_patronen_ongewijzigd():
    record = json.loads(
        (REPO / "src/toetsregels/regels/ESS-04.json").read_text(encoding="utf-8")
    )
    rc = record["runtime_contract"]
    assert rc["evaluator"] == "judgment_review"
    assert rc["automation_status"] == "review_required"
    assert rc["score_policy"] == "excluded_from_score"
    assert rc["example_pair_policy"] == "review_policy"
    assert len(record["herkenbaar_patronen"]) == 15
    # Norm en generatie wijzen dezelfde kant op: kwalitatief mag, geen cijferplicht.
    assert "Kwalitatieve criteria kunnen volstaan" in record["toelichting"]
    assert "Kwalitatieve criteria zijn toegestaan" in G2_V5
    assert "betekenisgrond ontbreken" in record["toetsvraag"]
