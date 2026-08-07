# BATCH-016

- Status: `pending`
- Reviewgroep: `6` — Prompts, orchestrators en generatieflow
- Review-base: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Membership-SHA256: `b575a1d896663c595628f51402113e1fb254220e10934a4329fc012bafa86c82`
- Bestanden: `14`
- Fysieke regels: `3690`
- Python-symbolen: `150`
- Reviewer: ``
- Onafhankelijke verifier: ``

## Scope

| Pad | path_b64 | Regelbereik | Symbolen | Object-ID |
|---|---|---:|---:|---|
| `src/services/prompts/modules/error_prevention_module.py` | `c3JjL3NlcnZpY2VzL3Byb21wdHMvbW9kdWxlcy9lcnJvcl9wcmV2ZW50aW9uX21vZHVsZS5weQ==` | `1-259` | 11 | `fb573aef500c856e7a07b7b2b5c30ce7bb891a87` |
| `src/services/prompts/modules/expertise_module.py` | `c3JjL3NlcnZpY2VzL3Byb21wdHMvbW9kdWxlcy9leHBlcnRpc2VfbW9kdWxlLnB5` | `1-181` | 11 | `7814a979b96df47a1006c97d990eddd5f8030ba2` |
| `src/services/prompts/modules/grammar_module.py` | `c3JjL3NlcnZpY2VzL3Byb21wdHMvbW9kdWxlcy9ncmFtbWFyX21vZHVsZS5weQ==` | `1-262` | 11 | `0fd0b826d9f5d27dc88af92f815253b4aafa633d` |
| `src/services/prompts/modules/integrity_rules_module.py` | `c3JjL3NlcnZpY2VzL3Byb21wdHMvbW9kdWxlcy9pbnRlZ3JpdHlfcnVsZXNfbW9kdWxlLnB5` | `1-295` | 14 | `e5e2d7898b0a12f4c33039fbd9313c8e5333cbe2` |
| `src/services/prompts/modules/json_based_rules_module.py` | `c3JjL3NlcnZpY2VzL3Byb21wdHMvbW9kdWxlcy9qc29uX2Jhc2VkX3J1bGVzX21vZHVsZS5weQ==` | `1-308` | 9 | `3dbd82fc91c06edc9023dc0991f45e3fef8bc4c8` |
| `src/services/prompts/modules/metrics_module.py` | `c3JjL3NlcnZpY2VzL3Byb21wdHMvbW9kdWxlcy9tZXRyaWNzX21vZHVsZS5weQ==` | `1-99` | 7 | `356f7136ceecb9c02dcee6abd2948a15c086257b` |
| `src/services/prompts/modules/output_specification_module.py` | `c3JjL3NlcnZpY2VzL3Byb21wdHMvbW9kdWxlcy9vdXRwdXRfc3BlY2lmaWNhdGlvbl9tb2R1bGUucHk=` | `1-174` | 10 | `a51c20077a3084dce44f1da6f36467c7ae0b3725` |
| `src/services/prompts/modules/prompt_orchestrator.py` | `c3JjL3NlcnZpY2VzL3Byb21wdHMvbW9kdWxlcy9wcm9tcHRfb3JjaGVzdHJhdG9yLnB5` | `1-552` | 20 | `10dc464ecec92b535a614be64f671ee5eddfc78a` |
| `src/services/prompts/modules/semantic_categorisation_module.py` | `c3JjL3NlcnZpY2VzL3Byb21wdHMvbW9kdWxlcy9zZW1hbnRpY19jYXRlZ29yaXNhdGlvbl9tb2R1bGUucHk=` | `1-275` | 9 | `f25b49a473105c68f383b9143066a482f194015b` |
| `src/services/prompts/modules/structure_rules_module.py` | `c3JjL3NlcnZpY2VzL3Byb21wdHMvbW9kdWxlcy9zdHJ1Y3R1cmVfcnVsZXNfbW9kdWxlLnB5` | `1-307` | 16 | `ea9fcea97130aa68e68b26f041767338f6f9f95b` |
| `src/services/prompts/modules/template_module.py` | `c3JjL3NlcnZpY2VzL3Byb21wdHMvbW9kdWxlcy90ZW1wbGF0ZV9tb2R1bGUucHk=` | `1-255` | 10 | `5f084342e5ad02f72175382d4ba28dcebe64f7d8` |
| `src/services/prompts/prompt_service_v2.py` | `c3JjL3NlcnZpY2VzL3Byb21wdHMvcHJvbXB0X3NlcnZpY2VfdjIucHk=` | `1-487` | 14 | `142ffeb752bc974d3315096f37837f166780a8c5` |
| `src/services/prompts/synonym_research_prompt.py` | `c3JjL3NlcnZpY2VzL3Byb21wdHMvc3lub255bV9yZXNlYXJjaF9wcm9tcHQucHk=` | `1-151` | 5 | `c302705f9868bd8baf9461fbe5d21c40812d4da4` |
| `src/services/prompts/synonym_response_parser.py` | `c3JjL3NlcnZpY2VzL3Byb21wdHMvc3lub255bV9yZXNwb25zZV9wYXJzZXIucHk=` | `1-85` | 3 | `fe176eae8447fc148b24674fe0ee56705e0ddb5b` |

## Verplichte reviewchecklist

- [ ] Iedere toegewezen regel rechtstreeks uit het immutable object-ID gelezen.
- [ ] Ieder toegewezen symbool en iedere functie line-by-line beoordeeld.
- [ ] Callers, afhankelijkheden, tests en foutpaden gecontroleerd.
- [ ] Codekwaliteit en architectuur beoordeeld.
- [ ] Bugs, security en foutafhandeling beoordeeld.
- [ ] Functionaliteit en relevante tests beoordeeld.
- [ ] UI/UX, toegankelijkheid en responsive gedrag beoordeeld indien van toepassing.
- [ ] Findings bevatten prioriteit, bewijs, reproductie en oplossing.
- [ ] Bewezen, vermoed en niet-getest expliciet onderscheiden.
- [ ] Onafhankelijke tweede reviewer heeft scope en findings geverifieerd.

## Bevindingen

Nog niet geregistreerd.

## Resultaat

Nog niet uitgevoerd.
