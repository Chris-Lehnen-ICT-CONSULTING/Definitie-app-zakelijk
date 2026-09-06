"""
Test UI integratie met nieuwe services.

DEF-519: dit bestand was een importscript met prints en try/except-blokken die
elke fout wegprintten; pytest verzamelde nul nodes (exit 5) en de sys.path-regel
wees naar het niet-bestaande tests/integration/src. Het is nu een gewone
offline integrationtest: de echte TabbedInterface wordt gebouwd op eigen
tijdelijke databases en de servicebinding wordt inhoudelijk getoetst.
"""

from contextlib import contextmanager
from typing import Any
from unittest.mock import patch

import pytest

pytestmark = [pytest.mark.integration]


def _sluit_databaseverbinding(db: Any) -> None:
    """Sluit de thread-lokale SQLite-verbinding van een `DatabaseConnection`."""
    toestand = getattr(getattr(db, "_thread_local", None), "state", None)
    if toestand is not None:
        toestand.close()


def _sluit_container_verbindingen(container: Any) -> None:
    """Sluit de SQLite-verbindingen die deze container zelf opende."""
    from database.db_connection import DatabaseConnection

    gezien: set[int] = set()
    for instantie in list(getattr(container, "_instances", {}).values()):
        for houder in (instantie, getattr(instantie, "legacy_repo", None)):
            db = getattr(houder, "_db", None)
            if not isinstance(db, DatabaseConnection) or id(db) in gezien:
                continue
            gezien.add(id(db))
            _sluit_databaseverbinding(db)


def is_echte_service_adapter(service: Any) -> bool:
    """Herken de échte ServiceAdapter en sluit de dummy-fallback uit.

    Bewust geen `hasattr`: de dummy in `TabbedInterface.__init__` heeft
    `get_service_info` óók. Getoetst wordt het type én de inhoud die
    ServiceAdapter.get_service_info werkelijk teruggeeft.
    """
    from services.service_factory import ServiceAdapter

    if not isinstance(service, ServiceAdapter):
        return False
    info = service.get_service_info()
    return (
        info["service_mode"] == "container_v2"
        and info["architecture"] == "microservices"
        and info["version"] == "2.0"
    )


@pytest.fixture
def eigen_container(tmp_path):
    """Echte `ServiceContainer` op een verse database in `tmp_path`."""
    from services.container import ContainerConfigs, ServiceContainer

    container = ServiceContainer(
        {**ContainerConfigs.testing(), "db_path": str(tmp_path / "container.db")}
    )
    try:
        yield container
    finally:
        _sluit_container_verbindingen(container)


@contextmanager
def eigen_ui_grenzen(tmp_path, container, servicefabriek):
    """Bind de fabrieksgrenzen van `TabbedInterface` aan eigen echte instances.

    Drie grenzen: de containercache (`ui.cached_services`), de
    repositoryfabriek (`database.definitie_repository`) en de servicefabriek
    (`ui.tabbed_interface.get_definition_service`). Alle drie krijgen een échte
    instantie op eigen opslag in `tmp_path` — geen mock, geen repo- of
    gebruikersdatabase, geen providercalls.

    Dit is de enige cleanupimplementatie in dit bestand; zowel de goede binding
    als de kapotte binding lopen erdoorheen. Isolatiecontract:

    * de vooraf bestaande `_repository_singleton` blijft eigendom van de sessie:
      hij wordt bewaard en op identiteit teruggezet, en zijn verbinding wordt
      niet aangeraakt;
    * alleen wat binnen deze scope is aangemaakt (eigen repositories en een
      singleton die tijdens de scope verscheen) wordt gesloten;
    * herstel gebeurt in `finally`, dus ook op het foutpad.
    """
    from database import definitie_repository as repo_module
    from database.definitie_repository import DefinitieRepository
    from ui import cached_services, tabbed_interface

    ui_db = tmp_path / "ui-definities.db"
    vorige_singleton = repo_module._repository_singleton
    originelen = {
        (cached_services, "get_cached_service_container"): (
            cached_services.get_cached_service_container
        ),
        (repo_module, "get_definitie_repository"): (
            repo_module.get_definitie_repository
        ),
        (tabbed_interface, "get_definition_service"): (
            tabbed_interface.get_definition_service
        ),
    }
    eigen_repositories: list[Any] = []

    def _eigen_repository(*_a: Any, **_k: Any):
        if not eigen_repositories:
            eigen_repositories.append(DefinitieRepository(str(ui_db)))
        return eigen_repositories[0]

    cached_services.get_cached_service_container = lambda *_a, **_k: container
    repo_module.get_definitie_repository = _eigen_repository
    tabbed_interface.get_definition_service = servicefabriek
    try:
        yield {"ui_db": ui_db, "container": container}
    finally:
        for (module, naam), origineel in originelen.items():
            setattr(module, naam, origineel)

        # Een singleton die tijdens de scope is ontstaan is van ons; de vooraf
        # bestaande blijft ongemoeid en houdt zijn identiteit.
        huidige_singleton = repo_module._repository_singleton
        if huidige_singleton is not None and huidige_singleton is not vorige_singleton:
            _sluit_databaseverbinding(huidige_singleton._db)
        repo_module._repository_singleton = vorige_singleton

        for repo in eigen_repositories:
            _sluit_databaseverbinding(repo._db)


@pytest.fixture
def ui_grenzen(tmp_path, eigen_container):
    """De goede route: de echte `ServiceAdapter` achter de servicefabriek."""
    from services.service_factory import ServiceAdapter

    adapter = ServiceAdapter(eigen_container)
    with eigen_ui_grenzen(tmp_path, eigen_container, lambda: adapter) as grenzen:
        yield {**grenzen, "adapter": adapter}


class TestUIServiceIntegratie:
    """De UI-servicebinding op eigen, echte instances."""

    def test_service_adapter_reports_container_v2(self, eigen_container):
        """De echte ServiceAdapter draait op de eigen container."""
        from services.service_factory import ServiceAdapter

        adapter = ServiceAdapter(eigen_container)

        assert is_echte_service_adapter(adapter)
        assert adapter.container is eigen_container
        assert adapter.orchestrator is eigen_container.orchestrator()

    def test_tabbed_interface_binds_real_service_adapter(self, ui_grenzen):
        """TabbedInterface krijgt de echte adapter, niet de dummy-fallback."""
        from ui.tabbed_interface import TabbedInterface

        with patch("streamlit.session_state", {}):
            interface = TabbedInterface()

        assert interface.definition_service is ui_grenzen["adapter"]
        assert is_echte_service_adapter(interface.definition_service)
        assert type(interface.definition_service).__name__ != "_DummyService"

        # Eigen opslag: de UI praat met de tijdelijke database, niet met data/.
        assert interface.container is ui_grenzen["container"]
        assert interface.repository.db_path == str(ui_grenzen["ui_db"])

        # Wiring: de generatiehandler deelt exact dezelfde service én repository.
        assert interface.generation_handler.definition_service is (
            interface.definition_service
        )
        assert interface.generation_handler.repository is interface.repository
        assert interface.checker.repository is interface.repository

    def test_broken_service_binding_falls_back_and_is_detected(
        self, tmp_path, eigen_container
    ):
        """Discriminator: een kapotte servicegrens haalt de positieve proef niet.

        De productfallback mag blijven bestaan; deze node toetst alleen dat de
        controle in `is_echte_service_adapter` hem niet voor de echte service
        aanziet. Zonder deze node zou de positieve assertie vacuüm kunnen zijn.
        """
        from ui.tabbed_interface import TabbedInterface

        def _kapotte_servicefabriek():
            raise RuntimeError("servicefabriek onbeschikbaar (testgrens)")

        with eigen_ui_grenzen(tmp_path, eigen_container, _kapotte_servicefabriek):
            with patch("streamlit.session_state", {}):
                interface = TabbedInterface()

            assert not is_echte_service_adapter(interface.definition_service)
            assert (
                interface.definition_service.get_service_info()["service_mode"]
                == "dummy"
            )
            assert interface.generation_handler.definition_service is (
                interface.definition_service
            )

    def test_singleton_identity_survives_error_path(self, tmp_path, eigen_container):
        """Foutpadproef op het isolatiecontract van `eigen_ui_grenzen`.

        Een synthetische, vooraf bestaande singleton mag de scope ongeschonden
        overleven: zelfde identiteit én bruikbare verbinding. De repository die
        binnen de scope ontstaat is van ons en moet gesloten zijn — ook wanneer
        de scope met een exception eindigt.
        """
        from database import definitie_repository as repo_module
        from database.definitie_repository import DefinitieRepository
        from services.service_factory import ServiceAdapter

        vorige = DefinitieRepository(str(tmp_path / "vorige-singleton.db"))
        # De échte handle vóór de scope. `get_connection()` opent stilzwijgend
        # een nieuwe verbinding als de oude gesloten is, dus alleen een leesactie
        # op deze bewaarde handle bewijst dat hij ongemoeid bleef.
        oude_handle = vorige._db.get_connection()
        origineel = repo_module._repository_singleton
        repo_module._repository_singleton = vorige
        tweede: Any = None
        try:
            adapter = ServiceAdapter(eigen_container)

            def _scope_die_faalt():
                nonlocal tweede
                with eigen_ui_grenzen(tmp_path, eigen_container, lambda: adapter):
                    # Eigen tweede repository op verse tmp-data, als gedeelde
                    # singleton gezet: precies de mutatie die hersteld moet
                    # worden.
                    tweede = DefinitieRepository(str(tmp_path / "tweede.db"))
                    repo_module._repository_singleton = tweede
                    assert tweede is not vorige
                    raise AssertionError("opgewekte foutpadproef")

            with pytest.raises(AssertionError, match="opgewekte foutpadproef"):
                _scope_die_faalt()

            # Oude identiteit terug, niet slechts een gelijkwaardig object.
            assert repo_module._repository_singleton is vorige

            # Nog steeds dezelfde handle bij `vorige`: er is niets gesloten en
            # stilzwijgend heropend.
            assert vorige._db._thread_local.state.connection is oude_handle

            # En die bewaarde handle doet het nog: rechtstreeks lezen, zonder
            # heropenroute. Was hij gesloten, dan faalt dit met een
            # ProgrammingError in plaats van een verse verbinding te krijgen.
            rij = oude_handle.execute(
                "SELECT begrip FROM definities WHERE id = 1"
            ).fetchone()
            assert rij is not None

            # De binnen de scope aangemaakte verbinding is gesloten.
            toestand = getattr(tweede._db._thread_local, "state", None)
            assert toestand is None or toestand.connection is None
        finally:
            _sluit_databaseverbinding(vorige._db)
            if tweede is not None:
                _sluit_databaseverbinding(tweede._db)
            repo_module._repository_singleton = origineel
