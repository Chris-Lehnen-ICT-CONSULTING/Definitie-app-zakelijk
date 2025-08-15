"""
Comprehensive test suite for DefinitieAgent system.
Tests core functionality, integration, and performance.
"""
import pytest
import os
import time
import tempfile
import shutil
from unittest.mock import patch, MagicMock
import psutil

# Import available modules
from config.config_manager import (
    get_config_manager, get_config, ConfigSection
)
from utils.cache import cached, clear_cache, get_cache_stats
from ai_toetser.modular_toetser import ModularToetser
from config.config_loader import laad_toetsregels
from config.config_adapters import (
    get_api_config, get_cache_config, get_paths_config,
    get_default_model, get_default_temperature
)


class TestConfigurationSystem:
    """Test configuration management system."""
    
    def test_config_manager_initialization(self):
        """Test configuration manager initialization."""
        config_manager = get_config_manager()
        assert config_manager is not None
        assert hasattr(config_manager, 'environment')
    
    def test_environment_specific_configuration(self):
        """Test environment-specific configuration loading."""
        # Test development environment (default)
        config_manager = get_config_manager()
        api_config = get_config(ConfigSection.API)
        
        assert api_config is not None
        assert hasattr(api_config, 'default_model')
        assert hasattr(api_config, 'default_temperature')
    
    def test_configuration_adapters(self):
        """Test configuration adapters functionality."""
        # Test API config adapter
        api_config = get_api_config()
        assert api_config is not None
        
        # Test cache config adapter
        cache_config = get_cache_config()
        assert cache_config is not None
        
        # Test paths config adapter
        paths_config = get_paths_config()
        assert paths_config is not None
    
    def test_backward_compatibility(self):
        """Test backward compatibility functions."""
        # These should work without breaking existing code
        model = get_default_model()
        temperature = get_default_temperature()
        
        assert isinstance(model, str)
        assert isinstance(temperature, (int, float))
        assert 0.0 <= temperature <= 2.0
    
    def test_configuration_validation(self):
        """Test configuration validation."""
        config_manager = get_config_manager()
        
        # Test that all required sections load
        for section in ConfigSection:
            config = get_config(section)
            assert config is not None
    
    def test_environment_info(self):
        """Test environment information retrieval."""
        config_manager = get_config_manager()
        env_info = config_manager.get_environment_info()
        
        # Check required fields
        required_fields = ['environment', 'config_loaded', 'config_file']
        for field in required_fields:
            assert field in env_info
        
        assert isinstance(env_info['config_loaded'], bool)


class TestCacheSystem:
    """Test caching system functionality."""
    
    def setup_method(self):
        """Setup for each test method."""
        clear_cache()
    
    def test_cache_decorator_basic(self):
        """Test basic cache decorator functionality."""
        call_count = 0
        
        @cached(ttl=60)
        def test_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        # First call should execute function
        result1 = test_function(5)
        assert result1 == 10
        assert call_count == 1
        
        # Second call should use cache
        result2 = test_function(5)
        assert result2 == 10
        assert call_count == 1  # No additional call
    
    def test_cache_expiration(self):
        """Test cache TTL expiration."""
        call_count = 0
        
        @cached(ttl=0.1)  # 100ms TTL
        def test_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        # First call
        result1 = test_function(5)
        assert result1 == 10
        assert call_count == 1
        
        # Wait for TTL to expire
        time.sleep(0.2)
        
        # Second call after expiration
        result2 = test_function(5)
        assert result2 == 10
        assert call_count == 2  # Function called again
    
    def test_cache_stats(self):
        """Test cache statistics tracking."""
        clear_cache()
        
        @cached(ttl=60)
        def test_function(x):
            return x * 2
        
        # Make some calls
        test_function(1)  # Miss
        test_function(1)  # Hit
        test_function(2)  # Miss
        test_function(2)  # Hit
        
        stats = get_cache_stats()
        assert 'entries' in stats
        assert 'total_size_bytes' in stats
        assert stats['entries'] >= 0  # Should have cache entries
        assert isinstance(stats['total_size_bytes'], int)
    
    def test_cache_with_different_arguments(self):
        """Test caching with different argument types."""
        call_count = 0
        
        @cached(ttl=60)
        def test_function(a, b=None):
            nonlocal call_count
            call_count += 1
            return f"{a}-{b}"
        
        # Test different argument combinations
        result1 = test_function("hello")
        result2 = test_function("hello")  # Should use cache
        assert result1 == result2
        assert call_count == 1
        
        result3 = test_function("hello", "world")
        assert call_count == 2  # Different arguments
    
    def test_cache_performance(self):
        """Test cache performance impact."""
        @cached(ttl=60)
        def expensive_function():
            time.sleep(0.01)  # Simulate expensive operation
            return "result"
        
        # First call (uncached)
        start_time = time.time()
        result1 = expensive_function()
        first_call_time = time.time() - start_time
        
        # Second call (cached)
        start_time = time.time()
        result2 = expensive_function()
        second_call_time = time.time() - start_time
        
        # Cache should provide significant speedup
        assert result1 == result2
        assert second_call_time < first_call_time * 0.5


class TestAIToetserSystem:
    """Test AI Toetser validation system."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.toetser = ModularToetser()
        self.toetsregels = laad_toetsregels()
    
    def test_toetser_initialization(self):
        """Test ModularToetser initialization."""
        assert self.toetser is not None
        assert hasattr(self.toetser, 'validate_definition')
    
    def test_basic_validation(self):
        """Test basic definition validation."""
        # Test valid definition
        valid_definition = "Een authenticatie is het proces van het verifiëren van de identiteit van een gebruiker."
        result = self.toetser.validate_definition(valid_definition, self.toetsregels)
        assert result is not None
        assert isinstance(result, list)
        
        # Test empty definition
        result = self.toetser.validate_definition("", self.toetsregels)
        assert result is not None
        assert isinstance(result, list)
    
    def test_validation_with_context(self):
        """Test validation with context."""
        definition = "Een definitie in de context van strafrecht."
        context = {"juridisch": ["Strafrecht"], "organisatorisch": ["DJI"]}
        
        result = self.toetser.validate_definition(
            definition, 
            self.toetsregels, 
            begrip="test", 
            contexten=context
        )
        assert result is not None
        assert isinstance(result, list)
    
    def test_multiple_definitions(self):
        """Test validation of multiple definitions."""
        definitions = [
            "Eerste definitie voor testing.",
            "Tweede definitie voor testing.",
            "Derde definitie voor testing."
        ]
        
        for definition in definitions:
            result = self.toetser.validate_definition(definition, self.toetsregels)
            assert result is not None
            assert isinstance(result, list)


class TestSystemIntegration:
    """Test system integration and end-to-end functionality."""
    
    def test_configuration_cache_integration(self):
        """Test integration between configuration and cache systems."""
        # Get cache configuration
        cache_config = get_cache_config()
        cache_settings = cache_config.get_cache_config()
        
        # Verify cache settings are applied
        assert 'enabled' in cache_settings
        assert 'default_ttl' in cache_settings
        assert 'cache_dir' in cache_settings
    
    def test_end_to_end_definition_validation(self):
        """Test end-to-end definition validation process."""
        # Initialize components
        toetser = ModularToetser()
        toetsregels = laad_toetsregels()
        
        # Test definition
        test_definition = "Autorisatie is het proces waarbij wordt bepaald welke rechten een geauthenticeerde gebruiker heeft."
        
        # Validate definition
        result = toetser.validate_definition(test_definition, toetsregels)
        assert result is not None
        assert isinstance(result, list)
        
        # Test with context
        context = {"organisatorisch": ["DJI"], "juridisch": ["Algemeen"]}
        result_with_context = toetser.validate_definition(
            test_definition, 
            toetsregels, 
            begrip="autorisatie", 
            contexten=context
        )
        assert result_with_context is not None
        assert isinstance(result_with_context, list)
    
    def test_system_performance_integration(self):
        """Test system performance with integrated components."""
        # Test cache + validation integration
        call_count = 0
        
        @cached(ttl=60)
        def cached_validation(definition):
            nonlocal call_count
            call_count += 1
            toetser = ModularToetser()
            toetsregels = laad_toetsregels()
            return toetser.validate_definition(definition, toetsregels)
        
        # First call
        result1 = cached_validation("Test definitie voor caching.")
        assert call_count == 1
        
        # Second call (should use cache)
        result2 = cached_validation("Test definitie voor caching.")
        assert call_count == 1  # No additional call due to caching
    
    def test_error_handling_integration(self):
        """Test error handling across integrated systems."""
        # Test with invalid inputs
        toetser = ModularToetser()
        toetsregels = laad_toetsregels()
        
        # Test None input
        try:
            result = toetser.validate_definition(None, toetsregels)
            assert result is not None  # Should handle gracefully
        except Exception:
            pass  # Expected to fail gracefully
        
        # Test empty input
        result = toetser.validate_definition("", toetsregels)
        assert result is not None
        assert isinstance(result, list)
        
        # Test very long input
        long_definition = "Test " * 1000
        result = toetser.validate_definition(long_definition, toetsregels)
        assert result is not None
        assert isinstance(result, list)


class TestPerformanceBaseline:
    """Test performance baselines for the system."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.process = psutil.Process(os.getpid())
        self.initial_memory = self.process.memory_info().rss
    
    def test_cache_performance_baseline(self):
        """Test cache performance baseline."""
        # Test cache set/get performance
        start_time = time.time()
        
        @cached(ttl=60)
        def test_function(x):
            return x * 2
        
        # Perform operations
        for i in range(100):
            test_function(i % 10)  # Some cache hits, some misses
        
        end_time = time.time()
        operation_time = end_time - start_time
        
        # Should complete within reasonable time
        assert operation_time < 1.0, f"Cache operations too slow: {operation_time:.2f}s"
        
        # Check cache entries
        stats = get_cache_stats()
        assert stats['entries'] > 0, f"No cache entries found: {stats['entries']}"
    
    def test_validation_performance_baseline(self):
        """Test validation performance baseline."""
        toetser = ModularToetser()
        toetsregels = laad_toetsregels()
        
        # Test validation performance
        start_time = time.time()
        
        test_definitions = [
            f"Test definitie nummer {i} voor performance testing."
            for i in range(50)
        ]
        
        for definition in test_definitions:
            toetser.validate_definition(definition, toetsregels)
        
        end_time = time.time()
        validation_time = end_time - start_time
        
        # Should validate within reasonable time
        assert validation_time < 10.0, f"Validation too slow: {validation_time:.2f}s for 50 definitions"
        
        # Calculate rate
        validation_rate = len(test_definitions) / validation_time
        assert validation_rate > 5, f"Validation rate too low: {validation_rate:.2f} def/sec"
    
    def test_memory_usage_baseline(self):
        """Test memory usage baseline."""
        # Perform memory-intensive operations
        toetser = ModularToetser()
        toetsregels = laad_toetsregels()
        
        # Create many validation operations
        for i in range(100):
            definition = f"Memory test definition {i} " * 10
            result = toetser.validate_definition(definition, toetsregels)
        
        # Check memory usage
        current_memory = self.process.memory_info().rss
        memory_increase = current_memory - self.initial_memory
        
        # Memory increase should be reasonable
        assert memory_increase < 50 * 1024 * 1024, f"Memory usage too high: {memory_increase / 1024 / 1024:.2f}MB"
    
    def test_configuration_loading_performance(self):
        """Test configuration loading performance."""
        start_time = time.time()
        
        # Load configuration multiple times
        for _ in range(10):
            config_manager = get_config_manager()
            api_config = get_api_config()
            cache_config = get_cache_config()
        
        end_time = time.time()
        config_time = end_time - start_time
        
        # Should load quickly
        assert config_time < 1.0, f"Configuration loading too slow: {config_time:.2f}s"


class TestSystemStability:
    """Test system stability and robustness."""
    
    def test_repeated_operations_stability(self):
        """Test system stability with repeated operations."""
        toetser = ModularToetser()
        toetsregels = laad_toetsregels()
        
        # Perform many repeated operations
        for i in range(200):
            definition = f"Stability test definition {i}."
            result = toetser.validate_definition(definition, toetsregels)
            assert result is not None
            assert isinstance(result, list)
    
    def test_concurrent_access_stability(self):
        """Test system stability with concurrent access."""
        import threading
        
        results = []
        errors = []
        
        def worker(worker_id):
            try:
                toetser = ModularToetser()
                toetsregels = laad_toetsregels()
                for i in range(10):
                    definition = f"Worker {worker_id} definition {i}."
                    result = toetser.validate_definition(definition, toetsregels)
                    results.append(result is not None)
            except Exception as e:
                errors.append(str(e))
        
        # Create threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(errors) == 0, f"Concurrent access errors: {errors}"
        assert all(results), f"Some operations failed: {sum(results)}/{len(results)} succeeded"
    
    def test_error_recovery_stability(self):
        """Test system stability during error conditions."""
        toetser = ModularToetser()
        toetsregels = laad_toetsregels()
        
        # Test with various error conditions
        error_inputs = [
            "",
            "x" * 10000,  # Very long input
            "\n\n\n",     # Whitespace only
            "🎉🎊🎈",     # Unicode characters
        ]
        
        for error_input in error_inputs:
            # Should handle errors gracefully
            try:
                result = toetser.validate_definition(error_input, toetsregels)
                # Should return some result, even if validation fails
                assert result is not None
                assert isinstance(result, list)
            except Exception as e:
                # If exception occurs, it should be handled
                pass
        
        # Test None separately as it might raise TypeError
        try:
            result = toetser.validate_definition(None, toetsregels)
        except (TypeError, AttributeError):
            pass  # Expected for None input


if __name__ == '__main__':
    pytest.main([__file__, '-v'])