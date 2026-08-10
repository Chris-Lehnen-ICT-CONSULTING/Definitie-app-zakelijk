# BATCH-037

- Status: `verified`
- Reviewgroep: `8` — Web lookup, document processing en RAG
- Review-base: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Membership-SHA256: `9ad0d7bc85bd1d829711875d55e886e8602f1d6b511b31059ca743e381e12c83`
- Bestanden: `6`
- Fysieke regels: `3206`
- Python-symbolen: `101`
- Reviewer: `codex-kierkegaard`
- Onafhankelijke verifier: `codex-root`

## Scope

| Pad | path_b64 | Regelbereik | Symbolen | Object-ID |
|---|---|---:|---:|---|
| `src/services/web_lookup/sru_service.py` | `c3JjL3NlcnZpY2VzL3dlYl9sb29rdXAvc3J1X3NlcnZpY2UucHk=` | `1-1281` | 35 | `9f4a2190554836441e57d5a664ce46aed46b5f96` |
| `src/services/web_lookup/synonym_service.py` | `c3JjL3NlcnZpY2VzL3dlYl9sb29rdXAvc3lub255bV9zZXJ2aWNlLnB5` | `1-432` | 14 | `14121ddb407de362fed244c00c1250b8623878a0` |
| `src/services/web_lookup/wikipedia_service.py` | `c3JjL3NlcnZpY2VzL3dlYl9sb29rdXAvd2lraXBlZGlhX3NlcnZpY2UucHk=` | `1-385` | 14 | `2d114023d481294a690e26d58f57f87f7686eb8c` |
| `src/services/web_lookup/wikipedia_synonym_extractor.py` | `c3JjL3NlcnZpY2VzL3dlYl9sb29rdXAvd2lraXBlZGlhX3N5bm9ueW1fZXh0cmFjdG9yLnB5` | `1-495` | 16 | `c97f1eb385a663e8d517ed02f558537180d271a7` |
| `src/services/web_lookup/wiktionary_service.py` | `c3JjL3NlcnZpY2VzL3dlYl9sb29rdXAvd2lrdGlvbmFyeV9zZXJ2aWNlLnB5` | `1-251` | 12 | `451a5852e92ef832a972fa314808130512a554d8` |
| `src/ui/renderers/document_upload_renderer.py` | `c3JjL3VpL3JlbmRlcmVycy9kb2N1bWVudF91cGxvYWRfcmVuZGVyZXIucHk=` | `1-362` | 10 | `ed27ec49b7e0563c756afdefb6fb34333257c5f4` |

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

- P2/proven: `B037-001` — Upload lookup can bind a document to the wrong file.
- P2/proven: `B037-002` — Document deletion leaves the original upload on disk.
- P3/proven: `B037-003` — Dormant jurisprudence helper targets a removed endpoint.
- P3/proven: `B037-004` — Wikipedia include_extract option is ignored.

## Resultaat

Geverifieerd door twee verschillende reviewers. Alle 6 bestanden, 3206 fysieke regels en 101 symbolen zijn line-by-line beoordeeld; gerichte tests, veilige reproducties en beperkingen staan in het bewijsdossier.
