# 📚 Documentatie Reorganisatie Plan - DefinitieAgent

## 🎯 Doel
Creëer een schone, onderhoudbare documentatie structuur voor het V2-only DefinitieAgent project.

## 📊 Huidige Situatie
- **268** markdown files in docs/
- **16+** verschillende archief directories
- **47%** documenten in archief status
- **Veel** V1 legacy referenties
- **Chaos** door meerdere reorganisatie pogingen

## ✅ ESSENTIËLE DOCUMENTATIE (Behouden & Actualiseren)

### Root Directory (5 files max)
```
docs/
├── README.md                        # Project overview & getting started
├── ARCHITECTURE.md                  # Current V2 architecture overview
├── REQUIREMENTS.md                  # Actuele requirements & features
├── DEPLOYMENT.md                    # Deployment & operations guide
└── CONTRIBUTING.md                  # Development guidelines
```

### Core Directories
```
docs/
├── architecture/                    # Technische architectuur
│   ├── adr/                        # Architecture Decision Records
│   │   ├── ADR-001-v2-async.md    # V2 async architecture
│   │   ├── ADR-002-orchestrator.md # Orchestrator pattern
│   │   └── ADR-003-services.md    # Service layer design
│   ├── diagrams/                   # Architectuur diagrammen
│   ├── services/                   # Service documentatie
│   └── components/                 # Component documentatie
│
├── operations/                     # Operationele documentatie
│   ├── deployment/                # Deployment guides
│   ├── monitoring/                # Monitoring & logging
│   ├── security/                  # Security guidelines
│   └── troubleshooting/           # Common issues & fixes
│
├── development/                    # Development documentatie
│   ├── setup/                     # Development setup
│   ├── testing/                   # Test strategy & guides
│   ├── modules/                   # Module documentatie
│   │   ├── toetsregels/          # Validatie regels
│   │   ├── prompts/              # Prompt modules
│   │   └── orchestration/        # Orchestration docs
│   └── standards/                 # Coding standards
│       ├── coding-standards.md
│       ├── tech-stack.md
│       └── source-tree.md
│
└── api/                           # API documentatie
    ├── interfaces/                # Interface definitions
    ├── endpoints/                 # API endpoints
    └── examples/                  # Usage examples
```

## 🗄️ ARCHIEF STRATEGIE (Één Consolidatie)

### Alles naar ÉÉN archief directory:
```
docs/
└── ARCHIEF_2025/                  # Alle legacy/oude docs
    ├── README.md                  # Index van gearchiveerde content
    ├── v1-legacy/                 # V1 documentatie
    ├── migration-history/         # Migratie documenten
    ├── old-architectures/         # Oude architectuur versies
    ├── historical-decisions/      # Oude beslissingen
    └── bulk-archives/             # Bestaande bulk archives
```

## 🚫 TE VERWIJDEREN/ARCHIVEREN

### Verouderd door V1 Eliminatie:
- `LEGACY_CODE_MIGRATION_ROADMAP.md`
- `V1_ELIMINATION_ROLLBACK.md`
- Alle UnifiedDefinitionGenerator referenties
- Legacy service documentatie

### Dubbel/Redundant:
- Multiple archief directories
- Duplicate ADRs in verschillende locaties
- Oude roadmaps en plannen
- Test coverage rapporten pre-V2

### Tijdelijke/Debug Files:
- `orchestrator-async-bug.md` (gefixed)
- `PROMPT_GENERATION_FIXES.md` (gefixed)
- Debug logs en analyses

## 🎬 ACTIEPLAN

### Week 1: Voorbereiding
1. **Backup** maken van huidige docs/
2. **Inventarisatie** van actieve referenties in code
3. **Identificatie** van echt gebruikte documentatie

### Week 2: Reorganisatie
1. **Creëer** nieuwe directory structuur
2. **Migreer** essentiële documentatie
3. **Update** alle code referenties naar nieuwe locaties
4. **Consolideer** alle archief materiaal

### Week 3: Cleanup
1. **Verwijder** lege directories
2. **Update** README met nieuwe structuur
3. **Valideer** alle documentatie links
4. **Commit** nieuwe structuur

## 📈 Verwachte Resultaten

### Voor:
- 268 markdown files
- 16+ archief directories
- Onduidelijke structuur
- V1/V2 mix

### Na:
- ~50-70 actieve documenten
- 1 archief directory
- Heldere V2-only structuur
- Makkelijk te navigeren

## ⚠️ Belangrijke Aandachtspunten

1. **CLAUDE.md** moet in root blijven (AI instructies)
2. **BMad documenten** blijven in .bmad-core/
3. **Test fixtures** niet archiveren (tests/fixtures/)
4. **Config files** niet verplaatsen (pyproject.toml, etc.)

## 🔄 Onderhoud

### Maandelijks:
- Review nieuwe documenten
- Archiveer verouderde content
- Update index files

### Per Release:
- Update architecture docs
- Archive oude ADRs
- Update deployment guides

---

*Dit plan creëert een schone, onderhoudbare documentatie structuur die focust op de huidige V2 architectuur terwijl alle historische informatie veilig gearchiveerd blijft.*
