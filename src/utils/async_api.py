"""
Async API utilities for DefinitieAgent.
Provides asynchronous OpenAI API calls with rate limiting and error handling.
"""

import asyncio
import logging
import os
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from functools import wraps
from typing import Any

from dotenv import load_dotenv
from openai import AsyncOpenAI, OpenAIError

from utils.cache import cache_gpt_call

load_dotenv()
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
    """Rate limiter for async API calls."""

    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.requests_this_minute = []
        self.requests_this_hour = []
        self.semaphore = asyncio.Semaphore(config.max_concurrent)
        self._lock = asyncio.Lock()

    async def acquire(self):
        """Acquire permission to make an API call."""
        async with self._lock:
            now = datetime.now(timezone.utc)

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
                await asyncio.sleep(wait_time)

            if len(self.requests_this_hour) >= self.config.requests_per_hour:
                wait_time = 3600 - (now - min(self.requests_this_hour)).total_seconds()
                logger.warning(f"Hourly rate limit reached, waiting {wait_time:.1f}s")
                await asyncio.sleep(wait_time)

            # Record this request
            self.requests_this_minute.append(now)
            self.requests_this_hour.append(now)

        await self.semaphore.acquire()

    def release(self):
        """Release semaphore after API call."""
        self.semaphore.release()


class AsyncGPTClient:
    """Async wrapper for OpenAI GPT API calls."""

    def __init__(self, rate_limit_config: RateLimitConfig | None = None):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            msg = "OPENAI_API_KEY not found in environment"
            raise ValueError(msg)

        self.client = AsyncOpenAI(api_key=self.api_key)
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
        **kwargs,
    ) -> str:
        """
        Make async chat completion request with caching and rate limiting.

        Args:
            prompt: The prompt text
            model: GPT model to use
            temperature: Response randomness (0.0-1.0)
            max_tokens: Maximum response tokens
            use_cache: Whether to use caching
            **kwargs: Additional OpenAI parameters

        Returns:
            Generated text response

        Raises:
            OpenAIError: If API call fails after retries
        """
        # Check cache first
        if use_cache:
            cache_key = cache_gpt_call(
                prompt=prompt,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )

            # Try to get from cache using sync cache for now
            # TODO: Implement async cache
            from utils.cache import _cache

            cached_result = _cache.get(cache_key)
            if cached_result is not None:
                self.session_stats["cache_hits"] += 1
                logger.debug(f"Cache hit for prompt: {prompt[:50]}...")
                return cached_result

        # Make API call with rate limiting and retries
        await self.rate_limiter.acquire()

        try:
            result = await self._make_request_with_retries(
                prompt=prompt,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )

            # Cache the result
            if use_cache:
                from utils.cache import _cache

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
        self, prompt: str, model: str, temperature: float, max_tokens: int, **kwargs
    ) -> str:
        """Make API request with exponential backoff retries."""
        last_error = None

        for attempt in range(self.rate_limiter.config.max_retries):
            try:
                response = await self.client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs,
                )

                result = response.choices[0].message.content.strip()

                # Track token usage
                if hasattr(response, "usage") and response.usage:
                    self.session_stats["total_tokens"] += response.usage.total_tokens

                return result

            except OpenAIError as e:
                last_error = e
                if attempt < self.rate_limiter.config.max_retries - 1:
                    wait_time = self.rate_limiter.config.backoff_factor**attempt
                    logger.warning(
                        f"API call failed (attempt {attempt + 1}), retrying in {wait_time}s: {e!s}"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(
                        f"API call failed after {self.rate_limiter.config.max_retries} attempts"
                    )

        raise last_error or OpenAIError("Unknown error after retries")

    async def batch_completion(
        self,
        prompts: list[str],
        model: str | None = None,
        temperature: float = 0.01,
        max_tokens: int = 300,
        progress_callback: Callable[[int, int], None] | None = None,
        **kwargs,
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

    async def close(self):
        """Close the async client."""
        await self.client.close()


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
    **kwargs,
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
    **kwargs,
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


def async_cached(ttl: int = 3600):
    """
    Decorator for async functions with caching.

    Args:
        ttl: Time to live in seconds

    Returns:
        Decorated async function
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            from utils.cache import _cache

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


async def cleanup_async_resources():
    """Clean up async resources on shutdown."""
    global _async_client
    if _async_client:
        await _async_client.close()
        _async_client = None
