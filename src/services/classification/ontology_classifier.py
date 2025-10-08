"""
Ontology Classification Service
Bepaalt ontologische categorie (TYPE/EXEMPLAAR/PROCES/RESULTAAT) voor begrippen.

Hybrid approach:
1. Primary: LLM-based classificatie (flexibel, context-aware)
2. Validation: Rules-based sanity checks (deterministisch)
"""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from src.services.ai_service_v2 import AIServiceV2
from src.services.classification.ontology_validator import OntologyValidator

logger = logging.getLogger(__name__)

OntologyLevel = Literal["TYPE", "EXEMPLAAR", "PROCES", "RESULTAAT", "ONBESLIST"]


@dataclass
class ClassificationResult:
    """Resultaat van ontologische classificatie."""

    level: OntologyLevel
    confidence: float
    rationale: str
    linguistic_cues: list[str]
    validation_warnings: list[str] = None

    def __post_init__(self):
        if self.validation_warnings is None:
            self.validation_warnings = []

    def to_dict(self) -> dict:
        return {
            "level": self.level,
            "confidence": self.confidence,
            "rationale": self.rationale,
            "linguistic_cues": self.linguistic_cues,
            "validation_warnings": self.validation_warnings,
        }


class OntologyClassifierService:
    """
    Service voor ontologische classificatie van begrippen.

    Gebruikt LLM (GPT-4) voor primaire classificatie met rules-based validatie.
    """

    PROMPT_PATH = Path("config/prompts/ontology_classification.yaml")

    def __init__(self, ai_service: AIServiceV2):
        self.ai_service = ai_service
        self.validator = OntologyValidator()
        self._load_prompt_template()

    def _load_prompt_template(self):
        """Laad prompt template uit YAML config."""
        import yaml

        if not self.PROMPT_PATH.exists():
            raise FileNotFoundError(
                f"Ontology classification prompt niet gevonden: {self.PROMPT_PATH}"
            )

        with open(self.PROMPT_PATH, encoding="utf-8") as f:
            config = yaml.safe_load(f)

        self.system_prompt = config["system"]
        self.user_template = config["user_template"]

    def classify(
        self,
        begrip: str,
        definitie: str,
        context: str | None = None,
        voorbeelden: list[str] | None = None,
    ) -> ClassificationResult:
        """
        Classificeer begrip naar ontologische categorie.

        Args:
            begrip: Te classificeren begrip
            definitie: Definitie van het begrip
            context: Optionele context (bronnen, domein)
            voorbeelden: Optionele voorbeeldzinnen

        Returns:
            ClassificationResult met level, confidence, rationale
        """
        # Build context sectie
        context_parts = []
        if context:
            context_parts.append(f"**Context:** {context}")
        if voorbeelden:
            voorbeelden_str = "\n".join(f"- {v}" for v in voorbeelden)
            context_parts.append(f"**Voorbeelden:**\n{voorbeelden_str}")

        context_section = "\n\n".join(context_parts) if context_parts else ""

        # Build user prompt
        user_prompt = self.user_template.format(
            begrip=begrip, definitie=definitie, context_section=context_section
        )

        # Call LLM
        logger.info(f"Classificeren begrip via LLM: {begrip}")
        try:
            response = self.ai_service.generate_completion(
                prompt=user_prompt,
                system_prompt=self.system_prompt,
                temperature=0.3,  # Lager voor consistentie
                max_tokens=500,
            )

            # Parse JSON response
            result_data = self._parse_llm_response(response)

            # Validate met rules
            validation_warnings = self.validator.validate(
                level=result_data["level"], begrip=begrip, definitie=definitie
            )

            result = ClassificationResult(
                level=result_data["level"],
                confidence=result_data["confidence"],
                rationale=result_data["rationale"],
                linguistic_cues=result_data.get("linguistic_cues", []),
                validation_warnings=validation_warnings,
            )

            logger.info(
                f"Classificatie resultaat: {result.level} "
                f"(confidence: {result.confidence:.2f})"
            )
            if validation_warnings:
                logger.warning(f"Validatie warnings: {validation_warnings}")

            return result

        except Exception as e:
            logger.error(f"Fout bij classificatie: {e}", exc_info=True)
            # Fallback naar ONBESLIST
            return ClassificationResult(
                level="ONBESLIST",
                confidence=0.0,
                rationale=f"Classificatie gefaald: {e!s}",
                linguistic_cues=[],
                validation_warnings=[f"ERROR: {e!s}"],
            )

    def _parse_llm_response(self, response: str) -> dict:
        """Parse LLM response naar gestructureerde data."""
        try:
            # Strip markdown code blocks als aanwezig
            cleaned = response.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()

            data = json.loads(cleaned)

            # Valideer vereiste velden
            required = ["level", "confidence", "rationale"]
            for field in required:
                if field not in data:
                    raise ValueError(f"Ontbrekend veld in LLM response: {field}")

            # Valideer level waarde
            valid_levels = ["TYPE", "EXEMPLAAR", "PROCES", "RESULTAAT", "ONBESLIST"]
            if data["level"] not in valid_levels:
                raise ValueError(f"Ongeldige level: {data['level']}")

            # Valideer confidence range
            conf = float(data["confidence"])
            if not 0.0 <= conf <= 1.0:
                raise ValueError(f"Confidence buiten range: {conf}")

            return data

        except json.JSONDecodeError as e:
            logger.error(f"JSON parse fout: {e}\nResponse: {response}")
            raise ValueError(f"Ongeldige JSON response van LLM: {e}")

    def classify_batch(self, items: list[dict[str, str]]) -> list[ClassificationResult]:
        """
        Classificeer meerdere begrippen in batch.

        Args:
            items: List van dicts met 'begrip' en 'definitie' keys

        Returns:
            List van ClassificationResult objecten
        """
        results = []
        for item in items:
            result = self.classify(
                begrip=item["begrip"],
                definitie=item["definitie"],
                context=item.get("context"),
                voorbeelden=item.get("voorbeelden"),
            )
            results.append(result)

        return results
