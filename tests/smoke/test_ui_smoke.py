"""Quick UI smoke test voor beide modes.

DEF-519: deze smoke-test bouwde de UI op de gedeelde productiefabrieken. Die
openen `data/definities.db` in de checkout, en de offline-gate weigert dat
terecht — beide nodes vielen daarop om in `root-final-acceptance-01/make.log`.
De test draait nu op een échte `ServiceContainer`, `ServiceAdapter` en
repository met eigen databases in `tmp_path`, via exact de grenzen- en
herstelhelpers die `tests/integration/test_ui_integration.py` al bewijst:
containercache, repositoryfabriek en servicefabriek worden daar gebonden en in
`finally` teruggezet, en alleen wat binnen de scope is aangemaakt wordt
gesloten. Geen mock, geen vervangen validator of storage, geen dummy-service,
geen app- of browserstart.

De parametrisatie blijft staan maar claimt geen twee architecturen: sinds
US-043 levert `services/service_factory.py::get_definition_service` altijd de
V2-adapter. `USE_NEW_SERVICES` wordt via `monkeypatch` gezet zodat de
omgevingswaarde na afloop hersteld wordt; beide nodes toetsen dezelfde
gegarandeerde V2-bedrading, en dat is precies wat hier bewezen wordt.

De `sys.path`-regel naar `tests/smoke/src` is vervallen: dat pad bestaat niet;
`pytest.ini` zet `pythonpath = src`.
"""

from unittest.mock import patch

import pytest

# De grenzenhelper, de adaptercontrole en de opruiming komen uit de bewezen
# UI-integratiescope; ze worden hier hergebruikt, niet nagebouwd.
from tests.integration.test_ui_integration import (
    _sluit_container_verbindingen,
    eigen_ui_grenzen,
    is_echte_service_adapter,
)

pytestmark = [pytest.mark.smoke]


@pytest.mark.parametrize("use_new_services", [False, True], ids=["legacy", "new"])
def test_ui_mode(use_new_services, tmp_path, monkeypatch):
    """De UI-bedrading komt in beide modes op eigen, echte instances uit.

    De échte servicefabriek wordt aangeroepen — alleen haar containergrens
    wijst naar een eigen container op een database in `tmp_path`, zodat er geen
    enkele gebruikers- of repositorydatabase aan te pas komt. Wat daarna wordt
    getoetst is identiteit, niet vorm: dezelfde adapter, container,
    orchestrator, repository en handlerbinding als de bestaande
    UI-integratiecontracten eisen.
    """
    from services import service_factory
    from services.container import ContainerConfigs, ServiceContainer
    from ui.tabbed_interface import TabbedInterface

    monkeypatch.setenv("USE_NEW_SERVICES", str(use_new_services).lower())

    container = ServiceContainer(
        {**ContainerConfigs.testing(), "db_path": str(tmp_path / "container.db")}
    )
    try:
        # Enige grens die verlegd wordt: de gedeelde singletoncontainer. Via
        # monkeypatch, dus hij staat na deze node weer op de productiefabriek.
        monkeypatch.setattr(service_factory, "get_cached_container", lambda: container)

        service = service_factory.get_definition_service()
        assert service is not None
        # Oorspronkelijke smoke-verwachting: de service draagt het
        # generatiecontract.
        assert hasattr(service, "generate_definition") or hasattr(
            service, "genereer_definitie"
        )

        # Dezelfde fabriek levert in beide modes de echte V2-adapter op de eigen
        # container: één architectuur, geen legacy-tweede pad meer (US-043).
        assert is_echte_service_adapter(service)
        assert service.container is container
        assert service.orchestrator is container.orchestrator()

        with eigen_ui_grenzen(tmp_path, container, lambda: service) as grenzen:
            with patch("streamlit.session_state", {}):
                interface = TabbedInterface()

            assert interface is not None
            # Identiteit, niet gelijkenis: exact deze service, nooit de fallback.
            assert interface.definition_service is service
            assert type(interface.definition_service).__name__ != "_DummyService"
            assert interface.container is container

            # Eigen opslag: precies het tijdelijke pad, nooit data/definities.db.
            assert interface.repository.db_path == str(grenzen["ui_db"])

            # Bedrading: handler en checker delen dezelfde service en repository.
            assert interface.generation_handler.definition_service is (
                interface.definition_service
            )
            assert interface.generation_handler.repository is interface.repository
            assert interface.checker.repository is interface.repository
    finally:
        # Alleen de verbindingen die deze node zelf opende.
        _sluit_container_verbindingen(container)
