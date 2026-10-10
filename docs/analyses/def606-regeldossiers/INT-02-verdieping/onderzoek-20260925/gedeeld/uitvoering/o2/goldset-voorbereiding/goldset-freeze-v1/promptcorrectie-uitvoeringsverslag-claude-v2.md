# INT-02 O2 — promptcorrectie /2: verslag Claude Code CLI-uitvoerder (v2)

30 september 2026. Dit is een vervolg op `promptcorrectie-uitvoeringsverslag-claude-v1.md`, in dezelfde uitvoerdersessie. Opdrachten: `promptcorrectie-opdracht-claude-v1.md` en de vervolgopdracht van de coördinator (implementatie). Werkboom `DEF-835-int02-o2`, branch `feature/DEF-835-int02-o2`, HEAD `a9fb4a0b7444d073813182b662056e7c3265fc7c` (ongewijzigd, geen commit). Deze uitvoerder startte geen agents of andere CLI-sessies.

## Rood (door de coördinator)

`promptcorrectie-rood-coordinator-v1.log`, r.78–83: **5 failed, 57 passed**. Rood waren alleen `test_promptversie_is_twee_na_de_promptcorrectie`, `test_systeemprompt_bevat_de_aanwijzing_als_een_regel[fail|citaat]` en `test_aanwijzing_staat_na_de_invoerduiding_en_voor_de_posities[fail|citaat]`. Die run is gedaan op testblob `bb7fb96d380d78f70cb1d063832f4e4bc0f42ca7`, met de dienst op HEAD-blob `e6ee8eba7177fceb64e06d1961789e2685b55078`. Vóór deze bewerking heb ik beide blobs teruggelezen; ze waren ongewijzigd.

## Wijziging

| Bestand | Blob vóór | Blob na | Diff |
| --- | --- | --- | --- |
| `src/services/validation/int02_assessment_service.py` | `e6ee8eba…` (= HEAD; herstelkopie `promptcorrectie-herstelkopie-int02_assessment_service.py-v1`) | `e0af1bd813107fc7dc2787a7430f1ee2a1555b76` | +25/−3 (28 regels) |
| `tests/unit/services/prompts/test_def835_int02_prompt.py` | `30a7e7e2…` (= HEAD; herstelkopie `promptcorrectie-herstelkopie-test_def835_int02_prompt.py-v1`) | `1f1823b78eb33cd5b3b273d23036754b948df804` | +57/−1 |

Dienst (`int02_assessment_service.py`):

1. `PROMPT_VERSION = "def835-int02-prompt/2"`; het commentaar noemt `/1` en `/2`.
2. In `_systeemprompt` staat na het blok `Invoer:` (na "- Geef geen score, …") en vóór `Posities:` een nieuw blok `Oordeel en citaten:`. De twee regels daarin zijn tekstueel identiek aan `AANWIJZING_FAIL` en `AANWIJZING_CITAAT` in de test; ik heb de stringconcatenaties handmatig per fragment vergeleken, inclusief de spaties op de naden. `grep -c "controleer vóór"` geeft in beide bestanden 1, dus dezelfde bytevorm van "vóór".
3. Niet gewijzigd: `T_TEKST`, de norm en het regelrecord, het contract, de parser, de statusmapping, de cache, de container en de activering. Er zijn geen lokale citaatcorrectie en geen casusuitkomst toegevoegd.

Test (`test_def835_int02_prompt.py`):

- De bestaande test `test_promptversie_is_eigen_en_verschilt_van_contract_en_norm` verwacht nu `/2` in plaats van `/1`. De test blijft staan; er is geen test of geval verwijderd.
- In mijn eigen, eerder toegevoegde testcode staan twee vormcorrecties voor black, zonder inhoudelijk effect. Eén string van `AANWIJZING_CITAAT` staat nu tussen dubbele quotes in plaats van enkele; de waarde is identiek. De fragmentenlijst in `test_aanwijzingen_zijn_invoeronafhankelijk_en_zonder_casusmateriaal` staat in een variabele, zodat de regel niet boven de 88 tekens uitkomt. Daardoor verschilt de testblob van de blob die de coördinator rood draaide (`bb7fb96…` → `1f1823b…`). De asserties en waarden zijn gelijk; een nieuwe rode run is daarom niet nodig. Een herhaalde run tegen de herstelkopie van de dienst kan dit bevestigen.

Volledige diff: `git diff -- src/services/validation/int02_assessment_service.py tests/unit/services/prompts/test_def835_int02_prompt.py` op de genoemde blobs.

## Teststatus in deze sessie

- `/Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python -m pytest tests/unit/services/prompts/test_def835_int02_prompt.py -p no:cacheprovider -q -rA --tb=short` gaf opnieuw `This command requires approval`. Volgens de opdracht ben ik daarna met testen gestopt. **Er is in deze sessie geen groene en geen regressierun waargenomen.**
- Een statische controle via `python3 -c` (AST-vergelijking, zonder import) werd door `security-guard.sh` geblokkeerd ("Gevaarlijke Python one-liner"). Ik heb die niet omzeild.
- Wel uitgevoerd: `grep -nE '^.{89,}$'` op beide bestanden. Dat vond alleen drie regels die al vóór deze wijziging bestonden: test r.72, en dienst r.505 en r.560 (voorheen r.483 en r.538; netto +22 regels). Lint (ruff/black) is niet gedraaid.
- Statisch gecontroleerd: `tests/unit/validation/test_def835_int02_evaluator.py` gebruikt `def835-int02-prompt/1` en `/2` alleen als synthetische fixturewaarden (r.189, 669, 798), los van de moduleconstante. `tests/unit/validation/test_def835_int02_assessment_service.py` gebruikt de constante `PROMPT_VERSION` of een monkeypatch (r.771, 780, 908, 1432, 1449). Geen van beide pint een prompthash. De runner (`scripts/analysis/def835_int02_modelproef.py`, r.1083–1105) leest `PROMPT_VERSION` en hasht de gerenderde prompt tijdens een run; er is daar geen vaste waarde.

Wat de coördinator nog moet draaien:
- groen: de prompttest hierboven;
- regressie: `tests/unit/validation/test_def835_int02_assessment_service.py`, `tests/unit/validation/test_def835_int02_evaluator.py`, `tests/unit/domain/test_def835_int02_contract.py`, `tests/unit/services/test_def835_int02_container.py` en `tests/unit/services/orchestrators/test_def835_int02_wrappers.py`;
- lint: `make lint`, plus ruff/black op het testbestand.

## Open punten voor review

1. **Formulering "grond uit kern, bevestigde bedoeling, context of bronpassage"** in plaats van de voorstelterm "betekenisgrond". De bestaande prompt rekent de kern niet tot de betekenisgrond, terwijl T grond uit de kern wel toestaat. Een letterlijke overname zou daardoor een `fail` op een expliciet voorschrift in de kern kunnen uitsluiten. Zie v1, § Open punt. De reviewer moet toetsen of deze lezing overeenkomt met T en het voorstel.
2. Offline tests bewijzen alleen dat de tekst aanwezig is, niet het modelgedrag voor C105, C107 of C112. Daarvoor is een nieuwe, apart geaccordeerde proef nodig met een nieuw manifest.
3. `prompt_sha256` en de WP1-binding veranderen door `/2`. Eerdere documenten en caches op `/1` worden daardoor historisch. Dat is bedoeld (versiegebonden contract). Het v2-bewijs blijft ongewijzigd.

Er is niets gecommit, gepusht of gemerged. Er zijn geen live aanroepen gedaan, geen sleutels gebruikt, geen Actions of activering aangeraakt en geen hold-outbestanden gelezen.

Bronnen: `promptcorrectie-rood-coordinator-v1.log` r.78–83; `promptcorrectie-voorstel-v1.md` r.12–17; `promptcorrectie-uitvoeringsverslag-claude-v1.md`; `git diff`/`git hash-object` in de werkboom (30-09-2026); `tests/unit/validation/test_def835_int02_evaluator.py` r.187–193, 660–672, 791–805.
