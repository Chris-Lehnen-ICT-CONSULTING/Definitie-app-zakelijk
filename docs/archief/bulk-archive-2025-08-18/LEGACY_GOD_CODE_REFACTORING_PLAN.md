# Legacy God Code Refactoring Plan

## 🎯 Target: `ai_toetser/core.py` (2062 regels)

**Probleem**: Dit bestand is een klassiek "God Object" - het doet te veel en is moeilijk te onderhouden.

### 📊 Huidige Situatie

**Bestand**: `src/ai_toetser/core.py`
- **Lines of Code**: 2062
- **Functies**: 51
- **Verantwoordelijkheden**: Te veel!

### 🔍 Analyse van Verantwoordelijkheden

#### 1. **OpenAI Client Management**
```python
def _get_openai_client() -> OpenAI:
```
- Configuratie en instantiatie van OpenAI client
- Environment variabele management

#### 2. **Toetsregels - CON (Consistentie)**
```python
def toets_CON_01(definitie: str, regel: dict, contexten: dict = None) -> str:
def toets_CON_02(definitie: str, regel: dict, bronnen_gebruikt: str = None) -> str:
```

#### 3. **Toetsregels - ESS (Essentieel)**
```python
def toets_ESS_01(definitie: str, regel: dict) -> str:
def toets_ESS_02(...) -> str:
def toets_ESS_03(...) -> str:
def toets_ESS_04(...) -> str:
def toets_ESS_05(...) -> str:
```

#### 4. **Toetsregels - INT (Integriteit)**
```python
def toets_INT_01(definitie, regel):
def toets_INT_02(...) -> str:
# ... tot INT_10
```

#### 5. **Toetsregels - SAM (Samenhang)**
```python
def toets_SAM_01(definitie: str, regel: Dict[str, Any]) -> str:
def toets_SAM_02(...) -> str:
```

#### 6. **Utility Functions**
```python
def fetch_base_definition(term: str) -> Optional[str]:
```

### 🏗️ Refactoring Strategie

#### **Stap 1: Categorisatie & Analyse**
- [x] Identificeer alle functie groepen
- [x] Map dependencies tussen functies
- [ ] Analyseer shared state en data

#### **Stap 2: Module Extractie Plan**
Splits op basis van Single Responsibility Principle:

1. **`ai_client.py`** - OpenAI client management
2. **`toetsregels/con_rules.py`** - CON toetsregels
3. **`toetsregels/ess_rules.py`** - ESS toetsregels
4. **`toetsregels/int_rules.py`** - INT toetsregels
5. **`toetsregels/sam_rules.py`** - SAM toetsregels
6. **`toetsregels/ara_rules.py`** - ARA toetsregels (als die bestaan)
7. **`rule_utils.py`** - Gedeelde utilities

#### **Stap 3: Interface Ontwerp**
```python
# New structure
from ai_toetser.rules.con_rules import toets_CON_01, toets_CON_02
from ai_toetser.rules.ess_rules import toets_ESS_01, toets_ESS_02, ...
from ai_toetser.rules.int_rules import toets_INT_01, toets_INT_02, ...
from ai_toetser.rules.sam_rules import toets_SAM_01, toets_SAM_02, ...
from ai_toetser.client import get_ai_client
from ai_toetser.utils import fetch_base_definition
```

#### **Stap 4: Backward Compatibility**
```python
# ai_toetser/core.py (legacy compatibility wrapper)
from ai_toetser.rules.con_rules import toets_CON_01, toets_CON_02
from ai_toetser.rules.ess_rules import *
from ai_toetser.rules.int_rules import *
from ai_toetser.rules.sam_rules import *
from ai_toetser.client import get_ai_client as _get_openai_client
from ai_toetser.utils import *

# All original function names remain available
```

### 📋 Executie Plan

#### **Week 1: Analyse & Voorbereiding**
- [ ] **Dag 1**: Dependencies mapping
- [ ] **Dag 2**: Shared state analyse
- [ ] **Dag 3**: Module boundaries definitie
- [ ] **Dag 4**: Test strategie ontwerp
- [ ] **Dag 5**: Backup en safety measures

#### **Week 2: Extractie Uitvoering**
- [ ] **Dag 1**: Extract OpenAI client → `ai_client.py`
- [ ] **Dag 2**: Extract CON rules → `toetsregels/con_rules.py`
- [ ] **Dag 3**: Extract ESS rules → `toetsregels/ess_rules.py`
- [ ] **Dag 4**: Extract INT rules → `toetsregels/int_rules.py`
- [ ] **Dag 5**: Extract SAM rules → `toetsregels/sam_rules.py`

#### **Week 3: Integration & Testing**
- [ ] **Dag 1**: Extract utilities → `rule_utils.py`
- [ ] **Dag 2**: Setup legacy compatibility wrapper
- [ ] **Dag 3**: Update all imports in codebase
- [ ] **Dag 4**: Comprehensive testing
- [ ] **Dag 5**: Documentation & cleanup

### 🧪 Testing Strategie

#### **1. Pre-Refactoring Tests**
```python
# Capture current behavior
python -c "
from ai_toetser.core import *
# Test all 51 functions with sample data
# Generate baseline results
"
```

#### **2. During Refactoring Tests**
- Unit tests voor elke geëxtraheerde module
- Integration tests voor module samenwerking
- Regression tests voor unchanged behavior

#### **3. Post-Refactoring Tests**
- Verify all original functionality
- Performance tests (should be same or better)
- Memory usage tests

### ⚠️ Risk Mitigation

#### **High Risk Areas**
1. **Circular Dependencies**: Toetsregels die elkaar aanroepen
2. **Shared State**: Global variables of shared data
3. **Import Chaos**: 51 functies zijn overal gebruikt
4. **Configuration**: Gedeelde config tussen functies

#### **Mitigation Strategies**
1. **Feature Flags**: Graduale rollout van nieuwe modules
2. **A/B Testing**: Oude vs nieuwe implementatie parallel
3. **Rollback Plan**: Mogelijkheid om terug te gaan naar god object
4. **Monitoring**: Track performance en errors tijdens overgang

### 📊 Success Metrics

#### **Code Quality**
- [ ] Lines of code per file < 500
- [ ] Functies per file < 15
- [ ] Cyclomatic complexity reduction
- [ ] Test coverage behouden (>90%)

#### **Maintainability**
- [ ] Time to add new toetsregel: -50%
- [ ] Bug fix time: -40%
- [ ] Code review tijd: -60%

#### **Performance**
- [ ] Execution time: ±5% (geen regressie)
- [ ] Memory usage: ±10% (geen regressie)
- [ ] Import time: -20% (beter door kleinere modules)

### 🎯 Long-term Vision

Na refactoring krijgen we:

1. **Modulaire Architectuur**: Elke toetsregel groep in eigen module
2. **Single Responsibility**: Elk bestand heeft één duidelijk doel
3. **Testbaarheid**: Makkelijker om individuele regels te testen
4. **Uitbreidbaarheid**: Nieuwe toetsregels toevoegen zonder god object
5. **Maintainability**: Bug fixes zijn gelokaliseerd
6. **Team Development**: Multiple developers kunnen parallel werken

### 🚀 Benefits

**Voor Development:**
- Snellere feature development
- Minder merge conflicts
- Betere code reviews
- Makkelijker debugging

**Voor Maintenance:**
- Gelokaliseerde bug fixes
- Duidelijke verantwoordelijkheden
- Betere test isolation
- Reduced cognitive load

**Voor Performance:**
- Snellere imports (lazy loading mogelijk)
- Betere memory usage
- Makkelijkere optimalisatie per regel

---

**Status**: Ready for execution 🚀
**Priority**: High - God objects zijn development bottlenecks
**Timeline**: 3 weeks for complete refactoring
