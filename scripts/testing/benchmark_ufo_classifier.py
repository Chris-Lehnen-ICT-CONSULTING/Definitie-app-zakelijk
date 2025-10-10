#!/usr/bin/env python3
"""
Benchmark script voor UFO Classifier performance testing.

Dit script meet de performance van de UFO classifier onder verschillende scenario's
en genereert een rapport met statistieken.
"""

import json
import statistics
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.services.ufo_classifier_service import (UFOCategory,
                                                 UFOClassifierService)


class UFOClassifierBenchmark:
    """Benchmark suite voor UFO Classifier."""

    def __init__(self):
        self.classifier = UFOClassifierService()
        self.test_data = self._load_test_data()
        self.results = {}

    def _load_test_data(self) -> list[tuple[str, str, UFOCategory]]:
        """Laad test data voor benchmarking."""
        return [
            # KIND examples
            (
                "Persoon",
                "Een natuurlijk mens met rechtspersoonlijkheid",
                UFOCategory.KIND,
            ),
            (
                "Organisatie",
                "Een rechtspersoon zoals een bedrijf of instelling",
                UFOCategory.KIND,
            ),
            (
                "Document",
                "Een schriftelijk stuk met juridische waarde",
                UFOCategory.KIND,
            ),
            ("Voorwerp", "Een fysiek object dat eigendom kan zijn", UFOCategory.KIND),
            ("Gebouw", "Een constructie met muren en een dak", UFOCategory.KIND),
            # EVENT examples
            (
                "Arrestatie",
                "Het proces waarbij een verdachte wordt aangehouden tijdens onderzoek",
                UFOCategory.EVENT,
            ),
            (
                "Zitting",
                "Een bijeenkomst van de rechtbank waar een zaak wordt behandeld",
                UFOCategory.EVENT,
            ),
            (
                "Procedure",
                "Een reeks handelingen die in bepaalde volgorde worden uitgevoerd",
                UFOCategory.EVENT,
            ),
            (
                "Onderzoek",
                "Het proces van het verzamelen en analyseren van informatie",
                UFOCategory.EVENT,
            ),
            (
                "Verhoor",
                "Het ondervragen van een verdachte of getuige",
                UFOCategory.EVENT,
            ),
            # ROLE examples
            (
                "Verdachte",
                "Een persoon in de hoedanigheid van mogelijke dader",
                UFOCategory.ROLE,
            ),
            (
                "Advocaat",
                "Een persoon in de rol van juridisch vertegenwoordiger",
                UFOCategory.ROLE,
            ),
            (
                "Rechter",
                "Een persoon fungerend als onpartijdige beslisser",
                UFOCategory.ROLE,
            ),
            (
                "Getuige",
                "Iemand in de rol van informatie verschaffer",
                UFOCategory.ROLE,
            ),
            (
                "Curator",
                "Een persoon aangesteld als beheerder van een faillissement",
                UFOCategory.ROLE,
            ),
            # RELATOR examples
            (
                "Contract",
                "Een overeenkomst tussen twee of meer partijen",
                UFOCategory.RELATOR,
            ),
            (
                "Huwelijk",
                "Een formele verbintenis tussen twee personen",
                UFOCategory.RELATOR,
            ),
            (
                "Vergunning",
                "Een toestemming verleend door een bevoegd gezag",
                UFOCategory.RELATOR,
            ),
            (
                "Dagvaarding",
                "Een oproep om voor de rechter te verschijnen",
                UFOCategory.RELATOR,
            ),
            (
                "Mandaat",
                "Een bevoegdheid verleend aan iemand om namens een ander te handelen",
                UFOCategory.RELATOR,
            ),
            # MODE examples
            (
                "Gezondheid",
                "De fysieke en mentale toestand van een persoon",
                UFOCategory.MODE,
            ),
            ("Locatie", "De plaats waar iets of iemand zich bevindt", UFOCategory.MODE),
            (
                "Status",
                "De actuele toestand van een zaak of procedure",
                UFOCategory.MODE,
            ),
            (
                "Eigenschap",
                "Een kenmerk dat aan iets wordt toegeschreven",
                UFOCategory.MODE,
            ),
            # QUANTITY examples
            (
                "Bedrag",
                "Een hoeveelheid geld uitgedrukt in euro's",
                UFOCategory.QUANTITY,
            ),
            (
                "Percentage",
                "Een deel uitgedrukt als fractie van 100",
                UFOCategory.QUANTITY,
            ),
            ("Duur", "De tijdspanne tussen begin en einde", UFOCategory.QUANTITY),
            (
                "Aantal",
                "Een meetbare hoeveelheid van discrete items",
                UFOCategory.QUANTITY,
            ),
            # QUALITY examples
            (
                "Betrouwbaarheid",
                "De mate waarin iets te vertrouwen is",
                UFOCategory.QUALITY,
            ),
            ("Ernst", "De graad van zwaarte van een situatie", UFOCategory.QUALITY),
            (
                "Relevantie",
                "De mate van belangrijkheid voor de zaak",
                UFOCategory.QUALITY,
            ),
            (
                "Waarschijnlijkheid",
                "De kans dat iets waar of juist is",
                UFOCategory.QUALITY,
            ),
            # PHASE examples
            (
                "Voorlopig",
                "Een tijdelijke fase in afwachting van definitieve status",
                UFOCategory.PHASE,
            ),
            ("Gesloten", "De eindstatus van een afgeronde zaak", UFOCategory.PHASE),
            (
                "In behandeling",
                "De fase waarin actief aan iets wordt gewerkt",
                UFOCategory.PHASE,
            ),
            ("Concept", "Een vroege ontwikkelingsfase", UFOCategory.PHASE),
        ]

    def benchmark_single_classification(self, iterations: int = 1000) -> dict:
        """Benchmark enkele classificaties."""
        print(f"\n📊 Benchmarking single classification ({iterations} iterations)...")

        times = []
        for i in range(iterations):
            term, definition, _ = self.test_data[i % len(self.test_data)]

            start = time.perf_counter()
            _ = self.classifier.classify(term, definition)
            end = time.perf_counter()

            times.append((end - start) * 1000)  # Convert to milliseconds

        return {
            "iterations": iterations,
            "mean_ms": statistics.mean(times),
            "median_ms": statistics.median(times),
            "stdev_ms": statistics.stdev(times) if len(times) > 1 else 0,
            "min_ms": min(times),
            "max_ms": max(times),
            "p95_ms": statistics.quantiles(times, n=20)[18],  # 95th percentile
            "p99_ms": statistics.quantiles(times, n=100)[98],  # 99th percentile
        }

    def benchmark_batch_classification(self, batch_sizes: list[int] = None) -> dict:
        """Benchmark batch classificaties."""
        if batch_sizes is None:
            batch_sizes = [10, 50, 100, 500]

        print("\n📊 Benchmarking batch classification...")

        results = {}
        for batch_size in batch_sizes:
            print(f"  Testing batch size: {batch_size}")

            # Prepare batch
            batch = []
            for i in range(batch_size):
                term, definition, _ = self.test_data[i % len(self.test_data)]
                batch.append((term, definition, None))

            # Measure
            times = []
            for _ in range(10):  # 10 iterations per batch size
                start = time.perf_counter()
                _ = self.classifier.batch_classify(batch)
                end = time.perf_counter()
                times.append((end - start) * 1000)

            results[batch_size] = {
                "mean_ms": statistics.mean(times),
                "median_ms": statistics.median(times),
                "per_item_ms": statistics.mean(times) / batch_size,
                "throughput_per_sec": (batch_size / statistics.mean(times)) * 1000,
            }

        return results

    def benchmark_accuracy(self) -> dict:
        """Benchmark classificatie accuraatheid."""
        print("\n📊 Benchmarking classification accuracy...")

        correct = 0
        high_confidence_correct = 0
        total = len(self.test_data)
        category_accuracy = {cat: {"correct": 0, "total": 0} for cat in UFOCategory}
        confidence_distribution = []

        for term, definition, expected in self.test_data:
            result = self.classifier.classify(term, definition)

            # Track overall accuracy
            if result.primary_category == expected:
                correct += 1
                if result.confidence >= 0.8:
                    high_confidence_correct += 1

            # Track per-category accuracy
            category_accuracy[expected]["total"] += 1
            if result.primary_category == expected:
                category_accuracy[expected]["correct"] += 1

            # Track confidence distribution
            confidence_distribution.append(result.confidence)

        # Calculate metrics
        accuracy_results = {
            "overall_accuracy": correct / total,
            "high_confidence_accuracy": high_confidence_correct / total,
            "mean_confidence": statistics.mean(confidence_distribution),
            "median_confidence": statistics.median(confidence_distribution),
            "category_accuracy": {},
        }

        for cat, stats in category_accuracy.items():
            if stats["total"] > 0:
                accuracy_results["category_accuracy"][cat.value] = {
                    "accuracy": stats["correct"] / stats["total"],
                    "total_samples": stats["total"],
                }

        return accuracy_results

    def benchmark_memory_usage(self) -> dict:
        """Benchmark geheugen gebruik."""
        import tracemalloc

        print("\n📊 Benchmarking memory usage...")

        # Start tracing
        tracemalloc.start()

        # Create new instance
        classifier = UFOClassifierService()

        # Classify all test data
        for term, definition, _ in self.test_data:
            _ = classifier.classify(term, definition)

        # Get memory stats
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        return {"current_mb": current / 1024 / 1024, "peak_mb": peak / 1024 / 1024}

    def benchmark_caching_effectiveness(self) -> dict:
        """Benchmark caching effectiviteit."""
        print("\n📊 Benchmarking caching effectiveness...")

        term, definition, _ = self.test_data[0]

        # First call (no cache)
        times_no_cache = []
        for _ in range(100):
            # Clear cache
            self.classifier.pattern_matcher.find_matches.cache_clear()

            start = time.perf_counter()
            _ = self.classifier.classify(term, definition)
            end = time.perf_counter()
            times_no_cache.append((end - start) * 1000)

        # Warm up cache
        _ = self.classifier.classify(term, definition)

        # Cached calls
        times_cached = []
        for _ in range(100):
            start = time.perf_counter()
            _ = self.classifier.classify(term, definition)
            end = time.perf_counter()
            times_cached.append((end - start) * 1000)

        return {
            "no_cache_mean_ms": statistics.mean(times_no_cache),
            "cached_mean_ms": statistics.mean(times_cached),
            "speedup_factor": statistics.mean(times_no_cache)
            / statistics.mean(times_cached),
            "cache_info": str(
                self.classifier.pattern_matcher.find_matches.cache_info()
            ),
        }

    def run_all_benchmarks(self) -> dict:
        """Draai alle benchmarks."""
        print("=" * 60)
        print("UFO CLASSIFIER PERFORMANCE BENCHMARK")
        print("=" * 60)

        results = {
            "single_classification": self.benchmark_single_classification(),
            "batch_classification": self.benchmark_batch_classification(),
            "accuracy": self.benchmark_accuracy(),
            "memory_usage": self.benchmark_memory_usage(),
            "caching": self.benchmark_caching_effectiveness(),
        }

        return results

    def print_report(self, results: dict):
        """Print een mooi geformateerd rapport."""
        print("\n" + "=" * 60)
        print("BENCHMARK RESULTS")
        print("=" * 60)

        # Single classification
        print("\n🎯 Single Classification Performance:")
        single = results["single_classification"]
        print(f"  • Mean time: {single['mean_ms']:.2f} ms")
        print(f"  • Median time: {single['median_ms']:.2f} ms")
        print(f"  • Min/Max: {single['min_ms']:.2f} / {single['max_ms']:.2f} ms")
        print(f"  • P95: {single['p95_ms']:.2f} ms")
        print(f"  • P99: {single['p99_ms']:.2f} ms")
        print(f"  • Throughput: {1000/single['mean_ms']:.0f} classifications/sec")

        # Batch classification
        print("\n📦 Batch Classification Performance:")
        for batch_size, metrics in results["batch_classification"].items():
            print(f"  Batch size {batch_size}:")
            print(f"    • Total time: {metrics['mean_ms']:.2f} ms")
            print(f"    • Per item: {metrics['per_item_ms']:.3f} ms")
            print(f"    • Throughput: {metrics['throughput_per_sec']:.0f} items/sec")

        # Accuracy
        print("\n✅ Classification Accuracy:")
        acc = results["accuracy"]
        print(f"  • Overall accuracy: {acc['overall_accuracy']:.1%}")
        print(f"  • High confidence accuracy: {acc['high_confidence_accuracy']:.1%}")
        print(f"  • Mean confidence: {acc['mean_confidence']:.2f}")
        print("\n  Per category accuracy:")
        for cat, stats in acc["category_accuracy"].items():
            print(
                f"    • {cat}: {stats['accuracy']:.1%} ({stats['total_samples']} samples)"
            )

        # Memory usage
        print("\n💾 Memory Usage:")
        mem = results["memory_usage"]
        print(f"  • Current: {mem['current_mb']:.2f} MB")
        print(f"  • Peak: {mem['peak_mb']:.2f} MB")

        # Caching
        print("\n⚡ Caching Effectiveness:")
        cache = results["caching"]
        print(f"  • No cache: {cache['no_cache_mean_ms']:.2f} ms")
        print(f"  • With cache: {cache['cached_mean_ms']:.2f} ms")
        print(f"  • Speedup: {cache['speedup_factor']:.1f}x")
        print(f"  • Cache stats: {cache['cache_info']}")

    def save_results(self, results: dict, filename: str = "benchmark_results.json"):
        """Sla resultaten op in JSON formaat."""
        output_path = Path(__file__).parent / filename

        with open(output_path, "w") as f:
            json.dump(results, f, indent=2, default=str)

        print(f"\n📁 Results saved to: {output_path}")


def main():
    """Main entry point."""
    benchmark = UFOClassifierBenchmark()

    # Run benchmarks
    results = benchmark.run_all_benchmarks()

    # Print report
    benchmark.print_report(results)

    # Save results
    benchmark.save_results(results)

    # Check performance targets
    print("\n" + "=" * 60)
    print("PERFORMANCE TARGETS CHECK")
    print("=" * 60)

    targets_met = []
    targets_failed = []

    # Check single classification < 10ms
    if results["single_classification"]["mean_ms"] < 10:
        targets_met.append("✅ Single classification < 10ms")
    else:
        targets_failed.append("❌ Single classification >= 10ms")

    # Check accuracy > 80% for high confidence
    if results["accuracy"]["high_confidence_accuracy"] > 0.8:
        targets_met.append("✅ High confidence accuracy > 80%")
    else:
        targets_failed.append("❌ High confidence accuracy <= 80%")

    # Check memory < 100MB
    if results["memory_usage"]["peak_mb"] < 100:
        targets_met.append("✅ Memory usage < 100MB")
    else:
        targets_failed.append("❌ Memory usage >= 100MB")

    # Check caching speedup > 2x
    if results["caching"]["speedup_factor"] > 2:
        targets_met.append("✅ Caching speedup > 2x")
    else:
        targets_failed.append("❌ Caching speedup <= 2x")

    # Print results
    for target in targets_met:
        print(target)
    for target in targets_failed:
        print(target)

    print(
        f"\nOverall: {len(targets_met)}/{len(targets_met) + len(targets_failed)} targets met"
    )

    return len(targets_failed) == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
