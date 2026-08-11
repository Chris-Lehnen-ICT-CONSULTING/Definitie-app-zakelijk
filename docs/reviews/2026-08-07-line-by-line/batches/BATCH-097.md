# BATCH-097

- Status: `verified`
- Reviewgroep: `15` — Operationele scripts en shellcode
- Review-base: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Membership-SHA256: `5ae384ce96eae95b6a24025e44d12e35f495bcd0244786ba277ae8e7a2ebd117`
- Bestanden: `20`
- Fysieke regels: `3457`
- Python-symbolen: `79`
- Reviewer: `codex-hypatia`
- Onafhankelijke verifier: `codex-kierkegaard`

## Scope

| Pad | path_b64 | Regelbereik | Symbolen | Object-ID |
|---|---|---:|---:|---|
| `scripts/archive_data.py` | `c2NyaXB0cy9hcmNoaXZlX2RhdGEucHk=` | `1-516` | 10 | `81c8b2b8ce9b39c8c4249d5fb71caa2ce0465d8e` |
| `scripts/auto_backup_database.sh` | `c2NyaXB0cy9hdXRvX2JhY2t1cF9kYXRhYmFzZS5zaA==` | `1-103` | 0 | `7cb64b7cd51f3a8039ae5bb7b32d5db989a6cbe8` |
| `scripts/backup_database.sh` | `c2NyaXB0cy9iYWNrdXBfZGF0YWJhc2Uuc2g=` | `1-83` | 0 | `59aee4a730b6328ca92157a581a9659dc8ae553e` |
| `scripts/backup_restore.py` | `c2NyaXB0cy9iYWNrdXBfcmVzdG9yZS5weQ==` | `1-469` | 11 | `47f86d8014dd65adba6da386290bdd576b5f14e8` |
| `scripts/batch_suggest_synonyms.py` | `c2NyaXB0cy9iYXRjaF9zdWdnZXN0X3N5bm9ueW1zLnB5` | `1-358` | 8 | `30e055668dccdedd53793f4bde7eea2df99d7834` |
| `scripts/benchmark_voorbeelden_parallel.py` | `c2NyaXB0cy9iZW5jaG1hcmtfdm9vcmJlZWxkZW5fcGFyYWxsZWwucHk=` | `1-219` | 6 | `7cf03ef90b1f6e3dc669b8e10c620002d32d8ac6` |
| `scripts/benchmarks/benchmark_services.py` | `c2NyaXB0cy9iZW5jaG1hcmtzL2JlbmNobWFya19zZXJ2aWNlcy5weQ==` | `1-210` | 9 | `dad6248dafc8d9bcc86815b8b59286be4909bc52` |
| `scripts/benchmarks/simple_benchmark.py` | `c2NyaXB0cy9iZW5jaG1hcmtzL3NpbXBsZV9iZW5jaG1hcmsucHk=` | `1-95` | 1 | `9356e0ff7bfd6248da2b8c85a7c83f3388c580fb` |
| `scripts/build_macos_app.sh` | `c2NyaXB0cy9idWlsZF9tYWNvc19hcHAuc2g=` | `1-45` | 0 | `953a8f46d6ad1e1af46652450f5dd5deb3ff83c9` |
| `scripts/check_rechtspraak_api.py` | `c2NyaXB0cy9jaGVja19yZWNodHNwcmFha19hcGkucHk=` | `1-222` | 7 | `0a2690c97e90656d03b36681f568ac9b5aea2189` |
| `scripts/check_streamlit_patterns.py` | `c2NyaXB0cy9jaGVja19zdHJlYW1saXRfcGF0dGVybnMucHk=` | `1-196` | 8 | `bcb729957aefede23d5002568e109e08f53e3f90` |
| `scripts/check_tool_pins.py` | `c2NyaXB0cy9jaGVja190b29sX3BpbnMucHk=` | `1-124` | 7 | `bc254e5e4dbe663163cd14673b947c5ff896613b` |
| `scripts/ci/check-file-size.sh` | `c2NyaXB0cy9jaS9jaGVjay1maWxlLXNpemUuc2g=` | `1-77` | 0 | `6ddfada2ea0727833c79adb5223a81913f307f25` |
| `scripts/ci/check-forbidden-patterns.sh` | `c2NyaXB0cy9jaS9jaGVjay1mb3JiaWRkZW4tcGF0dGVybnMuc2g=` | `1-106` | 0 | `53be818aab2e5676994ed771aa3209dbbc8490d3` |
| `scripts/ci/check-legacy-patterns.sh` | `c2NyaXB0cy9jaS9jaGVjay1sZWdhY3ktcGF0dGVybnMuc2g=` | `1-169` | 0 | `a65d159d52d1915153209050b954e74b7da3675c` |
| `scripts/ci/check-v1-symbols.sh` | `c2NyaXB0cy9jaS9jaGVjay12MS1zeW1ib2xzLnNo` | `1-49` | 0 | `c448f539b77e2f4de931454e430e8a70675bf147` |
| `scripts/ci/check_namespace_collisions.py` | `c2NyaXB0cy9jaS9jaGVja19uYW1lc3BhY2VfY29sbGlzaW9ucy5weQ==` | `1-274` | 12 | `c2addab68ec695b56769fea1782b81b24bcde343` |
| `scripts/ci/check_namespace_collisions.sh` | `c2NyaXB0cy9jaS9jaGVja19uYW1lc3BhY2VfY29sbGlzaW9ucy5zaA==` | `1-33` | 0 | `947013bdc552141db11f662d4a8a5a2bfafaa0d8` |
| `scripts/ci/check_no_root_db_files.sh` | `c2NyaXB0cy9jaS9jaGVja19ub19yb290X2RiX2ZpbGVzLnNo` | `1-45` | 0 | `52377d4524e637ae85721991212d86fe382c12ea` |
| `scripts/ci/check_no_todo_markers.sh` | `c2NyaXB0cy9jaS9jaGVja19ub190b2RvX21hcmtlcnMuc2g=` | `1-64` | 0 | `2f9ff63941b9c6b3080238dbedd0703f465e09e1` |

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

- P1/proven: `B097-001` — Archive deletion uses every historical archive ID instead of the successful copy set.
- P1/proven: `B097-002` — Hourly backup copies only the SQLite main file and silently omits committed WAL data.
- P2/proven: `B097-003` — Restore overwrites the live database non-atomically and has no rollback.
- P2/proven: `B097-004` — Archive and restore CLIs open log files before creating the log directory.
- P2/proven: `B097-005` — Partial synonym failures are reported as no results and still exit successfully.
- P2/proven: `B097-006` — Streamlit anti-pattern gate misses multiline widget calls.
- P2/proven: `B097-007` — Active legacy gate treats an invalid ripgrep regex as PASS.
- P3/proven: `B097-008` — File-size checker word-splits filenames and skips large files containing spaces.

## Resultaat

Geverifieerd door twee verschillende reviewers. Alle 20 bestanden, 3457 fysieke regels en 79 symbolen zijn line-by-line beoordeeld; gerichte tests, veilige reproducties en beperkingen staan in het bewijsdossier.
