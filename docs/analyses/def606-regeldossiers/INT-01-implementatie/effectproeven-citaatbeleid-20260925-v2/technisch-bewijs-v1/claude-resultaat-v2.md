# DEF-770 citaatcorrectie — resultaat Claude-uitvoerder v2

Uitvoerder: Claude Code CLI-sessie 442a98fb-a377-403f-996e-433cf4a664fc. Ik heb geen agents, reviewers of extra CLI-sessies gestart. Er waren geen API-calls, geen commit of push en geen bundels van mij.
Opdracht: `logs/def770-citaatbeleid/claude-correctie-v2.md`. Bevindingen: `logs/def770-citaatbeleid/astra-acceptatie-v1.md`.
Bases: app `ad4be749b2e38b968a22605f3842e244e6a766b7`, skills `e414eee84552b74818233e5c0fc4dacf36cd729a`. Beide HEADs zijn ongewijzigd.

**Geen acceptatieclaim.** T15, T17, T20 en T08 zijn nu ontwikkelregressies op een al geziene proef. Een nieuwe onafhankelijke proef en de gerichte review staan open. Ik heb geen v2-maker-, referentie- of adjudicatiebestanden gelezen, en ook niets uit `effectproeven-citaatbeleid-20260925-v2`.

## Samenvatting

| Bevinding | Oorzaak (/8) | Herstel (/9) |
|---|---|---|
| 1 T15 lijstcontext | `_regelgrenzen` keek alleen naar het teken vlak vóór iedere regelovergang. | Een inleidende `:` geldt voor het hele aaneengesloten opsommingsblok (`_in_ingeleid_lijstblok`). Tekst direct na zo'n blok is onzeker. |
| 2 T17/T20 citaatslot plus scheidingsteken | `_leestekenkandidaten` verwierp de kandidaat als na het sluitende aanhalingsteken geen witruimte stond. | Na een citaatslot hoort `,` `;` `:` gevolgd door witruimte en tekst bij de overgang (`_scheider_na_citaat`). Daarna volgt de bestaande classificatie, met de positie van het slotteken. |
| 3 T08 `bijv. R7.` | `_classificeer_afkorting` gaf „afkorting gevolgd door een hoofdletter” voor elke hoofdletter. | Bij een gewone afkorting (functie `afkorting`) gevolgd door één alfanumerieke code die direct met één slotteken of het tekstenende afsluit, is de afkortingspunt intern (`_afsluitende_code`). |

Contract `def770-int01/8` → `/9`. Opgeslagen `/8`-uitkomsten gelden niet meer als actueel.

## Onderbouwing en afbakening per bevinding

### 1. Lijstcontext (T15)

- **Positief:** de inleidende dubbele punt blijft gelden zolang de regels erna aaneengesloten opsommingsleden zijn (`_LIJSTREGEL`). Resultaat: T15 (0,0) → zinsstructuur-pass, en `lagen:\n- bovenlaag\n- onderlaag` → (0,0).
- **Behouden:**

  | Geval | Uitkomst |
  |---|---|
  | niet-ingeleide lijst `lagen\n- …` | 2× „opsommingsteken” |
  | lege regel in het blok | alinea-overgang + opsommingsteken |
  | werkelijk zinseindteken in een lid | punt + teken dat geen zinsbegin is: onzeker |
  | punt + hoofdletter in een lid | zeker |

- **Niet vrijgesteld: tekst na of in het blok.** Tot en met /8 werd dit alleen afgedekt doordat de grens tussen de leden al meldde. Het eenledige `lagen:\n- bovenlaag\nDe kaart ligt klaar` gaf op /8 zelfs (0,0). Nieuw is een onzekere grens „tekst na een opsomming zonder slotteken: vervolg van het laatste lid of zelfstandige vervolgtekst niet vast te stellen”. Die geldt voor:
  - vervolgtekst direct na het blok;
  - tussentekst die het blok onderbreekt; het lid erna blijft dan onzeker.
- **Grens:**
  - Genummerde lijsten (`1. …`) blijven via `_classificeer_getal` „genummerd opsommingsitem”, zoals voorheen; alleen de regelgrens tussen de leden vervalt.
  - Een opsomming na `;` of `,` volgde al de bestaande K4-route en is niet verbreed.
  - Een omgebroken lid (vervolgregel zonder opsommingsteken) wordt conservatief onzeker.

### 2. Citaatslot met scheidingsteken (T17, T20)

- **Bewezen verlies:** in `voorprobe-v2.log` gaven `‘kom terug!’, dat`, `‘kom terug!’; de`, `‘kom terug!’: de`, `“Gereed.”, dat` en `‘kom terug!’, Dat` allemaal (0,0). De familie is daarom begrensd tot `,;:`, direct na het sluitende aanhalingsteken van een citaat met slotteken, en gevolgd door witruimte en tekst.
- **Positie en reden:** de positie blijft die van het slotteken (`!`/`?`/`.`). De passage bevat het scheidingsteken; T17 geeft „…betekenis ‘kom terug!’, dat verschijnt zodra een”.
  - Na een kleine letter volgt de bestaande `_classificeer_citaatslot`: onzeker.
  - Na een hoofdletter volgt de bestaande route voor een teken binnen een citaat: onzeker, nooit zeker.
- **Geen nieuwe pass-heuristiek.** Het scheidingsteken wordt niet als bewijs voor doorlopen gebruikt.
- **Behouden:**
  - citaat zonder slotteken (`‘kom terug’, dat`) (0,0);
  - interne citaatpunctuatie (`‘Klaar. Ga door’, dat`) (0,0);
  - haakjes: `(Stop!), dat` blijft haakjesslot, `(zie hfst. 3), dat` blijft (0,0);
  - de latere zekere grens in T20 („weergegeven. De achterzijde”) blijft.
- **Grens, niet onderzocht:**
  - een scheidingsteken zonder witruimte erna (`’,dat`);
  - andere tekens (`-`, `—`). Voor die gevallen is geen kandidaatverlies aangetoond.

### 3. Voorbeeldcode na afkorting (T08)

- **Structureel argument:** begint na `bijv.` een nieuwe zin, dan bestaat die alleen uit de code (`R7.`) of alleen uit de code aan het tekstenende. Dat is geen zin, dus de afkortingspunt is intern. De punt na `R7` blijft zelf een kandidaat: T08 houdt de zekere grens „R7. De laatste positie” (fail) zonder de extra onzekere melding.
- **Code:** `_CODE` = alleen hoofdletters, cijfers en `-`, met ten minste één cijfer, beginnend met een hoofdletter. Er is geen woordrollenlijst bijgekomen; de bestaande afkortingsfunctie `afkorting` wordt hergebruikt.
- **Negatieve tegenhangers, onzeker gebleven:**

  | Geval | Waarom |
  |---|---|
  | `bijv. R7 bevat een cijfer` | code gevolgd door woorden |
  | `bijv. R7, R8 en R9` | komma na de code |
  | `bijv. De kaart ligt klaar` | gewoon woord |
  | `bijv. NVR.` | geen cijfer |
  | `bijv. Rood7.` | kleine letters |
  | `enz. R7.` | mogelijk zinslot, blijft „afkorting die ook een zin kan afsluiten” |

- **Bewijs voor generalisatie ontbreekt voor:**
  - andere afkortingsfuncties: titel, verwijzing, initiaal, mogelijk zinslot;
  - codes met kleine letters of zonder cijfer;
  - codes gevolgd door meer tekst.

  Alleen T08 en de minimale varianten hierboven zijn onderbouwd. Voor `ca.`/`max.`/maandafkortingen vóór zo'n code geldt de vrijstelling ook, omdat zij in dezelfde functie `afkorting` zitten. Daarvoor is geen afzonderlijk proefbewijs; het rust op hetzelfde structurele argument.

## Tests

**Nieuw: `tests/unit/validation/test_def770_citaatcorrectie_zinsgrenzen.py`**

- 32 segmentatiegevallen die elk exact het aantal grenzen toetsen, met soort, teken op de positie, passagedeel en reden.
- Een binding aan de afgeronde proef, alleen lezend:
  - de teksten zijn gelijk aan `t24-gevallen-v1.json`;
  - de automatische zinsstatus plus de grens- en boundary-passages volgen `t24-adjudicatie-v1.json` voor T08, T15, T17 en T20.
- Service op beide laadpaden: T15 zinsstructuur-pass; T17 `zinsgrens_onzeker_1`; T20 `zinsgrens_1` fail + `zinsgrens_onzeker_1`; T08 alleen `zinsgrens_1`.
- `/8`-uitkomst niet actueel (`lees_beoordeling`, `applied False`, reden „contractversie”).
- Contract `/9`.
- De proeflabels zijn niet aangepast. Er zijn geen overrides die acceptatie groen maken.

**Aangepast, met trace naar astra-acceptatie-v1:**

- `test_def770_int01_zinsgrenzen.py::test_opsomming_met_opsommingstekens_is_onzeker_niet_zeker` (sinds 5b93df46f, contract /1) verwachtte voor de ingeleide lijst `sanctie bestaande uit:\n- …\n- …` een onzekere grens. Dat is precies het gat van bevinding 1.
  - Nu: de ingeleide lijst heeft geen grenzen.
  - De oorspronkelijke bedoeling („lijststructuur mag niet stil wegvallen”) blijft geborgd met de niet-ingeleide variant.
  - De historische verwachting staat in de docstring.
- De contracttests in de herstel-, restherstel- en citaatbeleid-test → `/9`, met historische docstring.
- De currentness-parametrisatie in de herstel-test heeft `def770-int01/8` erbij gekregen.

## Commando's, exits en logs (`logs/def770-citaatbeleid/`)

`PY` = `/Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python`. Pytest-runs gaan via `PY logs/def770-citaatbeleid/pytest-log-v2.py <naam> <args>`. Die draait `PY -B -m pytest -q --tb=line -p no:cacheprovider --junitxml=…` met cwd app, weigert te overschrijven en zet het commando plus de exit in de log.

| Stap | Log | Exit | Resultaat |
|---|---|---|---|
| Herstelkopieën (`herstelkopie-maken-v2.py` → `herstelkopie-v2/`) | `herstelkopie-maken-v2.log` | 0 | 8/8 GELIJK |
| Voorprobe op /8 (`voorprobe-v2.py`) | `voorprobe-v2.log` | 0 | alle drie oorzaken plus het `;`/`:`-verlies aangetoond |
| RED, alleen de nieuwe module, op /8 | `red-v2.log`/`.xml` | 1 | 51 tests, 34 failures (alle doelgevallen). De behoud- en negatieve gevallen en de proeftekstbinding slaagden al. |
| Eerste run na de runtimewijziging, 6 zinsgrensbestanden | `green-poging-v2.log`/`.xml` | 1 | 497 tests, 4 failures: 3 contracttests + de opsommingstest hierboven |
| GREEN, 6 zinsgrensbestanden | `green-v2.log`/`.xml` | 0 | 501 tests, 0 failures |
| Ontwikkelvergelijking 24 proefgevallen /8 vs /9 (`proefvergelijking-v2.py`) | `proefvergelijking-v2.log` | 1 | Eerste poging: importfout in mijn script (`sys.modules`-registratie ontbrak). Bewaard. |
| idem, na scriptcorrectie | `proefvergelijking-v2b.log` | 0 | Alleen T08, T15, T17 en T20 wijzigen, en precies zoals bedoeld; de overige 20 zijn identiek. Zinsstatus conform adjudicatie: /8 21/24, /9 23/24. De enige „afwijking” is T21 `not_evaluated` (lege kern, app `None`). |
| Lint (`lint-v2.py`): Ruff 0.16.5 `--version`, `check`, Black `--check` op 6 bestanden, `make PY=… lint` | `lint-v2.log` | 0/0/0/0 | schoon |
| Gerichte regressie `-m unit` (zelfde bestandsset als v1, zonder `tests/unit/services/prompts`) | `regressie-v2.log`/`.xml` | 0 | 1054 tests, 0 failures |
| Offline integratie `test_offline_core_journey.py`, `test_export_levels_comprehensive.py` `--timeout=120` | `integratie-v2.log`/`.xml` | 0 | 28 tests, 0 failures, 1 bestaande skip |
| **Volledige gate** `make PY=… GATE_REPORTS=logs/def770-citaatbeleid/correctie-unit-v2 test` (via `gate-v2.py`, cwd app) | `correctie-unit-v2.log`, `correctie-unit-v2/unit-junit.xml`, `unit-inventaris.json` | **0** | 7534 passed, 75 skipped, 722 deselected, 1 xfailed; `run_profile status=ok` |
| Hashes en diff (`hashes-en-diffs-v2.py`) | `hashes-en-diffs-v2.log`, `diff-v2.patch` | 0 | zie hieronder |

De DEF-126 `red_phase`-prompttest valt buiten de gate (scope-waiver, geen promptwijziging). Ik heb hem niet opnieuw gedraaid.

## Bronhashes (SHA256)

| Bestand | Voor (herstelkopie-v2) | Na |
|---|---|---|
| `src/domain/int01/zinsgrenzen.py` | `3f0e0224e50a8bfeacff9e420b72b411b0c453f7c85b20a6b960b9040d9cbf29` | `bdefb3e38d351408ecd4a6192ed198f4830eb8a892e55874d63623f85f469ea2` |
| `tests/unit/validation/test_def770_citaatcorrectie_zinsgrenzen.py` | — (nieuw) | `69c6af43d3fb68b12419c7e48014f2e7fa70f3faad5679a499a9847746ad10f9` |
| `tests/unit/validation/test_def770_int01_zinsgrenzen.py` | `cdab46b5…2427` | `b9ca82956e75594a8ba688c4b7cff9eea2419199ff5339f6139fd0da3d430834` |
| `tests/unit/validation/test_def770_herstel_zinsgrenzen.py` | `9ce34a95…b461` | `4472cb401c9fe9f5361736cca6bcb3bce8bd03d5803494375fcbefe6d931248f` |
| `tests/unit/validation/test_def770_restherstel_zinsgrenzen.py` | `36b7aef0…9ab1` | `d514de4021b0b7c02d45a37ab0aee812c52710933397dc538fed07dd35e261bf` |
| `tests/unit/validation/test_def770_citaatbeleid_zinsgrenzen.py` | `dcbe5ff4…397c` | `3ce8f73726fa88f57afc664867cef8f27706b0044c3b6babf02e88e29630732f` |
| `tests/unit/validation/test_def770_vervolg_zinsgrenzen.py` | `d5fe8252…d302` | ongewijzigd |
| skills `definitie-toetsregels/reference.md` | `899e1fbf…b361a` | `77eda8f6ecc7afe9b027910cd45ac5689a35494c095f55f677ebcb126c1863c1` |
| skills `definitie-toetsregels/SKILL.md` | `1aebed21…9bfa` | ongewijzigd |

- Diff tegen herstelkopie-v2: `diff-v2.patch` (sha256 `45e227099fe3a36cd4f156c1fecc4433f3940c4396d6fa5c790e4d780a1dfca1`).
- Toetsinstructie: alleen de contractregel is gewijzigd, `def770-int01/8` → `/9`, plus „ook na een komma, puntkomma of dubbele punt” in de samenvatting van wat open blijft. De normtekst over opsommingen dekte bevinding 1 al.
- Proefbestanden, alleen gelezen:

  | Bestand | SHA256 |
  |---|---|
  | `t24-gevallen-v1.json` | `f0aedf52…e416f6` |
  | `t24-adjudicatie-v1.json` | `21298996…0fbb8d` |
  | `t24-referentie-A-v1.json` | `245bdc99…ec232` |
  | `t24-referentie-B-v1.json` | `0029b34e…c433` |
  | `t24-resultaat-nieuw-v1.json` | `d8eaa803…9fd2a` |

  De resultaathash is gelijk aan die in astra-acceptatie-v1.
- `git diff --name-only HEAD -- docs config src/services/prompts src/toetsregels scripts Makefile` is leeg. De generatieskill `definitie-nederlandse-definities` is ongewijzigd.

## Beperkingen en meldingen

- **Andere schrijver in de skills-worktree.** `cowork-exports/definitie-toetsregels.zip` en `cowork-exports/toetsregels.zip` zijn om 11:10:41 gewijzigd. Dat viel tijdens mijn gate-run (`make test` in de app-repo, 11:09–11:14). Bij de preflight waren ze niet gewijzigd.
  - `definitie-toetsregels.zip` bevat al mijn nieuwe `reference.md` (sha256 `77eda8f6…`).
  - De app-repo (tests, src, scripts, Makefile) bevat geen verwijzing naar `cowork-exports`.
  - Ik heb geen bundels gebouwd en de zips niet aangeraakt of teruggezet. De coördinator moet de herkomst vaststellen.
- **Werkelijke doorwerking in de proef.** De verbetering op T15/T17/T20/T08 is ontwikkelbewijs op een al geziene set, geen acceptatie. De nieuwe onafhankelijke set heb ik niet gezien.
- **Niet onderzocht en niet gewijzigd:**
  - genummerde lijsten (itempunten blijven onzeker);
  - een scheidingsteken zonder witruimte na een citaat;
  - codes na andere afkortingsfuncties.
- `proefvergelijking-v2.log` (exit 1, mijn scriptfout) is bewaard naast de geslaagde `…-v2b.log`.
- De lege map `probe/` uit v1 staat er nog; niets verwijderd.

Gestopt voor de gerichte review.
