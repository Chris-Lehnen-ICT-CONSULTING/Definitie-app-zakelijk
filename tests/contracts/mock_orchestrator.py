from __future__ import annotations

from collections.abc import Iterable
from uuid import uuid4

from services.interfaces import Definition
from services.validation.interfaces import (CONTRACT_VERSION,
                                            ValidationContext,
                                            ValidationOrchestratorInterface,
                                            ValidationRequest,
                                            ValidationResult)


class MockValidationOrchestrator(ValidationOrchestratorInterface):
    """Concrete mock orchestrator for contract testing.

    Produces schema-conform ValidationResult dictionaries for
    happy/edge/degraded scenarios.
    """

    def __init__(
        self,
        *,
        should_fail: bool = False,
        degraded_mode: bool = False,
        default_score: float | None = None,
        delay_ms: int | None = None,  # not used, placeholder for later perf tests
    ) -> None:
        self.should_fail = should_fail
        self.degraded_mode = degraded_mode
        self.default_score = default_score
        self.delay_ms = delay_ms

    async def validate_text(
        self,
        begrip: str,
        text: str,
        ontologische_categorie: str | None = None,
        context: ValidationContext | None = None,
    ) -> ValidationResult:
        correlation_id = (
            str(context.correlation_id)
            if context and context.correlation_id
            else str(uuid4())
        )

        # Degraded path (simulated upstream failure)
        if self.should_fail or self.degraded_mode:
            return {
                "version": CONTRACT_VERSION,
                "overall_score": 0.0,
                "is_acceptable": False,
                "violations": [
                    {
                        "code": "SYS-SVC-001",
                        "severity": "error",
                        "message": "Service temporarily unavailable",
                        "rule_id": "SYSTEM",
                        "category": "system",
                    }
                ],
                "passed_rules": [],
                "detailed_scores": {},
                "system": {
                    "correlation_id": correlation_id,
                    "error": "Upstream timeout",
                },
            }

        # Empty text → violation
        if text == "":
            return {
                "version": CONTRACT_VERSION,
                "overall_score": 0.0,
                "is_acceptable": False,
                "violations": [
                    {
                        "code": "VAL-STR-001",
                        "severity": "error",
                        "message": "Tekst mag niet leeg zijn",
                        "rule_id": "ARAI04SUB1",
                        "category": "structuur",
                    }
                ],
                "passed_rules": [],
                "detailed_scores": {
                    "taal": 0.8,
                    "structuur": 0.0,
                    "juridisch": 0.9,
                    "samenhang": 0.7,
                },
                "system": {"correlation_id": correlation_id},
            }

        # Happy path
        score = self.default_score if self.default_score is not None else 0.85
        return {
            "version": CONTRACT_VERSION,
            "overall_score": score,
            "is_acceptable": True,
            "violations": [],
            "passed_rules": ["TAAL01", "TAAL02", "STRU01", "JURI01"],
            "detailed_scores": {
                "taal": 0.9,
                "structuur": 0.8,
                "juridisch": 0.9,
                "samenhang": 0.8,
            },
            "system": {
                "correlation_id": correlation_id,
                "engine_version": "2.1.0",
                "profile_used": (
                    context.profile if context and context.profile else "default"
                ),
                "timestamp": "2025-08-29T10:00:00Z",
                "duration_ms": 150,
                "timings": {
                    "cleaning_ms": 10,
                    "validation_ms": 120,
                    "enhancement_ms": 20,
                },
            },
        }

    async def validate_definition(
        self,
        definition: Definition,
        context: ValidationContext | None = None,
    ) -> ValidationResult:
        # Delegate to validate_text with definition content
        return await self.validate_text(
            begrip=definition.begrip,
            text=definition.definitie,
            ontologische_categorie=definition.ontologische_categorie,
            context=context,
        )

    async def batch_validate(
        self, items: Iterable[ValidationRequest], max_concurrency: int = 1
    ) -> list[ValidationResult]:
        results: list[ValidationResult] = []
        for item in items:
            results.append(
                await self.validate_text(
                    item.begrip, item.text, item.ontologische_categorie, item.context
                )
            )
        return results
