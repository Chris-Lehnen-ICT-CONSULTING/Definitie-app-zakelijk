# BATCH-095

- Status: `verified`
- Reviewgroep: `15` — Operationele scripts en shellcode
- Review-base: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Membership-SHA256: `63566961cc82c1b02e37df7b15931a3cb87130d7f835ecfc46a788610b4aedf9`
- Bestanden: `16`
- Fysieke regels: `3941`
- Python-symbolen: `70`
- Reviewer: `codex-root`
- Onafhankelijke verifier: `codex-galileo`

## Scope

| Pad | path_b64 | Regelbereik | Symbolen | Object-ID |
|---|---|---:|---:|---|
| `docs/archiveer-simpel.sh` | `ZG9jcy9hcmNoaXZlZXItc2ltcGVsLnNo` | `1-190` | 0 | `43f2fe7343b2fb6f66efb566a18a476f2c4be534` |
| `docs/reorganize-docs-simple.sh` | `ZG9jcy9yZW9yZ2FuaXplLWRvY3Mtc2ltcGxlLnNo` | `1-298` | 0 | `51b68c3697f52036869d77e352a404c2bcde0b66` |
| `docs/reorganize-docs.sh` | `ZG9jcy9yZW9yZ2FuaXplLWRvY3Muc2g=` | `1-297` | 0 | `e13c8bb0db5fe69af632c898abdc5dc9105b34cd` |
| `scripts/README_MIGRATION.md` | `c2NyaXB0cy9SRUFETUVfTUlHUkFUSU9OLm1k` | `1-125` | 0 | `71aeb3fcb3d19603a309a414ccd84c5d9a5854e1` |
| `scripts/README_VALIDATE_SYNONYMS.md` | `c2NyaXB0cy9SRUFETUVfVkFMSURBVEVfU1lOT05ZTVMubWQ=` | `1-285` | 0 | `cb2cc47307a501a94d853bc3d32ba0bdf0e7c043` |
| `scripts/SYNONYM_VALIDATION_SUMMARY.md` | `c2NyaXB0cy9TWU5PTllNX1ZBTElEQVRJT05fU1VNTUFSWS5tZA==` | `1-162` | 0 | `504ce197a4fe83ff5973bb043cfefa383c1ffbab` |
| `scripts/ai-pre-commit` | `c2NyaXB0cy9haS1wcmUtY29tbWl0` | `1-73` | 0 | `b19b6cb0baf098fab95fe2c4a83879332e9b8a24` |
| `scripts/analyse/hernoem-naar-nederlands.py` | `c2NyaXB0cy9hbmFseXNlL2hlcm5vZW0tbmFhci1uZWRlcmxhbmRzLnB5` | `1-451` | 12 | `99e2321016b55810f79d44b5f5c71cc13b6cbf33` |
| `scripts/analysis/agent_scoreboard.sh` | `c2NyaXB0cy9hbmFseXNpcy9hZ2VudF9zY29yZWJvYXJkLnNo` | `1-99` | 0 | `71b1165d8a328949036ca73296eab501121de247` |
| `scripts/analysis/ai-metrics-dashboard.py` | `c2NyaXB0cy9hbmFseXNpcy9haS1tZXRyaWNzLWRhc2hib2FyZC5weQ==` | `1-194` | 10 | `dc0d156f1f7bba0f2f668a9460fff684f3db69cb` |
| `scripts/analysis/ai_metrics_tracker.py` | `c2NyaXB0cy9hbmFseXNpcy9haV9tZXRyaWNzX3RyYWNrZXIucHk=` | `1-414` | 13 | `5ad0602df87a44bcfb322a0df3644d441aa7062e` |
| `scripts/analysis/analyze_core_module.py` | `c2NyaXB0cy9hbmFseXNpcy9hbmFseXplX2NvcmVfbW9kdWxlLnB5` | `1-305` | 12 | `663e14d609ede772b28844dca51123450b2bb73d` |
| `scripts/analysis/analyze_coverage.py` | `c2NyaXB0cy9hbmFseXNpcy9hbmFseXplX2NvdmVyYWdlLnB5` | `1-354` | 10 | `8924130aa9aaff48d38f6a9ec97cb8434eddff74` |
| `scripts/analysis/analyze_coverage_targeted.py` | `c2NyaXB0cy9hbmFseXNpcy9hbmFseXplX2NvdmVyYWdlX3RhcmdldGVkLnB5` | `1-378` | 9 | `0a10fe5aa9b99fadaae47932b5909971b2a7b303` |
| `scripts/analysis/analyze_dependencies.py` | `c2NyaXB0cy9hbmFseXNpcy9hbmFseXplX2RlcGVuZGVuY2llcy5weQ==` | `1-158` | 1 | `1b27358e8005ed287bd181733daf2612a01e8067` |
| `scripts/analysis/analyze_modular_prompts.py` | `c2NyaXB0cy9hbmFseXNpcy9hbmFseXplX21vZHVsYXJfcHJvbXB0cy5weQ==` | `1-158` | 3 | `e01e2dd7e49486cdc12db2cbee73365fa2cfe2a0` |

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

- P1/proven: `B095-001` — Flat documentation archive silently overwrites same-named files.
- P1/proven: `B095-002` — Documentation reorganization mutates reviews before a guaranteed invalid move.
- P1/proven: `B095-003` — Rename tool stages all user changes and creates its backup inside the source tree.
- P1/proven: `B095-004` — Failed rename rolls back the filename but not rewritten references.
- P2/proven: `B095-005` — Installed AI pre-commit hook references missing script paths.
- P2/proven: `B095-006` — AI metrics CLI is unreachable whenever Streamlit is installed.
- P2/proven: `B095-007` — Coverage analyzers accept stale output and hardcode one workstation.
- P2/proven: `B095-008` — Agent scoreboard integration uses a missing path and unsafe branch switching.
- P3/proven: `B095-009` — Core prompt analyzer uses removed private APIs but exits successfully.
- P3/proven: `B095-010` — Dependency analyzer scans and writes during import.
- P3/proven: `B095-011` — Modular prompt analyzer crashes on empty or zero-sized reports.
- P3/proven: `B095-012` — Synonym validation documentation points to a missing green suite.

## Resultaat

Geverifieerd door twee verschillende reviewers. Alle 16 bestanden, 3941 fysieke regels en 70 symbolen zijn line-by-line beoordeeld; gerichte tests, veilige reproducties en beperkingen staan in het bewijsdossier.
