# AI Configuration Guide

## Overzicht

DefinitieAgent gebruikt een gecentraliseerd AI configuratie systeem via `ConfigManager` dat component-specifieke AI instellingen mogelijk maakt. Dit document beschrijft hoe het systeem werkt en hoe je het kunt configureren.

## Core Configuratie Systeem

### ConfigManager (`src/config/config_manager.py`)

Het centrale configuratie systeem beheert alle AI-gerelateerde instellingen:

```python
from src.config.config_manager import get_config_manager, get_component_config

# Globale config manager
config = get_config_manager()

# Component-specifieke config
voorbeelden_config = get_component_config('voorbeelden', 'synoniemen')
```

### Standaard AI Configuratie

```python
@dataclass
class APIConfig:
    default_model: str = "gpt-4.1"           # Stabiel voor juridische definities
    default_temperature: float = 0.0          # Deterministisch voor consistentie
    default_max_tokens: int = 300            # Standaard token limiet

    model_settings: dict = {
        "gpt-4": {
            "max_tokens": 300,
            "temperature": 0.01,              # Zeer lage temperatuur
            "cost_per_token": 0.00003
        },
        "gpt-4.1": {
            "max_tokens": 300,
            "temperature": 0.0,               # Volledig deterministisch
            "cost_per_token": 0.00003
        }
    }
```

## Component-Specifieke Configuratie

### Configuratie Hiërarchie

Het systeem ondersteunt geneste component configuratie:

```yaml
# config/config_default.yaml
ai_components:
  voorbeelden:
    synoniemen:
      model: "gpt-4.1"
      temperature: 0.2      # Iets creatiever voor synoniemen
      max_tokens: 150
    uitleg:
      model: "gpt-4.1"
      temperature: 0.0      # Exact voor uitleg
      max_tokens: 200

  expert_review:
    model: "gpt-4.1"
    temperature: 0.0        # Strikt voor reviews
    max_tokens: 500

  definition_generator:
    model: "gpt-4.1"
    temperature: 0.0        # Deterministisch voor definities
    max_tokens: 300
```

### Component Config Ophalen

```python
# Hoofd component config
config = get_component_config('voorbeelden')

# Sub-component config
config = get_component_config('voorbeelden', 'synoniemen')

# Retourneert dict met:
# {
#   "model": "gpt-4.1",
#   "temperature": 0.2,
#   "max_tokens": 150
# }
```

## Environment Variabelen

De configuratie kan worden overschreven met environment variabelen:

```bash
# API configuratie
export OPENAI_API_KEY="sk-..."
export OPENAI_DEFAULT_MODEL="gpt-4.1"
export OPENAI_DEFAULT_TEMPERATURE="0.0"
export OPENAI_DEFAULT_MAX_TOKENS="300"

# Environment setting
export ENVIRONMENT="production"  # development, testing, staging, production

# Logging
export LOG_LEVEL="INFO"

# Rate limiting
export RATE_LIMIT_RPM="60"
export RATE_LIMIT_RPH="3000"
```

## Gebruik in Services

### AIServiceV2 Integratie

```python
from src.config.config_manager import get_component_config

class AIServiceV2:
    async def generate_response(
        self,
        prompt: str,
        component: str = None,
        sub_component: str = None,
        **kwargs
    ):
        # Component-specifieke config ophalen
        if component:
            config = get_component_config(component, sub_component)
            model = kwargs.get("model", config["model"])
            temperature = kwargs.get("temperature", config["temperature"])
            max_tokens = kwargs.get("max_tokens", config["max_tokens"])
        else:
            # Gebruik defaults
            model = kwargs.get("model", self.config.api.default_model)
            temperature = kwargs.get("temperature", self.config.api.default_temperature)
            max_tokens = kwargs.get("max_tokens", self.config.api.default_max_tokens)
```

### Voorbeelden Service

```python
class UnifiedVoorbeelden:
    def __init__(self, ai_service):
        self.ai_service = ai_service

    async def genereer_synoniemen(self, definitie: str):
        # Component-specifieke config wordt automatisch gebruikt
        response = await self.ai_service.generate_response(
            prompt=prompt,
            component="voorbeelden",
            sub_component="synoniemen"
        )
```

## Configuration Files

### Structuur

```
config/
├── config_default.yaml        # Standaard configuratie
├── config_development.yaml    # Development overrides
├── config_testing.yaml        # Test configuratie
├── config_staging.yaml        # Staging configuratie
└── config_production.yaml     # Productie configuratie
```

### Voorbeeld config_default.yaml

```yaml
api:
  default_model: "gpt-4.1"
  default_temperature: 0.0
  default_max_tokens: 300
  request_timeout: 30.0
  max_retries: 3

ai_components:
  definition_generator:
    model: "gpt-4.1"
    temperature: 0.0
    max_tokens: 300

  validation:
    toetsregels:
      model: "gpt-4.1"
      temperature: 0.0
      max_tokens: 200
    expert_review:
      model: "gpt-4.1"
      temperature: 0.0
      max_tokens: 500

  voorbeelden:
    synoniemen:
      model: "gpt-4.1"
      temperature: 0.2
      max_tokens: 150
    uitleg:
      model: "gpt-4.1"
      temperature: 0.0
      max_tokens: 200

cache:
  enabled: true
  default_ttl: 3600
  definition_ttl: 3600
  examples_ttl: 1800
  validation_ttl: 900

rate_limiting:
  enabled: true
  requests_per_minute: 60
  requests_per_hour: 3000
  tokens_per_second: 1.0
```

## Beveiliging Best Practices

1. **Nooit API keys in code**
   - Gebruik altijd environment variabelen
   - Configuratie files mogen GEEN secrets bevatten

2. **Environment-specifieke configs**
   - Development: Lagere rate limits
   - Production: Stricte security settings
   - Testen: Mock configuraties

3. **API Key Validatie**
   ```python
   config = get_config_manager()
   if not config.validate_api_key():
       raise ValueError("Invalid or missing API key")
   ```

## Monitoring & Metrics

De configuratie bevat ook monitoring instellingen:

```python
@dataclass
class MonitoringConfig:
    enabled: bool = True
    collect_metrics: bool = True

    # Cost tracking
    cost_threshold_daily: float = 10.0
    cost_threshold_monthly: float = 300.0

    # OpenAI pricing (per 1K tokens)
    openai_pricing: dict = {
        "gpt-4": 0.03,
        "gpt-4.1": 0.03
    }
```

## Troubleshooting

### Check huidige configuratie

```python
from src.config.config_manager import get_config_manager

config = get_config_manager()
print(config.get_environment_info())
```

### Reload configuratie

```python
from src.config.config_manager import reload_config

reload_config()  # Herlaad alle configuratie files
```

### Configuratie callbacks

```python
def on_config_change(section, key, old_value, new_value):
    print(f"Config changed: {section}.{key} from {old_value} to {new_value}")

config.register_change_callback("api", on_config_change)
```

## Migration Guide

Voor teams die migreren van hardcoded configuratie:

1. **Identificeer hardcoded waarden**
   ```bash
   grep -r "temperature=" src/
   grep -r "model=" src/
   ```

2. **Vervang met config calls**
   ```python
   # Oud (hardcoded)
   temperature = 0.7

   # Nieuw (geconfigureerd)
   from src.config.config_manager import get_component_config
   config = get_component_config('my_component')
   temperature = config['temperature']
   ```

3. **Voeg component config toe**
   ```yaml
   # config/config_default.yaml
   ai_components:
     my_component:
       model: "gpt-4.1"
       temperature: 0.7
       max_tokens: 200
   ```

4. **Test met verschillende environments**
   ```bash
   ENVIRONMENT=development python src/main.py
   ENVIRONMENT=production python src/main.py
   ```

## Component Configuratie Voorbeelden

### Definition Generator
```yaml
definition_generator:
  model: "gpt-4.1"
  temperature: 0.0    # Volledig deterministisch
  max_tokens: 300
```

### Validation Service
```yaml
validation:
  toetsregels:
    model: "gpt-4.1"
    temperature: 0.0  # Strikte validatie
    max_tokens: 200
  expert_review:
    model: "gpt-4.1"
    temperature: 0.0
    max_tokens: 500
```

### Voorbeelden Generator
```yaml
voorbeelden:
  synoniemen:
    model: "gpt-4.1"
    temperature: 0.2  # Licht creatief
    max_tokens: 150
  uitleg:
    model: "gpt-4.1"
    temperature: 0.0  # Exact
    max_tokens: 200
  gebruiksvoorbeelden:
    model: "gpt-4.1"
    temperature: 0.1  # Minimaal creatief
    max_tokens: 250
```

## Toekomstige Uitbreidingen

- [ ] Hot-reloading van configuratie zonder restart
- [ ] A/B testing met verschillende model configuraties
- [ ] Automatische fallback naar goedkopere modellen bij errors
- [ ] Cost-based model selectie
- [ ] Prestaties-based temperature tuning
