# Legacy Feature Implementatie - Prioriteitslijst

## 🎯 Doel
Herstel alle kritieke functionaliteit uit de legacy applicatie met hoogste prioriteit eerst, zodat de app minimaal even goed functioneert als voorheen.

## 🔴 PRIORITEIT 1: Kritieke Business Features (Direct implementeren)

### 1.1 **Metadata Velden** ⏱️ 2 uur ✅ VOLTOOID
**Waarom kritiek**: Zonder deze velden is er geen traceerbaarheid van definities
```python
# Toe te voegen aan definition_generator_tab.py:
datum_voorstel = st.date_input("Datum voorstel", value=datetime.today())
voorgesteld_door = st.text_input("Voorgesteld door")
ketenpartners = st.multiselect("Ketenpartners die akkoord zijn", 
                               options=["ZM", "DJI", "KMAR", "CJIB", "JUSTID"])
```
**Implementatie**:
- Update `SessionStateManager` met deze velden
- Voeg velden toe aan UI
- Update database schema
- Zorg dat export deze metadata meeneemt

### 1.2 **AI Content Generatie** ⏱️ 1 week
**Waarom kritiek**: Core functionaliteit - gebruikers verwachten rijke definities met voorbeelden
```python
# Nieuwe module: src/generation/content_enrichment.py
class ContentEnrichmentService:
    def generate_voorbeeldzinnen(begrip, context) -> List[str]
    def generate_praktijkvoorbeelden(begrip, context) -> List[str]
    def generate_tegenvoorbeelden(begrip, context) -> List[str]
    def generate_toelichting(begrip, context) -> str
    def generate_synoniemen(begrip, context) -> List[str]
    def generate_antoniemen(begrip, context) -> List[str]
```
**Implementatie**:
- Maak nieuwe service voor content generatie
- Integreer in definitie generatie workflow
- Voeg UI componenten toe voor weergave
- Test kwaliteit output

### 1.3 **Aangepaste Definitie Tab** ⏱️ 3 dagen
**Waarom kritiek**: Gebruikers moeten definities kunnen verfijnen
```python
# Nieuw: src/ui/components/custom_definition_tab.py
- Toon gegenereerde definitie
- Bewerkbare text area
- "Hercontroleer" knop voor re-testing
- Track wijzigingen
- Save met audit trail
```
**Implementatie**:
- Nieuwe tab component maken
- Integreer met AI toetser voor re-testing
- Update session state voor tracking changes

## 🟠 PRIORITEIT 2: Belangrijke Features (Week 2)

### 2.1 **Prompt Viewer & AI Bronnen** ⏱️ 4 uur
**Waarom belangrijk**: Transparantie over AI beslissingen
```python
# Uitbreiding definition_generator_tab.py:
with st.expander("📄 Bekijk gegenereerde prompt"):
    st.text_area("Prompt naar GPT", prompt_text, height=200)
    st.button("📋 Kopieer", on_click=copy_to_clipboard)

with st.expander("📚 AI Bronnen"):
    st.write(ai_sources)
```

### 2.2 **Voorkeursterm Selectie** ⏱️ 2 uur
**Waarom belangrijk**: Standaardisatie van terminologie
```python
# Na synoniemen generatie:
voorkeursterm = st.selectbox(
    "Selecteer voorkeursterm",
    options=[""] + [begrip] + synoniemen_lijst,
    format_func=lambda x: x if x else "— kies voorkeursterm —"
)
```

### 2.3 **Export met Volledige Context** ⏱️ 4 uur
**Waarom belangrijk**: Complete documentatie export
- Update TXT export om alle gegenereerde content mee te nemen
- Inclusief voorbeelden, synoniemen, metadata, etc.

## 🟡 PRIORITEIT 3: Developer Tools (Week 3)

### 3.1 **Developer Logging Toggle** ⏱️ 2 uur
```python
gebruik_logging = st.checkbox("🛠️ Log detailinformatie (ontwikkelaars)", value=False)
if gebruik_logging:
    # Toon gedetailleerde logs per toetsregel
```

### 3.2 **Verboden Woorden Management** ⏱️ 1 dag
**Nieuwe tab**: Developer Tools
- CRUD operaties voor verboden woorden
- Test interface
- Tijdelijke overrides

### 3.3 **CSV Log Download** ⏱️ 1 uur
```python
with open("log/definities_log.csv", "rb") as f:
    st.download_button("📥 Download CSV log", data=f, file_name="definities_log.csv")
```

## 🟢 PRIORITEIT 4: Nice-to-have (Week 4)

### 4.1 **Toetsregels Preview**
- Toon welke regels toegepast worden vóór generatie

### 4.2 **Ontologische Categorie Display**
- Direct tonen van bepaalde categorie in UI

### 4.3 **Validatie Structuur Testing**
- Tool om log integriteit te controleren

## 📊 Implementatie Volgorde

### Week 1: Foundation (MUST HAVE)
1. **Dag 1**: Metadata velden (2 uur) ✅
2. **Dag 2-3**: Start AI content generatie service
3. **Dag 4-5**: Complete content generatie + UI integratie

### Week 2: Core Features
1. **Dag 1-2**: Aangepaste definitie tab
2. **Dag 3**: Prompt viewer & AI bronnen
3. **Dag 4**: Voorkeursterm selectie
4. **Dag 5**: Export updates

### Week 3: Developer Experience
1. **Dag 1**: Developer logging
2. **Dag 2-3**: Verboden woorden management
3. **Dag 4**: Overige dev tools

### Week 4: Polish
1. Testing & bug fixes
2. Performance optimalisatie
3. Documentatie update

## ✅ Acceptatiecriteria

**De app is "net zo goed als voorheen" wanneer**:
1. ✅ Alle metadata velden aanwezig en werkend
2. ✅ AI genereert weer voorbeelden, toelichting, synoniemen
3. ✅ Gebruikers kunnen definities handmatig aanpassen
4. ✅ Export bevat alle gegenereerde content
5. ✅ Transparantie features (prompt, bronnen) aanwezig
6. ✅ Basis developer tools beschikbaar

## 🚀 Quick Start - Vandaag beginnen

**Stap 1**: Metadata velden (2 uur werk)
```python
# In definition_generator_tab.py, voeg toe na regel 20:
col1, col2, col3 = st.columns(3)
with col1:
    datum_voorstel = st.date_input("Datum voorstel", value=datetime.today())
with col2:
    voorgesteld_door = st.text_input("Voorgesteld door")
with col3:
    ketenpartners = st.multiselect("Ketenpartners", ["ZM", "DJI", "KMAR", "CJIB", "JUSTID"])

# Update session state
st.session_state['datum_voorstel'] = datum_voorstel
st.session_state['voorgesteld_door'] = voorgesteld_door
st.session_state['ketenpartners'] = ketenpartners
```

**Stap 2**: Begin met content enrichment service structuur
```python
# Maak src/generation/content_enrichment.py
# Start met de interface definitie
# Implementeer één generator tegelijk
```

Dit plan zorgt ervoor dat de app zo snel mogelijk weer volledig functioneel is!