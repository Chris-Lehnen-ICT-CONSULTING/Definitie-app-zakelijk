## P2-poortcorrectie (codex-review-v2) — klaar

**Code** (`src/domain/sources/contract.py`, `is_bruikbare_hyperlink`): `delen.port` wordt nu binnen het `try/except ValueError` gelezen; een niet-numerieke (`:ongeldig`) of buiten-bereik (`:99999`) poort geeft `False`. Docstring noemt de poortvoorwaarde. Geen overige wijzigingen.

**Tests** (`tests/unit/domain/test_def806_verwijzing_hyperlink.py`): `ONBRUIKBARE_LINKS` + `https://intern.example:ongeldig/awb` en `:99999/awb`; `BRUIKBARE_LINKS` + `https://intranet.example:8443/awb#art-1-3`; nieuwe `test_uitzondering_geldt_ook_bij_ongeldige_poort` (uitzondering via helper toegepast); `test_menselijke_correctie_volgt_dezelfde_definitie_van_bruikbaar` geparametriseerd over `https://` en `:ongeldig` (correctie geweigerd).

**Resultaat (stdout, exact toegestane commando's)**
- RED vóór fix: `4 failed` — beide ongeldige poorten via helper/AI-pad, uitzondering (`accepted_exception None`), correctie (`applied True`).
- GREEN na fix: `48 passed` (alle 48 tests, 0 failures).
- Black: `2 files left unchanged` (al conform).

Geen commit/push; overige suites/lint/bewijs bij de coördinator. Stop.