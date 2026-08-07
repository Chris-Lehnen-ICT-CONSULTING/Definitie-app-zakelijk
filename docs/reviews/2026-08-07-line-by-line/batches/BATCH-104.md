# BATCH-104

- Status: `pending`
- Reviewgroep: `15` — Operationele scripts en shellcode
- Review-base: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Membership-SHA256: `66dbf3c086a811506d21aa961045a233e59a8eac5e5b5beb3cb50842cbeb0146`
- Bestanden: `20`
- Fysieke regels: `2728`
- Python-symbolen: `64`
- Reviewer: ``
- Onafhankelijke verifier: ``

## Scope

| Pad | path_b64 | Regelbereik | Symbolen | Object-ID |
|---|---|---:|---:|---|
| `scripts/phase-tracker.py` | `c2NyaXB0cy9waGFzZS10cmFja2VyLnB5` | `1-218` | 12 | `7dd59c91a522797e545f9b9e6513917034b4bbc7` |
| `scripts/rebuild/backlog/dashboard/README.md` | `c2NyaXB0cy9yZWJ1aWxkL2JhY2tsb2cvZGFzaGJvYXJkL1JFQURNRS5tZA==` | `1-2` | 0 | `5fb9cedece97bca066a8ef642dec9e2227c5c4ab` |
| `scripts/rebuild/backlog/dashboard/assets/style.css` | `c2NyaXB0cy9yZWJ1aWxkL2JhY2tsb2cvZGFzaGJvYXJkL2Fzc2V0cy9zdHlsZS5jc3M=` | `1-14` | 0 | `f57d32528a7aa1081da8f6284e1653016915b7d2` |
| `scripts/rebuild/backlog/dashboard/data.json` | `c2NyaXB0cy9yZWJ1aWxkL2JhY2tsb2cvZGFzaGJvYXJkL2RhdGEuanNvbg==` | `1-4` | 0 | `cf39f9b6be3b38169e89ba9aad312ad5dfe46f86` |
| `scripts/rebuild/backlog/dashboard/graph.html` | `c2NyaXB0cy9yZWJ1aWxkL2JhY2tsb2cvZGFzaGJvYXJkL2dyYXBoLmh0bWw=` | `1-144` | 0 | `7492594c2e8f2d253673404f6c27e3f5c98ea1df` |
| `scripts/rebuild/backlog/dashboard/index.html` | `c2NyaXB0cy9yZWJ1aWxkL2JhY2tsb2cvZGFzaGJvYXJkL2luZGV4Lmh0bWw=` | `1-74` | 0 | `8a256d494c7e88a6ff46b011049571fe3825903e` |
| `scripts/rebuild/backlog/dashboard/per-epic.html` | `c2NyaXB0cy9yZWJ1aWxkL2JhY2tsb2cvZGFzaGJvYXJkL3Blci1lcGljLmh0bWw=` | `1-82` | 0 | `356fcfa1b3000d7bb764a46abf46c998a9114d90` |
| `scripts/recover_voorbeelden.py` | `c2NyaXB0cy9yZWNvdmVyX3Zvb3JiZWVsZGVuLnB5` | `1-330` | 14 | `1b5cb693462ad362fa7fab407f47e9e4a3ebe12a` |
| `scripts/restore_orphaned_voorbeelden.py` | `c2NyaXB0cy9yZXN0b3JlX29ycGhhbmVkX3Zvb3JiZWVsZGVuLnB5` | `1-190` | 3 | `d558aded39075bdf60eb03a4a2baac501620c42d` |
| `scripts/setup-github-labels.sh` | `c2NyaXB0cy9zZXR1cC1naXRodWItbGFiZWxzLnNo` | `1-52` | 0 | `b1d76c325b3b2baad8c308c033bdac1c7f3d366f` |
| `scripts/setup_auto_backup.sh` | `c2NyaXB0cy9zZXR1cF9hdXRvX2JhY2t1cC5zaA==` | `1-69` | 0 | `451ee4315acd621bf020b2c1466ae5dab65bdee7` |
| `scripts/test_all_endpoints_onherroepelijk.py` | `c2NyaXB0cy90ZXN0X2FsbF9lbmRwb2ludHNfb25oZXJyb2VwZWxpamsucHk=` | `1-220` | 8 | `988a39e75da19305615fcadb9ac53bddce975a35` |
| `scripts/test_enrichment_logger.py` | `c2NyaXB0cy90ZXN0X2VucmljaG1lbnRfbG9nZ2VyLnB5` | `1-53` | 2 | `ed00120f83f145746a085c0bd6ca1119352d88f1` |
| `scripts/test_export_levels.py` | `c2NyaXB0cy90ZXN0X2V4cG9ydF9sZXZlbHMucHk=` | `1-253` | 7 | `e1aaa1e649518b835880f7e4c7d9c58ba7aab022` |
| `scripts/test_improved_classifier.py` | `c2NyaXB0cy90ZXN0X2ltcHJvdmVkX2NsYXNzaWZpZXIucHk=` | `1-225` | 6 | `933acc55596f0528cf2c8540a70d9a8f5766eace` |
| `scripts/test_live_sru_response.py` | `c2NyaXB0cy90ZXN0X2xpdmVfc3J1X3Jlc3BvbnNlLnB5` | `1-163` | 3 | `2715596cf2bdf280b6b0c377462fd0e8abea1bb1` |
| `scripts/test_monitoring.py` | `c2NyaXB0cy90ZXN0X21vbml0b3JpbmcucHk=` | `1-27` | 1 | `3c8ff6f731d126dc4fdb703f8dd96bc3ad4604fa` |
| `scripts/test_mvp.sh` | `c2NyaXB0cy90ZXN0X212cC5zaA==` | `1-329` | 0 | `1410a30e4132df3ec61f00e2ef8668ca255c2dd1` |
| `scripts/test_onherroepelijk_vonnis_fix.py` | `c2NyaXB0cy90ZXN0X29uaGVycm9lcGVsaWprX3Zvbm5pc19maXgucHk=` | `1-143` | 5 | `5bcf5396f3f9406da2855138dfae773becead288` |
| `scripts/test_rechtspraak_api.py` | `c2NyaXB0cy90ZXN0X3JlY2h0c3ByYWFrX2FwaS5weQ==` | `1-136` | 3 | `f972e63eac0b7ada7cfcd1016a712e1c1c33b6e9` |

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
