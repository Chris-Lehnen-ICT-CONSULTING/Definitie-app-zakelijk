# Configuratie Systeem Audit - Definitie-app

## Executive Summary

Het Definitie-app project heeft momenteel **twee overlappende configuratie systemen** die naast elkaar bestaan, wat leidt tot inconsistenties en verwarring. Deze audit geeft een volledig overzicht van de huidige situatie.

## 1. ConfigManager Systeem (`src/config/config_manager.py`)

### Structuur en Functionaliteit

**Kerncomponenten:**
- **Environment Enum**: Development, Testing, Staging, Production
- **ConfigSection Enum**: API, Cache, Paths, UI, Validation, Monitoring, Logging, Rate Limiting, Resilience, Security
- **Dataclasses**: APIConfig, CacheConfig, PathsConfig, UIConfig, ValidationConfig, etc.
- **ConfigManager Class**: Centrale manager voor alle configuratie

**Belangrijke Features:**
- Environment-specifieke configuratie (YAML bestanden)
- Omgevingsvariabelen overschrijving
- Hot-reloading mogelijkheden
- Change callbacks voor dynamische updates
- Validatie van configuratie waarden

**Standaard Waarden:**
```python
# API Defaults
default_model: str = "gpt-5"
default_temperature: float = 0.01
default_max_tokens: int = 300

# Model-specifieke settings
"gpt-4": {
    "temperature": 0.01,
    "max_tokens": 300
},
"gpt-5": {
    "temperature": 0.0,
    "max_tokens": 300
}
```

### Helper Functies

```python
get_default_model() -> str  # Retourneert "gpt-5"
get_default_temperature() -> float  # Retourneert 0.01
fill_ai_defaults(**kwargs) -> dict  # Vult None waarden met defaults
```

### Modules die ConfigManager gebruiken

**Direct gebruik:**
- `src/config/config_adapters.py` - Bridge tussen ConfigManager en legacy code
- `src/services/ai_service.py` - Gebruikt get_default_model/temperature functies
- `src/toetsregels/adapter.py` - Via config_adapters

**Via config_adapters:**
- Verschillende utils modules (retry, resilience, rate limiting)
- UI componenten voor Streamlit configuratie

## 2. UnifiedGeneratorConfig Systeem (`src/services/definition_generator_config.py`)

### Structuur en Functionaliteit

**Kerncomponenten:**
- **GenerationStrategy Enum**: BASIC, CONTEXT_AWARE, HYBRID, ADAPTIVE
- **CacheStrategy Enum**: NONE, MEMORY, REDIS, HYBRID
- **Dataclasses**: GPTConfig, CacheConfig, ContextConfig, QualityConfig, MonitoringConfig, CompatibilityConfig
- **UnifiedGeneratorConfig**: Master configuratie class

**Standaard Waarden:**
```python
# GPTConfig defaults
model: str = "gpt-5"
temperature: float = 0.0
max_tokens: int = 350

# QualityConfig
enhancement_temperature: float = 0.5
enhancement_max_tokens: int = 300
```

### Modules die UnifiedGeneratorConfig gebruiken

**Direct gebruik:**
- `src/services/container.py` - Service container met eigen defaults
- `src/services/definition_orchestrator.py` - Via container
- `src/ui/components/definition_generator_tab.py`
- `src/services/prompts/` modules - Verschillende prompt componenten

## 3. Service Container Defaults (`src/services/container.py`)

De service container overschrijft centrale configuratie met eigen defaults:

```python
# In _load_configuration():
gpt_config = GPTConfig(
    model=self.config.get("generator_model", "gpt-5"),
    temperature=self.config.get("generator_temperature", 0.4),  # VERSCHILT van centrale config!
    api_key=self.openai_api_key,
)
```

**Probleem**: Container default temperature (0.4) verschilt van beide configuratie systemen (0.0/0.01)

### Container Config Presets

```python
# Development
"generator_temperature": 0.5  # Weer anders!

# Testing
# Geen specifieke temperature override

# Production
"generator_temperature": 0.0  # Consistent met UnifiedGeneratorConfig
```

## 4. Hardcoded Waarden

### Voorbeelden Modules (`src/voorbeelden/`)

Alle voorbeelden modules hebben hardcoded waarden:

**voorbeelden.py:**
- `temperature=0.5` (regels 28, 68, 114)
- `model=None` (vertrouwt op fill_ai_defaults)

**async_voorbeelden.py:**
- `model="gpt-4"` (hardcoded oud model)
- `temperature` varieert: 0.2, 0.3, 0.5, 0.6

**cached_voorbeelden.py:**
- Zelfde patroon als async_voorbeelden.py
- Mix van temperatures: 0.2, 0.3, 0.5, 0.6

**unified_voorbeelden.py:**
- Mogelijk gebruik van configuratie systeem (niet direct zichtbaar)

### AI Service (`src/services/ai_service.py`)

- Gebruikt ConfigManager helper functies correct
- AIRequest dataclass vult defaults aan via `__post_init__`
- Geen hardcoded waarden

## 5. Test Files Impact

### Tests die ConfigManager gebruiken:
- `tests/unit/test_config_system.py` - Test van ConfigManager zelf
- `tests/integration/test_modular_prompts.py`
- Verschillende regression tests

### Tests die UnifiedGeneratorConfig gebruiken:
- `tests/manual_test_regeneration.py`
- `tests/manual_test_enhanced_ui_flow.py`
- Service-specifieke tests

**Impact van wijzigingen:**
- Tests kunnen falen als defaults veranderen
- Sommige tests vertrouwen op specifieke configuratie waarden
- Manual tests kunnen andere resultaten geven

## 6. Configuratie Overlap en Conflicten

### Overlappende Configuratie Items

| Item | ConfigManager | UnifiedGeneratorConfig | Container Default |
|------|--------------|----------------------|-------------------|
| Model | gpt-5 | gpt-5 | gpt-5 |
| Temperature | 0.01 | 0.0 | 0.4 |
| Max Tokens | 300 | 350 | Via config |
| Cache TTL | 3600 | 3600 | - |
| Retry Count | 3 | 3 | - |

### Conflict Bronnen

1. **Temperature Inconsistenties**:
   - ConfigManager: 0.01
   - UnifiedGeneratorConfig: 0.0
   - Container default: 0.4
   - Container development: 0.5
   - Voorbeelden: 0.2-0.6

2. **Model Versie Management**:
   - Centrale config: gpt-5
   - Async voorbeelden: gpt-4 (verouderd)
   - Geen centrale migratie strategie

3. **Dubbele Configuratie Paden**:
   - ConfigManager via environment/YAML
   - UnifiedGeneratorConfig via environment
   - Container via constructor dict

## 7. Categorisatie per Module Type

### Core Services
- Gebruiken voornamelijk UnifiedGeneratorConfig via Container
- Sommige gebruiken ConfigManager via adapters

### UI Componenten
- Mix van beide systemen
- Streamlit config via ConfigManager
- Generator settings via UnifiedGeneratorConfig

### Utilities
- Voornamelijk ConfigManager via adapters
- Clean abstractie via adapter pattern

### Voorbeelden/Demo Code
- Volledig hardcoded waarden
- Geen gebruik van configuratie systemen
- Verouderde model referenties

## 8. Aanbevelingen

### Korte Termijn
1. **Centraliseer temperature defaults** - Kies één waarde en gebruik overal
2. **Update voorbeelden modules** - Gebruik configuratie i.p.v. hardcoded waarden
3. **Migreer van gpt-4 naar gpt-5** in alle voorbeelden code

### Middellange Termijn
1. **Consolideer configuratie systemen** - Één systeem i.p.v. twee
2. **Verwijder Container overrides** - Laat Container centrale config gebruiken
3. **Implementeer configuratie hiërarchie** - Duidelijke override volgorde

### Lange Termijn
1. **Type-safe configuratie** - Gebruik Pydantic voor runtime validatie
2. **Configuratie UI** - Admin interface voor runtime config changes
3. **Configuratie audit trail** - Log alle configuratie wijzigingen

## 9. Migratie Pad

### Fase 1: Normalisatie (1-2 weken)
- Standaardiseer alle temperature waarden naar 0.0
- Update alle gpt-4 referenties naar gpt-5
- Fix voorbeelden modules om configuratie te gebruiken

### Fase 2: Consolidatie (2-4 weken)
- Kies hoofdconfiguratie systeem (aanbeveling: ConfigManager)
- Migreer UnifiedGeneratorConfig settings naar ConfigManager
- Update alle imports en dependencies

### Fase 3: Cleanup (1-2 weken)
- Verwijder deprecated configuratie code
- Update documentatie
- Voeg configuratie tests toe

## 10. Risico's

1. **Breaking Changes**: Tests kunnen falen door gewijzigde defaults
2. **Performance Impact**: Andere temperature kan output quality beïnvloeden
3. **Backwards Compatibility**: Bestaande deployments kunnen breken
4. **Hidden Dependencies**: Niet alle configuratie gebruik is direct zichtbaar

## Conclusie

Het huidige configuratie landschap is gefragmenteerd met significante inconsistenties, vooral rond temperature settings. Een gestructureerde consolidatie is noodzakelijk om maintainability te verbeteren en bugs te voorkomen.

De ConfigManager biedt de meest complete oplossing met environment support, hot-reloading en validatie. Het consolideren rond dit systeem met de features van UnifiedGeneratorConfig zou de beste path forward zijn.
