# Deprecated Web Lookup Modules

Deze directory bevat legacy web lookup modules die zijn vervangen door de moderne service architectuur.

## Status: DEPRECATED ⚠️

**Deze modules worden niet meer actief onderhouden en zullen in een toekomstige release worden verwijderd.**

## Migratie

Alle functionaliteit is gemigreerd naar:
- `services/modern_web_lookup_service.py` - Moderne web lookup implementatie
- `services/unified_definition_generator.py` - Geïntegreerde definitie generatie

## Structuur

```
deprecated/
├── docs/                    # Legacy documentatie
├── legacy_modules/          # Legacy web_lookup module code
│   └── web_lookup_legacy/
└── services/               # Transitional service wrappers
```

## Verwijdering Planning

Deze modules zullen worden verwijderd zodra:
1. Alle dependent modules zijn gemigreerd
2. Integration tests zijn bijgewerkt
3. Een grace period van 2 releases is verstreken

Voor vragen over de migratie, zie `docs/active/architecture/complete-architecture-diagram.md`.