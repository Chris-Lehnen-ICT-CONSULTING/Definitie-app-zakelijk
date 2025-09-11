---
id: CFR-BUG-014
epic: EPIC-010
titel: Synoniemen en Antoniemen Generatie Incorrect
prioriteit: HOOG
status: RESOLVED
aangemaakt: 2025-09-10
bijgewerkt: 2025-09-11
gevonden_in: v1.0.1
component: voorbeelden_service
---

# CFR-BUG-014: Synoniemen en Antoniemen Generatie Incorrect (OPGELOST)

## 🐛 Bug Beschrijving

De generatie van synoniemen en antoniemen werkt niet correct volgens de specificaties:
- **Synoniemen**: Genereert slechts 2 van de 5 vereiste items (met bullets)
- **Antoniemen**: Genereert 5 items maar slechts 1 heeft een bullet

### Verwacht Gedrag
- Synoniemen: 5 items zonder bullets
- Antoniemen: 5 items zonder bullets

### Actueel Gedrag
```
↔️ Synoniemen
• genootschap
• organisatie

↔️ Antoniemen
• scheiding
splitsing
verdeling
ontbinding
isolatie
```

## 📊 Impact Analyse

- **Gebruikersimpact**: HOOG - Juridische professionals vertrouwen op complete synoniemen/antoniemen
- **Business Impact**: MEDIUM - Verminderde kwaliteit van gegenereerde definities
- **Technisch Risico**: LAAG - Waarschijnlijk een prompt/parsing issue

## 🔍 Root Cause Analyse

### Mogelijke Oorzaken
1. **Prompt Module Issue**: De prompts voor synoniemen/antoniemen specificeren mogelijk niet correct het aantal
2. **Parser Issue**: De response parser handelt bullets/formatting niet correct
3. **Model Response**: GPT-4 geeft inconsistente formatting terug
4. **Cache Issue**: Oude gecachte responses met verkeerde formatting

### Te Onderzoeken
- [ ] Check `src/services/prompts/modules/synoniemen_module.py`
- [ ] Check `src/services/prompts/modules/antoniemen_module.py`
- [ ] Check `src/voorbeelden/voorbeelden_service.py` parsing logic
- [ ] Check `DEFAULT_EXAMPLE_COUNTS` configuratie
- [ ] Test met cache disabled

## 🛠️ Reproductie Stappen (historisch)

1. Start applicatie: `streamlit run src/main.py`
2. Vul begrip in: "verbinding"
3. Selecteer context (bijv. "Rechtspraak")
4. Genereer definitie
5. Observeer synoniemen/antoniemen sectie

## 🔧 Fix Strategie

### Fase 1: Diagnose
```python
# Test prompt modules direct
from services.prompts.modules.synoniemen_module import SynoniemenModule
module = SynoniemenModule()
prompt = module.build_prompt("verbinding", {})
print(prompt)  # Check of "EXACT 5" en "zonder bullets" er staat
```

### Fase 2: Fix Prompts
```python
# In synoniemen_module.py en antoniemen_module.py
SYNONIEMEN_PROMPT = """
Geef EXACT 5 synoniemen voor het begrip '{begrip}'.
- Alleen de woorden, zonder bullets of nummering
- Elk synoniem op een nieuwe regel
- PRECIES 5, niet meer en niet minder
"""
```

### Fase 3: Fix Parser
```python
# In voorbeelden_service.py
def _parse_synoniemen(self, response: str) -> list[str]:
    lines = response.strip().split('\n')
    # Remove bullets and clean
    cleaned = []
    for line in lines:
        line = line.strip()
        if line.startswith('•') or line.startswith('-'):
            line = line[1:].strip()
        if line:
            cleaned.append(line)
    return cleaned[:5]  # Ensure max 5
```

## ✅ Acceptance Criteria

- [ ] Synoniemen: Altijd exact 5 items
- [ ] Antoniemen: Altijd exact 5 items
- [ ] Geen bullets of andere formatting
- [ ] Consistent over meerdere runs
- [ ] Unit tests voor parser functies
- [ ] Integration test voor complete flow

## 📝 Test Cases

### Test Case 1: Basis Generatie
```python
def test_synoniemen_count():
    result = voorbeelden_service.genereer_synoniemen("verbinding")
    assert len(result) == 5
    assert all(not item.startswith('•') for item in result)
```

### Test Case 2: Edge Cases
```python
def test_synoniemen_with_rare_word():
    result = voorbeelden_service.genereer_synoniemen("xenofilie")
    assert len(result) <= 5  # May be less for rare words
```

## 🔗 Gerelateerde Issues

- [EPIC-010](../../EPIC-010-context-flow-refactoring.md): Context Flow Refactoring (parent epic)
- US-041: Fix Context Field Mapping (mogelijk gerelateerd)
- Previous synoniemen/antoniemen fixes in commit history

## 📌 Notes

- Dit probleem ontstond waarschijnlijk tijdens de EPIC-010 refactoring
- De DEFAULT_EXAMPLE_COUNTS config suggereert 5 items maar wordt mogelijk niet correct toegepast
- Debug logging in `DEBUG_EXAMPLES=true` mode kan helpen bij diagnose
