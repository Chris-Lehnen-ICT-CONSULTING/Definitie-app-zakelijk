# DEF-664 — Schemacontract, fail-closed init en migratiegrenzen

Status: geleverd op branch `bugfix/DEF-664-fail-closed-migraties` (baseline `cbb24257`, 5 september 2026).
Bron van waarheid voor het schema: `src/database/schema.sql`. Contract en grenzen: `src/database/schema_contract.py`.

## 1. Wat er mis was

Gemeten op tijdelijke databases (bewijs in `/private/tmp/def664-evidence-20260905/`):

- `DatabaseConnection.init_database` telde alleen de tabellen `definities` en `synonym_groups`. Een database met één minimale `definities`-tabel werd geaccepteerd; een botsend object liet `executescript` halverwege falen met alleen een warning, waarna drie tabellen en negen indexen achterbleven en de app gewoon startte.
- Een verse database kreeg de schema.sql-vorm van vóór v6/v7: geen `bron_type`/`metadata` op `rag_chunks` terwijl de embedding-store die schrijft, geen `file_path`, nog wel de v7-tellers, en een lege `schema_version`.
- v5 eiste vijf historische tabellen die geen code aanmaakt en faalde daardoor op elke verse database, ná het committen van versie 1. v6 en v7 committen vóór hun verificatie en maakten geen backup. v7 meldde succes zonder `rag_collections`.
- De legacy-route `migrate_database.py` voegde elke run zelf de verouderde kolommen toe en herbouwde daarna beide tabellen, liep bij ADD COLUMN/backfill/index/normalisatie door met een warning, en eindigde met exit 0 bij een incomplete verificatie.

## 2. Canoniek contract en versieprofielen

`schema.sql` is de declaratieve **versie 3**: v5 (RAG/ontologie/projects + `file_path`), v6 (`bron_type`, `metadata`, drie filterindexen) en v7 (tellers weg) zijn erin verwerkt en het bestand zaait zelf de drie `schema_version`-rijen. Er is bewust géén tweede bron (overlays) meer: een verse en een gemigreerde database dragen dezelfde structuur en dezelfde versiegeschiedenis. De voorbeelddata (twee definities, vier tags) blijft zoals het bestaande contract.

`schema_contract.read_contract` leest de **structuur** van een database en `contract_problems` vergelijkt die met het in-memory uit `schema.sql` opgebouwde contract:

| Objectsoort | Vergeleken op |
|---|---|
| tabel / kolom | aanwezigheid, kolomaffiniteit (SQLite-regels), `NOT NULL`, `DEFAULT` (genormaliseerd), primary-key-positie |
| CHECK-constraint | genormaliseerde expressie per tabel (canoniek ⊆ waargenomen) |
| UNIQUE-constraint | kolomtupel mét collatie |
| index | tabel, uniek, partieel, kolommen met sortering en collatie, én de genormaliseerde DDL (predicaat/expressie) |
| trigger | tabel + genormaliseerde DDL |
| view | genormaliseerde DDL |
| foreign key | kolomgroep (ook composite), doeltabel, `ON UPDATE`, `ON DELETE` |

De normalisatie raakt uitsluitend tekst **buiten** quotes: commentaar, witruimte, hoofdletters en `IF NOT EXISTS`. Commentaar is daarbij een tokenscheiding zoals in SQLite zelf (`ON/**/CONFLICT` is `on conflict`, Codex-review 4). Kolomnamen worden op hun echte eerste identifier-token herkend (kaal, `"…"`, `` `…` ``, `[…]` of `'…'` in identifierpositie) en vergeleken met de SQLite-identifiersemantiek: uitsluitend ASCII-hoofdletters zijn gelijk (`fold_identifier`, één gedeelde fold voor identifiers, keywords en typen; nooit voor string-literals). `"ID"` en `id` zijn dezelfde kolom, maar `"Éxtra"` en `"éxtra"` of `ketenpartners` en `"Ketenpartners"` (het Kelvinteken U+212A gevolgd door `etenpartners`; dat teken is visueel niet van een `K` te onderscheiden, terwijl de ASCII-`K` U+004B juist wél gelijk is aan `k`) zijn verschillende kolommen en worden nooit samengevoegd (Codex-review 5, rootprobe 13); een botsende fold laat contract en rebuild fail-closed stoppen. Herkenning loopt via één gedeelde `column_definition` voor contract én rebuild; een niet-herkende declaratie telt in de rebuild als onveilig. Ook de CHECK-detectie is quote-bewust: een `check(...)`-tekst in een DEFAULT-literal of commentaar telt niet als constraint (rootprobe `probe-check-literal`). Literals en gequote identifiers blijven letterlijk, zodat `'STATUS_CHANGED'` ≠ `'status_changed'` en een omgekeerd indexpredicaat als drift telt (rootprobe `probe-manifest-semantics.py`: alle drie sabotages worden geweigerd). Niet vergeleken: de letterlijke tabel-DDL, kolomvolgorde en rijaantallen. De DEF-672-rebuild (`DEFINITIES_TABLE_SQL`) schrijft `definities` met een andere tekst en volgorde maar dezelfde kolommen, defaults, `NOT NULL`, CHECK-lijsten en FK's en passeert daardoor aantoonbaar (`test_door_de_legacy_route_herbouwde_tabel_passeert`). **Extra** gebruikerstabellen, -kolommen en -indexen (bv. `idx_synonyms_text_ci` uit de legacy-route, `definitie_drafts`) zijn toegestaan; **ontbrekende** canonieke objecten (`schema_incomplete`) of objecten met de juiste naam maar een verkeerde definitie (`schema_drift`) niet.

Versieprofielen (testbaar via `tests/fixtures/schema_profiles.py`):

| Profiel | Vorm | Startup | Migratie-input voor |
|---|---|---|---|
| pre-v5 (`None`) | kerntabellen, geen `schema_version` | geweigerd: `schema_version_outdated` | v5 |
| 1 | + v5-tabellen, `file_path`, tellers aanwezig | geweigerd: `schema_version_outdated` | v6 |
| 2 | + `bron_type`/`metadata` + filterindexen | geweigerd: `schema_version_outdated` | v7 |
| 3 | canoniek | toegelaten na contractcheck | — |
| > 3 | onbekend | geweigerd: `schema_version_unsupported` | — |

Een database zonder de kerntabellen (`CORE_TABLE_COLUMNS` uit DEF-663) is geen "oudere versie" maar een onbekend deelschema: `schema_incomplete`, ook zonder versietabel.

## 3. Startup: fail-closed, nooit migrerend

`init_database`:

1. **Geen schemaobjecten** → `schema.sql` in één transactie (`BEGIN` staat in het script; `executescript` zou een vooraf geopende transactie impliciet committen), contract + versie geverifieerd **vóór** `COMMIT`; bij elke fout — syntax, botsing, verificatie, falende COMMIT — `ROLLBACK`, typed `SchemaContractError` (`schema_init_failed` / `schema_incomplete`) en een lege database.
2. **Bestaande database** → `assert_startup_contract`: kern → versie → contract. Startup migreert of repareert nooit; de fout noemt het te draaien commando.
3. Zonder `schema.sql` is er geen noodschema meer (`schema_init_failed`).

Verwacht gevolg: een werkelijk onvolledige of verouderde lokale database blokkeert de app-start met een duidelijke reden. Dat is de gevraagde garantie; herstel gaat via de expliciete migraties hieronder.

## 4. Migratieroutes: preconditie → backup → één transactie → verificatie → commit

Alle vier actieve routes volgen hetzelfde patroon met de gedeelde helpers uit `schema_contract`. Ondersteunde profielen zijn expliciet (`SUPPORTED_VERSIONS = (0, 1, 2, 3)`); `target_contract(N)` leidt het volledige doelcontract van elk profiel declaratief af uit `schema.sql` door precies de v7-, v6- en v5-wijzigingen terug te draaien. Elke route toetst **binnen** haar transactie drie losse dingen: (a) bronbehoud — geen enkel object uit het pre-migratiemanifest mag verdwijnen, behalve wat de route aantoonbaar bewust verwijdert; (b) het volledige versiespecifieke doelcontract incl. de complete markerverzameling, `integrity_check` en `foreign_key_check`; (c) haar eigen lokale verificatie. Op een al hogere database is het doelcontract de hoogste aanwezige versie (idempotentie). Onbekende of ongeldige versiewaarden (`3.5`, tekst) zijn `schema_version_invalid`, nooit een stille afronding.

| Route | Preconditie (vóór enige schrijfactie) | Backupprefix | Doel | CLI |
|---|---|---|---|---|
| `python -m database.migrate_database [db]` (legacy) | kernschema (DEF-663-guard) | `pre_legacy_migration` | legacy kolommen/indexen, rebuilds alleen als een verouderde kolom of een FK naar `definities_old` (DEF-688) bestaat | exit 1 bij mislukking **of** incomplete verificatie |
| `python -m database.migrations.v5_migration` | kerntabellen | `pre_v5_migration` | versie 1; historische tabellen behouden als aanwezig, niet vereist | exit 1 |
| `python -m database.migrations.v6_migration` | versie 1 + `rag_chunks` | `pre_v6_migration` | versie 2 | exit 1 |
| `python -m database.migrations.v7_migration` | versie 2 + `rag_collections` | `pre_v7_migration` | versie 3 | exit 1 |

- `create_migration_backup` gebruikt uitsluitend het DEF-663-contract (`create_verified_backup`: read-only snapshot, WAL-veilig, `integrity_check`, kernschema, manifest, atomische publicatie). Weigert de helper, dan is er niets gewijzigd en blijft er geen lege `backups/`-map achter.
- `migration_transaction`: `BEGIN IMMEDIATE` … `COMMIT`; elke fout, ook in de COMMIT zelf, geeft `ROLLBACK`. De route verifieert **binnen** de scope en raist `migration_verification_failed`, zodat versiemarker, DDL en verificatie samen committen of samen terugrollen.
- De legacy-route is als geheel **één transactie**: ADD COLUMN, backfill, indexen, de DEF-672-rebuilds (als `SAVEPOINT` binnen de buitenste grens; standalone blijven ze een eigen `BEGIN IMMEDIATE`), normalisatie én eindverificatie (bestaande objecten, `_old`-resten, kandidatenindex, FK/integrity, plus het volledige doelcontract van het bronprofiel). Een afgewezen eindverificatie, een fout in een latere stap of een falende COMMIT laat schema, objecten en data exact zoals ervoor. De PRAGMA's van `_migratiemodus` staan bewust buiten de transactie en worden altijd hersteld. `_ensure_definitie_voorbeelden_indexes` gebruikt geen `executescript` meer (impliciete commit).
- Rebuilds behouden **extra gebruikerskolommen** met type, `NOT NULL` en `DEFAULT` (inhoud incl. NULL en JSON wordt meegekopieerd). Wat `ADD COLUMN` niet reproduceert — primary key, `NOT NULL` zonder default, generated kolommen (`table_xinfo`), of een kolom met/in `REFERENCES`, `COLLATE` of `CHECK` — laat de migratie fail-closed falen (`rebuild_unsafe_extra_column`) met het origineel intact. Sleutelwoorddetectie leest uitsluitend tekst buiten quotes (een `DEFAULT 'generated'` is geen generated kolom).
- **Alle bronconstraints** worden per rebuild afzonderlijk vóór/na vergeleken uit de SQLite-metagegevens (`index_list`/`index_xinfo`, `foreign_key_list`, CHECK-expressies), ook op canonieke kolommen (Codex-herreview P1). Verloren `UNIQUE`-semantiek — inline, benoemd (`CONSTRAINT … UNIQUE`), gequote, composite of op een canonieke kolom — wordt teruggezet als unique index `uq_<tabel>_<kolommen>` met dezelfde collatie. Alleen een volledige, niet-partiële unieke index op echte kolommen geldt als equivalent van een `UNIQUE`-constraint; een partiële of expressie-index (bv. `UNIQUE(external_ref) WHERE status='established'`) telt niet als vervanging, blijft via zijn eigen volledige DDL behouden en wordt nooit tot een volledige constraint verstrakt (rootprobe `probe-partial-unique-equivalence`); een verloren FK of CHECK, of `COLLATE`/generated op een canonieke kolom, laat de migratie fail-closed stoppen (`rebuild_constraint_lost`). Alleen constraints die een bewust verwijderde kolom raken vervallen mee; de DEF-688-FK naar `definities_old` wordt op het herstelde doel `definities` vergeleken.
- Semantiek die niet in PRAGMA-metagegevens staat wordt **conservatief geweigerd** met de bron intact (Codex-review 3): `ON CONFLICT`-beleid op UNIQUE/PK en `DEFERRABLE` op foreign keys (buiten quotes ergens in de tabel-DDL van een rebuildtabel), en sterkere `NOT NULL`, andere `DEFAULT`, een andere **affiniteit** of een andere **sleutelsemantiek** (rowid-alias/AUTOINCREMENT) op canonieke kolommen (`rebuild_column_semantics_lost`, vergeleken uit `table_info` en de contractgrammatica van bron en nieuwe tabel). Een BLOB-bronkolom die `7` als integer bewaart zou anders stil `'7'` (text) worden (rootprobe `probe-canonical-column-affinity`); een `INT PRIMARY KEY`-bron met een geldige NULL-id zou stil een nieuw id krijgen (rootprobe `probe-rebuild-primary-key-values-v2`). Geen automatische id-reparatie of typeconversie. Een CHECK mag alleen meevervallen als hij de verwijderde kolom als **identifier** noemt (ook gequote); een string-literal met die naam is geen verwijzing.
- De **AUTOINCREMENT-teller** (`sqlite_sequence`) van een herbouwde tabel wordt binnen dezelfde transactie op minimaal de oude waarde teruggezet, ook als de hoogste oude rij niet meer bestaat; eerder uitgegeven ids komen nooit terug (rootprobe `probe-autoincrement-preservation`).
- Het kolomcontract legt naast affiniteit, `NOT NULL`, `DEFAULT` en pk-positie ook **rowid-alias** en **AUTOINCREMENT** vast: alleen `INTEGER PRIMARY KEY` (zonder `DESC`) geeft zelf ids uit; `BIGINT PRIMARY KEY` of `INT PRIMARY KEY` levert bij een gewone INSERT `id = NULL` en is drift (Codex-herreview P1). `AUTOINCREMENT` telt alleen als sleutelwoord in de grammaticale positie na `PRIMARY KEY [ASC|DESC] [ON CONFLICT x]`; het woord in een gequote constraintnaam, literal of commentaar is geen sleutelwoord (Codex-review 3). Versiemarkers worden in startup, fresh init en migratieverificatie strikt als ruwe `int` gevalideerd vóór enige conversie (`2.5` of tekst → `schema_version_invalid`, met rollback).
- Fresh init verifieert vóór de commit het volledige doelcontract inclusief de complete markerverzameling `{1, 2, 3}`; een script dat alleen marker 3 zaait wordt teruggerold (Codex-herreview P2). `_migratiemodus` herstelt PRAGMA's ook na een gedeeltelijk mislukte setup of een falende herstelstap, op dezelfde verbinding; de CLI-verificatie `verify_migration` sluit haar verbinding in een `finally`.
- v7 verwijdert alleen de views `failed_generations`/`definities_with_generation` die bij uitvoering (`SELECT … LIMIT 0`) aantoonbaar falen met precies "no such table: generation_logs_old". Geen substringclassificatie: een geldige gebruikersview met dezelfde naam, ook met die tekst als literal, alias of commentaar, blijft staan; een view met bekende naam die om een andere reden onbruikbaar is, is een twijfelgeval en laat v7 fail-closed stoppen (`stale_view_unresolvable`).
- I/O en resources: de hele init-grens is getypeerd — een onbeschikbare databasemap (`schema_init_failed: database_dir_unavailable`), een corrupt of onleesbaar bestand (`database_unreadable`), PRAGMA-fouten na `connect` (de nieuwe verbinding wordt gesloten, ook in `DatabaseConnection.get_connection`), een onschrijfbare `backups/`-map (`backup_refused: backup_dir_unwritable`) en een onleesbaar `schema.sql` (`canonical_schema_unreadable`). Elke migratieroute sluit haar verbinding in een `finally`. Een open buitenste transactie van de aanroeper wordt door init nooit gecommit of teruggerold; init weigert dan getypeerd.
- Restorebewijs per route: `tests/integration/database/test_migratie_restore.py` legt vóór de migratie de **volledige inhoud van elke tabel** (alle kolommen incl. een extra gebruikerskolom, alle rijen, de AUTOINCREMENT-tellers) én het volledige bronmanifest vast. Na migratie moeten alle oorspronkelijke kolomwaarden behouden zijn met uitsluitend de expliciet bedoelde kolomverwijderingen (legacy: `voorkeursterm_is_begrip`; v7: de tellers) en bedoelde rijtoevoegingen (`schema_version`); na echte restore naar een **nieuw** pad geldt volledige gelijkheid. Een aparte test bewijst dat een corruptie in een voorheen niet geselecteerde kolom (`rag_documents.file_path`) de vergelijking laat falen. In-place herstel blijft DEF-666.

Herstelvolgorde voor een lokale database die bij startup wordt geweigerd: maak zelf ook een backup (`scripts/backup_database.sh`), draai de migraties in volgorde v5 → v6 → v7 (elke stap is idempotent en weigert bij een ontbrekende voorganger), start de app opnieuw.

## 5. Historie: trigger verplicht, app-audit blijft, geen nieuw beleid

- De canonieke trigger `log_definitie_changes` (AFTER UPDATE op `definities`) is **verplicht** onderdeel van het contract. Een database zonder die trigger, of met een trigger van dezelfde naam maar een andere body, wordt geweigerd. Er is geen alternatief "app-only"-profiel.
- Daarnaast schrijven de app-lagen zelf auditrijen (`AuditHelpers.log_geschiedenis`, `definition_edit_repository._add_history_entry`). Bewuste behoudkeuze: **triggerrijen leggen waarden en context vast** (oude/nieuwe definitie, statusovergang, context-snapshot), **app-rijen leggen actie, actor en reden vast**. Eén gebruikersactie kan dus meerdere fysieke rijen in `definitie_geschiedenis` opleveren; de timestamp-trigger laat de historietrigger bovendien nogmaals vuren (bekende cascade, vastgelegd in de DEF-663-restoretest).
- Er wordt niets gededupliceerd, verwijderd of als "de" bewijsautoriteit aangewezen. Eén gezaghebbend snapshotcontract is de scope van **DEF-626**; deze story documenteert alleen de huidige, bewust behouden situatie. De eerder geobserveerde productiedrift (DEF-482-notitie: trigger afwezig) is geen actuele meting en is hier niet opnieuw gemeten.

## 6. Buiten scope / bewust niet gedaan

- Geen productiedatabase geopend, gemigreerd of gemeten; alle bewijs op tijdelijke paden.
- Niet-canonieke historische tabellen (`definitie_drafts`, `generation_logs`, `synonym_suggestions`, `performance_*`) zijn geen nieuwe verplichte producttabellen; ze blijven behouden als ze bestaan.
- `tests/integration/database/test_unique_constraint_removal.py` faalt op twee tests vóór én na deze wijziging (bewijs: `claude-impl-01c-…`); pre-existing, niet in scope.
- De brede smoke-/gate-reparatie is DEF-519. Tests die het standaardpad `data/definities.db` gebruikten (`ServiceContainer()`, `get_definition_service()`, `DefinitieRepository()` zonder pad) kregen de opt-in fixture `hermetische_werkmap` (tmp-werkmap met `config/` en `src/` als symlink en een lege `data/`). Beperking: `get_definitie_repository()` zonder pad gebruikt een **absoluut** pad onder de repo-root, dus daar moet de singleton vooraf op een tijdelijke database worden gezet (zie `tests/unit/ui/test_document_snippets_docx.py`). Integratietests buiten de actieve route die dat pad nog gebruiken (`test_duplicate_detection_fix.py`, `test_history_removal.py::test_database_history_table_intact`) blijven DEF-519.
- In-place restore: DEF-666.
