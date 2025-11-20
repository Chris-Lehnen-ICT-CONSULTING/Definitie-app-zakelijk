"""Adapter for executing validation modules (rules) with isolation.

Handles both sync and async rule validators, passing an EvaluationContext
and catching exceptions to mark individual rules as errored instead of
failing the whole validation process.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any

from .types_internal import EvaluationContext, RuleResult


class ValidationModuleAdapter:
    """Executes a single validation rule safely.

    The rule object is expected to expose a `code` attribute and a
    `validate(context)` method that may be sync or async.
    """

    def __init__(self) -> None:
        pass

    async def evaluate(
        self,
        rule: Any,
        context: EvaluationContext | Any,
        params: dict[str, Any] | None = None,
    ) -> RuleResult | dict[str, Any]:
        """Evaluate a rule (async/sync tolerant) and return a RuleResult-like object.

        Catches exceptions and returns an errored result with empty violations,
        as required by error isolation tests.
        """
        rule_code = getattr(rule, "code", getattr(rule, "id", "UNKNOWN"))
        try:
            validate_fn: Callable[..., Any] | None = getattr(rule, "validate", None)
            if validate_fn is None:
                # No validate function; treat as pass with score 1.0
                return RuleResult(rule_code=rule_code, score=1.0).__dict__

            result = (
                validate_fn(context)
                if params is None
                else validate_fn(context, **params)
            )

            if asyncio.iscoroutine(result):
                result = await result  # Await async validators

            rr = RuleResult.from_rule_output(rule_code, result)
            return rr.__dict__  # Dict-like for broad compatibility in tests

        except Exception as e:  # Error isolation per rule
            rr = RuleResult.from_error(rule_code, e)
            # Ensure violations is always an empty list for errored rules
            rr.violations = []
            return rr.__dict__

    def evaluate_sync(
        self,
        rule: Any,
        context: EvaluationContext | Any,
        params: dict[str, Any] | None = None,
    ) -> RuleResult | dict[str, Any]:
        """Synchronous evaluation (used in some unit tests)."""
        rule_code = getattr(rule, "code", getattr(rule, "id", "UNKNOWN"))
        try:
            validate_fn: Callable[..., Any] | None = getattr(rule, "validate", None)
            if validate_fn is None:
                return RuleResult(rule_code=rule_code, score=1.0)
            result = (
                validate_fn(context)
                if params is None
                else validate_fn(context, **params)
            )
            return RuleResult.from_rule_output(rule_code, result)
        except Exception as e:
            return RuleResult.from_error(rule_code, e)
