# DEF-835 WP3 — GREEN-verslag Claude Code CLI v1

28 september 2026. Uitvoerder: dezelfde Claude Code CLI-sessie als RED (claude-opus-5-5). Er zijn geen agents, reviewers of extra CLI-sessies gestart.

Opdracht: `wp3-opdracht-claude-groen-v1.md`, plus de aanvulling van de coördinator over de versiepins. De TDD-skill is gelezen via `/Users/chrislehnen/.agents/skills/test-driven-development/SKILL.md`.

**Status:** GREEN afgerond, geen commit of push. Branch `feature/DEF-835-int02-o2`, HEAD `2be81c577653f8efbab6fa2c3794598556d32d13`.

## 1. Gewijzigde bestanden (alleen de negen geaccordeerde)

| # | Bestand | Omvang |
|---|---|---|
| 1 | `src/services/validation/evaluators/decision_rule_assessment.py` (nieuw) | 259 regels |
| 2 | `src/toetsregels/runtime_contract.py` | +5: `EvaluatorType.DECISION_RULE_ASSESSMENT` met toelichting |
| 3 | `src/services/validation/evaluators/__init__.py` | +4: import en registratie |
| 4 | `docs/architectuur/contracts/validation_result_contract.md` | +19/−1: versie 2.3.0, wijzigingsrij en sectie "INT-02 O2-deeluitkomst (2.3.0)" met metadata-aansluiting en grens |
| 5 | `docs/architectuur/contracts/schemas/validation_result.schema.json` | +16/−1: beschrijving 2.3.0 en eigenschap `rule_results.INT-02` (`$ref #regeluitkomst`, `assessment` object\|null, `signals` string[], `unevaluatedProperties: false`) |
| 6 | `tests/unit/validation/test_def835_int02_evaluator.py` | ongewijzigd sinds RED (sha256 `c8a1c170…a413d509`) |
| 7 | `tests/integration/contracts/test_validation_result_schema.py` | ongewijzigd sinds RED (sha256 `712f5e52…f496369d`) |
| 8 | `config/toetsregels/toetsregels_config.yaml` | +6: alleen de bekende waarde `decision_rule_assessment` met toelichting |
| 9 | `src/services/validation/interfaces.py` | +14/−2: `CONTRACT_VERSION = "2.3.0"`, versiecommentaar en INT-02-documentatie in `RuleResult` |

Herstelkopieën, gemaakt vóór de wijziging (git-blob gelijk aan HEAD):
- `bewijs/wp3-herstelkopie-validation_result.schema-v1.json` (`2b98205e…`)
- `bewijs/wp3-herstelkopie-validation_result_contract-v1.md` (`5eb24f10…`)
- de RED-kopie van bestand 7 bestond al.

Niet gewijzigd:
- `INT-02.json`: het actieve record blijft `judgment_review` (O1);
- WP1/WP2;
- `modular_validation_service.py` (`_EVALUATORS_MET_DEELUITKOMST`);
- container, orchestrator, UI en opslag;
- de vijf bestaande testbestanden met versiepins.

Geen dependencies, modelcalls, productiedata of Actions.

**Testcorrecties:** geen. Beide testbestanden zijn byte-gelijk aan RED en alle RED-tests zijn ongewijzigd groen geworden.

## 2. Testresultaten

| Controle | Resultaat | Log |
|---|---|---|
| Nulmeting vóór productiewijziging: 5 regressiebestanden + 4 versiepinbestanden | 436 passed, exit 0 | `bewijs/wp3-claude-basis-voor-groen-v1.log` |
| GREEN: beide WP3-testbestanden | **111 passed**, exit 0 (RED: 92 failed, 19 passed) | `bewijs/wp3-claude-groen-v1.log` (kop met sha256 van alle negen bestanden) |
| Gerichte regressie: `test_def771_int02_o1`, `test_def772_int03_evaluator`, `test_evaluator_registry_contract`, `test_rule_cache_runtime_contract`, `test_def835_int02_contract` | **4 failed, 354 passed**, exit 1. Alle 4 zijn verklaarde oude verwachtingen (§3) | `bewijs/wp3-claude-regressie-v1.log` |
| Aparte controle van de vier bestaande versiepinbestanden | **4 failed, 74 passed**, exit 1. Alle 4 op `== "2.2.0"` (§3) | `bewijs/wp3-claude-bestaande-versiepins-rood-v1.log` |
| Lint: Ruff 0.15.17 (venv) en 0.16.5 (pre-commit-versie uit de cache, zonder `--fix`), Black 26.5.1 `--check`, JSON/YAML laadbaar | alles exit 0 | `bewijs/wp3-claude-lint-v1.log` |

Totaal: 354 + 4 + 74 + 4 = 436. Dat is gelijk aan de nulmeting. Er is dus geen test verdwenen, en naast de verklaarde failures is geen andere test gaan falen.

Aanvullend, niet gevraagd:

**Mutatiecontrole in het geheugen** (`bewijs/wp3-claude-mutatie-v1.log`). Beide mutaties worden gevangen:
- `toets_actualiteit` die de binding negeert: 23 failed;
- `review.actuality` altijd `current`: 46 failed.

**Brede unit-run** (`pytest tests -m unit -n auto`, `bewijs/wp3-claude-breed-unit-v1.log`): 10 failed, 8395 passed, 1 error. Classificatie:
- 8 failures zijn de verklaarde pins hieronder;
- 2 failures in `test_performance_tracker.py::TestGlobalTracker` (`OfflineGateError` op `data/definities.db`) zijn voorbestaand. Ze falen identiek op een schone HEAD-export via `git archive`;
- 1 collectiefout in `web_lookup/test_sanitization.py` ("import file mismatch") komt doordat `-o addopts=` de `--import-mode=importlib` uitschakelt. Het is een artefact van het commando, geen WP3-effect.

Procesnoten:
- De eerste poging van de brede run gebruikte `timeout`, dat op macOS niet bestaat (exit 127, er is niets gedraaid).
- De eerste diagnosepoging hieronder collecteerde niets (exit 5).
- Beide pogingen zijn in de logs gemeld.

## 3. Verklaarde oude verwachtingen (niet aangepast, niet geaccordeerd)

| Test | Faalregel | Oorzaak |
|---|---|---|
| `test_def771_int02_o1.py::test_ne_resultaat_past_in_schema_en_conversie` (3 parametrisaties: C06, C23, C56) | `:291` `assert CONTRACT_VERSION == "2.2.0"` | versie 2.3.0 |
| `test_def771_int02_o1.py::test_onbekende_velden_en_int03_velden_elders_blijven_afgewezen` | `:376` voor de rij `(…, "INT-02", "signals", [])` | 2.3.0 staat `signals`/`assessment` voor INT-02 bewust toe |
| `test_validation_readiness.py::test_contractversie_is_verhoogd_naar_2_2_0` | `:188` | versie 2.3.0 |
| `test_def743_source_assessment_wrappers.py::test_validate_text_verkrijgt_verse_beoordeling_en_geeft_haar_terug` | `:138` | versie 2.3.0 |
| `test_def772_int03_wrappers.py::test_validate_text_verkrijgt_verse_beoordeling_met_binding` | `:103` | versie 2.3.0 |
| `test_def766_ess03_wrappers.py::test_validate_text_verkrijgt_verse_beoordeling_en_geeft_haar_terug` | `:95` | versie 2.3.0 |

**Gemaskeerde asserties gecontroleerd.** In drie van deze tests staan na de pin nog asserties die nu niet meer worden uitgevoerd:
- `readiness:189-…`
- `int03_wrappers:104`
- `o1:292-296` en `o1:377-379`, plus de INT-02-`assessment`-rij.

Om te voorkomen dat daar ongemerkt iets verdwijnt, heb ik de vijf bestanden buiten de repo gekopieerd (`/tmp/wp3_pinprobe2`). In die kopieën zijn alleen de pins naar 2.3.0 gezet en de twee INT-02-weigerrijen weggelaten. Uitvoering met de repo-conftest: **121 passed**, exit 0. Alle overige asserties houden dus stand.

Bewijs: `bewijs/wp3-claude-versiepins-diagnose-v1.py` en `bewijs/wp3-claude-versiepins-diagnose-v1.log`. Er is geen repobestand gewijzigd.

## 4. Metadata-interface (zoals geïmplementeerd)

In `EvaluationContext.metadata`. De constanten `METADATA_DOCUMENT`, `METADATA_CONFIGURATIE`, `METADATA_BEDOELING` en `METADATA_BRONNEN` staan in de module.

- **`record_text`** (str): de exacte kern. Zonder deze sleutel geldt `ctx.raw_text`.
- **`organisatorische_context`, `juridische_context`, `wettelijke_basis`**: afwezig of `None` telt als leeg. Een ander type gaat naar de WP1-validatie en geeft `error`.
- **`int02_bedoeling`**: tekst, of `None` / afwezig (expliciet onbekend).
- **`int02_bronnen`**: lijst van `{id, tekst}`. Afwezig of `None` betekent geen bronnen.
- **`int02_configuratie`**: `Configuratie`. Afwezig: NE bij ontbrekende kern of context, anders nog niet beoordeeld. Een ander type geeft `error`.
- **`int02_document`**: `Beoordelingsdocument` of `None`. Elk ander type geeft `error`, via `toets_actualiteit`.

Werking:
- De invoer wordt uitsluitend gebouwd met `maak_invoer`, uit `ctx.begrip` en de metadata, nooit uit het document.
- Een `Int02ContractError` wordt `error`, niet een exceptie.
- De actualiteit komt uit precies één aanroep van `toets_actualiteit(document, invoer, configuratie)`.
- Er wordt niets gelogd.

Deeluitkomst `rule_result`:
- `status`;
- `score: null`, `fingerprint: null`;
- `contract_version` `def835-int02-assessment/1`;
- één onderdeel `beoordeling` met de exacte WP1-melding;
- `review.actuality`: `current`, `historical`, `not_assessed`, of `null` bij NE en fout;
- `assessment`: `document.als_dict()` alleen als het document is aanvaard (niet bij NE of fout), anders `null`;
- `signals`: de recordpatronen op de actuele kern, gecachet per regelcode in `deps.pattern_cache`.

Uitkomst per status:
- **fail:** een violation met `warning`/`medium` (de INT-03-constanten), `metadata.advisory=True` en `contract_version`. De suggestie is een neutrale actietekst zonder herschrijfopdracht.
- **pass:** geen reden, geen violation.
- **overige statussen:** `reason` is de melding. Bij `review_required` staat ook `metadata.signals` erin.

**Uitvoeringsteksten.** De `parts[].action`-teksten zijn uitvoeringstekst van de evaluator, geen sjabloon uit synthese §4. Voorbeelden: "Laat INT-02 opnieuw beoordelen voor de actuele versie." en "Weeg de passage mee in de integrale expertbeoordeling; de tekst is niet gewijzigd.". De meldingen zelf zijn letterlijk die uit WP1.

## 5. Bewijsgrenzen

- Bewezen: evaluator, register, root-SSOT en publiek schema, met een tijdelijk testrecord. De echte evaluatoruitkomst is voor alle zes statussen schemageldig.
- Niet bewezen: container-, orchestrator- en `ModularValidationService`-integratie. `_EVALUATORS_MET_DEELUITKOMST` boekt de INT-02-deeluitkomst nog niet op alle statuspaden. UI, opslag en herladen evenmin. De volledige appketen voert O2 dus nog niet uit (WP5).
- Geen semantische modelkwaliteit: de oordelen in de tests zijn handmatig ingevuld.
- Het actieve INT-02-record blijft O1. Er is niets geactiveerd.
- Een volledig consistent vervalst document is, zoals in WP1, niet te onderscheiden. Herkomst is een zaak van de opslaglaag.

## 6. Afwijkingen en open punten

- De zes verklaarde oude verwachtingen in vijf testbestanden buiten de scope blijven rood, tot de coördinator of Chris besluit over het gebundelde voorstel.
- Binnen de negen bestanden is geen afwijking of scope-uitbreiding nodig geweest.
- Na RED zijn geen testcorrecties gedaan.

## Bronnen

- Opdrachten en verslagen: `wp3-opdracht-claude-groen-v1.md`, `wp3-opdracht-claude-rood-v1.md`, `wp3-claude-rood-verslag-v1.md`, `wp3-scopeaanvulling-v1.md`.
- `src/domain/int02/contract.py` (`maak_invoer`, `ontbrekende_invoer`, `toets_actualiteit`, `Actualiteit`, meldingen).
- De diff van de zeven getrackte bestanden: `git diff HEAD --numstat` geeft 280 insertions en 4 deletions. Daarnaast is er één nieuw productiebestand.
- Bewijs onder `gedeeld/uitvoering/o2/bewijs/`:
  - `wp3-claude-basis-voor-groen-v1.log`
  - `wp3-claude-groen-v1.log`
  - `wp3-claude-regressie-v1.log`
  - `wp3-claude-bestaande-versiepins-rood-v1.log`
  - `wp3-claude-versiepins-diagnose-v1.{py,log}`
  - `wp3-claude-lint-v1.log`
  - `wp3-claude-mutatie-v1.log`
  - `wp3-claude-breed-unit-v1.log`
  - de herstelkopieën

Let op: `*.log` staat in `.gitignore`.
