# BATCH-036

- Status: `verified`
- Reviewgroep: `8` — Web lookup, document processing en RAG
- Review-base: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Membership-SHA256: `4117d71c910eb5aa19d870d2181634c498931312912e459bc9b50ba460ccc75e`
- Bestanden: `14`
- Fysieke regels: `3097`
- Python-symbolen: `119`
- Reviewer: `codex-kierkegaard`
- Onafhankelijke verifier: `codex-root`

## Scope

| Pad | path_b64 | Regelbereik | Symbolen | Object-ID |
|---|---|---:|---:|---|
| `src/services/rag/legal_structure_recognizer.py` | `c3JjL3NlcnZpY2VzL3JhZy9sZWdhbF9zdHJ1Y3R1cmVfcmVjb2duaXplci5weQ==` | `1-310` | 13 | `13c17e56818301fa9ad446ac737ebf793f3f3a92` |
| `src/services/rag/models.py` | `c3JjL3NlcnZpY2VzL3JhZy9tb2RlbHMucHk=` | `1-46` | 4 | `8a6d2c28294be75257b83419f1f6273179a037a3` |
| `src/services/rag/rag_management_service.py` | `c3JjL3NlcnZpY2VzL3JhZy9yYWdfbWFuYWdlbWVudF9zZXJ2aWNlLnB5` | `1-335` | 15 | `3084bc17e312bcc1e6ffdd1d777d7fdd72008905` |
| `src/services/rag/rag_service.py` | `c3JjL3NlcnZpY2VzL3JhZy9yYWdfc2VydmljZS5weQ==` | `1-516` | 13 | `9f362083ac3d10f295089806eca659b542fe1db5` |
| `src/services/rag/token_counter.py` | `c3JjL3NlcnZpY2VzL3JhZy90b2tlbl9jb3VudGVyLnB5` | `1-31` | 3 | `9f211b0263cff28a16d2c6f5ed7d520c96ef8050` |
| `src/services/web_lookup/__init__.py` | `c3JjL3NlcnZpY2VzL3dlYl9sb29rdXAvX19pbml0X18ucHk=` | `1-6` | 1 | `ee66bceb1c89c4455139776dceccb2bff82b4f4f` |
| `src/services/web_lookup/brave_search_service.py` | `c3JjL3NlcnZpY2VzL3dlYl9sb29rdXAvYnJhdmVfc2VhcmNoX3NlcnZpY2UucHk=` | `1-354` | 11 | `aefeef07eaa0bf765b9c9e07efb4dc2e7a204cee` |
| `src/services/web_lookup/config_loader.py` | `c3JjL3NlcnZpY2VzL3dlYl9sb29rdXAvY29uZmlnX2xvYWRlci5weQ==` | `1-113` | 5 | `825887e7cf85c9bbae048a35d5b2389c003dc03c` |
| `src/services/web_lookup/context_filter.py` | `c3JjL3NlcnZpY2VzL3dlYl9sb29rdXAvY29udGV4dF9maWx0ZXIucHk=` | `1-235` | 8 | `7c2c629c0c93da98c36777251b2ccba19a56dcdd` |
| `src/services/web_lookup/contracts.py` | `c3JjL3NlcnZpY2VzL3dlYl9sb29rdXAvY29udHJhY3RzLnB5` | `1-51` | 3 | `41cf37952d32ea32ed5a6cbca60a7559b1788812` |
| `src/services/web_lookup/juridisch_ranker.py` | `c3JjL3NlcnZpY2VzL3dlYl9sb29rdXAvanVyaWRpc2NoX3Jhbmtlci5weQ==` | `1-688` | 22 | `9f1a4254ab2f6513315a0355d258738fe089b420` |
| `src/services/web_lookup/provenance.py` | `c3JjL3NlcnZpY2VzL3dlYl9sb29rdXAvcHJvdmVuYW5jZS5weQ==` | `1-151` | 7 | `2155f6d90a88625d505659d9a4663f5240625dc0` |
| `src/services/web_lookup/ranking.py` | `c3JjL3NlcnZpY2VzL3dlYl9sb29rdXAvcmFua2luZy5weQ==` | `1-94` | 6 | `8e387d81fe9b03c9e2ad971da900885beef8d4fe` |
| `src/services/web_lookup/rechtspraak_rest_service.py` | `c3JjL3NlcnZpY2VzL3dlYl9sb29rdXAvcmVjaHRzcHJhYWtfcmVzdF9zZXJ2aWNlLnB5` | `1-167` | 8 | `f5db7ed80c948d3ee46b64e363857cdf3098182b` |

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

- P2/proven: `B036-001` — Offline tokenizer initialization breaks RAG.
- P2/proven: `B036-002` — Concurrent collection creation races on a unique key.
- P2/proven: `B036-003` — Malformed chunk metadata crashes management queries.
- P2/proven: `B036-004` — Trusted legal domains are accepted by substring.

## Resultaat

Geverifieerd door twee verschillende reviewers. Alle 14 bestanden, 3097 fysieke regels en 119 symbolen zijn line-by-line beoordeeld; gerichte tests, veilige reproducties en beperkingen staan in het bewijsdossier.
