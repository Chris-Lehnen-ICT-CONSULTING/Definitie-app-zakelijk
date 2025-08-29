# Database Migration Strategy - Pragmatische Aanpak

## 🎯 Doel
De database is **GEEN blocker** voor de core functionaliteit. We gaan het opsplitsen in behapbare stukken.

## 📋 3-Stappen Plan

### Stap 1: In-Memory Repository (1 dag)
**Doel**: Ontkoppel de definitie generator van database afhankelijkheid

```python
# src/services/in_memory_repository.py
class InMemoryDefinitionRepository(DefinitionRepositoryInterface):
    """
    Simpele in-memory implementatie voor development en testing.
    Geen database nodig!
    """
    def __init__(self):
        self.definitions = {}
        self.next_id = 1

    def save(self, definition: Definition) -> int:
        definition.id = self.next_id
        self.definitions[self.next_id] = definition
        self.next_id += 1
        return definition.id

    def get(self, id: int) -> Optional[Definition]:
        return self.definitions.get(id)

    def search(self, query: str) -> List[Definition]:
        # Simpele in-memory search
        results = []
        for def in self.definitions.values():
            if query.lower() in def.begrip.lower():
                results.append(def)
        return results
```

**Voordeel**:
- Generator werkt zonder database
- Makkelijk testen
- Geen legacy dependencies

### Stap 2: Repository Facade (2 dagen)
**Doel**: Abstraheer database operaties achter service layer

```python
# src/services/definition_storage_service.py
class DefinitionStorageService:
    """
    Business logic voor opslag, GEEN directe database access.
    """
    def __init__(self, repository: DefinitionRepositoryInterface):
        self.repository = repository

    def store_with_validation(self, definition: Definition):
        # Business logic hier
        if self.is_duplicate(definition):
            raise DuplicateError()
        return self.repository.save(definition)

    def find_similar(self, begrip: str):
        # Zoek logica hier, niet in repository
        pass
```

**Voordeel**:
- Business logic uit database layer
- Repository wordt "dom" (alleen CRUD)
- Makkelijk te mocken/testen

### Stap 3: Gradual UI Migration (1 week)
**Doel**: Migreer UI tabs één voor één

**Volgorde (makkelijk → moeilijk):**
1. **Definition Generator Tab** - Gebruik in-memory (geen history nodig)
2. **Quality Control Tab** - Alleen huidige sessie data
3. **Export Tab** - Kan vanuit services/memory
4. **History Tab** - Eerste tab die echt database nodig heeft
5. **Management Tab** - Complexste, als laatste

## 🚀 Implementatie Volgorde

### Week 1: Foundation
```python
# 1. Maak InMemoryRepository
# 2. Update ServiceContainer om repository type te kiezen:
def repository(self) -> DefinitionRepositoryInterface:
    if self.config.get("use_database", True):
        return DefinitionRepository(self.db_path)
    else:
        return InMemoryDefinitionRepository()
```

### Week 2: Service Layer
```python
# 1. Maak StorageService
# 2. Verplaats business logic:
#    - Duplicate detection → StorageService
#    - Export logic → ExportService
#    - Import logic → ImportService
```

### Week 3-4: UI Migration
```python
# Per tab:
# 1. Verwijder directe database access
# 2. Gebruik services via container
# 3. Test uitgebreid
```

## ✅ Voordelen van deze aanpak

1. **Geen Big Bang** - Alles blijft werken tijdens migratie
2. **Database wordt optioneel** - Kan draaien zonder SQLite
3. **Testbaar** - In-memory voor unit tests
4. **Incrementeel** - Tab voor tab migreren
5. **Business logic separated** - Uit database layer

## 🎯 Quick Win: Start met InMemoryRepository

Dit kunnen we **vandaag** implementeren en direct testen:

```bash
# In .env
USE_DATABASE=false  # Gebruik in-memory
USE_NEW_SERVICES=true  # Gebruik nieuwe architectuur
```

Dan werkt de generator zonder database dependencies!

## 📊 Geschatte Tijd

- **In-Memory Repository**: 4 uur
- **Storage Service**: 8 uur
- **UI Tab Migration**: 2-3 uur per tab
- **Testing**: 8 uur

**Totaal**: ~40 uur (1 week fulltime)

Veel beter dan de oorspronkelijke 10 weken!
