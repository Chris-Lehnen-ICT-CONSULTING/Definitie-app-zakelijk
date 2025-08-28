"""
DefinitieAgent - Intelligente orchestrator voor iteratieve definitie verbetering.
Combineert DefinitieGenerator en DefinitieValidator in een zelf-verbeterende feedback loop.

Deze module bevat de hoofdorchestrator die AI generatie en validatie
combineert in een iteratief verbeteringsproces.
"""

import logging  # Logging faciliteiten voor debug en monitoring
import time  # Tijd functies voor prestatie meting
from dataclasses import (  # Dataklassen voor gestructureerde resultaat data
    dataclass,
    field,
)
from enum import Enum  # Enumeraties voor agent status tracking
from typing import Any  # Type hints voor betere code documentatie

from domain.ontological_categories import OntologischeCategorie
from validation.definitie_validator import (
    DefinitieValidator,
    RuleViolation,
    ValidationResult,
    ViolationSeverity,
    ViolationType,
)

# Initialiseer logger
logger = logging.getLogger(__name__)

# Import modern service interfaces
try:
    from services.container import ServiceContainer
    from services.interfaces import GenerationRequest

    MODERN_SERVICES_AVAILABLE = True
except ImportError:
    logger.error("Could not import modern service interfaces")
    MODERN_SERVICES_AVAILABLE = False


# Define compatibility classes for legacy interface
class GenerationContext:
    """Compatibility wrapper for legacy interface"""

    def __init__(
        self,
        begrip,
        organisatorische_context=None,
        juridische_context=None,
        wettelijke_basis=None,
        categorie=None,
        feedback_history=None,
        **kwargs,
    ):
        self.begrip = begrip
        self.organisatorische_context = organisatorische_context or ""
        self.juridische_context = juridische_context or ""
        self.wettelijke_basis = wettelijke_basis or []
        self.categorie = categorie
        self.feedback_history = feedback_history or []
        # Handle additional attributes from kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)


class GenerationResult:
    """Compatibility wrapper for legacy interface"""

    def __init__(self, definitie, metadata=None, context=None):
        self.definitie = definitie
        self.metadata = metadata or {}
        self.context = context  # Store context for compatibility
        self.voorbeelden = {}  # Add voorbeelden attribute
        self.voorbeelden_gegenereerd = False
        self.voorbeelden_error = None

    @property
    def prompt_template(self):
        """Get prompt template from metadata for debug section"""
        return self.metadata.get("prompt_template", "Geen prompt beschikbaar")


class DefinitieGenerator:
    """Modern DefinitionOrchestrator adapter for legacy compatibility"""

    def __init__(self, service_container=None):
        """Initialize with modern ServiceContainer"""
        self.service_container = service_container or ServiceContainer()
        logger.info("DefinitieGenerator initialized with modern DefinitionOrchestrator")

    def generate_with_examples(
        self, generation_context, _generate_examples=True, _example_types=None
    ):
        """Generate definition using modern DefinitionOrchestrator"""
        if not MODERN_SERVICES_AVAILABLE:
            return GenerationResult(
                definitie="[Error: Modern services not available]",
                metadata={"error": "Service initialization failed"},
            )

        try:
            # Get DefinitionOrchestrator via service container
            orchestrator = self.service_container.orchestrator()

            # Create GenerationRequest from legacy context
            request = GenerationRequest(
                begrip=generation_context.begrip,
                context=generation_context.organisatorische_context,  # Legacy fallback
                domein=generation_context.juridische_context,  # Legacy fallback
                organisatie=generation_context.organisatorische_context,
                extra_instructies=self._format_feedback_history(
                    generation_context.feedback_history
                ),
                # Nieuwe rijke context velden
                juridische_context=(
                    [generation_context.juridische_context]
                    if generation_context.juridische_context
                    and generation_context.juridische_context.strip()
                    else None
                ),
                wettelijke_basis=(
                    generation_context.wettelijke_basis
                    if hasattr(generation_context, "wettelijke_basis")
                    and generation_context.wettelijke_basis
                    else None
                ),
                organisatorische_context=(
                    [generation_context.organisatorische_context]
                    if generation_context.organisatorische_context
                    and generation_context.organisatorische_context.strip()
                    else None
                ),
            )

            # Run async method in sync context
            import asyncio

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                response = loop.run_until_complete(
                    orchestrator.create_definition(request)
                )
            finally:
                loop.close()

            # Convert DefinitionResponse to GenerationResult for compatibility
            if response.success and response.definition:
                generation_result = GenerationResult(
                    definitie=response.definition.definitie,
                    metadata=response.definition.metadata or {},
                    context=generation_context,  # Store original context
                )

                # Add voorbeelden if available
                if response.definition.voorbeelden:
                    generation_result.voorbeelden = {
                        "sentence": (
                            response.definition.voorbeelden[:3]
                            if response.definition.voorbeelden
                            else []
                        ),
                        "practical": (
                            response.definition.voorbeelden[3:6]
                            if len(response.definition.voorbeelden) > 3
                            else []
                        ),
                        "counter": (
                            response.definition.voorbeelden[6:]
                            if len(response.definition.voorbeelden) > 6
                            else []
                        ),
                    }
                    generation_result.voorbeelden_gegenereerd = True

                return generation_result

            return GenerationResult(
                definitie=f"[Error: {response.message}]",
                metadata={"error": response.message or "Unknown error"},
                context=generation_context,
            )

        except Exception as e:
            logger.error(f"Generation failed: {e}")
            return GenerationResult(
                definitie=f"[Error during generation: {e!s}]",
                metadata={"error": str(e)},
                context=generation_context,
            )

    def _format_feedback_history(self, feedback_history):
        """Format feedback history for extra instructions"""
        if not feedback_history:
            return None
        return "Feedback van vorige iteraties: " + "; ".join(feedback_history)


# Validatie imports zijn al bovenaan toegevoegd


class AgentStatus(Enum):
    """Status van de DefinitieAgent workflow voor voortgangsmonitoring."""

    INITIALIZING = "initializing"  # Agent wordt geïnitialiseerd
    GENERATING = "generating"  # Bezig met definitie generatie
    VALIDATING = "validating"  # Bezig met definitie validatie
    IMPROVING = "improving"  # Bezig met iteratieve verbetering
    COMPLETED = "completed"  # Workflow succesvol voltooid
    FAILED = "failed"  # Workflow mislukt


@dataclass
class IterationResult:
    """Resultaat van één iteratie in de feedback loop."""

    iteration_number: int
    definitie: str
    generation_result: GenerationResult
    validation_result: ValidationResult
    improvement_feedback: list[str]
    processing_time: float
    status: AgentStatus

    def is_successful(self) -> bool:
        """Check of deze iteratie succesvol was."""
        return (
            self.validation_result.is_acceptable
        )  # Retourneer of validatie acceptabel was

    def get_score_improvement(
        self, previous_iteration: "IterationResult" = None
    ) -> float:
        """Bereken score verbetering t.o.v. vorige iteratie."""
        if not previous_iteration:
            return 0.0
        return (
            self.validation_result.overall_score
            - previous_iteration.validation_result.overall_score
        )


@dataclass
class FeedbackContext:
    """Context informatie voor feedback generatie."""

    violations: list[RuleViolation]
    previous_attempts: list[str]
    score_history: list[float]
    successful_patterns: list[str] = field(default_factory=list)
    failed_patterns: list[str] = field(default_factory=list)


@dataclass
class AgentResult:
    """Eindresultaat van de DefinitieAgent."""

    final_definitie: str
    iterations: list[IterationResult]
    total_processing_time: float
    success: bool
    reason: str
    best_iteration: IterationResult
    improvement_history: list[float]

    @property
    def iteration_count(self) -> int:
        """Aantal uitgevoerde iteraties."""
        return len(self.iterations)

    @property
    def final_score(self) -> float:
        """Finale validatie score."""
        return (
            self.best_iteration.validation_result.overall_score
            if self.best_iteration
            else 0.0
        )

    def get_performance_metrics(self) -> dict[str, Any]:
        """Haal performance metrics op."""
        if not self.iterations:
            return {}

        scores = [it.validation_result.overall_score for it in self.iterations]
        times = [it.processing_time for it in self.iterations]

        return {
            "iterations": self.iteration_count,
            "final_score": self.final_score,
            "score_improvement": scores[-1] - scores[0] if len(scores) > 1 else 0.0,
            "average_iteration_time": sum(times) / len(times),
            "total_time": self.total_processing_time,
            "success_rate": 1.0 if self.success else 0.0,
        }


class FeedbackBuilder:
    """Bouwt intelligente feedback voor iteratieve verbetering."""

    def __init__(self):
        self.violation_feedback_mapping = self._build_violation_feedback_mapping()
        self.pattern_suggestions = self._build_pattern_suggestions()

    def build_improvement_feedback(
        self, context: FeedbackContext, iteration_number: int
    ) -> list[str]:
        """
        Bouw intelligente feedback op basis van violations en context.

        Args:
            context: FeedbackContext met violations en geschiedenis
            iteration_number: Huidige iteratie nummer

        Returns:
            List van concrete verbetersuggesties
        """
        feedback = []

        # 1. Prioriteer kritieke violations
        critical_violations = [
            v for v in context.violations if v.severity == ViolationSeverity.CRITICAL
        ]
        if critical_violations:
            feedback.extend(self._handle_critical_violations(critical_violations))

        # 2. Groepeer violations per type voor efficiënte feedback
        violation_groups = self._group_violations_by_type(context.violations)

        # 3. Genereer type-specifieke feedback
        for v_type, violations in violation_groups.items():
            type_feedback = self._generate_type_specific_feedback(
                v_type, violations, iteration_number
            )
            if type_feedback:
                feedback.extend(type_feedback)

        # 4. Leer van vorige pogingen
        if context.previous_attempts:
            learning_feedback = self._generate_learning_feedback(context)
            feedback.extend(learning_feedback)

        # 5. Positieve versterking van wat wel werkt
        if context.successful_patterns:
            reinforcement_feedback = self._generate_reinforcement_feedback(
                context.successful_patterns
            )
            feedback.extend(reinforcement_feedback)

        # Limiteer en prioriteer feedback
        return self._prioritize_feedback(feedback, max_items=5)

    def _build_violation_feedback_mapping(self) -> dict[str, str]:
        """Bouw mapping van regel violations naar specifieke feedback."""
        return {
            "CON-01": "Maak de definitie context-specifiek zonder expliciete vermelding van organisaties of context namen.",
            "CON-02": "Baseer de definitie op authentieke bronnen door verwijzing naar wetgeving of officiële standaarden.",
            "ESS-01": "Beschrijf WAT het begrip is, niet waarvoor het gebruikt wordt. Vermijd doelgerichte formuleringen.",
            "ESS-02": "Maak expliciet duidelijk of het een type/soort, proces/activiteit, resultaat/uitkomst of specifiek exemplaar betreft.",
            "ESS-03": "Voeg unieke identificerende kenmerken toe waarmee verschillende instanties onderscheiden kunnen worden.",
            "ESS-04": "Gebruik objectief meetbare criteria zoals aantallen, percentages, deadlines of verificeerbare kenmerken.",
            "ESS-05": "Benadruk de onderscheidende eigenschappen die dit begrip uniek maken t.o.v. gerelateerde begrippen.",
            "INT-01": "Formuleer als één enkele, goed gestructureerde zin zonder opsommingen of bijzinnen.",
            "INT-03": "Vervang onduidelijke verwijzingen ('deze', 'dit', 'die') door concrete begrippen of beschrijvingen.",
            "STR-01": "Start de definitie met het centrale zelfstandig naamwoord dat het begrip het best weergeeft.",
            "STR-02": "Gebruik concrete, specifieke terminologie in plaats van abstracte of vage begrippen.",
        }

    def _build_pattern_suggestions(self) -> dict[str, list[str]]:
        """Bouw pattern-based suggestions voor veelvoorkomende problemen."""
        return {
            "forbidden_context_words": [
                "Vervang 'binnen de context van' door context-specifieke eigenschappen",
                "Gebruik terminologie die herkenbaar is binnen de context zonder deze expliciet te noemen",
                "Maak impliciete verwijzingen naar relevante processen of systemen",
            ],
            "vague_terminology": [
                "Vervang 'proces' door specifieke activiteit beschrijving",
                "Gebruik concrete werkwoorden in plaats van abstracte begrippen",
                "Specificeer wat er precies gebeurt in plaats van algemene termen",
            ],
            "goal_oriented_language": [
                "Vervang 'om te...' door 'waarbij...' gevolgd door concrete actie",
                "Beschrijf de aard van het begrip in plaats van het doel",
                "Focus op WHAT it IS rather than WHAT it's FOR",
            ],
            "unclear_references": [
                "Vervang 'deze' door het specifieke begrip of object",
                "Maak alle verwijzingen expliciet en ondubbelzinnig",
                "Gebruik volledige beschrijvingen in plaats van pronomina",
            ],
        }

    def _handle_critical_violations(
        self, critical_violations: list[RuleViolation]
    ) -> list[str]:
        """Genereer urgente feedback voor kritieke violations."""
        feedback = []

        for violation in critical_violations[:3]:  # Max 3 kritieke issues tegelijk
            rule_feedback = self.violation_feedback_mapping.get(violation.rule_id)
            if rule_feedback:
                feedback.append(f"🚨 KRITIEK: {rule_feedback}")

            if violation.suggestion:
                feedback.append(f"💡 Suggestie: {violation.suggestion}")

        return feedback

    def _group_violations_by_type(
        self, violations: list[RuleViolation]
    ) -> dict[ViolationType, list[RuleViolation]]:
        """Groepeer violations per type voor efficiënte behandeling."""
        groups = {}
        for violation in violations:
            v_type = violation.violation_type
            if v_type not in groups:
                groups[v_type] = []
            groups[v_type].append(violation)
        return groups

    def _generate_type_specific_feedback(
        self,
        v_type: ViolationType,
        violations: list[RuleViolation],
        iteration_number: int,
    ) -> list[str]:
        """Genereer feedback specifiek voor violation type."""
        feedback = []

        if v_type == ViolationType.FORBIDDEN_PATTERN:
            patterns = [v.detected_pattern for v in violations if v.detected_pattern]
            unique_patterns = list(set(patterns))

            if unique_patterns:
                if iteration_number == 1:
                    feedback.append(
                        f"Vermijd deze patronen: {', '.join(unique_patterns[:3])}"
                    )
                else:
                    feedback.append(
                        f"Nog steeds aanwezig: {', '.join(unique_patterns[:2])}. Probeer alternatieve formuleringen."
                    )

        elif v_type == ViolationType.MISSING_ELEMENT:
            missing_elements = []
            for violation in violations:
                if "ontbreekt:" in violation.description:
                    element = violation.description.split("ontbreekt: ")[1]
                    missing_elements.append(element)

            if missing_elements:
                unique_missing = list(set(missing_elements))
                feedback.append(f"Voeg toe: {', '.join(unique_missing[:3])}")

        elif v_type == ViolationType.STRUCTURE_ISSUE:
            if iteration_number > 1:
                feedback.append(
                    "Focus op structuur: één duidelijke zin die start met een kernzelfstandig naamwoord"
                )
            else:
                feedback.append(
                    "Herstructureer: gebruik de template [KERNWOORD] [specificatie] [onderscheidende kenmerken]"
                )

        return feedback

    def _generate_learning_feedback(self, context: FeedbackContext) -> list[str]:
        """Genereer feedback op basis van eerdere pogingen."""
        feedback = []

        # Detecteer herhalende problemen
        if len(context.previous_attempts) > 1:
            current_score = context.score_history[-1] if context.score_history else 0
            previous_score = (
                context.score_history[-2] if len(context.score_history) > 1 else 0
            )

            if current_score <= previous_score:
                feedback.append(
                    "Vorige aanpak werkte beter. Probeer een andere benadering."
                )

            # Detecteer stagnatie
            if len(context.score_history) >= 2:
                recent_scores = context.score_history[-2:]
                if all(
                    abs(recent_scores[i] - recent_scores[i - 1]) < 0.05
                    for i in range(1, len(recent_scores))
                ):
                    feedback.append(
                        "Score stagneert. Probeer een fundamenteel andere formulering."
                    )

        return feedback

    def _generate_reinforcement_feedback(
        self, successful_patterns: list[str]
    ) -> list[str]:
        """Genereer positieve feedback voor succesvolle patronen."""
        feedback = []

        if successful_patterns:
            feedback.append(
                f"Behoud deze succesvolle elementen: {', '.join(successful_patterns[:2])}"
            )

        return feedback

    def _prioritize_feedback(
        self, feedback: list[str], max_items: int = 5
    ) -> list[str]:
        """Prioriteer en limiteer feedback tot meest belangrijke items."""
        # Sorteer op prioriteit (kritieke feedback eerst)
        prioritized = []

        # 1. Kritieke feedback eerst
        critical_feedback = [f for f in feedback if f.startswith("🚨")]
        prioritized.extend(critical_feedback)

        # 2. Concrete suggesties
        suggestion_feedback = [
            f
            for f in feedback
            if f.startswith("💡") or "Voeg toe:" in f or "Vervang" in f
        ]
        prioritized.extend(suggestion_feedback)

        # 3. Overige feedback
        other_feedback = [f for f in feedback if f not in prioritized]
        prioritized.extend(other_feedback)

        # Deduplicatie en limitering
        unique_feedback = []
        seen = set()
        for item in prioritized:
            if item not in seen:
                unique_feedback.append(item)
                seen.add(item)
                if len(unique_feedback) >= max_items:
                    break

        return unique_feedback


class DefinitieAgent:
    """Intelligente orchestrator voor iteratieve definitie verbetering."""

    def __init__(
        self,
        max_iterations: int = 3,
        acceptance_threshold: float = 0.8,
        improvement_threshold: float = 0.05,
        service_container: ServiceContainer = None,
    ):
        """
        Initialiseer DefinitieAgent met moderne ServiceContainer.

        Args:
            max_iterations: Maximum aantal iteraties
            acceptance_threshold: Minimum score voor acceptatie
            improvement_threshold: Minimum verbetering per iteratie
            service_container: ServiceContainer instance voor dependency injection
        """
        # Initialize service container
        self.service_container = service_container or ServiceContainer()

        # Initialize components via service container
        self.generator = DefinitieGenerator(self.service_container)
        self.validator = DefinitieValidator()
        self.feedback_builder = FeedbackBuilder()

        # Configuration
        self.max_iterations = max_iterations
        self.acceptance_threshold = acceptance_threshold
        self.improvement_threshold = improvement_threshold

        # State tracking
        self.current_status = AgentStatus.INITIALIZING
        self.iterations: list[IterationResult] = []
        self.start_time: float | None = None

    def generate_definition(
        self,
        begrip: str,
        organisatorische_context: str,
        juridische_context: str = "",
        categorie: OntologischeCategorie = OntologischeCategorie.TYPE,
        initial_feedback: list[str] | None = None,
        # Hybrid context parameters
        selected_document_ids: list[str] | None = None,
        enable_hybrid: bool = False,
    ) -> AgentResult:
        """
        Genereer definitie met iteratieve verbetering.
        Ondersteunt hybrid context enhancement met document integration.

        Args:
            begrip: Het te definiëren begrip
            organisatorische_context: Organisatorische context
            juridische_context: Juridische context
            categorie: Ontologische categorie
            initial_feedback: Optionele initiële feedback
            selected_document_ids: IDs van documenten voor hybrid context
            enable_hybrid: Of hybrid context enhancement gebruikt moet worden

        Returns:
            AgentResult met eindresultaat en iteratie geschiedenis
        """
        logger.info(
            f"Starting definition generation for '{begrip}' in category {categorie.value}"
        )

        self.start_time = time.time()
        self.current_status = AgentStatus.INITIALIZING
        self.iterations = []

        # Bouw initiële context met mogelijke hybrid enhancement
        generation_context = GenerationContext(
            begrip=begrip,
            organisatorische_context=organisatorische_context,
            juridische_context=juridische_context,
            categorie=categorie,
            feedback_history=initial_feedback or [],
            # Hybrid context ondersteuning
            use_hybrid_enhancement=enable_hybrid,
            hybrid_context=None,  # Wordt later gevuld door generator
        )

        # Voeg selected_document_ids toe als attribuut voor hybrid context
        if selected_document_ids and enable_hybrid:
            generation_context.selected_document_ids = selected_document_ids
            logger.info(
                f"Hybrid context enabled with {len(selected_document_ids)} documents"
            )

        best_iteration = None
        success = False
        reason = ""

        try:
            # Iteratieve verbetering loop
            for iteration in range(1, self.max_iterations + 1):
                logger.info(f"Starting iteration {iteration}/{self.max_iterations}")

                iteration_result = self._execute_iteration(
                    generation_context, iteration
                )

                self.iterations.append(iteration_result)

                # Update best iteration
                if (
                    not best_iteration
                    or iteration_result.validation_result.overall_score
                    > best_iteration.validation_result.overall_score
                ):
                    best_iteration = iteration_result

                # Check voor succes
                if iteration_result.is_successful():
                    success = True
                    reason = f"Acceptable definition achieved in iteration {iteration}"
                    logger.info(
                        f"Success! Definition accepted with score {iteration_result.validation_result.overall_score:.3f}"
                    )
                    break

                # Check voor verbetering
                if iteration > 1:
                    improvement = iteration_result.get_score_improvement(
                        self.iterations[-2]
                    )
                    if improvement < self.improvement_threshold:
                        reason = f"Insufficient improvement ({improvement:.3f}) in iteration {iteration}"
                        logger.warning(reason)
                        # Ga door voor nog een poging, maar houd dit bij

                # Bereid feedback voor voor volgende iteratie
                if iteration < self.max_iterations:
                    self._prepare_next_iteration(generation_context, iteration_result)

            # Bepaal eindresultaat
            if not success:
                if not reason:
                    reason = f"Maximum iterations ({self.max_iterations}) reached without acceptable result"
                logger.info(f"Generation completed without success: {reason}")

            self.current_status = (
                AgentStatus.COMPLETED if success else AgentStatus.FAILED
            )

        except Exception as e:
            logger.error(f"Error during definition generation: {e}")
            self.current_status = AgentStatus.FAILED
            reason = f"Error: {e!s}"
            if not best_iteration and self.iterations:
                best_iteration = self.iterations[-1]

        # Bouw eindresultaat
        total_time = time.time() - self.start_time if self.start_time else 0.0
        improvement_history = [
            it.validation_result.overall_score for it in self.iterations
        ]

        final_definitie = (
            best_iteration.definitie
            if best_iteration
            else "Failed to generate definition"
        )

        return AgentResult(
            final_definitie=final_definitie,
            iterations=self.iterations,
            total_processing_time=total_time,
            success=success,
            reason=reason,
            best_iteration=best_iteration,
            improvement_history=improvement_history,
        )

    def _execute_iteration(
        self, generation_context: GenerationContext, iteration_number: int
    ) -> IterationResult:
        """Voer één iteratie van de feedback loop uit."""
        iteration_start = time.time()

        # 1. Generate definitie
        self.current_status = AgentStatus.GENERATING
        logger.debug(
            f"Generating definition with {len(generation_context.feedback_history)} feedback items"
        )

        # Genereer definitie met voorbeelden (alleen in eerste iteratie voor performance)
        try:
            generation_result = self.generator.generate_with_examples(
                generation_context,
                _generate_examples=(
                    iteration_number == 1
                ),  # Alleen voorbeelden in eerste iteratie
                _example_types=None,  # Gebruik standaard: sentence, practical, counter
            )
            definitie = generation_result.definitie

            # Als dit niet de eerste iteratie is, kopieer voorbeelden van eerste iteratie
            if iteration_number > 1 and hasattr(self, "_first_iteration_voorbeelden"):
                generation_result.voorbeelden = self._first_iteration_voorbeelden
                generation_result.voorbeelden_gegenereerd = True
                logger.debug(
                    f"Copied examples from first iteration to iteration {iteration_number}"
                )
            elif iteration_number == 1 and generation_result.voorbeelden:
                # Bewaar voorbeelden van eerste iteratie
                self._first_iteration_voorbeelden = generation_result.voorbeelden
                logger.debug(
                    f"Stored examples from first iteration: {list(generation_result.voorbeelden.keys())}"
                )

        except Exception as e:
            logger.error(f"Error in generate: {e}")
            logger.error(f"Generation context: {generation_context}")
            raise

        # 2. Generate voorbeelden (apart van definitie)
        try:
            from voorbeelden import genereer_alle_voorbeelden

            # Converteer context naar dictionary voor voorbeelden module
            context_dict = {
                "organisatorische_context": (
                    [generation_context.organisatorische_context]
                    if generation_context.organisatorische_context
                    else []
                ),
                "juridische_context": (
                    [generation_context.juridische_context]
                    if generation_context.juridische_context
                    else []
                ),
            }

            voorbeelden = genereer_alle_voorbeelden(
                begrip=generation_context.begrip,
                definitie=definitie,
                context_dict=context_dict,
            )

            # Voeg voorbeelden toe aan generation_result
            generation_result.voorbeelden = voorbeelden
            generation_result.voorbeelden_gegenereerd = True
            logger.info(f"Generated examples for {len(voorbeelden)} types")

        except Exception as e:
            logger.error(f"Error generating voorbeelden: {e}")
            generation_result.voorbeelden_error = str(e)
            generation_result.voorbeelden_gegenereerd = False

        # 3. Validate definitie
        self.current_status = AgentStatus.VALIDATING
        logger.debug(f"Validating generated definition: '{definitie[:50]}...'")

        validation_result = self.validator.validate(
            definitie, generation_context.categorie
        )

        # 3. Generate improvement feedback (als niet de laatste iteratie)
        self.current_status = AgentStatus.IMPROVING
        improvement_feedback = []

        if not validation_result.is_acceptable:
            feedback_context = self._build_feedback_context(
                validation_result, generation_context
            )
            improvement_feedback = self.feedback_builder.build_improvement_feedback(
                feedback_context, iteration_number
            )

        processing_time = time.time() - iteration_start

        # Bepaal status
        status = (
            AgentStatus.COMPLETED
            if validation_result.is_acceptable
            else AgentStatus.IMPROVING
        )

        logger.info(
            f"Iteration {iteration_number}: Score {validation_result.overall_score:.3f}, "
            f"Violations: {len(validation_result.violations)}, "
            f"Acceptable: {validation_result.is_acceptable}"
        )

        return IterationResult(
            iteration_number=iteration_number,
            definitie=definitie,
            generation_result=generation_result,
            validation_result=validation_result,
            improvement_feedback=improvement_feedback,
            processing_time=processing_time,
            status=status,
        )

    def _build_feedback_context(
        self,
        validation_result: ValidationResult,
        generation_context: GenerationContext,  # noqa: ARG002
    ) -> FeedbackContext:
        """Bouw context voor feedback generatie."""
        # Collect score history
        score_history = [it.validation_result.overall_score for it in self.iterations]
        score_history.append(validation_result.overall_score)

        # Collect previous attempts
        previous_attempts = [it.definitie for it in self.iterations]

        # Analyze successful patterns (for future enhancement)
        successful_patterns = []
        failed_patterns = []

        return FeedbackContext(
            violations=validation_result.violations,
            previous_attempts=previous_attempts,
            score_history=score_history,
            successful_patterns=successful_patterns,
            failed_patterns=failed_patterns,
        )

    def _prepare_next_iteration(
        self, generation_context: GenerationContext, iteration_result: IterationResult
    ):
        """Bereid context voor voor volgende iteratie."""
        # Voeg feedback toe aan context voor volgende iteratie
        if iteration_result.improvement_feedback:
            generation_context.feedback_history.extend(
                iteration_result.improvement_feedback
            )

            # Limiteer feedback history om prompt bloat te voorkomen
            if len(generation_context.feedback_history) > 10:
                generation_context.feedback_history = (
                    generation_context.feedback_history[-10:]
                )

    def get_status(self) -> dict[str, Any]:
        """Haal huidige status op."""
        return {
            "status": self.current_status.value,
            "iterations_completed": len(self.iterations),
            "max_iterations": self.max_iterations,
            "current_best_score": max(
                (it.validation_result.overall_score for it in self.iterations),
                default=0.0,
            ),
            "processing_time": (
                time.time() - self.start_time if self.start_time else 0.0
            ),
        }


# Convenience functions
def generate_definition_with_feedback(
    begrip: str,
    organisatorische_context: str,
    categorie: str = "type",
    max_iterations: int = 3,
    service_container: ServiceContainer = None,
    **kwargs,
) -> AgentResult:
    """
    Convenience functie voor definitie generatie met feedback loop.
    Gebruikt moderne ServiceContainer architectuur.

    Args:
        begrip: Het te definiëren begrip
        organisatorische_context: Organisatorische context
        categorie: Ontologische categorie ("type", "proces", "resultaat", "exemplaar")
        max_iterations: Maximum aantal iteraties
        service_container: ServiceContainer instance voor dependency injection
        **kwargs: Extra parameters

    Returns:
        AgentResult met eindresultaat
    """
    # Convert string to enum
    cat_mapping = {
        "type": OntologischeCategorie.TYPE,
        "proces": OntologischeCategorie.PROCES,
        "resultaat": OntologischeCategorie.RESULTAAT,
        "exemplaar": OntologischeCategorie.EXEMPLAAR,
    }

    cat_enum = cat_mapping.get(categorie.lower(), OntologischeCategorie.TYPE)

    # Initialize agent with service container for modern architecture
    agent = DefinitieAgent(
        max_iterations=max_iterations, service_container=service_container
    )

    return agent.generate_definition(
        begrip=begrip,
        organisatorische_context=organisatorische_context,
        juridische_context=kwargs.get("juridische_context", ""),
        categorie=cat_enum,
        initial_feedback=kwargs.get("initial_feedback"),
        selected_document_ids=kwargs.get("selected_document_ids"),
        enable_hybrid=kwargs.get("enable_hybrid", False),
    )


if __name__ == "__main__":
    # Test de DefinitieAgent
    print("🤖 Testing DefinitieAgent")
    print("=" * 30)

    # Test FeedbackBuilder
    print("🔧 Testing FeedbackBuilder...")
    feedback_builder = FeedbackBuilder()

    # Mock violations voor test
    from validation.definitie_validator import (
        RuleViolation,
        ViolationSeverity,
        ViolationType,
    )

    mock_violations = [
        RuleViolation(
            rule_id="CON-01",
            rule_name="Context regel",
            violation_type=ViolationType.FORBIDDEN_PATTERN,
            severity=ViolationSeverity.CRITICAL,
            description="Verboden patroon gevonden",
            detected_pattern="binnen de context",
        )
    ]

    feedback_context = FeedbackContext(
        violations=mock_violations,
        previous_attempts=["Eerdere poging"],
        score_history=[0.6, 0.7],
    )

    feedback = feedback_builder.build_improvement_feedback(feedback_context, 2)
    print(f"✅ Generated feedback: {len(feedback)} items")
    for item in feedback:
        print(f"   - {item}")

    # Test DefinitieAgent with modern architecture
    print("\n🤖 Testing DefinitieAgent...")
    service_container = ServiceContainer() if MODERN_SERVICES_AVAILABLE else None
    agent = DefinitieAgent(
        max_iterations=2,  # Beperkt voor test
        service_container=service_container,
    )

    result = agent.generate_definition(
        begrip="verificatie",
        organisatorische_context="DJI",
        categorie=OntologischeCategorie.PROCES,
    )

    print("\n📊 Agent Results:")
    print(f"   Success: {result.success}")
    print(f"   Iterations: {result.iteration_count}")
    print(f"   Final score: {result.final_score:.3f}")
    print(f"   Processing time: {result.total_processing_time:.2f}s")
    print(f"   Reason: {result.reason}")
    print(f"   Final definition: {result.final_definitie[:100]}...")

    # Performance metrics
    metrics = result.get_performance_metrics()
    print("\n📈 Performance Metrics:")
    for key, value in metrics.items():
        if isinstance(value, float):
            print(f"   {key}: {value:.3f}")
        else:
            print(f"   {key}: {value}")

    # Test convenience function
    print("\n🔧 Testing convenience function...")
    quick_result = generate_definition_with_feedback(
        "toezicht",
        "OM",
        "proces",
        max_iterations=1,
        service_container=service_container,
    )
    print(
        f"✅ Quick result: {quick_result.success}, Score: {quick_result.final_score:.3f}"
    )

    print("\n🎯 DefinitieAgent test voltooid!")
