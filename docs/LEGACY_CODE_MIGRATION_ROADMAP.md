# Legacy Code Migration Roadmap

**Laatste update**: 2025-08-25
**Status**: In uitvoering met adapter pattern strategie

## Executive Summary

This document identifies legacy code that needs migration to the new service architecture and provides a prioritized migration roadmap. The analysis reveals several areas still using the old architecture patterns, including direct database access, UI components bypassing services, and business logic outside the service layer.

### Update: Adapter Pattern Strategy
The migration strategy has been refined to use an adapter pattern approach, allowing gradual migration without breaking changes. The `ServiceAdapter` and `LegacyGenerationResult` provide backward compatibility while the UI is incrementally updated.

## Current Architecture State

### New Service Architecture (Target State)
- **Service Layer**: Modular services with clear interfaces
- **Repository Pattern**: All database access through repositories
- **Dependency Injection**: Service container for dependency management
- **Clear Separation**: UI → Services → Repository → Database

### Legacy Patterns Still in Use
1. Direct usage of `UnifiedDefinitionGenerator` (the God Object)
2. Direct database operations outside repositories
3. Business logic embedded in UI components
4. External API calls without service abstraction
5. Tight coupling between modules

## Identified Legacy Components

### 1. UI Components (High Priority)

#### Components Still Using Legacy Patterns:
- **`definition_generator_tab.py`**: Direct usage of `DefinitieChecker` with embedded business logic
- **`management_tab.py`**: Direct database access and CLI tool imports
- **`web_lookup_tab.py`**: May contain direct API calls
- **`export_tab.py`**: Likely has direct repository access
- **`quality_control_tab.py`**: Business logic embedded in UI

#### Components Partially Migrated:
- **`tabbed_interface.py`**: Uses service factory but still has direct imports
- **`orchestration_tab.py`**: Currently disabled due to compatibility issues

### 2. Database Layer (Critical Priority)

#### Issues Identified:
- **`definitie_repository.py`**: Still contains business logic that should be in services
- Direct SQL queries in multiple components
- No clear separation between data access and business rules
- Missing abstraction for complex queries

### 3. Domain Layer (Medium Priority)

#### Components Needing Service Extraction:
- **`ontologie/ontological_analyzer.py`**: Contains business logic, uses adapter pattern
- **`domain/autoriteit/`**: Authority calculation logic should be a service
- **`domain/juridisch/`**: Legal pattern matching should be a service
- **`domain/linguistisch/`**: Linguistic analysis should be a service

### 4. Integration Layer (High Priority)

#### Issues:
- **`definitie_checker.py`**: Circular dependency issues, lazy loading workarounds
- Direct instantiation of services instead of using dependency injection
- Tight coupling with `DefinitieAgent`

### 5. Document Processing (Medium Priority)

#### Current State:
- **`document_processor.py`**: Contains business logic for document analysis
- Direct file system access
- No service abstraction for document operations

### 6. Toetsregels Integration (Low Priority)

#### Current State:
- **`adapter.py`**: Provides backward compatibility
- Individual validators still use old patterns
- Not fully integrated with new validation service

## Migration Priority List

### Phase 1: Critical Foundation (Weeks 1-2)

1. **Database Repository Refactoring**
   - Extract all business logic from `definitie_repository.py`
   - Create pure data access repository
   - Move business logic to appropriate services
   - **Blockers**: None
   - **Impact**: Unblocks all other migrations

2. **Service Container Enhancement**
   - Fix circular dependency issues
   - Implement proper dependency injection for all services
   - Create service interfaces for all major components
   - **Blockers**: None
   - **Impact**: Enables proper service architecture

### Phase 2: High Priority Services (Weeks 3-4)

3. **Definition Generation Service** ✅ COMPLETED
   - ~~Complete migration from `UnifiedDefinitionGenerator`~~ ✅ Removed
   - ~~Create clean service interface~~ ✅ ServiceAdapter implemented
   - ~~Remove direct usage from all components~~ ✅ Via adapter pattern
   - **Current State**: Using ServiceAdapter for backward compatibility
   - **Next Step**: See Phase 6 for adapter removal

4. **Integration Service Refactoring**
   - Fix `definitie_checker.py` circular dependencies
   - Create proper integration service
   - Use dependency injection
   - **Blockers**: Service container enhancement
   - **Impact**: Cleaner integration patterns

### Phase 3: UI Layer Migration (Weeks 5-6)

5. **Tab Component Refactoring**
   - Migrate `definition_generator_tab.py` to use services only
   - Refactor `management_tab.py` to remove direct DB access
   - Update `export_tab.py` to use service layer
   - **Blockers**: Service implementations
   - **Impact**: Clean UI/service separation

6. **Orchestration Tab Revival**
   - Fix compatibility issues
   - Integrate with new service architecture
   - Re-enable in the interface
   - **Blockers**: All service migrations
   - **Impact**: Full feature availability

### Phase 4: Domain Services (Weeks 7-8)

7. **Ontological Analysis Service**
   - Extract business logic from `ontological_analyzer.py`
   - Create proper service interface
   - Remove adapter pattern workarounds
   - **Blockers**: Web lookup service
   - **Impact**: Cleaner domain logic

8. **Domain Logic Services**
   - Create AuthorityService from `domain/autoriteit/`
   - Create LegalPatternService from `domain/juridisch/`
   - Create LinguisticService from `domain/linguistisch/`
   - **Blockers**: None
   - **Impact**: Modular domain logic

### Phase 5: Supporting Services (Weeks 9-10)

9. **Document Processing Service**
   - Extract logic from `document_processor.py`
   - Create service interface
   - Implement proper file handling
   - **Blockers**: None
   - **Impact**: Better document handling

10. **Validation Service Enhancement**
    - Fully integrate toetsregels validators
    - Remove adapter pattern
    - Implement service-based validation
    - **Blockers**: None
    - **Impact**: Unified validation

### Phase 6: Adapter Pattern Removal (Weeks 11-12) 🆕

11. **UI Components Direct Service Integration**
    - Update all UI components to use V2 service responses directly
    - Remove `LegacyGenerationResult` dependencies
    - Update session state structure for new format
    - **Blockers**: All UI components must be migrated first
    - **Impact**: Remove technical debt

12. **ServiceAdapter Deprecation**
    - Remove `ServiceAdapter` wrapper
    - Update all imports to use services directly
    - Clean up compatibility code
    - **Blockers**: UI migration complete
    - **Impact**: Clean architecture achieved

## Adapter Pattern Trade-offs 🆕

### Advantages of Adapter Pattern Approach:
1. **Gradual Migration**
   - No big-bang refactoring needed
   - Components can be migrated one at a time
   - Reduced risk of breaking changes

2. **Backward Compatibility**
   - UI continues to work during migration
   - Session state remains compatible
   - Export/import functionality preserved

3. **Testing Benefits**
   - Can test new services with adapter
   - A/B testing possible between implementations
   - Rollback capability maintained

4. **Development Velocity**
   - Teams can work independently
   - UI updates decoupled from service changes
   - Parallel development possible

### Disadvantages:
1. **Technical Debt**
   - Temporary code that must be removed later
   - Additional complexity during transition
   - Dual format support overhead

2. **Performance Impact**
   - Extra translation layer
   - Object conversion overhead
   - Memory usage for dual representations

3. **Maintenance Burden**
   - Two patterns to maintain
   - Risk of adapter becoming permanent
   - Documentation complexity

### Mitigation Strategy:
- Set clear deadline for Phase 6 completion
- Regular reviews of adapter usage
- Gradual UI component migration
- Automated tests for both formats

## Migration Guidelines

### For Each Component Migration:

1. **Create Service Interface**
   ```python
   class IDefinitionService(Protocol):
       async def generate_definition(self, request: DefinitionRequest) -> DefinitionResponse:
           ...
   ```

2. **Extract Business Logic**
   - Move from UI/Repository to Service
   - Keep UI components thin
   - Keep repositories focused on data access

3. **Use Dependency Injection**
   ```python
   def __init__(self, service: IDefinitionService):
       self.service = service
   ```

4. **Remove Direct Dependencies**
   - No direct database access
   - No direct external API calls
   - No business logic in UI

5. **Add Proper Error Handling**
   - Service-level error handling
   - Proper error propagation
   - User-friendly error messages

## Success Metrics

- **Zero direct database access** outside repositories
- **All business logic** in service layer
- **No circular dependencies**
- **All UI components** use services only
- **100% service interface coverage**
- **Dependency injection** for all services

## Risk Mitigation

1. **Backward Compatibility**
   - Maintain adapters during migration
   - Gradual rollout with feature flags
   - Comprehensive testing

2. **Performance**
   - Monitor service call overhead
   - Implement caching where needed
   - Optimize service boundaries

3. **Data Integrity**
   - Ensure transactional consistency
   - Validate data migrations
   - Maintain audit trails

## Conclusion

The migration to the new service architecture is essential for maintainability, scalability, and feature development. The adapter pattern strategy allows for a safer, more gradual migration path than originally planned.

**Updated Timeline**: 12 weeks (added 2 weeks for Phase 6)
- Weeks 1-10: Service migration with adapter pattern
- Weeks 11-12: Adapter removal and final cleanup

The prioritized approach ensures critical components are migrated first, with each phase building on the previous one. The adapter pattern provides stability during transition while maintaining forward progress toward the target architecture.
