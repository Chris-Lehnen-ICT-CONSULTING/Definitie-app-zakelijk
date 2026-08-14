"""Evaluatorstrategieën achter één expliciet register (DEF-606 / ADR-001).

Iedere strategie wordt hier met de hand geregistreerd. Er is bewust geen
autodiscovery: dynamische bestandsimport was precies het mechanisme van de
oude, niet-productieve `json_validator_loader`, en het maakt onzichtbaar
welke evaluator een regel werkelijk draait.
"""

from __future__ import annotations

from services.validation.evaluators.base import (
    EvaluationDeps,
    EvaluationOutcome,
    Finding,
    RuleEvaluator,
)
from services.validation.evaluators.compound import CompoundEvaluator
from services.validation.evaluators.context_metadata import ContextMetadataEvaluator
from services.validation.evaluators.deferred import DEFERRED_EVALUATORS
from services.validation.evaluators.duplicate_detection import (
    DuplicateDetectionEvaluator,
)
from services.validation.evaluators.generic import GenericEvaluator
from services.validation.evaluators.judgment_review import JudgmentReviewEvaluator
from services.validation.evaluators.lemma_morphology import LemmaMorphologyEvaluator
from services.validation.evaluators.ontological_category import (
    OntologicalCategoryEvaluator,
)
from services.validation.evaluators.positive_indicator import PositiveIndicatorEvaluator
from services.validation.evaluators.qualification import QualificationEvaluator
from services.validation.evaluators.registry import (
    DuplicateEvaluatorError,
    EvaluatorRegistry,
    UnknownEvaluatorError,
    get_default_registry,
)

__all__ = [
    "DuplicateEvaluatorError",
    "EvaluationDeps",
    "EvaluationOutcome",
    "EvaluatorRegistry",
    "Finding",
    "RuleEvaluator",
    "UnknownEvaluatorError",
    "build_default_registry",
    "get_default_registry",
]


def build_default_registry() -> EvaluatorRegistry:
    """Bouw een register met alle standaard evaluatorstrategieën.

    De annotatie is nodig, niet cosmetisch: zonder haar leidt mypy uit de
    heterogene tuple het gemeenschappelijke supertype `object` af, en dan
    accepteert `register` het argument niet meer. Expliciet typen bewijst
    tegelijk dat elke strategie het `RuleEvaluator`-protocol nakomt.
    """
    strategieen: tuple[RuleEvaluator, ...] = (
        GenericEvaluator(),
        PositiveIndicatorEvaluator(),
        OntologicalCategoryEvaluator(),
        LemmaMorphologyEvaluator(),
        QualificationEvaluator(),
        CompoundEvaluator(),
        ContextMetadataEvaluator(),
        DuplicateDetectionEvaluator(),
        JudgmentReviewEvaluator(),
        *DEFERRED_EVALUATORS,
    )
    registry = EvaluatorRegistry()
    for evaluator in strategieen:
        registry.register(evaluator)
    return registry
