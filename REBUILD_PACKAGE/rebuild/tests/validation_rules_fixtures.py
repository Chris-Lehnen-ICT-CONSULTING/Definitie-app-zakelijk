"""
Pytest fixtures for validation rules testing.

This module provides comprehensive fixtures for testing validation rules,
including sample definitions, rule configurations, mock AI responses,
and database connections.
"""

import json
import sqlite3
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest

# ========================================
# SAMPLE DEFINITIONS
# ========================================


@pytest.fixture()
def sample_good_definition() -> dict[str, Any]:
    """A single high-quality definition that should pass all validations."""
    return {
        "begrip": "authenticatie",
        "definitie": "Het proces waarbij de identiteit van een persoon of systeem wordt geverifieerd aan de hand van verstrekte credentials.",
        "categorie": "proces",
        "organisatorische_context": ["identiteitsbeheer", "toegangscontrole"],
        "juridische_context": ["AVG", "eIDAS"],
        "wettelijke_basis": ["AVG artikel 32"],
    }


@pytest.fixture()
def sample_bad_definition() -> dict[str, Any]:
    """A definition with multiple validation violations."""
    return {
        "begrip": "auth",
        "definitie": "Auth is auth.",
        "categorie": "proces",
        "expected_violations": ["ESS-002", "SAM-01", "VER-01"],
    }


@pytest.fixture()
def sample_circular_definition() -> dict[str, Any]:
    """A circular definition for testing ESS-002."""
    return {
        "begrip": "verificatie",
        "definitie": "Verificatie is het proces van verificatie.",
        "categorie": "proces",
        "expected_violations": ["ESS-002"],
    }


@pytest.fixture()
def sample_too_short_definition() -> dict[str, Any]:
    """A definition that's too short."""
    return {
        "begrip": "test",
        "definitie": "Een test.",
        "categorie": "type",
        "expected_violations": ["SAM-01", "VER-01"],
    }


@pytest.fixture()
def sample_too_long_definition() -> dict[str, Any]:
    """A definition that exceeds maximum length."""
    return {
        "begrip": "test",
        "definitie": "Een definitie " + "zeer " * 200 + "lang.",
        "categorie": "type",
        "expected_violations": ["SAM-01", "VER-01"],
    }


@pytest.fixture()
def all_good_definitions() -> list[dict[str, Any]]:
    """Load all good definitions from test data."""
    data_file = Path(__file__).parent.parent / "data" / "good_definitions.json"
    if data_file.exists():
        with open(data_file, encoding="utf-8") as f:
            data = json.load(f)
            return data.get("definitions", [])
    return []


@pytest.fixture()
def all_bad_definitions() -> list[dict[str, Any]]:
    """Load all bad definitions from test data."""
    data_file = Path(__file__).parent.parent / "data" / "bad_definitions.json"
    if data_file.exists():
        with open(data_file, encoding="utf-8") as f:
            data = json.load(f)
            return data.get("definitions", [])
    return []


@pytest.fixture()
def all_edge_case_definitions() -> list[dict[str, Any]]:
    """Load all edge case definitions from test data."""
    data_file = Path(__file__).parent.parent / "data" / "edge_case_definitions.json"
    if data_file.exists():
        with open(data_file, encoding="utf-8") as f:
            data = json.load(f)
            return data.get("definitions", [])
    return []


# ========================================
# VALIDATION RULE CONFIGURATIONS
# ========================================


@pytest.fixture()
def validation_rule_metadata() -> dict[str, Any]:
    """Sample validation rule metadata structure."""
    return {
        "id": "SAM-01",
        "naam": "Maximaal aantal zinnen",
        "uitleg": "Een definitie mag maximaal 3 zinnen bevatten",
        "prioriteit": "high",
        "categorie": "SAM",
        "thresholds": {"max_sentences": 3},
    }


@pytest.fixture()
def all_validation_rules() -> list[str]:
    """List of all validation rule IDs."""
    return [
        # ARAI rules
        "ARAI-01",
        "ARAI-02",
        "ARAI-03",
        "ARAI-04",
        "ARAI-05",
        "ARAI-06",
        # CON rules
        "CON-001",
        "CON-002",
        # ESS rules
        "ESS-001",
        "ESS-002",
        "ESS-003",
        "ESS-004",
        "ESS-005",
        # INT rules
        "INT-01",
        "INT-02",
        "INT-03",
        "INT-04",
        "INT-05",
        "INT-06",
        "INT-07",
        "INT-08",
        "INT-09",
        "INT-10",
        # SAM rules
        "SAM-01",
        "SAM-02",
        "SAM-03",
        "SAM-04",
        "SAM-05",
        "SAM-06",
        "SAM-07",
        "SAM-08",
        # STR rules
        "STR-001",
        "STR-002",
        "STR-003",
        "STR-004",
        "STR-005",
        "STR-006",
        "STR-007",
        "STR-008",
        "STR-009",
        # VER rules
        "VER-01",
        "VER-02",
        "VER-03",
        # DUP rule
        "DUP-001",
    ]


@pytest.fixture()
def high_priority_rules() -> list[str]:
    """List of high-priority validation rules."""
    return ["ESS-001", "ESS-002", "STR-003", "CON-001"]


@pytest.fixture()
def medium_priority_rules() -> list[str]:
    """List of medium-priority validation rules."""
    return ["STR-002", "VER-01", "VER-02", "SAM-01"]


# ========================================
# MOCK AI SERVICE RESPONSES
# ========================================


@pytest.fixture()
def mock_ai_service():
    """Mock AI service with common responses."""
    mock = AsyncMock()

    # Default response for definition generation
    mock.generate_definition.return_value = {
        "definitie": "Een gestructureerde beschrijving van een begrip binnen een specifieke context.",
        "confidence": 0.85,
        "reasoning": "Generated based on ontological patterns",
    }

    # Default response for category determination
    mock.determine_category.return_value = {
        "categorie": "type",
        "confidence": 0.90,
        "reasoning": "Based on keyword analysis",
    }

    # Default response for validation
    mock.validate_definition.return_value = {
        "score": 0.85,
        "issues": [],
        "passed": True,
    }

    return mock


@pytest.fixture()
def mock_ai_service_with_errors():
    """Mock AI service that returns errors."""
    mock = AsyncMock()

    # Simulate API errors
    mock.generate_definition.side_effect = Exception("API rate limit exceeded")

    return mock


@pytest.fixture()
def mock_validation_response() -> dict[str, Any]:
    """Sample validation response from AI service."""
    return {
        "overall_score": 0.85,
        "rule_results": [
            {
                "rule_id": "SAM-01",
                "passed": True,
                "score": 1.0,
                "message": "✔️ Definitie bevat 2 zinnen (max 3)",
            },
            {
                "rule_id": "VER-01",
                "passed": True,
                "score": 1.0,
                "message": "✔️ Lengte is adequaat",
            },
        ],
        "issues": [],
        "passed": True,
    }


# ========================================
# DATABASE FIXTURES
# ========================================


@pytest.fixture()
def temp_database():
    """Create a temporary SQLite database for testing."""
    # Create temporary database file
    temp_db = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".db")
    temp_db.close()
    db_path = Path(temp_db.name)

    # Initialize database with schema
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Create definities table
    cursor.execute(
        """
        CREATE TABLE definities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            begrip VARCHAR(255) NOT NULL,
            definitie TEXT NOT NULL,
            categorie VARCHAR(50) NOT NULL,
            organisatorische_context TEXT NOT NULL DEFAULT '[]',
            juridische_context TEXT NOT NULL DEFAULT '[]',
            wettelijke_basis TEXT NOT NULL DEFAULT '[]',
            status VARCHAR(50) NOT NULL DEFAULT 'draft',
            validation_score DECIMAL(3,2),
            validation_issues TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    # Create voorbeelden table
    cursor.execute(
        """
        CREATE TABLE voorbeelden (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            definitie_id INTEGER NOT NULL,
            voorbeeldtekst TEXT NOT NULL,
            type VARCHAR(50),
            bron VARCHAR(255),
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (definitie_id) REFERENCES definities(id)
        )
    """
    )

    conn.commit()
    conn.close()

    yield db_path

    # Cleanup
    db_path.unlink(missing_ok=True)


@pytest.fixture()
def populated_database(temp_database):
    """Temporary database populated with test data."""
    conn = sqlite3.connect(str(temp_database))
    cursor = conn.cursor()

    # Insert test definitions
    test_definitions = [
        (
            "authenticatie",
            "Het proces van identiteitsverificatie.",
            "proces",
            "[]",
            "[]",
            "[]",
        ),
        (
            "identiteitsbewijs",
            "Een document voor identiteitsvaststelling.",
            "type",
            "[]",
            "[]",
            "[]",
        ),
        (
            "verificatiebesluit",
            "Het formele besluit na verificatie.",
            "resultaat",
            "[]",
            "[]",
            "[]",
        ),
    ]

    for begrip, definitie, categorie, org_ctx, jur_ctx, wet_ctx in test_definitions:
        cursor.execute(
            """
            INSERT INTO definities (begrip, definitie, categorie, organisatorische_context, juridische_context, wettelijke_basis)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (begrip, definitie, categorie, org_ctx, jur_ctx, wet_ctx),
        )

    conn.commit()
    conn.close()

    return temp_database


@pytest.fixture()
def mock_database_connection():
    """Mock database connection for testing without actual DB."""
    mock_conn = Mock()
    mock_cursor = Mock()

    # Configure mock cursor
    mock_cursor.fetchone.return_value = {
        "id": 1,
        "begrip": "test",
        "definitie": "Een test definitie.",
        "categorie": "type",
    }

    mock_cursor.fetchall.return_value = []

    mock_conn.cursor.return_value = mock_cursor

    return mock_conn


# ========================================
# CONTEXT FIXTURES
# ========================================


@pytest.fixture()
def sample_context() -> dict[str, Any]:
    """Sample context for definition generation."""
    return {
        "organisatorische_context": ["identiteitsbeheer", "toegangscontrole"],
        "juridische_context": ["AVG", "eIDAS"],
        "wettelijke_basis": ["AVG artikel 32"],
        "voorbeelden": [
            "De gebruiker wordt geauthenticeerd met username en password.",
            "Authenticatie vindt plaats via twee-factor verificatie.",
        ],
    }


@pytest.fixture()
def sample_document_context() -> dict[str, Any]:
    """Sample document context for definition generation."""
    return {
        "document_snippets": [
            "Authenticatie is het proces waarbij de identiteit wordt geverifieerd.",
            "Het systeem ondersteunt meerdere authenticatiemethoden.",
        ],
        "document_metadata": {
            "title": "Authenticatiebeleid",
            "type": "policy",
            "date": "2024-01-01",
        },
    }


# ========================================
# ONTOLOGICAL PATTERN FIXTURES
# ========================================


@pytest.fixture()
def ontological_patterns() -> dict[str, list[str]]:
    """Ontological categorization patterns."""
    return {
        "proces": ["atie", "eren", "ing", "verificatie", "authenticatie", "validatie"],
        "type": ["bewijs", "document", "middel", "systeem", "methode"],
        "resultaat": ["besluit", "uitslag", "rapport", "conclusie"],
        "exemplaar": ["specifiek", "individueel", "uniek", "persoon"],
    }


# ========================================
# SERVICE CONTAINER FIXTURES
# ========================================


@pytest.fixture()
def mock_service_container():
    """Mock service container with all required services."""
    container = Mock()

    # Mock all required services
    container.ai_service = AsyncMock()
    container.validation_service = Mock()
    container.definition_generator = Mock()
    container.definition_repository = Mock()
    container.categorization_service = AsyncMock()

    return container
