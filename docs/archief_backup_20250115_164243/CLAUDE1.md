# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **DefinitieAgent** (Dutch Definition Agent) - a Streamlit-based application that generates, validates, and manages legal/policy definitions for Dutch government organizations. The application uses OpenAI's GPT models to generate definitions and applies automated quality testing rules.

## Key Commands

### Running the Application

**New Refactored Version (Recommended):**
```bash
streamlit run src/main.py
```

**Legacy Version (Do NOT use - Missing features being migrated):**
```bash
# streamlit run src/centrale_module_definitie_kwaliteit.py  # DEPRECATED
```

### ⚠️ Legacy Migration Status
The application is currently missing critical features from the legacy version:
- **AI Content Generation**: Voorbeeldzinnen, synoniemen, toelichting (Week 2-3)
- **Custom Definition Tab**: Manual editing workflow (Week 2-3)
- **Developer Tools**: Forbidden words management, debugging (Week 3)
- **Metadata Fields**: Datum voorstel, voorsteller, ketenpartners (Week 1)

See `LEGACY_FEATURE_IMPLEMENTATION_PLAN.md` for migration progress.

### Testing
```bash
pytest                                    # Run all tests
pytest tests/test_refactored_imports.py  # Test new modular structure
pytest tests/test_ai_toetser.py          # Test AI validation
pytest -v                                # Verbose output
```

### Dependencies
```bash
pip install -r requirements.txt
```

## Refactored Architecture Overview

### ⚠️ Current Limitations
The refactored version is missing several features from the original:
1. **Content Generation**: No voorbeeldzinnen, synoniemen, antoniemen generation
2. **Custom Editing**: No manual definition editing capability
3. **Developer Tools**: No forbidden words management or debugging tools
4. **Metadata**: Missing datum voorstel, voorsteller, ketenpartners fields

These features are being migrated - see roadmap in architecture docs.

## Architecture Details

The application has been refactored into a modular structure with proper separation of concerns:

### Core Application Flow
1. **User Input**: Term + organizational/legal context via Streamlit interface
2. **Definition Generation**: GPT generates definition using structured prompts
3. **Quality Testing**: Automated validation against ~30 quality rules
4. **Post-processing**: Text cleaning and formatting
5. **Export**: TXT export with full metadata

### New Modular Structure

#### Main Application (`src/main.py`)
- **Entry Point**: Streamlit application startup and main workflow
- **Clean Architecture**: Orchestrates UI components and services
- **Error Handling**: Comprehensive error management with user-friendly messages

#### UI Layer (`src/ui/`)
- **`components.py`**: Reusable Streamlit UI components
- **`session_state.py`**: Centralized session state management
- **Separation**: UI logic separated from business logic

#### Services Layer (`src/services/`)
- **`definition_service.py`**: Core business logic for definition processing
- **API Integration**: Handles OpenAI API calls with error handling
- **Workflow Management**: Complete definition generation and validation workflow

#### Utilities (`src/utils/`)
- **`exceptions.py`**: Custom exceptions and error handling decorators
- **Defensive Programming**: Comprehensive error handling and logging

#### Original Modules (Unchanged)
- **`definitie_generator/`**: GPT-based definition generation
- **`ai_toetser/`**: Quality validation system with rule-based testing
- **`prompt_builder/`**: Structured prompt construction for GPT
- **`opschoning/`**: Text cleaning and post-processing
- **`config/`**: Configuration management (rules, forbidden words, contexts)
- **`log/`**: CSV and JSON logging of all definitions and test results
- **`export/`**: TXT export functionality
- **`web_lookup/`**: External source lookup (legal databases, definitions)
- **`voorbeelden/`**: Example sentence generation

### Error Handling Features

#### Custom Exception Types
- **`DefinitieAgentError`**: Base exception for the application
- **`APIError`**: For OpenAI API and external service failures
- **`ValidationError`**: For quality rule validation failures
- **`ConfigurationError`**: For configuration loading issues
- **`ExportError`**: For export functionality problems

#### Error Handling Patterns
- **Decorators**: `@handle_api_error`, `@handle_validation_error`
- **Safe Execution**: `safe_execute()` function for graceful degradation
- **User-Friendly Messages**: Technical errors translated to user-friendly Dutch

### Session State Management

#### Centralized Management
- **`SessionStateManager`**: Single point of control for all session state
- **Default Values**: Consistent initialization across the application
- **Type Safety**: Proper typing and validation

#### Key Methods
- `initialize_session_state()`: Initialize all variables
- `update_definition_results()`: Update definition-related state
- `get_export_data()`: Prepare data for export
- `has_generated_definition()`: Check if definition exists

### Configuration System

The application uses JSON configuration files:
- **`config/toetsregels.json`**: Quality testing rules with priorities
- **`config/verboden_woorden.json`**: Forbidden starting words for definitions
- **`config/context_wet_mapping.json`**: Legal context mappings

### Quality Testing Framework

The AI toetser (tester) applies approximately 30 validation rules categorized by:
- **Priority**: high, medium, low
- **Type**: content, structure, language, legal compliance
- **Scope**: term usage, forbidden patterns, context requirements

## Development Notes

### Key Dependencies
- **Streamlit**: Web interface framework
- **OpenAI**: GPT model integration via openai library
- **pandas**: Data handling and CSV export
- **dotenv**: Environment variable management for API keys

### Testing Structure
- Tests are located in `tests/` directory
- `conftest.py` adds `src/` to Python path
- New tests in `test_refactored_imports.py` verify modular structure
- Original tests in `test_ai_toetser.py` test quality validation

### Important Files
- **`src/main.py`**: New modular main application (150 lines vs 1000+ original)
- **`src/centrale_module_definitie_kwaliteit.py`**: Original monolithic application (backup)
- **`src/services/definition_service.py`**: Core business logic service
- **`src/ui/components.py`**: Reusable UI components
- **`src/utils/exceptions.py`**: Comprehensive error handling

### Environment Setup
- Requires OpenAI API key via `.env` file
- Dutch language processing and legal terminology
- Designed for Dutch government/legal domain usage

### Development Best Practices
- **Modular Design**: Each module has a single responsibility
- **Error Handling**: Comprehensive error handling at all levels
- **Type Hints**: Added throughout the new modules
- **Logging**: Proper logging instead of print statements
- **Testing**: Unit tests for all new modules

### Migration Notes
- Original file backed up as `centrale_module_definitie_kwaliteit_backup.py`
- New structure maintains full backward compatibility
- All original functionality preserved
- Enhanced with proper error handling and modular design