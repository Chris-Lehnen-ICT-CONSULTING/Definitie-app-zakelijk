# Remediation-backlog

De volgorde is risicogestuurd. Iedere fase start met een reproduceerbare regressietest en eindigt met de hieronder genoemde gates.

De canonieke queue bevat 673 verified findings: 63 P1, 331 P2 en 279 P3.

## Fase 0 — productiebeveiliging en herstelbaarheid

- bevries destructieve migratie-/recoveryrunbooks en standaard-DB-mutaties;
- maak geverifieerde WAL-aware backups en herstelproeven verplicht;
- roteer/controleer secretflows en herstel fail-open scanners;
- accepteer geen production-readiness zolang een P1 openstaat.

### P1-queue

| ID | Gebied | Locatie | Titel |
|---|---|---|---|
| INV-ENCODING-D2C4CCDFC47C | inventory | `docs/voorbeelden/Identiteitsbehandeling_fixed_v2.json:1` | Blocking text encoding error |
| PILOT-001 | concurrency | `src/database/db_connection.py:19` | Shared SQLite transaction can roll back another session |
| PILOT-003 | error_handling | `src/database/db_connection.py:96` | Schema initialization accepts incomplete or failed databases |
| PILOT-014 | session_isolation | `src/services/service_factory.py:32` | Provider reset returns a stale process-cached adapter |
| B007-002 | security | `src/domain/autoriteit/betrouwbaarheid.py:134` | Trusted-host predicate accepts substring-spoofed URLs |
| B009-001 | data_loss | `src/database/migrate_database.py:38` | Migration rebuild drops generation prompt data |
| B009-002 | data_loss | `src/database/migrate_database.py:403` | Failed destructive rebuild returns success |
| B010-001 | backup_restore | `src/database/migrations/v5_migration.py:198` | SQLite backup omits committed WAL data but verifies successfully |
| B010-002 | data_loss | `src/database/schema.sql:362` | Synonym uniqueness ignores per-definition ownership |
| B010-003 | transactionality | `src/database/synonym_sync.py:96` | Synonym synchronization commits partially after failure |
| B011-001 | data_integrity | `src/services/definition_repository.py:80` | Repository save ignores a failed legacy update |
| B011-002 | data_integrity | `src/services/definition_repository.py:305` | Hard delete confirms an uncommitted delete |
| B012-001 | secret_handling | `src/services/ai/openai_client.py:84` | Sanitized AI errors retain the raw SDK cause |
| B012-002 | session_isolation | `src/services/container.py:108` | Provider reset leaves singleton configuration stale |
| B014-001 | deserialization | `src/services/definition_generator_cache.py:199` | Redis cache deserializes attacker-controlled bytes with pickle |
| B014-002 | cache_isolation | `src/services/definition_generator_cache.py:333` | Cache identity and invalidation mishandle context variants |
| B014-003 | functionality | `src/services/definition_generator_context.py:70` | Document-only context is omitted from the active prompt |
| B015-001 | functionality | `src/services/prompts/modular_prompt_adapter.py:297` | Prompt cap removes the term and final instruction |
| B015-002 | secret_handling | `src/services/orchestrators/definition_orchestrator_v2.py:337` | Raw term is logged before sanitization |
| B015-005 | configuration | `src/services/orchestrators/definition_orchestrator_v2.py:579` | Invalid RAG minimum score breaks generation without RAG |
| B016-001 | error_handling | `src/services/prompts/modules/prompt_orchestrator.py:143` | Essential prompt module failures are silently omitted |
| B017-001 | availability | `src/services/synonym_orchestrator.py:49` | Import-time logging writes to the project root |
| B017-002 | data_integrity | `src/ui/handlers/definition_generation_handler.py:243` | Force-duplicate bypass persists after a generation |
| B023-001 | validation | `src/services/validation/modular_validation_service.py:644` | Soft floor overrides failed critical acceptance gates |
| B023-002 | availability | `src/services/validation/modular_validation_service.py:181` | Degraded validation fallback crashes on first use |
| B023-003 | validation | `src/services/validation/modular_validation_service.py:348` | Category and domain context disappear from active validation |
| B025-001 | validation | `src/toetsregels/regels/CON-01.json:3` | CON-01 ignores free user-provided context |
| B025-002 | legal_correctness | `src/toetsregels/regels/CON-02.json:2` | CON-02 accepts explicitly negated source evidence |
| B026-001 | validation | `src/toetsregels/regels/ESS-02.json:3` | Selected ontology category is ignored |
| B026-002 | validation | `src/toetsregels/regels/ESS-03.json:17` | Rule applicability conditions are ignored |
| B027-001 | validation | `src/toetsregels/regels/INT-07.json:7` | INT-07 flags ordinary lowercase words as abbreviations |
| B035-008 | concurrency | `src/services/modern_web_lookup_service.py:66` | Singleton web debug state mixes concurrent requests |
| B039-001 | authorization | `src/services/definition_workflow_service.py:464` | Direct status adapter bypasses workflow transition policy |
| B039-002 | validation | `src/services/definition_workflow_service.py:595` | Critical workflow validation issues can pass the gate |
| B041-002 | data_integrity | `src/ui/helpers/examples.py:104` | Examples from the last generation leak into another record |
| B042-001 | security | `src/ui/components/ai_provider_sidebar.py:43` | Provider and API key are process-global across sessions |
| B042-002 | authorization | `src/ui/components/definition_edit_tab.py:472` | Established definitions still allow category mutation |
| B042-003 | data_integrity | `src/ui/components/definition_edit_tab.py:1640` | Undo and revert leave stale widget edits active |
| B043-001 | data_integrity | `src/ui/components/expert_review_tab.py:984` | Expert edits persist before an impossible approval transition |
| B043-002 | data_integrity | `src/ui/components/expert_review_tab.py:655` | UFO update is outside the approval transaction |
| B046-001 | functionality | `src/opschoning/opschoning.py:91` | Cleaning strips valid term prefixes from definitions |
| B047-001 | functionality | `src/services/data_aggregation_service.py:136` | JSON export fails on aggregated datetime metadata |
| B047-002 | data_integrity | `src/services/definition_edit_service.py:451` | Definition edits erase process explanation |
| B047-003 | workflow | `src/services/policies/approval_gate_policy.py:85` | Invalid approval thresholds can bypass quality gates |
| B063-001 | authorization | `tests/unit/services/test_workflow_service.py:25` | Workflow policy treats a missing role as archive authorization |
| B082-001 | data_integrity | `tests/unit/voorbeelden_functionality_tests.py:1` | Hidden voorbeelden suite masks overwrite that inherits prior approval |
| B095-001 | data_integrity | `docs/archiveer-simpel.sh:64` | Flat documentation archive silently overwrites same-named files |
| B095-002 | data_integrity | `docs/reorganize-docs.sh:203` | Documentation reorganization mutates reviews before a guaranteed invalid move |
| B095-003 | repository_integrity | `scripts/analyse/hernoem-naar-nederlands.py:86` | Rename tool stages all user changes and creates its backup inside the source tree |
| B095-004 | data_integrity | `scripts/analyse/hernoem-naar-nederlands.py:236` | Failed rename rolls back the filename but not rewritten references |
| B097-001 | data_integrity | `scripts/archive_data.py:391` | Archive deletion uses every historical archive ID instead of the successful copy set |
| B097-002 | data_integrity | `scripts/auto_backup_database.sh:58` | Hourly backup copies only the SQLite main file and silently omits committed WAL data |
| B102-001 | operational | `scripts/maintenance/grep_gate.sh:7` | Active grep gate scans the wrong root and treats rg errors as clean |
| B103-003 | data_integrity | `scripts/migrate_synonyms_to_registry.py:743` | Synonym migration rollback deletes unrelated human data and leaves migrated data behind |
| B104-001 | data_integrity | `scripts/restore_orphaned_voorbeelden.py:115` | Orphan cleanup drops backup tables even when restore refused rows |
| B100-001 | data_integrity | `scripts/docs/normalize_documentation.py:93` | Documentation normalizer corrupts prose and structured dates and targets another checkout |
| B100-002 | privacy | `scripts/export_baseline_definitions.py:28` | Production baseline export publishes audit identities and internal provenance into tracked documentation |
| B101-001 | data_migration | `scripts/fix_definities_old_fk.py:224` | Generation-log table rebuild leaves SQLite views pointing to the dropped old table |
| B101-002 | data_integrity | `scripts/fix_unicode_chars.py:13` | Unicode fixer can turn valid Python string literals into invalid syntax |
| B101-003 | data_loss | `scripts/import_from_txt_exports.py:45` | TXT recovery parser truncates definitions at ordinary colon-prefixed continuation lines |
| B101-004 | data_loss | `scripts/maintenance/cleanup_nan_contexts.py:21` | NaN-context cleanup silently replaces malformed context data with empty arrays |
| B151-001 | security | `docs/analyses/SECURITY_AUDIT_REPORT.md:182` | Secret-response runbook exposes the current key and its history scrub expression cannot match leaked keys |
| B004-001 | security | `.gitleaks.toml:13` | Globale Gitleaks-allowlists schakelen secret-detectie uit voor alle tests en documentatie |

## Fase 1 — transacties, migraties en datacontracten

Pak connection ownership, atomic check-and-write, migratie-ledgers, schema-invarianten en typed recovery-outcomes als samenhangend programma aan. Acceptatie: concurrency- en recoverytests op tijdelijke databases, integriteitscheck na herstel en geen open SQLite ResourceWarnings.

## Fase 2 — validatie, AI en weblookup

Herstel de 53-regel-SSoT, exacte provider/configmapping, context/provenance, timeouts/cancellation en exception-redactie. Acceptatie: directe contracttests op productiehelpers, deterministische fake providers en geen copied-logic tests.

## Fase 3 — test- en CI-gates

Maak smoke/acceptance/integratie hermetisch, pin actions/dependencies, gebruik `$(PY) -m pytest`, laat lege collecties en scannerfouten hard falen en verhoog de coverage-ratchet stapsgewijs. Acceptatie: alle hoofdgates groen zonder credentials; integratie-live-tests expliciet gemarkeerd en begrensd.

## Fase 4 — privacy, dependencies en licenties

Minimaliseer logs/prompts/screenshots, upgrade aiohttp en GitPython, leg de PyMuPDF-licentiebasis vast en genereer SBOM/advisorybewijs. Acceptatie: zero-secret canaries, gelogde data-classificatie en goedgekeurde licentie-inventaris.

## Fase 5 — UI, toegankelijkheid en documentatiesanering

Herstel actieve navigatie, contrast, deprecated Streamlit-API's en keyboard/SR-flow; archiveer of genereer stale documentatie. Acceptatie: browsermatrix, WCAG AA, fail-closed interne linkcheck en uitvoerbare doctests.

## P2/P3-capaciteitsverdeling

| Reviewgebied | P2/P3 findings |
|---|---:|
| test_quality | 83 |
| data_integrity | 52 |
| functionality | 35 |
| validation | 28 |
| error_handling | 24 |
| security | 24 |
| documentation | 23 |
| architecture | 22 |
| configuration | 21 |
| accessibility | 19 |
| process_safety | 18 |
| operational | 15 |
| privacy | 14 |
| test_isolation | 14 |
| test_coverage | 13 |
| test_gate | 12 |
| resilience | 11 |
| ux | 11 |
| concurrency | 9 |
| resource_management | 9 |
| analysis_integrity | 8 |
| correctness | 7 |
| availability | 6 |
| input_validation | 6 |
| observability | 6 |
| api_contract | 5 |
| audit | 5 |
| path_handling | 5 |
| developer_workflow | 4 |
| test_infrastructure | 4 |
| cli | 3 |
| code_quality_architecture | 3 |
| evidence_integrity | 3 |
| metrics | 3 |
| rag | 3 |
| state_management | 3 |
| ui_ux | 3 |
| validation_quality | 3 |
| code_quality | 2 |
| contract | 2 |
| coverage | 2 |
| dependency_management | 2 |
| external_side_effect | 2 |
| integration | 2 |
| legal_correctness | 2 |
| maintenance | 2 |
| migration | 2 |
| operational_safety | 2 |
| portability | 2 |
| rate_limiting | 2 |
| reporting | 2 |
| secret_handling | 2 |
| test_configuration | 2 |
| tooling | 2 |
| ui_ux_accessibility | 2 |
| api_documentation | 1 |
| audit_integrity | 1 |
| backup_restore | 1 |
| cache | 1 |
| caching | 1 |
| ci_configuration | 1 |
| classification | 1 |
| confidentiality | 1 |
| cost_observability | 1 |
| data_loss | 1 |
| data_migration | 1 |
| data_provenance | 1 |
| dead_code | 1 |
| deployment | 1 |
| design | 1 |
| design_correctness | 1 |
| determinism | 1 |
| documentation_integrity | 1 |
| feedback | 1 |
| governance | 1 |
| import_side_effect | 1 |
| information_architecture | 1 |
| license_compliance | 1 |
| maintainability | 1 |
| performance | 1 |
| process_governance | 1 |
| schema | 1 |
| schema_drift | 1 |
| security_audit | 1 |
| security_compliance | 1 |
| security_policy | 1 |
| session_isolation | 1 |
| test_resource_safety | 1 |
| test_safety | 1 |
| test_strategy | 1 |
| timeout | 1 |
| traceability | 1 |
| transactionality | 1 |
| workflow | 1 |
