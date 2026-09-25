# DEF-770 citaatbeleid — resultaat Claude-uitvoerder v1

Uitvoerder: Claude Code CLI-sessie 442a98fb-a377-403f-996e-433cf4a664fc. Ik heb geen agents, reviewers of extra CLI-sessies gestart en niets gecommit, gepusht of gebundeld. Er waren geen API-calls, geen dependencies en geen live skillsactivatie.
Besluit: `docs/analyses/def606-regeldossiers/INT-01-implementatie/herstel-20260924-v1/algemeen-citaatbesluit-v1.md`.
Bases: app `c8e8997ec39693e6c66c4792be4459ed214c080d` (HEAD ongewijzigd), product `108f38a3…`, skills `990ec253067f6a0ef212f8b6b41cc38570acfeb4` (HEAD ongewijzigd).

**Geen volledige acceptatieclaim.** Een nieuwe onafhankelijke T24 onder dit beleid en de review staan nog open.

## Conclusie

De runtime voldeed niet aan het besluit. Een voorprobe onder `/7` (vastgelegd in de uitvoeringssessie vóór de wijziging) gaf zinsstructuur-pass (0,0) voor citaatvervolgen waarvan de samenhang op veronderstelde woordrollen rust:

- ‘kaart met de titel ‘Klaar?’ met het regent’;
- ‘code met de melding “Gereed.” op het scherm’;
- ‘code die de melding “Gereed.” toont’;
- ‘code die de melding “Gereed.” klaar’.

Daarom heb ik de runtime gewijzigd: TDD RED → GREEN, met het contract van `def770-int01/7` naar `def770-int01/8`.

## Wijziging (runtime)

`src/domain/int01/zinsgrenzen.py`: `_classificeer_citaatslot()` geeft nu altijd `onzeker`, met de grond „slotteken vóór een sluitend aanhalingsteken gevolgd door verdere tekst: einde van het citaat of ook van de buitenste zin niet vast te stellen”. Dat geldt voor een slotteken direct vóór een sluitend aanhalingsteken, gevolgd door tekst die niet met een hoofdletter of cijfer begint.

- **Vervallen:** de twee positieve paden uit /4, samen met hun hulpfuncties en woordlijsten (`_open_bijzin`, `_voorzetselgroepen`, `_woorden_tot_zeker_zinsbegin`, `_PERSOONSVORMEN`, `_ZEKER_ZINSBEGIN`, `_ONDERSCHIKKEND`, `_VOORZETSELS`). De twee paden waren:
  - een vervolg uit voorzetselgroepen;
  - een vóór het citaat geopende bijzin.
- **Toegevoegd:** geen morfologie- of woordlijstheuristiek.
- **Behouden (afbakening):**
  - interne citaatpunctuatie die niet direct vóór het sluitende teken staat (route "geen");
  - een citaat zonder slotteken;
  - een zekere buitenste grens (hoofdletter of cijfer na het citaat, via de bestaande classificatie);
  - een geheel geciteerde kern (zinsstructuur pass plus broncitaat review_required).
- **Contract en actualiteit:** `CONTRACTVERSIE = "def770-int01/8"`, met contractcommentaar en moduledocstring bijgewerkt. Opgeslagen `/7`-uitkomsten gelden niet meer als actueel: de bestaande currentness-test in de herstel-test heeft `def770-int01/7` in de lijst met oude versies gekregen. De opslag- en teruglees-test in de nieuwe testmodule controleert `/8`.

Naprobe (`logs/def770-citaatbeleid/naprobe-v1.py` → `naprobe-v1.log`, exit 0) met dezelfde zeven teksten:

| Tekst | Voor (/7) | Na (/8) |
|---|---|---|
| T17 ‘bord met de tekst ‘Ga verder!’ dat tijdens een oefening een vrije doorgang markeert’ | (0,1) | (0,1) |
| ‘kaart met de titel ‘Klaar?’ met het regent’ | (0,0) | (0,1) |
| ‘code met de melding “Gereed.” op het scherm’ | (0,0) | (0,1) |
| ‘code die de melding “Gereed.” toont’ | (0,0) | (0,1) |
| ‘code die de melding “Gereed.” klaar’ | (0,0) | (0,1) |
| ‘melding “Klaar. Ga door” op het scherm’ (intern) | (0,0) | (0,0) |
| ‘bord met de tekst ‘Ga verder’ dat een doorgang markeert’ (geen slotteken) | (0,0) | (0,0) |

De totaalstatus is overal review_required, omdat compactheid en begrijpelijkheid open blijven. Een volledige INT-01-pass komt niet voor.

## Tests

**Nieuw: `tests/unit/validation/test_def770_citaatbeleid_zinsgrenzen.py`**

- R-T17 (ontwikkelbewijs): `REFERENTIE_NORMATIEF = {"T17": "pass"}` en `HISTORISCH_AUTOMATISCH = {"T17": "pass"}` blijven zichtbaar en ongewijzigd. Daarnaast staat de afzonderlijke `BESLUIT_AUTOMATISCH = {"T17": "review_required"}`.
- Regressiegevallen dat/die:
  - ‘… ‘Ga verder!’ dat markeert tijdens een oefening een vrije doorgang’ (lezing als hoofdzin mogelijk);
  - ‘… ‘Klaar?’ die de speler bewaart’.
- Voormalige positieve paden, nu (0,1):
  - de voorzetselgroepvarianten, waaronder ‘met het regent’;
  - de bijzinvarianten ‘toont’, ‘klaar’ en ‘op het scherm zet’.
- Afbakening, beoordeling behouden:

  | Geval | Uitkomst |
  |---|---|
  | interne punt | (0,0) |
  | interne vraagtekens | (0,0) |
  | geen slotteken | (0,0) |
  | zekere buitenste grens naast de citaatgrens | (1,1) |
  | nominale kern zonder citaat | (0,0) |
  | geheel geciteerde kern | ongewijzigd |

- Per onzeker geval wordt gecontroleerd: passage, positie op het slotteken en de grond met „aanhalingsteken”.
- Service op beide laadpaden (toetsregel_manager en cached_manager) voor R-T17 en ‘op het scherm’: `zinsgrens_onzeker_1` review_required, plus compactheid en begrijpelijkheid open.
- Verder: opslag en teruglezen, en de contractversie `/8`.

**Bijgewerkte bestaande verwachtingen**

De historische tuples blijven zichtbaar staan. Daarnaast is er een overridetabel met trace naar algemeen-citaatbesluit-v1:

- `test_def770_herstel_zinsgrenzen.py`:
  - `CITAATBESLUIT` voor 11 segmentatiegevallen: `T17-ingesloten-citaat`, `citaat-recht`, `zin-na-citaat` (1,0 → 1,1), `r2-citaat-voortzetting`, `r2-citaat-voorzetsel`, `r3-citaat-korte-pp`, `r4-bijzin-voornaamwoord`, `r4-open-bijzin-pp`, `r4-open-bijzin-een`, `e1-T17-bijzin-meer-groepen` en `e1-T20-voorzetselgroepen`, elk → (0,1) tenzij anders vermeld;
  - `CITAATBESLUIT_SERVICE` voor T17, e1-T17 en e1-T20: van `zinsstructuur: pass` naar `zinsgrens_onzeker_1: review_required`;
  - contracttest → `/8`, met `/7` in de lijst met oude versies;
  - moduledocstring aangevuld.
- `test_def770_int01_zinsgrenzen.py`: `CITAATBESLUIT = {"ingesloten-vraagtitel": (0, 1)}` (‘rapport met de titel ‘Wie betaalt?’ van de commissie.’).
- `test_def770_restherstel_zinsgrenzen.py`:
  - `a-T20-zonder-extra-woord` (0,0) → (0,1), met commentaar over het oude basisgedrag;
  - `test_contractversie_is_7_na_restherstel` hernoemd tot `test_contractversie_na_restherstel_en_citaatbeleid` en → `/8`, met historische docstring;
  - moduledocstring aangevuld.
- `test_def770_vervolg_zinsgrenzen.py`: ongewijzigd (geen geraakte verwachting).

## Skills (worktree DEF-770-int01-skills)

- `skills/definitie-toetsregels/reference.md`, sectie Toetsen: de passage over citaatvervolgen volgt nu het besluit.
  - Elke voortzetting zonder hoofdletter of cijfer na een slotteken direct vóór een sluitend aanhalingsteken gaat naar inhoudelijke beoordeling. Dat omvat dat/die-bijzinnen na het citaat, ‘waar’ + voorzetsel, voorzetselgroepen en een bijzin die vóór het citaat begon.
  - Normatief kan het één correcte formulering zijn.
  - Geen positief bewijs uit woorduitgang, veronderstelde correctheid of het ontbreken van een hoofdzin.
  - Geen algemene onzekerverklaring: de uitzonderingen voor interne leestekens, citaten zonder slotteken en zekere buitenste grenzen blijven.
  - De zin „alleen groepen met hooguit een lidwoord en één woord gelden automatisch als voortzetting” is verwijderd.
- Zelfde bestand: de contractregel is `def770-int01/7` → `/8`, met een aanvulling in de conservatieve samenvatting.
- `SKILL.md`: niet gewijzigd. Hij bevat geen citaatvervolgregel of contractversie.
- De generatieskill `definitie-nederlandse-definities` is niet gewijzigd, net als de sectie „Norm en generatie” in reference.md.

## Commando's en exits

Python: `/Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python` (hieronder `PY`). Alle commando's zijn uitgevoerd vanuit de app-worktree. Logs en XML staan in `logs/def770-citaatbeleid/`.

**Herstelkopieën**

- Commando: `PY logs/def770-citaatbeleid/herstelkopie-maken-v1.py` → `herstelkopie-v1/`.
- Exit 0; alle 7 bestanden GELIJK.

**RED**

- Commando: `PY -B -m pytest -q <5 zinsgrenstestbestanden> --tb=line -p no:cacheprovider --junitxml=…/red-v1.xml` → `red-v1.log`.
- exit=1: 442 tests, 16 failures. Dit zijn de verwachte nieuwe gevallen, plus contract /8 en de service ‘op het scherm’ op beide paden.

**Na de runtimewijziging: `green-poging-v1`**

- exit=1: 442 tests, 22 failures.
- Dat zijn de bestaande verwachtingen hierboven, plus één fout van mijzelf. Mijn eigen testgeval `intern-vraag` gebruikte eerst ‘“Wie? Wat?”’; daarin is ‘Wat?’ zelf een citaatslot. Ik heb het vervangen door ‘formulier met de kop “Wie? Wanneer” boven de velden’.

**GREEN**

- Commando: `green-v1` (dezelfde 5 bestanden).
- exit=0: 446 tests, 0 failures, 0 errors.

**Lint (Ruff 0.16.5)**

- Commando: `/Users/chrislehnen/.cache/pre-commit/repoy903793m/py_env-python3.13/bin/ruff check` op het gewijzigde src-bestand en de 4 gewijzigde of nieuwe testbestanden.
- „All checks passed!”, exit 0.

**Black**

- Commando: `black --check` (venv) op dezelfde bestanden.
- Exit 1 op `test_def770_herstel_zinsgrenzen.py`. De oorzaak was alleen opmaak in mijn eigen parametrize-hunk: één regel in plaats van vier.
- Daarna `black` op dat bestand, exit 0.

**`make PY=… lint`**

- Log: `lint-v1.log`.
- Exit 0: Ruff „All checks passed!”, Black 405 files unchanged.

**Gerichte regressie (na black)**

- Log: `regressie-v1.log`/`.xml`.
- Bestanden:
  - de 5 zinsgrenstestbestanden;
  - `validation/test_rule_runtime_matrix.py`, `test_v2_golden_additional_patterns.py`, `test_v2_golden_initial_int_con.py`, `test_category_mapping_externalized.py` en `test_json_validators.py`;
  - `services/test_def770_int01_keten.py`, `test_def770_int01_opslag.py` en `test_def766_ess03_persistentie.py`;
  - `services/orchestrators/test_def622_tekstwijziging_bewijs.py`;
  - `ui/test_def770_int01_editor_binding.py`;
  - `database/test_def751_*` (4);
  - `tests/unit/services/prompts`.
- exit=1: 1405 tests, 1 failure, 6 skipped.
- De enige failure is `tests/unit/services/prompts/modules/test_definition_task_transformation.py::…::test_no_negative_commands_in_guide`:
  - de test heeft marker `red_phase`, geen `unit`, en valt dus buiten `make test`;
  - hij test `DefinitionTaskModule`, die ik niet heb gewijzigd;
  - `git diff HEAD -- src/services/prompts` is leeg;
  - hij heeft geen relatie met int01.
- Hij is niet vergeleken tegen de base; zie Beperkingen.

**Offline integratie**

- Commando: `tests/integration/test_offline_core_journey.py` en `test_export_levels_comprehensive.py` met `--timeout=120`.
- Log: `integratie-v1.log`.
- exit=0: 28 tests, 0 failures, 1 skipped (bestaande skip voor Excel-timezone).

**Volledige unitsuite**

- Commando: `PY -B -m pytest -q -m unit tests --timeout=300 …`.
- Log: `unit-v1.log`/`.xml`.
- exit=1: 7576 tests, 2 failures, 0 errors, 76 skipped.
- De 2 failures zijn `tests/unit/test_performance_tracker.py::TestGlobalTracker::test_reset_tracker` en `…::test_get_tracker_singleton`.
- Ze falen ook los (`perftracker-los-v1.log`, exit 1), met `OfflineGateError: SQLite-doel 'data/definities.db' ligt buiten de tijdelijke sessieroot`. `monitoring/performance_tracker.py` gebruikt alleen stdlib, met standaardpad `data/definities.db`, en importeert niets uit `domain.int01`.
- Ik heb dit bestand, de test en `tests/offline_bootstrap.py` niet gewijzigd. De laatste commit op die bestanden is `e0dc96bc2` (2026-09-07).
- Deze fouten zijn niet op de base gereproduceerd; zie Beperkingen.

**Hashes en diffs**

- Commando: `PY logs/def770-citaatbeleid/hashes-en-diffs-v1.py` → `hashes-en-diffs-v1.log`.
- Exit 0.
- Diff tegen herstelkopie-v1: `diff-v1.patch`.

## Bronhashes (SHA256, voor → na)

| Bestand | Voor | Na |
|---|---|---|
| `src/domain/int01/zinsgrenzen.py` | `7f1216d3825caec0beca7f405a0931ecf9e7dbd26f8f41b3630e984665574bb0` (= classifier-hash in astra-t24-acceptatie-v1) | `3f0e0224e50a8bfeacff9e420b72b411b0c453f7c85b20a6b960b9040d9cbf29` |
| `tests/unit/validation/test_def770_int01_zinsgrenzen.py` | `b6d9c3f2…76d5` | `cdab46b55afe71115ed5032a7ed41df1ccf34a89d4d1f9af3c3ead9890012427` |
| `tests/unit/validation/test_def770_herstel_zinsgrenzen.py` | `b858f645…ff7e` | `9ce34a95bc44fde3f3d0346bff71618c6add4e1ad3492060be97b858a2c9b461` |
| `tests/unit/validation/test_def770_restherstel_zinsgrenzen.py` | `2be2d167…e2e3` | `36b7aef0280db3174dce524f5b2d151ddbd85cdb772dc2ccf74558aa63359ab1` |
| `tests/unit/validation/test_def770_vervolg_zinsgrenzen.py` | `d5fe8252…d302` | ongewijzigd |
| `tests/unit/validation/test_def770_citaatbeleid_zinsgrenzen.py` | — (nieuw) | `dcbe5ff420a43b9a9a350e9be2cbe77e1e1c489ff92e71d58be32058747c397c` |
| skills `definitie-toetsregels/reference.md` | `d053f336…ea2e` | `899e1fbf0e89687709746a20f66615b30f1c7079aef41b5e3be85e721cab361a` |
| skills `definitie-toetsregels/SKILL.md` | `1aebed21…9bfa` | ongewijzigd |

De volledige voorhashes staan in `hashes-en-diffs-v1.log`.

Onveranderd bevestigd (`git diff --name-only HEAD`, leeg):

- `docs/`, waaronder alle historische proeven;
- `config/`;
- `src/services/prompts`;
- `src/toetsregels`;
- `scripts`;
- `logs/def770-restherstel`;
- de generatieskill `skills/definitie-nederlandse-definities`.

Getrackte wijzigingen in de app zijn alleen de 4 genoemde bestanden; in de skills alleen reference.md.

## Beperkingen

- De 3 niet-int01-failures (1× red_phase-promptguide, 2× performance-tracker offline-gate) zijn niet op de base gedraaid. Dat de oorzaak losstaat van mijn wijziging, volgt uit de import- en diffanalyse hierboven, niet uit een A/B-run.
- De GREEN-run liep vóór de Black-herformattering. De gerichte regressierun erna bevat dezelfde 5 zinsgrenstestbestanden en had daarin geen failures.
- De T24-ontwikkelregressie (`analyse-t24-regressie-v1.py`) is niet opnieuw gedraaid. De historische T24-uitslag (23/24) blijft onder `/7` onaangetast, maar geldt niet als bewijs voor `/8`. Onder `/8` wijken de eerder als pass gelabelde citaatvervolgen bewust af van hun historische automatische label. Beoordeling volgt in de nieuwe onafhankelijke T24.
- Niet gelezen:
  - `maker-v1.json`, `maker-sessie-v1.jsonl`, `maker-opdracht-v1.md`, `t24-referentie-*-opdracht-v1.md`;
  - `astra-opdracht-v1.md`, `astra-review-sessie-v1.jsonl`, `review-*-v1.patch`, `review-manifest-v1.json`, `maak-reviewbinding-v1.py`;
  - nieuwe proefsets.

  De review-patches en het manifest zijn door de coördinator aangemaakt (10:41–10:43) en kunnen ouder zijn dan mijn laatste stappen: de Black-herformattering (±10:36) valt ervoor, dit rapport erna. Controleer of de reviewdiff overeenkomt met de hashes hierboven.
- Tijdens de voorprobe is een lege map `logs/def770-citaatbeleid/probe/` ontstaan. Ik heb hem niet verwijderd (geen verwijderopdracht).
- `sentence_status`-achtige historische velden in bestaande proefbestanden zijn niet aangeraakt.

Gestopt voor dezelfde onafhankelijke reviewer.
