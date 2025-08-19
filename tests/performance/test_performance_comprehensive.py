"""
Comprehensive performance tests for DefinitieAgent.
Tests load performance, memory usage, response times, and scalability.
"""

import asyncio
import json
import os
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import MagicMock, patch

import psutil
import pytest

# Import modules for performance testing
from ai_toetser.modular_toetser import ModularToetser
from document_processing.document_extractor import extract_text_from_file
from utils.cache import cached, clear_cache, get_cache_stats
from validation.sanitizer import get_sanitizer, sanitize_content

from config.config_loader import laad_toetsregels
from config.config_manager import ConfigSection, get_config_manager

# Import resilience and rate limiting components
try:
    from utils.optimized_resilience import OptimizedResilience
    from utils.smart_rate_limiter import SmartRateLimiter

    RESILIENCE_AVAILABLE = True
except ImportError:
    RESILIENCE_AVAILABLE = False


class PerformanceMonitor:
    """Helper class to monitor system performance during tests."""

    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.start_memory = self.process.memory_info().rss
        self.start_time = time.time()
        self.peak_memory = self.start_memory
        self.measurements = []

    def start_measurement(self, operation_name: str):
        """Start measuring an operation."""
        return {
            "operation": operation_name,
            "start_time": time.time(),
            "start_memory": self.process.memory_info().rss,
            "start_cpu_percent": self.process.cpu_percent(),
        }

    def end_measurement(self, measurement: dict):
        """End measuring an operation."""
        end_time = time.time()
        end_memory = self.process.memory_info().rss
        end_cpu = self.process.cpu_percent()

        result = {
            "operation": measurement["operation"],
            "duration": end_time - measurement["start_time"],
            "memory_delta": end_memory - measurement["start_memory"],
            "peak_memory": max(self.peak_memory, end_memory),
            "cpu_usage": end_cpu,
            "memory_mb": end_memory / 1024 / 1024,
        }

        self.measurements.append(result)
        self.peak_memory = max(self.peak_memory, end_memory)
        return result

    def get_summary(self):
        """Get performance summary."""
        total_time = time.time() - self.start_time
        total_memory_delta = self.peak_memory - self.start_memory

        return {
            "total_duration": total_time,
            "total_memory_delta_mb": total_memory_delta / 1024 / 1024,
            "peak_memory_mb": self.peak_memory / 1024 / 1024,
            "operation_count": len(self.measurements),
            "avg_operation_time": (
                sum(m["duration"] for m in self.measurements) / len(self.measurements)
                if self.measurements
                else 0
            ),
            "slowest_operation": (
                max(self.measurements, key=lambda x: x["duration"])
                if self.measurements
                else None
            ),
            "memory_intensive_operation": (
                max(self.measurements, key=lambda x: x["memory_delta"])
                if self.measurements
                else None
            ),
        }


class TestAIToetserPerformance:
    """Test AI Toetser performance under various conditions."""

    def setup_method(self):
        """Setup for each test method."""
        self.monitor = PerformanceMonitor()
        self.toetser = ModularToetser()
        self.toetsregels = laad_toetsregels()

    def test_single_validation_performance(self):
        """Test performance of single definition validation."""
        definition = "Authenticatie is het proces van het verifiëren van de identiteit van een gebruiker of systeem."

        measurement = self.monitor.start_measurement("single_validation")

        result = self.toetser.validate_definition(definition, self.toetsregels)

        perf_result = self.monitor.end_measurement(measurement)

        # Assertions
        assert result is not None
        assert (
            perf_result["duration"] < 0.5
        ), f"Single validation too slow: {perf_result['duration']:.3f}s"
        assert (
            perf_result["memory_delta"] < 10 * 1024 * 1024
        ), f"Memory usage too high: {perf_result['memory_delta'] / 1024 / 1024:.2f}MB"

    def test_batch_validation_performance(self):
        """Test performance of batch validation operations."""
        definitions = [
            f"Definitie nummer {i} voor authenticatie en identiteitsbehandeling in de Nederlandse rechtsorde."
            for i in range(50)
        ]

        measurement = self.monitor.start_measurement("batch_validation")

        results = []
        for definition in definitions:
            result = self.toetser.validate_definition(definition, self.toetsregels)
            results.append(result)

        perf_result = self.monitor.end_measurement(measurement)

        # Assertions
        assert len(results) == 50
        assert all(r is not None for r in results)
        assert (
            perf_result["duration"] < 10.0
        ), f"Batch validation too slow: {perf_result['duration']:.3f}s"

        # Calculate throughput
        throughput = len(definitions) / perf_result["duration"]
        assert (
            throughput > 5
        ), f"Validation throughput too low: {throughput:.2f} def/sec"

    def test_concurrent_validation_performance(self):
        """Test performance under concurrent validation load."""
        definitions = [
            f"Concurrent definitie {i} voor performance testing van het systeem."
            for i in range(20)
        ]

        def validate_worker(definition):
            return self.toetser.validate_definition(definition, self.toetsregels)

        measurement = self.monitor.start_measurement("concurrent_validation")

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [
                executor.submit(validate_worker, def_text) for def_text in definitions
            ]
            results = [future.result() for future in futures]

        perf_result = self.monitor.end_measurement(measurement)

        # Assertions
        assert len(results) == 20
        assert all(r is not None for r in results)
        assert (
            perf_result["duration"] < 5.0
        ), f"Concurrent validation too slow: {perf_result['duration']:.3f}s"

    def test_memory_usage_under_load(self):
        """Test memory usage under sustained load."""
        initial_memory = self.monitor.process.memory_info().rss

        # Perform many validation operations
        for i in range(100):
            definition = f"Memory test definitie {i} met uitgebreide Nederlandse terminologie voor identiteitsbehandeling."
            result = self.toetser.validate_definition(definition, self.toetsregels)
            assert result is not None

            # Check memory every 20 operations
            if i % 20 == 0:
                current_memory = self.monitor.process.memory_info().rss
                memory_growth = current_memory - initial_memory
                # Memory growth should be reasonable
                assert (
                    memory_growth < 50 * 1024 * 1024
                ), f"Memory growth too high: {memory_growth / 1024 / 1024:.2f}MB at iteration {i}"


class TestCachePerformance:
    """Test cache system performance."""

    def setup_method(self):
        """Setup for each test method."""
        self.monitor = PerformanceMonitor()
        clear_cache()

    def test_cache_hit_performance(self):
        """Test cache hit performance."""

        @cached(ttl=300)
        def expensive_operation(x):
            time.sleep(0.01)  # Simulate expensive operation
            return f"result_{x}"

        # First call (cache miss)
        measurement = self.monitor.start_measurement("cache_miss")
        result1 = expensive_operation("test")
        miss_perf = self.monitor.end_measurement(measurement)

        # Second call (cache hit)
        measurement = self.monitor.start_measurement("cache_hit")
        result2 = expensive_operation("test")
        hit_perf = self.monitor.end_measurement(measurement)

        # Assertions
        assert result1 == result2
        assert (
            hit_perf["duration"] < miss_perf["duration"] * 0.1
        ), "Cache hit not significantly faster than miss"
        assert (
            hit_perf["duration"] < 0.001
        ), f"Cache hit too slow: {hit_perf['duration']:.6f}s"

    def test_cache_scalability(self):
        """Test cache performance with many entries."""

        @cached(ttl=300)
        def cached_function(x):
            return f"cached_result_{x}"

        measurement = self.monitor.start_measurement("cache_scalability")

        # Create many cache entries
        for i in range(1000):
            result = cached_function(f"key_{i}")
            assert result == f"cached_result_key_{i}"

        # Test access performance with many entries
        for i in range(100):
            result = cached_function(f"key_{i}")  # Should be cache hits
            assert result == f"cached_result_key_{i}"

        perf_result = self.monitor.end_measurement(measurement)

        # Check cache stats
        stats = get_cache_stats()

        # Assertions
        assert (
            perf_result["duration"] < 2.0
        ), f"Cache scalability test too slow: {perf_result['duration']:.3f}s"
        assert stats["entries"] >= 1000, f"Not all entries cached: {stats['entries']}"

    def test_cache_memory_efficiency(self):
        """Test cache memory efficiency."""

        @cached(ttl=300)
        def memory_test_function(x):
            return "x" * 1000  # 1KB strings

        initial_memory = self.monitor.process.memory_info().rss

        # Create many cached entries
        for i in range(500):
            result = memory_test_function(f"key_{i}")
            assert len(result) == 1000

        final_memory = self.monitor.process.memory_info().rss
        memory_usage = final_memory - initial_memory

        # Memory usage should be reasonable (less than 50MB for 500KB of data)
        assert (
            memory_usage < 50 * 1024 * 1024
        ), f"Cache memory usage too high: {memory_usage / 1024 / 1024:.2f}MB"


class TestConfigurationPerformance:
    """Test configuration system performance."""

    def setup_method(self):
        """Setup for each test method."""
        self.monitor = PerformanceMonitor()

    def test_config_loading_performance(self):
        """Test configuration loading performance."""
        measurement = self.monitor.start_measurement("config_loading")

        # Load configuration multiple times
        for i in range(50):
            config_manager = get_config_manager()
            api_config = get_api_config()
            assert config_manager is not None
            assert api_config is not None

        perf_result = self.monitor.end_measurement(measurement)

        # Assertions
        assert (
            perf_result["duration"] < 1.0
        ), f"Config loading too slow: {perf_result['duration']:.3f}s"

        # Calculate loading rate
        loading_rate = 50 / perf_result["duration"]
        assert (
            loading_rate > 50
        ), f"Config loading rate too low: {loading_rate:.2f} loads/sec"

    def test_toetsregels_loading_performance(self):
        """Test toetsregels loading performance."""
        measurement = self.monitor.start_measurement("toetsregels_loading")

        # Load toetsregels multiple times
        for i in range(20):
            regels = laad_toetsregels()
            assert isinstance(regels, dict)
            assert len(regels) > 0

        perf_result = self.monitor.end_measurement(measurement)

        # Assertions
        assert (
            perf_result["duration"] < 2.0
        ), f"Toetsregels loading too slow: {perf_result['duration']:.3f}s"


class TestSanitizationPerformance:
    """Test sanitization system performance."""

    def setup_method(self):
        """Setup for each test method."""
        self.monitor = PerformanceMonitor()
        self.sanitizer = get_sanitizer()

    def test_sanitization_speed(self):
        """Test sanitization processing speed."""
        test_texts = [
            "Normal text content",
            "<script>alert('xss')</script>Malicious content",
            "Text with profanity: kut and shit words",
            "SQL injection: '; DROP TABLE users; --",
            "Very long text content " * 100,
        ]

        measurement = self.monitor.start_measurement("sanitization_speed")

        results = []
        for text in test_texts * 20:  # 100 total operations
            result = sanitize_content(text)
            results.append(result)

        perf_result = self.monitor.end_measurement(measurement)

        # Assertions
        assert len(results) == 100
        assert (
            perf_result["duration"] < 1.0
        ), f"Sanitization too slow: {perf_result['duration']:.3f}s"

        # Calculate sanitization rate
        sanitization_rate = 100 / perf_result["duration"]
        assert (
            sanitization_rate > 100
        ), f"Sanitization rate too low: {sanitization_rate:.2f} ops/sec"

    def test_large_content_sanitization(self):
        """Test sanitization of large content."""
        large_content = "Test content with various patterns. " * 1000  # ~35KB

        measurement = self.monitor.start_measurement("large_content_sanitization")

        result = sanitize_content(large_content)

        perf_result = self.monitor.end_measurement(measurement)

        # Assertions
        assert result is not None
        assert len(result) > 0
        assert (
            perf_result["duration"] < 0.5
        ), f"Large content sanitization too slow: {perf_result['duration']:.3f}s"


class TestDocumentProcessingPerformance:
    """Test document processing performance."""

    def setup_method(self):
        """Setup for each test method."""
        self.monitor = PerformanceMonitor()

    def test_text_extraction_performance(self):
        """Test text extraction performance."""
        # Create test content of various sizes
        test_contents = [
            b"Small content",
            b"Medium content " * 100,
            b"Large content " * 1000,
        ]

        measurement = self.monitor.start_measurement("text_extraction")

        results = []
        for content in test_contents:
            for i in range(10):  # Extract each size 10 times
                result = extract_text_from_file(content, f"test_{len(content)}.txt")
                results.append(result)

        perf_result = self.monitor.end_measurement(measurement)

        # Assertions
        assert len(results) == 30
        assert all(r is not None for r in results)
        assert (
            perf_result["duration"] < 1.0
        ), f"Text extraction too slow: {perf_result['duration']:.3f}s"

    def test_concurrent_document_processing(self):
        """Test concurrent document processing performance."""
        test_documents = [
            (f"Document content {i} " * 50).encode("utf-8") for i in range(20)
        ]

        def process_document(content):
            return extract_text_from_file(content, "test.txt")

        measurement = self.monitor.start_measurement("concurrent_document_processing")

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [
                executor.submit(process_document, content) for content in test_documents
            ]
            results = [future.result() for future in futures]

        perf_result = self.monitor.end_measurement(measurement)

        # Assertions
        assert len(results) == 20
        assert all(r is not None for r in results)
        assert (
            perf_result["duration"] < 2.0
        ), f"Concurrent document processing too slow: {perf_result['duration']:.3f}s"


@pytest.mark.skipif(
    not RESILIENCE_AVAILABLE, reason="Resilience components not available"
)
class TestResiliencePerformance:
    """Test resilience system performance."""

    def setup_method(self):
        """Setup for each test method."""
        self.monitor = PerformanceMonitor()

    def test_circuit_breaker_performance(self):
        """Test circuit breaker performance impact."""
        if not RESILIENCE_AVAILABLE:
            pytest.skip("Resilience components not available")

        resilience = OptimizedResilience()

        def test_operation():
            time.sleep(0.001)  # Simulate operation
            return "success"

        # Test normal operation performance
        measurement = self.monitor.start_measurement("circuit_breaker_normal")

        for i in range(100):
            result = resilience.execute_with_resilience(test_operation)
            assert result == "success"

        perf_result = self.monitor.end_measurement(measurement)

        # Circuit breaker should have minimal overhead
        assert (
            perf_result["duration"] < 1.0
        ), f"Circuit breaker overhead too high: {perf_result['duration']:.3f}s"

    def test_rate_limiter_performance(self):
        """Test rate limiter performance."""
        if not RESILIENCE_AVAILABLE:
            pytest.skip("Resilience components not available")

        rate_limiter = SmartRateLimiter(requests_per_second=100)

        measurement = self.monitor.start_measurement("rate_limiter")

        allowed_requests = 0
        for i in range(50):
            if rate_limiter.allow_request("test_key"):
                allowed_requests += 1

        perf_result = self.monitor.end_measurement(measurement)

        # Rate limiter should be fast
        assert (
            perf_result["duration"] < 0.1
        ), f"Rate limiter too slow: {perf_result['duration']:.3f}s"
        assert allowed_requests > 0, "Rate limiter blocked all requests"


class TestSystemPerformanceIntegration:
    """Test integrated system performance."""

    def setup_method(self):
        """Setup for each test method."""
        self.monitor = PerformanceMonitor()

    def test_end_to_end_performance(self):
        """Test end-to-end system performance."""
        # Simulate complete workflow
        measurement = self.monitor.start_measurement("end_to_end")

        # 1. Load configuration
        config_manager = get_config_manager()
        toetsregels = laad_toetsregels()

        # 2. Initialize components
        toetser = ModularToetser()
        sanitizer = get_sanitizer()

        # 3. Process content
        test_content = "Authenticatie is het proces van identiteitsverificatie in Nederlandse systemen."
        sanitized_content = sanitize_content(test_content)

        # 4. Validate definition
        result = toetser.validate_definition(sanitized_content, toetsregels)

        # 5. Process document
        doc_content = test_content.encode("utf-8")
        extracted_text = extract_text_from_file(doc_content, "test.txt")

        perf_result = self.monitor.end_measurement(measurement)

        # Assertions
        assert config_manager is not None
        assert len(toetsregels) > 0
        assert sanitized_content is not None
        assert result is not None
        assert extracted_text is not None

        # End-to-end should be fast
        assert (
            perf_result["duration"] < 1.0
        ), f"End-to-end workflow too slow: {perf_result['duration']:.3f}s"

    def test_sustained_load_performance(self):
        """Test performance under sustained load."""
        toetser = ModularToetser()
        toetsregels = laad_toetsregels()

        measurement = self.monitor.start_measurement("sustained_load")

        # Simulate sustained load for 30 seconds or 1000 operations, whichever comes first
        operations = 0
        start_time = time.time()

        while time.time() - start_time < 30 and operations < 1000:
            definition = (
                f"Load test definitie {operations} voor sustained performance testing."
            )
            result = toetser.validate_definition(definition, toetsregels)
            assert result is not None
            operations += 1

        perf_result = self.monitor.end_measurement(measurement)

        # Calculate sustained throughput
        throughput = operations / perf_result["duration"]

        # Assertions
        assert operations >= 100, f"Not enough operations completed: {operations}"
        assert (
            throughput >= 10
        ), f"Sustained throughput too low: {throughput:.2f} ops/sec"

        # Memory should not grow excessively
        assert (
            perf_result["memory_delta"] < 100 * 1024 * 1024
        ), f"Memory growth too high: {perf_result['memory_delta'] / 1024 / 1024:.2f}MB"


class TestPerformanceRegression:
    """Test for performance regressions."""

    def setup_method(self):
        """Setup for each test method."""
        self.monitor = PerformanceMonitor()

        # Performance baselines (in seconds)
        self.baselines = {
            "single_validation": 0.1,
            "config_loading": 0.02,
            "text_extraction": 0.01,
            "sanitization": 0.001,
            "cache_hit": 0.0001,
        }

    def test_performance_baselines(self):
        """Test that performance meets established baselines."""
        toetser = ModularToetser()
        toetsregels = laad_toetsregels()

        # Test single validation baseline
        start_time = time.time()
        result = toetser.validate_definition("Test definitie", toetsregels)
        validation_time = time.time() - start_time

        assert result is not None
        assert (
            validation_time < self.baselines["single_validation"]
        ), f"Validation regression: {validation_time:.3f}s > {self.baselines['single_validation']}s"

        # Test config loading baseline
        start_time = time.time()
        config_manager = get_config_manager()
        config_time = time.time() - start_time

        assert config_manager is not None
        assert (
            config_time < self.baselines["config_loading"]
        ), f"Config loading regression: {config_time:.3f}s > {self.baselines['config_loading']}s"

        # Test text extraction baseline
        start_time = time.time()
        extracted = extract_text_from_file(b"Test content", "test.txt")
        extraction_time = time.time() - start_time

        assert extracted is not None
        assert (
            extraction_time < self.baselines["text_extraction"]
        ), f"Text extraction regression: {extraction_time:.3f}s > {self.baselines['text_extraction']}s"

        # Test sanitization baseline
        start_time = time.time()
        sanitized = sanitize_content("Test content")
        sanitization_time = time.time() - start_time

        assert sanitized is not None
        assert (
            sanitization_time < self.baselines["sanitization"]
        ), f"Sanitization regression: {sanitization_time:.3f}s > {self.baselines['sanitization']}s"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
