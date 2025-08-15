# Deprecated: AI Toetser God Object

## 📄 Bestand: `core.py` (2062 regels)

**Verplaatst op**: 2025-08-15  
**Reden**: God Object patroon vervangen door moderne modulaire architectuur

### 🚨 Probleem

`ai_toetser/core.py` was een klassiek "God Object":
- **2062 regels code** in één bestand
- **51 functies** (alle toetsregels)
- **Alle verantwoordelijkheden** in één plaats
- **Moeilijk te onderhouden** en uitbreiden
- **Single point of failure** voor alle validaties

### ✅ Moderne Vervanging

Het god object is vervangen door een modulaire architectuur:

#### **Individual Rule Files**
```
/src/toetsregels/regels/
├── CON-01.py + CON-01.json
├── CON-02.py + CON-02.json  
├── ESS-01.py + ESS-01.json
├── ESS-02.py + ESS-02.json
├── INT-01.py + INT-01.json
└── ... (90+ regel bestanden)
```

#### **Management System**
```
/src/toetsregels/
├── manager.py          # Centraal beheer
├── loader.py           # Regel laden
├── adapter.py          # Interface adapters
└── modular_loader.py   # Modulaire loading
```

#### **Validation System**
```
/src/validation/
├── definitie_validator.py   # Moderne validator
├── dutch_text_validator.py  # Tekst validatie
└── input_validator.py       # Input validatie
```

### 📊 Voordelen Nieuwe Architectuur

#### **Maintainability**
- **Single Responsibility**: Elke regel heeft eigen bestand
- **Easy Extension**: Nieuwe regels toevoegen zonder god object
- **Parallel Development**: Team kan parallel werken aan verschillende regels
- **Targeted Testing**: Test individuele regels in isolatie

#### **Performance**
- **Lazy Loading**: Alleen benodigde regels laden
- **Memory Efficient**: Minder geheugen door selectieve loading
- **Faster Startup**: Snellere applicatie start

#### **Code Quality**
- **Better Structure**: Heldere scheiding van verantwoordelijkheden
- **Type Safety**: Betere type hints per regel
- **Documentation**: Elke regel heeft eigen documentatie
- **Version Control**: Eenvoudigere merge conflicts

### 🔄 Migratie Details

#### **Wat is Vervangen**
- `toets_CON_01()` → `/toetsregels/regels/CON-01.py`
- `toets_ESS_01()` → `/toetsregels/regels/ESS-01.py`  
- `toets_INT_01()` → `/toetsregels/regels/INT-01.py`
- `_get_openai_client()` → Moderne client management
- Alle 51 functies → Individuele modules

#### **Laatste Referentie Bijgewerkt**
- **`services/definition_validator.py`**: 
  - `from ai_toetser.core import toets_definitie` 
  - → `from validation.definitie_validator import DefinitieValidator`

#### **Backward Compatibility**
Geen backward compatibility behouden omdat:
- God object was interne implementatie
- Moderne API is beter en consistenter  
- Geen externe dependencies op god object gevonden
- Refactoring is complete migration, niet gradual

### 🎯 Impact Measurement

#### **Before (God Object)**
- **Lines of Code**: 2062 regels in 1 bestand
- **Functions**: 51 functies in 1 namespace
- **Maintainability**: Moeilijk (cognitive overload)
- **Testing**: Complex (alles samen testen)
- **Extension**: Moeilijk (merge conflicts)

#### **After (Modular System)**
- **Lines of Code**: ~50-80 regels per regel bestand
- **Functions**: 1-2 functies per bestand
- **Maintainability**: Excellent (single responsibility)
- **Testing**: Easy (isolated unit tests)
- **Extension**: Easy (nieuwe bestanden toevoegen)

### 📚 Reference

Voor implementatie details van de nieuwe architectuur:
- **Manager**: `src/toetsregels/manager.py`
- **Validator**: `src/validation/definitie_validator.py`
- **Individual Rules**: `src/toetsregels/regels/`
- **Documentation**: `docs/toetsregels/`

---

**Status**: Successfully migrated to modern architecture ✅  
**Safe to Delete**: Na 3 maanden productie gebruik  
**Rollback**: Mogelijk via deze backup (niet aanbevolen)