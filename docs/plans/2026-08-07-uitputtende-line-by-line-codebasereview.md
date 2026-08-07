# Exhaustieve line-by-line codebasereview Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use **executing-plans** to execute this plan task-by-task. Use **requesting-code-review**, **executing-tests**, **accessibility-review**, **code-quality**, **dependency-auditor**, **webapp-testing**, and **verification-before-completion** at the indicated checkpoints.

**Goal:** Voer een aantoonbaar volledige, read-only line-by-line review uit van ieder bestand en iedere functie in de vastgezette repositorysnapshot, inclusief tests, scripts, configuratie, documentatie en binaire artefacten, met een sluitende dekkingsmatrix en onafhankelijk geverifieerde bevindingen.

**Architecture:** De review wordt uitgevoerd tegen één immutable `REVIEW_BASE_SHA`. Een automatisch gegenereerde bestands- en symboleninventaris vormt de single source of truth. Kleine, exclusief toegewezen reviewbatches krijgen een eerste beoordeling, een onafhankelijke tweede beoordeling en een automatische sluitingscontrole; applicatiecode wordt tijdens de review niet gewijzigd.

**Tech Stack:** Git, Python 3.13 AST/tokenize, Ruff, Black, mypy, pytest/pytest-cov, Bandit, pip-audit, SQLite, Streamlit, FastAPI en browsergebaseerde UI-tests.

---

## 1. Scope en harde randvoorwaarden

### 1.1 Huidige omvang als planningsbaseline

De aantallen worden bij uitvoering opnieuw tegen `REVIEW_BASE_SHA` vastgesteld:

| Categorie | Huidige telling |
|---|---:|
| Alle tracked bestanden | 1.884 |
| Pythonbestanden totaal | 870 |
| Python in `src/` | 372 bestanden, 96.308 regels, 2.836 functies/methoden |
| Python in `tests/` | 354 bestanden, 83.960 regels, 4.408 functies/methoden |
| Python in `scripts/` | 138 bestanden, 36.698 regels, 823 functies/methoden |
| Markdown | 756 bestanden, 294.633 regels |
| JSON | 81 bestanden, 130.442 regels |
| Shell | 55 bestanden, 6.442 regels |
| YAML/YML | 49 bestanden, 6.790 regels |
| SQL | 15 bestanden, 1.426 regels |

De term “ieder bestand” betekent:

1. elk pad uit `git ls-files` op de vastgezette SHA;
2. alle relevante untracked bron-, configuratie- en instructiebestanden, afzonderlijk gelabeld als user-owned;
3. executable code, tests, scripts, migraties, configuratie, prompts en documentatie line-by-line;
4. binaire bestanden via type-, metadata-, herkomst-, gebruiks- en visuele inspectie;
5. secrets zoals `.env` worden nooit inhoudelijk uitgelezen; aanwezigheid en veilige omgang worden wel beoordeeld.

### 1.2 Niet onderhandelbare regels

- Wijzig tijdens de review geen bestanden onder `src/`, `tests/`, `scripts/`, `config/`, `prompts/` of andere bestaande applicatiepaden.
- Leg alleen nieuwe reviewartefacten vast onder `docs/reviews/2026-08-07-line-by-line/`.
- Fix geen bevindingen in dezelfde branch of reviewrun.
- Beoordeel elke regel tegen exact dezelfde SHA; bij SHA-drift stopt de batch.
- Geen bestand krijgt status `reviewed` zolang één symbool, regelbereik of checklistonderdeel openstaat.
- De eerste en tweede beoordeling van een batch worden niet door dezelfde reviewer uitgevoerd.
- Rapporteer feiten als `proven`, risico’s als `suspected` en blokkades als `not_tested`.
- Verwijder niets en voer muterende gebruikersflows uitsluitend uit op een tijdelijke databasekopie.

### 1.3 Definitie van “volledig beoordeeld”

Een bestand is pas volledig beoordeeld wanneer:

- de blob-SHA overeenkomt met de scope-inventaris;
- mode, objecttype, object-ID, grootte en inhoud overeenkomen met de base-tree;
- `line-coverage.csv` de fysieke regels 1..N exact partitioneert zonder gaten,
  overlap of ranges buiten het bestand; binaries krijgen één equivalente reviewrij;
- elke module, class, functie, async functie, methode, property en geneste functie in de symboleninventaris staat;
- imports, publieke contracten, callers en callees zijn gevolgd;
- correctness, randgevallen, foutafhandeling, security, privacy, logging, resources, concurrency, performance, typen en onderhoudbaarheid zijn beoordeeld;
- toepasselijke tests zijn gelezen en aan het symbool gekoppeld, of een testgap is geregistreerd;
- bevindingen bewijs, prioriteit, locatie, reproductie en oplossing bevatten;
- een tweede reviewer de dekking en conclusies heeft bevestigd;
- de coverage-validator voor het bestand geen open rijen rapporteert.

Een testbestand is pas volledig beoordeeld wanneer daarnaast alle assertions, fixtures, mocks, markers, skips, xfails, exception handlers en timeouts op betekenis en actualiteit zijn gecontroleerd.

## 2. Reviewartefacten

Alle uitvoering produceert uitsluitend nieuwe bestanden in:

```text
docs/reviews/2026-08-07-line-by-line/
├── README.md
├── scope/
│   ├── snapshot.md
│   ├── file-inventory.csv
│   ├── symbol-inventory.csv
│   ├── line-coverage.csv
│   ├── batch-membership.csv
│   ├── batch-index.csv
│   ├── review-infrastructure.csv
│   ├── tooling-snapshot.md
│   ├── untracked-inventory.csv
│   └── exclusions.csv
├── tools/
│   ├── build_inventory.py
│   ├── validate_inventory.py
│   └── test_inventory_tools.py
├── baseline/
│   ├── commands.md
│   ├── test-results.md
│   ├── static-analysis.md
│   └── environment.md
├── batches/
│   ├── BATCH-001.md
│   └── ...
├── findings/
│   ├── findings.csv
│   ├── findings.md
│   └── false-positives.md
├── traceability/
│   ├── production-to-tests.csv
│   ├── entrypoint-dataflows.md
│   └── architecture-boundaries.md
├── functional/
│   ├── api-results.md
│   ├── ui-flow-results.md
│   └── accessibility-responsive.md
├── handovers/
└── final-report.md
```

### Verplichte CSV-schema’s

`file-inventory.csv` (`path_b64` is de lossless representatie; `path` is alleen
de leesbare UTF-8-weergave):

```csv
path,path_b64,git_mode,object_type,object_id,file_type,bytes,physical_lines,logical_lines,scope_tier,status,reviewer,verified_by,reviewed_at,finding_ids,notes
```

`symbol-inventory.csv`:

```csv
symbol_id,path,path_b64,qualified_name,kind,start_line,start_col,end_line,end_col,parent_symbol,decorators,complexity,status,reviewer,verified_by,test_ids,finding_ids,notes
```

`line-coverage.csv`:

```csv
path,path_b64,reviewed_object_id,start_line,end_line,classification,batch,status,reviewer,verified_by,finding_ids,notes
```

`batch-membership.csv`:

```csv
batch,path,path_b64,reviewed_object_id,start_line,end_line,symbol_id,role,reviewer,verified_by
```

`batch-index.csv`:

```csv
batch,status,reviewer,verified_by,manifest_sha256,membership_sha256
```

`review-infrastructure.csv`:

```csv
path,tooling_sha,blob_sha,physical_lines,status,reviewer,verified_by,test_result,notes
```

`untracked-inventory.csv`:

```csv
path,path_b64,source_root,captured_at,content_sha256,file_type,bytes,scope_tier,status,reviewer,verified_by,owner,notes
```

`findings.csv`:

```csv
finding_id,priority,certainty,review_area,title,path,start_line,end_line,evidence,reproduction,recommendation,status,reviewer,verified_by
```

Toegestane statussen zijn: `pending`, `in_review`, `reviewed`, `verified`, `blocked` en `out_of_scope`. `out_of_scope` is alleen toegestaan voor tier-F generated/vendor/binaire inhoud en vereist een concrete reden, approval en twee onafhankelijke reviewers. Bij `--require-final` is `blocked` niet verenigbaar met een 100%-claim. Iedere regel- en batchrij pint `reviewed_object_id` aan het object-ID uit de immutable base-tree.

De applicatiescope gebruikt uitsluitend `REVIEW_BASE_SHA`. Reviewtools die daarna
ontstaan krijgen een afzonderlijke immutable `TOOLING_SHA` en worden via
`review-infrastructure.csv` beoordeeld; zij worden nooit achteraf in de
applicatie-inventaris gemengd. Na de eerste scopefreeze wordt de commit met de
immutable untracked-metadata vastgelegd als `SCOPE_SHA`; de finale validator
vergelijkt de actuele reviewstatus tegen exact die committed set.

## 3. Batchmodel en capaciteit

- Een codebatch bevat maximaal 20 bestanden, 4.000 fysieke regels of 150 symbolen; de laagste grens geldt.
- Een data-/documentatiebatch bevat maximaal 30 bestanden of 6.000 regels.
- Zeer grote bestanden worden op natuurlijke class-/functieranges gesplitst, maar krijgen pas bestandsstatus `reviewed` nadat alle delen klaar zijn.
- Per parallelle golf werken maximaal drie eerste reviewers naast één coördinator. In een volgende golf wisselen reviewers voor de onafhankelijke verificatie.
- Iedere batch krijgt één eigenaar; parallelle reviewers delen geen bestanden.
- Na iedere 10 batches volgt een consolidatie- en consistentiecheckpoint.

Op basis van de huidige omvang moet rekening worden gehouden met circa 180–240 eerste-reviewbatches plus een tweede-reviewpass. Dit is naar verwachting 350–650 revieweruren; dit is een werklastindicatie, geen kalenderbelofte.

## 4. Uitvoeringsplan

### Task 1: Maak een geïsoleerde reviewworktree en zet de scope vast

**Files:**
- Create: `docs/reviews/2026-08-07-line-by-line/scope/snapshot.md`
- Create: `docs/reviews/2026-08-07-line-by-line/baseline/environment.md`

**Step 1:** Gebruik **using-git-worktrees** om een worktree te maken vanaf de expliciet gekozen targetbranch.

**Step 2:** Leg vóór enige artefactwijziging vast:

```bash
git rev-parse HEAD
git status --short
git branch --show-current
git submodule status
```

Expected: één `REVIEW_BASE_SHA`, plus een expliciete lijst van bestaande wijzigingen en submodules.

**Step 3:** Registreer Python-, OS- en toolversies:

```bash
python3 --version
python3 -m pip --version
python3 -m pytest --version
python3 -m ruff --version
python3 -m mypy --version
```

**Step 4:** Schrijf SHA, branch, status, toolversies en timestamp naar `snapshot.md` en `environment.md`.

**Step 5:** Commit alleen deze reviewartefacten:

```bash
git add docs/reviews/2026-08-07-line-by-line/
git commit -m "docs(DEF-XX): start exhaustive codebase review"
```

### Task 2: Bouw eerst falende tests voor de inventarisatie

**Files:**
- Create: `docs/reviews/2026-08-07-line-by-line/tools/test_inventory_tools.py`
- Create: `docs/reviews/2026-08-07-line-by-line/tools/build_inventory.py`
- Create: `docs/reviews/2026-08-07-line-by-line/tools/validate_inventory.py`

**Step 1:** Schrijf tests die eisen dat:

- `REVIEW_BASE_SHA` een volledige commit-SHA is en de scope uitsluitend uit
  `git ls-tree -rz --full-tree REVIEW_BASE_SHA` komt;
- ieder raw Git-pad exact één file-row krijgt, ook bij spaties, komma’s, quotes,
  tabs, newlines, leading dashes, NFC/NFD- en case-only namen;
- duplicate blobs op verschillende paden afzonderlijke rijen blijven;
- object-ID, Git-mode, objecttype, bytes en regeldefinitie vanuit Git-objecten
  worden berekend en werkboomdrift de base-inventaris niet verandert;
- line- en batchrijen het daadwerkelijk beoordeelde base-object via
  `reviewed_object_id` pinnen en een gewijzigde checkout niet als bewijsbron kan
  gelden;
- Python parsing `tokenize.detect_encoding` gebruikt en AST alle classes,
  sync/async functies, methods, nested definities, decorated ranges,
  property getter/setter/deleter, overloads/herdefinities en lambda’s opneemt;
- syntaxfouten als blocking finding worden geregistreerd;
- binaire bestanden geen line-by-line claim krijgen maar een binary-reviewstatus;
- line coverage voor tekstbestanden exact 1..N partitioneert en binaries één
  equivalente reviewrij hebben;
- batchmembership geen gat/overlap heeft en de batchlimieten afdwingt;
- duplicate, ontbrekende, onbekende of inhoudelijk verschoven rijen falen;
- `verified` onmogelijk is zonder verschillende `reviewer` en `verified_by`.
- findings geldige enums, foreign keys, ranges en bidirectionele referenties hebben;
- untracked alleen via `git ls-files --others --exclude-standard -z` wordt
  geïnventariseerd, met expliciete bronwerkboom, capturetijd en contenthash, en
  ignored/secrets nooit inhoudelijk worden gescand.

**Step 2:** Run de tests vóór implementatie:

```bash
pytest docs/reviews/2026-08-07-line-by-line/tools/test_inventory_tools.py -q
```

Expected: FAIL omdat de inventoryfuncties nog ontbreken.

**Step 3:** Implementeer `build_inventory.py` uitsluitend met de Python-
standaardbibliotheek. Verwerk Git-output NUL-delimited, lees blobs via
`git cat-file`, representeer raw paden lossless en geef syntax-/encodingfouten
als blocking inventoryrecords terug.

**Step 4:** Implementeer `validate_inventory.py` met exitcode 1 voor:

- ontbrekende tracked bestanden;
- drift in pad, mode, objecttype, object-ID, grootte of regels;
- uncovered Python-symbolen;
- ontbrekende/overlappende line-ranges en batchmembership;
- `pending`/`in_review`-rijen bij finalisatie;
- `blocked`-rijen bij een 100%-finalisatie;
- ontbrekende tweede reviewer;
- findings zonder verplichte velden.

**Step 5:** Run de tests opnieuw.

Expected: PASS.

**Step 6:** Laat een andere reviewer de drie reviewtoolbestanden line-by-line
controleren vóór de commit. Registreer de review later afzonderlijk in
`review-infrastructure.csv`; meng de tools niet in de applicatie-inventaris.

**Step 7:** Commit:

```bash
git add docs/reviews/2026-08-07-line-by-line/tools/
git commit -m "test(DEF-XX): add review inventory gates"
```

De resulterende commit wordt in Task 3 immutable vastgelegd als `TOOLING_SHA`.

### Task 3: Genereer en verifieer de volledige scope-inventaris

**Files:**
- Create: `docs/reviews/2026-08-07-line-by-line/scope/file-inventory.csv`
- Create: `docs/reviews/2026-08-07-line-by-line/scope/symbol-inventory.csv`
- Create: `docs/reviews/2026-08-07-line-by-line/scope/line-coverage.csv`
- Create: `docs/reviews/2026-08-07-line-by-line/scope/batch-membership.csv`
- Create: `docs/reviews/2026-08-07-line-by-line/scope/batch-index.csv`
- Create: `docs/reviews/2026-08-07-line-by-line/scope/review-infrastructure.csv`
- Create: `docs/reviews/2026-08-07-line-by-line/scope/tooling-snapshot.md`
- Create: `docs/reviews/2026-08-07-line-by-line/scope/untracked-inventory.csv`
- Create: `docs/reviews/2026-08-07-line-by-line/scope/exclusions.csv`

**Step 1:** Verifieer `REVIEW_BASE_SHA^{commit}` en genereer de inventaris
rechtstreeks uit de immutable base-tree, niet uit index of worktree:

```bash
python3 docs/reviews/2026-08-07-line-by-line/tools/build_inventory.py \
  --base-sha "$REVIEW_BASE_SHA" \
  --output-dir docs/reviews/2026-08-07-line-by-line/scope \
  --untracked-root /Users/chrislehnen/Projecten/Definitie-app
```

**Step 2:** Vergelijk aantallen met onafhankelijke base-treecommando’s:

```bash
git ls-tree -r --name-only "$REVIEW_BASE_SHA" | wc -l
git ls-tree -r --name-only "$REVIEW_BASE_SHA" | rg '\.py$' | wc -l
```

Expected: de CSV-aantallen sluiten exact aan.

**Step 3:** Classificeer ieder bestand in één van deze scope tiers:

- A: executable productiecode;
- B: tests en testfixtures;
- C: build-, deployment-, migratie- en operationele scripts;
- D: runtimeconfiguratie, prompts en toetsregeldata;
- E: documentatie en historische beslisartefacten;
- F: binaire/generated/vendor-artefacten.

**Step 4:** Registreer iedere uitzondering expliciet. Alleen technisch onleesbare generated/vendor-inhoud mag worden uitgezonderd; het bestand zelf blijft in de matrix.

**Step 5:** Leg de aparte `TOOLING_SHA` vast, genereer de review-
infrastructuurinventaris en bewijs dat application- en tooling-scope niet mengen.

**Step 6:** Run de non-final validator tegen dezelfde expliciete bronwerkboom:

```bash
python3 docs/reviews/2026-08-07-line-by-line/tools/validate_inventory.py \
  --base-sha "$REVIEW_BASE_SHA" \
  --review-dir docs/reviews/2026-08-07-line-by-line \
  --untracked-root /Users/chrislehnen/Projecten/Definitie-app
```

Expected: PASS voor scopevolledigheid; reviewstatus mag nog `pending` zijn.

**Step 7:** Commit uitsluitend de scopefreeze en leg de volledige resulterende
commit-SHA vast als `SCOPE_SHA`. De finale validator gebruikt deze commit als
trust anchor voor de exacte untracked set en immutable metadata.

### Task 4: Leg de baseline vast

**Files:**
- Create: `docs/reviews/2026-08-07-line-by-line/baseline/commands.md`
- Create: `docs/reviews/2026-08-07-line-by-line/baseline/test-results.md`
- Create: `docs/reviews/2026-08-07-line-by-line/baseline/static-analysis.md`

**Step 1:** Draai en registreer exitcode, duur, samenvatting en volledige loglocatie van:

```bash
make lint
make complexity-check
make mypy-check
make overrides-check
make pins-check
make test-markers-check
make test-cov-ci
make test-smoke
make test-acceptance
make audit
python3 -m bandit -r src -ll -f json
python3 -m pip check
```

**Step 2:** Draai de integration-suite per bestand, niet als één hangende run:

```bash
for file in $(git ls-files 'tests/integration/test_*.py' 'tests/integration/**/test_*.py'); do
  pytest "$file" -q --timeout=120
done
```

Expected: ieder bestand krijgt `pass`, `fail`, `timeout`, `skip` of `blocked`; geen ontbrekende resultaten.

**Step 3:** Registreer alle warnings afzonderlijk, ook wanneer de command exitcode 0 is.

**Step 4:** Classificeer scanneruitvoer pas na handmatige broninspectie als finding of false positive.

### Task 5: Maak batchmanifesten zonder gaten of overlap

**Files:**
- Create: `docs/reviews/2026-08-07-line-by-line/batches/BATCH-001.md`
- Create: volgende `BATCH-NNN.md`-bestanden op basis van de inventaris

**Step 1:** Deel tiers A–F deterministisch in op padvolgorde en batchlimieten.

**Step 2:** Geef ieder bestand en ieder Python-symbool precies één primaire batch.

**Step 2a:** Genereer `batch-membership.csv`; grote bestanden mogen meerdere
range-rijen hebben, maar iedere regel en ieder symbool heeft exact één primaire
eigenaar.

**Step 2b:** Genereer `batch-index.csv`. Pin per batch de SHA-256 van het
manifest en de canonieke, volgorde-onafhankelijke SHA-256 van alle membership-
rijen. De batchindex bevat status, eerste reviewer en onafhankelijke verifier;
een leeg of inhoudelijk afwijkend manifest faalt.

**Step 3:** Gebruik deze reviewvolgorde:

1. entrypoints, build, dependencies en configuratie;
2. security en FastAPI;
3. domain, models, ontologie en classificatie;
4. database, repositories, schema en migraties;
5. AI-clients, interfaces, container en modelrouter;
6. prompts, orchestrators en generatieflow;
7. validatie, toetsregels, opschoning en sanitization;
8. web lookup, document processing en RAG;
9. workflow, import/export, cache en voorbeelden;
10. Streamlit state, helpers, renderers en handlers;
11. generatie-, edit-, expert- en beheer-UI;
12. monitoring, utils, CLI, tools en integrations;
13. unit-tests gekoppeld aan bovenstaande productieonderdelen;
14. integration-, contract-, smoke-, performance-, manual- en archived-tests;
15. operationele scripts en shellcode;
16. JSON/YAML/SQL/prompts en overige runtime-data;
17. documentatie, plannen en handovers;
18. binaire en overige artefacten.

**Step 4:** Laat de validator bewijzen dat alle line-ranges en symbolen exact één
primaire batch hebben, zonder gaten/overlap en binnen de code-/databatchlimieten.

### Task 6: Voer de pilotbatch uit en kalibreer het protocol

**Files:**
- Modify: `docs/reviews/2026-08-07-line-by-line/batches/BATCH-001.md`
- Modify: inventory- en finding-CSV’s

**Step 1:** Selecteer een representatieve pilot met één entrypoint, één service, één databasebestand, één UI-component en hun tests.

**Step 2:** Lees ieder bestand volledig met regelnummers, rechtstreeks uit het
`reviewed_object_id` van de immutable base-tree en nooit impliciet uit de
checkout:

```bash
git cat-file blob <reviewed_object_id> | nl -ba | sed -n '<start>,<einde>p'
```

**Step 3:** Controleer per symbool callers en referenties:

```bash
rg -n "<symboolnaam>" src tests scripts
```

**Step 4:** Vul voor ieder bestand de volledige checklist uit §1.3 in.

**Step 5:** Run uitsluitend relevante tests en registreer exacte commando’s en resultaten.

**Step 6:** Laat een andere reviewer dezelfde batch onafhankelijk controleren.

**Step 7:** Run `validate_inventory.py` voor alleen BATCH-001.

Expected: nul pending symbolen, nul SHA-drift en twee verschillende reviewers.

**Step 8:** Pas alleen het reviewprotocol aan als de pilot een aantoonbaar dekkingsgat toont; vergroot de scope nooit stilzwijgend.

### Task 7: Review alle productiecodebatches

**Files:**
- Modify: toegewezen `BATCH-NNN.md`
- Modify: `file-inventory.csv`, `symbol-inventory.csv`, `findings.csv`

Herhaal voor iedere tier-A/C-productiebatch:

**Step 1:** Claim de batch met reviewer, starttijd en verwachte bestanden.

**Step 2:** Verifieer blob-SHA’s vóór het lezen.

**Step 3:** Lees ieder fysiek regelbereik en ieder symbool volledig.

**Step 4:** Traceer inputs vanaf entrypoints naar database, logs, prompts en externe services, plus outputs terug naar API/UI.

**Step 5:** Controleer alle exceptionpaden, retries, timeouts, cleanup en fallbackgedrag.

**Step 6:** Controleer trust boundaries, inputvalidatie, secrets, PII en serialisatie.

**Step 7:** Koppel bestaande tests; registreer ontbrekende of ineffectieve tests als findings zonder tests toe te voegen.

**Step 8:** Reproduceer iedere mogelijke finding met een read-only test, minimale aanroep of bestaande test waar veilig.

**Step 9:** Vul prioriteit, zekerheid, bewijs, locatie, reproductie en oplossing in.

**Step 10:** Laat een andere reviewer alle rijen en minimaal iedere P0/P1-codepath opnieuw lezen.

**Step 11:** Valideer de batch en commit alleen reviewartefacten.

### Task 8: Review alle testbestanden line-by-line

**Files:**
- Modify: batches voor `tests/**`
- Modify: `traceability/production-to-tests.csv`

Herhaal per testbatch:

**Step 1:** Lees iedere fixture, mock, patch, assertion, skip, xfail en exception handler.

**Step 2:** Controleer of de test het actuele productiecontract aanroept.

**Step 3:** Controleer dat een assertion werkelijk kan falen en niet wordt ingeslikt.

**Step 4:** Controleer isolatie, tijdelijke bestanden/databases, resourcecleanup en netwerkafhankelijkheid.

**Step 5:** Koppel test-ID’s aan productie-symbolen in `production-to-tests.csv`.

**Step 6:** Registreer per productie-symbool `direct`, `indirect`, `none` of `not_applicable` testdekking.

**Step 7:** Run het testbestand afzonderlijk en registreer het resultaat.

**Step 8:** Laat een tweede reviewer de assertionkwaliteit en mapping verifiëren.

### Task 9: Review configuratie, regels, prompts, migraties en documentatie

**Files:**
- Modify: tier-D/E-batches en findings

**Step 1:** Lees JSON/YAML/TOML/INI/requirements en toetsregelbestanden regel voor regel.

**Step 2:** Controleer schema, duplicaten, dead keys, defaults, secretverwijzingen en consumptie door code.

**Step 3:** Controleer iedere SQL-migratie voor forward/rollback-symmetrie, locks, idempotentie, constraints en dataverlies.

**Step 4:** Review prompts op variabele-escaping, promptinjectie, PII, outputcontract en versieconsistentie zonder prompt builders te wijzigen.

**Step 5:** Review Markdown op strijdige instructies, verouderde claims, broken lokale links en securitygevoelige inhoud.

**Step 6:** Markeer historische documentatie niet automatisch als irrelevant; leg de status expliciet vast.

**Step 7:** Laat een tweede reviewer alle runtimeconfiguratie, prompts en migraties opnieuw controleren.

### Task 10: Review binaire en generated artefacten

**Files:**
- Modify: tier-F-batches en exclusions

**Step 1:** Bepaal MIME-type, grootte, Git LFS-status, herkomst en referenties.

**Step 2:** Inspecteer PNG/PDF/HTML visueel waar relevant.

**Step 3:** Controleer archives op verwachte inhoud zonder extractie naar de repository.

**Step 4:** Controleer dat databases, exports, caches en secrets niet onbedoeld tracked zijn.

**Step 5:** Registreer waarom line-by-line niet toepasbaar is en welke equivalente inspectie is uitgevoerd.

### Task 11: Voer volledige functionele, API- en UI-verificatie uit

**Files:**
- Create: `functional/api-results.md`
- Create: `functional/ui-flow-results.md`
- Create: `functional/accessibility-responsive.md`

**Step 1:** Start Streamlit en FastAPI vanuit een geïsoleerde kopie met een tijdelijke SQLite-database.

**Step 2:** Test alle niet-muterende flows en vervolgens de muterende flows uitsluitend tegen die tijdelijke database.

**Step 3:** Test iedere FastAPI-route op success, validation error, malformed input, not found, security headers en CORS.

**Step 4:** Test iedere Streamlitpagina, tab, modal, upload, download, empty state, error state en success state.

**Step 5:** Test responsive breedtes 320, 390, 600, 768, 1024 en 1440 px plus 200% zoom.

**Step 6:** Gebruik **accessibility-review** voor contrast, headings, labels, focusvolgorde, toetsenbord, touch targets en screenreadersemantiek.

**Step 7:** Live AI- en externe netwerkflows vereisen vooraf expliciete toestemming voor credentials, kosten en netwerkgebruik. Zonder toestemming krijgen zij status `not_tested`, nooit `passed`.

### Task 12: Voer cross-cutting architectuur- en securitypasses uit

**Files:**
- Create: `traceability/entrypoint-dataflows.md`
- Create: `traceability/architecture-boundaries.md`

**Step 1:** Traceer iedere entrypoint naar services, dataopslag, logs, prompts en externe verbindingen.

**Step 2:** Controleer importgrenzen: services mogen niet van Streamlit/UI afhangen; UI mag businesslogica niet dupliceren.

**Step 3:** Controleer lifecycle van alle SQLite-connecties, HTTP-sessies, files en async tasks.

**Step 4:** Controleer alle loggingcalls op secrets en persoonsgegevens.

**Step 5:** Controleer iedere externe parser en deserialisatiegrens voor onbetrouwbare input.

**Step 6:** Controleer dependencygebruik en bereikbaarheid van alle auditbevindingen.

**Step 7:** Herleid iedere cross-cutting finding tot concrete bestand-/symbolenrijen.

### Task 13: Consolideer en dedupliceer findings

**Files:**
- Modify: `findings/findings.csv`
- Create: `findings/findings.md`
- Create: `findings/false-positives.md`

**Step 1:** Merge duplicaten op root cause, niet alleen op dezelfde regel.

**Step 2:** Gebruik prioriteiten:

- P0: actieve compromise, onherstelbaar dataverlies of volledige uitval;
- P1: direct exploiteerbaar/ernstig privacy-, integriteits- of kernfunctionaliteitsprobleem;
- P2: reproduceerbare functionele, onderhoudbaarheids- of toegankelijkheidsafwijking;
- P3: lage impact, lokale schuld of toekomstige compatibiliteitsrisico’s.

**Step 3:** Eis voor `proven`: concrete runtime-uitkomst, falende test of logisch sluitend codepad.

**Step 4:** Label niet-uitgevoerde exploits, externe services en ontbrekende credentials expliciet.

**Step 5:** Laat alle P0/P1’s en een steekproef van minimaal 20% van P2/P3’s onafhankelijk reproduceren.

### Task 14: Bewijs dat de reviewdekking 100% is

**Files:**
- Create: `docs/reviews/2026-08-07-line-by-line/coverage-validation.md`

**Step 1:** Run de finale validator:

```bash
python3 docs/reviews/2026-08-07-line-by-line/tools/validate_inventory.py \
  --base-sha "$REVIEW_BASE_SHA" \
  --review-dir docs/reviews/2026-08-07-line-by-line \
  --untracked-root /Users/chrislehnen/Projecten/Definitie-app \
  --scope-sha "$SCOPE_SHA" \
  --require-final
```

Expected:

```text
Tracked files missing: 0
Files pending: 0
Python symbols missing: 0
Symbols pending: 0
Line ranges missing/overlapping: 0
Batch memberships invalid: 0
SHA drift: 0
Tooling SHA drift: 0
Unverified batches: 0
Invalid findings: 0
```

**Step 2:** Vergelijk opnieuw `git ls-files` met de file-inventaris.

**Step 3:** Controleer dat elke batch twee verschillende reviewers heeft.

**Step 4:** Controleer dat ieder productie-symbool een testmapping of gemotiveerde `not_applicable` heeft.

**Step 5:** Run alle baselinecommando’s opnieuw en leg delta’s vast.

**Step 6:** Gebruik **verification-before-completion**. Zonder volledig groene coverage-validator mag de review niet “volledig” worden genoemd.

### Task 15: Lever het eindrapport en een herstelbacklog op

**Files:**
- Create: `docs/reviews/2026-08-07-line-by-line/final-report.md`
- Create: `docs/reviews/2026-08-07-line-by-line/remediation-backlog.md`

**Step 1:** Rapporteer scope, SHA, methode, dekkingsbewijs en testresultaten.

**Step 2:** Presenteer findings per reviewgebied en prioriteit met bewijs, locatie, reproductie en oplossing.

**Step 3:** Scheid `proven`, `suspected` en `not_tested` in afzonderlijke secties.

**Step 4:** Maak een herstelbacklog met afhankelijkheden en aanbevolen volgorde, maar voer geen fixes uit.

**Step 5:** Neem resterende onzekerheden en expliciete exclusions op.

**Step 6:** Laat een reviewer die geen batches heeft gecoördineerd het eindrapport tegen de CSV’s en validatoruitvoer controleren.

**Step 7:** Commit de finale reviewartefacten:

```bash
git add docs/reviews/2026-08-07-line-by-line/
git commit -m "docs(DEF-XX): complete exhaustive codebase review"
```

## 5. Checkpoints en stopcriteria

Stop en rapporteer wanneer:

- `REVIEW_BASE_SHA` niet meer beschikbaar is of bestanden tijdens een batch veranderen;
- een bestand niet veilig kan worden gelezen zonder secrets te tonen;
- live tests credentials, kosten, destructive acties of externe toestemming vereisen;
- dezelfde technische blokkade drie opeenvolgende reviewturns verhindert;
- de inventarisvalidator een niet-oplosbare inconsistentie vindt.

Menselijke checkpoints zijn verplicht na:

1. scopefreeze en exclusions;
2. pilotbatch;
3. iedere 10 batches;
4. alle P0/P1-bevindingen;
5. functionele/live-testgrenzen;
6. finale 100%-coveragevalidatie.

## 6. Definition of Done

- [ ] Alle tracked bestanden staan exact eenmaal in de file-inventaris.
- [ ] Mode, objecttype, object-ID en raw pad zijn voor ieder base-object bewezen.
- [ ] Alle fysieke tekstregels zijn zonder gat/overlap `verified`; binaries hebben equivalente inspectie.
- [ ] Alle Pythonfuncties/methoden/classes/lambda’s staan in de symboleninventaris.
- [ ] Alle file- en symbolenrijen zijn `verified` of onafhankelijk gemotiveerd `out_of_scope`.
- [ ] `blocked` komt niet voor in een geslaagde 100%-finalisatie.
- [ ] Iedere batch heeft twee verschillende reviewers.
- [ ] Reviewtools zijn afzonderlijk vastgezet en geverifieerd tegen `TOOLING_SHA`.
- [ ] Alle baseline-, marker- en per-file integration-tests hebben een resultaat.
- [ ] Alle productie-symbolen hebben een testmapping of gemotiveerde uitzondering.
- [ ] Alle findings bevatten prioriteit, zekerheid, bewijs, locatie, reproductie en oplossing.
- [ ] UI, API, accessibility en responsive flows zijn aantoonbaar getest of als `not_tested` benoemd.
- [ ] Finale SHA-controle toont nul drift.
- [ ] `validate_inventory.py --require-final` eindigt met exitcode 0.
- [ ] Er zijn geen applicatiebestanden gewijzigd.

## 7. Uitvoeringshandoff

Aanbevolen uitvoering: **Parallel Session** met **executing-plans**, batches van maximaal tien en een menselijk checkpoint na iedere batchgroep. Voor onafhankelijke beoordeling worden reviewers per golf gerouleerd; maximaal vier gelijktijdige agents inclusief coördinator.

Alternatief: **Subagent-Driven in deze sessie**, met een verse reviewer per batch en een aparte verificatiereviewer. Door de omvang zal dit over veel automatische vervolgturns en handovers lopen.

Start uitvoering pas nadat de gebruiker de scopefreeze, artefactstructuur, inzet van subagents en eventuele live AI-/netwerktests expliciet heeft goedgekeurd.
