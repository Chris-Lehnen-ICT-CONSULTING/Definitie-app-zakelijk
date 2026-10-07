# INT-02 O2 — promptcorrectie /2: verslag Claude Code CLI-uitvoerder (v1)

30 september 2026. Opdracht: `promptcorrectie-voorstel-v1.md`, waarmee Chris op 30-09-2026 heeft ingestemd (volgens de opdracht van de coördinator). Werkboom `DEF-835-int02-o2`, branch `feature/DEF-835-int02-o2`, HEAD `a9fb4a0b7444d073813182b662056e7c3265fc7c`. Deze uitvoerder startte geen agents of andere CLI-sessies.

## Uitkomst: gestopt na de rode tests door een omgevingsblokkade

- **Gedaan:** herstelkopieën gemaakt en de rode tests toegevoegd in `tests/unit/services/prompts/test_def835_int02_prompt.py`. Zie `promptcorrectie-rood-v1.md`.
- **Niet gedaan:** de rode run is niet uitgevoerd. De 3.13-projectvenv vraagt goedkeuring, en die kan deze niet-interactieve sessie niet krijgen. Daarom is ook de productiecode (`src/services/validation/int02_assessment_service.py`) **niet** gewijzigd: de opdracht eist eerst een vastgelegd rood resultaat. Er is geen groene run en geen regressierun.
- Niet aangeraakt: T-tekst, norm/regelrecord, contract (`domain/int02/contract.py`), schema, statusmapping, container/activering, hold-outbestanden, bestaande dossierbestanden, runner. Geen live aanroep, geen sleutel, geen commit, push, merge of Actions.

## Voorgenomen productiewijziging (nog niet toegepast)

1. `PROMPT_VERSION = "def835-int02-prompt/2"`, met een commentaarregel `/2` bij de bestaande `/1`-uitleg.
2. In `_systeemprompt` komt na het blok `Invoer:` (na "- Geef geen score, …") en vóór `Posities:` een nieuw blok. De twee regels zijn exact `AANWIJZING_FAIL` en `AANWIJZING_CITAAT` uit de test:
   - `- Voor "fail" moet de aangeleverde grond uit kern, bevestigde bedoeling, context of bronpassage de functie als handelingsvoorschrift ("actor_prescription") of discretionaire beslisregel ("discretionary_decision_rule") zelfstandig dragen. Is de bedoeling onbekend ("bedoeling": null) en kan de passage zowel een begripscriterium als een voorschrift zijn, kies dan bij ontbrekende beslissende grond "insufficient_information" met precies één gerichte vraag. Leid "fail" niet enkel af uit een kwalitatief of modaal woord of uit het feit dat een actor een oordeel vormt.`
   - `- Kopieer elk passage- en grondcitaat letterlijk uit het opgegeven veld. Bepaal "start" nulgebaseerd, bereken "end" = "start" + len("quote") in Python-Unicode-codepoints en controleer vóór verzending dat tekst[start:end] == quote voor de exacte tekst van dat veld. Lukt dat niet, verzin dan geen citaat of positie.`
3. In de bestaande test `test_promptversie_is_eigen_en_verschilt_van_contract_en_norm` vervalt alleen de regel `assert PROMPT_VERSION == "def835-int02-prompt/1"`. De test zelf blijft staan.

## Open punt voor de coördinator en de reviewer: formulering "betekenisgrond"

Het voorstel zegt "de aangeleverde **betekenisgrond** moet de functie … zelfstandig dragen". In de bestaande systeemprompt heet "betekenisgrond" uitsluitend begrip, bevestigde bedoeling, context en bronpassages: de kern valt daarbuiten. De T-tekst staat echter uitdrukkelijk grond **uit de kern** toe. Een letterlijke overname zou een `fail` op een expliciet voorschrift in de kern zelf (zoals het C105-type) kunnen uitsluiten. Dat zou neerkomen op een normverschuiving.

Daarom luidt de getoetste regel "de aangeleverde grond uit kern, bevestigde bedoeling, context of bronpassage". Die opsomming volgt T letterlijk. Bij een voorkeur voor de letterlijke voorstelformulering hoeft alleen `AANWIJZING_FAIL` in de test te wijzigen, samen met dezelfde regel in de dienst.

## Overige risico's

- De nieuwe "fail"-aanwijzing kan het model in grensgevallen vaker naar `insufficient_information` duwen. Of C105 `fail` blijft, is alleen met een nieuwe, apart geaccordeerde proef vast te stellen. Offline tests bewijzen alleen dat de tekst aanwezig is, niet het modelgedrag.
- Voor de citaataanwijzing geldt hetzelfde: het contract blijft ongeldige posities afwijzen, en de prompt maakt een ongeldig citaat alleen minder waarschijnlijk.
- De omgeving: `python3` op deze Mac is 3.14.7 zonder pytest. De projectnotitie "systeem-Python 3.9" is verouderd.

## Volgende stap (vereist actie van de coördinator)

Herstart dezelfde uitvoerdersopdracht met toestemming voor de projectvenv (zie `promptcorrectie-rood-v1.md`, § Nodig om verder te gaan). Daarna volgen: rood waarnemen en vastleggen, de productiewijziging hierboven, groen, en gerichte regressie (`tests/unit/services/prompts/test_def835_int02_prompt.py`, `tests/unit/validation/test_def835_int02_assessment_service.py`, `tests/unit/validation/test_def835_int02_evaluator.py`, `tests/unit/domain/test_def835_int02_contract.py`, `tests/unit/services/test_def835_int02_container.py`, `tests/unit/services/orchestrators/test_def835_int02_wrappers.py`), plus `make lint`.

## Bestanden in deze sessie

| Bestand | Actie |
| --- | --- |
| `tests/unit/services/prompts/test_def835_int02_prompt.py` | bewerkt (+55, alleen toevoegingen) |
| `…/goldset-freeze-v1/promptcorrectie-herstelkopie-int02_assessment_service.py-v1` | nieuw |
| `…/goldset-freeze-v1/promptcorrectie-herstelkopie-test_def835_int02_prompt.py-v1` | nieuw |
| `…/goldset-freeze-v1/promptcorrectie-rood-v1.md` | nieuw |
| `…/goldset-freeze-v1/promptcorrectie-uitvoeringsverslag-claude-v1.md` | nieuw (dit verslag) |

Bronnen: `promptcorrectie-voorstel-v1.md` r.12–17; `kwalificatie-uitvoeringsverslag-v2.md` r.9–15; `src/services/validation/int02_assessment_service.py` r.126, 132–164, 331–428; `tests/unit/services/prompts/test_def835_int02_prompt.py` r.217–219; `Makefile` r.3–4; `pytest.ini` r.8.
