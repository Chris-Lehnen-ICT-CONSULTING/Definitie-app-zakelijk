# BATCH-090

- Status: `verified`
- Reviewgroep: `14` — Integration-, contract-, smoke-, performance- en archived-tests
- Review-base: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Membership-SHA256: `41bb15f7c8fc4bfd682d8cf1aeaeddbc91713c31568e14cda5ed3c1362a1244e`
- Bestanden: `7`
- Fysieke regels: `2321`
- Python-symbolen: `138`
- Reviewer: `codex-kierkegaard`
- Onafhankelijke verifier: `codex-hypatia`

## Scope

| Pad | path_b64 | Regelbereik | Symbolen | Object-ID |
|---|---|---:|---:|---|
| `tests/integration/services/test_brave_search_integration.py` | `dGVzdHMvaW50ZWdyYXRpb24vc2VydmljZXMvdGVzdF9icmF2ZV9zZWFyY2hfaW50ZWdyYXRpb24ucHk=` | `1-471` | 65 | `05f3946692a5048b92cff4c8007a9232fdcb27c6` |
| `tests/integration/services/web_lookup/test_e2e_orchestrator_prompt.py` | `dGVzdHMvaW50ZWdyYXRpb24vc2VydmljZXMvd2ViX2xvb2t1cC90ZXN0X2UyZV9vcmNoZXN0cmF0b3JfcHJvbXB0LnB5` | `1-158` | 19 | `a2aa5ce0ffbe40e532122a180a4fc4c8116cb57c` |
| `tests/integration/services/web_lookup/test_orchestrator_integration.py` | `dGVzdHMvaW50ZWdyYXRpb24vc2VydmljZXMvd2ViX2xvb2t1cC90ZXN0X29yY2hlc3RyYXRvcl9pbnRlZ3JhdGlvbi5weQ==` | `1-133` | 18 | `f66e5d84465aaf72990d0b731258152ed540ead1` |
| `tests/integration/services/web_lookup/test_sru_integration.py` | `dGVzdHMvaW50ZWdyYXRpb24vc2VydmljZXMvd2ViX2xvb2t1cC90ZXN0X3NydV9pbnRlZ3JhdGlvbi5weQ==` | `1-176` | 6 | `6af9d74847dd55cf5731709fe3871a6a9d0aba92` |
| `tests/integration/test_def_154_prompt_module_pipeline.py` | `dGVzdHMvaW50ZWdyYXRpb24vdGVzdF9kZWZfMTU0X3Byb21wdF9tb2R1bGVfcGlwZWxpbmUucHk=` | `1-919` | 12 | `40144ebc040a311221b7f67b51334979547aada6` |
| `tests/integration/test_definition_save_integration.py` | `dGVzdHMvaW50ZWdyYXRpb24vdGVzdF9kZWZpbml0aW9uX3NhdmVfaW50ZWdyYXRpb24ucHk=` | `1-228` | 14 | `2fd41ccb352485dbbc33ef402946dfdfbcd64d04` |
| `tests/integration/test_duplicate_detection_fix.py` | `dGVzdHMvaW50ZWdyYXRpb24vdGVzdF9kdXBsaWNhdGVfZGV0ZWN0aW9uX2ZpeC5weQ==` | `1-236` | 4 | `4febcd89de44482884bb030399909b865ef473e2` |

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

- P2/proven: `B090-001` — Duplicate integration tests delete from the default application database.
- P2/proven: `B090-002` — Offline orchestrator test can reach the global examples generator.
- P2/proven: `B090-003` — SRU integration performs real HTTP and includes a vacuous dead-endpoint case.
- P3/proven: `B090-004` — Brave integration can pass without exercising Brave.
- P3/proven: `B090-005` — DEF-154 pipeline fabricates token savings and module reads.
- P3/proven: `B090-006` — Definition-save tests neither verify metadata nor concurrency.

## Resultaat

Geverifieerd door twee verschillende reviewers. Alle 7 bestanden, 2321 fysieke regels en 138 symbolen zijn line-by-line beoordeeld; gerichte tests, veilige reproducties en beperkingen staan in het bewijsdossier.
