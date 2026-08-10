# BATCH-010

- Status: `verified`
- Reviewgroep: `4` — Database, repositories, schema en migraties
- Review-base: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Membership-SHA256: `233fb83ac49454091027482c57e4bc94e5f265beb6ae6262d5d6dbbeefbc8bdc`
- Bestanden: `11`
- Fysieke regels: `3909`
- Python-symbolen: `88`
- Reviewer: `codex-root`
- Onafhankelijke verifier: `codex-hypatia`

## Scope

| Pad | path_b64 | Regelbereik | Symbolen | Object-ID |
|---|---|---:|---:|---|
| `src/database/migrations/fix_category_constraint.sql` | `c3JjL2RhdGFiYXNlL21pZ3JhdGlvbnMvZml4X2NhdGVnb3J5X2NvbnN0cmFpbnQuc3Fs` | `1-123` | 0 | `c5b0b02042c3fe8dbe474019301fe54e5180e479` |
| `src/database/migrations/reset_with_category_support.sql` | `c3JjL2RhdGFiYXNlL21pZ3JhdGlvbnMvcmVzZXRfd2l0aF9jYXRlZ29yeV9zdXBwb3J0LnNxbA==` | `1-116` | 0 | `5a7c2a7245564ef773d26d8f8a448e35a6d59bbb` |
| `src/database/migrations/v5_migration.py` | `c3JjL2RhdGFiYXNlL21pZ3JhdGlvbnMvdjVfbWlncmF0aW9uLnB5` | `1-534` | 10 | `a951dbc60a6da5b34d92e921b4c5b9167bae9c7a` |
| `src/database/migrations/v6_migration.py` | `c3JjL2RhdGFiYXNlL21pZ3JhdGlvbnMvdjZfbWlncmF0aW9uLnB5` | `1-312` | 9 | `9723b8037efb039b07af9472d3ab9aa6d250f253` |
| `src/database/migrations/v7_migration.py` | `c3JjL2RhdGFiYXNlL21pZ3JhdGlvbnMvdjdfbWlncmF0aW9uLnB5` | `1-203` | 7 | `92f1ce52f83adfd6f9413e010882c8fa709fef56` |
| `src/database/models.py` | `c3JjL2RhdGFiYXNlL21vZGVscy5weQ==` | `1-225` | 19 | `d1c3ea051db64d90f4f2b827a038b2de2e6a47d7` |
| `src/database/schema.sql` | `c3JjL2RhdGFiYXNlL3NjaGVtYS5zcWw=` | `1-556` | 0 | `8dcde92cbc7e4ff1f1ff849ab8ba57f0e93ab31e` |
| `src/database/synonym_sync.py` | `c3JjL2RhdGFiYXNlL3N5bm9ueW1fc3luYy5weQ==` | `1-182` | 4 | `d1d83ba837a875f4be0e58000253cc19ce0d1a82` |
| `src/database/voorbeelden_repository.py` | `c3JjL2RhdGFiYXNlL3Zvb3JiZWVsZGVuX3JlcG9zaXRvcnkucHk=` | `1-457` | 12 | `684a2f9d4208fd6df00f1d2416e69e8e7e7cc167` |
| `src/repositories/__init__.py` | `c3JjL3JlcG9zaXRvcmllcy9fX2luaXRfXy5weQ==` | `1-13` | 1 | `b838d761e1b7f25ef99227e541f77455b3473c6d` |
| `src/repositories/synonym_registry.py` | `c3JjL3JlcG9zaXRvcmllcy9zeW5vbnltX3JlZ2lzdHJ5LnB5` | `1-1188` | 26 | `e3d5b59549eb995b45c9663ae53a1518722ebfd3` |

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

- P1/proven: `B010-001` — SQLite backup omits committed WAL data but verifies successfully.
- P1/proven: `B010-002` — Synonym uniqueness ignores per-definition ownership.
- P1/proven: `B010-003` — Synonym synchronization commits partially after failure.
- P2/proven: `B010-004` — Production schema seeds invalid test definitions.
- P2/proven: `B010-005` — Fresh schema contradicts migration version seven.
- P2/proven: `B010-006` — SynonymRegistry leaks SQLite connections.
- P3/proven: `B010-007` — Dormant category migration fails on the current schema.
- Volledig bewijs en niet-geteste onderdelen: `evidence/BATCH-010/review-evidence.md`.

## Resultaat

Geverifieerd door twee verschillende reviewers. Alle 11 bestanden en 88 symbolen zijn line-by-line beoordeeld; functionele beperkingen en niet-geteste externe of visuele flows staan expliciet in het bewijsdossier.
