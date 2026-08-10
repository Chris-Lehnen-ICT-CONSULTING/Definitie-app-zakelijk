# BATCH-061

- Status: `verified`
- Reviewgroep: `13` — Unit-tests gekoppeld aan productieonderdelen
- Review-base: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Membership-SHA256: `92192461faceae33e7874868a6c5518684bc9d81ff6ec69cb03f5802315fa1d8`
- Bestanden: `10`
- Fysieke regels: `1927`
- Python-symbolen: `126`
- Reviewer: `codex-galileo`
- Onafhankelijke verifier: `codex-hypatia`

## Scope

| Pad | path_b64 | Regelbereik | Symbolen | Object-ID |
|---|---|---:|---:|---|
| `tests/unit/services/test_export_stille_overslaan.py` | `dGVzdHMvdW5pdC9zZXJ2aWNlcy90ZXN0X2V4cG9ydF9zdGlsbGVfb3ZlcnNsYWFuLnB5` | `1-295` | 19 | `998f697cceacbdefa110bf820fcd3ba131b5b819` |
| `tests/unit/services/test_modern_web_lookup_service_unit.py` | `dGVzdHMvdW5pdC9zZXJ2aWNlcy90ZXN0X21vZGVybl93ZWJfbG9va3VwX3NlcnZpY2VfdW5pdC5weQ==` | `1-398` | 40 | `845408f0ab64e5bd0464d6a0e38a6de7670dca11` |
| `tests/unit/services/test_modular_validation_aggregation.py` | `dGVzdHMvdW5pdC9zZXJ2aWNlcy90ZXN0X21vZHVsYXJfdmFsaWRhdGlvbl9hZ2dyZWdhdGlvbi5weQ==` | `1-217` | 7 | `477de249595c1e3fa56d935eae730f24c739db74` |
| `tests/unit/services/test_modular_validation_determinism.py` | `dGVzdHMvdW5pdC9zZXJ2aWNlcy90ZXN0X21vZHVsYXJfdmFsaWRhdGlvbl9kZXRlcm1pbmlzbS5weQ==` | `1-197` | 6 | `144970132c2655b14fada07a6e93d3f2bc9d3402` |
| `tests/unit/services/test_modular_validation_heuristics.py` | `dGVzdHMvdW5pdC9zZXJ2aWNlcy90ZXN0X21vZHVsYXJfdmFsaWRhdGlvbl9oZXVyaXN0aWNzLnB5` | `1-72` | 5 | `906c7d56426e64086e19aa195b022400c93a1be1` |
| `tests/unit/services/test_modular_validation_race_condition.py` | `dGVzdHMvdW5pdC9zZXJ2aWNlcy90ZXN0X21vZHVsYXJfdmFsaWRhdGlvbl9yYWNlX2NvbmRpdGlvbi5weQ==` | `1-268` | 8 | `940bd3cf5a861907fcf07e1047bb849890cd8e99` |
| `tests/unit/services/test_module_adapter_error_isolation.py` | `dGVzdHMvdW5pdC9zZXJ2aWNlcy90ZXN0X21vZHVsZV9hZGFwdGVyX2Vycm9yX2lzb2xhdGlvbi5weQ==` | `1-54` | 5 | `bb944b2f0fc0e6c9b722b8c73c8345194dbea892` |
| `tests/unit/services/test_pandas3_na_contract.py` | `dGVzdHMvdW5pdC9zZXJ2aWNlcy90ZXN0X3BhbmRhczNfbmFfY29udHJhY3QucHk=` | `1-61` | 5 | `c143697709a5e3f1c5f9ce9eb36ca8c538693d6e` |
| `tests/unit/services/test_security_service.py` | `dGVzdHMvdW5pdC9zZXJ2aWNlcy90ZXN0X3NlY3VyaXR5X3NlcnZpY2UucHk=` | `1-122` | 15 | `cc1c31db3674c70675ddb5331dee18c8f2b817f4` |
| `tests/unit/services/test_service_container.py` | `dGVzdHMvdW5pdC9zZXJ2aWNlcy90ZXN0X3NlcnZpY2VfY29udGFpbmVyLnB5` | `1-243` | 16 | `f6ee62baeaf4c21ad0f8005cbabff567bc00f35f` |

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

- P3/proven: `B061-001` — Concurrent validation test does not force coroutine overlap.
- P3/proven: `B061-002` — Pandas missing-value test copies rather than calls production logic.
- P3/proven: `B061-003` — Web lookup defaults depend on the process working directory.

## Resultaat

Geverifieerd door twee verschillende reviewers. Alle 10 bestanden, 1927 fysieke regels en 126 symbolen zijn line-by-line beoordeeld; gerichte tests, veilige reproducties en beperkingen staan in het bewijsdossier.
