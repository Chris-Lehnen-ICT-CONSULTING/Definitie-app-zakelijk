# Service Dependency Matrix

## Dependency Overview

Deze matrix toont welke service (rij) welke andere service (kolom) importeert. Een 'X' betekent dat de service in de rij de service in de kolom importeert.

| Service | config | context | prompts | web_lookup | data_agg | container | orchestrator | repository | validator | cleaning | workflow | export | Other |
|---------|--------|---------|---------|------------|----------|-----------|--------------|------------|-----------|----------|----------|--------|--------|
| **container** | X | - | - | X | X | - | X | X | X | X | X | X | duplicate_detection, null_repository |
| **definition_orchestrator** | X | X | X | X | - | - | - | - | - | - | - | - | - |
| **definition_generator_context** | X | - | - | X | - | - | - | - | - | - | - | - | - |
| **definition_generator_prompts** | X | X | - | - | - | - | - | - | - | - | - | - | - |
| **workflow_service** | - | - | - | - | X | - | - | - | - | - | - | - | category_service |
| **export_service** | - | - | - | - | X | - | - | - | - | - | - | - | - |
| **regeneration_service** | - | - | X | - | - | - | - | - | - | - | - | - | - |
| **service_factory** | - | - | - | - | - | X | - | - | - | - | - | - | regeneration_service |
| **definition_generator_cache** | X | - | - | - | - | - | - | - | - | - | - | - | - |
| **definition_generator_enhancement** | X | - | - | - | - | - | - | - | - | - | - | - | - |
| **definition_generator_monitoring** | X | - | - | - | - | - | - | - | - | - | - | - | - |

## Import Frequency

### Meest geïmporteerd (incoming dependencies):
1. **definition_generator_config**: 7x
2. **modern_web_lookup_service**: 3x
3. **data_aggregation_service**: 3x
4. **definition_generator_context**: 2x
5. **definition_generator_prompts**: 2x

### Meeste imports (outgoing dependencies):
1. **container**: 12 services
2. **definition_orchestrator**: 4 services
3. **workflow_service**: 2 services
4. **definition_generator_prompts**: 2 services
5. **definition_generator_context**: 2 services

## Service Roles

### Hub Services (veel outgoing)
- **container**: Central Dependency Injection hub
- **definition_orchestrator**: Orchestreert definitie generatie proces

### Core Services (veel incoming)
- **definition_generator_config**: Configuratie voor alle generator services
- **modern_web_lookup_service**: Web data integratie
- **data_aggregation_service**: Data processing en aggregatie

### Bridge Services (zowel incoming als outgoing)
- **definition_generator_context**: Brug tussen config en prompts
- **definition_generator_prompts**: Brug tussen context en orchestrator

### Leaf Services (alleen incoming, geen outgoing naar andere services)
- **definition_generator_cache**
- **definition_generator_enhancement**
- **definition_generator_monitoring**
- **export_service**
- **regeneration_service**

## Architectural Insights

1. **Layered Architecture**: Services volgen een duidelijke gelaagde structuur
2. **No Cycles**: Geen circulaire dependencies gevonden
3. **Clear Separation**: Config, context, en prompts vormen een logische pipeline
4. **Container Pattern**: Container service implementeert Dependency Injection pattern effectief
5. **Interface Usage**: Services met interfaces zijn beter geïsoleerd en testbaar
