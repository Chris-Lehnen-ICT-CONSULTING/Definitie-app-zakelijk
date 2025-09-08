"""
Global pytest configuration and fixtures for the test suite.
"""

import sys
from pathlib import Path
import pytest
import asyncio

# Add src to path for all tests
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import all fixtures from v2_service_mocks to make them globally available
sys.path.insert(0, str(Path(__file__).parent))
from fixtures.v2_service_mocks import *

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


@pytest.fixture
def test_db_path(tmp_path):
    """Provide a temporary database path for testing."""
    return str(tmp_path / "test.db")


@pytest.fixture
def in_memory_db():
    """Provide in-memory database configuration."""
    return ":memory:"


# Mark configurations for different test types
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "smoke: mark test as a smoke test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "contract: mark test as a contract test"
    )
    config.addinivalue_line(
        "markers", "tdd: mark test as TDD (expected to fail until implemented)"
    )
    config.addinivalue_line(
        "markers", "flaky: mark test as flaky (may fail intermittently)"
    )


# Configure test collection to ignore certain files
def pytest_ignore_collect(path, config):
    """Ignore certain test files during collection."""
    # Ignore US-041/042/043 tests until features are implemented
    if "us041" in str(path).lower():
        return True
    if "us042" in str(path).lower():
        return True
    if "us043" in str(path).lower():
        return True
    if "context_flow" in str(path).lower():
        return True
    return False


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
            assert self.elapsed < seconds, f"Took {self.elapsed:.2f}s, expected under {seconds}s"

    return Timer()


# Test data fixtures
@pytest.fixture
def sample_definition_data():
    """Provide sample definition data for testing."""
    return {
        "begrip": "rechtspersoon",
        "definitie": "Een juridische entiteit die rechten en plichten kan hebben",
        "ontologische_categorie": "juridisch concept"
    }


@pytest.fixture
def sample_validation_rules():
    """Provide sample validation rules for testing."""
    return [
        {"id": "RULE001", "name": "Minimum Length", "threshold": 10},
        {"id": "RULE002", "name": "Contains Definition", "threshold": 0.8},
        {"id": "RULE003", "name": "Dutch Language", "threshold": 0.9}
    ]


# Environment setup
@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-123")
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("LOG_LEVEL", "ERROR")  # Reduce log noise in tests
    return monkeypatch
