"""
DefinitionOrchestrator service implementatie.

Deze service orkestreert het complete proces van definitie creatie,
validatie en opslag door de verschillende services te coördineren.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from services.interfaces import (
    Definition,
    DefinitionGeneratorInterface,
    DefinitionOrchestratorInterface,
    DefinitionRepositoryInterface,
    DefinitionResponse,
    DefinitionValidatorInterface,
    GenerationRequest,
    ValidationResult,
)

# Optionele imports voor extra functionaliteit
try:
    # Legacy import replaced with modern service
    # from web_lookup.bron_lookup import zoek_bronnen_voor_begrip  # DEPRECATED
    
    # Modern replacement using ModernWebLookupService
    async def zoek_bronnen_voor_begrip(term: str):
        """Modern replacement for source lookup"""
        from services.modern_web_lookup_service import ModernWebLookupService
        from services.interfaces import LookupRequest
        
        service = ModernWebLookupService()
        request = LookupRequest(term=term, max_results=5)
        results = await service.lookup(request)
        
        # Extract sources from results
        sources = []
        for result in results:
            sources.append({
                'name': result.source.name,
                'url': result.source.url,
                'confidence': result.source.confidence
            })
        return sources

    WEB_LOOKUP_AVAILABLE = True
except ImportError:
    WEB_LOOKUP_AVAILABLE = False

try:
    from voorbeelden.unified_voorbeelden import genereer_alle_voorbeelden_async

    EXAMPLES_AVAILABLE = True
except ImportError:
    EXAMPLES_AVAILABLE = False

logger = logging.getLogger(__name__)


class ProcessingStep(Enum):
    """Stappen in het definitie verwerkingsproces."""

    GENERATION = "generation"
    VALIDATION = "validation"
    ENRICHMENT = "enrichment"
    STORAGE = "storage"
    COMPLETED = "completed"


@dataclass
class OrchestratorConfig:
    """Configuratie voor de DefinitionOrchestrator."""

    enable_validation: bool = True
    enable_enrichment: bool = True
    enable_web_lookup: bool = True
    enable_examples: bool = True
    enable_auto_save: bool = True
    save_drafts: bool = True
    min_quality_score: float = 0.6
    parallel_enrichment: bool = True
    retry_on_failure: bool = True
    max_retries: int = 3


@dataclass
class ProcessingContext:
    """Context voor het verwerken van een definitie."""

    request: GenerationRequest
    definition: Optional[Definition] = None
    validation_result: Optional[ValidationResult] = None
    enrichment_data: Dict[str, Any] = field(default_factory=dict)
    current_step: ProcessingStep = ProcessingStep.GENERATION
    start_time: datetime = field(default_factory=datetime.now)
    errors: List[str] = field(default_factory=list)


class DefinitionOrchestrator(DefinitionOrchestratorInterface):
    """
    Service voor het orkestreren van definitie operaties.

    Deze implementatie coördineert de verschillende services om een
    complete definitie workflow te bieden: generatie, validatie,
    verrijking en opslag.
    """

    def __init__(
        self,
        generator: DefinitionGeneratorInterface,
        validator: DefinitionValidatorInterface,
        repository: DefinitionRepositoryInterface,
        config: Optional[OrchestratorConfig] = None,
    ):
        """
        Initialiseer de DefinitionOrchestrator.

        Args:
            generator: Service voor definitie generatie
            validator: Service voor definitie validatie
            repository: Service voor definitie opslag
            config: Optionele configuratie
        """
        self.generator = generator
        self.validator = validator
        self.repository = repository
        self.config = config or OrchestratorConfig()

        self._stats = {
            "total_requests": 0,
            "successful_creations": 0,
            "failed_creations": 0,
            "average_processing_time": 0.0,
            "validation_failures": 0,
            "enrichment_successes": 0,
        }

        logger.info("DefinitionOrchestrator geïnitialiseerd")

    async def create_definition(self, request: GenerationRequest) -> DefinitionResponse:
        """
        Orkestreer het complete proces van definitie creatie.

        Dit omvat:
        1. Generatie van de definitie
        2. Validatie van de kwaliteit
        3. Verrijking met extra data (optioneel)
        4. Opslag in de repository (optioneel)

        Args:
            request: GenerationRequest met input data

        Returns:
            DefinitionResponse met resultaat en status
        """
        self._stats["total_requests"] += 1
        context = ProcessingContext(request=request)

        try:
            # Stap 1: Genereer definitie
            context.current_step = ProcessingStep.GENERATION
            context.definition = await self._generate_definition(context)

            if not context.definition:
                raise ValueError("Generatie mislukt: geen definitie ontvangen")

            # Stap 2: Valideer definitie (optioneel)
            if self.config.enable_validation:
                context.current_step = ProcessingStep.VALIDATION
                context.validation_result = await self._validate_definition(context)

                # Check kwaliteit
                if context.validation_result.score < self.config.min_quality_score:
                    self._stats["validation_failures"] += 1
                    if not self.config.save_drafts:
                        return self._create_failed_response(
                            context,
                            f"Kwaliteitsscore te laag: {context.validation_result.score:.2f}",
                        )

            # Stap 3: Verrijk definitie (optioneel)
            if self.config.enable_enrichment:
                context.current_step = ProcessingStep.ENRICHMENT
                await self._enrich_definition(context)

            # Stap 4: Sla op in repository (optioneel)
            if self.config.enable_auto_save:
                context.current_step = ProcessingStep.STORAGE
                await self._save_definition(context)

            # Markeer als voltooid
            context.current_step = ProcessingStep.COMPLETED
            self._stats["successful_creations"] += 1

            # Update processing time statistieken
            processing_time = (datetime.now() - context.start_time).total_seconds()
            self._update_average_processing_time(processing_time)

            # Creëer succesvolle response
            return DefinitionResponse(
                definition=context.definition,
                validation=context.validation_result,
                definition_id=context.definition.id,
                success=True,
                message="Definitie succesvol aangemaakt",
            )

        except Exception as e:
            self._stats["failed_creations"] += 1
            logger.error(f"Fout in create_definition: {e}", exc_info=True)
            context.errors.append(str(e))
            return self._create_failed_response(context, str(e))

    async def update_definition(
        self, definition_id: int, updates: Dict[str, Any]
    ) -> DefinitionResponse:
        """
        Orkestreer het update proces van een bestaande definitie.

        Args:
            definition_id: ID van de te updaten definitie
            updates: Dictionary met veld updates

        Returns:
            DefinitionResponse met resultaat en status
        """
        try:
            # Haal bestaande definitie op
            existing = self.repository.get(definition_id)
            if not existing:
                return DefinitionResponse(
                    definition=Definition(),
                    success=False,
                    message=f"Definitie met ID {definition_id} niet gevonden",
                )

            # Pas updates toe
            for field, value in updates.items():
                if hasattr(existing, field):
                    setattr(existing, field, value)

            # Update timestamp
            existing.updated_at = datetime.now()

            # Valideer geüpdatete definitie
            validation_result = None
            if self.config.enable_validation:
                validation_result = self.validator.validate(existing)

                # Alleen validatie voor gewijzigde velden
                if "definitie" in updates or "begrip" in updates:
                    if validation_result.score < self.config.min_quality_score:
                        return DefinitionResponse(
                            definition=existing,
                            validation=validation_result,
                            success=False,
                            message=f"Update geweigerd: kwaliteitsscore te laag ({validation_result.score:.2f})",
                        )

            # Sla updates op
            success = self.repository.update(definition_id, existing)

            if success:
                return DefinitionResponse(
                    definition=existing,
                    validation=validation_result,
                    success=True,
                    message="Definitie succesvol geüpdatet",
                )
            else:
                return DefinitionResponse(
                    definition=existing,
                    validation=validation_result,
                    success=False,
                    message="Update mislukt in repository",
                )

        except Exception as e:
            logger.error(f"Fout bij update definitie {definition_id}: {e}")
            return DefinitionResponse(
                definition=Definition(),
                success=False,
                message=f"Update mislukt: {str(e)}",
            )

    async def validate_and_save(self, definition: Definition) -> DefinitionResponse:
        """
        Valideer en sla een definitie op.

        Dit wordt gebruikt voor handmatig aangemaakte definities of
        definities die van externe bronnen komen.

        Args:
            definition: Te valideren en op te slaan definitie

        Returns:
            DefinitionResponse met resultaat en status
        """
        try:
            # Valideer definitie
            validation_result = self.validator.validate(definition)

            # Check kwaliteit
            if (
                validation_result.score < self.config.min_quality_score
                and not self.config.save_drafts
            ):
                return DefinitionResponse(
                    definition=definition,
                    validation=validation_result,
                    success=False,
                    message=f"Kwaliteitsscore te laag: {validation_result.score:.2f}",
                )

            # Voeg metadata toe
            if not definition.metadata:
                definition.metadata = {}

            definition.metadata["validation_score"] = validation_result.score
            definition.metadata["validated_at"] = datetime.now().isoformat()

            # Bepaal status op basis van score
            if validation_result.score >= 0.8:
                definition.metadata["status"] = "established"
            elif validation_result.score >= self.config.min_quality_score:
                definition.metadata["status"] = "review"
            else:
                definition.metadata["status"] = "draft"

            # Sla op in repository
            definition_id = self.repository.save(definition)
            definition.id = definition_id

            return DefinitionResponse(
                definition=definition,
                validation=validation_result,
                success=True,
                message="Definitie gevalideerd en opgeslagen",
            )

        except Exception as e:
            logger.error(f"Fout bij validate_and_save: {e}")
            return DefinitionResponse(
                definition=definition,
                success=False,
                message=f"Validatie/opslag mislukt: {str(e)}",
            )

    # Private helper methods

    async def _generate_definition(self, context: ProcessingContext) -> Definition:
        """Genereer definitie via generator service."""
        try:
            definition = await self.generator.generate(context.request)

            # Voeg request metadata toe
            if not definition.metadata:
                definition.metadata = {}

            definition.metadata["request_timestamp"] = context.start_time.isoformat()
            definition.metadata["orchestrator_version"] = "1.0"

            return definition

        except Exception as e:
            context.errors.append(f"Generatie fout: {str(e)}")
            raise

    async def _validate_definition(
        self, context: ProcessingContext
    ) -> ValidationResult:
        """Valideer definitie via validator service."""
        try:
            # Run validation in executor voor sync compatibility
            loop = asyncio.get_event_loop()
            validation_result = await loop.run_in_executor(
                None, self.validator.validate, context.definition
            )

            # Voeg validatie metadata toe
            context.definition.metadata["validation_completed"] = True
            context.definition.metadata["validation_score"] = validation_result.score

            return validation_result

        except Exception as e:
            context.errors.append(f"Validatie fout: {str(e)}")
            # Return basis validatie result bij fout
            return ValidationResult(
                is_valid=False, errors=[f"Validatie mislukt: {str(e)}"], score=0.0
            )

    async def _enrich_definition(self, context: ProcessingContext) -> None:
        """Verrijk definitie met extra informatie."""
        enrichment_tasks = []

        # Web lookup voor bronnen
        if self.config.enable_web_lookup and WEB_LOOKUP_AVAILABLE:
            enrichment_tasks.append(self._enrich_with_web_lookup(context))

        # Genereer voorbeelden
        if self.config.enable_examples and EXAMPLES_AVAILABLE:
            enrichment_tasks.append(self._enrich_with_examples(context))

        # AI enhancement
        enrichment_tasks.append(self._enrich_with_ai(context))

        # Voer verrijking uit (parallel of sequentieel)
        if self.config.parallel_enrichment and len(enrichment_tasks) > 1:
            results = await asyncio.gather(*enrichment_tasks, return_exceptions=True)
            # Log eventuele fouten maar ga door
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.warning(f"Verrijking taak {i} mislukt: {result}")
        else:
            for task in enrichment_tasks:
                try:
                    await task
                except Exception as e:
                    logger.warning(f"Verrijking taak mislukt: {e}")

        self._stats["enrichment_successes"] += 1

    async def _enrich_with_web_lookup(self, context: ProcessingContext) -> None:
        """Verrijk met web bronnen."""
        try:
            loop = asyncio.get_event_loop()
            bronnen = await loop.run_in_executor(
                None,
                zoek_bronnen_voor_begrip,
                context.definition.begrip,
                {"domein": [context.request.domein] if context.request.domein else []},
            )

            if bronnen:
                context.enrichment_data["web_bronnen"] = bronnen
                # Voeg eerste bron toe als referentie
                if not context.definition.bron and bronnen:
                    context.definition.bron = bronnen[0].get("titel", "Web bron")

        except Exception as e:
            logger.debug(f"Web lookup mislukt: {e}")

    async def _enrich_with_examples(self, context: ProcessingContext) -> None:
        """Verrijk met voorbeeldzinnen."""
        try:
            voorbeelden = await genereer_alle_voorbeelden_async(
                context.definition.begrip,
                context.definition.definitie,
                {"domein": [context.request.domein] if context.request.domein else []},
            )

            if voorbeelden:
                context.definition.voorbeelden = voorbeelden
                context.enrichment_data["voorbeelden_gegenereerd"] = len(voorbeelden)

        except Exception as e:
            logger.debug(f"Voorbeelden generatie mislukt: {e}")

    async def _enrich_with_ai(self, context: ProcessingContext) -> None:
        """Verrijk met AI enhancement."""
        try:
            enhanced = await self.generator.enhance(context.definition)

            # Merge enhancements
            if enhanced.synoniemen and not context.definition.synoniemen:
                context.definition.synoniemen = enhanced.synoniemen

            if (
                enhanced.gerelateerde_begrippen
                and not context.definition.gerelateerde_begrippen
            ):
                context.definition.gerelateerde_begrippen = (
                    enhanced.gerelateerde_begrippen
                )

            if enhanced.toelichting and not context.definition.toelichting:
                context.definition.toelichting = enhanced.toelichting

        except Exception as e:
            logger.debug(f"AI enhancement mislukt: {e}")

    async def _save_definition(self, context: ProcessingContext) -> None:
        """Sla definitie op in repository."""
        try:
            # Voeg finale metadata toe
            context.definition.metadata["processing_time"] = (
                datetime.now() - context.start_time
            ).total_seconds()

            if context.validation_result:
                context.definition.metadata["auto_saved"] = True
                context.definition.metadata["quality_score"] = (
                    context.validation_result.score
                )

            # Bepaal status
            if context.validation_result and context.validation_result.score >= 0.8:
                context.definition.metadata["status"] = "established"
            elif (
                context.validation_result
                and context.validation_result.score >= self.config.min_quality_score
            ):
                context.definition.metadata["status"] = "review"
            else:
                context.definition.metadata["status"] = "draft"

            # Sla op
            loop = asyncio.get_event_loop()
            definition_id = await loop.run_in_executor(
                None, self.repository.save, context.definition
            )

            context.definition.id = definition_id

        except Exception as e:
            context.errors.append(f"Opslag fout: {str(e)}")
            # Niet fataal - definitie is nog steeds bruikbaar
            logger.warning(f"Definitie opslag mislukt: {e}")

    def _create_failed_response(
        self, context: ProcessingContext, message: str
    ) -> DefinitionResponse:
        """Creëer een gefaalde response."""
        return DefinitionResponse(
            definition=context.definition or Definition(begrip=context.request.begrip),
            validation=context.validation_result,
            success=False,
            message=f"Proces mislukt bij {context.current_step.value}: {message}",
        )

    def _update_average_processing_time(self, new_time: float) -> None:
        """Update gemiddelde verwerkingstijd."""
        total = self._stats["successful_creations"]
        if total == 0:
            self._stats["average_processing_time"] = new_time
        else:
            current_avg = self._stats["average_processing_time"]
            self._stats["average_processing_time"] = (
                current_avg * (total - 1) + new_time
            ) / total

    # Statistics methods

    def get_stats(self) -> Dict[str, Any]:
        """Haal orchestrator statistieken op."""
        return self._stats.copy()

    def reset_stats(self) -> None:
        """Reset de statistieken."""
        self._stats = {
            "total_requests": 0,
            "successful_creations": 0,
            "failed_creations": 0,
            "average_processing_time": 0.0,
            "validation_failures": 0,
            "enrichment_successes": 0,
        }
