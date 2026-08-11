# BATCH-105

- Status: `verified`
- Reviewgroep: `15` — Operationele scripts en shellcode
- Review-base: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Membership-SHA256: `bee92815e999c9673d449778d991da72c071e969d42407c128e0824f4001f91e`
- Bestanden: `20`
- Fysieke regels: `3232`
- Python-symbolen: `81`
- Reviewer: `codex-root`
- Onafhankelijke verifier: `codex-galileo`

## Scope

| Pad | path_b64 | Regelbereik | Symbolen | Object-ID |
|---|---|---:|---:|---|
| `scripts/test_rechtspraak_rest_fix.py` | `c2NyaXB0cy90ZXN0X3JlY2h0c3ByYWFrX3Jlc3RfZml4LnB5` | `1-114` | 5 | `2fa9c2f0d08be7cfa2d27a0a6e0bdaeb35851ba1` |
| `scripts/test_rechtspraak_scraping.py` | `c2NyaXB0cy90ZXN0X3JlY2h0c3ByYWFrX3NjcmFwaW5nLnB5` | `1-264` | 7 | `0f037c668bec92339d5de5350721bb737c0b3a57` |
| `scripts/test_rechtspraak_search.py` | `c2NyaXB0cy90ZXN0X3JlY2h0c3ByYWFrX3NlYXJjaC5weQ==` | `1-237` | 12 | `8a154fac2238ba397fabe61ac7429aaf64ebdb1e` |
| `scripts/test_sru_endpoints.py` | `c2NyaXB0cy90ZXN0X3NydV9lbmRwb2ludHMucHk=` | `1-221` | 5 | `12276690dff5d3d083cf553ac30ecc004569adaa` |
| `scripts/test_synonym_orchestrator_manual.py` | `c2NyaXB0cy90ZXN0X3N5bm9ueW1fb3JjaGVzdHJhdG9yX21hbnVhbC5weQ==` | `1-344` | 11 | `0bd4548c70fcb20e5406320ef9f727b46304a6b9` |
| `scripts/test_web_lookup_live.py` | `c2NyaXB0cy90ZXN0X3dlYl9sb29rdXBfbGl2ZS5weQ==` | `1-226` | 6 | `6e517c8d75405a54769ca894b8849b40b6f54ce1` |
| `scripts/testing/Makefile.history_removal` | `c2NyaXB0cy90ZXN0aW5nL01ha2VmaWxlLmhpc3RvcnlfcmVtb3ZhbA==` | `1-83` | 0 | `55a766d3593d04754d9a39e7efaf1ec3cd5ee187` |
| `scripts/testing/_marker_utils.py` | `c2NyaXB0cy90ZXN0aW5nL19tYXJrZXJfdXRpbHMucHk=` | `1-72` | 4 | `f1655635b0e188b8d04f6c8467c3ad326047712e` |
| `scripts/testing/add_test_markers.py` | `c2NyaXB0cy90ZXN0aW5nL2FkZF90ZXN0X21hcmtlcnMucHk=` | `1-372` | 13 | `49ca3c16bf4f602e06556aa7b79f40318b3c8569` |
| `scripts/testing/agent_quick_checks.sh` | `c2NyaXB0cy90ZXN0aW5nL2FnZW50X3F1aWNrX2NoZWNrcy5zaA==` | `1-72` | 0 | `7018602f30738f008c16f3260969523c3940a8ff` |
| `scripts/testing/check_test_markers.py` | `c2NyaXB0cy90ZXN0aW5nL2NoZWNrX3Rlc3RfbWFya2Vycy5weQ==` | `1-34` | 2 | `92ced55ba2bcd5a4ecf3fc1ebde467d29b5f51b6` |
| `scripts/testing/final_verification.py` | `c2NyaXB0cy90ZXN0aW5nL2ZpbmFsX3ZlcmlmaWNhdGlvbi5weQ==` | `1-215` | 4 | `022ebdfa8a4caed7d4d696abe7c92ab83d5685e5` |
| `scripts/testing/measure_interface_performance.py` | `c2NyaXB0cy90ZXN0aW5nL21lYXN1cmVfaW50ZXJmYWNlX3BlcmZvcm1hbmNlLnB5` | `1-211` | 4 | `bc871ac51f40efac20ad1810dcc8e434004979e1` |
| `scripts/testing/quick_verify_history_removal.sh` | `c2NyaXB0cy90ZXN0aW5nL3F1aWNrX3ZlcmlmeV9oaXN0b3J5X3JlbW92YWwuc2g=` | `1-63` | 0 | `a23a854b372f8a65e1652ad0c81518c8036a29ae` |
| `scripts/testing/run_per007_tdd.sh` | `c2NyaXB0cy90ZXN0aW5nL3J1bl9wZXIwMDdfdGRkLnNo` | `1-230` | 0 | `937dc172a9e1f96cf08ed4d2838be95baf797d68` |
| `scripts/testing/run_smoke_tests.sh` | `c2NyaXB0cy90ZXN0aW5nL3J1bl9zbW9rZV90ZXN0cy5zaA==` | `1-21` | 0 | `ada3bff79a49e4a5330b283ea04832046b6ad605` |
| `scripts/testing/run_story_2_4_tests.py` | `c2NyaXB0cy90ZXN0aW5nL3J1bl9zdG9yeV8yXzRfdGVzdHMucHk=` | `1-311` | 8 | `12c6b80d42443e1d529453af243dea8ae178e2a7` |
| `scripts/testing/run_tests.sh` | `c2NyaXB0cy90ZXN0aW5nL3J1bl90ZXN0cy5zaA==` | `1-62` | 0 | `a675f5eb09eea9504656854a1201a2702d4cb30f` |
| `scripts/testing/run_web_lookup_smoke.sh` | `c2NyaXB0cy90ZXN0aW5nL3J1bl93ZWJfbG9va3VwX3Ntb2tlLnNo` | `1-7` | 0 | `686c4d5c169549d266786cb94c0d5255d915f857` |
| `scripts/testing/test_auto_load_edit_tab.sh` | `c2NyaXB0cy90ZXN0aW5nL3Rlc3RfYXV0b19sb2FkX2VkaXRfdGFiLnNo` | `1-73` | 0 | `8afa9096365b0ef98b9f188a111731534ac7e17b` |

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

- P2/proven: `B105-001` — Actieve quick-check-workflow slaagt zonder uitvoerbare checks.
- P3/proven: `B105-002` — Markercontrole accepteert modifiers en docstringtekst als classificatie.
- P2/proven: `B105-003` — Live operationele tests rapporteren volledige mislukking met exitcode 0.
- P3/proven: `B105-004` — Gedocumenteerde synonym-orchestrator-test importeert verwijderd modulepad.
- P2/proven: `B105-005` — Migratieverificatie verklaart een lege of andere worktree volledig voltooid.
- P2/proven: `B105-006` — PER-007 TDD-runner slikt een lege falende GREEN- en CONFIRM-run.
- P3/proven: `B105-007` — Story-2.4-runner weigert een geldige gekozen suite wegens drie stale globale paden.
- P3/proven: `B105-008` — Gedocumenteerde fast- en performanceprofielen wijzen naar ontbrekende paden.
- P3/proven: `B105-009` — History-removal-verificatie skipt of slikt de enige pytest-suite.
- P3/proven: `B105-010` — Cachebenchmark accepteert negatieve verbetering zonder cachebewijs.

## Resultaat

Geverifieerd door twee verschillende reviewers. Alle 20 bestanden, 3232 fysieke regels en 81 symbolen zijn line-by-line beoordeeld; gerichte tests, veilige reproducties en beperkingen staan in het bewijsdossier.
