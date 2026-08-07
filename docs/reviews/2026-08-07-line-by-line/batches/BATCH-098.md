# BATCH-098

- Status: `pending`
- Reviewgroep: `15` — Operationele scripts en shellcode
- Review-base: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Membership-SHA256: `7f98348a3c11d47b9ad85c71d5523c45b743394002f2b015895d0010367438d4`
- Bestanden: `20`
- Fysieke regels: `3309`
- Python-symbolen: `58`
- Reviewer: ``
- Onafhankelijke verifier: ``

## Scope

| Pad | path_b64 | Regelbereik | Symbolen | Object-ID |
|---|---|---:|---:|---|
| `scripts/ci/validate-branch-name.sh` | `c2NyaXB0cy9jaS92YWxpZGF0ZS1icmFuY2gtbmFtZS5zaA==` | `1-67` | 0 | `92250073969c7f743853c006ea4f0e5b91ce3eee` |
| `scripts/ci/verify-precommit.sh` | `c2NyaXB0cy9jaS92ZXJpZnktcHJlY29tbWl0LnNo` | `1-85` | 0 | `2f2b1b4b6561950d1e64172f82e7ac10876ce0e2` |
| `scripts/cleanup_duplicates.py` | `c2NyaXB0cy9jbGVhbnVwX2R1cGxpY2F0ZXMucHk=` | `1-145` | 3 | `a04e084f23bf4c78178e4bf110846db5faaa2be9` |
| `scripts/com.definitieagent.backup.plist` | `c2NyaXB0cy9jb20uZGVmaW5pdGllYWdlbnQuYmFja3VwLnBsaXN0` | `1-50` | 0 | `0834bc5e8e13bc65acebdc8add38c755269f63c9` |
| `scripts/compare_validation_results.py` | `c2NyaXB0cy9jb21wYXJlX3ZhbGlkYXRpb25fcmVzdWx0cy5weQ==` | `1-508` | 18 | `fc2fcf9cf8ecd1a9a3d080faa47126c0fd5580ae` |
| `scripts/complexity_baseline.txt` | `c2NyaXB0cy9jb21wbGV4aXR5X2Jhc2VsaW5lLnR4dA==` | `1-1` | 0 | `3bc92d44ac9d8a185fa33dec183c593d71d79372` |
| `scripts/complexity_ratchet.py` | `c2NyaXB0cy9jb21wbGV4aXR5X3JhdGNoZXQucHk=` | `1-138` | 6 | `a2b3c33c054e6029829ea8c7b2f6964dc13c7ea5` |
| `scripts/db/reset_context_model_v2.sh` | `c2NyaXB0cy9kYi9yZXNldF9jb250ZXh0X21vZGVsX3YyLnNo` | `1-14` | 0 | `88da2ebd36184002c668e93524f3d7578352a111` |
| `scripts/debug_rechtspraak_html.py` | `c2NyaXB0cy9kZWJ1Z19yZWNodHNwcmFha19odG1sLnB5` | `1-172` | 9 | `c9f9f21631000be2e7b1bd734178e54ab3cbdc53` |
| `scripts/debug_sru_parsing.py` | `c2NyaXB0cy9kZWJ1Z19zcnVfcGFyc2luZy5weQ==` | `1-316` | 4 | `62032fb69572f689d560e145e4a98c4d2f9afa82` |
| `scripts/demo_cache_monitoring.py` | `c2NyaXB0cy9kZW1vX2NhY2hlX21vbml0b3JpbmcucHk=` | `1-125` | 2 | `f9474fbd78285e89aa10ee980854fefd7c318613` |
| `scripts/demo_ontology_classification.py` | `c2NyaXB0cy9kZW1vX29udG9sb2d5X2NsYXNzaWZpY2F0aW9uLnB5` | `1-300` | 12 | `d3927681a318baf178a5d806cd94a42149cd4af6` |
| `scripts/demo_term_classifier.py` | `c2NyaXB0cy9kZW1vX3Rlcm1fY2xhc3NpZmllci5weQ==` | `1-211` | 4 | `17fefb025944a34d0b88bffdf7ad90bf832b5c3f` |
| `scripts/deployment/launcher.sh` | `c2NyaXB0cy9kZXBsb3ltZW50L2xhdW5jaGVyLnNo` | `1-34` | 0 | `9abc08dfbaade2103319a4d8bb6b0651b3fa36de` |
| `scripts/deployment/multiagent.sh` | `c2NyaXB0cy9kZXBsb3ltZW50L211bHRpYWdlbnQuc2g=` | `1-299` | 0 | `b1324c83413adb51094707656eee689e0a87503e` |
| `scripts/deployment/quick_deploy.sh` | `c2NyaXB0cy9kZXBsb3ltZW50L3F1aWNrX2RlcGxveS5zaA==` | `1-445` | 0 | `f28d425ff5ad5f3af92b9d670d7bb521fd2902d3` |
| `scripts/deployment/run_app.sh` | `c2NyaXB0cy9kZXBsb3ltZW50L3J1bl9hcHAuc2g=` | `1-20` | 0 | `cea3704c85e06de6f27d86bbd845153f8f20acc7` |
| `scripts/deployment/setup-ai-review.sh` | `c2NyaXB0cy9kZXBsb3ltZW50L3NldHVwLWFpLXJldmlldy5zaA==` | `1-82` | 0 | `0e83510368ad449007e77c4d203851551ecda0a2` |
| `scripts/deployment/setup_ai_review.sh` | `c2NyaXB0cy9kZXBsb3ltZW50L3NldHVwX2FpX3Jldmlldy5zaA==` | `1-285` | 0 | `4520a65526d137bbb6471d8eacf67f2584e7853e` |
| `scripts/deployment/start_app.sh` | `c2NyaXB0cy9kZXBsb3ltZW50L3N0YXJ0X2FwcC5zaA==` | `1-12` | 0 | `473346abd006ab9abd0905c505dd44e2c4b9e1dd` |

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
