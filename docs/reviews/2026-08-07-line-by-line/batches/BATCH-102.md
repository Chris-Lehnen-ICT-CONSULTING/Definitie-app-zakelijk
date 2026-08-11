# BATCH-102

- Status: `verified`
- Reviewgroep: `15` — Operationele scripts en shellcode
- Review-base: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Membership-SHA256: `cb0e0fb0b19c2aa2fa27939f30e42ed117bb066563c0810efa18881f141238a0`
- Bestanden: `17`
- Fysieke regels: `3836`
- Python-symbolen: `106`
- Reviewer: `codex-kierkegaard`
- Onafhankelijke verifier: `codex-root`

## Scope

| Pad | path_b64 | Regelbereik | Symbolen | Object-ID |
|---|---|---:|---:|---|
| `scripts/maintenance/debug_session_state.py` | `c2NyaXB0cy9tYWludGVuYW5jZS9kZWJ1Z19zZXNzaW9uX3N0YXRlLnB5` | `1-165` | 1 | `2ea4277b1aac85f1be2ef0d4879c6d554d20a529` |
| `scripts/maintenance/document_cleanup.py` | `c2NyaXB0cy9tYWludGVuYW5jZS9kb2N1bWVudF9jbGVhbnVwLnB5` | `1-449` | 16 | `87ae08f85f114bf94d26f889b622af2ff9788555` |
| `scripts/maintenance/find_duplicates.sh` | `c2NyaXB0cy9tYWludGVuYW5jZS9maW5kX2R1cGxpY2F0ZXMuc2g=` | `1-64` | 0 | `3e7468a46fe5242f9bd7def40630a949a4802f2c` |
| `scripts/maintenance/fix_all_links.sh` | `c2NyaXB0cy9tYWludGVuYW5jZS9maXhfYWxsX2xpbmtzLnNo` | `1-101` | 0 | `f7611567ffe4d85cc479e8b9cc071b3afd9ada5d` |
| `scripts/maintenance/fix_broken_links.py` | `c2NyaXB0cy9tYWludGVuYW5jZS9maXhfYnJva2VuX2xpbmtzLnB5` | `1-279` | 10 | `4c8f3dd950429afb722b964187d7e6969b04f464` |
| `scripts/maintenance/fix_context_mapping_cfr.py` | `c2NyaXB0cy9tYWludGVuYW5jZS9maXhfY29udGV4dF9tYXBwaW5nX2Nmci5weQ==` | `1-360` | 9 | `86d5006f1948a303af8d07b66eda539146f359d4` |
| `scripts/maintenance/fix_documentation_issues.py` | `c2NyaXB0cy9tYWludGVuYW5jZS9maXhfZG9jdW1lbnRhdGlvbl9pc3N1ZXMucHk=` | `1-213` | 7 | `65a6149713839b4249763f82affbf62b9b0c42f1` |
| `scripts/maintenance/fix_domein_tests.py` | `c2NyaXB0cy9tYWludGVuYW5jZS9maXhfZG9tZWluX3Rlc3RzLnB5` | `1-94` | 3 | `79b35e1f268a640a74a2aa072eb4343b3a87b391` |
| `scripts/maintenance/fix_double_replacements.py` | `c2NyaXB0cy9tYWludGVuYW5jZS9maXhfZG91YmxlX3JlcGxhY2VtZW50cy5weQ==` | `1-112` | 5 | `739057df4323b957012325fa8e84b68e710fc2f4` |
| `scripts/maintenance/fix_generation_request_tests.py` | `c2NyaXB0cy9tYWludGVuYW5jZS9maXhfZ2VuZXJhdGlvbl9yZXF1ZXN0X3Rlc3RzLnB5` | `1-63` | 3 | `61208629a572007f29beab55c18030eb34f80ff6` |
| `scripts/maintenance/fix_requirements.py` | `c2NyaXB0cy9tYWludGVuYW5jZS9maXhfcmVxdWlyZW1lbnRzLnB5` | `1-299` | 12 | `6b09ccb391cb0cac0423743d8e945c3ef39a0aaa` |
| `scripts/maintenance/fix_requirements_v2.py` | `c2NyaXB0cy9tYWludGVuYW5jZS9maXhfcmVxdWlyZW1lbnRzX3YyLnB5` | `1-299` | 7 | `3aeb5eb1e831c0483329bffcba59f5a60f4c6a0a` |
| `scripts/maintenance/fix_smart_compliance.py` | `c2NyaXB0cy9tYWludGVuYW5jZS9maXhfc21hcnRfY29tcGxpYW5jZS5weQ==` | `1-854` | 28 | `addd3f90e7a184bc19fbee8e1e207a961a347ca6` |
| `scripts/maintenance/fix_translation_issues.py` | `c2NyaXB0cy9tYWludGVuYW5jZS9maXhfdHJhbnNsYXRpb25faXNzdWVzLnB5` | `1-145` | 5 | `93d579dde8f281fb91627d11a05cf67373953d97` |
| `scripts/maintenance/fix_unassigned_stories.sh` | `c2NyaXB0cy9tYWludGVuYW5jZS9maXhfdW5hc3NpZ25lZF9zdG9yaWVzLnNo` | `1-76` | 0 | `34bb84c59a6d182485972ccbdb5dd17b06a939e1` |
| `scripts/maintenance/grep-gate-context.sh` | `c2NyaXB0cy9tYWludGVuYW5jZS9ncmVwLWdhdGUtY29udGV4dC5zaA==` | `1-130` | 0 | `dfa7a65f0cc4383b238f9d1b743716406d9c905f` |
| `scripts/maintenance/grep_gate.sh` | `c2NyaXB0cy9tYWludGVuYW5jZS9ncmVwX2dhdGUuc2g=` | `1-133` | 0 | `91cec96afc0340068c415a7fdda3b6eb80a70ce5` |

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

- P1/proven: `B102-001` — Active grep gate scans the wrong root and treats rg errors as clean.
- P2/proven: `B102-002` — Document cleanup resolves the project root to scripts/.
- P2/proven: `B102-003` — Document cleanup can erase malformed frontmatter and report failed writes as success.
- P3/proven: `B102-004` — Broken-link fixer writes its report in dry-run mode.
- P2/proven: `B102-005` — Requirement fixers hardcode the original checkout and can write across worktrees.
- P3/proven: `B102-006` — Smart-compliance threshold is printed but not used.

## Resultaat

Geverifieerd door twee verschillende reviewers. Alle 17 bestanden, 3836 fysieke regels en 106 symbolen zijn line-by-line beoordeeld; gerichte tests, veilige reproducties en beperkingen staan in het bewijsdossier.
