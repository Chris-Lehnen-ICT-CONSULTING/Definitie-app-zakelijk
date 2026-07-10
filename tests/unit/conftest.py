"""Hermetische omgeving voor de unit-suite (DEF-573).

`ConfigManager()` laadde bij elke constructie `.env` in `os.environ`. Lokaal
vond een unit-test daardoor de echte API-keys van de ontwikkelaar; in CI (waar
geen `.env` staat) niet. Dat verschil maskeerde bugs in beide richtingen: een
test die juist toetst dát een key ontbreekt slaagde lokaal ten onrechte, en een
test die stiekem op een key leunde faalde alleen in CI.

Deze fixture maakt elke unit-test identiek aan de CI-test-job:

* `.env` wordt niet geladen (`DEFINITIE_DISABLE_DOTENV=1`);
* de DI-container krijgt niet-lege dummy-keys.

`dummy` is bewust niet-leeg (de container bouwt) en begint niet met `sk-`, zodat
de skip-guards van de integration-suite blijven werken. De keys worden
*geforceerd*, niet via `setdefault`: een echte sleutel in de shell van de
ontwikkelaar hoort nooit in een unit-test terecht te komen — dat zou een echte
API-call kunnen veroorzaken.

Bewust een **function-scoped autouse fixture** en géén module-niveau-mutatie van
`os.environ`. `pytest.ini` heeft `testpaths = tests`, dus `pytest -m integration`
(zoals `make test-integration`) collecteert óók `tests/unit/` en importeert deze
conftest — de markerfilter deselecteert pas ná de import. Een mutatie op
module-niveau zou dan proces-breed lekken en de integration-suite stilzwijgend
uithollen: skip-guards slaan over, of tests draaien tegen de key "dummy".
Monkeypatch herstelt de omgeving na elke test.
"""

import pytest

from config.dotenv_loader import DISABLE_ENV_VAR

_DUMMY_KEYS = ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "OPENAI_API_KEY_PROD")


@pytest.fixture(autouse=True)
def _hermetische_unit_omgeving(monkeypatch):
    """Isoleer elke unit-test van `.env` en van echte API-keys."""
    monkeypatch.setenv(DISABLE_ENV_VAR, "1")
    for sleutel in _DUMMY_KEYS:
        monkeypatch.setenv(sleutel, "dummy")
