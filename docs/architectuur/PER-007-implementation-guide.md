---
canonical: true
status: active
owner: architecture
last_verified: 2025-09-04
applies_to: definitie-app@v2
---

# PER-007 Context Flow Fix - Implementation Guide

## Quick Start

This guide provides step-by-step instructions for implementing the PER-007 Context Flow Fix, which adds proper support for structured justice domain context fields.

## Implementation Phases

### Phase 1: Interface Extension (Day 1)

#### Step 1.1: Update GenerationRequest Interface
**File**: `/src/services/interfaces.py` ✅ ALREADY DONE

The interface has already been extended with the three new fields:
```python
juridische_context: list[str] | None = None
wettelijke_basis: list[str] | None = None  
organisatorische_context: list[str] | None = None
```

#### Step 1.2: Create ASTRA Validator
**File**: Create `/src/services/validation/astra_validator.py`

```python
"""ASTRA compliance validator for justice organizations."""

from typing import list

# ASTRA registered organizations
ASTRA_ORGANIZATIONS = {
    # Primary justice organizations
    "OM": "Openbaar Ministerie",
    "DJI": "Dienst Justitiële Inrichtingen",
    "Rechtspraak": "De Rechtspraak",
    "CJIB": "Centraal Justitieel Incassobureau",
    "KMAR": "Koninklijke Marechaussee",
    "NP": "Nederlandse Politie",
    "Justid": "Justitiële Informatiedienst",
    
    # Secondary organizations
    "IND": "Immigratie- en Naturalisatiedienst",
    "RvdK": "Raad voor de Kinderbescherming",
    "SRN": "Slachtofferhulp Nederland",
    "NRGD": "Nederlands Register Gerechtelijk Deskundigen",
    "3RO": "Reclasseringsorganisaties",
    "FIOD": "Fiscale Inlichtingen- en Opsporingsdienst",
    
    # Chain contexts
    "ZSM": "ZSM-keten",
    "Strafrechtketen": "Strafrechtketen",
    "Jeugdketen": "Jeugdketen",
}

def validate_organization(org: str) -> tuple[bool, str | None]:
    """Validate organization against ASTRA registry."""
    if org in ASTRA_ORGANIZATIONS:
        return True, None
    
    # Check for full name
    if org in ASTRA_ORGANIZATIONS.values():
        return True, None
    
    # Suggest alternatives
    suggestions = [k for k in ASTRA_ORGANIZATIONS.keys() 
                  if k.lower().startswith(org[:2].lower())]
    
    if suggestions:
        return False, f"Organization '{org}' not recognized. Did you mean: {', '.join(suggestions)}?"
    
    return False, f"Organization '{org}' not in ASTRA registry"

def validate_organizations(orgs: list[str] | None) -> list[str]:
    """Validate list of organizations, return warnings."""
    if not orgs:
        return []
    
    warnings = []
    for org in orgs:
        valid, warning = validate_organization(org)
        if not valid and warning:
            warnings.append(warning)
    
    return warnings
```

### Phase 2: Context Manager Enhancement (Day 2)

#### Step 2.1: Update HybridContextManager
**File**: `/src/services/definition_generator_context.py`

Update the `_build_base_context` method:

```python
def _build_base_context(self, request: GenerationRequest) -> dict[str, list[str]]:
    """Bouw basis context dictionary met prioriteit voor nieuwe velden."""
    context = {
        "organisatorisch": [],
        "juridisch": [],
        "wettelijk": [],
        "domein": [],
        "technisch": [],
        "historisch": [],
    }
    
    # PRIORITY 1: Use new structured fields if present
    if request.organisatorische_context:
        context["organisatorisch"] = request.organisatorische_context
        # Validate organizations
        from services.validation.astra_validator import validate_organizations
        warnings = validate_organizations(request.organisatorische_context)
        for warning in warnings:
            logger.warning(f"ASTRA validation: {warning}")
    
    if request.juridische_context:
        context["juridisch"] = request.juridische_context
    
    if request.wettelijke_basis:
        context["wettelijk"] = request.wettelijke_basis
    
    # PRIORITY 2: Add legacy fields if no overlap
    if request.organisatie and request.organisatie not in context["organisatorisch"]:
        context["organisatorisch"].append(request.organisatie)
    
    if request.domein and request.domein not in context["domein"]:
        context["domein"].append(request.domein)
    
    # PRIORITY 3: Parse generic context string only if new fields are empty
    if not any([request.organisatorische_context, 
                request.juridische_context,
                request.wettelijke_basis]) and request.context:
        self._parse_context_string(request.context, context)
    
    return context
```

#### Step 2.2: Add Context Metrics
**File**: Update `/src/services/definition_generator_context.py`

Add metrics to EnrichedContext:

```python
@dataclass
class EnrichedContext:
    """Verrijkte context met meerdere bronnen."""
    
    base_context: dict[str, list[str]]
    sources: list[ContextSource]
    expanded_terms: dict[str, str]
    confidence_scores: dict[str, float]
    metadata: dict[str, Any]
    
    # New metrics fields
    context_quality_score: float = 0.0
    categorization_method: str = "unknown"  # "structured" | "parsed" | "hybrid"
    
    def __post_init__(self):
        # Calculate quality score based on context completeness
        filled_categories = sum(1 for v in self.base_context.values() if v)
        self.context_quality_score = filled_categories / len(self.base_context)
        
        # Determine categorization method
        if self.metadata.get("used_structured_fields"):
            self.categorization_method = "structured"
        elif self.metadata.get("parsed_from_string"):
            self.categorization_method = "parsed"
        else:
            self.categorization_method = "hybrid"
```

### Phase 3: UI Integration (Day 3-4)

#### Step 3.1: Update UI Components
**File**: `/src/ui/components/definition_generator_tab.py`

Update the form to use structured fields:

```python
# Replace single context field with three structured fields

col1, col2, col3 = st.columns(3)

with col1:
    organisatorische_context = st.multiselect(
        "Organisatorische Context",
        options=list(ASTRA_ORGANIZATIONS.keys()),
        help="Selecteer relevante organisaties (bijv. DJI, OM, KMAR)"
    )

with col2:
    juridische_context = st.multiselect(
        "Juridische Context",
        options=["Strafrecht", "Bestuursrecht", "Civiel recht", 
                "Staatsrecht", "Europees recht"],
        help="Selecteer juridische domeinen"
    )

with col3:
    wettelijke_basis_input = st.text_area(
        "Wettelijke Basis",
        placeholder="Bijv: Art. 27 Sv, Art. 6:162 BW",
        help="Voer relevante wetsartikelen in (gescheiden door komma's)"
    )
    wettelijke_basis = [w.strip() for w in wettelijke_basis_input.split(",") if w.strip()]

# Build request with new fields
request = GenerationRequest(
    id=str(uuid.uuid4()),
    begrip=begrip,
    organisatorische_context=organisatorische_context if organisatorische_context else None,
    juridische_context=juridische_context if juridische_context else None,
    wettelijke_basis=wettelijke_basis if wettelijke_basis else None,
    # Keep legacy field for backward compatibility
    context=st.session_state.get("legacy_context", None)
)
```

#### Step 3.2: Add Context Display
**File**: `/src/ui/components/definition_generator_tab.py`

Add visualization of categorized context:

```python
def display_context_categories(enriched_context: EnrichedContext):
    """Display categorized context in the UI."""
    
    st.subheader("📋 Context Categorisatie")
    
    # Show quality score
    quality_color = "green" if enriched_context.context_quality_score > 0.7 else "orange"
    st.metric(
        "Context Kwaliteit",
        f"{enriched_context.context_quality_score:.0%}",
        delta=f"via {enriched_context.categorization_method}"
    )
    
    # Display categories
    cols = st.columns(3)
    for i, (cat_name, items) in enumerate(enriched_context.base_context.items()):
        if items:
            with cols[i % 3]:
                st.write(f"**{cat_name.title()}**")
                for item in items:
                    st.write(f"• {item}")
```

### Phase 4: Testing (Day 5)

#### Step 4.1: Unit Tests
**File**: Create `/tests/unit/test_per007_context_flow.py`

```python
import pytest
from src.services.interfaces import GenerationRequest
from src.services.definition_generator_context import HybridContextManager
from src.services.validation.astra_validator import validate_organization

class TestPER007ContextFlow:
    """Test suite for PER-007 Context Flow Fix."""
    
    def test_new_fields_take_priority(self):
        """Test that new structured fields take priority over legacy."""
        request = GenerationRequest(
            id="test-1",
            begrip="verdachte",
            organisatorische_context=["DJI", "OM"],
            juridische_context=["Strafrecht"],
            wettelijke_basis=["Art. 27 Sv"],
            context="some legacy context"  # Should be ignored
        )
        
        manager = HybridContextManager(config)
        context = manager._build_base_context(request)
        
        assert context["organisatorisch"] == ["DJI", "OM"]
        assert context["juridisch"] == ["Strafrecht"]
        assert context["wettelijk"] == ["Art. 27 Sv"]
    
    def test_backward_compatibility(self):
        """Test that legacy context parsing still works."""
        request = GenerationRequest(
            id="test-2",
            begrip="sanctie",
            context="DJI, Strafrecht, Art. 27 Sv"
        )
        
        manager = HybridContextManager(config)
        context = manager._build_base_context(request)
        
        assert "DJI" in context["organisatorisch"]
        assert "Strafrecht" in context["juridisch"]
        assert "Art. 27 Sv" in context["wettelijk"]
    
    def test_astra_validation(self):
        """Test ASTRA organization validation."""
        valid, _ = validate_organization("DJI")
        assert valid is True
        
        valid, warning = validate_organization("InvalidOrg")
        assert valid is False
        assert "not recognized" in warning
```

#### Step 4.2: Integration Tests
**File**: Create `/tests/integration/test_per007_end_to_end.py`

```python
async def test_end_to_end_context_flow():
    """Test complete context flow from UI to prompt."""
    
    # Create request with new fields
    request = GenerationRequest(
        id="test-e2e",
        begrip="detentie",
        organisatorische_context=["DJI"],
        juridische_context=["Penitentiair recht"],
        wettelijke_basis=["Art. 15 Pbw"]
    )
    
    # Process through orchestrator
    orchestrator = container.definition_orchestrator_v2()
    response = await orchestrator.create_definition(request)
    
    # Verify context appears in definition
    assert response.success
    assert "DJI" in response.definition.metadata.get("context_used", "")
    assert "Penitentiair recht" in response.definition.metadata.get("context_used", "")
```

### Phase 5: Monitoring & Rollout (Day 6)

#### Step 5.1: Add Monitoring
**File**: `/src/services/monitoring/context_metrics.py`

```python
from prometheus_client import Counter, Histogram

# Metrics for context categorization
context_method_counter = Counter(
    'context_categorization_method',
    'Method used for context categorization',
    ['method']  # "structured", "parsed", "hybrid"
)

context_quality_histogram = Histogram(
    'context_quality_score',
    'Quality score of context categorization',
    buckets=[0.1, 0.3, 0.5, 0.7, 0.9, 1.0]
)

astra_validation_counter = Counter(
    'astra_validation_results',
    'ASTRA organization validation results',
    ['status']  # "valid", "invalid", "warning"
)
```

#### Step 5.2: Feature Flag
**File**: `/src/config/feature_flags.py`

```python
FEATURE_FLAGS = {
    "use_structured_context_fields": {
        "enabled": False,  # Start disabled
        "rollout_percentage": 0,
        "description": "Use new structured context fields (PER-007)"
    }
}

def is_feature_enabled(feature: str, user_id: str = None) -> bool:
    """Check if feature is enabled for user."""
    flag = FEATURE_FLAGS.get(feature)
    if not flag:
        return False
    
    if not flag["enabled"]:
        return False
    
    # Gradual rollout logic
    if user_id and flag["rollout_percentage"] < 100:
        import hashlib
        hash_val = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
        return (hash_val % 100) < flag["rollout_percentage"]
    
    return True
```

## Rollout Plan

### Week 1: Development & Testing
- Day 1-2: Implement interface and context manager changes
- Day 3-4: Update UI components
- Day 5: Complete testing suite
- Day 6: Add monitoring and feature flags

### Week 2: Staged Rollout
- Day 1: Enable for 10% of users
- Day 2-3: Monitor metrics, fix issues
- Day 4: Increase to 50%
- Day 5: Full rollout (100%)

### Week 3: Optimization
- Analyze context categorization metrics
- Optimize ASTRA validation caching
- Performance tuning
- Documentation updates

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Context categorization accuracy | >95% | Validation tests |
| ASTRA validation hit rate | >99% | Monitoring dashboard |
| Context processing time | <50ms | P95 latency |
| User adoption of new fields | >80% | Usage analytics |
| Backward compatibility | 100% | Regression tests |

## Troubleshooting Guide

### Issue: ASTRA validation failures
**Solution**: Check if organization uses abbreviation vs full name, update ASTRA_ORGANIZATIONS dict

### Issue: Context not appearing in prompts
**Solution**: Verify EnrichedContext.get_all_context_text() is called in prompt building

### Issue: Performance degradation
**Solution**: Enable context caching in HybridContextManager, check for N+1 queries

### Issue: UI not showing new fields
**Solution**: Clear Streamlit cache, verify feature flag is enabled

## Checklist for Production

- [ ] All unit tests passing (>90% coverage)
- [ ] Integration tests successful
- [ ] ASTRA validator has current organization list
- [ ] Feature flags configured
- [ ] Monitoring dashboards created
- [ ] Performance baseline established
- [ ] Documentation updated
- [ ] Rollback plan tested
- [ ] Security review completed
- [ ] Compliance check passed

## References

- [ADR-PER-007](/docs/architectuur/beslissingen/ADR-PER-007-context-flow-fix.md)
- [PER-007 Architectural Assessment](/docs/architectuur/PER-007-architectural-assessment.md)
- [PER-007 Test Scenarios](/docs/testing/PER-007-test-scenarios.md)
- [ASTRA Guidelines](https://www.astra.nl/architecture)