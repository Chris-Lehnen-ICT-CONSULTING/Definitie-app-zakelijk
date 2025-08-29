from __future__ import annotations

import json
import re
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from jsonschema import FormatChecker, ValidationError, validate
from services.interfaces import Definition
from services.validation.interfaces import (
    CONTRACT_VERSION,
    ValidationContext,
    ValidationRequest,
)

from tests.contracts.mock_orchestrator import MockValidationOrchestrator


class SchemaValidator:
    """Helper for JSON schema validation with format checking and extra guards."""

    def __init__(self) -> None:
        schema_path = (
            Path(__file__).parents[2]
            / "docs/architecture/contracts/schemas/validation_result.schema.json"
        )
        with open(schema_path, encoding="utf-8") as f:
            self.schema = json.load(f)
        self.format_checker = FormatChecker()
        self.error_code_pattern = re.compile(r"^[A-Z]{3}-[A-Z]{3}-\d{3}$")

    def validate_result(self, result: dict) -> None:
        validate(
            instance=result, schema=self.schema, format_checker=self.format_checker
        )
        self._validate_error_codes(result)
        self._validate_correlation_id_format(result)

    def _validate_error_codes(self, result: dict) -> None:
        for violation in result.get("violations", []):
            code = violation.get("code", "")
            if code and not self.error_code_pattern.match(code):
                raise ValidationError(
                    f"Invalid error code format: {code}. Expected pattern: XXX-XXX-NNN"
                )

    def _validate_correlation_id_format(self, result: dict) -> None:
        correlation_id = result.get("system", {}).get("correlation_id")
        if correlation_id:
            UUID(correlation_id)


@pytest.fixture()
def schema_validator() -> SchemaValidator:
    return SchemaValidator()


@pytest.fixture()
def mock_orchestrator() -> MockValidationOrchestrator:
    return MockValidationOrchestrator()


@pytest.fixture()
def validation_context() -> ValidationContext:
    return ValidationContext(
        correlation_id=UUID("12345678-1234-5678-1234-567812345678"),
        profile="test",
        locale="nl-NL",
        feature_flags={"test_mode": True},
    )


@pytest.mark.contract()
class TestValidationInterfaceContract:
    @pytest.mark.asyncio()
    async def test_happy_path_text_validation(
        self,
        mock_orchestrator: MockValidationOrchestrator,
        schema_validator: SchemaValidator,
        validation_context: ValidationContext,
    ) -> None:
        result = await mock_orchestrator.validate_text(
            begrip="natuurlijk persoon",
            text="Een mens van vlees en bloed met rechtspersoonlijkheid",
            ontologische_categorie="juridisch",
            context=validation_context,
        )

        schema_validator.validate_result(result)

        assert result["version"] == CONTRACT_VERSION
        assert 0.0 <= result["overall_score"] <= 1.0
        assert isinstance(result["is_acceptable"], bool)
        assert isinstance(result["violations"], list)
        assert isinstance(result["passed_rules"], list)
        assert isinstance(result["detailed_scores"], dict)
        assert result["system"]["correlation_id"] == str(
            validation_context.correlation_id
        )

    @pytest.mark.asyncio()
    async def test_empty_text_validation(
        self,
        mock_orchestrator: MockValidationOrchestrator,
        schema_validator: SchemaValidator,
    ) -> None:
        result = await mock_orchestrator.validate_text(
            begrip="test begrip", text="", context=None
        )

        schema_validator.validate_result(result)
        assert result["is_acceptable"] is False
        assert result["overall_score"] == 0.0
        assert len(result["violations"]) > 0
        # Auto-generated correlation id present
        assert "correlation_id" in result["system"]
        UUID(result["system"]["correlation_id"])  # raises if invalid

    @pytest.mark.asyncio()
    async def test_degraded_result_on_failure(
        self, schema_validator: SchemaValidator, validation_context: ValidationContext
    ) -> None:
        failing = MockValidationOrchestrator(should_fail=True)
        result = await failing.validate_text(
            begrip="test", text="test text", context=validation_context
        )

        schema_validator.validate_result(result)
        assert result["is_acceptable"] is False
        assert any(
            v["code"].startswith("SYS-") for v in result["violations"]
        )  # SYS-* code
        assert "error" in result["system"]

    @pytest.mark.asyncio()
    async def test_batch_validation_order_preserved(
        self,
        mock_orchestrator: MockValidationOrchestrator,
        schema_validator: SchemaValidator,
    ) -> None:
        items = [
            ValidationRequest(
                begrip=f"begrip_{i}",
                text=f"text_{i}",
                context=ValidationContext(correlation_id=uuid4()),
            )
            for i in range(5)
        ]
        results = await mock_orchestrator.batch_validate(items, max_concurrency=3)

        assert len(results) == len(items)
        for item, result in zip(items, results, strict=False):
            schema_validator.validate_result(result)
            assert result["system"]["correlation_id"] == str(
                item.context.correlation_id
            )

    @pytest.mark.asyncio()
    async def test_definition_validation_includes_scores(
        self,
        mock_orchestrator: MockValidationOrchestrator,
        schema_validator: SchemaValidator,
        validation_context: ValidationContext,
    ) -> None:
        definition = Definition(
            begrip="natuurlijk persoon",
            definitie="Een mens",
            ontologische_categorie="juridisch",
            bron="test",
        )
        result = await mock_orchestrator.validate_definition(
            definition, context=validation_context
        )

        schema_validator.validate_result(result)
        for category in ["taal", "juridisch", "structuur", "samenhang"]:
            assert category in result["detailed_scores"]
            assert 0.0 <= result["detailed_scores"][category] <= 1.0

    @pytest.mark.parametrize("score", [0.0, 0.5, 1.0])
    @pytest.mark.asyncio()
    async def test_score_boundaries(
        self,
        schema_validator: SchemaValidator,
        validation_context: ValidationContext,
        score: float,
    ) -> None:
        orch = MockValidationOrchestrator(default_score=score)
        result = await orch.validate_text(
            begrip="test",
            text="test text",
            context=validation_context,
        )
        schema_validator.validate_result(result)
        assert result["overall_score"] == score

    def test_additional_properties_rejected(
        self, schema_validator: SchemaValidator
    ) -> None:
        result = {
            "version": CONTRACT_VERSION,
            "overall_score": 0.85,
            "is_acceptable": True,
            "violations": [],
            "passed_rules": ["TEST-001"],
            "detailed_scores": {"taal": 0.9},
            "system": {"correlation_id": str(uuid4())},
            "extra_field": "should not be allowed",
        }
        with pytest.raises(ValidationError):
            schema_validator.validate_result(result)

    @pytest.mark.parametrize(
        "invalid_code",
        [
            "INVALID",
            "VAL-TST-1",
            "val-tst-001",
            "VAL_TST_001",
            "VAL-TOOLONG-001",
        ],
    )
    def test_invalid_error_codes_rejected(
        self, schema_validator: SchemaValidator, invalid_code: str
    ) -> None:
        result = {
            "version": CONTRACT_VERSION,
            "overall_score": 0.5,
            "is_acceptable": False,
            "violations": [
                {
                    "code": invalid_code,
                    "severity": "error",
                    "message": "Test error",
                    "rule_id": "TEST",
                    "category": "system",
                }
            ],
            "passed_rules": [],
            "detailed_scores": {},
            "system": {"correlation_id": str(uuid4())},
        }
        with pytest.raises(ValidationError):
            schema_validator.validate_result(result)
