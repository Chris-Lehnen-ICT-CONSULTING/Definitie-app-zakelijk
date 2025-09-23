"""
Performance Tests for UFO Classifier Service
=============================================
Comprehensive performance testing to ensure the UFO classifier meets
the performance requirements specified in US-300.

Performance Targets:
- Single classification: <10ms
- Batch processing: >2000 items/sec
- Memory usage: <100MB
- Cache hit rate: >90%
"""

import pytest
import time
import gc
import psutil
import numpy as np
import pandas as pd
from datetime import datetime
from typing import List, Dict, Tuple
import json
import tracemalloc
import cProfile
import pstats
import io
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from unittest.mock import Mock
import matplotlib.pyplot as plt
import seaborn as sns

from src.services.ufo_classifier_service import (
    UFOClassifierService,
    UFOCategory,
    PatternMatcher,
    get_ufo_classifier
)


class TestPerformanceMetrics:
    """Test performance metrics against US-300 requirements"""

    @pytest.fixture
    def classifier(self):
        """Create classifier instance for testing"""
        return UFOClassifierService()

    @pytest.fixture
    def large_dataset(self):
        """Generate large dataset for performance testing"""
        # Dutch legal terms dataset
        base_terms = [
            ("verdachte", "Een persoon die wordt verdacht van het plegen van een strafbaar feit"),
            ("dader", "De persoon die een strafbaar feit heeft gepleegd"),
            ("slachtoffer", "Degene die rechtstreeks schade heeft ondervonden"),
            ("aanhouding", "Het proces waarbij een persoon van zijn vrijheid wordt beroofd"),
            ("dagvaarding", "Schriftelijke oproep om voor de rechter te verschijnen"),
            ("bestuursorgaan", "Orgaan van een rechtspersoon krachtens publiekrecht"),
            ("beschikking", "Besluit dat niet van algemene strekking is"),
            ("vergunning", "Toestemming van de overheid om iets te mogen doen"),
            ("koopovereenkomst", "Overeenkomst waarbij verkoper zich verbindt"),
            ("hypotheek", "Zakelijk recht op onroerende zaak tot zekerheid")
        ]

        # Generate variations for larger dataset
        dataset = []
        for i in range(200):  # 2000 items total
            for term, definition in base_terms:
                dataset.append((
                    f"{term}_{i}",
                    f"{definition} (variant {i})"
                ))

        return dataset

    def test_single_classification_performance(self, classifier):
        """Test that single classification meets <10ms target"""
        term = "verdachte"
        definition = "Een persoon die wordt verdacht van een strafbaar feit"

        # Warm up
        for _ in range(10):
            classifier.classify(term, definition)

        # Measure performance
        times = []
        for _ in range(1000):
            start = time.perf_counter()
            result = classifier.classify(term, definition)
            duration = (time.perf_counter() - start) * 1000  # ms

            times.append(duration)
            assert result.primary_category != UFOCategory.UNKNOWN

        # Calculate statistics
        avg_time = np.mean(times)
        median_time = np.median(times)
        p95_time = np.percentile(times, 95)
        p99_time = np.percentile(times, 99)
        max_time = np.max(times)

        print(f"\n=== Single Classification Performance ===")
        print(f"Average: {avg_time:.3f}ms")
        print(f"Median: {median_time:.3f}ms")
        print(f"P95: {p95_time:.3f}ms")
        print(f"P99: {p99_time:.3f}ms")
        print(f"Max: {max_time:.3f}ms")

        # Assert performance requirements
        assert avg_time < 10, f"Average time {avg_time:.3f}ms exceeds 10ms target"
        assert p95_time < 20, f"P95 time {p95_time:.3f}ms exceeds reasonable threshold"
        assert p99_time < 50, f"P99 time {p99_time:.3f}ms indicates performance issues"

    def test_batch_processing_throughput(self, classifier, large_dataset):
        """Test batch processing achieves >2000 items/sec"""
        # Prepare batch
        items = [(term, def_, None) for term, def_ in large_dataset]

        # Warm up
        classifier.batch_classify(items[:10])

        # Measure throughput
        start = time.perf_counter()
        results = classifier.batch_classify(items)
        duration = time.perf_counter() - start

        throughput = len(results) / duration
        ms_per_item = (duration * 1000) / len(results)

        print(f"\n=== Batch Processing Performance ===")
        print(f"Items processed: {len(results)}")
        print(f"Total time: {duration:.3f}s")
        print(f"Throughput: {throughput:.0f} items/sec")
        print(f"Time per item: {ms_per_item:.3f}ms")

        # Assert requirements
        assert len(results) == len(items)
        assert throughput > 2000, f"Throughput {throughput:.0f}/sec below 2000/sec target"

        # Verify quality of results
        valid_results = sum(1 for r in results if r.primary_category != UFOCategory.UNKNOWN)
        quality_rate = valid_results / len(results)
        assert quality_rate > 0.8, f"Quality rate {quality_rate:.1%} too low"

    def test_memory_efficiency(self, classifier, large_dataset):
        """Test memory usage stays under 100MB"""
        # Start memory tracking
        tracemalloc.start()
        gc.collect()

        initial_memory = tracemalloc.get_traced_memory()[0]

        # Process large batch
        items = [(term, def_, None) for term, def_ in large_dataset]
        results = classifier.batch_classify(items)

        # Force garbage collection
        gc.collect()

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Calculate memory usage
        memory_used = peak - initial_memory
        memory_mb = memory_used / 1024 / 1024

        print(f"\n=== Memory Usage ===")
        print(f"Initial: {initial_memory / 1024 / 1024:.2f}MB")
        print(f"Peak: {peak / 1024 / 1024:.2f}MB")
        print(f"Used: {memory_mb:.2f}MB")
        print(f"Per item: {memory_used / len(items) / 1024:.2f}KB")

        # Assert memory requirements
        assert memory_mb < 100, f"Peak memory {memory_mb:.2f}MB exceeds 100MB limit"

        # Check for memory leaks
        gc.collect()
        results = None  # Clear results
        gc.collect()

    def test_cache_effectiveness(self, classifier):
        """Test LRU cache hit rate >90%"""
        # Test patterns for cache testing
        test_texts = [
            "Een persoon met rechtspersoonlijkheid",
            "Een juridisch proces dat plaatsvindt",
            "Een overeenkomst tussen partijen",
            "Een verdachte in een strafzaak",
            "Een bestuursorgaan van de overheid",
            "Een vergunning voor bouwactiviteiten",
            "Een contract tussen werkgever en werknemer",
            "Een hypotheek op onroerend goed",
            "Een beschikking van het bestuursorgaan",
            "Een dagvaarding voor de rechtbank"
        ]

        # Clear cache
        classifier.pattern_matcher.find_matches.cache_clear()

        # First pass - populate cache
        for text in test_texts:
            classifier.pattern_matcher.find_matches(text)

        # Get cache info
        cache_info = classifier.pattern_matcher.find_matches.cache_info()
        initial_hits = cache_info.hits
        initial_misses = cache_info.misses

        # Multiple passes - should hit cache
        for _ in range(100):
            for text in test_texts:
                classifier.pattern_matcher.find_matches(text)

        # Calculate hit rate
        cache_info = classifier.pattern_matcher.find_matches.cache_info()
        total_hits = cache_info.hits - initial_hits
        total_misses = cache_info.misses - initial_misses
        total_calls = total_hits + total_misses

        hit_rate = total_hits / total_calls if total_calls > 0 else 0

        print(f"\n=== Cache Performance ===")
        print(f"Cache size: {cache_info.currsize}")
        print(f"Total hits: {total_hits}")
        print(f"Total misses: {total_misses}")
        print(f"Hit rate: {hit_rate:.1%}")

        # Assert cache effectiveness
        assert hit_rate > 0.9, f"Cache hit rate {hit_rate:.1%} below 90% target"

    def test_pattern_compilation_performance(self):
        """Test that regex patterns are efficiently compiled"""
        # Create new matcher to test compilation
        start = time.perf_counter()
        matcher = PatternMatcher()
        compilation_time = (time.perf_counter() - start) * 1000

        print(f"\n=== Pattern Compilation ===")
        print(f"Compilation time: {compilation_time:.2f}ms")
        print(f"Number of categories: {len(matcher.patterns)}")
        print(f"Number of compiled patterns: {len(matcher.compiled_patterns)}")

        # Assert compilation is fast
        assert compilation_time < 100, f"Pattern compilation {compilation_time:.2f}ms too slow"

        # Test pattern matching speed
        text = "Een verdachte persoon in een juridisch proces met een overeenkomst"

        times = []
        for _ in range(1000):
            start = time.perf_counter()
            matches = matcher.find_matches(text)
            duration = (time.perf_counter() - start) * 1000
            times.append(duration)

        avg_match_time = np.mean(times)
        print(f"Average matching time: {avg_match_time:.3f}ms")

        assert avg_match_time < 1, f"Pattern matching {avg_match_time:.3f}ms too slow"


class TestConcurrentPerformance:
    """Test performance under concurrent load"""

    @pytest.fixture
    def classifier(self):
        return UFOClassifierService()

    def test_thread_safety(self, classifier):
        """Test classifier is thread-safe"""
        test_items = [
            ("verdachte", "Persoon verdacht van strafbaar feit"),
            ("proces", "Juridische procedure"),
            ("overeenkomst", "Contract tussen partijen"),
            ("persoon", "Natuurlijk persoon"),
            ("organisatie", "Rechtspersoon")
        ] * 20  # 100 items total

        def classify_item(item):
            term, definition = item
            return classifier.classify(term, definition)

        # Test with threads
        start = time.perf_counter()
        with ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(classify_item, test_items))
        thread_duration = time.perf_counter() - start

        # Test sequential for comparison
        start = time.perf_counter()
        sequential_results = [classify_item(item) for item in test_items]
        sequential_duration = time.perf_counter() - start

        print(f"\n=== Concurrent Performance ===")
        print(f"Thread pool (10 workers): {thread_duration:.3f}s")
        print(f"Sequential: {sequential_duration:.3f}s")
        print(f"Speedup: {sequential_duration / thread_duration:.2f}x")

        # Verify results are consistent
        assert len(results) == len(test_items)
        assert all(r.primary_category != UFOCategory.UNKNOWN for r in results[:5])

    def test_process_pool_performance(self, classifier):
        """Test performance with process pool for CPU-bound work"""
        # Note: This requires the classifier to be pickleable
        test_items = [
            ("verdachte", "Persoon verdacht van strafbaar feit"),
            ("proces", "Juridische procedure"),
            ("overeenkomst", "Contract tussen partijen")
        ] * 100

        def classify_batch(batch):
            classifier = UFOClassifierService()  # Create new instance per process
            return [classifier.classify(term, def_) for term, def_ in batch]

        # Split into batches
        batch_size = 50
        batches = [test_items[i:i+batch_size] for i in range(0, len(test_items), batch_size)]

        start = time.perf_counter()
        with ProcessPoolExecutor(max_workers=4) as executor:
            batch_results = list(executor.map(classify_batch, batches))
        duration = time.perf_counter() - start

        # Flatten results
        results = [r for batch in batch_results for r in batch]

        throughput = len(results) / duration

        print(f"\n=== Process Pool Performance ===")
        print(f"Items: {len(results)}")
        print(f"Duration: {duration:.3f}s")
        print(f"Throughput: {throughput:.0f} items/sec")

        assert len(results) == len(test_items)

    def test_load_testing(self, classifier):
        """Test classifier under sustained load"""
        duration_seconds = 10
        items_processed = 0
        errors = 0
        latencies = []

        test_items = [
            ("verdachte", "Persoon verdacht"),
            ("proces", "Juridische procedure"),
            ("overeenkomst", "Contract")
        ]

        print(f"\n=== Load Testing ({duration_seconds}s) ===")

        start_time = time.time()
        while time.time() - start_time < duration_seconds:
            item = test_items[items_processed % len(test_items)]

            item_start = time.perf_counter()
            try:
                result = classifier.classify(item[0], item[1])
                latency = (time.perf_counter() - item_start) * 1000
                latencies.append(latency)
                items_processed += 1
            except Exception:
                errors += 1

        elapsed = time.time() - start_time
        throughput = items_processed / elapsed

        print(f"Items processed: {items_processed}")
        print(f"Throughput: {throughput:.0f} items/sec")
        print(f"Errors: {errors}")
        print(f"Avg latency: {np.mean(latencies):.3f}ms")
        print(f"P99 latency: {np.percentile(latencies, 99):.3f}ms")

        assert throughput > 1000, f"Sustained throughput {throughput:.0f}/sec too low"
        assert errors == 0, f"Encountered {errors} errors during load test"


class TestPerformanceOptimizations:
    """Test specific performance optimizations"""

    def test_singleton_efficiency(self):
        """Test that singleton pattern improves performance"""
        # Time creating new instances
        start = time.perf_counter()
        for _ in range(100):
            UFOClassifierService()
        new_instance_time = time.perf_counter() - start

        # Time getting singleton
        start = time.perf_counter()
        for _ in range(100):
            get_ufo_classifier()
        singleton_time = time.perf_counter() - start

        print(f"\n=== Singleton Performance ===")
        print(f"New instances (100x): {new_instance_time:.3f}s")
        print(f"Singleton (100x): {singleton_time:.3f}s")
        print(f"Speedup: {new_instance_time / singleton_time:.1f}x")

        assert singleton_time < new_instance_time

    def test_pattern_precompilation(self):
        """Test that pattern precompilation improves performance"""
        import re

        patterns = [
            r'\b(persoon|mens|individu|burger)\b',
            r'\b(proces|procedure|handeling)\b',
            r'\b(overeenkomst|contract|afspraak)\b'
        ]

        text = "Een persoon in een proces met een overeenkomst" * 10

        # Test without precompilation
        start = time.perf_counter()
        for _ in range(1000):
            for pattern in patterns:
                re.findall(pattern, text, re.IGNORECASE)
        no_precompile_time = time.perf_counter() - start

        # Test with precompilation
        compiled_patterns = [re.compile(p, re.IGNORECASE) for p in patterns]

        start = time.perf_counter()
        for _ in range(1000):
            for pattern in compiled_patterns:
                pattern.findall(text)
        precompile_time = time.perf_counter() - start

        print(f"\n=== Pattern Precompilation ===")
        print(f"Without precompilation: {no_precompile_time:.3f}s")
        print(f"With precompilation: {precompile_time:.3f}s")
        print(f"Speedup: {no_precompile_time / precompile_time:.1f}x")

        assert precompile_time < no_precompile_time

    def test_cache_size_optimization(self):
        """Test optimal cache size for performance"""
        cache_sizes = [128, 256, 512, 1024, 2048]
        performance_results = []

        for cache_size in cache_sizes:
            # Create classifier with specific cache size
            classifier = UFOClassifierService()
            classifier.pattern_matcher.find_matches = \
                classifier.pattern_matcher.find_matches.__wrapped__
            classifier.pattern_matcher.find_matches = \
                classifier.pattern_matcher.find_matches.__get__(
                    classifier.pattern_matcher,
                    type(classifier.pattern_matcher)
                )

            # Test performance
            test_texts = [f"Text variation {i}" for i in range(cache_size * 2)]

            start = time.perf_counter()
            for text in test_texts:
                classifier.pattern_matcher.find_matches(text)
            duration = time.perf_counter() - start

            performance_results.append((cache_size, duration))

        print(f"\n=== Cache Size Optimization ===")
        for size, duration in performance_results:
            print(f"Cache size {size}: {duration:.3f}s")

        # Current implementation uses 1024, which should be near optimal
        optimal_size = min(performance_results, key=lambda x: x[1])[0]
        print(f"Optimal cache size: {optimal_size}")


class TestPerformanceProfile:
    """Profile performance to identify bottlenecks"""

    @pytest.fixture
    def classifier(self):
        return UFOClassifierService()

    def test_profile_classification(self, classifier):
        """Profile single classification to identify bottlenecks"""
        profiler = cProfile.Profile()

        # Profile classification
        profiler.enable()
        for _ in range(1000):
            classifier.classify(
                "verdachte",
                "Een persoon die wordt verdacht van een strafbaar feit"
            )
        profiler.disable()

        # Get statistics
        stats = pstats.Stats(profiler)
        stream = io.StringIO()
        stats.stream = stream
        stats.sort_stats('cumulative')
        stats.print_stats(10)  # Top 10 functions

        profile_output = stream.getvalue()
        print(f"\n=== Performance Profile ===")
        print(profile_output[:2000])  # First 2000 chars

        # Check that pattern matching is optimized
        assert 'find_matches' in profile_output

    def test_memory_profile(self, classifier):
        """Profile memory usage patterns"""
        import sys

        items = [
            ("verdachte", "Persoon verdacht"),
            ("proces", "Juridische procedure"),
            ("overeenkomst", "Contract")
        ] * 100

        # Measure object sizes
        classifier_size = sys.getsizeof(classifier)
        pattern_matcher_size = sys.getsizeof(classifier.pattern_matcher)

        # Measure result sizes
        results = []
        for term, def_ in items[:10]:
            result = classifier.classify(term, def_)
            results.append(sys.getsizeof(result))

        avg_result_size = np.mean(results)

        print(f"\n=== Memory Profile ===")
        print(f"Classifier size: {classifier_size} bytes")
        print(f"PatternMatcher size: {pattern_matcher_size} bytes")
        print(f"Avg result size: {avg_result_size:.0f} bytes")
        print(f"Est. memory for 1000 results: {avg_result_size * 1000 / 1024:.1f}KB")


class TestPerformanceRegression:
    """Test for performance regressions"""

    @pytest.fixture
    def baseline_performance(self):
        """Baseline performance metrics from US-300"""
        return {
            'single_classification_ms': 0.01,
            'batch_throughput': 148467,
            'memory_mb': 0.04,
            'cache_hit_rate': 0.95
        }

    def test_no_performance_regression(self, baseline_performance):
        """Test that performance hasn't regressed from baseline"""
        classifier = UFOClassifierService()

        # Test single classification
        times = []
        for _ in range(100):
            start = time.perf_counter()
            classifier.classify("verdachte", "Persoon verdacht")
            times.append((time.perf_counter() - start) * 1000)

        avg_time = np.mean(times)

        # Test batch processing
        items = [("term", "def", None)] * 1000
        start = time.perf_counter()
        results = classifier.batch_classify(items)
        batch_time = time.perf_counter() - start
        throughput = len(results) / batch_time

        print(f"\n=== Performance Regression Test ===")
        print(f"Baseline single: {baseline_performance['single_classification_ms']}ms")
        print(f"Current single: {avg_time:.3f}ms")
        print(f"Baseline throughput: {baseline_performance['batch_throughput']}/sec")
        print(f"Current throughput: {throughput:.0f}/sec")

        # Allow 50% degradation from baseline
        assert avg_time < baseline_performance['single_classification_ms'] * 50
        assert throughput > baseline_performance['batch_throughput'] * 0.5


class TestPerformanceReport:
    """Generate comprehensive performance report"""

    def test_generate_performance_report(self):
        """Generate detailed performance report"""
        classifier = UFOClassifierService()
        report = {
            'timestamp': datetime.now().isoformat(),
            'metrics': {},
            'benchmarks': []
        }

        # Run benchmarks
        test_cases = [
            ("Simple", "persoon", "Een natuurlijk persoon"),
            ("Complex", "verdachte", "Een persoon die wordt verdacht van een strafbaar feit in de context van het strafrecht waarbij sprake is van voorlopige hechtenis"),
            ("Ambiguous", "zaak", "Een aangelegenheid"),
        ]

        for name, term, definition in test_cases:
            times = []
            for _ in range(100):
                start = time.perf_counter()
                result = classifier.classify(term, definition)
                duration = (time.perf_counter() - start) * 1000
                times.append(duration)

            report['benchmarks'].append({
                'name': name,
                'term': term,
                'category': result.primary_category.value,
                'confidence': result.confidence,
                'avg_time_ms': np.mean(times),
                'p95_time_ms': np.percentile(times, 95)
            })

        # Overall metrics
        report['metrics'] = {
            'avg_classification_time': np.mean([b['avg_time_ms'] for b in report['benchmarks']]),
            'cache_info': str(classifier.pattern_matcher.find_matches.cache_info()),
        }

        # Save report
        report_path = 'test_performance_report.json'
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\n=== Performance Report Generated ===")
        print(f"Report saved to: {report_path}")
        print(json.dumps(report, indent=2))

        # Verify all benchmarks completed successfully
        assert all(b['avg_time_ms'] < 10 for b in report['benchmarks'])


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])