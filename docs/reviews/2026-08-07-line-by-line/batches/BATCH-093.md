# BATCH-093

- Status: `verified`
- Reviewgroep: `14` — Integration-, contract-, smoke-, performance- en archived-tests
- Review-base: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Membership-SHA256: `6c2a0b09441fba3aa9ac92f199af22bb12b41b4eac717a55eb8a8e83f9f15756`
- Bestanden: `20`
- Fysieke regels: `2790`
- Python-symbolen: `68`
- Reviewer: `codex-galileo`
- Onafhankelijke verifier: `codex-root`

## Scope

| Pad | path_b64 | Regelbereik | Symbolen | Object-ID |
|---|---|---:|---:|---|
| `tests/manual/rate_limiting/test_endpoint_rate_limiting.py` | `dGVzdHMvbWFudWFsL3JhdGVfbGltaXRpbmcvdGVzdF9lbmRwb2ludF9yYXRlX2xpbWl0aW5nLnB5` | `1-147` | 6 | `e57ba882968f5a1110f8e4f4ee311d8af73f3a81` |
| `tests/manual/rate_limiting/test_final_rate_limiter.py` | `dGVzdHMvbWFudWFsL3JhdGVfbGltaXRpbmcvdGVzdF9maW5hbF9yYXRlX2xpbWl0ZXIucHk=` | `1-155` | 8 | `5d845f42252bc260517cd78f3f3aeac872b2333c` |
| `tests/manual/rate_limiting/test_rate_limit_config.py` | `dGVzdHMvbWFudWFsL3JhdGVfbGltaXRpbmcvdGVzdF9yYXRlX2xpbWl0X2NvbmZpZy5weQ==` | `1-78` | 2 | `46b750d134ead9d4e8a25388914d5150ef217e50` |
| `tests/manual/rate_limiting/test_rate_limiter.py` | `dGVzdHMvbWFudWFsL3JhdGVfbGltaXRpbmcvdGVzdF9yYXRlX2xpbWl0ZXIucHk=` | `1-42` | 3 | `50998e9dca3f45806336dde864b87baa6e2d1b26` |
| `tests/manual/rate_limiting/test_rate_limiter_simple.py` | `dGVzdHMvbWFudWFsL3JhdGVfbGltaXRpbmcvdGVzdF9yYXRlX2xpbWl0ZXJfc2ltcGxlLnB5` | `1-139` | 4 | `2f2d151d1c8845e60a43c9aba51a549340968fa6` |
| `tests/manual/rate_limiting/test_ui_rate_limiter.py` | `dGVzdHMvbWFudWFsL3JhdGVfbGltaXRpbmcvdGVzdF91aV9yYXRlX2xpbWl0ZXIucHk=` | `1-192` | 5 | `9aeae3509616d12a1e6069f60955359f69d9e198` |
| `tests/manual/rate_limiting/test_voorbeelden_rate_limiter.py` | `dGVzdHMvbWFudWFsL3JhdGVfbGltaXRpbmcvdGVzdF92b29yYmVlbGRlbl9yYXRlX2xpbWl0ZXIucHk=` | `1-203` | 5 | `1c03a4309a1806fc0c8033478f4702f6e80b4254` |
| `tests/manual/scratch/README.md` | `dGVzdHMvbWFudWFsL3NjcmF0Y2gvUkVBRE1FLm1k` | `1-26` | 0 | `b8429e464b8b9fb1d2355e86568bb156ab875695` |
| `tests/manual/scratch/test_contradictions.py` | `dGVzdHMvbWFudWFsL3NjcmF0Y2gvdGVzdF9jb250cmFkaWN0aW9ucy5weQ==` | `1-320` | 9 | `8b081ac1aa1e326b87025fcc6a10badf7b114e2f` |
| `tests/manual/scratch/test_csv_import_websocket.py` | `dGVzdHMvbWFudWFsL3NjcmF0Y2gvdGVzdF9jc3ZfaW1wb3J0X3dlYnNvY2tldC5weQ==` | `1-139` | 4 | `4b5612289d2cbc84454cc1f349be8862f199fcf4` |
| `tests/manual/scratch/test_def126_simple.py` | `dGVzdHMvbWFudWFsL3NjcmF0Y2gvdGVzdF9kZWYxMjZfc2ltcGxlLnB5` | `1-188` | 4 | `0b4e94b0955d21eeea00195ab57be157932837f7` |
| `tests/manual/scratch/test_env.py` | `dGVzdHMvbWFudWFsL3NjcmF0Y2gvdGVzdF9lbnYucHk=` | `1-16` | 1 | `2c4cdd0ba2af549ff04e18780325a1a9ab8b31b7` |
| `tests/manual/scratch/test_new_default.py` | `dGVzdHMvbWFudWFsL3NjcmF0Y2gvdGVzdF9uZXdfZGVmYXVsdC5weQ==` | `1-55` | 1 | `6e2e6bbd1ef1cd0560b0a12c1611357448eb4a01` |
| `tests/manual/scratch/test_ui_new_services.py` | `dGVzdHMvbWFudWFsL3NjcmF0Y2gvdGVzdF91aV9uZXdfc2VydmljZXMucHk=` | `1-55` | 1 | `91a64b23220ef55213aa4ac8c71c391ec9073920` |
| `tests/manual/scratch/test_ui_scores.py` | `dGVzdHMvbWFudWFsL3NjcmF0Y2gvdGVzdF91aV9zY29yZXMucHk=` | `1-55` | 2 | `21f9613f3bc6e8d726fc60500a187ca392c94d86` |
| `tests/manual/test_def176_duplicate_performance.py` | `dGVzdHMvbWFudWFsL3Rlc3RfZGVmMTc2X2R1cGxpY2F0ZV9wZXJmb3JtYW5jZS5weQ==` | `1-123` | 2 | `999ca8fe4fbdff3d08858347de7d75616e543d1d` |
| `tests/manual_test_category_aware_duplicates.py` | `dGVzdHMvbWFudWFsX3Rlc3RfY2F0ZWdvcnlfYXdhcmVfZHVwbGljYXRlcy5weQ==` | `1-582` | 9 | `98869703727557177940d3d7c59146dca91f8b8b` |
| `tests/manual_test_category_regeneration_fix.py` | `dGVzdHMvbWFudWFsX3Rlc3RfY2F0ZWdvcnlfcmVnZW5lcmF0aW9uX2ZpeC5weQ==` | `1-115` | 2 | `35396139dd260edbceb31fee114c12dbc471d8cc` |
| `tests/output/test_baseline.txt` | `dGVzdHMvb3V0cHV0L3Rlc3RfYmFzZWxpbmUudHh0` | `1-148` | 0 | `3fee810f9d9acc58e85c69211bf5e5c27e4b02e4` |
| `tests/output/test_baseline_continue.txt` | `dGVzdHMvb3V0cHV0L3Rlc3RfYmFzZWxpbmVfY29udGludWUudHh0` | `1-12` | 0 | `7a6d3fb7b02e225cbac041a7e5fe0ee9e28c8c96` |

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

- P3/proven: `B093-001` — Manual duplicate performance test mutates a shared fixed database.

## Resultaat

Geverifieerd door twee verschillende reviewers. Alle 20 bestanden, 2790 fysieke regels en 68 symbolen zijn line-by-line beoordeeld; gerichte tests, veilige reproducties en beperkingen staan in het bewijsdossier.
