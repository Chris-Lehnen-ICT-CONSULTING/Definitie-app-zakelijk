---
id: EPIC-030
titel: "EPIC-030: Prompt & Definitiekwaliteit - Minder tokens, rijkere context en dubbele definities voorkomen"
status: active
prioriteit: HOOG
owner: product-development
applies_to: definitie-app@current
canonical: true
last_verified: 2025-10-14
stories:
  - US-143
  - US-195
  - US-015
  - US-227
doelstelling: "Optimaliseer promptopbouw en contextverwerking om betere definities te genereren met lagere kosten."
completion: 0%
target_release: v1.1
---


# EPIC-030: Prompt & Definitiekwaliteit

## Businesswaarde
- **Betere definities** door actuele context en duplicate-bewaking
- **Lagere kosten** dankzij tokenreductie en slimme caching
- **Snellere iteraties** door herbruikbare promptcomponenten

## Succesindicatoren
- Prompt tokens ≤ 3.000 bij standaardaanvraag
- 0 duplicaten bij genereren van dezelfde context
- Context uit geselecteerde documenten verschijnt in definitieprompt
- Bronnen en metadata kloppen in UI en logboek

## Scope (MVP)
1. Tokenoptimalisatie via deduplicatie, context filtering en caching (US-143)
2. Duplicate-gate in generatiepad met expliciete gebruikerskeuze (US-195)
3. Documentcontext doorgeven aan de service-laag en prompt (US-227)
4. Wikipedia verrijking als lichte externe bron met provenance (US-015)

## Buiten Scope
- Volledige multi-source orchestratie
- Enterprise prompts of multi-tenant workflows

## Afhankelijkheden
- Security Baseline voor sanitizing & logging (EPIC-006)
- Single-User Werkruimte voor UI-aanpassingen (EPIC-028)

