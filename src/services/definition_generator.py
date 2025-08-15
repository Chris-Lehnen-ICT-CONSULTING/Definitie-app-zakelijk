"""
DefinitionGenerator service implementatie.

Deze service is verantwoordelijk voor het genereren van definities
met behulp van AI (OpenAI GPT-4).
"""

import asyncio
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from opschoning.opschoning import opschonen

# Legacy imports voor backward compatibility
from prompt_builder.prompt_builder import (
    PromptBouwer,
    PromptConfiguratie,
    stuur_prompt_naar_gpt,
)
from services.interfaces import (
    Definition,
    DefinitionGeneratorInterface,
    GenerationRequest,
)
from utils.exceptions import handle_api_error

# Monitoring (optioneel)
try:
    from monitoring.api_monitor import record_api_call

    MONITORING_AVAILABLE = True
except ImportError:
    MONITORING_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class GeneratorConfig:
    """Configuratie voor de DefinitionGenerator."""

    model: str = "gpt-4"
    temperature: float = (
        0.0  # Changed from 0.4 to 0.0 for consistency (MASTER-TODO requirement)
    )
    max_tokens: int = 500
    enable_monitoring: bool = True
    enable_cleaning: bool = True
    enable_ontology: bool = True
    retry_count: int = 3
    timeout: float = 30.0


class DefinitionGenerator(DefinitionGeneratorInterface):
    """
    Service voor het genereren van definities met AI.

    Deze implementatie extraheert de generatie logica uit de
    UnifiedDefinitionService en maakt het herbruikbaar als een
    focused service.
    """

    def __init__(self, config: Optional[GeneratorConfig] = None):
        """
        Initialiseer de DefinitionGenerator.

        Args:
            config: Optionele configuratie, gebruikt defaults indien niet opgegeven
        """
        self.config = config or GeneratorConfig()
        # PromptBouwer wordt per request gemaakt met specifieke configuratie
        # Disable monitoring for now due to signature issues
        self.config.enable_monitoring = False
        self._stats = {
            "total_generations": 0,
            "successful_generations": 0,
            "failed_generations": 0,
            "total_tokens_used": 0,
        }
        logger.info("DefinitionGenerator geïnitialiseerd")

    async def generate(self, request: GenerationRequest) -> Definition:
        """
        Genereer een nieuwe definitie op basis van het request.

        Args:
            request: GenerationRequest met begrip en context

        Returns:
            Definition object met gegenereerde content

        Raises:
            APIError: Bij problemen met de AI API
            ValueError: Bij ongeldige input
        """
        if not request.begrip:
            raise ValueError("Begrip is verplicht voor definitie generatie")

        self._stats["total_generations"] += 1

        try:
            # Bepaal ontologische categorie indien ingeschakeld
            categorie = None
            categorie_info = {}

            if self.config.enable_ontology:
                try:
                    from ontologie.ontological_analyzer import OntologischeAnalyzer

                    analyzer = OntologischeAnalyzer()

                    categorie_enum, analyse_resultaat = (
                        await analyzer.bepaal_ontologische_categorie(
                            request.begrip, request.context or "", request.domein or ""
                        )
                    )

                    categorie = categorie_enum.value
                    categorie_info = {
                        "categorie_reasoning": analyse_resultaat.get("reasoning", ""),
                        "categorie_scores": analyse_resultaat.get(
                            "categorie_resultaat", {}
                        ).get("test_scores", {}),
                    }
                    logger.info(f"Ontologische categorie bepaald: {categorie}")

                except Exception as e:
                    logger.warning(
                        f"Ontologische analyse mislukt, gebruik fallback: {e}"
                    )
                    # Fallback naar simpele pattern matching
                    categorie = self._simple_category_detection(request.begrip)
            else:
                # Gebruik simpele detection als ontologie uit staat
                categorie = self._simple_category_detection(request.begrip)

            # Genereer de definitie
            origineel, gecorrigeerd, marker = await self._generate_base_definition(
                request.begrip, self._build_context_dict(request)
            )

            # Maak Definition object
            definition = Definition(
                begrip=request.begrip,
                definitie=gecorrigeerd,
                context=request.context,
                domein=request.domein,
                categorie=categorie,
                bron="AI-gegenereerd (GPT-4)",
                metadata={
                    "origineel": origineel,
                    "marker": marker,
                    "model": self.config.model,
                    "temperature": self.config.temperature,
                    "organisatie": request.organisatie,
                    **categorie_info,  # Voeg categorie info toe
                },
            )

            self._stats["successful_generations"] += 1

            # Monitoring indien beschikbaar
            if MONITORING_AVAILABLE and self.config.enable_monitoring:
                record_api_call(
                    "generation",
                    {"begrip": request.begrip, "model": self.config.model},
                    "success",
                )

            return definition

        except Exception as e:
            self._stats["failed_generations"] += 1
            logger.error(f"Definitie generatie mislukt voor '{request.begrip}': {e}")

            if MONITORING_AVAILABLE and self.config.enable_monitoring:
                record_api_call(
                    "generation", {"begrip": request.begrip, "error": str(e)}, "failure"
                )

            raise

    async def enhance(self, definition: Definition) -> Definition:
        """
        Verbeter een bestaande definitie met extra informatie.

        Dit kan gebruikt worden om bijvoorbeeld synoniemen, gerelateerde
        begrippen of extra toelichting toe te voegen.

        Args:
            definition: Bestaande definitie om te verbeteren

        Returns:
            Verbeterde definitie
        """
        # Bouw een enhancement prompt
        enhancement_prompt = self._build_enhancement_prompt(definition)

        try:
            # Gebruik executor voor sync functie
            loop = asyncio.get_event_loop()
            enhanced_text = await loop.run_in_executor(
                None,
                stuur_prompt_naar_gpt,
                enhancement_prompt,
                self.config.model,
                0.5,  # Iets hogere temperature voor creativiteit
                300,  # Minder tokens nodig voor enhancement
            )

            # Parse de enhancement response
            enhancements = self._parse_enhancement_response(enhanced_text)

            # Update de definitie met enhancements
            if enhancements.get("toelichting"):
                definition.toelichting = enhancements["toelichting"]

            if enhancements.get("synoniemen"):
                definition.synoniemen = enhancements["synoniemen"]

            if enhancements.get("gerelateerde_begrippen"):
                definition.gerelateerde_begrippen = enhancements[
                    "gerelateerde_begrippen"
                ]

            return definition

        except Exception as e:
            logger.warning(f"Enhancement mislukt voor '{definition.begrip}': {e}")
            # Return originele definitie bij fout
            return definition

    # Private helper methods

    async def _generate_base_definition(
        self, begrip: str, context_dict: Dict[str, List[str]]
    ) -> Tuple[str, str, str]:
        """
        Genereer basis definitie met async wrapper.

        Returns:
            Tuple van (origineel, gecorrigeerd, marker)
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self._generate_base_definition_sync, begrip, context_dict
        )

    @handle_api_error
    def _generate_base_definition_sync(
        self, begrip: str, context_dict: Dict[str, List[str]]
    ) -> Tuple[str, str, str]:
        """
        Synchrone implementatie van definitie generatie.

        Returns:
            Tuple van (origineel, gecorrigeerd, marker)
        """
        # Bouw prompt
        prompt = self._build_prompt(begrip, context_dict)

        # Genereer definitie via GPT
        definitie = stuur_prompt_naar_gpt(
            prompt, self.config.model, self.config.temperature, self.config.max_tokens
        )

        # Schoon op indien ingeschakeld
        if self.config.enable_cleaning:
            definitie_gecorrigeerd = opschonen(definitie, begrip)

            # Bepaal marker
            if definitie == definitie_gecorrigeerd:
                marker = "✅ Opschoning niet nodig"
            else:
                marker = "🔧 Definitie is opgeschoond"
        else:
            definitie_gecorrigeerd = definitie
            marker = "⚡ Opschoning overgeslagen"

        return definitie, definitie_gecorrigeerd, marker

    def _build_prompt(self, begrip: str, context_dict: Dict[str, List[str]]) -> str:
        """Bouw prompt voor definitie generatie."""
        configuratie = PromptConfiguratie(begrip=begrip, context_dict=context_dict)

        prompt_builder = PromptBouwer(configuratie)
        return prompt_builder.bouw_prompt()

    def _simple_category_detection(self, begrip: str) -> str:
        """
        Simpele categorie detectie op basis van patronen.

        Args:
            begrip: Het begrip om te categoriseren

        Returns:
            Categorie string ('type', 'proces', 'resultaat', 'exemplaar')
        """
        begrip_lower = begrip.lower()

        # Proces patronen
        if any(begrip_lower.endswith(p) for p in ["atie", "ing", "eren"]):
            return "proces"
        elif any(
            w in begrip_lower for w in ["verificatie", "authenticatie", "controle"]
        ):
            return "proces"

        # Type patronen
        elif any(
            w in begrip_lower for w in ["document", "bewijs", "systeem", "middel"]
        ):
            return "type"

        # Resultaat patronen
        elif any(
            w in begrip_lower for w in ["resultaat", "uitkomst", "besluit", "rapport"]
        ):
            return "resultaat"

        # Default naar proces
        return "proces"

    def _build_context_dict(self, request: GenerationRequest) -> Dict[str, List[str]]:
        """Converteer GenerationRequest naar context dictionary."""
        context_dict = {
            "organisatorisch": [],
            "juridisch": [],
            "wettelijk": [],
            "domein": [],
        }

        if request.organisatie:
            context_dict["organisatorisch"].append(request.organisatie)

        if request.domein:
            context_dict["domein"].append(request.domein)

        if request.context:
            # Parse context string voor verschillende types
            context_parts = request.context.split(",")
            for part in context_parts:
                part = part.strip()
                # Simpele heuristiek voor context type detectie
                if any(word in part.lower() for word in ["wet", "artikel", "lid"]):
                    context_dict["wettelijk"].append(part)
                elif any(word in part.lower() for word in ["recht", "juridisch"]):
                    context_dict["juridisch"].append(part)
                else:
                    context_dict["organisatorisch"].append(part)

        return context_dict

    def _build_enhancement_prompt(self, definition: Definition) -> str:
        """Bouw prompt voor definitie verbetering."""
        return f"""
Gegeven de volgende definitie:

Begrip: {definition.begrip}
Definitie: {definition.definitie}

Genereer de volgende aanvullende informatie:
1. Een korte toelichting (max 2 zinnen) die extra context geeft
2. 3-5 synoniemen of verwante termen
3. 2-3 gerelateerde begrippen die relevant zijn

Formaat je antwoord als:
TOELICHTING: [toelichting hier]
SYNONIEMEN: [synoniem1], [synoniem2], ...
GERELATEERD: [begrip1], [begrip2], ...
"""

    def _parse_enhancement_response(self, response: str) -> Dict[str, any]:
        """Parse de enhancement response naar structured data."""
        result = {"toelichting": None, "synoniemen": [], "gerelateerde_begrippen": []}

        lines = response.strip().split("\n")
        for line in lines:
            if line.startswith("TOELICHTING:"):
                result["toelichting"] = line.replace("TOELICHTING:", "").strip()
            elif line.startswith("SYNONIEMEN:"):
                synoniemen_text = line.replace("SYNONIEMEN:", "").strip()
                result["synoniemen"] = [s.strip() for s in synoniemen_text.split(",")]
            elif line.startswith("GERELATEERD:"):
                gerelateerd_text = line.replace("GERELATEERD:", "").strip()
                result["gerelateerde_begrippen"] = [
                    g.strip() for g in gerelateerd_text.split(",")
                ]

        return result

    # Statistieken methods

    def get_stats(self) -> Dict[str, int]:
        """Haal generator statistieken op."""
        return self._stats.copy()

    def reset_stats(self) -> None:
        """Reset de statistieken."""
        self._stats = {
            "total_generations": 0,
            "successful_generations": 0,
            "failed_generations": 0,
            "total_tokens_used": 0,
        }
