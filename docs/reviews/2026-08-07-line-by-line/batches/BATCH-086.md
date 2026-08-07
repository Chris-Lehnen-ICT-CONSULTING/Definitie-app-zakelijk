# BATCH-086

- Status: `pending`
- Reviewgroep: `14` — Integration-, contract-, smoke-, performance- en archived-tests
- Review-base: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Membership-SHA256: `1e946725c647ac8cbec76061232b38d6607b4751025856b1766504cf33bddf19`
- Bestanden: `13`
- Fysieke regels: `3664`
- Python-symbolen: `133`
- Reviewer: ``
- Onafhankelijke verifier: ``

## Scope

| Pad | path_b64 | Regelbereik | Symbolen | Object-ID |
|---|---|---:|---:|---|
| `tests/integration/database/test_unique_constraint_removal.py` | `dGVzdHMvaW50ZWdyYXRpb24vZGF0YWJhc2UvdGVzdF91bmlxdWVfY29uc3RyYWludF9yZW1vdmFsLnB5` | `1-560` | 17 | `a2f723d3b7efbafebaf9fb64bb75ae196da042e7` |
| `tests/integration/functionality/test_bulk_with_delay.py` | `dGVzdHMvaW50ZWdyYXRpb24vZnVuY3Rpb25hbGl0eS90ZXN0X2J1bGtfd2l0aF9kZWxheS5weQ==` | `1-144` | 3 | `62f24377138a7c38f5fc26638c6ff05c25354011` |
| `tests/integration/functionality/test_deep_functionality.py` | `dGVzdHMvaW50ZWdyYXRpb24vZnVuY3Rpb25hbGl0eS90ZXN0X2RlZXBfZnVuY3Rpb25hbGl0eS5weQ==` | `1-310` | 8 | `658e2d61844234a1984d8a6a62a672a600831853` |
| `tests/integration/functionality/test_final_functionality.py` | `dGVzdHMvaW50ZWdyYXRpb24vZnVuY3Rpb25hbGl0eS90ZXN0X2ZpbmFsX2Z1bmN0aW9uYWxpdHkucHk=` | `1-255` | 5 | `b136d89d99f3ea3c8d1b59b603eabe1ddf552dcc` |
| `tests/integration/functionality/test_metadata_fields.py` | `dGVzdHMvaW50ZWdyYXRpb24vZnVuY3Rpb25hbGl0eS90ZXN0X21ldGFkYXRhX2ZpZWxkcy5weQ==` | `1-108` | 2 | `9e619ce4395b7a71db8865a7a554611a8f6bbb05` |
| `tests/integration/functionality/test_simple_functionality.py` | `dGVzdHMvaW50ZWdyYXRpb24vZnVuY3Rpb25hbGl0eS90ZXN0X3NpbXBsZV9mdW5jdGlvbmFsaXR5LnB5` | `1-169` | 4 | `7601a6bb393d98395a7aec9847e90fa85d013db3` |
| `tests/integration/golden/test_data.py` | `dGVzdHMvaW50ZWdyYXRpb24vZ29sZGVuL3Rlc3RfZGF0YS5weQ==` | `1-141` | 1 | `195b854588880e730defa654a9237222dc9c83f3` |
| `tests/integration/performance/test_context_flow_performance.py` | `dGVzdHMvaW50ZWdyYXRpb24vcGVyZm9ybWFuY2UvdGVzdF9jb250ZXh0X2Zsb3dfcGVyZm9ybWFuY2UucHk=` | `1-624` | 36 | `a3c60b4db5a637b06e66b230f90d03208a1b9ff1` |
| `tests/integration/performance/test_def110_regression.py` | `dGVzdHMvaW50ZWdyYXRpb24vcGVyZm9ybWFuY2UvdGVzdF9kZWYxMTBfcmVncmVzc2lvbi5weQ==` | `1-308` | 9 | `b8cf1cf4dd0ce66d76444723ce2845d6e9b266df` |
| `tests/integration/performance/test_def138_performance.py` | `dGVzdHMvaW50ZWdyYXRpb24vcGVyZm9ybWFuY2UvdGVzdF9kZWYxMzhfcGVyZm9ybWFuY2UucHk=` | `1-196` | 11 | `91d81663c42ef0445e3b90d4914ce0bd3dbb86b7` |
| `tests/integration/performance/test_def66_lazy_loading.py` | `dGVzdHMvaW50ZWdyYXRpb24vcGVyZm9ybWFuY2UvdGVzdF9kZWY2Nl9sYXp5X2xvYWRpbmcucHk=` | `1-254` | 12 | `2b77e774e9d7c8820739754d7b421bf3580fe588` |
| `tests/integration/performance/test_def90_validation_lazy_loading.py` | `dGVzdHMvaW50ZWdyYXRpb24vcGVyZm9ybWFuY2UvdGVzdF9kZWY5MF92YWxpZGF0aW9uX2xhenlfbG9hZGluZy5weQ==` | `1-319` | 16 | `b34b6fd0cc3f656dda5c984841a9b5c0a73331f3` |
| `tests/integration/performance/test_parallel_voorbeelden.py` | `dGVzdHMvaW50ZWdyYXRpb24vcGVyZm9ybWFuY2UvdGVzdF9wYXJhbGxlbF92b29yYmVlbGRlbi5weQ==` | `1-276` | 9 | `325827eab9836442fc0ef212dca15d67fcf9c963` |

## Verplichte reviewchecklist

- [ ] Iedere toegewezen regel rechtstreeks uit het immutable object-ID gelezen.
- [ ] Ieder toegewezen symbool en iedere functie line-by-line beoordeeld.
- [ ] Callers, afhankelijkheden, tests en foutpaden gecontroleerd.
- [ ] Codekwaliteit en architectuur beoordeeld.
- [ ] Bugs, security en foutafhandeling beoordeeld.
- [ ] Functionaliteit en relevante tests beoordeeld.
- [ ] UI/UX, toegankelijkheid en responsive gedrag beoordeeld indien van toepassing.
- [ ] Findings bevatten prioriteit, bewijs, reproductie en oplossing.
- [ ] Bewezen, vermoed en niet-getest expliciet onderscheiden.
- [ ] Onafhankelijke tweede reviewer heeft scope en findings geverifieerd.

## Bevindingen

Nog niet geregistreerd.

## Resultaat

Nog niet uitgevoerd.
