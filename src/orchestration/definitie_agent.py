"""
Compatibility shim for legacy imports: orchestration.definitie_agent

Provides minimal AgentResult and DefinitieAgent classes expected by
legacy integration code, while delegating generation to the V2
service layer via ServiceAdapter.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional


# --- Minimal legacy-shaped result structures ---


@dataclass
class GenerationContextShim:
    begrip: str
    organisatorische_context: str
    juridische_context: str


@dataclass
class GenerationResultShim:
    context: GenerationContextShim


@dataclass
class IterationShim:
    generation_result: GenerationResultShim


@dataclass
class ValidationViolationShim:
    rule_id: str
    severity: str
    description: str
    suggestion: Optional[str] = None


@dataclass
class ValidationResultShim:
    violations: List[ValidationViolationShim] = field(default_factory=list)


class AgentResult:
    """Legacy-compatible result wrapper used by DefinitieChecker."""

    def __init__(
        self,
        success: bool,
        final_definitie: str,
        final_score: float = 0.0,
        reason: str | None = None,
        iterations: list[IterationShim] | None = None,
        iteration_count: int = 1,
        validation_result: ValidationResultShim | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.success = success
        self.final_definitie = final_definitie
        self.final_score = final_score
        self.reason = reason or ""
        self.iterations = iterations or []
        self.iteration_count = iteration_count
        self.validation_result = validation_result
        self.metadata = metadata or {}


class DefinitieAgent:
    """Legacy facade that proxies to the V2 ServiceAdapter.

    The generate_definition method keeps the old signature and returns
    an AgentResult built from the V2 canonical response.
    """

    def __init__(self, max_iterations: int = 1, **_: Any) -> None:
        self.max_iterations = max_iterations

    def generate_definition(
        self,
        begrip: str,
        organisatorische_context: str,
        juridische_context: str = "",
        categorie: Any | None = None,
        *,
        selected_document_ids: list[str] | None = None,
        enable_hybrid: bool = False,
    ) -> AgentResult:
        # Lazy imports to avoid circular dependencies at import time
        from services.service_factory import get_definition_service
        from ui.helpers.async_bridge import generate_definition_sync

        # Build legacy-style context dict expected by ServiceAdapter
        context_dict = {
            "organisatorisch": [organisatorische_context] if organisatorische_context else [],
            "juridisch": [juridische_context] if juridische_context else [],
            # No wettelijke basis available in legacy call
            "wettelijk": [],
        }

        # Pass through optional args (not used directly here)
        extra_kwargs: dict[str, Any] = {
            "organisatie": organisatorische_context,
            "categorie": categorie,
        }
        # Keep hybrid options available for future use; ignored by adapter if unsupported
        if selected_document_ids is not None:
            extra_kwargs["selected_document_ids"] = selected_document_ids
        if enable_hybrid:
            extra_kwargs["enable_hybrid"] = enable_hybrid

        # Obtain V2 adapter and generate definition synchronously via bridge
        adapter = get_definition_service()
        v2_result = generate_definition_sync(
            adapter, begrip=begrip, context_dict=context_dict, **extra_kwargs
        )

        success = bool(v2_result.get("success"))
        final_def = (
            v2_result.get("definitie_gecorrigeerd")
            or v2_result.get("definitie_origineel")
            or ""
        )
        final_score = float(v2_result.get("final_score") or 0.0)
        reason = (
            v2_result.get("error_message")
            or v2_result.get("message")
            or ("OK" if success else "Unknown error")
        )

        # Build a minimal validation result shim
        validation_details = v2_result.get("validation_details") or {}
        violations_data = validation_details.get("violations") or []
        violations = [
            ValidationViolationShim(
                rule_id=str(v.get("rule_id", "unknown")),
                severity=str(v.get("severity", "low")),
                description=str(v.get("description", "")),
                suggestion=v.get("suggestion"),
            )
            for v in violations_data
        ]
        validation_result = ValidationResultShim(violations=violations)

        # Build minimal iteration/context chain used by repository save path
        context = GenerationContextShim(
            begrip=begrip,
            organisatorische_context=organisatorische_context,
            juridische_context=juridische_context,
        )
        iteration = IterationShim(generation_result=GenerationResultShim(context=context))

        return AgentResult(
            success=success,
            final_definitie=final_def,
            final_score=final_score,
            reason=reason,
            iterations=[iteration],
            iteration_count=1,
            validation_result=validation_result,
            metadata=v2_result.get("metadata") or {},
        )


# Backward-compatibility dataclass for tests importing GenerationResult from this module
from dataclasses import dataclass


@dataclass
class GenerationResult:
    definitie: str
    metadata: dict[str, Any] | None = None
    context: dict[str, Any] | None = None
    voorbeelden: dict[str, Any] | None = None
    voorbeelden_gegenereerd: bool = False
    voorbeelden_error: str | None = None

    @property
    def prompt_template(self):
        return (
            self.metadata.get("prompt_template", "Geen prompt beschikbaar")
            if self.metadata
            else "Geen prompt beschikbaar"
        )


__all__ = ["AgentResult", "DefinitieAgent", "GenerationResult"]
