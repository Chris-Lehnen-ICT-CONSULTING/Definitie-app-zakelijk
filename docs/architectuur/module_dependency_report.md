# Module Dependency Analysis Report

## Overview

Total modules analyzed: 7

## Module Dependencies

### context_awareness
- **Direct Dependencies**: None
- **Shared Data Set**: ['organization_contexts', 'domain_contexts']
- **Shared Data Get**: None

### definition_task
- **Direct Dependencies**: ['semantic_categorisation']
- **Shared Data Set**: None
- **Shared Data Get**: ['organization_contexts', 'word_type', 'ontological_category', 'domain_contexts']

### error_prevention
- **Direct Dependencies**: ['context_awareness']
- **Shared Data Set**: None
- **Shared Data Get**: ['organization_contexts', 'domain_contexts']

### expertise
- **Direct Dependencies**: None
- **Shared Data Set**: ['word_type']
- **Shared Data Get**: None

### output_specification
- **Direct Dependencies**: None
- **Shared Data Set**: None
- **Shared Data Get**: None

### quality_rules
- **Direct Dependencies**: None
- **Shared Data Set**: None
- **Shared Data Get**: None

### semantic_categorisation
- **Direct Dependencies**: None
- **Shared Data Set**: ['ontological_category']
- **Shared Data Get**: None

## Coupling Analysis

### Independent Modules
Modules with no direct dependencies:
- context_awareness
- expertise
- output_specification
- quality_rules
- semantic_categorisation

### Direct Dependencies
- **definition_task** depends on: semantic_categorisation
- **error_prevention** depends on: context_awareness

### Data Flow Dependencies
- **definition_task**
  - Needs: organization_contexts, word_type, ontological_category, domain_contexts
  - Provides: None
- **error_prevention**
  - Needs: organization_contexts, domain_contexts
  - Provides: None

### Dependency Chains
1. definition_task → semantic_categorisation
2. error_prevention → context_awareness

## Modularity Assessment

- **Modularity Score**: 71.4% (5/7 modules are independent)
- **Tightly Coupled Pairs**: 0
- **Longest Dependency Chain**: 2

## Recommendations


## Dependency Graph

```mermaid
graph TD
    context_awareness[context_awareness]
    definition_task[definition_task]
    error_prevention[error_prevention]
    expertise[expertise]
    output_specification[output_specification]
    quality_rules[quality_rules]
    semantic_categorisation[semantic_categorisation]
    definition_task -->|depends on| semantic_categorisation
    error_prevention -->|depends on| context_awareness
    context_awareness -.->|organization_contexts| definition_task
    expertise -.->|word_type| definition_task
    semantic_categorisation -.->|ontological_category| definition_task
    context_awareness -.->|domain_contexts| definition_task
    context_awareness -.->|organization_contexts| error_prevention
    context_awareness -.->|domain_contexts| error_prevention
```
