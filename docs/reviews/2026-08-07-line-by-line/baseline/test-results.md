# Baseline test results

## Samenvatting

| Onderdeel | Resultaat | Bewezen status |
|---|---|---|
| Lint/format | PASS | Ruff schoon; Black laat 371 bestanden ongewijzigd |
| Mypy-ratchet | PASS | 0 fouten, gelijk aan baseline |
| Markercontrole | PASS | alle 317 testbestanden hebben classificatiemarkers |
| Unit coverage-gate | FAIL | 49,21% bereikt de projectvloer 45%, maar 14 tests falen |
| Seriële unitdiagnose | FAIL | één test blijft falen |
| Afgebakende dummy-keydiagnose | PASS | alle betrokken tests slagen; één verwachte xfail |
| Smoke | FAIL | 3 failures; 1 expliciete credential-skip |
| Acceptance | FAIL | 5 failures, 2 pass |
| Integration per bestand | DEELS | 41 pass, 17 fail, 15 skip, 3 blocked, 0 timeout |

Een `FAIL` is een bewezen testresultaat. Een daaruit afgeleide oorzaak is
hieronder expliciet als bewezen of vermoed gemarkeerd. Formele prioritering en
finding-IDs volgen pas na bronreview van de betrokken batch.

## Unit en coverage

De CI-recipe rapporteert 34.447 statements, 17.494 gemist en 49,21% dekking
(`TOTAL` rondt af op 49%). Daarmee wordt de projectratchet van 45% gehaald,
maar de opdracht eindigt rood door 14 `ValueError: API key is required for
provider 'anthropic'`-failures.

- **Bewezen:** de seriële herhaling reduceert dit tot alleen
  `tests/unit/services/test_service_factory_caching.py::test_service_factory_returns_same_instance`.
- **Bewezen:** de test zet `OPENAI_API_KEY=test`, maar het product initialiseert
  standaard provider `anthropic`; de stack eindigt in
  `src/services/ai/__init__.py:52` met een lege Anthropic-key.
- **Bewezen:** de zes betrokken testbestanden slagen parallel met de afgebakende
  dummywaarde `ANTHROPIC_API_KEY=test` en zonder live AI-aanroep.
- **Vermoeden:** de 13 extra xdist-failures worden veroorzaakt door dezelfde
  niet-hermetische credential-/containerconfiguratie en proceslokale singleton-
  toestand. De diagnostiek bewijst niet dat alle mogelijke racecondities afwezig
  zijn.

De globale code-quality-richtlijn gebruikt 80% als blocker; dit project heeft
expliciet een 45%-ratchet. De gemeten 49,21% is dus een **bewezen dekkingsgat ten
opzichte van 80%**, maar geen daling onder de huidige projectspecifieke gate.

## Smoke en acceptance

### Smoke

- **Bewezen:** `tests/smoke/test_ui_smoke.py` faalt voor zowel `legacy` als
  `new`, en `tests/smoke/test_critical_paths.py` faalt, doordat
  `ServiceContainer` zonder Anthropic-key initialiseert.
- **Bewezen:** `tests/smoke/test_smoke_generation.py` skipt correct wanneer geen
  AI-key beschikbaar is.
- **Vermoeden:** de andere smoke-tests missen dezelfde expliciete skip of een
  gemockte provider. Er is zonder credentials geen bewijs dat de echte
  generatieflow werkt.

### Acceptance

- **Bewezen:** vijf PER-007-tests falen omdat `HybridContextManager()` zonder
  de inmiddels verplichte `config` wordt aangeroepen; twee tests slagen.
- **Vermoeden:** de acceptancesuite is niet bijgewerkt na de constructorwijziging.
  Of ook productgedrag afwijkt, wordt pas in de gekoppelde bronbatch vastgesteld.

## Integration per bestand

Exacte set: 76 van 76 bestanden, geen ontbrekende of dubbele paden.

| Status | Aantal |
|---|---:|
| pass | 41 |
| fail | 17 |
| skip | 15 |
| blocked | 3 |
| timeout | 0 |

### Bewezen falende bestanden

| Bestand | Bewijs uit individuele run | Oorzaakstatus |
|---|---|---|
| `tests/integration/compliance/test_architecture_consolidation.py` | 5 failures; zoekt canonieke docs en index onder niet-bestaand `tests/integration/docs/` | vermoed verouderd testpad |
| `tests/integration/compliance/test_per007_documentation_compliance.py` | 10 failures; documenten en 6 verwachte PER-007-testfiles niet gevonden onder testpad | vermoed verouderd testpad |
| `tests/integration/database/test_unique_constraint_removal.py` | 2 failures; UNIQUE-index ontbreekt vóór migratie en is na rollback niet hersteld | vermoed migratie-/fixturecontract |
| `tests/integration/performance/test_def110_regression.py` | Streamlit niet ready binnen 20 s; bestandsrun 39,82 s | bewezen readinessfailure; oorzaak niet getest |
| `tests/integration/performance/test_per007_performance.py` | 7 failures; `GenerationRequest` mist verplicht `id`; 1 skip voor ontbrekende `ContextFormatter` | vermoed verouderd testcontract |
| `tests/integration/performance/test_performance_comprehensive.py` | cache 2,284 s > 2,0 s; geheugengroei 167,38 MB > 100 MB | bewezen drempeloverschrijding; stabiliteit nog niet herhaald |
| `tests/integration/performance/test_rule_cache_performance.py` | fixture verwacht `TEST-01`, cache bevat productieregels | vermoed isolatie-/fixturefout |
| `tests/integration/regression/test_category_regeneration.py` | `DefinitionGeneratorTab` mist `_trigger_regeneration_with_category` | vermoed verouderd UI-contract |
| `tests/integration/regression/test_regression_suite.py` | 5 failures: docstringassertie, ontbrekende `ai_toetser`, logmodule en packagefiles; AI-mock vraagt toch key | gemengde bewezen failures; oorzaken nog te reviewen |
| `tests/integration/regression/test_story_2_4_regression.py` | 11 failures, waaronder 8× ontbrekende `ServiceContainer.get_orchestrator` | vermoed verouderd containercontract plus resultaatverschillen |
| `tests/integration/regression/test_validation_orchestrator_v2_regression.py` | initialisatie faalt zonder Anthropic-key | blocked-by-environment-achtig, maar bestand bevat echte failure |
| `tests/integration/security/test_security_comprehensive.py` | 3 failures: rate-limitverwachting en twee sanitizers laten payload onveranderd | **vermoed securityprobleem; broninspectie vereist** |
| `tests/integration/test_per007_acceptance.py` | 5 failures door verplichte `HybridContextManager(config)` | vermoed verouderd testcontract |
| `tests/integration/test_per007_single_source_red.py` | 3 failures: 8 contextpaden, UI-manipulatie en constructorcontract | bewezen RED-technische schuld; niet als xfail gemarkeerd |
| `tests/integration/test_synonym_container_integration.py` | 9 failures door ontbrekende Anthropic-key en ontbrekende synoniementabellen | gemengd environment/schemafixture |
| `tests/integration/test_validate_synonyms.py` | 2 failures: lege `Colors.RESET`; niet-string synonym niet gerapporteerd | vermoed environmenttest en validatorbug |
| `tests/integration/test_voorbeelden_validation_chain.py` | 2 failures: verwachte INFO-log ontbreekt terwijl save slaagt | vermoed verouderde logassertie |

### Blocked en skipped

- `test_def66_lazy_loading.py` en `test_def90_validation_lazy_loading.py` zijn
  **blocked** doordat clientinitialisatie een Anthropic-key vereist.
- `test_ui_integration.py` is **blocked** als testbewijs: pytest verzamelt geen
  tests (exit 5); top-level code vangt fouten zelf af.
- 14 bestanden skippen geheel wegens ontbrekende API-credentials of hun eigen
  skipvoorwaarden. `tests/integration/golden/test_data.py` verzamelt geen tests.
- Live AI-resultaten en credentialafhankelijke externe flows zijn daarom
  **niet getest**; er zijn bewust geen productiecredentials gebruikt.

## Warnings

Warnings zijn niet weggefilterd:

- `pythonjsonlogger.jsonlogger` is deprecated;
- meerdere unclosed SQLite-connections, bestanden en `aiohttp.ClientSession`s;
- `AsyncMock`-coroutines die nooit awaited worden;
- gedepricieerde SQLite datetime-adapter;
- performance-run: 8.000 waarschuwingen over acht ontbrekende validators en
  1.173 `ResourceWarning`-regels.

Deze warnings zijn bewezen waargenomen; impact en prioriteit volgen tijdens de
line-by-line review van de eigenaarbestanden.
