# BATCH-084

- Status: `verified`
- Reviewgroep: `14` — Integration-, contract-, smoke-, performance- en archived-tests
- Review-base: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Membership-SHA256: `5c711722dd913dee53e91ba635a8cefd6ae60d4afb219201e3d1c5bb0b4c5c5b`
- Bestanden: `20`
- Fysieke regels: `1726`
- Python-symbolen: `105`
- Reviewer: `codex-kierkegaard`
- Onafhankelijke verifier: `codex-hypatia`

## Scope

| Pad | path_b64 | Regelbereik | Symbolen | Object-ID |
|---|---|---:|---:|---|
| `tests/README.md` | `dGVzdHMvUkVBRE1FLm1k` | `1-347` | 0 | `ea3c4681a9137b0b6732d502d15ae73b8427ca49` |
| `tests/__init__.py` | `dGVzdHMvX19pbml0X18ucHk=` | `1-7` | 1 | `efb222e13d641c4ba005c9bc55be60d9d091189f` |
| `tests/ci/test_check_namespace_collisions.py` | `dGVzdHMvY2kvdGVzdF9jaGVja19uYW1lc3BhY2VfY29sbGlzaW9ucy5weQ==` | `1-314` | 30 | `2a1c5ade9792756799cb35198f0fb5bc9bcf1e75` |
| `tests/conftest.py` | `dGVzdHMvY29uZnRlc3QucHk=` | `1-408` | 35 | `950fe4d39ed379e80ba7ff6d96be26615b85d5a5` |
| `tests/fixtures/__init__.py` | `dGVzdHMvZml4dHVyZXMvX19pbml0X18ucHk=` | `1-1` | 1 | `bcb1fa1d922aeac11d16def10f0e6a836e1c2e99` |
| `tests/fixtures/circular_reference_synoniemen.yaml` | `dGVzdHMvZml4dHVyZXMvY2lyY3VsYXJfcmVmZXJlbmNlX3N5bm9uaWVtZW4ueWFtbA==` | `1-16` | 0 | `94f664e8de7f8d68605e24535cff874ef3131977` |
| `tests/fixtures/cross_contamination_synoniemen.yaml` | `dGVzdHMvZml4dHVyZXMvY3Jvc3NfY29udGFtaW5hdGlvbl9zeW5vbmllbWVuLnlhbWw=` | `1-20` | 0 | `e70be8a68569919532e6f082e1e34bb22b397c93` |
| `tests/fixtures/duplicate_synoniemen.yaml` | `dGVzdHMvZml4dHVyZXMvZHVwbGljYXRlX3N5bm9uaWVtZW4ueWFtbA==` | `1-12` | 0 | `d6d72627f930cb51ea5845d570a69dcdcded0b0f` |
| `tests/fixtures/empty_list_synoniemen.yaml` | `dGVzdHMvZml4dHVyZXMvZW1wdHlfbGlzdF9zeW5vbmllbWVuLnlhbWw=` | `1-11` | 0 | `4e4dbd3bd8bb03603187ba3087e55efd11abcce1` |
| `tests/fixtures/import/test_import_100_rows.csv` | `dGVzdHMvZml4dHVyZXMvaW1wb3J0L3Rlc3RfaW1wb3J0XzEwMF9yb3dzLmNzdg==` | `1-101` | 0 | `65fd127f86f537b01816863d9c2892ace7782003` |
| `tests/fixtures/import/test_import_10_rows.csv` | `dGVzdHMvZml4dHVyZXMvaW1wb3J0L3Rlc3RfaW1wb3J0XzEwX3Jvd3MuY3N2` | `1-11` | 0 | `d9bd1206691af347a81102b3b21f72138a60827b` |
| `tests/fixtures/import/test_import_200_rows.csv` | `dGVzdHMvZml4dHVyZXMvaW1wb3J0L3Rlc3RfaW1wb3J0XzIwMF9yb3dzLmNzdg==` | `1-201` | 0 | `ea86b01a67cc6186f665cafe0ba820679cf1ebd5` |
| `tests/fixtures/import/test_import_50_rows.csv` | `dGVzdHMvZml4dHVyZXMvaW1wb3J0L3Rlc3RfaW1wb3J0XzUwX3Jvd3MuY3N2` | `1-51` | 0 | `17d13f9bb34955fee2c88d3d442a75c80456e31a` |
| `tests/fixtures/invalid_yaml_synoniemen.yaml` | `dGVzdHMvZml4dHVyZXMvaW52YWxpZF95YW1sX3N5bm9uaWVtZW4ueWFtbA==` | `1-7` | 0 | `8f0802e0ba40f2af14475f2dacd93d0a6d0ad48a` |
| `tests/fixtures/normalization_issues_synoniemen.yaml` | `dGVzdHMvZml4dHVyZXMvbm9ybWFsaXphdGlvbl9pc3N1ZXNfc3lub25pZW1lbi55YW1s` | `1-16` | 0 | `9e371ae9b269f72be9f25661396b01b4495f150e` |
| `tests/fixtures/streamlit_mock.py` | `dGVzdHMvZml4dHVyZXMvc3RyZWFtbGl0X21vY2sucHk=` | `1-118` | 29 | `e262412116f90537815366c11c49f7cbf4e9608d` |
| `tests/fixtures/valid_synoniemen.yaml` | `dGVzdHMvZml4dHVyZXMvdmFsaWRfc3lub25pZW1lbi55YW1s` | `1-22` | 0 | `cd2956b1048566e1e7f84913ff570c86378bd414` |
| `tests/fixtures/web_lookup_mocks.py` | `dGVzdHMvZml4dHVyZXMvd2ViX2xvb2t1cF9tb2Nrcy5weQ==` | `1-54` | 7 | `636efbcc5cdc913c9cc28f2b8d67853ac0ddb8e6` |
| `tests/import_test.py` | `dGVzdHMvaW1wb3J0X3Rlc3QucHk=` | `1-9` | 1 | `72322dcc297c877c910516c5ba27361980b76e18` |
| `tests/integration/__init__.py` | `dGVzdHMvaW50ZWdyYXRpb24vX19pbml0X18ucHk=` | `0-0` | 1 | `e69de29bb2d1d6434b8b29ae775ad8c2e48c5391` |

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

- P3/proven: `B084-001` — Import smoke file collects no tests while printing success.
- P3/proven: `B084-002` — Test README reports obsolete paths and evidence.
- P3/proven: `B084-003` — Benchmark fallback fixture is structurally unreachable.
- P3/suspected: `B084-004` — Outbound-network block starts too late for collection and session setup.

## Resultaat

Geverifieerd door twee verschillende reviewers. Alle 20 bestanden, 1726 fysieke regels en 105 symbolen zijn line-by-line beoordeeld; gerichte tests, veilige reproducties en beperkingen staan in het bewijsdossier.
