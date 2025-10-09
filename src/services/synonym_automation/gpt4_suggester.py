"""
GPT-4 Synonym Suggester voor juridische termen.

Deze service gebruikt GPT-4 om context-aware synoniemen te genereren voor
juridische begrippen. De service produceert synoniemen met confidence scores
en rationale voor menselijke review.

Features:
- Context-aware suggestions (gebruikt database definities)
- Confidence scoring (0.0-1.0)
- Rationale voor elke suggestie
- JSON-based structured output
- Retry logica voor malformed responses
"""

import json
import logging
from dataclasses import dataclass, field
from typing import Any

from services.ai_service_v2 import AIServiceV2
from services.interfaces import AIServiceError

logger = logging.getLogger(__name__)


@dataclass
class SynonymSuggestion:
    """
    Represents een synoniem suggestie van GPT-4.

    Attributes:
        hoofdterm: De originele juridische term
        synoniem: De gesuggereerde synoniem
        confidence: Confidence score (0.0-1.0)
        rationale: Uitleg waarom dit een goede synoniem is
        context_used: Context die gebruikt is voor de suggestie
    """

    hoofdterm: str
    synoniem: str
    confidence: float
    rationale: str
    context_used: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for database/CSV export."""
        return {
            "hoofdterm": self.hoofdterm,
            "synoniem": self.synoniem,
            "confidence": self.confidence,
            "rationale": self.rationale,
            "context": self.context_used,
        }


class GPT4SynonymSuggester:
    """
    Service voor het genereren van synoniem suggesties met GPT-4.

    Deze service gebruikt GPT-4 Turbo om context-aware juridische synoniemen
    te genereren. De output bevat confidence scores en rationale voor
    menselijke review.
    """

    # Prompt template met voorbeelden voor betere kwaliteit
    SYSTEM_PROMPT = """Je bent een expert in Nederlands juridisch taalgebruik en
terminologie. Je taak is om synoniemen te genereren voor juridische begrippen.

BELANGRIJKE REGELS:
1. Synoniemen moeten juridisch correct zijn
2. Vermijd pejoratieven of informele termen
3. Focus op termen die uitwisselbaar zijn in juridische context
4. Geef een rationale waarom elk synoniem geschikt is
5. Wees conservatief met confidence scores (0.6-0.95)

VOORBEELDEN VAN GOEDE SYNONIEMEN:
- "voorlopige hechtenis" → "voorarrest" (0.95, vrijwel identiek juridisch begrip)
- "voorlopige hechtenis" → "bewaring" (0.90, sterk synoniem in strafrecht)
- "onherroepelijk" → "kracht van gewijsde" (0.95, technische juridische term)
- "verdachte" → "beklaagde" (0.90, verschillende procesfase, beide correct)

VOORBEELDEN VAN SLECHTE SYNONIEMEN (VERMIJD):
- "voorlopige hechtenis" → "gevangenis" (te algemeen, geen synoniem)
- "verdachte" → "crimineel" (pejoratief, niet juridisch neutraal)
- "vonnis" → "straf" (verwarring tussen uitspraak en sanctie)
- "advocaat" → "raadgever" (te breed, verliest juridische specificiteit)

OUTPUT FORMAAT:
Geef ALLEEN een JSON object terug in dit formaat (geen extra tekst):
{
  "synoniemen": [
    {
      "term": "synoniem hier",
      "confidence": 0.95,
      "rationale": "Korte uitleg waarom dit een goed synoniem is"
    }
  ]
}
"""

    USER_PROMPT_TEMPLATE = """Genereer synoniemen voor de juridische term: "{term}"

{context_section}

Genereer 5-8 relevante synoniemen met confidence scores en rationale.
Focus op termen die daadwerkelijk uitwisselbaar zijn in juridische teksten.

Onthoud: Output ALLEEN de JSON, geen extra tekst."""

    def __init__(
        self,
        ai_service: AIServiceV2 | None = None,
        model: str = "gpt-4-turbo",
        temperature: float = 0.3,
        max_tokens: int = 800,
        max_synonyms: int = 8,
        min_confidence: float = 0.6,
        max_retries: int = 3,
    ):
        """
        Initialize GPT-4 synonym suggester.

        Args:
            ai_service: AIServiceV2 instance (creates default if None)
            model: GPT model to use (default: gpt-4-turbo)
            temperature: Creativity parameter (default: 0.3 for consistency)
            max_tokens: Maximum response tokens (default: 800)
            max_synonyms: Maximum synonyms per term (default: 8)
            min_confidence: Minimum confidence to include (default: 0.6)
            max_retries: Maximum retries for malformed JSON (default: 3)
        """
        self.ai_service = ai_service or AIServiceV2(default_model=model)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.max_synonyms = max_synonyms
        self.min_confidence = min_confidence
        self.max_retries = max_retries

    def _build_context_section(
        self, definitie: str | None, context: list[str] | None
    ) -> str:
        """
        Build context section for prompt.

        Args:
            definitie: Optional definitie van de term
            context: Optional extra context (bijv. ["Sv", "strafrecht"])

        Returns:
            Formatted context string
        """
        sections = []

        if definitie:
            sections.append(f"DEFINITIE:\n{definitie}")

        if context:
            sections.append("CONTEXT:\n- " + "\n- ".join(context))

        if sections:
            return "\n\n".join(sections)

        return "CONTEXT: Geen extra context beschikbaar."

    def _parse_json_response(self, response: str) -> dict[str, Any]:
        """
        Parse JSON response van GPT-4, met error handling.

        Args:
            response: Raw response string

        Returns:
            Parsed JSON dict

        Raises:
            ValueError: Als JSON niet parseable is
        """
        # Strip whitespace en markdown code fences
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        response = response.strip()

        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {response[:200]}...")
            raise ValueError(f"Invalid JSON response from GPT-4: {e}") from e

    def _validate_suggestion(self, suggestion_data: dict[str, Any]) -> bool:
        """
        Validate synonym suggestion data structure.

        Args:
            suggestion_data: Dict with 'term', 'confidence', 'rationale' keys

        Returns:
            True if valid, False otherwise
        """
        required_keys = {"term", "confidence", "rationale"}
        if not all(key in suggestion_data for key in required_keys):
            logger.warning(f"Missing required keys in suggestion: {suggestion_data}")
            return False

        # Validate types
        if not isinstance(suggestion_data["term"], str):
            return False
        if not isinstance(suggestion_data["confidence"], (int, float)):
            return False
        if not isinstance(suggestion_data["rationale"], str):
            return False

        # Validate confidence range
        if not (0.0 <= suggestion_data["confidence"] <= 1.0):
            logger.warning(f"Confidence out of range: {suggestion_data['confidence']}")
            return False

        return True

    async def suggest_synonyms(
        self,
        term: str,
        definitie: str | None = None,
        context: list[str] | None = None,
    ) -> list[SynonymSuggestion]:
        """
        Genereer synoniem suggesties voor een juridische term.

        Args:
            term: De juridische term om synoniemen voor te genereren
            definitie: Optional definitie van de term (helpt GPT-4 context begrijpen)
            context: Optional extra context (bijv. ["Sv", "strafrecht", "bewaring"])

        Returns:
            Lijst van SynonymSuggestion objecten met confidence >= min_confidence

        Raises:
            AIServiceError: Bij AI service fouten
            ValueError: Bij malformed JSON na max_retries
        """
        logger.info(f"Generating GPT-4 synonym suggestions for: {term}")

        # Build prompt
        context_section = self._build_context_section(definitie, context)
        user_prompt = self.USER_PROMPT_TEMPLATE.format(
            term=term, context_section=context_section
        )

        # Retry logic voor malformed JSON
        last_error = None
        for attempt in range(self.max_retries):
            try:
                # Call GPT-4
                result = await self.ai_service.generate_definition(
                    prompt=user_prompt,
                    system_prompt=self.SYSTEM_PROMPT,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    model=self.model,
                    timeout_seconds=30,
                )

                # Parse JSON response
                response_data = self._parse_json_response(result.text)

                # Validate structure
                if "synoniemen" not in response_data:
                    raise ValueError("Response missing 'synoniemen' key")

                # Convert to SynonymSuggestion objects
                suggestions = []
                for item in response_data["synoniemen"]:
                    # Validate suggestion
                    if not self._validate_suggestion(item):
                        logger.warning(f"Skipping invalid suggestion: {item}")
                        continue

                    # Filter by confidence
                    if item["confidence"] < self.min_confidence:
                        logger.debug(
                            f"Skipping low confidence suggestion: {item['term']} "
                            f"({item['confidence']})"
                        )
                        continue

                    # Create suggestion object
                    suggestion = SynonymSuggestion(
                        hoofdterm=term,
                        synoniem=item["term"],
                        confidence=item["confidence"],
                        rationale=item["rationale"],
                        context_used={
                            "definitie": definitie,
                            "context": context,
                            "model": self.model,
                            "temperature": self.temperature,
                        },
                    )
                    suggestions.append(suggestion)

                # Limit to max_synonyms
                suggestions = suggestions[: self.max_synonyms]

                logger.info(
                    f"Generated {len(suggestions)} synonym suggestions for '{term}'"
                )
                return suggestions

            except (ValueError, json.JSONDecodeError) as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    logger.warning(
                        f"Attempt {attempt + 1}/{self.max_retries} failed: {e}. Retrying..."
                    )
                    continue
                else:
                    logger.error(
                        f"Failed to parse GPT-4 response after {self.max_retries} attempts"
                    )
                    raise ValueError(
                        f"Failed to get valid JSON response after {self.max_retries} attempts"
                    ) from last_error

            except AIServiceError as e:
                # Don't retry on API errors (rate limits, etc.)
                logger.error(f"AI service error: {e}")
                raise

        # Should not reach here, but just in case
        raise ValueError(
            f"Failed to generate synonyms after {self.max_retries} attempts"
        )
