---
canonical: true
status: active
owner: validation
last_verified: 2025-09-02
applies_to: definitie-app@v2
---

# Business Validation Rules — DefinitieAgent (V2)

Doel: enkel de zakelijke (business) regels en acceptatiecriteria vastleggen, met verwijzingen naar canonieke bronnen en testartefacten.

## Core Acceptance Criteria

- Overall score moet ≥ 0.75 voor acceptatie.
- Lege definities zijn altijd onacceptabel.
- Circulaire definities (bijv. “Belasting is belasting”) zijn onacceptabel/major violation.

Bronnen:
- Config: `src/config/validation_rules.yaml` (thresholds/weights leidend)
- Golden dataset: `tests/fixtures/golden_definitions.yaml` (≥10–20 cases, incl. edge cases)

## Validation Weights & Impact (bron: YAML)

| Rule Code     | Beschrijving              | Weight | Impact    |
|---------------|---------------------------|--------|-----------|
| VAL-EMP-001   | Empty text                | 1.0    | Critical  |
| ESS-CONT-001  | Essential content         | 1.0    | Critical  |
| CON-CIRC-001  | Circular definition       | 0.8    | Major     |
| VAL-LEN-001   | Minimum length            | 0.9    | Major     |
| STR-ORG-001   | Structure                 | 0.7    | Moderate  |

Toelichting: dit is een representatieve tabel; de exacte set en waarden staan in de YAML‑config en zijn de bron van waarheid.

## Quality Thresholds

- Perfect: ≥ 0.80
- Acceptable: 0.75–0.80
- Borderline: 0.60–0.75
- Unacceptable: < 0.75

## Domain Rules (NL overheid)

- Gebruik overheidsterminologie; geen mixed‑language in NL definities.
- Goedgekeurde definities (established) zijn immutable; wijzigingen via nieuwe versieflow.

## Duplicate Detection Policy (samenvatting)

- Exact: begrip + context (organisatorisch/juridisch) gelijk → duplicaat.
- Fuzzy: vergelijk begrip semantisch/normalized; status ‘archived’ wordt niet meegenomen.

## Artefacten en Tests

- YAML configuratie: `src/config/validation_rules.yaml`.
- Golden dataset: `tests/fixtures/golden_definitions.yaml` (cases met expected score/acceptabel/violations).
- V2 smoke test: `tests/smoke/test_validation_v2_smoke.py` (offline, CI).
- (Optioneel) V2 unit tests: aggregatie/determinisme en loader‑fallback.

## Regression Prevention

- Elke businessregel wordt gedekt door ten minste één golden case.
- Nieuwe/gewijzigde regels: update zowel YAML (weights/thresholds) als golden cases.
- Breaking changes: duidelijk documenteren (changelog) en via feature flag/afgesproken gate.

## Legacy Mapping (indicatief)

| Legacy testbestand                                   | Status            | Geborgd in                                 |
|------------------------------------------------------|-------------------|--------------------------------------------|
| tests/integration/test_story_2_4_interface_migration.py | SAFE_TO_DELETE    | (Puur technisch; geen businessregels)      |
| tests/test_unified_service_v2.py                     | SAFE_TO_DELETE    | (Puur technisch; geen businessregels)      |
| tests/test_db_compatibility.py                       | SAFE_TO_DELETE    | (Puur technisch; geen businessregels)      |
| tests/test_ab_testing_framework.py                   | SAFE_TO_DELETE    | (Puur technisch; geen businessregels)      |
| tests/integration/test_simple_integration.py         | SAFE_TO_DELETE    | (Puur technisch; geen businessregels)      |
| …                                                    | …                 | …                                          |

NB: Voor legacy tests met impliciete businessregels (bijv. prompts/validatoren) geldt: regel/edge‑case vastleggen in golden cases + hierboven, vervolgens test verwijderen.
