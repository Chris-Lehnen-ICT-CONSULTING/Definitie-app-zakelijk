# BATCH-009 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-galileo`
- Onafhankelijke verifier: `codex-kierkegaard`
- Scope: 20/20 blobs, 2.511/2.511 fysieke regels en 84/84 Python-symbolen

Alle toegewezen regels en symbolen zijn rechtstreeks uit de immutable
Git-objecten gelezen. Er zijn geen applicatiebestanden gewijzigd.

## Verificatie

- Primaire relevante selectie in de wave: 263 tests geslaagd, 2 gefaald en
  1 verwachte xfail. De twee failures behoren bij B009-004.
- Onafhankelijke source-selectie: 111 tests geslaagd.
- Defecte migratietest afzonderlijk: 2 gefaald, 9 geslaagd.
- Ruff en Black: geslaagd. Repro’s gebruikten uitsluitend tijdelijke SQLite-DB’s.

## Bewezen bevindingen

### B009-001 — P1 — migratierebuild verwijdert generation_prompt_data

`src/database/migrate_database.py:38-81,448-470` definieert en kopieert de
vervangende tabel zonder het canonieke veld uit `schema.sql:75`. Reproductie:
een tijdelijke actuele database met prompt-JSON plus de legacykolom migreerde
met `True`, maar kolom en data waren daarna weg. Aanbevolen: één canonical DDL
of een expliciet gecontroleerde kolomintersectie; postconditions op schema,
rijaantallen en datafingerprints.

### B009-002 — P1 — defecte rebuild rapporteert succes na destructief dataverlies

`migrate_database.py:403-405,448-481,483-533` commit vóór de rename/copy,
degradeert fouten tot waarschuwingen en retourneert daarna onvoorwaardelijk
succes. Een rij die de nieuwe categorie-CHECK schendt gaf `True`, terwijl
`definities=0` en alleen `definities_old=1`; een view werd bovendien herschreven
naar de oude tabel. Aanbevolen: één transaction/savepoint rond rename, create,
copy, index, view en FK; iedere fout rollback + False/raise; controleer integrity,
FK’s, views en rijaantallen vóór commit.

### B009-003 — P2 — voorkeurstermbackfill wordt conditioneel overgeslagen

`migrate_database.py:344-373,448-479` voert de backfill alleen uit wanneer de
tekstkolom nog ontbreekt, maar dropt de boolean bij de rebuild altijd. Een DB
met bestaande nullable `voorkeursterm` en flag TRUE eindigde met `True`, zonder
flag en met NULL voorkeursterm. Aanbevolen: idempotente backfills loskoppelen van
`ADD COLUMN` en resultaat aantoonbaar controleren vóór een bronkolom verdwijnt.

### B009-004 — P2 — migratie-integratietest zoekt vanaf de verkeerde projectroot

`tests/integration/database/test_unique_constraint_removal.py:54-60` en negen
vergelijkbare plekken klimmen één parent te weinig omhoog en zoeken daardoor
onder `tests/src/...`. De `exists()`-guard slaat de migratie stil over; exacte
run: 2 failures en 9 passes, waaronder ontbrekende pre-index en niet herstelde
rollback-index. Dit testbestand ligt buiten de batchscope en blijft daarom zelf
pending; het defect is wel door beide reviewers functioneel bewezen. Aanbevolen:
een gedeelde repo-rootfixture (`parents[3]`) en altijd `assert migration.exists()`.

## Niet getest

- Geen echte productie-DB of productiebackup; geen multi-process load.
- Geen externe AI/RAG/web-calls en geen visuele UI/a11y/responsive flow.
