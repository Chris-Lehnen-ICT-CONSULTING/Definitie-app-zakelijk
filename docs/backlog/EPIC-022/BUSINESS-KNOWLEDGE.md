---
id: BUSINESS-KNOWLEDGE-022
titel: Business Kennis uit External Sources Implementatie
type: knowledge-document
epic: EPIC-022
status: Preserved
aangemaakt: 2025-09-29
reden: Code wordt verwijderd maar business kennis moet behouden blijven
canonical: true
---

# Business Kennis uit External Sources Implementatie

Dit document bewaart belangrijke business kennis uit de verwijderde External Sources implementatie voor toekomstige referentie.

## 1. Status Mapping Logica (KRITIEK)

Bij het importeren van externe definities moet de status correct worden gemapped:

```python
STATUS_MAPPING = {
    "draft": DefinitieStatus.DRAFT,
    "concept": DefinitieStatus.DRAFT,
    "review": DefinitieStatus.REVIEW,
    "pending": DefinitieStatus.REVIEW,
    "approved": DefinitieStatus.ESTABLISHED,
    "established": DefinitieStatus.ESTABLISHED,
    "final": DefinitieStatus.ESTABLISHED,
    "archived": DefinitieStatus.ARCHIVED,
    "deprecated": DefinitieStatus.ARCHIVED,
}
# Default: Als status onbekend → DRAFT
```

**Business Rationale**:
- Externe systemen gebruiken verschillende terminologie
- Voorkomt dat goedgekeurde externe definities als draft worden geïmporteerd
- Behoudt workflow integriteit

## 2. Import Validatie Regels

### Duplicate Prevention
- **Regel**: Check altijd of begrip al bestaat voordat import
- **Optie**: Gebruiker kan kiezen voor "overwrite_existing"
- **Default**: NIET overschrijven (veilige default)

### Metadata Preservatie
Bij import ALTIJD bewaren:
- `source_reference`: "{source_id}:{external_id}"
- `imported_from`: Naam van de bron
- `import_timestamp`: Wanneer geïmporteerd
- **Reden**: Audit trail, provenance, compliance

## 3. Bulk Import Strategie

### Error Handling
- **Principe**: Individual failure mag bulk import NIET stoppen
- **Implementatie**:
  - Verzamel errors in lijst
  - Ga door met volgende items
  - Rapporteer aan einde: X van Y succesvol
- **UI Feedback**: Progress bar met real-time status updates

### Performance Limits
- **Max bulk import**: 100 items per keer
- **Default**: 10 items
- **Timeout per item**: 30 seconden
- **Retry count**: 3 pogingen bij failure

## 4. Configuration Management

### Export Format
```json
{
  "export_timestamp": "ISO-8601 datetime",
  "sources": [
    {
      "source_id": "unique_id",
      "source_name": "human_readable_name",
      "source_type": "database|rest_api|file_system|web_service|graph_api",
      "connection_string": "...",
      "timeout": 30,
      "retry_count": 3
    }
  ]
}
```

### Security Considerations
- **NOOIT** exporteer credentials (api_key, password)
- **ALTIJD** vraag om re-authenticatie bij import
- **Log** alle import/export acties voor audit

## 5. Source Type Hierarchy

```
ExternalSourceType:
├── DATABASE      → Voor directe database connecties
├── REST_API      → Voor RESTful services
├── FILE_SYSTEM   → Voor lokale/netwerk bestanden
├── WEB_SERVICE   → Voor SOAP/XML services
└── GRAPH_API     → Voor GraphQL endpoints
```

**Prioritering**: File system eerst (laagste complexiteit), dan REST, dan database

## 6. Import History Tracking

Elk import event moet vastleggen:
```python
{
    "timestamp": "ISO-8601",
    "source_id": "bron identificatie",
    "begrip": "geïmporteerde term (bij single)",
    "imported_count": aantal_succesvol,
    "total_attempted": aantal_geprobeerd,
    "errors": ["lijst", "van", "error", "messages"],
    "status": "success|partial|failed"
}
```

**Retention**: Laatste 50 import events bewaren in session

## 7. Adapter Pattern Requirements

Elke externe bron adapter MOET implementeren:
1. `connect()` - Verbinding maken
2. `disconnect()` - Verbinding verbreken
3. `test_connection()` - Connectiviteit testen
4. `search_definitions()` - Zoeken met filters
5. `get_definition()` - Specifieke definitie ophalen
6. `create_definition()` - Nieuwe definitie aanmaken
7. `update_definition()` - Bestaande definitie updaten
8. `delete_definition()` - Definitie verwijderen
9. `get_source_info()` - Metadata over de bron

## 8. Mock Data als Business Voorbeelden

De mock adapter bevatte deze representatieve juridische definities:
1. **Overeenkomst** - type - Burgerlijk Wetboek
2. **Rechtspersoon** - type - Handelsrecht
3. **Dwangsom** - proces - Bestuursrecht
4. **Hoger beroep** - proces - Procesrecht
5. **Eigendom** - type - Goederenrecht
6. **Aansprakelijkheid** - resultaat - Verbintenissenrecht
7. **Vonnis** - resultaat - Procesrecht
8. **Dagvaarding** - proces - Procesrecht
9. **Testament** - type - Erfrecht
10. **Vruchtgebruik** - type - Goederenrecht

Deze voorbeelden tonen de verwachte categorieën en contexten.

## 9. Beslissingslogica voor Toekomstige Implementatie

### Wanneer WEL External Sources implementeren:
- Multiple gebruikers delen definities
- Integratie met juridische databases (Rechtspraak.nl, EUR-Lex)
- Synchronisatie met organisatie-brede terminologie
- Import van legacy systemen

### Wanneer NIET nodig:
- Single-user applicatie (huidige situatie)
- Alleen web lookup voor verrijking
- Eenvoudige file import/export voldoet

## 10. Lessons Learned

1. **Over-engineering**: Adapter pattern was te complex voor huidige requirements
2. **Feature overlap**: Export tab dekt 95% van de use cases
3. **Mock complexity**: Mock adapter bevatte meer code dan werkende implementatie
4. **UI cognitive load**: Extra tab zonder duidelijke meerwaarde verwart gebruikers
5. **Maintenance burden**: 1291 regels code voor hypothetische toekomst

## Bewaar Deze Kennis Voor:

- Als organisatie groeit naar multi-user
- Bij integratie met juridische databases
- Voor enterprise deployment
- Als API integratie requirement wordt

---
*Deze business kennis is geëxtraheerd uit de verwijderde implementatie om toekomstige herimplementatie te vergemakkelijken zonder het verlies van opgedane inzichten.*