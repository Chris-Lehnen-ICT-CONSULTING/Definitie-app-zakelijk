# Feature Flags Configuration Guide

## Overview

Feature flags worden gebruikt voor veilige, graduele rollout van V2 services. Flags kunnen geconfigureerd worden via environment variables of programmatisch.

## Environment Variables

Alle feature flags kunnen overschreven worden via environment variables met het prefix `FEATURE_FLAG_`.

### Boolean Flags

Voor aan/uit schakelaars:
```bash
# Enable/disable features
export FEATURE_FLAG_VALIDATION_ORCHESTRATOR_V2=true
export FEATURE_FLAG_AI_SUGGESTIONS=false
export FEATURE_FLAG_BATCH_PROCESSING=true
```

Geaccepteerde waarden:
- `true`, `1`, `yes`, `on` → enabled
- `false`, `0`, `no`, `off` → disabled

### Shadow Mode

Voor side-by-side vergelijking zonder impact:
```bash
# Run both V1 and V2, log differences
export FEATURE_FLAG_VALIDATION_ORCHESTRATOR_V2_SHADOW=true
```

### Canary Deployments

Voor percentage-based rollouts:
```bash
# Enable for 10% of users (waarde is percentage 0-100)
export FEATURE_FLAG_VALIDATION_ORCHESTRATOR_V2_CANARY=10
```

## Available Flags

### Validation Orchestrator V2
- `FEATURE_FLAG_VALIDATION_ORCHESTRATOR_V2` - Enable V2 orchestrator
- `FEATURE_FLAG_VALIDATION_ORCHESTRATOR_V2_SHADOW` - Run in shadow mode
- `FEATURE_FLAG_VALIDATION_ORCHESTRATOR_V2_CANARY` - Canary percentage (0-100)

### AI Features
- `FEATURE_FLAG_AI_SUGGESTIONS` - Enable AI-powered suggestions (default: true)
- `FEATURE_FLAG_AI_VALIDATION` - Enable AI validation rules (default: true)

### Performance
- `FEATURE_FLAG_BATCH_PROCESSING` - Enable batch processing (default: true)
- `FEATURE_FLAG_ASYNC_VALIDATION` - Enable async validation (default: true)

### Monitoring
- `FEATURE_FLAG_ENHANCED_METRICS` - Enable detailed metrics (default: true)
- `FEATURE_FLAG_CORRELATION_TRACKING` - Enable correlation ID tracking (default: true)

## Usage Examples

### Development Environment
```bash
# Full V2 testing
export FEATURE_FLAG_VALIDATION_ORCHESTRATOR_V2=true
export FEATURE_FLAG_VALIDATION_ORCHESTRATOR_V2_SHADOW=false
export FEATURE_FLAG_ENHANCED_METRICS=true
```

### Staging Environment
```bash
# Shadow mode for comparison
export FEATURE_FLAG_VALIDATION_ORCHESTRATOR_V2=false
export FEATURE_FLAG_VALIDATION_ORCHESTRATOR_V2_SHADOW=true
export FEATURE_FLAG_ENHANCED_METRICS=true
```

### Production Rollout
```bash
# Start with 5% canary
export FEATURE_FLAG_VALIDATION_ORCHESTRATOR_V2_CANARY=5

# Increase to 25%
export FEATURE_FLAG_VALIDATION_ORCHESTRATOR_V2_CANARY=25

# Full rollout
export FEATURE_FLAG_VALIDATION_ORCHESTRATOR_V2=true
export FEATURE_FLAG_VALIDATION_ORCHESTRATOR_V2_CANARY=0
```

## Programmatic Usage

```python
from services.feature_flags import FeatureFlag, get_feature_flags

# Check if feature is enabled
flags = get_feature_flags()
if flags.is_enabled(FeatureFlag.VALIDATION_ORCHESTRATOR_V2):
    # Use V2
    pass

# Check shadow mode
if flags.is_shadow_mode(FeatureFlag.VALIDATION_ORCHESTRATOR_V2):
    # Run both versions
    pass

# Set canary percentage
flags.set_canary_percentage(FeatureFlag.VALIDATION_ORCHESTRATOR_V2, 10.0)

# Emergency kill switch
flags.kill_switch(FeatureFlag.VALIDATION_ORCHESTRATOR_V2)
```

## Monitoring

Check current flag status:
```python
from services.feature_flags import get_feature_flags

flags = get_feature_flags()
status = flags.get_status()
print(status)
# Output:
# {
#   "flags": {...},
#   "canary_percentages": {...}
# }
```

## Rollback Procedures

Bij problemen met V2:

1. **Immediate rollback** (kill switch):
   ```bash
   export FEATURE_FLAG_VALIDATION_ORCHESTRATOR_V2=false
   export FEATURE_FLAG_VALIDATION_ORCHESTRATOR_V2_SHADOW=false
   export FEATURE_FLAG_VALIDATION_ORCHESTRATOR_V2_CANARY=0
   ```

2. **Programmatic kill switch**:
   ```python
   flags.kill_switch(FeatureFlag.VALIDATION_ORCHESTRATOR_V2)
   ```

3. **Restart services** om wijzigingen door te voeren

## Best Practices

1. **Start met shadow mode** om V2 te valideren zonder impact
2. **Gebruik canary deployments** voor graduele rollout
3. **Monitor metrics** tijdens rollout voor performance verschillen
4. **Have rollback ready** - test kill switch procedures vooraf
5. **Document flag changes** in deployment logs

## Integration with Story 2.3

In Story 2.3 (Container Wiring) wordt de feature flag manager geïntegreerd in de dependency injection container om automatisch tussen V1 en V2 orchestrators te schakelen op basis van flags.
