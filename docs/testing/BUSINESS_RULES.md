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

## Validation Rules Details (harde drempels)

- VAL-LEN-001 (te kort): minder dan 5 woorden of minder dan 15 karakters → fail (0.0) met violation VAL-LEN-001.
- VAL-LEN-002 (te lang): meer dan 80 woorden of meer dan 600 karakters → fail (0.0) met violation VAL-LEN-002.
- ESS-CONT-001 (essentie ontbreekt): minder dan 6 woorden → fail (0.0) met ESS-CONT-001.
- CON-CIRC-001 (circulair): begrip komt (case-insensitive) in de definitietekst voor → major violation.
- STR-TERM-001/STR-ORG-001 (terminologie/structuur): structurele/terminologie‑issues met impact conform YAML‑gewichten.

NB: berichtteksten zijn implementatie‑details; drempels en codes borgen het beleid.

## Resultaatcontract‑invarianten (ValidationResult)

- Verplichte velden: version, overall_score, is_acceptable, violations, passed_rules, detailed_scores, system.
- system.correlation_id: altijd aanwezig; UUID (gegenereerd indien niet meegegeven).
- Violations: deterministisch gesorteerd (stabiele volgorde).
- is_acceptable: afgeleid van thresholds/weights; overall_accept (YAML) = 0.75.

## Determinisme

- V2‑validatie is deterministisch: bij identieke input/parameters blijft score/violations/detailed_scores gelijk.
- Golden cases moeten identieke resultaten geven bij herhaalde runs (geen randomness in regels/aggregatie).

## Quality Thresholds

- Perfect: ≥ 0.80
- Acceptable: 0.75–0.80
- Borderline: 0.60–0.75
- Unacceptable: < 0.75

## Domain Rules (NL overheid)

- Gebruik overheidsterminologie; geen mixed‑language in NL definities.
- Goedgekeurde definities (established) zijn immutable; wijzigingen via nieuwe versieflow.

NB: Taalregels (LANG‑…) zijn config‑afhankelijk. In de standaard YAML zijn deze niet geactiveerd; golden cases met taal‑mix gelden alleen wanneer de betreffende regels enabled zijn.

## Duplicate Detection Policy (samenvatting)

- Exact: begrip + context (organisatorisch/juridisch) exact gelijk (case‑insensitive) → duplicaat.
- Fuzzy: Jaccard‑similarity op woordsets van begrip met threshold ≥ 0.7.
- Statusfilter: definitions met status 'archived' worden uitgesloten.
- Risicobuckets: high (≥ 0.9), medium (≥ 0.8), low (anders).

Voorbeelden:
- Exact: ("Belasting", context="OM|Strafrecht") ↔ ("Belasting", context="OM|Strafrecht").
- Fuzzy medium: ("Inspectierapport" ↔ "Rapport inspectie") ≈ 0.8.
- Geen match: lege of totaal afwijkende begrippen.

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
