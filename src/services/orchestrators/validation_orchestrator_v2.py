"""ValidationOrchestratorV2 — sequentiële orchestrator voor validatie.

Deze orchestrator levert een dunne, async-first laag bovenop de
`ValidationServiceInterface`, met optionele pre-cleaning. Batchverwerking
gebeurt sequentieel; parallelisme volgt in een latere iteratie.
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import Iterable

from services.interfaces import (
    CleaningServiceInterface,
    Definition,
    ValidationServiceInterface,
)
from services.validation.interfaces import (
    ValidationContext,
    ValidationOrchestratorInterface,
    ValidationRequest,
    ValidationResult,
)
from services.validation.mappers import (
    create_degraded_result,
    ensure_schema_compliance,
)

logger = logging.getLogger(__name__)


class ValidationOrchestratorV2(ValidationOrchestratorInterface):
    """Orchestrator voor validatie (V2).

    Afhankelijkheden worden via de constructor geïnjecteerd. De orchestrator
    zelf bevat geen businessregels; die leven in de onderliggende service/validator.

    Story 2.2: Core Implementation
    - Concrete implementatie van ValidationOrchestratorInterface
    - Dunne orchestration laag bovenop bestaande services
    - Sequentiële batch processing (parallelisme in latere story)
    - Optionele pre-cleaning support
    """

    def __init__(
        self,
        validation_service: ValidationServiceInterface,
        cleaning_service: CleaningServiceInterface | None = None,
    ) -> None:
        if validation_service is None:
            raise ValueError("validation_service is vereist")
        self.validation_service = validation_service
        self.cleaning_service = cleaning_service

    async def validate_text(
        self,
        begrip: str,
        text: str,
        ontologische_categorie: str | None = None,
        context: ValidationContext | None = None,
    ) -> ValidationResult:
        """Valideer losse tekst met optionele pre-cleaning.

        Args:
            begrip: Het begrip waarvoor de tekst wordt gevalideerd
            text: Te valideren tekst (mag leeg zijn)
            ontologische_categorie: Optionele categorie voor contextuele regels
            context: Optionele validatiecontext

        Returns:
            ValidationResult: Schema-conform resultaat
        """
        # Extract correlation ID from context
        correlation_id = (
            str(context.correlation_id)
            if context and context.correlation_id
            else str(uuid.uuid4())
        )

        try:
            cleaned_text = text
            if self.cleaning_service is not None:
                cleaning = await self.cleaning_service.clean_text(text, begrip)
                cleaned_text = cleaning.cleaned_text if cleaning else text

            # Build context dict with all relevant fields
            context_dict = None
            if context:
                context_dict = {}
                if context.profile:
                    context_dict["profile"] = context.profile
                if context.correlation_id:
                    context_dict["correlation_id"] = str(context.correlation_id)
                if context.locale:
                    context_dict["locale"] = context.locale
                if context.feature_flags:
                    context_dict["feature_flags"] = dict(context.feature_flags)

            # Call underlying service
            result = await self.validation_service.validate_definition(
                begrip=begrip,
                text=cleaned_text,
                ontologische_categorie=ontologische_categorie,
                context=context_dict,
            )

            # Ensure result is schema-compliant
            return ensure_schema_compliance(result, correlation_id)

        except Exception as e:
            logger.error(
                f"Validation failed for begrip='{begrip}', correlation_id='{correlation_id}': {e}"
            )
            return create_degraded_result(
                error=str(e), correlation_id=correlation_id, begrip=begrip
            )

    async def validate_definition(
        self,
        definition: Definition,
        context: ValidationContext | None = None,
    ) -> ValidationResult:
        """Valideer een volledig Definition-object met optionele pre-cleaning.

        Args:
            definition: Te valideren Definition object
            context: Optionele validatiecontext

        Returns:
            ValidationResult: Schema-conform resultaat met detailed_scores
        """
        # Extract correlation ID from context
        correlation_id = (
            str(context.correlation_id)
            if context and context.correlation_id
            else str(uuid.uuid4())
        )

        try:
            text = definition.definitie
            if self.cleaning_service is not None:
                cleaned = await self.cleaning_service.clean_definition(definition)
                text = cleaned.cleaned_text if cleaned else definition.definitie

            # Build context dict with all relevant fields
            context_dict = None
            if context:
                context_dict = {}
                if context.profile:
                    context_dict["profile"] = context.profile
                if context.correlation_id:
                    context_dict["correlation_id"] = str(context.correlation_id)
                if context.locale:
                    context_dict["locale"] = context.locale
                if context.feature_flags:
                    context_dict["feature_flags"] = dict(context.feature_flags)

            # Call underlying service
            result = await self.validation_service.validate_definition(
                begrip=definition.begrip,
                text=text,
                ontologische_categorie=definition.ontologische_categorie,
                context=context_dict,
            )

            # Ensure result is schema-compliant
            return ensure_schema_compliance(result, correlation_id)

        except Exception as e:
            logger.error(
                f"Validation failed for definition begrip='{definition.begrip}', correlation_id='{correlation_id}': {e}"
            )
            return create_degraded_result(
                error=str(e), correlation_id=correlation_id, begrip=definition.begrip
            )

    async def batch_validate(
        self, items: Iterable[ValidationRequest], max_concurrency: int = 1
    ) -> list[ValidationResult]:
        """Valideer meerdere items sequentieel.

        Args:
            items: Itereerbare van ValidationRequest objects
            max_concurrency: Maximum parallelle validaties (genegeerd in v2.2)

        Returns:
            List[ValidationResult]: Resultaten in zelfde volgorde als input

        Note:
            - max_concurrency wordt genegeerd in deze versie (Story 2.2)
            - Parallelisme wordt toegevoegd in Story 2.3
            - Individuele failures resulteren in degraded results, niet batch failure
        """
        results: list[ValidationResult] = []
        for item in items:
            results.append(
                await self.validate_text(
                    begrip=item.begrip,
                    text=item.text,
                    ontologische_categorie=item.ontologische_categorie,
                    context=item.context,
                )
            )
        return results
