# DEF-808 / DEF-809 — uitvoerdersrapport Claude Code CLI (18 september 2026)

Werkboom `/private/tmp/DEF-808-809-p01-20260917`, branch `bugfix/DEF-808-809-p01`,
basis `29d8176b3` (DEF-806-fix, PR 460). Geen commit, push, appserver of modelaanroep.
Rolverdeling: Claude Code CLI implementeerde; onafhankelijke Codex CLI-review volgt
(door de coördinator te starten). Geen agents of extra CLI-sessies gebruikt.

## Oorzaken

**DEF-809.** `DefinitionEditService.save_definition` bouwt de `source_evidence`-
invoer uit de metadata van het *geladen* record (oude `source_assessment`). De verse
beoordeling van "Valideren" staat uitsluitend in de sessie
(`edit_last_validation`) en bereikt de repository nooit; de DB-laag ziet gelijk
bewijs en schrijft niets (`_bronbewijs_samenvoegen`). `set_source_assessment` in de
DB-laag had geen enkele aanroeper. Gevolg: na status → review + Opslaan leest Expert
Review het oude `source_assessment` en de oude `candidate` terug, terwijl `definitie`
wel exact P01 is (precies de readback van 17 september).

**DEF-808.** Documentbronnen krijgen bij generatie alleen `filename/doc_id/
citation_label/snippet/selection_basis` (handler `_build_document_snippets` →
orchestrator-normalisatie met vaste sleutellijst). Er was geen invoer, opslag of
doorvoer van `url`/`source_version`/`locator`, terwijl het broncontract die velden al
leest (`Bronidentiteit`, DEF-806-hyperlinkregel). Daarnaast liet `_locator` een
top-level `locator` alleen tellen als er géén positie binnen het document was.

**Autosave `no such table: definitie_drafts`** (observatie, niet gewijzigd): de tabel
staat niet in `schema.sql` en wordt door geen actieve migratie aangemaakt (alleen een
oud los `add_definitie_drafts_table.sql`). Autosave schrijft naar een aparte
draftstabel en zit niet in het opslag-/bewijspad; los van DEF-809. Herstel is een
schemawijziging → buiten mandaat, apart issue aanbevolen.

## Wijzigingen (13 bestanden gewijzigd, 7 nieuw; 704 regels toegevoegd, 3 verwijderd)

Gedeelde domeinlaag (nieuw) — `src/domain/sources/bronmetadata.py`:
`valideer_bronmetadata` (DEF-806-regel `is_bruikbare_hyperlink`, interne http(s) volstaat,
ongeldig = zichtbare fout en niets opgeleverd; eerdere opgave wordt aangevuld, niet
gewist), `pas_bronmetadata_toe` (zet `url`/`source_version`/`locator` + herkomstblok
`declared_metadata` met door/op; invoer niet gemuteerd), `vul_documentbronnen_aan`.
`src/domain/sources/normalisatie.py::_locator`: opgegeven vindplaats telt altijd mee,
ook naast `citation_label`.

Uploadroute: `ProcessedDocument.source_metadata` (optioneel veld, oude JSON laadt
ongewijzigd) + `DocumentProcessor.set_source_metadata`; handler
`_build_document_snippets` past de opgave op elke passage toe; orchestrator
(`definition_orchestrator_v2.py`, fase 2.9) kopieert `source_version`/`locator`/
`declared_metadata` mee; upload-UI `DocumentUploadRenderer._render_bronmetadata_invoer`
(key-only widgets, per geselecteerd document).

Aanvulroute op een opgeslagen record: DB-laag `DefinitieCRUD.vul_bronmetadata_aan`
(onder schrijflock + versieguard; nieuw bewijsdocument `origin: correction`, oud naar
historie, kwitantie/beoordeling/peildatum/generatie-identiteit blijven; eerdere
beoordeling geldt niet meer via vingerafdruk) met `Bronmetadatatoepassing` in
`models.py`; delegaties in `database/definitie_repository.py` en
`services/definition_repository.py`; `DefinitionEditService.vul_bronmetadata_aan`
(reviewer → record → versie/bewerkbaarheid → validatie → D); editor-UI
`_render_bronmetadata_section` in `definition_edit_tab.py`; bronkaart-caption
"Opgegeven bronmetadata (geen authenticiteitsbewijs)" in `sources_renderer.py`.

DEF-809: `save_definition(..., source_assessment=)` + `bindingsafwijzing_beoordeling`
(alleen `assessed` én exact dezelfde kernvingerafdruk als de op te slaan kandidaat
→ dan als actueel bewijs mee, DB legt vast als `origin: revalidation`; anders blijft
het opgeslagen bewijs staan en meldt `source_assessment_reason` waarom).
`DefinitionEditTab._save_definition` geeft `_sessiebeoordeling()` door en toont het
resultaat (success/warning). Geen schema-, dependency- of regelwijziging; geen deletes.

## Tests (TDD: RED bevestigd op basiscode, daarna GREEN)

Nieuw: `tests/fixtures/def808_p01.py` (vaste P01-casus), `tests/unit/domain/
test_def808_bronmetadata.py` (20), `tests/unit/services/test_def809_hervalidatie_bewaard.py`
(10), `tests/unit/services/test_def808_bronmetadata_aanvullen.py` (13),
`tests/unit/document_processing/test_def808_upload_bronmetadata.py` (11),
`tests/unit/ui/test_def808_809_editor_ui.py` (7), plus 1 test toegevoegd aan
`tests/unit/services/orchestrators/test_def743_source_transport.py`.

- RED (vóór implementatie): `test_def809_hervalidatie_bewaard.py` + orchestrator-test →
  **10 failed, 1 passed** (de reproductie van het oude gedrag slaagde, de fixes faalden;
  DEF-808-modules gaven `ModuleNotFoundError`).
- GREEN nieuwe tests: **62 passed in 2.69s**.
- Gerichte regressie aangrenzende suites (DEF-743/806/622, document_processing,
  transport, voorstelworkflow, experttab): **467 passed in 15.42s**.
- `make PY=<project-venv> lint`: ruff *All checks passed*, black *390 files unchanged*.
- `make PY=<project-venv> test` (unitgate via run_profile): **6135 passed, 75 skipped
  (bestaande skips), 1 xfailed, exitcode 0** in 3m36s.

Bewezen: metadata-doorvoer upload → snippet → orchestrator → bewijs; ongeldige links
(`javascript:`, schema-loos, `https://`, poort buiten bereik, witruimte, `mailto:`,
`file:`) zichtbaar afgewezen zonder te schrijven; stale binding (verder bewerkte tekst,
andere context, niet-uitgevoerde beoordeling) nooit als actueel bewijs; opslaan/
heropenen/statusovergang behoudt nieuwe beoordeling en kandidaat; deskundige
verwijzingsuitzondering vervalt na toevoegen van een link; P01-keten eindigt op
CON-02 `pass` met `reference_quality` uit de AI-beoordeling zonder uitzondering.

## UI-hertoetsstappen P01 (bestaand record 5)

1. Editor → record 5 openen. Expander **🔗 Bronmetadata aanvullen**: document
   `awb-1-3-20260815.txt` kiezen; hyperlink (P01-URL), bronversie `2026-08-15`,
   vindplaats `artikel 1:3 lid 1 Awb`; reviewer naam indien gevraagd; **Vastleggen**.
   Verwacht: succesmelding, versiebump, bronkaart toont url/versie/vindplaats met
   "Opgegeven bronmetadata (geen authenticiteitsbewijs) … door … op …", oude
   AI-beoordeling zichtbaar als niet meer geldend (bronnen gewijzigd).
2. Tekst exact P01 (ongewijzigd laten als al zo), **Valideren**: nieuwe beoordeling;
   verwijskwaliteit kan nu `voldoet` (echte DEF-806-regel; geen no-linkuitzondering).
3. Status **review**, **Opslaan**: melding "Bronbeoordeling van de laatste toetsing
   opgeslagen …". Expert Review / SQL-readback: `source_assessment.assessed_at` =
   nieuwe toetsing, `source_evidence.candidate.definitie` = exact P01,
   `sources[*].url/source_version/locator` gevuld, `declared_metadata` aanwezig,
   `source_evidence_history` bevat de oudere documenten.
4. Negatief: ongeldige link (`intern.example/awb`) → zichtbare afwijzing, niets
   geschreven; Valideren → verder bewerken → Opslaan → waarschuwing "niet
   opgeslagen: hoort niet bij de op te slaan kandidaat".
5. Uploadroute (nieuw document): Document Upload → selecteer → **🔗 Bronmetadata per
   geselecteerd document** → vastleggen → genereren: bronnen dragen url/versie/vindplaats.

## Buiten scope / open

- Expert Review "Hervalidatie" schrijft haar beoordeling nog alleen naar de sessie
  (zelfde patroon als het oude editorgedrag); niet in de geobserveerde keten, niet gewijzigd.
- `definitie_drafts` ontbreekt in `schema.sql` (autosave-melding): schemawijziging,
  apart issue.
- DEF-805 (sortering) niet geraakt.
