---
canonical: true
status: active
owner: validation
last_verified: 2025-09-02
applies_to: definitie-app@v2
---

# Legacy Test Mapping → BUSINESS_RULES & Golden Dataset

Doel: legacy tests met afhankelijkheden op oude modules veilig verwijderen, zonder businesskennis te verliezen. Deze mapping legt per testbestand vast welke kennis wordt geborgd in BUSINESS_RULES.md en/of golden cases en welke V2‑tests de route valideren.

Bronnen:
- Businessregels: `docs/testing/BUSINESS_RULES.md`
- Config/weights: `src/config/validation_rules.yaml`
- Golden dataset: `tests/fixtures/golden_definitions.yaml`
- V2 smoke: `tests/smoke/test_validation_v2_smoke.py`

## Mapping Tabel

| Testbestand | Legacy‑import/reden | Geborgde kennis | Golden cases | V2 tests |
|-------------|----------------------|------------------|--------------|----------|
| tests/integration/test_performance_comparison.py | UnifiedDefinitionService/definition_generator | N.v.t. (infra/perf) | n/a | smoke V2 |
| tests/regression/test_complete_orchestrator.py | prompt_builder / oude orchestrator | Circulair/essentie/lengte → BUSINESS_RULES; route = V2 | voeg cases toe | smoke V2 + unit (determinisme) |
| tests/regression/test_modular_orchestrator.py | prompt_builder | Idem | voeg cases toe | smoke V2 |
| tests/regression/test_prompt_comparison.py | prompt_builder | Alleen promptstijl; geen extra businessregels | n/a | n/a |
| tests/test_new_services_integration.py | definition_generator | Acceptatie 0.75; drempels (LEN/ESS/CIRC) → BUSINESS_RULES | koppel cases | smoke V2 |
| tests/test_services_simple.py | definition_generator | Idem | koppel cases | smoke V2 |
| tests/unit/test_voorbeelden.py | generation.* | Niet‑leidend voor V2 validatie; voorbeelden los | n/a | n/a |
| tests/unit/test_voorbeelden_clean.py | generation.* | Idem | n/a | n/a |
| tests/unit/test_toets_ver_02.py | ai_toetser.core | Regelinhoud nu in BUSINESS_RULES/ YAML | koppel cases | unit (aggregatie) |
| tests/unit/test_toets_ver_03.py | ai_toetser.core | Idem | koppel cases | unit (aggregatie) |
| tests/services/test_service_factory.py | mixed legacy | Geen businessregels; route in V2 via factory | n/a | smoke V2 |
| tests/test_services_basic.py | definition_generator | Drempel/acceptatie → BUSINESS_RULES | koppel cases | smoke V2 |
| tests/test_ai_service_v2.py | oudere AI service | Niet relevant voor V2 validatie | n/a | n/a |

NB: “voeg cases toe / koppel cases” = expliciet linken naar één of meer golden case ID’s zodra deze gereed zijn.

## Richtlijnen voor verwijderen

Test verwijderen als:
- [x] BUSINESS_RULES.md bevat de relevante regel/drempel/edge‑case.
- [x] Golden case(s) bestaan met expected outcomes.
- [x] V2 smoke/unit de route dekt (shape/determinisme/acceptatie).

## Notities

- Tests met pure infra/performance (UnifiedDefinitionService, prompt_builder) bevatten geen nieuwe businessregels en kunnen direct weg.
- Tests die impliciet regels valideren (lengte/essentie/circulaire/structuur) worden geborgd in BUSINESS_RULES + golden dataset; daarna weg.
- Taalregels (“LANG‑…”) zijn optioneel/config‑afhankelijk; golden cases alleen van toepassing als deze geactiveerd worden in YAML.
