---
id: EPIC-019
titel: "EPIC-019: Prompt Compactie - 60-80% token reductie via dedup, Top-N regels en context normalisatie"
canonical: true
status: proposed
priority: HIGH
owner: architecture
applies_to: definitie-app@v2
last_verified: 2025-09-22
tags:
  - prompts
  - performance
  - token-efficiency
  - architecture
depends_on:
  - EPIC-010
  - EPIC-018
  - EPIC-002
  - EPIC-020
---

# EPIC-019 — Prompt Compact & Dedup (Token Efficiency)

Doel: 60–80% reductie van prompttokens zonder kwaliteitsverlies door systematische deduplicatie, compacte instructies en context‑/categorie‑afhankelijke selectie van regels en voorbeelden.

## Probleemschets
- Duplicatie tussen secties (BELANGRIJKE VEREISTEN vs. DEFINITIE KWALITEIT; dubbele bronsecties).
- Overmaat aan voorbeelden in Grammar/Templates/Toetsregels.
- Regels worden altijd volledig getoond i.p.v. relevantie‑gefilterd (Top‑N).
- Contextwaarden bevatten duplicaten of niet‑genormaliseerde input (bv. 'DJI' en '["DJI"]').
- Metrics/validatiematrix/metadata‑blokken in prompt i.p.v. UI.
- Web/doc‑snippets overschrijden budget; dubbele bronsecties bij augmentation.

## Scope
In scope:
- Promptinhoud en volgorde; compact‑mode/flags; filtering en budgetten.
- Module‑specifieke aanpassingen (Expertise/OutputSpec/Grammar/Context/ESS‑02/Templates/Regelmodules/ErrorPrevention/Metrics/DefinitionTask).
- Contextnormalisatie (PromptServiceV2/ContextManager).

Out of scope:
- Validatorlogica (ESS‑02 validatieregel valt onder EPIC‑002; hier alleen promptweergave).
- Nieuwe UI‑features (behalve flags/instellingen doorgegeven als config/ENV).

## KPI’s / DoD
- Tokenreductie ≥ 60% t.o.v. huidige voorbeeldprompt.
- Geen gedupliceerde secties of metadata in de prompt.
- Voorbeelden: standaard uit of max 1 per sectie (configureerbaar).
- Top‑N regels per categorie; N centraal instelbaar.
- Snippetbudgetten gehandhaafd; geen dubbele bronsecties.

## User Stories (prioriteit)
P0 (Hoog):
- US‑019‑01 Dedup basisvereisten vs. definitiekwaliteit
- US‑019‑02 Eén bronsectie (geen duplicatie)
- US‑019‑03 Voorbeelden beperken/globale switch
- US‑019‑04 Relevantie‑filtering (Top‑N) per regelssectie
- US‑019‑05 Context normalisatie/deduplicatie

P1 (Middel):
- US‑019‑06 ESS‑02 compact (met UI‑injectie)
- US‑019‑07 Metrics uit prompt (UI‑only)
- US‑019‑08 Metadata‑blok dedupliceren
- US‑019‑09 ErrorPrevention inkorten (top‑10, matrix UI‑only)
- US‑019‑10 Templates versimpelen (1 template + 2 patronen)
- US‑019‑11 Document‑snippets budget verlagen
- US‑019‑12 Web‑snippets budget verlagen en dedup met contextsectie

P2 (Laag):
- US‑019‑13 Modulevolgorde optimaliseren
- US‑019‑14 Centraliseer compact‑mode flags (ENV/Config)
- US‑019‑15 Token‑budget guards en max‑prompt‑length tuning

## Afhankelijkheden
- EPIC‑010 (V2/gates; contextvelden en ontologie doorgeven): hergebruiken (US‑041/US‑049/US‑179).
- EPIC‑018 (documentcontext/snippets): budgetten afstemmen (US‑229).
- EPIC‑002 (Validator V2; ESS‑02): consistentie met validatieregel (US‑191).
- EPIC‑020 (Phoenix): sluit aan op algemene token optimalisatie.

## Acceptatie
- Review door Product Owner + Architectuur (compactheid/helderheid).
- Testlogs tonen tokenreductie en sectie‑deduplicatie op 5 representatieve gevallen.

## Bijlagen
- Broncode referenties in US documenten.

