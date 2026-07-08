"""SynonymSuggester - model-onafhankelijke synoniem-suggestie service (DEF-459).

Roept het geconfigureerde model aan via AIServiceV2 + ModelRouter
(task_type="synonyms") met een dedicated juridische onderzoeksprompt en een
defensieve response-parser. Geen provider- of modelnaam wordt gehardcodeerd;
de router kiest provider + model.

Architecture Reference:
    docs/architectuur/synonym-orchestrator-architecture-v3.1.md
    Lines 330-502: SynonymOrchestrator specification (dependency)
"""

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from services.ai_service_v2 import AIServiceV2

logger = logging.getLogger(__name__)


@dataclass
class SynonymSuggestion:
    """
    Synoniem-suggestie met metadata.

    Attributes:
        synoniem: Het voorgestelde synoniem
        confidence: Confidence score (0.0-1.0)
        rationale: Uitleg waarom dit een goed synoniem is
    """

    synoniem: str
    confidence: float
    rationale: str

    def __post_init__(self) -> None:
        """Valideer velden."""
        if not self.synoniem or not self.synoniem.strip():
            msg = "synoniem mag niet leeg zijn"
            raise ValueError(msg)

        if not (0.0 <= self.confidence <= 1.0):
            msg = f"confidence moet tussen 0.0 en 1.0 zijn: {self.confidence}"
            raise ValueError(msg)


class SynonymSuggester:
    """Model-onafhankelijke synoniem-suggester (DEF-459).

    Roept het geconfigureerde model aan via AIServiceV2 + ModelRouter
    (task_type="synonyms") met een dedicated juridische onderzoeksprompt.
    Nooit een modelnaam hardcoden — de router kiest provider + model.
    """

    def __init__(self, ai_service: "AIServiceV2", timeout_seconds: int = 30) -> None:
        self._ai_service = ai_service
        self._timeout = timeout_seconds
        self._stats: dict[str, int] = {
            "total_calls": 0,
            "success_count": 0,
            "failure_count": 0,
        }
        logger.info(
            "SynonymSuggester initialized (model-onafhankelijk via ModelRouter)"
        )

    async def suggest_synonyms(
        self,
        term: str,
        definitie: str | None = None,
        context: list[str] | str | None = None,
    ) -> list[SynonymSuggestion]:
        """Vraag synoniemen op bij het geconfigureerde model.

        Args:
            term: De juridische term waarvoor synoniemen gezocht worden.
            definitie: Optionele definitie als betekenis-anker.
            context: Optionele juridische context (lijst of enkele string).

        Returns:
            Lijst van SynonymSuggestion objecten; leeg bij fout of geen resultaat.
        """
        from services.prompts.synonym_research_prompt import (
            build_synonym_research_prompt,
        )
        from services.prompts.synonym_response_parser import parse_synonym_response

        self._stats["total_calls"] += 1
        if isinstance(context, list):
            juridische_context: list[str] | None = context
        elif isinstance(context, str) and context:
            juridische_context = [context]
        else:
            juridische_context = None

        system_prompt, user_prompt = build_synonym_research_prompt(
            term=term, definitie=definitie, juridische_context=juridische_context
        )
        try:
            result = await self._ai_service.generate_definition(
                prompt=user_prompt,
                system_prompt=system_prompt,
                task_type="synonyms",
                temperature=0.3,
                max_tokens=800,
                timeout_seconds=self._timeout,
            )
            suggestions = parse_synonym_response(getattr(result, "text", ""))
            self._stats["success_count"] += 1
            return suggestions
        except Exception as exc:
            self._stats["failure_count"] += 1
            logger.warning("SynonymSuggester: AI-call mislukt voor '%s': %s", term, exc)
            return []

    def get_stats(self) -> dict:
        """Geef suggester-statistieken (calls/successen/fouten + status)."""
        return {**self._stats, "status": "active"}
