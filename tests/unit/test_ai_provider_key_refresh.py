"""DEF-730: een gewijzigde API-sleutel bereikt de nieuwe AI-client in dezelfde sessie.

De sidebar zette bij een sleutel- of providerwissel wel de omgevingsvariabelen en
resette de container, maar niet de `ConfigManager`-singleton en niet de
service-container in de Streamlit-sessie. De container leest zijn AI-sleutel via
`get_config_manager().api`, dus bleef de oude sleutel actief tot een procesherstart.

Deze tests toetsen het *gedrag* tot aan de SDK-grens: de echte sidebarhandler, de
echte `create_ai_client`-factory en de echte client-adapters draaien; alleen de
SDK-constructor (`AsyncAnthropic` / `AsyncOpenAI`) is vervangen door een opname-fake
die de meegegeven sleutel vastlegt. Er wordt nooit een netwerkverbinding, database
of echte sleutel aangeraakt: alle sleutels hieronder zijn synthetische, niet-geheime
strings, `.env` is uit via de unit-conftest en de DEF-519-offlinegate staat dicht.
"""

from __future__ import annotations

import logging
import os

import pytest

from config import config_manager as config_manager_module
from services import service_factory
from services.service_factory import get_definition_service
from ui import cached_services
from ui.cached_services import initialize_services_once
from ui.components.ai_provider_sidebar import (
    _apply_provider_change,
    render_ai_provider_sidebar,
)
from ui.session_state import SessionStateManager
from utils.container_manager import clear_container_cache, get_cached_container

pytestmark = [pytest.mark.unit]

# Synthetische, niet-geheime sleutels. Bewust zonder `sk-`/`sk-ant-`-vorm zodat ze
# door geen enkele secret-scanner als echte sleutel gelezen kunnen worden.
ANTHROPIC_SLEUTEL_A = "synthetische-anthropic-sleutel-alfa"
ANTHROPIC_SLEUTEL_B = "synthetische-anthropic-sleutel-bravo"
OPENAI_SLEUTEL_A = "synthetische-openai-sleutel-alfa"
OPENAI_SLEUTEL_B = "synthetische-openai-sleutel-bravo"

_ENV_NAAM = {"anthropic": "ANTHROPIC_API_KEY", "openai": "OPENAI_API_KEY"}

# Marker die alleen in de tekst van een opgevangen exception voorkomt. Belandt hij
# in een log of in de UI, dan lekt de foutafhandeling exception-tekst die in
# productie een API-sleutel kan bevatten.
SLEUTELMARKER = "MARKER-synthetische-sleutel-mag-niet-lekken"


class _StreamlitStopError(BaseException):
    """Zelfde controlflow-semantiek als `st.stop()`: de scriptrun wordt afgebroken.

    Streamlit gooit hiervoor een echte exception; een fake die netjes terugkeert
    zou verzwijgen dat het renderpad daarna gewoon doorloopt. Erft net als
    `streamlit.runtime.scriptrunner_utils.exceptions.ScriptControlException` van
    `BaseException`, zodat een `except Exception` onderweg hem — terecht — niet
    opvangt en de test niet milder is dan de werkelijkheid.
    """


class _StreamlitRerunError(BaseException):
    """Zelfde controlflow-semantiek als `st.rerun()`: de run stopt en herstart."""


@pytest.fixture
def sdk_opname(monkeypatch):
    """Vervang beide SDK-constructors door een fake die (provider, sleutel) vastlegt."""
    aanroepen: list[tuple[str, str]] = []

    def _maak_fake(provider: str):
        class _FakeSdkClient:
            def __init__(self, *_args, api_key: str = "", **_kwargs) -> None:
                aanroepen.append((provider, api_key))

        return _FakeSdkClient

    monkeypatch.setattr(
        "services.ai.anthropic_client.AsyncAnthropic", _maak_fake("anthropic")
    )
    monkeypatch.setattr("services.ai.openai_client.AsyncOpenAI", _maak_fake("openai"))
    return aanroepen


@pytest.fixture
def verse_configsingleton(monkeypatch):
    """Geef de test een eigen ConfigManager-singleton en ruim de containers op."""
    monkeypatch.setattr(config_manager_module, "_config_manager", None)
    yield
    # Laat geen container achter die op de synthetische omgeving is gebouwd.
    clear_container_cache()
    SessionStateManager.clear_value("service_container")


@pytest.fixture
def streamlit_controlflow(monkeypatch):
    """Geef `st.stop()` en `st.rerun()` hun echte, run-afbrekende semantiek."""
    import streamlit as st

    def _stop(*_a, **_k):
        raise _StreamlitStopError

    def _rerun(*_a, **_k):
        raise _StreamlitRerunError

    monkeypatch.setattr(st, "stop", _stop, raising=False)
    monkeypatch.setattr(st, "rerun", _rerun)
    return st


@pytest.fixture
def renderbaar(monkeypatch, streamlit_controlflow):
    """Maak `render_ai_provider_sidebar()` aanroepbaar op de Streamlit-mock."""
    st = streamlit_controlflow

    def _selectbox(_label, *, options, index=0, **_kwargs):
        return options[index]

    monkeypatch.setattr(st, "caption", lambda *a, **k: None, raising=False)
    monkeypatch.setattr(st, "selectbox", _selectbox)
    monkeypatch.setattr(st, "text_input", lambda *a, **k: None)
    return st


def _pas_wissel_toe(provider: str, sleutel: str) -> None:
    """Roep de handler aan; een geslaagde wissel eindigt altijd in `st.rerun()`."""
    with pytest.raises(_StreamlitRerunError):
        _apply_provider_change(provider, sleutel)


@pytest.fixture
def productiecache(monkeypatch):
    """Geef de test een activatie van het cachepad zoals het in productie draait.

    De factory slaat zijn adaptercache over zodra `PYTEST_CURRENT_TEST` gezet is;
    zonder deze activatie toetst een test dus een pad dat in productie niet
    bestaat. De activatie hoort bewust in de testbody: pytest zet
    `PYTEST_CURRENT_TEST` bij élke fase opnieuw, dus een `delenv` tijdens
    fixture-setup is aan het begin van de call-fase alweer ongedaan gemaakt.

    Monkeypatch herstelt de omgeving na afloop. De offline-gate en de netwerk- en
    databaseguards blijven onaangeroerd; `APP_ENV=testing` houdt de container op
    een in-memory database, zodat er geen bestaand databasebestand geopend wordt.
    """

    def _activeer() -> None:
        monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
        monkeypatch.setenv("APP_ENV", "testing")
        service_factory._SERVICE_ADAPTER_CACHE.clear()

    yield _activeer
    service_factory._SERVICE_ADAPTER_CACHE.clear()


def _stel_omgeving_in(monkeypatch, provider: str, sleutel: str) -> None:
    """Zet de omgeving op *provider*/*sleutel* en leeg de containercaches."""
    monkeypatch.setenv("AI_PROVIDER", provider)
    monkeypatch.setenv(_ENV_NAAM[provider], sleutel)
    clear_container_cache()
    SessionStateManager.clear_value("service_container")


def _warm_sessie_op(monkeypatch, provider: str, sleutel: str) -> object:
    """Zet de omgeving op *provider*/*sleutel* en bouw de eerste AI-client op."""
    _stel_omgeving_in(monkeypatch, provider, sleutel)
    return _bouw_ai_client_via_sessiecache()


def _bouw_ai_client_via_sessiecache() -> object:
    """Haal de container uit de sessioncache en forceer de echte AI-clientbouw."""
    initialize_services_once()
    container = SessionStateManager.get_value("service_container")
    container.ai_service()
    return container


def test_gewijzigde_anthropic_sleutel_bereikt_nieuwe_sdk_client(
    monkeypatch, sdk_opname, verse_configsingleton, streamlit_controlflow
):
    """Same-provider Anthropic: na sleutel B krijgt de SDK B, niet meer A."""
    oude_container = _warm_sessie_op(monkeypatch, "anthropic", ANTHROPIC_SLEUTEL_A)
    assert sdk_opname == [("anthropic", ANTHROPIC_SLEUTEL_A)]

    _pas_wissel_toe("anthropic", ANTHROPIC_SLEUTEL_B)

    nieuwe_container = _bouw_ai_client_via_sessiecache()
    assert nieuwe_container is not oude_container
    assert sdk_opname[-1] == ("anthropic", ANTHROPIC_SLEUTEL_B)
    assert ("anthropic", ANTHROPIC_SLEUTEL_A) not in sdk_opname[1:]


def test_gewijzigde_openai_sleutel_bereikt_nieuwe_sdk_client(
    monkeypatch, sdk_opname, verse_configsingleton, streamlit_controlflow
):
    """Same-provider OpenAI: na sleutel B krijgt de SDK B, niet meer A."""
    oude_container = _warm_sessie_op(monkeypatch, "openai", OPENAI_SLEUTEL_A)
    assert sdk_opname == [("openai", OPENAI_SLEUTEL_A)]

    _pas_wissel_toe("openai", OPENAI_SLEUTEL_B)

    nieuwe_container = _bouw_ai_client_via_sessiecache()
    assert nieuwe_container is not oude_container
    assert sdk_opname[-1] == ("openai", OPENAI_SLEUTEL_B)
    assert ("openai", OPENAI_SLEUTEL_A) not in sdk_opname[1:]


def test_providerwissel_bouwt_client_van_de_nieuwe_provider(
    monkeypatch, sdk_opname, verse_configsingleton, streamlit_controlflow
):
    """Wissel Anthropic→OpenAI: de SDK-client is van OpenAI met de OpenAI-sleutel."""
    _warm_sessie_op(monkeypatch, "anthropic", ANTHROPIC_SLEUTEL_A)
    assert sdk_opname == [("anthropic", ANTHROPIC_SLEUTEL_A)]

    monkeypatch.setenv("OPENAI_API_KEY", OPENAI_SLEUTEL_B)
    _pas_wissel_toe("openai", OPENAI_SLEUTEL_B)

    _bouw_ai_client_via_sessiecache()
    assert sdk_opname[-1] == ("openai", OPENAI_SLEUTEL_B)
    assert not any(provider == "anthropic" for provider, _ in sdk_opname[1:])


def _mislukte_reload() -> None:
    """Config-refresh die faalt met een exception die de sleutelmarker meedraagt."""
    raise RuntimeError(f"upstream configfout met sleutel {SLEUTELMARKER}")


def test_mislukte_configrefresh_breekt_de_run_af_en_draait_de_wissel_terug(
    monkeypatch, sdk_opname, verse_configsingleton, renderbaar
):
    """Faalt de refresh, dan stopt de run en blijft de wissel openstaan.

    Alleen terugkeren uit de handler is niet genoeg: het renderpad zou daarna
    gewoon doorlopen en een volgende rerun zou stil met de oude sleutel verder
    kunnen. Het bewijs zit in de afgebroken run, de teruggedraaide omgeving en het
    uitblijven van elke nieuwe SDK-client.
    """
    st = renderbaar
    _warm_sessie_op(monkeypatch, "anthropic", ANTHROPIC_SLEUTEL_A)
    st.messages.clear()
    monkeypatch.setattr(config_manager_module, "reload_config", _mislukte_reload)

    with pytest.raises(_StreamlitStopError):
        _apply_provider_change("anthropic", ANTHROPIC_SLEUTEL_B)

    assert any(soort == "error" for soort, _ in st.messages)
    # Niet-toegepaste wijziging teruggedraaid: de detectie in het renderpad ziet de
    # wissel daardoor nog steeds als openstaand en probeert het opnieuw.
    assert os.environ["ANTHROPIC_API_KEY"] == ANTHROPIC_SLEUTEL_A
    assert os.environ["AI_PROVIDER"] == "anthropic"

    SessionStateManager.set_value("ai_api_key_input", ANTHROPIC_SLEUTEL_B)
    with pytest.raises(_StreamlitStopError):
        render_ai_provider_sidebar()

    assert sdk_opname == [("anthropic", ANTHROPIC_SLEUTEL_A)]


def test_mislukte_servicecacheverversing_breekt_de_run_af(
    monkeypatch, sdk_opname, verse_configsingleton, renderbaar
):
    """Ook een falende schoning van de sessioncache mag niet stil doorgaan."""
    st = renderbaar
    _warm_sessie_op(monkeypatch, "anthropic", ANTHROPIC_SLEUTEL_A)
    st.messages.clear()

    def _mislukte_cacheschoning() -> None:
        raise RuntimeError(f"cacheschoning faalde met sleutel {SLEUTELMARKER}")

    monkeypatch.setattr(cached_services, "clear_service_cache", _mislukte_cacheschoning)

    with pytest.raises(_StreamlitStopError):
        _apply_provider_change("anthropic", ANTHROPIC_SLEUTEL_B)

    assert any(soort == "error" for soort, _ in st.messages)
    assert os.environ["ANTHROPIC_API_KEY"] == ANTHROPIC_SLEUTEL_A
    assert sdk_opname == [("anthropic", ANTHROPIC_SLEUTEL_A)]


def test_geslaagde_retry_na_fout_levert_de_nieuwe_sleutel(
    monkeypatch, sdk_opname, verse_configsingleton, renderbaar
):
    """Herstelt de oorzaak, dan past de eerstvolgende render de wissel alsnog toe."""
    echte_reload = config_manager_module.reload_config
    _warm_sessie_op(monkeypatch, "anthropic", ANTHROPIC_SLEUTEL_A)
    monkeypatch.setattr(config_manager_module, "reload_config", _mislukte_reload)
    SessionStateManager.set_value("ai_api_key_input", ANTHROPIC_SLEUTEL_B)

    with pytest.raises(_StreamlitStopError):
        render_ai_provider_sidebar()

    monkeypatch.setattr(config_manager_module, "reload_config", echte_reload)
    with pytest.raises(_StreamlitRerunError):
        render_ai_provider_sidebar()

    _bouw_ai_client_via_sessiecache()
    assert sdk_opname[-1] == ("anthropic", ANTHROPIC_SLEUTEL_B)


def test_foutafhandeling_lekt_geen_sleutel_naar_logs_of_ui(
    monkeypatch, caplog, sdk_opname, verse_configsingleton, streamlit_controlflow
):
    """De tekst van de opgevangen fout mag niet in log of UI belanden.

    In productie kan die tekst uit een config- of SDK-laag komen en de API-sleutel
    letterlijk meedragen; daarom logt de handler een vaste melding zonder
    exception-tekst en zonder `exc_info`.
    """
    st = streamlit_controlflow
    _warm_sessie_op(monkeypatch, "anthropic", ANTHROPIC_SLEUTEL_A)
    st.messages.clear()
    monkeypatch.setattr(config_manager_module, "reload_config", _mislukte_reload)

    with caplog.at_level(logging.DEBUG), pytest.raises(_StreamlitStopError):
        _apply_provider_change("anthropic", ANTHROPIC_SLEUTEL_B)

    # Zonder dit positieve anker zou de negatieve assertie ook slagen als er
    # helemaal niets gelogd was.
    assert "AI provider change failed" in caplog.text
    assert SLEUTELMARKER not in caplog.text
    assert all(SLEUTELMARKER not in str(bericht) for _, bericht in st.messages)


def test_leeg_overrideveld_behoudt_de_bestaande_env_sleutel(
    monkeypatch, sdk_opname, verse_configsingleton, streamlit_controlflow
):
    """Zonder ingevulde override blijft de sleutel uit de omgeving in gebruik."""
    _warm_sessie_op(monkeypatch, "anthropic", ANTHROPIC_SLEUTEL_A)

    _pas_wissel_toe("anthropic", "")

    _bouw_ai_client_via_sessiecache()
    assert sdk_opname[-1] == ("anthropic", ANTHROPIC_SLEUTEL_A)


def test_generatiepad_krijgt_de_nieuwe_sleutel_met_productiecache_aan(
    monkeypatch,
    sdk_opname,
    verse_configsingleton,
    streamlit_controlflow,
    productiecache,
):
    """Met de echte adaptercache actief bereikt sleutel B het generatiepad.

    `get_definition_service()` levert de ServiceAdapter die de UI voor generatie
    gebruikt. Die adapter bevriest container én orchestrator, en daarmee de
    AI-client van dat moment; de sessiecontainer-test dekt dat pad niet.
    """
    productiecache()
    _stel_omgeving_in(monkeypatch, "anthropic", ANTHROPIC_SLEUTEL_A)

    oude_adapter = get_definition_service()
    assert sdk_opname[-1] == ("anthropic", ANTHROPIC_SLEUTEL_A)
    opnames_na_warmup = len(sdk_opname)

    _pas_wissel_toe("anthropic", ANTHROPIC_SLEUTEL_B)

    nieuwe_adapter = get_definition_service()
    assert nieuwe_adapter is not oude_adapter
    assert nieuwe_adapter.container is not oude_adapter.container
    assert sdk_opname[-1] == ("anthropic", ANTHROPIC_SLEUTEL_B)
    assert ("anthropic", ANTHROPIC_SLEUTEL_A) not in sdk_opname[opnames_na_warmup:]


def test_serviceadapter_wordt_hergebruikt_zonder_wijziging(
    monkeypatch,
    sdk_opname,
    verse_configsingleton,
    streamlit_controlflow,
    productiecache,
):
    """Zonder wissel blijven dezelfde adapter en dezelfde client in gebruik.

    Bewaakt dat de fix de cache gericht ongeldig maakt en hem niet simpelweg
    uitschakelt: dat zou elke render opnieuw de hele servicelaag opbouwen.
    """
    productiecache()
    _stel_omgeving_in(monkeypatch, "anthropic", ANTHROPIC_SLEUTEL_A)

    eerste = get_definition_service()
    opnames_na_eerste = len(sdk_opname)

    tweede = get_definition_service()

    assert tweede is eerste
    assert len(sdk_opname) == opnames_na_eerste


def test_interfaceverversing_volgt_de_containeridentiteit(
    monkeypatch,
    sdk_opname,
    verse_configsingleton,
    streamlit_controlflow,
    productiecache,
):
    """De interfacecache hangt aan de container, niet aan een module-identiteit.

    Streamlit draait het entrypoint als `__main__`, dus de sidebar bereikt met
    `import main` een tweede module-object; een cache die op die identiteit leunt
    is niet betrouwbaar te legen. Deze test toont dat een verse container hoe dan
    ook een verse interface oplevert.
    """
    import main

    class _NepInterface:
        """Registreert met welke container hij gebouwd is; bouwt zelf niets op."""

        def __init__(self) -> None:
            self.container_id = get_cached_container().get_container_id()

    productiecache()
    monkeypatch.setattr(main, "TabbedInterface", _NepInterface)
    _stel_omgeving_in(monkeypatch, "anthropic", ANTHROPIC_SLEUTEL_A)

    eerste = main.get_tabbed_interface()

    _pas_wissel_toe("anthropic", ANTHROPIC_SLEUTEL_B)

    tweede = main.get_tabbed_interface()
    assert tweede is not eerste
    assert tweede.container_id != eerste.container_id
