# S1 — uitvoerdersbriefing gedeelde validatiesnapshots (DEF-626, voorbereid)

Jij bent de Claude Code CLI-uitvoerder. Voer deze opdracht zelf uit; start geen agents, reviewers of extra CLI-sessies. De coördinator geeft de definitieve werkboom en basis mee bij dispatch. Dit bestand alleen start geen proces.

## Mandaat en leidende bron
Chris heeft op28september2026 letterlijk "akkoord! go" gegeven op vervolgplan-opslag-ui-v1.md en kwalificatieprotocol-v1.md. S1 is expliciet geaccordeerd inclusief16bestanden, schemaversie4→5 en het vervangen van uitsluitend de twee triggers log_definitie_changes en update_definities_timestamp in migratiecode. Geen historieregels, bestanden of testcases verwijderen. Geen echte database migreren. Geen nieuwe dependency.

Lees volledig vervolgplan-opslag-ui-v1.md §1–2 en vervolg-akkoord-v1.md; technische inhoud daarvan is leidend. Lees actuele DEF-626-issuekopie die bij dispatch wordt meegeleverd, CLAUDE.md, toepasselijke regels en migratiepatroon. Q1 moet eerst geverifieerd zijn; deze opdracht wordt niet parallel met ander codewerk uitgevoerd.

Eigen branch feature/DEF-626-validatiesnapshots vanaf de door coördinator vastgelegde O2-afhankelijkheid; nooit main. Maak unieke herstelkopieën van bestaande doelbestanden onder eigen bewijsmap. Eén schrijver, laat andermans veranderingen intact.

## Bestandsbereik
Uitsluitend de16bestanden uit plan§2:
src/database/schema.sql
src/database/schema_contract.py
src/database/definitie_crud.py
src/database/definitie_repository.py
src/database/audit_helpers.py
src/database/models.py
src/services/definition_repository.py
src/services/definition_edit_repository.py
tests/unit/database/test_schema_contract_init.py
src/database/migrations/v9_migration.py (nieuw)
src/domain/validation_snapshot.py (nieuw)
src/database/validation_snapshot_repository.py (nieuw)
tests/unit/database/test_v9_migration.py (nieuw)
tests/unit/services/test_def626_validation_snapshots.py (nieuw)
docs/architectuur/contracts/validation_snapshot_contract_v1.md (nieuw)
tests/unit/services/test_definition_workflow_atomiciteit.py

Documenteer bewijs en eigen verslag uitsluitend onder de bij dispatch aangewezen dossiermap. Geen code erbuiten. Indien een callsite aantoonbaar een extra bestand of ander contract vereist: meld exact bestand, call, fout en kleinste oplossing; laat afhankelijke wijziging liggen. Heronderzoek niet het hele project.

## Te bewijzen, vóór bouwen kritisch beoordelen
- Gedeeld immutable versie-/snapshotcontract met volledige input en metadata uit plan; UUID/run-ID en idempotentie, geen fictieve versies.
- Eén applicatiewriter voor create/update/status/edit, geen dubbele events of verborgen commits.
- SQLite4→5 met bestaande gecontroleerde backup/migration_transaction; verse schema5 en migratie dezelfde structuur.
- UPDATE/DELETE op nieuwe historische bewijstabellen geweigerd, geen cascading delete; bestaande legacyhistorie behouden.
- NULL versus werkelijk0.0 versus ontbrekend legacybewijs. Geen automatisch herstel/backfill van oud bewijs.
- Transactie herleest onder lock; stale expected_version weigert alles. Volledige kwaliteit + definitieversie atomair.
- Snapshotfout rollbackt kwaliteit. Een expliciet gekozen draftfallback mag alleen in nieuwe transactie unknown/stale bewaren en geen vastgestelde status/kwaliteitsclaim hebben. Als ook dat schrijven faalt: fout teruggeven. De actuele verwijzing moet ontbrekend bewijs kunnen aanduiden; verzin geen geslaagde snapshot. Leg die toestand expliciet vast en test hem.
- ESS-03/INT-03 historische payloads blijven intact en leesbaar; gedeelde writer wordt eigenaar van nieuw bewijs. Geen nieuwe losse INT-02-historylijst.
- Publieke validatieresultaten niet uitbreiden. S2 levert straks de O2-documentdrager. S1 bewijst generieke componenten met synthetische input.
- Ontologie, approvalgate en algemene stale-backfill vallen buiten S1. Geen INT-02-poort/herstelroute.

TDD: eerst relevante tests rood met echte tijdelijkeSQLite en repository/adapterroutes, dan minimale implementatie, dan groen. Bewaar rode/groene output en foutinjectiebewijs. Tests vóór productiecode. Gebruik bestaande offline-bootstrap, geen echte providerkeys/netwerk en geen productiedb. Testfiles/cases niet verwijderen of uitschakelen.

Gerichte selectie uit plan: nieuwe migratie/contracttests, bestaande schema_contract_init, workflow_atomiciteit en ESS-03/INT-03-persistentie. Onderzoek geraakte overige tests gericht op een concrete regressierisico; geen eindeloze brede rondes. Mypy en Ruff/Black op relevante scope. Nooit controlebypass of stil aanpassen van securitybeleid.

Lever eigen verslag op met aantallen rood→groen, schema-/APIbeschrijving, exacte bronnen/diff en beperkingen. Geen gitstage/commit/push/merge: coördinator geeft na verificatie de diff aan onafhankelijke Codex CLI; jij verwerkt diens bevestigde bevindingen daarna zelf.

