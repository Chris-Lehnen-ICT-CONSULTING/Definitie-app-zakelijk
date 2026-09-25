# DEF-770 citaatcorrectie — resultaat Claude-uitvoerder v3

Uitvoerder: Claude Code CLI-sessie 442a98fb-a377-403f-996e-433cf4a664fc. Ik heb geen agents, reviewers of extra CLI-sessies gestart en geen API-calls gedaan. Er is niets gecommit, gepusht of gebundeld.
Invoer: `logs/def770-citaatbeleid/astra-correctiereview-v2.md`. R1 is gesloten en niet verder verbreed; alleen R2 en R3 zijn verwerkt.
Bases: app `ad4be749b2e38b968a22605f3842e244e6a766b7`, skills `e414eee84552b74818233e5c0fc4dacf36cd729a`. Beide HEADs zijn ongewijzigd.
Contract blijft `def770-int01/9`: nog niet gepubliceerd of bevroren voor een proef, volgens de opdracht.

**Geen bronvrijgave of acceptatieclaim.** Ik heb geen volledige suite gestart; de coördinator start `make test` na de bronvrijgave. Er zijn geen v2-maker-, referentie- of proefdata gelezen.

## Status v2-fullgate (brongebonden)

De canonieke gate van v2 is afgerond:

- **Commando:** `make PY=/Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python GATE_REPORTS=logs/def770-citaatbeleid/correctie-unit-v2 test` (via `gate-v2.py`, cwd app).
- **Log:** `correctie-unit-v2.log`. Exit 0: 7534 passed, 75 skipped, 722 deselected, 1 xfailed; `run_profile status=ok`.
- **Rapporten:** `correctie-unit-v2/unit-junit.xml` en `unit-inventaris.json`.
- **Bronbinding:** v2-bron `zinsgrenzen.py` sha256 `bdefb3e38d351408ecd4a6192ed198f4830eb8a892e55874d63623f85f469ea2` en testmodule `69c6af43…`. Deze uitkomst geldt dus **niet** voor de v3-bron hieronder.

## Delta v2 → v3

### R2 — citaatslot met scheidingsteken zonder spatie

**Oorzaak:** `_scheider_na_citaat` eiste witruimte na `,`/`;`/`:`, en daarna verwierp `_leestekenkandidaten` de kandidaat omdat `tekst[index]` geen witruimte was.

**Fix:**

- `_scheider_na_citaat` vraagt alleen nog een scheidingsteken direct na het sluitende aanhalingsteken van een citaatslot, gevolgd door verdere tekst, met of zonder witruimte.
- In `_leestekenkandidaten` geldt de witruimte-eis niet als zo'n scheider is herkend (`scheider or tekst[index].isspace()`).
- Classificatie en positie zijn ongewijzigd: de bestaande citaatslotroute, of bij een hoofdletter de bestaande route voor een teken binnen een citaat. De positie blijft die van het slotteken.
- `_passage` voegt in dat geval geen spatie in, dus de passage luidt „…terug!’,dat verschijnt”. Bij de al bestaande haakjesgevallen (`(Stop!), dat`) verandert de passage niet.

**Resultaat:**

| Tekst | Uitkomst |
|---|---|
| `‘kom terug!’,dat verschijnt` | onzeker op `!` |
| `‘kom terug!’;de lamp brandt` | onzeker op `!` |
| `‘kom terug!’:de lamp brandt` | onzeker op `!` |
| `“Gereed.”,dat verschijnt` | onzeker op `.` |
| `‘kom terug!’,Dat` | onzeker, reden „binnen een ingesloten citaat” |
| T20 zonder spatie | onzeker + de latere zekere grens |

- **Behouden:** `‘kom terug’,dat` (geen slotteken) (0,0); `‘Klaar. Ga door’,dat` (interne punctuatie) (0,0). De spatievarianten uit v2 zijn ongewijzigd groen.
- **Geen pass-heuristiek:** het scheidingsteken en de ontbrekende spatie worden nergens als bewijs voor samenhang gebruikt.

### R3 — codevrijstelling alleen bij positief ondersteunde voorbeeldcontext

**Oorzaak:** v2 stelde elke afkorting met functie `afkorting` vrij, en daaronder vallen ook onbekende gestippelde lettervormen (`_GESTIPPELDE_AFKORTING`, bijvoorbeeld `q.z.`).

**Fix:**

- De vrijstelling geldt alleen nog als het woord vóór de punt in `_VOORBEELDAANKONDIGING = frozenset({"bijv"})` staat én er een afsluitende code volgt (`_afsluitende_code`, ongewijzigd).
- `bijv.` betekent zelf „bijvoorbeeld” en kondigt dus positief een voorbeeld aan; dat is de ondersteuning uit T08 en beide referenties.
- **Bewust niet `bv`:** dat staat ook voor „besloten vennootschap”, dus het voorbeeldbewijs is dubbelzinnig. Evenmin andere afkortingen (`ca.`, `max.`, maanden) of onbekende gestippelde vormen.
- Er is geen nieuwe grammaticale heuristiek. Het is geen algemene vrijstelling na afkortingen.

**Resultaat:**

- Weer onzeker, zoals op de /8-base, met reden „afkorting gevolgd door een hoofdletter”:
  - `houder volgens q.z. AB-12.`
  - `houder volgens q.z. AB-12`
  - `houder, ca. R7.`
  - `houder, bv. R7.`
- T08 houdt alleen de echte zekere grens „R7. De laatste positie” (fail).
- De v2-tegenhangers (`bijv. R7 bevat`, `bijv. R7, R8`, `bijv. De`, `bijv. NVR.`, `bijv. Rood7.`, `enz. R7.`) blijven onzeker.
- **Bewijs voor generalisatie ontbreekt** voor andere voorbeeldaankondigers (`bv.`, `vb.`, `o.a.`). Die blijven daarom onzeker.

### Documentatie in de code

De moduledocstring, het contractcommentaar (/9) en de docstrings van `_scheider_na_citaat` en de testmodule zijn bijgewerkt naar deze afbakening.

**Toetsinstructie:** geen wijziging nodig. De `/9`-regel in `reference.md` noemt „ook na een komma, puntkomma of dubbele punt” zonder spatievoorwaarde, en de codevrijstelling staat er niet in. Hash ongewijzigd: `77eda8f6…`.

## Tests

In `test_def770_citaatcorrectie_zinsgrenzen.py` staan nu 44 segmentatiegevallen, 12 meer dan in v2. Elk geval controleert het exacte aantal grenzen, met soort, teken op de positie, passage en reden.

- **R2, zes doelgevallen:**
  - `citaat-komma-zonder-spatie`
  - `citaat-puntkomma-zonder-spatie`
  - `citaat-dubbelepunt-zonder-spatie`
  - `citaat-punt-komma-zonder-spatie`
  - `citaat-komma-hoofdletter-zonder-spatie`
  - `T20-zonder-spatie`
- **R2, twee behoudgevallen:** `citaat-zonder-slotteken-zonder-spatie` en `citaat-intern-zonder-spatie`.
- **R3, vier gevallen:** `onbekende-afkorting-code`, `onbekende-afkorting-code-einde`, `andere-afkorting-code` en `bv-code`.

De proeflabels zijn niet aangepast; de proefbindingstests zijn ongewijzigd. Er zijn geen historische data gewijzigd.

## Commando's en exits (`logs/def770-citaatbeleid/`)

`PY` = `/Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python`. Pytest-runs gaan via `PY logs/def770-citaatbeleid/pytest-log-v2.py <naam> <args>`, met cwd app, JUnit, het commando plus de exit in de log, en weigering tot overschrijven.

| Stap | Log | Exit | Resultaat |
|---|---|---|---|
| Herstelkopie (`herstelkopie-maken-v3.py` → `herstelkopie-v3/`) | `herstelkopie-maken-v3.log` | 0 | 3/3 GELIJK (classifier, testmodule, reference.md) |
| RED op de v2-bron, alleen de nieuwe module | `red-v3.log`/`.xml` | 1 | 63 tests, 10 failures: precies de 6 R2- en 4 R3-doelgevallen. De behoudgevallen slaagden al. |
| GREEN, 6 zinsgrensbestanden (vóór Black) | `green-v3.log`/`.xml` | 0 | 513 tests, 0 failures |
| Lint (`lint-v3.py`): Ruff 0.16.5 `--version`/`check`, Black `--check` op 2 bestanden, `make PY=… lint` | `lint-v3.log` | 0/0/1/2 | Black: alleen opmaak in mijn eigen v3-hunks |
| `black -q` op dezelfde 2 bestanden | — | 0 | |
| Lint opnieuw (`lint-v3b.py`) | `lint-v3b.log` | 0/0/0/0 | schoon |
| Gerichte regressie `-m unit` (na Black): 6 zinsgrensbestanden + dezelfde set als v2 | `regressie-v3.log`/`.xml` | 0 | 1066 tests, 0 failures |
| Offline integratie `--timeout=120` | `integratie-v3.log`/`.xml` | 0 | 28 tests, 0 failures, 1 bestaande skip |
| 24 gevallen van de al geziene v1-proef, /8 vs /9 (`proefvergelijking-v2.py`) | `proefvergelijking-v3.log` | 0 | Ongewijzigd t.o.v. v2: alleen T08, T15, T17 en T20 wijzigen zoals bedoeld; zinsstatus 23/24 (T21 `not_evaluated`) |
| Hashes en delta-diff (`hashes-en-diffs-v3.py`) | `hashes-en-diffs-v3.log`, `diff-v2-naar-v3.patch` | 0 | zie hieronder |

**Volledige suite: niet gestart**, conform de opdracht. Na de v3-bron is geen canonieke gate gedraaid.

## Hashes (SHA256)

| Bestand | v2 | v3 |
|---|---|---|
| `src/domain/int01/zinsgrenzen.py` | `bdefb3e38d351408ecd4a6192ed198f4830eb8a892e55874d63623f85f469ea2` | `23e9c0b65d862074b4d5fb1de79c570172ebd0fc9cc00f67c98756550e3644cc` |
| `tests/unit/validation/test_def770_citaatcorrectie_zinsgrenzen.py` | `69c6af43d3fb68b12419c7e48014f2e7fa70f3faad5679a499a9847746ad10f9` | `3940415295a07cf106c1d3940d5c1e7d763eb3293088435090c02d5a3fde33d4` |
| skills `definitie-toetsregels/reference.md` | `77eda8f6…63c1` | ongewijzigd |
| `test_def770_int01_zinsgrenzen.py` | `b9ca8295…0834` | ongewijzigd |
| `test_def770_herstel_zinsgrenzen.py` | `4472cb40…248f` | ongewijzigd |
| `test_def770_restherstel_zinsgrenzen.py` | `d514de40…61bf` | ongewijzigd |
| `test_def770_citaatbeleid_zinsgrenzen.py` | `3ce8f737…732f` | ongewijzigd |
| `test_def770_vervolg_zinsgrenzen.py` | `d5fe8252…d302` | ongewijzigd |

- Delta v2 → v3: `diff-v2-naar-v3.patch`, sha256 `6885c27208659124bc48b0391ff98ce253453e1f726314de3806e1c2b52dd3f0`.
- De cumulatieve diff t.o.v. /8 is te reconstrueren uit `herstelkopie-v2/` en de huidige werkboom.
- `git diff --name-only HEAD -- docs config src/services/prompts src/toetsregels scripts Makefile` is leeg. De generatieskill is ongewijzigd.
- De `cowork-exports`-zips in de skills-worktree zijn van de coördinator; niet aangeraakt.

## Beperkingen

- Een scheidingsteken aan het tekstenende (`‘kom terug!’,`) blijft zonder kandidaat, want er volgt geen verdere tekst. Dat is ongewijzigd en niet onderzocht.
- Andere scheidingstekens (`-`, `—`) zijn niet onderzocht; voor die tekens is geen kandidaatverlies aangetoond.
- De codevrijstelling is bewust smal (alleen `bijv.`). Dat kan terecht onzekere meldingen opleveren bij andere voorbeeldaankondigers; die zijn conservatief en niet vrijgesteld.
- De 24-gevallenvergelijking is ontwikkelbewijs op een al geziene set, geen acceptatie.

Gestopt voor dezelfde reviewer.
