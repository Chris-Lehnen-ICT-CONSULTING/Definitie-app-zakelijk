"""Hermetische omgeving voor de unit-suite (DEF-573).

`ConfigManager()` laadde bij elke constructie `.env` in `os.environ`. Lokaal
vond een unit-test daardoor de echte API-keys van de ontwikkelaar; in CI (waar
geen `.env` staat) niet. Dat verschil maskeerde bugs in beide richtingen: een
test die juist toetst dát een key ontbreekt slaagde lokaal ten onrechte, en een
test die stiekem op een key leunde faalde alleen in CI.

Deze conftest maakt de unit-suite lokaal identiek aan CI:

* `.env` wordt niet geladen (`DEFINITIE_DISABLE_DOTENV=1`);
* de DI-container krijgt niet-lege dummy-keys, net als de CI-job.

`dummy` is bewust niet-leeg (de container bouwt) en begint niet met `sk-`, zodat
de skip-guards van de integration-suite blijven werken.

Bewust op module-niveau en niet in een fixture: conftest wordt vóór de collectie
geïmporteerd, terwijl een fixture pas bij de eerste test draait — te laat als een
module bij import al een `ConfigManager()` bouwt.

De integration-suite heeft deze conftest niet en mag `.env` dus wél gebruiken:
die tests hebben een echte key nodig om iets zinnigs te doen.
"""

import os

from config.dotenv_loader import DISABLE_ENV_VAR

# Geen .env in de unit-suite: expliciet, niet via setdefault. Een .env van de
# ontwikkelaar mag het testresultaat niet bepalen.
os.environ[DISABLE_ENV_VAR] = "1"

# Spiegelt de env van de CI-test-job (.github/workflows/test.yml). setdefault:
# een bewust gezette shell-waarde blijft leidend.
for _sleutel in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "OPENAI_API_KEY_PROD"):
    os.environ.setdefault(_sleutel, "dummy")
