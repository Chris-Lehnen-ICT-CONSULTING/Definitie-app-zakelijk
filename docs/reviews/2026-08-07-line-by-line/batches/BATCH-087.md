# BATCH-087

- Status: `verified`
- Reviewgroep: `14` — Integration-, contract-, smoke-, performance- en archived-tests
- Review-base: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Membership-SHA256: `713f0e3cbc60991c3b86569e814514d1a282c09f3c4bbb21bca9365f336d9fb9`
- Bestanden: `9`
- Fysieke regels: `3136`
- Python-symbolen: `144`
- Reviewer: `codex-hypatia`
- Onafhankelijke verifier: `codex-kierkegaard`

## Scope

| Pad | path_b64 | Regelbereik | Symbolen | Object-ID |
|---|---|---:|---:|---|
| `tests/integration/performance/test_per007_performance.py` | `dGVzdHMvaW50ZWdyYXRpb24vcGVyZm9ybWFuY2UvdGVzdF9wZXIwMDdfcGVyZm9ybWFuY2UucHk=` | `1-357` | 11 | `359859f354c394bc762c5e8d7218e32ca5481250` |
| `tests/integration/performance/test_performance.py` | `dGVzdHMvaW50ZWdyYXRpb24vcGVyZm9ybWFuY2UvdGVzdF9wZXJmb3JtYW5jZS5weQ==` | `1-642` | 32 | `9476dc7dcfd84ac753294d69738e07d04aeab664` |
| `tests/integration/performance/test_performance_comprehensive.py` | `dGVzdHMvaW50ZWdyYXRpb24vcGVyZm9ybWFuY2UvdGVzdF9wZXJmb3JtYW5jZV9jb21wcmVoZW5zaXZlLnB5` | `1-628` | 46 | `a9557bd491fbf10c494581730f6067ad4481e891` |
| `tests/integration/performance/test_rule_cache_performance.py` | `dGVzdHMvaW50ZWdyYXRpb24vcGVyZm9ybWFuY2UvdGVzdF9ydWxlX2NhY2hlX3BlcmZvcm1hbmNlLnB5` | `1-166` | 9 | `1c58eebfcdff13ef05874363a0730e2a467597fb` |
| `tests/integration/performance/test_story_2_4_performance.py` | `dGVzdHMvaW50ZWdyYXRpb24vcGVyZm9ybWFuY2UvdGVzdF9zdG9yeV8yXzRfcGVyZm9ybWFuY2UucHk=` | `1-630` | 18 | `ee5df208601a469a51010ea3485772b02aa4df6a` |
| `tests/integration/performance/test_validation_performance_baseline.py` | `dGVzdHMvaW50ZWdyYXRpb24vcGVyZm9ybWFuY2UvdGVzdF92YWxpZGF0aW9uX3BlcmZvcm1hbmNlX2Jhc2VsaW5lLnB5` | `1-381` | 16 | `3cffb829e0d638553b57ce965d4d2cc8e3eefbb9` |
| `tests/integration/regression/test_categorie_complete_flow.py` | `dGVzdHMvaW50ZWdyYXRpb24vcmVncmVzc2lvbi90ZXN0X2NhdGVnb3JpZV9jb21wbGV0ZV9mbG93LnB5` | `1-162` | 3 | `15257bd6ead40bc33037e33a89a369911cb96e59` |
| `tests/integration/regression/test_category_regeneration.py` | `dGVzdHMvaW50ZWdyYXRpb24vcmVncmVzc2lvbi90ZXN0X2NhdGVnb3J5X3JlZ2VuZXJhdGlvbi5weQ==` | `1-93` | 7 | `ad9616c435eecbe228482c4656eb8758001ad06f` |
| `tests/integration/regression/test_legacy_activation.py` | `dGVzdHMvaW50ZWdyYXRpb24vcmVncmVzc2lvbi90ZXN0X2xlZ2FjeV9hY3RpdmF0aW9uLnB5` | `1-77` | 2 | `30eebe1dae627619d3e50c59d2121eccbcf2f627` |

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

- P2/proven: `B087-001` — PER-007 performance suite never reaches its criteria.
- P3/proven: `B087-002` — Rule-cache performance test patches after singleton caches are warm.
- P3/proven: `B087-003` — Performance suites retain stale skips and measure test sleeps.
- P2/proven: `B087-004` — Category regeneration regression targets a removed UI method.
- P3/proven: `B087-005` — Legacy activation test converts prompt failures into a pass.

## Resultaat

Geverifieerd door twee verschillende reviewers. Alle 9 bestanden, 3136 fysieke regels en 144 symbolen zijn line-by-line beoordeeld; gerichte tests, veilige reproducties en beperkingen staan in het bewijsdossier.
