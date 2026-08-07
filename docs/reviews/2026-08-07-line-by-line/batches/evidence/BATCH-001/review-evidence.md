# BATCH-001 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-root`
- Onafhankelijke verifier: `codex-kierkegaard`
- Scope: 8/8 blobs, 2.581/2.581 fysieke regels en 119/119 Python-symbolen
- Ruw bewijsarchief: `raw-evidence.tar.gz`
- SHA-256 bewijsarchief: `d8178544872fecf40001396339508ba0e8aaa57fbe9b89179aca1f7790b4a50c`

De bestanden zijn rechtstreeks uit hun immutable Git-object-ID gelezen. Voor
ieder symbool is een referentiezoekactie tegen de base-tree uitgevoerd. De
ruwe matrix, primaire review en pytest-uitvoer staan in het bewijsarchief.
Geen applicatiebestand is gewijzigd.

## Verificatie

- Pilotselectie met dummy providerinitialisatie: 28/28 tests geslaagd. Er zijn
  geen echte providerrequests gedaan. De run rapporteerde ongeclosed
  SQLite-resources.
- Relevante caller- en regressietests: 81 geslaagd, 5 expliciet overgeslagen.
- Zonder credentials: 8 smoke-tests geslaagd, 1 gefaald doordat service-init
  al een API-key vereist.
- Ruff op de acht toegewezen Pythonbestanden: geslaagd.
- Streamlit health endpoint: `ok`; hoofdpagina: HTTP 200.
- Streamlit AppTest: startup zonder exception; vier knoppen, twee selectboxes
  en drie gelabelde tekstvelden; de no-contextflow deed geen externe AI-call.

## Bewezen bevindingen

### PILOT-001 — P1 — gelijktijdige transacties verliezen succesvolle writes

`src/database/db_connection.py:19-94` bewaart een gedeelde SQLiteconnection
met `check_same_thread=False`; iedere al actieve transactie geldt als genest,
zonder thread- of sessie-eigenaar. Twee threads zijn deterministisch
georkestreerd: thread B keerde succesvol terug, waarna rollback door thread A
ook B's write verwijderde (`thread_B_errors=[]`, `rows=[]`). Aanbevolen:
connection-per-transactie/request of een thread-/contextlokale pool,
transaction ownership en savepoints/rollback-only-semantiek.

### PILOT-002 — P2 — reviewaudit gebruikt altijd fictieve actor

`src/ui/components/definition_generator_tab.py:662-689` geeft altijd
`user="web_user"` door. De workflow persisteert dit downstream als auditactor.
Met `current_user="alice"` bleef de call exact `user="web_user"`. Aanbevolen:
haal een verplichte principal server-side uit één authcontext en blokkeer de
mutatie wanneer die ontbreekt.

### PILOT-003 — P1 — schema-init maskeert defecte of onvolledige databases

`src/database/db_connection.py:96-156` controleert slechts twee tabellen,
draait het volledige schema alleen bij count nul en slikt `executescript`-
fouten. Een database met alleen `definities` bleef zonder exception onvolledig;
een gemockte `schema broken`-fout werd alleen gelogd. Aanbevolen: versioned,
atomaire migraties; valideer alle vereiste objecten en fail startup/readiness.

### PILOT-004 — P2 — service-init vereist credentials vóór een AI-flow

`src/services/service_factory.py:120-130,767-790` bouwt de orchestrator en
clients bij adapterconstructie. Zonder keys faalt service-init; met alleen een
Anthropic-dummykey blijft OpenAI-embeddinginit falen. Aanbevolen: lazy clients,
config-/clientinjectie en hermetische smoke-fixtures.

### PILOT-005 — P2 — strings `false` en `0` worden waar

`src/services/service_factory.py:240-340` past Python `bool()` toe op externe
waarden. `"false"`, `"False"`, `"0"` en `"no"` leverden `True`. Aanbevolen:
een strikte centrale parser die alleen echte booleans of een kleine expliciete
stringenum accepteert en verder fail-closed reageert.

### PILOT-006 — P2 — smoke-tests schrijven naar de standaarddatabase

`tests/smoke/test_critical_paths.py:40-49,96-106,136-146` maakt repositories
zonder tijdelijk databasepad. De test liet `data/definities.db` achter in de
execution-worktree. Aanbevolen: `tmp_path`/fixtures en een testmode-gate die
toegang tot het standaard ontwikkelpad weigert.

### PILOT-007 — P2 — documentcontext staat in promptdebug en download

`src/ui/components/definition_generator_tab.py:149-161,457-501` rendert
promptdebug zonder rol- of environmentgate. AppTest met
`DOCUMENT_SECRET_CASE_123` toonde exact die tekst in `st.code` en bood een
downloadknop. Aanbevolen: productie-default uit, admin/debugautorisatie,
redactie van documentinhoud en audit op downloads.

### PILOT-008 — P2 — definitietekst wordt letterlijk gelogd

`src/ui/components/definition_generator_tab.py:627-647` schrijft bij
opschoning de eerste 100 tekens van origineel en correctie naar debuglogs.
Dat de inhoud wordt gelogd is bewezen; of een concrete invoer persoonsgegevens
bevat is contextafhankelijk. Aanbevolen: uitsluitend IDs, lengtes en een
niet-omkeerbare digest loggen.

### PILOT-009 — P2 — interne exceptiondetails verschijnen in de UI

`src/ui/components/definition_generator_tab.py:404-407,445-455,687-689,715-717`
interpoleert raw exceptions. Een `RuntimeError('/srv/private.db: token=secret')`
verscheen ongewijzigd in `st.error`. Aanbevolen: generieke Nederlandse
microcopy met correlation-ID; technische details alleen gesaniteerd server-side.

### PILOT-010 — P2 — renders boven vijf seconden omzeilen regressiecontrole

`src/main.py:120-150,189-276` classificeert uitsluitend op tijd. Iedere render
boven vijf seconden is automatisch "heavy" en doorloopt daardoor geen
`check_regression`. De bypass is bewezen; een productiestoring door dit pad is
niet live waargenomen. Aanbevolen: operationtype/spans plus een onafhankelijke
absolute UI-watchdog.

### PILOT-011 — P2 — SQLite-lifecycle sluit resources niet deterministisch

`src/database/db_connection.py:23-49` heeft geen expliciet close-/shutdownpad.
De groene pilotrun rapporteerde ongeclosed SQLiteconnections. Aanbevolen:
`close()` en container/repository-teardown; test resourcewarnings als fouten.

### PILOT-012 — P3 — smoke-suite geeft zwakker bewijs dan zij claimt

`tests/smoke/test_critical_paths.py:1-7,53-63,136-170` claimt tien tests maar
verzamelt er negen; de validatietest heeft geen assertion en de exporttest
exporteert niets. Aanbevolen: concrete functionele smokecriteria, assertion op
regelset/IDs en hermetische fixtures.

### PILOT-013 — P3 — bewezen ongebruikte migratieresten

`src/services/service_factory.py:32-108,714-764` en
`src/ui/components/definition_generator_tab.py:719-723` bevatten onder meer
`_freeze_config` en `_clear_results` zonder productiecaller. Aanbevolen:
verwijder shims pas in een aparte gecontroleerde migratie en consolideer het
publieke servicecontract.

### PILOT-014 — P1 — providerreset retourneert stale procescache

`src/services/service_factory.py:32-33,767-790` cachet de adapter onder de
constante key `singleton`. De provider-sidebar reset andere caches maar niet
`_SERVICE_ADAPTER_CACHE` en bewaart keys procesglobaal in `os.environ`.
Na wissel van factorytarget `old` naar `new` was `same_adapter=True` en bleef
`returned_container=old`. Aanbevolen: verwijder de redundante adaptercache of
invalideer atomair met configversie; houd secrets/clients session-scoped.

### PILOT-015 — P3 — readinessfeedback spreekt zichzelf tegen

`src/ui/components/definition_generator_tab.py:76-84` waarschuwt bij ontbrekende
context maar blokkeert de CTA niet. AppTest gaf daarna tegelijk de context-
waarschuwing en een fout over ontbrekende ontologische categorie. Aanbevolen:
één readinessmodel, disabled CTA en een complete lijst van ontbrekende eisen.

### PILOT-016 — P3 — headinghiërarchie is niet consistent

`src/ui/components/definition_generator_tab.py:94,264,292,308,311` springt van
h3 naar h4 en daarna terug naar h3/subheader. Aanbevolen: één semantische
headingladder die de visuele structuur volgt.

## Afgewezen vermoedens

- Single-thread transactieatomiciteit is niet defect: alle twaalf toegewezen
  atomiciteitstests slagen; het probleem is cross-thread ownership.
- De debuglog van voorbeelden logt alleen presence, keys en aantallen, niet de
  voorbeeldinhoud.
- Promptdebug gebruikt geen unsafe HTML; XSS is niet bewezen. De bewezen
  bevinding betreft gegevensblootstelling.
- Statusfeedback gebruikt tekst en iconen en is dus niet uitsluitend kleur.

## Niet getest

- Echte AI-generatie, web lookup/RAG of externe providerresponse: geen echte
  credentials, kosten of netwerkcalls toegestaan.
- Twee echte gelijktijdige Streamlit-browsersessies; de DB-race is wel met twee
  threads gereproduceerd.
- Een volledige edit/review/export-E2E op een productie-record; reviewcallers
  zijn met mocks gecontroleerd.
- Visueel contrast, focusvolgorde, keyboard-only, screenreader/VoiceOver,
  touch targets, 200% zoom en viewports 320–1440 px. Er was geen bruikbare
  browserbackend/Playwright-installatie. De vaste twee-/driekolomslayouts zijn
  daarom slechts een responsive vermoeden en niet als bewezen finding gemeld.
