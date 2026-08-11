# BATCH-105 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-root`
- Onafhankelijke verifier: `codex-galileo`
- Scope: 20/20 blobs, 3232/3232 fysieke regels en 81/81 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit immutable Git-objecten gelezen. Callers, foutpaden en relevante tests zijn gevolgd; applicatie- en testbestanden zijn niet gewijzigd.

## Verificatie

- De actuele Story-2.4-unitset gaf 24/24 groen; de handmatige runners en gates zijn daarnaast afzonderlijk op exitcode, collection en foutpaden gereproduceerd.
- Object-ID's, EOF-ranges, line owners en symbol-memberships matchten het batchmanifest exact.

## Bevindingen

### B105-001 — P2 — Actieve quick-check-workflow slaagt zonder uitvoerbare checks

**Bewijs:** Het canonieke checkscript en alle drie targettests ontbreken; de fallback gebruikt een door Rust-ripgrep geweigerde lookahead maar behandelt de parsefout als geen match. De actieve PR-workflow roept dit script aan en de run eindigt met Quick checks passed.

**Reproductie:** Voer `bash scripts/testing/agent_quick_checks.sh` uit: rg meldt look-around is not supported, er worden nul targets gevonden en het proces eindigt met exitcode 0.

**Aanbevolen oplossing:** Gebruik een valide regex of expliciet PCRE2, laat iedere grep-/parsefout hard falen, verwijs naar bestaande tests en eis dat minimaal één test is verzameld.

### B105-002 — P3 — Markercontrole accepteert modifiers en docstringtekst als classificatie

**Bewijs:** slow en flaky staan in de classificatie-enum en de regelgebaseerde parser herkent zelfs `pytestmark = pytest.mark.unit` binnen een module-docstring. De huidige codebase heeft nul weak-only-bestanden, dus de impact is latent maar de gate is actief.

**Reproductie:** Roep `has_classification_marker` aan met een slow-only blok, een flaky-only blok en een triple-quoted docstring met pytestmark; alle drie retourneren True.

**Aanbevolen oplossing:** Parse top-level Python-AST/tokenstructuur, behandel slow/flaky alleen als modifiers en voeg adversarial regressietests toe.

### B105-003 — P2 — Live operationele tests rapporteren volledige mislukking met exitcode 0

**Bewijs:** Zeven geforceerde endpointmislukkingen leveren return None en exitcode 0. Dezelfde false-greenklasse is bewezen in test_rechtspraak_scraping.py, test_rechtspraak_rest_fix.py, test_rechtspraak_search.py en test_web_lookup_live.py.

**Reproductie:** Mock alle endpointfuncties als failure en voer main uit: 7/7 SRU-failures, 3/3 scraping-failures, 0/3 searchresultaten en vier weblookup-failures beëindigen zonder foutstatus.

**Aanbevolen oplossing:** Tel semantische resultaten, laat iedere echte failure nonzero eindigen en onderscheid ontbrekende netwerktoegang expliciet als skip/blocked.

### B105-004 — P3 — Gedocumenteerde synonym-orchestrator-test importeert verwijderd modulepad

**Bewijs:** De import services.gpt4_synonym_suggester bestaat niet in de immutable base. De commandoregel staat nog in twee documentatiebestanden, maar is geen app- of CI-caller.

**Reproductie:** Voer het script met project-Python uit; het stopt bij import met ModuleNotFoundError en exitcode 1.

**Aanbevolen oplossing:** Migreer het script naar de actuele suggester-API en voeg een offline smoke-test toe, of verwijder de verouderde documentatie en het script.

### B105-005 — P2 — Migratieverificatie verklaart een lege of andere worktree volledig voltooid

**Bewijs:** Het script gebruikt een hardcoded absolute docs-root, analyseert alleen de eerste vijf stories en baseert het eindoordeel alleen op ontbrekende/orphan-referenties. Een fixture met nul epics, stories en requirements meldt MIGRATION FULLY COMPLETE AND VERIFIED.

**Reproductie:** Laat Path naar drie lege tijdelijke directories wijzen en voer main uit; de tellingen zijn alle nul en het volledige-succesbericht wordt toch afgedrukt.

**Aanbevolen oplossing:** Maak de root expliciet, eis een niet-lege exacte scope, controleer alle documenten en laat completeness- en referentiefouten de exitcode blokkeren.

### B105-006 — P2 — PER-007 TDD-runner slikt een lege falende GREEN- en CONFIRM-run

**Bewijs:** De stale glob tests/test_per007_*.py verzamelt nul tests. Pytest meldt failure, waarna de else-tak eindigt met succesvolle echo/checklistcommando's en het script exitcode 0 retourneert; CONFIRM heeft hetzelfde propagatieprobleem. Pytest is bovendien ongepind aan sys.executable.

**Reproductie:** Voer `bash scripts/testing/run_per007_tdd.sh GREEN` uit met cache uitgeschakeld; pytest meldt file not found en collected 0 items, maar de shell exitcode is 0.

**Aanbevolen oplossing:** Gebruik de repo-root, project-Python en actuele paden/markers; eis collection groter dan nul en propageer de pytest-exitcode in iedere fase.

### B105-007 — P3 — Story-2.4-runner weigert een geldige gekozen suite wegens drie stale globale paden

**Bewijs:** De actuele unitfile slaagt met 24 tests, maar zelfs --suite unit valideert vooraf vier hardcoded paden waarvan drie niet bestaan en stopt met exitcode 1.

**Reproductie:** Draai eerst pytest op tests/unit/test_story_2_4_unit.py (24 passed) en daarna de runner met --suite unit (drie missing files, exit 1).

**Aanbevolen oplossing:** Valideer alleen de geselecteerde suite, map de actuele integration/regression/performance-paden en start pytest met sys.executable.

### B105-008 — P3 — Gedocumenteerde fast- en performanceprofielen wijzen naar ontbrekende paden

**Bewijs:** Fast bevat het ontbrekende tests/services en eindigt met pytest-exitcode 4; perf gebruikt het eveneens ontbrekende tests/performance. TESTING_GUIDE verwijst bovendien naar ./scripts/run_tests.sh in plaats van scripts/testing/run_tests.sh. CI gebruikt alleen het correcte pr-profiel.

**Reproductie:** Voer het fast-profiel uit: pytest meldt tests/services not found en exit 4; controleer dat tests/performance niet in de base-tree bestaat.

**Aanbevolen oplossing:** Gebruik actuele directories of markerselection, corrigeer de documentatie en voeg contracttests voor ieder runnerprofiel toe.

### B105-009 — P3 — History-removal-verificatie skipt of slikt de enige pytest-suite

**Bewijs:** De scripts verwachten tests/test_history_removal.py, terwijl de test onder tests/integration staat. Het Makefile gebruikt `|| true`, quick_verify skipt een ontbrekend bestand en de aangeroepen Python-verifier behandelt missing of failing pytest expliciet als succes.

**Reproductie:** Controleer de base-tree en voer de betreffende testtargetlogica uit: het pad ontbreekt, maar de verificatie blijft groen of slaat de suite over.

**Aanbevolen oplossing:** Verwijs naar de actuele integrationtest en maak ontbreken, collection 0 en iedere pytestfailure blokkerend met onveranderde exitcode.

### B105-010 — P3 — Cachebenchmark accepteert negatieve verbetering zonder cachebewijs

**Bewijs:** Iedere rerun na nummer 1 wordt zonder instrumentatie als cache hit gelabeld en de uiteindelijke boolean kijkt alleen naar gemiddelde hitduur onder 50 ms. Een cold call van 1 ms en hits van 11 ms geven -1000 procent verbetering maar return True en ACCEPTABLE.

**Reproductie:** Mock perf_counter met 1 ms voor de eerste call en 11 ms voor vijf vervolgcalls; measure_performance retourneert True ondanks negatieve verbetering.

**Aanbevolen oplossing:** Meet echte cache-hit/call-countinformatie, valideer de baseline en eis zowel positieve significante verbetering als de absolute latencygrens.

## Niet getest

- Geen echte SRU/Rechtspraak/provider/netwerkcalls, browser of productiegegevens; handmatige scripts zijn offline of met mocks beoordeeld.
