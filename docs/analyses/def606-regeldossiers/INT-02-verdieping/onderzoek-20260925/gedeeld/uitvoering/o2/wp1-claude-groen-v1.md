# DEF-835 WP1 — rapport Claude Code CLI, GREEN v1

26 september 2026 · uitvoerder: Claude Code CLI (Opus 5.5), sessie `177f1484-4e5c-482e-b431-450befdab835`, dezelfde sessie als RED · opdracht: `wp1-opdracht-claude-groen-v1.md`. Leidend: `plan-v1.md` WP1, `akkoord-wp1-v1.md` en `wp1-opdracht-claude-v1.md`. RED-rapport: `wp1-claude-rood-v1.md`.

**Status: GREEN met bewijs gereed.** Er is niets gecommit of gepusht en er is geen PR gemaakt. Er is geen netwerk gebruikt, geen modelcall gedaan, geen `.env` gelezen en geen productiedata aangeraakt. Bestaande bestanden zijn niet gewijzigd en er is niets verwijderd.

## Bestanden (exact de vijf inhoudelijke bestanden)

Werkboom `.claude/worktrees/DEF-835-int02-o2`, branch `feature/DEF-835-int02-o2`, HEAD `84bdc8c1b060ab50a1bd1428aed778bb2ed6007f`. `git diff --stat` is leeg: er zijn geen getrackte wijzigingen.

| Bestand | Regels | SHA-256 | Ten opzichte van RED |
|---|---|---|---|
| `src/domain/int02/__init__.py` | 6 | `7c581491801ded0b0ab20e46ef54c8c477d930480dc93dc1fbe40256e8e961cb` | ongewijzigd |
| `src/domain/int02/contract.py` | 788 | `915d2537dd243d6d5d7719339a6bfc986240dc2c9fa27bc4cd4b31b0696094f5` | stubs vervangen door het contract |
| `tests/unit/domain/test_def835_int02_contract.py` | 1104 | `989ac11c9d17f0c87c192135d055233b1c3eadef0a4deeae78f93b8497d129e4` | **ongewijzigd** (dezelfde hash als RED) |
| `tests/fixtures/def835_int02_ontwerpgevallen.json` | 414 | `e18adb97279fa0fe75889df3541186c9341051c33348d1dd848526867239867d` | **ongewijzigd** |
| `docs/architectuur/contracts/int02_assessment_contract_v1.md` | 173 | `189be99a7284994630fd324bf8da80f416bfd868ac7bc54010f32865e2940e48` | nieuw |

Totaal 2485 regels. De raming was 650–950; de overschrijding valt onder de geautoriseerde omvangverruiming. `contract.py` telt 788 regels, inclusief docstrings, de letterlijke meldingssjablonen en de uitvouwing van samengestelde voorwaarden door Black. Er is geen generieke infrastructuur of extra package toegevoegd en geen duplicatie van bestaande modules. Het `int03`-/`ess03`-patroon is alleen als voorbeeld gelezen.

**Tests niet aangepast.** Alle 162 RED-tests zijn onveranderd groen geworden. Geen enkele test bleek aantoonbaar onjuist.

## Bewijs (map `bewijs/`)

| Bestand | SHA-256 | Inhoud |
|---|---|---|
| `wp1-groen-v1.log` | `546ae245492f1960a5b88531031cf9d6f51c68192a41c8002c89010d1d36fac0` | pytest: **162 passed in 0.51s, exit 0** |
| `wp1-groen-lint-v1.log` | `66b4e3535c031d1fef3da40e8bb10a49df07babb8267d985e2f344373d1c1a95` | `ruff check`: "All checks passed!", exit 0 · `black --check`: "3 files would be left unchanged", exit 0 · `ruff format --check`: "3 files already formatted", exit 0 |
| `wp1-groen-extra-controles-v2.log` | `ebf01c640af553b514da7ee6681091d3c1ac249b8792d5c2c46ee5d098d04a24` | Omzeilings- en mutatiecontroles op de eindcode (zie hieronder), exit 0. Het uitgevoerde script staat volledig in het log. |
| `wp1-groen-extra-controles-v1.log` | `60d1e5de6a532443929a0510d98ae800c0646d5e5f7e454613f65e2d0fad9557` | Dezelfde controles 1–16, gedraaid vóór de laatste kleine wijziging (validatie van `Actualiteit`), met gelijke uitkomsten. Bewaard, geen eindbewijs. |

Elk log vermeldt tijdstip, werkboom, branch, HEAD, commando en exitcode. `wp1-groen-v1.log`, `wp1-groen-lint-v1.log` en `wp1-groen-extra-controles-v2.log` bevatten de SHA-256 van de bestanden die ze beoordeelden; dat is voor alle drie de eindversie `contract.py` `915d2537…`.

Commando's, telkens met `/Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python`:
- `-m pytest tests/unit/domain/test_def835_int02_contract.py -o addopts= -q -ra`
- `-m ruff check src/domain/int02 tests/unit/domain/test_def835_int02_contract.py`
- `-m black --check src/domain/int02 tests/unit/domain/test_def835_int02_contract.py` (extra: `-m ruff format --check …`)

Formattering: `black` is alleen toegepast op `src/domain/int02/contract.py`. Ruff meldde N818 op de interne klasse `_Afgewezen`; ik heb die hernoemd naar `_AfwijzingError`.

### Verificatie buiten de testsuite (`wp1-groen-extra-controles-v2.log`)

Openbare constructors mogen de validatie niet omzeilen. Elk van deze gevallen wordt geweigerd met `Int02ContractError`:
1. `Int02Invoer` direct aangemaakt met een lijst als context.
2. `Int02Invoer` direct aangemaakt met een ruwe bron-dict.
3. `Bronpassage` met een lege ID.
4. `Binding` met een ongeldige hash.
5. `Uitvoering` met een niet-hashbare actor.

Een incoherent of gemanipuleerd document wordt nooit een actueel oordeel. Elk van deze gevallen geeft `error` met melding E:

6. Een direct samengesteld pass-document op een fail-oordeel.
7. `oordeel_json` gewijzigd naar een incoherente pass.
8. Een vervalste binding, zowel tegen de oude als tegen de nieuwe invoer.
9. De invoer vervangen door een string.
10. De kern in de snapshot gewijzigd naar een int.
11. Een corrupte `oordeel_json`.
12. Een bewaarde technische fout blijft `error`.

Tegenproef: een echt, ongewijzigd document blijft actueel (13).

Overige controles:
- Een niet-hashbaar verdict en een `Mapping` die geen `dict` is, geven `invalid_output` in plaats van een crash (14, 15).
- Een contextwaarde verplaatsen van organisatorische naar juridische context wijzigt `context_hash` (16). De binding is dus per veld en niet alleen over de waarden samen.

Mutatiebewijs: naïeve varianten zijn in het geheugen gepatcht, de repository is niet aangeraakt.

| Mutatie | Gevangen door |
|---|---|
| replay zonder herleidbaarheidscontrole | 3 failures (manipulatietests) |
| geen citaat-/grondcontrole | 14 failures |
| geen samenhangcontrole | 21 failures (alle inconsistente oordelen) |

Na herstel: 162 passed.

## Gerealiseerde API en interfacekeuzes

Volledig beschreven in `docs/architectuur/contracts/int02_assessment_contract_v1.md`. Kern:

- **`maak_invoer` / `Int02Invoer` / `Bronpassage`** (frozen).
  - Defensieve kopie; de kern wordt bytegelijk bewaard.
  - `bedoeling=None` betekent expliciet onbekend.
  - Validatie gebeurt in `__post_init__`, dus ook bij directe constructie.
  - Contextwaarden en bedoeling moeten niet-lege tekst zijn.
- **`Configuratie`** met gevraagde provider/model, normversie (standaard `def771-int02/2`), normhash, promptversie en routeringshash. Hashes zijn SHA-256 in kleine hex.
- **`Uitvoering`**.
  - `actor` is `ai`/`human`; `status` is `completed`/`failed`/`not_executed`.
  - Alleen bij `failed` hoort een transportcategorie: `timeout`, `transport` of `provider`.
  - Meetvelden zijn standaard `"unknown"`; `bool` telt niet als int en `float` telt niet als kosten.
  - De gerapporteerde `modelversie` staat hier.
- **`bereken_binding`**.
  - Hashes over canonieke JSON: begrip, kern, bedoeling, context per veld, en bronnen met ID en tekst.
  - Daarnaast de contract- en configuratievelden.
  - De gerapporteerde modelversie telt niet mee in de replayvergelijking: zij is vóór een nieuwe beoordeling onbekend. Zij staat wel in het document en telt mee in de herleidbaarheid.
- **`beoordeel`**.
  - Volgorde: NE → transportfout → niet uitgevoerd → structuur (`invalid_output`) → citaten en gronden (`invalid_citation`) → samenhang (`invalid_output`) → status en melding.
  - De structuur wordt volledig gecontroleerd vóór de citaten, zodat de foutcategorie niet afhangt van de volgorde van passages.
  - De meegegeven uitvoer wordt niet gemuteerd. Een afgewezen uitvoer wordt niet bewaard en nooit gerepareerd.
- **`Beoordelingsdocument`** (frozen).
  - Het oordeel staat als canonieke JSON-string in `oordeel_json`; `oordeel` geeft telkens een verse kopie.
- **`toets_actualiteit`**.
  - Volgorde: NE → geen document (`not_assessed`) → technische fout of niet-herleidbaar (`error`) → andere binding (`historical`) → het bewaarde oordeel.
  - Herleidbaar betekent: de onderdelen worden opnieuw via hun constructors gevalideerd en `beoordeel` levert exact hetzelfde document op.
- **`Actualiteit`** valideert status en reden: een reden hoort alleen bij `review_required`.
- **`Int02ContractError`** geldt uitsluitend voor fouten van de aanroeper. Een fout in de uitvoer van de beoordelaar is een document met status `error`, nooit een exceptie.

## Meldingen: letterlijk tegenover aanvulling

Deze teksten zijn letterlijk overgenomen uit synthese v5 §4 en staan in de tests, niet hardgecodeerd maar uit de synthese gelezen: V, VN, discretievariant, O, NE, E en Historisch.

Deze teksten zijn uitvoeringstekst van dit contract, met akkoord van de coördinator. Ze zijn in code en document als zodanig gemarkeerd:
- **Nog niet beoordeeld** volgt letterlijk de T-toestand: `INT-02 — Nog te beoordelen — beoordeling niet uitgevoerd.`
- **Niet van toepassing** vereist een reikwijdtegrond: `INT-02 — Niet van toepassing. {reikwijdtegrond}. Er is geen oordeel over de definitiekern.` Ik claim niet dat deze tekst uit de synthese komt.
- **Discretie**: de VN-basistekst ("een afweging") met geldig citaat en grond, gevolgd door de letterlijke discretievariant. Dit is een weergavekeuze en geen nieuwe norm.
- **Precies één vraag** wordt mechanisch gecontroleerd: één niet-lege tekst die eindigt op het enige vraagteken. Of de vraag gericht is, bewijst de code niet.

## Beperkingen en bewijsgrenzen

- **Geen persistentie.** Er is geen opslag en geen save/reload (DEF-626/WP5). De herleidbaarheidscontrole ontdekt incoherente en gedeeltelijke mutatie. Een volledig consistent vervalst document valt samen met een document dat met hetzelfde oordeel opnieuw via `beoordeel` is gemaakt. Authenticiteit en herkomst zijn een taak van de opslaglaag. Dit staat ook in het contractdocument.
- **Geen semantische kwaliteit.** De code bewijst niet dat een model de juiste functie, passage, vraag of dekking kiest. De fixturegevallen zijn ontwikkelgevallen met handmatig ingevulde responsen, geen goldset of hold-out (WP4).
- **Geen app-route.** Er zijn geen prompt, service, evaluator, UI, record, publiek resultaatveld of schema gewijzigd; niets is geactiveerd. O1 (`judgment_review`) blijft ongewijzigd.
- **Beperkte suite.** Alleen de nieuwe testmodule is gedraaid, geen volledige suite. De nieuwe code wordt nergens geïmporteerd buiten de eigen test, dus bestaande tests kunnen er niet door veranderen. Dit is niet met een volledige run bewezen.
- **NE-regel overgenomen.** De label-zonder-kernregel (`[^:.!?;\n]{1,80}:`) is overgenomen uit het O1-patroon in `judgment_review.py` en niet geïmporteerd, omdat het domein geen services mag importeren. Dat is bewuste duplicatie van één regex; hij is gemarkeerd in de code en het document.

## Omgeving

- `.claude/hooks/check-silent-exceptions.py` blijft de lokale symlink uit RED. **Niet committen.** Er zijn geen andere omgevingsaanpassingen gedaan.
- De hulpscripts voor de extra controles stonden in `/tmp`, buiten de repository. Hun volledige inhoud staat in de extra-controlelogs.
- De automatisch gegenereerde `.claude/handovers/WIP-snapshot.md` is niet aangeraakt.

## Voor de coördinator

Te committen voor de onafhankelijke review:
- de vijf inhoudelijke bestanden hierboven;
- dit rapport;
- `bewijs/wp1-groen-v1.log`, `bewijs/wp1-groen-lint-v1.log` en `bewijs/wp1-groen-extra-controles-v1.log` en `-v2.log`;
- de RED-artefacten (`wp1-claude-rood-v1.md`, `bewijs/wp1-rood-v1.log` en `-v2.log`).

Buiten de commit laten: de symlink.

**GREEN met bewijs gereed; wacht op coördinator.**
