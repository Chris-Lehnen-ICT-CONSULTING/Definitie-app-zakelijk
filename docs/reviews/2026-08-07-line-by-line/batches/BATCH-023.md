# BATCH-023

- Status: `verified`
- Reviewgroep: `7` — Validatie, toetsregels, opschoning en sanitization
- Review-base: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Membership-SHA256: `a843be35409662920907ac4e7c95e06f72087bd0be06094e85bbca7a0f2bab18`
- Bestanden: `11`
- Fysieke regels: `3501`
- Python-symbolen: `123`
- Reviewer: `codex-hypatia`
- Onafhankelijke verifier: `codex-root`

## Scope

| Pad | path_b64 | Regelbereik | Symbolen | Object-ID |
|---|---|---:|---:|---|
| `src/config/validation_rules.yaml` | `c3JjL2NvbmZpZy92YWxpZGF0aW9uX3J1bGVzLnlhbWw=` | `1-19` | 0 | `766da154c363a1bf9edea808d2b589bae0c69707` |
| `src/services/cleaning_service.py` | `c3JjL3NlcnZpY2VzL2NsZWFuaW5nX3NlcnZpY2UucHk=` | `1-282` | 9 | `455a302b3a0c609ebe33b444075f3527d3d6c492` |
| `src/services/validation/__init__.py` | `c3JjL3NlcnZpY2VzL3ZhbGlkYXRpb24vX19pbml0X18ucHk=` | `0-0` | 1 | `e69de29bb2d1d6434b8b29ae775ad8c2e48c5391` |
| `src/services/validation/aggregation.py` | `c3JjL3NlcnZpY2VzL3ZhbGlkYXRpb24vYWdncmVnYXRpb24ucHk=` | `1-73` | 6 | `1c3ebf32dc25c3e266644a4f2f55aef9f6181c57` |
| `src/services/validation/astra_validator.py` | `c3JjL3NlcnZpY2VzL3ZhbGlkYXRpb24vYXN0cmFfdmFsaWRhdG9yLnB5` | `1-327` | 21 | `06a3954e5cddf496885ce7f335f71966d257132b` |
| `src/services/validation/config.py` | `c3JjL3NlcnZpY2VzL3ZhbGlkYXRpb24vY29uZmlnLnB5` | `1-97` | 6 | `82fa63ccb6e30b3a1da85303540f1638f9927fd9` |
| `src/services/validation/context_validator.py` | `c3JjL3NlcnZpY2VzL3ZhbGlkYXRpb24vY29udGV4dF92YWxpZGF0b3IucHk=` | `1-366` | 12 | `a9c398280690452966e910201db72cf93c3ad59f` |
| `src/services/validation/interfaces.py` | `c3JjL3NlcnZpY2VzL3ZhbGlkYXRpb24vaW50ZXJmYWNlcy5weQ==` | `1-210` | 14 | `5296a1abc0409584e5aea162d564d7eb7f1a8ce9` |
| `src/services/validation/mappers.py` | `c3JjL3NlcnZpY2VzL3ZhbGlkYXRpb24vbWFwcGVycy5weQ==` | `1-278` | 4 | `8d777245f93d0583ea1887ed5ff6dcac2eb93378` |
| `src/services/validation/modular_validation_service.py` | `c3JjL3NlcnZpY2VzL3ZhbGlkYXRpb24vbW9kdWxhcl92YWxpZGF0aW9uX3NlcnZpY2UucHk=` | `1-1767` | 45 | `6e9e1fa95958fb068f6d13494bb409d508aa4cef` |
| `src/services/validation/module_adapter.py` | `c3JjL3NlcnZpY2VzL3ZhbGlkYXRpb24vbW9kdWxlX2FkYXB0ZXIucHk=` | `1-82` | 5 | `1fcbc9e1b83a6af6466e14550f89f7fb72995489` |

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

- P1/proven: `B023-001` — Soft floor overrides failed critical acceptance gates.
- P1/proven: `B023-002` — Degraded validation fallback crashes on first use.
- P1/proven: `B023-003` — Category and domain context disappear from active validation.
- P2/proven: `B023-004` — Cleaning configuration flags have no effect.
- P2/proven: `B023-005` — Schema compliance helper accepts arbitrary shapes.
- P2/proven: `B023-006` — Raw exception detail is returned to validation clients.
- P2/proven: `B023-007` — Public batch validation deadlocks and fails whole batches.
- P3/proven: `B023-008` — Context validator crashes after reporting invalid root types.
- P3/proven: `B023-009` — Empty legal reference crashes ASTRA validation.
- P3/proven: `B023-010` — Concrete cleaning service is called with the wrong signature.
- P3/proven: `B023-011` — Fallback redundancy regex uses literal backslashes.
- Volledig bewijs en niet-geteste onderdelen: `evidence/BATCH-023/review-evidence.md`.

## Resultaat

Geverifieerd door twee verschillende reviewers. Alle toegewezen bestanden, regels en symbolen van BATCH-023 zijn line-by-line beoordeeld; beperkingen staan expliciet in het bewijsdossier.
