# BATCH-091

- Status: `verified`
- Reviewgroep: `14` — Integration-, contract-, smoke-, performance- en archived-tests
- Review-base: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Membership-SHA256: `03071385a068b7ae8beb0164067dc8a7c4f9bb3d61594b23dc6b225ad8356b5e`
- Bestanden: `8`
- Fysieke regels: `2744`
- Python-symbolen: `113`
- Reviewer: `codex-kierkegaard`
- Onafhankelijke verifier: `codex-hypatia`

## Scope

| Pad | path_b64 | Regelbereik | Symbolen | Object-ID |
|---|---|---:|---:|---|
| `tests/integration/test_export_levels_comprehensive.py` | `dGVzdHMvaW50ZWdyYXRpb24vdGVzdF9leHBvcnRfbGV2ZWxzX2NvbXByZWhlbnNpdmUucHk=` | `1-703` | 25 | `46906eaebae4a5609971bea48bddda950720066d` |
| `tests/integration/test_history_removal.py` | `dGVzdHMvaW50ZWdyYXRpb24vdGVzdF9oaXN0b3J5X3JlbW92YWwucHk=` | `1-377` | 18 | `ba1a74006815e2b8e39f57d392db46fef718cd5a` |
| `tests/integration/test_legacy_vs_new_parity.py` | `dGVzdHMvaW50ZWdyYXRpb24vdGVzdF9sZWdhY3lfdnNfbmV3X3Bhcml0eS5weQ==` | `1-419` | 19 | `d2a6f526625d91521a3a1aa64d85e855d8718b76` |
| `tests/integration/test_modular_prompt_builder.py` | `dGVzdHMvaW50ZWdyYXRpb24vdGVzdF9tb2R1bGFyX3Byb21wdF9idWlsZGVyLnB5` | `1-133` | 9 | `9cab3fc35611494b906da7a2af6f5cc10f3ef1f9` |
| `tests/integration/test_ontology_integration.py` | `dGVzdHMvaW50ZWdyYXRpb24vdGVzdF9vbnRvbG9neV9pbnRlZ3JhdGlvbi5weQ==` | `1-89` | 2 | `78eb569c8b5e05a9845243a4d3a523493dbcb681` |
| `tests/integration/test_per007_acceptance.py` | `dGVzdHMvaW50ZWdyYXRpb24vdGVzdF9wZXIwMDdfYWNjZXB0YW5jZS5weQ==` | `1-426` | 10 | `350f1c070e9d573b6e5a4ea7bdefcc7c1de3b283` |
| `tests/integration/test_per007_single_source_red.py` | `dGVzdHMvaW50ZWdyYXRpb24vdGVzdF9wZXIwMDdfc2luZ2xlX3NvdXJjZV9yZWQucHk=` | `1-204` | 8 | `88bc3f5e42243eb65ad951fe2c2a70a749e90947` |
| `tests/integration/test_prompt_security_and_edge_cases.py` | `dGVzdHMvaW50ZWdyYXRpb24vdGVzdF9wcm9tcHRfc2VjdXJpdHlfYW5kX2VkZ2VfY2FzZXMucHk=` | `1-393` | 22 | `55aefa00dcf294fee591bc2bf76b9e68df0bb1d0` |

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

- P2/proven: `B091-001` — Legacy parity suite compares the same current implementation.
- P2/proven: `B091-002` — Ontology integration leaks environment state and passes after traceback.
- P2/proven: `B091-003` — PER-007 acceptance suite uses a removed context-manager constructor.
- P2/proven: `B091-004` — Intentionally red PER-007 tests remain normal integration tests.
- P3/proven: `B091-005` — History-removal tests swallow arbitrary failures and use the default database.

## Resultaat

Geverifieerd door twee verschillende reviewers. Alle 8 bestanden, 2744 fysieke regels en 113 symbolen zijn line-by-line beoordeeld; gerichte tests, veilige reproducties en beperkingen staan in het bewijsdossier.
