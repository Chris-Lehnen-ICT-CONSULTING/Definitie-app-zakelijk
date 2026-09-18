claude-run5.jsonl

LOW verwerkt; alleen de melding (en de daaraan gekoppelde docstringclaim in dezelfde methode) gewijzigd.

## Wijziging (1 bestand: `src/document_processing/document_processor.py`, +11/−7)

- `BronmetadataOpslagError`-melding in `set_source_metadata` beloofde "de eerdere opgave blijft gelden" (impliciet ook op schijf). Nu: *"… kon niet worden geschreven; de nieuwe opgave is in het geheugen teruggedraaid (de eerdere opgave blijft in deze sessie gelden), controleer het metadata-bestand"* — uitsluitend herstel in het geheugen, geen garantie over de schijf.
- De docstringzin "geheugen en schijf blijven gelijk" in dezelfde methode maakte dezelfde claim; aangepast naar "over de toestand van het bestand op schijf wordt niets beloofd". Commentaar bij de rollback benoemt de ENOSPC/afkap-oorzaak (niet-atomaire schrijver).
- Geen atomaire-opslagrefactor, geen andere wijzigingen. Gekoppelde stringassertie: de test matcht op `"niet opgeslagen"` — nog aanwezig in de nieuwe melding, dus geen testaanpassing nodig (gecontroleerd via grep op "eerdere opgave blijft" / "blijft gelden" in `tests/`: geen koppeling).

## Resultaten

- Gerichte tests (`tests/unit/document_processing`, `tests/unit/domain/test_def808_bronmetadata.py`, `tests/unit/ui/test_def808_809_editor_ui.py`): **56 passed in 1.06s**.
- `ruff check src/document_processing/document_processor.py`: *All checks passed!*
- `black --check src/document_processing/document_processor.py`: *1 file would be left unchanged*.

Geen commit; werkboom bevat alleen deze delta ten opzichte van `d6be2ccd`.

claude-run6.jsonl

Bug hersteld en met een échte Streamlit `AppTest` geborgd (RED → GREEN).

## Oorzaak (bevestigd)

Precies het vermoeden: in `_render_bronmetadata_section` werd het naamveld (`edit_bronmeta_reviewer_name_input`) alleen gerenderd als `_handelende_gebruiker()` géén actor vond — en die lookup las het eigen widget. Rerun 2 (na naam + Tab): actor gevonden → widget niet gerenderd → Streamlit ruimt de sessiewaarde op aan het eind van die run. Rerun 3 (URL + Tab): actor leeg, veld terug/leeg, knop disabled. RED-waarnemingen op de oude code (`apptest-red-c18a7ec3-waarnemingen.json`): `na_naam: naamveld_aanwezig False, naam_sessie None` → `na_url: naam_widget '', knop_disabled True`.

## Fix (`src/ui/components/definition_edit_tab.py`, +38/−13, geen overige wijzigingen)

- Nieuw `_bekende_gebruiker()` = bestaande identiteitsbronnen (`user`, `edit_reviewer_name_input`, `reviewer_name_input`) zónder het eigen naamveld; `_handelende_gebruiker()` = bekende gebruiker, anders het naamveld (gedrag voor de voorstelsectie ongewijzigd).
- De sectie rendert het naamveld nu **altijd zolang er geen bestaande identiteit is** (conditie op de andere bronnen, nooit op de eigen waarde) en leest de actor uit de widgetwaarde. Een bestaande `user` wordt nooit vervangen: dan geen naamveld.

## Uploadroute onderzocht

`_render_bronmetadata_invoer` rendert zijn velden onvoorwaardelijk per geselecteerd document en leest de identiteit alleen uit `user` — geen widget dat van zijn eigen waarde afhangt, dus **niet** dezelfde fout. Aangetoond in dezelfde AppTest (velden blijven over drie reruns staan; opgave op schijf).

## Regressie (echte AppTest, `tests/unit/ui/test_def808_bronmetadata_apptest.py`, subprocess-driver achter offline-gate, 5 tests)

Echte reruns: render → naam invullen + rerun → URL + rerun → versie/vindplaats + reruns → klik. GREEN-waarnemingen: `na_naam`/`na_url`/`na_alles`: naamveld aanwezig, `naam_widget == naam_sessie == "Reviewer Rood"`, knop na URL enabled; vastleggen `applied`, versie 2, `declared_by == ["Reviewer Rood", "Reviewer Rood"]`; met `user` gezet: geen naamveld, `declared_by`/`updated_by == "Ingelogde Gebruiker"`; upload: velden behouden, opgave op schijf. Op de oude code faalden 2 van 5 (naamveld verdwenen, niets vastgelegd).

## Resultaten

- `test_def808_bronmetadata_apptest.py` + `test_def808_809_editor_ui.py` + `test_def743_editor_ui.py` + `test_def743_editor_apptest.py` + `test_def808_upload_bronmetadata.py`: **71 passed in 13.10s**.
- ruff (`definition_edit_tab.py`, nieuwe test): *All checks passed*; black: *2 files would be left unchanged*.
- Nieuw bewijs in `docs/analyses/def808-809-uitvoering-20260918-v1/`: `apptest-red-c18a7ec3-waarnemingen.json`, `apptest-green-waarnemingen.json`.

Observatie buiten scope (niet gewijzigd): de bestaande voorstelsectie (`_render_voorstel_section`, DEF-743) gebruikt hetzelfde conditionele patroon op `edit_reviewer_name_input` en heeft daardoor dezelfde latente rerun-cleanup. Geen commit gedaan.