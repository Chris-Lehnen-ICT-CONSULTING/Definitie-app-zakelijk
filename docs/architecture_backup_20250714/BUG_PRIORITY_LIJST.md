# 🐛 Bug Priority Lijst - App Stabilisatie

**Doel:** Alle bugs fixen om DefinitieAgent volledig werkend en stabiel te krijgen  
**Aanpak:** Stap-voor-stap, test na elke fix  
**Datum:** 2025-07-14  

---

## 🚨 **KRITIEK - Moet nu gefixed (Broken Core Functionality)**

### **1. Web Lookup Syntax Error** ⏱️ *15 minuten*
- **Status**: ❌ **BREEKT MODULE IMPORT**
- **File**: `src/web_lookup/definitie_lookup.py:676`
- **Error**: `unterminated string literal (detected at line 676)`
- **Impact**: Hele web lookup module kan niet geïmporteerd worden
- **Fix**: String literal afsluiten op regel 676
- **Test**: `python -c "from src.web_lookup.definitie_lookup import zoek_definitie"`

### **2. Web Lookup UTF-8 Encoding Error** ⏱️ *1 uur*
- **Status**: ❌ **BREEKT IMPORT**
- **Files**: `src/web_lookup/bron_lookup.py`, `src/web_lookup/definitie_lookup.py`
- **Error**: `'utf-8' codec can't decode byte 0xa0 in position 0`
- **Impact**: `WEB_LOOKUP_AVAILABLE = False` - geen externe validatie
- **Fix**: Converteer bestanden naar UTF-8 encoding
- **Test**: `python -c "from src.web_lookup.bron_lookup import zoek_bronnen_voor_begrip"`

### **3. Database Concurrent Access Lock** ⏱️ *4 uur*
- **Status**: ❌ **BREEKT MULTI-USER**
- **File**: `src/database/definitie_repository.py:738`
- **Error**: `sqlite3.OperationalError: database is locked`
- **Impact**: Database locks bij concurrent gebruik
- **Fix**: Implementeer connection timeout + proper connection handling
- **Test**: Concurrent database operations test

---

## 🔴 **URGENT - Deze week (Core Features Broken)**

### **4. SessionStateManager Missing Methods** ⏱️ *30 minuten*
- **Status**: ❌ **API INCONSISTENTIE**
- **File**: `src/ui/session_state.py`
- **Error**: `AttributeError: 'SessionStateManager' has no attribute 'clear_value'`
- **Impact**: Memory leaks, inconsistent session management
- **Fix**: Voeg `clear_value` method toe aan SessionStateManager
- **Test**: Unit test voor alle SessionStateManager methods

### **5. Plotly Import Dependencies** ⏱️ *10 minuten*
- **Status**: ✅ **OPGELOST** (requirements.txt updated)
- **Test**: Verify `python -c "import plotly"`

### **6. Resilience Utilities Import Error** ⏱️ *2 uur*
- **Status**: ❌ **MISSING FUNCTIONS**
- **File**: `src/utils/resilience.py`
- **Error**: `cannot import name 'with_retry' from 'utils.resilience'`
- **Impact**: Performance tests fail, geen error handling
- **Fix**: Implementeer missing `with_retry` en `CircuitBreaker` functions
- **Test**: `from src.utils.resilience import with_retry, CircuitBreaker`

### **7. AsyncAPIManager Missing** ⏱️ *3 uur*
- **Status**: ❌ **MISSING CLASS**
- **File**: `src/utils/async_api.py`
- **Error**: `cannot import name 'AsyncAPIManager' from 'utils.async_api'`
- **Impact**: Performance tests fail, geen async API management
- **Fix**: Implementeer AsyncAPIManager class
- **Test**: `from src.utils.async_api import AsyncAPIManager`

---

## 🟡 **BELANGRIJK - Volgende week (Quality Issues)**

### **8. Test Infrastructure Failures** ⏱️ *1 dag*
- **Status**: ❌ **MANY BROKEN TESTS**
- **Files**: Various test files
- **Issues**: Import errors, data structure mismatches, missing fixtures
- **Impact**: Geen reliable test coverage (16%)
- **Fix**: Fix test imports, update test data structures
- **Test**: `pytest tests/ -v` - target >80% pass rate

### **9. Configuration File Path Issues** ⏱️ *1 uur*
- **Status**: ⚠️ **PARTIALLY FIXED**
- **File**: `src/config/toetsregel_manager.py`
- **Issue**: Relative path resolution warnings
- **Impact**: Configuration warnings in logs
- **Fix**: Ensure robust absolute path handling
- **Test**: App starts zonder configuration warnings

### **10. Performance Issues** ⏱️ *2 uur*
- **Status**: ❌ **SLOW RESPONSE**
- **Issue**: 17 files met blocking `time.sleep()` in async context
- **Impact**: App response 5-8 seconds instead of <2s
- **Fix**: Replace `time.sleep()` with `asyncio.sleep()`
- **Test**: Response time benchmarks

---

## 🟢 **NICE TO HAVE - Later (Enhancement)**

### **11. Code Duplication Cleanup** ⏱️ *1 dag*
- **Status**: ❌ **TECHNICAL DEBT**
- **Issue**: 4 different resilience modules, ~20% code duplication
- **Impact**: Maintenance overhead
- **Fix**: Consolidate duplicate code
- **Test**: Code analysis tools

### **12. UI Component Size Reduction** ⏱️ *2 dagen*
- **Status**: ❌ **MAINTAINABILITY**
- **Issue**: Components >100 lines, mixed concerns
- **Impact**: Hard to maintain UI
- **Fix**: Break down large components
- **Test**: Component size metrics

---

## 📋 **WEEKPLANNING**

### **Week 1: Kritieke Fixes**
**Maandag:**
- [ ] **#1** Web lookup syntax error fix (15 min)
- [ ] **#2** UTF-8 encoding fix (1 uur)
- [ ] Test: Verify web lookup imports work

**Dinsdag:**
- [ ] **#3** Database concurrent access fix (4 uur)
- [ ] Test: Concurrent database operations

**Woensdag:**
- [ ] **#4** SessionStateManager methods (30 min)
- [ ] **#6** Resilience utilities (2 uur)
- [ ] Test: Verify utility imports

**Donderdag:**
- [ ] **#7** AsyncAPIManager implementation (3 uur)
- [ ] Test: Async functionality

**Vrijdag:**
- [ ] **Volledige app test** - alles testen
- [ ] **Regressie test** - geen nieuwe bugs
- [ ] **Performance check** - response times

### **Week 2: Quality & Stabiliteit**
**Maandag-Dinsdag:**
- [ ] **#8** Test infrastructure fixes (1 dag)
- [ ] Target: >80% tests passing

**Woensdag:**
- [ ] **#9** Configuration improvements (1 uur)
- [ ] **#10** Performance fixes (2 uur)

**Donderdag-Vrijdag:**
- [ ] **End-to-end testing** volledige app
- [ ] **Documentation update** fixes
- [ ] **Stability validation** - 24 uur continuous running

---

## 🧪 **TEST STRATEGIE PER FIX**

### **Immediate Testing (na elke fix):**
```bash
# 1. Import test
python -c "from src.module import function"

# 2. Unit test (waar mogelijk)
pytest tests/test_specific_module.py -v

# 3. Integration test
python -m src.main  # Start app, test basic functionality

# 4. No regression check
python -c "import src; print('No import errors')"
```

### **Daily Integration Test:**
```bash
# Full application test
1. Start app: streamlit run src/main.py
2. Test basic workflow:
   - Input begrip: "test"
   - Generate definition
   - Verify validation results
   - Check no errors in logs
3. Test advanced features:
   - Web lookup (if fixed)
   - Document upload
   - Export functionality
```

### **Weekly Stability Test:**
```bash
# Continuous operation test
1. Run app for 24 hours
2. Multiple concurrent users (if database fixed)
3. Memory usage monitoring
4. Error rate tracking
5. Performance metrics
```

---

## 🎯 **SUCCESS CRITERIA**

### **Week 1 Target: Core Stability**
- [ ] **Zero import errors** - all modules load successfully
- [ ] **Database stability** - no concurrent access locks
- [ ] **Web lookup functional** - external source validation works
- [ ] **Basic features work** - definition generation complete workflow
- [ ] **No critical exceptions** - app runs without crashes

### **Week 2 Target: Quality & Performance**
- [ ] **>80% tests passing** - reliable test suite
- [ ] **<3 second response time** - acceptable performance
- [ ] **Clean startup** - no configuration warnings
- [ ] **24h continuous operation** - stability proven
- [ ] **All core features tested** - comprehensive validation

### **Final Goal: Production Ready**
- [ ] **All P0 bugs fixed** - critical functionality works
- [ ] **All P1 bugs fixed** - important features work  
- [ ] **Test coverage >40%** - basic reliability
- [ ] **Performance acceptable** - user experience good
- [ ] **Documented known issues** - remaining bugs catalogued

---

## 🔧 **GEREEDSCHAP & SETUP**

### **Development Environment:**
```bash
# Ensure clean environment
cd /Users/chrislehnen/Projecten/Definitie-app
source venv/bin/activate  # or create if needed
pip install -r requirements.txt

# Verification commands
python -c "import sys; print(f'Python: {sys.version}')"
python -c "import streamlit; print(f'Streamlit: {streamlit.__version__}')"
```

### **Testing Commands:**
```bash
# Quick smoke test
python -c "import src; print('Basic imports OK')"

# Module specific tests
python -c "from src.web_lookup.definitie_lookup import zoek_definitie"
python -c "from src.web_lookup.bron_lookup import zoek_bronnen_voor_begrip"
python -c "from src.utils.resilience import with_retry"

# Run test suite
pytest tests/ -v --tb=short

# Start application
streamlit run src/main.py
```

---

## 📊 **PROGRESS TRACKING**

| Bug | Priority | Status | Estimated | Actual | Blocker For |
|-----|----------|--------|-----------|---------|-------------|
| Web Syntax Error | P0 | ❌ | 15 min | - | Web Lookup |
| UTF-8 Encoding | P0 | ❌ | 1 hour | - | Web Lookup |
| Database Locks | P0 | ❌ | 4 hours | - | Multi-user |
| SessionState API | P1 | ❌ | 30 min | - | UI Features |
| Resilience Utils | P1 | ❌ | 2 hours | - | Error Handling |
| AsyncAPIManager | P1 | ❌ | 3 hours | - | Performance |
| Test Infrastructure | P2 | ❌ | 1 day | - | Quality |
| Performance | P2 | ❌ | 2 hours | - | User Experience |

**Overall Progress: 0/8 (0%)**

---

## 🚨 **ESCALATION PLAN**

### **If Stuck >2 hours:**
1. **Document the issue** - exact error, steps tried
2. **Create minimal reproduction** - isolated test case
3. **Check dependencies** - version conflicts, environment
4. **Ask for help** - team collaboration
5. **Consider workaround** - temporary solution

### **If Timeline Slips:**
- **Week 1 slip**: Focus only on P0 bugs
- **Week 2 slip**: Defer P2 bugs to later
- **Major blocker**: Consider external help

---

**Next Action:** Start with #1 (Web Lookup Syntax Error) - snelle win!  
**Owner:** Development Team  
**Review:** Daily standup on progress  

---

*Deze prioriteitslijst zorgt ervoor dat jullie een stabiele, werkende app hebben voordat jullie aan de grote architectuur roadmap beginnen.*