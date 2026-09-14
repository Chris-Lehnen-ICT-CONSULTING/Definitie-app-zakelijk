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

from dataclasses import replace
from types import MappingProxyType
from typing import Any

import pytest

from config.dotenv_loader import DISABLE_ENV_VAR

_DUMMY_KEYS = ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "OPENAI_API_KEY_PROD")


@pytest.fixture(autouse=True)
def _hermetische_unit_omgeving(monkeypatch):
    """Isoleer elke unit-test van `.env` en van echte API-keys."""
    monkeypatch.setenv(DISABLE_ENV_VAR, "1")
    for sleutel in _DUMMY_KEYS:
        monkeypatch.setenv(sleutel, "dummy")


@pytest.fixture
def service_met_totaalscore():
    """Fabriek: `ModularValidationService` op de echte regelset mínus de
    regels zonder cijfer (DEF-622).

    Sinds DEF-622 draagt CON-01 `score_policy: no_score` en is de totaalscore
    met de echte 53-regelset niet beschikbaar (`overall_score` None, gate
    geblokkeerd op `overall_score_unavailable`). Tests die de score- en
    gate-aggregatie zélf bewijzen — soft floor, gate-consistentie, "een error
    of een duplicaat beweegt het cijfer niet" — hebben een regelset nodig
    waarin de totaalscore wél bestaat, anders vergelijken ze `None` met
    `None` en bewijzen ze niets meer.

    Dit is bewust géén productnoemer: de productieketen berekent geen score
    "over de rest". Het is een synthetische regelset voor het bewijs van de
    aggregatiemechanica, gepubliceerd als volledige generatie zodat de
    readiness-guard hem als compleet ziet.
    """
    from services.validation.modular_validation_service import (
        ModularValidationService,
    )
    from services.validation.readiness import bepaal_readiness
    from toetsregels.manager import get_toetsregel_manager
    from toetsregels.runtime_contract import ScorePolicy

    def _bouw(repository: Any | None = None) -> ModularValidationService:
        svc = ModularValidationService(
            get_toetsregel_manager(), None, None, repository=repository
        )
        echt = svc._ververs_state_indien_nodig()
        assert echt.readiness.ready, "de echte regelset dekt het contract niet"
        behouden = tuple(
            code
            for code in echt.internal_rules
            if echt.rule_records[code].score_policy is not ScorePolicy.NO_SCORE
        )
        assert len(behouden) < len(echt.internal_rules), (
            "de echte regelset bevat geen regel zonder cijfer meer; deze "
            "fixture is dan overbodig"
        )
        svc._snapshot = replace(
            echt,
            readiness=bepaal_readiness(behouden, behouden),
            contract_rule_ids=behouden,
            internal_rules=behouden,
            rule_records=MappingProxyType(
                {code: echt.rule_records[code] for code in behouden}
            ),
            json_rules=MappingProxyType(
                {code: echt.json_rules[code] for code in behouden}
            ),
            default_weights=MappingProxyType(
                {
                    code: gewicht
                    for code, gewicht in echt.default_weights.items()
                    if code in behouden
                }
            ),
            pattern_cache={},
            rules_loaded_count=len(behouden),
            rules_expected_count=len(behouden),
        )
        return svc

    return _bouw
