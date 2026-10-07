"""
Async API utilities for DefinitieAgent.
Provides asynchronous AI API calls with rate limiting and error handling.
"""

from __future__ import annotations

import asyncio
import logging
import os
import threading
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

UTC = UTC  # Python 3.10 compatibility
from functools import wraps
from typing import Any, cast

from services.ai.base_client import (
    AIClientError,
    AIStructuredOutputUnsupportedError,
    AsyncAIClient,
    ChatMessage,
    ChatResponse,
    response_schema_sha256,
)
from utils.cache import _cache, cache_gpt_call

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Configuration for API rate limiting."""

    requests_per_minute: int = 60
    requests_per_hour: int = 3000
    max_concurrent: int = 10
    backoff_factor: float = 1.5
    max_retries: int = 3


class AsyncRateLimiter:
    """Rate limiter for async API calls.

    DEF-840: één instantie wordt via ``AIServiceV2`` gedeeld door alle
    aanroepen, terwijl de UI-bridge elke aanroep in een eigen event loop (en
    thread) draait. Een asyncio-primitief bindt aan de loop waarin hij voor het
    eerst moet wachten; een gedeelde ``asyncio.Lock``/``Semaphore`` gaf in de
    volgende loop "is bound to a different event loop". Daarom:

    * het verzoekbudget (per minuut/uur) is procesbreed en wordt bewaakt met
      een ``threading.Lock`` waaronder nooit gewacht wordt;
    * de semaphore voor gelijktijdigheid bestaat per event loop (lui
      aangemaakt). ``max_concurrent`` geldt dus per loop.

    Geen ``WeakKeyDictionary``: een gebonden semaphore verwijst zelf naar zijn
    loop en zou die dan nooit loslaten. Semaphores van gesloten loops worden
    bij de volgende aanvraag opgeruimd.
    """

    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.requests_this_minute: list[datetime] = []
        self.requests_this_hour: list[datetime] = []
        self._budget_lock = threading.Lock()
        self._semaphores: dict[asyncio.AbstractEventLoop, asyncio.Semaphore] = {}

    def _semaphore(self) -> asyncio.Semaphore:
        """Semaphore van de lopende event loop; lui aangemaakt."""
        loop = asyncio.get_running_loop()
        with self._budget_lock:
            for gesloten in [lp for lp in self._semaphores if lp.is_closed()]:
                del self._semaphores[gesloten]
            semaphore = self._semaphores.get(loop)
            if semaphore is None:
                semaphore = asyncio.Semaphore(self.config.max_concurrent)
                self._semaphores[loop] = semaphore
            return semaphore

    def _reserveer(self) -> float | None:
        """Boek een verzoek als het budget het toelaat (None), anders de wachttijd in s."""
        with self._budget_lock:
            now = datetime.now(UTC)

            # Clean old requests
            minute_ago = now - timedelta(minutes=1)
            hour_ago = now - timedelta(hours=1)

            self.requests_this_minute = [
                req for req in self.requests_this_minute if req > minute_ago
            ]
            self.requests_this_hour = [
                req for req in self.requests_this_hour if req > hour_ago
            ]

            # Check rate limits
            if len(self.requests_this_minute) >= self.config.requests_per_minute:
                wait_time = 60 - (now - min(self.requests_this_minute)).total_seconds()
                logger.info(f"Rate limit reached, waiting {wait_time:.1f}s")
                return max(wait_time, 0.001)

            if len(self.requests_this_hour) >= self.config.requests_per_hour:
                wait_time = 3600 - (now - min(self.requests_this_hour)).total_seconds()
                logger.warning(f"Hourly rate limit reached, waiting {wait_time:.1f}s")
                return max(wait_time, 0.001)

            # Record this request
            self.requests_this_minute.append(now)
            self.requests_this_hour.append(now)
            return None

    async def acquire(self) -> None:
        """Acquire permission to make an API call."""
        # Na het wachten opnieuw toetsen: een andere loop kan de vrijgekomen
        # plek inmiddels hebben genomen.
        while (wait_time := self._reserveer()) is not None:
            await asyncio.sleep(wait_time)

        await self._semaphore().acquire()

    def release(self) -> None:
        """Release semaphore after API call (in dezelfde loop als acquire)."""
        self._semaphore().release()


class AsyncGPTClient:
    """Async wrapper for AI API calls with rate limiting and caching."""

    def __init__(
        self,
        rate_limit_config: RateLimitConfig | None = None,
        client: AsyncAIClient | None = None,
    ):
        if client is not None:
            self._ai_client = client
        else:
            from services.ai.openai_client import OpenAIClient

            api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY_PROD")
            if not api_key:
                msg = "OPENAI_API_KEY not found in environment"
                raise ValueError(msg)
            self._ai_client = OpenAIClient(api_key=api_key)

        self.rate_limiter = AsyncRateLimiter(rate_limit_config or RateLimitConfig())
        self.session_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "cache_hits": 0,
            "total_tokens": 0,
        }

    async def chat_completion(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.01,
        max_tokens: int = 300,
        use_cache: bool = True,
        system_prompt: str | None = None,
        **kwargs: Any,
    ) -> str:
        """
        Make async chat completion request with caching and rate limiting.

        Args:
            prompt: The prompt text
            model: GPT model to use
            temperature: Response randomness (0.0-1.0)
            max_tokens: Maximum response tokens
            use_cache: Whether to use caching
            system_prompt: Optional system prompt for context
            **kwargs: Additional OpenAI parameters

        Returns:
            Generated text response

        Raises:
            OpenAIError: If API call fails after retries
        """
        # DEF-766 opt-ins (alleen wanneer gezet): eigen aantal pogingen en
        # SDK-retries per aanroep bij de providerclient. Ze zijn geen
        # providerparameters en gaan daarom niet mee in de cachesleutel.
        max_attempts = kwargs.pop("max_attempts", None)
        max_retries = kwargs.pop("max_retries", None)
        # DEF-766 (correctieronde 3, F1): optionele callback die de volledige
        # `ChatResponse` van de providerclient ontvangt (o.a. `stop_reason`),
        # omdat deze methode contractueel alleen de tekst teruggeeft. Geen
        # providerparameter, niet in de cachesleutel, niet naar de provider.
        response_hook = kwargs.pop("response_hook", None)
        # DEF-836 P1 (opt-in): antwoordschema voor de providerclient. In de
        # cachesleutel alleen als volgordegevoelige hash en alleen wanneer
        # gezet, zodat sleutels van andere aanroepen gelijk blijven.
        response_schema = kwargs.pop("response_schema", None)
        schemasleutel = (
            {"response_schema_sha256": response_schema_sha256(response_schema)}
            if response_schema is not None
            else {}
        )

        # Check cache first
        if use_cache:
            cache_key = cache_gpt_call(
                prompt=prompt,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                system_prompt=system_prompt,
                **schemasleutel,
                **kwargs,
            )

            # Try to get from cache (sync cache)
            cached_result = _cache.get(cache_key)
            if cached_result is not None:
                self.session_stats["cache_hits"] += 1
                logger.debug(f"Cache hit for prompt: {prompt[:50]}...")
                return cast(str, cached_result)

        # Make API call with rate limiting and retries
        await self.rate_limiter.acquire()

        try:
            # DEF-314: Resolve model via ModelRouter when None
            resolved_model = model
            if resolved_model is None:
                try:
                    from utils.container_manager import get_cached_container

                    router = get_cached_container().model_router()
                    _, resolved_model = router.get_model("definition_core")
                except Exception:
                    from config.config_manager import get_default_model

                    resolved_model = get_default_model()

            result = await self._make_request_with_retries(
                prompt=prompt,
                model=resolved_model,
                temperature=temperature,
                max_tokens=max_tokens,
                system_prompt=system_prompt,
                max_attempts=max_attempts,
                max_retries=max_retries,
                response_hook=response_hook,
                response_schema=response_schema,
                **kwargs,
            )

            # Cache the result
            if use_cache:
                _cache.set(cache_key, result, ttl=3600)

            self.session_stats["successful_requests"] += 1
            return result

        except Exception as e:
            self.session_stats["failed_requests"] += 1
            logger.error(f"API call failed: {e!s}")
            raise
        finally:
            self.rate_limiter.release()
            self.session_stats["total_requests"] += 1

    async def _make_request_with_retries(
        self,
        prompt: str,
        model: str,
        temperature: float,
        max_tokens: int,
        system_prompt: str | None = None,
        max_attempts: int | None = None,
        max_retries: int | None = None,
        response_hook: Callable[[ChatResponse], None] | None = None,
        response_schema: Mapping[str, Any] | None = None,
        **kwargs: Any,
    ) -> str:
        """Make API request with exponential backoff retries.

        DEF-766 (opt-in, alleen wanneer gezet): ``max_attempts`` begrenst deze
        retrylus tot dat aantal pogingen (1 = geen herhaling); ``max_retries``
        reist door naar de providerclient als SDK-retries per aanroep;
        ``response_hook`` ontvangt de volledige ``ChatResponse`` van de
        geslaagde poging (correctieronde 3, F1); ``response_schema`` reist
        door naar de providerclient (DEF-836 P1). Zonder deze argumenten is
        het gedrag exact het bestaande.
        """
        last_error = None
        pogingen = (
            max(1, int(max_attempts))
            if max_attempts is not None
            else self.rate_limiter.config.max_retries
        )
        clientopties: dict[str, Any] = (
            {"max_retries": int(max_retries)} if max_retries is not None else {}
        )
        if response_schema is not None:
            clientopties["response_schema"] = response_schema

        for attempt in range(pogingen):
            try:
                messages: list[ChatMessage] = []
                if system_prompt:
                    messages.append(ChatMessage(role="system", content=system_prompt))
                messages.append(ChatMessage(role="user", content=prompt))

                response = await self._ai_client.chat_completion(
                    messages=messages,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **clientopties,
                )

                result = response.text

                if response.tokens_used:
                    self.session_stats["total_tokens"] += response.tokens_used
                if response_hook is not None:
                    response_hook(response)

                # ChatResponse.text is contractueel `str`; de cast onderdrukt enkel
                # de Any die ontstaat doordat AsyncAIClient via de services.ai-import
                # naar Any resolvet (DEF-439). Weghalen zodra die resolutie gefixt is.
                return cast(str, result)

            except AIStructuredOutputUnsupportedError:
                # DEF-836 P1: een configuratieweigering vóór verzending is
                # blijvend; herhalen verandert niets.
                raise
            except AIClientError as e:
                last_error = e
                if attempt < pogingen - 1:
                    wait_time = self.rate_limiter.config.backoff_factor**attempt
                    logger.warning(
                        f"API call failed (attempt {attempt + 1}), retrying in {wait_time}s: {e!s}"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"API call failed after {pogingen} attempts")

        raise last_error or AIClientError("Unknown error after retries")

    async def batch_completion(
        self,
        prompts: list[str],
        model: str | None = None,
        temperature: float = 0.01,
        max_tokens: int = 300,
        progress_callback: Callable[[int, int], None] | None = None,
        **kwargs: Any,
    ) -> list[str]:
        """
        Process multiple prompts concurrently.

        Args:
            prompts: List of prompt strings
            model: GPT model to use
            temperature: Response randomness
            max_tokens: Maximum response tokens
            progress_callback: Optional callback for progress updates
            **kwargs: Additional OpenAI parameters

        Returns:
            List of generated responses in same order as prompts
        """
        if not prompts:
            return []

        logger.info(f"Starting batch processing of {len(prompts)} prompts")

        # Create tasks for all prompts
        tasks = []
        for _i, prompt in enumerate(prompts):
            task = self.chat_completion(
                prompt=prompt,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )
            tasks.append(task)

        # Process with progress tracking
        results = []
        completed = 0

        for coro in asyncio.as_completed(tasks):
            try:
                result = await coro
                results.append(result)
                completed += 1

                if progress_callback:
                    progress_callback(completed, len(prompts))

                logger.debug(f"Completed {completed}/{len(prompts)} requests")

            except Exception as e:
                logger.error(f"Batch request failed: {e!s}")
                results.append(f"❌ Error: {e!s}")
                completed += 1

                if progress_callback:
                    progress_callback(completed, len(prompts))

        logger.info(f"Batch processing completed: {len(results)} results")
        return results

    def get_stats(self) -> dict[str, Any]:
        """Get session statistics."""
        return self.session_stats.copy()

    async def close(self) -> None:
        """Close the async client."""
        if hasattr(self._ai_client, "close"):
            await self._ai_client.close()


# Global async client instance
_async_client: AsyncGPTClient | None = None


async def get_async_client() -> AsyncGPTClient:
    """Get or create global async GPT client."""
    global _async_client
    if _async_client is None:
        _async_client = AsyncGPTClient()
    return _async_client


async def async_gpt_call(
    prompt: str,
    model: str | None = None,
    temperature: float = 0.01,
    max_tokens: int = 300,
    **kwargs: Any,
) -> str:
    """
    Convenience function for async GPT calls.

    Args:
        prompt: The prompt text
        model: GPT model to use
        temperature: Response randomness
        max_tokens: Maximum response tokens
        **kwargs: Additional parameters

    Returns:
        Generated text response
    """
    client = await get_async_client()
    return await client.chat_completion(
        prompt=prompt,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        **kwargs,
    )


async def async_batch_gpt_calls(
    prompts: list[str],
    model: str | None = None,
    temperature: float = 0.01,
    max_tokens: int = 300,
    progress_callback: Callable[[int, int], None] | None = None,
    **kwargs: Any,
) -> list[str]:
    """
    Convenience function for batch async GPT calls.

    Args:
        prompts: List of prompt strings
        model: GPT model to use
        temperature: Response randomness
        max_tokens: Maximum response tokens
        progress_callback: Optional progress callback
        **kwargs: Additional parameters

    Returns:
        List of generated responses
    """
    client = await get_async_client()
    return await client.batch_completion(
        prompts=prompts,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        progress_callback=progress_callback,
        **kwargs,
    )


def async_cached(
    ttl: int = 3600,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator for async functions with caching.

    Args:
        ttl: Time to live in seconds

    Returns:
        Decorated async function
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Generate cache key
            cache_key = _cache._generate_cache_key(func.__name__, *args, **kwargs)

            # Try cache first
            cached_result = _cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Async cache hit for {func.__name__}")
                return cached_result

            # Execute async function
            result = await func(*args, **kwargs)

            # Store in cache
            _cache.set(cache_key, result, ttl)

            return result

        return wrapper

    return decorator


async def cleanup_async_resources() -> None:
    """Clean up async resources on shutdown."""
    global _async_client
    if _async_client:
        await _async_client.close()
        _async_client = None
