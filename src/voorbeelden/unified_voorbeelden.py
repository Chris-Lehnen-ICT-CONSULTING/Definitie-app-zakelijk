"""
Geünificeerd Voorbeeld Generatie Systeem voor DefinitieAgent.

Consolideert synchrone, asynchrone, en gecachte voorbeeld generatie
in één uniform interface voor alle typen voorbeelden.
"""

import asyncio  # Asynchrone programmering voor parallelle voorbeeld generatie
import logging  # Logging faciliteiten voor debug en monitoring
import re  # Reguliere expressies voor tekst processing
from dataclasses import (  # Dataklassen voor gestructureerde request/response data
    dataclass,
)
from datetime import datetime  # Datum en tijd functionaliteit voor timestamps, timezone
from enum import Enum  # Enumeraties voor voorbeeld types en modi
from typing import Any  # Type hints voor betere code documentatie

from prompt_builder.prompt_builder import stuur_prompt_naar_gpt  # GPT prompt interface
from utils.cache import cached  # Caching decorator voor performance optimalisatie

# Importeer resilience en caching systemen voor robuuste voorbeeld generatie
from utils.integrated_resilience import (  # Volledig resilience systeem
    with_full_resilience,
)
from utils.smart_rate_limiter import (  # Smart rate limiting voor API calls
    RequestPriority,
)

logger = logging.getLogger(__name__)  # Logger instantie voor unified voorbeelden module


class ExampleType(Enum):
    """Types van voorbeelden die gegenereerd kunnen worden."""

    SENTENCE = "sentence"  # Voorbeeldzinnen met het begrip
    PRACTICAL = "practical"  # Praktische gebruiksvoorbeelden
    COUNTER = "counter"  # Tegenvoorbeelden ter verduidelijking
    SYNONYMS = "synonyms"  # Synoniemen van het begrip
    ANTONYMS = "antonyms"  # Antoniemen van het begrip
    EXPLANATION = "explanation"  # Uitgebreide toelichting


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
    max_examples: int = 5  # Default naar 5 voor synoniemen/antoniemen
    temperature: float = 0.5
    model: str = "gpt-4"


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

    def generate_examples(self, request: ExampleRequest) -> ExampleResponse:
        """Generate examples based on request configuration."""
        start_time = datetime.now(timezone.utc)

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
            generation_time = (datetime.now(timezone.utc) - start_time).total_seconds()

            return ExampleResponse(
                examples=examples, success=True, generation_time=generation_time
            )

        except Exception as e:
            self.error_count += 1
            logger.error(f"Example generation failed: {e}")

            return ExampleResponse(examples=[], success=False, error_message=str(e))

    def _generate_sync(self, request: ExampleRequest) -> list[str]:
        """Synchronous example generation."""
        prompt = self._build_prompt(request)

        try:
            response = stuur_prompt_naar_gpt(
                prompt=prompt,
                model=request.model,
                temperatuur=request.temperature,
                max_tokens=300,
            )
            return self._parse_response(response)
        except Exception as e:
            msg = f"Synchronous generation failed: {e}"
            raise RuntimeError(msg)

    async def _generate_async(self, request: ExampleRequest) -> list[str]:
        """Asynchronous example generation."""
        prompt = self._build_prompt(request)

        try:
            # Use async wrapper for GPT call
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: stuur_prompt_naar_gpt(
                    prompt=prompt,
                    model=request.model,
                    temperatuur=request.temperature,
                    max_tokens=300,
                ),
            )
            return self._parse_response(response)
        except Exception as e:
            msg = f"Asynchronous generation failed: {e}"
            raise RuntimeError(msg)

    @cached(ttl=3600)  # Cache for 1 hour
    def _generate_cached(self, request: ExampleRequest) -> list[str]:
        """Cached example generation."""
        self.cache_hits += 1
        return self._generate_sync(request)

    async def _generate_resilient(self, request: ExampleRequest) -> list[str]:
        """Resilient example generation with retry logic and rate limiting."""
        # Route to specific resilient method based on example type
        if request.example_type == ExampleType.SENTENCE:
            return await self._generate_resilient_sentence(request)
        if request.example_type == ExampleType.PRACTICAL:
            return await self._generate_resilient_practical(request)
        if request.example_type == ExampleType.COUNTER:
            return await self._generate_resilient_counter(request)
        if request.example_type == ExampleType.SYNONYMS:
            return await self._generate_resilient_synonyms(request)
        if request.example_type == ExampleType.ANTONYMS:
            return await self._generate_resilient_antonyms(request)
        if request.example_type == ExampleType.EXPLANATION:
            return await self._generate_resilient_explanation(request)
        msg = f"Unknown example type: {request.example_type}"
        raise ValueError(msg)

    @with_full_resilience(
        endpoint_name="examples_generation_sentence",
        priority=RequestPriority.NORMAL,
        timeout=10.0,
        model="gpt-4",
        expected_tokens=200,
    )
    async def _generate_resilient_sentence(self, request: ExampleRequest) -> list[str]:
        """Resilient sentence example generation."""
        return await self._generate_resilient_common(request)

    @with_full_resilience(
        endpoint_name="examples_generation_practical",
        priority=RequestPriority.NORMAL,
        timeout=10.0,
        model="gpt-4",
        expected_tokens=200,
    )
    async def _generate_resilient_practical(self, request: ExampleRequest) -> list[str]:
        """Resilient practical example generation."""
        return await self._generate_resilient_common(request)

    @with_full_resilience(
        endpoint_name="examples_generation_counter",
        priority=RequestPriority.NORMAL,
        timeout=10.0,
        model="gpt-4",
        expected_tokens=200,
    )
    async def _generate_resilient_counter(self, request: ExampleRequest) -> list[str]:
        """Resilient counter example generation."""
        return await self._generate_resilient_common(request)

    @with_full_resilience(
        endpoint_name="examples_generation_synonyms",
        priority=RequestPriority.NORMAL,
        timeout=10.0,
        model="gpt-4",
        expected_tokens=200,
    )
    async def _generate_resilient_synonyms(self, request: ExampleRequest) -> list[str]:
        """Resilient synonyms generation."""
        return await self._generate_resilient_common(request)

    @with_full_resilience(
        endpoint_name="examples_generation_antonyms",
        priority=RequestPriority.NORMAL,
        timeout=10.0,
        model="gpt-4",
        expected_tokens=200,
    )
    async def _generate_resilient_antonyms(self, request: ExampleRequest) -> list[str]:
        """Resilient antonyms generation."""
        return await self._generate_resilient_common(request)

    @with_full_resilience(
        endpoint_name="examples_generation_explanation",
        priority=RequestPriority.NORMAL,
        timeout=10.0,
        model="gpt-4",
        expected_tokens=200,
    )
    async def _generate_resilient_explanation(
        self, request: ExampleRequest
    ) -> list[str]:
        """Resilient explanation generation."""
        prompt = self._build_prompt(request)

        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: stuur_prompt_naar_gpt(
                    prompt=prompt,
                    model=request.model,
                    temperatuur=request.temperature,
                    max_tokens=300,
                ),
            )
            # Voor explanation, return de hele response als één item
            return [response.strip()] if response.strip() else []
        except Exception as e:
            msg = f"Resilient generation failed: {e}"
            raise RuntimeError(msg)

    async def _generate_resilient_common(self, request: ExampleRequest) -> list[str]:
        """Common resilient generation logic."""
        prompt = self._build_prompt(request)

        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: stuur_prompt_naar_gpt(
                    prompt=prompt,
                    model=request.model,
                    temperatuur=request.temperature,
                    max_tokens=300,
                ),
            )
            return self._parse_response(response)
        except Exception as e:
            msg = f"Resilient generation failed: {e}"
            raise RuntimeError(msg)

    def _build_prompt(self, request: ExampleRequest) -> str:
        """Build appropriate prompt based on example type."""
        begrip = request.begrip
        definitie = request.definitie
        context_dict = request.context_dict

        # Context formatting
        context_text = self._format_context(context_dict)

        # Type-specific prompts
        if request.example_type == ExampleType.SENTENCE:
            return f"""
Geef {request.max_examples} korte voorbeeldzinnen waarin het begrip '{begrip}'
op een duidelijke manier wordt gebruikt. De zinnen moeten passen binnen de gegeven context.

Definitie: {definitie}

Context:
{context_text}

Integreer de context natuurlijk in de voorbeeldzinnen. Als er een organisatie of domein
is opgegeven, gebruik deze in de zinnen. Geef alleen de voorbeeldzinnen, elk op een nieuwe regel.
"""

        if request.example_type == ExampleType.PRACTICAL:
            return f"""
Geef {request.max_examples} praktische voorbeelden waarbij het begrip '{begrip}'
van toepassing is in de praktijk binnen de gegeven context.

Definitie: {definitie}

Context:
{context_text}

Geef concrete, herkenbare situaties uit de opgegeven organisatie/domein waarin dit begrip
gebruikt wordt. Maak de voorbeelden specifiek voor de context.
"""

        if request.example_type == ExampleType.COUNTER:
            return f"""
Geef {request.max_examples} tegenvoorbeelden die NIET onder het begrip '{begrip}' vallen,
maar wel relevant zijn voor de gegeven context.

Definitie: {definitie}

Context:
{context_text}

Geef voorbeelden uit dezelfde organisatie/domein die lijken op '{begrip}' maar er niet
onder vallen. Leg kort uit waarom deze voorbeelden niet onder de definitie vallen.
"""

        if request.example_type == ExampleType.SYNONYMS:
            return f"""
Geef {request.max_examples} synoniemen of verwante termen voor '{begrip}' die gebruikt
worden binnen de gegeven context.

Definitie: {definitie}

Context:
{context_text}

Geef synoniemen die specifiek in deze organisatie/domein gebruikt worden.
Geef alleen de synoniemen, elk op een nieuwe regel.
"""

        if request.example_type == ExampleType.ANTONYMS:
            return f"""
Geef {request.max_examples} antoniemen of tegengestelde termen voor '{begrip}'
die relevant zijn binnen de gegeven context.

Definitie: {definitie}

Context:
{context_text}

Geef antoniemen die in deze organisatie/domein gebruikt worden.
Geef alleen de antoniemen, elk op een nieuwe regel.
"""

        if request.example_type == ExampleType.EXPLANATION:
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

    def _parse_response(self, response: str) -> list[str]:
        """Parse GPT response into list of examples."""
        if not response:
            return []

        # Split on lines and clean up
        lines = response.strip().split("\n")
        examples = []

        for line in lines:
            # Remove numbering and bullets
            cleaned = re.sub(r"^\s*(?:\d+\.|-|\*)\s*", "", line).strip()
            if cleaned and not cleaned.startswith("Voorbeelden:"):
                examples.append(cleaned)

        # Fallback: return whole response if no lines found
        return examples if examples else [response.strip()]

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
        example_type=ExampleType.SENTENCE,
        generation_mode=mode,
        max_examples=3,  # Expliciet 3 voorbeeldzinnen
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
        example_type=ExampleType.PRACTICAL,
        generation_mode=mode,
        max_examples=3,  # Expliciet 3 praktijkvoorbeelden
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
        example_type=ExampleType.COUNTER,
        generation_mode=mode,
        max_examples=3,  # Expliciet 3 tegenvoorbeelden
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
        example_type=ExampleType.SYNONYMS,
        generation_mode=mode,
        max_examples=5,  # Expliciet 5 synoniemen
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
        example_type=ExampleType.ANTONYMS,
        generation_mode=mode,
        max_examples=5,  # Expliciet 5 antoniemen
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
        example_type=ExampleType.EXPLANATION,
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

    # Define max_examples per type
    max_examples_per_type = {
        ExampleType.SENTENCE: 3,
        ExampleType.PRACTICAL: 3,
        ExampleType.COUNTER: 3,
        ExampleType.SYNONYMS: 5,
        ExampleType.ANTONYMS: 5,
        ExampleType.EXPLANATION: 1,
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
            results[example_type.value] = response.examples
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
        )
        task = asyncio.create_task(generator._generate_async(request))
        tasks.append((example_type, task))

    # Wait for all tasks to complete
    results = {}
    for example_type, task in tasks:
        try:
            examples = await task
            results[example_type.value] = examples
        except Exception as e:
            logger.error(f"Failed to generate {example_type.value}: {e}")
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
