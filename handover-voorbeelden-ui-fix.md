# Handover Document: Voorbeelden UI Display Fix

## 🔴 CRITICAL ISSUE
**De daadwerkelijke voorbeelden/tegenvoorbeelden worden NIET getoond in de UI - alleen de prompts zijn zichtbaar!**

## Context & Achtergrond

### Wat is er gedaan (Phases 1-2 Completed)
1. **V2 Canonical Dict-Only Contract Geïmplementeerd**
   - TypedDicts toegevoegd in `src/services/interfaces.py`
   - Normalisatie functies in `src/services/service_factory.py`
   - Verwijderd: best_iteration, is_valid mapping
   - Tests aangepast en passing

2. **Metadata Fix in V2 Orchestrator**
   - `src/services/orchestrators/definition_orchestrator_v2.py` (lines 447-451)
   - Voorbeelden worden nu toegevoegd aan generation_metadata
   - Prompt text wordt correct opgeslagen

3. **UI Label Fixes**
   - English keys behouden (sentence, practical, counter)
   - Nederlandse labels in UI ("Toelichting" i.p.v. "Explanation")

### Huidige Situatie
✅ Prompts worden correct gegenereerd en getoond
✅ Definitie wordt gegenereerd 
✅ Metadata bevat voorbeelden dictionary
❌ **PROBLEEM: Daadwerkelijke voorbeelden content wordt NIET getoond in UI**

## Probleem Analyse

### Symptomen
1. In debug sectie zie je de prompts voor:
   - 📄 Voorbeeldzinnen
   - 💼 Praktijkvoorbeelden  
   - ❌ Tegenvoorbeelden
   - 🔄 Synoniemen
   - ↔️ Antoniemen
   - 💡 Toelichting

2. MAAR: De gegenereerde content zelf (de voorbeelden) verschijnt nergens

### Vermoedelijke Oorzaak
De voorbeelden worden WEL gegenereerd (API calls naar GPT gebeuren), maar:
- Ofwel: Ze worden niet correct doorgegeven van orchestrator → UI
- Ofwel: Ze worden niet correct gerenderd in de UI componenten

## Waar te Zoeken

### 1. Check Definition Generator Tab
```bash
# Hoofdcomponent voor definitie generatie UI
src/ui/components/definition_generator_tab.py
```
- Kijk naar `_handle_voorbeelden_generation()` 
- Check hoe voorbeelden uit response worden gehaald
- Verifieer SessionStateManager.set_value() calls

### 2. Check Voorbeelden Display Component
```bash
# Component dat voorbeelden moet tonen
src/ui/components/voorbeelden_display.py
```
- Check render() methode
- Verifieer of het data uit session state haalt
- Kijk of het correct voorbeelden dict parsed

### 3. Trace Data Flow
```python
# In definition_orchestrator_v2.py
voorbeelden = await self._generate_voorbeelden(...)  # Line ~380
# Check: Bevat 'voorbeelden' de juiste data?

# Dan in generation_metadata
"voorbeelden": voorbeelden if voorbeelden else {},  # Line 449
# Check: Wordt dit correct doorgegeven?

# In service_factory.py to_ui_response()
"voorbeelden": generation_metadata.get("voorbeelden", {})
# Check: Komt het hier aan?

# In definition_generator_tab.py
voorbeelden = response.get("voorbeelden", {})
# Check: Wordt het correct uit response gehaald?

# SessionStateManager
SessionStateManager.set_value("voorbeelden", voorbeelden)
# Check: Wordt het in session state gezet?
```

### 4. Debug Tips
```python
# Voeg logging toe op kritieke punten:
import logging
logger = logging.getLogger(__name__)

# In orchestrator na voorbeelden generatie:
logger.info(f"Generated voorbeelden: {voorbeelden}")

# In UI component:
logger.info(f"Received voorbeelden: {voorbeelden}")
st.write("DEBUG voorbeelden:", voorbeelden)  # Tijdelijk voor debugging
```

## Test Scenario

1. Start app: `OPENAI_API_KEY="$OPENAI_API_KEY_PROD" streamlit run src/main.py`
2. Vul begrip in: "test"
3. Genereer definitie
4. Check:
   - Worden API calls gemaakt? (check logs)
   - Staat voorbeelden data in session state? 
   - Wordt VoorbeeldenDisplay.render() aangeroepen?

## Verwachte Fix

Het probleem zit waarschijnlijk in een van deze gebieden:

1. **VoorbeeldenDisplay component rendert niet correct**
   - Mogelijk kijkt het naar verkeerde session state keys
   - Of parsed het de voorbeelden dict niet goed

2. **Session state wordt niet correct gevuld**
   - Check of voorbeelden dict de juiste structuur heeft
   - Verifieer dat keys matchen (sentence/practical/counter)

3. **UI tabs/sections missen render call**
   - Mogelijk wordt VoorbeeldenDisplay.render() niet aangeroepen
   - Of wordt het overschreven door andere UI updates

## Belangrijke Files

```bash
# Core files voor dit probleem:
src/ui/components/definition_generator_tab.py  # Hoofdcomponent
src/ui/components/voorbeelden_display.py       # Voorbeelden rendering
src/services/orchestrators/definition_orchestrator_v2.py  # Data generatie
src/services/service_factory.py                # Response formatting
src/voorbeelden/unified_voorbeelden.py         # Voorbeelden generator

# Session state management:
src/ui/session_state_manager.py
```

## Commando's voor Debugging

```bash
# Start app met debug logging
OPENAI_API_KEY="$OPENAI_API_KEY_PROD" PYTHONPATH=. streamlit run src/main.py --logger.level=debug

# Grep voor voorbeelden handling
grep -r "voorbeelden" src/ui/components/ --include="*.py"
grep -r "SessionStateManager.get_value.*voorbeelden" src/

# Check voor render calls
grep -r "VoorbeeldenDisplay" src/ui/
```

## Next Steps

1. **PRIORITEIT 1**: Find waar voorbeelden content verloren gaat
2. Check of UnifiedExamplesGenerator daadwerkelijk content returnt
3. Verifieer complete data flow van generator → orchestrator → UI
4. Fix rendering in VoorbeeldenDisplay component

## Laatste Status

- Gebruiker meldt: "dit zijn dus alleen de prompts! de daadwerkelijke voorbeelden etc. zijn nog steeds niet in de UI zichtbaar"
- Labels zijn correct (behalve Explanation → Toelichting, nu gefixed)
- Prompts worden getoond in debug sectie
- Definitie wordt wel gegenereerd en getoond
- **PROBLEEM: Voorbeelden content mist volledig**

## Git Status
```
Branch: main
Modified: 
- data/definities.db
- docs/backlog/bugs/CFR-BUG-003-generation-result-import.md
```

Recent commits show V2 contract implementation and various bug fixes.

---

**Start hier met debuggen van het voorbeelden display probleem!**