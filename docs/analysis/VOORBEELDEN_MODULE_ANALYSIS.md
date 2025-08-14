# Voorbeelden Module Analysis

## Overview
The voorbeelden (examples) module is responsible for generating various types of examples, synonyms, antonyms, and explanations for legal terms. It provides both synchronous and asynchronous generation capabilities with caching and resilience features.

## Structure

```
voorbeelden/
├── __init__.py                # Module initialization
├── voorbeelden.py            # Original synchronous implementation
├── unified_voorbeelden.py    # Unified example generation system
├── async_voorbeelden.py      # Asynchronous implementation
└── cached_voorbeelden.py     # Cached implementation
```

## Key Components

### 1. Original Implementation (voorbeelden.py)
**Purpose**: Basic synchronous example generation using OpenAI API

**Key Functions**:
- `genereer_voorbeeld_zinnen()`: Generate 2-3 short example sentences
- `genereer_praktijkvoorbeelden()`: Generate practical use cases
- `genereer_tegenvoorbeelden()`: Generate counter-examples

**Characteristics**:
- Direct OpenAI client usage
- Simple error handling
- Basic response parsing
- No caching or resilience features
- Hardcoded prompts and parameters

### 2. Unified Examples System (unified_voorbeelden.py)
**Purpose**: Consolidated system for all example generation needs

**Key Features**:
- Six example types via `ExampleType` enum:
  - SENTENCE: Example sentences
  - PRACTICAL: Practical use cases
  - COUNTER: Counter-examples
  - SYNONYMS: Synonyms
  - ANTONYMS: Antonyms
  - EXPLANATION: Detailed explanations
- Four generation modes via `GenerationMode` enum:
  - SYNC: Synchronous blocking
  - ASYNC: Asynchronous non-blocking
  - CACHED: With caching enabled
  - RESILIENT: Full resilience features

**Main Classes**:
- `ExampleRequest`: Structured request data
- `ExampleResponse`: Structured response with metadata
- `UnifiedExamplesGenerator`: Main generator class

**Advanced Features**:
- Per-endpoint resilience configuration
- Batch generation support
- Async concurrent generation
- Statistics tracking
- Context-aware prompt building
- Response parsing with fallbacks

### 3. Architecture Pattern

**Request Flow**:
1. User calls convenience function (e.g., `genereer_voorbeeld_zinnen()`)
2. Function creates `ExampleRequest` with appropriate settings
3. Request routed to generator based on mode
4. Generator builds context-aware prompt
5. Call to GPT API with resilience
6. Response parsed and structured
7. Results returned in `ExampleResponse`

**Prompt Engineering**:
- Context-aware prompts that incorporate:
  - Organizational context (e.g., "Strafrechtketen")
  - Legal context (e.g., "Strafrecht")
  - Legislative basis (e.g., "Wetboek van Strafrecht")
- Different prompt templates per example type
- Natural language integration of context

## Issues and Observations

### 1. Code Duplication
- Multiple implementations of similar functionality
- Original `voorbeelden.py` still exists alongside unified system
- Async and cached versions likely duplicate unified functionality

### 2. Direct OpenAI Usage
- Original implementation uses OpenAI client directly
- Unified system uses `prompt_builder` module
- Inconsistent API interaction patterns

### 3. Error Handling
- Original: Basic try-catch with error messages in results
- Unified: Structured error handling with response objects
- No clear error recovery strategies

### 4. Prompt Management
- Prompts hardcoded in functions
- No version control for prompts
- Dutch language prompts mixed with English code

### 5. Configuration
- Model selection hardcoded ("gpt-4")
- Temperature and token limits hardcoded
- No easy way to adjust generation parameters

### 6. Performance
- Sync operations block the UI
- No request batching optimization
- Cache key generation could be expensive

### 7. Response Parsing
- Regex-based parsing is fragile
- Assumes specific formatting from GPT
- Limited error recovery in parsing

### 8. Context Handling
- Context dictionary structure not validated
- Missing context handled with "geen" (none)
- No context priority or weighting

## Recommendations

### 1. Consolidate Implementations
- Remove duplicate files (voorbeelden.py, async_voorbeelden.py, cached_voorbeelden.py)
- Use only unified system
- Migrate any unique features to unified system

### 2. Improve Prompt Management
- Extract prompts to configuration files
- Version control prompts
- Support multiple languages
- A/B testing for prompt effectiveness

### 3. Enhanced Error Handling
- Implement fallback strategies
- Add retry logic for parsing failures
- Provide user-friendly error messages
- Log errors for analysis

### 4. Configuration Improvements
- Move all hardcoded values to configuration
- Support model selection per example type
- Allow temperature tuning
- Dynamic token allocation

### 5. Performance Optimization
- Implement request batching
- Add response streaming
- Optimize cache key generation
- Pre-compile regex patterns

### 6. Better Response Parsing
- Use structured output from GPT (JSON mode)
- Implement robust parsing with multiple strategies
- Add validation for parsed results
- Handle edge cases gracefully

### 7. Context Enhancement
- Validate context structure
- Add context priority system
- Support context inheritance
- Implement context templates

## Integration Points

- **Services**: Used by unified service layer for example generation
- **Utils**: Leverages caching and resilience utilities
- **Prompt Builder**: Uses centralized prompt building
- **UI**: Called from Streamlit interface

## Usage Examples

### Basic Example Generation
```python
# Generate example sentences
sentences = genereer_voorbeeld_zinnen(
    begrip="verdachte",
    definitie="Persoon die wordt verdacht van een strafbaar feit",
    context_dict={
        "organisatorisch": ["OM"],
        "juridisch": ["Strafrecht"]
    }
)
```

### Batch Generation
```python
# Generate all example types at once
all_examples = genereer_alle_voorbeelden(
    begrip="verdachte",
    definitie="...",
    context_dict={...},
    mode=GenerationMode.RESILIENT
)
```

### Async Generation
```python
# Generate examples concurrently
results = await genereer_alle_voorbeelden_async(
    begrip="verdachte",
    definitie="...",
    context_dict={...}
)
```

## Future Considerations

1. **Multi-language Support**: Extend beyond Dutch
2. **Example Quality Scoring**: Rate and filter generated examples
3. **User Feedback Loop**: Learn from user selections
4. **Template System**: User-defined example templates
5. **Integration with Legal Databases**: Pull real examples
6. **Caching Strategy**: Implement semantic similarity caching
7. **A/B Testing Framework**: Test different generation strategies
8. **Example Validation**: Verify examples against legal standards