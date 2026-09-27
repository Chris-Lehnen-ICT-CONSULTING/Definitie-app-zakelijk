# DEF-835 WP3 — RED-verslag Claude Code CLI v1

27/28 september 2026. Uitvoerder: Claude Code CLI (claude-opus-5-5), toegewezen uitvoerder; geen agents, reviewers of extra CLI-sessies gestart. Opdracht: `wp3-opdracht-claude-rood-v1.md`. **Status: RED afgerond; gestopt vóór implementatie. Geen commit/push.**

## 1. Werkplek en scope

- Werkboom `.claude/worktrees/DEF-835-int02-o2`, branch `feature/DEF-835-int02-o2`, HEAD `2be81c577653f8efbab6fa2c3794598556d32d13` (gecontroleerd bij start en in de logkop).
- Alleen bestanden 6 en 7 uit de geaccordeerde negen:
  - nieuw `tests/unit/validation/test_def835_int02_evaluator.py` (958 regels, sha256 `c8a1c170…a413d509`);
  - `tests/integration/contracts/test_validation_result_schema.py`: **alleen toevoegingen** (`git diff --stat`: 216 insertions, 0 deletions; sha256 `712f5e52…f496369d`). Geen bestaande test gewijzigd of verwijderd.
- Herstelkopie vooraf: `bewijs/wp3-herstelkopie-test_validation_result_schema-v1.py`, sha256 `dc77d059…986357f7`, gelijk aan de HEAD-blob `7d44b938f3408f855acf8184c3b4edb51444451c`.
- Niet gewijzigd: productiecode, schema, contractdocument, `interfaces.py`, root-SSOT-YAML, `INT-02.json`, WP1/WP2, `modular_validation_service.py` (`_EVALUATORS_MET_DEELUITKOMST`). Geen dependencies, modelcalls of productiedata.
- Lint: `ruff check` groen op beide bestanden; `black` (de pre-commit-formatter) groen. `ruff format --check` meldt op bestand 7 één verschil in regels 187–192; dat verschil zit al in de HEAD-versie en is niet door mij veroorzaakt.

## 2. Testselectie en resultaat

Commando (vanuit de werkboom):
`/Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python -m pytest tests/unit/validation/test_def835_int02_evaluator.py tests/integration/contracts/test_validation_result_schema.py -o addopts= -q -ra`

Resultaat: **92 failed, 19 passed in 5.53s, exitcode 1**. Beide bestanden collecteren; geen collectie- of setupfouten. Volledig log met kop (HEAD, tijdstip, sha256 van beide testbestanden): `bewijs/wp3-claude-rood-v1.log`.

Procesnoot: de eerste poging in dat log is een shellfout (zsh splitste `$CMD` niet, exit 127; pytest startte niet). Die regel staat er nog en is gemarkeerd. Poging 2 is hetzelfde commando, direct uitgeschreven, en is de geldige RED-run.

| Bestand | Verzameld | Rood | Groen |
|---|---|---|---|
| nieuw evaluatortestbestand | 70 | 69 | 1 (`test_actief_int02_record_blijft_o1_en_ongewijzigd`) |
| schematestbestand | 41 | 23 | 18: de 12 bestaande tests plus 6 nieuwe bewakers |

De zes nieuwe bewakers die nu al groen zijn en groen moeten blijven:
- `assessment_en_signals_blijven_dicht_voor_andere_regels`, voor CON-01, ESS-04 en INT-01;
- `bestaande_regeluitkomsten_blijven_geldig`;
- `bestaande_int03_uitkomst_met_beoordeling_blijft_geldig`;
- `o1_ne_uitkomst_van_int02_blijft_geldig`.

Faalredenen volgens het log, allemaal ontbrekend gedrag:
- `'decision_rule_assessment' is not a valid EvaluatorType`, en dus faalt het bouwen van het tijdelijke O2-record met `RuleContractError`. Die melding komt uit de bestaande contractcontrole, niet uit een testfout.
- `No module named 'services.validation.evaluators.decision_rule_assessment'`: via `importlib`, als testfailure.
- `assert '2.2.0' == '2.3.0'` (`CONTRACT_VERSION`).
- Het schema zegt `Unevaluated properties are not allowed ('assessment', 'signals' were unexpected)` bij INT-02. Dat is direct getoetst, los van de evaluator.
- `'INT-02' in getsource(RuleResult)`: de gerichte TypedDict-documentatie ontbreekt.

**Controle van de testopzet** (scratchscript `/tmp/wp3_opzetcontrole.py`, buiten de repo, 0 fouten). Elke fixture is apart tegen de bestaande WP1-functies gelegd:
- alle zeven scenario-documenten geven via `beoordeel` en `toets_actualiteit` de verwachte status;
- alle elf bindingswijzigingen geven `historical`;
- alle acht fout- en sabotagedocumenten geven `error`;
- alle vijf NE-gevallen geven de verwachte grond.

Het rood komt dus niet uit onjuiste testdata. Na implementatie hangt groen alleen af van het gespecificeerde gedrag.

Extra ter vergelijking: `tests/unit/validation/test_def771_int02_o1.py` blijft ongewijzigd groen, **43 passed**, exit 0.

## 3. Wat de tests specificeren (ontbrekend gedrag)

1. **Registratie/SSOT:**
   - `EvaluatorType("decision_rule_assessment")` bestaat en staat in `runtime_contract.evaluators` van de root-YAML;
   - de policy-set is gelijk aan de enum;
   - `build_default_registry()` en `get_default_registry()` lossen het type op naar `DecisionRuleAssessmentEvaluator` in de nieuwe module.
   - Tijdelijk record: `INT-02.json` in een deepcopy met `evaluator=decision_rule_assessment` en `automation_status=automated`, verder ongewijzigd. Dan `judgment`, `excluded_from_score`, vereiste invoer `definition_text` en `context_lists`. Het bronrecord wordt niet gemuteerd.
   - Het actieve record blijft `judgment_review`, `review_required` en `excluded_from_score`, en wordt opgelost naar `JudgmentReviewEvaluator`.
2. **Puur/synchroon:**
   - `evaluate` is geen coroutine en geeft geen awaitable terug;
   - `Int02AssessmentService.assess` en `bouw_int02_prompt` zijn in de test verboden en worden niet aangeroepen.
3. **WP1 in plaats van parallelle logica:**
   - de module gebruikt de naam `toets_actualiteit` uit `domain.int02.contract`;
   - een spion bevestigt precies één aanroep met het document, exact `maak_invoer(...)` van de huidige invoer (inclusief bedoeling en bronnen) en de actuele `Configuratie`.
4. **Actuele oordelen:**
   - de statussen pass, fail (voorschrift, discretie en zonder signaalwoord), review_required (onvoldoende informatie) en not_applicable volgen het document;
   - de reden is gelijk aan `document.melding`, of bevat bij O precies de ene vraag;
   - fail is adviserend:
     - een violation `INT-02` met `warning`/`medium`, gelijk aan de INT-03-constanten;
     - `metadata.advisory=True`;
     - de melding bevat "De tekst is ongewijzigd.";
     - de suggestie bevat geen "herschrijf".
5. **Nog niet beoordeeld:**
   - Geen document, `None`, of geen actuele configuratie: `review_required` met `MELDING_NIET_BEOORDEELD`, nooit pass, ook zonder signaalwoord.
   - Een WP1-document met `not_executed`: idem, maar met het document als assessment.
6. **Historisch:**
   - Elk bindingsveld afzonderlijk gewijzigd, elf gevallen: kern (alleen een witruimte aan het eind), begrip, bedoeling, context, bron, normhash, normversie, promptversie, routeringshash, provider en model.
   - Uitkomst: `review_required` met `MELDING_HISTORISCH`, géén violation (een historische afkeur is geen actuele afkeur), en het oude document ongewijzigd als assessment.
7. **NE:** vijf gevallen, elk met en zonder voorbereid oordeel:
   - lege kern;
   - kern van alleen witruimte;
   - los label `Toegang:`;
   - geen context;
   - kern én context ontbreken.

   Uitkomst: `not_evaluated` met de exacte `MELDING_NE`; het oordeel wordt genegeerd en er komt geen assessment.
8. **Fout:** steeds `error` met `MELDING_E`, geen assessment en nooit pass of fail. Dit geldt voor:
   - WP1-foutdocumenten: transport mislukt, ongeldig antwoord en verzonnen citaat (C117; het citaat komt niet in de uitvoer);
   - een onbekend documenttype: dict, tekst, lijst, getal of het WP2-omhulsel `Int02Beoordeling`;
   - gesaboteerde documenten: fout als pass, pass als fail, vervangen oordeel, corrupte JSON en een direct samengesteld document. "Voldoet" komt niet in de uitvoer;
   - ongeldige metadata: configuratie als dict of tekst, context als tekst of met een getal, bedoeling als getal, bronnen als tekst, een bron zonder tekst en een dubbel bron-ID. Dit geeft een nette fout, geen exceptie.
9. **Signalen:**
   - de patronen uit het record worden op de actuele kern toegepast, niet op de kern van het oordeel;
   - een door de aanroeper meegegeven `metadata["signals"]` wordt genegeerd;
   - een record zonder patronen geeft dezelfde status, hetzelfde assessment, dezelfde onderdelen en dezelfde review, alleen andere `signals`;
   - een afkeur zonder signaalwoord blijft `fail`.
10. **Geen mutatie:**
    - herhaalde evaluatie geeft een identieke uitkomst;
    - metadata, document en `oordeel_json` blijven ongewijzigd;
    - het gepubliceerde assessment is een kopie.
11. **Publiek contract 2.3.0 (bestand 7):**
    - Versie en bronnen:
      - `interfaces.CONTRACT_VERSION == "2.3.0"`;
      - de schemabeschrijving bevat "Contractversie 2.3.0";
      - het contractdocument bevat `- **Versie**: 2.3.0 (SemVer)` en een wijzigingsrij `| 2.3.0 |`.
    - Echte evaluatoruitkomsten:
      - de echte evaluatoruitvoer is voor negen scenario's schemageldig, samen alle zes statussen;
      - `assessment` en `signals` hebben expliciete typen (object of null, lijst van tekst);
      - `score: 0.0` wordt geweigerd;
      - een onbekend veld wordt geweigerd;
      - dezelfde echte uitkomst onder ESS-04 wordt geweigerd; zonder de twee velden is zij geldig.
    - Direct op het schema: INT-02 met `assessment` null of object en `signals: []` is geldig.
    - De TypedDict `RuleResult` documenteert INT-02 naast INT-03.

## 4. Voorgestelde metadata-interface (klein en expliciet)

| Sleutel in `EvaluationContext.metadata` | Type | Betekenis |
|---|---|---|
| `record_text` | `str` | Exacte kern. Ontbreekt deze, dan geldt `ctx.raw_text`. |
| `organisatorische_context`, `juridische_context`, `wettelijke_basis` | lijst/tuple van niet-lege teksten | Afwezig of `None` betekent leeg. Een ander type geeft `error`. |
| `int02_bedoeling` | `str` of `None`/afwezig | `None` betekent expliciet onbekend (WP1). |
| `int02_bronnen` | lijst van `{"id", "tekst"}` | Afwezig of `None` betekent geen bronnen. |
| `int02_configuratie` | `domain.int02.contract.Configuratie` | De actuele configuratie. Afwezig: nog niet beoordeeld. Een ander type geeft `error`. |
| `int02_document` | `domain.int02.contract.Beoordelingsdocument` of `None`/afwezig | Getypeerd WP1-document. Elk ander type, ook het WP2-omhulsel, geeft `error`. |

`ctx.begrip` is het begrip. De invoer wordt uitsluitend via `maak_invoer` gebouwd. Een `Int02ContractError` wordt de nette uitkomst `error`.

Volgorde:
1. Invoer bouwen.
2. Ontbrekende kern of context: NE, ook zonder configuratie.
3. Geen configuratie: nog niet beoordeeld.
4. Anders: `toets_actualiteit(document, invoer, configuratie)`.

**Publieke deeluitkomst** (`outcome.metadata["rule_result"]`):
- `status`;
- `score: null`;
- `contract_version`: `def835-int02-assessment/1`;
- `fingerprint`: niet vastgelegd in de tests, alleen via het schema (string of null);
- `parts`: precies één onderdeel met de status en de exacte WP1-melding;
- `review.actuality`: `current`, `historical`, `not_assessed`, of `null` bij NE en fout;
- `assessment`: `document.als_dict()` alleen als `toets_actualiteit` het document heeft aanvaard (actueel, historisch of niet-uitgevoerd WP1-document); anders `null`;
- `signals`: een lijst patroonteksten uit het record.

## 5. Ontwerpkeuzes ter bevestiging door de coördinator

- **Kernbron:** `record_text`, anders `raw_text`. Dit volgt het precedent van INT-03, CON-01 en ESS-03, zodat de binding bij het record hoort. O1 gebruikt `cleaned_text`. Dit is vastgelegd in `test_kern_is_de_exacte_recordtekst` en `test_zonder_recordtekst_geldt_de_aangeleverde_tekst`. Kiest de coördinator anders, dan moeten alleen die twee tests mee.
- **`contract_version`** wordt de WP1-contractversie, niet de normversie uit het record (O1-NE gebruikt `def771-int02/2`). De normversie staat in de binding van het assessment.
- **Geen assessment bij fouten.** Het document wordt ook niet gepubliceerd bij een WP1-foutdocument, omdat `toets_actualiteit` een foutdocument niet op herleidbaarheid controleert. Zo lekt er geen onverifieerbare inhoud.
- **De spiontest eist de modulenaam `toets_actualiteit`.** Dat is bewust: een aantoonbare borging tegen parallelle logica.
- **Het WP2-omhulsel wordt niet aanvaard.** Dat houdt de interface klein: WP5 geeft het `document` door.

## 6. Concrete blocker voor GREEN binnen negen bestanden

GREEN zet de centrale `CONTRACT_VERSION` op 2.3.0 en staat `assessment`/`signals` toe voor INT-02. Beide zijn vereist. Zes bestaande asserties in **vijf testbestanden buiten de geaccordeerde negen** worden daardoor rood. Hun inhoud is hierboven gelezen en geciteerd. Volgens de opdracht mogen versiepins niet worden aangepast om rood te verbergen, en een tiende bestand mag niet stil worden meegenomen.

| Vindplaats | Tekst | Gevolg na GREEN |
|---|---|---|
| `tests/unit/validation/test_def771_int02_o1.py:291` | `assert CONTRACT_VERSION == "2.2.0"` | rood |
| `tests/unit/validation/test_def771_int02_o1.py:369-376` | `(ne["rule_results"], "INT-02", "signals", [])` en `("assessment", None)` moeten door het schema worden geweigerd | rood; de verwachting is inhoudelijk tegengesteld aan 2.3.0 |
| `tests/unit/validation/test_validation_readiness.py:188` | `assert CONTRACT_VERSION == "2.2.0"` | rood |
| `tests/unit/services/orchestrators/test_def743_source_assessment_wrappers.py:138` | `assert result["version"] == CONTRACT_VERSION == "2.2.0"` | rood |
| `tests/unit/services/orchestrators/test_def772_int03_wrappers.py:103` | idem | rood |
| `tests/unit/services/orchestrators/test_def766_ess03_wrappers.py:95` | idem | rood |

Het plan (plan-v1 §WP3, "O1-regressie blijft groen", met `test_def771_int02_o1.py` in het commando) kan dus niet volledig groen worden zonder een inhoudelijke herijking van deze asserties. Beslissing voor de coördinator/Chris, niet door mij genomen:
- **(a)** Scope uitbreiden met deze vijf testbestanden. Dan worden de pins gericht herijkt naar 2.3.0, zonder cases te verwijderen, en de INT-02-rij in `test_def771_int02_o1.py:371-372` wordt omgezet naar "toegestaan voor INT-02, gesloten voor andere regels". Die dekking zit nu al in bestand 7.
- **(b)** Een ander, expliciet besluit.

Tot dat besluit rapporteer ik bij GREEN deze asserties als bekend en verwacht rood, zonder ze aan te passen.

Andere open punten:
- `_EVALUATORS_MET_DEELUITKOMST` blijft ongewijzigd (WP5). Deze tests bewijzen dus alleen de evaluator, de registry en het schema, niet dat de volledige `ModularValidationService` O2 publiek doorgeeft.
- De TDD-skill kon niet via een Skill-tool worden geladen: die ontbreekt in deze CLI-sessie. De principes zijn toegepast: eerst rood, faalt om de juiste reden, en een fixturecontrole tegen de echte WP1-functies.

## Bronnen

- `wp3-opdracht-claude-rood-v1.md`, `wp3-scopeaanvulling-v1.md`, `takenlijst-v9.md`/`-v10.md`, `plan-v1.md` §WP3/§Ontwerpvoorstel, `besluiten-chris-v1.md` (B2, B3, B5, B6), `gezamenlijke-synthese-v5.md` §2 en §4.
- `src/domain/int02/contract.py`: `maak_invoer`, `ontbrekende_invoer`, `toets_actualiteit` (r. 796–823), meldingen (r. 101–139).
- `docs/architectuur/contracts/int02_assessment_contract_v1.md`.
- `src/services/validation/int02_assessment_service.py`: `Int02Beoordeling`, r. 484–509.
- `src/services/validation/evaluators/pronoun_reference_assessment.py` (architectuurvoorbeeld), `judgment_review.py` (O1-NE), `base.py`, `registry.py`, `__init__.py`.
- `src/toetsregels/runtime_contract.py`: r. 94–122, 257–305, 433–520.
- `src/toetsregels/regels/INT-02.json`, `config/toetsregels/toetsregels_config.yaml` r. 68–105.
- `docs/architectuur/contracts/schemas/validation_result.schema.json` r. 285–369; `validation_result_contract.md` r. 29–36; `src/services/validation/interfaces.py` r. 70–77 en 262–279.
- `src/services/validation/modular_validation_service.py` r. 929–940 en 1519–1549 (metadata en contextbeschikbaarheid).
- Bewijs:
  - `bewijs/wp3-claude-rood-v1.log`;
  - `bewijs/wp3-herstelkopie-test_validation_result_schema-v1.py`;
  - `bewijs/wp3-nulmeting-v1.log` (uitgangssituatie: 55 passed).
