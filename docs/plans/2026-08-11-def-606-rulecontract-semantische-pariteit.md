# DEF-606 Rulecontract en semantische pariteit — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Maak de 53 JSON-regels één gevalideerd uitvoerbaar contract, herstel het contextcontract, classificeer alle regels naar toetsbaarheid en implementeer de normatieve betekenis zonder de oude Pythonvalidatorlagen te activeren of niet-uitgevoerde regels als pass te scoren.

**Architecture:** `config/toetsregels/toetsregels_config.yaml` blijft de root-SSOT en wijst uitsluitend het actieve JSON-runtimeformaat en de contractpolicy aan. De 53 JSON-bestanden zijn de uitvoerbare regelrecords daaronder. Een typed RuleRecord declareert één evaluatorstrategie en vereiste invoer; een centraal register resolveert generieke en gespecialiseerde evaluators. `ModularValidationService` blijft voorlopig orchestration, scoring en aggregatie doen. Context en repositorydata worden expliciet via `EvaluationContext` aangeleverd.

**Tech Stack:** Python 3.13, Pydantic/dataclasses volgens bestaand projectpatroon, pytest/pytest-asyncio, JSON-regelrecords, SQLite-repository, ruff/black.

---

## Besluiten en begrenzing

- ADR: `docs/adr/ADR-001-json-rulecontract-en-evaluatorstrategie.md`.
- Linear parent: DEF-606.
- Contextwerk: DEF-622.
- Semantische regelpariteit: DEF-623.
- Toetsbaarheidsclassificatie en scorepolicy: DEF-624.
- ASTRA-herkomst en drift: DEF-625.
- Bestaande runtime-defecten: DEF-621.
- Gedragssuite: DEF-503.
- Latere god-objectextractie: DEF-424.
- Oude Pythonlagen worden in dit plan niet verwijderd. Stop voor verwijdering en vraag Chris afzonderlijk toestemming.
- Voeg geen dependency, schemawijziging of brekend contract toe zonder voorafgaande toestemming.
- Werk niet direct op `main` en behoud alle bestaande gebruikerswijzigingen.

## Eerst beantwoorden in Linear

Plaats vóór implementatie een comment `Specificatie afgerond` op DEF-622 en
DEF-623 met de gekozen antwoorden:

1. Contextnormalisatie: alleen trim/casefold/deduplicatie/volgorde of ook aliasmapping?
2. Exact duplicaat: blokkeren of force-duplicate met auditreden behouden?
3. Nederlandse morfologie: bestaande conservatieve heuristiek of goedgekeurde dependency?
4. SAM-05: realtime tekstvalidatie of integriteitscontrole bij opslaan/vaststellen?
5. Oordeelregels: gecontroleerde AI-jury, verplichte menselijke review of per regel een keuze?
6. Welke `review_required`-regels blokkeren vaststellen/exporteren?
7. Hoe worden kwaliteitsscore en evaluatiedekking afzonderlijk berekend en getoond?
8. Is ASTRA-prioriteit leidend of mag een gedocumenteerde projectoverride bestaan?

## Task 1: Bevries het huidige gedrag met RED-contracttests

**Files:**
- Modify: `tests/unit/validation/test_rule_runtime_matrix.py`
- Modify: `tests/fixtures/toetsregels/runtime_cases.yaml`
- Create: `tests/unit/validation/test_rule_contract.py`

**Step 1:** Voeg falende tests toe die voor alle 53 JSON-records `evaluator`,
`required_inputs` en een geldige scoringpolicy eisen.

**Step 2:** Voeg expliciete RED-cases toe voor:

- onbekend evaluatortype;
- ontbrekende vereiste invoer;
- dubbele of ontbrekende evaluatorregistratie;
- SAM-06 die nu nog `defect_inert` is;
- SAM-05-cycli van diepte 2 en 3;
- VER-03 met zelfstandig naamwoord `besluit`;
- CON-01 zonder contextmetadata.

**Step 2a:** Lees voor alle 44 JSON-records met zowel `goede_voorbeelden` als
`foute_voorbeelden` ten minste het eerste paar rechtstreeks in. Eis dat een
automatisch geclassificeerde regel het foute voorbeeld slechter beoordeelt dan
het goede. Een uitzondering vereist een expliciet goedgekeurde reviewpolicy;
geen stille xfail/skip.

**Step 3:** Draai:

```bash
.venv/bin/python -m pytest -q \
  tests/unit/validation/test_rule_contract.py \
  tests/unit/validation/test_rule_runtime_matrix.py
```

Expected: FAIL op ontbrekend RuleRecord/evaluatorcontract en de genoemde
semantische gaten; bestaande niet-gerelateerde cases blijven groen.

**Step 4:** Leg het RED-bewijs vast in het werklog/Linear-comment. Commit alleen
na expliciete toestemming en stage uitsluitend de genoemde files.

## Task 2: Introduceer een typed RuleRecord

**Files:**
- Create: `src/toetsregels/runtime_contract.py`
- Modify: `config/toetsregels/toetsregels_config.yaml`
- Modify: `src/toetsregels/rule_cache.py`
- Modify: `src/toetsregels/manager.py`
- Test: `tests/unit/validation/test_rule_contract.py`

**Step 1:** Definieer een gesloten set evaluatortypen en required-inputnamen.
Minimaal: `generic`, `positive_indicator`, `lemma_morphology`,
`definition_grammar`, `qualification`, `definition_overlap`, `compound`,
`definition_graph`, `preferred_term`, `context_metadata`.

Definieer daarnaast gesloten waarden voor uitvoerbaarheidsklasse,
automatiseringsstatus, resultaatstatus en scorepolicy. Resultaatstatus bevat
minimaal `pass`, `fail`, `review_required`, `not_evaluated` en `error`.

**Step 2:** Valideer ieder JSON-record bij laden. Behoud promptmetadata, maar
weiger onbekende evaluatorwaarden, ontbrekende vereiste velden, ID/bestandsnaam-
drift en ongeldige scoringstatus.

**Step 2a:** Maak de root-SSOT consistent met ADR-001: zet alleen JSON als actief
runtimeformaat, voeg de nieuwe verplichte contractvelden toe en verwijder de
runtime-eis dat beide formaten aanwezig/synchroon zijn. Verwijder in deze fase
geen bestanden.

**Step 3:** Maak loaderfalen zichtbaar en fail-closed volgens de beslissing uit
DEF-621; geen `logger.error + continue` dat stil een regel verwijdert.

**Step 4:** Vul de nieuwe contractvelden in alle 53 JSON-regelrecords. Dit is een
wijziging over meer dan vijf bestanden: vraag Chris vooraf expliciete toestemming
en voer het mechanisch/reviewbaar uit.

**Step 5:** Draai de contracttests. Expected: contracttests groen; semantische
RED-tests blijven rood.

## Task 2a: Classificeer alle 53 regels — DEF-624

**Files:**
- Modify: `config/toetsregels/toetsregels_config.yaml`
- Modify: `src/toetsregels/regels/*.json`
- Modify: `tests/fixtures/toetsregels/runtime_cases.yaml`
- Test: `tests/unit/validation/test_rule_contract.py`

**Step 1:** Beoordeel per rule-ID de norm, vereiste invoer en betrouwbare
detectiestrategie. Gebruik als startpunt, niet als onbewezen einduitkomst:

- repositorykandidaten: SAM-01, SAM-02, SAM-03, SAM-05, SAM-08, DUP-01;
- oordeelskandidaten: ARAI-03, ESS-01, ESS-04, INT-02, INT-06, STR-03, STR-05,
  STR-06;
- deterministisch implementatiegat: VER-03.

**Step 2:** Leg de classificatie en motivatie in ieder RuleRecord vast. Een
schijnzekere regex is geen geldige vervanging voor `review_required`.

**Step 3:** Laat contracttests falen wanneer een regel geen classificatie,
vereiste invoer, resultaatpolicy of scorepolicy heeft.

**Step 4:** Dit raakt meer dan vijf bestanden. Vraag Chris vóór de wijziging
expliciet toestemming en voer de recordmigratie mechanisch en reviewbaar uit.

## Task 3: Bouw evaluatorinterface en register

**Files:**
- Create: `src/services/validation/evaluators/__init__.py`
- Create: `src/services/validation/evaluators/base.py`
- Create: `src/services/validation/evaluators/registry.py`
- Create: `src/services/validation/evaluators/generic.py`
- Modify: `src/services/validation/modular_validation_service.py`
- Create: `tests/unit/validation/evaluators/test_registry.py`

**Step 1:** Schrijf RED-tests voor exact één evaluator per type, onbekend type en
ontbrekende required inputs.

**Step 2:** Maak één evaluatorprotocol met input `RuleRecord` +
`EvaluationContext` en output die zonder adapterverlies in `RuleResult` past.

**Step 3:** Registreer evaluators expliciet; geen dynamische bestandsimport en
geen fallback naar default-pass bij onbekende types.

**Step 4:** Verplaats uitsluitend de bestaande generieke patroon-/lengtewerking
naar `generic.py`. Wijzig nog geen regelgedrag.

**Step 5:** Routeer vanuit `ModularValidationService` via het register en behoud
scoring/aggregatie/outputcompatibiliteit.

**Step 6:** Draai registertests, bestaande JSON-validatortests en de 53×-matrix.

## Task 4: Herstel contexttransport en harde contextinvariant — DEF-622

**Files:**
- Modify: `src/services/orchestrators/validation_orchestrator_v2.py`
- Modify: `src/services/validation/types_internal.py`
- Modify: `src/services/definition_workflow_service.py`
- Modify: `config/approval_gate.yaml`
- Create: `tests/unit/services/orchestrators/test_validation_context_passthrough.py`
- Create: `tests/integration/validation/test_con01_context_contract.py`

**Step 1:** Schrijf RED-tests dat de drie contextlijsten uit `Definition` via
`ValidationContext` in `EvaluationContext.metadata` terechtkomen.

**Step 2:** Schrijf RED-tests voor geen context: service-/workflowgate weigert en
de algemene hard-override kan deze specifieke invariant niet passeren.

**Step 3:** Gebruik of vervang `_enrich_context_with_definition_fields`; laat geen
ongebruikte tweede route bestaan.

**Step 4:** Centraliseer contextnormalisatie volgens het antwoord op DEF-622.

**Step 5:** Draai de nieuwe unit- en integratietests. Expected: groen.

## Task 5: Implementeer CON-01 als contextmetadata-evaluator — DEF-622

**Files:**
- Create: `src/services/validation/evaluators/context_metadata.py`
- Modify: `src/toetsregels/regels/CON-01.json`
- Modify: `tests/fixtures/toetsregels/runtime_cases.yaml`
- Test: `tests/integration/validation/test_con01_context_contract.py`

**Step 1:** Schrijf cases voor:

- minimaal één context aanwezig;
- alle context ontbreekt;
- geselecteerde contextwaarde letterlijk in tekst;
- expliciete generieke contextlabeltekst;
- inhoudelijk contextspecifieke tekst zonder label;
- dezelfde term/andere context;
- dezelfde term/dezelfde genormaliseerde context.

**Step 2:** Detecteer dynamisch de werkelijk geselecteerde contextwaarden. Houd
een kleine expliciete patroonset alleen voor generieke constructies zoals “in de
context van”; gebruik geen onverklaarde vaste organisatielijst als hoofdlogica.

**Step 3:** Laat duplicaatcontrole dezelfde normalisatiefunctie gebruiken als de
contextinvariant.

**Step 4:** Draai DEF-622-tests via manager én CachedToetsregelManager.

## Task 6: Implementeer VER-01–03 — DEF-623

**Files:**
- Create: `src/services/validation/evaluators/lemma_morphology.py`
- Create: `src/services/validation/evaluators/definition_grammar.py`
- Modify: `src/toetsregels/regels/VER-01.json`
- Modify: `src/toetsregels/regels/VER-02.json`
- Modify: `src/toetsregels/regels/VER-03.json`
- Create: `tests/unit/validation/evaluators/test_ver_rules.py`
- Modify: `tests/fixtures/toetsregels/runtime_cases.yaml`

**Step 1:** Schrijf RED-cases voor enkelvoud/meervoud/plurale tantum en
enkelvoudige woorden op `-en`.

**Step 2:** Schrijf RED-cases voor definitieformulering in enkelvoud, inclusief
meervouden op `-s` en plurale-tantumgrenzen.

**Step 3:** Schrijf RED-cases voor infinitief/vervoegde vorm en zelfstandige
naamwoorden op `-t/-d`.

**Step 4:** Implementeer de conservatieve, goedgekeurde morfologiestrategie.
Twijfelgevallen mogen zichtbaar naar review, maar niet als zeker fout worden
gescoord.

**Step 5:** Verwijder de VER-special-cases pas uit `_evaluate_json_rule` wanneer
de nieuwe tests via het register groen zijn.

## Task 7: Implementeer SAM-02 en SAM-04

**Files:**
- Create: `src/services/validation/evaluators/qualification.py`
- Create: `src/services/validation/evaluators/compound.py`
- Modify: `src/toetsregels/regels/SAM-02.json`
- Modify: `src/toetsregels/regels/SAM-04.json`
- Create: `tests/unit/validation/evaluators/test_qualification_rules.py`
- Modify: `tests/fixtures/toetsregels/runtime_cases.yaml`

**Step 1:** Schrijf RED-tests met repository-/begripsfixtures voor hoofdbegrip,
gekwalificeerd begrip, herhaling, conflict en correcte genus+differentia.

**Step 2:** Verwijder de hardcoded delictfrase uit de actieve evaluatie.

**Step 3:** Maak conservatieve compoundanalyse: alleen afkeuren wanneer het
specialiserende component betrouwbaar is vastgesteld.

**Step 4:** Draai unitcases en de volledige matrix.

## Task 8: Implementeer SAM-03 definitietekst-overlap

**Files:**
- Create: `src/services/validation/evaluators/definition_overlap.py`
- Modify: `src/toetsregels/regels/SAM-03.json`
- Create: `tests/unit/validation/evaluators/test_definition_overlap.py`
- Create: `tests/integration/validation/test_sam_repository_rules.py`

**Step 1:** Schrijf RED-cases voor letterlijke belangrijke overlap, triviale
stopwoorden, korte gemeenschappelijke genusfrasen en werkelijk geneste tekst.

**Step 2:** Definieer en documenteer minimumlengte/normalisatie; voorkom dat een
algemene tweewoordenfrase een violation veroorzaakt.

**Step 3:** Gebruik repositorydata via DI, niet door de evaluator zelf een nieuwe
repository te laten construeren.

**Step 4:** Draai unit- en repository-integratietests.

## Task 9: Implementeer SAM-05 definitiegraaf

**Files:**
- Create: `src/services/validation/evaluators/definition_graph.py`
- Modify: `src/toetsregels/regels/SAM-05.json`
- Create: `tests/unit/validation/evaluators/test_definition_graph.py`
- Modify: `tests/integration/validation/test_sam_repository_rules.py`

**Step 1:** Schrijf RED-grafen voor geen cyclus, A→B→A, A→B→C→A,
zelfreferentie en een onbekende term.

**Step 2:** Implementeer bounded DFS/cycle detection volgens het in DEF-623
gekozen uitvoeringsmoment. Houd directe lemmaherhaling onder de bestaande
afzonderlijke regel.

**Step 3:** Maak repositoryfouten zichtbaar; geen succesresultaat omdat de
repository ontbreekt.

**Step 4:** Verander SAM-05 van `bewust_niet_scorend` naar de afgesproken policy
en werk de matrix bewust bij.

## Task 10: Implementeer SAM-06 voorkeursterm

**Files:**
- Create: `src/services/validation/evaluators/preferred_term.py`
- Modify: `src/toetsregels/regels/SAM-06.json`
- Create: `tests/unit/validation/evaluators/test_preferred_term.py`
- Modify: `tests/fixtures/toetsregels/runtime_cases.yaml`

**Step 1:** Schrijf RED-cases voor één voorkeursterm, ontbrekende voorkeursterm,
meerdere voorkeurstermen, alternatieve term en consistente referentie.

**Step 2:** Gebruik het bestaande voorkeursterm-/synoniemencontract op
recordniveau. Kopieer de oude Pythonvalidator niet blind: ASTRA vereist selectie
en relatiebeheer, niet alleen substringcontrole in de definitietekst.

**Step 3:** Verander SAM-06 van `defect_inert` naar automatisch of expliciete
reviewpolicy en werk DEF-621/matrix mee bij.

## Task 10a: Implementeer overige repositoryregels — DEF-624

**Files:**
- Create/Modify: gerichte evaluators onder `src/services/validation/evaluators/`
- Modify: `src/toetsregels/regels/SAM-01.json`
- Modify: `src/toetsregels/regels/SAM-08.json`
- Modify: `src/toetsregels/regels/DUP-01.json`
- Create: `tests/integration/validation/test_repository_rule_contract.py`

**Step 1:** Schrijf RED-cases met echte repositoryfixtures voor betekenisafwijking
van een gekwalificeerd begrip, één definitie voor synoniemen en duplicaatdetectie.

**Step 2:** Lever repositorydata via `EvaluationContext`/DI. Een ontbrekende
repository levert volgens DEF-624 `not_evaluated` of `error`, nooit pass.

**Step 3:** Houd de duplicaatidentiteit voor CON-01 op term plus genormaliseerde
context en gebruik dezelfde normalisatiefunctie.

## Task 10b: Maak oordeelregels eerlijk uitvoerbaar — DEF-624

**Files:**
- Modify: de RuleRecords voor ARAI-03, ESS-01, ESS-04, INT-02, INT-06,
  STR-03, STR-05 en STR-06
- Create/Modify: evaluator- of reviewadapter volgens het goedgekeurde besluit
- Create: `tests/unit/validation/test_judgment_rule_contract.py`

**Step 1:** Leg per regel vast of een deterministische evaluator betrouwbaar is,
een gecontroleerde AI-jury wordt gebruikt of menselijke review verplicht is.

**Step 2:** Voer geen generieke LLM-fallback in. Als AI wordt gekozen, leg
prompt/modelversie, structured output, foutbeleid en een expert-goldset vast.

**Step 3:** Laat onzekerheid of ontbrekende jurering `review_required` opleveren,
niet pass. Test ook dat de approval/exportgate de afgesproken policy respecteert.

## Task 11: Verwijder special-case-drift uit het god-object

**Files:**
- Modify: `src/services/validation/modular_validation_service.py`
- Modify: `src/services/validation/evaluators/registry.py`
- Test: alle evaluator- en matrixtests

**Step 1:** Bevestig dat iedere gemigreerde regel uitsluitend via het register
wordt uitgevoerd.

**Step 2:** Verwijder alleen de vervangen VER/SAM/CON-special-casebranches uit
`_evaluate_json_rule`; laat niet-gerelateerde DEF-424-refactorwerkzaamheden staan.

**Step 3:** Bewijs outputcompatibiliteit voor score, violationvelden, categorie,
severity en suggestions.

## Task 12: Maak tests de uitvoerbare semantische specificatie

**Files:**
- Modify: `tests/fixtures/toetsregels/runtime_cases.yaml`
- Modify: `tests/unit/validation/test_rule_runtime_matrix.py`
- Modify: `tests/unit/validation/test_json_validators.py`
- Inspect: overige loadergerichte tests uit DEF-606

**Step 1:** Laat iedere automatisch getoetste regel een normatieve positieve,
negatieve en grenscase hebben; niet alleen een case die toevallig een branch
raakt.

**Step 2:** Laat repository-/contextregels met gerichte fixtures via het echte
productiepad lopen.

**Step 3:** Vervang dode-loader-smoketests door contract-/productiegedragstests.
Verwijder nog geen productie- of testbestanden zonder Chris' expliciete
toestemming.

**Step 4:** Voeg scoretests toe: `review_required`, `not_evaluated` en `error`
dragen niet als 1,0 bij. Rapporteer naast de kwaliteitsscore de geëvalueerde
dekking en bewijs dat lagere dekking de score niet kunstmatig verhoogt.

**Step 5:** Voeg de 44 JSON-voorbeeldparen toe als directe regressielaag naast
de gerichte fixtures. Documenteer afwijkende projectcases expliciet.

## Task 12a: Leg ASTRA-provenance en drift vast — DEF-625

**Files:**
- Modify: `config/toetsregels/toetsregels_config.yaml`
- Modify: `src/toetsregels/regels/*.json`
- Create: een versioned ASTRA-snapshot/manifest op een met Chris af te spreken pad
- Create: gerichte contract-/drifttests

**Step 1:** Leg bronsoort, bronregel/URL, peildatum/status, bronprioriteit en
eventuele projectoverride per record vast.

**Step 2:** Verifieer de tien door Cowork gerapporteerde prioriteitsverschillen,
STR-02/STR-04-status en ESS-02-uitbreiding afzonderlijk; neem ze niet ongezien
over.

**Step 3:** Markeer CON-01 expliciet als lokale representatiekeuze: context is
verplichte recorddata en geen onderdeel van de definitietekst.

**Step 4:** Maak drift reproduceerbaar zichtbaar zonder productieruntime-netwerk
en zonder externe wijzigingen automatisch te accepteren.

## Task 13: Verse verificatie en handover

**Step 1:** Draai gericht:

```bash
.venv/bin/python -m pytest -q \
  tests/unit/validation \
  tests/unit/services/orchestrators/test_validation_context_passthrough.py \
  tests/integration/validation/test_con01_context_contract.py \
  tests/integration/validation/test_sam_repository_rules.py
```

**Step 2:** Draai projectgates:

```bash
make test
make lint
make test-cov-ci
```

Expected: exit 0; coverage blijft minimaal op de projectratchet van 45%.

**Step 3:** Controleer architectuurinvarianten:

```bash
rg -n "json_validator_loader|toetsregels\.validators" src
rg -n "spec_from_file_location" src/toetsregels src/services/validation
```

Expected: geen nieuw productiepad naar de oude lagen.

Controleer bovendien dat geen pad `review_required`, `not_evaluated` of `error`
naar een pass-score normaliseert en dat het rapport evaluatiedekking bevat.

**Step 4:** Plaats per issue een Linear-comment `Oplevering` met gewijzigde
bestanden, besluiten, verse testoutput en bekende beperkingen. Zet een issue pas
op Done wanneer alle eigen acceptatiecriteria bewezen zijn.

**Step 5:** Stop. Meld dat de verwijderingsgate klaar is voor beoordeling, maar
verwijder niets uit `src/toetsregels/validators/` of de `.py`-bestanden onder
`src/toetsregels/regels/` zonder een nieuwe expliciete opdracht van Chris.
