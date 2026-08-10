# BATCH-017

- Status: `verified`
- Reviewgroep: `6` — Prompts, orchestrators en generatieflow
- Review-base: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Membership-SHA256: `2a246345afa37c59459eaf5db3e5a2a1429ba0f7aadcc0eb6a66f6f1eac0c37d`
- Bestanden: `6`
- Fysieke regels: `1801`
- Python-symbolen: `43`
- Reviewer: `codex-hypatia`
- Onafhankelijke verifier: `codex-root`

## Scope

| Pad | path_b64 | Regelbereik | Symbolen | Object-ID |
|---|---|---:|---:|---|
| `src/services/synonym_orchestrator.py` | `c3JjL3NlcnZpY2VzL3N5bm9ueW1fb3JjaGVzdHJhdG9yLnB5` | `1-629` | 15 | `86de54564307143afa899b08495c7d6b4f320c1e` |
| `src/ui/components/category_regeneration_helper.py` | `c3JjL3VpL2NvbXBvbmVudHMvY2F0ZWdvcnlfcmVnZW5lcmF0aW9uX2hlbHBlci5weQ==` | `1-61` | 4 | `e3e4f69bc4713bf6ef0d173bef12773f0699743f` |
| `src/ui/components/prompt_debug_section.py` | `c3JjL3VpL2NvbXBvbmVudHMvcHJvbXB0X2RlYnVnX3NlY3Rpb24ucHk=` | `1-223` | 4 | `632b900dc32aff095b93a122572ebf4d5e5bc7e7` |
| `src/ui/components/tabs/import_export_beheer/orchestrator.py` | `c3JjL3VpL2NvbXBvbmVudHMvdGFicy9pbXBvcnRfZXhwb3J0X2JlaGVlci9vcmNoZXN0cmF0b3IucHk=` | `1-88` | 7 | `483c6b140a3f7cd242507dd85539f5d927be1cbe` |
| `src/ui/handlers/definition_generation_handler.py` | `c3JjL3VpL2hhbmRsZXJzL2RlZmluaXRpb25fZ2VuZXJhdGlvbl9oYW5kbGVyLnB5` | `1-746` | 9 | `1b456812d0c34b703302bce69e66975ce6735a79` |
| `src/ui/regeneration_handler.py` | `c3JjL3VpL3JlZ2VuZXJhdGlvbl9oYW5kbGVyLnB5` | `1-54` | 4 | `c22b5f387ae4b5b4a8c17fe989d3ebf1ae32be3f` |

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

- P1/proven: `B017-001` — Import-time logging writes to the project root.
- P1/proven: `B017-002` — Force-duplicate bypass persists after a generation.
- P2/proven: `B017-003` — Serialized duplicate context replaces the primary organization.
- P2/proven: `B017-004` — Failed generation is shown as success.
- P2/proven: `B017-005` — Synonym cache check and read are not atomic.
- P2/proven: `B017-006` — Duplicate flow hardcodes the process category.
- P3/proven: `B017-007` — Explicit zero synonym weight is replaced by the default.
- P3/proven: `B017-008` — Active Test Prompt button performs no test.
- Volledig bewijs en niet-geteste onderdelen: `evidence/BATCH-017/review-evidence.md`.

## Resultaat

Geverifieerd door twee verschillende reviewers. Alle toegewezen bestanden, regels en symbolen van BATCH-017 zijn line-by-line beoordeeld; beperkingen staan expliciet in het bewijsdossier.
