---
canonical: false
status: archived
owner: architecture
last_verified: 2025-09-02
applies_to: definitie-app@v2
---

# [ARCHIVED] Verbeterde Definitie Opschoning Architectuur

Deze versie is gearchiveerd. Actuele informatie staat in:
- `docs/architectuur/improved-cleaning-architecture.md`

**Auteur**: Winston (System Architect)
**Datum**: 2025-08-25
**Versie**: 1.0

## Executive Summary

Dit document beschrijft een verbeterde architectuur voor de definitie opschoning module die:
- Een meer modulaire en uitbreidbare pipeline implementeert
- Betere traceerbaarheid biedt van alle transformaties
- UI verbeteringen mogelijk maakt voor side-by-side vergelijking
- Performance en schaalbaarheid verbetert

## 1. Huidige Situatie Analyse

### 1.1 Sterke Punten
- ✅ CleaningService scheidt concerns goed
- ✅ Opschoning bewaart origineel in metadata
- ✅ UI toont al beide versies (origineel en opgeschoond)
- ✅ Cleaning rules zijn configureerbaar via JSON

### 1.2 Verbeterpunten
- ❌ Opschoning gebeurt VOOR validatie (geen inzicht in AI kwaliteit)
- ❌ Beperkte set van opschoning regels (alleen prefix/suffix)
- ❌ Geen gradaties in opschoning (alles of niets)
- ❌ UI presentatie kan verbeterd worden (niet prominent genoeg)
- ❌ Geen analytics over welke regels het meest worden toegepast

## 2. Voorgestelde Architectuur

### 2.1 Enhanced Cleaning Pipeline

```python
# Nieuwe pipeline structuur
class EnhancedCleaningPipeline:
    """
    Modulaire cleaning pipeline met meerdere stages en configureerbare regels.
    """

    stages = [
        # Stage 1: Syntax Cleaning
        RemoveForbiddenPrefixesStage(),      # Huidige functionaliteit
        RemoveCircularDefinitionsStage(),     # Huidige functionaliteit
        CorrectCapitalizationStage(),        # Huidige functionaliteit
        AddPunctuationStage(),               # Huidige functionaliteit

        # Stage 2: Semantic Cleaning (NIEUW)
        RemoveRedundancyStage(),             # Verwijder onnodige herhalingen
        SimplifyComplexSentencesStage(),     # Vereenvoudig complexe zinnen
        RemoveFillerWordsStage(),            # Verwijder vulwoorden

        # Stage 3: Quality Enhancement (NIEUW)
        ImproveReadabilityStage(),           # Verbeter leesbaarheid
        StandardizeTerminologyStage(),       # Standaardiseer terminologie
        AddStructureMarkersStage(),          # Voeg structuur markers toe
    ]
```

### 2.2 Cleaning Result Tracking

```python
@dataclass
class EnhancedCleaningResult:
    """Uitgebreide tracking van alle cleaning transformaties."""

    # Basis informatie
    original_text: str
    final_text: str

    # Stage tracking
    stage_results: List[StageResult]  # Per stage: input, output, applied rules

    # Analytics
    total_changes: int
    readability_improvement: float
    quality_score_delta: float

    # Visualisatie data
    diff_segments: List[DiffSegment]  # Voor UI highlighting
    transformation_timeline: List[TransformationStep]
```

### 2.3 Configureerbare Cleaning Profiles

```yaml
# cleaning_profiles.yaml
profiles:
  strict:
    name: "Streng"
    description: "Maximale opschoning voor formele documenten"
    enabled_stages: ["syntax", "semantic", "quality"]
    aggressiveness: high

  moderate:
    name: "Gematigd"
    description: "Balans tussen opschoning en behoud origineel"
    enabled_stages: ["syntax", "semantic"]
    aggressiveness: medium

  light:
    name: "Licht"
    description: "Minimale opschoning, alleen syntax correcties"
    enabled_stages: ["syntax"]
    aggressiveness: low

  custom:
    name: "Aangepast"
    description: "Gebruiker selecteert individuele regels"
    user_configurable: true
```

## 3. UI Verbeteringen

### 3.1 Side-by-Side Comparison View

```python
def render_cleaning_comparison(result: EnhancedCleaningResult):
    """Verbeterde UI voor cleaning resultaten."""

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🤖 Originele AI Output")
        # Highlight problematische delen
        annotated_text = highlight_issues(
            result.original_text,
            result.stage_results
        )
        st.markdown(annotated_text)

    with col2:
        st.subheader("✨ Opgeschoonde Definitie")
        # Highlight verbeteringen
        improved_text = highlight_improvements(
            result.final_text,
            result.stage_results
        )
        st.markdown(improved_text)

    # Transformatie timeline
    with st.expander("🔄 Opschoning Stappen"):
        render_transformation_timeline(result.transformation_timeline)

    # Analytics dashboard
    with st.expander("📊 Opschoning Analytics"):
        render_cleaning_metrics(result)
```

### 3.2 Interactive Cleaning Controls

```python
def render_cleaning_controls():
    """Gebruiker controle over cleaning proces."""

    # Profile selector
    profile = st.selectbox(
        "Opschoning Profiel",
        ["strict", "moderate", "light", "custom"],
        help="Selecteer hoeveel opschoning toegepast moet worden"
    )

    if profile == "custom":
        # Toon individuele regel toggles
        st.subheader("Selecteer Opschoning Regels")

        rules = {}
        for stage in cleaning_stages:
            rules[stage.name] = st.checkbox(
                stage.display_name,
                value=stage.default_enabled,
                help=stage.description
            )

    # Preview mode
    if st.toggle("Preview Mode", help="Bekijk wijzigingen voor toepassing"):
        show_cleaning_preview(current_definition)
```

## 4. Implementatie Roadmap

### Phase 1: Core Refactoring (Week 1-2)
1. **Refactor opschoning.py naar stage-based pipeline**
   - Behoud backward compatibility
   - Implementeer StageResult tracking
   - Voeg unit tests toe per stage

2. **Enhance CleaningService met nieuwe pipeline**
   - Integreer EnhancedCleaningPipeline
   - Implementeer profile support
   - Update interfaces voor rich results

### Phase 2: Nieuwe Cleaning Stages (Week 3-4)
1. **Implementeer Semantic Cleaning stages**
   - RemoveRedundancyStage
   - SimplifyComplexSentencesStage
   - RemoveFillerWordsStage

2. **Implementeer Quality Enhancement stages**
   - ImproveReadabilityStage
   - StandardizeTerminologyStage
   - AddStructureMarkersStage

### Phase 3: UI Improvements (Week 5-6)
1. **Update definition_generator_tab.py**
   - Implementeer side-by-side view
   - Voeg transformation timeline toe
   - Integreer cleaning analytics

2. **Voeg Interactive Controls toe**
   - Profile selector
   - Custom rule configuration
   - Preview mode

### Phase 4: Analytics & Monitoring (Week 7-8)
1. **Implementeer Cleaning Analytics**
   - Track meest gebruikte regels
   - Monitor quality improvements
   - Genereer insights rapporten

2. **Performance Optimalisatie**
   - Cache cleaning results
   - Parallelliseer stages waar mogelijk
   - Implementeer lazy evaluation

## 5. Testing Strategie

### 5.1 Unit Tests
```python
# Per cleaning stage
def test_remove_forbidden_prefixes_stage():
    stage = RemoveForbiddenPrefixesStage()

    test_cases = [
        ("Is een definitie", "Een definitie"),
        ("betekent iets", "Iets"),
        ("De term", "Term"),
    ]

    for input_text, expected in test_cases:
        result = stage.apply(input_text, "term")
        assert result.output == expected
        assert result.rules_applied == ["removed_forbidden_prefix"]
```

### 5.2 Integration Tests
- Test complete pipeline met verschillende profiles
- Valideer UI rendering met mock data
- Performance benchmarks per stage

### 5.3 User Acceptance Tests
- A/B test verschillende cleaning profiles
- Gebruikersfeedback op UI improvements
- Expert review van opgeschoonde definities

## 6. Migratie Strategie

1. **Fase 1**: Implementeer nieuwe architectuur naast bestaande
2. **Fase 2**: Feature flag voor nieuwe cleaning pipeline
3. **Fase 3**: Gradual rollout naar gebruikers
4. **Fase 4**: Deprecate oude implementatie

## 7. Success Metrics

- **Quality Metrics**:
  - 20% verbetering in definitie kwaliteitsscore
  - 50% reductie in expert correcties
  - 90% gebruikerstevredenheid

- **Performance Metrics**:
  - <100ms cleaning latency
  - <500ms UI render tijd
  - Zero blocking operations

- **Usage Metrics**:
  - 80% adoptie van cleaning profiles
  - 30% gebruikers past settings aan
  - 95% definities worden opgeschoond

## 8. Risico's en Mitigatie

| Risico | Impact | Mitigatie |
|--------|--------|-----------|
| Over-cleaning verwijdert te veel | Hoog | Preview mode, undo functionaliteit |
| Performance degradatie | Medium | Caching, lazy evaluation |
| Complexiteit voor gebruikers | Medium | Goede defaults, progressive disclosure |
| Breaking changes | Hoog | Feature flags, gradual rollout |

## 9. Conclusie

Deze verbeterde architectuur biedt:
- ✅ Modulaire, uitbreidbare cleaning pipeline
- ✅ Rijke tracking van alle transformaties
- ✅ Verbeterde UI met side-by-side vergelijking
- ✅ Configureerbare cleaning profiles
- ✅ Analytics en monitoring capabilities

De implementatie kan incrementeel gebeuren zonder breaking changes, met duidelijke value delivery in elke fase.
