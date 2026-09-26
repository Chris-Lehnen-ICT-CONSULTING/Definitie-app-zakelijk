"""Offline kernjourney: generatie → opslag → bewerken → review → export (DEF-519).

Eén doorlopende journey over de *echte* servicelaag. De enige bevroren grens is
`services.ai.create_ai_client` — geleverd door de bestaande fixture
`bevroren_omgeving` (tests/integration/functionality/conftest.py). Alles
daarbinnen is productiecode: promptopbouw, opschoning, `ModularValidationService`
met de echte `ToetsregelManager`, `DefinitionRepository`, `DefinitionEditService`,
`DefinitionWorkflowService` met de echte `GatePolicyService`, en `ExportService`.
Er wordt geen validator-, opslag-, edit-, workflow-, gate- of exportdubbel
gebruikt, en het doelrecord wordt nooit met directe SQL geseed: elke rij die deze
test terugleest is door de productiecode geschreven.

Elke actor in deze test is expliciet synthetisch (`synthetische-…`). De
reviewstap bewijst uitsluitend het *contract* van de workflowservice; er wordt
geen menselijk oordeel, rol of expertreview geclaimd of toegekend.

Vastgelegde beperkingen van het huidige gedrag (bewust niet gerepareerd; deze
story levert geen Fase-A-productcode):

* **Validatiescore wordt niet gepersisteerd.** De orchestrator valideert echt
  (`validation_status="validated"`, 53 regels geladen) maar schrijft
  `validation_score`/`validation_issues` niet naar de rij. De vaststelgate ziet
  daardoor "Geen validatieresultaat beschikbaar". Dit is een *waarneming*, geen
  assertie: het ontbreken van die Fase-A-garantie wordt hier niet als gewenst
  gedrag vastgelegd. De rode verwachting voor aanwezigheid en actualiteit hoort
  onder DEF-627 (oude/lege score na bewerking) en DEF-630 (verplichte
  gate/bypass).
* **Bewerken hervalideert niet.** `DefinitionEditService._validate_definition`
  slaat een async validatie-API bewust over, dus het snapshot wordt na een
  bewerking niet vernieuwd (DEF-626/DEF-627). De echte validatieservice wordt
  hier wél geïnjecteerd. Ook dit blijft een waarneming zonder assertie.
* **JSON-export van één definitie faalt — deze test staat daarop ROOD.**
  `ExportService._export_to_json` zet `metadata["datum_voorstel"]` op het
  `datetime`-object van het record en roept `json.dump` zonder `default=`. Elke
  opgeslagen definitie laat de export daardoor afbreken met
  ``TypeError: Object of type datetime is not JSON serializable``, met een half
  geschreven `.json` als enige spoor. De exportstap hieronder eist een échte,
  geparseerde JSON-uitvoer met exacte tekst, id, status, versie en context; er
  wordt bewust géén aggregatiepayload en géén kapot artefact als vervanging
  geaccepteerd. De test blijft dus rood tot de minimale serialisatiegrens in een
  aparte, geautoriseerde wijziging is hersteld. Deze story wijzigt geen
  productiecode.

Alle verwachtingen hieronder zijn gemeten op de huidige code, niet afgeleid uit
wat de journey "zou moeten" doen.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pytest
import yaml

from domain.ontological_categories import OntologischeCategorie
from tests.integration.functionality.conftest import (
    DEFINITIE_TEKST,
    INT03_ANTECEDENT,
    INT03_SOORT,
    INT03_VERWIJZEND_WOORD,
    bevroren_omgeving,
    int03_definitie_uit_prompt,
    lees_opgeslagen_definitie,
)

pytestmark = [pytest.mark.acceptance, pytest.mark.integration]

_PROJECTWORTEL = Path(__file__).resolve().parents[2]

# --------------------------------------------------------------------------
# Vaste invoer
# --------------------------------------------------------------------------

BEGRIP = "vervoersverbod"
#: De canonieke ontologische categorie uit de actuele enum — dezelfde waarde die
#: de al groene functionality-fixtures gebruiken. Het is een proceshandeling.
CATEGORIE = OntologischeCategorie.PROCES.value
ORGANISATORISCH = "Openbaar Ministerie"
JURIDISCH = "strafprocesrecht"
WETTELIJK = "Wetboek van Strafvordering artikel 509"
CONTEXT: dict[str, list[str]] = {
    "organisatorisch": [ORGANISATORISCH],
    "juridisch": [JURIDISCH],
    "wettelijk": [WETTELIJK],
}

#: Het tweede begrip is uitsluitend voor de discriminator: een tweede generatie
#: van hetzelfde begrip zou de duplicaatregel CON-01 raken en dan zou een
#: falende assertie ook zonder defecte provider kunnen ontstaan.
BEGRIP_DISCRIMINATOR = "voertuigbeslag"

#: De opgeschoonde uitkomst van de bevroren provider. `DEFINITIE_TEKST` uit het
#: antwoordboek begint met "Een "; `opschonen_enhanced` haalt dat lidwoord weg.
#: De verwachting wordt hier afgeleid van het antwoordboek zodat zichtbaar is
#: welke transformatie de productiecode uitvoert — geen los gekopieerde string.
_ZONDER_LIDWOORD = DEFINITIE_TEKST.removeprefix("Een ")
VERWACHTE_DEFINITIE = _ZONDER_LIDWOORD[0].upper() + _ZONDER_LIDWOORD[1:]

NIEUWE_DEFINITIE = (
    "Handeling waarbij een bevoegde instantie een persoon verbiedt zich met een "
    "vervoermiddel te verplaatsen, conform het Wetboek van Strafvordering."
)

REDACTEUR = "synthetische-redacteur"
INDIENER = "synthetische-indiener"
BEOORDELAAR = "synthetische-beoordelaar"
WIJZIGINGSREDEN = "synthetische acceptatiewijziging: tekst aangescherpt"

# --------------------------------------------------------------------------
# Gemeten verwachtingen (huidige code)
# --------------------------------------------------------------------------

#: DEF-622: de drie contextlijsten reizen nu mee naar de validatieservice.
#: Daardoor draait DUP_01 (pass: geen duplicaat) i.p.v. `not_evaluated`, en
#: signaleert CON-01 de geselecteerde juridische context "strafprocesrecht" in
#: de definitiezin als naamsignaal (`review_required`, B-04) i.p.v. `pass`.
#: DEF-743: CON-02 toetst de aangeleverde bronnen; deze journey levert er
#: geen aan, dus CON-02 is expliciet open (`review_required`) i.p.v. een
#: woordpatroon-`fail` — één regel minder gefaald, één meer open.
#: DEF-750: ESS-02 is een menselijk betekenisoordeel; de marker-/categoriehit-
#: pass is vervallen, dus ESS-02 is open (`review_required`) i.p.v. `pass` —
#: één regel minder geslaagd, één meer open.
#: DEF-766: ESS-03 is een AI-beoordeling van eenheid en onderscheidbaarheid
#: via dezelfde bevroren providergrens; de woordindicator-fail (geen
#: 'uniek'/'nummer'/'code' in de zin) is vervallen. Het bevroren antwoord is
#: 'onvoldoende informatie' met één gerichte vraag (`ess03_bevroren_antwoord`),
#: wat als `review_required` telt — dus ESS-03 is open i.p.v. `fail`: één
#: regel minder gefaald, één meer open; 34/29/5/15 → 33/29/4/16. De dekking
#: telt sindsdien ook afgeronde niet-toepasselijkheid apart (`not_applicable`,
#: hier nul).
#: DEF-770: INT-01 keurt niet meer af op het woord 'die' in de bevroren
#: definitie (een foutpositief); zij stelt één zin vast als deelbevinding en
#: laat compactheid en begrijpelijkheid open (`review_required`). Eén regel
#: minder gefaald, één meer open; 33/29/4/16 → 32/29/3/17.
#: DEF-772: INT-03 is een AI-beoordeling van voornaamwoord-verwijzingen via
#: dezelfde bevroren providergrens. In de bevroren zin verwijst het enige
#: verwijzende woord 'die' eenduidig naar 'proefdefinitie' (betrekkelijke
#: bijzin met eenduidig antecedent, K6); het bevroren antwoord is dat
#: onderbouwde `pass`/`clear`-oordeel met het letterlijke antecedent
#: (`int03_bevroren_antwoord`). INT-03 was open (verwijssignalen zonder
#: oordeel) en is nu geslaagd: één regel meer geslaagd, één minder open;
#: 32/29/3/17 → 33/30/3/16. Zonder dat antwoord (de generieke definitietekst
#: of een lege respons als modeluitvoer, of zonder INT-03-routing) is INT-03
#: een technische fout — 16 open, 1 `error` — de oorspronkelijke CI-fout op
#: PR #482; zie `test_int03_bevroren_antwoord_discrimineert`.
VERWACHTE_DEKKING: dict[str, float | int] = {
    "evaluated": 33,
    "passed": 30,
    "failed": 3,
    "review_required": 16,
    "not_evaluated": 4,
    "error": 0,
    "not_applicable": 0,
    "total": 53,
    "coverage_ratio": 0.6226,
}
#: DEF-622 (B-06): CON-01 draagt geen cijfer, dus de totaalscore is niet
#: beschikbaar — `None`, nooit 0.0.
VERWACHTE_SCORE = None
VERWACHTE_GESLAAGDE_REGELS = [
    "ARAI-01",
    "ARAI-02",
    "ARAI-02SUB1",
    "ARAI-02SUB2",
    "ARAI-04",
    "ARAI-04SUB1",
    "ARAI-05",
    "ARAI-06",
    "CON-CIRC-001",
    "DUP_01",
    "ESS-CONT-001",
    "INT-03",
    "INT-04",
    "INT-07",
    "INT-08",
    "INT-09",
    "INT-10",
    "SAM-02",
    "SAM-04",
    "SAM-07",
    "STR-01",
    "STR-02",
    "STR-04",
    "STR-07",
    "STR-ORG-001",
    "STR-TERM-001",
    "VAL-EMP-001",
    "VAL-LEN-001",
    "VAL-LEN-002",
    "VER-02",
]
VERWACHTE_GEFAALDE_REGELS = [
    "ESS-05",
    "VER-01",
    "VER-03",
]

#: De gate ziet geen `validation_score` op de rij (zie modulebeschrijving) en
#: meldt dat als enige reden. `allow_hard_override: true` in de productiepolicy
#: maakt daar `override_required` van in plaats van `blocked`.
VERWACHTE_GATE: dict[str, Any] = {
    "status": "override_required",
    "reasons": ["Geen validatieresultaat beschikbaar (eerst (her)valideren)"],
}
#: De generieke scorereden uit `VERWACHTE_GATE`, apart benoemd omdat hij ook
#: naast de CON-02-blokkades hoort te staan (de gate laat geen reden vallen).
VERWACHTE_SCOREREDEN = VERWACHTE_GATE["reasons"][0]

#: DEF-743 (CON-02): deze journey levert geen bronnen aan (web lookup is door de
#: testgate geblokkeerd, geen RAG, geen upload). Zonder bronbewijs is CON-02
#: 'nog te beoordelen' en blokkeert de vaststelgate — dat is geen defect maar
#: de norm (besluit 15-09-2026). De enige gedocumenteerde route is de
#: deskundige uitzondering "geen passende bron" na gedocumenteerd zoeken; die
#: wordt hieronder via de echte repositorycommand vastgelegd (bevroren platte
#: vorm, C-contract §6) en blijft zichtbaar een uitzondering — geen pass.
CON02_ONDERDELEN = ("brongezag/toepasselijkheid", "betekenissteun", "verwijskwaliteit")
UITZONDERINGSMOTIVERING = (
    "synthetisch begrip zonder externe bron: geen passende authentieke of "
    "gezaghebbende bron beschikbaar voor deze betekenis, context en peildatum"
)
GEDOCUMENTEERD_ZOEKEN = {
    "queries": [f"{BEGRIP} definitie", f"{BEGRIP} Wetboek van Strafrecht"],
    "consulted": [
        "wetten.overheid.nl (geblokkeerd in de offline journey)",
        "intern register",
    ],
    "conclusion": "geen passende bron gevonden; uitzondering gedocumenteerd",
}

#: Vaststellen wordt geweigerd omdat een synthetische actor geen rol draagt en
#: `WorkflowService.ROLE_PERMISSIONS["approve_to_established"]` de transitie
#: daarom niet toestaat. Dit is de werkelijke huidige uitkomst; er wordt geen rol
#: toegekend om de keten "mooi af te maken".
VERWACHTE_APPROVE_FOUT = "Transitie van review naar ESTABLISHED niet toegestaan"


# --------------------------------------------------------------------------
# Leeshulpmiddelen
# --------------------------------------------------------------------------


def _verse_rij(db_path: Path, definitie_id: int) -> dict[str, Any] | None:
    """Lees de volledige rij via een **nieuwe** SQLite-verbinding.

    Bewust buiten elke repository om: een positief serviceantwoord bewijst geen
    duurzame rij. De verbinding wordt vanaf het moment van verkrijgen in een
    `finally` gesloten.
    """
    verbinding = sqlite3.connect(str(db_path))
    try:
        verbinding.row_factory = sqlite3.Row
        rij = verbinding.execute(
            "SELECT * FROM definities WHERE id = ?", (definitie_id,)
        ).fetchone()
        return dict(rij) if rij is not None else None
    finally:
        verbinding.close()


def _repository_verbinding(repository: Any) -> sqlite3.Connection | None:
    """De thread-local verbinding die deze repository zelf openhoudt.

    `DefinitieRepository.__init__` roept `init_database()` aan en houdt daarna
    één verbinding per thread vast in `_ThreadConnectionState`. Die verbinding is
    van ons zodra we de repository aanmaken; de leespaden in de servicelaag
    openen daarnaast per aanroep hun eigen verbinding en sluiten die zelf — daar
    blijven we van af.
    """
    toestand = getattr(repository.legacy_repo._db._thread_local, "state", None)
    return None if toestand is None else toestand.connection


@contextmanager
def _edit_service(db_path: Path, validation_service: Any) -> Iterator[Any]:
    """Echte editservice op een expliciet tijdelijk db-pad, met eigen opruiming.

    De `finally` sluit de verbinding die deze test zelf verkreeg — ook wanneer de
    body afbreekt op een verwachte rode assertie of een setupfout. Zonder dit
    blijft de verbinding open tot de garbage collector langskomt; de fixture
    ruimt alleen de containerinstanties op, niet onze eigen repository.
    """
    from services.definition_edit_repository import DefinitionEditRepository
    from services.definition_edit_service import DefinitionEditService

    repository: Any = None
    try:
        repository = DefinitionEditRepository(str(db_path))
        yield DefinitionEditService(
            repository=repository, validation_service=validation_service
        )
    finally:
        if repository is not None:
            toestand = getattr(repository.legacy_repo._db._thread_local, "state", None)
            if toestand is not None:
                toestand.close()


def _generatieprompt(oproepen: list[Any], begrip: str) -> str:
    """De ene providerprompt die de definitie voor `begrip` opvraagt."""
    marker = f"<begrip>{begrip}</begrip>"
    prompts = [oproep.prompt for oproep in oproepen if marker in oproep.prompt]
    assert len(prompts) == 1, (
        f"generatie: verwacht precies één definitieprompt voor {begrip!r}, "
        f"gezien: {len(prompts)}"
    )
    return prompts[0]


def _spiegel_gatepolicy(werkmap: Path) -> dict[str, Any]:
    """Spiegel `config/approval_gate.yaml` naar de tijdelijke werkmap.

    `GatePolicyService` opent dat pad **CWD-relatief**. Zonder deze spiegeling
    zou de gate stil op ingebouwde defaults draaien (met
    ``allow_hard_override=False``) en zou de test een andere policy meten dan de
    applicatie gebruikt. De inhoud wordt niet aangepast; het bestand in de
    repository blijft onaangeroerd.
    """
    bron = _PROJECTWORTEL / "config" / "approval_gate.yaml"
    assert bron.is_file(), f"gate-policy ontbreekt in de repository: {bron}"
    doel = werkmap / "config" / "approval_gate.yaml"
    doel.parent.mkdir(parents=True, exist_ok=True)
    doel.write_bytes(bron.read_bytes())
    return dict(yaml.safe_load(bron.read_text(encoding="utf-8")))


# --------------------------------------------------------------------------
# Bewijsstappen — pure assertiehelpers, gedeeld door journey en discriminatoren
# --------------------------------------------------------------------------


def _bewijs_generatie(respons: Any, oproepen: list[Any], begrip: str) -> None:
    """De vaste invoer bereikt de provider en de opgeschoonde tekst is exact."""
    assert (
        respons.success is True
    ), f"generatie: orchestrator meldde geen succes ({getattr(respons, 'error', None)})"
    assert respons.definition is not None, "generatie: geen definitieobject"
    assert (
        respons.definition.definitie == VERWACHTE_DEFINITIE
    ), f"generatie: opgeschoonde tekst wijkt af: {respons.definition.definitie!r}"
    assert (
        respons.definition.categorie == CATEGORIE
    ), f"generatie: categorie niet doorgegeven: {respons.definition.categorie!r}"
    assert isinstance(
        respons.definition.id, int
    ), f"generatie: geen numeriek id toegekend: {respons.definition.id!r}"

    prompt = _generatieprompt(oproepen, begrip)
    for waarde in (ORGANISATORISCH, JURIDISCH, WETTELIJK):
        assert (
            waarde in prompt
        ), f"generatie: contextwaarde {waarde!r} niet in de prompt"
    assert (
        f"<context>Organisatorisch: {ORGANISATORISCH}" in prompt
    ), "generatie: organisatorische context staat niet in het contextdatablok"
    # De opgegeven categorie stuurt de prompt aantoonbaar: de opbouw schakelt
    # naar het procesblok en noemt de categorie als opgegeven, te controleren
    # betekenisclaim (DEF-750: geen exclusieve klasse, geen markerregel).
    assert (
        f"opgegeven categorie **{CATEGORIE}**" in prompt
    ), f"generatie: categorie {CATEGORIE!r} stuurt de prompt niet aan"
    assert (
        "PROCES — activiteit als kern" in prompt
    ), "generatie: het procesblok ontbreekt in de prompt"
    assert (
        "Ontologische marker (lever als eerste regel)" not in prompt
    ), "generatie: de vervallen markerregel staat nog in de prompt"


def _bewijs_validatie(validatie: Any) -> None:
    """Er is werkelijk geëvalueerd met de actuele, volledige regelset."""
    assert isinstance(
        validatie, dict
    ), f"validatie: geen resultaatdict maar {type(validatie).__name__}"
    assert (
        validatie["validation_status"] == "validated"
    ), f"validatie: status is {validatie['validation_status']!r}"
    assert (
        "unknown_reason" not in validatie
    ), f"validatie: fail-closed reden aanwezig: {validatie.get('unknown_reason')!r}"

    systeem = validatie["system"]
    assert systeem["degraded_mode"] is False, "validatie: degraded mode actief"
    assert (
        systeem["degradation_reason"] is None
    ), f"validatie: degradatiereden {systeem['degradation_reason']!r}"
    assert (
        systeem["rules_loaded"] == 53
    ), f"validatie: {systeem['rules_loaded']} regels geladen i.p.v. 53"
    assert (
        systeem["rules_expected"] == 53
    ), f"validatie: {systeem['rules_expected']} regels verwacht i.p.v. 53"

    assert (
        validatie["evaluation_coverage"] == VERWACHTE_DEKKING
    ), f"validatie: dekking wijkt af: {validatie['evaluation_coverage']}"
    assert (
        validatie["overall_score"] == VERWACHTE_SCORE
    ), f"validatie: score {validatie['overall_score']} i.p.v. {VERWACHTE_SCORE}"
    assert (
        sorted(validatie["passed_rules"]) == VERWACHTE_GESLAAGDE_REGELS
    ), f"validatie: geslaagde regels wijken af: {sorted(validatie['passed_rules'])}"
    assert (
        sorted(overtreding["code"] for overtreding in validatie["violations"])
        == VERWACHTE_GEFAALDE_REGELS
    ), "validatie: gefaalde regels wijken af"


def _bewijs_int03_pass_op_bevroren_antwoord(
    validatie: Any, oproepen: list[Any], *, tekst: str
) -> None:
    """INT-03 slaagt op grond van het bevroren, aan `tekst` gebonden antwoord.

    De providergrens heeft precies één INT-03-prompt gezien met exact deze
    tekst als enige bewijsplaats; de dienst heeft het antwoord door de
    codecontrole gehaald (niets afgewezen) en de uitkomst is het onderbouwde
    `pass`/`clear`-oordeel: 'die' met het letterlijke antecedent
    'proefdefinitie' — geen technische fout, geen open vraag.
    """
    assert (
        validatie["rule_statuses"]["INT-03"] == "pass"
    ), f"INT-03: status is {validatie['rule_statuses'].get('INT-03')!r}"
    assert validatie["evaluation_coverage"]["error"] == 0, (
        "INT-03: de dekking telt een technische fout: "
        f"{validatie['evaluation_coverage']}"
    )
    document = validatie["rule_results"]["INT-03"]["assessment"]
    assert (
        document["status"] == "assessed"
    ), f"INT-03: beoordeling is {document['status']!r} ({document.get('error')})"
    assert document["rejected"] == [], f"INT-03: afgewezen: {document['rejected']}"
    assert (
        document["input"]["text_sha256"] == hashlib.sha256(tekst.encode()).hexdigest()
    ), "INT-03: beoordeling is niet aan de getoetste tekst gebonden"
    oordeel = document["judgment"]
    assert oordeel["verdict"] == "pass", f"INT-03: verdict is {oordeel['verdict']!r}"
    assert oordeel["status"] == "pass", f"INT-03: {oordeel['status']!r}"
    assert oordeel["finding"] == "clear", f"INT-03: {oordeel['finding']!r}"
    assert oordeel["question"] is None, f"INT-03: vraag {oordeel['question']!r}"
    [verwijzing] = oordeel["references"]
    assert (
        verwijzing["word"] == INT03_VERWIJZEND_WOORD
    ), f"INT-03: verwijzend woord {verwijzing['word']!r}"
    assert verwijzing["status"] == "clear", f"INT-03: {verwijzing['status']!r}"
    assert (
        verwijzing["passage"] in tekst
    ), f"INT-03: passage staat niet in de tekst: {verwijzing['passage']!r}"
    [kandidaat] = verwijzing["candidates"]
    assert (
        kandidaat["quote"] == INT03_ANTECEDENT
    ), f"INT-03: antecedent {kandidaat['quote']!r} i.p.v. {INT03_ANTECEDENT!r}"
    assert (
        f"{INT03_ANTECEDENT} {INT03_VERWIJZEND_WOORD}" in tekst
    ), "INT-03: het antecedent staat niet direct vóór het verwijzende woord"

    assert len(oproepen) == 1, f"INT-03: {len(oproepen)} beoordelingsprompts i.p.v. 1"
    assert (
        int03_definitie_uit_prompt(oproepen[0].prompt) == tekst
    ), "INT-03: de prompt draagt niet exact de getoetste tekst"
    assert (
        oproepen[0].temperature == 0.0
    ), f"INT-03: temperature {oproepen[0].temperature}"
    # Outputtokenlimiet (Chris, 26-09-2026: max 2500): het budget bereikt via de
    # echte AIServiceV2 ongewijzigd de providergrens.
    assert (
        oproepen[0].max_tokens == 2500
    ), f"INT-03: outputbudget {oproepen[0].max_tokens} i.p.v. 2500"


def _bewijs_opgeslagen_rij(
    rij: dict[str, Any] | None,
    *,
    tekst: str,
    status: str,
    versie: int,
) -> None:
    """De verse DB-lezing draagt exact de verwachte inhoud."""
    assert rij is not None, "opslag: geen rij gevonden bij dit id"
    assert rij["definitie"] == tekst, f"opslag: tekst wijkt af: {rij['definitie']!r}"
    assert rij["begrip"] == BEGRIP, f"opslag: begrip wijkt af: {rij['begrip']!r}"
    assert (
        rij["categorie"] == CATEGORIE
    ), f"opslag: categorie wijkt af: {rij['categorie']!r}"
    assert rij["status"] == status, f"opslag: status is {rij['status']!r}"
    assert (
        rij["version_number"] == versie
    ), f"opslag: versie is {rij['version_number']} i.p.v. {versie}"
    assert json.loads(rij["organisatorische_context"]) == [
        ORGANISATORISCH
    ], f"opslag: organisatorische context wijkt af: {rij['organisatorische_context']!r}"
    assert json.loads(rij["juridische_context"]) == [
        JURIDISCH
    ], f"opslag: juridische context wijkt af: {rij['juridische_context']!r}"
    assert json.loads(rij["wettelijke_basis"]) == [
        WETTELIJK
    ], f"opslag: wettelijke basis wijkt af: {rij['wettelijke_basis']!r}"


def _bewijs_geschiedenis(historie: list[dict[str, Any]]) -> None:
    """De bewerking staat met oude tekst, actor en reden in de geschiedenis."""
    met_reden = [
        regel for regel in historie if regel.get("wijziging_reden") == WIJZIGINGSREDEN
    ]
    assert (
        len(met_reden) == 1
    ), f"geschiedenis: {len(met_reden)} regels met de wijzigingsreden i.p.v. 1"
    regel = met_reden[0]
    assert (
        regel["definitie_oude_waarde"] == VERWACHTE_DEFINITIE
    ), f"geschiedenis: oude waarde wijkt af: {regel['definitie_oude_waarde']!r}"
    assert (
        regel["definitie_nieuwe_waarde"] == NIEUWE_DEFINITIE
    ), f"geschiedenis: nieuwe waarde wijkt af: {regel['definitie_nieuwe_waarde']!r}"
    assert (
        regel["gewijzigd_door"] == REDACTEUR
    ), f"geschiedenis: actor is {regel['gewijzigd_door']!r}"
    assert (
        regel["wijziging_type"] == "updated"
    ), f"geschiedenis: type is {regel['wijziging_type']!r}"


def _bewijs_reviewrij(
    rij: dict[str, Any] | None, *, versie: int = 3, actor: str = INDIENER
) -> None:
    """Na indienen staat de rij aantoonbaar in review, met opgehoogde versie.

    De statuswijziging verbruikt zélf een versienummer (2 → 3). Dat is relevant
    voor de reviewer: het snapshot dat hij beoordeelt heeft een ander
    versienummer dan de bewerking die hij las. De vastgelegde CON-02-
    uitzondering verbruikt daarna opnieuw een versie (3 → 4) en zet de
    beoordelaar als handelende gebruiker.
    """
    assert rij is not None, "review: geen rij gevonden bij dit id"
    assert rij["status"] == "review", f"review: status is {rij['status']!r}"
    assert (
        rij["version_number"] == versie
    ), f"review: versie is {rij['version_number']} i.p.v. {versie}"
    assert rij["updated_by"] == actor, f"review: indiener is {rij['updated_by']!r}"
    assert (
        rij["definitie"] == NIEUWE_DEFINITIE
    ), f"review: beoordeelde tekst wijkt af: {rij['definitie']!r}"


def _bewijs_gate_geblokkeerd_zonder_bronbewijs(gate: dict[str, Any]) -> None:
    """Vóór de deskundige uitzondering blokkeert CON-02 (nog te beoordelen).

    Drie open onderdelen, elk met een eigen reden, náást de generieke
    scorereden: de gate laat geen reden vallen en maakt van ontbrekend
    bronbewijs geen 'override_required'.
    """
    assert gate["status"] == "blocked", f"review: gate vóór uitzondering: {gate}"
    redenen = gate["reasons"]
    for onderdeel in CON02_ONDERDELEN:
        assert any(
            r.startswith("CON-02 Nog te beoordelen") and onderdeel in r for r in redenen
        ), f"review: CON-02-blokkade voor {onderdeel!r} ontbreekt: {redenen}"
    assert VERWACHTE_SCOREREDEN in redenen, f"review: scorereden ontbreekt: {redenen}"
    assert (
        len(redenen) == len(CON02_ONDERDELEN) + 1
    ), f"review: onverwachte reden: {redenen}"


def _bewijs_uitzondering_vastgelegd(
    repository: Any, definitie_id: int, *, versie: int
) -> dict[str, Any]:
    """De uitzondering staat op het record, gebonden aan versie en vingerafdruk.

    Gelezen via de repository (de route van gate en export), niet via de invoer:
    een geaccepteerd commando bewijst nog geen duurzame, gebonden review.
    """
    record = repository.get_definitie(definitie_id)
    assert record is not None, "review: record na uitzondering niet gevonden"
    velden = record.get_contractvelden()
    review = velden.get("source_review")
    assert isinstance(
        review, dict
    ), f"review: geen uitzondering op het record: {velden!r}"
    assert review["type"] == "no_appropriate_source", review
    assert review["accepted"] is True, review
    assert review["actor"] == BEOORDELAAR, review
    assert review["version_number"] == versie, review
    assert review["search"]["conclusion"] == GEDOCUMENTEERD_ZOEKEN["conclusion"], review
    return review


def _bewijs_reviewbesluit(
    indienen: Any, gate: dict[str, Any], vaststellen: Any
) -> None:
    """Indienen slaagt; de gate en de vaststelpoging leveren hun exacte uitkomst."""
    assert (
        indienen.success is True
    ), f"review: indienen mislukte ({indienen.error_message})"
    assert (
        indienen.new_status == "review"
    ), f"review: nieuwe status is {indienen.new_status!r}"
    assert indienen.updated_by == INDIENER, f"review: actor is {indienen.updated_by!r}"

    assert gate == VERWACHTE_GATE, f"review: gate-uitkomst wijkt af: {gate}"

    assert vaststellen.success is False, (
        "review: vaststellen slaagde onverwacht — een rolloze synthetische actor "
        "hoort de ESTABLISHED-transitie niet te passeren"
    )
    assert (
        vaststellen.error_message == VERWACHTE_APPROVE_FOUT
    ), f"review: foutmelding wijkt af: {vaststellen.error_message!r}"
    assert (
        vaststellen.new_status is None
    ), f"review: er is toch een status gezet: {vaststellen.new_status!r}"


def _bewijs_exportbestand(
    export_resultaat: dict[str, Any], rij: dict[str, Any]
) -> None:
    """Parse het werkelijk geschreven JSON-bestand en toets het tegen de rij.

    Geen payload-, pad- of bestaat-assertie: het bestand wordt geopend, met
    `json.loads` geparseerd en veld voor veld vergeleken met de verse DB-lezing.
    """
    assert (
        export_resultaat["success"] is True
    ), f"export: export meldde geen succes ({export_resultaat.get('error')})"
    bestand = Path(export_resultaat["path"])
    assert bestand.is_file(), f"export: geen bestand op {bestand}"
    inhoud = json.loads(bestand.read_text(encoding="utf-8"))

    assert (
        inhoud["export_info"]["format"] == "json"
    ), f"export: formaat is {inhoud['export_info']['format']!r}"
    definitieblok = inhoud["definitie"]
    assert (
        definitieblok["begrip"] == rij["begrip"]
    ), f"export: begrip wijkt af: {definitieblok['begrip']!r}"
    assert definitieblok["definitie_origineel"] == rij["definitie"], (
        "export: tekst wijkt af van de opgeslagen rij: "
        f"{definitieblok['definitie_origineel']!r}"
    )
    assert (
        definitieblok["definitie_gecorrigeerd"] == rij["definitie"]
    ), f"export: gecorrigeerde tekst wijkt af: {definitieblok['definitie_gecorrigeerd']!r}"

    metadata = inhoud["metadata"]
    assert metadata["id"] == rij["id"], f"export: id wijkt af: {metadata['id']!r}"
    assert (
        metadata["status"] == rij["status"]
    ), f"export: status wijkt af: {metadata['status']!r}"
    assert (
        metadata["versie"] == rij["version_number"]
    ), f"export: versie wijkt af: {metadata['versie']!r}"
    assert (
        metadata["categorie"] == rij["categorie"]
    ), f"export: categorie wijkt af: {metadata['categorie']!r}"
    assert (
        inhoud["context"] == CONTEXT
    ), f"export: context wijkt af: {inhoud['context']}"


# --------------------------------------------------------------------------
# De journey
# --------------------------------------------------------------------------


async def test_offline_kernjourney_van_generatie_tot_export(
    bevroren_omgeving,  # noqa: F811
) -> None:
    """Genereer, sla op, bewerk, dien in ter review en exporteer — offline."""
    from services.service_factory import ServiceAdapter

    omgeving = bevroren_omgeving
    policybestand = _spiegel_gatepolicy(omgeving.werkmap)

    # --- 1. generatie ---------------------------------------------------
    adapter = ServiceAdapter(omgeving.container)
    respons = await adapter.generate_definition(
        begrip=BEGRIP, context_dict=CONTEXT, categorie=CATEGORIE
    )
    _bewijs_generatie(respons, omgeving.client.oproepen, BEGRIP)
    definitie_id = respons.definition.id

    # --- 2. echte validatie ---------------------------------------------
    _bewijs_validatie(respons.validation_result)

    # --- 3. opslag, teruggelezen via een verse verbinding -----------------
    rij = _verse_rij(omgeving.db_path, definitie_id)
    _bewijs_opgeslagen_rij(rij, tekst=VERWACHTE_DEFINITIE, status="draft", versie=1)
    # Tweede, onafhankelijke leesroute (de helper van de fixture) op dezelfde
    # rij: twee losse verbindingen moeten hetzelfde zien.
    kern = lees_opgeslagen_definitie(omgeving.db_path, definitie_id)
    assert kern == {
        "id": definitie_id,
        "begrip": BEGRIP,
        "definitie": VERWACHTE_DEFINITIE,
        "categorie": CATEGORIE,
        "status": "draft",
        "version_number": 1,
    }, f"opslag: tweede leesroute ziet iets anders: {kern}"
    # Waarneming, bewust géén assertie: `validation_score` staat vandaag niet op
    # de rij hoewel er echt gevalideerd is. Het ontbreken van die Fase-A-garantie
    # is geen gewenst productgedrag en wordt hier dus niet vastgelegd. De rode
    # verwachting voor aanwezigheid en actualiteit hoort onder DEF-627/DEF-630.

    # --- 4. bewerken via de echte editservice ----------------------------
    # De échte validatieservice van dezelfde container gaat mee; haar API is
    # async, dus de editservice slaat hervalidatie over (DEF-626/DEF-627). Dat is
    # een waarneming en geen verwachting: er staat hier bewust geen assertie die
    # `validation is None` als gewenst gedrag vastlegt.
    with _edit_service(
        omgeving.db_path, omgeving.container.validation_orchestrator()
    ) as edit_service:
        sessie = edit_service.start_edit_session(definitie_id, user=REDACTEUR)
        assert (
            sessie["success"] is True
        ), f"edit: sessie mislukte ({sessie.get('error')})"
        assert (
            sessie["definition"].definitie == VERWACHTE_DEFINITIE
        ), f"edit: sessie toont een andere tekst: {sessie['definition'].definitie!r}"
        assert sessie["user"] == REDACTEUR, f"edit: actor is {sessie['user']!r}"

        bewaard = edit_service.save_definition(
            definitie_id,
            {"definitie": NIEUWE_DEFINITIE},
            user=REDACTEUR,
            reason=WIJZIGINGSREDEN,
        )
        assert (
            bewaard["success"] is True
        ), f"edit: opslaan mislukte ({bewaard.get('error')})"
        assert (
            bewaard["definition_id"] == definitie_id
        ), f"edit: ander id teruggekregen: {bewaard['definition_id']!r}"

        rij_na_edit = _verse_rij(omgeving.db_path, definitie_id)
        _bewijs_opgeslagen_rij(
            rij_na_edit, tekst=NIEUWE_DEFINITIE, status="draft", versie=2
        )
        assert (
            rij_na_edit["updated_by"] == REDACTEUR
        ), f"edit: updated_by is {rij_na_edit['updated_by']!r}"
        _bewijs_geschiedenis(edit_service.get_version_history(definitie_id))

    # --- 5. review: aanvraag, gate en werkelijke uitkomst -----------------
    workflow = omgeving.container.definition_workflow_service()
    policy = workflow.gate_policy_service.get_policy()
    assert (
        policy.soft_requirements["allow_hard_override"]
        is policybestand["soft_requirements"]["allow_hard_override"]
    ), "review: de geladen policy komt niet uit config/approval_gate.yaml"

    indienen = workflow.submit_for_review(
        definitie_id, user=INDIENER, notes="synthetische reviewaanvraag"
    )
    rij_in_review = _verse_rij(omgeving.db_path, definitie_id)
    _bewijs_reviewrij(rij_in_review)

    # DEF-743 (CON-02): zonder bronbewijs blokkeert de gate — vóór enige
    # uitzondering. Dit is de norm en wordt hier eerst bewezen.
    _bewijs_gate_geblokkeerd_zonder_bronbewijs(workflow.preview_gate(definitie_id))

    # De deskundige legt de gedocumenteerde uitzondering "geen passende bron"
    # vast via de echte repositorycommand (optimistic lock op de beoordeelde
    # versie, vingerafdruk over het OPGESLAGEN record zoals D die herberekent:
    # begrip, definitiezin, contextlijsten, opgeslagen bronset, peildatum).
    from domain.sources.contract import bereken_bronvingerafdruk

    repository = omgeving.container.repository()
    record_in_review = repository.get_definitie(definitie_id)
    assert record_in_review is not None, "review: record niet leesbaar via repository"
    bewijs = record_in_review.get_source_evidence() or {}
    assert not (bewijs.get("sources") or []), (
        "review: deze journey hoort geen bronnen te dragen; de uitzondering "
        f"'geen passende bron' is dan niet de juiste route: {bewijs.get('sources')!r}"
    )
    uitzondering = {
        "type": "no_appropriate_source",
        "accepted": True,
        "actor": BEOORDELAAR,
        "rationale": UITZONDERINGSMOTIVERING,
        "version_number": rij_in_review["version_number"],
        "fingerprint": bereken_bronvingerafdruk(
            record_in_review.begrip,
            record_in_review.get_definitie_tekst(),
            record_in_review.get_contextlijsten(),
            bewijs.get("sources") or [],
            peildatum=bewijs.get("peildatum"),
        ),
        "reviewed_at": None,
        "search": dict(GEDOCUMENTEERD_ZOEKEN),
    }
    assert repository.set_source_review(
        definitie_id,
        uitzondering,
        BEOORDELAAR,
        expected_version=rij_in_review["version_number"],
    ), "review: de uitzondering is niet vastgelegd (versieconflict of afwijzing)"
    rij_met_uitzondering = _verse_rij(omgeving.db_path, definitie_id)
    _bewijs_reviewrij(rij_met_uitzondering, versie=4, actor=BEOORDELAAR)
    _bewijs_uitzondering_vastgelegd(repository, definitie_id, versie=4)

    # Mét de geaccepteerde uitzondering blijft alleen de generieke scoregate
    # (DEF-630) over: `override_required`, niet 'pass' — de uitzondering is
    # geen goedkeuring en de rolloze actor kan nog steeds niet vaststellen.
    gate = workflow.preview_gate(definitie_id)
    vaststellen = workflow.approve(
        definitie_id,
        user=BEOORDELAAR,
        notes="synthetische override-reden bij ontbrekende score",
        expected_version=rij_met_uitzondering["version_number"],
    )
    _bewijs_reviewbesluit(indienen, gate, vaststellen)

    rij_na_review = _verse_rij(omgeving.db_path, definitie_id)
    _bewijs_reviewrij(rij_na_review, versie=4, actor=BEOORDELAAR)
    assert (
        rij_na_review["approved_by"] is None
    ), f"review: er is toch vastgesteld door {rij_na_review['approved_by']!r}"

    # --- 6. export --------------------------------------------------------
    export_service = omgeving.container.export_service()
    assert export_service.export_dir.resolve().is_relative_to(
        omgeving.werkmap.resolve()
    ), f"export: schrijft buiten de tijdelijke werkmap ({export_service.export_dir})"

    export_resultaat = adapter.export_definition(
        definition_id=definitie_id, format="json"
    )
    _bewijs_exportbestand(export_resultaat, rij_na_review)

    # Discriminator op dezelfde, échte exportuitvoer: een geparseerd bestand dat
    # niet de actuele rij beschrijft moet worden verworpen. Deze stap wordt pas
    # bereikt zodra de export weer een bestand oplevert; vandaag valt de journey
    # hierboven om op de datetime-serialisatiegrens.
    with pytest.raises(AssertionError, match=r"^export: tekst wijkt af"):
        _bewijs_exportbestand(export_resultaat, rij)


# --------------------------------------------------------------------------
# Discriminatoren: bewijst dat elke stap werkelijk bewaakt wordt
# --------------------------------------------------------------------------


async def test_discriminatoren_bewaken_elke_stap(
    bevroren_omgeving,  # noqa: F811
) -> None:
    """Sla per stap de échte actie over en toon dat de assertie dan valt.

    Er wordt geen productiebron gemuteerd: elke discriminator laat een stap uit
    de journey weg of voert gerichte synthetische defectinvoer aan door de
    bevroren providergrens op ``leeg`` te zetten.
    """
    from services.service_factory import ServiceAdapter

    omgeving = bevroren_omgeving
    _spiegel_gatepolicy(omgeving.werkmap)

    adapter = ServiceAdapter(omgeving.container)
    respons = await adapter.generate_definition(
        begrip=BEGRIP, context_dict=CONTEXT, categorie=CATEGORIE
    )
    _bewijs_generatie(respons, omgeving.client.oproepen, BEGRIP)
    definitie_id = respons.definition.id
    rij_na_generatie = _verse_rij(omgeving.db_path, definitie_id)

    # --- opslag overgeslagen: er is geen rij -----------------------------
    with pytest.raises(AssertionError, match=r"^opslag: geen rij"):
        _bewijs_opgeslagen_rij(
            _verse_rij(omgeving.db_path, definitie_id + 10_000),
            tekst=VERWACHTE_DEFINITIE,
            status="draft",
            versie=1,
        )

    # --- edit overgeslagen: tekst en versie staan nog op de generatie ----
    with pytest.raises(AssertionError, match=r"^opslag: tekst wijkt af"):
        _bewijs_opgeslagen_rij(
            rij_na_generatie, tekst=NIEUWE_DEFINITIE, status="draft", versie=2
        )
    with (
        _edit_service(
            omgeving.db_path, omgeving.container.validation_orchestrator()
        ) as edit_service,
        pytest.raises(AssertionError, match=r"^geschiedenis: 0 regels"),
    ):
        _bewijs_geschiedenis(edit_service.get_version_history(definitie_id))

    # --- review overgeslagen: de rij staat nog op draft ------------------
    with pytest.raises(AssertionError, match=r"^review: status is 'draft'"):
        _bewijs_reviewrij(rij_na_generatie)

    # De exportdiscriminator staat bij de journey zelf: hij toetst een werkelijk
    # geschreven en geparseerd JSON-bestand, en er is vandaag geen bestand omdat
    # de serialisatiegrens breekt. Een payload of half geschreven artefact zou
    # geen geslaagde export vervangen, dus die route staat hier bewust niet.

    # --- generatie met defecte provider: de tekst klopt niet meer --------
    # De bevroren grens levert een lege respons. De orchestrator meldt dan nog
    # steeds `success=True` en slaat de lege tekst zelfs op; precies daarom
    # bewaakt de assertie de *tekst* en niet alleen de succesvlag.
    omgeving.zet_modus("leeg")
    lege_respons = await adapter.generate_definition(
        begrip=BEGRIP_DISCRIMINATOR, context_dict=CONTEXT, categorie=CATEGORIE
    )
    with pytest.raises(
        AssertionError, match=r"^generatie: opgeschoonde tekst wijkt af"
    ):
        _bewijs_generatie(lege_respons, omgeving.client.oproepen, BEGRIP_DISCRIMINATOR)


async def test_int03_bevroren_antwoord_discrimineert(
    bevroren_omgeving,  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """INT-03 slaagt dankzij het bevroren antwoord, niet dankzij een vangnet.

    DEF-772: dezelfde echte toetsroute als de journey (`ValidationOrchestratorV2`
    → `Int03AssessmentService` → providergrens) op dezelfde tekst. Zonder
    geldig antwoord — de generieke definitietekst als modeluitvoer, een lege
    respons, of helemaal geen INT-03-routing (precies wat de grens vóór deze
    routing deed: de CI-fout op PR #482) — is INT-03 een technische fout, telt
    de dekking één `error` en valt de dekkingsassertie van de journey. Mét het
    bevroren antwoord is INT-03 `pass` met een aan exact deze tekst gebonden,
    door code geverifieerd `clear`-oordeel met het letterlijke antecedent. Een
    technische fout is dus nooit de gewenste uitkomst en de verwachting kan
    niet zonder het antwoord slagen. Alleen het antwoord op, of de herkenning
    van, de INT-03-prompt wordt vervangen; prompt, dienst, validatie en dekking
    zijn productiecode.
    """
    from services.service_factory import ServiceAdapter
    from services.validation.interfaces import ValidationContext

    omgeving = bevroren_omgeving
    _spiegel_gatepolicy(omgeving.werkmap)
    grens = sys.modules[type(omgeving.client).__module__]
    bevroren_antwoord = grens.int03_bevroren_antwoord
    bevroren_herkenning = grens.is_int03_beoordelingsprompt
    orchestrator = omgeving.container.validation_orchestrator()
    context = ValidationContext(
        metadata={
            "organisatorische_context": [ORGANISATORISCH],
            "juridische_context": [JURIDISCH],
            "wettelijke_basis": [WETTELIJK],
        }
    )

    def _int03_prompts() -> list[Any]:
        """Elke providerprompt die exact de getoetste tekst als bewijsplaats draagt,
        ongeacht of de grens haar als INT-03 herkende."""
        return [
            oproep
            for oproep in omgeving.client.oproepen
            if int03_definitie_uit_prompt(oproep.prompt) == VERWACHTE_DEFINITIE
        ]

    # --- zonder geldig antwoord op uitsluitend de INT-03-prompt --------------
    # Eerst, op een lege dienstcache: `Int03AssessmentService` (één instantie
    # per container) onthoudt alleen gelukte beoordelingen, dus elke variant
    # bereikt aantoonbaar de grens met precies één INT-03-prompt.
    varianten: list[tuple[str, str, Any]] = [
        (
            "generieke definitietekst als modeluitvoer",
            "int03_bevroren_antwoord",
            lambda _p: DEFINITIE_TEKST,
        ),
        ("lege respons", "int03_bevroren_antwoord", lambda _p: ""),
        # Zonder herkenning valt de prompt terug op het generieke antwoordboek
        # (de definitietekst): het gedrag van de grens vóór DEF-772.
        ("zonder INT-03-routing", "is_int03_beoordelingsprompt", lambda _p: False),
    ]
    for etiket, naam, vervanging in varianten:
        omgeving.zet_modus("geldig")  # wist oproepen en AI-cache
        monkeypatch.setattr(grens, "int03_bevroren_antwoord", bevroren_antwoord)
        monkeypatch.setattr(grens, "is_int03_beoordelingsprompt", bevroren_herkenning)
        monkeypatch.setattr(grens, naam, vervanging)
        defect = await orchestrator.validate_text(
            BEGRIP, VERWACHTE_DEFINITIE, CATEGORIE, context
        )
        assert (
            len(_int03_prompts()) == 1
        ), f"{etiket}: {len(_int03_prompts())} INT-03-prompts i.p.v. 1"
        assert (
            defect["rule_statuses"]["INT-03"] == "error"
        ), f"{etiket}: INT-03 is {defect['rule_statuses'].get('INT-03')!r}"
        document = defect["rule_results"]["INT-03"]["assessment"]
        assert (
            document["status"] == "error"
        ), f"{etiket}: beoordeling is {document['status']!r}"
        assert document["judgment"] is None, f"{etiket}: toch een oordeel"
        assert (
            defect["evaluation_coverage"]["error"] == 1
        ), f"{etiket}: dekking {defect['evaluation_coverage']}"
        with pytest.raises(AssertionError, match=r"^validatie: dekking wijkt af"):
            _bewijs_validatie(defect)
        with pytest.raises(AssertionError, match=r"^INT-03: status is 'error'"):
            _bewijs_int03_pass_op_bevroren_antwoord(
                defect, _int03_prompts(), tekst=VERWACHTE_DEFINITIE
            )

    # --- mét het bevroren antwoord: de journeyroute -------------------------
    monkeypatch.setattr(grens, "int03_bevroren_antwoord", bevroren_antwoord)
    monkeypatch.setattr(grens, "is_int03_beoordelingsprompt", bevroren_herkenning)
    omgeving.zet_modus("geldig")
    adapter = ServiceAdapter(omgeving.container)
    respons = await adapter.generate_definition(
        begrip=BEGRIP, context_dict=CONTEXT, categorie=CATEGORIE
    )
    _bewijs_generatie(respons, omgeving.client.oproepen, BEGRIP)
    _bewijs_validatie(respons.validation_result)
    _bewijs_int03_pass_op_bevroren_antwoord(
        respons.validation_result,
        omgeving.client.oproepen_van(INT03_SOORT),
        tekst=VERWACHTE_DEFINITIE,
    )
    assert omgeving.client.oproepen_van(INT03_SOORT) == _int03_prompts()
    document = respons.validation_result["rule_results"]["INT-03"]["assessment"]
    assert (
        document["attribution"]["cached"] is False
    ), "INT-03: de beoordeling kwam uit de dienstcache, niet van de grens"


class _SynthetischeInjectieError(RuntimeError):
    """Alleen voor de opruimcontrole; geen productiefoutklasse."""


def _injecteer_fout_tijdens_bewerken(db_path: Path, gezien: dict[str, Any]) -> None:
    """Breek middenin een bewerksessie af, met de geopende verbinding vastgelegd."""
    with _edit_service(db_path, None) as edit_service:
        gezien["repository"] = edit_service.repository
        verbinding = _repository_verbinding(edit_service.repository)
        assert verbinding is not None, (
            "cleanup: de repository hield geen eigen verbinding open — dan is "
            "deze opruiming zinloos en moet de aanname herzien worden"
        )
        gezien["verbinding"] = verbinding
        raise _SynthetischeInjectieError("synthetische fout midden in de bewerking")


async def test_editservice_ruimt_eigen_verbinding_op(
    bevroren_omgeving,  # noqa: F811
) -> None:
    """Gerichte foutinjectie: de `finally` sluit de zelf geopende verbinding.

    Er ontstaat werkelijk een resource — `DefinitieRepository.__init__` opent via
    `init_database()` een thread-local verbinding — dus die opruiming moet
    bewezen worden, ook wanneer de body afbreekt.
    """
    omgeving = bevroren_omgeving
    gezien: dict[str, Any] = {}
    with pytest.raises(_SynthetischeInjectieError):
        _injecteer_fout_tijdens_bewerken(omgeving.db_path, gezien)

    assert (
        _repository_verbinding(gezien["repository"]) is None
    ), "cleanup: de thread-local verbinding is niet losgelaten"
    with pytest.raises(sqlite3.ProgrammingError):
        gezien["verbinding"].execute("SELECT 1")
