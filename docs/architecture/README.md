# Architecture Documentation

Deze folder bevat alle architectuur-gerelateerde documentatie voor het DefinitieAgent project.

## 📁 Structuur

- **[decisions/](decisions/)** - Architecture Decision Records (ADRs)
- **[../architecture.md](../architecture.md)** - Hoofddocument met systeem architectuur
- **[../architecture-interactive.html](../architecture-interactive.html)** - Interactief architectuur document met diagrammen

## 🏗️ Architectuur Overzicht

DefinitieAgent volgt een **Modular Monolith** architectuur met:

- **Presentation Layer**: Streamlit UI (10 tabs)
- **Service Layer**: UnifiedDefinitionService (Singleton)
- **Domain Services**: AI, Validation, Document Processing
- **Data Layer**: SQLAlchemy + SQLite/PostgreSQL

## 🔑 Key Decisions

1. **Monolithische Structuur** - Simpliciteit voor klein team
2. **Features First** - Gebruikerswaarde boven technische perfectie
3. **Legacy als Spec** - Bestaande functionaliteit behouden
4. **Incrementele Migratie** - Strangler Fig pattern

## 📊 Architectuur Principes

- **Clean Architecture**: Dependencies wijzen naar binnen
- **Domain-Driven Design**: Business logic centraal
- **SOLID Principles**: Modulaire, testbare code
- **Feature Folders**: Organisatie per functionaliteit

## 🚀 Migration Strategy

Actieve migratie van legacy naar modern:

```
Legacy System → Facade Layer → Modern Services → Clean Architecture
```

## 📚 Gerelateerde Documenten

- [Technical Docs](../technical/) - API, Database, Validation
- [Setup Guide](../setup/) - Development environment
- [Roadmap](../roadmap.md) - 6-week implementation plan

## 🔗 Quick Links

- [Huidige Architectuur](../architecture.md#system-architecture)
- [Gewenste Architectuur](../architecture-interactive.html)
- [ADR Index](decisions/README.md)
- [Migration Plan](decisions/ADR-004-incrementele-migratie-strategie.md)