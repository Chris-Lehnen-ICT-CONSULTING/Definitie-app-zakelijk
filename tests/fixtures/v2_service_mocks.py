"""
Mock fixtures for V2 services to support testing without external dependencies.
"""

import pytest
from unittest.mock import AsyncMock, Mock, MagicMock
from typing import Any
import asyncio

from services.interfaces import (
    Definition, 
    ValidationResult,
    GenerationResult,
    DefinitionResponseV2,
    WebSource
)
from services.validation.interfaces import CONTRACT_VERSION


@pytest.fixture
def mock_ai_service_v2():
    """Mock AIServiceV2 to prevent actual API calls."""
    mock = AsyncMock()
    
    # Mock the generate method
    async def mock_generate(prompt: str, **kwargs) -> str:
        """Return predictable test response."""
        return f"Generated definition for: {prompt[:50]}..."
    
    mock.generate = mock_generate
    mock.get_model = Mock(return_value="gpt-4-test")
    mock.get_temperature = Mock(return_value=0.0)
    
    return mock


@pytest.fixture
def mock_validation_orchestrator_v2():
    """Mock ValidationOrchestratorV2 for testing."""
    mock = AsyncMock()
    
    async def mock_validate_definition(definition: Definition, context=None) -> dict:
        """Return valid validation result."""
        return {
            "version": CONTRACT_VERSION,
            "overall_score": 0.85,
            "is_acceptable": True,
            "violations": [],
            "passed_rules": ["rule1", "rule2"],
            "system": {
                "correlation_id": "test-correlation-id",
                "timestamp": "2025-01-01T00:00:00Z"
            }
        }
    
    mock.validate_definition = mock_validate_definition
    return mock


@pytest.fixture
def mock_modular_validation_service():
    """Mock ModularValidationService."""
    mock = AsyncMock()
    
    async def mock_validate(begrip: str, definitie: str, **kwargs) -> ValidationResult:
        """Return mock validation result."""
        result = ValidationResult()
        result.overall_score = 0.9
        result.is_valid = True
        result.messages = []
        result.rule_results = {}
        return result
    
    mock.validate = mock_validate
    mock.validate_all = AsyncMock(return_value=[])
    
    return mock


@pytest.fixture  
def mock_web_lookup_service():
    """Mock ModernWebLookupService."""
    mock = AsyncMock()
    
    async def mock_search(query: str, **kwargs) -> list[WebSource]:
        """Return mock web sources."""
        return [
            WebSource(
                url=f"https://example.com/{query}",
                title=f"Mock result for {query}",
                snippet=f"This is a mock search result for {query}",
                reliability_score=0.8
            )
        ]
    
    mock.search = mock_search
    mock.enrich_definition = AsyncMock(return_value="Enriched definition")
    
    return mock


@pytest.fixture
def mock_prompt_service_v2():
    """Mock PromptServiceV2."""
    mock = Mock()
    
    mock.build_definition_prompt = Mock(
        return_value="Mock definition generation prompt"
    )
    mock.build_validation_prompt = Mock(
        return_value="Mock validation prompt"  
    )
    mock.get_system_prompt = Mock(
        return_value="You are a helpful assistant."
    )
    
    return mock


@pytest.fixture
def mock_definition_repository():
    """Mock DefinitionRepository for testing."""
    mock = Mock()
    
    mock.save = Mock(return_value=1)  # Return mock ID
    mock.get = Mock(return_value=Definition(
        begrip="test",
        definitie="test definition",
        ontologische_categorie="concept"
    ))
    mock.search = Mock(return_value=[])
    mock.update = Mock(return_value=True)
    mock.delete = Mock(return_value=True)
    
    return mock


@pytest.fixture
def mock_cleaning_service():
    """Mock CleaningService."""
    mock = Mock()
    
    mock.clean_text = Mock(side_effect=lambda text: text.strip())
    mock.remove_special_chars = Mock(side_effect=lambda text: text)
    mock.normalize_whitespace = Mock(side_effect=lambda text: " ".join(text.split()))
    
    return mock


@pytest.fixture
async def mock_definition_orchestrator_v2(
    mock_ai_service_v2,
    mock_validation_orchestrator_v2,
    mock_prompt_service_v2,
    mock_definition_repository,
    mock_cleaning_service,
    mock_web_lookup_service
):
    """Complete mock for DefinitionOrchestratorV2."""
    mock = AsyncMock()
    
    # Set up the service dependencies
    mock.ai_service = mock_ai_service_v2
    mock.validation_service = mock_validation_orchestrator_v2
    mock.prompt_service = mock_prompt_service_v2
    mock.repository = mock_definition_repository
    mock.cleaning_service = mock_cleaning_service
    mock.web_lookup_service = mock_web_lookup_service
    
    async def mock_create_definition(request, context=None) -> DefinitionResponseV2:
        """Mock definition creation."""
        return DefinitionResponseV2(
            success=True,
            definition=Definition(
                begrip=request.begrip,
                definitie="Mock generated definition",
                ontologische_categorie=request.ontologische_categorie or "concept"
            ),
            validation_result=await mock_validation_orchestrator_v2.validate_definition(None),
            generation_metadata={
                "model": "gpt-4-test",
                "temperature": 0.0,
                "prompt_tokens": 100,
                "completion_tokens": 50
            }
        )
    
    mock.create_definition = mock_create_definition
    mock.update_definition = AsyncMock()
    mock.validate_and_save = AsyncMock()
    
    return mock


@pytest.fixture
def mock_service_container(mock_definition_orchestrator_v2):
    """Mock ServiceContainer with all V2 services."""
    mock = Mock()
    
    mock.orchestrator = Mock(return_value=mock_definition_orchestrator_v2)
    mock.generator = Mock(return_value=mock_definition_orchestrator_v2)  # V2 is both
    mock.repository = Mock(return_value=mock_definition_repository)
    mock.web_lookup = Mock(return_value=mock_web_lookup_service)
    
    mock.config = {
        "db_path": ":memory:",
        "use_database": False,
        "enable_monitoring": False
    }
    
    mock._instances = {}
    mock.reset = Mock()
    mock.update_config = Mock()
    mock.get_service = Mock(side_effect=lambda name: {
        "generator": mock_definition_orchestrator_v2,
        "orchestrator": mock_definition_orchestrator_v2,
        "repository": mock_definition_repository,
        "web_lookup": mock_web_lookup_service
    }.get(name))
    
    return mock


# Helper functions for common test scenarios

def create_test_definition(
    begrip: str = "testbegrip",
    definitie: str = "Een test definitie",
    categorie: str = "concept"
) -> Definition:
    """Create a test Definition object."""
    return Definition(
        begrip=begrip,
        definitie=definitie,
        ontologische_categorie=categorie
    )


def create_test_validation_result(
    score: float = 0.85,
    is_valid: bool = True,
    violations: list = None
) -> dict:
    """Create a test validation result matching contract."""
    return {
        "version": ValidationContract.VERSION,
        "overall_score": score,
        "is_acceptable": is_valid,
        "violations": violations or [],
        "passed_rules": ["rule1", "rule2", "rule3"],
        "system": {
            "correlation_id": "test-id",
            "timestamp": "2025-01-01T00:00:00Z"
        }
    }


def create_test_generation_result(
    success: bool = True,
    definition_text: str = "Generated definition"
) -> GenerationResult:
    """Create a test GenerationResult."""
    return GenerationResult(
        success=success,
        definition=definition_text,
        metadata={
            "model": "gpt-4-test",
            "temperature": 0.0,
            "tokens_used": 150
        }
    )