# Golden Dataset voor Validation Testen

**Status**: ACTIEF
**Versie**: 1.0.0
**Laatst Bijgewerkt**: 29-08-2025
**Eigenaar**: QA Team

## Overzicht

Dit document beschrijft het golden dataset voor ValidationOrchestratorV2 testing. Het golden dataset bevat referentie-definities met bekende validation scores en wordt gebruikt voor:
- Regressie testing
- Prestaties benchmarking
- Contract compliance verificatie
- Drift detectie tussen versies

## Dataset Structuur

### Locatie & Opslag
```
data/testing/golden-dataset/
├── definitions/
│   ├── valid/           # 100% valide definities
│   ├── invalid/         # Definities met bekende fouten
│   └── edge-cases/      # Rand gevallen
├── expected-results/    # Verwachte validation resultaten
└── metadata.json        # Dataset metadata en versie info
```

### Dataset Samenstelling

| Categorie | Aantal | Beschrijving |
|-----------|--------|--------------|
| Valid Definitions | 50 | Perfecte definities (score > 0.95) |
| Invalid Definitions | 30 | Definities met specifieke fouten |
| Edge Cases | 20 | Grensgevallen en speciale karakters |
| **Totaal** | **100** | Complete test coverage |

## Definitie Categorieën

### Valid Definitions (50)
```json
{
  "category": "valid",
  "examples": [
    {
      "id": "GD-VAL-001",
      "term": "natuurlijk persoon",
      "definition": "mens van vlees en bloed met rechtspersoonlijkheid vanaf geboorte tot overlijden",
      "expected_score": 0.98,
      "tolerance": 0.02
    }
  ]
}
```

### Invalid Definitions (30)
```json
{
  "category": "invalid",
  "examples": [
    {
      "id": "GD-INV-001",
      "term": "burger",
      "definition": "De burger is een persoon die...",
      "expected_violations": ["GRAMMAR_001"],
      "expected_score": 0.65,
      "tolerance": 0.05,
      "reason": "Begint met lidwoord"
    }
  ]
}
```

### Edge Cases (20)
```json
{
  "category": "edge-cases",
  "examples": [
    {
      "id": "GD-EDG-001",
      "term": "e-mail",
      "definition": "elektronisch bericht verzonden via TCP/IP protocol",
      "notes": "Speciale karakters in term",
      "expected_score": 0.90,
      "tolerance": 0.03
    }
  ]
}
```

## Update Process

### Versie Beheer
- Golden dataset volgt semantic versioning (MAJOR.MINOR.PATCH)
- MAJOR: Breaking changes in dataset structuur
- MINOR: Nieuwe test cases toegevoegd
- PATCH: Fixes in bestaande cases

### Update Werkstroom
1. **Propose Change**: Via PR met rationale
2. **Review**: Door QA Lead + Tech Lead
3. **Impact Analysis**: Check op downstream tests
4. **Approval**: Minimum 2 reviewers
5. **Versie Bump**: Update metadata.json
6. **Snapshot**: Maak backup van oude versie

### Change Log Format
```markdown
## [1.1.0] - 2025-MM-DD
### Added
- 5 nieuwe edge cases voor Unicode support
### Changed
- Updated tolerance voor GD-VAL-001
### Fixed
- Typo in GD-INV-003 definition
```

## Drift Detection

### Drift Drempels
| Metric | Warning | Critical | Action |
|--------|---------|----------|--------|
| Score Drift | > 3% | > 5% | Block deployment |
| New Violations | > 2 | > 5 | Investigation required |
| Missing Violations | > 1 | > 3 | Contract review |
| Prestaties | > 10% slower | > 20% slower | Prestaties analysis |

### Monitoring Script
```python
def check_drift(current_results, golden_results):
    """Vergelijk huidige resultaten met golden dataset."""
    drift_report = {
        "timestamp": datetime.now().isoformat(),
        "version": GOLDEN_DATASET_VERSION,
        "drifts": []
    }

    for golden, current in zip(golden_results, current_results):
        score_drift = abs(golden.score - current.score)
        if score_drift > golden.tolerance:
            drift_report["drifts"].append({
                "id": golden.id,
                "expected": golden.score,
                "actual": current.score,
                "drift": score_drift,
                "severity": "KRITIEK" if score_drift > 0.05 else "WARNING"
            })

    return drift_report
```

## Snapshot Management

### Snapshot Creation
```bash
# Create snapshot before update
./scripts/snapshot-golden-dataset.sh create "Pre-v1.1.0 update"

# Restore snapshot if needed
./scripts/snapshot-golden-dataset.sh restore "29-08-2025-v1.0.0"
```

### Retention Policy
- Keep last 5 versions
- Archive older versions to cold storage
- Maintain change log for all versions

## Integration met CI/CD

### Pre-Uitrol Check
```yaml
# .github/workflows/golden-dataset-check.yml
- name: Golden Dataset Validation
  run: |
    python scripts/validate_golden_dataset.py
    if [ $? -ne 0 ]; then
      echo "Golden dataset validation failed!"
      exit 1
    fi
```

### Automated Regression Test
```python
@pytest.mark.golden
def test_golden_dataset_regression():
    """Test alle golden dataset cases."""
    orchestrator = ValidationOrchestratorV2()
    results = []

    for case in load_golden_dataset():
        result = await orchestrator.validate_definition(case.definition)
        assert_within_tolerance(result.score, case.expected_score, case.tolerance)
        results.append(result)

    generate_drift_report(results)
```

## Maintenance

### Weekly Review
- Check voor drift trends
- Review failed cases
- Update edge cases based on production issues

### Monthly Update
- Add new cases from production
- Remove obsolete cases
- Update tolerance based on metrics

### Quarterly Audit
- Full dataset review
- Prestaties baseline update
- Contract alignment check

## Contacten

- **Dataset Eigenaar**: QA Team Lead
- **Technical Contact**: Senior Developer
- **Approval Board**: QA Lead, Tech Lead, Product Eigenaar

---

*Voor vragen of updates, open een issue in het project repository met label `golden-dataset`.*
