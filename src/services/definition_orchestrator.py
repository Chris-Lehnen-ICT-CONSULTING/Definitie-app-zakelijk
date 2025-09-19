"""
DefinitionOrchestrator service implementatie.

Deze service orkestreert het complete proces van definitie creatie,
validatie en opslag door de verschillende services te coördineren.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from services.interfaces import (
    CleaningServiceInterface,
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
        from services.interfaces import LookupRequest
        from services.modern_web_lookup_service import ModernWebLookupService

        service = ModernWebLookupService()
        request = LookupRequest(term=term, max_results=5)
        results = await service.lookup(request)

        # Extract sources from results
        sources = []
        for result in results:
            sources.append(
                {
                    "name": result.source.name,
                    "url": result.source.url,
                    "confidence": result.source.confidence,
                }
            )
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
    # enable_web_lookup removed - web lookup runs always when service available
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
    definition: Definition | None = None
    validation_result: ValidationResult | None = None
    enrichment_data: dict[str, Any] = field(default_factory=dict)
    current_step: ProcessingStep = ProcessingStep.GENERATION
    start_time: datetime = field(default_factory=lambda: datetime.now(UTC))
    errors: list[str] = field(default_factory=list)


class DefinitionOrchestrator(
    DefinitionOrchestratorInterface, DefinitionGeneratorInterface
):
    """
    Service voor het orkestreren van definitie operaties.

    Deze implementatie coördineert de verschillende services om een
    complete definitie workflow te bieden: generatie, validatie,
    verrijking en opslag.
    """

    def __init__(
        self,
        validator: DefinitionValidatorInterface,
        repository: DefinitionRepositoryInterface,
        cleaning_service: CleaningServiceInterface | None = None,
        config: OrchestratorConfig | None = None,
    ):
        """
        Initialiseer de DefinitionOrchestrator.

        Args:
            validator: Service voor definitie validatie
            repository: Service voor definitie opslag
            cleaning_service: Service voor definitie opschoning
            config: Optionele configuratie
        """
        self.validator = validator
        self.repository = repository
        self.cleaning_service = cleaning_service
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
                msg = "Generatie mislukt: geen definitie ontvangen"
                raise ValueError(msg)

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
            processing_time = (datetime.now(UTC) - context.start_time).total_seconds()
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
        self, definition_id: int, updates: dict[str, Any]
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
            existing.updated_at = datetime.now(UTC)

            # Valideer geüpdatete definitie
            validation_result = None
            if self.config.enable_validation:
                validation_result = self.validator.validate(existing)

                # Alleen validatie voor gewijzigde velden
                if (
                    "definitie" in updates or "begrip" in updates
                ) and validation_result.score < self.config.min_quality_score:
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
                message=f"Update mislukt: {e!s}",
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
            definition.metadata["validated_at"] = datetime.now(UTC).isoformat()

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
                message=f"Validatie/opslag mislukt: {e!s}",
            )

    # Private helper methods

    async def generate(self, request: GenerationRequest) -> Definition:
        """
        Implementeer DefinitionGeneratorInterface.generate().

        Dit is de hoofdmethode voor definitie generatie.
        """
        # Gebruik create_definition voor de complete workflow
        response = await self.create_definition(request)
        if response.success and response.definition:
            return response.definition
        # Als create_definition faalt, maak een basis definitie
        return Definition(
            begrip=request.begrip,
            definitie=f"Fout bij generatie: {response.message}",
            context=request.context,
            # EPIC-010: domein field verwijderd
        )

    async def enhance(self, definition: Definition) -> Definition:
        """
        Implementeer DefinitionGeneratorInterface.enhance().

        Verbeter een bestaande definitie.
        """
        # Voor nu, return de originele definitie (enhancement volgt via US-066)
        return definition

    async def _generate_definition(self, context: ProcessingContext) -> Definition:
        """Genereer basis definitie met echte GPT integration."""
        prompt = "Geen prompt beschikbaar"  # Default waarde voor error handling

        try:
            # Gebruik nieuwe Clean Services UnifiedPromptBuilder met categorie ondersteuning
            from services.definition_generator_config import UnifiedGeneratorConfig
            from services.definition_generator_context import EnrichedContext
            from services.definition_generator_prompts import UnifiedPromptBuilder

            # Maak config voor de nieuwe prompt builder
            config = UnifiedGeneratorConfig()

            # Converteer GenerationRequest naar EnrichedContext met ontologische categorie
            base_context = {
                "organisatorisch": (
                    [context.request.context] if context.request.context else []
                ),
                "juridisch": [],  # EPIC-010: domein field verwijderd - gebruik juridische_context
                "wettelijk": [],
                # ontologische_categorie verwijderd uit base_context om string->char array bug te fixen
            }

            # US-043: Legacy code - will be replaced by V2 orchestrator
            # This direct EnrichedContext creation is allowed only in legacy code
            enriched_context = EnrichedContext(
                base_context=base_context,
                sources=[],  # Geen externe bronnen voor nu
                expanded_terms={},  # Geen afkortingen om te expanderen
                confidence_scores={},  # Geen confidence scores zonder bronnen
                metadata={
                    "ontologische_categorie": context.request.ontologische_categorie,
                    "extra_instructies": context.request.extra_instructies,
                },
            )

            # Gebruik UnifiedPromptBuilder met categorie-ondersteuning
            prompt_builder = UnifiedPromptBuilder(config)
            prompt = prompt_builder.build_prompt(
                context.request.begrip, enriched_context
            )

            if context.request.ontologische_categorie:
                logger.info(
                    f"Prompt gebouwd met ontologische categorie: {context.request.ontologische_categorie}"
                )
            else:
                logger.info("Prompt gebouwd zonder specifieke categorie")

            # Stuur naar GPT via extracted AI service method
            gpt_response = await self._ai_service_call(prompt)

            # Maak definitie met GPT response
            definition = Definition(
                begrip=context.request.begrip,
                definitie=gpt_response.strip(),
                context=context.request.context,
                # EPIC-010: domein field verwijderd
            )

            logger.info(f"GPT definitie gegenereerd: {gpt_response[:50]}...")

        except Exception as e:
            logger.error(f"GPT generatie fout: {e}")
            # Fallback naar basis definitie bij fout
            definition = Definition(
                begrip=context.request.begrip,
                definitie=f"Fout bij GPT generatie: {e!s}",
                context=context.request.context,
                # EPIC-010: domein field verwijderd
            )

        # Voeg request metadata toe (buiten try/except block)
        if not definition.metadata:
            definition.metadata = {}

        definition.metadata["request_timestamp"] = context.start_time.isoformat()
        definition.metadata["orchestrator_version"] = "1.0"
        definition.metadata["prompt_template"] = prompt  # Voor debug sectie

        # Pas opschoning toe (VOOR validatie - deel van GVI workflow)
        if self.cleaning_service and definition.definitie:
            logger.info(f"Cleaning definitie voor begrip: {definition.begrip}")
            cleaning_result = self.cleaning_service.clean_definition(definition)

            # Update definitie met opgeschoond resultaat
            definition.definitie = cleaning_result.cleaned_text

            # Voeg cleaning metadata toe
            definition.metadata.update(
                {
                    "cleaning_applied": cleaning_result.was_cleaned,
                    "cleaning_rules": cleaning_result.applied_rules,
                    "cleaning_improvements": cleaning_result.improvements,
                }
            )

            # Sla ALTIJD de originele definitie op, ook als er geen opschoning was
            definition.metadata["definitie_origineel"] = cleaning_result.original_text

            if cleaning_result.was_cleaned:
                logger.info(
                    f"Definitie opgeschoond: {len(cleaning_result.applied_rules)} regels toegepast"
                )
            else:
                logger.debug("Geen opschoning nodig voor definitie")

        return definition

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
            context.errors.append(f"Validatie fout: {e!s}")
            # Return basis validatie result bij fout
            return ValidationResult(
                is_valid=False, errors=[f"Validatie mislukt: {e!s}"], score=0.0
            )

    async def _enrich_definition(self, context: ProcessingContext) -> None:
        """Verrijk definitie met extra informatie."""
        enrichment_tasks = []

        # Web lookup voor bronnen (always when available, no flag)
        if WEB_LOOKUP_AVAILABLE:
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
                {},  # EPIC-010: domein field verwijderd
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
                {},  # EPIC-010: domein field verwijderd
            )

            if voorbeelden:
                context.definition.voorbeelden = voorbeelden
                context.enrichment_data["voorbeelden_gegenereerd"] = len(voorbeelden)

        except Exception as e:
            logger.debug(f"Voorbeelden generatie mislukt: {e}")

    async def _ai_service_call(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.01,
        max_tokens: int = 300,
    ) -> str:
        """
        Extracted AI service call - first step toward IntelligentAIService.

        This method isolates the AI generation logic to prepare for eventual
        extraction into a dedicated AI service following SOA principles.

        Args:
            prompt: The prompt to send to AI
            model: AI model to use (default: gpt-5)
            temperature: Randomness level (default: 0.01 for consistency)
            max_tokens: Maximum tokens in response

        Returns:
            AI-generated response text
        """
        try:
            from services.ai_service import get_ai_service

            # Use central config for defaults
            if model is None:
                model = "gpt-4o"  # Default model
            if temperature is None:
                temperature = 0.7  # Default temperature

            logger.debug(
                f"AI service call: model={model}, temp={temperature}, max_tokens={max_tokens}"
            )

            ai_service = get_ai_service()
            response = ai_service.generate_definition(
                prompt=prompt,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            logger.info(f"AI response generated: {len(response)} characters")
            return response.strip()

        except Exception as e:
            logger.error(f"AI service call failed: {e}")
            # Return error message that can be processed by caller
            return f"AI generatie fout: {e!s}"

    async def _enrich_with_ai(self, context: ProcessingContext) -> None:
        """Verrijk met AI enhancement."""
        try:
            # For now, skip AI enhancement (US-066)
            logger.debug(
                "AI enhancement temporarily disabled - orchestrator is the generator"
            )

        except Exception as e:
            logger.debug(f"AI enhancement mislukt: {e}")

    async def _save_definition(self, context: ProcessingContext) -> None:
        """Sla definitie op in repository."""
        try:
            # Voeg finale metadata toe
            context.definition.metadata["processing_time"] = (
                datetime.now(UTC) - context.start_time
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
            context.errors.append(f"Opslag fout: {e!s}")
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

    def get_stats(self) -> dict[str, Any]:
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
