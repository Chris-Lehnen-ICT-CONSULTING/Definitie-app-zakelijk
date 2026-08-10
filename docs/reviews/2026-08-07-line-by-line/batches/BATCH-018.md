# BATCH-018

- Status: `verified`
- Reviewgroep: `6` — Prompts, orchestrators en generatieflow
- Review-base: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Membership-SHA256: `4f7fc89e571ffa8cb5a9820448e09e5a2f95e7180afd943719badcddecb85dc2`
- Bestanden: `15`
- Fysieke regels: `5715`
- Python-symbolen: `0`
- Reviewer: `codex-kierkegaard`
- Onafhankelijke verifier: `codex-galileo`

## Scope

| Pad | path_b64 | Regelbereik | Symbolen | Object-ID |
|---|---|---:|---:|---|
| `prompts/README.md` | `cHJvbXB0cy9SRUFETUUubWQ=` | `1-299` | 0 | `d869b604bff9ad76fa2c6c244a127266647a087c` |
| `prompts/analyse-DEF-254-hookify.md` | `cHJvbXB0cy9hbmFseXNlLURFRi0yNTQtaG9va2lmeS5tZA==` | `1-99` | 0 | `4298be12f35af0ae7a07ec5b6fbd753ba8d20b8e` |
| `prompts/analyse-docs-cleanup.md` | `cHJvbXB0cy9hbmFseXNlLWRvY3MtY2xlYW51cC5tZA==` | `1-126` | 0 | `51b03b1b42cff66b9648472c7834ce23f732208b` |
| `prompts/analysis/ANALYSIS-REPORT-claude-code-agents.md` | `cHJvbXB0cy9hbmFseXNpcy9BTkFMWVNJUy1SRVBPUlQtY2xhdWRlLWNvZGUtYWdlbnRzLm1k` | `1-502` | 0 | `cd6fe455b2c78e3afc6f2fe4f146727984e22bba` |
| `prompts/analysis/claude-code-agents-analysis.md` | `cHJvbXB0cy9hbmFseXNpcy9jbGF1ZGUtY29kZS1hZ2VudHMtYW5hbHlzaXMubWQ=` | `1-600` | 0 | `c12dd7efd461aa776ca7a488d3fe939c1b0739e9` |
| `prompts/analysis/hookify-gap-analysis.md` | `cHJvbXB0cy9hbmFseXNpcy9ob29raWZ5LWdhcC1hbmFseXNpcy5tZA==` | `1-267` | 0 | `a9d8be450bd19b23814654af295962036eaa15f7` |
| `prompts/analysis/hookify-rules-analysis.md` | `cHJvbXB0cy9hbmFseXNpcy9ob29raWZ5LXJ1bGVzLWFuYWx5c2lzLm1k` | `1-165` | 0 | `a623e7a0ef1d779a6cb30e8f67bf3b90e69c47d5` |
| `prompts/analysis/prompt-engineering-analysis.md` | `cHJvbXB0cy9hbmFseXNpcy9wcm9tcHQtZW5naW5lZXJpbmctYW5hbHlzaXMubWQ=` | `1-608` | 0 | `0e0eeac46935869ebfc8c12ad3cd644da33a7a4b` |
| `prompts/analysis/prompt-first-enforcement-analysis.md` | `cHJvbXB0cy9hbmFseXNpcy9wcm9tcHQtZmlyc3QtZW5mb3JjZW1lbnQtYW5hbHlzaXMubWQ=` | `1-504` | 0 | `a8cf6fee3d32ee01ec8fa6d1375d65eff1b2b124` |
| `prompts/analysis/subagent-inventory-analysis.md` | `cHJvbXB0cy9hbmFseXNpcy9zdWJhZ2VudC1pbnZlbnRvcnktYW5hbHlzaXMubWQ=` | `1-575` | 0 | `55256ed4757fdb9aaa315df73e4651cebc4cc671` |
| `prompts/chained-code-review-orchestrator.md` | `cHJvbXB0cy9jaGFpbmVkLWNvZGUtcmV2aWV3LW9yY2hlc3RyYXRvci5tZA==` | `1-618` | 0 | `d97f012913dc32c6f51fb1db7426ea1206e752f5` |
| `prompts/define-project-areas.md` | `cHJvbXB0cy9kZWZpbmUtcHJvamVjdC1hcmVhcy5tZA==` | `1-491` | 0 | `75f4be319a78c80b0b0771340e023129279da86e` |
| `prompts/implementatie-DEF-253-quick-wins.md` | `cHJvbXB0cy9pbXBsZW1lbnRhdGllLURFRi0yNTMtcXVpY2std2lucy5tZA==` | `1-105` | 0 | `0d96c88208db07ab59ee958369923ee2a779084c` |
| `prompts/implementatie-silent-exception-hookify.md` | `cHJvbXB0cy9pbXBsZW1lbnRhdGllLXNpbGVudC1leGNlcHRpb24taG9va2lmeS5tZA==` | `1-85` | 0 | `9c39d81ce8ed41abe955c735d9cb5fa4d8ca248c` |
| `prompts/implementation/agent-consistency-system.md` | `cHJvbXB0cy9pbXBsZW1lbnRhdGlvbi9hZ2VudC1jb25zaXN0ZW5jeS1zeXN0ZW0ubWQ=` | `1-671` | 0 | `33aaa3cfa4e7411922653071d89b5156453e9ec2` |

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

- P3/proven: `B018-001` — Dormant code-review prompt uses a stale CLI and wrong stack.
- Volledig bewijs en niet-geteste onderdelen: `evidence/BATCH-018/review-evidence.md`.

## Resultaat

Geverifieerd door twee verschillende reviewers. Alle toegewezen bestanden, regels en symbolen van BATCH-018 zijn line-by-line beoordeeld; beperkingen staan expliciet in het bewijsdossier.
