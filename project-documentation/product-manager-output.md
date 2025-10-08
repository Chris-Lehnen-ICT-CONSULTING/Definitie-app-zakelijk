# Product Manager Solution Synthesis: Definition Display Metadata Issue

## Executive Summary

**Elevator Pitch**: Remove unwanted metadata headers from definition display to show only the clean, formatted definition text to users.

**Problem Statement**: The application currently displays definitions with unwanted metadata prefixes including "Ontologische categorie: [type]" headers and "[term]: [definition]" patterns, reducing readability and professional appearance.

**Target Audience**:
- Primary: Legal professionals using the DefinitieAgent application
- Secondary: System administrators and content managers

**Unique Selling Proposition**: Clean, professional definition display that meets Nederlandse wetgevingstechniek standards without distracting metadata.

**Success Metrics**:
- 100% of definitions displayed without metadata headers
- Zero regression in definition generation quality
- Maintained performance (< 5 seconds generation time)
- No impact on validation rules or scoring

## Problem Analysis

### Current State
Based on my initial investigation:

1. **GPT Output Format**: The system prompts GPT-4 to include an "Ontologische categorie" marker as the first line of output
   - Location: `src/services/prompts/modules/definition_task_module.py`, line 253
   - Purpose: Classification of definition type (soort, exemplaar, proces, resultaat)

2. **Cleaning Pipeline**: Two-stage cleaning process exists:
   - Stage 1: `opschoning_enhanced.py` - Removes GPT metadata headers
   - Stage 2: `opschoning.py` - Removes forbidden word patterns

3. **Display Logic**: Definition display happens in:
   - `src/ui/components/definition_generator_tab.py` - Main display component
   - Shows both "origineel" and "gecorrigeerd" versions

### Root Cause Hypothesis

The issue appears to stem from:
1. **Prompt Instruction**: The system explicitly asks GPT to include the ontological header
2. **Incomplete Cleaning**: The cleaning may not be applied consistently to all display paths
3. **Multiple Display Paths**: Different code paths for displaying definitions may bypass cleaning

## Initial Findings

### Code Flow Analysis

1. **Generation Flow**:
   ```
   DefinitionTaskModule → GPT-4 → Response with header → Cleaning → Display
   ```

2. **Key Components**:
   - `definition_task_module.py`: Adds ontology instruction to prompt
   - `definition_orchestrator_v2.py`: Orchestrates the cleaning process
   - `opschoning_enhanced.py`: Contains `extract_definition_from_gpt_response()` function
   - `definition_generator_tab.py`: Displays the final definition

3. **Existing Mitigation**:
   - Line 590-593 in `definition_orchestrator_v2.py` attempts to remove headers
   - `opschoning_enhanced.py` has dedicated header removal logic

## Awaiting Agent Reports

### Expected Input from Other Agents

1. **Code Architect Agent**:
   - Detailed flow analysis
   - Architecture impact assessment
   - Dependency mapping

2. **Implementation Agent**:
   - Specific code locations requiring changes
   - Technical implementation options
   - Performance implications

3. **Testing Agent**:
   - Current test coverage
   - Required test modifications
   - Regression risk assessment

4. **Documentation Agent**:
   - Impact on existing documentation
   - Required documentation updates
   - User communication needs

## Solution Options (Preliminary)

### Option 1: Remove Ontology Instruction from Prompt
**Description**: Modify the prompt module to stop requesting the ontological header

**Pros**:
- Prevents the issue at the source
- Simplest conceptual solution
- No performance impact

**Cons**:
- May lose valuable classification data
- Could affect downstream validation
- Requires prompt retraining/testing

### Option 2: Enhance Cleaning Pipeline
**Description**: Ensure all display paths consistently apply the cleaning functions

**Pros**:
- Preserves classification capability
- Minimal architectural change
- Can be implemented incrementally

**Cons**:
- Treating symptom, not cause
- Multiple code paths to verify
- Potential for missed edge cases

### Option 3: Separate Metadata Storage
**Description**: Extract and store metadata separately from the display text

**Pros**:
- Clean separation of concerns
- Preserves all metadata for analysis
- Future-proof architecture

**Cons**:
- Requires database schema changes
- More complex implementation
- Higher testing burden

## Testing Strategy (Draft)

### Verification Requirements
1. **Unit Tests**:
   - Test cleaning functions with various input formats
   - Verify metadata extraction
   - Confirm display formatting

2. **Integration Tests**:
   - End-to-end generation without metadata display
   - Validation rule compliance
   - Performance benchmarks

3. **User Acceptance Tests**:
   - Visual inspection of generated definitions
   - Expert review of formatting compliance
   - Regression testing on existing definitions

## Risk Assessment

### Technical Risks
- **Data Loss**: Ontological classification might be needed elsewhere
- **Validation Impact**: Some validation rules might depend on the classification
- **Display Regression**: Other display components might expect the current format

### Mitigation Strategies
- Comprehensive test coverage before deployment
- Gradual rollout with monitoring
- Backup of current classification logic
- Clear rollback procedure

## Next Steps

1. **Await agent reports** for comprehensive analysis
2. **Synthesize findings** into consensus solution
3. **Validate solution** with technical constraints
4. **Document implementation plan** with clear acceptance criteria
5. **Define rollout strategy** with success metrics

---

## Status
- Document Status: **AWAITING AGENT INPUT**
- Last Updated: 2025-10-08
- Author: Product Manager Agent

## Appendix: Key Code References

### Critical Files
- `/src/services/prompts/modules/definition_task_module.py` - Prompt construction
- `/src/services/orchestrators/definition_orchestrator_v2.py` - Orchestration logic
- `/src/opschoning/opschoning_enhanced.py` - Metadata cleaning
- `/src/ui/components/definition_generator_tab.py` - Display logic

### Important Functions
- `extract_definition_from_gpt_response()` - Header removal
- `opschonen()` - General cleaning
- `_build_ontological_marker()` - Header generation

---

*This document will be updated once all agent reports are received and synthesized.*