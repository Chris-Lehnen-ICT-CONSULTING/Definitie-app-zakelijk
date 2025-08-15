"""
Demo script voor A/B Testing Framework.

Demonstreert de A/B testing functionaliteit voor vergelijking
tussen legacy en moderne web lookup implementaties.
"""

import asyncio
import logging
import sys
import os
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services.ab_testing_framework import (
    ABTestingFramework, ABTestConfig, TestVariant,
    quick_ab_test, ab_test_with_report
)
from services.modern_web_lookup_service import ModernWebLookupService
from services.interfaces import LookupRequest

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def demo_basic_ab_testing():
    """Demo van basis A/B testing functionaliteit."""
    print("🧪 A/B Testing Framework Demo - Basic Functionality")
    print("=" * 70)
    
    # Configuration voor tests
    config = ABTestConfig(
        test_terms=["strafrecht", "burgerlijk recht", "grondwet"],
        max_results_per_service=3,
        timeout_seconds=20,
        repeat_count=2,
        include_performance=True,
        include_quality=True
    )
    
    framework = ABTestingFramework(config)
    
    print(f"\n📋 Test Configuration:")
    print(f"  Termen: {config.test_terms}")
    print(f"  Max resultaten per service: {config.max_results_per_service}")
    print(f"  Timeout: {config.timeout_seconds}s")
    print(f"  Herhalingen: {config.repeat_count}")
    print(f"  Performance analyse: {'Ja' if config.include_performance else 'Nee'}")
    print(f"  Quality analyse: {'Ja' if config.include_quality else 'Nee'}")
    
    # Test verschillende varianten
    test_cases = [
        ("Modern Only", TestVariant.MODERN, ["recht"]),
        ("Legacy Only", TestVariant.LEGACY, ["wet"]),
        ("Both Implementations", TestVariant.BOTH, ["artikel"])
    ]
    
    for test_name, variant, terms in test_cases:
        print(f"\n🔬 {test_name} Test")
        print("-" * 40)
        
        try:
            start_time = time.time()
            results = await framework.run_comparison(terms, variant)
            duration = time.time() - start_time
            
            if results:
                result = results[0]
                print(f"✅ Test completed in {duration:.2f}s")
                print(f"   Term: '{result.term}'")
                print(f"   Recommendation: {result.recommendation.value}")
                print(f"   Confidence: {result.confidence:.2f}")
                print(f"   Modern results: {result.modern_performance.results_count}")
                print(f"   Legacy results: {result.legacy_performance.results_count}")
                print(f"   Modern response time: {result.modern_performance.response_time:.2f}s")
                print(f"   Legacy response time: {result.legacy_performance.response_time:.2f}s")
                print(f"   Notes: {result.notes}")
            else:
                print("❌ No results returned")
                
        except Exception as e:
            print(f"❌ Test failed: {e}")
            logger.exception(f"Test error for {test_name}")


async def demo_comprehensive_comparison():
    """Demo van comprehensive vergelijking met meerdere termen."""
    print(f"\n📊 Comprehensive A/B Testing - Multiple Terms")
    print("=" * 60)
    
    # Juridische termen die goede vergelijking mogelijk maken
    juridical_terms = [
        "wetboek van strafrecht",
        "burgerlijk wetboek", 
        "grondwet",
        "rechtspraak",
        "verdrag",
        "artikel 1",
        "wet op de inkomstenbelasting"
    ]
    
    # Algemene termen
    general_terms = [
        "democratie",
        "regering",
        "parlement",
        "constitutie"
    ]
    
    print(f"\n⚖️ Testing Juridische Termen ({len(juridical_terms)} terms)")
    print("-" * 50)
    
    config = ABTestConfig(
        max_results_per_service=2,
        timeout_seconds=15,
        repeat_count=1,  # Reduced voor demo snelheid
        include_performance=True,
        include_quality=True
    )
    
    framework = ABTestingFramework(config)
    
    try:
        start_time = time.time()
        juridical_results = await framework.run_comparison(
            juridical_terms[:3],  # Test eerste 3 voor demo
            TestVariant.BOTH
        )
        juridical_duration = time.time() - start_time
        
        print(f"✅ Juridical test completed in {juridical_duration:.2f}s")
        
        # Analyseer resultaten
        modern_wins = sum(1 for r in juridical_results if r.recommendation == TestVariant.MODERN)
        legacy_wins = sum(1 for r in juridical_results if r.recommendation == TestVariant.LEGACY)
        mixed_results = sum(1 for r in juridical_results if r.recommendation == TestVariant.BOTH)
        
        print(f"\n📈 Juridical Terms Analysis:")
        print(f"  Modern preferred: {modern_wins}/{len(juridical_results)} ({modern_wins/len(juridical_results)*100:.1f}%)")
        print(f"  Legacy preferred: {legacy_wins}/{len(juridical_results)} ({legacy_wins/len(juridical_results)*100:.1f}%)")
        print(f"  Mixed/No clear winner: {mixed_results}/{len(juridical_results)} ({mixed_results/len(juridical_results)*100:.1f}%)")
        
        # Performance vergelijking
        modern_times = [r.modern_performance.response_time for r in juridical_results 
                       if r.modern_performance.response_time > 0]
        legacy_times = [r.legacy_performance.response_time for r in juridical_results 
                       if r.legacy_performance.response_time > 0]
        
        if modern_times and legacy_times:
            avg_modern = sum(modern_times) / len(modern_times)
            avg_legacy = sum(legacy_times) / len(legacy_times)
            
            print(f"\n⚡ Performance Comparison:")
            print(f"  Modern avg response: {avg_modern:.2f}s")
            print(f"  Legacy avg response: {avg_legacy:.2f}s")
            print(f"  Performance improvement: {((avg_legacy - avg_modern) / avg_legacy * 100):.1f}%")
        
        # Top resultaten details
        print(f"\n🎯 Best Performing Tests:")
        sorted_results = sorted(juridical_results, key=lambda r: r.confidence, reverse=True)
        for i, result in enumerate(sorted_results[:2], 1):
            print(f"  {i}. '{result.term}' - {result.recommendation.value} (confidence: {result.confidence:.2f})")
            print(f"     {result.notes}")
            
    except Exception as e:
        print(f"❌ Comprehensive test failed: {e}")
        logger.exception("Comprehensive test error")


async def demo_performance_focus():
    """Demo met focus op performance metrics."""
    print(f"\n⚡ Performance-Focused A/B Testing")
    print("=" * 50)
    
    # Terms die verschillende performance profielen kunnen hebben
    performance_terms = ["recht", "wet", "artikel"]
    
    config = ABTestConfig(
        max_results_per_service=5,
        timeout_seconds=30,
        repeat_count=3,  # Meer herhalingen voor betrouwbare performance data
        include_performance=True,
        include_quality=False  # Focus alleen op performance
    )
    
    framework = ABTestingFramework(config)
    
    print(f"\n🏃‍♂️ Running Performance Tests...")
    print(f"   Terms: {performance_terms}")
    print(f"   Repeat count: {config.repeat_count} (for statistical significance)")
    print(f"   Max results per service: {config.max_results_per_service}")
    
    try:
        start_time = time.time()
        results = await framework.run_comparison(performance_terms, TestVariant.BOTH)
        total_duration = time.time() - start_time
        
        print(f"\n📊 Performance Test Results (Total time: {total_duration:.2f}s)")
        print("-" * 60)
        
        # Detailed performance analysis
        all_modern_times = []
        all_legacy_times = []
        all_modern_success_rates = []
        all_legacy_success_rates = []
        
        for result in results:
            if result.modern_performance.response_time > 0:
                all_modern_times.append(result.modern_performance.response_time)
                all_modern_success_rates.append(result.modern_performance.success_rate)
            
            if result.legacy_performance.response_time > 0:
                all_legacy_times.append(result.legacy_performance.response_time)
                all_legacy_success_rates.append(result.legacy_performance.success_rate)
            
            print(f"Term: '{result.term}'")
            print(f"  Modern: {result.modern_performance.response_time:.2f}s, "
                  f"success: {result.modern_performance.success_rate:.1%}, "
                  f"results: {result.modern_performance.results_count}")
            print(f"  Legacy: {result.legacy_performance.response_time:.2f}s, "
                  f"success: {result.legacy_performance.success_rate:.1%}, "
                  f"results: {result.legacy_performance.results_count}")
            print(f"  Winner: {result.recommendation.value} (confidence: {result.confidence:.2f})")
            print()
        
        # Summary statistics
        if all_modern_times and all_legacy_times:
            print(f"📈 Performance Summary:")
            print(f"  Modern - Avg: {sum(all_modern_times)/len(all_modern_times):.2f}s, "
                  f"Min: {min(all_modern_times):.2f}s, Max: {max(all_modern_times):.2f}s")
            print(f"  Legacy - Avg: {sum(all_legacy_times)/len(all_legacy_times):.2f}s, "
                  f"Min: {min(all_legacy_times):.2f}s, Max: {max(all_legacy_times):.2f}s")
            
            print(f"  Modern Success Rate: {sum(all_modern_success_rates)/len(all_modern_success_rates):.1%}")
            print(f"  Legacy Success Rate: {sum(all_legacy_success_rates)/len(all_legacy_success_rates):.1%}")
            
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        logger.exception("Performance test error")


async def demo_convenience_functions():
    """Demo van convenience functies voor A/B testing."""
    print(f"\n🛠️ Convenience Functions Demo")
    print("=" * 40)
    
    # Quick A/B test
    print(f"\n⚡ Quick A/B Test")
    try:
        start_time = time.time()
        results = await quick_ab_test(["constitutie"])
        duration = time.time() - start_time
        
        if results:
            result = results[0]
            print(f"✅ Quick test completed in {duration:.2f}s")
            print(f"   Term: '{result.term}'")
            print(f"   Recommendation: {result.recommendation.value}")
            print(f"   Confidence: {result.confidence:.2f}")
        else:
            print("❌ Quick test returned no results")
            
    except Exception as e:
        print(f"❌ Quick test failed: {e}")
    
    # A/B test with report
    print(f"\n📋 A/B Test with Automatic Report")
    try:
        start_time = time.time()
        report = await ab_test_with_report(["democratie", "regering"])
        duration = time.time() - start_time
        
        print(f"✅ Report test completed in {duration:.2f}s")
        print(f"\n📄 Generated Report:")
        print("-" * 40)
        # Show first part of report (truncated for demo)
        report_lines = report.split('\n')
        for line in report_lines[:15]:  # Show first 15 lines
            print(line)
        
        if len(report_lines) > 15:
            print("... (report truncated for demo)")
            
    except Exception as e:
        print(f"❌ Report test failed: {e}")


async def demo_framework_features():
    """Demo van geavanceerde framework features."""
    print(f"\n🔧 Advanced Framework Features")
    print("=" * 45)
    
    config = ABTestConfig(
        test_terms=["test1", "test2"],
        max_results_per_service=2,
        timeout_seconds=10,
        repeat_count=1
    )
    
    framework = ABTestingFramework(config)
    
    # Test history management
    print(f"\n📚 Test History Management")
    
    # Run a test to generate history
    await framework.run_comparison(["rechtsstaat"], TestVariant.MODERN)
    
    history = framework.get_test_history()
    print(f"✅ Test history contains {len(history)} entries")
    
    if history:
        latest = history[-1]
        print(f"   Latest test: '{latest.term}' -> {latest.recommendation.value}")
    
    # Clear history
    framework.clear_history()
    history_after_clear = framework.get_test_history()
    print(f"✅ History cleared: {len(history_after_clear)} entries remaining")
    
    # Configuration variations
    print(f"\n⚙️ Configuration Variations")
    
    # High performance config
    perf_config = ABTestConfig(
        max_results_per_service=1,
        timeout_seconds=5,
        repeat_count=1,
        include_performance=True,
        include_quality=False
    )
    
    print(f"  Performance-focused config: timeout={perf_config.timeout_seconds}s, "
          f"repeats={perf_config.repeat_count}")
    
    # Quality focused config
    quality_config = ABTestConfig(
        max_results_per_service=5,
        timeout_seconds=30,
        repeat_count=2,
        include_performance=False,
        include_quality=True
    )
    
    print(f"  Quality-focused config: max_results={quality_config.max_results_per_service}, "
          f"quality_analysis={quality_config.include_quality}")


async def demo_integration_with_modern_service():
    """Demo van integratie met ModernWebLookupService."""
    print(f"\n🔗 Integration with ModernWebLookupService")
    print("=" * 50)
    
    # Toon beschikbare bronnen in moderne service
    modern_service = ModernWebLookupService()
    sources = modern_service.get_available_sources()
    
    print(f"\n📋 Available Sources in Modern Service:")
    for source in sources:
        status = "✅" if source.api_type in ["mediawiki", "sru"] else "🔄"
        print(f"  {status} {source.name} ({source.api_type}) - Confidence: {source.confidence:.2f}")
        print(f"      Juridical: {'Yes' if source.is_juridical else 'No'}, URL: {source.url}")
    
    # Test hoe A/B framework samenwerkt met moderne service
    print(f"\n🧪 A/B Framework + Modern Service Test")
    
    config = ABTestConfig(
        max_results_per_service=2,
        timeout_seconds=15,
        repeat_count=1
    )
    
    framework = ABTestingFramework(config)
    
    try:
        # Test een juridische term die zou moeten profiteren van SRU sources
        juridical_term = "wetboek"
        
        print(f"Testing term: '{juridical_term}' (should favor SRU sources)")
        
        results = await framework.run_comparison([juridical_term], TestVariant.MODERN)
        
        if results:
            result = results[0]
            print(f"✅ Integration test completed")
            print(f"   Modern results found: {result.modern_performance.results_count}")
            print(f"   Response time: {result.modern_performance.response_time:.2f}s")
            print(f"   Success rate: {result.modern_performance.success_rate:.1%}")
            
            # Show which sources were likely used (based on result analysis)
            if result.modern_results:
                sources_used = set(r.source.name for r in result.modern_results)
                print(f"   Sources used: {', '.join(sources_used)}")
        else:
            print("❌ No integration test results")
            
    except Exception as e:
        print(f"❌ Integration test failed: {e}")


async def main():
    """Main demo functie."""
    print("A/B Testing Framework - Comprehensive Demo")
    print("=" * 80)
    print("Dit script demonstreert de A/B testing functionaliteit voor")
    print("vergelijking tussen legacy en moderne web lookup implementaties.")
    print()
    
    try:
        # Basic functionality
        await demo_basic_ab_testing()
        
        # Comprehensive comparison
        await demo_comprehensive_comparison()
        
        # Performance focus
        await demo_performance_focus()
        
        # Convenience functions
        await demo_convenience_functions()
        
        # Advanced features
        await demo_framework_features()
        
        # Integration demo
        await demo_integration_with_modern_service()
        
        print(f"\n🎯 Demo Summary")
        print("=" * 40)
        print("✅ Basic A/B testing functionality demonstrated")
        print("✅ Comprehensive multi-term comparison shown")
        print("✅ Performance-focused testing showcased")
        print("✅ Convenience functions demonstrated")
        print("✅ Advanced framework features explored")
        print("✅ Integration with ModernWebLookupService tested")
        
        print(f"\n📋 Next Steps for Implementation:")
        print("1. 🧪 Run comprehensive tests: python -m pytest tests/test_ab_testing_framework.py -v")
        print("2. 📊 Use A/B testing voor migration decisions")
        print("3. 🔍 Implement remaining services (Wiktionary)")
        print("4. 📈 Add performance monitoring")
        print("5. 🚀 Begin gradual migration with confidence")
        
    except KeyboardInterrupt:
        print(f"\n❌ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        logger.exception("Demo error")


if __name__ == "__main__":
    asyncio.run(main())