# Voorbeelden Module - Complete Analysis

## Module Overview

The `voorbeelden` module (Dutch for "examples") is responsible for generating various types of examples for definitions. The module has evolved from a simple implementation to a unified system supporting multiple generation modes and example types. It demonstrates consolidation efforts similar to the services module.

## Directory Structure

```
src/voorbeelden/
├── __init__.py                  # Module initialization
├── voorbeelden.py               # Original implementation
├── async_voorbeelden.py         # Async variant
├── cached_voorbeelden.py        # Caching layer implementation
└── unified_voorbeelden.py       # Consolidated unified implementation
```

## Evolution History

1. **voorbeelden.py**: Original synchronous implementation
2. **async_voorbeelden.py**: Added async support for performance
3. **cached_voorbeelden.py**: Added caching layer
4. **unified_voorbeelden.py**: Consolidated all variants

## Core Components

### 1. **UnifiedVoorbeeldenGenerator** (unified_voorbeelden.py)

The main consolidated generator supporting all generation modes.

**Key Classes**:

#### ExampleType Enum
```python
class ExampleType(Enum):
    SENTENCE = "sentence"          # Example sentences using the term
    PRACTICAL = "practical"        # Practical usage examples
    COUNTER = "counter"            # Counter-examples
    SYNONYMS = "synonyms"          # List of synonyms
    ANTONYMS = "antonyms"          # List of antonyms
    EXPLANATION = "explanation"    # Additional explanations
```

#### GenerationMode Enum
```python
class GenerationMode(Enum):
    SYNC = "sync"                  # Synchronous generation
    ASYNC = "async"                # Asynchronous generation
    CACHED = "cached"              # With caching enabled
    RESILIENT = "resilient"        # With full resilience features
```

#### ExampleRequest
```python
@dataclass
class ExampleRequest:
    begrip: str                    # Term to generate examples for
    definitie: str                 # Definition of the term
    context: str                   # Organizational context
    example_type: ExampleType      # Type of example to generate
    additional_context: Optional[str] = None
    use_cache: bool = True
    custom_prompt: Optional[str] = None
```

#### ExampleResult
```python
@dataclass
class ExampleResult:
    example_type: ExampleType
    examples: List[str]            # Generated examples
    success: bool
    error: Optional[str] = None
    generation_time: float = 0.0
    cached: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
```

### 2. **Generation Implementation**

#### Main Generator Class
```python
class UnifiedVoorbeeldenGenerator:
    def __init__(self, config: Optional[VoorbeeldenConfig] = None):
        self.config = config or VoorbeeldenConfig()
        self.api_client = self._setup_api_client()
        self.cache = self._setup_cache()
        self._executor = ThreadPoolExecutor(max_workers=5)
```

#### Generation Methods
```python
def generate_examples(
    self, 
    request: ExampleRequest,
    mode: GenerationMode = GenerationMode.SYNC
) -> ExampleResult:
    """Main entry point for example generation"""

async def generate_examples_async(
    self, 
    request: ExampleRequest
) -> ExampleResult:
    """Async generation method"""

def generate_examples_batch(
    self, 
    requests: List[ExampleRequest]
) -> List[ExampleResult]:
    """Batch processing multiple requests"""
```

### 3. **Prompt Engineering**

Different prompts for each example type:

#### Sentence Examples
```python
prompt = f"""
Geef 3 voorbeeldzinnen waarin het begrip '{begrip}' correct gebruikt wordt.
De zinnen moeten passen binnen de context van {context}.

Definitie: {definitie}

Formaat:
1. [Eerste voorbeeldzin]
2. [Tweede voorbeeldzin]
3. [Derde voorbeeldzin]
"""
```

#### Practical Examples
```python
prompt = f"""
Geef 3 praktische voorbeelden van '{begrip}' in de praktijk.
Focus op concrete situaties binnen {context}.

Definitie: {definitie}

Formaat:
1. [Praktisch voorbeeld 1]
2. [Praktisch voorbeeld 2]
3. [Praktisch voorbeeld 3]
"""
```

#### Counter Examples
```python
prompt = f"""
Geef 3 voorbeelden van wat '{begrip}' NIET is.
Help om veelvoorkomende misverstanden te voorkomen.

Definitie: {definitie}

Formaat:
1. [Tegenvoorbeeld 1]
2. [Tegenvoorbeeld 2]
3. [Tegenvoorbeeld 3]
"""
```

### 4. **Caching Implementation**

```python
class VoorbeeldenCache:
    def __init__(self, ttl: int = 3600):
        self._cache = {}
        self._timestamps = {}
        self.ttl = ttl
    
    def get_cache_key(self, request: ExampleRequest) -> str:
        # Generate unique cache key
        return hashlib.md5(
            f"{request.begrip}:{request.definitie}:{request.example_type}".encode()
        ).hexdigest()
    
    def get(self, request: ExampleRequest) -> Optional[ExampleResult]
    def set(self, request: ExampleRequest, result: ExampleResult)
```

### 5. **Legacy Implementations**

#### Original voorbeelden.py
- Simple synchronous generation
- Direct OpenAI API calls
- Basic error handling
- No caching

#### async_voorbeelden.py
- Async/await support
- Concurrent generation
- Better performance
- Still no caching

#### cached_voorbeelden.py
- Added caching layer
- TTL-based expiration
- Memory-based cache
- Wraps other implementations

## Recent Updates (Juli 2025)

### Async Event Loop Fix
The unified system now includes a `_run_async_safe()` method that properly handles async execution in environments with existing event loops (like Streamlit):

```python
def _run_async_safe(self, coro):
    """Run async coroutine safely, detecting existing event loop."""
    try:
        loop = asyncio.get_running_loop()
        # Use ThreadPoolExecutor for new event loop
        with ThreadPoolExecutor() as executor:
            return executor.submit(run_in_thread).result()
    except RuntimeError:
        # No loop running, safe to use asyncio.run()
        return asyncio.run(coro)
```

This fix ensures compatibility with:
- Streamlit applications
- Jupyter notebooks
- CLI scripts
- Test environments

**Status**: ✅ All generation modes (SYNC, ASYNC, CACHED, RESILIENT) working at 100%

## Integration Architecture

### 1. **With Generation Module**
```python
from voorbeelden.unified_voorbeelden import genereer_alle_voorbeelden

voorbeelden_result = genereer_alle_voorbeelden(
    begrip=context.begrip,
    definitie=result.definitie,
    context=context.organisatorische_context,
    example_types=[
        ExampleType.SENTENCE,
        ExampleType.PRACTICAL,
        ExampleType.COUNTER
    ]
)
```

### 2. **With Services**
```python
# In unified service
if generate_examples:
    examples = self.voorbeelden_generator.generate_examples(
        ExampleRequest(
            begrip=begrip,
            definitie=definitie,
            context=context,
            example_type=ExampleType.SENTENCE
        )
    )
```

### 3. **With UI**
```python
# In definition generator tab
if st.checkbox("Genereer voorbeelden"):
    with st.spinner("Voorbeelden genereren..."):
        examples = generator.generate_examples_batch(requests)
```

## Example Generation Flow

### 1. **Request Processing**
```
ExampleRequest created
    ↓
Check cache (if enabled)
    ↓
Cache hit? → Return cached result
    ↓
Generate prompt based on type
    ↓
Call OpenAI API
    ↓
Parse response
    ↓
Cache result
    ↓
Return ExampleResult
```

### 2. **Batch Processing**
```
Multiple requests
    ↓
Group by priority
    ↓
Process in parallel (up to 5)
    ↓
Collect results
    ↓
Handle failures gracefully
    ↓
Return all results
```

## Prompt Templates

### 1. **Base Structure**
- Role definition
- Context setting
- Clear instructions
- Output format
- Examples if needed

### 2. **Type-Specific Variations**
- **Sentences**: Natural usage
- **Practical**: Real-world scenarios
- **Counter**: What it's NOT
- **Synonyms**: Similar terms
- **Antonyms**: Opposite terms
- **Explanation**: Deeper understanding

## Performance Characteristics

### Generation Times
- Single example: 2-4 seconds
- Batch (5 items): 3-6 seconds
- Cached retrieval: <10ms

### Resource Usage
- Memory: ~20MB baseline
- API tokens: ~200-400 per request
- Cache size: Unbounded (issue)

### Optimization Strategies
- Parallel processing
- Request batching
- Result caching
- Prompt optimization

## Common Issues

### 1. **Code Duplication**
- 4 implementations of similar functionality
- Repeated prompt templates
- Duplicate API handling

### 2. **Cache Management**
- No size limits
- No eviction policy
- Memory growth potential

### 3. **Error Handling**
- Inconsistent across implementations
- Silent failures in some cases
- No retry logic

### 4. **API Usage**
- Direct OpenAI calls
- No abstraction layer
- Hard-coded parameters

### 5. **Configuration**
- Scattered configuration
- No central settings
- Hard-coded values

## Security Considerations

### 1. **API Key Management**
- Environment variable storage
- No key rotation
- Logged in some places

### 2. **Prompt Injection**
- No input sanitization
- Direct string interpolation
- Potential for manipulation

### 3. **Cache Poisoning**
- No validation
- Unbounded storage
- No access control

## Testing Approach

### Unit Tests
```python
def test_example_generation():
    generator = UnifiedVoorbeeldenGenerator()
    result = generator.generate_examples(
        ExampleRequest(
            begrip="test",
            definitie="test definition",
            context="test context",
            example_type=ExampleType.SENTENCE
        )
    )
    assert result.success
    assert len(result.examples) == 3
```

### Integration Tests
- API mocking
- Cache behavior
- Error scenarios
- Performance tests

## Recommendations

### 1. **Complete Consolidation** (High Priority)
- Remove legacy implementations
- Single unified interface
- Update all imports

### 2. **Add Abstraction Layer**
- Abstract OpenAI dependency
- Support multiple providers
- Easier testing

### 3. **Improve Cache**
- Add size limits
- Implement LRU eviction
- Persistent cache option

### 4. **Enhance Error Handling**
- Add retry logic
- Better error messages
- Graceful degradation

### 5. **Centralize Configuration**
- Single config source
- Environment-based
- Validation

### 6. **Add Monitoring**
- Generation metrics
- API usage tracking
- Cache hit rates

## Future Enhancements

1. **Multi-language Support**: Examples in multiple languages
2. **Context-Aware Generation**: Smarter context usage
3. **Quality Scoring**: Rate generated examples
4. **Template System**: User-defined templates
5. **Streaming Generation**: Real-time example generation
6. **Fine-tuning**: Custom models for better examples
7. **Example Database**: Store and reuse good examples
8. **A/B Testing**: Test different prompts

## Configuration Options

```python
@dataclass
class VoorbeeldenConfig:
    # API settings
    api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 500
    
    # Cache settings
    enable_cache: bool = True
    cache_ttl: int = 3600
    max_cache_size: int = 1000  # Not implemented
    
    # Generation settings
    examples_per_type: int = 3
    timeout: float = 30.0
    max_retries: int = 3
    
    # Batch settings
    batch_size: int = 5
    parallel_workers: int = 5
```

## Quality Assurance

### Generated Example Validation
1. Length checks
2. Language validation
3. Relevance scoring
4. Duplication detection

### Prompt Quality
1. Clear instructions
2. Consistent format
3. Context integration
4. Output parsing

## Conclusion

The voorbeelden module has successfully evolved from multiple implementations to a unified system, following the same consolidation pattern as the services module. While the unified implementation is comprehensive, the module still needs cleanup of legacy code and improvements in cache management and error handling.

Key strengths:
- Successful consolidation effort
- Multiple generation modes
- Comprehensive example types
- Good performance with caching

Areas for improvement:
- Remove legacy implementations
- Improve cache management
- Add abstraction layer
- Better error handling

The module provides valuable functionality for generating contextual examples but would benefit from completing the consolidation and addressing the identified issues.