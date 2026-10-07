# INT-02 O2 — promptcorrectie /2: rode tests (v1)

30 september 2026. Claude Code CLI-uitvoerder, werkboom `DEF-835-int02-o2`, branch `feature/DEF-835-int02-o2`, HEAD `a9fb4a0b7444d073813182b662056e7c3265fc7c`.

## Status: rode tests geschreven, rode run NIET uitgevoerd

De rode tests staan in `tests/unit/services/prompts/test_def835_int02_prompt.py` (alleen toevoegingen: +55 regels; blob na wijziging `bb7fb96d380d78f70cb1d063832f4e4bc0f42ca7`). De productiecode is **niet** aangeraakt.

Bedoeld exact rood commando (vanuit de werkboomroot, Python 3.13-projectvenv):

```
.venv/bin/python -m pytest tests/unit/services/prompts/test_def835_int02_prompt.py -p no:cacheprovider -q -rA --tb=line
```

Dit commando kon in deze sessie niet worden uitgevoerd. Er is **geen** testresultaat waargenomen, dus hier staat ook geen resultaat. Gebeurtenissen in deze sessie:

| Poging | Uitkomst |
| --- | --- |
| `/Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python -m pytest …` | `This command requires approval` (niet-interactieve sessie; pad buiten de werkmap) |
| `ln -s /Users/chrislehnen/Projecten/Definitie-app/.venv .venv` (git-ignored via `.git/info/exclude:18`) | `This command requires approval`; symlink niet aangemaakt |
| `.venv/bin/python -m pytest …` | `no such file or directory: .venv/bin/python` (de werkboom heeft geen eigen venv) |
| `python3 -m pytest --version` | `python3` is 3.14.7 (Homebrew), `No module named pytest`; bovendien niet de vereiste 3.13 |

De permissie is niet omzeild via een `python3`-subprocess of een symlink vanuit Python.

## Toegevoegde tests en verwachte uitkomst op HEAD (niet waargenomen)

Wat hieronder staat, is afgeleid uit het lezen van de code, niet uit een run.

| Test | Verwachting op HEAD | Reden |
| --- | --- | --- |
| `test_promptversie_is_twee_na_de_promptcorrectie` | rood | `PROMPT_VERSION == "def835-int02-prompt/1"` |
| `test_systeemprompt_bevat_de_aanwijzing_als_een_regel[fail]` | rood | de regel `AANWIJZING_FAIL` bestaat niet |
| `test_systeemprompt_bevat_de_aanwijzing_als_een_regel[citaat]` | rood | de regel `AANWIJZING_CITAAT` bestaat niet |
| `test_aanwijzing_staat_na_de_invoerduiding_en_voor_de_posities[fail]` | rood | de aanwijzing ontbreekt |
| `test_aanwijzing_staat_na_de_invoerduiding_en_voor_de_posities[citaat]` | rood | de aanwijzing ontbreekt |
| `test_aanwijzingen_zijn_invoeronafhankelijk_en_zonder_casusmateriaal` | groen (bewaking) | geen casusfragment in norm of prompt; `grep -c` op `INT-02.json` en de dienst gaf 0 |

De bestaande test `test_promptversie_is_eigen_en_verschilt_van_contract_en_norm` (assert `/1`) blijft op HEAD groen. Na de productiewijziging wordt hij rood en moet zijn `/1`-regel vervallen: de nieuwe test legt `/2` vast.

## Herstelkopieën (vóór bewerking, byte-identiek aan HEAD)

- `promptcorrectie-herstelkopie-int02_assessment_service.py-v1`, git-blob `e6ee8eba7177fceb64e06d1961789e2685b55078` = `HEAD:src/services/validation/int02_assessment_service.py`;
- `promptcorrectie-herstelkopie-test_def835_int02_prompt.py-v1`, git-blob `30a7e7e2fd85e871cdaaa588a405114478a467d9` = `HEAD:tests/unit/services/prompts/test_def835_int02_prompt.py`.

## Nodig om verder te gaan

Een uitvoerdersessie die de 3.13-projectvenv mag draaien, bijvoorbeeld met `--add-dir /Users/chrislehnen/Projecten/Definitie-app/.venv` en een allowlist voor `Bash(/Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python -m pytest:*)`. Een andere route is een door de coördinator aangelegde `.venv`-symlink in de werkboom plus de allowlist `Bash(.venv/bin/python -m pytest:*)`. Daarna: rood waarnemen en vastleggen (nieuwe versie van dit bestand), en pas dan de productiecode.
