# tests/manual/scratch/

Diagnostische scratch-scripts, verplaatst uit `tests/unit/` (DEF-493).

Deze bestanden hadden `pytestmark = unit` maar zijn **geen echte tests**: ze
bevatten geen asserts (alleen `print`) of draaien module-level side-effects
(service-/UI-instantiatie, DB-open, API-key-check) tijdens collectie. Daardoor
telden ze vals-groen mee in de unit-suite en vervuilden ze elke unit-run.

`tests/manual/` staat in `norecursedirs` (`pytest.ini`), dus deze scripts
draaien niet mee in de reguliere suite. Ze zijn bewaard (niet verwijderd) omdat
ze handmatig-diagnostische waarde houden.

| Script | Doel (handmatig) |
|--------|------------------|
| `test_env.py` | Check of `OPENAI_API_KEY` geladen is (toont géén key-waarde). |
| `test_new_default.py` | Toont welk service-type de factory default teruggeeft. |
| `test_ui_new_services.py` | Instantieert `TabbedInterface` + toont service-info. |
| `test_ui_scores.py` | Roept `_determine_ontological_category` aan (echte AI). |
| `test_def126_simple.py` | Analyseert prompt-module-duplicatie via regex. |
| `test_contradictions.py` | "Forensische" check op regel-tegenstrijdigheden (laadt de dode `regels/*.py`-laag — zie DEF-464/494). |
| `test_csv_import_websocket.py` | Simuleert CSV-import-timing (echte dekking: `test_csv_import_hardening.py` + `test_csv_import_timeout.py`). |

**Toekomstig werk:** `test_contradictions.py` zou een echte regressietest kunnen
worden als het tegen de *actieve* `validators/*.py`-laag draait en asserteert
(niet tegen de dode `regels/*.py`). Buiten scope van DEF-493.
