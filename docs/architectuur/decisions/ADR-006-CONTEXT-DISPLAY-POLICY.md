---
id: ADR-006
title: Contextweergavebeleid in UI (alleen vastgelegde context)
status: active
owner: architecture
canonical: true
applies_to: definitie-app@current
last_verified: 2025-09-13
---

# ADR-006: Contextweergavebeleid in UI (alleen vastgelegde context)

## Besluit
- De UI (Expert‑tab en Bewerk‑tab) toont uitsluitend de **vastgelegde context** die bij een definitie in de database is opgeslagen:
  - Organisatorische context (string)
  - Juridische context (string)
  - Wettelijke basis (lijst; JSON TEXT in DB)
- De **globale context** (ContextManager/Context Selector) wordt **niet getoond** en **niet als fallback** gebruikt in de contextweergave.
- Alle drie contextvelden worden **altijd** getoond. Als er niets is vastgelegd wordt dit expliciet weergegeven als **“—”**.

## Achtergrond
- De applicatie kent twee contextbronnen:
  1) Globale context (sessie) voor generatie/validatie/web‑lookup
  2) Vastgelegde context (per definitie) voor opslag, tonen, zoeken en audit
- Voor consistentie, transparantie en auditbaarheid willen we exact laten zien wat er bij een definitie is vastgelegd — zonder impliciete menging met sessie‑instellingen.

## Overwegingen
- Minimal invasive (AGENTS/CLAUDE): geen aanpassing van DB‑model of services noodzakelijk; dit is een UI‑presentatiekeuze.
- Voorkomt verwarring tussen tijdelijke sessiecontext en persistente definitiecontext.
- Maakt audit/geschiedenis eenduidig: wat je ziet, is wat er is opgeslagen.

## Consequenties
- Lege contextvelden blijven expliciet leeg (—) tot de gebruiker ze vastlegt in de Bewerk‑tab en opslaat (met logging/geschiedenis).
- Zoeken en statusflows werken op de vastgelegde context; de globale context heeft hier geen invloed op.
- “Vastgesteld” blijft read‑only; om context te wijzigen moet de status eerst bewust worden teruggezet (met logging).

## Uitvoering
- Expert‑tab: contextdetails tonen altijd Organisatorisch / Juridisch / Wettelijke basis op basis van het record; leeg = “—”.
- Bewerk‑tab: dezelfde drie velden; read‑only bij status “Vastgesteld”.
- Geen fallback/merge met globale context in de weergave.

