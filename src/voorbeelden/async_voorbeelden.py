"""
Async voorbeelden (examples) generation for DefinitieAgent.
Provides concurrent generation of all example types for improved performance.
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass

from utils.async_api import async_cached, async_gpt_call

logger = logging.getLogger(__name__)


@dataclass
class ExampleGenerationResult:
    """Result container for example generation."""

    voorbeeld_zinnen: list[str]
    praktijkvoorbeelden: list[str]
    tegenvoorbeelden: list[str]
    synoniemen: str
    antoniemen: str
    toelichting: str
    generation_time: float
    cache_hits: int
    total_requests: int


class AsyncExampleGenerator:
    """Async generator for all types of examples and related content."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    @async_cached(ttl=1800)  # 30 minutes
    async def _generate_voorbeeld_zinnen(
        self, begrip: str, definitie: str, context_dict: dict[str, list[str]]
    ) -> list[str]:
        """Generate example sentences asynchronously."""
        prompt = (
            f"Geef 2 tot 3 korte voorbeeldzinnen waarin het begrip '{begrip}' "
            "op een duidelijke manier wordt gebruikt.\n"
            "Gebruik onderstaande contexten alleen als achtergrond, maar noem ze niet letterlijk:\n\n"
            f"Organisatorische context: {', '.join(context_dict.get('organisatorisch', [])) or 'geen'}\n"
            f"Juridische context:      {', '.join(context_dict.get('juridisch', [])) or 'geen'}\n"
            f"Wettelijke basis:        {', '.join(context_dict.get('wettelijk', [])) or 'geen'}"
        )

        try:
            response = await async_gpt_call(
                prompt=prompt, model=None, temperature=0.5, max_tokens=200
            )

            # Parse response into separate sentences
            zinnen = []
            for line in response.splitlines():
                zin = line.strip()
                # Remove numbering if present
                if zin and (zin[0].isdigit() or zin.startswith("-")):
                    zin = zin.lstrip("0123456789.- ")
                if zin:
                    zinnen.append(zin)

            return zinnen or [response]

        except Exception as e:
            self.logger.error(f"Error generating example sentences: {e!s}")
            return [f"❌ Fout bij genereren korte voorbeelden: {e}"]

    @async_cached(ttl=1800)  # 30 minutes
    async def _generate_praktijkvoorbeelden(
        self, begrip: str, definitie: str, context_dict: dict[str, list[str]]
    ) -> list[str]:
        """Generate practice examples asynchronously."""
        prompt = (
            f"Geef 2 tot 3 praktijkvoorbeelden waarin het begrip '{begrip}' "
            "in een realistische situatie wordt toegepast.\n"
            "Gebruik onderstaande contexten voor realisme, maar noem ze niet letterlijk:\n\n"
            f"Organisatorische context: {', '.join(context_dict.get('organisatorisch', [])) or 'geen'}\n"
            f"Juridische context:      {', '.join(context_dict.get('juridisch', [])) or 'geen'}\n"
            f"Wettelijke basis:        {', '.join(context_dict.get('wettelijk', [])) or 'geen'}\n\n"
            f"Definitie ter referentie: {definitie}"
        )

        try:
            response = await async_gpt_call(
                prompt=prompt, model="gpt-4", temperature=0.6, max_tokens=400
            )

            # Parse response into separate examples
            voorbeelden = []
            for line in response.splitlines():
                voorbeeld = line.strip()
                # Remove numbering if present
                if voorbeeld and (voorbeeld[0].isdigit() or voorbeeld.startswith("-")):
                    voorbeeld = voorbeeld.lstrip("0123456789.- ")
                if voorbeeld and len(voorbeeld) > 10:
                    voorbeelden.append(voorbeeld)

            return voorbeelden or [response]

        except Exception as e:
            self.logger.error(f"Error generating practice examples: {e!s}")
            return [f"❌ Fout bij genereren praktijkvoorbeelden: {e}"]

    @async_cached(ttl=1800)  # 30 minutes
    async def _generate_tegenvoorbeelden(
        self, begrip: str, definitie: str, context_dict: dict[str, list[str]]
    ) -> list[str]:
        """Generate counter-examples asynchronously."""
        prompt = (
            f"Geef 2 tot 3 tegenvoorbeelden die NIET onder het begrip '{begrip}' vallen, "
            "maar wel verwant zijn of verwarrend kunnen zijn.\n"
            "Leg kort uit waarom elk voorbeeld NIET onder de definitie valt.\n\n"
            f"Definitie: {definitie}\n\n"
            f"Context (alleen voor begrip): {', '.join(context_dict.get('organisatorisch', [])) or 'geen'}"
        )

        try:
            response = await async_gpt_call(
                prompt=prompt, model="gpt-4", temperature=0.6, max_tokens=300
            )

            # Parse response into separate counter-examples
            tegenvoorbeelden = []
            for line in response.splitlines():
                voorbeeld = line.strip()
                # Remove numbering if present
                if voorbeeld and (voorbeeld[0].isdigit() or voorbeeld.startswith("-")):
                    voorbeeld = voorbeeld.lstrip("0123456789.- ")
                if voorbeeld and len(voorbeeld) > 10:
                    tegenvoorbeelden.append(voorbeeld)

            return tegenvoorbeelden or [response]

        except Exception as e:
            self.logger.error(f"Error generating counter-examples: {e!s}")
            return [f"❌ Fout bij genereren tegenvoorbeelden: {e}"]

    @async_cached(ttl=7200)  # 2 hours
    async def _generate_synoniemen(
        self, begrip: str, context_dict: dict[str, list[str]]
    ) -> str:
        """Generate synonyms asynchronously."""
        prompt = (
            f"Geef maximaal 5 synoniemen voor het begrip '{begrip}', "
            f"relevant binnen de context van overheidsgebruik.\n"
            f"Gebruik onderstaande contexten als achtergrond. Geef de synoniemen als een lijst, zonder toelichting:\n\n"
            f"Organisatorische context: {', '.join(context_dict.get('organisatorisch', [])) or 'geen'}\n"
            f"Juridische context:      {', '.join(context_dict.get('juridisch', [])) or 'geen'}\n"
            f"Wettelijke basis:        {', '.join(context_dict.get('wettelijk', [])) or 'geen'}"
        )

        try:
            return await async_gpt_call(
                prompt=prompt, model="gpt-4", temperature=0.2, max_tokens=150
            )
        except Exception as e:
            self.logger.error(f"Error generating synonyms: {e!s}")
            return f"❌ Fout bij genereren synoniemen: {e}"

    @async_cached(ttl=7200)  # 2 hours
    async def _generate_antoniemen(
        self, begrip: str, context_dict: dict[str, list[str]]
    ) -> str:
        """Generate antonyms asynchronously."""
        prompt = (
            f"Geef maximaal 5 antoniemen voor het begrip '{begrip}', "
            f"binnen de context van overheidsgebruik.\n"
            f"Gebruik onderstaande contexten alleen als achtergrond. Geef de antoniemen als een lijst, zonder toelichting:\n\n"
            f"Organisatorische context: {', '.join(context_dict.get('organisatorisch', [])) or 'geen'}\n"
            f"Juridische context:      {', '.join(context_dict.get('juridisch', [])) or 'geen'}\n"
            f"Wettelijke basis:        {', '.join(context_dict.get('wettelijk', [])) or 'geen'}"
        )

        try:
            return await async_gpt_call(
                prompt=prompt, model="gpt-4", temperature=0.2, max_tokens=150
            )
        except Exception as e:
            self.logger.error(f"Error generating antonyms: {e!s}")
            return f"❌ Fout bij genereren antoniemen: {e}"

    @async_cached(ttl=3600)  # 1 hour
    async def _generate_toelichting(
        self, begrip: str, context_dict: dict[str, list[str]]
    ) -> str:
        """Generate explanation asynchronously."""
        prompt = (
            f"Geef een korte toelichting op de betekenis en toepassing van het begrip '{begrip}', "
            f"zoals het zou kunnen voorkomen in overheidsdocumenten.\n"
            f"Gebruik de contexten hieronder alleen als achtergrond en noem ze niet letterlijk:\n\n"
            f"Organisatorische context: {', '.join(context_dict.get('organisatorisch', [])) or 'geen'}\n"
            f"Juridische context:      {', '.join(context_dict.get('juridisch', [])) or 'geen'}\n"
            f"Wettelijke basis:        {', '.join(context_dict.get('wettelijk', [])) or 'geen'}"
        )

        try:
            return await async_gpt_call(
                prompt=prompt, model="gpt-4", temperature=0.3, max_tokens=200
            )
        except Exception as e:
            self.logger.error(f"Error generating explanation: {e!s}")
            return f"❌ Fout bij genereren toelichting: {e}"

    async def generate_all_examples(
        self,
        begrip: str,
        definitie: str,
        context_dict: dict[str, list[str]],
        progress_callback: Callable[[str, int, int], None] | None = None,
    ) -> ExampleGenerationResult:
        """
        Generate all types of examples concurrently.

        Args:
            begrip: Term to generate examples for
            definitie: Definition of the term
            context_dict: Context information
            progress_callback: Optional callback for progress updates

        Returns:
            ExampleGenerationResult with all generated content
        """
        import time

        start_time = time.time()

        self.logger.info(f"Starting concurrent example generation for '{begrip}'")

        # Create all tasks
        tasks = {
            "voorbeeld_zinnen": self._generate_voorbeeld_zinnen(
                begrip, definitie, context_dict
            ),
            "praktijkvoorbeelden": self._generate_praktijkvoorbeelden(
                begrip, definitie, context_dict
            ),
            "tegenvoorbeelden": self._generate_tegenvoorbeelden(
                begrip, definitie, context_dict
            ),
            "synoniemen": self._generate_synoniemen(begrip, context_dict),
            "antoniemen": self._generate_antoniemen(begrip, context_dict),
            "toelichting": self._generate_toelichting(begrip, context_dict),
        }

        # Execute tasks concurrently with progress tracking
        results = {}
        completed = 0
        total = len(tasks)

        for name, coro in tasks.items():
            if progress_callback:
                progress_callback(f"Generating {name}...", completed, total)

            try:
                results[name] = await coro
                completed += 1

                if progress_callback:
                    progress_callback(f"Completed {name}", completed, total)

                self.logger.debug(f"Completed {name} ({completed}/{total})")

            except Exception as e:
                self.logger.error(f"Error generating {name}: {e!s}")
                results[name] = f"❌ Error: {e!s}"
                completed += 1

                if progress_callback:
                    progress_callback(f"Error in {name}", completed, total)

        generation_time = time.time() - start_time

        self.logger.info(f"Completed all example generation in {generation_time:.2f}s")

        return ExampleGenerationResult(
            voorbeeld_zinnen=results.get("voorbeeld_zinnen", []),
            praktijkvoorbeelden=results.get("praktijkvoorbeelden", []),
            tegenvoorbeelden=results.get("tegenvoorbeelden", []),
            synoniemen=results.get("synoniemen", ""),
            antoniemen=results.get("antoniemen", ""),
            toelichting=results.get("toelichting", ""),
            generation_time=generation_time,
            cache_hits=0,
            total_requests=total,
        )


# Global async example generator
_async_generator: AsyncExampleGenerator | None = None


def get_async_generator() -> AsyncExampleGenerator:
    """Get or create global async example generator."""
    global _async_generator
    if _async_generator is None:
        _async_generator = AsyncExampleGenerator()
    return _async_generator


async def async_generate_all_examples(
    begrip: str,
    definitie: str,
    context_dict: dict[str, list[str]],
    progress_callback: Callable[[str, int, int], None] | None = None,
) -> ExampleGenerationResult:
    """
    Convenience function for async example generation.

    Args:
        begrip: Term to generate examples for
        definitie: Definition of the term
        context_dict: Context information
        progress_callback: Optional progress callback

    Returns:
        ExampleGenerationResult with all generated content
    """
    generator = get_async_generator()
    return await generator.generate_all_examples(
        begrip=begrip,
        definitie=definitie,
        context_dict=context_dict,
        progress_callback=progress_callback,
    )


# Individual async functions for compatibility
async def async_genereer_voorbeeld_zinnen(
    begrip: str, definitie: str, context_dict: dict[str, list[str]]
) -> list[str]:
    """Generate example sentences asynchronously."""
    generator = get_async_generator()
    return await generator._generate_voorbeeld_zinnen(begrip, definitie, context_dict)


async def async_genereer_praktijkvoorbeelden(
    begrip: str, definitie: str, context_dict: dict[str, list[str]]
) -> list[str]:
    """Generate practice examples asynchronously."""
    generator = get_async_generator()
    return await generator._generate_praktijkvoorbeelden(
        begrip, definitie, context_dict
    )


async def async_genereer_tegenvoorbeelden(
    begrip: str, definitie: str, context_dict: dict[str, list[str]]
) -> list[str]:
    """Generate counter-examples asynchronously."""
    generator = get_async_generator()
    return await generator._generate_tegenvoorbeelden(begrip, definitie, context_dict)


async def async_genereer_synoniemen(
    begrip: str, context_dict: dict[str, list[str]]
) -> str:
    """Generate synonyms asynchronously."""
    generator = get_async_generator()
    return await generator._generate_synoniemen(begrip, context_dict)


async def async_genereer_antoniemen(
    begrip: str, context_dict: dict[str, list[str]]
) -> str:
    """Generate antonyms asynchronously."""
    generator = get_async_generator()
    return await generator._generate_antoniemen(begrip, context_dict)


async def async_genereer_toelichting(
    begrip: str, context_dict: dict[str, list[str]]
) -> str:
    """Generate explanation asynchronously."""
    generator = get_async_generator()
    return await generator._generate_toelichting(begrip, context_dict)
