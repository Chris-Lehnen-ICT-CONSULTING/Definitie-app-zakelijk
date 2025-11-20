# 🏗️ DefinitieAgent Architecture Documentation

**Laatste Update**: 13-11-2025 (Architecture Simplificatie - Solo Dev Alignment)

## 📋 Overview

Deze directory bevat de architectuur documentatie voor DefinitieAgent, een **solo developer tool** voor Nederlandse juridische definitie generatie met AI (GPT-4) en 45 validatieregels.

### ⚠️ Reality Check

DefinitieAgent is:
- ✅ **Solo developer tool** - 1 ontwikkelaar, 1 gebruiker
- ✅ **Local workstation deployment** - `streamlit run src/main.py`
- ✅ **Modular monolith** - ServiceContainer DI + Clean Architecture
- ✅ **NIET in productie** - Development/experimentation tool

DefinitieAgent is NIET:
- ❌ Enterprise platform
- ❌ Multi-user systeem
- ❌ Cloud native applicatie
- ❌ Microservices architectuur

## 🎯 Hoofddocument

| Document | Doel | Status | Laatste Update |
|----------|------|--------|----------------|
| **[ARCHITECTURE.md](./ARCHITECTURE.md)** | Solo dev/solo user architectuur overzicht | ✅ Actief (v1.0) | 13-11-2025 |

**Inhoud**:
- Architectural Principles (solo dev optimized)
- Technology Stack (Streamlit, SQLite, Python)
- Core Patterns (ServiceContainer DI, Clean Architecture, RuleCache)
- Performance Optimizations (77% sneller via caching)
- Explicitly Rejected Patterns (microservices, Kubernetes, etc.)

## 📁 Directory Structuur

```
docs/architectuur/
├── ARCHITECTURE.md          # Hoofddocument (solo dev reality)
├── README.md               # Dit bestand
│
├── contracts/              # API contracts (ValidationResult, etc.)
├── decisions/              # Architecture Decision Records (ADRs)
├── diagrams/               # Mermaid/PlantUML diagrams
├── templates/              # Architecture templates (EA/SA/TA templates)
│
└── [feature-specific docs] # Cache monitoring, validation, etc.
    ├── cache-monitoring-*.md
    ├── validation_orchestrator_v2.md
    └── ...
```

## 🚀 Quick Start

**Voor Developers:**
1. Start met **[ARCHITECTURE.md](./ARCHITECTURE.md)** voor architectuur principes
2. Check **Core Patterns** (§3) voor ServiceContainer DI, Clean Architecture
3. Bekijk **Performance Optimizations** (§7) voor RuleCache, singleton patterns
4. Lees **Explicitly Rejected Patterns** (§10) om enterprise overkill te vermijden

**Voor AI Assistants (Claude Code):**
- ARCHITECTURE.md beschrijft ACTUELE deployment (`streamlit run src/main.py`)
- Focus op patterns die WERKEN (modular monolith, SQLite, DI)
- Vermijd enterprise patterns (microservices, Kubernetes, cloud deployment)

## 📊 Architecture Highlights

### Technology Stack (Working)
- **Language**: Python 3.11+
- **UI**: Streamlit (adequate voor solo user)
- **Database**: SQLite (`data/definities.db` - perfect voor single-user)
- **AI**: OpenAI GPT-4
- **Testing**: pytest
- **Linting**: Ruff + Black

### Core Patterns
1. **ServiceContainer DI** - Singleton met lazy initialization (`src/services/container.py`)
2. **Clean Architecture** - UI → Services → Domain → Data layers
3. **RuleCache** - Bulk loading van 45 validation rules (77% sneller)
4. **SessionStateManager** - Single access point voor Streamlit state
5. **ConfigManager** - Component-specific AI configuration

### Performance Wins
- **US-202**: RuleCache optimization (77% sneller, 81% minder memory)
- **Singleton Container**: 1x initialization i.p.v. 2x (81% minder memory)
- **Token optimization**: Prompt deduplication voor GPT-4 cost reduction

## 🗂️ Gearchiveerde Documentatie

**13-11-2025**: Enterprise Fantasy Documenten Gearchiveerd

| Document | Nieuw Pad | Reden |
|----------|-----------|-------|
| ~~ENTERPRISE_ARCHITECTURE.md~~ | `/docs/archief/2025-11-enterprise-architecture-docs/` | Enterprise fantasy |
| ~~SOLUTION_ARCHITECTURE.md~~ | `/docs/archief/2025-11-enterprise-architecture-docs/` | Microservices TO-BE overkill |
| ~~TECHNICAL_ARCHITECTURE.md~~ | `/docs/archief/2025-11-enterprise-architecture-docs/` | Kubernetes/cloud native overkill |

**Waarom gearchiveerd?**
- Beschreven fictieve enterprise platform (€1.5M budget, 100+ users, microservices)
- Niet aligned met solo dev/solo user realiteit
- CLAUDE.md zegt expliciet: "single-user applicatie, NIET in productie"
- 70% enterprise overkill (Kubernetes, Terraform, compliance matrices)
- 30% goede patterns overgenomen in ARCHITECTURE.md

**Zie**: `docs/archief/2025-11-enterprise-architecture-docs/README.md` voor details

## 🔗 Gerelateerde Documentatie

- **Development Instructions**: `/CLAUDE.md` (root) - Claude Code instructies
- **Canonical Locations**: `/docs/guidelines/CANONICAL_LOCATIONS.md`
- **Streamlit Patterns**: `/docs/guidelines/STREAMLIT_PATTERNS.md`
- **Vibe Coding**: `/docs/methodologies/vibe-coding/PATTERNS.md`

## 📝 Document Conventies

- **Canonical docs**: `ARCHITECTURE.md` (solo source of truth)
- **Feature docs**: `feature-name-architecture.md` (kleine letters)
- **ADRs**: `docs/architectuur/decisions/ADR-XXX-titel.md`
- **Diagrams**: Mermaid (.mmd) of PlantUML (.puml) in `diagrams/`

## 🛠️ Voor Documentatie Schrijvers

### Richtlijnen
- **Eerlijkheid**: Documenteer REALITEIT, geen ambities
- **Solo dev focus**: Simpliciteit is feature, niet limitation
- **CLAUDE.md alignment**: Check consistency met development instructies
- **Geen enterprise fantasy**: Geen fictieve budgets/stakeholders/roadmaps

### Validation
- **Alignment check**: Consistent met CLAUDE.md principes?
- **Reality check**: Beschrijft dit de actuele deployment?
- **Simplicity check**: Voegt dit waarde toe of is het overhead?

## 🚧 Onderhoud

| Document | Review Cyclus | Eigenaar |
|----------|---------------|-------|
| ARCHITECTURE.md | Bij significante wijzigingen | Solo Developer |
| Feature docs | Bij feature implementatie | Solo Developer |
| ADRs | Bij architectuur beslissingen | Solo Developer |

**Update trigger**: Significante refactors, nieuwe core patterns, technology wijzigingen

---

## 📚 Lessons Learned (13-11-2025)

**Enterprise Roleplaying Vermijden**:
- Architectuur documenten moeten REALITEIT reflecteren, niet ambities
- Solo dev/solo user is FEATURE (simpliciteit), niet limitation
- Microservices/Kubernetes zijn overkill, modular monolith is juiste keuze
- CLAUDE.md development instructies zijn leidend voor architectuur

**Simpliciteit Principe**:
```bash
# Dit is "deployment"
streamlit run src/main.py

# Dit is "infrastructure"
data/definities.db  # SQLite file

# Dit is "monitoring"
tail -f logs/app.log
```

**Alignment Checklist**:
- ✅ Consistent met solo dev/solo user realiteit?
- ✅ Aligned met CLAUDE.md principes?
- ✅ Focus op patterns die WERKEN?
- ✅ Vermijdt enterprise overkill?
- ✅ Eerlijk over deployment (`streamlit run`, geen Kubernetes)?

Voor vragen: Check ARCHITECTURE.md of CLAUDE.md
