"""
End-to-End Integration Tests voor Synonym Orchestrator v3.1 (Architecture PHASE 3).

Test complete flow: definitie generation → synonym enrichment → review → manual edit sync.

Test Categories:
- PHASE 3.1 & 3.2: Generation flow with enrichment and review UI
- PHASE 3.3: Manual edit sync to registry
- Cache invalidation and data consistency

Architecture Reference: docs/architectuur/synonym-orchestrator-architecture-v3.1.md

DEF-519 — de drie nodes draaien nu offline op hun échte keten:

* de module-brede `skipif(not OPENAI_API_KEY)` is weg. Bevroren zijn uitsluitend
  de externe clientgrenzen, drie stuks: (a) de AI-providerfabriek
  `services.ai.create_ai_client`, (b) de web-lookupclients (Wikipedia,
  Wiktionary, SRU, Rechtspraak) en (c) de OpenAI-embeddingclient van de
  `EmbeddingService`. De voorbeeldenfase draait echt:
  `UnifiedExamplesGenerator.ai_service` resolvet via
  `get_cached_container().orchestrator().ai_service`, dus ook die fase komt op
  dezelfde bevroren AI-client uit. Orchestrator, registry, repository, cache,
  suggester en sync zijn echt; er wordt niets in de registry geplant om een
  uitkomst te maken;
* de embeddingstub gooit bewust een `RuntimeError` bij `create`. Wat deze tests
  daarmee aantonen is de gecontroleerde optionele RAG-fallback: de keten loopt
  door terwijl de embeddinggrens hard faalt. Het is nadrukkelijk géén bewijs van
  geslaagde RAG-retrieval en ook geen "leeg maar succesvol" embeddingantwoord;
* de oude fixture schreef `container_module._default_container`. Sinds DEF-249
  delegeert `get_container()` naar `utils.container_manager.get_cached_container`,
  dus die schrijfactie had geen effect: `SynonymSyncService` viel terug op de
  productiecontainer. De fabrieksgrens wordt nu aan de eigen container gebonden
  en na afloop teruggezet; er wordt geen globale cache van anderen gewist
  (`reset_container()` is daarom vervallen);
* de database komt uit `initialized_synonym_db` (eigen schema + migratie 006).

Beperking: dit is een synthetische workflow. De "goedkeuring" is een testhandeling
op de echte registry, geen menselijke beoordeling, en de AI-suggesties komen uit
de bevroren clientgrens — geen uitspraak over echte modelkwaliteit.
"""

from __future__ import annotations

import json
import logging

import pytest

from services.ai.base_client import ChatMessage, ChatResponse
from services.interfaces import Definition, GenerationRequest

pytestmark = [pytest.mark.integration]

logger = logging.getLogger(__name__)

#: Synthetische AI-suggesties; ze bereiken de registry uitsluitend via de
#: normale suggester → ensure_synonyms → registry-route.
SYNTHETISCHE_SYNONIEMEN = [
    {"synoniem": "voorarrest", "confidence": 0.9, "rationale": "synthetisch"},
    {
        "synoniem": "preventieve hechtenis",
        "confidence": 0.8,
        "rationale": "synthetisch",
    },
    {
        "synoniem": "inverzekeringstelling",
        "confidence": 0.7,
        "rationale": "synthetisch",
    },
]

#: Vaste openingszin van de suggesterprompt (synonym_research_prompt.py:129).
SUGGESTER_PROMPT_MARKER = "Zoek synoniemen voor de juridische term"

#: Waarmee de offline-gate uitgaand verkeer weigert (offline_bootstrap.py:366).
GATEMELDING = "geblokkeerd door de DEF-519-testgate"

SYNTHETISCHE_DEFINITIE = (
    "Voorlopige hechtenis is een strafvorderlijke vrijheidsbeneming van een "
    "verdachte in afwachting van de behandeling van zijn zaak."
)

#: Wat de échte CleaningService van dat antwoord maakt (aanhef verwijderd).
GEREINIGDE_DEFINITIE = (
    "Strafvorderlijke vrijheidsbeneming van een verdachte in afwachting van de "
    "behandeling van zijn zaak."
)


class BevrorenAIClient:
    """Eén van de drie bevroren externe clientgrenzen: de AI-provider.

    De andere twee zitten in `bevroren_externe_clients`: de web-lookupclients en
    de OpenAI-embeddingclient. Deze stub levert een vast synoniemenantwoord voor
    synoniemprompts en een vaste definitietekst voor de rest. Registreert elke
    aanroep, zodat een test kan toetsen dat de keten werkelijk langs deze grens
    liep.
    """

    def __init__(self, *, synoniemen: list[dict] | None = None) -> None:
        self.synoniemen = SYNTHETISCHE_SYNONIEMEN if synoniemen is None else synoniemen
        self.prompts: list[str] = []
        self.faalt_op_suggester = False
        self.gesloten = False

    @property
    def provider_name(self) -> str:
        return "bevroren"

    def suggesteroproepen(self) -> list[str]:
        """Alleen de calls van SynonymSuggester.

        De voorbeeldenfase vraagt óók om synoniemen, dus 'synoniem' als
        trefwoord is niet onderscheidend; de suggesterprompt herken je aan zijn
        vaste openingszin uit `synonym_research_prompt.py`.
        """
        return [p for p in self.prompts if p.startswith(SUGGESTER_PROMPT_MARKER)]

    def voorbeeldoproepen(self) -> list[str]:
        """Calls van de voorbeeldenfase.

        Die prompts dragen de al gegenereerde definitie mee; de
        hoofddefinitieprompt kan dat per definitie niet.
        """
        return [
            p
            for p in self.prompts
            if not p.startswith(SUGGESTER_PROMPT_MARKER) and SYNTHETISCHE_DEFINITIE in p
        ]

    def hoofddefinitieoproepen(self) -> list[str]:
        """Calls van de definitiegeneratie zelf."""
        return [
            p
            for p in self.prompts
            if not p.startswith(SUGGESTER_PROMPT_MARKER)
            and SYNTHETISCHE_DEFINITIE not in p
        ]

    async def chat_completion(
        self,
        messages: list[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 300,
        timeout: float | None = None,
    ) -> ChatResponse:
        prompt = messages[-1].content if messages else ""
        self.prompts.append(prompt)

        # Alleen de suggesterprompt krijgt het synoniemen-JSON; de
        # hoofddefinitieprompt bevat het woord 'synoniem' ook, dus dat trefwoord
        # is niet onderscheidend.
        if prompt.startswith(SUGGESTER_PROMPT_MARKER):
            if self.faalt_op_suggester:
                # Echte providerfout ná registratie: de call is aantoonbaar
                # bereikt en faalt daarna, dus geen lege respons in vermomming.
                raise RuntimeError("providerfout (teststub)")
            tekst = json.dumps({"synoniemen": self.synoniemen}, ensure_ascii=False)
        else:
            tekst = SYNTHETISCHE_DEFINITIE

        return ChatResponse(
            text=tekst,
            tokens_used=len(tekst.split()),
            model=model,
            metadata={"bevroren": True},
        )

    async def close(self) -> None:
        self.gesloten = True


def _gatesporen(records: list[logging.LogRecord]) -> list[str]:
    """Vastgelegde records waarin een gateweigering voorkomt.

    Een geslaagde pytest-run toont géén captured logs, dus "ik zie niets in de
    output" bewijst niets. Deze functie leest de records expliciet uit — zowel
    de boodschap als de `__cause__`/`__context__`-keten van een eventueel
    meegegeven exception, zodat een gateweigering die onderweg werd ingepakt en
    als "provider niet beschikbaar" gelogd, alsnog opvalt.
    """
    treffers: list[str] = []
    for record in records:
        if GATEMELDING in record.getMessage():
            treffers.append(f"{record.name}: {record.getMessage()}")
        fout = record.exc_info[1] if record.exc_info else None
        gezien: set[int] = set()
        while fout is not None and id(fout) not in gezien:
            gezien.add(id(fout))
            if GATEMELDING in str(fout):
                treffers.append(f"{record.name}: {type(fout).__name__}: {fout}")
            fout = fout.__cause__ or fout.__context__
    return treffers


def _sluit_container_verbindingen(container) -> None:
    """Sluit uitsluitend de SQLite-verbindingen die déze container opende."""
    from database.db_connection import DatabaseConnection

    gezien: set[int] = set()
    for instantie in list(getattr(container, "_instances", {}).values()):
        for houder in (instantie, getattr(instantie, "legacy_repo", None)):
            db = getattr(houder, "_db", None)
            if not isinstance(db, DatabaseConnection) or id(db) in gezien:
                continue
            gezien.add(id(db))
            toestand = getattr(getattr(db, "_thread_local", None), "state", None)
            if toestand is not None:
                toestand.close()


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def bevroren_client(monkeypatch):
    """Bevries de externe AI-providergrens.

    Dit is de eerste van drie bevroren externe clientgrenzen; de web-lookup- en
    embeddinggrens staan in `bevroren_externe_clients`. Interne services blijven
    onaangeroerd.
    """
    import services.ai as ai_pakket

    client = BevrorenAIClient()
    monkeypatch.setattr(
        ai_pakket,
        "create_ai_client",
        lambda provider, api_key, timeout=30.0: client,
    )
    return client


@pytest.fixture
def bevroren_externe_clients(monkeypatch):
    """Bevries de overige externe clientgrenzen: web-providers en embeddings.

    Zonder deze bevriezing doen de web-lookupfase (Wikipedia/Wiktionary/SRU/
    Rechtspraak) en de RAG-embeddings echte netwerkpogingen; die worden door de
    offline-gate geblokkeerd en vervolgens stil als "provider niet beschikbaar"
    afgehandeld. Dat is geen hermetisch bewijs. De gate blijft volledig actief;
    hier worden alleen de externe clientgrenzen vastgezet. Er wordt geen interne
    resultaatfunctie vervangen.

    De twee grenzen gedragen zich verschillend en dat is bewust:

    * de web-lookupclients geven een leeg, vast antwoord — de lookupfase draait
      dus wel, maar levert niets op;
    * de embeddingclient gooit bij `create` een `RuntimeError`. Daarmee toont de
      keten haar gecontroleerde optionele RAG-fallback: hij loopt door terwijl
      de embeddinggrens hard faalt. Dit is géén bewijs van geslaagde
      RAG-retrieval en ook geen leeg-maar-succesvol embeddingantwoord.
    """
    oproepen: dict[str, list[str]] = {"web": [], "embedding": []}

    async def geen_webresultaat(term, *args, **kwargs):
        oproepen["web"].append(str(term))

    class LegeSRUService:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args: object) -> bool:
            return False

        async def search(self, term, endpoint="overheid", max_records=3):
            oproepen["web"].append(str(term))
            return []

        def get_attempts(self) -> list[dict]:
            return []

    class LegeOpenAIClient:
        """Externe OpenAI-clientgrens van de EmbeddingService.

        `create` faalt bewust hard: dat oefent de optionele RAG-fallback en
        levert nadrukkelijk geen embeddingresultaat.
        """

        def __init__(self, *args: object, **kwargs: object) -> None:
            oproepen["embedding"].append("client")
            self.embeddings = self

        def create(self, *args: object, **kwargs: object):
            raise RuntimeError("embeddingprovider bevroren (teststub)")

    monkeypatch.setattr(
        "services.web_lookup.wikipedia_service.wikipedia_lookup", geen_webresultaat
    )
    monkeypatch.setattr(
        "services.web_lookup.wiktionary_service.wiktionary_lookup", geen_webresultaat
    )
    monkeypatch.setattr("services.web_lookup.sru_service.SRUService", LegeSRUService)
    monkeypatch.setattr(
        "services.web_lookup.rechtspraak_rest_service.rechtspraak_lookup",
        geen_webresultaat,
    )
    monkeypatch.setattr(
        "services.rag.embedding_service.openai.OpenAI", LegeOpenAIClient
    )
    return oproepen


@pytest.fixture
def container(
    initialized_synonym_db,
    bevroren_client,
    bevroren_externe_clients,
    monkeypatch,
    tmp_path,
):
    """Eigen echte container op de eigen synoniemdatabase.

    De fabrieksgrens die `SynonymSyncService` gebruikt
    (`utils.container_manager.get_cached_container`, waarnaar
    `services.container.get_container` sinds DEF-249 delegeert) wijst hier naar
    déze container. `monkeypatch` zet die binding daarna exact terug; er wordt
    geen globale containercache van anderen gewist of gereset.
    """
    from services.container import ServiceContainer
    from utils import container_manager
    from voorbeelden import unified_voorbeelden

    test_container = ServiceContainer(
        {
            "db_path": str(initialized_synonym_db),
            # Echte regelset: met use_json_rules=False laadde de validator 0/53
            # regels en meldde "regelset dekt contract niet".
            "use_json_rules": True,
            "enable_monitoring": False,
            "enable_ontology": False,
        }
    )
    vorige_generator = unified_voorbeelden._generator
    try:
        monkeypatch.setattr(
            container_manager, "get_cached_container", lambda: test_container
        )

        # De voorbeeldenfase draait écht. Haar `ai_service`-property resolvet via
        # `get_cached_container().orchestrator().ai_service`, dus zij komt op
        # dezelfde bevroren providerfabriek uit. De module-singleton wordt vers
        # gemaakt (een eerdere test kan een override hebben achtergelaten) en
        # daarna exact teruggezet.
        unified_voorbeelden.reset_examples_generator()

        yield test_container
    finally:
        unified_voorbeelden._generator = vorige_generator
        _sluit_container_verbindingen(test_container)


# ============================================================================
# TEST 1: Complete Flow - Generation → Enrichment → Review
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.integration
async def test_definition_generation_with_synonym_enrichment_e2e(
    container, bevroren_client, caplog
):
    """
    E2E: Definitiegeneratie → enrichment → weblookup → review.

    Flow (Architecture v3.1, PHASE 3.1 & 3.2):
    1. Generate definition for term with <5 synonyms
    2. Verify enrichment triggered via de bevroren providergrens
    3. Verify AI-pending synonyms created in registry
    4. Verify metadata in generation response
    5. Synthetische goedkeuring via de echte registry
    6. Verify synonyms activated and cache invalidated
    """
    registry = container.synonym_registry()
    orchestrator = container.orchestrator()
    synonym_orch = container.synonym_orchestrator()

    # Verify orchestrator has synonym_orchestrator injected (PHASE 3.1)
    assert orchestrator.synonym_orchestrator is not None
    assert orchestrator.synonym_orchestrator is synonym_orch

    request = GenerationRequest(
        id="test-gen-001",
        begrip="voorlopige hechtenis",
        organisatorische_context=["strafrecht"],
        juridische_context=["detentie"],
        wettelijke_basis=[],
        ontologische_categorie="proces",
        actor="test_user",
    )

    with caplog.at_level(logging.DEBUG):
        response = await orchestrator.create_definition(request, context={})

    assert response.success is True, response.error

    # Fixturegrenscontrole: de drie bevroren clientgrenzen horen het uitgaande
    # verkeer af te vangen vóórdat de offline-gate eraan te pas komt. Staat er
    # tóch een gateweigering in de vastgelegde records, dan liep een fase langs
    # een niet-bevroren grens en werd de blokkade daarna stil weggeslikt.
    #
    # Beperking, expliciet: dit is géén volledig netwerkverkeersbewijs. De gate
    # laat sowieso geen enkele uitgaande call slagen, en `caplog` ziet alleen
    # records die de root bereiken (een logger met `propagate=False` valt
    # erbuiten). Wat deze controle wél uitsluit, is dat de keten stilletjes op
    # een geblokkeerde poging terugviel.
    assert (
        caplog.records
    ), "er is niets vastgelegd; de gatecontrole hieronder zou leeg meelopen"
    sporen = _gatesporen(caplog.records)
    assert not sporen, f"gateweigering in de vastgelegde logs: {sporen}"

    # Actueel contract: onder de STRICT-policy telt ai_pending niet mee in de
    # teruggegeven lijst, dus de status is "no_synonyms" terwijl er wél
    # AI-suggesties ter beoordeling zijn aangemaakt.
    assert response.metadata["synonym_enrichment_status"] == "no_synonyms"

    # De enrichment én de overige fasen liepen werkelijk langs de providergrens.
    assert (
        len(bevroren_client.suggesteroproepen()) == 1
    ), "suggester heeft de AI-grens niet precies één keer gebruikt"
    assert (
        bevroren_client.hoofddefinitieoproepen()
    ), "de definitiegeneratie liep niet langs de providergrens"
    assert (
        bevroren_client.voorbeeldoproepen()
    ), "de voorbeeldenfase liep niet langs de providergrens"

    # De definitietekst komt aantoonbaar uit het vastgezette providerantwoord;
    # de echte CleaningService haalt de "<begrip> is een"-aanhef eraf.
    assert response.definition is not None
    assert response.definition.definitie == GEREINIGDE_DEFINITIE

    # Echte validatie op deze call (echte regelset, use_json_rules=True).
    assert response.validation_result is not None
    assert "overall_score" in response.validation_result
    assert response.validation_result["passed_rules"] or (
        response.validation_result["violations"]
    ), "validator evalueerde geen enkele regel voor deze call"

    # Het bovenstaande alleen kan ook door een gedegradeerd of foutresultaat
    # gehaald worden (een enkele violation volstaat). Het actuele
    # resultaatcontract discrimineert daar wél tegen: op het noodpad staat
    # `validation_status` op "validation_unknown", laadt de validator 0 regels
    # en meldt de dekking nul geëvalueerde regels.
    # Veldpaden: tests/integration/performance/test_validation_performance_baseline.py:86-104.
    assert (
        response.validation_result["validation_status"] == "validated"
    ), f"validatiestatus is {response.validation_result['validation_status']!r}"
    systeem = response.validation_result["system"]
    assert systeem["degraded_mode"] is False, systeem
    assert systeem["rules_loaded"] == 53, systeem

    # Geen snapshot van score of dekking: dit legt geen toekomstige
    # kwaliteitsuitkomst vast, alleen dat er werkelijk geëvalueerd is en dat de
    # dekking intern sluit.
    dekking = response.validation_result["evaluation_coverage"]
    assert dekking["evaluated"] > 0, dekking
    assert dekking["evaluated"] == dekking["passed"] + dekking["failed"], dekking

    verwachte_termen = [s["synoniem"] for s in SYNTHETISCHE_SYNONIEMEN]
    assert response.metadata["ai_pending_synonyms_count"] == len(verwachte_termen)

    # Onder STRICT levert ensure_synonyms geen actieve synoniemen op; de
    # metadata-lijst is dus expliciet leeg (geen lus met nul assertions).
    assert response.metadata.get("enriched_synonyms", []) == []

    # Verse readback uit de echte registry.
    group = registry.find_group_by_term("voorlopige hechtenis")
    assert group is not None, "ensure_synonyms hoort een groep te maken"

    pending_members = registry.get_group_members(
        group_id=group.id, statuses=["ai_pending"]
    )
    assert {m.term for m in pending_members} == set(verwachte_termen)

    # Synthetische goedkeuring (geen menselijke beoordeling) op de echte registry.
    first_pending = sorted(pending_members, key=lambda m: m.id)[0]
    registry.update_member_status(
        member_id=first_pending.id, new_status="active", reviewed_by="test_user"
    )

    updated_member = registry.get_member(first_pending.id)
    assert updated_member.status == "active"
    assert updated_member.reviewed_by == "test_user"

    active_members = registry.get_group_members(group_id=group.id, statuses=["active"])
    assert {m.term for m in active_members} == {first_pending.term}

    # Lookup ziet de goedgekeurde term (cache ge-invalideerd door de callback).
    lookup_synonyms = synonym_orch.get_synonyms_for_lookup("voorlopige hechtenis")
    approved_terms = [s.term for s in lookup_synonyms]
    assert approved_terms == [first_pending.term]


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.parametrize("providermodus", ["lege_respons", "exception"])
async def test_enrichment_fallback_bij_provideruitval(
    container, bevroren_client, providermodus
):
    """Fallback mag geen groep, pending of goedkeuring simuleren.

    Twee verschillende gevallen, eerlijk uit elkaar gehouden:
    `lege_respons` is een geldig leeg antwoord van de provider;
    `exception` is een échte providerfout tijdens de call.
    """
    registry = container.synonym_registry()
    synonym_orch = container.synonym_orchestrator()

    if providermodus == "lege_respons":
        bevroren_client.synoniemen = []
    else:
        bevroren_client.faalt_op_suggester = True

    term = f"term-{providermodus}"
    synoniemen, ai_pending = await synonym_orch.ensure_synonyms(term, min_count=5)

    # De externe clientcall is in beide gevallen werkelijk bereikt.
    assert len(bevroren_client.suggesteroproepen()) == 1
    assert ai_pending == 0
    assert synoniemen == []
    assert registry.find_group_by_term(term) is None


# ============================================================================
# TEST 2: Manual Edit Sync to Registry
# ============================================================================


@pytest.mark.integration
def test_manual_edit_sync_to_registry(container):
    """
    E2E: Manual edit in definitie-editor → registry sync (PHASE 3.3).

    Flow: create → add synoniemen → verify scoped sync → remove → deprecated →
    re-add → reactivated (idempotent sync). Gebruikt de echte
    `save_voorbeelden`-API en de echte registry van de eigen container.
    """
    repo = container.repository()
    registry = container.synonym_registry()

    def mapping(group_id: int, definitie_id: int) -> dict[str, tuple]:
        """term → (status, source, definitie_id, weight) uit een verse readback."""
        leden = registry.get_group_members(
            group_id=group_id, filters={"definitie_id": definitie_id}
        )
        return {m.term: (m.status, m.source, m.definitie_id, m.weight) for m in leden}

    definitie = Definition(
        begrip="test_manual_term",
        definitie="Test definitie voor manual synonym sync",
        organisatorische_context=["test"],
        juridische_context=[],
        wettelijke_basis=[],
        categorie="proces",
        created_by="test_user",
    )

    definitie_id = repo.save(definitie)
    assert definitie_id > 0
    logger.info(f"Created definitie {definitie_id}: {definitie.begrip}")

    synoniemen = ["manueel_syn1", "manueel_syn2", "manueel_syn3"]

    repo.legacy_repo.save_voorbeelden(
        definitie_id=definitie_id,
        voorbeelden_dict={"synoniemen": synoniemen},
        gegenereerd_door="test_user",
    )

    group = registry.find_group_by_term("test_manual_term")
    assert group is not None, "Synonym group should be created"

    members = registry.get_group_members(
        group_id=group.id, filters={"definitie_id": definitie_id, "source": "manual"}
    )

    assert len(members) == 3, f"Expected 3 manual synonyms, got {len(members)}"
    assert all(m.status == "active" for m in members), "All should be active"
    assert all(
        m.definitie_id == definitie_id for m in members
    ), "All should be scoped to definitie_id"
    assert all(m.source == "manual" for m in members), "All should have source=manual"
    assert all(
        m.weight == 1.0 for m in members
    ), "Manual synonyms should have weight=1.0"

    member_terms = {m.term for m in members}
    assert member_terms == set(
        synoniemen
    ), "Registry should contain all manual synonyms"

    # Exacte mapping na stadium 1.
    assert mapping(group.id, definitie_id) == {
        "manueel_syn1": ("active", "manual", definitie_id, 1.0),
        "manueel_syn2": ("active", "manual", definitie_id, 1.0),
        "manueel_syn3": ("active", "manual", definitie_id, 1.0),
    }

    # Step 4: Manual edit - remove one synonym (manueel_syn3)
    updated_synoniemen = ["manueel_syn1", "manueel_syn2"]  # syn3 removed

    repo.legacy_repo.save_voorbeelden(
        definitie_id=definitie_id,
        voorbeelden_dict={"synoniemen": updated_synoniemen},
        gegenereerd_door="test_user",
    )

    members = registry.get_group_members(
        group_id=group.id, filters={"definitie_id": definitie_id}
    )

    syn3_member = next((m for m in members if m.term == "manueel_syn3"), None)
    assert syn3_member is not None, "manueel_syn3 should still exist in registry"
    assert syn3_member.status == "deprecated", "manueel_syn3 should be deprecated"

    active_members = [m for m in members if m.status == "active"]
    assert len(active_members) == 2, "Two synonyms should still be active"
    assert {m.term for m in active_members} == {"manueel_syn1", "manueel_syn2"}

    # Exacte mapping na stadium 2: alleen syn3 wijzigt, de rest blijft gelijk.
    assert mapping(group.id, definitie_id) == {
        "manueel_syn1": ("active", "manual", definitie_id, 1.0),
        "manueel_syn2": ("active", "manual", definitie_id, 1.0),
        "manueel_syn3": ("deprecated", "manual", definitie_id, 1.0),
    }

    # Step 6: Manual edit - re-add syn3
    re_added_synoniemen = ["manueel_syn1", "manueel_syn2", "manueel_syn3"]

    repo.legacy_repo.save_voorbeelden(
        definitie_id=definitie_id,
        voorbeelden_dict={"synoniemen": re_added_synoniemen},
        gegenereerd_door="test_user",
    )

    members = registry.get_group_members(
        group_id=group.id, filters={"definitie_id": definitie_id}
    )

    syn3_member = next((m for m in members if m.term == "manueel_syn3"), None)
    assert syn3_member is not None
    assert syn3_member.status == "active", "manueel_syn3 should be reactivated"

    active_members = [m for m in members if m.status == "active"]
    assert len(active_members) == 3, "All three synonyms should be active"

    # Exacte mapping na stadium 3: alle drie terug op active, niets verdwenen
    # of vervangen (een count van 3 alleen zou dat niet aantonen).
    assert mapping(group.id, definitie_id) == {
        "manueel_syn1": ("active", "manual", definitie_id, 1.0),
        "manueel_syn2": ("active", "manual", definitie_id, 1.0),
        "manueel_syn3": ("active", "manual", definitie_id, 1.0),
    }


# ============================================================================
# TEST 3: Cache Invalidation After Approval
# ============================================================================


@pytest.mark.integration
def test_synonym_cache_invalidation_after_approval(container):
    """
    Verify cache invalidation after synonym approval (PHASE 3 cache behavior).

    Ongewijzigde hit/miss-grenzen en teruggegeven bron; alleen de container is
    nu de eigen, echte container.
    """
    orchestrator = container.synonym_orchestrator()
    registry = container.synonym_registry()

    # Reset cache stats
    orchestrator._cache_hits = 0
    orchestrator._cache_misses = 0

    group = registry.get_or_create_group(
        canonical_term="test_cache_term", created_by="test"
    )

    member_id = registry.add_group_member(
        group_id=group.id,
        term="pending_cache_syn",
        weight=0.9,
        status="ai_pending",
        source="ai_suggested",
        created_by="test",
    )

    # Step 2: Query synonyms (cache miss)
    result1 = orchestrator.get_synonyms_for_lookup("test_cache_term")
    assert orchestrator._cache_misses == 1, "First query should be cache miss"
    assert len(result1) == 0, "ai_pending should NOT be included (policy=STRICT)"

    # Step 3: Query again (cache hit)
    result2 = orchestrator.get_synonyms_for_lookup("test_cache_term")
    assert orchestrator._cache_hits == 1, "Second query should be cache hit"
    assert len(result2) == 0, "Still no ai_pending synonyms"

    # Step 4: Approve synonym (should invalidate cache via callback)
    registry.update_member_status(
        member_id=member_id, new_status="active", reviewed_by="test"
    )

    # Step 5: Query again (cache should be invalidated, fresh query)
    result3 = orchestrator.get_synonyms_for_lookup("test_cache_term")

    assert (
        orchestrator._cache_misses == 2
    ), "Approval should invalidate cache (new miss)"

    assert len(result3) == 1, "Approved synonym should now be included"
    assert result3[0].term == "pending_cache_syn"
    assert result3[0].weight == 0.9
    # De bron blijft in de registry vastgelegd (WeightedSynonym draagt hem niet).
    assert registry.get_member(member_id).source == "ai_suggested"

    # Step 6: Query one more time (should be cache hit again)
    result4 = orchestrator.get_synonyms_for_lookup("test_cache_term")
    assert orchestrator._cache_hits == 2, "Fourth query should be cache hit"
    assert len(result4) == 1

    assert orchestrator._cache_hits == 2
    assert orchestrator._cache_misses == 2
