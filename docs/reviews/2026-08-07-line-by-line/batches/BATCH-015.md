# BATCH-015

- Status: `verified`
- Reviewgroep: `6` — Prompts, orchestrators en generatieflow
- Review-base: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Membership-SHA256: `9a68474f80d5d07f2c870768d00dd2a4e558033e2c99f5f2167fcf611d86c0be`
- Bestanden: `11`
- Fysieke regels: `3990`
- Python-symbolen: `133`
- Reviewer: `codex-galileo`
- Onafhankelijke verifier: `codex-kierkegaard`

## Scope

| Pad | path_b64 | Regelbereik | Symbolen | Object-ID |
|---|---|---:|---:|---|
| `src/services/definition_generator_monitoring.py` | `c3JjL3NlcnZpY2VzL2RlZmluaXRpb25fZ2VuZXJhdG9yX21vbml0b3JpbmcucHk=` | `1-414` | 24 | `3a4fe768fdf6c47f3b55c932ecdeac26e3f95682` |
| `src/services/definition_generator_prompts.py` | `c3JjL3NlcnZpY2VzL2RlZmluaXRpb25fZ2VuZXJhdG9yX3Byb21wdHMucHk=` | `1-144` | 13 | `7c51602b0424fa170963738fcd6e0780a326b465` |
| `src/services/orchestrators/__init__.py` | `c3JjL3NlcnZpY2VzL29yY2hlc3RyYXRvcnMvX19pbml0X18ucHk=` | `1-13` | 1 | `150320dc8d5ff15d693a16777004407577439d38` |
| `src/services/orchestrators/definition_orchestrator_v2.py` | `c3JjL3NlcnZpY2VzL29yY2hlc3RyYXRvcnMvZGVmaW5pdGlvbl9vcmNoZXN0cmF0b3JfdjIucHk=` | `1-1488` | 15 | `73b2c39c218956264f53d0fa7003d3e0ceb579b8` |
| `src/services/orchestrators/validation_orchestrator_v2.py` | `c3JjL3NlcnZpY2VzL29yY2hlc3RyYXRvcnMvdmFsaWRhdGlvbl9vcmNoZXN0cmF0b3JfdjIucHk=` | `1-270` | 7 | `7ee650620dd7d9383831df5980b02c82f3f3fba6` |
| `src/services/prompts/modular_prompt_adapter.py` | `c3JjL3NlcnZpY2VzL3Byb21wdHMvbW9kdWxhcl9wcm9tcHRfYWRhcHRlci5weQ==` | `1-437` | 11 | `1799be056439df9cd42c97c6857592a135d81dbd` |
| `src/services/prompts/modular_prompt_builder.py` | `c3JjL3NlcnZpY2VzL3Byb21wdHMvbW9kdWxhcl9wcm9tcHRfYnVpbGRlci5weQ==` | `1-45` | 2 | `cc976ef0c57568877b326348730ab5ffc64f6040` |
| `src/services/prompts/modules/__init__.py` | `c3JjL3NlcnZpY2VzL3Byb21wdHMvbW9kdWxlcy9fX2luaXRfXy5weQ==` | `1-56` | 1 | `b17b1c9da91e170547d4ea9ac693384da7871060` |
| `src/services/prompts/modules/base_module.py` | `c3JjL3NlcnZpY2VzL3Byb21wdHMvbW9kdWxlcy9iYXNlX21vZHVsZS5weQ==` | `1-285` | 25 | `6a97ca1301b2775f2ea276c43e115df27148e6ed` |
| `src/services/prompts/modules/context_awareness_module.py` | `c3JjL3NlcnZpY2VzL3Byb21wdHMvbW9kdWxlcy9jb250ZXh0X2F3YXJlbmVzc19tb2R1bGUucHk=` | `1-502` | 19 | `8be894c152d7aa659b3ca4ce8eff2a5c2814f788` |
| `src/services/prompts/modules/definition_task_module.py` | `c3JjL3NlcnZpY2VzL3Byb21wdHMvbW9kdWxlcy9kZWZpbml0aW9uX3Rhc2tfbW9kdWxlLnB5` | `1-336` | 15 | `4097e61624295ebb264d8e67a7476f1576d30ec5` |

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

- P1/proven: `B015-001` — Prompt cap removes the term and final instruction.
- P1/proven: `B015-002` — Raw term is logged before sanitization.
- P2/proven: `B015-003` — Global prompt orchestrator leaks configuration between adapters.
- P2/proven: `B015-004` — Prompt include flags have no effect.
- P1/proven: `B015-005` — Invalid RAG minimum score breaks generation without RAG.
- Volledig bewijs en niet-geteste onderdelen: `evidence/BATCH-015/review-evidence.md`.

## Resultaat

Geverifieerd door twee verschillende reviewers. Alle 11 bestanden en 133 symbolen zijn line-by-line beoordeeld; functionele beperkingen en niet-geteste externe of visuele flows staan expliciet in het bewijsdossier.
