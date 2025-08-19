# Ongebruikte Python Bestanden Rapport

**Datum**: 2025-08-19
**Totaal Python bestanden in src/**: 222
**Gebruikt**: 62 (28%)
**Ongebruikt**: 160 (72%)

## Samenvatting

De meerderheid van de Python bestanden in de `src/` directory wordt niet gebruikt door de applicatie. Dit duidt op significante technische schuld en legacy code.

## Grootste Ongebruikte Directories

### 1. Toetsregels Duplicaten (91 bestanden)
- `src/toetsregels/regels/`: 45 bestanden (ARAI-01.py t/m INT-05.py)
- `src/toetsregels/validators/`: 46 bestanden (ARAI01.py t/m INT_05.py)

**Opmerking**: Dit zijn waarschijnlijk oude implementaties van validatieregels die zijn vervangen door het nieuwe JSON-based systeem in `src/ai_toetsing/`.

### 2. Hybrid Context (4 bestanden)
- `context_fusion.py`
- `smart_source_selector.py`
- `test_hybrid_context.py`
- `__init__.py`

**Opmerking**: Deze module lijkt een onafgemaakte feature voor context verrijking.

### 3. Services (3 bestanden)
- `ab_testing_framework.py`
- `web_lookup/sru_service.py`
- `web_lookup/wikipedia_service.py`

**Opmerking**: Experimentele features die nooit zijn geïntegreerd.

### 4. Tools (3 bestanden)
- `definitie_manager.py`
- `setup_database.py`

**Opmerking**: CLI tools die waarschijnlijk voor development/setup werden gebruikt.

### 5. UI Components (6 bestanden)
- `async_progress.py`
- `cache_manager.py`
- `components.py`
- `orchestration_tab.py`

**Opmerking**: Ongebruikte UI componenten, mogelijk van niet-geïmplementeerde features.

## Aanbevelingen

### Onmiddellijke Acties
1. **Verwijder toetsregels duplicaten** (91 bestanden)
   - Bevestig dat `src/ai_toetsing/` het actieve systeem is
   - Archive of verwijder `src/toetsregels/regels/` en `src/toetsregels/validators/`

2. **Archive experimentele features**
   - Verplaats `src/hybrid_context/` naar `docs/archief/`
   - Verplaats ongebruikte services naar archive

### Vervolgstappen
1. **Code audit**: Review elk ongebruikt bestand om te bepalen of het:
   - Veilig verwijderd kan worden
   - Gearchiveerd moet worden voor toekomstige referentie
   - Alsnog geïmplementeerd moet worden

2. **Documenteer beslissingen**: Voor elk verwijderd/gearchiveerd bestand:
   - Waarom het niet gebruikt werd
   - Of de functionaliteit elders is geïmplementeerd
   - Of het in de toekomst nog nodig kan zijn

## Impact

Door het opruimen van deze ongebruikte bestanden:
- **Verminderde complexiteit**: Van 222 naar ~62 bestanden (-72%)
- **Betere onderhoudbaarheid**: Ontwikkelaars hoeven niet door legacy code te zoeken
- **Snellere ontwikkeling**: Minder verwarring over welke code actief is
- **Kleinere codebase**: Makkelijker te begrijpen en te testen

## Volgende Stappen

1. Review dit rapport met het team
2. Maak een backup van de huidige staat
3. Begin met het verwijderen van de toetsregels duplicaten
4. Test grondig na elke verwijdering
5. Update de documentatie
