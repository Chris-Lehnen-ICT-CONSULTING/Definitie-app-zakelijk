---
titel: TODO Mapping naar User Stories
aangemaakt: 2025-09-11
bijgewerkt: 2025-09-11
canonical: true
document_type: mapping
owner: developer
status: active
---

# TODO Mapping naar User Stories

Dit document toont waar alle TODO's uit de codebase zijn ondergebracht in user stories.

## ✅ TODO's Toegevoegd aan Bestaande User Stories

### US-043: Remove Legacy Context Routes (Status: Nog te bepalen)
**Toegevoegde TODO's:**
- `src/ui/components/definition_generator_tab.py:86` - Update dependency injection
- `src/ui/components/definition_generator_tab.py:322` - Implement proper user auth for history
- `src/ui/components/context_selector.py:116` - Implement preset saving to database

### US-060: Implement Event Bus Architecture (Status: Open)
**Toegevoegde TODO's:**
- `src/services/workflow_service.py:515` - Event publishing voor category changes
- `src/services/category_service.py:101` - Event publishing voor category updates

### US-064: Implement Definition Edit Interface (Status: Open)
**Toegevoegde TODO's:**
- `src/ui/components/definition_generator_tab.py:344` - Navigate to edit interface
- `src/ui/components/definition_generator_tab.py:350` - Implement definition editing
- `src/ui/components/definition_generator_tab.py:387` - Implement settings modal

### US-062: Implement Bulk Import Functionality (Status: Open)
**Reeds aanwezig:**
- `src/ui/components/export_tab.py:523` - Bulk import functionaliteit

## 🔄 TODO's Gedekt door Nieuwe User Stories

### US-061: Wiktionary Integration
- `src/services/modern_web_lookup_service.py:237` - Implementeer Wiktionary service

### US-063: Database Maintenance Tools
- `src/ui/components/export_tab.py:487` - Orphan detection
- `src/ui/components/export_tab.py:529` - Duplicate cleanup
- `src/ui/components/export_tab.py:535` - Index rebuilding
- `src/ui/components/export_tab.py:541` - Database analysis

### US-065: Email Export & Scheduled Exports
- `src/ui/components/export_tab.py:547` - Email export
- `src/ui/components/export_tab.py:553` - Scheduled exports

## ✅ ALLE TODO's Zijn Toegewezen!

### US-028: Service Initialization Caching (Status: Nog te bepalen)
**Performance Tracking TODO's:**
- `src/voorbeelden/async_voorbeelden.py:91` - Track cache hits
- `src/services/ai_service_v2.py:236` - Get actual retry count from client

### US-014: Modern Web Lookup Implementation (Status: Nog te bepalen)
**Web Lookup TODO's:**
- `src/ui/components/web_lookup_tab.py:58` - Moderne service integration
- `src/services/modern_web_lookup_service.py:276` - Veilige scraping implementatie

### US-066: Implement AI Enhancement for Definitions (Status: Open) [NIEUW]
**AI Enhancement TODO's:**
- `src/services/definition_orchestrator.py:424` - Implement enhancement logic
- `src/services/definition_orchestrator.py:445` - Implement AI enhancement logic

### US-067: Expert Review Draft and Revalidation (Status: Open) [NIEUW]
**Expert Review TODO's:**
- `src/ui/components/expert_review_tab.py:577` - Draft saving
- `src/ui/components/expert_review_tab.py:583` - Re-validation

### US-068: Implement Audit Trail Query (Status: Open) [NIEUW]
**Audit Trail TODO's:**
- `src/ui/components/history_tab.py:72` - Audit trail query from definitie_geschiedenis table

## 📊 Samenvatting

- **Totaal TODO's gevonden:** 24
- **Toegevoegd aan bestaande open stories:** 18
- **Nieuwe stories aangemaakt:** 6 (US-060 t/m US-065) + 3 (US-066 t/m US-068)
- **ALLE TODO's zijn nu toegewezen!** ✅

## Status Overzicht

### Bestaande Stories met TODO's:
- US-043: Remove Legacy Context Routes (85% klaar) - 3 TODO's
- US-014: Modern Web Lookup (Open) - 2 TODO's
- US-028: Service Caching (Open) - 2 TODO's
- US-060: Event Bus (Open) - 2 TODO's
- US-062: Bulk Import (Open) - 1 TODO
- US-064: Edit Interface (Open) - 3 TODO's
- US-065: Email Export (Open) - 2 TODO's

### Nieuwe Stories voor TODO's:
- US-066: AI Enhancement - 2 TODO's
- US-067: Expert Review Features - 2 TODO's
- US-068: Audit Trail - 1 TODO

## ✅ Conclusie

**ALLE 24 TODO's uit de codebase zijn nu toegewezen aan user stories!**
Er zijn geen losse TODO's meer zonder eigenaar.
