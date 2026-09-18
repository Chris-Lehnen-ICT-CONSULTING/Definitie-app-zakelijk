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
5. **Twee publicaties, in vaste volgorde.** Eerst het optionele rapport,
   exclusief (`O_CREAT|O_EXCL|O_NOFOLLOW`: nieuw bestand, nooit overschrijven,
   nooit een symlink volgen, modus 0600); faalt dat, dan bestaat er ook geen
   doel. Daarna het doel atomisch (`publish_staged_file`; weigert een bestaand
   doel). Faalt dát — om welke reden ook, ook `PermissionError`/`OSError` —
   dan meldt de route `herstel_publicatie_mislukt` en **blijft het rapport
   bewust staan** (detail `rapport_behouden`): de route verwijdert nooit iets
   op een pad buiten haar eigen werkmap, want een padnaam bewijst geen
   eigenaarschap. Vervolgens wordt de tijdelijke map opgeruimd. Het doel is
   een zelfstandig bestand (journal `DELETE`, bestandsmodus 0600 zoals elke
   backup van de helper).

**Wat het rapport betekent.** Het rapport bewijst uitsluitend een
*gecontroleerde momentopname*: alle controles (contract v3 → v8 → contract v4,
integrity, FK, volledige inhoudsvergelijking) zijn op de kopie geslaagd. Het
bewijst **niet** dat er een doel gepubliceerd of geactiveerd is: het veld
`publicatie_bevestigd` is altijd `false`, omdat het rapport vóór de
doelpublicatie wordt aangemaakt. Publicatie blijkt alleen uit exit 0 (of de
teruggegeven waarde) én het bestaan van het doelbestand. Een rapport zonder
doel is het eigen bewijsartefact van een mislukte poging; een nieuwe poging
vraagt een **nieuw rapportpad** (het oude wordt als bestaand geweigerd).

Wat de route **niet** doet: in-place migreren, een bestaand doel of rapport
overschrijven, waarden aanpassen of weggooien, ontbrekende definities
verzinnen, het contract versoepelen, of bij startup automatisch herstellen.
Onbekende varianten worden geweigerd (`herstel_onbekende_variant`), evenals
ongeldige enumwaarden, verweesde tags (`herstel_ongeldige_waarden`) en
tijdstempels die door de affiniteitswissel van waarde zouden veranderen
(`herstel_waarden_gewijzigd`).

**Bekende legacy-vorm = letterlijke, volledige DDL.** Een herstel-tabel wordt
alleen herbouwd als haar volledige `CREATE TABLE` — kop (gewone `CREATE
TABLE` met de tabelnaam), alle onderdelen (genormaliseerd, volgorde-
onafhankelijk) én alles ná de sluitende haak — gelijk is aan de gemeten
legacy-vorm in `LEGACY_DDL`, `PRAGMA table_xinfo` geen verborgen kolommen
toont en `pragma_table_list` een gewone rowid-tabel zonder `STRICT` meldt.
Een extra of `GENERATED`-kolom, een `COLLATE`, een ander declaratietype, een
andere `DEFAULT`, een kolom-`CHECK`, een `REFERENCES` of een tabeloptie
(`STRICT`, `WITHOUT ROWID`) maakt de tabel onbekend en de route weigert vóór
de herbouw — de PRAGMA-metagegevens van het contract zien generated
kolommen, collaties en tabelopties namelijk niet (Codex-reviews 1544296bc en
13da3e813: een `STRICT`-bron werd stil een niet-strict doel). Tabellen die de
route niet herbouwt komen ongewijzigd via de kopie mee; hun generated
kolommen tellen in de inhoudsvergelijking mee.

**Grenzen van de twee publicaties (eerlijk).** Rapport en doel zijn twee
bestanden op twee paden; ze verschijnen niet in één atomaire stap. De route
garandeert: nooit een doel zonder rapport als er een rapport gevraagd is;
nooit overschrijven van wat op een van beide paden staat of intussen
verschijnt (eindcomponent door de kernel gegarandeerd nieuw en geen symlink);
en nooit verwijderen van iets buiten de eigen werkmap. De keerzijde is
bewust: bij een mislukte doelpublicatie (of een schrijffout ná de exclusieve
aanmaak) blijft het rapportbestand — eventueel onvolledig — staan als eigen
bewijsartefact; het claimt nooit publicatie (`publicatie_bevestigd: false`).
Niet gedekt: een symlink die in een *bovenliggende map* van het rapport- of
doelpad verschijnt tussen de laatste padcontrole en de `open`/`link` (venster
van microseconden). Gebruik daarom paden in een map die alleen de beheerder
kan schrijven.

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
- De bron mag read-only zijn (bestandsmodus 0444 volstaat). De route leest
  technisch veilig naast een draaiende app (WAL-lezer met begrensde
  busy-timeout), maar **de kopie is een momentopname**: alles wat een
  schrijver ná het begin van de kopie commit, staat niet in het doel en de
  route kan dat niet zien. Voor een proefkopie is dat aanvaardbaar; voor de
  definitieve kopie die geactiveerd wordt niet — zie *Activeren*.
- `BRON`, `DOEL` en `--rapport` moeten drie verschillende, niet-bestaande
  (behalve de bron) en niet-gealiaste paden zijn; anders
  `herstel_doel_ongeldig`/`herstel_rapport_ongeldig` vóór enig werk.
- Het rapport bevat uitsluitend versies, objectnamen, aantallen en sha256-hashes.
- Herhaald gebruik met dezelfde bron en een nieuw doelpad geeft dezelfde
  tabelhashes; een v4-database is geen geldige bron (`herstel_precondition_failed`).

Bewijs van de proeven op een read-only kopie van de gebruikersdatabase
(18 september 2026): `/private/tmp/ess02-20260918-herstel/` —
`herstel-rapport*.json`, `proef-vergelijk*.json`, `stap*-herstel*.log`. Die
proefdoelen zijn momentopnamen van 18 september en worden **niet**
geactiveerd; de definitieve kopie wordt volgens de procedure hieronder
opnieuw gemaakt.

## Activeren (aparte, bewuste stap — niet door de route zelf)

De route publiceert alleen een nieuw bestand. Activering is een besluit van de
beheerder en gebeurt pas na onafhankelijke review en runtimeproef. Volgorde
is essentieel (Codex-review 1544296bc: een historierij die tijdens de route
werd gecommit, ontbrak in het doel terwijl de route succes meldde):

1. **Schrijvers stoppen vóór de definitieve kopie**: app stoppen en
   controleren dat niets `data/definities.db` open heeft (`lsof
   data/definities.db` leeg; `-wal` leeg of afwezig na een checkpoint).
   Schrijvers blijven gestopt tot en met stap 5.
2. **Nu pas de definitieve route draaien** (commando hierboven), met nieuw
   doel- en rapportpad. Eerdere proefdoelen niet hergebruiken: een kopie van
   eerder is per definitie ouder dan de bron. Wil je tóch een bestaand doel
   activeren, controleer eerst de versheid — de volledige inhoudsvergelijking
   van de route tegen de huidige bron moet leeg zijn:

   ```bash
   PYTHONPATH=src .venv/bin/python - <<'EOF'
   from pathlib import Path
   from database.migrations.schema3_herstel import HerstelRapport, vergelijk_bron_en_doel
   from database.sqlite_backup import open_readonly_snapshot
   bron, doel = open_readonly_snapshot(Path("data/definities.db")), open_readonly_snapshot(Path("PAD/NAAR/DOEL.db"))
   rapport = HerstelRapport(3, 4, nieuwe_tabellen=["definitie_geschiedenis_verweesd", "externe_bronnen"])
   problemen = vergelijk_bron_en_doel(bron, doel, rapport)
   print("vers" if not problemen else problemen)
   EOF
   ```

   Elke melding (bijv. `gekoppelde geschiedenis wijkt af van de bron`)
   betekent: niet activeren, route opnieuw draaien met gestopte schrijvers.
3. Het origineel bewaren als rollback (bijv. `data/definities-v3-<datum>.db`,
   inclusief `-wal`/`-shm` als die niet leeg zijn; of via
   `python -m database.sqlite_backup`). **Niet verwijderen.**
4. Het gepubliceerde doel op `data/definities.db` zetten (verplaatsen, niet
   kopiëren over het origineel heen; de app opent uitsluitend
   `data/definities.db` — projectregel, geen omgevingsvariabele). Geen
   `-wal`/`-shm` van het origineel laten staan naast het nieuwe bestand.
5. Starten: `assert_startup_contract` moet slagen (versie 4). Faalt dat, dan
   het origineel terugzetten — de route heeft het origineel nooit geschreven.
   Pas hierna mogen schrijvers weer werken.

Dit is een expliciete, stilgelegde overgang voor een lokale app met één
gebruiker; er is bewust geen synchronisatie van wijzigingen die tijdens de
route zouden plaatsvinden.

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
| `herstel_rapport_ongeldig`               | het `--rapport`-pad bestaat al, is geen veilig nieuw pad, of is een alias van doel (`report_is_destination`) of bron (`report_is_source`) |
| `herstel_rapport_mislukt`                | bij de exclusieve aanmaak verscheen er intussen iets op het rapportpad (bestand/symlink) of de map verdween (niets aangemaakt), óf het schrijven faalde ná de aanmaak (detail `rapport_behouden`: het onvolledige bestand blijft staan); er is dan geen doel gepubliceerd |
| `herstel_kopie_geweigerd`                | de DEF-663-kopie weigerde (bron ontbreekt, symlink, integriteit, timeout) |
| `herstel_precondition_failed`            | bron niet op versie 3, of resttabellen (`*_old`, bewaartabel) aanwezig |
| `herstel_onbekende_variant`              | een herstel-tabel is noch canoniek, noch letterlijk de bekende legacy-vorm (extra/generated kolom, collatie, ander type, andere DEFAULT, kolom-CHECK, FK) |
| `herstel_ongeldige_waarden`              | CHECK/NOT NULL/UNIQUE-schending bij de kopie, of verweesde tags |
| `herstel_waarden_gewijzigd`              | een waarde of type zou door de canonieke affiniteit veranderen |
| `herstel_rijen_verloren`                 | gekoppeld + bewaard ≠ brontotaal (interne bewaking)    |
| `migration_target_contract_failed`       | contract v3 (na herstel) of v4 (eindcontrole) niet gehaald |
| `herstel_v8_mislukt`                     | de bestaande v8-route weigerde (zie v8-log)            |
| `herstel_gegevensvergelijking_mislukt`   | bron en doel zijn niet inhoudelijk gelijk              |
| `herstel_publicatie_mislukt`             | doelpublicatie faalde: doel verscheen intussen, werd een symlink, of de `link` gaf een `PermissionError`/`OSError` (alleen de foutklasse wordt gemeld). Detail `rapport_behouden` als er een rapport was: dat blijft staan, geen doel |

Tests: `tests/unit/database/test_schema3_herstel.py`.
