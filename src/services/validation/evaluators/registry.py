"""Expliciet evaluatorregister (DEF-606 / ADR-001).

Registratie is expliciet: geen dynamische bestandsimport, geen
`spec_from_file_location`, geen fallback naar default-pass bij een onbekend
type. Een onbekende of dubbele registratie faalt zichtbaar, zodat een
regelrecord nooit stil zonder uitvoerbare evaluator kan blijven.
"""

from __future__ import annotations

import threading

from services.validation.evaluators.base import RuleEvaluator
from toetsregels.runtime_contract import EvaluatorType, RuleContractError

__all__ = [
    "DuplicateEvaluatorError",
    "EvaluatorRegistry",
    "UnknownEvaluatorError",
    "get_default_registry",
]


class UnknownEvaluatorError(RuleContractError):
    """Er is geen evaluator geregistreerd voor het gevraagde type."""


class DuplicateEvaluatorError(RuleContractError):
    """Voor dit evaluatortype bestaat al een registratie."""


class EvaluatorRegistry:
    """Kleine, expliciete mapping van evaluatortype naar implementatie."""

    def __init__(self) -> None:
        self._evaluators: dict[EvaluatorType, RuleEvaluator] = {}

    def register(self, evaluator: RuleEvaluator) -> None:
        soort = getattr(evaluator, "evaluator_type", None)
        if not isinstance(soort, EvaluatorType):
            msg = (
                f"{type(evaluator).__name__} declareert geen geldig "
                f"'evaluator_type' (gevonden: {soort!r})"
            )
            raise RuleContractError(msg)
        if soort in self._evaluators:
            msg = (
                f"evaluatortype {soort.value!r} is al geregistreerd door "
                f"{type(self._evaluators[soort]).__name__}"
            )
            raise DuplicateEvaluatorError(msg)
        self._evaluators[soort] = evaluator

    def resolve(self, soort: EvaluatorType | str) -> RuleEvaluator:
        try:
            sleutel = EvaluatorType(soort)
        except ValueError as exc:
            msg = f"onbekend evaluatortype {soort!r}"
            raise UnknownEvaluatorError(msg) from exc
        evaluator = self._evaluators.get(sleutel)
        if evaluator is None:
            msg = (
                f"evaluatortype {sleutel.value!r} heeft geen registratie; "
                f"geregistreerd: {sorted(t.value for t in self._evaluators)}"
            )
            raise UnknownEvaluatorError(msg)
        return evaluator

    def registered_types(self) -> frozenset[str]:
        return frozenset(soort.value for soort in self._evaluators)


_default_registry: EvaluatorRegistry | None = None
_registry_lock = threading.Lock()


def get_default_registry() -> EvaluatorRegistry:
    """Het proces-brede register met alle standaard evaluatorstrategieën."""
    global _default_registry
    if _default_registry is None:
        with _registry_lock:
            if _default_registry is None:
                from services.validation.evaluators import build_default_registry

                _default_registry = build_default_registry()
    return _default_registry
