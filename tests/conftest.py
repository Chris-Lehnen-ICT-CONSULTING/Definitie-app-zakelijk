"""
Global pytest configuration and fixtures for the test suite.
"""

# DEF-519: de offline-gate moet dicht zijn vóór er ook maar één applicatiepakket
# geimporteerd wordt. Alles hieronder (de Streamlit-mock, `config`, indirect de
# servicelaag) draaide voorheen met de geerfde omgeving van de ontwikkelaar:
# echte providerkeys, een leesbare `.env` en open sockets. `install()` is
# idempotent; onder scripts/testing/run_profile.py is de gate al bij
# interpreterstart gezet en is deze aanroep een no-op die dezelfde sessieroot
# teruggeeft. Zie tests/offline_bootstrap.py voor het contract.
import sys as _sys
from pathlib import Path as _Path

_def519_project_root = str(_Path(__file__).resolve().parents[1])
if _def519_project_root not in _sys.path:
    _sys.path.append(_def519_project_root)

from tests import offline_bootstrap as _def519_bootstrap

_def519_bootstrap.install()

import asyncio
import builtins
import os
import socket
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Ensure src directory is on sys.path for imports
# This is redundant with pytest.ini but ensures it's available during collection
project_root = Path(__file__).parent.parent
src_path = project_root / "src"

# DEF-439: project_root (parent van tests/) op sys.path, NIET tests/ zelf.
# tests/ heeft een __init__.py, dus testmodules resolven dan als fully-qualified
# `tests.*` (bv. tests.integration) en botsen niet meer met gelijknamige
# src-packages (tests/integration vs src/integration, tests/unit/validation vs
# src/validation, ...) onder --import-mode=importlib. Zou tests/ wél op path staan,
# dan is tests/integration/__init__.py importeerbaar als bare `integration` en
# shadowt het de echte src/integration → collection faalt met
# `ModuleNotFoundError: No module named 'integration.definitie_checker'`.
# project_root staat low-priority (append); src wordt daarna naar voren geforceerd
# zodat bare top-level namen altijd naar src resolven.
root_str = str(project_root)
if root_str not in sys.path:
    sys.path.append(root_str)

src_str = str(src_path)
if src_str in sys.path:
    sys.path.remove(src_str)
sys.path.insert(0, src_str)

# Install a minimal Streamlit mock BEFORE importing modules that might reference it
try:
    from tests.fixtures.streamlit_mock import get_streamlit_mock  # type: ignore

    sys.modules["streamlit"] = get_streamlit_mock()
except Exception:  # pragma: no cover - inline fallback

    class _NoOpDec:
        def __call__(self, *args, **kwargs):
            def _decorator(func):
                return func

            return _decorator

        def clear(self):
            return None

    class _InlineSt:
        def __init__(self):
            self.session_state = {}
            self.cache_data = _NoOpDec()
            self.cache_resource = _NoOpDec()

    sys.modules["streamlit"] = _InlineSt()

# Provide legacy-compatible config helpers in builtins for tests that assume
# top-level imports (e.g., get_api_config without explicit import).
try:  # pragma: no cover - integration convenience
    from config import (
        get_api_config as _compat_get_api_config,
        get_cache_config as _compat_get_cache_config,
        get_default_model as _compat_get_default_model,
        get_default_temperature as _compat_get_default_temperature,
        get_paths_config as _compat_get_paths_config,
    )

    builtins.get_api_config = getattr(  # type: ignore[attr-defined]
        builtins, "get_api_config", _compat_get_api_config
    )
    builtins.get_cache_config = getattr(  # type: ignore[attr-defined]
        builtins, "get_cache_config", _compat_get_cache_config
    )
    builtins.get_paths_config = getattr(  # type: ignore[attr-defined]
        builtins, "get_paths_config", _compat_get_paths_config
    )
    builtins.get_default_model = getattr(  # type: ignore[attr-defined]
        builtins, "get_default_model", _compat_get_default_model
    )
    builtins.get_default_temperature = getattr(  # type: ignore[attr-defined]
        builtins, "get_default_temperature", _compat_get_default_temperature
    )
except Exception:
    pass

# Import all fixtures from v2_service_mocks to make them globally available
# DISABLED: fixtures directory was removed, will restore incrementally as needed
# from fixtures.v2_service_mocks import *


# Configure asyncio for testing
@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True, scope="session")
def _warm_config_manager():
    """Initialiseer de config_manager-singleton één keer in de project-root (DEF-413).

    De singleton wordt anders lazy aangemaakt door de eerste test die config
    nodig heeft. Draait die test in een `chdir`'d tmp-dir (bv. via
    chdir_tmp_path), dan vindt ConfigManager `config.yaml` niet → lege api_key →
    "API key niet geconfigureerd" + netwerk-fouten in alle volgende
    container-tests. Eager warmen (cwd = root, env al gezet) voorkomt dat.
    """
    try:
        from config.config_manager import get_config_manager

        get_config_manager()
    except Exception:
        pass


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset gedeelde singleton-/globale state tussen tests (DEF-414).

    Zonder deze resets lekken de ServiceContainer-singleton, de
    container_manager LRU-cache en Streamlit's session_state door naar volgende
    tests in hetzelfde proces. Dat veroorzaakte order-afhankelijke (flaky)
    failures: tests slaagden in isolatie maar faalden na een vervuilende test.
    """
    # 1. services.container global singleton
    try:
        from services.container import reset_container

        reset_container()
    except ImportError:
        pass
    # 2. utils.container_manager LRU-cache (get_cached_container singleton)
    try:
        from utils.container_manager import clear_container_cache

        clear_container_cache()
    except ImportError:
        pass
    # 3. Streamlit session_state (gedeelde mock-dict over alle tests)
    try:
        import streamlit as st

        if hasattr(st, "session_state"):
            st.session_state.clear()
    except Exception:
        pass


@pytest.fixture
def test_db_path(tmp_path):
    """Provide a temporary database path for testing."""
    return str(tmp_path / "test.db")


@pytest.fixture
def in_memory_db():
    """Provide in-memory database configuration."""
    return ":memory:"


@pytest.fixture
def initialized_synonym_db(tmp_path):
    """
    Provide a database with full schema + synonym tables initialized.

    This fixture:
    1. Creates a temp SQLite database file
    2. Applies the full schema (schema.sql) for definities tables
    3. Applies the synonym_groups migration (006_synonym_groups_tables.sql)
    4. Returns the database path for use with ServiceContainer

    Use this fixture when testing SynonymOrchestrator or SynonymRegistry
    to ensure ALL tables exist before queries run.
    """
    import sqlite3

    # Use tmp file instead of :memory: so we can pass path to ServiceContainer
    db_path = tmp_path / "test_synonyms.db"

    # Read main schema SQL
    schema_path = Path(__file__).parent.parent / "src" / "database" / "schema.sql"

    # Read migration SQL for synonym tables
    migration_path = (
        Path(__file__).parent.parent
        / "src"
        / "database"
        / "migrations"
        / "006_synonym_groups_tables.sql"
    )

    # Initialize database with full schema + migration
    conn = sqlite3.connect(str(db_path))
    try:
        # First: Apply main schema (definities tables)
        with open(schema_path, encoding="utf-8") as f:
            schema_sql = f.read()
        conn.executescript(schema_sql)

        # Second: Apply synonym migration (synonym_groups tables)
        with open(migration_path, encoding="utf-8") as f:
            migration_sql = f.read()
        conn.executescript(migration_sql)

        conn.commit()
    finally:
        conn.close()

    return str(db_path)


# Marker-registratie is gecentreerd in pytest.ini (strict-markers).
# Dubbele registraties hier zijn verwijderd om drift te voorkomen.


@pytest.hookimpl(trylast=True)
def pytest_configure(config):
    """DEF-519: adopteer de basetemp van pytest als eigen, tijdelijke root.

    `trylast`: conftest-hooks draaien standaard vóór de ingebouwde plugins, en
    `config._tmp_path_factory` wordt pas door `_pytest.tmpdir.pytest_configure`
    gezet.

    `tmp_path`/`tmp_path_factory` liggen buiten de sessieroot van de bootstrap.
    Zonder deze expliciete adoptie zou elke bestaande test die een SQLite-DB in
    `tmp_path` opent door de gate geweigerd worden. Bewust géén prefixvertrouwen
    op `/tmp`: alleen deze ene, door pytest vers aangemaakte map wordt eigendom.
    """
    fabriek = getattr(config, "_tmp_path_factory", None)
    if fabriek is None:  # pragma: no cover - pytest levert de factory altijd
        raise RuntimeError(
            "pytest levert geen _tmp_path_factory; de DEF-519-gate zou dan elke "
            "tmp_path-database weigeren. Los dit op, val niet stil terug."
        )
    # `.lock` is het eigen opruimbestand dat pytest direct in een verse basetemp
    # zet; expliciet benoemd, zodat 'niet leeg' verder gewoon geweigerd wordt.
    _def519_bootstrap.own_root(
        fabriek.getbasetemp(), toegestane_resten=frozenset({".lock"})
    )


# Configure test collection to ignore certain files
def pytest_ignore_collect(collection_path: Path, config):
    """Ignore certain test files during collection."""
    p = str(collection_path).lower()
    # Ignore US-041/042/043 tests until features are implemented
    if "us041" in p:
        return True
    if "us042" in p:
        return True
    if "us043" in p:
        return True
    # Ignore manual exploratory scripts
    if "/manual/" in p.replace("\\", "/"):
        return True
    # Ignore ad-hoc debug tests (niet bedoeld voor standaard runs)
    return "/debug/" in p.replace("\\", "/")


# Performance monitoring for tests
@pytest.fixture
def benchmark_timer():
    """Simple benchmark timer for performance testing."""
    import time

    class Timer:
        def __init__(self):
            self.start_time = None
            self.elapsed = None

        def start(self):
            self.start_time = time.perf_counter()

        def stop(self):
            if self.start_time:
                self.elapsed = time.perf_counter() - self.start_time
                return self.elapsed
            return None

        def assert_under(self, seconds: float):
            """Assert that elapsed time is under specified seconds."""
            assert self.elapsed is not None, "Timer not stopped"
            assert (
                self.elapsed < seconds
            ), f"Took {self.elapsed:.2f}s, expected under {seconds}s"

    return Timer()


# Provide a minimal fallback for the 'benchmark' fixture ONLY when
# pytest-benchmark is not installed. When the plugin is present, its
# BenchmarkFixture should be used to avoid conflicts.
try:  # pragma: no cover - import guard for optional plugin
    _HAS_BENCHMARK_PLUGIN = True
except Exception:  # plugin not available
    _HAS_BENCHMARK_PLUGIN = False

if not _HAS_BENCHMARK_PLUGIN:

    @pytest.fixture
    def benchmark():
        def run(fn, *args, **kwargs):
            return fn(*args, **kwargs)

        return run


# Test data fixtures
@pytest.fixture
def sample_definition_data():
    """Provide sample definition data for testing."""
    return {
        "begrip": "rechtspersoon",
        "definitie": "Een juridische entiteit die rechten en plichten kan hebben",
        "ontologische_categorie": "juridisch concept",
    }


@pytest.fixture
def sample_validation_rules():
    """Provide sample validation rules for testing."""
    return [
        {"id": "RULE001", "name": "Minimum Length", "threshold": 10},
        {"id": "RULE002", "name": "Contains Definition", "threshold": 0.8},
        {"id": "RULE003", "name": "Dutch Language", "threshold": 0.9},
    ]


# Environment setup
@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-123")
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("LOG_LEVEL", "ERROR")  # Reduce log noise in tests
    return monkeypatch


@pytest.fixture
def hermetische_werkmap(tmp_path, monkeypatch):
    """Werkmap in tmp met de repo-`config/` en `src/` als symlink en een lege `data/`.

    DEF-664: de repository-init is fail-closed op het canonieke schema. Code
    die het standaardpad `data/definities.db` gebruikt (ServiceContainer(),
    DefinitieRepository() zonder pad, service_factory) landt hiermee in een
    verse tijdelijke database in plaats van in de werkmap van de repo. Opt-in
    per testmodule; de brede gate-hermeticiteit blijft DEF-519.
    """
    repo_root = Path(__file__).resolve().parents[1]
    for map_ in ("config", "src"):
        (tmp_path / map_).symlink_to(repo_root / map_, target_is_directory=True)
    (tmp_path / "data").mkdir()
    monkeypatch.chdir(tmp_path)
    return tmp_path


# Opt-in fixture to sandbox relative writes under a temporary directory.
# Usage: add 'chdir_tmp_path' to your test function signature.
@pytest.fixture
def chdir_tmp_path(tmp_path, monkeypatch):
    """Change CWD to pytest's tmp_path for the duration of a test.

    Useful to prevent accidental creation of files in the repository root
    by code that uses relative paths.
    Returns the temporary path for convenience.
    """
    monkeypatch.chdir(tmp_path)
    return tmp_path


# Prevent tiktoken BPE download — provide fake encoder for RAG tests.
# Must run before _disable_network blocks sockets.
@pytest.fixture(autouse=True, scope="session")
def _mock_tiktoken():
    class FakeEncoder:
        def encode(self, text):
            return list(range(max(1, len(text) // 4)))

        def decode(self, tokens):
            return "x" * (len(tokens) * 4)

    fake = FakeEncoder()
    with (
        patch("services.rag.token_counter._encoder", fake),
        patch("services.rag.embedding_service._encoder", fake),
        # AIServiceV2 token-estimatie: forceer de heuristiek i.p.v. tiktoken.
        # tiktoken.encoding_for_model("gpt-5.2") raist KeyError en de o200k_base
        # fallback wil downloaden (geblokkeerd) → netwerk-fouten in generator-tests
        # (DEF-413). De char-heuristiek is hermetisch en functioneel equivalent.
        patch("services.ai_service_v2.TIKTOKEN_AVAILABLE", False),
    ):
        yield


# Hard-block all outbound network access during tests unless explicitly allowed.
# Opt-out by setting environment variable ALLOW_NETWORK=1 when running pytest.
@pytest.fixture(autouse=True)
def _disable_network(monkeypatch):
    if os.getenv("ALLOW_NETWORK") == "1":
        return

    def _blocked_create_connection(*args, **kwargs):  # pragma: no cover - guard
        msg = "Network access is disabled in tests. Set ALLOW_NETWORK=1 to override."
        raise RuntimeError(msg)

    def _blocked_connect(self, *args, **kwargs):  # pragma: no cover - guard
        msg = "Network access is disabled in tests. Set ALLOW_NETWORK=1 to override."
        raise RuntimeError(msg)

    # Block common socket entry points
    monkeypatch.setattr(
        socket, "create_connection", _blocked_create_connection, raising=True
    )
    monkeypatch.setattr(socket.socket, "connect", _blocked_connect, raising=True)
    monkeypatch.setattr(socket.socket, "connect_ex", _blocked_connect, raising=True)


# Opt-in versnellen van asyncio.sleep om lokale testruns te versnellen.
# Activeer met FAST_SLEEP=1; wordt automatisch overgeslagen voor performance/benchmark/slow tests
# via test-markers in individuele tests (geen globale patch).
@pytest.fixture(autouse=True)
def _fast_asyncio_sleep(monkeypatch, request):
    import os as _os

    if _os.getenv("FAST_SLEEP") != "1":
        return

    # Niet versnellen voor performance/benchmark/slow gemarkeerde tests
    if any(
        request.node.get_closest_marker(m) for m in ("performance", "benchmark", "slow")
    ):
        return

    import asyncio as _asyncio

    _orig_sleep = _asyncio.sleep

    async def _quick_sleep(delay, *args, **kwargs):
        # Eén event loop yield om scheduling-semantiek te behouden
        if delay and delay > 0:
            await _orig_sleep(0)

    monkeypatch.setattr(_asyncio, "sleep", _quick_sleep, raising=True)
