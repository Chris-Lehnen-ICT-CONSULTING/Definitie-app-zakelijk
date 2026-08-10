# BATCH-010 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-root`
- Onafhankelijke verifier: `codex-hypatia`
- Scope: 11/11 blobs, 3.909/3.909 fysieke regels en 88/88 Python-symbolen

Alle regels, SQL en symbolen zijn uit de immutable Git-objecten gelezen. Er zijn
geen applicatiebestanden gewijzigd.

## Verificatie

- Primaire gecombineerde selectie voor B006/B010: 183 tests geslaagd.
- Onafhankelijke selectie: 160/160 tests geslaagd.
- Ruff: geslaagd. Repro’s gebruikten uitsluitend tijdelijke SQLite-databases.

## Bewezen bevindingen

### B010-001 — P1 — SQLitebackup mist gecommitte WAL-data maar verifieert groen

`src/database/migrations/v5_migration.py:198-277,453-462` kopieert alleen het
hoofdbestand met `shutil.copy2` en controleert slechts grootte/tabelnamen. In
WAL-mode had de bron één gecommitte rij uitsluitend in WAL; de backup nul,
terwijl `verify_backup=True`. Aanbevolen: SQLite backup API of `VACUUM INTO`,
daarna `PRAGMA integrity_check`, rijaantallen en inhoudsfingerprint vergelijken.

### B010-002 — P1 — synonym-uniekheid verliest per-definitie-eigenaarschap

`src/database/schema.sql:362-379` bewaart `definitie_id`, maar
`UNIQUE(group_id,term)` negeert die scope; `synonym_sync.py:126-139` slaat de
tweede definitie over. Na sync voor definitie 1 en 2 bestond alleen eigenaar 1;
vervanging bij 1 deprecieerde die enige rij, zodat 2 geen actieve term had.
Aanbevolen: partiële unique-indexen voor globale en per-definitieleden en
duplicate-detectie binnen dezelfde scope/source.

### B010-003 — P1 — synonym-sync commit gedeeltelijk na fout

`synonym_sync.py:96-182` voert een meerstapswijziging uit, maar
`synonym_registry.py:97-122` gebruikt per methode een nieuwe autocommitconnection.
Een trigger brak insert 2 af; insert 1 bleef actief gecommit. De actieve caller
slikt de fout als warning. Aanbevolen: één unit-of-work/connection en transactie
voor groep, inserts en deprecations; rollback op elke fout, cache-invalidatie na
commit.

### B010-004 — P2 — productieschema seedt ongeldige testdefinities

`schema.sql:519-556` voegt bij iedere verse database twee definities en tags toe.
Vier van zes als JSON-array gedocumenteerde contextwaarden waren geen geldige
JSON. Aanbevolen: demo-seeds naar expliciete testfixtures of een optionele
seedcommand verplaatsen; production schema moet datavrij initialiseren.

### B010-005 — P2 — verse schema en migratieversie spreken elkaar tegen

`schema.sql:413-431` laat `schema_version` leeg en introduceert
`document_count`/`chunk_count` opnieuw, terwijl `v7_migration.py:1-10,84-91`
ze dood verklaart. Temp-DB: twee definities, nul versionrows en beide dode
kolommen. Aanbevolen: één strategie: migreren vanaf versie 0, of canonical latest
schema dat exact v7 weerspiegelt en de actuele versie registreert.

### B010-006 — P2 — SynonymRegistry sluit connections niet

`src/repositories/synonym_registry.py:126-1091` gebruikt herhaaldelijk
`with self._get_connection()`, wat alleen commit/rollbackt. Zes publieke calls
veroorzaakten door nesting 11 `ResourceWarning: unclosed database`-meldingen;
de integratietests toonden hetzelfde patroon. Aanbevolen: echte contextmanager
met `finally: close()` en geneste methoden dezelfde connection laten hergebruiken.

### B010-007 — P3 — dormant category-fix SQL faalt op het huidige schema

`src/database/migrations/fix_category_constraint.sql:10-75` maakt een tabel met
26 kolommen en kopieert via `SELECT *` uit een tabel met 31. Repro gaf
`OperationalError: table definities_new has 26 columns but 31 values were supplied`
en liet `definities_new` achter. Er is geen productiecaller gevonden. Aanbevolen:
als superseded markeren/verwijderen of herschrijven met expliciete kolommapping
en volledige rollback.

## Niet getest

- Echte productie-DB, multi-process WAL-load en productiebackup/herstel.
- Uitvoering van dormant SQL op productiegegevens, externe services of UI-flow.
