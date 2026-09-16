# DEF-751 B1 — categoriekeuze verliesvrij door editor, generatie en CSV-import

Datum: 16 september 2026. Basis: main bceb6ab80a930a2403b51de9a0312880de527f97.
Werkboom: /private/tmp/DEF-751-ess02-categorie-20260916. Branch: feature/DEF-751-ess02-categorie.

Leidend: [DEF-751](https://linear.app/definitie-app/issue/DEF-751) en de [vastgestelde ESS-02-besluiten](https://linear.app/definitie-app/document/ess-02-vastgestelde-besluiten-en-implementatieafbakening-6e9459c232e0). B1 is het deel dat zonder gedeelde opslagvoorzieningen (DEF-626/627) kan: geen crash, geen stille omzetting, geen verzonnen categorie. Herkomst/actor/tijd/versie van een keuze (B2) is niet geleverd en wordt nergens geclaimd. Prompts, regelbeleid, schema, orchestrator en repository zijn niet gewijzigd; ESS-01/CON-01/CON-02 blijven zoals in DEF-746/747/743.

## Bevindingen op de basis
- Editor (`definition_edit_tab.py:605-613`): vier keuzes, `list.index(definition.categorie or "proces")`; een record met een schemawaarde buiten de vier (ENT/ACT/REL/ATT/AUT/STA/OTH, `schema.sql:21-32`) gaf `ValueError` en de hele Bewerk-tab viel om. De selectbox volgde bovendien het alleen-lezenbeleid (`disabled`) van de andere velden niet.
- Generatiehandler (`definition_generation_handler.py:153-155,190-197`): `category_map.get(…, OntologischeCategorie.PROCES)` voor handmatige keuze én modelvoorstel — elke waarde buiten de vier werd stil PROCES, ook richting duplicaatvoorcontrole (`zoek_gelijke_context` matcht op categorie) en model.
- CSV-import (`csv_importer.py:208`): ontbrekende categorie werd `"Type"`; die faalt de CHECK (hoofdlettergevoelig) → rij verloren met een cryptische `CHECK constraint failed`-melding; `"entiteit"` idem. Bestaande tests zagen dit niet (Mock-repository).
- `DefinitionImportService._payload_to_definition` (stil `"type"`, synoniemmapping) heeft geen actieve caller in `src/`; ongewijzigd, zie B2.

## Gedragskeuzes B1
1. Editor: opties = vier standaardkeuzes + de geladen waarde als die daar niet in zit (exact, achteraan); label via de bestaande `get_category_display_name` met "bestaande waarde — ongewijzigd" (geen herkomstclaim, dus niet "historisch"). Ontbrekende waarde → lege optie "— geen categorie —" vooraan; een lege keuze wordt bij opslaan `None` zodat `_definition_to_updates` de kolom overslaat. Alleen-lezen (`established`/`archived`) → `disabled`, zoals de overige velden. Validatiekandidaat zonder widgetwaarde gebruikt de geladen categorie, niet "proces".
2. Handler: `generatiecategorie_van()` herkent uitsluitend de vier enumwaarden (kastongevoelig). Anders: begrijpelijke `st.error` met de aangetroffen waarde en de vier geldige keuzes, `logger.warning`, eenmalige force-opties verbruikt (regel DEF-622 D3), `return` vóór checker en model. Geldige keuze reist exact door; de bestaande "niet bepaald"-gate en de reasoning/scores-sessie-informatie blijven ongewijzigd.
3. CSV-import: rij zonder categorie of met een waarde die geen exacte schemawaarde is → gemeld ("Rij N: niet opgeslagen — … de definitie zelf is niet inhoudelijk beoordeeld of afgekeurd, maar de opslag kan een definitie zonder geldige categorie nog niet bewaren") en overgeslagen; geen default, geen synoniemmapping. Elf schemawaarden worden exact bewaard. Foutentelling blijft zichtbaar in de expander (geen verborgen rijverlies).
4. Gedeelde bron: de elf opslagwaarden staan al in `definition_formatter_utils.get_category_display_name`; die tabel is als `CATEGORY_DISPLAY_NAMES` ontsloten en door `ui/helpers/categorie_weergave.py` hergebruikt — geen tweede lijst.

## Bestanden
- Nieuw: `src/ui/helpers/categorie_weergave.py`; tests `tests/unit/ui/helpers/test_def751_categorie_weergave.py`, `tests/unit/ui/test_def751_editor_categorie.py`, `tests/unit/ui/handlers/test_def751_categorie_gate.py`, `tests/unit/ui/test_def751_csv_import_categorie.py`.
- Gewijzigd: `definition_edit_tab.py`, `definition_generation_handler.py`, `csv_importer.py`, `definition_formatter_utils.py`; fixtures in `test_csv_import_hardening.py` en `test_import_export_repository_contract.py` kregen een geldige `categorie`-kolom (zij toetsen andere invarianten; zonder kolom worden hun rijen nu — terecht — gemeld en overgeslagen).

## Bewijs (TDD)
- RED: 23 failed + collectiefout op de nog niet bestaande helper (`b1-red.txt`); GREEN: 55 passed (`b1-green.txt`); gerichte regressie 243 passed (`b1-regressie-gericht.txt`); `make lint` en `make test` volgens `b1-make-*.txt`.
- Editor: `_render_editor` op een tmp-SQLite-record met ACT/ENT rendert zonder `ValueError`, selectbox op exact die waarde; openen + tekstwijziging + `_save_definition` → nieuwe `DefinitionRepository`- én `DefinitieRepository`-instantie lezen ACT/ENT/resultaat ongewijzigd terug; lege widgetwaarde overschrijft "type" niet; `established`/`archived` → `disabled=True`.
- Handler: ENT/Kind als handmatige keuze of voorstel → één foutmelding, checker en `generate_definition` niet aangeroepen, force-opties gewist; TYPE/exemplaar/RESULTAAT/type reizen exact als enum naar `check_before_generation`.
- CSV op tmp-SQLite: ontbrekend, `"Type"`, `"entiteit"` → drie precieze meldingen zonder `CHECK constraint`; `ENT` en `resultaat` bewaard; elke schemawaarde afzonderlijk exact bewaard.

## B2-gaps (expliciet niet geleverd)
- Herkomst/actor/tijd/kandidaat-/recordversie van een categoriekeuze: `GenerationRequest` heeft geen herkomstveld, `DefinitieRecord` geen herkomstkolom; `category_reasoning`/`category_scores` blijven sessie-informatie. Vereist DEF-626-levering of een schema-/JSON-veldbesluit (owner benoemen).
- Labelvrij opslaan (definitie zonder categorie) is onmogelijk door `NOT NULL` + CHECK; de CSV-melding benoemt dit als technische grens. Repositorydefault `"proces"` (`definition_repository.py:765-771`) voor `categorie=None` uit niet-UI-callers en `DefinitionImportService._normalize_categorie` (dode route, stil `"type"`) blijven staan tot dat besluit.
- Bulk-/massaherclassificatie van bestaande records: bewust niet.
