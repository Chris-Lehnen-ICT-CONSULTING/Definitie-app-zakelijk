"""
Unified Examples Generation System for DefinitieAgent.
Consolidates synchronous, asynchronous, and cached example generation.
"""

import asyncio
import logging
from typing import List, Optional, Dict, Any, Union
from dataclasses import dataclass
from enum import Enum
import re
from datetime import datetime

# Import resilience and caching systems
from utils.integrated_resilience import with_full_resilience
from utils.smart_rate_limiter import RequestPriority
from utils.cache import cached
from prompt_builder.prompt_builder import stuur_prompt_naar_gpt

logger = logging.getLogger(__name__)


class ExampleType(Enum):
    """Types of examples that can be generated."""
    SENTENCE = "sentence"
    PRACTICAL = "practical"
    COUNTER = "counter"
    SYNONYMS = "synonyms"
    ANTONYMS = "antonyms"
    EXPLANATION = "explanation"


class GenerationMode(Enum):
    """Generation modes for different performance/reliability needs."""
    SYNC = "sync"            # Synchronous generation
    ASYNC = "async"          # Asynchronous generation
    CACHED = "cached"        # Cached generation
    RESILIENT = "resilient"  # With full resilience


@dataclass
class ExampleRequest:
    """Request for example generation."""
    begrip: str
    definitie: str
    context_dict: Dict[str, List[str]]
    example_type: ExampleType
    generation_mode: GenerationMode = GenerationMode.RESILIENT
    max_examples: int = 3
    temperature: float = 0.5
    model: str = "gpt-4"


@dataclass
class ExampleResponse:
    """Response from example generation."""
    examples: List[str]
    success: bool
    error_message: Optional[str] = None
    generation_time: Optional[float] = None
    cached: bool = False


class UnifiedExamplesGenerator:
    """Unified system for generating all types of examples."""
    
    def __init__(self):
        self.generation_count = 0
        self.error_count = 0
        self.cache_hits = 0
        
    def generate_examples(self, request: ExampleRequest) -> ExampleResponse:
        """Generate examples based on request configuration."""
        start_time = datetime.now()
        
        try:
            # Route to appropriate generation method
            if request.generation_mode == GenerationMode.SYNC:
                examples = self._generate_sync(request)
            elif request.generation_mode == GenerationMode.ASYNC:
                examples = asyncio.run(self._generate_async(request))
            elif request.generation_mode == GenerationMode.CACHED:
                examples = self._generate_cached(request)
            elif request.generation_mode == GenerationMode.RESILIENT:
                examples = asyncio.run(self._generate_resilient(request))
            else:
                raise ValueError(f"Unsupported generation mode: {request.generation_mode}")
            
            self.generation_count += 1
            generation_time = (datetime.now() - start_time).total_seconds()
            
            return ExampleResponse(
                examples=examples,
                success=True,
                generation_time=generation_time
            )
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"Example generation failed: {e}")
            
            return ExampleResponse(
                examples=[],
                success=False,
                error_message=str(e)
            )
    
    def _generate_sync(self, request: ExampleRequest) -> List[str]:
        """Synchronous example generation."""
        prompt = self._build_prompt(request)
        
        try:
            response = stuur_prompt_naar_gpt(
                prompt=prompt,
                model=request.model,
                temperatuur=request.temperature,
                max_tokens=300
            )
            return self._parse_response(response)
        except Exception as e:
            raise RuntimeError(f"Synchronous generation failed: {e}")
    
    async def _generate_async(self, request: ExampleRequest) -> List[str]:
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
                    max_tokens=300
                )
            )
            return self._parse_response(response)
        except Exception as e:
            raise RuntimeError(f"Asynchronous generation failed: {e}")
    
    @cached(ttl=3600)  # Cache for 1 hour
    def _generate_cached(self, request: ExampleRequest) -> List[str]:
        """Cached example generation."""
        self.cache_hits += 1
        return self._generate_sync(request)
    
    @with_full_resilience(
        endpoint_name="examples_generation",
        priority=RequestPriority.NORMAL,
        timeout=30.0,
        model="gpt-4",
        expected_tokens=200
    )
    async def _generate_resilient(self, request: ExampleRequest) -> List[str]:
        """Resilient example generation with retry logic and rate limiting."""
        prompt = self._build_prompt(request)
        
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: stuur_prompt_naar_gpt(
                    prompt=prompt,
                    model=request.model,
                    temperatuur=request.temperature,
                    max_tokens=300
                )
            )
            return self._parse_response(response)
        except Exception as e:
            raise RuntimeError(f"Resilient generation failed: {e}")
    
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
op een duidelijke manier wordt gebruikt.

Definitie: {definitie}

Context (gebruik alleen als achtergrond, noem niet letterlijk):
{context_text}

Geef alleen de voorbeeldzinnen, elk op een nieuwe regel.
"""
        
        elif request.example_type == ExampleType.PRACTICAL:
            return f"""
Geef {request.max_examples} praktische voorbeelden waarbij het begrip '{begrip}' 
van toepassing is in de praktijk.

Definitie: {definitie}

Context:
{context_text}

Geef concrete, herkenbare situaties waarin dit begrip gebruikt wordt.
"""
        
        elif request.example_type == ExampleType.COUNTER:
            return f"""
Geef {request.max_examples} tegenvoorbeelden die NIET onder het begrip '{begrip}' vallen.

Definitie: {definitie}

Context:
{context_text}

Leg kort uit waarom deze voorbeelden niet onder de definitie vallen.
"""
        
        elif request.example_type == ExampleType.SYNONYMS:
            return f"""
Geef {request.max_examples} synoniemen of verwante termen voor '{begrip}'.

Definitie: {definitie}

Context:
{context_text}

Geef alleen de synoniemen, elk op een nieuwe regel.
"""
        
        elif request.example_type == ExampleType.ANTONYMS:
            return f"""
Geef {request.max_examples} antoniemen of tegengestelde termen voor '{begrip}'.

Definitie: {definitie}

Context:
{context_text}

Geef alleen de antoniemen, elk op een nieuwe regel.
"""
        
        elif request.example_type == ExampleType.EXPLANATION:
            return f"""
Geef een korte, heldere toelichting bij het begrip '{begrip}'.

Definitie: {definitie}

Context:
{context_text}

Leg uit wat dit begrip betekent in de praktijk en waarom het belangrijk is.
"""
        
        else:
            raise ValueError(f"Unsupported example type: {request.example_type}")
    
    def _format_context(self, context_dict: Dict[str, List[str]]) -> str:
        """Format context dictionary for prompts."""
        context_lines = []
        
        for key, values in context_dict.items():
            if values:
                context_lines.append(f"{key.capitalize()}: {', '.join(values)}")
            else:
                context_lines.append(f"{key.capitalize()}: geen")
        
        return "\n".join(context_lines)
    
    def _parse_response(self, response: str) -> List[str]:
        """Parse GPT response into list of examples."""
        if not response:
            return []
        
        # Split on lines and clean up
        lines = response.strip().split('\n')
        examples = []
        
        for line in lines:
            # Remove numbering and bullets
            cleaned = re.sub(r'^\s*(?:\d+\.|-|\*)\s*', '', line).strip()
            if cleaned and not cleaned.startswith('Voorbeelden:'):
                examples.append(cleaned)
        
        # Fallback: return whole response if no lines found
        return examples if examples else [response.strip()]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get generation statistics."""
        return {
            'total_generations': self.generation_count,
            'total_errors': self.error_count,
            'cache_hits': self.cache_hits,
            'success_rate': (self.generation_count - self.error_count) / self.generation_count if self.generation_count > 0 else 0
        }


# Global generator instance
_generator: Optional[UnifiedExamplesGenerator] = None


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
    context_dict: Dict[str, List[str]],
    mode: GenerationMode = GenerationMode.RESILIENT
) -> List[str]:
    """Generate example sentences."""
    generator = get_examples_generator()
    request = ExampleRequest(
        begrip=begrip,
        definitie=definitie,
        context_dict=context_dict,
        example_type=ExampleType.SENTENCE,
        generation_mode=mode
    )
    response = generator.generate_examples(request)
    return response.examples if response.success else []


def genereer_praktijkvoorbeelden(
    begrip: str,
    definitie: str,
    context_dict: Dict[str, List[str]],
    mode: GenerationMode = GenerationMode.RESILIENT
) -> List[str]:
    """Generate practical examples."""
    generator = get_examples_generator()
    request = ExampleRequest(
        begrip=begrip,
        definitie=definitie,
        context_dict=context_dict,
        example_type=ExampleType.PRACTICAL,
        generation_mode=mode
    )
    response = generator.generate_examples(request)
    return response.examples if response.success else []


def genereer_tegenvoorbeelden(
    begrip: str,
    definitie: str,
    context_dict: Dict[str, List[str]],
    mode: GenerationMode = GenerationMode.RESILIENT
) -> List[str]:
    """Generate counter examples."""
    generator = get_examples_generator()
    request = ExampleRequest(
        begrip=begrip,
        definitie=definitie,
        context_dict=context_dict,
        example_type=ExampleType.COUNTER,
        generation_mode=mode
    )
    response = generator.generate_examples(request)
    return response.examples if response.success else []


def genereer_synoniemen(
    begrip: str,
    definitie: str,
    context_dict: Dict[str, List[str]],
    mode: GenerationMode = GenerationMode.RESILIENT
) -> List[str]:
    """Generate synonyms."""
    generator = get_examples_generator()
    request = ExampleRequest(
        begrip=begrip,
        definitie=definitie,
        context_dict=context_dict,
        example_type=ExampleType.SYNONYMS,
        generation_mode=mode
    )
    response = generator.generate_examples(request)
    return response.examples if response.success else []


def genereer_antoniemen(
    begrip: str,
    definitie: str,
    context_dict: Dict[str, List[str]],
    mode: GenerationMode = GenerationMode.RESILIENT
) -> List[str]:
    """Generate antonyms."""
    generator = get_examples_generator()
    request = ExampleRequest(
        begrip=begrip,
        definitie=definitie,
        context_dict=context_dict,
        example_type=ExampleType.ANTONYMS,
        generation_mode=mode
    )
    response = generator.generate_examples(request)
    return response.examples if response.success else []


def genereer_toelichting(
    begrip: str,
    definitie: str,
    context_dict: Dict[str, List[str]],
    mode: GenerationMode = GenerationMode.RESILIENT
) -> str:
    """Generate explanation/clarification."""
    generator = get_examples_generator()
    request = ExampleRequest(
        begrip=begrip,
        definitie=definitie,
        context_dict=context_dict,
        example_type=ExampleType.EXPLANATION,
        generation_mode=mode,
        max_examples=1
    )
    response = generator.generate_examples(request)
    return response.examples[0] if response.success and response.examples else ""


# Batch generation for multiple types
def genereer_alle_voorbeelden(
    begrip: str,
    definitie: str,
    context_dict: Dict[str, List[str]],
    mode: GenerationMode = GenerationMode.RESILIENT
) -> Dict[str, List[str]]:
    """Generate all types of examples in one call."""
    generator = get_examples_generator()
    
    results = {}
    
    # Generate all example types
    for example_type in ExampleType:
        request = ExampleRequest(
            begrip=begrip,
            definitie=definitie,
            context_dict=context_dict,
            example_type=example_type,
            generation_mode=mode
        )
        
        response = generator.generate_examples(request)
        
        if response.success:
            results[example_type.value] = response.examples
        else:
            results[example_type.value] = []
            logger.warning(f"Failed to generate {example_type.value}: {response.error_message}")
    
    return results


# Async batch generation
async def genereer_alle_voorbeelden_async(
    begrip: str,
    definitie: str,
    context_dict: Dict[str, List[str]]
) -> Dict[str, List[str]]:
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
            generation_mode=GenerationMode.ASYNC
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
        "wettelijk": ["Wetboek van Strafrecht"]
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
    print(f"\n📊 Statistics:")
    print(f"   Total generations: {stats['total_generations']}")
    print(f"   Success rate: {stats['success_rate']:.1%}")
    print(f"   Cache hits: {stats['cache_hits']}")


if __name__ == "__main__":
    asyncio.run(test_unified_examples())
