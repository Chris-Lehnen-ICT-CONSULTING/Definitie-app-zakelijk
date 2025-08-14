# 🔍 Code Review Protocol - Systematische Verificatie

**Doel**: Verifiëren wat werkelijk functioneert vs wat alleen bestaat/geclaimd wordt  
**Gebruik**: Dit protocol voor ELKE component/feature uitvoeren

---

## 📋 Standaard Review Checklist

### Phase 1: Quick Existence Check (5 min)
```bash
□ Bestaat het bestand/de module?
□ Kan het geïmporteerd worden zonder errors?
□ Zijn er obvious syntax errors?
□ Bestaat de documentatie?
```

### Phase 2: Dependency Analysis (10 min)
```bash
□ Lijst alle imports
□ Verifieer dat alle dependencies bestaan
□ Check of import namen kloppen
□ Identificeer circulaire dependencies
□ Controleer versie compatibiliteit
```

### Phase 3: Functionality Test (20 min)
```bash
□ Start de functionaliteit op
□ Voer happy path test uit
□ Test edge cases
□ Test error handling
□ Verifieer output format
```

### Phase 4: Integration Check (15 min)
```bash
□ Hoe integreert het met andere componenten?
□ Worden interfaces correct gebruikt?
□ Data flow verificatie
□ Side effects check
```

### Phase 5: Test Suite Verification (10 min)
```bash
□ Draaien de tests echt?
□ Wat is de werkelijke coverage?
□ Zijn er skipped tests?
□ Mock vs echte functionaliteit
```

---

## 🎯 Component-Specifieke Reviews

### 1. Service Review Template
```python
# VOOR ELKE SERVICE (Generator, Validator, Repository, etc.)

## Stap 1: Import Test
try:
    from services.{service_name} import {ServiceClass}
    print("✅ Import succesvol")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    # STOP - service bestaat niet/kan niet laden

## Stap 2: Instantiation Test  
try:
    service = {ServiceClass}()
    print("✅ Instantiatie succesvol")
except Exception as e:
    print(f"❌ Instantiatie failed: {e}")
    # Documenteer missing dependencies

## Stap 3: Method Test
# Test ELKE publieke methode
methods_to_test = [
    ("method_name", test_args, expected_output),
    # ... voor elke methode
]

for method, args, expected in methods_to_test:
    try:
        result = getattr(service, method)(*args)
        print(f"✅ {method} werkt")
        # Verifieer output
    except Exception as e:
        print(f"❌ {method} failed: {e}")

## Stap 4: Integration Test
# Test met echte dependencies
# Documenteer welke andere services nodig zijn
# Test data flow
```

### 2. Database/Repository Review
```python
## Stap 1: Connection Test
□ Kan verbinding maken?
□ Correct schema?
□ UTF-8 encoding werkt?

## Stap 2: CRUD Operations
□ Create - nieuw record
□ Read - ophalen data
□ Update - wijzigen record  
□ Delete - verwijderen record

## Stap 3: Concurrent Access
# Start 5 parallelle processen
□ Geen deadlocks?
□ Data integrity behouden?
□ Performance acceptabel?

## Stap 4: Migration Check
□ Alle migraties uitgevoerd?
□ Rollback mogelijk?
□ Data loss risico's?
```

### 3. API/Interface Review
```python
## Stap 1: Contract Verification
□ Alle methodes geïmplementeerd?
□ Correct return types?
□ Parameters match interface?

## Stap 2: Behavior Test
□ Expected behavior matches actual
□ Error cases handled
□ Async/sync correctheid

## Stap 3: Version Compatibility
□ Backwards compatible?
□ Breaking changes gedocumenteerd?
```

### 4. UI Component Review
```python
## Stap 1: Render Test
□ Component rendert zonder errors?
□ Alle UI elementen zichtbaar?
□ Correct styling?

## Stap 2: Interaction Test
□ Click handlers werken?
□ Forms submitten correct?
□ Validatie werkt?

## Stap 3: State Management
□ State updates correct?
□ No infinite loops?
□ Performance OK?

## Stap 4: Integration
□ Data komt aan van backend?
□ Updates worden gepersist?
□ Error states handled?
```

---

## 📊 Review Output Template

Voor elk gereviewd item, documenteer:

```markdown
# Component: [Naam]
**Review Datum**: [YYYY-MM-DD]
**Reviewer**: [Naam/Tool]
**Claimed Status**: [Wat wordt beweerd]
**Actual Status**: [Wat werkelijk werkt]

## Bevindingen

### ✅ Wat Werkt
- [Lijst van werkende functionaliteit]

### ❌ Wat Niet Werkt  
- [Lijst van kapotte functionaliteit]
- [Root cause per probleem]

### ⚠️ Gedeeltelijk Werkend
- [Functionaliteit die partly werkt]
- [Onder welke condities faalt het]

## Dependencies
- **Werkend**: [lijst]
- **Ontbrekend**: [lijst]
- **Incorrect**: [lijst]

## Test Coverage
- **Claimed**: X%
- **Actual**: Y%
- **Tests die falen**: [lijst]

## Integratie Status
- **Component A**: ✅/❌ [details]
- **Component B**: ✅/❌ [details]

## Geschatte Reparatietijd
- **Quick fixes** (< 1 dag): [lijst]
- **Medium fixes** (1-3 dagen): [lijst]  
- **Major fixes** (> 3 dagen): [lijst]

## Prioriteit
🔴 KRITIEK / 🟡 BELANGRIJK / 🟢 NICE TO HAVE

## Aanbevelingen
1. [Concrete actie 1]
2. [Concrete actie 2]
```

---

## 🚀 Uitvoering Strategie

### Week 1, Dag 1-2: Batch Review
```bash
Maandag Ochtend:
09:00-10:00: Service Architecture overview
10:00-11:00: DefinitionGenerator deep dive  
11:00-12:00: DefinitionValidator + regels
13:00-14:00: DefinitionRepository + DB
14:00-15:00: DefinitionOrchestrator
15:00-16:00: WebLookupService (al gedaan)
16:00-17:00: Documenteer findings

Dinsdag:
09:00-10:00: Feature flags system
10:00-11:00: UI Components (alle tabs)
11:00-12:00: Test infrastructure
13:00-14:00: Database/migrations
14:00-15:00: Integration points
15:00-17:00: Prioriteit matrix maken
```

### Output: Priority Matrix
```
         Urgent  | Not Urgent
        ---------|----------
Broken  | FIX NOW | Schedule
        |   🔴    |    🟡
        ---------|----------
Works   | Verify  | Document  
        |   🟡    |    🟢
```

---

## 🔧 Tools & Commands

### Automated Checks
```bash
# Import check
python -c "from services.xyz import XYZ; print('✅')"

# Test runner
pytest tests/test_xyz.py -v --tb=short

# Coverage check
pytest --cov=services.xyz --cov-report=term-missing

# Lint check
pylint services/xyz.py

# Type check
mypy services/xyz.py
```

### Manual Verification
```python
# Quick service test script
def verify_service(service_class, test_method, test_args):
    try:
        service = service_class()
        result = getattr(service, test_method)(*test_args)
        return True, result
    except Exception as e:
        return False, str(e)

# Database test
def verify_concurrent_access():
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(db_operation) for _ in range(5)]
        results = [f.result() for f in futures]
    return all(results)
```

---

## ⚡ Quick Decision Tree

```
Kan het geïmporteerd worden?
├─ NEE → Component bestaat niet/syntax error
│   └─ Actie: Volledige rebuild nodig
├─ JA → Kan het geïnstantieerd worden?
    ├─ NEE → Dependencies missing/incorrect
    │   └─ Actie: Fix dependencies eerst
    ├─ JA → Werken de methodes?
        ├─ NEE → Implementation bugs
        │   └─ Actie: Debug & fix methods
        ├─ JA → Integreert het correct?
            ├─ NEE → Interface mismatch
            │   └─ Actie: Update interfaces
            └─ JA → Component werkt! ✅
```

---

## 📝 Review Log Template

Houd een log bij tijdens review:

```
[09:15] Starting review of DefinitionGenerator
[09:16] ✅ Import successful
[09:18] ❌ Missing dependency: OpenAI client not configured  
[09:20] ❌ Method generate_definition fails with: "api_key required"
[09:25] ⚠️ Tests exist but skip due to missing API key
[09:30] Priority: 🔴 KRITIEK - core functionaliteit
[09:32] Est. fix time: 2 hours (config setup)
```

---

Dit protocol geeft een systematische aanpak voor het reviewen van elke component. Het belangrijkste is:
1. **Wees methodisch** - sla geen stappen over
2. **Documenteer alles** - ook kleine problemen
3. **Test echt** - vertrouw niet op bestaande tests
4. **Prioriteer** - niet alles hoeft perfect