# Legacy Feature Implementation Plan

## 🎯 Doel
Implementeer alle kritieke functionaliteit uit `centrale_module_definitie_kwaliteit.py` in de nieuwe modulaire architectuur zonder functieverlies.

## 📊 Overzicht Ontbrekende Features

### Prioriteit 1: Kritieke Business Features (Week 1-2)

#### 1.1 **Metadata Velden** 
**Impact**: Incomplete definitie documentatie
**Implementatie**:
```python
# In src/ui/components/definition_generator_tab.py
# Voeg toe aan definitie generatie form:
datum_voorstel = st.date_input("Datum voorstel")
voorgesteld_door = st.text_input("Voorgesteld door")
ketenpartners = st.multiselect("Ketenpartners", ketenpartner_opties)

# Update SessionStateManager om deze velden op te slaan
# Update export functionaliteit om metadata mee te nemen
```

#### 1.2 **AI Content Generatie Features**
**Impact**: Verminderde definitiekwaliteit en bruikbaarheid
**Modules toe te voegen**:
- `src/generation/content_enrichment.py` - Voor alle AI content types
- `src/ui/components/content_generation_tab.py` - UI voor content generatie

**Content types**:
- Voorbeeldzinnen (3-5 contextrelevante voorbeelden)
- Praktijkvoorbeelden (real-world use cases)
- Tegenvoorbeelden (wat het NIET is)
- Toelichting (uitgebreide uitleg)
- Synoniemen/Antoniemen

#### 1.3 **Aangepaste Definitie Tab**
**Impact**: Geen mogelijkheid tot handmatige aanpassing
**Implementatie**:
```python
# Nieuw bestand: src/ui/components/custom_definition_tab.py
class CustomDefinitionTab:
    def render(self):
        # Toon gegenereerde definitie
        # Bewerkbare text area
        # Voorkeursterm selectie
        # Save met tracking van wijzigingen
```

### Prioriteit 2: Developer Tools (Week 3)

#### 2.1 **Verboden Woorden Management**
**Nieuwe module**: `src/ui/components/admin/forbidden_words_manager.py`
```python
class ForbiddenWordsManager:
    def display_current_words()
    def add_word()
    def remove_word()
    def test_sentence()
    def temporary_override()
```

#### 2.2 **Developer Controls**
**Toevoegen aan**: `src/ui/components/developer_tools_tab.py`
- Log detail niveau selector
- CSV log download
- Validation structure checker
- Debug mode toggle

### Prioriteit 3: UI/UX Features (Week 4)

#### 3.1 **AI Bronnen & Prompt Viewer**
**Uitbreiding van**: `definition_generator_tab.py`
- Toon gebruikte bronnen in expander
- Toon gegenereerde prompt in expander
- Copy-to-clipboard functionaliteit

## 🏗️ Implementatie Architectuur

### Directory Structure
```
src/
├── generation/
│   ├── content_enrichment.py      # NEW: AI content generation
│   └── prompt_variants.py         # NEW: Different prompt types
├── ui/
│   ├── components/
│   │   ├── custom_definition_tab.py    # NEW: Manual editing
│   │   ├── content_generation_tab.py   # NEW: AI content
│   │   ├── developer_tools_tab.py      # NEW: Dev tools
│   │   └── admin/
│   │       └── forbidden_words_manager.py  # NEW
│   └── tabbed_interface.py         # UPDATE: Add new tabs
├── services/
│   └── content_service.py          # NEW: Business logic
└── utils/
    └── legacy_compatibility.py     # NEW: Migration helpers
```

### Integration Points

#### 1. **SessionStateManager Updates**
```python
# Voeg toe aan session_state.py:
'datum_voorstel': None,
'voorgesteld_door': '',
'ketenpartners': [],
'generated_content': {
    'voorbeeldzinnen': [],
    'praktijkvoorbeelden': [],
    'tegenvoorbeelden': [],
    'toelichting': '',
    'synoniemen': [],
    'antoniemen': []
},
'show_developer_tools': False,
'debug_mode': False
```

#### 2. **Database Schema Updates**
```sql
-- Voeg columns toe aan definities tabel:
ALTER TABLE definities ADD COLUMN datum_voorstel DATE;
ALTER TABLE definities ADD COLUMN voorgesteld_door TEXT;
ALTER TABLE definities ADD COLUMN ketenpartners TEXT;
ALTER TABLE definities ADD COLUMN voorbeeldzinnen TEXT;
ALTER TABLE definities ADD COLUMN praktijkvoorbeelden TEXT;
-- etc.
```

## 📋 Implementatie Stappen

### Week 1: Foundation
1. ✅ Update SessionStateManager met alle legacy fields
2. ✅ Update database schema
3. ✅ Create base services voor content generation
4. ✅ Implementeer metadata velden in UI

### Week 2: AI Content
1. ✅ Implementeer content_enrichment.py
2. ✅ Create prompts voor elke content type
3. ✅ Integreer in generation workflow
4. ✅ Test kwaliteit output

### Week 3: Developer Tools
1. ✅ Forbidden words management UI
2. ✅ Developer controls tab
3. ✅ Logging enhancements
4. ✅ Debug functionaliteit

### Week 4: Polish & Testing
1. ✅ Custom definition editing
2. ✅ AI sources display
3. ✅ Prompt viewer
4. ✅ End-to-end testing
5. ✅ Performance optimalisatie

## ✅ Success Criteria

1. **Feature Parity**: Alle legacy features werken in nieuwe architectuur
2. **No Breaking Changes**: Bestaande functionaliteit blijft intact
3. **Performance**: Geen degradatie vs legacy versie
4. **Code Quality**: Modulair, testbaar, maintainable
5. **User Experience**: Intuïtieve UI zonder regressies

## 🚀 Quick Wins (Dag 1)

Deze kunnen vandaag nog geïmplementeerd worden:

1. **Metadata velden toevoegen**
   - Simpele UI fields in definition_generator_tab.py
   - SessionState update
   - Export integratie

2. **Prompt Viewer**
   - Expander met gegenereerde prompt
   - Copy button

3. **Developer Log Toggle**
   - Checkbox in sidebar
   - Conditional logging

## 📝 Notes

- Gebruik legacy code als referentie, niet copy-paste
- Volg nieuwe architectuur patterns
- Voeg unit tests toe voor elke nieuwe feature
- Documenteer in CLAUDE.md
- Update UI flow diagrams

De legacy module kan pas verwijderd worden als ALLE features zijn geïmplementeerd en getest!