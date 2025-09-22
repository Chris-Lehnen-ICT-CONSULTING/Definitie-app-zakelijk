# Implementatieplan: Auto-load Gegenereerde Definitie in Bewerk Tab

## Management Samenvatting
Wanneer een gebruiker een definitie genereert en daarna naar het "Bewerk" tabblad navigeert, moet de zojuist gegenereerde definitie automatisch geladen worden zonder handmatig zoeken.

## Huidige Situatie

### ✅ Wat werkt al:
1. **Edit tab heeft auto-load logica** (`definition_edit_tab.py` regel 54-66)
2. **SessionStateManager wordt correct gebruikt** overal in de code
3. **Tab navigatie werkt** via radio buttons
4. **Placeholder bug is al opgelost** (ik zie dat `_edit_definition` nu werkt)

### ❌ Wat ontbreekt:
1. **Session state keys niet gedefinieerd** in `DEFAULT_VALUES`
2. **Geen koppeling** tussen gegenereerde definitie ID en edit tab
3. **Geen auto-load trigger** bij tab switch

## Voorgestelde Oplossing

### Fase 1: Session State Keys Toevoegen (MINIMAAL - 2 minuten)

**Bestand:** `src/ui/session_state.py`
**Locatie:** In `DEFAULT_VALUES` dictionary (na regel 51)

```python
# External sources manager
"external_source_manager": None,
# Edit tab state variables - NIEUW
"editing_definition_id": None,      # ID van definitie om te bewerken
"editing_definition": None,          # Definitie object
"edit_session": None,               # Edit sessie metadata
"edit_search_results": None,        # Zoekresultaten
"last_auto_save": None,             # Auto-save timestamp
```

**Waarom:** Zonder deze keys krijgt de edit tab `None` terug en kan niet detecteren dat er een definitie moet worden geladen.

### Fase 2: Koppeling bij Generatie (ESSENTIEEL - 5 minuten)

**Bestand:** `src/ui/tabbed_interface.py`
**Locatie:** Na regel 947 (waar `last_generation_result` wordt gezet)

```python
# Store results voor display in tabs
SessionStateManager.set_value(
    "last_generation_result",
    { ... bestaande code ... }
)

# NIEUW: Koppel gegenereerde definitie aan edit tab
if saved_record and hasattr(saved_record, 'id'):
    SessionStateManager.set_value("editing_definition_id", saved_record.id)
    # Optional: Auto-navigate to edit tab
    # SessionStateManager.set_value("active_tab", "edit")
```

**Waarom:** Dit zorgt ervoor dat de edit tab weet welke definitie geladen moet worden.

### Fase 3: Verbeter Auto-load Detectie (OPTIONEEL - 10 minuten)

**Bestand:** `src/ui/components/definition_edit_tab.py`
**Locatie:** In `render()` method, voor regel 55

```python
def render(self):
    """Render de edit tab interface."""
    st.markdown("## ✏️ Definitie Editor")
    st.markdown("Bewerk definities met een rijke text editor...")

    # NIEUW: Check voor recent gegenereerde definitie
    last_result = SessionStateManager.get_value('last_generation_result')
    if last_result and last_result.get('saved_record'):
        saved_record = last_result['saved_record']
        if hasattr(saved_record, 'id'):
            current_edit_id = SessionStateManager.get_value('editing_definition_id')
            # Als er geen definitie geladen is, of het is een andere
            if not current_edit_id or current_edit_id != saved_record.id:
                SessionStateManager.set_value('editing_definition_id', saved_record.id)
                st.info(f"📝 Laatst gegenereerde definitie geladen (ID: {saved_record.id})")

    # Bestaande auto-start logica...
```

## Implementatie Volgorde

### Stap 1: Test Huidige Situatie
```bash
# Start applicatie
make dev

# Test:
1. Genereer een definitie
2. Klik op Bewerk tab
3. Observeer: Definitie wordt NIET automatisch geladen
```

### Stap 2: Implementeer Fase 1 (Session State Keys)
1. Open `src/ui/session_state.py`
2. Voeg de 5 nieuwe keys toe aan `DEFAULT_VALUES`
3. Herstart applicatie

### Stap 3: Test Fase 1
```bash
# Test of keys nu bestaan:
1. Genereer een definitie
2. Klik op Bewerk tab
3. Check developer tools voor errors (zouden weg moeten zijn)
```

### Stap 4: Implementeer Fase 2 (Koppeling)
1. Open `src/ui/tabbed_interface.py`
2. Voeg koppeling code toe na regel 947
3. Herstart applicatie

### Stap 5: Eindtest
```bash
# Complete flow test:
1. Genereer definitie voor "authenticatie"
2. Klik op Bewerk tab
3. Definitie moet automatisch geladen zijn!
```

## Risico's en Mitigaties

### Risico 1: Overschrijven bestaand werk
**Mitigatie:** Check of er al een `editing_definition_id` is voordat auto-load gebeurt

### Risico 2: Race conditions
**Mitigatie:** Gebruik consequent SessionStateManager, geen directe st.session_state

### Risico 3: Memory leaks
**Mitigatie:** Clear oude `last_generation_result` na succesvolle load

## Alternatieve Aanpakken

### Optie A: Query Parameters (Streamlit Native)
```python
# In generator tab:
st.query_params["edit_id"] = saved_record.id

# In edit tab:
if edit_id := st.query_params.get("edit_id"):
    load_definition(edit_id)
```
**Pro:** Bookmarkable URLs
**Con:** Meer complexiteit

### Optie B: Event System
```python
# Publisher-Subscriber pattern
SessionStateManager.publish_event("definition_generated", {
    "id": saved_record.id
})
```
**Pro:** Losjes gekoppeld
**Con:** Over-engineering voor dit probleem

## Aanbeveling

✅ **Implementeer Fase 1 + 2** (7 minuten werk)
- Lost het probleem direct op
- Minimale code wijzigingen
- Geen breaking changes
- Makkelijk te testen

⏸️ **Wacht met Fase 3**
- Eerst zien of Fase 1+2 voldoende is
- Fase 3 kan altijd later toegevoegd worden

## Test Checklist

- [ ] Genereer definitie → Bewerk tab → Auto-load werkt
- [ ] Bestaande edit sessie wordt niet overschreven
- [ ] Handmatige zoeken werkt nog steeds
- [ ] Geen errors in console
- [ ] Performance blijft goed

## Code Review Vragen

1. Zijn de session state key namen duidelijk?
2. Is de koppeling logica op de juiste plek?
3. Moeten we auto-navigatie toevoegen of niet?
4. Zijn er edge cases die we missen?

---
*Document aangemaakt: 2025-09-22*
*Geschatte implementatietijd: 7-17 minuten*
*Risico niveau: LAAG*