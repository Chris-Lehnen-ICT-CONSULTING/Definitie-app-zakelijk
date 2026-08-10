# BATCH-009

- Status: `verified`
- Reviewgroep: `4` — Database, repositories, schema en migraties
- Review-base: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Membership-SHA256: `3d39d4b5aba5d173a601df8be6619cc8a21b9acd1b9397f0ff9c6a990b046994`
- Bestanden: `20`
- Fysieke regels: `2511`
- Python-symbolen: `84`
- Reviewer: `codex-galileo`
- Onafhankelijke verifier: `codex-kierkegaard`

## Scope

| Pad | path_b64 | Regelbereik | Symbolen | Object-ID |
|---|---|---:|---:|---|
| `src/database/__init__.py` | `c3JjL2RhdGFiYXNlL19faW5pdF9fLnB5` | `1-7` | 1 | `69adb9e381b19a00ed2ca9bd35763662cd214e07` |
| `src/database/audit_helpers.py` | `c3JjL2RhdGFiYXNlL2F1ZGl0X2hlbHBlcnMucHk=` | `1-195` | 8 | `3c44a6259ff14a4aa8cbc435a8567ba7fda86242` |
| `src/database/definitie_crud.py` | `c3JjL2RhdGFiYXNlL2RlZmluaXRpZV9jcnVkLnB5` | `1-337` | 10 | `e23cebbb0776f129d54b56a31e3265f8daa59eab` |
| `src/database/definitie_duplicates.py` | `c3JjL2RhdGFiYXNlL2RlZmluaXRpZV9kdXBsaWNhdGVzLnB5` | `1-134` | 6 | `24d4d3399be1d22d202c03be04d93aaae334aef2` |
| `src/database/definitie_import_export.py` | `c3JjL2RhdGFiYXNlL2RlZmluaXRpZV9pbXBvcnRfZXhwb3J0LnB5` | `1-169` | 6 | `8cc01281feacda9b192fa4d081b48453e38e0a0a` |
| `src/database/definitie_repository.py` | `c3JjL2RhdGFiYXNlL2RlZmluaXRpZV9yZXBvc2l0b3J5LnB5` | `1-361` | 37 | `7e568050914faf666de083d9ef020e43aec349e6` |
| `src/database/definitie_search.py` | `c3JjL2RhdGFiYXNlL2RlZmluaXRpZV9zZWFyY2gucHk=` | `1-65` | 4 | `71ede9dcfea344022ccbd8fe30f5ab08188a184b` |
| `src/database/migrate_database.py` | `c3JjL2RhdGFiYXNlL21pZ3JhdGVfZGF0YWJhc2UucHk=` | `1-612` | 12 | `59f635fc8efd0333fe633334d15bb1760d14c392` |
| `src/database/migrations/006_synonym_groups_tables.sql` | `c3JjL2RhdGFiYXNlL21pZ3JhdGlvbnMvMDA2X3N5bm9ueW1fZ3JvdXBzX3RhYmxlcy5zcWw=` | `1-178` | 0 | `b66e0501f7ed8203dd58457d6c0efb42cd9b6df5` |
| `src/database/migrations/008_add_unique_constraint.sql` | `c3JjL2RhdGFiYXNlL21pZ3JhdGlvbnMvMDA4X2FkZF91bmlxdWVfY29uc3RyYWludC5zcWw=` | `1-41` | 0 | `ace8650d89bc1250e22a5a7b10d3e724ee676255` |
| `src/database/migrations/009_remove_unique_constraint.sql` | `c3JjL2RhdGFiYXNlL21pZ3JhdGlvbnMvMDA5X3JlbW92ZV91bmlxdWVfY29uc3RyYWludC5zcWw=` | `1-32` | 0 | `9c33fd281190bbf9598f1303bfe066b396dee7ac` |
| `src/database/migrations/009_remove_unique_index.sql` | `c3JjL2RhdGFiYXNlL21pZ3JhdGlvbnMvMDA5X3JlbW92ZV91bmlxdWVfaW5kZXguc3Fs` | `1-57` | 0 | `a9106aab644604fab6f8240ea0d59c234e473fbd` |
| `src/database/migrations/009_rollback.sql` | `c3JjL2RhdGFiYXNlL21pZ3JhdGlvbnMvMDA5X3JvbGxiYWNrLnNxbA==` | `1-85` | 0 | `3c46f09cce4237215c6a0e2aa637aacbadd588ac` |
| `src/database/migrations/009_rollback_remove_unique_constraint.sql` | `c3JjL2RhdGFiYXNlL21pZ3JhdGlvbnMvMDA5X3JvbGxiYWNrX3JlbW92ZV91bmlxdWVfY29uc3RyYWludC5zcWw=` | `1-46` | 0 | `382f1dbcf5774bb7b3a7a57afbf9f12075c2d275` |
| `src/database/migrations/20250126_def176_optimize_duplicates.sql` | `c3JjL2RhdGFiYXNlL21pZ3JhdGlvbnMvMjAyNTAxMjZfZGVmMTc2X29wdGltaXplX2R1cGxpY2F0ZXMuc3Fs` | `1-25` | 0 | `1d8e2b1c9f4aec5a991b59573c1400c8dd369a15` |
| `src/database/migrations/20251111_add_generation_prompt.sql` | `c3JjL2RhdGFiYXNlL21pZ3JhdGlvbnMvMjAyNTExMTFfYWRkX2dlbmVyYXRpb25fcHJvbXB0LnNxbA==` | `1-26` | 0 | `2fbf978b1215df9720bfa7d4e3ba95c051ecaaf1` |
| `src/database/migrations/add_definitie_drafts_table.sql` | `c3JjL2RhdGFiYXNlL21pZ3JhdGlvbnMvYWRkX2RlZmluaXRpZV9kcmFmdHNfdGFibGUuc3Fs` | `1-38` | 0 | `f29b9a6866b7cf8e8694cfbbd1cedc8b11b61423` |
| `src/database/migrations/add_legacy_fields.sql` | `c3JjL2RhdGFiYXNlL21pZ3JhdGlvbnMvYWRkX2xlZ2FjeV9maWVsZHMuc3Fs` | `1-16` | 0 | `80df8704ae127ede331b8e4c3581b5836455228c` |
| `src/database/migrations/add_metadata_fields.sql` | `c3JjL2RhdGFiYXNlL21pZ3JhdGlvbnMvYWRkX21ldGFkYXRhX2ZpZWxkcy5zcWw=` | `1-23` | 0 | `0133cc31ce32c38e845d93b28de0e9697bf3f50e` |
| `src/database/migrations/add_synonym_suggestions_table.sql` | `c3JjL2RhdGFiYXNlL21pZ3JhdGlvbnMvYWRkX3N5bm9ueW1fc3VnZ2VzdGlvbnNfdGFibGUuc3Fs` | `1-64` | 0 | `8f270654fb6e59c551fc728a457f399d689fdd9b` |

## Verplichte reviewchecklist

- [x] Iedere toegewezen regel rechtstreeks uit het immutable object-ID gelezen.
- [x] Ieder toegewezen symbool en iedere functie line-by-line beoordeeld.
- [x] Callers, afhankelijkheden, tests en foutpaden gecontroleerd.
- [x] Codekwaliteit en architectuur beoordeeld.
- [x] Bugs, security en foutafhandeling beoordeeld.
- [x] Functionaliteit en relevante tests beoordeeld.
- [x] UI/UX, toegankelijkheid en responsive gedrag beoordeeld indien van toepassing.
- [x] Findings bevatten prioriteit, bewijs, reproductie en oplossing.
- [x] Bewezen, vermoed en niet-getest expliciet onderscheiden.
- [x] Onafhankelijke tweede reviewer heeft scope en findings geverifieerd.

## Bevindingen

- P1/proven: `B009-001` — Migration rebuild drops generation prompt data.
- P1/proven: `B009-002` — Failed destructive rebuild returns success.
- P2/proven: `B009-003` — Preference-term backfill is conditionally skipped.
- P2/proven: `B009-004` — Migration integration test resolves the wrong project root.
- Volledig bewijs en niet-geteste onderdelen: `evidence/BATCH-009/review-evidence.md`.

## Resultaat

Geverifieerd door twee verschillende reviewers. Alle 20 bestanden en 84 symbolen zijn line-by-line beoordeeld; functionele beperkingen en niet-geteste externe of visuele flows staan expliciet in het bewijsdossier.
