# BATCH-017 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-hypatia`
- Onafhankelijke verifier: `codex-root`
- Scope: 6/6 blobs, 1.801/1.801 fysieke regels en 43/43 Python-symbolen

Alle regels, functies, callers en foutpaden zijn vanuit immutable object-ID's
beoordeeld. Er is geen applicatiecode gewijzigd.

## Verificatie

- Gerichte selectie: 136 tests geslaagd; één verouderde regeneratietest faalde.
- Batchvalidatie: 6 geslaagd en één timingtest in CI-modus overgeslagen.
- Ruff en Black schoon; veilige mocks, geen netwerk of credentials.

## Bevindingen

### B017-001 — P1 — import schrijft naar de projectroot

`src/services/synonym_orchestrator.py:49-111` maakt bij import `logs/` en een
`FileHandler`. Import in een read-only checkout gaf `PermissionError`; de
container valt dan terug zonder enrichment en de beheerpagina importeert direct.
Aanbevolen: geen I/O bij import, logging uitsluitend in bootstrap configureren
naar writable/stdout en `OSError` gecontroleerd afhandelen.

### B017-002 — P1 — force-duplicate blijft na één generatie actief

`src/ui/handlers/definition_generation_handler.py:243-252,486-492` zet twee
force-flags maar ruimt alleen `force_generate` op. De orchestrator en repository
dragen `force_duplicate` door en omzeilen daarmee de duplicate guard. Na een
mock-succes bleef `{'force_duplicate': True}` in de sessie. Aanbevolen: beide
flags in `finally` verwijderen en de bypass aan één request/beslissing binden.

### B017-003 — P2 — duplicate-checkrepresentatie vervangt organisatienaam

`definition_generation_handler.py:115-117,203-212,315-324` overschrijft `DJI`
met de JSON-string `["DJI"]` en geeft die aan generatie/cachecontext door. Een
mock ving exact deze organisatieparameter. Aanbevolen: afzonderlijke variabelen
voor primaire organisatie en genormaliseerde duplicate-checkcontext.

### B017-004 — P2 — servicefailure wordt als succes getoond

`definition_generation_handler.py:338-351,407-423,505-516` kent `success`, maar
slaat failureoutput op en toont daarna onvoorwaardelijk succes. Een response
`success=False,error=provider failed` gaf één `st.success` en geen `st.error`.
Aanbevolen: expliciete failurebranch, veilige fouttekst en geen success-state.

### B017-005 — P2 — cachecheck en cacheget zijn niet atomair

`synonym_orchestrator.py:197-202,395-453,489-528` neemt de lock tweemaal.
Invalidatie tussen check en get gaf deterministisch `KeyError('term')` vóór de
registryfallback. Aanbevolen: atomische get-if-fresh onder één lock of een
tolerante get die als cachemiss opnieuw probeert.

### B017-006 — P2 — duplicateflow gebruikt altijd categorie PROCES

`definition_generation_handler.py:522-563` hardcodeert `PROCES`; de actieve
algemene caller gebruikt dit ook bij TYPE. Een capture bij TYPE zag PROCES.
Aanbevolen: geselecteerde/sessioncategorie expliciet doorgeven en dezelfde bron
als de generatieflow gebruiken.

### B017-007 — P3 — expliciete minimumweight 0,0 wordt genegeerd

`synonym_orchestrator.py:162-183,221` gebruikt `min_weight or default`. Repro
met 0,0 liet de registry 0,7 ontvangen. Aanbevolen: alleen bij `None` defaulten.

### B017-008 — P3 — actieve Test Prompt-knop test niets

`src/ui/components/prompt_debug_section.py:155-180` presenteert model,
temperature en een actieve knop, maar meldt na klikken alleen “binnenkort”.
Aanbevolen: knop disabled met beta-uitleg of de test werkelijk implementeren.

## Niet getest

- Geen echte AI-enrichment, databasecallback-race of productieopslag.
- Geen browservisuals, toetsenbord, screenreader, contrast of viewports.
