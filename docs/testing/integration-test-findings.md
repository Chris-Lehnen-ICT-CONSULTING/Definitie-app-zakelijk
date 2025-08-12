# Integration Test Findings

## Datum: 2025-08-11

## Gevonden Issues

### 1. ✅ OPGELOST: Service Factory Feature Flag Issue
De `service_factory.py` gaf prioriteit aan Streamlit session state boven environment variables.

**Oplossing:**
Environment variables krijgen nu prioriteit voor tests en deployment:
```python
# Check feature flag - environment variable heeft prioriteit voor tests/deployment
use_new_services = os.getenv('USE_NEW_SERVICES', '').lower() == 'true'

# Als geen env var, check Streamlit session state
if not use_new_services and not os.getenv('USE_NEW_SERVICES'):
    try:
        use_new_services = st.session_state.get('use_new_services', False)
```

**Status:** Fixed en getest

### 2. Database Locking Issues
Bij het runnen van integration tests krijgen we "database is locked" errors.

**Error:**
```
ERROR services.definition_repository:definition_repository.py:86 Fout bij opslaan definitie: database is locked
```

**Mogelijke oorzaak:**
- Concurrent access zonder proper connection pooling
- SQLite limitaties met concurrent writes
- Test isolation probleem

### 3. Async Function Handling
Verschillende async functies worden niet correct afgehandeld:

**Warning:**
```
RuntimeWarning: coroutine 'zoek_bronnen_voor_begrip' was never awaited
```

**Betrokken functies:**
- `zoek_bronnen_voor_begrip`
- Mogelijk andere async helpers

### 4. Mock Patching Issues
Mocks worden niet correct toegepast in de nieuwe service architectuur.

**Probleem:**
- `@patch('prompt_builder.stuur_prompt_naar_gpt')` wordt niet opgepikt
- Mock call count blijft 0

**Mogelijke oorzaak:**
- Import paths verschillen tussen legacy en nieuwe services
- Dependency injection maakt mocking complexer

## Gevonden Architectuur Verschillen

### 1. Service Initialization
- **Legacy**: Singleton pattern met directe imports
- **Nieuwe**: Dependency injection met lazy loading

### 2. Error Handling
- **Legacy**: Direct exceptions naar caller
- **Nieuwe**: Wrapped in response objects

### 3. Async Patterns
- **Legacy**: Mixed async/sync met run_in_executor
- **Nieuwe**: Native async throughout

## Aanbevelingen

### Korte Termijn (Voor Production)
1. **Fix Feature Flag**: Debug waarom service factory niet correct switcht
2. **Database Connection**: Implementeer connection pooling of gebruik async SQLite
3. **Mock Strategy**: Ontwikkel mock helpers specifiek voor DI architectuur

### Medium Termijn
1. **Integration Test Suite**: Bouw dedicated test harness voor A/B testing
2. **Performance Monitoring**: Add metrics voor legacy vs new comparison
3. **Gradual Rollout**: Start met read-only operations

### Lange Termijn
1. **Database Migration**: Overweeg PostgreSQL voor betere concurrency
2. **Complete Async**: Maak alle code paths fully async
3. **Remove Legacy**: Plan voor complete legacy removal

## Test Strategie Aanpassing

### Phase 1: Unit Test Focus
Focus op unit tests per service (✅ Completed - 84% coverage)

### Phase 2: Service Integration Tests
Test services in isolatie met gemockte dependencies

### Phase 3: System Integration Tests
Test complete flow met echte database en services

### Phase 4: A/B Comparison Tests
Side-by-side comparison van legacy vs nieuwe implementatie

## Volgende Stappen

1. **Debug Feature Flag Issue**
   - Trace door service_factory.py execution
   - Check Streamlit session state interference
   - Test met clean environment

2. **Fix Database Locking**
   - Implement connection retry logic
   - Use WAL mode voor SQLite
   - Consider connection pooling

3. **Update Mock Strategy**
   - Create DI-aware mock helpers
   - Document correct mock patterns
   - Update alle tests met nieuwe patterns

4. **Create Smoke Tests**
   - Basic functionality verificatie
   - Performance benchmarks
   - Error scenario testing