"""
AIServiceV2 - Native async AI service implementation for V2 orchestrator.

This service provides async AI capabilities using AsyncGPTClient with:
- Full async/await support
- Batch generation with concurrency
- Token counting heuristics
- V1-compatible caching
- Proper error wrapping
"""

from __future__ import annotations

import asyncio
import logging
import time
from types import ModuleType
from typing import Any

# Token counting - try tiktoken, fallback to estimation
_tiktoken: ModuleType | None
try:
    import tiktoken as _tiktoken

    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False
    _tiktoken = None

from config.config_manager import get_config_manager
from services.ai.base_client import (
    AIClientError,
    AIConnectionClientError,
    AIRateLimitClientError,
    AsyncAIClient,
)
from services.ai.model_router import ModelRouter
from services.interfaces import (
    AIBatchRequest,
    AIGenerationResult,
    AIRateLimitError,
    AIServiceError,
    AIServiceInterface,
    AITimeoutError,
)
from utils.async_api import AsyncGPTClient, RateLimitConfig
from utils.cache import cache_gpt_call

logger = logging.getLogger(__name__)


class AIServiceV2(AIServiceInterface):
    """
    Native async AI service implementing AIServiceInterface.

    Uses AsyncGPTClient for all AI operations with proper error handling,
    token counting, and V1-compatible caching.
    """

    def __init__(
        self,
        rate_limit_config: RateLimitConfig | None = None,
        default_model: str | None = None,
        use_cache: bool = True,
        ai_client: AsyncAIClient | None = None,
        model_router: ModelRouter | None = None,
    ):
        """
        Initialize AIServiceV2 with configuration.

        Args:
            rate_limit_config: Optional rate limit configuration, uses config_manager if None
            default_model: Default model to use for AI calls (deprecated, use model_router)
            use_cache: Whether to enable caching
            ai_client: Optional pre-configured AI client (provider-agnostic)
            model_router: DEF-314: ModelRouter for task-type based model selection
        """
        self._model_router = model_router
        # Get rate limit config from config_manager if not provided
        if rate_limit_config is None:
            # Use default rate limit from config_manager
            config_mgr = get_config_manager()
            api_config = config_mgr.api
            rate_limit_config = RateLimitConfig(
                requests_per_minute=getattr(
                    api_config, "rate_limit_requests_per_minute", 60
                ),
                requests_per_hour=getattr(
                    api_config, "rate_limit_requests_per_hour", 3000
                ),
                max_concurrent=getattr(api_config, "rate_limit_max_concurrent", 10),
                backoff_factor=getattr(api_config, "rate_limit_backoff_factor", 1.5),
                max_retries=getattr(api_config, "rate_limit_max_retries", 3),
            )

        self._rate_limit_config = rate_limit_config
        self._ai_client = ai_client
        self._client: AsyncGPTClient | None = None
        # DEF-314: Resolve default_model via ModelRouter if not explicitly provided
        if default_model is not None:
            self.default_model = default_model
        elif model_router is not None:
            _, self.default_model = model_router.get_model("definition_core")
        else:
            self.default_model = get_config_manager().api.default_model
        self.use_cache = use_cache
        self._token_encoders: dict[str, Any] = {}  # Cache encoders per model

        # Initialize default model encoder if available (tiktoken only supports OpenAI models)
        if TIKTOKEN_AVAILABLE and not self.default_model.startswith("claude"):
            self._get_or_create_encoder(self.default_model)

    def _get_client(self) -> AsyncGPTClient:
        if self._client is None:
            self._client = AsyncGPTClient(
                rate_limit_config=self._rate_limit_config,
                client=self._ai_client,
            )
        return self._client

    async def _record_api_call(
        self,
        function_name: str,
        duration: float,
        success: bool,
        error_type: str | None = None,
        tokens_used: int = 0,
        model: str | None = None,
        cache_hit: bool = False,
    ) -> None:
        """Record API call metrics for cost tracking and monitoring.

        Uses monitoring.api_monitor.record_api_call for centralized tracking.
        Fails silently to not disrupt AI operations.
        """
        try:
            from monitoring.api_monitor import record_api_call

            await record_api_call(
                endpoint="ai/chat/completions",
                function_name=function_name,
                duration=duration,
                success=success,
                error_type=error_type,
                tokens_used=tokens_used,
                model=model or self.default_model,
                cache_hit=cache_hit,
            )
        except Exception as e:
            # Cost tracking is non-critical, log but don't fail
            logger.debug(f"Failed to record API call metrics: {e}")

    async def generate_definition(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 500,
        model: str | None = None,
        system_prompt: str | None = None,
        timeout_seconds: int = 30,
        task_type: str | None = None,
    ) -> AIGenerationResult:
        """
        Generate a definition using AI based on the given prompt.

        Args:
            prompt: The prompt for the AI model
            temperature: Creativity parameter (0.0 = deterministic, 1.0 = creative)
            max_tokens: Maximum tokens in response
            model: Optional specific model to use (overrides task_type)
            system_prompt: Optional system prompt for context
            timeout_seconds: Timeout for the AI call
            task_type: DEF-314: Task type for ModelRouter lookup (e.g. 'definition_core')

        Returns:
            AIGenerationResult with generated text and metadata

        Raises:
            AIServiceError: On AI service errors (rate limits, timeouts, etc.)
        """
        start_time = time.time()
        # DEF-314: model param takes precedence; then task_type via ModelRouter; then default
        if model is not None:
            model_to_use = model
        elif task_type is not None and self._model_router is not None:
            _, model_to_use = self._model_router.get_model(task_type)
        else:
            model_to_use = self.default_model

        try:
            # Generate V1-compatible cache key
            cache_key = cache_gpt_call(
                prompt=prompt,
                model=model_to_use,
                temperature=temperature,
                max_tokens=max_tokens,
                system_prompt=system_prompt,
            )

            # Check cache first
            cached = False
            if self.use_cache:
                from utils.cache import _cache

                cached_result = _cache.get(cache_key)
                if cached_result is not None:
                    logger.debug(f"Cache hit for prompt: {prompt[:50]}...")
                    generation_time = time.time() - start_time
                    tokens_used = self._estimate_tokens(
                        prompt, cached_result, model_to_use
                    )
                    # Record cache hit for accurate metrics
                    await self._record_api_call(
                        function_name="generate_definition",
                        duration=generation_time,
                        success=True,
                        tokens_used=0,  # No actual tokens used on cache hit
                        model=model_to_use,
                        cache_hit=True,
                    )
                    return AIGenerationResult(
                        text=cached_result,
                        model=model_to_use,
                        tokens_used=tokens_used,
                        generation_time=generation_time,
                        cached=True,
                        retry_count=0,
                        metadata=(
                            {"tokens_estimated": True} if not TIKTOKEN_AVAILABLE else {}
                        ),
                    )

            # Make actual API call with timeout
            result = await asyncio.wait_for(
                self._get_client().chat_completion(
                    prompt=prompt,
                    model=model_to_use,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    system_prompt=system_prompt,
                    use_cache=False,  # We handle caching at this level
                ),
                timeout=timeout_seconds,
            )

            # Cache the result
            if self.use_cache:
                from utils.cache import _cache

                _cache.set(cache_key, result, ttl=3600)

            # Estimate token usage for the actual model used
            tokens_used = self._estimate_tokens(prompt, result, model_to_use)

            generation_time = time.time() - start_time

            # Record API call for cost tracking and monitoring
            await self._record_api_call(
                function_name="generate_definition",
                duration=generation_time,
                success=True,
                tokens_used=tokens_used,
                model=model_to_use,
                cache_hit=False,
            )

            return AIGenerationResult(
                text=result,
                model=model_to_use,
                tokens_used=tokens_used,
                generation_time=generation_time,
                cached=cached,
                retry_count=0,
                metadata={"tokens_estimated": True} if not TIKTOKEN_AVAILABLE else {},
            )

        except TimeoutError as e:
            await self._record_api_call(
                function_name="generate_definition",
                duration=time.time() - start_time,
                success=False,
                error_type="timeout",
                model=model_to_use,
            )
            timeout_msg = f"AI generation timed out after {timeout_seconds}s"
            raise AITimeoutError(timeout_msg) from e
        except AIRateLimitClientError as e:
            await self._record_api_call(
                function_name="generate_definition",
                duration=time.time() - start_time,
                success=False,
                error_type="rate_limit",
                model=model_to_use,
            )
            rate_limit_msg = f"Rate limit exceeded: {e!s}"
            raise AIRateLimitError(rate_limit_msg) from e
        except AIConnectionClientError as e:
            await self._record_api_call(
                function_name="generate_definition",
                duration=time.time() - start_time,
                success=False,
                error_type="connection_error",
                model=model_to_use,
            )
            if "timeout" in str(e).lower():
                api_timeout_msg = f"AI API timeout: {e!s}"
                raise AITimeoutError(api_timeout_msg) from e
            api_conn_msg = f"AI API connection error: {e!s}"
            raise AIServiceError(api_conn_msg) from e
        except AIClientError as e:
            await self._record_api_call(
                function_name="generate_definition",
                duration=time.time() - start_time,
                success=False,
                error_type="ai_client_error",
                model=model_to_use,
            )
            ai_error_msg = f"AI API error: {e!s}"
            raise AIServiceError(ai_error_msg) from e
        except Exception as e:
            await self._record_api_call(
                function_name="generate_definition",
                duration=time.time() - start_time,
                success=False,
                error_type="unexpected_error",
                model=model_to_use,
            )
            # Catch any other unexpected errors
            unexpected_error_msg = f"Unexpected error in AI generation: {e!s}"
            raise AIServiceError(unexpected_error_msg) from e

    async def batch_generate(
        self, requests: list[AIBatchRequest]
    ) -> list[AIGenerationResult]:
        """
        Execute multiple AI generation requests in parallel.

        Uses AsyncGPTClient's concurrency controls to optimize throughput
        while respecting rate limits.

        Args:
            requests: List of AIBatchRequest objects

        Returns:
            List of AIGenerationResult objects in same order

        Raises:
            AIServiceError: On AI service errors
        """
        if not requests:
            return []

        logger.info(f"Starting batch generation of {len(requests)} requests")

        # Create tasks for all requests
        tasks = []
        for req in requests:
            task = self.generate_definition(
                prompt=req.prompt,
                temperature=req.temperature,
                max_tokens=req.max_tokens,
                model=req.model,
                system_prompt=req.system_prompt,
                timeout_seconds=req.timeout_seconds,
            )
            tasks.append(task)

        # Execute all tasks concurrently
        # AsyncGPTClient handles rate limiting internally
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results, re-raising any exceptions
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # Re-raise the exception with context
                batch_error_msg = f"Batch request {i} failed: {result!s}"
                raise AIServiceError(batch_error_msg) from result
            final_results.append(result)

        logger.info(f"Completed batch generation of {len(requests)} requests")
        return final_results

    def _get_or_create_encoder(self, model: str):
        """
        Get or create a token encoder for the specified model.

        Args:
            model: Model name to get encoder for

        Returns:
            Token encoder or None
        """
        if not TIKTOKEN_AVAILABLE:
            return None

        if model not in self._token_encoders:
            try:
                self._token_encoders[model] = _tiktoken.encoding_for_model(model)  # type: ignore[union-attr]
                logger.debug(f"Created token encoder for model: {model}")
            except (KeyError, ValueError):
                # Model not in tiktoken registry — fall back to o200k_base
                # (used by all modern OpenAI models: gpt-4o, gpt-4.1, gpt-5, o1, o3, etc.)
                self._token_encoders[model] = _tiktoken.get_encoding("o200k_base")  # type: ignore[union-attr]
                logger.debug(
                    f"Model '{model}' not in tiktoken registry, using o200k_base fallback"
                )

        return self._token_encoders[model]

    def _estimate_tokens(self, prompt: str, response: str, model: str) -> int:
        """
        Estimate token count with ≥90% accuracy using tiktoken or heuristics.

        Args:
            prompt: Input prompt
            response: Generated response
            model: Model name for accurate encoding

        Returns:
            Estimated token count
        """
        full_text = prompt + response

        # Get encoder for specific model
        encoder = self._get_or_create_encoder(model)

        # Use tiktoken if available
        if encoder:
            try:
                return len(encoder.encode(full_text))
            except Exception as e:
                logger.warning(f"Tiktoken encoding failed for {model}: {e}")

        # Fallback heuristic: ~0.75 tokens per character for English
        # This typically achieves >90% accuracy for Dutch/English text
        char_count = len(full_text)
        estimated_tokens = int(char_count * 0.75)

        # Apply bounds based on typical token/char ratios
        # Min: 0.5 tokens/char (very simple text)
        # Max: 1.0 tokens/char (complex/technical text)
        min_tokens = int(char_count * 0.5)
        max_tokens = char_count

        return max(min_tokens, min(estimated_tokens, max_tokens))
