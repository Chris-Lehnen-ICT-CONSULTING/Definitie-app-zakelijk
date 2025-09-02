---
canonical: false
status: archived
owner: architecture
last_verified: 2025-09-02
applies_to: definitie-app@v2
---

# [ARCHIVED] Technische Specificatie: Cleaning UI Componenten

Deze versie is gearchiveerd. Actuele informatie staat in:
- `docs/architectuur/cleaning-ui-technical-spec.md`

**Auteur**: Winston (System Architect)
**Datum**: 2025-08-25
**Type**: Technische UI Architectuur Specificatie

## 1. Component Architectuur

### 1.1 CleaningComparisonComponent

```python
class CleaningComparisonComponent:
    """
    Hoofdcomponent voor side-by-side vergelijking van origineel vs opgeschoond.
    """

    def __init__(self):
        self.layout_mode: Literal["side_by_side", "tabbed", "inline_diff"]
        self.highlight_changes: bool = True
        self.show_metrics: bool = True

    def render(self, cleaning_result: CleaningResult) -> None:
        """
        Render component gebaseerd op layout mode.

        Data Requirements:
        - cleaning_result.original_text
        - cleaning_result.cleaned_text
        - cleaning_result.applied_rules
        - cleaning_result.diff_segments
        """
```

### 1.2 Data Structuren voor UI

```python
@dataclass
class DiffSegment:
    """Segment voor text diff visualisatie."""
    start_pos: int
    end_pos: int
    segment_type: Literal["unchanged", "removed", "added", "modified"]
    original_text: str
    cleaned_text: str
    rule_applied: str

@dataclass
class CleaningMetrics:
    """Metrics voor UI dashboard."""
    character_reduction: int
    readability_score_delta: float
    rules_applied_count: int
    processing_time_ms: float
```

## 2. State Management

### 2.1 Session State Structuur

```python
# Uitbreiding van bestaande SessionStateManager
cleaning_ui_state = {
    "comparison_mode": "side_by_side",  # of "tabbed", "inline_diff"
    "show_original": True,
    "show_cleaned": True,
    "highlight_enabled": True,
    "selected_cleaning_profile": "moderate",
    "custom_rules": {},
    "preview_mode": False,
}
```

### 2.2 Event Handlers

```python
def on_comparison_mode_change(mode: str):
    """Handler voor layout mode wijziging."""
    st.session_state.cleaning_ui_state["comparison_mode"] = mode
    st.rerun()

def on_cleaning_profile_change(profile: str):
    """Handler voor cleaning profile wijziging."""
    st.session_state.cleaning_ui_state["selected_cleaning_profile"] = profile
    # Trigger re-cleaning met nieuw profile
    if st.session_state.cleaning_ui_state["preview_mode"]:
        trigger_preview_update()
```

## 3. Integration Points

### 3.1 Met CleaningService

```python
# Interface uitbreiding
class EnhancedCleaningService(CleaningServiceInterface):
    def clean_with_profile(
        self,
        text: str,
        term: str,
        profile: str = "moderate"
    ) -> EnhancedCleaningResult:
        """Clean met specifiek profile."""
        pass

    def preview_cleaning(
        self,
        text: str,
        term: str,
        profile: str
    ) -> CleaningPreview:
        """Preview zonder opslag."""
        pass
```

### 3.2 Met DefinitionGeneratorTab

```python
# Locatie: src/ui/components/definition_generator_tab.py
# Vervang huidige cleaning display (regels 217-244) met:

def _render_cleaning_section(self, agent_result: dict):
    """Render verbeterde cleaning sectie."""

    if self._has_cleaning_applied(agent_result):
        # Gebruik nieuwe component
        cleaning_component = CleaningComparisonComponent()

        cleaning_result = self._extract_cleaning_result(agent_result)
        cleaning_component.render(cleaning_result)

        # Metrics dashboard
        if st.session_state.cleaning_ui_state["show_metrics"]:
            self._render_cleaning_metrics(cleaning_result)
```

## 4. Performance Optimalisaties

### 4.1 Lazy Loading

```python
@st.cache_data
def compute_diff_segments(original: str, cleaned: str) -> List[DiffSegment]:
    """Cache diff berekeningen voor performance."""
    # Gebruik difflib voor efficiënte diff
    import difflib
    # ... implementatie
```

### 4.2 Streaming Updates

```python
def render_cleaning_progress():
    """Toon progress tijdens cleaning stages."""
    progress_container = st.empty()

    for stage_result in cleaning_pipeline.stream_results():
        with progress_container.container():
            st.progress(stage_result.progress)
            st.text(f"Stage: {stage_result.stage_name}")
```

## 5. Configuratie

### 5.1 UI Configuratie

```yaml
# config/ui_settings.yaml
cleaning_ui:
  default_layout: "side_by_side"
  enable_preview: true
  max_diff_length: 5000  # Karakters
  highlight_colors:
    removed: "#ffcccc"
    added: "#ccffcc"
    modified: "#ffffcc"
  animation_duration: 300  # ms
```

### 5.2 Feature Flags

```python
FEATURE_FLAGS = {
    "enhanced_cleaning_ui": True,
    "cleaning_preview_mode": True,
    "custom_cleaning_profiles": False,  # Later release
    "cleaning_analytics_dashboard": True,
}
```

## 6. Error Handling

```python
def safe_render_comparison(cleaning_result):
    """Veilige rendering met fallback."""
    try:
        if not cleaning_result or not cleaning_result.original_text:
            st.info("Geen cleaning data beschikbaar")
            return

        # Check text length limits
        if len(cleaning_result.original_text) > MAX_DISPLAY_LENGTH:
            st.warning("Tekst te lang voor volledige weergave")
            # Render truncated version

        # Normal rendering
        render_comparison(cleaning_result)

    except Exception as e:
        logger.error(f"Fout bij cleaning UI render: {e}")
        # Fallback naar simpele text display
        st.text("Origineel:")
        st.code(cleaning_result.original_text[:500] + "...")
```

## 7. Testing Requirements

### 7.1 Component Tests

```python
def test_cleaning_comparison_component():
    """Test verschillende render modes."""
    component = CleaningComparisonComponent()

    # Test data
    result = create_mock_cleaning_result()

    # Test each layout mode
    for mode in ["side_by_side", "tabbed", "inline_diff"]:
        component.layout_mode = mode
        rendered = component.render(result)
        assert_valid_render(rendered)
```

### 7.2 Integration Tests

- Test met echte CleaningService resultaten
- Test state persistence tussen page reloads
- Test performance met grote teksten
- Test error scenarios

## 8. Migration Path

1. **Fase 1**: Implementeer nieuwe componenten naast bestaande
2. **Fase 2**: Feature flag voor nieuwe UI
3. **Fase 3**: A/B test met gebruikers
4. **Fase 4**: Volledig overschakelen

Deze technische specificatie geeft de developer alle informatie om de verbeterde UI te implementeren zonder visuele mockups.
