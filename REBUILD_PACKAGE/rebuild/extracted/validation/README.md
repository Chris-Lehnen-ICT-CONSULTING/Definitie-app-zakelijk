# Validation Rules Configuration

**Directory:** config/validation_rules/
**Purpose:** YAML configurations for all 46 validation rules
**Format:** Category-based subdirectories (arai/, con/, ess/, int/, sam/, str/, ver/, dup/)

## Structure

```
config/validation_rules/
├── arai/          # 9 ARAI rules (Atomiciteit, Relevantie, Actualiteit, Inzichtelijkheid)
├── con/           # 6 CON rules (Consistentie)
├── ess/           # 8 ESS rules (Essentialiteit)
├── int/           # 6 INT rules (Intertextuele relaties)
├── sam/           # 7 SAM rules (Samenhang)
├── str/           # 4 STR rules (Structuur)
├── ver/           # 4 VER rules (Verstaanbaarheid)
├── dup/           # 2 DUP rules (Duplicate detection)
└── README.md      # This file
```

## Example Rule: ARAI-01.yaml

```yaml
id: ARAI-01
category: arai
priority: high
enabled: true
metadata:
  naam: "Atomiciteit: Eén begrip per definitie"
  uitleg: "Een definitie moet zich beperken tot precies één begrip"
  version: "1.0"
  code_reference: "src/toetsregels/regels/ARAI-01.py"
patterns:
  - type: count
    description: "Tel aantal begrippen in definitie"
    regex: null
    threshold: 1
validation:
  severity: error
  message: "Definitie bevat meer dan één begrip"
  suggestion: "Split definitie in meerdere aparte definities"
```

## Usage

1. **Week 1 Extraction:** Use `rebuild/scripts/extract_rule.py` to generate YAMLs from Python
2. **Testing:** Configurations loaded by `ValidationService` during rule execution
3. **Customization:** Edit YAML to adjust priority, patterns, thresholds

## Status

- ✅ Structure created (8 directories)
- ✅ Example ARAI-01.yaml present
- ⏳ Remaining 45 rules: Generate via extraction script during Week 1

