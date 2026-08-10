# BATCH-035

- Status: `verified`
- Reviewgroep: `8` — Web lookup, document processing en RAG
- Review-base: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Membership-SHA256: `7bdae370bdb2adcf1d8be81a918847746a752a4dd1d8bf8ebc8d3b7cb3381679`
- Bestanden: `11`
- Fysieke regels: `3902`
- Python-symbolen: `125`
- Reviewer: `codex-galileo`
- Onafhankelijke verifier: `codex-kierkegaard`

## Scope

| Pad | path_b64 | Regelbereik | Symbolen | Object-ID |
|---|---|---:|---:|---|
| `src/document_processing/__init__.py` | `c3JjL2RvY3VtZW50X3Byb2Nlc3NpbmcvX19pbml0X18ucHk=` | `1-25` | 1 | `e1a2bee58bcc04a16e0de526f61e625b6ccca619` |
| `src/document_processing/document_extractor.py` | `c3JjL2RvY3VtZW50X3Byb2Nlc3NpbmcvZG9jdW1lbnRfZXh0cmFjdG9yLnB5` | `1-310` | 13 | `419daabd4dca201efbf448d0b8dab296c5c212e0` |
| `src/document_processing/document_processor.py` | `c3JjL2RvY3VtZW50X3Byb2Nlc3NpbmcvZG9jdW1lbnRfcHJvY2Vzc29yLnB5` | `1-608` | 21 | `ad3c8ff632a6fa4f4404ea085c8d4ad26a240246` |
| `src/services/modern_web_lookup_service.py` | `c3JjL3NlcnZpY2VzL21vZGVybl93ZWJfbG9va3VwX3NlcnZpY2UucHk=` | `1-1229` | 34 | `a235a579681de802fe4a417073139f2afc8dc94b` |
| `src/services/rag/__init__.py` | `c3JjL3NlcnZpY2VzL3JhZy9fX2luaXRfXy5weQ==` | `1-34` | 1 | `295d89b136735e4ff4a0b3c28c1dc151a344d301` |
| `src/services/rag/chunking_strategies.py` | `c3JjL3NlcnZpY2VzL3JhZy9jaHVua2luZ19zdHJhdGVnaWVzLnB5` | `1-690` | 21 | `fdbdae09028e1df7de764ec377aa7a7ac82ba508` |
| `src/services/rag/chunking_utils.py` | `c3JjL3NlcnZpY2VzL3JhZy9jaHVua2luZ191dGlscy5weQ==` | `1-160` | 5 | `e20ba8f6a7536ce84552110def770e93aef3c750` |
| `src/services/rag/constants.py` | `c3JjL3NlcnZpY2VzL3JhZy9jb25zdGFudHMucHk=` | `1-58` | 2 | `c75d0db97a6f504933bc29934349911402a3f307` |
| `src/services/rag/document_chunker.py` | `c3JjL3NlcnZpY2VzL3JhZy9kb2N1bWVudF9jaHVua2VyLnB5` | `1-150` | 5 | `c5d53f029f2e829053d2712ad137f13e028246d8` |
| `src/services/rag/embedding_service.py` | `c3JjL3NlcnZpY2VzL3JhZy9lbWJlZGRpbmdfc2VydmljZS5weQ==` | `1-129` | 8 | `a903a9dcafb033bfd7f6cd30605bd01a95199553` |
| `src/services/rag/embedding_store.py` | `c3JjL3NlcnZpY2VzL3JhZy9lbWJlZGRpbmdfc3RvcmUucHk=` | `1-509` | 14 | `4120879cd91607f9dd0442d9ac362b796822a088` |

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

- P2/proven: `B035-001` — Partial metadata writes are reported as document success.
- P3/proven: `B035-002` — Failure cache ignores MIME type and prevents retry.
- P2/proven: `B035-003` — DOC is advertised but unsupported and DOCX tables are lost.
- P2/suspected: `B035-004` — Document extraction lacks resource limits.
- P2/proven: `B035-005` — RAG overlap and maximum chunk size contracts are ineffective.
- P2/proven: `B035-006` — Duplicate URL reconstruction corrupts ranked results.
- P2/proven: `B035-007` — Substring sr classifies administrative law as criminal law.
- P1/proven: `B035-008` — Singleton web debug state mixes concurrent requests.
- P3/proven: `B035-009` — Every lookup stage receives the full timeout budget.
- P2/proven: `B035-010` — Embedding search materializes the full collection twice.
- P2/suspected: `B035-011` — Global document processor can share session data.
- P3/proven: `B035-012` — Upload UI counts error records as successfully processed.
- Volledig bewijs en niet-geteste onderdelen: `evidence/BATCH-035/review-evidence.md`.

## Resultaat

Geverifieerd door twee verschillende reviewers. Alle 11 bestanden, 3902 fysieke regels en 125 symbolen zijn line-by-line beoordeeld; gerichte tests, veilige reproducties en beperkingen staan in het bewijsdossier.
