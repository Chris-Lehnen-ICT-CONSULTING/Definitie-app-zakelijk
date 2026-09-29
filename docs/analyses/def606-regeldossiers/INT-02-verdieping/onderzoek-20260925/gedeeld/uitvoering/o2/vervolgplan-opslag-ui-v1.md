# DEF-835 / DEF-626 — vervolgplan opslag, herladen en presentatie v1

> **Voor Claude:** gebruik de skill **executing-plans** na akkoord, één pakket tegelijk. Claude Code CLI implementeert en corrigeert; een afzonderlijke Codex CLI reviewt zonder bronwijzigingen.

**Doel:** een INT-02-O2-beoordeling en haar exacte betekenisgronden veilig bewaren, herladen en tonen zonder verborgen modelcall.

**Architectuur:** eerst de ontbrekende gedeelde DEF-626-opslagvoorziening bouwen; daarna INT-02 erop aansluiten. Onveranderlijk historisch bewijs en actuele toepasselijkheid zijn afzonderlijke begrippen. Bestaande ESS-03/INT-03-data blijven behouden.

**Techniek:** bestaande Python/SQLite/repositoryketen, pytest, Streamlit; geen nieuwe dependency.

28 september 2026 · voorstel voor schema-/contractbesluit, **geen bouwstart**. Onderzocht op `f9bb9e6973926a3cf768995f5d879f6edfd6322d`. `git fetch origin` is geslaagd; `origin/main=84bdc8c1b060ab50a1bd1428aed778bb2ed6007f` bevat geen nieuwere commits dan deze branch.

## 1. Gecontroleerde afwijkingen en aansluitpunten

Actuele Linearbronnen: DEF-626 Backlog; DEF-835 In Progress; DEF-815 Backlog. De in DEF-626 genoemde voorbeeldpaden zijn geen bestaande generieke opslagimplementatie.

| Vindplaats op bovenstaande HEAD | Aangetroffen feit / gevolg |
| --- | --- |
| `src/database/schema.sql:55,85,118` | Definitierij met version_number en generation_prompt_data; losse geschiedenis bevat geen volledige validatiesnapshot. |
| `src/database/definitie_crud.py:2647` | Letterlijk `"version_number = version_number + 1"`; in-place update, geen onveranderlijke versie. |
| `src/database/definitie_crud.py:1416,1531` | INT-03/ESS-03 hebben eigen append-logica met `"assessment"`, `"superseded_at"`, `"superseded_on_version"`. Geen generieke snapshot. |
| `src/database/definitie_crud.py:2518,2592,2662` | validation_date ontbreekt in allowed_fields; herlezen onder lock; daarna app-audit naast trigger. |
| `src/database/schema.sql:247,256` | `update_definities_timestamp` doet een geneste UPDATE; `log_definitie_changes AFTER UPDATE` schrijft historie. |
| `src/database/audit_helpers.py:160` | Tweede app-auditwriter. |
| `src/services/definition_edit_repository.py:99,458` | Derde historiepad met eigen commit; fouten worden gelogd. Dit verhindert één betrouwbare atomaire grens. |
| `src/database/db_connection.py:98` | Bestaande transactiehulp met BEGIN IMMEDIATE en rollback, hergebruiken. |
| `src/database/migrations/v8_migration.py:193` | Migratie vereist voorgaande marker, gecontroleerde backup en migration_transaction. Huidige schemaversie 4; modulenaam v8 is niet schemaversie 8. |
| `src/services/definition_repository.py:975,1094,1328,1707` | Slechts score bij aanmaak; aparte assessmentvelden bij opslag/herstel; geen volledig generiek bewijscontract. |
| `src/services/validation/evaluators/decision_rule_assessment.py:140,215` | O2 heeft review.actuality; assessment is bij error/NE None. Alleen de publieke assessment overnemen verliest foutdocumenten. |
| `src/domain/int02/contract.py:804` | Replay verwacht een getypeerd Beoordelingsdocument; ruwe dict is geen geldig document. |
| `src/services/definition_edit_service.py:253,565,577,607,788` | INT-03 extractie, pure replay en sessieherbinding aanwezig; O2-aansluiting ontbreekt. |
| `src/ui/components/definition_edit_tab.py:1180,1318,1423,2337,2577` | Bestaande INT-03-editorflow; INT-02 moet ook bedoeling, bronnen en routeringshash binden. |
| `src/ui/components/validation_view.py:441,486,537,590,879` | Algemene scoreloze renderer; INT-03 verwacht review.assessment; O1-passagehulp kan bij O2 dupliceren. |
| `src/services/data_aggregation_service.py:346,597` | Exportreplay gebeurt pas na opbouw van de werkelijke exportkandidaat; dit patroon behouden. |
| `src/services/export_service.py:233,278,546,615,804,1028`, `src/export/export_txt.py:416` | Bestaande INT-03-velden in JSON/CSV/TXT en bulk; INT-02 ontbreekt. |

Geen productiegegevens gelezen of gewijzigde tests gedraaid voor deze inventarisatie. De laatste 526 geslaagde tests bewijzen WP5a, niet onderstaande nieuwe pakketten.

## 2. Voorgesteld gedeeld contract S1 — expliciet besluit nodig

Dit raakt DEF-626 en valt buiten het afgeronde WP5a. Voorstel: één eigen branch `feature/DEF-626-validatiesnapshots` vanaf de gecontroleerde O2-HEAD, met die afhankelijkheid expliciet in de latere PR. Geen maincheckout wijzigen.

### Schema 4 → 5, uitsluitend offline bouwen en migratietesten

- Nieuwe append-only tabel `definition_evidence_versions`: UUID, definitie-ID, versienummer, exact versiepayload als JSON, payloadhash en tijd. Uniek op definitie-ID/versienummer. De betekenisdragende tekst/context/bedoeling/bronnen zijn volledig bewaard, niet alleen hun hashes.
- Nieuwe append-only tabel `validation_snapshots`: UUID, versie-UUID, unieke run-ID/idempotentiesleutel, snapshotcontractversie, volledige validatieresultaat-JSON, bewijscomponenten-JSON, invoer-/context-/bronhashes, regel/config/validatorversies en tijd. Expliciete runstatus, unknown_reason/readiness, score inclusief NULL/0.0, acceptability, violations en dekking blijven aanwezig.
- Nieuwe tabel `validation_snapshot_heads`: definitie-ID, actuele versie en snapshotverwijzing plus toepassingstoestand/reden. Alleen deze verwijzing mag wijzigen; historie blijft ongewijzigd. Historisch bewijs nooit aanpassen om stale te markeren.
- UPDATE/DELETE op beide bewijstabellen wordt geweigerd; verwijzingen krijgen geen cascading delete. Bestaande historie blijft volledig staan. Identieke herhaling met dezelfde run-ID is idempotent; andere inhoud met dezelfde ID is een fout.
- Geen automatische backfill of nieuwe kwaliteitstoekenning aan legacyrecords. Ontbrekend legacybewijs blijft expliciet unknown. Een gemeten 0.0 wordt niet als ontbrekend gelezen. Oude ESS-03/INT-03-payloads worden leesbaar behouden; nieuwe bewijscomponenten krijgen de gedeelde writer als eigenaar.
- Een schemawijziging wordt alleen op tijdelijke databases beproefd. Migratie op Chris' echte database is een latere, afzonderlijke uitvoeringsstap.

### Eén transactie en één historieschrijver

Voorstel: de centrale applicatietransactie wordt de enige historieschrijver. De migratie vervangt daartoe de twee bestaande triggers `log_definitie_changes` en `update_definities_timestamp` door centrale applicatiewrites; bestaande historie wordt niet verwijderd. **Het verwijderen van precies deze twee triggerdefinities vraagt expliciete toestemming onder de verwijderregel.** Er worden geen bestanden, testgevallen of historieregels verwijderd.

De lagere CRUD-route verzamelt definitiemutatie, versiebump, timestamp, immutable versie, snapshot, actuele verwijzing en precies één audit-event in één BEGIN IMMEDIATE. Generieke updates en statusupdates gebruiken dezelfde ingang. Losse editor- en audithelpers delegeren; geen eigen commit, geen ingeslikte bewijsfout. Een stale expected_version weigert de gehele mutatie.

Nieuw intern opslagcontract: optionele volledige validatie-uitkomst plus bewijscomponenten, verplichte verwachte versie bij bestaande records en run-ID bij bewijsschrijven. Bestaande callers zonder bewijs krijgen expliciet unknown/stale, nooit impliciet geldig bewijs. O2-foutdocumenten worden vanuit de verkrijgingsroute aangeleverd, ook wanneer de publieke evaluator assessment=None geeft.

Bij een snapshotfout rollback van de gehele kwaliteitsmutatie. Alleen een afzonderlijk expliciet gekozen draftfallback mag in een nieuwe transactie gewijzigde tekst met unknown/stale bewaren; geen vastgestelde status en geen geldig bewijs claimen. Deze technische integriteitsvoorwaarde is geen nieuwe INT-02-inhoudspoort. Andere inhoudelijke poortregels blijven DEF-831 volgen.

### Bestandsbereik S1 en omvang

Bestaand (9):
- `src/database/schema.sql`
- `src/database/schema_contract.py`
- `src/database/definitie_crud.py`
- `src/database/definitie_repository.py`
- `src/database/audit_helpers.py`
- `src/database/models.py`
- `src/services/definition_repository.py`
- `src/services/definition_edit_repository.py`
- `tests/unit/database/test_schema_contract_init.py`

Nieuw (6):
- `src/database/migrations/v9_migration.py` (schemaversie 5, naam opnieuw op botsing controleren)
- `src/domain/validation_snapshot.py`
- `src/database/validation_snapshot_repository.py`
- `tests/unit/database/test_v9_migration.py`
- `tests/unit/services/test_def626_validation_snapshots.py`
- `docs/architectuur/contracts/validation_snapshot_contract_v1.md`

Bestaande atomaire tests aanpassen met behoud van cases (1):
- `tests/unit/services/test_definition_workflow_atomiciteit.py`

Raming: **16 bestanden, 1.000–1.600 regels inclusief tests/documentatie**. Geen dependency. Een buiten dit bereik noodzakelijke contractuitbreiding eerst concreet melden; geen stil brede refactor.

### S1 uitvoering en bewijs

1. Claude schrijft falende tijdelijke-SQLite-tests voor schema 4→5, verse schema-5-db en behoud van oude historie.
2. Rode uitvoer opslaan; falen moet door het ontbrekende nieuwe contract komen.
3. Contract en migratie minimaal bouwen; startup migreert niet automatisch.
4. Nieuwe rode tests: echte create/update/status/edit save→reload, 0.0/NULL/legacy, ongewijzigde oude snapshot, één event/versiebump, idempotentie, twee schrijvers met stale versie, UPDATE/DELETE op bewijs geweigerd.
5. Centrale repositoryroute implementeren; geen tweede INT-02-historylijst.
6. Foutinjectie tussen definitie-/snapshotinsert bewijst rollback; expliciete draftfallback wordt afzonderlijk getest.
7. Groen draaien plus bestaande ESS-03/INT-03-persistentie, versie- en auditregressie. Rode toekomsttests uit DEF-626 behouden; relevante contractclaims over echte adapterroutes aantonen.
8. Ruff/Black/mypy; onafhankelijke Codex CLI-review van concrete diff; correcties bij dezelfde Claude; gerichte herverificatie en normale lokale commit.

Gerichte pytestselectie (na aanleg nieuwe bestanden):
`/Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python -m pytest tests/unit/database/test_v9_migration.py tests/unit/database/test_schema_contract_init.py tests/unit/services/test_def626_validation_snapshots.py tests/unit/services/test_definition_workflow_atomiciteit.py tests/unit/services/test_def772_int03_persistentie.py tests/unit/services/test_def766_ess03_persistentie.py -o addopts= -q -ra`.

Offline-bootstrap en tijdelijke databases verplicht. DEF-626 pas geleverd noemen wanneer alle geraakte criteria werkelijk bewezen zijn; geen algemene approvalgate/ontologie-evaluator bouwen.

## 3. O2-opslag en replay S2 — ná S1

Doel: getypeerd O2-document, inclusief error, via de gedeelde bewijscomponent INT-02 bewaren en zonder AI-call herladen. Geen derde losse assessmenthistorie.

Bestanden (6; raming 400–700 regels):
- nieuw `src/domain/int02/serialization.py`: strikte heen/terugconversie met behoud van exact document; geen reparatie van corrupte inhoud.
- `src/services/orchestrators/validation_orchestrator_v2.py`: interne documentdrager vanuit verkrijgingsroute, onafhankelijk van publieke assessment.
- `src/services/orchestrators/definition_orchestrator_v2.py`: volledige validatie en oorspronkelijke O2-document naar gedeelde opslag.
- `src/services/definition_edit_service.py`: INT-02 inputopbouw/replay/herbinding en opslaan via S1.
- nieuw `tests/unit/domain/test_def835_int02_serialization.py`.
- nieuw `tests/unit/services/test_def835_int02_opslag_herbinding.py`.

Contractuitbreiding: interne documentdrager `assessment_documents["INT-02"]` en bewijscomponent in het gedeelde snapshot; niet als onbewezen caller-oordeel accepteren en niet stil aan het publieke resultaten-schema toevoegen. Na foutieve/corrupte opslag geen pass/fail. Oude documenten ongewijzigd, toepasselijkheid opnieuw bepaald met domeincontract.

TDD per stap: serialisatie inclusief foutdocumenten → echt save/reload → wijzig ieder bindingsveld afzonderlijk → wijzig terug → recordwissel. Citaten en oorspronkelijke kern bytegelijk; nul modelcalls tijdens opslaan/herladen. C118 plus error/NE/RR/pass/fail/NA, ontbrekende bron/betekenis en gewijzigde routerhash. Getter voor configuratie mag geen call starten.

Testcommando: bovenstaande Python met `-m pytest tests/unit/domain/test_def835_int02_serialization.py tests/unit/services/test_def835_int02_opslag_herbinding.py tests/unit/validation/test_def835_int02_evaluator.py -o addopts= -q -ra`. Zelfde review-/commitcyclus als S1.

## 4. UI U1 en export E1 — ná betrouwbare replay

### U1, 4 bestanden, circa 300–500 regels

- `src/ui/components/definition_edit_tab.py`
- `src/ui/components/validation_view.py`
- nieuw `tests/unit/ui/test_def835_int02_weergave.py`
- nieuw `tests/unit/ui/test_def835_int02_apptest.py`

Gebruik SessionStateManager en bestaande widget-keypatronen. Toon oordeel, reden, gerichte vraag, bron/versie en actueel/historisch/fout duidelijk en scoreloos. Geen dubbele O1-reden bij O2, geen oude citaten als actueel, geen herstelknop. AppTest: opslaan, echte herlaadroute, invoer wijzigen/terugzetten, recordwissel, error/RR en nul modelcalls. Bestaande `test_def771_int02_validation_view.py` blijft behouden en groen.

### E1, 5 bestanden, circa 250–450 regels

- `src/services/data_aggregation_service.py`
- `src/services/export_service.py`
- `src/export/export_txt.py`
- nieuw `tests/unit/services/test_def835_int02_export_actualiteit.py`
- `tests/integration/test_export_levels_comprehensive.py`

Additief exportveld `int02_beoordeling` in uitgebreide/complete JSON/CSV/TXT en bulk. Dit is een expliciet te accorderen exportcontractuitbreiding. Beperkte export blijft binnen haar bestaande veldkeuze. Replay vindt plaats na alle aanpassingen aan de werkelijk geëxporteerde kandidaat, inclusief expliciet leeg gemaakte bedoeling/bronnen/context. Status/reden/herkomst/actualiteit tonen; tekst niet wijzigen, geen exportpoort en geen modelcall. Historische inhoud blijft herkenbaar historisch. Veldtellingen aanpassen met behoud van bestaande testcases.

Voor U1/E1: nieuwe tests eerst rood, groen plus bestaande INT-03-weergave/editor/exportregressie. Exacte pytestselectie in de uitvoerdersbriefing; Ruff/Black op gewijzigde bestanden. Ieder pakket afzonderlijk reviewen en committen, geen overlappende schrijvers.

## 5. Volgorde, oplevering en besluiten

Voorgestelde uitvoervolgorde: Q1/protocol → goldsetvoorbereiding → S1 → S2 → U1 → E1 → begrensde kwalificatie → geïntegreerde eindcontrole. Eén codepakket tegelijk; onbeantwoorde goldsetvraag blokkeert geen geaccordeerd offline opslagpakket.

Eindcontrole na code-integratie: bestaande offline `scripts/testing/run_profile.py unit`, `integration`, `acceptance-smoke`, met eigen volledige logs en daadwerkelijke failures; mypy en toepasselijke lint. Claims blijven beperkt tot gedraaide selectie. De twee eerder bewezen baselinefouten niet als nieuwe O2-regressie presenteren, maar ook niet verbergen.

Pas na gesloten reviewbevindingen en geslaagde onafhankelijke kwalificatie volgt een concrete activeringsdiff. Actions blijven uit; geen push, merge of productieactivering onder dit voorstel.

Benodigd akkoord:
1. S1: gedeeld schema-/opslagcontract, 16 bestanden en één centrale historieschrijver; expliciet vervangen/verwijderen van alleen de twee genoemde triggerdefinities in migratiecode.
2. S2: zes bestanden en de interne documentdrager; U1 en E1 inclusief additief exportveld zoals hierboven.
3. Het aparte kwalificatieprotocol/proefmandaat. De eerdere algemene toestemming voor modelcalls vervangt het verbruikte concrete driecallbudget niet.

Na deze concrete besluiten vraagt de coördinator binnen het afgebakende bereik geen herhaald algemeen akkoord. Een echte scope-/contractwijziging, nieuwe verwijdering of extra proefbudget wordt apart voorgelegd.

