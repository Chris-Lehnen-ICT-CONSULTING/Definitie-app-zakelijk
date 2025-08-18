# Epic 4: Content Enrichment Service

**Epic Goal**: Voeg synoniemen, antoniemen en voorbeelden toe aan definities.

**Business Value**: Lever rijkere, meer educatieve definities aan gebruikers.

**Total Story Points**: 11

**Target Sprint**: 2-3

## Background

Gebruikers willen meer dan alleen een definitie. Ze willen context, voorbeelden en gerelateerde termen om begrippen echt te begrijpen.

## Stories

### STORY-004-01: Implementeer Synonym Service

**Story Points**: 3

**Als een** gebruiker  
**wil ik** synoniemen zien bij definities  
**zodat** ik alternatieven ken.

#### Acceptance Criteria
- [ ] 3-5 synoniemen per definitie
- [ ] Context-aware selectie
- [ ] Nederlandse taal support
- [ ] Fallback bij geen synoniemen

#### Technical Design
```python
class SynonymService:
    """Generate context-aware synonyms for terms."""
    
    async def generate_synonyms(
        self, 
        term: str, 
        context: str,
        definition: str
    ) -> List[str]:
        prompt = f"""
        Geef 3-5 synoniemen voor '{term}' in {context} context.
        
        Definitie: {definition}
        
        Regels:
        - Alleen Nederlandse woorden
        - Context-appropriate
        - Verschillende nuances
        - Geen herhaling van het woord zelf
        
        Format: komma-gescheiden lijst
        """
        
        response = await self.ai_client.complete(prompt)
        return self._parse_synonyms(response)
    
    def _parse_synonyms(self, response: str) -> List[str]:
        # Clean and validate synonyms
        synonyms = [s.strip() for s in response.split(',')]
        return [s for s in synonyms if self._is_valid(s)][:5]
```

#### Examples
- "aansprakelijkheid" → verantwoordelijkheid, liability, schuld
- "gemeente" → stad, municipaliteit, lokaal bestuur
- "verordening" → regeling, voorschrift, besluit

---

### STORY-004-02: Implementeer Antonym Service

**Story Points**: 3

**Als een** gebruiker  
**wil ik** antoniemen zien waar relevant  
**zodat** ik tegenstellingen begrijp.

#### Acceptance Criteria
- [ ] Antoniemen alleen waar zinvol
- [ ] Duidelijke UI indicatie
- [ ] Skip voor abstracte begrippen
- [ ] Quality check op relevantie

#### Implementation Logic
```python
class AntonymService:
    """Generate antonyms where meaningful."""
    
    # Terms that typically have antonyms
    ANTONYM_CATEGORIES = {
        'binary': ['schuldig', 'onschuldig', 'geldig', 'ongeldig'],
        'gradual': ['zwaar', 'licht', 'streng', 'mild'],
        'directional': ['koper', 'verkoper', 'eiser', 'verweerder']
    }
    
    async def generate_antonyms(
        self, 
        term: str,
        definition: str
    ) -> Optional[List[str]]:
        # First check if antonyms make sense
        if not self._has_meaningful_opposite(term, definition):
            return None
            
        prompt = f"""
        Geef antoniemen voor '{term}' als die bestaan.
        
        Definitie: {definition}
        
        Return NULL als geen zinvolle tegenstelling bestaat.
        Anders: komma-gescheiden lijst (max 3)
        """
        
        response = await self.ai_client.complete(prompt)
        return self._parse_antonyms(response)
```

#### Skip Logic
- Abstract begrippen (democratie, filosofie)
- Processen (procedure, methodologie)
- Neutrale termen (document, systeem)

---

### STORY-004-03: Genereer Voorbeeldzinnen

**Story Points**: 3

**Als een** gebruiker  
**wil ik** voorbeeldzinnen zien  
**zodat** ik het gebruik begrijp.

#### Acceptance Criteria
- [ ] 3-5 voorbeeldzinnen per definitie
- [ ] Verschillende contexten gedekt
- [ ] Grammaticaal correct Nederlands
- [ ] Relevantie voor doelgroep

#### Example Generation
```python
class ExampleService:
    """Generate contextual example sentences."""
    
    async def generate_examples(
        self,
        term: str,
        definition: str,
        context: str
    ) -> List[str]:
        contexts = self._get_contexts(context)
        
        prompt = f"""
        Genereer 5 voorbeeldzinnen voor '{term}'.
        
        Definitie: {definition}
        
        Contexten te gebruiken:
        {json.dumps(contexts, ensure_ascii=False)}
        
        Regels:
        - Realistische scenarios
        - Verschillende gebruikssituaties
        - Helder en begrijpelijk
        - 15-25 woorden per zin
        """
        
        response = await self.ai_client.complete(prompt)
        return self._parse_examples(response)
    
    def _get_contexts(self, base_context: str) -> List[str]:
        """Get varied contexts for examples."""
        context_map = {
            'juridisch': ['rechtszaak', 'contract', 'wet', 'procedure'],
            'algemeen': ['dagelijks', 'zakelijk', 'informeel', 'formeel'],
            'technisch': ['specificatie', 'implementatie', 'documentatie']
        }
        return context_map.get(base_context, ['algemeen'])
```

#### Quality Criteria
- Natuurlijk taalgebruik
- Relevante situaties
- Educatieve waarde
- Geen jargon overload

---

### STORY-004-04: UI Integratie Enrichments

**Story Points**: 2

**Als een** gebruiker  
**wil ik** enrichments overzichtelijk zien  
**zodat** de interface niet cluttered wordt.

#### Acceptance Criteria
- [ ] Expandable/collapsible secties
- [ ] Duidelijke labels per enrichment type
- [ ] Optie om enrichments te verbergen
- [ ] Export inclusief enrichments

#### UI Components
```python
def render_enriched_definition(definition: EnrichedDefinition):
    """Display definition with all enrichments."""
    
    # Main definition always visible
    st.markdown(f"### {definition.term}")
    st.write(definition.definition)
    
    # Enrichments in tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📝 Basis", 
        "🔄 Synoniemen",
        "↔️ Antoniemen",
        "💡 Voorbeelden"
    ])
    
    with tab1:
        display_metadata(definition)
    
    with tab2:
        if definition.synonyms:
            st.write("**Synoniemen:**")
            for syn in definition.synonyms:
                st.write(f"• {syn}")
        else:
            st.info("Geen synoniemen beschikbaar")
    
    with tab3:
        if definition.antonyms:
            st.write("**Antoniemen:**")
            for ant in definition.antonyms:
                st.write(f"• {ant}")
        else:
            st.info("Geen antoniemen van toepassing")
    
    with tab4:
        if definition.examples:
            st.write("**Voorbeeldzinnen:**")
            for i, ex in enumerate(definition.examples, 1):
                st.write(f"{i}. {ex}")
```

#### Export Format
```json
{
  "term": "aansprakelijkheid",
  "definition": "...",
  "enrichments": {
    "synonyms": ["verantwoordelijkheid", "liability"],
    "antonyms": ["onschuld", "vrijwaring"],
    "examples": [
      "De aansprakelijkheid voor de schade ligt bij de veroorzaker.",
      "..."
    ]
  }
}
```

## Definition of Done (Epic Level)

- [ ] Alle enrichment services werkend
- [ ] UI integratie smooth
- [ ] Performance <2 sec per enrichment
- [ ] Export functionaliteit compleet
- [ ] User feedback verzameld
- [ ] A/B test results positief

## Architecture

```
DefinitionService
    ├── generate_definition()
    └── enrich_definition()
         ├── SynonymService
         ├── AntonymService
         └── ExampleService
```

## Performance Considerations

- Parallel enrichment generation
- Caching van enrichments
- Optional enrichments (user toggle)
- Progressive loading UI

## Success Metrics

- 85% definities hebben synoniemen
- 40% definities hebben antoniemen
- 95% definities hebben voorbeelden
- User engagement +30%
- Export usage +50%

---
*Epic owner: AI Team*  
*Last updated: 2025-01-18*