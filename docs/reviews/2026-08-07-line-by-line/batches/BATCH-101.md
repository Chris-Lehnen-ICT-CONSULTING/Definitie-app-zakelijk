# BATCH-101

- Status: `pending`
- Reviewgroep: `15` — Operationele scripts en shellcode
- Review-base: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Membership-SHA256: `d61ccf4e66c19e07ff0a78db8534f0ec288b31b1da40ae117e3ebf206d4f9582`
- Bestanden: `20`
- Fysieke regels: `3739`
- Python-symbolen: `104`
- Reviewer: ``
- Onafhankelijke verifier: ``

## Scope

| Pad | path_b64 | Regelbereik | Symbolen | Object-ID |
|---|---|---:|---:|---|
| `scripts/extract_wikipedia_synonyms.py` | `c2NyaXB0cy9leHRyYWN0X3dpa2lwZWRpYV9zeW5vbnltcy5weQ==` | `1-386` | 7 | `d95fdbbe70405ed4c44b57a3f2e19974f95be3ff` |
| `scripts/fetch_linear_issues.py` | `c2NyaXB0cy9mZXRjaF9saW5lYXJfaXNzdWVzLnB5` | `1-74` | 2 | `6a22cac2e22c75194cebc151d87c316630ca274b` |
| `scripts/fix_definities_old_fk.py` | `c2NyaXB0cy9maXhfZGVmaW5pdGllc19vbGRfZmsucHk=` | `1-451` | 8 | `67ceef6f7fe77fe7716873895dd92ab461d625b8` |
| `scripts/fix_unicode_chars.py` | `c2NyaXB0cy9maXhfdW5pY29kZV9jaGFycy5weQ==` | `1-85` | 3 | `0a35a2e8b55517a92576797d338a13ceb9114bda` |
| `scripts/functional_verification.py` | `c2NyaXB0cy9mdW5jdGlvbmFsX3ZlcmlmaWNhdGlvbi5weQ==` | `1-282` | 7 | `ba0a7de3c600e880faf0f0835243f7a5f0ff51db` |
| `scripts/hooks/README.md` | `c2NyaXB0cy9ob29rcy9SRUFETUUubWQ=` | `1-40` | 0 | `c38f00039aea48723f0225298a65fcc4d0033d0e` |
| `scripts/hooks/check-doc-links.py` | `c2NyaXB0cy9ob29rcy9jaGVjay1kb2MtbGlua3MucHk=` | `1-81` | 4 | `df3108634415b80518ce8fa6ed0213f9662de390` |
| `scripts/hooks/check-doc-location.py` | `c2NyaXB0cy9ob29rcy9jaGVjay1kb2MtbG9jYXRpb24ucHk=` | `1-212` | 4 | `e264087d48df8650856025269c6077d37b0a5d39` |
| `scripts/hooks/check-doc-metadata.py` | `c2NyaXB0cy9ob29rcy9jaGVjay1kb2MtbWV0YWRhdGEucHk=` | `1-68` | 3 | `4c08911b79f331d4ad16bff04d3c8485c1d6a690` |
| `scripts/hooks/post-commit-review-reminder` | `c2NyaXB0cy9ob29rcy9wb3N0LWNvbW1pdC1yZXZpZXctcmVtaW5kZXI=` | `1-85` | 0 | `48f60ad359af64a70ae24f002aa2525d8a37367b` |
| `scripts/hooks/run_black_changed.sh` | `c2NyaXB0cy9ob29rcy9ydW5fYmxhY2tfY2hhbmdlZC5zaA==` | `1-18` | 0 | `15da6a5e057582847f264fd2c91bb7a927bd793e` |
| `scripts/hooks/run_ruff_changed.sh` | `c2NyaXB0cy9ob29rcy9ydW5fcnVmZl9jaGFuZ2VkLnNo` | `1-18` | 0 | `eff277ed244124d435258f3e4ee7bb93229d5352` |
| `scripts/import/convert_export_to_import_csv.py` | `c2NyaXB0cy9pbXBvcnQvY29udmVydF9leHBvcnRfdG9faW1wb3J0X2Nzdi5weQ==` | `1-169` | 8 | `3ce58c18e698019e70395e6aa0766cdfe3c9a3d4` |
| `scripts/import_from_txt_exports.py` | `c2NyaXB0cy9pbXBvcnRfZnJvbV90eHRfZXhwb3J0cy5weQ==` | `1-353` | 17 | `0124ea024998eb67f8d886f9eba70d51d03618c2` |
| `scripts/import_v9_model.py` | `c2NyaXB0cy9pbXBvcnRfdjlfbW9kZWwucHk=` | `1-446` | 7 | `6afb1dc092217915b6c36786a7d03dedab3e0900` |
| `scripts/maintenance/clean_history_session_state.py` | `c2NyaXB0cy9tYWludGVuYW5jZS9jbGVhbl9oaXN0b3J5X3Nlc3Npb25fc3RhdGUucHk=` | `1-48` | 2 | `6f744f1da13fbf435601db796fb53bf9d23a9464` |
| `scripts/maintenance/clean_openai_keys.sh` | `c2NyaXB0cy9tYWludGVuYW5jZS9jbGVhbl9vcGVuYWlfa2V5cy5zaA==` | `1-110` | 0 | `a66e13eb711bb9cad9033d66a795ce90545184e1` |
| `scripts/maintenance/cleanup_nan_contexts.py` | `c2NyaXB0cy9tYWludGVuYW5jZS9jbGVhbnVwX25hbl9jb250ZXh0cy5weQ==` | `1-91` | 3 | `ddaed79f0e074a74e4c32a86755b37025d9f3cd8` |
| `scripts/maintenance/code_review_tool.py` | `c2NyaXB0cy9tYWludGVuYW5jZS9jb2RlX3Jldmlld190b29sLnB5` | `1-164` | 8 | `eaa1fda640d3d995f619842255fbb7bf7b4d01aa` |
| `scripts/maintenance/debug_performance_issues.py` | `c2NyaXB0cy9tYWludGVuYW5jZS9kZWJ1Z19wZXJmb3JtYW5jZV9pc3N1ZXMucHk=` | `1-558` | 21 | `aa15568dbc93a7f0a4f15daad7a583f7b250b918` |

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
