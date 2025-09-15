# Handover Document: Epic-010 Context Flow Analysis & Harmonisatie

## 📅 Datum: 2025-09-09 (Update: 2025-09-10)
## 👤 Analyst: Claude Code
## 🎯 Doel: Context flow harmonisatie en legacy domein veld verwijdering

## 📊 Status Epic-010: Context Flow Refactoring (2025-09-10)

### User Stories Status
- **US-041**: Fix Context Field Mapping to Prompts - **✅ GEREED**
- **US-042**: Fix "Anders..." Custom Context Option - **✅ GEREED**
- **US-043**: Remove Legacy Context Routes - **🟡 OPEN**
- **US-048**: Context Type Validation - **🟡 OPEN**
- **US-049**: Context Traceability for ASTRA - **🟡 OPEN**
- **US-050**: End-to-End Context Tests - **🟡 OPEN**

## 🔍 Analyse Resultaten

### Context Flow Tracing

#### 1. UI Context Collectie ✅
**Locatie:** `src/ui/tabbed_interface.py:638`
```python
from ui.components.enhanced_context_manager_selector import render_context_selector
return render_context_selector()
```
**Output:**
```python
{
    "organisatorische_context": [...],
    "juridische_context": [...],
    "wettelijke_basis": [...]
}
```

#### 2. Service Layer Ontvangst ⚠️ INCONSISTENTIE GEVONDEN
**Locatie:** `src/ui/tabbed_interface.py:799-805`
```python
service_result = self.definition_service.generate_definition_sync(
    begrip=begrip,
    context_dict={
        "organisatorisch": org_context,      # Gebruikt variabele
        "juridisch": jur_context,            # Gebruikt variabele
        "wettelijk": context_data.get("wettelijke_basis", [])  # Direct uit context_data!
    },
    organisatie=primary_org,
    categorie=auto_categorie,
)
```

**⚠️ PROBLEEM:** Inconsistente data handling:
- `org_context` en `jur_context` komen uit variabelen (mogelijk bewerkt)
- `wettelijke_basis` komt direct uit `context_data` (onbewerkt)

#### 3. Request Aanmaak ✅
**Locatie:** `src/services/service_factory.py:337-339`
```python
request = GenerationRequest(
    organisatorische_context=org_list,
    juridische_context=context_dict.get("juridisch", []),
    wettelijke_basis=context_dict.get("wettelijk", []),
)
```

#### 4. Context Enrichment ✅
**Locatie:** `src/services/definition_generator_context.py:258-260`
```python
extend_unique(getattr(request, "organisatorische_context", None), context["organisatorisch"])
extend_unique(getattr(request, "juridische_context", None), context["juridisch"])
extend_unique(getattr(request, "wettelijke_basis", None), context["wettelijk"])
```

#### 5. Prompt Building ✅
**Locatie:** `src/services/prompts/modules/definition_task_module.py:285-297`
```python
lines.append(f"- Organisatorische context: {', '.join(org_contexts)}")
lines.append(f"- Juridische context: {', '.join(jur_contexts)}")
lines.append(f"- Wettelijke basis: {', '.join(wet_basis)}")
```

## 🐛 Gevonden Issues

### 1. Inconsistente Context Verwerking
**Severiteit:** MEDIUM
**Locatie:** `src/ui/tabbed_interface.py:801-805`

De wettelijke basis wordt anders behandeld dan andere context velden:
- `organisatorisch` en `juridisch` gebruiken voorbewerkte variabelen
- `wettelijk` haalt direct uit raw `context_data`

Dit kan leiden tot:
- Missende transformaties voor wettelijke basis
- "Anders..." optie werkt mogelijk niet voor wettelijke basis
- Inconsistente data sanitization

### 2. Mogelijke Data Loss Points
**Severiteit:** LOW

Onderzoek waar `org_context` en `jur_context` vandaan komen:
- Worden deze getransformeerd?
- Is er filtering toegepast?
- Waarom geen `wet_context` variabele?

## ✅ Wat Werkt

1. **Context wordt WEL doorgegeven** van UI naar prompts
2. **"Anders..." optie** werkt nu zonder crashes (vandaag gefixt)
3. **Wetboek van Strafvordering** opties zijn hersteld (huidig/toekomstig)
4. **Alle drie context types** komen in de finale prompt

## 🔧 Aanbevolen Fixes

### Prioriteit 1: Consistente Context Handling
```python
# HUIDIGE CODE (inconsistent)
context_dict={
    "organisatorisch": org_context,
    "juridisch": jur_context,
    "wettelijk": context_data.get("wettelijke_basis", [])
}

# VOORGESTELDE FIX
wet_context = context_data.get("wettelijke_basis", [])
# Pas dezelfde transformaties toe als op org_context en jur_context
context_dict={
    "organisatorisch": org_context,
    "juridisch": jur_context,
    "wettelijk": wet_context
}
```

### Prioriteit 2: Onderzoek Context Transformaties
1. Trace waar `org_context` en `jur_context` worden aangemaakt
2. Identificeer welke transformaties worden toegepast
3. Pas dezelfde transformaties toe op `wettelijke_basis`

## 📋 Openstaande Taken Epic-010

### Moet Nog Gebeuren:
1. **US-043**: Legacy context routes verwijderen
2. **US-048**: Type validatie implementeren
3. **US-049**: ASTRA compliance audit trail
4. **US-050**: End-to-end tests schrijven

### Al Opgelost:
- ✅ Context wordt doorgegeven (US-041 deels)
- ✅ "Anders..." optie werkt (US-042)
- ✅ Wetboek opties hersteld

## 🎯 Conclusie

US-041 is afgerond: mapping is aanwezig in PromptServiceV2 en V2‑contracten; UI‑keys zijn geverifieerd. Inconsistente verwerking van wettelijke basis is verholpen in de huidige UI‑flow.

De context flow werkt technisch, maar heeft verbetering nodig in:
1. Consistente data handling
2. Legacy route cleanup
3. Proper testing
4. ASTRA compliance

---

## 🧭 Actieplan afronding EPIC‑010

### Uitgevoerde Wijzigingen

#### 1. **Legacy `domein` veld volledig verwijderd**
- ✅ `src/services/interfaces.py` - domein veld verwijderd uit GenerationRequest en Definition
- ✅ `src/services/prompts/prompt_service_v2.py` - domein mapping verwijderd
- ✅ `src/services/definition_generator_context.py` - domein context verwijderd
- ✅ `src/services/service_factory.py` - domein_text variabele volledig verwijderd
- ✅ `src/services/definition_orchestrator.py` - domein referenties verwijderd
- ✅ `src/services/orchestrators/definition_orchestrator_v2.py` - domein verwijderd
- ✅ `src/orchestration/definitie_agent.py` - domein mapping verwijderd

#### 2. **Context Harmonisatie in UI**
- ✅ `src/ui/tabbed_interface.py`:
  ```python
  # Consistente variabelen voor alle 3 types
  org_context = context_data.get("organisatorische_context", [])
  jur_context = context_data.get("juridische_context", [])
  wet_context = context_data.get("wettelijke_basis", [])  # NIEUW
  ```

#### 3. **Context Sharing Modules Updated**
- ✅ `src/services/prompts/modules/context_awareness_module.py`:
  - Verwijderd: `domain_contexts` sharing
  - Toegevoegd: `juridical_contexts` en `legal_basis_contexts` sharing
  - Nu worden alle 3 actieve context types gedeeld

- ✅ `src/services/prompts/modules/error_prevention_module.py`:
  - Updated om juridical_contexts en legal_basis_contexts te gebruiken
  - Domain context verboden vervangen door juridisch/wettelijk

#### 4. **Verificatie**
- ✅ Geen `domein_text` referenties meer in codebase
- ✅ Alle 3 context types worden consistent behandeld
- ✅ Geen direct gebruik van `context_data` meer, alleen variabelen

### Impact Analyse
- **Breaking Changes**: Ja - `domein` veld is niet meer beschikbaar
- **Backward Compatibility**: Behouden via juridische_context mapping
- **Performance**: Neutraal - geen impact op performance
- **Testing Required**: Unit tests voor context flow

### Nieuwe Context Flow
```
UI Input → 3 Context Types → Consistente Variabelen → Service Layer
   ↓              ↓                    ↓                     ↓
org_context  jur_context      wet_context           Alle modules
```

1) US‑043: Legacy context routes verwijderen (zie EPIC‑010 epic voor uitgewerkt plan)
2) US‑048: Type validatie afdwingen (alle context velden lijst van strings)
3) US‑049: ASTRA traceability uitbreiden (audit trail van context in metadata/logs)
4) US‑050: E2E context tests uitbreiden en stabiliseren

Status: EPIC‑010 is deels afgerond (US‑041/042 gereed); resterende stories staan open.
