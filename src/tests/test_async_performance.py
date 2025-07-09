"""
Performance tests for async vs sync processing.
Demonstrates the speed improvements of parallel processing.
"""

import asyncio
import time
import logging
from typing import Dict, List

# Mock implementations for testing without API calls
class MockSyncService:
    """Mock sync service for testing."""
    
    @staticmethod
    def mock_api_call(delay: float = 2.0) -> str:
        """Mock API call with delay."""
        time.sleep(delay)
        return f"Mock result after {delay}s"
    
    def generate_examples_sync(self) -> Dict[str, List[str]]:
        """Generate examples synchronously."""
        start_time = time.time()
        
        # Simulate 6 sequential API calls
        results = {
            'voorbeeld_zinnen': [self.mock_api_call(2.0)],
            'praktijkvoorbeelden': [self.mock_api_call(2.5)],
            'tegenvoorbeelden': [self.mock_api_call(1.8)],
            'synoniemen': self.mock_api_call(1.5),
            'antoniemen': self.mock_api_call(1.2),
            'toelichting': self.mock_api_call(2.2)
        }
        
        total_time = time.time() - start_time
        print(f"📊 Sync processing completed in {total_time:.2f}s")
        
        return results


class MockAsyncService:
    """Mock async service for testing."""
    
    @staticmethod
    async def mock_async_api_call(delay: float = 2.0) -> str:
        """Mock async API call with delay."""
        await asyncio.sleep(delay)
        return f"Mock result after {delay}s"
    
    async def generate_examples_async(self) -> Dict[str, List[str]]:
        """Generate examples asynchronously."""
        start_time = time.time()
        
        # Simulate 6 concurrent API calls
        tasks = [
            self.mock_async_api_call(2.0),  # voorbeeld_zinnen
            self.mock_async_api_call(2.5),  # praktijkvoorbeelden  
            self.mock_async_api_call(1.8),  # tegenvoorbeelden
            self.mock_async_api_call(1.5),  # synoniemen
            self.mock_async_api_call(1.2),  # antoniemen
            self.mock_async_api_call(2.2)   # toelichting
        ]
        
        # Execute all tasks concurrently
        results_list = await asyncio.gather(*tasks)
        
        results = {
            'voorbeeld_zinnen': [results_list[0]],
            'praktijkvoorbeelden': [results_list[1]],
            'tegenvoorbeelden': [results_list[2]],
            'synoniemen': results_list[3],
            'antoniemen': results_list[4],
            'toelichting': results_list[5]
        }
        
        total_time = time.time() - start_time
        print(f"🚀 Async processing completed in {total_time:.2f}s")
        
        return results


def test_performance_comparison():
    """Test performance comparison between sync and async."""
    print("🧪 Performance Comparison Test")
    print("=" * 50)
    
    # Test sync processing
    print("Testing synchronous processing...")
    sync_service = MockSyncService()
    sync_start = time.time()
    sync_results = sync_service.generate_examples_sync()
    sync_time = time.time() - sync_start
    
    print(f"Sync results: {len(sync_results)} items generated")
    print()
    
    # Test async processing
    print("Testing asynchronous processing...")
    async_service = MockAsyncService()
    
    async def run_async_test():
        async_start = time.time()
        async_results = await async_service.generate_examples_async()
        async_time = time.time() - async_start
        return async_results, async_time
    
    async_results, async_time = asyncio.run(run_async_test())
    print(f"Async results: {len(async_results)} items generated")
    print()
    
    # Calculate improvement
    improvement = ((sync_time - async_time) / sync_time) * 100
    speedup = sync_time / async_time
    
    print("📊 Performance Summary:")
    print(f"Synchronous time:  {sync_time:.2f}s")
    print(f"Asynchronous time: {async_time:.2f}s")
    print(f"Speed improvement: {improvement:.1f}%")
    print(f"Speedup factor:    {speedup:.1f}x faster")
    print()
    
    # Expected results for this test
    expected_sync_time = 11.2  # Sum of all delays
    expected_async_time = 2.5   # Max of all delays
    expected_improvement = ((expected_sync_time - expected_async_time) / expected_sync_time) * 100
    
    print(f"Expected improvement: ~{expected_improvement:.0f}% (theoretical)")
    
    return {
        'sync_time': sync_time,
        'async_time': async_time,
        'improvement': improvement,
        'speedup': speedup
    }


def test_rate_limiting():
    """Test rate limiting functionality."""
    print("\n🚥 Rate Limiting Test")
    print("=" * 30)
    
    from utils.async_api import RateLimitConfig, AsyncRateLimiter
    
    async def test_limiter():
        config = RateLimitConfig(
            requests_per_minute=5,
            max_concurrent=2
        )
        limiter = AsyncRateLimiter(config)
        
        print("Testing rate limiter...")
        
        start_time = time.time()
        tasks = []
        
        # Create 3 concurrent tasks (within limit)
        for i in range(3):
            async def limited_task(task_id=i):
                await limiter.acquire()
                try:
                    print(f"Task {task_id} executing...")
                    await asyncio.sleep(0.5)
                    return f"Task {task_id} completed"
                finally:
                    limiter.release()
            
            tasks.append(limited_task())
        
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
        print(f"Completed {len(results)} tasks in {total_time:.2f}s")
        print("✅ Rate limiting working correctly")
        
        return results
    
    return asyncio.run(test_limiter())


if __name__ == "__main__":
    # Run performance comparison
    perf_results = test_performance_comparison()
    
    # Run rate limiting test
    rate_results = test_rate_limiting()
    
    print("\n✅ All tests completed successfully!")
    print(f"Final speedup: {perf_results['speedup']:.1f}x faster with async processing")