# Legacy Code Reference

Deze directory bevat de oorspronkelijke werkende legacy code die teruggehaald is uit git history voor referentie tijdens de "Features First" implementatie.

## Herstelde Files

### 1. centrale_module_definitie_kwaliteit_legacy.py
- **Bron**: Git commit 9243eb2
- **Grootte**: 1,088 regels
- **Inhoud**: Complete werkende UI implementatie met alle tabs
- **Belangrijkste features**:
  - ✅ Definitie Generator tab
  - ✅ Quality Control tab  
  - ✅ Expert Review tab
  - ✅ Management tab
  - ✅ Orchestration tab
  - ✅ Session state management
  - ✅ Export functionaliteit

### 2. core_legacy.py
- **Bron**: Git commit 61f728c
- **Grootte**: 2,025 regels
- **Inhoud**: Complete AI toetsing implementatie
- **Belangrijkste features**:
  - ✅ Alle 45+ toetsregels
  - ✅ Validatie logica
  - ✅ Score berekening
  - ✅ Feedback generatie

## Gebruik

Deze files dienen als **referentie** voor het implementeren van ontbrekende features in de nieuwe modulaire architectuur:

1. **UI Tabs**: Kopieer tab implementaties naar `src/ui/components/`
2. **Validatie**: Gebruik core.py om te zien hoe toetsregels werkten
3. **Session State**: Check hoe state management werkte
4. **Workflows**: Zie complete user journeys

## BELANGRIJK

- Deze files zijn **NIET bedoeld om direct te runnen**
- Ze dienen alleen als **referentie/documentatie**
- Kopieer relevante delen naar de nieuwe modules
- Test na elke kopie of het werkt in nieuwe context

## Migratie Status

- [ ] Definitie Generator tab → Gedeeltelijk gemigreerd
- [ ] Quality Control tab → Basis UI alleen
- [ ] Expert Review tab → Niet geïmplementeerd
- [ ] Management tab → Niet geïmplementeerd
- [ ] Orchestration tab → Gedeeltelijk werkend
- [ ] Export functionaliteit → Niet gemigreerd
- [ ] Session state → Inconsistent gebruikt