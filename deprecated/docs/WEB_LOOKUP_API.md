# Web Lookup API Documentation

**Version**: 2.0 (Modern Implementation)  
**Status**: Production Ready  
**Last Updated**: 2025-08-15

## 🔄 Migration Status

| Component | Status | Coverage | Notes |
|-----------|--------|----------|-------|
| **ModernWebLookupService** | ✅ Ready | 80% | Strangler Fig implementation |
| **WikipediaService** | ✅ Ready | 89% | Full MediaWiki API integration |
| **Test Suite** | ✅ Complete | 96% | 47 comprehensive tests |
| **Legacy Fallback** | ✅ Active | - | Zero downtime migration |

## 🚀 Quick Example

```python
from services.modern_web_lookup_service import ModernWebLookupService
from services.interfaces import LookupRequest

# Initialize
service = ModernWebLookupService()

# Simple lookup
request = LookupRequest(term="democratie", sources=["wikipedia"])
results = await service.lookup(request)

# Results
for result in results:
    print(f"{result.source.name}: {result.definition[:100]}...")
    print(f"Confidence: {result.source.confidence}")
```

## 📋 Interface Compliance

Implements `WebLookupServiceInterface`:

```python
class WebLookupServiceInterface(ABC):
    @abstractmethod
    async def lookup(self, request: LookupRequest) -> List[LookupResult]
    
    @abstractmethod  
    async def lookup_single_source(self, term: str, source: str) -> Optional[LookupResult]
    
    @abstractmethod
    def get_available_sources(self) -> List[WebSource]
    
    @abstractmethod
    def validate_source(self, text: str) -> WebSource
    
    @abstractmethod
    def find_juridical_references(self, text: str) -> List[JuridicalReference]
    
    @abstractmethod
    def detect_duplicates(self, term: str, definitions: List[str]) -> List[Dict[str, Any]]
```

## 🛠️ Service Configuration

### Source Types

| API Type | Description | Examples |
|----------|-------------|----------|
| `mediawiki` | MediaWiki API (Wikipedia family) | Wikipedia, Wiktionary |
| `sru` | Search/Retrieve via URL | overheid.nl, rechtspraak.nl |
| `scraping` | Web scraping (fallback) | Custom sites |
| `legacy` | Legacy implementation fallback | Original code |

### Confidence Scoring

| Confidence | Meaning | Use Case |
|------------|---------|----------|
| 0.95 | Exact match | Identical title match |
| 0.85 | High match | Partial title match |
| 0.70 | Good match | Related content |
| 0.50 | Default | Unknown/fallback |

## 📊 Performance Characteristics

### Concurrent Operations
```python
# Multiple terms simultaneously  
tasks = [service.lookup_single_source(term, "wikipedia") for term in terms]
results = await asyncio.gather(*tasks)
```

### Response Times (Typical)
- **Wikipedia API**: 200-500ms
- **Legacy Fallback**: 1-3s  
- **Concurrent (5 sources)**: 300-800ms
- **Cached Results**: <50ms

## 🧪 Testing Examples

### Unit Test Example
```python
@pytest.mark.asyncio
async def test_wikipedia_lookup():
    service = ModernWebLookupService()
    result = await service.lookup_single_source("Nederland", "wikipedia")
    
    assert result is not None
    assert result.success is True
    assert "Nederland" in result.definition
    assert result.source.confidence > 0.7
```

### Integration Test Example
```python
@pytest.mark.asyncio  
@pytest.mark.skipif(not os.getenv("RUN_INTEGRATION_TESTS"))
async def test_real_api():
    service = ModernWebLookupService()
    request = LookupRequest(term="democratie", max_results=2)
    results = await service.lookup(request)
    
    assert len(results) > 0
    assert any(r.success for r in results)
```

## 🔍 Error Handling

### Exception Types
- **`RuntimeError`**: Service not properly initialized
- **`ValueError`**: Invalid input parameters  
- **`ImportError`**: Missing dependencies (auto-handled)
- **`asyncio.TimeoutError`**: Request timeout (auto-retry)

### Error Response Format
```python
LookupResult(
    term="failed_term",
    source=WebSource(name="Wikipedia", url="", confidence=0.0),
    success=False,
    error_message="Specific error description"
)
```

## 🔄 Legacy Compatibility

### Automatic Fallback
```python
# Transparent fallback - no code changes needed
service = ModernWebLookupService()
results = await service.lookup(request)  # Will use legacy if modern fails
```

### Monitoring Fallback Usage
```python
# Check logs for fallback patterns
import logging
logging.basicConfig(level=logging.INFO)

# Look for:
# "Using legacy fallback for {term} in {source}"
# "Legacy fallback not available: {error}"
```

## 📈 Migration Path

### Phase 1: ✅ Complete
- Modern interface implementation
- Wikipedia API integration  
- Comprehensive test suite
- Legacy fallback system

### Phase 2: 🔄 In Progress  
- SRU API services (overheid.nl, rechtspraak.nl)
- A/B testing framework
- Performance monitoring

### Phase 3: 🔄 Planned
- Dependent module migration
- Legacy code removal
- Advanced features

## 🎯 Best Practices

### Recommended Usage
```python
# ✅ Good: Use async context properly
async def lookup_terms(terms: List[str]):
    service = ModernWebLookupService()
    results = []
    
    for term in terms:
        result = await service.lookup_single_source(term, "wikipedia")
        if result and result.success:
            results.append(result)
    
    return results

# ✅ Better: Concurrent operations
async def lookup_terms_concurrent(terms: List[str]):
    service = ModernWebLookupService() 
    
    tasks = [
        service.lookup_single_source(term, "wikipedia") 
        for term in terms
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [r for r in results if isinstance(r, LookupResult) and r.success]
```

### Error Handling Best Practices
```python
# ✅ Comprehensive error handling
async def safe_lookup(term: str):
    service = ModernWebLookupService()
    
    try:
        request = LookupRequest(term=term, timeout=10)
        results = await service.lookup(request)
        
        if not results:
            logger.warning(f"No results found for: {term}")
            return None
            
        return results[0]  # Best result
        
    except Exception as e:
        logger.error(f"Lookup failed for {term}: {e}")
        return None
```

---

**🔗 Related Documentation:**
- [Modern Web Lookup Guide](./MODERN_WEB_LOOKUP_GUIDE.md)
- [WEB_LOOKUP_REFACTOR_CONTEXT.md](../WEB_LOOKUP_REFACTOR_CONTEXT.md)  
- [Test Documentation](../tests/README.md)

**📞 Support**: Use BMAD `*help` command for assistance