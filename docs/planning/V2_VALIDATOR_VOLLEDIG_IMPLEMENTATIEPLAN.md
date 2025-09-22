# V2 Validator Verbeterplan (JSON‑Centrisch) — Review Versie

## Management Samenvatting

Doel: V2‑validatie (ModularValidationService) inhoudelijk verbeteren met acceptatiegates, echte categorie‑scores en regelpariteit — zonder legacy .py‑regelmodules aan te roepen. Regels worden JSON‑leidend geëvalueerd, met kleine V2‑hooks waar nodig. UI blijft backwards‑compatibel.

Kernacties (op volgorde):
1) Acceptance gates + severity‑mapping
2) Echte category‑compliance berekenen
3) Pariteit port (JSON + V2‑hooks; additional_patterns centraal)
4) Violation‑metadata (optioneel/compatibel)
5) Pass‑uitleg voor JSON‑regels (UI‑heuristiek)
6) Micro‑performance tweaks
7) Legacy‑opschoning na pariteit

## Guiding Principles
- JSON‑leidend: regels via ToetsregelManager en generieke evaluator.
- Geen legacy calls: geen dynamische aanroep van `src/toetsregels/regels/*.py`.
- Compatibele UI: nieuwe velden zijn optioneel; bestaande rendering blijft werken.

## Fase 1 — Acceptance Gates + Severity (Dag 1)
- Gates: `critical==0` ∧ `overall≥T_overall` ∧ `category≥T_cat`; thresholds via config/policy.
- Severity: map JSON `aanbeveling/prioriteit` → critical/high/medium/low; toepassen als multipliers of gewichten.
- Output: `is_acceptable` blijft, `acceptance_gate` (optioneel) met verklaring.

## Fase 2 — Category‑Compliance (Dag 1–2)
- Mapping: ESS/VAL→juridisch; STR/INT→structuur; CON/SAM→samenhang; ARAI/VER→taal.
- Bereken gewogen gemiddelden per categorie uit rule_scores en gebruik in gates.

## Fase 3 — Pariteit Port (Dag 2–3)
- Additional patterns: centraal in `src/validation/additional_patterns.py` (uitgebreid waar nodig).
- V2‑hooks: kleine regel‑specifieke checks (zoals ESS‑02, SAM‑02, SAM‑04).
- Declaratief uitbreiden van JSON (required/forbidden patterns) voor ontbrekende signalen.
- Volgorde: ARAI → STR → CON/SAM → VER.

## Fase 4 — Violation‑Metadata (Dag 3)
- Optionele velden: `detected_pattern`, `position`, `type` (forbidden_pattern/…); `rule_name`.
- UI: geen wijziging vereist; velden zijn optioneel.

## Fase 5 — Pass‑Uitleg JSON (Dag 3)
- UI‑heuristiek uitbreiden: “waarom geslaagd” voor JSON‑regels o.b.v. drempels/afwezigheid patronen.

## Fase 6 — Micro‑performance (Dag 4)
- Early break bij harde fails; limiet op regex‑hits per regel; caching behouden.

## Fase 7 — Legacy‑Opschoning (na pariteit)
- Voorwaarden: goldens/gates groen; functionaliteit gedekt via JSON/V2‑hooks.
- Acties: verwijder legacy .py‑regelmodules en `validation/definitie_validator.py` (of markeer deprecated → remove); update tests/docs.

## Succescriteria & Verificatie
- Gates: deterministisch; severity consistent.
- Category‑scores: verschillen bij passende inputs en gebruikt in acceptatie.
- Pariteit: goldens per cluster (ARAI/STR/CON/SAM/VER) met JSON‑voorbeelden groen.
- UI: geen breuk; optionele metadata zichtbaar waar aanwezig.

## Risico’s & Mitigatie
- Score verschuift door multipliers → drempels config; tune‑pass op corpus.
- Regex vals‑positief → additional_patterns beperkt/traceerbaar; goldens per regel.
- Mapping‑fouten → centrale mapping + tests per prefix.

## Tijdlijn (indicatief)
- Dag 1: Gates + severity; tests.
- Dag 1–2: Category scoring; tests.
- Dag 2–3: Pariteit port (JSON + hooks) met goldens.
- Dag 3: Metadata/pass‑uitleg JSON; tests.
- Dag 4: Micro‑perf; docs bijwerken; voorbereiding legacy clean‑up.

## Deliverables
- Code: aanpassingen in `src/services/validation/modular_validation_service.py`, uitbreiding `src/validation/additional_patterns.py`, kleine UI‑heuristiek.
- Tests: goldens per cluster; unit voor gates/severity/category.
- Docs: bijgewerkt migratieplan/README/CLAUDE.

## Review Checklist
1) Sluit plan aan bij EPIC‑002 migratierichtlijn (geen legacy calls)?
2) Zijn gates en category‑scores concreet en testbaar beschreven?
3) Zijn pariteit‑stappen JSON‑centrisch en beheersbaar (patterns/hooks)?
4) Beperken we risico’s (opt. metadata, compatibele UI)?

## Beslissing
- [ ] Goedgekeurd — Start met Fase 1 (Gates + Severity)
- [ ] Aanpassingen nodig — Zie opmerkingen

Document status: Review — Datum: 2025‑09‑22 — Versie: 2.0
