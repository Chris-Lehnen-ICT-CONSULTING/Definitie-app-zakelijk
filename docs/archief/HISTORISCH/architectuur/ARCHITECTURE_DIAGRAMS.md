# DefinitieAgent 2.0 - Architectuur Diagrammen

**Versie:** 2.2 - UI Flow & Error Handling Enhancement  
**Laatste Update:** 2025-07-14  
**Features:** Document Upload, Hybrid Context Verrijking, Web Lookup Integratie

Deze architectuur diagrammen tonen de complete structuur van DefinitieAgent 2.0 inclusief de nieuwe document upload functionaliteit en hybride context verrijking die web lookup combineert met document processing voor optimale definitie generatie.

## 1. Component Overzicht Diagram

```mermaid
graph TB
    subgraph "🖥️ User Interface Layer"
        UI[Streamlit UI]
        TI[Tabbed Interface]
        CTX[Context Selector]
        DGT[Definition Generator Tab]
        ERT[Expert Review Tab]
        HT[History Tab]
        ET[Export Tab]
    end

    subgraph "🧠 Business Logic Layer"
        DA[Definitie Agent]
        DG[Definitie Generator]
        DV[Definitie Validator]
        DC[Definitie Checker]
        AI[AI Toetser]
        VB[Voorbeelden Generator]
        DP[Document Processor]
    end

    subgraph "🔧 Service Layer"
        DS[Definition Service]
        AS[Async Service]
        WL[Web Lookup Service]
        EX[Export Service]
        DE[Document Extractor]
    end

    subgraph "💾 Data Layer"
        DR[Definitie Repository]
        DB[(SQLite Database)]
        CH[Cache Manager]
        FS[(File System)]
        DM[Document Metadata Store]
    end

    subgraph "🌐 External APIs"
        GPT[OpenAI GPT API]
        WP[Wikipedia API]
        LD[Legal Databases]
        WK[Wiktionary API]
    end

    subgraph "⚙️ Infrastructure"
        CF[Config Manager]
        RL[Rate Limiter]
        RES[Resilience Layer]
        LOG[Logging System]
    end

    %% User Interface connections
    UI --> TI
    TI --> CTX
    TI --> DGT
    TI --> ERT
    TI --> HT
    TI --> ET

    %% UI to Business Logic
    DGT --> DC
    DGT --> DA
    DGT --> DP
    ERT --> DR
    HT --> DR
    ET --> EX

    %% Business Logic connections
    DC --> DR
    DA --> DG
    DA --> DV
    DG --> AI
    DG --> VB
    DG --> DP
    AI --> CF
    DP --> DE

    %% Service Layer connections
    DA --> DS
    DG --> AS
    VB --> WL
    DP --> WL
    ET --> EX
    DE --> FS

    %% Data Layer connections
    DS --> DR
    DR --> DB
    AS --> CH
    CH --> FS
    DP --> DM
    DM --> FS

    %% External API connections
    DG --> GPT
    WL --> WP
    WL --> LD
    WL --> WK

    %% Infrastructure connections
    AS --> RL
    AS --> RES
    DS --> LOG
    CF --> LOG

    style UI fill:#e1f5fe
    style DA fill:#f3e5f5
    style DR fill:#e8f5e8
    style GPT fill:#fff3e0
    style CF fill:#fce4ec
```

## 2. Data Flow Diagram - Definitie Generatie met Document Upload

```mermaid
sequenceDiagram
    participant U as User
    participant UI as Streamlit UI
    participant DP as Document Processor
    participant WL as Web Lookup
    participant DC as Definitie Checker
    participant DR as Repository
    participant DA as Definitie Agent
    participant DG as Definitie Generator
    participant GPT as OpenAI API
    participant DV as Definitie Validator
    participant CH as Cache
    participant DB as Database
    participant DM as Document Metadata

    U->>UI: Upload documenten + begrip + context
    
    opt Document Processing
        UI->>DP: process_uploaded_files()
        DP->>DM: extract_text_and_metadata()
        DM-->>DP: extracted_content
        DP->>DP: analyze_keywords_concepts()
        DP->>WL: extract_legal_references()
        WL-->>DP: legal_refs
        DP-->>UI: processed_documents
    end
    
    UI->>DC: generate_with_check()
    
    DC->>DR: check_duplicates()
    DR->>DB: SELECT similar definitions
    DB-->>DR: existing_records
    DR-->>DC: duplicate_check_result
    
    alt No Duplicates Found
        DC->>DA: start_generation()
        
        par Hybrid Context Enrichment
            DA->>DP: get_aggregated_context()
            DP-->>DA: document_context
        and
            DA->>WL: zoek_definitie_combinatie()
            WL-->>DA: web_context
        end
        
        DA->>DG: generate_definition(hybrid_context)
        
        DG->>CH: check_cache()
        CH-->>DG: cache_miss
        
        DG->>GPT: completion_request(enriched_prompt)
        GPT-->>DG: ai_response
        
        DG->>CH: store_result()
        DG-->>DA: generated_definition
        
        DA->>DV: validate_quality()
        DV-->>DA: validation_score
        
        alt Quality Score < Threshold
            DA->>DG: regenerate_with_feedback()
            Note over DA,DG: Iterative improvement loop
        else Quality Score OK
            DA->>DR: save_definition(with_sources)
            DR->>DB: INSERT new definition
            DB-->>DR: saved_record
            DR-->>DA: success
        end
        
        DA-->>DC: generation_result
    else Duplicates Found
        DC-->>UI: duplicate_warning
    end
    
    DC-->>UI: final_result(with_document_attribution)
    UI-->>U: Display enhanced result
```

## 3. API Structuur Diagram

```mermaid
graph LR
    subgraph "🎯 Application APIs"
        subgraph "Core Services"
            DS[Definition Service]
            AS[Async Service]
            VS[Validation Service]
        end
        
        subgraph "Data Services"
            DR[Repository API]
            CM[Cache Manager]
            IM[Import/Export]
        end
        
        subgraph "Integration Services"
            WL[Web Lookup]
            EG[Example Generator]
            AI[AI Integration]
            DP[Document Processing]
        end
    end

    subgraph "🌐 External APIs"
        subgraph "AI Services"
            GPT[OpenAI GPT-4]
            EMB[OpenAI Embeddings]
        end
        
        subgraph "Reference Data"
            WP[Wikipedia API]
            WN[Wetten.nl API]
            ON[Overheid.nl API]
            WK[Wiktionary API]
        end
    end

    subgraph "📊 API Methods"
        subgraph "Definition Operations"
            GEN[generate_definition]
            VAL[validate_definition]
            CHK[check_duplicates]
            SAV[save_definition]
            DOC[process_document]
            CTX[get_aggregated_context]
        end
        
        subgraph "Data Operations"
            GET[get_definitions]
            UPD[update_definition]
            DEL[delete_definition]
            EXP[export_definitions]
        end
        
        subgraph "Utility Operations"
            CLR[clear_cache]
            STA[get_statistics]
            HEA[health_check]
            CFG[get_config]
        end
    end

    %% API Connections
    DS --> GEN
    DS --> VAL
    DS --> CHK
    AS --> SAV
    DP --> DOC
    DP --> CTX
    
    DR --> GET
    DR --> UPD
    DR --> DEL
    IM --> EXP
    
    CM --> CLR
    DR --> STA
    DS --> HEA
    CM --> CFG

    %% External API Connections
    AI --> GPT
    AI --> EMB
    WL --> WP
    WL --> WN
    WL --> ON
    WL --> WK
    DP --> WL

    style DS fill:#e3f2fd
    style DR fill:#e8f5e8
    style WL fill:#fff3e0
    style GPT fill:#ffebee
```

## 4. Database Relaties Diagram

```mermaid
erDiagram
    DEFINITIES {
        integer id PK
        text begrip
        text definitie
        text categorie
        text organisatorische_context
        text juridische_context
        text wettelijke_basis
        text status
        integer version_number
        integer previous_version_id FK
        real validation_score
        text validation_issues
        text source_type
        text source_reference
        datetime created_at
        datetime updated_at
        text created_by
        text approved_by
        datetime approved_at
        text approval_notes
        text export_destinations
    }

    DEFINITIE_GESCHIEDENIS {
        integer id PK
        integer definitie_id FK
        text wijziging_type
        text wijziging_reden
        text oude_waarde
        text nieuwe_waarde
        text context_snapshot
        datetime wijziging_datum
        text gewijzigd_door
    }

    DEFINITIE_VOORBEELDEN {
        integer id PK
        integer definitie_id FK
        text voorbeeld_type
        text voorbeeld_tekst
        text generation_model
        text generation_parameters
        boolean beoordeeld
        text beoordeling
        datetime gegenereerd_op
        text gegenereerd_door
    }

    DEFINITIE_TAGS {
        integer id PK
        integer definitie_id FK
        text tag_naam
        text tag_waarde
        datetime toegevoegd_op
        text toegevoegd_door
    }

    DOCUMENT_METADATA {
        text id PK
        text filename
        text mime_type
        integer size
        datetime uploaded_at
        text extracted_text
        integer text_length
        text keywords
        text key_concepts
        text legal_references
        text context_hints
        text processing_status
        text error_message
    }

    IMPORT_EXPORT_LOGS {
        integer id PK
        text operatie_type
        text bron_bestemming
        integer aantal_verwerkt
        integer aantal_succesvol
        text fouten_details
        text status
        datetime gestart_op
        datetime voltooid_op
        text uitgevoerd_door
    }

    CACHE_METADATA {
        text cache_key PK
        text operatie_type
        integer file_size
        datetime created_at
        datetime last_accessed
        datetime expires_at
        integer access_count
    }

    DOCUMENT_SOURCES {
        integer id PK
        integer definitie_id FK
        text document_id FK
        text source_type
        datetime used_at
    }

    %% Relationships
    DEFINITIES ||--o{ DEFINITIE_GESCHIEDENIS : "heeft geschiedenis"
    DEFINITIES ||--o{ DEFINITIE_VOORBEELDEN : "heeft voorbeelden"
    DEFINITIES ||--o{ DEFINITIE_TAGS : "heeft tags"
    DEFINITIES ||--o{ DOCUMENT_SOURCES : "gebruikt documenten"
    DEFINITIES ||--o| DEFINITIES : "vorige versie"
    DOCUMENT_METADATA ||--o{ DOCUMENT_SOURCES : "gebruikt in definities"
```

## 5. Deployment Architectuur Diagram

```mermaid
graph TB
    subgraph "💻 Local Development"
        DEV[Development Environment]
        subgraph "Dev Stack"
            DAPP[Streamlit App :8501]
            DDB[(SQLite Database)]
            DCACHE[File Cache]
            DLOG[Local Logs]
        end
    end

    subgraph "🧪 Testing Environment"
        TEST[Testing Environment]
        subgraph "Test Stack"
            TAPP[Test Streamlit :8502]
            TDB[(Test Database)]
            TCACHE[Test Cache]
            TLOG[Test Logs]
        end
    end

    subgraph "🚀 Production Environment"
        PROD[Production Environment]
        subgraph "Prod Stack"
            PAPP[Production App :80]
            PDB[(Production Database)]
            PCACHE[Production Cache]
            PLOG[Production Logs]
            PMON[Monitoring]
        end
    end

    subgraph "☁️ External Services"
        OPENAI[OpenAI API]
        WIKI[Wikipedia API]
        LEGAL[Legal Databases]
        BACKUP[Backup Storage]
    end

    subgraph "📁 File System Structure"
        FS[File System]
        subgraph "Directory Structure"
            SRC[/src - Source Code]
            CONF[/config - Configuration]
            DATA[/data - Database Files]
            CACHE_DIR[/cache - Cache Files]
            EXPORT[/exports - Generated Exports]
            LOG_DIR[/log - Application Logs]
            DOC_DIR[/data/uploaded_documents - Document Storage]
        end
    end

    subgraph "⚙️ Configuration Management"
        CONFIG[Configuration System]
        subgraph "Config Files"
            YAML_DEF[config_default.yaml]
            YAML_DEV[config_development.yaml]
            YAML_TEST[config_testing.yaml]
            YAML_PROD[config_production.yaml]
            ENV[Environment Variables]
        end
    end

    %% Environment connections
    DEV --> DAPP
    DAPP --> DDB
    DAPP --> DCACHE
    DAPP --> DLOG

    TEST --> TAPP
    TAPP --> TDB
    TAPP --> TCACHE
    TAPP --> TLOG

    PROD --> PAPP
    PAPP --> PDB
    PAPP --> PCACHE
    PAPP --> PLOG
    PAPP --> PMON

    %% External service connections
    DAPP --> OPENAI
    TAPP --> OPENAI
    PAPP --> OPENAI

    DAPP --> WIKI
    TAPP --> WIKI
    PAPP --> WIKI

    DAPP --> LEGAL
    TAPP --> LEGAL
    PAPP --> LEGAL

    PDB --> BACKUP

    %% File system connections
    DAPP --> FS
    TAPP --> FS
    PAPP --> FS

    FS --> SRC
    FS --> CONF
    FS --> DATA
    FS --> CACHE_DIR
    FS --> EXPORT
    FS --> LOG_DIR
    FS --> DOC_DIR

    %% Configuration connections
    DAPP --> CONFIG
    TAPP --> CONFIG
    PAPP --> CONFIG

    CONFIG --> YAML_DEF
    CONFIG --> YAML_DEV
    CONFIG --> YAML_TEST
    CONFIG --> YAML_PROD
    CONFIG --> ENV

    style DEV fill:#e8f5e8
    style TEST fill:#fff3e0
    style PROD fill:#ffebee
    style OPENAI fill:#e3f2fd
    style CONFIG fill:#f3e5f5
```

## 6. Cache & Performance Architectuur

```mermaid
graph TB
    subgraph "🚀 Performance Layer"
        subgraph "Request Flow"
            REQ[Incoming Request]
            VAL[Input Validation]
            CACHE_CHECK[Cache Check]
            PROC[Process Request]
            CACHE_STORE[Cache Result]
            RESP[Return Response]
        end

        subgraph "🗄️ Caching System"
            MEM[Memory Cache]
            FILE[File Cache]
            META[Cache Metadata]
            CLEAN[Cache Cleanup]
        end

        subgraph "⚡ Rate Limiting"
            RL[Smart Rate Limiter]
            BUCKET[Token Bucket]
            QUOTA[API Quota Manager]
            BACKOFF[Backoff Strategy]
        end

        subgraph "🛡️ Resilience"
            CB[Circuit Breaker]
            RETRY[Retry Logic]
            FALLBACK[Fallback Cache]
            DLQ[Dead Letter Queue]
        end
    end

    subgraph "📊 Monitoring"
        METRICS[Performance Metrics]
        HEALTH[Health Checks]
        ALERTS[Alert System]
        DASHBOARD[Monitoring Dashboard]
    end

    %% Request flow
    REQ --> VAL
    VAL --> CACHE_CHECK
    CACHE_CHECK -->|Hit| RESP
    CACHE_CHECK -->|Miss| PROC
    PROC --> CACHE_STORE
    CACHE_STORE --> RESP

    %% Cache system
    CACHE_CHECK --> MEM
    CACHE_CHECK --> FILE
    FILE --> META
    META --> CLEAN

    %% Rate limiting
    PROC --> RL
    RL --> BUCKET
    RL --> QUOTA
    RL --> BACKOFF

    %% Resilience
    PROC --> CB
    CB --> RETRY
    RETRY --> FALLBACK
    FALLBACK --> DLQ

    %% Monitoring
    PROC --> METRICS
    CB --> HEALTH
    HEALTH --> ALERTS
    METRICS --> DASHBOARD

    style REQ fill:#e3f2fd
    style CACHE_CHECK fill:#e8f5e8
    style CB fill:#fff3e0
    style METRICS fill:#f3e5f5
```

## 7. Security & Compliance Diagram

```mermaid
graph TB
    subgraph "🔐 Security Layer"
        subgraph "Input Security"
            SANITIZE[Input Sanitization]
            VALIDATE[Input Validation]
            ESCAPE[HTML/SQL Escaping]
        end

        subgraph "API Security"
            API_KEY[API Key Management]
            RATE_LIMIT[Rate Limiting]
            TIMEOUT[Request Timeouts]
        end

        subgraph "Data Security"
            ENCRYPT[Data Encryption]
            BACKUP[Secure Backups]
            AUDIT[Audit Logging]
        end
    end

    subgraph "📋 Compliance"
        GDPR[GDPR Compliance]
        DATA_MIN[Data Minimization]
        RETENTION[Data Retention]
        CONSENT[User Consent]
    end

    subgraph "🔍 Monitoring"
        LOG_MON[Security Logging]
        ANOMALY[Anomaly Detection]
        INCIDENT[Incident Response]
    end

    %% Security connections
    SANITIZE --> VALIDATE
    VALIDATE --> ESCAPE
    API_KEY --> RATE_LIMIT
    RATE_LIMIT --> TIMEOUT
    ENCRYPT --> BACKUP
    BACKUP --> AUDIT

    %% Compliance connections
    GDPR --> DATA_MIN
    DATA_MIN --> RETENTION
    RETENTION --> CONSENT

    %% Monitoring connections
    AUDIT --> LOG_MON
    LOG_MON --> ANOMALY
    ANOMALY --> INCIDENT

    style SANITIZE fill:#ffebee
    style API_KEY fill:#e8f5e8
    style GDPR fill:#e3f2fd
    style LOG_MON fill:#fff3e0
```

## 8. AI Integration Architectuur

```mermaid
graph TB
    subgraph "🤖 AI Services Layer"
        subgraph "Generation Services"
            DEF_GEN[Definition Generator]
            EX_GEN[Example Generator]
            FEEDBACK[Feedback Generator]
        end

        subgraph "Validation Services"
            RULE_VAL[Rule Validator]
            QUALITY[Quality Checker]
            COMPLIANCE[Compliance Checker]
        end

        subgraph "Enhancement Services"
            SYNONYM[Synonym Generator]
            TRANSLATION[Translation Service]
            SUMMARY[Summary Generator]
            DOC_ENHANCE[Document Enhancement]
            HYBRID_CTX[Hybrid Context Builder]
        end
    end

    subgraph "🧠 AI Models"
        GPT4[GPT-4 Turbo]
        GPT35[GPT-3.5 Turbo]
        EMBEDDING[Text Embeddings]
        CUSTOM[Custom Models]
    end

    subgraph "📝 Prompt Management"
        TEMPLATES[Prompt Templates]
        CONTEXT[Context Builder]
        OPTIMIZER[Prompt Optimizer]
    end

    subgraph "⚡ Performance"
        CACHE_AI[AI Response Cache]
        BATCH[Batch Processing]
        ASYNC_AI[Async Processing]
    end

    %% AI Service connections
    DEF_GEN --> GPT4
    EX_GEN --> GPT35
    FEEDBACK --> GPT4
    RULE_VAL --> GPT35
    QUALITY --> GPT4
    COMPLIANCE --> GPT4
    SYNONYM --> GPT35
    TRANSLATION --> GPT4
    SUMMARY --> GPT35
    DOC_ENHANCE --> GPT35
    HYBRID_CTX --> GPT4

    %% Embedding connections
    RULE_VAL --> EMBEDDING
    QUALITY --> EMBEDDING

    %% Prompt management
    DEF_GEN --> TEMPLATES
    TEMPLATES --> CONTEXT
    CONTEXT --> OPTIMIZER

    %% Performance
    DEF_GEN --> CACHE_AI
    EX_GEN --> BATCH
    FEEDBACK --> ASYNC_AI

    style DEF_GEN fill:#e3f2fd
    style GPT4 fill:#ffebee
    style TEMPLATES fill:#e8f5e8
    style CACHE_AI fill:#fff3e0
```

## 9. Hybride Context Verrijking Architectuur

```mermaid
graph TB
    subgraph "📄 Document Processing Pipeline"
        subgraph "Upload & Extraction"
            UP[Document Upload]
            EXT[Text Extraction]
            META[Metadata Analysis]
        end
        
        subgraph "Content Analysis"
            KW[Keyword Extraction]
            CONC[Concept Identification]
            LEG[Legal Reference Detection]
            HINT[Context Hints Generation]
        end
        
        subgraph "Document Intelligence"
            CLASS[Document Classification]
            TOPIC[Topic Modeling]
            REL[Relevance Scoring]
        end
    end

    subgraph "🌐 Web Lookup Integration"
        subgraph "Source Selection"
            SMART[Smart Source Selector]
            PRIO[Priority Engine]
            FILTER[Context Filter]
        end
        
        subgraph "Enhanced Lookup"
            WIKI[Wikipedia Enhanced]
            LEGAL_WEB[Legal Databases Enhanced]
            GOV[Government Sources Enhanced]
            DICT[Dictionary Enhanced]
        end
        
        subgraph "Result Enhancement"
            MERGE[Result Merger]
            DEDUP[Deduplication]
            RANK[Relevance Ranking]
        end
    end

    subgraph "🔄 Hybrid Context Engine"
        subgraph "Context Fusion"
            AGG[Context Aggregator]
            WEIGHT[Weighted Combination]
            VALIDATE[Cross-Validation]
        end
        
        subgraph "Intelligence Layer"
            MATCH[Document-Web Matching]
            CONFLICT[Conflict Resolution]
            CONFIDENCE[Confidence Scoring]
        end
        
        subgraph "Output Generation"
            UNIFIED[Unified Context]
            SOURCES[Source Attribution]
            ENRICHED[Enriched Prompt]
        end
    end

    subgraph "🎯 Definition Generation"
        GPT_ENHANCED[GPT with Hybrid Context]
        QUALITY_CHECK[Enhanced Quality Check]
        RESULT[Enhanced Definition]
    end

    %% Document Processing Flow
    UP --> EXT
    EXT --> META
    META --> KW
    META --> CONC
    META --> LEG
    KW --> HINT
    CONC --> HINT
    LEG --> HINT
    
    %% Document Intelligence
    HINT --> CLASS
    CLASS --> TOPIC
    TOPIC --> REL

    %% Web Lookup Enhancement
    CLASS --> SMART
    TOPIC --> PRIO
    REL --> FILTER
    
    SMART --> WIKI
    SMART --> LEGAL_WEB
    SMART --> GOV
    SMART --> DICT
    
    WIKI --> MERGE
    LEGAL_WEB --> MERGE
    GOV --> MERGE
    DICT --> MERGE
    
    MERGE --> DEDUP
    DEDUP --> RANK

    %% Hybrid Context Generation
    HINT --> AGG
    RANK --> AGG
    AGG --> WEIGHT
    WEIGHT --> VALIDATE
    VALIDATE --> MATCH
    MATCH --> CONFLICT
    CONFLICT --> CONFIDENCE
    CONFIDENCE --> UNIFIED
    UNIFIED --> SOURCES
    SOURCES --> ENRICHED

    %% Final Generation
    ENRICHED --> GPT_ENHANCED
    GPT_ENHANCED --> QUALITY_CHECK
    QUALITY_CHECK --> RESULT

    style UP fill:#e3f2fd
    style SMART fill:#e8f5e8
    style AGG fill:#fff3e0
    style GPT_ENHANCED fill:#ffebee
```

## 10. Context Enrichment Data Flow

```mermaid
sequenceDiagram
    participant U as User
    participant UI as Interface
    participant DP as Document Processor
    participant WE as Web Enhancer
    participant HCE as Hybrid Context Engine
    participant AI as AI Generator
    participant R as Repository

    U->>UI: Upload docs + request definition
    
    par Document Analysis
        UI->>DP: analyze_documents()
        DP->>DP: extract_keywords()
        DP->>DP: identify_concepts()
        DP->>DP: detect_legal_refs()
        DP->>DP: classify_content()
        DP-->>UI: document_intelligence
    and Web Lookup Preparation
        UI->>WE: prepare_enhanced_lookup()
        WE->>WE: select_relevant_sources()
        WE->>WE: prioritize_by_context()
        WE-->>UI: source_strategy
    end
    
    UI->>HCE: create_hybrid_context()
    
    par Context Integration
        HCE->>DP: get_document_context()
        DP-->>HCE: structured_doc_context
    and Enhanced Web Lookup
        HCE->>WE: execute_enhanced_lookup()
        WE->>WE: query_prioritized_sources()
        WE->>WE: filter_by_document_keywords()
        WE->>WE: rank_by_relevance()
        WE-->>HCE: enhanced_web_context
    end
    
    HCE->>HCE: merge_contexts()
    HCE->>HCE: resolve_conflicts()
    HCE->>HCE: calculate_confidence()
    HCE->>HCE: generate_unified_context()
    HCE-->>UI: hybrid_context
    
    UI->>AI: generate_with_hybrid_context()
    AI->>AI: build_enriched_prompt()
    AI->>AI: call_gpt_with_context()
    AI->>AI: validate_against_sources()
    AI-->>UI: enhanced_definition
    
    UI->>R: save_with_source_attribution()
    R-->>UI: saved_with_lineage
    
    UI-->>U: display_enhanced_result()
```

---

## Diagram Implementatie Instructies

### Voor Mermaid Diagrammen:
1. Kopieer de mermaid code naar [mermaid.live](https://mermaid.live)
2. Of gebruik een Mermaid plugin in je editor (VS Code, IntelliJ)
3. Export als SVG/PNG voor documentatie

### Voor Uitgebreide Visualisatie:
- **Lucidchart**: Voor professionele diagrammen
- **Draw.io**: Gratis online diagram tool
- **PlantUML**: Voor tekstuele diagram definitie
- **Visio**: Voor Microsoft omgevingen

### Kleuren Schema:
- 🔵 **Blauw** (#e3f2fd): User Interface componenten
- 🟢 **Groen** (#e8f5e8): Data & Storage componenten  
- 🟠 **Oranje** (#fff3e0): External Services & APIs
- 🔴 **Rood** (#ffebee): AI Services & Critical components
- 🟣 **Paars** (#f3e5f5): Configuration & Infrastructure

Deze diagrammen geven een complete overview van de DefinitieAgent architectuur en kunnen als basis dienen voor verdere ontwikkeling en documentatie.

## 11. UI User Flow Diagram

```mermaid
graph TD
    Start([User Opens App]) --> MainPage[Main Page]
    
    MainPage --> TermInput{Term Input<br/>Visible?}
    TermInput -->|No - Current Issue| NavigateTab[Navigate to Tab First]
    TermInput -->|Yes - Fixed| DirectInput[Enter Term Directly]
    
    NavigateTab --> TabView[Definition Generator Tab]
    TabView --> EnterTerm[Enter Term in Tab]
    
    DirectInput --> ContextSelect[Select Context]
    EnterTerm --> ContextSelect
    
    ContextSelect --> PresetChoice{Use Preset?}
    PresetChoice -->|Yes - Complex| SelectPreset[Select from Presets]
    PresetChoice -->|No - Simple| DirectSelect[Direct Multiselect]
    
    SelectPreset --> ManualAdjust[Manual Adjustments]
    DirectSelect --> Generate[Generate Definition]
    ManualAdjust --> Generate
    
    Generate --> ViewResults[View Results]
    ViewResults --> Actions{User Actions}
    
    Actions -->|Export| ExportDef[Export Definition]
    Actions -->|Edit| EditDef[Edit Definition]
    Actions -->|New| Start
    
    style TermInput fill:#ff9999
    style NavigateTab fill:#ff9999
    style PresetChoice fill:#ffcc99
    style SelectPreset fill:#ffcc99
```

## 12. Error Handling Flow Diagram

```mermaid
graph TB
    subgraph "Error Detection Layer"
        E1[Web Lookup Error]
        E2[Database Lock Error]
        E3[API Key Error]
        E4[UI State Error]
        E5[Validation Error]
    end
    
    subgraph "Error Handling Strategy"
        H1[Retry with Backoff]
        H2[Connection Pool]
        H3[Key Vault Integration]
        H4[State Recovery]
        H5[Graceful Degradation]
    end
    
    subgraph "User Communication"
        U1[User-Friendly Message]
        U2[Technical Details Toggle]
        U3[Recovery Actions]
        U4[Support Contact]
    end
    
    E1 --> H1 --> U1
    E2 --> H2 --> U1
    E3 --> H3 --> U1
    E4 --> H4 --> U1
    E5 --> H5 --> U1
    
    U1 --> U2
    U1 --> U3
    U3 --> U4
    
    subgraph "Logging & Monitoring"
        L1[Error Logger]
        L2[Performance Monitor]
        L3[Alert System]
    end
    
    H1 --> L1
    H2 --> L1
    H3 --> L1
    H4 --> L1
    H5 --> L1
    
    L1 --> L2
    L2 --> L3
```

## Update Summary v2.2

**Nieuwe Diagrammen:**
- UI User Flow Diagram: Toont huidige workflow problemen en gewenste flow
- Error Handling Flow Diagram: Visualiseert error handling strategie

**Highlighted Issues:**
- Term input navigatie probleem (rood gemarkeerd)
- Context selector complexiteit (oranje gemarkeerd)

Deze update reflecteert de UI regressie issues en voorgestelde verbeteringen uit de consolidatie.