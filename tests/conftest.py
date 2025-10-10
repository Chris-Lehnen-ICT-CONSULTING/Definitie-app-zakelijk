"""
Global pytest configuration and fixtures for the test suite.
"""

import asyncio
import builtins
import os
import socket
import sys
from pathlib import Path

import pytest

# Ensure src directory is on sys.path for imports
# This is redundant with pytest.ini but ensures it's available during collection
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Install a minimal Streamlit mock BEFORE importing modules that might reference it
# Ensure tests directory is on sys.path to import our mock module
sys.path.insert(0, str(Path(__file__).parent))
try:
    from mocks.streamlit_mock import get_streamlit_mock  # type: ignore

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
    from config import get_api_config as _compat_get_api_config
    from config import get_cache_config as _compat_get_cache_config
    from config import get_default_model as _compat_get_default_model
    from config import get_default_temperature as _compat_get_default_temperature
    from config import get_paths_config as _compat_get_paths_config

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


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset singleton instances between tests."""
    # Reset the global container if it exists
    try:
        from services.container import reset_container

        reset_container()
    except ImportError:
        pass


@pytest.fixture()
def test_db_path(tmp_path):
    """Provide a temporary database path for testing."""
    return str(tmp_path / "test.db")


@pytest.fixture()
def in_memory_db():
    """Provide in-memory database configuration."""
    return ":memory:"


@pytest.fixture()
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
    if "/debug/" in p.replace("\\", "/"):
        return True
    return False


# Performance monitoring for tests
@pytest.fixture()
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

    @pytest.fixture()
    def benchmark():
        def run(fn, *args, **kwargs):
            return fn(*args, **kwargs)

        return run


# Test data fixtures
@pytest.fixture()
def sample_definition_data():
    """Provide sample definition data for testing."""
    return {
        "begrip": "rechtspersoon",
        "definitie": "Een juridische entiteit die rechten en plichten kan hebben",
        "ontologische_categorie": "juridisch concept",
    }


@pytest.fixture()
def sample_validation_rules():
    """Provide sample validation rules for testing."""
    return [
        {"id": "RULE001", "name": "Minimum Length", "threshold": 10},
        {"id": "RULE002", "name": "Contains Definition", "threshold": 0.8},
        {"id": "RULE003", "name": "Dutch Language", "threshold": 0.9},
    ]


# Environment setup
@pytest.fixture()
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-123")
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("LOG_LEVEL", "ERROR")  # Reduce log noise in tests
    return monkeypatch


# Opt-in fixture to sandbox relative writes under a temporary directory.
# Usage: add 'chdir_tmp_path' to your test function signature.
@pytest.fixture()
def chdir_tmp_path(tmp_path, monkeypatch):
    """Change CWD to pytest's tmp_path for the duration of a test.

    Useful to prevent accidental creation of files in the repository root
    by code that uses relative paths.
    Returns the temporary path for convenience.
    """
    monkeypatch.chdir(tmp_path)
    return tmp_path


# Hard-block all outbound network access during tests unless explicitly allowed.
# Opt-out by setting environment variable ALLOW_NETWORK=1 when running pytest.
@pytest.fixture(autouse=True)
def _disable_network(monkeypatch):
    if os.getenv("ALLOW_NETWORK") == "1":
        return

    def _blocked_create_connection(*args, **kwargs):  # pragma: no cover - guard
        raise RuntimeError(
            "Network access is disabled in tests. Set ALLOW_NETWORK=1 to override."
        )

    def _blocked_connect(self, *args, **kwargs):  # pragma: no cover - guard
        raise RuntimeError(
            "Network access is disabled in tests. Set ALLOW_NETWORK=1 to override."
        )

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
