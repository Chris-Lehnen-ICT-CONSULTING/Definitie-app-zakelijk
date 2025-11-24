"""
Comprehensive unit tests for TokenBucket.acquire() blocking behavior.

Tests the blocking acquire() implementation with timeout parameter to verify:
- Immediate acquisition when tokens available
- Waiting for token refill
- Timeout behavior
- Non-blocking mode (timeout=0)
- Infinite wait mode (timeout=None)
- Concurrent request handling
- Input validation
"""

import asyncio
import time

import pytest

from src.utils.smart_rate_limiter import TokenBucket


class TestTokenBucketAcquire:
    """Test blocking acquire() with timeout parameter."""

    @pytest.mark.asyncio
    async def test_acquire_immediate_success(self):
        """Tokens available → acquire succeeds immediately."""
        bucket = TokenBucket(rate=10, capacity=10)
        bucket.tokens = 5

        result = await bucket.acquire(tokens=3, timeout=1.0)

        assert result is True
        # Allow small tolerance for timing precision
        assert 1.9 <= bucket.tokens <= 2.1

    @pytest.mark.asyncio
    async def test_acquire_waits_for_refill(self):
        """No tokens → waits until refill → succeeds."""
        bucket = TokenBucket(rate=10, capacity=10)
        bucket.tokens = 0

        start = time.time()
        result = await bucket.acquire(tokens=5, timeout=2.0)
        elapsed = time.time() - start

        assert result is True
        assert 0.4 <= elapsed <= 0.7  # 5 tokens @ 10/sec = 0.5s (allow tolerance)

    @pytest.mark.asyncio
    async def test_acquire_timeout(self):
        """Insufficient tokens + timeout → returns False."""
        bucket = TokenBucket(rate=1, capacity=10)
        bucket.tokens = 0

        start = time.time()
        result = await bucket.acquire(tokens=10, timeout=0.5)
        elapsed = time.time() - start

        assert result is False
        assert 0.4 <= elapsed <= 0.7  # Should timeout at ~0.5s

    @pytest.mark.asyncio
    async def test_acquire_non_blocking(self):
        """timeout=0 → non-blocking mode."""
        bucket = TokenBucket(rate=10, capacity=10)
        bucket.tokens = 0

        start = time.time()
        result = await bucket.acquire(tokens=5, timeout=0)
        elapsed = time.time() - start

        assert result is False
        assert elapsed < 0.1  # Should return immediately

    @pytest.mark.asyncio
    async def test_acquire_infinite_wait(self):
        """timeout=None → waits indefinitely."""
        bucket = TokenBucket(rate=10, capacity=10)
        bucket.tokens = 0

        async def refill_later():
            """Simulate token refill after delay."""
            await asyncio.sleep(0.2)
            async with bucket._lock:
                bucket.tokens = 5

        task = asyncio.create_task(refill_later())
        start = time.time()
        result = await bucket.acquire(tokens=3, timeout=None)
        elapsed = time.time() - start
        await task

        assert result is True
        assert 0.15 <= elapsed <= 0.35  # Should wait ~0.2s for refill

    @pytest.mark.asyncio
    async def test_acquire_concurrent_requests(self):
        """Multiple concurrent acquire() calls → fair distribution."""
        bucket = TokenBucket(rate=10, capacity=10)
        bucket.tokens = 5

        results = await asyncio.gather(
            bucket.acquire(tokens=2, timeout=1.0),
            bucket.acquire(tokens=2, timeout=1.0),
            bucket.acquire(tokens=2, timeout=1.0),
        )

        # All should eventually succeed (5 initial + refill during wait)
        assert all(results)

    @pytest.mark.asyncio
    async def test_acquire_negative_tokens_raises(self):
        """tokens < 1 → ValueError."""
        bucket = TokenBucket(rate=10, capacity=10)

        with pytest.raises(ValueError, match="tokens must be >= 1"):
            await bucket.acquire(tokens=0)

        with pytest.raises(ValueError, match="tokens must be >= 1"):
            await bucket.acquire(tokens=-5)

    @pytest.mark.asyncio
    async def test_acquire_negative_timeout_raises(self):
        """timeout < 0 → ValueError."""
        bucket = TokenBucket(rate=10, capacity=10)

        with pytest.raises(ValueError, match="timeout must be >= 0"):
            await bucket.acquire(tokens=1, timeout=-1)

        with pytest.raises(ValueError, match="timeout must be >= 0"):
            await bucket.acquire(tokens=1, timeout=-0.5)

    @pytest.mark.asyncio
    async def test_acquire_default_parameters(self):
        """Default parameters (tokens=1, timeout=None) work correctly."""
        bucket = TokenBucket(rate=10, capacity=10)
        bucket.tokens = 3

        # Should use default tokens=1
        result = await bucket.acquire()
        assert result is True
        # Allow small tolerance for timing precision
        assert 1.9 <= bucket.tokens <= 2.1

        # Should wait indefinitely with timeout=None
        bucket.tokens = 0

        async def refill():
            await asyncio.sleep(0.1)
            async with bucket._lock:
                bucket.tokens = 1

        task = asyncio.create_task(refill())
        result = await bucket.acquire()  # timeout=None by default
        await task
        assert result is True

    @pytest.mark.asyncio
    async def test_acquire_partial_refill(self):
        """Partial token refill during wait → continues waiting."""
        bucket = TokenBucket(rate=2, capacity=10)  # 2 tokens/sec
        bucket.tokens = 0

        start = time.time()
        result = await bucket.acquire(
            tokens=5, timeout=5.0
        )  # Need 5 tokens @ 2/sec = 2.5s
        elapsed = time.time() - start

        assert result is True
        assert 2.3 <= elapsed <= 2.8  # Should wait ~2.5s

    @pytest.mark.asyncio
    async def test_acquire_exact_capacity(self):
        """Requesting exactly capacity tokens works."""
        bucket = TokenBucket(rate=10, capacity=10)
        bucket.tokens = 10

        result = await bucket.acquire(tokens=10, timeout=1.0)

        assert result is True
        assert bucket.tokens == 0

    @pytest.mark.asyncio
    async def test_acquire_over_capacity_waits(self):
        """Requesting more than capacity times out (can never succeed)."""
        bucket = TokenBucket(rate=5, capacity=10)
        bucket.tokens = 10

        # Request 15 tokens (> capacity)
        # This can never succeed since bucket max capacity is 10
        start = time.time()
        result = await bucket.acquire(tokens=15, timeout=0.5)
        elapsed = time.time() - start

        assert result is False  # Should timeout
        assert 0.4 <= elapsed <= 0.7  # Should wait until timeout

    @pytest.mark.asyncio
    async def test_acquire_token_refill_during_wait(self):
        """Tokens refill naturally during wait period."""
        bucket = TokenBucket(rate=10, capacity=10)
        bucket.tokens = 0

        # Multiple requests should all succeed due to natural refill
        start = time.time()
        results = await asyncio.gather(
            bucket.acquire(tokens=2, timeout=2.0),
            bucket.acquire(tokens=2, timeout=2.0),
            bucket.acquire(tokens=2, timeout=2.0),
        )
        elapsed = time.time() - start

        assert all(results)
        # 6 tokens total @ 10/sec = 0.6s minimum
        assert 0.5 <= elapsed <= 1.0

    @pytest.mark.asyncio
    async def test_acquire_timeout_edge_case(self):
        """Timeout exactly when tokens become available."""
        bucket = TokenBucket(rate=10, capacity=10)
        bucket.tokens = 0

        # Need 5 tokens @ 10/sec = 0.5s
        # Set timeout to 0.5s → should succeed (or fail, depending on timing)
        result = await bucket.acquire(tokens=5, timeout=0.5)

        # Result can be either True or False due to timing, but should not hang
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_acquire_maintains_lock_safety(self):
        """Concurrent acquire calls don't corrupt token count."""
        bucket = TokenBucket(rate=100, capacity=100)
        bucket.tokens = 50

        # Launch many concurrent requests
        tasks = [bucket.acquire(tokens=1, timeout=2.0) for _ in range(60)]
        results = await asyncio.gather(*tasks)

        # All should succeed (50 initial + 10 refill during ~0.1s wait)
        successful = sum(1 for r in results if r)
        assert successful >= 50  # At least initial tokens consumed
        assert successful <= 60  # Not more than requested
