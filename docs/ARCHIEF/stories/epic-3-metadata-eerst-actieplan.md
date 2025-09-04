---
canonical: true
status: active
owner: development
last_verified: 2025-09-04
applies_to: definitie-app@v2.3
document_type: actieplan
epic: epic-3-web-lookup
priority: critical
sprint: UAT-2025-09
---

# Epic 3: "Metadata Eerst, Prompt Daarna" - Compleet Actieplan

**Doel**: Implementeer de complete "metadata eerst, prompt daarna" flow waarbij bronnen eerst worden vastgelegd en zichtbaar gemaakt, en daarna pas gebruikt worden voor prompt verrijking.

**UAT Deadline**: 20 september 2025
**Totale Effort**: 6-8 dagen

---

## 📊 HUIDIGE STATUS OVERZICHT

### ✅ WAT IS AL GEÏMPLEMENTEERD (Story 3.1 - September 2025)

#### 1. Web Lookup Pre-step ✅
```python
# src/services/orchestrators/definition_orchestrator_v2.py:190-256
- Web lookup wordt uitgevoerd vóór prompt generatie
- build_provenance() doet ranking/dedup
- Top-K sources worden gemarkeerd met used_in_prompt=true
```

#### 2. Metadata Opslag ✅
```python
# src/services/orchestrators/definition_orchestrator_v2.py:443
"sources": provenance_sources  # Sources in metadata["sources"]
```

#### 3. UI Bronnen Weergave ✅
```python
# src/ui/components/definition_generator_tab.py:750-816
- _render_sources_section toont bronnen uit metadata
- Badges voor "Autoritatief" en "In prompt"
- Expandable UI met titel, URL, snippet
- Melding bij geen bronnen (regel 771-773)
```

#### 4. Provider-Neutraal in Prompt ✅
```python
# src/services/prompts/prompt_service_v2.py:288
label = f"Bron {added + 1}"  # Geen provider namen in prompt
```

#### 5. Juridische Metadata ✅
```python
# src/services/web_lookup/provenance.py
- ECLI extractie voor rechtspraak
- Artikel/wet parsing voor overheid.nl
- citation_text veld voor UI weergave
```

---

## ❌ KRITIEKE GAPS - Wat Ontbreekt

### 🔴 GAP 1: Context Flow Broken
**Probleem**: Alleen `organisatorische_context` komt in prompt, `juridische_context` en `wettelijke_basis` worden genegeerd

**Locatie**: `src/services/definition_generator_context.py:237-258`

**Fix Required**:
```python
# VOOR (alleen organisatorische):
context = {"organisatorische_context": self.organisatorische_context}

# NA (alle 3 velden):
context = {
    "organisatorische_context": self.organisatorische_context,
    "juridische_context": self.juridische_context,
    "wettelijke_basis": self.wettelijke_basis
}
```

### 🔴 GAP 2: Prompt Augmentatie uit Context, Niet uit Metadata
**Probleem**: Prompt gebruikt `context["web_lookup"]["sources"]` in plaats van `metadata["sources"]`

**Locatie**:
- Orchestrator zet sources in context (regel 245-248)
- Prompt service gebruikt context, niet metadata

**Fix Required**:
```python
# Prompt service moet sources uit metadata halen:
sources = agent_result.get("metadata", {}).get("sources", [])
# Filter op used_in_prompt=true
selected = [s for s in sources if s.get("used_in_prompt")]
```

### 🔴 GAP 3: Toetsregel → Prompt Mapping Ontbreekt
**Probleem**: Geen individuele prompt instructies per toetsregel

**Fix Required**: Nieuwe service voor regel-specifieke prompts
```yaml
# config/prompt-instructions/arai/ARAI-01.yaml
rule_id: ARAI-01
instruction: "Start NOOIT met een werkwoord"
context_variants:
  juridisch: "Juridische begrippen starten met substantief"
  dji: "Detentie-begrippen altijd als naamwoord"
```

### 🔴 GAP 4: Ontologie als Vraag i.p.v. Instructie
**Probleem**: Ontologie wordt als vraag gesteld, niet als instructie

**Fix Required**:
```python
# VAN:
"Wat is de ontologische categorie?"
# NAAR:
"INSTRUCTIE: Definieer als {categorie} - {specifieke richtlijnen}"
```

---

## 🎯 VOORGESTELDE USER STORIES

### Epic 3: Web Lookup Modernization - Stories

| Story ID | Titel | Priority | Effort | Status |
|----------|-------|----------|---------|--------|
| **WEB-3.1** | Sources Visibility in UI | ✅ DONE | - | Completed |
| **WEB-3.2** | Fix Context Flow (3 velden) | 🔥 P0 | 1 dag | Ready |
| **WEB-3.3** | Prompt uit Metadata | 🔥 P0 | 1 dag | Ready |
| **WEB-3.4** | Toetsregel Prompt Mapping | 📋 P1 | 2 dagen | Ready |
| **WEB-3.5** | Ontologie als Instructie | 📋 P1 | 1 dag | Ready |
| **WEB-3.6** | Export met Bronnen | 📋 P2 | 0.5 dag | Ready |

---

## 📋 GEDETAILLEERDE USER STORIES

### 🔥 Story WEB-3.2: Fix Context Flow (P0 - 1 dag)
**Als** gebruiker
**Wil ik** dat alle 3 contextvelden (organisatorisch, juridisch, wettelijk) worden meegenomen
**Zodat** de definitie alle relevante context gebruikt

**Acceptatiecriteria**:
- [ ] Alle 3 contextvelden komen in de prompt
- [ ] Context wordt correct gecombineerd
- [ ] Logging toont alle 3 velden
- [ ] Tests voor context flow

**Implementation**:
1. Fix `definition_generator_context.py:_build_base_context()`
2. Update prompt templates om alle context te gebruiken
3. Add integration test voor 3-velden flow
4. Verify in UI dat alle context zichtbaar is

---

### 🔥 Story WEB-3.3: Prompt uit Metadata (P0 - 1 dag)
**Als** developer
**Wil ik** dat prompt augmentatie uitsluitend metadata["sources"] gebruikt
**Zodat** er één single source of truth is voor bronnen

**Acceptatiecriteria**:
- [ ] Prompt service leest uit metadata["sources"]
- [ ] Alleen sources met used_in_prompt=true worden gebruikt
- [ ] Context["web_lookup"] wordt deprecated
- [ ] Provider-neutraal blijft behouden

**Implementation**:
1. Refactor `prompt_service_v2.py` augmentation
2. Pass metadata dict naar prompt service
3. Remove context["web_lookup"] dependency
4. Update tests voor nieuwe flow

---

### 📋 Story WEB-3.4: Toetsregel Prompt Mapping (P1 - 2 dagen)
**Als** beheerder
**Wil ik** per toetsregel de prompt instructies kunnen beheren
**Zodat** elke regel optimaal geconfigureerd is

**Acceptatiecriteria**:
- [ ] 45 YAML bestanden met prompt instructies
- [ ] RulePromptMappingService voor laden/beheren
- [ ] Context-aware variaties (juridisch/dji/default)
- [ ] Fallback naar default instructies

**Implementation**:
1. Create `config/prompt-instructions/{category}/{rule}.yaml` structure
2. Implement `RulePromptMappingService`
3. Integrate in prompt builder
4. Admin UI voor beheer (later)

---

### 📋 Story WEB-3.5: Ontologie als Instructie (P1 - 1 dag)
**Als** gebruiker
**Wil ik** dat ontologie als instructie wordt meegegeven
**Zodat** definities beter aansluiten bij de categorie

**Acceptatiecriteria**:
- [ ] Ontologie wordt als INSTRUCTIE geformuleerd
- [ ] Specifieke richtlijnen per categorie
- [ ] Geen vraagstelling meer in prompt
- [ ] Betere kwaliteit definities

**Implementation**:
1. Create ontology instruction templates
2. Update prompt builder logic
3. Test met verschillende categorieën
4. Measure quality improvement

---

### 📋 Story WEB-3.6: Export met Bronnen (P2 - 0.5 dag)
**Als** gebruiker
**Wil ik** bronnen in mijn exports zien
**Zodat** ik de herkomst kan verifiëren

**Acceptatiecriteria**:
- [ ] JSON export bevat sources array
- [ ] TXT export toont bronnen sectie
- [ ] PDF export (indien aanwezig) toont bronnen
- [ ] WCAG compliant formatting

---

## 📅 IMPLEMENTATIE PLANNING

### Week 1 (4-6 September): Critical Fixes
```
Dag 1: WEB-3.2 - Fix Context Flow (3 velden) ⚡
Dag 2: WEB-3.3 - Prompt uit Metadata ⚡
Dag 3: Testing & Integration
```

### Week 2 (9-13 September): Structurele Verbeteringen
```
Dag 4-5: WEB-3.4 - Toetsregel Prompt Mapping 🔧
Dag 6: WEB-3.5 - Ontologie als Instructie 📝
```

### Week 3 (16-20 September): Polish & UAT
```
Dag 7: WEB-3.6 - Export met Bronnen ✨
Dag 8-9: Integration testing
Dag 10: UAT preparation
```

---

## 🚀 QUICK WINS (< 1 dag)

1. **Context Flow Fix** - Direct 3 velden werkend (4 uur)
2. **Export Bronnen** - JSON/TXT export update (2 uur)
3. **Debug Logging** - Betere visibility (1 uur)
4. **UI Polish** - Loading states, error messages (3 uur)

---

## 📊 SUCCESS METRICS

### UAT Must-Have (20 september)
- [ ] Alle 3 contextvelden werkend
- [ ] Bronnen zichtbaar in UI (✅ Done)
- [ ] Prompt uit metadata sources
- [ ] Provider-neutraal (✅ Done)
- [ ] Export bevat bronnen

### Performance Targets
- Web lookup: < 2 seconden
- UI render: < 200ms
- Metadata opslag: 100% betrouwbaar
- Token gebruik: -50% reductie

### Kwaliteit Metrics
- Bronnen relevantie: > 0.7 score
- Juridische bronnen: > 50% bij juridische termen
- Gebruiker tevredenheid: > 4/5 sterren

---

## 🔧 TECHNISCHE DEPENDENCIES

### Services
- `DefinitionOrchestratorV2` - Hoofdcoördinator
- `ModernWebLookupService` - Web lookup executie
- `PromptServiceV2` - Prompt building
- `ValidationOrchestratorV2` - Validatie flow
- `ServiceFactory` - Result building

### Nieuwe Components
- `RulePromptMappingService` - Voor WEB-3.4
- `OntologyInstructionBuilder` - Voor WEB-3.5
- `ContextCombiner` - Voor WEB-3.2

### Config Files
- `config/web_lookup_defaults.yaml` - Bestaand
- `config/prompt-instructions/*.yaml` - Nieuw
- `config/ontology-instructions.yaml` - Nieuw

---

## 🎯 DEFINITION OF DONE

Een story is DONE wanneer:
1. Code is geïmplementeerd en getest
2. Unit tests hebben > 80% coverage
3. Integration test succesvol
4. Code review is uitgevoerd
5. Documentatie is bijgewerkt
6. Geen regressions in bestaande functies
7. Performance targets zijn gehaald
8. UI/UX is gevalideerd

---

## 📝 NOTES & RISKS

### Risks
1. **Context flow fix** kan andere componenten breken
2. **Toetsregel mapping** verhoogt complexiteit
3. **UAT deadline** is krap (2.5 weken)

### Mitigaties
1. Feature flags voor geleidelijke uitrol
2. Fallbacks naar huidige gedrag
3. Focus op P0 stories eerst
4. Daily standups voor progress tracking

### Open Vragen
1. Moeten alle 45 toetsregels direct mapping krijgen?
2. Is database migration echt nodig voor UAT?
3. Welke export formaten hebben prioriteit?

---

**Document Status**: Ready for Implementation
**Next Review**: 5 September 2025
**Owner**: Development Team
