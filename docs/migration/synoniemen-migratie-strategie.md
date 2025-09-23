# Migratiestrategie: Synoniemen, Antoniemen & AI-Toelichting naar definitie_voorbeelden

## Executive Summary

Dit document beschrijft een complete strategie om synoniemen, antoniemen en AI-toelichting te migreren van de `definities` tabel naar de `definitie_voorbeelden` tabel. Deze migratie verbetert de datastructuur door gebruik te maken van de rijkere tracking mogelijkheden van de voorbeelden tabel.

## Huidige Situatie

### Database Schema
- **definities tabel**:
  - `synoniemen TEXT` - JSON array van synoniemen
  - `toelichting_proces TEXT` - Procesmatige toelichting (review/validatie notities)
  - GEEN expliciete kolommen voor antoniemen of AI-toelichting

- **definitie_voorbeelden tabel**:
  - Ondersteunt al types: `'synonyms'`, `'antonyms'`, `'explanation'`
  - Bevat rijke metadata: wie, wanneer, beoordeling, generation parameters
  - Heeft actief/inactief status voor versioning

### Dataflow Analyse

1. **Synoniemen**:
   - Worden opgeslagen als JSON array in `definities.synoniemen`
   - Worden gelezen via `Definition.synoniemen` property
   - Import service parsed CSV velden naar synoniemen lijst

2. **Antoniemen**:
   - NIET expliciet opgeslagen in definities tabel
   - WEL ondersteund in voorbeelden tabel met type='antonyms'
   - Worden gegenereerd door AI maar niet persistent opgeslagen

3. **AI-Toelichting**:
   - NIET expliciet in definities tabel (alleen proces toelichting)
   - WEL ondersteund in voorbeelden tabel met type='explanation'
   - Wordt gegenereerd maar niet opgeslagen

## Voorgestelde Database Strategie

### 1. Opslagmodel: Één Record per Item

**Rationale**: Maximum flexibiliteit en consistentie met bestaande voorbeelden structuur.

```sql
-- Elke synoniem als aparte rij
INSERT INTO definitie_voorbeelden (
    definitie_id, voorbeeld_type, voorbeeld_tekst, voorbeeld_volgorde, actief
) VALUES
    (123, 'synonyms', 'alternatieve term 1', 1, TRUE),
    (123, 'synonyms', 'alternatieve term 2', 2, TRUE),
    (123, 'synonyms', 'andere benaming', 3, TRUE);

-- Elke antoniem als aparte rij
INSERT INTO definitie_voorbeelden (
    definitie_id, voorbeeld_type, voorbeeld_tekst, voorbeeld_volgorde, actief
) VALUES
    (123, 'antonyms', 'tegengestelde term 1', 1, TRUE),
    (123, 'antonyms', 'tegengestelde term 2', 2, TRUE);

-- AI-toelichting als enkele rij (lange tekst)
INSERT INTO definitie_voorbeelden (
    definitie_id, voorbeeld_type, voorbeeld_tekst, voorbeeld_volgorde, actief
) VALUES
    (123, 'explanation', 'Uitgebreide AI-gegenereerde toelichting...', 1, TRUE);
```

### 2. Voordelen van Deze Aanpak

- **Consistentie**: Zelfde structuur als andere voorbeelden types
- **Flexibiliteit**: Elke synoniem/antoniem kan apart beoordeeld worden
- **Versioning**: Actief/inactief status per item
- **Metadata**: Generation info, beoordeling per item mogelijk
- **Query Performance**: Makkelijk filteren op type + actief status

### 3. Database Migratie Script

```sql
-- Stap 1: Migreer bestaande synoniemen van definities naar voorbeelden
INSERT INTO definitie_voorbeelden (
    definitie_id,
    voorbeeld_type,
    voorbeeld_tekst,
    voorbeeld_volgorde,
    gegenereerd_door,
    actief,
    aangemaakt_op
)
SELECT
    d.id,
    'synonyms',
    json_each.value,
    json_each.key + 1,  -- volgorde gebaseerd op array positie
    'migration',
    TRUE,
    CURRENT_TIMESTAMP
FROM definities d,
     json_each(d.synoniemen)
WHERE d.synoniemen IS NOT NULL
  AND d.synoniemen != '[]'
  AND d.synoniemen != '';

-- Stap 2: Verwijder synoniemen kolom (na verificatie)
-- ALTER TABLE definities DROP COLUMN synoniemen;
```

## Code Aanpassingen per Module

### 1. Definition Class (`src/services/interfaces.py`)

```python
@dataclass
class Definition:
    """Definitie data object met alle metadata."""

    # Bestaande velden...
    id: int | None = None
    begrip: str = ""
    definitie: str = ""

    # DEPRECATED - wordt lazy loaded uit voorbeelden tabel
    # synoniemen: list[str] | None = None

    # Nieuwe properties voor lazy loading
    _synoniemen: list[str] | None = None
    _antoniemen: list[str] | None = None
    _ai_toelichting: str | None = None
    _voorbeelden_loaded: bool = False

    @property
    def synoniemen(self) -> list[str]:
        """Lazy load synoniemen uit voorbeelden tabel."""
        if not self._voorbeelden_loaded and self.id:
            self._load_voorbeelden()
        return self._synoniemen or []

    @property
    def antoniemen(self) -> list[str]:
        """Lazy load antoniemen uit voorbeelden tabel."""
        if not self._voorbeelden_loaded and self.id:
            self._load_voorbeelden()
        return self._antoniemen or []

    @property
    def ai_toelichting(self) -> str:
        """Lazy load AI-toelichting uit voorbeelden tabel."""
        if not self._voorbeelden_loaded and self.id:
            self._load_voorbeelden()
        return self._ai_toelichting or ""

    def _load_voorbeelden(self):
        """Load voorbeelden data van repository (injected via metadata)."""
        if self.metadata and 'repository' in self.metadata:
            repo = self.metadata['repository']
            voorbeelden = repo.get_voorbeelden_by_type(self.id)
            self._synoniemen = voorbeelden.get('synonyms', [])
            self._antoniemen = voorbeelden.get('antonyms', [])
            explanations = voorbeelden.get('explanation', [])
            self._ai_toelichting = explanations[0] if explanations else ""
        self._voorbeelden_loaded = True
```

### 2. DefinitionRepository (`src/services/definition_repository.py`)

```python
class DefinitionRepository:

    def save(self, definition: Definition) -> int:
        """Sla definitie op inclusief synoniemen/antoniemen in voorbeelden."""

        # Sla hoofdrecord op (zonder synoniemen kolom)
        definition_id = self._save_main_record(definition)

        # Sla synoniemen/antoniemen/toelichting op in voorbeelden tabel
        if definition.synoniemen or definition.antoniemen or definition.ai_toelichting:
            voorbeelden_dict = {}

            if definition.synoniemen:
                voorbeelden_dict['synonyms'] = definition.synoniemen
            if definition.antoniemen:
                voorbeelden_dict['antonyms'] = definition.antoniemen
            if definition.ai_toelichting:
                voorbeelden_dict['explanation'] = [definition.ai_toelichting]

            self.legacy_repo.save_voorbeelden(
                definition_id,
                voorbeelden_dict,
                generation_model=definition.metadata.get('model'),
                gegenereerd_door=definition.metadata.get('created_by', 'system')
            )

        return definition_id

    def get(self, definition_id: int) -> Definition | None:
        """Haal definitie op inclusief synoniemen/antoniemen."""

        # Haal hoofdrecord op
        definition = self._get_main_record(definition_id)
        if not definition:
            return None

        # Injecteer repository voor lazy loading
        if not definition.metadata:
            definition.metadata = {}
        definition.metadata['repository'] = self

        # Voorbeelden worden lazy loaded via properties
        return definition

    def search(self, **criteria) -> list[Definition]:
        """Zoek definities met voorbeelden."""
        definitions = self._search_main_records(**criteria)

        # Injecteer repository voor lazy loading
        for definition in definitions:
            if not definition.metadata:
                definition.metadata = {}
            definition.metadata['repository'] = self

        return definitions
```

### 3. DefinitionImportService (`src/services/definition_import_service.py`)

```python
def _payload_to_definition(self, payload: Dict[str, Any]) -> Definition:
    """Converteer import payload naar Definition object."""

    # Bestaande velden...
    definition = Definition(
        begrip=payload.get('begrip', ''),
        definitie=payload.get('definitie', ''),
        # ... andere velden
    )

    # Parse synoniemen/antoniemen voor nieuwe structuur
    synoniemen_str = payload.get('Synoniemen', payload.get('synoniemen', ''))
    if synoniemen_str:
        definition._synoniemen = [s.strip() for s in synoniemen_str.split(',')]

    antoniemen_str = payload.get('Antoniemen', payload.get('antoniemen', ''))
    if antoniemen_str:
        definition._antoniemen = [a.strip() for a in antoniemen_str.split(',')]

    # AI toelichting (kan uit 'Toelichting' veld komen)
    toelichting = payload.get('Toelichting', '')
    if toelichting and not payload.get('Toelichting (optioneel)'):
        # Als alleen hoofdtoelichting, gebruik als AI-toelichting
        definition._ai_toelichting = toelichting
        definition._voorbeelden_loaded = True  # Prevent lazy loading

    return definition
```

### 4. UI Components Updates

```python
# In definition_edit_tab.py en expert_review_tab.py

def display_synoniemen(definition: Definition):
    """Toon synoniemen uit voorbeelden tabel."""
    # Properties doen automatisch lazy loading
    synoniemen = definition.synoniemen  # Haalt uit voorbeelden tabel

    if synoniemen:
        st.write("**Synoniemen:**")
        for syn in synoniemen:
            st.write(f"- {syn}")

    # Edit mogelijkheid
    new_synoniemen = st.text_area(
        "Synoniemen bewerken (komma-gescheiden)",
        value=", ".join(synoniemen)
    )

    if st.button("Synoniemen opslaan"):
        # Update via repository
        voorbeelden_dict = {'synonyms': [s.strip() for s in new_synoniemen.split(',')]}
        repository.save_voorbeelden(definition.id, voorbeelden_dict)
```

## Backward Compatibility Plan

### Fase 1: Dual-Write (2 weken)
1. **Schrijf naar beide locaties**: Nieuwe data naar zowel `synoniemen` kolom als `voorbeelden` tabel
2. **Lees met fallback**: Eerst uit `voorbeelden`, dan uit `synoniemen` kolom
3. **Monitor**: Log waar data vandaan komt voor analyse

### Fase 2: Migratie (1 week)
1. **Run migratie script**: Verplaats alle bestaande synoniemen naar voorbeelden
2. **Verificatie**: Check dat alle data correct gemigreerd is
3. **Backup**: Maak backup van definities tabel voor rollback

### Fase 3: Cutover (1 dag)
1. **Stop dual-write**: Schrijf alleen naar voorbeelden tabel
2. **Update reads**: Haal alles uit voorbeelden tabel
3. **Deprecate kolom**: Markeer synoniemen kolom als deprecated

### Fase 4: Cleanup (na 1 maand)
1. **Verwijder kolom**: `ALTER TABLE definities DROP COLUMN synoniemen`
2. **Cleanup code**: Verwijder legacy code paths

## Performance Overwegingen

### Query Performance
- **Index strategie**: Bestaande indexes op `definitie_voorbeelden` zijn voldoende
- **Lazy loading**: Voorkom N+1 queries met batch loading waar nodig
- **Caching**: Cache voorbeelden in Definition object na eerste load

### Geschatte Impact
- **Read performance**: Marginaal langzamer (extra join), maar met caching vergelijkbaar
- **Write performance**: Iets langzamer (2 inserts ipv 1), maar acceptabel
- **Storage**: Meer rows maar minder JSON parsing overhead

### Optimalisaties
```python
# Batch load voorbeelden voor meerdere definities
def load_voorbeelden_batch(definitions: list[Definition]):
    """Efficient batch loading van voorbeelden."""
    ids = [d.id for d in definitions if d.id]

    # Single query voor alle voorbeelden
    all_voorbeelden = repository.get_voorbeelden_for_ids(ids)

    # Map naar definities
    for definition in definitions:
        if definition.id in all_voorbeelden:
            voorbeelden = all_voorbeelden[definition.id]
            definition._synoniemen = voorbeelden.get('synonyms', [])
            definition._antoniemen = voorbeelden.get('antonyms', [])
            definition._ai_toelichting = voorbeelden.get('explanation', [''])[0]
            definition._voorbeelden_loaded = True
```

## Testing Strategie

### Unit Tests
```python
def test_synoniemen_migration():
    """Test dat synoniemen correct gemigreerd worden."""
    # Create definitie met synoniemen in oude structuur
    old_def = create_legacy_definition_with_synoniemen()

    # Run migratie
    migrate_synoniemen(old_def.id)

    # Verificeer in nieuwe structuur
    new_def = repository.get(old_def.id)
    assert new_def.synoniemen == old_def.synoniemen
```

### Integration Tests
- Test import flow met synoniemen/antoniemen
- Test export met nieuwe structuur
- Test UI weergave en editing

### Performance Tests
- Benchmark read/write performance voor/na migratie
- Load test met 1000+ definities
- Memory profiling voor lazy loading

## Risico's en Mitigaties

| Risico | Impact | Kans | Mitigatie |
|--------|--------|------|-----------|
| Data verlies tijdens migratie | Hoog | Laag | Backup + rollback plan |
| Performance degradatie | Medium | Medium | Caching + batch loading |
| Backward compatibility issues | Medium | Laag | Dual-write periode |
| UI bugs door lazy loading | Laag | Medium | Uitgebreide testing |

## Implementatie Timeline

### Week 1
- [ ] Database migratie script ontwikkelen
- [ ] Definition class aanpassen met lazy loading
- [ ] Repository layer updaten

### Week 2
- [ ] Import service aanpassen
- [ ] UI components updaten
- [ ] Unit tests schrijven

### Week 3
- [ ] Dual-write implementeren
- [ ] Integration tests
- [ ] Performance testing

### Week 4
- [ ] Productie migratie
- [ ] Monitoring
- [ ] Documentatie updaten

## Conclusie

Deze migratiestrategie biedt een robuuste en schone oplossing die:
1. **Hergebruikt** bestaande infrastructuur maximaal
2. **Verbetert** data consistency en tracking mogelijkheden
3. **Behoudt** backward compatibility tijdens transitie
4. **Minimaliseert** performance impact
5. **Vereenvoudigt** toekomstig onderhoud

De gefaseerde aanpak zorgt voor een veilige migratie met rollback mogelijkheden op elk punt.