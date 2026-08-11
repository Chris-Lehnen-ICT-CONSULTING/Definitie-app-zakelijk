# BATCH-082

- Status: `verified`
- Reviewgroep: `13` — Unit-tests gekoppeld aan productieonderdelen
- Review-base: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Membership-SHA256: `20f89d0b7ba538dda8f728bf19f6b32847d02454833c13ec1dfe45b3beaa494f`
- Bestanden: `20`
- Fysieke regels: `1666`
- Python-symbolen: `123`
- Reviewer: `codex-kierkegaard`
- Onafhankelijke verifier: `codex-hypatia`

## Scope

| Pad | path_b64 | Regelbereik | Symbolen | Object-ID |
|---|---|---:|---:|---|
| `tests/unit/validation/test_category_mapping_externalized.py` | `dGVzdHMvdW5pdC92YWxpZGF0aW9uL3Rlc3RfY2F0ZWdvcnlfbWFwcGluZ19leHRlcm5hbGl6ZWQucHk=` | `1-149` | 15 | `49b99f1f088c9db120bd45af6c75c58424ddc754` |
| `tests/unit/validation/test_con01_duplicate_count.py` | `dGVzdHMvdW5pdC92YWxpZGF0aW9uL3Rlc3RfY29uMDFfZHVwbGljYXRlX2NvdW50LnB5` | `1-60` | 6 | `ef3bb4b1a1c71a2efdca7f2a166a5b2b36e18c21` |
| `tests/unit/validation/test_json_validators.py` | `dGVzdHMvdW5pdC92YWxpZGF0aW9uL3Rlc3RfanNvbl92YWxpZGF0b3JzLnB5` | `1-108` | 5 | `1391624a616955ef0a1202bc11a6d26e9134fc47` |
| `tests/unit/validation/test_v2_golden_additional_patterns.py` | `dGVzdHMvdW5pdC92YWxpZGF0aW9uL3Rlc3RfdjJfZ29sZGVuX2FkZGl0aW9uYWxfcGF0dGVybnMucHk=` | `1-61` | 5 | `aa80427f13d37e2ba29de5bf2d3f82b0e30b9dff` |
| `tests/unit/validation/test_v2_golden_arai_str_more.py` | `dGVzdHMvdW5pdC92YWxpZGF0aW9uL3Rlc3RfdjJfZ29sZGVuX2FyYWlfc3RyX21vcmUucHk=` | `1-87` | 5 | `85322c3e22c4f47a10bd458b1fa28ea190371373` |
| `tests/unit/validation/test_v2_golden_con_sam_ver_more.py` | `dGVzdHMvdW5pdC92YWxpZGF0aW9uL3Rlc3RfdjJfZ29sZGVuX2Nvbl9zYW1fdmVyX21vcmUucHk=` | `1-58` | 5 | `360033705e622c8751caf50bed7df3aee13d85fa` |
| `tests/unit/validation/test_v2_golden_ess_more.py` | `dGVzdHMvdW5pdC92YWxpZGF0aW9uL3Rlc3RfdjJfZ29sZGVuX2Vzc19tb3JlLnB5` | `1-81` | 4 | `0086f1639a4bb67ae3e307516edda5481050c569` |
| `tests/unit/validation/test_v2_golden_initial_int_con.py` | `dGVzdHMvdW5pdC92YWxpZGF0aW9uL3Rlc3RfdjJfZ29sZGVuX2luaXRpYWxfaW50X2Nvbi5weQ==` | `1-117` | 8 | `dd93bacc8ec9f1bd9f79f8453d0403f974930ebb` |
| `tests/unit/validation/test_v2_golden_int_more.py` | `dGVzdHMvdW5pdC92YWxpZGF0aW9uL3Rlc3RfdjJfZ29sZGVuX2ludF9tb3JlLnB5` | `1-54` | 5 | `7bc37b0d797cba541e7cbc77507101e3a0b20c61` |
| `tests/unit/validation/test_v2_golden_latent_rules.py` | `dGVzdHMvdW5pdC92YWxpZGF0aW9uL3Rlc3RfdjJfZ29sZGVuX2xhdGVudF9ydWxlcy5weQ==` | `1-37` | 3 | `be03f7c97f7fb2450da7e7febef02503284fcf18` |
| `tests/unit/validation/test_v2_golden_str_more.py` | `dGVzdHMvdW5pdC92YWxpZGF0aW9uL3Rlc3RfdjJfZ29sZGVuX3N0cl9tb3JlLnB5` | `1-93` | 7 | `4742695c20d4872f50f5d6b4f8acd5ab627055c2` |
| `tests/unit/validation/test_v2_golden_ver.py` | `dGVzdHMvdW5pdC92YWxpZGF0aW9uL3Rlc3RfdjJfZ29sZGVuX3Zlci5weQ==` | `1-45` | 3 | `d19c9e416b9fe37cb1f14c6661b1352ad09aa6f3` |
| `tests/unit/validation/test_v2_json_rules.py` | `dGVzdHMvdW5pdC92YWxpZGF0aW9uL3Rlc3RfdjJfanNvbl9ydWxlcy5weQ==` | `1-106` | 10 | `15b058cafe021ff58d15c1609a31145d49454240` |
| `tests/unit/validation/test_v2_json_rules_more.py` | `dGVzdHMvdW5pdC92YWxpZGF0aW9uL3Rlc3RfdjJfanNvbl9ydWxlc19tb3JlLnB5` | `1-99` | 8 | `a4c1891d2b1503fb93273d355bfb621d55763687` |
| `tests/unit/validation/test_v2_violation_description.py` | `dGVzdHMvdW5pdC92YWxpZGF0aW9uL3Rlc3RfdjJfdmlvbGF0aW9uX2Rlc2NyaXB0aW9uLnB5` | `1-27` | 2 | `bcee59ebbf0fe5e94d1e358924b732dc87d8f3ec` |
| `tests/unit/validation/test_validators_interface_sweep.py` | `dGVzdHMvdW5pdC92YWxpZGF0aW9uL3Rlc3RfdmFsaWRhdG9yc19pbnRlcmZhY2Vfc3dlZXAucHk=` | `1-49` | 3 | `3c28a103debbd08be4c480cb3761e09d3071f426` |
| `tests/unit/voorbeelden_functionality_tests.py` | `dGVzdHMvdW5pdC92b29yYmVlbGRlbl9mdW5jdGlvbmFsaXR5X3Rlc3RzLnB5` | `1-315` | 22 | `188b13f2abba50f9e1a3ac2d2d8011de60489ed8` |
| `tests/unit/web_lookup/test_adapters_normalization.py` | `dGVzdHMvdW5pdC93ZWJfbG9va3VwL3Rlc3RfYWRhcHRlcnNfbm9ybWFsaXphdGlvbi5weQ==` | `1-69` | 3 | `78bf2a324776bc757b200d8e0911ea305aef2888` |
| `tests/unit/web_lookup/test_bwb_sru_endpoint_config.py` | `dGVzdHMvdW5pdC93ZWJfbG9va3VwL3Rlc3RfYndiX3NydV9lbmRwb2ludF9jb25maWcucHk=` | `1-14` | 2 | `2c2c5a91b89d8ec430fb7a3458e46efc68e046d0` |
| `tests/unit/web_lookup/test_config_loader.py` | `dGVzdHMvdW5pdC93ZWJfbG9va3VwL3Rlc3RfY29uZmlnX2xvYWRlci5weQ==` | `1-37` | 2 | `fba5a9be6b9c64975e7c75b0a2b8e3fa6a13483f` |

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

- P1/proven: `B082-001` — Hidden voorbeelden suite masks overwrite that inherits prior approval.
- P3/proven: `B082-002` — All-validator gate tolerates eight missing rules and a crashing validator.
- P3/proven: `B082-003` — Externalized category mapping test duplicates the configuration in code.
- P3/proven: `B082-004` — Violation description test inspects only the first matching violation.

## Resultaat

Geverifieerd door twee verschillende reviewers. Alle 20 bestanden, 1666 fysieke regels en 123 symbolen zijn line-by-line beoordeeld; gerichte tests, veilige reproducties en beperkingen staan in het bewijsdossier.
