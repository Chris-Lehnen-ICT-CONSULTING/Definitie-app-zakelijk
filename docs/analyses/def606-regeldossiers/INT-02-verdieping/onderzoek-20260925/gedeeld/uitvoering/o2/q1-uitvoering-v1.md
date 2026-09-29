# DEF-835 — Q1 offline kwalificatierunner, uitvoeringsverslag v1

28 september 2026 · uitvoerder: Claude Code CLI (Opus 5.5), inclusief correcties F1–F3 na de Codex-review (`q1-codex-review-v1.md`). Basis `f9bb9e6973926a3cf768995f5d879f6edfd6322d`, branch `feature/DEF-835-int02-o2`. Er zijn geen livecalls of tokenmetingen gedaan, geen productiedata gebruikt en niets gestaged, gecommit of gepusht. De map goldset-voorbereiding/ is niet gelezen.

## Gewijzigde bestanden (scope Q1)

| Bestand | Status | SHA-256 na correctie |
| --- | --- | --- |
| `scripts/analysis/def835_int02_modelproef.py` | gewijzigd (+1127/−57 t.o.v. basis) | `af59b9e0e2d86d29442a4e17865f8dc42c272ba11cb30e4fcd9ea3f5962373ab` |
| `tests/unit/validation/test_def835_int02_modelproef.py` | gewijzigd (+1287, niets verwijderd) | `111a4ef8b478bc8557806904929426bf2936cac03ca912912cd4f94de81e7eb3` |
| `tests/fixtures/def835_int02_kwalificatie_runner.json` | nieuw, alleen technisch | `2f50c456756614cc35e78b81f57f4c8afc748b79d4cfcd6da053306e6c8fd7a7` |

De raming van 250–450 regels is ruim overschreden. Die raming gold niet als maximum. De omvang komt vooral uit het grootboek, de gevallenmanifestvalidatie, de fase-evaluatie en de tests.

## Gekozen interface

- **Driecasusmodus** is ongewijzigd: dezelfde `voorbereid`/`voer_live_uit`, hetzelfde akkoordtype en dezelfde identiteitsvorm (test `test_driecasusmodus_identiteitsvorm_ongewijzigd`).
- **Kwalificatieprofiel** `def835-kwalificatieproef-opus5-v1`, met limieten 43 inferenties en 43 tokenmetingen, 16.000 in en 6.000 uit per call, 120 s per call, 6.000 s cumulatief en US$12 cumulatief.
  - Voorbereiding: `voorbereid_kwalificatie(gevallen, proefmap, manifest)`, of via de CLI met `--kwalificatie G --proefmap P --manifest M`. Die draait offline als dry-run door de echte keten. De proefmap wordt daarbij niet aangemaakt.
  - Uitvoering: `voer_kwalificatie_uit(manifest, akkoord, gevallen, fase)`, of via de CLI met `--live --kwalificatie G --manifest M --akkoord A --fase F`. Elke run voert precies één fase uit; er is geen automatische overgang.
- **Gevallenmanifest** `def835-int02-kwalificatie-gevallen/1`. De runner eist:
  - een freeze-blok (`bevroren`, acceptant, ISO-datum en bron);
  - protocol-SHA `53a199…f18f`;
  - de vlaggen `goldset` en `technische_testfixture`, waarvan precies één waar is;
  - de splitsing 3/24/16, met regressie exact C105/C107/C112 met invoer en status uit de ontwerpfixture;
  - een hold-outverdeling van exact 4 fail, 8 pass en 4 review_required.

  Labels gaan nooit in een request.
- **Identiteit** bindt invoer-, label- en payloadhash per geval, de splitsing, de criteria, het protocol, prompt/norm/T, de router, het transport, de bronbestanden, de versies, de proefmap en de SHA van het gevallenmanifest.
- **Akkoord** `def835-int02-kwalificatie-akkoord/1` heeft 13 exacte velden, met daarin de manifest-, gevallen- en protocol-SHA en expliciet 43/43/US$12. Een oud driecallakkoord of -manifest wordt geweigerd.
- **Grootboek** `proefmap/grootboek.jsonl` is alleen-toevoegend en wordt per regel gefsynct.
  - Tel- en inferentiereserveringen staan erin vóór het transport.
  - Een call zonder betrouwbare boeking telt voor de volle reservering.
  - Een open fase blokkeert alles (`grootboek_open`). Er is bewust geen hervatfunctie.
- **Weigercodes** gaan in alle gevallen aan transport vooraf: `akkoord_ontbreekt`, `akkoord_ongeldig`, `identiteit_gewijzigd`, `testfixture_niet_live`, `fasevolgorde`, `fase_al_uitgevoerd`, `proefmap_bestaat`, `proefmap_in_gebruik`, `calllimiet_ontoereikend`, `budget_ontoereikend` en `looptijd_ontoereikend`.
- **Evaluatie** is mechanisch en vergelijkt alleen de hoofdstatus. Tellers met teller en noemer staan per protocol §2 in het resultaat. `inhoudelijke_beoordeling` staat altijd op `open` (Chris); de runner vult geen akkoord in.

Interpretatiekeuzes:
- Een kritieke false-pass (fail→pass) stopt direct.
- Een review_required→pass stopt niet, maar laat de hold-out falen.
- De regressiefase maakt haar drie calls af en blokkeert daarna de volgende fase.

## Correcties na review (alle drie: fix nu)

- **F1 — exclusief processlot.**
  - `fcntl.flock` (stdlib) op `proefmap/grootboek.slot` wordt genomen vóór het lezen en beoordelen van de actuele stand. De toelaatbaarheid en de cumulatieve ruimte worden onder het slot opnieuw getoetst.
  - Het slot blijft vast tot en met de bewijsopslag en `fase_einde`. Een tweede uitvoerder krijgt `proefmap_in_gebruik` vóór enig transport.
  - De eerste fase maakt de proefmap exclusief aan (`mkdir`, niet bestaand). Het slotbestand blijft staan; het OS geeft het slot vrij als het proces eindigt.
  - Tests:
    - een echt tweede proces (`subprocess`) houdt het slot vast, waarna de run 0 requests doet en de administratie ongewijzigd blijft;
    - een onafhankelijke descriptor ziet het slot bezet bij elk transport en tijdens de bewijsopslag, en vrij na afloop.
- **F2 — p95 afgedwongen.**
  - De hold-outcriteria bevatten nu `max_p95_ms: 90000`, en dat zit ook in de bevroren identiteit.
  - `_beoordeel_fase` eist voor elk hold-outgeval een geldige `duur_ms`. Bij een ontbrekende, niet-gehele, bool-, negatieve of onvolledige reeks volgt `latentie_onvolledig`; bij overschrijding volgt `p95_boven_grens`.
  - Tests met een gesimuleerde klok (zonder echte wachttijd): 90000 ms toegestaan, 90001 ms geweigerd.
- **F3 — bewijs vóór afronding.**
  - De volgorde is nu: resultaat opstellen, daarna bundel en resultaat afzonderlijk schrijven (`open("x")` met fsync, nooit overschrijven), en pas daarna `fase_einde` met `bewijs_opgeslagen`.
  - Bij een opslagfout wordt het wel te schrijven artefact bewaard. De fase wordt dan afgesloten met `mechanisch_geslaagd=false` en `stopreden=bewijsopslag_mislukt`, gevolgd door een `ProefStopError` (CLI exit 3). Vervolgfasen worden daardoor geweigerd.
  - Faalt het schrijven van `fase_einde` zelf, dan blijft de fase open (`grootboek_open`).
  - Het resultaatbestand vermeldt dat het grootboek leidend is.

## TDD en bewijs (onder `bewijs/`)

| Stap | Bestand | Uitkomst |
| --- | --- | --- |
| Herstelkopieën | `q1-herstel-v1/`, `q1-F123-herstel-v1/` | originele en gereviewde staat |
| Oorspronkelijk rood | `q1-red-v1.log` | 79 nieuwe failed (ontbrekende API/CLI-optie), 77 passed |
| Oorspronkelijk groen | `q1-green-v1.log` | 156 passed |
| Oorspronkelijke lint | `q1-lint-v2.log` | Black, Ruff 0.15.17 en Ruff 0.16.5 schoon; `q1-lint-v1.log` is een mislukte run door zsh-quoting |
| Mutatiecontrole | `q1-mutatie-v2.log` (plugin `q1-mutatie-v3.py`) | 11 van 11 mutaties gedood; `q1-mutatie-v1.log` telde één mutatie niet mee (anker na Black), en `q1-mutatie-v2.py` is ongebruikt |
| F1–F3 rood | `q1-F123-red-v1.log` | 15 nieuwe gerichte failures, 156 eerdere tests groen |
| F1–F3 groen | `q1-F123-green-v1.log` | **171 passed** |
| F1–F3 lint | `q1-F123-lint-v1.log` | Black, Ruff 0.15.17 en 0.16.5 schoon |
| Diffs | `q1-F123-deltadiff-v1.patch` (gereviewd → nu), `q1-F123-diff-v1.patch` (basis → nu, incl. fixture) | hashes in `q1-F123-hashmanifest-v1.json` |

Na de oorspronkelijke rode run zijn in eigen nieuwe tests nog enkele dingen aangepast:
- een te naïeve `"label"`-assertie is vervangen door labelmerktekens;
- er zijn twee Ruff-conforme herschrijvingen gedaan (SIM300 en PLC3002);
- Black-opmaak is toegepast.

Er zijn geen bestaande tests gewijzigd of verwijderd. De test draait met `.venv/bin/python -m pytest tests/unit/validation/test_def835_int02_modelproef.py -o addopts= -q -ra`, met neutrale providersleutels en de bestaande offline-bootstrap via `tests/conftest.py`.

## Resterende beperkingen

- De borging is procedureel. Wie het grootboek, het slotbestand of de proefmap verwijdert, kan de administratie resetten; dat kan de runner niet voorkomen. Een nieuw manifest (nieuw akkoord) krijgt een eigen grootboek, dus het resterende budget moet dan in dat nieuwe mandaat worden vastgelegd.
- Er is geen hervatfunctie. Na een procesafbreking staat de fase open en is het mandaat geblokkeerd.
- In een zeer klein raceframe tussen `mkdir` en het slot kan een gelijktijdige vervolgrun de eerste fase `proefmap_in_gebruik` laten krijgen. Dat is fail-closed en er gebeurt geen transport, maar het mandaat is dan wel geblokkeerd.
- `flock` is POSIX (macOS/Linux) en geldt alleen voor lokale bestandssystemen.
- Directory-fsync na het aanmaken van bestanden is niet toegevoegd.
- De labelhashes in het proefmanifest zijn niet geheim. Behandel het manifest als hold-outmateriaal van de coördinator.
- Een andere hold-outverdeling dan 4/8/4 wordt geweigerd; die vraagt een nieuw protocolbesluit.
- De runner meet alleen de hoofdstatus. Passagegronden, normgrond en de relevantie van de vraag beoordeelt Chris.
- De p95 is lokaal gemeten rond het transport. Er is geen providerclaim en geen factuurplafondclaim.
- De eerdere driecallproef blijft opgebruikt. Het geaccordeerde budget is door deze opdracht niet aangesproken.
