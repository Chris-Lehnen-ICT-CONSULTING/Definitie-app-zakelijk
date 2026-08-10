# BATCH-019

- Status: `verified`
- Reviewgroep: `6` — Prompts, orchestrators en generatieflow
- Review-base: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Membership-SHA256: `91c502e731b36255b8bc196115ecea95cc32086123175280eb2a3bda1ba130f7`
- Bestanden: `3`
- Fysieke regels: `1321`
- Python-symbolen: `0`
- Reviewer: `codex-galileo`
- Onafhankelijke verifier: `codex-kierkegaard`

## Scope

| Pad | path_b64 | Regelbereik | Symbolen | Object-ID |
|---|---|---:|---:|---|
| `prompts/implementation/implementation-plan-claude-agents.md` | `cHJvbXB0cy9pbXBsZW1lbnRhdGlvbi9pbXBsZW1lbnRhdGlvbi1wbGFuLWNsYXVkZS1hZ2VudHMubWQ=` | `1-319` | 0 | `a549632cfb03fa6ec20270a9114c7ce3fb60ff19` |
| `prompts/implementation/linear-hookify-implementation.md` | `cHJvbXB0cy9pbXBsZW1lbnRhdGlvbi9saW5lYXItaG9va2lmeS1pbXBsZW1lbnRhdGlvbi5tZA==` | `1-152` | 0 | `13c690582f2394b1ea97493feb3a0e8c91c65540` |
| `prompts/implementation/prompt-generator-subagent-spec.md` | `cHJvbXB0cy9pbXBsZW1lbnRhdGlvbi9wcm9tcHQtZ2VuZXJhdG9yLXN1YmFnZW50LXNwZWMubWQ=` | `1-850` | 0 | `5cbad2f35523a4353077f59019634125a85f3e23` |

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

- P3/proven: `B019-001` — Prompt generator specification writes to filesystem root.
- Volledig bewijs en niet-geteste onderdelen: `evidence/BATCH-019/review-evidence.md`.

## Resultaat

Geverifieerd door twee verschillende reviewers. Alle toegewezen bestanden, regels en symbolen van BATCH-019 zijn line-by-line beoordeeld; beperkingen staan expliciet in het bewijsdossier.
