"""
VOORBEELD: ServiceAdapter met Ontological Classifier

ServiceAdapter is een optionele facade die:
    1. Classificatie + Generatie combineert in één call (convenience)
    2. Backwards compatibility biedt voor bestaande code
    3. Standaard flow implementeert (classificeer → genereer)

BELANGRIJK:
    - Classifier is ALTIJD standalone beschikbaar via container
    - ServiceAdapter is OPTIONEEL, voor gemak
    - UI kan kiezen: direct classifier gebruiken OF via adapter
"""

import logging

from services.classification import ClassificationResult, OntologicalClassifier
from services.orchestrators.definition_orchestrator_v2 import (
    DefinitionOrchestratorV2,
    GenerationRequest,
    GenerationResponse,
)

logger = logging.getLogger(__name__)


class ServiceAdapter:
    """
    Optionele facade die classificatie + generatie combineert.

    Twee modi:
        1. Auto-classify: Adapter doet classificatie automatisch
        2. Manual: Caller doet classificatie zelf

    Usage:
        # Modus 1: Auto-classify (gemak)
        adapter = ServiceAdapter(classifier, orchestrator)
        response = await adapter.generate_with_auto_classification(
            begrip="Overeenkomst",
            org_context="...",
            jur_context="..."
        )

        # Modus 2: Manual (meer controle)
        classification = classifier.classify(begrip, org_ctx, jur_ctx)
        # ... toon classification aan gebruiker, laat override toe
        response = await adapter.generate_with_classification(
            classification=classification,
            begrip="Overeenkomst",
            # ... andere inputs
        )
    """

    def __init__(
        self, classifier: OntologicalClassifier, orchestrator: DefinitionOrchestratorV2
    ):
        """
        Initialiseer adapter met dependencies.

        Args:
            classifier: Standalone ontological classifier
            orchestrator: Definition orchestrator voor generatie
        """
        self.classifier = classifier
        self.orchestrator = orchestrator

        logger.info("ServiceAdapter initialized with classifier + orchestrator")

    async def generate_with_auto_classification(
        self,
        begrip: str,
        organisatorische_context: str | None = None,
        juridische_context: str | None = None,
        wettelijke_context: str | None = None,
        voorbeelden: list[str] | None = None,
        document_context: dict | None = None,
    ) -> tuple[GenerationResponse, ClassificationResult]:
        """
        Genereer definitie met automatische classificatie.

        Flow:
            1. Classificeer begrip (intern)
            2. Genereer definitie met geclassificeerd niveau
            3. Retourneer beide resultaten

        Args:
            begrip: Te definiëren begrip
            organisatorische_context: Organisatie context
            juridische_context: Juridische context
            wettelijke_context: Wettelijke context
            voorbeelden: Voorbeeld zinnen
            document_context: Document metadata

        Returns:
            (GenerationResponse, ClassificationResult) tuple

        Raises:
            ValueError: Als begrip leeg is
            RuntimeError: Als classificatie of generatie faalt
        """
        if not begrip or not begrip.strip():
            raise ValueError("Begrip mag niet leeg zijn")

        logger.info(f"Auto-classify + generate for '{begrip}'")

        # Stap 1: Classificeer
        try:
            classification = self.classifier.classify(
                begrip=begrip,
                organisatorische_context=organisatorische_context,
                juridische_context=juridische_context,
            )

            logger.info(
                f"Classification: {begrip} → {classification.level.value} "
                f"(confidence: {classification.confidence:.2f})"
            )

        except Exception as e:
            logger.error(f"Classification failed: {e}", exc_info=True)
            raise RuntimeError(f"Classificatie gefaald: {e}") from e

        # Stap 2: Genereer met geclassificeerd niveau
        try:
            response = await self.generate_with_classification(
                classification=classification,
                begrip=begrip,
                organisatorische_context=organisatorische_context,
                juridische_context=juridische_context,
                wettelijke_context=wettelijke_context,
                voorbeelden=voorbeelden,
                document_context=document_context,
            )

            return response, classification

        except Exception as e:
            logger.error(f"Generation failed after classification: {e}", exc_info=True)
            raise RuntimeError(f"Generatie gefaald: {e}") from e

    async def generate_with_classification(
        self,
        classification: ClassificationResult,
        begrip: str,
        organisatorische_context: str | None = None,
        juridische_context: str | None = None,
        wettelijke_context: str | None = None,
        voorbeelden: list[str] | None = None,
        document_context: dict | None = None,
    ) -> GenerationResponse:
        """
        Genereer definitie met bestaande classificatie.

        Gebruik deze methode als je:
            - Classificatie al hebt gedaan
            - Classificatie aan gebruiker hebt getoond
            - Gebruiker override heeft toegestaan

        Args:
            classification: Bestaande ClassificationResult
            begrip: Te definiëren begrip
            organisatorische_context: Organisatie context
            juridische_context: Juridische context
            wettelijke_context: Wettelijke context
            voorbeelden: Voorbeeld zinnen
            document_context: Document metadata

        Returns:
            GenerationResponse met definitie + validatie

        Raises:
            RuntimeError: Als generatie faalt
        """
        logger.info(
            f"Generate with pre-classification: {begrip} @ {classification.level.value}"
        )

        # Bouw GenerationRequest met geclassificeerd niveau
        request = GenerationRequest(
            begrip=begrip,
            ontologische_categorie=classification.to_string_level(),  # ← Gebruik classificatie
            organisatorische_context=organisatorische_context or "",
            juridische_context=juridische_context or "",
            wettelijke_context=wettelijke_context or "",
            voorbeelden=voorbeelden or [],
            document_context=document_context,
        )

        # Delegeer naar orchestrator
        try:
            response = await self.orchestrator.create_definition(request)

            logger.info(
                f"Generation complete: success={response.success}, "
                f"validation_passed={response.validation_passed}"
            )

            return response

        except Exception as e:
            logger.error(f"Generation failed: {e}", exc_info=True)
            raise RuntimeError(f"Generatie gefaald: {e}") from e

    def classify_only(
        self,
        begrip: str,
        organisatorische_context: str | None = None,
        juridische_context: str | None = None,
    ) -> ClassificationResult:
        """
        Classificeer begrip zonder definitie te genereren.

        Nuttig voor:
            - Preview classificatie in UI
            - Batch classificatie
            - Validatie van bestaande definities

        Args:
            begrip: Te classificeren begrip
            organisatorische_context: Optionele context
            juridische_context: Optionele context

        Returns:
            ClassificationResult
        """
        return self.classifier.classify(
            begrip=begrip,
            organisatorische_context=organisatorische_context,
            juridische_context=juridische_context,
        )


# ===== USAGE EXAMPLES =====


async def example_auto_classification():
    """
    Voorbeeld: Auto-classificatie (gemakkelijkste weg)
    """
    from services.container import ServiceContainer

    # Setup
    container = ServiceContainer()
    classifier = container.ontological_classifier()
    orchestrator = container.orchestrator()
    adapter = ServiceAdapter(classifier, orchestrator)

    # Generate met auto-classificatie
    response, classification = await adapter.generate_with_auto_classification(
        begrip="Overeenkomst",
        organisatorische_context="Gemeente context",
        juridische_context="Burgerlijk wetboek",
    )

    print(
        f"Classification: {classification.level.value} (confidence: {classification.confidence:.1%})"
    )
    print(f"Definition: {response.definition_text}")
    print(f"Validation passed: {response.validation_passed}")


async def example_manual_classification():
    """
    Voorbeeld: Handmatige classificatie (meer controle)

    Flow:
        1. Classificeer
        2. Toon aan gebruiker
        3. Laat gebruiker override toe
        4. Genereer met (mogelijk gewijzigde) classificatie
    """
    from services.container import ServiceContainer

    # Setup
    container = ServiceContainer()
    classifier = container.ontological_classifier()
    orchestrator = container.orchestrator()
    adapter = ServiceAdapter(classifier, orchestrator)

    # Stap 1: Classificeer
    classification = adapter.classify_only(
        begrip="Overeenkomst", organisatorische_context="Gemeente context"
    )

    # Stap 2: Toon aan gebruiker
    print(f"Geclassificeerd als: {classification.level.value}")
    print(f"Confidence: {classification.confidence:.1%}")
    print(f"Rationale: {classification.rationale}")

    # Stap 3: Laat gebruiker override toe (in UI)
    user_wants_override = False  # Uit UI checkbox
    if user_wants_override:
        # Gebruiker kiest handmatig niveau
        from src.toetsregels.level_classifier import OntologicalLevel

        classification.level = OntologicalLevel.FUNCTIONEEL

    # Stap 4: Genereer met (mogelijk gewijzigde) classificatie
    response = await adapter.generate_with_classification(
        classification=classification,
        begrip="Overeenkomst",
        organisatorische_context="Gemeente context",
        juridische_context="Burgerlijk wetboek",
    )

    print(f"Definition generated: {response.success}")


def example_batch_validation():
    """
    Voorbeeld: Valideer bestaande definities in database

    Check of bestaande definities correct geclassificeerd zijn
    """
    from services.container import ServiceContainer

    # Setup
    container = ServiceContainer()
    classifier = container.ontological_classifier()

    # Simuleer bestaande definities
    existing_definitions = [
        {"begrip": "Overeenkomst", "claimed_level": "F"},
        {"begrip": "Perceel", "claimed_level": "O"},
        {"begrip": "Rechtspersoon", "claimed_level": "U"},
    ]

    # Valideer elke definitie
    mismatches = []
    for definition in existing_definitions:
        is_correct, reason = classifier.validate_existing_definition(
            begrip=definition["begrip"],
            claimed_level=definition["claimed_level"],
            definition_text="",  # Zou uit DB komen
        )

        if not is_correct:
            mismatches.append(
                {
                    "begrip": definition["begrip"],
                    "claimed": definition["claimed_level"],
                    "reason": reason,
                }
            )

    # Rapporteer mismatches
    if mismatches:
        print(f"Found {len(mismatches)} classification mismatches:")
        for mismatch in mismatches:
            print(f"  - {mismatch['begrip']}: {mismatch['reason']}")
    else:
        print("All definitions correctly classified!")


# ===== DI CONTAINER INTEGRATION =====


def add_service_adapter_to_container():
    """
    Voorbeeld: Voeg ServiceAdapter toe aan DI container

    Dit zou in src/services/container.py komen:
    """

    # In ServiceContainer class:
    """
    def service_adapter(self):
        '''
        Get or create ServiceAdapter instance (optional facade).

        ServiceAdapter combineert classificatie + generatie voor convenience.
        NIET verplicht - UI kan ook direct classifier + orchestrator gebruiken.

        Returns:
            Singleton instance van ServiceAdapter
        '''
        if "service_adapter" not in self._instances:
            classifier = self.ontological_classifier()
            orchestrator = self.orchestrator()

            self._instances["service_adapter"] = ServiceAdapter(
                classifier=classifier,
                orchestrator=orchestrator
            )

            logger.info("ServiceAdapter initialized (optional facade)")

        return self._instances["service_adapter"]
    """


# ===== CLI EXAMPLE (Herbruikbaarheid buiten UI) =====


async def cli_classification_tool():
    """
    CLI tool voor standalone classificatie

    Gebruik:
        python -m examples.cli_classifier "Overeenkomst" --org-context "..."

    Dit demonstreert herbruikbaarheid buiten definitie generatie flow
    """
    import argparse

    parser = argparse.ArgumentParser(description="Classificeer juridisch begrip")
    parser.add_argument("begrip", help="Begrip om te classificeren")
    parser.add_argument("--org-context", help="Organisatorische context")
    parser.add_argument("--jur-context", help="Juridische context")
    parser.add_argument("--batch", help="CSV bestand met begrippen")

    args = parser.parse_args()

    # Setup classifier
    from services.container import ServiceContainer

    container = ServiceContainer()
    classifier = container.ontological_classifier()

    if args.batch:
        # Batch mode
        import pandas as pd

        df = pd.read_csv(args.batch)
        results = classifier.classify_batch(df["begrip"].tolist())

        for begrip, result in results.items():
            print(f"{begrip}: {result.level.value} ({result.confidence:.1%})")

    else:
        # Single mode
        result = classifier.classify(
            begrip=args.begrip,
            organisatorische_context=args.org_context,
            juridische_context=args.jur_context,
        )

        print(f"Begrip: {args.begrip}")
        print(f"Niveau: {result.level.value}")
        print(f"Confidence: {result.confidence:.1%} ({result.confidence_level.value})")
        print(f"Rationale: {result.rationale}")
        print("\nScores:")
        for level, score in result.scores.items():
            print(f"  {level}: {score:.1%}")
