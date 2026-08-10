# BATCH-051

- Status: `verified`
- Reviewgroep: `13` — Unit-tests gekoppeld aan productieonderdelen
- Review-base: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Membership-SHA256: `0b3404c1bdef380684446a2c12fdfffd0aa41019fcab9e067386ae92fe60fb01`
- Bestanden: `13`
- Fysieke regels: `1644`
- Python-symbolen: `148`
- Reviewer: `codex-root`
- Onafhankelijke verifier: `codex-galileo`

## Scope

| Pad | path_b64 | Regelbereik | Symbolen | Object-ID |
|---|---|---:|---:|---|
| `tests/unit/__init__.py` | `dGVzdHMvdW5pdC9fX2luaXRfXy5weQ==` | `0-0` | 1 | `e69de29bb2d1d6434b8b29ae775ad8c2e48c5391` |
| `tests/unit/api/test_feature_status_api.py` | `dGVzdHMvdW5pdC9hcGkvdGVzdF9mZWF0dXJlX3N0YXR1c19hcGkucHk=` | `1-153` | 23 | `7c3d21070d0478025b83d67227bb4f01f102f626` |
| `tests/unit/api/test_uvicorn_pii_redaction.py` | `dGVzdHMvdW5pdC9hcGkvdGVzdF91dmljb3JuX3BpaV9yZWRhY3Rpb24ucHk=` | `1-99` | 8 | `1451b7fb5cc1c5a84bfcaecc46240afc68741905` |
| `tests/unit/config/test_dotenv_loader.py` | `dGVzdHMvdW5pdC9jb25maWcvdGVzdF9kb3RlbnZfbG9hZGVyLnB5` | `1-230` | 19 | `7c756102bb56d015395fce2db1968d9b2008ede2` |
| `tests/unit/conftest.py` | `dGVzdHMvdW5pdC9jb25mdGVzdC5weQ==` | `1-41` | 2 | `c15a7eaa8d18aaa8dfd7135e7bc4e8a0823bc6bc` |
| `tests/unit/database/test_v6_migration.py` | `dGVzdHMvdW5pdC9kYXRhYmFzZS90ZXN0X3Y2X21pZ3JhdGlvbi5weQ==` | `1-373` | 36 | `3c8462ad2226f9cf5e909f905d4cc2fd80ed6165` |
| `tests/unit/database/test_voorbeelden_voorkeursterm.py` | `dGVzdHMvdW5pdC9kYXRhYmFzZS90ZXN0X3Zvb3JiZWVsZGVuX3Zvb3JrZXVyc3Rlcm0ucHk=` | `1-109` | 8 | `2cfaaa40eec39f3a52885feb13d0c09855776c5f` |
| `tests/unit/document_processing/test_document_processor_cache_bounds.py` | `dGVzdHMvdW5pdC9kb2N1bWVudF9wcm9jZXNzaW5nL3Rlc3RfZG9jdW1lbnRfcHJvY2Vzc29yX2NhY2hlX2JvdW5kcy5weQ==` | `1-109` | 10 | `167e552c61d7218fe6e4a02e3808f49db170d8ae` |
| `tests/unit/document_processing/test_document_processor_exceptions.py` | `dGVzdHMvdW5pdC9kb2N1bWVudF9wcm9jZXNzaW5nL3Rlc3RfZG9jdW1lbnRfcHJvY2Vzc29yX2V4Y2VwdGlvbnMucHk=` | `1-206` | 12 | `249448e7de2ab3fcfb695c4d026df13d7c5a7bfc` |
| `tests/unit/document_processing/test_document_processor_placeholders.py` | `dGVzdHMvdW5pdC9kb2N1bWVudF9wcm9jZXNzaW5nL3Rlc3RfZG9jdW1lbnRfcHJvY2Vzc29yX3BsYWNlaG9sZGVycy5weQ==` | `1-32` | 2 | `e1e92b6185563520b498fb0c6a104eb1cdc86b05` |
| `tests/unit/prompt/test_prompt_snippet_injection.py` | `dGVzdHMvdW5pdC9wcm9tcHQvdGVzdF9wcm9tcHRfc25pcHBldF9pbmplY3Rpb24ucHk=` | `1-91` | 4 | `ff0122ac882881305afe4c31df195bb0e8ec3fbe` |
| `tests/unit/prompt/test_rag_token_budget.py` | `dGVzdHMvdW5pdC9wcm9tcHQvdGVzdF9yYWdfdG9rZW5fYnVkZ2V0LnB5` | `1-201` | 22 | `4d5e5460c18bb1847db77d6b623a224720744431` |
| `tests/unit/scripts/__init__.py` | `dGVzdHMvdW5pdC9zY3JpcHRzL19faW5pdF9fLnB5` | `0-0` | 1 | `e69de29bb2d1d6434b8b29ae775ad8c2e48c5391` |

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

- P2/proven: `B051-001` — Dotenv guard misses common load_dotenv call shapes.
- P2/proven: `B051-002` — V6 verifier accepts rows with NULL metadata.
- P3/proven: `B051-003` — Document-processor exception tests contain vacuous alternatives.
- P3/proven: `B051-004` — Placeholder test writes persistent metadata to a hardcoded data path.
- P3/proven: `B051-005` — RAG budget tests permit an oversized first chunk.

## Resultaat

Geverifieerd door twee verschillende reviewers. Alle 13 bestanden, 1644 fysieke regels en 148 symbolen zijn line-by-line beoordeeld; gerichte tests, veilige reproducties en beperkingen staan in het bewijsdossier.
