"""
Geünificeerd Voorbeeld Generatie Systeem voor DefinitieAgent.

Consolideert synchrone, asynchrone, en gecachte voorbeeld generatie
in één uniform interface voor alle typen voorbeelden.
"""

import asyncio  # Asynchrone programmering voor parallelle voorbeeld generatie
import logging  # Logging faciliteiten voor debug en monitoring
import re  # Reguliere expressies voor tekst processing
import uuid
from dataclasses import (  # Dataklassen voor gestructureerde request/response data
    dataclass,
)
from datetime import (  # Datum en tijd functionaliteit voor timestamps, timezone
    UTC,
    datetime,
)
from enum import Enum  # Enumeraties voor voorbeeld types en modi
from typing import Any  # Type hints voor betere code documentatie

from config.config_manager import (
    get_component_config,  # Centrale component configuratie
)
from services.ai_service_v2 import AIServiceV2  # V2 AI service interface

# Importeer resilience en caching systemen voor robuuste voorbeeld generatie
from utils.integrated_resilience import (  # Volledig resilience systeem
    with_full_resilience,
)
from utils.smart_rate_limiter import (  # Smart rate limiting voor API calls
    RequestPriority,
)
from utils.voorbeelden_debug import (  # Debug logging voor voorbeelden flow
    DEBUG_ENABLED,
    debug_flow_point,
    debugger,
)
from voorbeelden.robust_cache import (
    get_robust_cache,
)  # Robuuste cache voor voorbeelden

logger = logging.getLogger(__name__)  # Logger instantie voor unified voorbeelden module

# Centrale configuratie voor aantallen voorbeelden
DEFAULT_EXAMPLE_COUNTS = {
    "voorbeeldzinnen": 3,
    "praktijkvoorbeelden": 3,
    "tegenvoorbeelden": 3,
    "synoniemen": 5,
    "antoniemen": 5,
    "toelichting": 1,
}


class ExampleType(Enum):
    """Types van voorbeelden die gegenereerd kunnen worden."""

    VOORBEELDZINNEN = "voorbeeldzinnen"  # Voorbeeldzinnen met het begrip
    PRAKTIJKVOORBEELDEN = "praktijkvoorbeelden"  # Praktische gebruiksvoorbeelden
    TEGENVOORBEELDEN = "tegenvoorbeelden"  # Tegenvoorbeelden ter verduidelijking
    SYNONIEMEN = "synoniemen"  # Synoniemen van het begrip
    ANTONIEMEN = "antoniemen"  # Antoniemen van het begrip
    TOELICHTING = "toelichting"  # Uitgebreide toelichting


class GenerationMode(Enum):
    """Generatie modi voor verschillende prestatie en betrouwbaarheid behoeften."""

    SYNC = "sync"  # Synchrone generatie (blokkerende operatie)
    ASYNC = "async"  # Asynchrone generatie (niet-blokkerend)
    CACHED = "cached"  # Gecachte generatie (hergebruik resultaten)
    RESILIENT = "resilient"  # Met volledige resilience (retry, fallback, etc.)


@dataclass
class ExampleRequest:
    """Request for example generation."""

    begrip: str
    definitie: str
    context_dict: dict[str, list[str]]
    example_type: ExampleType
    generation_mode: GenerationMode = GenerationMode.RESILIENT
    max_examples: int = 3  # Default naar 3 voor alle voorbeelden
    temperature: float | None = None  # None betekent: gebruik centrale config
    model: str | None = None


@dataclass
class ExampleResponse:
    """Response from example generation."""

    examples: list[str]
    success: bool
    error_message: str | None = None
    generation_time: float | None = None
    cached: bool = False


class UnifiedExamplesGenerator:
    """Unified system for generating all types of examples."""

    def __init__(self):
        self.generation_count = 0
        self.error_count = 0
        self.cache_hits = 0
        # Initialize AI service V2
        self.ai_service = AIServiceV2(
            default_model=get_component_config("ai_service").get(
                "model", "gpt-4o-mini"
            ),
            use_cache=True,
        )

    def _get_config_for_type(self, example_type: ExampleType) -> dict:
        """Get configuration for a specific example type from central config."""
        # Map ExampleType enum to config keys
        # Gebruik Nederlandse keys overal
        type_mapping = {
            ExampleType.VOORBEELDZINNEN: "voorbeeldzinnen",
            ExampleType.PRAKTIJKVOORBEELDEN: "praktijkvoorbeelden",
            ExampleType.TEGENVOORBEELDEN: "tegenvoorbeelden",
            ExampleType.SYNONIEMEN: "synoniemen",
            ExampleType.ANTONIEMEN: "antoniemen",
            ExampleType.TOELICHTING: "toelichting",
        }

        config_key = type_mapping.get(example_type, "voorbeeldzinnen")
        return get_component_config("voorbeelden", config_key)

    def _run_async_safe(self, coro):
        """Run async coroutine safely, detecting existing event loop."""
        try:
            # Check if there's already a running event loop
            asyncio.get_running_loop()
            # If we're in an event loop, we can't use asyncio.run()
            # Instead, we'll run in a thread pool
            import concurrent.futures

            def run_in_thread():
                # Create new event loop in thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(coro)
                finally:
                    loop.close()

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_in_thread)
                return future.result()

        except RuntimeError:
            # No event loop running, safe to use asyncio.run()
            return asyncio.run(coro)

    @debug_flow_point("A")
    def generate_examples(self, request: ExampleRequest) -> ExampleResponse:
        """Generate examples based on request configuration."""
        start_time = datetime.now(UTC)

        # Start debug tracking if enabled
        generation_id = ""
        if DEBUG_ENABLED:
            generation_id = debugger.start_generation(
                begrip=request.begrip, definitie=request.definitie
            )
            debugger.log_point(
                "A",
                generation_id,
                example_type=request.example_type.value,
                generation_mode=request.generation_mode.value,
                max_examples=request.max_examples,
            )

        # Get configuration for this example type if not specified
        config = self._get_config_for_type(request.example_type)
        if request.model is None:
            request.model = config.get("model")
        if request.temperature is None:  # Use config if not specified
            request.temperature = config.get("temperature", 0.5)

        try:
            # Route to appropriate generation method
            if request.generation_mode == GenerationMode.SYNC:
                examples = self._generate_sync(request)
            elif request.generation_mode == GenerationMode.ASYNC:
                examples = self._run_async_safe(self._generate_async(request))
            elif request.generation_mode == GenerationMode.CACHED:
                examples = self._generate_cached(request)
            elif request.generation_mode == GenerationMode.RESILIENT:
                examples = self._run_async_safe(self._generate_resilient(request))
            else:
                msg = f"Unsupported generation mode: {request.generation_mode}"
                raise ValueError(msg)

            self.generation_count += 1
            generation_time = (datetime.now(UTC) - start_time).total_seconds()

            # Log successful generation
            if DEBUG_ENABLED and generation_id:
                debugger.log_point(
                    "B",
                    generation_id,
                    examples_count=len(examples),
                    generation_time=generation_time,
                )
                debugger.end_generation(
                    generation_id,
                    success=True,
                    results={request.example_type.value: examples},
                )

            return ExampleResponse(
                examples=examples, success=True, generation_time=generation_time
            )

        except Exception as e:
            self.error_count += 1
            logger.error(f"Example generation failed: {e}")

            # Log error in debug
            if DEBUG_ENABLED and generation_id:
                debugger.log_error(generation_id, "A", e)
                debugger.end_generation(generation_id, success=False)

            return ExampleResponse(examples=[], success=False, error_message=str(e))

    def _generate_sync(self, request: ExampleRequest) -> list[str]:
        """Synchronous example generation."""
        prompt = self._build_prompt(request)

        # Enhanced debug logging
        if DEBUG_ENABLED:
            generation_id = getattr(request, "generation_id", str(uuid.uuid4())[:8])
            debugger.log_point(
                "B", generation_id, method="sync", prompt_length=len(prompt)
            )

        # Debug logging voor synoniemen/antoniemen
        if request.example_type in [ExampleType.SYNONIEMEN, ExampleType.ANTONIEMEN]:
            logger.info(
                f"Generating {request.example_type} with prompt: {prompt[:200]}..."
            )

        try:
            # Run async method synchronously
            response = self._run_async_safe(
                self.ai_service.generate_definition(
                    prompt=prompt,
                    model=request.model,
                    temperature=request.temperature,
                    max_tokens=2000,
                )
            )

            # Debug logging voor synoniemen/antoniemen response
            if request.example_type in [ExampleType.SYNONIEMEN, ExampleType.ANTONIEMEN]:
                logger.info(
                    f"Received {request.example_type} response: {response.text[:300]}..."
                )

            return self._parse_response(response.text, request.example_type)
        except Exception as e:
            msg = f"Synchronous generation failed: {e}"
            raise RuntimeError(msg) from e

    async def _generate_async(self, request: ExampleRequest) -> list[str]:
        """Asynchronous example generation."""
        prompt = self._build_prompt(request)

        try:
            # Direct async call to V2 service
            response = await self.ai_service.generate_definition(
                prompt=prompt,
                model=request.model,
                temperature=request.temperature,
                max_tokens=1500,
            )
            return self._parse_response(response.text, request.example_type)
        except Exception as e:
            msg = f"Asynchronous generation failed: {e}"
            raise RuntimeError(msg) from e

    def _generate_cached(self, request: ExampleRequest) -> list[str]:
        """Cached example generation with robust cache keys."""
        cache = get_robust_cache()

        # Generate robust cache key
        cache_key = cache.generate_robust_key(
            example_type=request.example_type.value,
            begrip=request.begrip,
            definitie=request.definitie,
            context_dict=request.context_dict,
            max_examples=request.max_examples,
            model=request.model,
            temperature=request.temperature,
        )

        # Try to get from cache
        cached_value = cache.get(cache_key)
        if cached_value is not None:
            self.cache_hits += 1
            if DEBUG_ENABLED:
                logger.debug(f"Cache hit for {request.example_type.value}")
            return cached_value

        # Generate new value
        result = self._generate_sync(request)

        # Store in cache (will use type-specific TTL)
        cache.set(cache_key, result)

        return result

    async def _generate_resilient(self, request: ExampleRequest) -> list[str]:
        """Resilient example generation with retry logic and rate limiting."""
        # Route to specific resilient method based on example type
        if request.example_type == ExampleType.VOORBEELDZINNEN:
            return await self._generate_resilient_sentence(request)
        if request.example_type == ExampleType.PRAKTIJKVOORBEELDEN:
            return await self._generate_resilient_practical(request)
        if request.example_type == ExampleType.TEGENVOORBEELDEN:
            return await self._generate_resilient_counter(request)
        if request.example_type == ExampleType.SYNONIEMEN:
            return await self._generate_resilient_synonyms(request)
        if request.example_type == ExampleType.ANTONIEMEN:
            return await self._generate_resilient_antonyms(request)
        if request.example_type == ExampleType.TOELICHTING:
            return await self._generate_resilient_explanation(request)
        msg = f"Unknown example type: {request.example_type}"
        raise ValueError(msg)

    @with_full_resilience(
        endpoint_name="examples_generation_sentence",
        priority=RequestPriority.NORMAL,
        timeout=10.0,
        model=None,
        expected_tokens=200,
    )
    async def _generate_resilient_sentence(self, request: ExampleRequest) -> list[str]:
        """Resilient sentence example generation."""
        return await self._generate_resilient_common(request)

    @with_full_resilience(
        endpoint_name="examples_generation_practical",
        priority=RequestPriority.NORMAL,
        timeout=10.0,
        model=None,
        expected_tokens=200,
    )
    async def _generate_resilient_practical(self, request: ExampleRequest) -> list[str]:
        """Resilient practical example generation."""
        return await self._generate_resilient_common(request)

    @with_full_resilience(
        endpoint_name="examples_generation_counter",
        priority=RequestPriority.NORMAL,
        timeout=10.0,
        model=None,
        expected_tokens=200,
    )
    async def _generate_resilient_counter(self, request: ExampleRequest) -> list[str]:
        """Resilient counter example generation."""
        return await self._generate_resilient_common(request)

    @with_full_resilience(
        endpoint_name="examples_generation_synonyms",
        priority=RequestPriority.NORMAL,
        timeout=10.0,
        model=None,
        expected_tokens=200,
    )
    async def _generate_resilient_synonyms(self, request: ExampleRequest) -> list[str]:
        """Resilient synonyms generation."""
        return await self._generate_resilient_common(request)

    @with_full_resilience(
        endpoint_name="examples_generation_antonyms",
        priority=RequestPriority.NORMAL,
        timeout=10.0,
        model=None,
        expected_tokens=200,
    )
    async def _generate_resilient_antonyms(self, request: ExampleRequest) -> list[str]:
        """Resilient antonyms generation."""
        return await self._generate_resilient_common(request)

    @with_full_resilience(
        endpoint_name="examples_generation_explanation",
        priority=RequestPriority.NORMAL,
        timeout=10.0,
        model=None,
        expected_tokens=200,
    )
    async def _generate_resilient_explanation(
        self, request: ExampleRequest
    ) -> list[str]:
        """Resilient explanation generation."""
        prompt = self._build_prompt(request)

        try:
            response = await self.ai_service.generate_definition(
                prompt=prompt,
                model=request.model,
                temperature=request.temperature,
                max_tokens=1500,
            )
            # Voor explanation, return de hele response als één item
            return [response.text.strip()] if response.text.strip() else []
        except Exception as e:
            msg = f"Resilient generation failed: {e}"
            raise RuntimeError(msg) from e

    async def _generate_resilient_common(self, request: ExampleRequest) -> list[str]:
        """Common resilient generation logic."""
        prompt = self._build_prompt(request)

        try:
            response = await self.ai_service.generate_definition(
                prompt=prompt,
                model=request.model,
                temperature=request.temperature,
                max_tokens=1500,
            )
            return self._parse_response(response.text)
        except Exception as e:
            msg = f"Resilient generation failed: {e}"
            raise RuntimeError(msg) from e

    def _build_prompt(self, request: ExampleRequest) -> str:
        """Build appropriate prompt based on example type."""
        begrip = request.begrip
        definitie = request.definitie
        context_dict = request.context_dict

        # Context formatting
        context_text = self._format_context(context_dict)

        # Type-specific prompts
        if request.example_type == ExampleType.VOORBEELDZINNEN:
            return f"""
Geef {request.max_examples} korte voorbeeldzinnen waarin het begrip '{begrip}'
op een duidelijke manier wordt gebruikt. De zinnen moeten passen binnen de gegeven context.

Definitie: {definitie}

Context:
{context_text}

Integreer de context natuurlijk in de voorbeeldzinnen. Als er een organisatie of domein
is opgegeven, gebruik deze in de zinnen. Geef alleen de voorbeeldzinnen, elk op een nieuwe regel.
"""

        if request.example_type == ExampleType.PRAKTIJKVOORBEELDEN:
            return f"""
Geef {request.max_examples} praktische voorbeelden waarbij het begrip '{begrip}'
van toepassing is in de praktijk binnen de gegeven context.

Definitie: {definitie}

Context:
{context_text}

Geef concrete, herkenbare situaties uit de opgegeven organisatie/domein waarin dit begrip
gebruikt wordt. Maak de voorbeelden specifiek voor de context.
"""

        if request.example_type == ExampleType.TEGENVOORBEELDEN:
            return f"""
Geef {request.max_examples} tegenvoorbeelden die NIET onder het begrip '{begrip}' vallen,
maar wel relevant zijn voor de gegeven context.

Definitie: {definitie}

Context:
{context_text}

Geef voorbeelden uit dezelfde organisatie/domein die lijken op '{begrip}' maar er niet
onder vallen. Leg kort uit waarom deze voorbeelden niet onder de definitie vallen.
"""

        if request.example_type == ExampleType.SYNONIEMEN:
            return f"""Geef EXACT {request.max_examples} synoniemen of verwante termen voor '{begrip}'
BELANGRIJK: Geef PRECIES {request.max_examples} synoniemen, niet meer en niet minder.
Geef alleen de synoniemen, elk op een nieuwe regel, zonder nummering of bullets."""

        if request.example_type == ExampleType.ANTONIEMEN:
            return f"""Geef EXACT {request.max_examples} antoniemen of tegengestelde termen voor '{begrip}'
BELANGRIJK: Geef PRECIES {request.max_examples} antoniemen, niet meer en niet minder.
Geef alleen de antoniemen, elk op een nieuwe regel, zonder nummering of bullets."""

        if request.example_type == ExampleType.TOELICHTING:
            return f"""
Geef een korte, heldere toelichting bij het begrip '{begrip}' specifiek voor de gegeven context.

Definitie: {definitie}

Context:
{context_text}

Leg uit wat dit begrip betekent in de praktijk van deze organisatie/domein en waarom
het daar belangrijk is. Maak de uitleg relevant voor de opgegeven context.

GEEF ALLEEN ÉÉN ENKELE ALINEA ALS ANTWOORD, GEEN OPSOMMINGEN OF MEERDERE PARAGRAFEN.
"""

        msg = f"Unsupported example type: {request.example_type}"
        raise ValueError(msg)

    def _format_context(self, context_dict: dict[str, list[str]]) -> str:
        """Format context dictionary for prompts."""
        context_lines = []

        for key, values in context_dict.items():
            if values:
                context_lines.append(f"{key.capitalize()}: {', '.join(values)}")
            else:
                context_lines.append(f"{key.capitalize()}: geen")

        return "\n".join(context_lines)

    def _parse_response(  # noqa: PLR0912, PLR0915
        self, response: str, example_type: ExampleType | None = None
    ) -> list[str]:
        """Parse GPT response into list of examples."""
        if not response:
            return []

        # Voor synoniemen/antoniemen: gebruik example_type als beschikbaar, anders check response
        is_synonym_or_antonym = False
        if example_type:
            is_synonym_or_antonym = example_type in [
                ExampleType.SYNONIEMEN,
                ExampleType.ANTONIEMEN,
            ]
        else:
            # Fallback: check of het woord in de response staat
            is_synonym_or_antonym = any(
                word in response.lower() for word in ["synoniem", "antoniem"]
            )

        if is_synonym_or_antonym:
            # Debug logging
            logger.info(f"Parsing {example_type} response (length: {len(response)})")
            logger.debug(f"Raw response: {response[:500]}")

            lines = response.strip().split("\n")
            examples = []
            for line in lines:
                # Verwijder bullets, nummers, streepjes etc.
                cleaned = re.sub(r"^\s*[-—•*\d\.]+\s*", "", line).strip()
                # Filter lege regels en headers
                if (
                    cleaned
                    and len(cleaned) > 1
                    and not any(
                        skip in cleaned.lower()
                        for skip in [
                            "synoniem",
                            "antoniem",
                            "hier zijn",
                            "bijvoorbeeld",
                        ]
                    )
                ):
                    # Check of de regel komma-gescheiden items bevat
                    if "," in cleaned and not any(
                        c in cleaned for c in [".", ":", ";"]
                    ):
                        # Split op komma's voor meerdere items op één regel
                        items = [item.strip() for item in cleaned.split(",")]
                        examples.extend(
                            [item for item in items if item and len(item) > 1]
                        )
                    else:
                        examples.append(cleaned)

            logger.info(f"Parsed {len(examples)} {example_type} items: {examples}")
            return examples if examples else []

        # Voor complexe voorbeelden met uitleg (praktijk/tegenvoorbeelden)
        # Split op dubbele newlines of genummerde patronen
        text = response.strip()

        # Probeer eerst op "1." "2." etc met sterke scheiding
        # Ook ondersteuning voor markdown headers zoals "### 1." of "## 1."
        numbered_pattern = r"\n+(?=(?:#{1,3}\s*)?\d+[\.\)]\s*[A-Z\*#])"
        parts = re.split(numbered_pattern, text)

        if len(parts) > 1:
            examples = []
            for part in parts:
                # Parse praktijkvoorbeelden met verschillende formaten
                # Patroon 1: nummer. Titel\nSituatie:**\n[inhoud]\nToepassing:**\n[inhoud]
                # Patroon 2: nummer. Titel**\n[inhoud]
                # Patroon 3: nummer. Titel: [inhoud]

                # Probeer eerst het Situatie/Toepassing patroon (inclusief markdown headers)
                situatie_match = re.match(
                    r"^(?:#{1,3}\s*)?\d+[\.\)]\s*([^*\n]+?)\n+Situatie:\*{0,2}\s*\n+(.+?)\n+Toepassing[^:]*:\*{0,2}\s*\n+(.+)",
                    part,
                    re.DOTALL | re.IGNORECASE,
                )

                if situatie_match:
                    title = situatie_match.group(1).strip()
                    situatie = situatie_match.group(2).strip()
                    toepassing = situatie_match.group(3).strip()
                    # Format als "Titel: Situatie... Toepassing..."
                    formatted = f"{title}: {situatie}\n\n{toepassing}"
                    examples.append(formatted)
                    continue

                # Probeer het standaard patroon (inclusief markdown headers)
                # Ondersteunt: "1. Titel", "### 1. Titel", "1) Titel", etc.
                title_match = re.match(
                    r"^(?:#{1,3}\s*)?\d+[\.\)]\s*\*{0,2}([^*\n]+?)\*{0,2}[\n:](.+)",
                    part,
                    re.DOTALL,
                )

                if title_match:
                    title = title_match.group(1).strip()
                    content = title_match.group(2).strip()

                    # Check voor "Toelichting:" patroon
                    if "toelichting:" in content.lower():
                        # Split op toelichting
                        parts = re.split(r"\n*[Tt]oelichting:\s*", content, maxsplit=1)
                        if len(parts) == 2:
                            main_content = parts[0].strip()
                            explanation = parts[1].strip()
                            # Combineer alles als één entry met titel, inhoud en toelichting
                            formatted = f"{title}: {main_content}"
                            if explanation:
                                formatted += f"\n\nToelichting: {explanation}"
                            examples.append(formatted)
                        else:
                            # Geen toelichting gevonden, gebruik normale formatting
                            examples.append(f"{title}: {content}")
                    else:
                        # Geen toelichting, format als "Titel: inhoud"
                        examples.append(f"{title}: {content}")
                else:
                    # Fallback naar oude methode als het patroon niet matcht
                    # Verwijder ook markdown headers
                    cleaned = re.sub(
                        r"^(?:#{1,3}\s*)?\d+[\.\)]\s*\**\s*", "", part
                    ).strip()
                    if cleaned and not any(
                        skip in cleaned[:50].lower()
                        for skip in ["hier zijn", "voorbeelden", "bijvoorbeeld"]
                    ):
                        cleaned = re.sub(r"[\s—]+$", "", cleaned)
                        examples.append(cleaned)

            return examples if examples else [text]

        # Voor eenvoudige voorbeeldzinnen zonder nummering
        # Split op enkele newlines maar filter agressief
        lines = text.split("\n")
        if len(lines) > 1:
            examples = []
            for line in lines:
                # Verwijder bullets en streepjes
                cleaned = re.sub(r"^\s*[-—•*]+\s*", "", line).strip()
                # Filter lege regels, te korte regels, en headers
                if (
                    cleaned
                    and len(cleaned) > 10
                    and not any(
                        skip in cleaned.lower()
                        for skip in ["voorbeelden:", "hier zijn", "bijvoorbeeld:"]
                    )
                ):
                    examples.append(cleaned)

            # Als we minstens één goed voorbeeld hebben
            if examples:
                return examples

        # Fallback: return hele response als één voorbeeld (maar alleen als substantieel)
        if len(text) > 20:
            return [text]
        return []

    def get_statistics(self) -> dict[str, Any]:
        """Get generation statistics."""
        return {
            "total_generations": self.generation_count,
            "total_errors": self.error_count,
            "cache_hits": self.cache_hits,
            "success_rate": (
                (self.generation_count - self.error_count) / self.generation_count
                if self.generation_count > 0
                else 0
            ),
        }


# Global generator instance
_generator: UnifiedExamplesGenerator | None = None


def get_examples_generator() -> UnifiedExamplesGenerator:
    """Get or create global examples generator."""
    global _generator
    if _generator is None:
        _generator = UnifiedExamplesGenerator()
    return _generator


# Convenience functions for different example types
def genereer_voorbeeld_zinnen(
    begrip: str,
    definitie: str,
    context_dict: dict[str, list[str]],
    mode: GenerationMode = GenerationMode.RESILIENT,
) -> list[str]:
    """Generate example sentences."""
    generator = get_examples_generator()
    request = ExampleRequest(
        begrip=begrip,
        definitie=definitie,
        context_dict=context_dict,
        example_type=ExampleType.VOORBEELDZINNEN,
        generation_mode=mode,
        max_examples=DEFAULT_EXAMPLE_COUNTS[ExampleType.VOORBEELDZINNEN.value],
    )
    response = generator.generate_examples(request)
    return response.examples if response.success else []


def genereer_praktijkvoorbeelden(
    begrip: str,
    definitie: str,
    context_dict: dict[str, list[str]],
    mode: GenerationMode = GenerationMode.RESILIENT,
) -> list[str]:
    """Generate practical examples."""
    generator = get_examples_generator()
    request = ExampleRequest(
        begrip=begrip,
        definitie=definitie,
        context_dict=context_dict,
        example_type=ExampleType.PRAKTIJKVOORBEELDEN,
        generation_mode=mode,
        max_examples=DEFAULT_EXAMPLE_COUNTS[ExampleType.PRAKTIJKVOORBEELDEN.value],
    )
    response = generator.generate_examples(request)
    return response.examples if response.success else []


def genereer_tegenvoorbeelden(
    begrip: str,
    definitie: str,
    context_dict: dict[str, list[str]],
    mode: GenerationMode = GenerationMode.RESILIENT,
) -> list[str]:
    """Generate counter examples."""
    generator = get_examples_generator()
    request = ExampleRequest(
        begrip=begrip,
        definitie=definitie,
        context_dict=context_dict,
        example_type=ExampleType.TEGENVOORBEELDEN,
        generation_mode=mode,
        max_examples=DEFAULT_EXAMPLE_COUNTS[ExampleType.TEGENVOORBEELDEN.value],
    )
    response = generator.generate_examples(request)
    return response.examples if response.success else []


def genereer_synoniemen(
    begrip: str,
    definitie: str,
    context_dict: dict[str, list[str]],
    mode: GenerationMode = GenerationMode.RESILIENT,
) -> list[str]:
    """Generate synonyms."""
    generator = get_examples_generator()
    request = ExampleRequest(
        begrip=begrip,
        definitie=definitie,
        context_dict=context_dict,
        example_type=ExampleType.SYNONIEMEN,
        generation_mode=mode,
        max_examples=DEFAULT_EXAMPLE_COUNTS[ExampleType.SYNONIEMEN.value],
    )
    response = generator.generate_examples(request)
    return response.examples if response.success else []


def genereer_antoniemen(
    begrip: str,
    definitie: str,
    context_dict: dict[str, list[str]],
    mode: GenerationMode = GenerationMode.RESILIENT,
) -> list[str]:
    """Generate antonyms."""
    generator = get_examples_generator()
    request = ExampleRequest(
        begrip=begrip,
        definitie=definitie,
        context_dict=context_dict,
        example_type=ExampleType.ANTONIEMEN,
        generation_mode=mode,
        max_examples=DEFAULT_EXAMPLE_COUNTS[ExampleType.ANTONIEMEN.value],
    )
    response = generator.generate_examples(request)
    return response.examples if response.success else []


def genereer_toelichting(
    begrip: str,
    definitie: str,
    context_dict: dict[str, list[str]],
    mode: GenerationMode = GenerationMode.RESILIENT,
) -> str:
    """Generate explanation/clarification."""
    generator = get_examples_generator()
    request = ExampleRequest(
        begrip=begrip,
        definitie=definitie,
        context_dict=context_dict,
        example_type=ExampleType.TOELICHTING,
        generation_mode=mode,
        max_examples=1,
    )
    response = generator.generate_examples(request)
    return response.examples[0] if response.success and response.examples else ""


# Batch generation for multiple types
def genereer_alle_voorbeelden(
    begrip: str,
    definitie: str,
    context_dict: dict[str, list[str]],
    mode: str = "RESILIENT",
) -> dict[str, list[str]]:
    """Generate all types of examples in one call."""
    generator = get_examples_generator()

    # Convert string mode to enum
    if isinstance(mode, str):
        mode = GenerationMode(mode.lower())

    results = {}

    # Use central configuration for max_examples per type
    max_examples_per_type = {
        ExampleType.VOORBEELDZINNEN: DEFAULT_EXAMPLE_COUNTS["voorbeeldzinnen"],
        ExampleType.PRAKTIJKVOORBEELDEN: DEFAULT_EXAMPLE_COUNTS["praktijkvoorbeelden"],
        ExampleType.TEGENVOORBEELDEN: DEFAULT_EXAMPLE_COUNTS["tegenvoorbeelden"],
        ExampleType.SYNONIEMEN: DEFAULT_EXAMPLE_COUNTS["synoniemen"],
        ExampleType.ANTONIEMEN: DEFAULT_EXAMPLE_COUNTS["antoniemen"],
        ExampleType.TOELICHTING: DEFAULT_EXAMPLE_COUNTS["toelichting"],
    }

    # Generate all example types
    for example_type in ExampleType:
        request = ExampleRequest(
            begrip=begrip,
            definitie=definitie,
            context_dict=context_dict,
            example_type=example_type,
            generation_mode=mode,
            max_examples=max_examples_per_type.get(
                example_type, 3
            ),  # Gebruik type-specifieke waarde
        )

        response = generator.generate_examples(request)

        if response.success:
            # Voor toelichting: gebruik de eerste (en enige) item als string
            if example_type == ExampleType.TOELICHTING:
                results[example_type.value] = (
                    response.examples[0] if response.examples else ""
                )
            else:
                results[example_type.value] = response.examples
        else:
            # Voor toelichting een lege string, voor andere een lege lijst
            if example_type == ExampleType.TOELICHTING:
                results[example_type.value] = ""
            else:
                results[example_type.value] = []
            logger.warning(
                f"Failed to generate {example_type.value}: {response.error_message}"
            )

    return results


# Async batch generation
async def genereer_alle_voorbeelden_async(
    begrip: str, definitie: str, context_dict: dict[str, list[str]]
) -> dict[str, list[str]]:
    """Generate all types of examples concurrently."""
    generator = get_examples_generator()

    # Create tasks for all example types
    tasks = []
    for example_type in ExampleType:
        request = ExampleRequest(
            begrip=begrip,
            definitie=definitie,
            context_dict=context_dict,
            example_type=example_type,
            generation_mode=GenerationMode.ASYNC,
            max_examples=DEFAULT_EXAMPLE_COUNTS[example_type.value],
        )
        task = asyncio.create_task(generator._generate_async(request))
        tasks.append((example_type, task))

    # Wait for all tasks to complete
    results = {}
    for example_type, task in tasks:
        try:
            examples = await task
            # Voor toelichting: gebruik de eerste (en enige) item als string
            if example_type == ExampleType.TOELICHTING:
                results[example_type.value] = examples[0] if examples else ""
            else:
                results[example_type.value] = examples
        except Exception as e:
            logger.error(f"Failed to generate {example_type.value}: {e}")
            # Voor toelichting een lege string, voor andere een lege lijst
            if example_type == ExampleType.TOELICHTING:
                results[example_type.value] = ""
            else:
                results[example_type.value] = []

    return results


async def test_unified_examples():
    """Test the unified examples system."""
    print("🧪 Testing Unified Examples System")
    print("=" * 40)

    # Test data
    begrip = "identiteitsbehandeling"
    definitie = "Het proces waarbij de identiteit van een persoon wordt vastgesteld, geverifieerd en gevalideerd."
    context_dict = {
        "organisatorisch": ["Strafrechtketen"],
        "juridisch": ["Strafrecht"],
        "wettelijk": ["Wetboek van Strafrecht"],
    }

    generator = get_examples_generator()

    # Test different generation modes
    modes = [GenerationMode.SYNC, GenerationMode.CACHED, GenerationMode.RESILIENT]

    for mode in modes:
        print(f"\n🔄 Testing {mode.value} mode...")

        examples = genereer_voorbeeld_zinnen(begrip, definitie, context_dict, mode)
        print(f"✅ Generated {len(examples)} example sentences")

        if examples:
            print(f"   Example: {examples[0]}")

    # Test batch generation
    print("\n📦 Testing batch generation...")
    all_examples = genereer_alle_voorbeelden(begrip, definitie, context_dict)

    for example_type, examples in all_examples.items():
        print(f"✅ {example_type}: {len(examples)} examples")

    # Show statistics
    stats = generator.get_statistics()
    print("\n📊 Statistics:")
    print(f"   Total generations: {stats['total_generations']}")
    print(f"   Success rate: {stats['success_rate']:.1%}")
    print(f"   Cache hits: {stats['cache_hits']}")


if __name__ == "__main__":
    # Use the same async-safe pattern for testing
    try:
        asyncio.get_running_loop()
        # Already in async context, run in thread
        import concurrent.futures

        def run_test():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(test_unified_examples())
            finally:
                loop.close()

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_test)
            future.result()
    except RuntimeError:
        # No event loop running, safe to use asyncio.run()
        asyncio.run(test_unified_examples())
