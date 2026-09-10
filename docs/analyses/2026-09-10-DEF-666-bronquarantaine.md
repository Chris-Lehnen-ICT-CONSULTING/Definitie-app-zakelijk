# Bronquarantaine — onderhoudsdocument (DEF-666)

Gebruiksdocument voor onderhouders: wat er is uitgeschakeld, wat er bewust
werkend blijft, hoe je het controleert en wat er nodig is om iets weer aan te
zetten. Normatief zijn het manifest `scripts/ci/quarantine_manifest.json` en het
anker in `scripts/ci/quarantine_guard_check.py`; dit document beschrijft ze en
overrulet er niets van.

## Waarom

De inventaris bevatte 49 onderhoudstools met destructieve acties: bestanden
verplaatsen en verwijderen, documentatie herschrijven, git-branches wisselen,
`DROP TABLE`, `DELETE FROM` en het overschrijven van de live database. Meerdere
scripts wijzen bovendien naar een hardcoded pad van de echte werkkopie. De
risicovolle acties waren aanroepbaar — één ervan zelfs automatisch via een
pre-commit-hook. De acties zijn daarom **bij de bron**
uitgeschakeld, niet alleen bij de aanroepers.

## Scope: 49 paden in vier groepen

| Groep | Aantal | Blokkadevorm |
|---|---|---|
| `python_module` | 33 | Eerste uitvoerbare statement, ná docstring en `from __future__`: `raise RuntimeError("DEF-666-QUARANTINE-GUARD: <pad> …")` met één stringconstante |
| `shell` | 14 | Direct na de shebang: een vaste `printf` naar stderr, dan `return 92 2>/dev/null \|\| exit 92` |
| `make` | 1 | Eerste betekenisvolle regel op kolom 0: `$(error DEF-666-QUARANTINE-GUARD: … )` |
| `backup_actions` | 1 | Gemengd, zie hieronder |

Bij de 48 volledig geblokkeerde bestanden ligt de blokkade vóór de
oorspronkelijke code: elke import-, CLI-, shell-, source- en wrapperroute stopt
daar. De oude code is bewust blijven staan en is nu onbereikbaar; er is niets
verwijderd. De `$(error …)` in de Make-wrapper wordt al bij het *inlezen*
geëxpandeerd, dus ook `-n`, `-q` en een `include` vanuit een andere Makefile
falen.

De shellblokkade werkt in beide richtingen: gesourcet beëindigt `return` het
script zonder de aanroepende shell te doden, en bij directe uitvoering springt
`exit 92` bij. Let op dat de aanroeper daarna gewoon op 0 kan eindigen; de
status ván het sourcen is 92.

## Wat blijft werken

`scripts/backup_restore.py` is gemengd en blijft gewoon importeerbaar:

- **Behouden:** `create_backup`, `verify_backup`, `list_backups`, de constructor
  en alle veilige helpers, plus de CLI-acties `backup`, `list` en `verify`. De
  26 bestaande DEF-663-tests blijven ongewijzigd geldig en gelden als het
  positieve bewijs.
- **Geblokkeerd:** `restore_backup` en `clean_old_backups` weigeren
  onvoorwaardelijk als eerste statement na hun docstring, en de CLI wijst
  `restore` en `clean` af direct na `parse_args()` — dus vóór het aanmaken van
  `logs/`, vóór de backupmap en vóór de constructor.
- De logbestandconfiguratie is naar `main()` verplaatst: importeren schrijft
  niets meer.

Er is geen vlag, omgevingsvariabele of scope-optie waarmee een gevaarlijke
actie alsnog vrijgegeven kan worden.

## Commando's

```bash
make quarantine-check    # integriteitspoort: leest en hasht, voert niets uit
make test-tool-gates     # o.a. de twee stdlib-suites van DEF-666
make test                # bevat de backup-unittests
```

De pre-commit-hook `quarantine-source-integrity` draait dezelfde checker met
`python3 -I -B`, `always_run: true` en `pass_filenames: false`.

## Het anker: huidige én historische hashes

Het manifest staat op `version: 2` en houdt per pad twee metingen bij:

- `sha256` / `size_bytes` — de gereviewde **geblokkeerde** bytes zoals ze nu in
  de repository staan;
- `original_sha256` / `original_size_bytes` — de **oorspronkelijke
  inventarismeting**, bewaard voor herleidbaarheid.

`review_source_commit` is uitsluitend de herkomst van `risk` en `findings`.
`allowed_contexts` is historisch reviewbewijs: het pint de destijds beoordeelde
DEF-663-testbytes en geeft géén aanroep vrij.

De checker verankert het **hele geparste manifest** in één canonieke
SHA256-constante in zijn eigen bron. Wie een bronbestand wijzigt en netjes de
bijbehorende hash in het manifest bijwerkt, komt er dus nog steeds niet
doorheen: bestand en manifest kloppen dan onderling, maar het manifest wijkt af
van het gereviewde anker.

## Iets weer aanzetten

Een tool weer in gebruik nemen, hardenen, hernoemen of verwijderen vergt een
**aparte, gereviewde issue** die bron, manifest en checker-anker in dezelfde
wijziging aanpast. Losse aanpassingen worden per definitie geblokkeerd. Ongebruikte
acties blijven uit tot dat werk gedaan is.

## Grenzen — wat dit niet is

- **Geen bereikbaarheidsanalyse.** De checker leest en hasht; hij voert nooit
  een geïnspecteerd bestand uit en bouwt geen callgraph.
- **De scan van actieve configuratie is eindig en letterlijk.** Alleen de
  geregistreerde `.pre-commit-config.yaml`, `Makefile` en de YAML-bestanden
  onder `.github/workflows/` worden gecontroleerd op letterlijke padverwijzingen
  en exacte gepunte modulevormen. Dynamisch berekende namen worden niet
  gecertificeerd; de **bronblokkades** zijn de primaire bescherming, niet deze
  scan.
- **De 24 onopgeloste plaatsen van de oude analyzer worden hiermee niet groen
  verklaard.** Dat bewijsmateriaal blijft gearchiveerd en onaangetast; deze
  aanpak vervangt die claim, hij lost hem niet op.

## Bewijs

- `scripts/ci/test_quarantine_guard_check.py` — de 49 inventarisidentiteiten en
  de exacte guardvorm en het gedrag van de 48 volledig geblokkeerde bestanden;
  voert alleen verse kopieën uit, en uitsluitend
  nadat een statische voorwaarde de blokkade heeft aangetoond.
- `scripts/ci/test_quarantine_integrity.py` — manifest, hashes, symlinks en
  heringevoerde automatische ingangen.
- `tests/unit/scripts/test_backup_restore_def666.py` — de methode- en
  CLI-grenzen van het gemengde bestand.
- `tests/unit/scripts/test_backup_restore_script.py` — de 26 bestaande
  DEF-663-tests, byte-identiek bewaard.

*Versie 1.0 · 10 september 2026 · DEF-666*
