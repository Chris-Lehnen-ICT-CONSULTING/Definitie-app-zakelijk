# Schema-3-herstel naar een nieuwe v4-database (DEF-751)

> Beheerinstructie voor `src/database/migrations/schema3_herstel.py`.
> Context: ESS-02 lokale activering was geblokkeerd omdat de bestaande
> gebruikersdatabase versiemarker 3 draagt maar niet aan het schema-3-contract
> voldoet; v8 en de legacy-route weigeren die bron terecht.

## Wat de route doet

`BRON` (read-only) → nieuw `DOEL` op schemaversie 4, in vijf stappen die elk
fail-closed zijn; bij elke fout bestaat `DOEL` niet en is `BRON` onaangeroerd.

1. **Geverifieerde kopie** van de bron (DEF-663-contract, `create_verified_backup`,
   URI `mode=ro`, WAL-veilig) in een eigen tijdelijke map naast het doel.
2. **Herstel van de bekende afwijkingen** op die kopie, in één transactie:
   - `definitie_geschiedenis`, `definitie_tags`, `import_export_logs`: herbouwd
     naar de canonieke DDL uit `schema.sql` (FK's, CHECKs, TIMESTAMP-affiniteit);
     ids, alle kolommen, eigen indexen en de autoincrement-tellers blijven;
   - geschiedenisrijen zonder bestaande definitie → bewaartabel
     `definitie_geschiedenis_verweesd` (zie onder);
   - ontbrekende `externe_bronnen`, de vier `definities`-indexen, de triggers
     `update_definities_timestamp`/`log_definitie_changes` en de drie views
     worden uit `schema.sql` aangemaakt;
   - daarna moet het **volledige schema-3-contract** slagen (`verify_target_contract(3)`).
3. **Bestaande v8-migratie** (`definities.categorie` optioneel, versie 4).
4. **Volledige inhoudsvergelijking** bron ↔ doel vóór publicatie: elke brontabel
   rij-voor-rij gelijk (waarde én `typeof`), geschiedenis exact gesplitst
   (gekoppeld + bewaard = bron), `schema_version` = bron + {4}, elke
   `sqlite_sequence`-teller gelijk (`schema_version` +1), contract v4,
   `integrity_check`, `foreign_key_check`.
5. **Atomische publicatie** (`publish_staged_file`; weigert een bestaand doel) en
   opruimen van de tijdelijke map. Het doel is een zelfstandig bestand
   (journal `DELETE`, bestandsmodus 0600 zoals elke backup van de helper).

Wat de route **niet** doet: in-place migreren, een bestaand doel overschrijven,
waarden aanpassen of weggooien, ontbrekende definities verzinnen, het contract
versoepelen, of bij startup automatisch herstellen. Onbekende varianten worden
geweigerd (`herstel_onbekende_variant`), evenals ongeldige enumwaarden,
verweesde tags (`herstel_ongeldige_waarden`) en tijdstempels die door de
affiniteitswissel van waarde zouden veranderen (`herstel_waarden_gewijzigd`).

## Uitvoeren

```bash
cd <checkout>
PYTHONPATH=src .venv/bin/python -m database.migrations.schema3_herstel \
    data/definities.db \
    data/definities-v4.db \
    --rapport docs/analyses/herstel-rapport-$(date +%Y%m%d).json
```

- Exit 0 = gepubliceerd; exit 1 = geweigerd, met een veilige reden op stderr
  (`schema3_herstel: <reason>: <details>`), zonder rijinhoud.
- De bron mag read-only zijn (bestandsmodus 0444 volstaat) en mag door de app
  in gebruik zijn (WAL-lezer met begrensde busy-timeout).
- Het rapport bevat uitsluitend versies, objectnamen, aantallen en sha256-hashes.
- Herhaald gebruik met dezelfde bron en een nieuw doelpad geeft dezelfde
  tabelhashes; een v4-database is geen geldige bron (`herstel_precondition_failed`).

Bewijs van de proef op de gebruikersdatabase (18 september 2026):
`/private/tmp/ess02-20260918-herstel/` — `herstel-rapport.json`,
`proef-vergelijk.json`, `stap2-herstel.log`.

## Activeren (aparte, bewuste stap — niet door de route zelf)

De route publiceert alleen een nieuw bestand. Activering is een besluit van de
beheerder en gebeurt pas na onafhankelijke review en runtimeproef:

1. App stoppen (geen open schrijvers op `data/definities.db`).
2. Het origineel bewaren als rollback (bijv. `data/definities-v3-<datum>.db`,
   inclusief `-wal`/`-shm` als die niet leeg zijn; of de kopie uit stap 1 van
   de route via `python -m database.sqlite_backup`). **Niet verwijderen.**
3. Het gepubliceerde doel op `data/definities.db` zetten (verplaatsen, niet
   kopiëren over het origineel heen; de app opent uitsluitend
   `data/definities.db` — projectregel, geen omgevingsvariabele). Geen
   `-wal`/`-shm` van het origineel laten staan naast het nieuwe bestand.
4. Starten: `assert_startup_contract` moet slagen (versie 4). Faalt dat, dan
   het origineel terugzetten — de route heeft het origineel nooit geschreven.

De gewone `.env`, `.venv` en uploads (`rag_documents.file_path`) blijven
bruikbaar: de route wijzigt geen paden, sleutels of bestanden buiten het doel.

## De bewaartabel `definitie_geschiedenis_verweesd`

Duurzaam onderdeel van de doeldatabase. Bevat élke oorspronkelijke
geschiedenisrij waarvan `definitie_id` bij herstel geen bestaande definitie
had — met de **originele `id`**, de **originele `definitie_id`** en alle
overige kolommen letterlijk (brondeclaraties: `TEXT`, dezelfde NOT NULL/
DEFAULT), zonder foreign key, plus:

| Kolom          | Betekenis                                             |
|----------------|-------------------------------------------------------|
| `bewaar_reden` | vaste code `definitie_ontbreekt`                      |
| `bewaard_door` | vaste code `DEF-751 schema3_herstel`                  |
| `bewaard_op`   | tijdstip van herstel (`CURRENT_TIMESTAMP`)            |

Raadplegen:

```sql
-- alles wat bij een verdwenen definitie hoorde
SELECT * FROM definitie_geschiedenis_verweesd WHERE definitie_id = ? ORDER BY id;

-- de volledige oorspronkelijke geschiedenis (gekoppeld + bewaard), op id
SELECT id, definitie_id, begrip, wijziging_type, gewijzigd_op, 'gekoppeld' AS bron
  FROM definitie_geschiedenis
UNION ALL
SELECT id, definitie_id, begrip, wijziging_type, gewijzigd_op, 'bewaard'
  FROM definitie_geschiedenis_verweesd
ORDER BY id;
```

De ids van beide tabellen zijn disjunct (het zijn de oorspronkelijke ids);
`sqlite_sequence` van `definitie_geschiedenis` is niet teruggezet, dus nieuwe
geschiedenisrijen botsen nooit met bewaarde.

## Foutcodes

| Reason                                   | Betekenis                                              |
|------------------------------------------|--------------------------------------------------------|
| `herstel_doel_ongeldig`                  | doel bestaat, symlink in het pad, bron = doel, map ontbreekt |
| `herstel_rapport_ongeldig`               | het `--rapport`-pad bestaat al of is geen veilig nieuw pad |
| `herstel_kopie_geweigerd`                | de DEF-663-kopie weigerde (bron ontbreekt, symlink, integriteit, timeout) |
| `herstel_precondition_failed`            | bron niet op versie 3, of resttabellen (`*_old`, bewaartabel) aanwezig |
| `herstel_onbekende_variant`              | een herstel-tabel is noch canoniek, noch de bekende legacy-vorm |
| `herstel_ongeldige_waarden`              | CHECK/NOT NULL/UNIQUE-schending bij de kopie, of verweesde tags |
| `herstel_waarden_gewijzigd`              | een waarde of type zou door de canonieke affiniteit veranderen |
| `herstel_rijen_verloren`                 | gekoppeld + bewaard ≠ brontotaal (interne bewaking)    |
| `migration_target_contract_failed`       | contract v3 (na herstel) of v4 (eindcontrole) niet gehaald |
| `herstel_v8_mislukt`                     | de bestaande v8-route weigerde (zie v8-log)            |
| `herstel_gegevensvergelijking_mislukt`   | bron en doel zijn niet inhoudelijk gelijk              |
| `herstel_publicatie_mislukt`             | doel verscheen intussen of werd een symlink            |

Tests: `tests/unit/database/test_schema3_herstel.py`.
