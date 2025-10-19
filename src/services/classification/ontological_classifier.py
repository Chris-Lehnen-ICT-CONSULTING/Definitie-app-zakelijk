"""
Ontological Classifier Service - Standalone Component

Classificeert juridische begrippen in ontologische niveaus (U/F/O)
VOOR definitie generatie, omdat niveau de prompt template bepaalt.

Architecture:
    - Standalone service, niet gekoppeld aan definition flow
    - First-class citizen in ServiceContainer
    - Herbruikbaar voor batch analyse, validatie, etc.

NOTE: Dit is een NIEUWE standalone classifier voor U/F/O classificatie.
      Dit is ANDERS dan de bestaande OntologyClassifierService (TYPE/EXEMPLAAR/PROCES/RESULTAAT).
"""

import logging
from dataclasses import dataclass
from enum import Enum

# Voorlopig gebruik maken van bestaande types, later mogelijk eigen implementatie
# FUTURE: Wanneer LevelClassifier beschikbaar is, vervang door:
#   from src.toetsregels.level_classifier import LevelClassifier, OntologicalLevel

logger = logging.getLogger(__name__)


# Temporary implementation - zal vervangen worden door echte LevelClassifier
class OntologicalLevel(Enum):
    """
    Ontologische niveaus voor juridische begrippen (U/F/O classificatie).

    Gebaseerd op Enterprise Ontology theorie:
    - UNIVERSEEL (U): Universele begrippen (concepten die overal gelden)
    - FUNCTIONEEL (F): Functionele begrippen (domein-specifiek maar org-onafhankelijk)
    - OPERATIONEEL (O): Operationele begrippen (organisatie-specifiek)
    """

    UNIVERSEEL = "U"
    FUNCTIONEEL = "F"
    OPERATIONEEL = "O"


class ClassificationConfidence(Enum):
    """Confidence level voor classificatie"""

    HIGH = "high"  # >= 0.80
    MEDIUM = "medium"  # >= 0.60
    LOW = "low"  # < 0.60


@dataclass
class ClassificationResult:
    """
    Resultaat van ontologische classificatie

    Attributes:
        level: Geclassificeerd niveau (U/F/O)
        confidence: Confidence score (0.0-1.0)
        confidence_level: HIGH/MEDIUM/LOW
        rationale: Menselijk leesbare uitleg waarom dit niveau
        scores: Dict met alle niveau scores {U: 0.8, F: 0.15, O: 0.05}
        metadata: Extra context (gebruikte prompts, timing, etc.)
    """

    level: OntologicalLevel
    confidence: float
    confidence_level: ClassificationConfidence
    rationale: str
    scores: dict[str, float]
    metadata: dict | None = None

    @property
    def is_reliable(self) -> bool:
        """Is classificatie betrouwbaar genoeg voor productie gebruik?"""
        return self.confidence_level in (
            ClassificationConfidence.HIGH,
            ClassificationConfidence.MEDIUM,
        )

    def to_string_level(self) -> str:
        """Converteer naar string voor GenerationRequest.ontologische_categorie"""
        return self.level.value


class OntologicalClassifier:
    """
    Standalone service voor ontologische classificatie van juridische begrippen.

    Workflow:
        1. UI roept classify() aan met begrip + context
        2. Service gebruikt LevelClassifier + AI prompt voor scores
        3. Retourneert ClassificationResult met niveau + rationale
        4. UI zet result.to_string_level() in GenerationRequest
        5. DefinitionOrchestrator gebruikt categorie voor prompt selection

    Usage:
        # Via DI container
        classifier = container.get_ontological_classifier()
        result = classifier.classify("Overeenkomst", org_context, jur_context)

        # Standalone (testing)
        classifier = OntologicalClassifier(ai_service)
        result = classifier.classify("Overeenkomst")
    """

    def __init__(self, ai_service):
        """
        Initialiseer classifier

        Args:
            ai_service: AIServiceV2 instance voor prompt-based scoring
        """
        self.ai_service = ai_service

        logger.info("OntologicalClassifier initialized (temporary implementation)")

    async def classify(
        self,
        begrip: str,
        organisatorische_context: str | None = None,
        juridische_context: str | None = None,
    ) -> ClassificationResult:
        """
        Classificeer begrip in ontologisch niveau (U/F/O)

        Args:
            begrip: Te classificeren begrip
            organisatorische_context: Optionele organisatie context
            juridische_context: Optionele juridische context

        Returns:
            ClassificationResult met niveau, confidence, rationale

        Raises:
            ValueError: Als begrip leeg is
            RuntimeError: Als classificatie faalt
        """
        if not begrip or not begrip.strip():
            msg = "Begrip mag niet leeg zijn"
            raise ValueError(msg)

        logger.info(f"Classifying '{begrip}'")

        try:
            # FUTURE: Replace with real LevelClassifier when available
            # Temporary implementation: use AI service directly for classification

            # Build prompt for U/F/O classification
            prompt = f"""Classificeer het volgende juridische begrip in een ontologisch niveau:

Begrip: {begrip}

Ontologische niveaus:
- U (Universeel): Universele begrippen die overal gelden (bijv. "Persoon", "Datum")
- F (Functioneel): Functionele begrippen specifiek voor juridisch domein maar organisatie-onafhankelijk (bijv. "Overeenkomst", "Rechtspersoon")
- O (Operationeel): Operationele begrippen die organisatie-specifiek zijn (bijv. "Aanvraag vergunning gemeente X")

Context:
{f"Organisatie: {organisatorische_context}" if organisatorische_context else ""}
{f"Juridisch: {juridische_context}" if juridische_context else ""}

Geef antwoord in JSON formaat:
{{
    "level": "U/F/O",
    "confidence": 0.0-1.0,
    "rationale": "Uitleg waarom dit niveau",
    "scores": {{"U": 0.1, "F": 0.8, "O": 0.1}}
}}
"""

            # Call AI service
            import json

            response = await self.ai_service.generate_text(prompt, temperature=0.3)

            # Parse response
            response_data = json.loads(response)

            # Map to OntologicalLevel enum
            level_map = {
                "U": OntologicalLevel.UNIVERSEEL,
                "F": OntologicalLevel.FUNCTIONEEL,
                "O": OntologicalLevel.OPERATIONEEL,
            }

            level = level_map[response_data["level"]]
            confidence = float(response_data["confidence"])
            confidence_level = self._determine_confidence_level(confidence)

            result = ClassificationResult(
                level=level,
                confidence=confidence,
                confidence_level=confidence_level,
                rationale=response_data["rationale"],
                scores=response_data["scores"],
                metadata={
                    "begrip": begrip,
                    "has_org_context": bool(organisatorische_context),
                    "has_jur_context": bool(juridische_context),
                },
            )

            logger.info(
                f"Classification complete: {begrip} → {result.level.value} "
                f"(confidence: {result.confidence:.2f}, {result.confidence_level.value})"
            )

            return result

        except Exception as e:
            logger.error(f"Classification failed for '{begrip}': {e}", exc_info=True)
            msg = f"Classificatie gefaald voor '{begrip}': {e}"
            raise RuntimeError(msg) from e

    async def classify_batch(
        self, begrippen: list[str], shared_context: tuple[str, str] | None = None
    ) -> dict[str, ClassificationResult]:
        """
        Classificeer meerdere begrippen in batch

        Nuttig voor:
            - Validatie van bestaande definities database
            - Analyse van juridische corpus
            - Bulk import van begrippen

        Args:
            begrippen: Lijst van begrippen
            shared_context: Optionele (org_context, jur_context) tuple

        Returns:
            Dict mapping begrip → ClassificationResult
        """
        logger.info(f"Batch classification started: {len(begrippen)} begrippen")

        org_ctx, jur_ctx = shared_context if shared_context else (None, None)

        results = {}
        for begrip in begrippen:
            try:
                results[begrip] = await self.classify(begrip, org_ctx, jur_ctx)
            except Exception as e:
                logger.warning(f"Batch item '{begrip}' failed: {e}")
                # Continue met volgende begrip

        logger.info(
            f"Batch classification complete: {len(results)}/{len(begrippen)} succeeded"
        )
        return results

    async def validate_existing_definition(
        self, begrip: str, claimed_level: str, definition_text: str
    ) -> tuple[bool, str | None]:
        """
        Valideer of bestaande definitie correct geclassificeerd is

        Args:
            begrip: Begrip naam
            claimed_level: Beweerd niveau ("U"/"F"/"O")
            definition_text: Definitie tekst voor context extractie

        Returns:
            (is_correct, mismatch_reason) tuple
            - (True, None) als classificatie correct is
            - (False, "reason") als mismatch detected
        """
        # Classificeer opnieuw
        result = await self.classify(begrip)

        actual_level = result.level.value

        if actual_level == claimed_level:
            return True, None

        reason = (
            f"Niveau mismatch: bestaand={claimed_level}, "
            f"herclassificatie={actual_level} "
            f"(confidence: {result.confidence:.2f}). "
            f"Rationale: {result.rationale}"
        )

        return False, reason

    @staticmethod
    def _determine_confidence_level(score: float) -> ClassificationConfidence:
        """Bepaal confidence level op basis van score"""
        if score >= 0.80:
            return ClassificationConfidence.HIGH
        if score >= 0.60:
            return ClassificationConfidence.MEDIUM
        return ClassificationConfidence.LOW
