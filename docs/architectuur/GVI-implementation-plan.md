# Generation-Validation Integration (GVI) Implementation Plan

**Versie**: 4.0
**Datum**: 2025-08-20
**Status**: Praktische implementatie gids - complementair aan Solution Architecture
**Referentie**: Zie [Solution Architecture Section 7.1](./SOLUTION_ARCHITECTURE.md#71-phased-migration-approach) voor high-level GVI strategie

---

## Executive Summary

Dit document bevat de **praktische implementatie details** voor het GVI quality improvement project. De high-level architectuur en strategie staan in de Solution Architecture.

**Kernprobleem**: Het systeem heeft alle benodigde componenten maar ze zijn niet correct verbonden - als een stereo installatie waar de kabels niet zijn aangesloten.

**Oplossing**: Fix 4 bestanden in plaats van nieuwe architectuur bouwen.

---

## 1. Root Cause Analyse - De "Kabel" Metafoor

### Het echte probleem: Disconnected Components 🔌

**Analogie**: Het is alsof je een high-end stereo installatie hebt waar:
- ✅ De versterker (HybridContext) werkt perfect
- ✅ De speakers (Validator) zijn uitstekend
- ✅ De equalizer (PromptBuilder) is top kwaliteit
- ❌ **Maar de kabels zijn niet aangesloten!**

We hoeven geen nieuwe stereo te kopen, alleen de kabels aansluiten.

### De "ontbrekende kabels" in code:

| Kabel | Component | Probleem | Impact |
|-------|-----------|----------|---------|
| 🔴 Rode kabel | Feedback loop | `feedback_history` parameter wordt GENEGEERD | Systeem leert niet van fouten |
| 🟡 Gele kabel | Context | Context wordt EXPLICIET genoemd: "Context: NP" | CON-01 regel violations |
| 🔵 Blauwe kabel | Preventie | Validatie alleen achteraf, niet preventief | Onnodig veel retries |

---

## 2. Concrete Code Fixes - De 4 Bestanden

### 2.1 Fix 1: Feedback Integration (Rode Kabel 🔴)

**File**: `services/definition_generator_prompts.py` (regel ~89)

```python
# HUIDIGE CODE - feedback_history wordt NIET gebruikt!
def build_prompt(self, request, context, rules, feedback_history=None):
    # feedback_history parameter wordt volledig genegeerd

# NIEUWE CODE - Gebruik feedback in prompt
def build_prompt(self, request, context, rules, feedback_history=None):
    prompt = self._base_prompt(request, context, rules)

    if feedback_history:
        prompt += "\n\n## Eerdere pogingen en feedback:\n"
        for attempt in feedback_history[-3:]:  # Laatste 3 pogingen
            prompt += f"\nPoging: {attempt['definition']}\n"
            prompt += f"Problemen: {attempt['violations']}\n"
            prompt += f"Verbeter: {attempt['suggestions']}\n"
        prompt += "\nVermijd deze fouten in de nieuwe definitie.\n"

    return prompt
```

### 2.2 Fix 2: Impliciete Context (Gele Kabel 🟡)

**File**: `prompt_builder/prompt_builder.py` (regel ~193)

```python
# HUIDIGE CODE - Zegt letterlijk "Organisatorische context: NP"!
if organisatorische_context:
    contextregels.append(
        f"- Organisatorische context: {', '.join(organisatorische_context)}"
    )

# NIEUWE CODE - Maak context IMPLICIET
def _make_context_implicit(self, contexts: List[str]) -> List[str]:
    """Vertaal expliciete context naar impliciete instructies"""
    implicit_map = {
        'NP': [
            "- Gebruik terminologie uit het strafrechtelijk domein",
            "- Focus op opsporings- en handhavingsaspecten",
            "- Gebruik termen zoals 'verdachte' in plaats van 'persoon'"
        ],
        'OM': [
            "- Focus op vervolgings- en beslissingsaspecten",
            "- Gebruik juridische beslisterminologie"
        ],
        'DJI': [
            "- Focus op detentie en re-integratie aspecten",
            "- Gebruik penitentiaire terminologie"
        ]
    }

    instructions = []
    for ctx in contexts:
        instructions.extend(implicit_map.get(ctx, []))
    instructions.append(f"- NIET expliciet vermelden: {', '.join(contexts)}")

    return instructions
```

### 2.3 Fix 3: Preventieve Validatie (Blauwe Kabel 🔵)

**File**: `services/unified_definition_generator.py` (regel ~156)

```python
def _build_preventive_constraints(self, validation_rules: List[Rule]) -> str:
    """Bouw constraints van validatie regels voor in de prompt"""
    # Belangrijkste regels omzetten naar positieve instructies
    rule_map = {
        'STR-01': "Begin de definitie met een zelfstandig naamwoord",
        'CON-01': "Vermeld GEEN organisatienamen of contexten expliciet",
        'VER-01': "Gebruik alleen enkelvoud, geen meervouden",
        'INT-03': "Gebruik geen vage verwijzingen zoals 'deze' of 'dit'",
        'ESS-01': "Beschrijf WAT iets is, niet waarvoor het gebruikt wordt"
    }

    constraints = []
    for rule in validation_rules:
        if rule.code in rule_map:
            constraints.append(rule_map[rule.code])

    return "\n".join(f"- {c}" for c in constraints)
```

---

## 3. Codebase Analyse - 65% Ongebruikte Microservices

### Statistieken
- **Totaal Python bestanden**: 222
- **Actief in gebruik**: 64 (35%)
- **Ongebruikt**: 119 (65%)
- **Reeds gebouwde microservices**: 5+

### Microservice-Ready Components (Ongebruikt)

| Component | Locatie | Status | Direct Deployable |
|-----------|---------|--------|-------------------|
| **Security Service** | `security/security_middleware.py` | 100% compleet | ✅ Ja |
| **A/B Testing** | `services/ab_testing_framework.py` | Volledig werkend | ✅ Ja |
| **Validation Engine** | `toetsregels/` (78 files!) | 45 rules compleet | ✅ Ja |
| **Config Service** | `config/config_manager.py` | Centralized config | ✅ Ja |
| **Async API Layer** | `utils/async_api.py` | FastAPI ready | ✅ Ja |

### Implicatie
> **65% van het werk voor microservices is al gedaan!** We hoeven alleen te activeren wat al bestaat.

---

## 4. Quick Wins Implementation Plan

### Week 1: De 4 Fixes (Direct Impact)
- **Dag 1-2**: Rode kabel - Feedback integration
- **Dag 3-4**: Gele kabel - Impliciete context
- **Dag 5**: Blauwe kabel - Preventieve constraints

**Verwacht resultaat**: 70%+ first-time-right

### Week 2: Activeer Bestaande Services
- **Dag 1-2**: Security middleware activeren
- **Dag 3-4**: Validation engine als service
- **Dag 5**: A/B testing framework

**Verwacht resultaat**: 85%+ first-time-right

### Week 3: Polish & Productie
- **Dag 1-2**: Performance tuning
- **Dag 3-4**: Edge cases
- **Dag 5**: Deployment

**Eindresultaat**: 90%+ first-time-right ✅

---

## 5. Business Case

| Aanpak | Effort | Tijd | Quality Gain | Risico |
|--------|--------|------|--------------|--------|
| **4 Fixes (dit plan)** | Klein | 3 weken | 60% → 90% | Laag |
| **Nieuwe architectuur** | Groot | 6+ weken | 60% → 95% | Hoog |
| **Niets doen** | Geen | 0 weken | 60% blijft | Zeer hoog |

**ROI**: Met 3 weken werk bereiken we 90% van het ideale resultaat.

---

## Appendix: Test Strategie

### Nieuwe Test Files
```
tests/test_generation_with_feedback.py    # Test rode kabel
tests/test_implicit_context.py           # Test gele kabel
tests/test_preventive_validation.py      # Test blauwe kabel
tests/test_gvi_integration.py           # Test complete flow
```

### Success Metrics
- First-time-right rate: 60% → 90%
- CON-01 compliance: 60% → 95%
- Response time: 8-12s → <5s
- API kosten: -50%

---

*Dit document focust op praktische implementatie. Voor architectuur details, zie [Solution Architecture](./SOLUTION_ARCHITECTURE.md).*
