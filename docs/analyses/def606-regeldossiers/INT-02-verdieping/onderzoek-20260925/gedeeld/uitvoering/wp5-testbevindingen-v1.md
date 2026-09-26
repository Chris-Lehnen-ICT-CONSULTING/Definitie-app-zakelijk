# WP5 — volledige pytest en oorzaken per failure

26 september 2026. App-HEAD `5fb535ee45671007e5cb4557509560c793eec290`; skill-HEAD `750068253a7389e201daedc5b9aa0afd5c0be032`. Productiecode en getrackte werkboom na de run gecontroleerd: ongewijzigd.

## Letterlijk resultaat

```text
67 failed, 8212 passed, 114 skipped, 24 xfailed, 3397 warnings, 21 subtests passed in 619.51s (0:10:19)
EXITSTATUS=1
```

Bewijs: `wp5-pytest-volledig.log` en `wp5-pytest-volledig.xml`. Volledige suite met bestaande offline-bootstrap, plus DEF771_SKILLS_ROOT naar de beheerde skillwerkboom. Geen productiegegevens gelezen; pogingen tot repositorydatabase of ontwikkelaars-.env zijn door de gate geblokkeerd.

## Basisvergelijking

De 67 concrete node-ID’s uit de XML staan in `wp5-falende-nodeids.txt`. Die selectie is uitgevoerd in de bestaande git-archive van basis `0d26f0f4f5b2ebebe1c7d71fbff5e4ddb66b8c0d`, `/private/tmp/def771-wp1-basis-1790361228`. De daar eerder aangemaakte synthetische .env bevat uitsluitend een commentaarregel voor de gate-repro; geen echte credentials of productiedata.

```text
66 failed, 1 passed, 6 warnings in 43.24s
EXITSTATUS=1
```

Bewijs: `wp5-basis-failures.log` en `.xml`. De ene groene test was `TestSecurityIntegration::test_security_decorator`. Een tweecasussenproef was ook groen (`wp5-basis-security-volgorde.log`); daarna reproduceerden de twee volledige securitytestbestanden de fout op de basis: `3 failed, 41 passed in 0.98s`, exit 1 (`wp5-basis-security-bestanden.log`). Die derde run gebruikte pytest-randomly-seed 2523026766. Daarmee zijn alle 67 waargenomen failures ook op de basis aangetoond, over deze gerichte controles verdeeld.

De decoratortest faalt doordat het gedeelde middleware-object localhost als geblokkeerd onthoudt na de async-securitytests. `AsyncSecurityTestHarness` gebruikt get_security_middleware en standaard-IP 127.0.0.1; de decorator gebruikt dezelfde singleton en hetzelfde IP (src/security/security_middleware.py:598,615,626). De test is dus afhankelijk van gedeelde toestand/volgorde. Er is geen diff in die securitybron of tests.

Dit is geen identieke volledige baselinesuite: de selectie en testvolgorde verschillen. Timings blijven metingen. Bij twee structurele assertions verschillen aantallen/paden: de basis mist ook docs/architectuur/README.md; HEAD telt 13 ontbrekende __init__.py-bestanden tegen 8 op basis, mede door lokale extra directories. De bronstructuurassertie was al rood. Geen van deze feiten maakt de volledige suite groen.

De eerste make-test-run had vier failures; drie versieasserties zijn door dezelfde Claude-sessie gecorrigeerd naar het goedgekeurde resultaatcontract 2.2.0, met 57 groene tests en lint (`wp5-green.log`, `wp5-lint.log`). De volledige suite hierboven hoort bij die correctie. De .env-gatefailure resteert ook op basis.

## Groepen

- 17: Offlinegate: poging tot repositorydatabase.
- 3: Bestaande timing-/timeoutverwachting.
- 1: Appstart niet binnen de 20-secondenverwachting.
- 3: Open kwaliteit-/snapshotcontracten DEF-626/627/630.
- 1: Bestaande promptstijlassertie.
- 15: Ontbrekende documentatie op verwachte paden.
- 15: PER-007: open context-/presentatie- of performancecontract.
- 2: Ontbrekende verwachte weblookup-output in offline proef.
- 1: Offlinegate: poging tot ontwikkelaars-.env.
- 2: Bestaande MODERATE-sanitization-policy.
- 1: Gedeelde securitytoestand / testvolgorde.
- 6: Bestaande bronstructuur-/documentatieassertie.

## Iedere failure met waargenomen oorzaak en basisbewijs

De foutmeldingen hieronder zijn letterlijk de eerste regel uit de pytest-XML; volledige tracebacks staan in de genoemde logs/XML. Bestaande fouten blijven gemeld buiten de INT-02-scope; geen test verwijderd, verwachting versoepeld of securitygate uitgeschakeld.

### 1. tests.integration.regression.test_validation_orchestrator_v2_regression::test_validation_orchestrator_v2

Groep: Offlinegate: poging tot repositorydatabase.

```text
tests.offline_bootstrap.OfflineGateError: SQLite-doel 'data/definities.db' ligt buiten de tijdelijke sessieroot /private/var/folders/0y/443zs7b950b82xfzg4s_97x00000gn/T/def519-sessie-yqnqwfgk. Gebruik ':memory:' of een pad binnen de sessieroot; repository- en gebruikersdata zijn in tests niet beschikbaar.
```

Basis: eveneens gefaald in `wp5-basis-failures.xml`.

### 2. tests.integration.test_history_removal.TestApplicationFunctionality::test_definition_generation_flow

Groep: Offlinegate: poging tot repositorydatabase.

```text
tests.offline_bootstrap.OfflineGateError: SQLite-doel 'data/definities.db' ligt buiten de tijdelijke sessieroot /private/var/folders/0y/443zs7b950b82xfzg4s_97x00000gn/T/def519-sessie-yqnqwfgk. Gebruik ':memory:' of een pad binnen de sessieroot; repository- en gebruikersdata zijn in tests niet beschikbaar.
```

Basis: eveneens gefaald in `wp5-basis-failures.xml`.

### 3. tests.integration.test_history_removal.TestHistoryTabRemoval::test_tabbed_interface_loads_without_history

Groep: Offlinegate: poging tot repositorydatabase.

```text
tests.offline_bootstrap.OfflineGateError: SQLite-doel 'data/definities.db' ligt buiten de tijdelijke sessieroot /private/var/folders/0y/443zs7b950b82xfzg4s_97x00000gn/T/def519-sessie-yqnqwfgk. Gebruik ':memory:' of een pad binnen de sessieroot; repository- en gebruikersdata zijn in tests niet beschikbaar.
```

Basis: eveneens gefaald in `wp5-basis-failures.xml`.

### 4. tests.integration.test_history_removal.TestHistoryTabRemoval::test_tab_configuration_excludes_history

Groep: Offlinegate: poging tot repositorydatabase.

```text
tests.offline_bootstrap.OfflineGateError: SQLite-doel 'data/definities.db' ligt buiten de tijdelijke sessieroot /private/var/folders/0y/443zs7b950b82xfzg4s_97x00000gn/T/def519-sessie-yqnqwfgk. Gebruik ':memory:' of een pad binnen de sessieroot; repository- en gebruikersdata zijn in tests niet beschikbaar.
```

Basis: eveneens gefaald in `wp5-basis-failures.xml`.

### 5. tests.integration.test_history_removal.TestHistoryTabRemoval::test_no_history_in_tab_rendering

Groep: Offlinegate: poging tot repositorydatabase.

```text
tests.offline_bootstrap.OfflineGateError: SQLite-doel 'data/definities.db' ligt buiten de tijdelijke sessieroot /private/var/folders/0y/443zs7b950b82xfzg4s_97x00000gn/T/def519-sessie-yqnqwfgk. Gebruik ':memory:' of een pad binnen de sessieroot; repository- en gebruikersdata zijn in tests niet beschikbaar.
```

Basis: eveneens gefaald in `wp5-basis-failures.xml`.

### 6. tests.integration.test_history_removal.TestHistoryTabRemoval::test_no_broken_navigation_references

Groep: Offlinegate: poging tot repositorydatabase.

```text
tests.offline_bootstrap.OfflineGateError: SQLite-doel 'data/definities.db' ligt buiten de tijdelijke sessieroot /private/var/folders/0y/443zs7b950b82xfzg4s_97x00000gn/T/def519-sessie-yqnqwfgk. Gebruik ':memory:' of een pad binnen de sessieroot; repository- en gebruikersdata zijn in tests niet beschikbaar.
```

Basis: eveneens gefaald in `wp5-basis-failures.xml`.

### 7. tests.integration.test_history_removal.TestPerformanceImprovement::test_memory_usage

Groep: Offlinegate: poging tot repositorydatabase.

```text
tests.offline_bootstrap.OfflineGateError: SQLite-doel 'data/definities.db' ligt buiten de tijdelijke sessieroot /private/var/folders/0y/443zs7b950b82xfzg4s_97x00000gn/T/def519-sessie-yqnqwfgk. Gebruik ':memory:' of een pad binnen de sessieroot; repository- en gebruikersdata zijn in tests niet beschikbaar.
```

Basis: eveneens gefaald in `wp5-basis-failures.xml`.

### 8. tests.integration.test_ui_integration.TestUIServiceIntegratie::test_broken_service_binding_falls_back_and_is_detected

Groep: Offlinegate: poging tot repositorydatabase.

```text
tests.offline_bootstrap.OfflineGateError: SQLite-doel 'data/definities.db' ligt buiten de tijdelijke sessieroot /private/var/folders/0y/443zs7b950b82xfzg4s_97x00000gn/T/def519-sessie-yqnqwfgk. Gebruik ':memory:' of een pad binnen de sessieroot; repository- en gebruikersdata zijn in tests niet beschikbaar.
```

Basis: eveneens gefaald in `wp5-basis-failures.xml`.

### 9. tests.integration.test_ui_integration.TestUIServiceIntegratie::test_tabbed_interface_binds_real_service_adapter

Groep: Offlinegate: poging tot repositorydatabase.

```text
tests.offline_bootstrap.OfflineGateError: SQLite-doel 'data/definities.db' ligt buiten de tijdelijke sessieroot /private/var/folders/0y/443zs7b950b82xfzg4s_97x00000gn/T/def519-sessie-yqnqwfgk. Gebruik ':memory:' of een pad binnen de sessieroot; repository- en gebruikersdata zijn in tests niet beschikbaar.
```

Basis: eveneens gefaald in `wp5-basis-failures.xml`.

### 10. tests.integration.performance.test_validation_performance_baseline::test_concurrent_validation_scaling

Groep: Bestaande timing-/timeoutverwachting.

```text
AssertionError: Concurrent 5: 0.0083s exceeds expected 0.0029s (baseline 0.0024s). rode repro (eigenaar DEF-519, herbeoordeling uiterlijk 2026-10-06): de oorspronkelijke schaalverwachting elapsed <= baseline * (1 + 0.5 * (n - 1) / 10) heeft geen dekkende productcode; trigger is een productbesluit over schalen van gelijktijdige validatie
```

Basis: eveneens gefaald in `wp5-basis-failures.xml`.

### 11. tests.integration.performance.test_validation_performance_baseline::test_adapter_kapt_blokkerende_regel_af

Groep: Bestaande timing-/timeoutverwachting.

```text
AssertionError: Timeout protection failed: de adapter liet een regel die 3.0s blokkeert 3.01s doorlopen in plaats van af te kappen binnen 2.0s. rode advisory-repro (testdispositie-eigenaar DEF-519, herbeoordeling uiterlijk 2026-10-06): adaptertimeout is nooit gebouwd en is niet productiebedraad; trigger is vrijgegeven productbedrading of een timeoutcontract voor ValidationModuleAdapter
```

Basis: eveneens gefaald in `wp5-basis-failures.xml`.

### 12. tests.integration.performance.test_def110_regression.TestDEF110Regression::test_startup_time_acceptable

Groep: Appstart niet binnen de 20-secondenverwachting.

```text
AssertionError: App did not start within 20s - CRITICAL REGRESSION
```

Basis: eveneens gefaald in `wp5-basis-failures.xml`.

### 13. tests.future_phase_a.test_quality_evidence_contracts::test_def627_oude_score_geldt_niet_als_bewijs_voor_nieuwe_tekst

Groep: Open kwaliteit-/snapshotcontracten DEF-626/627/630.

```text
AssertionError: DEF-627: zonder hervalidatie blijft de score van de vorige tekst als actueel bewijs staan — oorspronkelijk: {'validation_score': 0.95, 'validation_date': None, 'validation_issues': None, 'version_number': 1, 'status': 'draft'}; na bewerking: {'validation_score': 0.95, 'validation_date': None, 'validation_issues': None, 'version_number': 2, 'status': 'draft'}; hervalidatieresultaat van save_definition: None
```

Basis: eveneens gefaald in `wp5-basis-failures.xml`.

### 14. tests.future_phase_a.test_quality_evidence_contracts::test_def626_validatiesnapshot_overleeft_de_opslaggrens

Groep: Open kwaliteit-/snapshotcontracten DEF-626/627/630.

```text
AssertionError: setup: score is geen getal maar None
```

Basis: eveneens gefaald in `wp5-basis-failures.xml`.

### 15. tests.future_phase_a.test_quality_evidence_contracts::test_def630_vaststellen_zonder_actueel_snapshot_wordt_geweigerd

Groep: Open kwaliteit-/snapshotcontracten DEF-626/627/630.

```text
AssertionError: DEF-630: vaststellen wordt niet geweigerd terwijl er geen actueel validatiesnapshot bij de tekst hoort — score=0.95 zonder validation_date/validation_issues; gate-uitkomst preview_gate={'status': 'blocked', 'reasons': ['CON-02 Nog te beoordelen: Er zijn geen bronnen aangeleverd of gevonden; de brongezag/toepasselijkheid kan niet worden beoordeeld. Een bronwoord in de definitiezin is geen bewijs. Vervolgstap: Lever passende bronpassages aan (upload, RAG of web), of laat een deskundige na gedocumenteerd zoeken het ontbreken van een passende bron als uitzondering vastleggen.', 'CON-02 Nog te beoordelen: Er zijn geen bronnen aangeleverd of gevonden; de betekenissteun kan niet worden beoordeeld. Een bronwoord in de definitiezin is geen bewijs. Vervolgstap: Lever passende bronpassages aan (upload, RAG of web), of laat een deskundige na gedocumenteerd zoeken het ontbreken van een passende bron als uitzondering vastleggen.', 'CON-02 Nog te beoordelen: Er zijn geen bronnen aangeleverd of gevonden; de verwijskwaliteit kan niet worden beoordeeld. Een bronwoord in de definitiezin is geen bewijs. Vervolgstap: Lever passende bronpassages aan (upload, RAG of web), of laat een deskundige na gedocumenteerd zoeken het ontbreken van een passende bron als uitzondering vastleggen.']}; update_status gaf True; status vóór='review', na='established', approved_by='synthetische-vaststeller'
```

Basis: eveneens gefaald in `wp5-basis-failures.xml`.

### 16. tests.unit.services.prompts.modules.test_definition_task_transformation.TestDefinitionTaskTransformation::test_no_negative_commands_in_guide

Groep: Bestaande promptstijlassertie.

```text
AssertionError: Guide has 12 negative commands. Should focus on positive construction instructions instead
```

Basis: eveneens gefaald in `wp5-basis-failures.xml`.

### 17. tests.integration.compliance.test_per007_documentation_compliance.TestPER007DocumentationCompliance::test_per007_adr_references

Groep: Ontbrekende documentatie op verwachte paden.

```text
AssertionError: PER-007 ADR niet gevonden op ['/Users/chrislehnen/Projecten/Definitie-app/docs/architectuur/beslissingen/ADR-PER-007-presentation-data-separation.md', '/Users/chrislehnen/Projecten/Definitie-app/docs/archief/ADR-PER-007-presentation-data-separation.md'] en de terugvalbron ontbreekt: /Users/chrislehnen/Projecten/Definitie-app/docs/architectuur/SOLUTION_ARCHITECTURE.md
```

Basis: eveneens gefaald in `wp5-basis-failures.xml`.

### 18. tests.integration.compliance.test_per007_documentation_compliance.TestPER007DocumentationCompliance::test_per007_configuration_documented

Groep: Ontbrekende documentatie op verwachte paden.

```text
AssertionError: Verplichte bron ontbreekt: /Users/chrislehnen/Projecten/Definitie-app/docs/architectuur/TECHNICAL_ARCHITECTURE.md
```

Basis: eveneens gefaald in `wp5-basis-failures.xml`.

### 19. tests.integration.compliance.test_per007_documentation_compliance.TestPER007DocumentationCompliance::test_per007_workflows_documented

Groep: Ontbrekende documentatie op verwachte paden.

```text
AssertionError: Verplichte bron ontbreekt: /Users/chrislehnen/Projecten/Definitie-app/docs/architectuur/SOLUTION_ARCHITECTURE.md
```

Basis: eveneens gefaald in `wp5-basis-failures.xml`.

### 20. tests.integration.compliance.test_per007_documentation_compliance.TestPER007DocumentationCompliance::test_per007_implementation_files_documented

Groep: Ontbrekende documentatie op verwachte paden.

```text
AssertionError: TECHNICAL_ARCHITECTURE.md not found at /Users/chrislehnen/Projecten/Definitie-app/docs/architectuur/TECHNICAL_ARCHITECTURE.md
```

Basis: eveneens gefaald in `wp5-basis-failures.xml`.

### 21. tests.integration.compliance.test_per007_documentation_compliance.TestPER007DocumentationCompliance::test_per007_coverage_in_solution_architecture

Groep: Ontbrekende documentatie op verwachte paden.

```text
AssertionError: SOLUTION_ARCHITECTURE.md not found at /Users/chrislehnen/Projecten/Definitie-app/docs/architectuur/SOLUTION_ARCHITECTURE.md
```

Basis: eveneens gefaald in `wp5-basis-failures.xml`.

### 22. tests.integration.compliance.test_per007_documentation_compliance.TestPER007DocumentationCompliance::test_per007_backwards_compatibility_noted

Groep: Ontbrekende documentatie op verwachte paden.

```text
AssertionError: Verplichte bron ontbreekt: /Users/chrislehnen/Projecten/Definitie-app/docs/architectuur/SOLUTION_ARCHITECTURE.md
```

Basis: eveneens gefaald in `wp5-basis-failures.xml`.

### 23. tests.integration.compliance.test_per007_documentation_compliance.TestPER007DocumentationCompliance::test_per007_migration_status_documented

Groep: Ontbrekende documentatie op verwachte paden.

```text
AssertionError: Verplichte bron(nen) ontbreken: ['/Users/chrislehnen/Projecten/Definitie-app/docs/architectuur/SOLUTION_ARCHITECTURE.md', '/Users/chrislehnen/Projecten/Definitie-app/docs/architectuur/TECHNICAL_ARCHITECTURE.md']
```

Basis: eveneens gefaald in `wp5-basis-failures.xml`.

### 24. tests.integration.compliance.test_per007_documentation_compliance.TestPER007DocumentationCompliance::test_per007_validation_rules_preserved

Groep: Ontbrekende documentatie op verwachte paden.

```text
AssertionError: Verplichte bron ontbreekt: /Users/chrislehnen/Projecten/Definitie-app/docs/architectuur/TECHNICAL_ARCHITECTURE.md
```

Basis: eveneens gefaald in `wp5-basis-failures.xml`.

### 25. tests.integration.performance.test_performance_comprehensive.TestCachePerformance::test_cache_scalability_binnen_twee_seconden

Groep: Bestaande timing-/timeoutverwachting.

```text
AssertionError: Cache scalability test too slow: 2.437s
```

Basis: eveneens gefaald in `wp5-basis-failures.xml`.

### 26. tests.integration.test_per007_acceptance.TestAcceptanceCriteria::test_ac5_complete_context_flow_integration

Groep: PER-007: open context-/presentatie- of performancecontract.

```text
AssertionError: assert 'Anders...' not in ['OM', 'Anders...', 'NieuweOrganisatie', 'DJI', 'LegacyOrg']
```

Basis: eveneens gefaald in `wp5-basis-failures.xml`.

### 27. tests.integration.test_per007_acceptance.TestAcceptanceCriteria::test_ac4_astra_warnings_not_errors

Groep: PER-007: open context-/presentatie- of performancecontract.

```text
AssertionError: geen ASTRA-waarschuwing voor onbekende organisaties
```

Basis: eveneens gefaald in `wp5-basis-failures.xml`.

### 28. tests.integration.test_per007_acceptance.TestAcceptanceCriteria::test_ac7_separation_of_concerns_validated

Groep: PER-007: open context-/presentatie- of performancecontract.

```text
AssertionError: UI-laagbestanden ontbreken: ['/Users/chrislehnen/Projecten/Definitie-app/src/ui/formatters.py', '/Users/chrislehnen/Projecten/Definitie-app/src/ui/components/context_display.py']
```

Basis: eveneens gefaald in `wp5-basis-failures.xml`.

### 29. tests.integration.test_per007_acceptance.TestAcceptanceCriteria::test_ac3_anders_works_all_lists

Groep: PER-007: open context-/presentatie- of performancecontract.

```text
AssertionError: Anders... marker still in: ['organisatorisch', 'juridisch', 'wettelijk']
```

Basis: eveneens gefaald in `wp5-basis-failures.xml`.

### 30. tests.integration.test_per007_acceptance.TestAcceptanceCriteria::test_ac6_no_ui_string_reverse_engineering

Groep: PER-007: open context-/presentatie- of performancecontract.

```text
AssertionError: UI emoji leaked into context
```

Basis: eveneens gefaald in `wp5-basis-failures.xml`.

### 31. tests.integration.test_per007_acceptance.TestAcceptanceCriteria::test_ac1_ui_preview_never_used_as_source

Groep: PER-007: open context-/presentatie- of performancecontract.

```text
AssertionError: ContextFormatter ontbreekt: /Users/chrislehnen/Projecten/Definitie-app/src/services/ui/formatters.py (AC1, dispositie DEF-519)
```

Basis: eveneens gefaald in `wp5-basis-failures.xml`.

### 32. tests.integration.compliance.test_architecture_consolidation.TestArchitectureConsolidation::test_astra_compliance_maintained

Groep: Ontbrekende documentatie op verwachte paden.

```text
AssertionError: Verplichte bron ontbreekt: /Users/chrislehnen/Projecten/Definitie-app/docs/architectuur/ENTERPRISE_ARCHITECTURE.md
```

Basis: eveneens gefaald in `wp5-basis-failures.xml`.

### 33. tests.integration.compliance.test_architecture_consolidation.TestArchitectureConsolidation::test_archive_structure

Groep: Ontbrekende documentatie op verwachte paden.

```text
AssertionError: Archive directory not found at /Users/chrislehnen/Projecten/Definitie-app/docs/archief/2025-09-architectuur-consolidatie
```

Basis: eveneens gefaald in `wp5-basis-failures.xml`.

### 34. tests.integration.compliance.test_architecture_consolidation.TestArchitectureConsolidation::test_canonical_docs_exist

Groep: Ontbrekende documentatie op verwachte paden.

```text
AssertionError: Canonical document ENTERPRISE_ARCHITECTURE.md not found at /Users/chrislehnen/Projecten/Definitie-app/docs/architectuur/ENTERPRISE_ARCHITECTURE.md
```

Basis: eveneens gefaald in `wp5-basis-failures.xml`.

### 35. tests.integration.compliance.test_architecture_consolidation.TestArchitectureConsolidation::test_document_sizes_acceptable

Groep: Ontbrekende documentatie op verwachte paden.

```text
AssertionError: Verplichte bron ontbreekt: /Users/chrislehnen/Projecten/Definitie-app/docs/architectuur/ENTERPRISE_ARCHITECTURE.md
```

Basis: eveneens gefaald in `wp5-basis-failures.xml`.

### 36. tests.integration.compliance.test_architecture_consolidation.TestArchitectureConsolidation::test_frontmatter_present_in_canonical_docs

Groep: Ontbrekende documentatie op verwachte paden.

```text
AssertionError: Verplichte bron ontbreekt: /Users/chrislehnen/Projecten/Definitie-app/docs/architectuur/ENTERPRISE_ARCHITECTURE.md
```

Basis: eveneens gefaald in `wp5-basis-failures.xml`.

### 37. tests.integration.compliance.test_architecture_consolidation.TestArchitectureConsolidation::test_cross_references_between_docs

Groep: Ontbrekende documentatie op verwachte paden.

```text
AssertionError: Verplichte bron(nen) ontbreken: ['/Users/chrislehnen/Projecten/Definitie-app/docs/architectuur/ENTERPRISE_ARCHITECTURE.md', '/Users/chrislehnen/Projecten/Definitie-app/docs/architectuur/SOLUTION_ARCHITECTURE.md', '/Users/chrislehnen/Projecten/Definitie-app/docs/architectuur/TECHNICAL_ARCHITECTURE.md']
```

Basis: eveneens gefaald in `wp5-basis-failures.xml`.

### 38. tests.integration.compliance.test_architecture_consolidation.TestArchitectureConsolidation::test_no_broken_internal_links

Groep: Ontbrekende documentatie op verwachte paden.

```text
AssertionError: Verplichte bron(nen) ontbreken: ['/Users/chrislehnen/Projecten/Definitie-app/docs/architectuur/ENTERPRISE_ARCHITECTURE.md', '/Users/chrislehnen/Projecten/Definitie-app/docs/architectuur/SOLUTION_ARCHITECTURE.md', '/Users/chrislehnen/Projecten/Definitie-app/docs/architectuur/TECHNICAL_ARCHITECTURE.md']
```

Basis: eveneens gefaald in `wp5-basis-failures.xml`.

### 39. tests.smoke.test_web_lookup_health_smoke::test_web_lookup_health_smoke

Groep: Ontbrekende verwachte weblookup-output in offline proef.

```text
assert []
```

Basis: eveneens gefaald in `wp5-basis-failures.xml`.

### 40. tests.integration.performance.test_per007_performance.TestPerformance::test_astra_validation_performance

Groep: PER-007: open context-/presentatie- of performancecontract.

```text
AssertionError: geen ASTRA-validatie waarneembaar tijdens de gemeten call (geen waarschuwing over InvalidOrg/FakeOrg)
```

Basis: eveneens gefaald in `wp5-basis-failures.xml`.

### 41. tests.integration.performance.test_per007_performance.TestPerformance::test_concurrent_processing_performance

Groep: PER-007: open context-/presentatie- of performancecontract.

```text
AssertionError: Concurrent processing too slow: 0.56ms
```

Basis: eveneens gefaald in `wp5-basis-failures.xml`.

### 42. tests.integration.performance.test_per007_performance.TestPerformance::test_ui_formatting_performance

Groep: PER-007: open context-/presentatie- of performancecontract.

```text
AssertionError: ContextFormatter ontbreekt: /Users/chrislehnen/Projecten/Definitie-app/src/services/ui/formatters.py — nooit gebouwd; advisory DEF-519 (testdispositie), herbeoordeling 2026-10-06
```

Basis: eveneens gefaald in `wp5-basis-failures.xml`.

### 43. tests.integration.performance.test_per007_performance.TestPerformance::test_anders_processing_overhead

Groep: PER-007: open context-/presentatie- of performancecontract.

```text
AssertionError: Anders... niet verwerkt; er is dus geen Anders-verwerking gemeten
```

Basis: eveneens gefaald in `wp5-basis-failures.xml`.

### 44. tests.integration.performance.test_per007_performance.TestPerformance::test_end_to_end_flow_performance

Groep: PER-007: open context-/presentatie- of performancecontract.

```text
AssertionError: ContextFormatter ontbreekt: /Users/chrislehnen/Projecten/Definitie-app/src/services/ui/formatters.py — nooit gebouwd; advisory DEF-519 (testdispositie), herbeoordeling 2026-10-06
```

Basis: eveneens gefaald in `wp5-basis-failures.xml`.

### 45. tests.unit.test_config_system.TestConfigManager::test_environment_detection

Groep: Offlinegate: poging tot ontwikkelaars-.env.

```text
tests.offline_bootstrap.OfflineGateError: .env op '/Users/chrislehnen/Projecten/Definitie-app/.env' ligt buiten de tijdelijke sessieroot; de omgeving van de ontwikkelaar mag een test niet beïnvloeden
```

Basis: eveneens gefaald in `wp5-basis-failures.xml`.

### 46. tests.unit.test_performance_tracker.TestGlobalTracker::test_reset_tracker

Groep: Offlinegate: poging tot repositorydatabase.

```text
tests.offline_bootstrap.OfflineGateError: SQLite-doel 'data/definities.db' ligt buiten de tijdelijke sessieroot /private/var/folders/0y/443zs7b950b82xfzg4s_97x00000gn/T/def519-sessie-yqnqwfgk. Gebruik ':memory:' of een pad binnen de sessieroot; repository- en gebruikersdata zijn in tests niet beschikbaar.
```

Basis: eveneens gefaald in `wp5-basis-failures.xml`.

### 47. tests.unit.test_performance_tracker.TestGlobalTracker::test_get_tracker_singleton

Groep: Offlinegate: poging tot repositorydatabase.

```text
tests.offline_bootstrap.OfflineGateError: SQLite-doel 'data/definities.db' ligt buiten de tijdelijke sessieroot /private/var/folders/0y/443zs7b950b82xfzg4s_97x00000gn/T/def519-sessie-yqnqwfgk. Gebruik ':memory:' of een pad binnen de sessieroot; repository- en gebruikersdata zijn in tests niet beschikbaar.
```

Basis: eveneens gefaald in `wp5-basis-failures.xml`.

### 48. tests.smoke.test_web_lookup_wetgeving_parked_smoke::test_wetgeving_parked_attempt_propagates

Groep: Ontbrekende verwachte weblookup-output in offline proef.

```text
assert False
```

Basis: eveneens gefaald in `wp5-basis-failures.xml`.

### 49. tests.integration.security.test_security_comprehensive.TestDefaultSanitizationPolicyAdvisory::test_default_user_input_strips_script_and_iframe

Groep: Bestaande MODERATE-sanitization-policy.

```text
AssertionError: assert '<script' not in 'test<script...(1)</script>'
```

Basis: eveneens gefaald in `wp5-basis-failures.xml`.

### 50. tests.integration.security.test_security_comprehensive.TestDefaultSanitizationPolicyAdvisory::test_default_sanitize_content_strips_script

Groep: Bestaande MODERATE-sanitization-policy.

```text
AssertionError: assert '<script>' not in '<script>alert(1)</script>'
```

Basis: eveneens gefaald in `wp5-basis-failures.xml`.

### 51. tests.integration.security.test_security_comprehensive.TestSecurityIntegration::test_security_decorator

Groep: Gedeelde securitytoestand / testvolgorde.

```text
ValueError: Security validation failed: IP address is blocked
```

Basis: geïsoleerd groen; dezelfde fout `Security validation failed: IP address is blocked` gereproduceerd met beide securitytestbestanden in `wp5-basis-security-bestanden.log`.

### 52. tests.integration.performance.test_def90_validation_lazy_loading.TestServiceContainerIntegration::test_container_validation_orchestrator_method

Groep: Offlinegate: poging tot repositorydatabase.

```text
tests.offline_bootstrap.OfflineGateError: SQLite-doel 'data/definities.db' ligt buiten de tijdelijke sessieroot /private/var/folders/0y/443zs7b950b82xfzg4s_97x00000gn/T/def519-sessie-yqnqwfgk. Gebruik ':memory:' of een pad binnen de sessieroot; repository- en gebruikersdata zijn in tests niet beschikbaar.
```

Basis: eveneens gefaald in `wp5-basis-failures.xml`.

### 53. tests.integration.performance.test_def90_validation_lazy_loading.TestServiceContainerIntegration::test_container_orchestrator_has_lazy_validation

Groep: Offlinegate: poging tot repositorydatabase.

```text
tests.offline_bootstrap.OfflineGateError: SQLite-doel 'data/definities.db' ligt buiten de tijdelijke sessieroot /private/var/folders/0y/443zs7b950b82xfzg4s_97x00000gn/T/def519-sessie-yqnqwfgk. Gebruik ':memory:' of een pad binnen de sessieroot; repository- en gebruikersdata zijn in tests niet beschikbaar.
```

Basis: eveneens gefaald in `wp5-basis-failures.xml`.

### 54. tests.integration.performance.test_def90_validation_lazy_loading.TestPerformanceRegressionValidation::test_orchestrator_init_under_400ms_with_both_lazy

Groep: Offlinegate: poging tot repositorydatabase.

```text
tests.offline_bootstrap.OfflineGateError: SQLite-doel 'data/definities.db' ligt buiten de tijdelijke sessieroot /private/var/folders/0y/443zs7b950b82xfzg4s_97x00000gn/T/def519-sessie-yqnqwfgk. Gebruik ':memory:' of een pad binnen de sessieroot; repository- en gebruikersdata zijn in tests niet beschikbaar.
```

Basis: eveneens gefaald in `wp5-basis-failures.xml`.

### 55. tests.smoke.test_ui_smoke::test_ui_mode[legacy]

Groep: Offlinegate: poging tot repositorydatabase.

```text
tests.offline_bootstrap.OfflineGateError: SQLite-doel 'data/definities.db' ligt buiten de tijdelijke sessieroot /private/var/folders/0y/443zs7b950b82xfzg4s_97x00000gn/T/def519-sessie-yqnqwfgk. Gebruik ':memory:' of een pad binnen de sessieroot; repository- en gebruikersdata zijn in tests niet beschikbaar.
```

Basis: eveneens gefaald in `wp5-basis-failures.xml`.

### 56. tests.smoke.test_ui_smoke::test_ui_mode[new]

Groep: Offlinegate: poging tot repositorydatabase.

```text
tests.offline_bootstrap.OfflineGateError: SQLite-doel 'data/definities.db' ligt buiten de tijdelijke sessieroot /private/var/folders/0y/443zs7b950b82xfzg4s_97x00000gn/T/def519-sessie-yqnqwfgk. Gebruik ':memory:' of een pad binnen de sessieroot; repository- en gebruikersdata zijn in tests niet beschikbaar.
```

Basis: eveneens gefaald in `wp5-basis-failures.xml`.

### 57. tests.integration.performance.test_def66_lazy_loading.TestPerformanceRegression::test_tabbed_interface_reuses_prewarmed_container_and_repository

Groep: Offlinegate: poging tot repositorydatabase.

```text
tests.offline_bootstrap.OfflineGateError: SQLite-doel 'data/definities.db' ligt buiten de tijdelijke sessieroot /private/var/folders/0y/443zs7b950b82xfzg4s_97x00000gn/T/def519-sessie-yqnqwfgk. Gebruik ':memory:' of een pad binnen de sessieroot; repository- en gebruikersdata zijn in tests niet beschikbaar.
```

Basis: eveneens gefaald in `wp5-basis-failures.xml`.

### 58. tests.integration.regression.test_regression_suite.TestRegressionSpecific::test_modern_service_encoding_fix

Groep: Bestaande bronstructuur-/documentatieassertie.

```text
AssertionError: verwachte bronbestanden ontbreken: ['/Users/chrislehnen/Projecten/Definitie-app/src/services/unified_definition_generator.py']
```

Basis: eveneens gefaald in `wp5-basis-failures.xml`.

### 59. tests.integration.regression.test_regression_suite.TestRegressionSpecific::test_logs_import_resolution

Groep: Bestaande bronstructuur-/documentatieassertie.

```text
AssertionError: verplichte module ontbreekt: logs.application.log_definitie (verwacht onder /Users/chrislehnen/Projecten/Definitie-app/logs/application)
```

Basis: eveneens gefaald in `wp5-basis-failures.xml`.

### 60. tests.integration.regression.test_regression_suite.TestImportStructure::test_package_init_files

Groep: Bestaande bronstructuur-/documentatieassertie.

```text
AssertionError: Ontbrekende __init__.py bestanden in 13 van 65 mappen: ['analysis', 'cache', 'models', 'orchestration', 'api', 'UNKNOWN.egg-info', 'pages', 'reports', 'ui/services', 'database/migrations', 'services/policies', 'services/prompts', 'ui/components/tabs']
```

Basis: eveneens gefaald in `wp5-basis-failures.xml`.

### 61. tests.integration.regression.test_regression_suite.TestNederlandseCommentaren::test_docstrings_are_dutch

Groep: Bestaande bronstructuur-/documentatieassertie.

```text
AssertionError: Te veel bestanden zonder Nederlandse docstrings: 186/406, eerste vijf: ['api/feature_status_api.py', 'cli/performance_cli.py', 'config/config_manager.py', 'config/feature_flags.py', 'database/audit_helpers.py']
```

Basis: eveneens gefaald in `wp5-basis-failures.xml`.

### 62. tests.integration.regression.test_regression_suite.TestNederlandseCommentaren::test_inline_comments_are_dutch

Groep: Bestaande bronstructuur-/documentatieassertie.

```text
AssertionError: Te veel bestanden met onvoldoende Nederlandse commentaren: 52/285 beoordeeld, eerste vijf: [('config/__init__.py', 0.6), ('config/synonym_config.py', 0.3), ('database/definitie_repository.py', 0.5), ('database/migrations/schema3_herstel.py', 0.62), ('database/migrations/v5_migration.py', 0.51)]
```

Basis: eveneens gefaald in `wp5-basis-failures.xml`.

### 63. tests.integration.regression.test_regression_suite.TestNederlandseCommentaren::test_function_documentation_completeness

Groep: Bestaande bronstructuur-/documentatieassertie.

```text
AssertionError: Te veel ongedocumenteerde functies: 211/648, eerste tien: ['api/feature_status_api.py:lifespan', 'api/feature_status_api.py:get_feature_status (no Dutch)', 'api/feature_status_api.py:get_feature_summary (no Dutch)', 'api/feature_status_api.py:get_epic_status (no Dutch)', 'api/feature_status_api.py:get_features_by_status (no Dutch)', 'cli/performance_cli.py:performance (no Dutch)', 'cli/performance_cli.py:status (no Dutch)', 'cli/performance_cli.py:baselines (no Dutch)', 'config/__init__.py:get_api_config', 'config/__init__.py:get_cache_config']
```

Basis: eveneens gefaald in `wp5-basis-failures.xml`.

### 64. tests.integration.test_per007_single_source_red.TestSingleSourceOfTruth::test_no_direct_context_string_processing

Groep: PER-007: open context-/presentatie- of performancecontract.

```text
AssertionError: Direct string processors still active: ['HybridContextManager._parse_context_string']
```

Basis: eveneens gefaald in `wp5-basis-failures.xml`.

### 65. tests.integration.test_per007_single_source_red.TestSingleSourceOfTruth::test_context_flow_has_single_entry_point

Groep: PER-007: open context-/presentatie- of performancecontract.

```text
AssertionError: Multiple context entry points: ['EnrichedContext.__init__', 'HybridContextManager']. Should only be HybridContextManager
```

Basis: eveneens gefaald in `wp5-basis-failures.xml`.

### 66. tests.integration.test_per007_single_source_red.TestSingleSourceOfTruth::test_no_context_manipulation_in_ui_layer

Groep: PER-007: open context-/presentatie- of performancecontract.

```text
AssertionError: UI layer manipulating context in: ['src/ui/components/expert_review_tab.py']
```

Basis: eveneens gefaald in `wp5-basis-failures.xml`.

### 67. tests.integration.test_per007_single_source_red.TestSingleSourceOfTruth::test_only_one_context_processing_path_exists

Groep: PER-007: open context-/presentatie- of performancecontract.

```text
AssertionError: Found 8 total paths but only 1 valid. Multiple context routes exist: ['src/services/definition_generator_context.py:_build_base_context', 'src/services/prompts/modules/context_awareness_module.py:_build_rich_context_section', 'src/services/prompts/modules/context_awareness_module.py:_build_moderate_context_section', 'src/services/prompts/modules/context_awareness_module.py:_build_minimal_context_section', 'src/services/prompts/modules/context_awareness_module.py:_build_fallback_context_section']
```

Basis: eveneens gefaald in `wp5-basis-failures.xml`.

## Open checkpoint

De voorgeschreven onafhankelijke Codex CLI-review ontbreekt door 401 Unauthorized. Geen algemene regressievrijheid, groene volledige suite, actieve skilluitrol of afgeronde oplevering geclaimd. Het herstelverzoek voor de CLI-aanmelding staat bij Chris. Geen PR, Linear-oplevering of merge uitgevoerd.
