# DEF-770 — titelbeleid geïmplementeerd (Claude Code CLI, resultaat v1)

25 september 2026. Uitvoerder: Claude Code CLI, sessie 442a98fb-a377-403f-996e-433cf4a664fc.
Leidende bron: `docs/analyses/def606-regeldossiers/INT-01-implementatie/herstel-20260924-v1/titel-en-budgetbesluit-v1.md` (Chris: “akkoord op beide”), met `logs/def770-vervolg/astra-review-v3.md`.
Geen agents, reviewers, extra CLI-sessies, modelcalls, dependencies, commits of pushes. Geen maker-v1, G24-invoer, nieuwe proefmappen of beoordelingsoutputs gelezen.

## Wijziging

Verwijderd uit `src/domain/int01/zinsgrenzen.py`: de positieve titelherkenning uit /5 waarvan de woordrollen niet bewezen zijn:
- `_betrekkelijke_bijzin`;
- `_bijzingroepen`;
- `_PERSOONSVORMUITGANG`;
- de aanroep in `_classificeer_citaatslot`.

Er is geen vervangende heuristiek. Die citaatslotgevallen vallen nu terug op de bestaande /4-logica (`_voorzetselgroepen`, `_open_bijzin`). Wat die niet aantoont, wordt onzeker, met passage, positie en reden ("slotteken vóór een sluitend aanhalingsteken …").

Behouden:
- de /4-detecties;
- de R2-afkortingscorrectie (`_vermeldingen_na_haakje`, `_aansluiting_na_haakje`, `_classificeer_verklaarde_afkorting`); de code is ongewijzigd, alleen het contractcommentaar is opnieuw ingedeeld.

`CONTRACTVERSIE`: `def770-int01/5` → `def770-int01/6`, met commentaarregel en moduledocstring bijgewerkt. Een uitkomst onder /5 geldt via het bestaande opslagmechanisme niet als actueel (getest).

## Tests (met besluittrace)

`tests/unit/validation/test_def770_vervolg_zinsgrenzen.py`:
- Docstring en commentaar verwijzen naar titel-en-budgetbesluit-v1.
- Het strikte T20-xfailmechanisme (`T20_OPEN`, `OPEN_IDS`, `_param`) is weg; de vijf xfails zijn vervangen door geldende verwachtingen.
- `BESLUIT_AUTOMATISCH = {"T20": "review_required"}`. Het historische HERPROEF-label (`"pass"`) blijft onaangeroerd staan.
- Van (0,0) naar (0,1):
  - `h-T20`, `t20-waarin`, `t20-waarbij`, `t20-waarvan-punt`;
  - `c2-r1-twee-groepen`, `c2-r1-voorzetselgroep`;
  - `c3-r1-gemarkeerd(-punt)`, `c3-r1-waarin/waarmee/waarvoor-gemarkeerd`.
- `t20-zin-na-bijzin` gaat van (1,0) naar (1,1); de zekere fail blijft.
- Nieuw zijn de tegenvoorbeelden van reviewer v3, elk (0,1):
  - `c4-r1-het-werkt`: “… waarop het werkt de deelnemers wachten”;
  - `c4-r1-dit-werkt`: dezelfde zin met “dit werkt”.
- De verwisselde woordrollen (`c3-r1-*-verwisseld`) blijven (0,1).
- `test_t20_titelvoortzetting_is_inhoudelijke_beoordeling` toetst: geen zekere grens, precies één onzekere grens op `?’`, passage met “hier?’”, een aanhalingstekenreden, status `review_required` en geen zinsstructuur-pass.
- Service `h-T20` (beide laadpaden) → `zinsgrens_onzeker_1: review_required` plus de open onderdelen.

`tests/unit/validation/test_def770_herstel_zinsgrenzen.py`:
- `test_contractversie_is_6_na_titelbeleid`, met besluitdocstring.
- De oude-versietest bevat nu ook `def770-int01/5`.

`test_def770_int01_zinsgrenzen.py` is ongewijzigd (diff -q met de herstelkopie). Andere bestaande xfails en skips zijn niet aangeraakt.

## Skills

`skills/definitie-toetsregels/reference.md` (skillswerkboom, branch `feature/DEF-770-int01-herstel-skills`):
- De positieve ‘waar’-bijzinclaim is vervangen door: “een voortzetting na een titel of citaat waarvan de woordrollen of de aansluiting niet bewezen zijn … krijgt inhoudelijke beoordeling en geen automatische pass; normatief kan het één formulering zijn.”
- De R2-zinnen over verklaarde afkortingen blijven.
- De versieregel gaat naar `/6`.
- De ZIP-bundels heb ik niet aangeraakt; die zijn voor root.

## Bewijs (logs in `logs/def770-vervolg/`)

| Stap | Log | Uitkomst |
|---|---|---|
| Herstelkopie | `titelbeleid-herstelkopie-v1/` | vooraf gemaakt, `ALLES_GELIJK` |
| RED | `titelbeleid-red.log/.xml` | exit 1, 18 failures, waaronder `c4-r1-het-werkt` en `c4-r1-dit-werkt` (onterechte pass), de gemarkeerde titelgevallen en contract /6 |
| GREEN | `titelbeleid-green.log/.xml` | 370 tests, 0 failures, 0 skips/xfails, exit 0 |
| Gerichte regressie | `titelbeleid-gericht-regressie.log/.xml` | 1195 tests, 0 failures, 5 skips (waren 1189 met 10 skips/xfails: de 5 T20-xfails zijn vervangen, er zijn 6 gevallen bijgekomen), exit 0 |
| Black | `titelbeleid-black.log` | alleen het vervolgtestbestand opnieuw geformatteerd, exit 0 |
| Ruff 0.16.5 (gepind) | `titelbeleid-ruff-0165.log` | All checks passed, exit 0 |
| make lint | `titelbeleid-make-lint.log` | exit 0 |
| Diffs t.o.v. herstelkopie | `titelbeleid-diff-app.log`, `titelbeleid-diff-skills.log` | — |

Git-blobs na afloop:
- `zinsgrenzen.py` `ee87ff7a`;
- `test_def770_vervolg_zinsgrenzen.py` `3df1dc91`;
- `test_def770_herstel_zinsgrenzen.py` `11104257`;
- `test_def770_int01_zinsgrenzen.py` `3437bbb9` (ongewijzigd);
- skills `reference.md` `dbd7e561`.

## Bytegelijkheid generatie en NL-skill t.o.v. review-manifest-v3

SHA256 (Python hashlib) is **GELIJK** aan `review-manifest-v3.json` voor:
- `definition_task_module.py` `fbdb9e19…`;
- `json_based_rules_module.py` `60bad74b…`;
- `test_def770_vervolg_betekenisbehoud.py` `8eccb32a…`;
- NL `SKILL.md` `399131dd…`;
- NL `reference.md` `a2e0bc26…`.

`git diff --stat HEAD` op deze paden is leeg.

## Restpunten voor root

- De brede gate, de actuele skillsbundels (de ZIPs moeten `/6` weerspiegelen), de commit en de Astra/high-review van deze diff.
- Resultaten, bundels en proefuitkomsten onder `/5` gelden niet als actueel. Vóór nieuwe T24- en G24-beoordelingen moet opnieuw worden getoetst onder `/6`.
- Titelvoortzettingen met onbewezen woordrollen geven nu altijd `review_required`. Dat is bewust dekkingsverlies volgens het besluit, geen fout. Of de nieuwe onafhankelijke referentielabeling dit beleid volgt, bepaalt de volgende fase.
- Geen effect- of acceptatieclaim: die hangt af van de nog afgeschermde T24- en G24-beoordeling.
