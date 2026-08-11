# BATCH-106 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Vastgelegde reviewer: `codex-hypatia`
- Onafhankelijke verifier: `codex-kierkegaard`
- Scope: 16/16 bereiken, 3976/3976 fysieke regels en 89/89 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit immutable Git-objecten gelezen. Callers, foutpaden en relevante tests zijn gevolgd; applicatie- en testbestanden zijn niet gewijzigd.

## Verificatie

- De gerichte selectie gaf 73 groene en acht verwachte rode gevallen; de rode gevallen bewijzen de geregistreerde contract- en omgevingsproblemen. Ruff, Black en bash -n waren schoon.
- Object-ID's, ranges, line owners en symbol-memberships matchten het batchmanifest exact.

## Bevindingen

### B106-001 — P3 — Consolidation-runner gebruikt verwijderde testpaden en stopt voor rapportage

**Bewijs:** De runner noemt tests/test_architecture_consolidation.py en tests/test_per007_documentation_compliance.py, terwijl de basebestanden onder tests/integration/compliance staan. Door set -e stopt de command substitution direct; de offline run eindigde met exit 4 voor de eerste samenvatting.

**Reproductie:** Run met PYTEST_ADDOPTS='-p no:cacheprovider' bash scripts/testing/test_consolidation.sh; observeer exit 4 na de eerste ontbrekende pytest-node.

**Aanbevolen oplossing:** Gebruik de actuele testpaden, handel pytest-exitcodes expliciet af en ontleen aantallen aan pytest/JUnit in plaats van vaste +10-tellingen.

### B106-002 — P2 — History-removal-verificatie muteert standaard de live applicatiedatabase

**Bewijs:** De verifier opent data/definities.db, INSERT een __TEST_HISTORY__-definitie en DELETE/commit daarna. De shellvariant doet losse autocommit-operaties op dezelfde standaarddatabase in regels 165-213, waardoor onderbreking testdata kan achterlaten.

**Reproductie:** Voer uitsluitend tegen een databasekopie uit, vergelijk definities voor en na en onderbreek de shellvariant na de INSERT; niet tegen productiedata uitvoeren.

**Aanbevolen oplossing:** Injecteer verplicht een tijdelijke of in-memory database, gebruik een transactie met rollback en weiger expliciet data/definities.db als testdoel.

### B106-003 — P3 — Requirements-verifier is checkout-gebonden en crasht op de verdwenen scope

**Bewijs:** BASE_PATH is hardcoded op /Users/chrislehnen/Projecten/Definitie-app/docs/requirements. Die map bevat nul requirements; de directe run analyseerde 0 bestanden en eindigde met ZeroDivisionError op regel 144.

**Reproductie:** Voer scripts/testing/verify_requirements_fix.py vanuit de reviewworktree uit; observeer Total requirements analyzed: 0 en exit 1 met ZeroDivisionError.

**Aanbevolen oplossing:** Bepaal de root uit __file__ of CLI, behandel een lege inventory als expliciete fout en schrijf rapporten alleen atomisch naar een gekozen outputpad.

### B106-004 — P3 — Een kopje Acceptatiecriteria maakt alle vijf SMART-criteria waar

**Bewijs:** Regels 69-72 overschrijven ieder inhoudelijk resultaat met True zodra smart criteria of acceptatiecriteria voorkomt. Een mockbestand met alleen ## Acceptatiecriteria en Niets concreets retourneerde vijfmaal True.

**Reproductie:** Roep check_smart_criteria aan op '## Acceptatiecriteria\nNiets concreets.' en inspecteer de vijf True-resultaten.

**Aanbevolen oplossing:** Gebruik het kopje alleen als sectie-afbakening, bewijs ieder criterium onafhankelijk en laat een lege analysematrix nonzero falen.

### B106-005 — P3 — Bulk title updater schrijft ongeldige YAML bij aanhalingstekens

**Bewijs:** De beschrijving wordt zonder escaping tussen dubbele quotes geplaatst en het bestand direct overschreven. Een story met 'Als gebruiker wil ik "veilig inloggen"' produceerde ongeldige titel-YAML en yaml.safe_load gaf ParserError.

**Reproductie:** Gebruik een Path-dubbel met een storyregel die dubbele quotes bevat, roep update_us_title aan en parse de geschreven tekst met yaml.safe_load.

**Aanbevolen oplossing:** Parse en dump frontmatter structureel, quote strings correct, valideer voor schrijven en gebruik een tijdelijk bestand plus atomic replace.

### B106-006 — P3 — Afwijkende juridische boostfactoren worden gewaarschuwd maar goedgekeurd

**Bewijs:** Bij een waardeverschil wordt all_valid niet False. Met juridische_bron=9.9 printte de functie zowel een waarschuwing als 'Alle boost factors correct' en retourneerde True.

**Reproductie:** Mock yaml.safe_load met alle verwachte keys en een afwijkende juridische_bron-waarde en roep validate_boost_factors aan.

**Aanbevolen oplossing:** Registreer iedere mismatch als fout, valideer extra en ontbrekende keys tegen een schema en retourneer nonzero.

### B106-007 — P3 — Geen webresultaten geldt als bewijs dat double-weighting is opgelost

**Bewijs:** all(r.source.confidence <= 1.0 for r in results) is True voor een lege lijst. Een offline fake service met nul resultaten retourneerde empty_results_returned=True; de bovengrens kan bovendien afgekapte double-weighting niet onderscheiden.

**Reproductie:** Vervang ModernWebLookupService door een fake waarvan lookup [] retourneert en voer test_no_double_weighting uit.

**Aanbevolen oplossing:** Vereis representatieve resultaten en controleer met deterministische providerfixtures de score voor en na exact één weightingstap.

### B106-008 — P3 — Negatieve SynonymRegistry-contractchecks kunnen falen terwijl de suite slaagt

**Bewijs:** Ontbrekende ValueErrors printen alleen FAILED en veranderen geen resultaat. Een fake registry die alle vier ongeldige inputs accepteerde printte vier failures en test_error_handling retourneerde None; main meldt daarna nog ALL TESTS PASSED.

**Reproductie:** Roep test_error_handling aan met een fake add_group_member die altijd een id retourneert.

**Aanbevolen oplossing:** Gebruik assertions of gestructureerde resultaten en laat iedere negatieve contractschending bijdragen aan exit 1.

### B106-009 — P2 — SynonymRegistry-validatie persisteert fixtures in de standaarddatabase zonder cleanup

**Bewijs:** SynonymRegistry() gebruikt het standaard DB-pad en de tests maken groepen en leden voor voorarrest_test, test_invalidation en andere fixtures. Er is geen teardown of rollback.

**Reproductie:** Draai uitsluitend tegen een gekopieerde DB en vergelijk synonym_groups en synonym_group_members voor en na; niet tegen productiedata uitvoeren.

**Aanbevolen oplossing:** Injecteer verplicht een tijdelijke DB, maak fixtures uniek en rol alle wijzigingen transactioneel terug.

### B106-011 — P2 — Niet-eindige synonym weights passeren de validator

**Bewijs:** float('NaN') slaagt en zowel weight < 0 als weight > 1 is bij NaN false. De directe repro retourneerde ([], []).

**Reproductie:** Roep validate_synonym_weights aan met {'term':[{'synoniem':'x','weight':'NaN'}]}.

**Aanbevolen oplossing:** Eis na conversie math.isfinite(weight) en behandel NaN en plus/min oneindig als fouten.

### B106-012 — P3 — Week1-validator retourneert succes wanneer alle controles falen

**Bewijs:** Een directe run vond 0 van 46 YAML-bestanden, 0 workflows en geen baseline, printte drie FAILs maar eindigde met exitcode 0.

**Reproductie:** Run bash scripts/validate_week1.sh en vergelijk de FAIL-uitvoer met de exitcode.

**Aanbevolen oplossing:** Aggregeer failures en exit 1; actualiseer inventarispaden en valideer inhoud in plaats van alleen aantallen.

### B106-013 — P2 — Make validation-status draait een verwijderd testpad en schrijft niet naar de geclaimde locatie

**Bewijs:** De pytestnode tests/services/test_modular_validation_service_contract.py bestaat niet; het actuele bestand staat onder tests/integration/contracts. Main schrijft twee rootbestanden, terwijl Makefile reports/status/validation-status.json belooft.

**Reproductie:** Controleer het ontbrekende Git-object en traceer de twee outputcalls; voer het volledige target alleen uit met gemockte container en tijdelijke outputdirectory.

**Aanbevolen oplossing:** Gebruik het actuele testpad, één expliciete outputdirectory en credentialvrije lazy dependencychecks met foutpropagatie.

### B106-014 — P2 — V2-migratieverificatie negeert een ontbrekende of falende smoke-test

**Bewijs:** De genoemde node test_service_container_initialization bestaat niet; de huidige node heet test_smoke_generation. De else-tak print alleen een waarschuwing en run_smoke_tests retourneert status 0, zodat overall_status ongewijzigd blijft.

**Reproductie:** Voer de op regel 90 genoemde pytestnode uit en observeer node-not-found; simuleer vervolgens de run_smoke_tests-tak en inspecteer status 0.

**Aanbevolen oplossing:** Gebruik de actuele credentialvrije smoke-node en laat missing, skipped en failed expliciet nonzero propageren.

## Niet getest

- Geen echte provider, credential, netwerk, productiedatabase of browser; muterende scripts zijn alleen statisch, met mocks of op tijdelijke data onderzocht.
