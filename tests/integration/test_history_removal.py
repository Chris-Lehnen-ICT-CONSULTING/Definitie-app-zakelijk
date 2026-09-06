"""Verificatie dat het History-tabblad verwijderd is — offline en op eigen data.

Het contract is ongewijzigd: de History-*tab* bestaat niet meer, terwijl de
history-*tabel* en haar trigger in de database intact blijven en de overige tabs
blijven werken.

Onder DEF-519 is uitsluitend de fixture en de foutafhandeling hersteld; er is
geen productiefunctionaliteit bijgekomen.

* Zes tests bouwden een `TabbedInterface`, die via `get_definitie_repository()`
  de repository-database (`data/definities.db`) opende. De offline-gate weigert
  dat terecht. De container- en repositoryfabriek krijgen nu een expliciet pad
  in `tmp_path`; de fabrieken zelf draaien onveranderd door — er wordt geen
  repository of container gemockt.
* Bronbestanden werden CWD-relatief opgezocht (`Path("src/ui/tabbed_interface.py")`,
  `Path("src/database/schema.sql")`), en een ontbrekende bron leverde een groene
  test of een skip op. De paden komen nu uit `__file__`; een ontbrekende
  verplichte bron is een fout.
* `test_database_history_table_intact` sloeg zichzelf over zodra
  `data/definities.db` ontbrak — precies de situatie in elke schone omgeving.
  De tabel wordt nu aangetoond op een verse database die door de
  productie-schema-init is aangelegd, met een echte INSERT en UPDATE en de
  werkelijke history-inhoud.
* `test_no_history_in_tab_rendering` liep over een hardgecodeerde lijst
  tabsleutels die niet meer bestaat (`export`, `management`) en ving daarna
  élke exception weg (`except Exception: pass`). Het rendert nu de actuele
  sleutels uit `interface.tab_config` en maakt zowel een ontbrekende handler
  als een weggeslikte fout zichtbaar: `_render_tab_content` vangt fouten zelf af
  en meldt ze via `st.error`.
* De `except`-blokken die alleen faalden als het woord "history" in de melding
  stond, verborgen iedere andere fout. Ze zijn weg.

BRONBEVINDING — geen stille vervanging: `src/ui/components/export_tab.py`
bestaat niet meer. De export is bij DEF-447 opgegaan in
`ui.components.tabs.import_export_beheer.ImportExportBeheerTab`, wat
`test_other_tabs_remain_functional` in dit bestand al vaststelt.
`test_export_functionality` importeerde `ExportTab`, ving de `ImportError` op en
werd groen omdat het woord "history" niet in de melding stond — de test toetste
dus niets. Zij richt zich nu op die opvolger, met de echte repository in plaats
van een `Mock`.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

pytestmark = [pytest.mark.integration]

#: Repository-root, afgeleid uit dit bestand (tests/integration/…), zodat de
#: bronopzoeking niet van de werkdirectory afhangt.
PROJECTWORTEL = Path(__file__).resolve().parents[2]

#: Sleutel uit `TabbedInterface.tab_config` → attribuut met de tabcomponent.
#: Deze afspraak wordt hieronder getoetst tegen de actuele configuratie: een
#: hernoemde of nieuwe tab valt op in plaats van stil te worden overgeslagen.
TABCOMPONENT_PER_SLEUTEL = {
    "generator": "definition_tab",
    "edit": "edit_tab",
    "expert": "expert_tab",
    "import_export_beheer": "import_export_beheer_tab",
}

BEGRIP = "def519_history_begrip"
DEFINITIE_EERST = "Eerste definitietekst voor de history-verificatie."
DEFINITIE_DAARNA = "Gewijzigde definitietekst voor de history-verificatie."


def lees_verplichte_bron(relatief_pad: str) -> str:
    """Lees een verplicht bronbestand, repo-root-relatief.

    Ontbreken is een fout: zonder de bron valt er niets te toetsen en zou de
    test anders groen worden op een bestand dat er niet is.
    """
    pad = PROJECTWORTEL / relatief_pad
    if not pad.is_file():
        raise FileNotFoundError(
            f"Verplichte bron ontbreekt: {pad}. Deze suite toetst de echte "
            "broncode; zonder dat bestand valt er niets te toetsen."
        )
    return pad.read_text(encoding="utf-8")


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


def _lees_geschiedenis(db_path: str, definitie_id: int) -> list[dict[str, Any]]:
    """Lees de history-rijen via een **nieuwe** verbinding op het bestand."""
    verbinding = sqlite3.connect(db_path)
    try:
        verbinding.row_factory = sqlite3.Row
        rijen = verbinding.execute(
            "SELECT begrip, definitie_oude_waarde, definitie_nieuwe_waarde, "
            "wijziging_type FROM definitie_geschiedenis WHERE definitie_id = ? "
            "ORDER BY id",
            (definitie_id,),
        ).fetchall()
        return [dict(rij) for rij in rijen]
    finally:
        verbinding.close()


def maak_testrecord(begrip: str, definitie: str):
    """Een DRAFT-record voor de databasetests in deze module."""
    from database.definitie_repository import (
        DefinitieRecord,
        DefinitieStatus,
        SourceType,
    )

    return DefinitieRecord(
        begrip=begrip,
        definitie=definitie,
        categorie="proces",
        organisatorische_context="[]",
        juridische_context="[]",
        status=DefinitieStatus.DRAFT.value,
        source_type=SourceType.MANUAL.value,
        wettelijke_basis="[]",
    )


class Rendermarkering:
    """UI-grensdubbel: registreert dat déze tabcomponent gerenderd is.

    Bewust géén `Mock`: `_render_tab_content` vangt elke exception zelf af, dus
    een dubbel dat stilletjes van alles accepteert zou een ontbrekende route
    niet zichtbaar maken. Deze klasse telt uitsluitend `render()`-aanroepen.
    """

    def __init__(self, naam: str) -> None:
        self.naam = naam
        self.aantal = 0

    def render(self, *args: Any, **kwargs: Any) -> None:
        self.aantal += 1


@pytest.fixture
def eigen_repository(tmp_path):
    """Echte `DefinitieRepository` op een verse database in `tmp_path`.

    De database wordt aangelegd door de gewone schema-init van de repository
    (`DatabaseConnection.init_database()` → `src/database/schema.sql`), dus
    tabellen en triggers zijn de productie-artefacten.
    """
    from database.definitie_repository import DefinitieRepository

    repo = DefinitieRepository(str(tmp_path / "definities.db"))
    try:
        yield repo
    finally:
        _sluit_databaseverbinding(repo._db)


@pytest.fixture
def ui_grenzen(tmp_path, monkeypatch):
    """Eigen container- en repositorydatabase voor de UI-tests.

    De twee fabrieksgrenzen die `TabbedInterface.__init__` gebruikt —
    `utils.container_manager.ServiceContainer` (via `get_cached_container`) en
    `database.definitie_repository.get_definitie_repository` — krijgen een pad
    in `tmp_path`. De echte container en de echte repository worden gebouwd,
    alleen op eigen opslag. Alles wat deze fixture liet aanmaken wordt in
    `finally` gesloten en de gedeelde caches worden hersteld.
    """
    from database import definitie_repository as repo_module
    from services.container import ServiceContainer
    from utils import container_manager

    container_db = tmp_path / "container-definities.db"
    ui_db = tmp_path / "ui-definities.db"
    containers: list[Any] = []

    def _container_met_eigen_db(config):
        container = ServiceContainer({**config, "db_path": str(container_db)})
        containers.append(container)
        return container

    originele_fabriek = repo_module.get_definitie_repository

    def _repository_met_eigen_db(_db_path=None):
        return originele_fabriek(str(ui_db))

    monkeypatch.setattr(container_manager, "ServiceContainer", _container_met_eigen_db)
    monkeypatch.setattr(
        repo_module, "get_definitie_repository", _repository_met_eigen_db
    )
    container_manager.get_cached_container.cache_clear()
    repo_module.clear_repository_singleton()
    try:
        yield ui_db
    finally:
        for container in containers:
            _sluit_container_verbindingen(container)
        singleton = repo_module._repository_singleton
        if singleton is not None:
            _sluit_databaseverbinding(singleton._db)
        repo_module.clear_repository_singleton()
        container_manager.get_cached_container.cache_clear()


class TestHistoryTabRemoval:
    """Test suite to verify History tab has been properly removed."""

    def test_no_history_tab_imports(self):
        """Verify no imports of HistoryTab remain in codebase."""
        content = lees_verplichte_bron("src/ui/tabbed_interface.py")

        assert "HistoryTab" not in content
        assert "history_tab" not in content

    def test_tabbed_interface_loads_without_history(self, ui_grenzen):
        """Test that TabbedInterface can be instantiated without History tab."""
        from ui.tabbed_interface import TabbedInterface

        with patch("streamlit.session_state", {}):
            interface = TabbedInterface()

        # Verify expected tabs exist (export/management zijn bij de refactor
        # geconsolideerd in import_export_beheer_tab — DEF-447)
        assert hasattr(interface, "definition_tab")
        assert hasattr(interface, "edit_tab")
        assert hasattr(interface, "expert_tab")
        assert hasattr(interface, "import_export_beheer_tab")

        # De History-tab is verwijderd, niet op None gezet: het attribuut
        # bestaat niet meer.
        assert not hasattr(interface, "history_tab")

    def test_tab_configuration_excludes_history(self, ui_grenzen):
        """Verify history is not in tab configuration."""
        from ui.tabbed_interface import TabbedInterface

        with patch("streamlit.session_state", {}):
            interface = TabbedInterface()

        assert "history" not in interface.tab_config

    def test_no_history_in_tab_rendering(self, ui_grenzen):
        """Elke geconfigureerde tab rendert zijn eigen component, zonder fout.

        `_render_tab_content` vangt exceptions zelf af en meldt ze via
        `st.error`; daarom is de afwezigheid van een foutmelding onderdeel van
        de assertie. Een sleutel zonder route rendert geen enkel component en
        valt zo op.
        """
        import streamlit as st

        from ui.tabbed_interface import TabbedInterface

        with patch("streamlit.session_state", {}):
            interface = TabbedInterface()

        sleutels = list(interface.tab_config)
        assert "history" not in sleutels
        assert set(sleutels) == set(TABCOMPONENT_PER_SLEUTEL), (
            "tab_config wijkt af van de bekende tabcomponenten: "
            f"{sleutels} vs {sorted(TABCOMPONENT_PER_SLEUTEL)}"
        )

        markeringen = {}
        for sleutel, attribuut in TABCOMPONENT_PER_SLEUTEL.items():
            markering = Rendermarkering(attribuut)
            setattr(interface, attribuut, markering)
            markeringen[sleutel] = markering

        for sleutel in sleutels:
            for markering in markeringen.values():
                markering.aantal = 0
            st.messages.clear()

            interface._render_tab_content(sleutel)

            gerenderd = {naam for naam, mark in markeringen.items() if mark.aantal == 1}
            assert gerenderd == {sleutel}, (
                f"Tab '{sleutel}' rendert {sorted(gerenderd)} in plaats van "
                "zichzelf — ontbrekende of verkeerde handler"
            )
            fouten = [bericht for soort, bericht in st.messages if soort == "error"]
            assert fouten == [], f"Tab '{sleutel}' meldde een fout: {fouten}"

    def test_database_history_table_intact(self, eigen_repository):
        """De history-tabel bestaat en vult zich op een verse productie-database.

        De database is aangelegd door de schema-init van de repository zelf, dus
        dit toetst het schema dat de applicatie in productie gebruikt — niet een
        losstaand testschema en niet de repository-database.

        Gemeten gedrag van de huidige code (niet afgeleid uit wat het "zou
        moeten" doen): via de repository levert een INSERT wél een history-rij
        op — niet van de trigger (die is AFTER UPDATE) maar van de
        Python-audit-laag, met type ``created``. De UPDATE voegt daar de rij(en)
        met oude en nieuwe tekst aan toe.

        Wat die ``created``-rij *niet* vastlegt, wordt hier bewust niet
        geasserteerd: dat zij op dit moment geen definitietekst meedraagt is een
        beperking van de huidige auditlaag, geen gewenste garantie. Het
        vastleggen van een rijker historiemodel hoort bij DEF-626, niet hier.
        """
        db_path = eigen_repository.db_path
        verbinding = sqlite3.connect(db_path)
        try:
            aanwezig = verbinding.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type='table' AND name='definitie_geschiedenis'"
            ).fetchone()
            assert aanwezig is not None, "History table should still exist"
            aantal = verbinding.execute(
                "SELECT COUNT(*) FROM definitie_geschiedenis"
            ).fetchone()[0]
            assert aantal == 0, "Een verse database begint zonder history"
        finally:
            verbinding.close()

        definitie_id = eigen_repository.create_definitie(
            maak_testrecord(BEGRIP, DEFINITIE_EERST)
        )
        assert isinstance(definitie_id, int)

        na_create = _lees_geschiedenis(db_path, definitie_id)
        assert [rij["wijziging_type"] for rij in na_create] == ["created"]

        gewijzigd = eigen_repository.update_definitie(
            definitie_id,
            {"definitie": DEFINITIE_DAARNA},
            updated_by="def519-test",
        )
        assert gewijzigd is True, "UPDATE via de repository moet slagen"

        na_update = _lees_geschiedenis(db_path, definitie_id)
        assert len(na_update) > len(na_create), "UPDATE moet history toevoegen"
        assert all(rij["begrip"] == BEGRIP for rij in na_update)

        met_tekst = [
            rij
            for rij in na_update
            if rij["definitie_nieuwe_waarde"] == DEFINITIE_DAARNA
        ]
        assert met_tekst, "De nieuwe definitietekst moet in de history staan"
        assert all(rij["definitie_oude_waarde"] == DEFINITIE_EERST for rij in met_tekst)

    def test_database_triggers_still_work(self):
        """Verify de history-trigger (log_definitie_changes) functioneert.

        Deterministisch tegen een in-memory DB opgebouwd uit schema.sql (de
        bron van waarheid) i.p.v. de muteerbare live data/definities.db — die
        kan een onvolledige trigger-set hebben. De trigger vuurt AFTER UPDATE,
        dus: insert -> update -> verwacht een history-entry. (DEF-447)
        """
        conn = sqlite3.connect(":memory:")
        try:
            conn.executescript(lees_verplichte_bron("src/database/schema.sql"))
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO definities (begrip, definitie, organisatorische_context, juridische_context, categorie)
                VALUES (?, ?, ?, ?, ?)
            """,
                ("TEST_HISTORY_CHECK", "Test definitie", "[]", "[]", "proces"),
            )
            test_id = cursor.lastrowid

            # INSERT alleen mag (nog) geen history-entry geven: de trigger is AFTER UPDATE
            cursor.execute(
                "SELECT COUNT(*) FROM definitie_geschiedenis WHERE definitie_id = ?",
                (test_id,),
            )
            assert cursor.fetchone()[0] == 0, "INSERT mag geen history-entry aanmaken"

            # UPDATE triggert log_definitie_changes (AFTER UPDATE)
            cursor.execute(
                "UPDATE definities SET definitie = ? WHERE id = ?",
                ("Gewijzigde test definitie", test_id),
            )

            # Verifieer precies één entry met de juiste gelogde waarden
            cursor.execute(
                """
                SELECT begrip, definitie_nieuwe_waarde
                FROM definitie_geschiedenis WHERE definitie_id = ?
            """,
                (test_id,),
            )
            rows = cursor.fetchall()
            # >=1: naast log_definitie_changes vuurt ook update_definities_timestamp
            # een geneste UPDATE, die de history-trigger nogmaals laat loggen.
            assert len(rows) >= 1, "UPDATE moet een history-entry aanmaken"
            assert all(r[0] == "TEST_HISTORY_CHECK" for r in rows)
            assert all(r[1] == "Gewijzigde test definitie" for r in rows)
        finally:
            conn.close()

    def test_session_state_no_history_keys(self):
        """Verify no history-related keys in session state initialization."""
        import streamlit as st

        from ui.session_state import SessionStateManager

        # Mock streamlit session state
        with patch("streamlit.session_state", {}):
            # Initialize session state
            SessionStateManager.initialize_session_state()

            # Check session state directly
            # Note: _get_default_values might not exist, check session_state directly
            if hasattr(st, "session_state"):
                history_keys = [
                    k for k in st.session_state if "history" in str(k).lower()
                ]

                # Should have no history-specific keys
                # (Some keys might legitimately contain 'history' in their name for other purposes)
                suspicious_keys = [
                    k
                    for k in history_keys
                    if any(x in str(k).lower() for x in ["tab", "view", "page"])
                ]
                melding = f"Found history tab keys: {suspicious_keys}"
                assert len(suspicious_keys) == 0, melding

    def test_other_tabs_remain_functional(self):
        """Test that other tabs can still be instantiated."""
        # export/management zijn geconsolideerd in tabs.import_export_beheer (DEF-447)
        tabs_to_test = [
            ("definition_generator_tab", "DefinitionGeneratorTab"),
            ("definition_edit_tab", "DefinitionEditTab"),
            ("expert_review_tab", "ExpertReviewTab"),
            ("tabs.import_export_beheer", "ImportExportBeheerTab"),
        ]

        for module_name, class_name in tabs_to_test:
            # Een importfout is hier altijd een fout: er is geen reden waarom
            # deze modules onbereikbaar zouden mogen zijn.
            module = __import__(f"ui.components.{module_name}", fromlist=[class_name])
            tab_class = getattr(module, class_name)

            assert tab_class is not None

    def test_no_broken_navigation_references(self, ui_grenzen):
        """Check that navigation doesn't reference non-existent history tab."""
        from ui.tabbed_interface import TabbedInterface

        with patch("streamlit.session_state", {}):
            interface = TabbedInterface()

        valid_keys = list(interface.tab_config.keys())
        assert "history" not in valid_keys

        # Elke geconfigureerde sleutel heeft een component met een render-methode.
        # Een onbekende sleutel valt hier op met een KeyError in plaats van
        # stilzwijgend te worden overgeslagen.
        for key in valid_keys:
            attribuut = TABCOMPONENT_PER_SLEUTEL[key]
            component = getattr(interface, attribuut, None)
            assert component is not None, f"Tab '{key}' mist component {attribuut}"
            assert callable(getattr(component, "render", None))


class TestApplicationFunctionality:
    """Test that core application functionality still works after History removal."""

    @patch("streamlit.session_state", {})
    def test_definition_generation_flow(self, ui_grenzen):
        """De generatieroute delegeert naar de handler, buiten history om.

        De oude versie patchte de methode die zij zelf aanriep en asserteerde
        daarna op dat patch-object; dat bewees niets. Nu wordt de *ontvanger*
        (de generatiehandler, een UI-grens) vervangen, zodat de echte
        delegatie in `_handle_definition_generation` wordt uitgevoerd.
        """
        from ui.tabbed_interface import TabbedInterface

        interface = TabbedInterface()
        aanroepen: list[tuple[str, dict[str, Any]]] = []

        class _Handlergrens:
            def handle_definition_generation(self, begrip, context_data, **kwargs):
                aanroepen.append((begrip, context_data))

        interface.generation_handler = _Handlergrens()
        context = {"organisatorisch": ["TestOrg"]}

        interface._handle_definition_generation("test_begrip", context)

        assert aanroepen == [("test_begrip", context)]

    def test_database_operations_work(self, eigen_repository):
        """Test that database operations still function.

        Er wordt bewust niet op een absoluut aantal geasserteerd: het canonieke
        `schema.sql` legt zelf twee voorbeeldrijen aan. De statistiek moet een
        *nieuwe* rij volgen, en dat is wat hier wordt gemeten.
        """
        from database.definitie_repository import DefinitieStatus

        basis = eigen_repository.get_statistics()

        assert isinstance(basis, dict)
        assert set(basis) >= {
            "total_definities",
            "by_status",
            "by_category",
            "average_validation_score",
        }

        eigen_repository.create_definitie(
            maak_testrecord("def519_statistiek_begrip", DEFINITIE_EERST)
        )
        na = eigen_repository.get_statistics()

        draft = DefinitieStatus.DRAFT.value
        assert na["total_definities"] == basis["total_definities"] + 1
        assert na["by_status"][draft] == basis["by_status"].get(draft, 0) + 1

    def test_export_functionality(self, eigen_repository):
        """De exportroute hangt niet aan history.

        `ui.components.export_tab.ExportTab` bestaat niet meer (DEF-447); de
        export zit in `ImportExportBeheerTab`. Zie de bronbevinding boven in
        deze module. De echte repository wordt geïnjecteerd, geen `Mock`.
        """
        from ui.components.tabs.import_export_beheer import ImportExportBeheerTab

        export_tab = ImportExportBeheerTab(eigen_repository)

        assert export_tab.repository is eigen_repository
        assert callable(getattr(export_tab, "render", None))


class TestPerformanceImprovement:
    """Bovengrenzen voor import en geheugen na de History-verwijdering.

    De klassenaam blijft staan zodat de node-ids niet verschuiven, maar hier
    wordt geen verbetering bewezen: er is geen meting van vóór de verwijdering
    om tegen af te zetten. Het zijn bovengrenzen, geen vergelijkingen.
    """

    def test_import_time(self):
        """Warme importcontrole van `ui.tabbed_interface`.

        Dit is nadrukkelijk **geen** cold-start-meting en geen bewijs van een
        prestatieverbetering: de module is in deze sessie al door de tests
        hierboven geïmporteerd, dus `import` levert hem uit `sys.modules` en de
        gemeten duur is die van een cache-hit. De grens van 2 seconden blijft
        onveranderd staan als bovengrens — hij slaat aan wanneer een warme
        import op een importtijd-regressie stuit (bijvoorbeeld werk op
        modulniveau bij herimport), niet wanneer de koude start trager wordt.
        """
        import time

        start = time.time()
        from ui.tabbed_interface import TabbedInterface

        end = time.time()

        import_time = end - start

        # Should import in reasonable time (< 2 seconds)
        assert import_time < 2.0, f"Import took too long: {import_time:.2f}s"

        # Log the time for comparison
        print(f"TabbedInterface import time: {import_time:.3f}s")

    def test_memory_usage(self, ui_grenzen):
        """Bovengrens voor het geheugengebruik van één `TabbedInterface`.

        `tracemalloc` is procesbrede toestand: deze test zet hem alleen aan als
        hij nog niet liep, en zet hem in `finally` weer uit — ook wanneer de
        constructor of een assertie eronder faalt. Een tracing-sessie die al
        actief was blijft staan; die is niet van deze test.
        """
        import tracemalloc

        from ui.tabbed_interface import TabbedInterface

        al_actief = tracemalloc.is_tracing()
        if not al_actief:
            tracemalloc.start()
        try:
            with patch("streamlit.session_state", {}):
                TabbedInterface()

            current, peak = tracemalloc.get_traced_memory()
        finally:
            if not al_actief:
                tracemalloc.stop()

        # Convert to MB
        current_mb = current / 1024 / 1024
        peak_mb = peak / 1024 / 1024

        print(f"Memory usage - Current: {current_mb:.2f} MB, Peak: {peak_mb:.2f} MB")

        # Should use reasonable memory (< 100 MB for interface)
        assert peak_mb < 100, f"Memory usage too high: {peak_mb:.2f} MB"


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "--tb=short"])
