Title: Consolidate GenerationResult contract and eliminate legacy paths/assumptions

Status: Open
Severity: High
Epic: EPIC-010 (Context Flow Refactoring)
Owners: Architecture, Services, UI

Beschrijving
- Er bestaan meerdere definities en aanroepen rondom `GenerationResult`:
  - `services.interfaces` definieert een (shim) `GenerationResult` voor compatibiliteit.
  - `orchestration.definitie_agent` definieert opnieuw een `GenerationResult` met `best_iteration` en
    `validation_result.overall_score` aannames (legacy patroon).
  - De UI/integratie gebruiken deels object‑achtige toegang (attribuut) en deels V2‑dicts, wat leidt tot fouten zoals
    `AttributeError: 'dict' object has no attribute 'overall_score'`.

Huidige impact
- Inconsistent resultaat‑model leidt tot UI‑crashes (zie CFR‑BUG‑007) en verhoogde complexiteit in adapters.
- Moeilijker debuggen en testen door twee (of meer) plekken met `GenerationResult` contracten.

Doel
- Eén canonische V2‑contract voor generatie‑resultaten en validatie‑details, beschikbaar via `services.interfaces`
  (of dedicated V2 dataclasses), en UI+services gebruiken uitsluitend dit contract.

Aanpakvoorstel
1) Canonicaliseren
   - Behoud `GenerationResult` (of nieuwe V2 dataclasses) enkel in `services.interfaces` als publiek contract.
   - Verwijder/deponeer duplicaatdefinitie in `orchestration.definitie_agent`; vervang door import uit `services.interfaces`.
2) UI‑adapter (fase 1)
   - Voeg een lichte adapter toe in de UI die zowel dict‑ als objectvorm aankan voor `validation_details`,
     maar zet deze direct om naar het V2 contract (dict of dataclass) voordat render‑code draait.
   - Verwijder gebruik van `best_iteration` en directe attribuut‑aanname (`.overall_score`) in UI; gebruik het contract.
3) Contract‑hardening (fase 2)
   - Introduceer typed dataclasses (bijv. `DefinitionResponseV2`, `ValidationDetails`, `Voorbeelden`) en zorg dat services
     altijd deze vormen teruggeven; converteer vlak vóór UI indien nodig naar dicts voor JSON‑friendly rendering.
4) Guardrails
   - Voeg grep‑gate toe die het oude importpad (`src/models/generation_result`) blokkeert in CI.
   - Voeg test die verzekert dat slechts één bron van `GenerationResult` aanwezig is en dat orchestrator niet zelf
     nog een klasse definieert.

Acceptatiecriteria
- Er is nog maar één `GenerationResult` contractbron (services.interfaces) of expliciete V2 dataclasses.
- UI toont geen AttributeErrors meer door attribuut‑vs‑dict verschillen; validatie en resultaten renderen consistent.
- Geen referenties meer naar `best_iteration` in UI‑flow; alle benodigde gegevens zijn beschikbaar via het contract.
- CI faalt als oude importpaden/duplicaatdefinities terugkeren (grep‑gate aanwezig).

Referenties
- CFR-BUG-007 (Validation AttributeError dict vs object)
- EPIC-010 context: ADR‑005 Unified State Management en V2 service‑architectuur
- Files: `src/services/interfaces.py`, `src/orchestration/definitie_agent.py`, `src/ui/components/definition_generator_tab.py`

