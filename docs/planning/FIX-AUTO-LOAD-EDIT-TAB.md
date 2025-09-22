# Fix: Auto-load Gegenereerde Definitie in Bewerk Tab

## Probleem Beschrijving
Wanneer een gebruiker een definitie genereert in het "Definitie Generatie" tabblad en vervolgens naar het "Bewerk" tabblad navigeert, wordt de zojuist gegenereerde definitie niet automatisch geladen. De gebruiker moet eerst handmatig zoeken naar de definitie.

## Root Cause Analyse

### Hoofdprobleem (CRITICAL BUG)
De `_edit_definition()` methode in `definition_generator_tab.py` (regel 1305-1307) is een **placeholder implementatie** die alleen "Edit functionality coming soon..." toont in plaats van daadwerkelijk naar de edit tab te navigeren.

### Bijkomende Problemen
1. **Missing Link**: Er wordt geen `editing_definition_id` gezet voor nieuw gegenereerde definities
2. **Session State Gap**: `saved_record.id` uit `last_generation_result` wordt niet gebruikt door de Edit tab
3. **Tab Switch Detection**: Geen automatische detectie wanneer gebruiker direct op Bewerk tab klikt

## Oplossing Strategie

### Fase 1: Quick Fix (Minimale wijziging - URGENT)
**Doel**: Herstel de basis functionaliteit van de "Bewerk" knop

#### Stap 1: Fix de placeholder methode
**Bestand**: `src/ui/components/definition_generator_tab.py`
**Regel**: 1305-1307
```python
# OUDE CODE (BUG):
def _edit_definition(self, definitie: DefinitieRecord):
    """Bewerk gegenereerde definitie."""
    st.info("🔄 Edit functionality coming soon...")

# NIEUWE CODE:
def _edit_definition(self, definitie: DefinitieRecord):
    """Bewerk gegenereerde definitie."""
    SessionStateManager.set_value("editing_definition_id", definitie.id)
    st.session_state["active_tab"] = "edit"
    st.success("✏️ Bewerk-tab geopend — laden van definitie…")
    st.rerun()
```

### Fase 2: Auto-load bij Tab Switch
**Doel**: Automatisch laden van laatst gegenereerde definitie bij navigatie naar Bewerk tab

#### Stap 2: Sla generated ID op
**Bestand**: `src/ui/tabbed_interface.py`
**Na regel**: 947
```python
# Voeg toe na het opslaan van last_generation_result:
if saved_record and hasattr(saved_record, 'id'):
    SessionStateManager.set_value("last_generated_definition_id", saved_record.id)
    SessionStateManager.set_value("auto_load_in_edit", True)
```

#### Stap 3: Auto-load in Edit Tab
**Bestand**: `src/ui/components/definition_edit_tab.py`
**Voor regel**: 55 (in render() method)
```python
# Auto-load laatst gegenereerde definitie indien beschikbaar
if SessionStateManager.get_value('auto_load_in_edit', False):
    last_gen_id = SessionStateManager.get_value('last_generated_definition_id')
    if last_gen_id and not SessionStateManager.get_value('editing_definition_id'):
        SessionStateManager.set_value('editing_definition_id', last_gen_id)
        SessionStateManager.set_value('auto_load_in_edit', False)  # Reset flag
```

#### Stap 4: Update Session State Defaults
**Bestand**: `src/ui/session_state.py`
**In DEFAULT_VALUES dict toevoegen**:
```python
"last_generated_definition_id": None,
"auto_load_in_edit": False,
```

### Fase 3: Verbeteringen (Optional)

#### Consolidatie van Edit Navigation
Maak één centrale methode voor navigatie naar edit tab:
```python
def _navigate_to_edit_tab(self, definition_or_id):
    """Centrale methode voor navigatie naar edit tab."""
    definition_id = definition_or_id.id if hasattr(definition_or_id, 'id') else definition_or_id
    SessionStateManager.set_value("editing_definition_id", definition_id)
    st.session_state["active_tab"] = "edit"
    st.success("✏️ Bewerk-tab geopend — laden van definitie…")
    st.rerun()
```

## Edge Cases & Mitigatie

### Edge Case 1: Gebruiker bewerkt al een definitie
**Probleem**: Auto-load zou huidige werk overschrijven
**Oplossing**: Check of `editing_definition_id` al gezet is voordat auto-load wordt uitgevoerd

### Edge Case 2: Database ID bestaat niet meer
**Probleem**: Definitie verwijderd tussen generatie en tab switch
**Oplossing**: Try-catch rond het laden met gebruikersvriendelijke foutmelding

### Edge Case 3: Meerdere generaties achter elkaar
**Probleem**: Alleen laatste definitie wordt onthouden
**Oplossing**: Dit is acceptabel gedrag - laatste generatie heeft prioriteit

## Test Plan

### Unit Tests
1. Test dat `_edit_definition()` correct de session state zet
2. Test dat auto-load flag correct wordt gezet/gereset
3. Test edge cases met missing IDs

### Manual Test Scenarios
1. **Happy Path**: Genereer definitie → Klik "Bewerk" knop → Verify definitie laadt
2. **Auto-load**: Genereer definitie → Klik direct op Bewerk tab → Verify auto-load
3. **Existing Edit**: Start edit → Genereer nieuwe → Check geen overwrite
4. **Error Case**: Genereer → Verwijder uit DB → Navigeer → Check error handling

## Implementatie Volgorde

### Prioriteit 1 (URGENT - Direct implementeren)
1. Fix de `_edit_definition()` placeholder bug (Stap 1)
2. Test dat "Bewerk" knop weer werkt

### Prioriteit 2 (Gebruikerservaring verbetering)
3. Implementeer auto-load mechanisme (Stap 2-4)
4. Test complete flow

### Prioriteit 3 (Code kwaliteit)
5. Consolideer navigation methods
6. Voeg comprehensive logging toe

## Rollback Plan
Als de fix problemen veroorzaakt:
1. Revert alleen de auto-load functionaliteit (Stap 2-4)
2. Behoud de fix voor de "Bewerk" knop (Stap 1) - dit is een kritieke bug fix

## Geschatte Impact
- **Gebruikers**: ~100% verbetering in workflow efficiency
- **Code Complexiteit**: Minimaal - alleen session state management
- **Risico**: Laag - geen database of backend wijzigingen

## Approval Required
- [ ] Code Review door senior developer
- [ ] Test door QA team
- [ ] Sign-off door Product Owner

---
*Document aangemaakt: 2025-09-22*
*Status: READY FOR IMPLEMENTATION*