# DEF-770 T08 voorbeeldgetal — resultaat Claude-uitvoerder v4

Uitvoerder: Claude Code CLI-sessie 442a98fb-a377-403f-996e-433cf4a664fc. Ik heb geen agents, reviewers of extra CLI-sessies gestart en geen API-calls gedaan. Er is niets gecommit, gepusht of gebundeld.
Invoer: `logs/def770-citaatbeleid/astra-acceptatie-v2.md`, alleen bevinding 3 (LOW, T08).
Bases: app `58f70cb1dc1e3f78381f420a716220058a623105`, skills `201053a192222b91e459f0b0c13b3170c1c01911`. Beide HEADs zijn ongewijzigd.

**Buiten scope en ongewijzigd:**

- T17 en T24: de beleidsvraag aan de gebruiker staat open. Geen code, testverwachting of skillregel gewijzigd.
- R1 en R2 zijn ongewijzigd.
- Geen nieuwe acceptatieset gemaakt of gelezen. Proef-v2 alleen gelezen, als ontwikkelbron voor T08.

**Geen acceptatieclaim.** Geen volledige suite gestart; die volgt pas na de gerichte herreview.

## Delta (contract /9 → /10)

**Oorzaak:** in `_classificeer_afkorting` wordt de cijferroute (`begin == "cijfer"`) afgehandeld vóór de voorbeeldvrijstelling uit /9. Die vrijstelling gold bovendien alleen voor een code met hoofdletter. Daardoor gaf `bijv. 12.` „afkorting gevolgd door een getal: mogelijk nieuw zinsbegin”.

**Fix in `src/domain/int01/zinsgrenzen.py`:**

- **Nieuwe hulpfunctie `_aangekondigd_voorbeeld(kandidaat)`:** geeft waar als het woord in `_VOORBEELDAANKONDIGING` (ongewijzigd `{"bijv"}`) staat én er een afsluitend voorbeeld volgt. De hoofdletterroute gebruikt deze functie (zelfde gedrag als /9), en de cijferroute nu ook, ná de bestaande `verwijzing`/`_VOOR_GETAL`-uitzondering.
- **Hernoemd en verbreed:** `_afsluitende_code` → `_afsluitend_voorbeeld`, dat naast `_CODE` ook één getal (`_GETAL`, bestaande regex) accepteert. De afsluitvoorwaarde is ongewijzigd: direct één slotteken of het tekstenende; geen woorden of komma erna.
- **Contract:** `CONTRACTVERSIE = "def770-int01/10"`, met toelichtend commentaar en een aangepaste moduledocstring-bullet.

**Geen algemene vrijstelling voor afkorting plus getal.** Onzeker met „afkorting gevolgd door een getal” blijven, zoals in het bestaande contract:

| Geval | Voorbeeld |
|---|---|
| andere aankondiger | `bv. 12.` |
| onbekende afkorting | `q.z. 12.` |
| mogelijk zinslot | `enz. 12.`, `enz. 12 stuks` |
| getal met vervolgwoorden | `bijv. 12 velden` |
| getal met komma | `bijv. 12, 13` |

`ca.`/`max.`/maanden (`_VOOR_GETAL`) en verwijzingen gaven al „geen”; dat blijft zo.

**De echte grens blijft.** De punt na `12` wordt door `_classificeer_getal` beoordeeld: zeker, „getal aan zinseinde gevolgd door een nieuw zinsbegin”.

**Toetsreferentie:** in `skills/definitie-toetsregels/reference.md` is alleen de contractregel `def770-int01/9` → `/10` gewijzigd. Er is geen nieuwe normtekst en geen wijziging voor T17/T24.

## Tests

**Nieuw: `tests/unit/validation/test_def770_voorbeeldgetal_zinsgrenzen.py`**

- 11 segmentatiegevallen die elk het exacte aantal grenzen toetsen, met soort, teken op de positie, passage en reden:
  - positief: `p2-T08`, `getal-slot`, `getal-einde`, `getal-decimaal-slot`, en `code-slot` (behoud van /9);
  - negatief: `getal-met-vervolg`, `getal-met-komma`, `andere-aankondiger`, `onbekende-afkorting`, `mogelijk-zinslot`, `mogelijk-zinslot-afsluitend`.
- Proefbinding, alleen lezend: de tekst is gelijk aan proef-v2 `t24-gevallen-v1.json`, en de adjudicatie (`sentence_status` fail, `boundary_passage` „bijv. 12. De achterkant”) wordt gevolgd, zonder extra grens.
- Service op beide laadpaden: fail met alleen `zinsgrens_1`, plus compactheid en begrijpelijkheid open.
- Currentness: een `/9`-uitkomst geldt niet als actueel.
- Contract `/10`.

**Aangepast, alleen de contractverwachting:**

- De contracttests in `test_def770_citaatcorrectie_…`, `…citaatbeleid_…`, `…restherstel_…` en `…herstel_zinsgrenzen.py` → `/10`, met docstring-trace naar astra-acceptatie-v2.
- De currentness-parametrisatie in de herstel-test heeft `def770-int01/9` erbij gekregen.

## Commando's en exits (`logs/def770-citaatbeleid/`)

`PY` = `/Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python`. Pytest-runs gaan via `PY logs/def770-citaatbeleid/pytest-log-v2.py <naam> <args>`, met cwd app, JUnit, het commando plus de exit in de log, en weigering tot overschrijven.

| Stap | Log | Exit | Resultaat |
|---|---|---|---|
| Herstelkopie (`herstelkopie-maken-v4.py` → `herstelkopie-v4/`) | `herstelkopie-maken-v4.log` | 0 | 6/6 GELIJK |
| RED op /9, alleen de nieuwe module | `red-v4.log`/`.xml` | 1 | 17 tests, 9 failures: `p2-T08`, `getal-slot`, `getal-einde`, `getal-decimaal-slot`, adjudicatiebinding, service ×2, currentness /9, contract /10. De negatieve tegenhangers, `code-slot` en de proeftekstbinding slaagden al. |
| GREEN, 7 zinsgrensbestanden | `green-v4.log`/`.xml` | 0 | 534 tests, 0 failures |
| Lint (`lint-v4.py`): Ruff 0.16.5 `--version`/`check`, Black `--check` op 6 bestanden, `make PY=… lint` | `lint-v4.log` | 0/0/0/0 | schoon |
| Gerichte regressie `-m unit` (7 zinsgrensbestanden + dezelfde set als v2/v3) | `regressie-v4.log`/`.xml` | 0 | 1087 tests, 0 failures |
| Offline integratie `--timeout=120` | `integratie-v4.log`/`.xml` | 0 | 28 tests, 0 failures, 1 bestaande skip |
| Proef-v2, 24 gevallen, /9 vs /10 (`proefvergelijking-v4.py`) | `proefvergelijking-v4.log` | 0 | Alleen T08 wijzigt: de extra onzekere grens na `bijv.` vervalt en de zekere grens blijft. T17 en T24 zijn onveranderd (beleidsvraag open). Zinsstatus conform adjudicatie: 21/24 → 21/24, omdat T08 al fail was; het verschil zit in de diagnostiek. |
| Hashes en diff (`hashes-en-diffs-v4.py`) | `hashes-en-diffs-v4.log`, `diff-v4.patch` | 0 | zie hieronder |

**Volledige suite: niet gestart**, conform de opdracht.

## Hashes (SHA256, base → v4)

| Bestand | Base | v4 |
|---|---|---|
| `src/domain/int01/zinsgrenzen.py` | `23e9c0b65d862074b4d5fb1de79c570172ebd0fc9cc00f67c98756550e3644cc` | `aac0d0c9f66ba96e0e78b73b8f4ab901eaa5ed837dc0446e2a8c40b4057802b8` |
| `tests/unit/validation/test_def770_voorbeeldgetal_zinsgrenzen.py` | — (nieuw) | `a86ab5d35c49d7cf4714a58e83326d29cbb9f15402eafa721d758306887c2ce5` |
| `tests/unit/validation/test_def770_citaatcorrectie_zinsgrenzen.py` | `39404152…33d4` | `783c1261247cb1ae0aadea701952d808e2e3157fc772cdad9666a2a3b2afa833` |
| `tests/unit/validation/test_def770_citaatbeleid_zinsgrenzen.py` | `3ce8f737…732f` | `2094783a938a1022301d975033e9b3d8fc4cb62dfca28218cf332fc9371db3a1` |
| `tests/unit/validation/test_def770_herstel_zinsgrenzen.py` | `4472cb40…248f` | `ca15b3d34be5f8b809f8e431583ccf1405a4b83c57a4f13db44614bddfbe9dfc` |
| `tests/unit/validation/test_def770_restherstel_zinsgrenzen.py` | `d514de40…61bf` | `c11d31300b2932e2b7c6339a25a8b2a0399a891e2f377b2f5ea57c2f5e265139` |
| skills `definitie-toetsregels/reference.md` | `77eda8f6…63c1` | `83bae6fd19a8baffb95613ead2284cf4527664fd26e84934867f0bc8b686d148` |

- Diff tegen herstelkopie-v4 (= bases): `diff-v4.patch`, sha256 `371be7385a83ecdb2a048d292ca33a4bb28ae0d8cea0777496711681451e61ba`.
- `git diff --name-only HEAD -- docs config src/services/prompts src/toetsregels scripts Makefile` is leeg. De generatieskill is ongewijzigd.
- Proef-v2, alleen gelezen:
  - `t24-gevallen-v1.json` `91bdd440…effe`
  - `t24-adjudicatie-v1.json` `085a0612…b998`
  - `t24-resultaat-nieuw-v1.json` `d4190b70…c7a7d`, gelijk aan astra-acceptatie-v2.

## Beperkingen

- De vrijstelling blijft beperkt tot `bijv.`. Numerieke voorbeelden na `bv.`, `vb.` of `o.a.` blijven onzeker; daarvoor is geen positief bewijs.
- Negatieve getallen, bereiken (`12-14`) en getallen met eenheid (`12 mm`) zijn niet onderzocht. Een eenheid geldt als vervolgwoord en blijft dus onzeker.
- T17- en T24-afwijkingen van de proef-v2-adjudicatie blijven bestaan tot het gebruikersbesluit.

Gestopt voor dezelfde reviewer.
