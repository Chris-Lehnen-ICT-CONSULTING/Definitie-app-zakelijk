# BATCH-170

- Status: `verified`
- Reviewgroep: `17` — Documentatie, plannen en handovers
- Review-base: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Membership-SHA256: `93cf29f04fb3b6cca14d2da269fc3f3eef2da611c35d73cf57c7e1195da4ef1e`
- Bestanden: `16`
- Fysieke regels: `5847`
- Python-symbolen: `29`
- Reviewer: `codex-galileo`
- Onafhankelijke verifier: `codex-hypatia`

## Scope

| Pad | path_b64 | Regelbereik | Symbolen | Object-ID |
|---|---|---:|---:|---|
| `docs/debugging/DEF-99-TEST-VALIDATION-REPORT.md` | `ZG9jcy9kZWJ1Z2dpbmcvREVGLTk5LVRFU1QtVkFMSURBVElPTi1SRVBPUlQubWQ=` | `1-281` | 0 | `5d2abe04301a1b55f33fc163af47cd3244df97f4` |
| `docs/definitie-app-architecture.md` | `ZG9jcy9kZWZpbml0aWUtYXBwLWFyY2hpdGVjdHVyZS5tZA==` | `1-1641` | 0 | `afad662b5fb056a52611ac7436ae6acb6c8fd3ae` |
| `docs/diagrams/export-architecture-problem.md` | `ZG9jcy9kaWFncmFtcy9leHBvcnQtYXJjaGl0ZWN0dXJlLXByb2JsZW0ubWQ=` | `1-206` | 0 | `195ca463cc1c9c058d4cdeb5a93345fda189f723` |
| `docs/epics/DEF-101-IMPLEMENTATION-GUIDE.md` | `ZG9jcy9lcGljcy9ERUYtMTAxLUlNUExFTUVOVEFUSU9OLUdVSURFLm1k` | `1-187` | 0 | `e3e9d557d8fcd152e5ae7f5de163a63d6f38044b` |
| `docs/examples/UI_CLASSIFICATION_FLOWS.md` | `ZG9jcy9leGFtcGxlcy9VSV9DTEFTU0lGSUNBVElPTl9GTE9XUy5tZA==` | `1-417` | 0 | `d53fae777cec11955b541f4a038d5d32f52e245b` |
| `docs/examples/classifier_integration_ui.py` | `ZG9jcy9leGFtcGxlcy9jbGFzc2lmaWVyX2ludGVncmF0aW9uX3VpLnB5` | `1-328` | 7 | `f175a88a6d955fcd1951e27817ca8e82d38afe28` |
| `docs/examples/service_adapter_with_classifier.py` | `ZG9jcy9leGFtcGxlcy9zZXJ2aWNlX2FkYXB0ZXJfd2l0aF9jbGFzc2lmaWVyLnB5` | `1-448` | 11 | `3f6533e84c0897b2fa92b8e4e37a0494e6082555` |
| `docs/examples/synonym_config_usage.py` | `ZG9jcy9leGFtcGxlcy9zeW5vbnltX2NvbmZpZ191c2FnZS5weQ==` | `1-259` | 11 | `c0c6bb58911c31ef6f8306448e8a0d3a102fe5b8` |
| `docs/frontend/AI-FRONTEND-PROMPT-NL.md` | `ZG9jcy9mcm9udGVuZC9BSS1GUk9OVEVORC1QUk9NUFQtTkwubWQ=` | `1-328` | 0 | `6bbab421249d1126ed30b011c446c915588db24a` |
| `docs/guidelines/AGENTS.md` | `ZG9jcy9ndWlkZWxpbmVzL0FHRU5UUy5tZA==` | `1-462` | 0 | `e1188ca31c8ac9a23d2623db9c0d9fa6cab50384` |
| `docs/guidelines/AI_CONFIGURATION_GUIDE.md` | `ZG9jcy9ndWlkZWxpbmVzL0FJX0NPTkZJR1VSQVRJT05fR1VJREUubWQ=` | `1-372` | 0 | `5618cbb36bea454163bcc5a9bb28e7c86355f499` |
| `docs/guidelines/CANONICAL_LOCATIONS.md` | `ZG9jcy9ndWlkZWxpbmVzL0NBTk9OSUNBTF9MT0NBVElPTlMubWQ=` | `1-153` | 0 | `ae0feab945d9021176430a2aa9bf56d27fc95717` |
| `docs/guidelines/CODE_ARCHAEOLOGY_CHECKLIST.md` | `ZG9jcy9ndWlkZWxpbmVzL0NPREVfQVJDSEFFT0xPR1lfQ0hFQ0tMSVNULm1k` | `1-209` | 0 | `3a76ceb5886c7685fbd7505039ac6d922baab3e5` |
| `docs/guidelines/DATABASE_BACKUP_RECOVERY.md` | `ZG9jcy9ndWlkZWxpbmVzL0RBVEFCQVNFX0JBQ0tVUF9SRUNPVkVSWS5tZA==` | `1-284` | 0 | `08ea8cb073c60366acdae2c74e447517d4bee3c3` |
| `docs/guidelines/DATABASE_GUIDELINES.md` | `ZG9jcy9ndWlkZWxpbmVzL0RBVEFCQVNFX0dVSURFTElORVMubWQ=` | `1-51` | 0 | `6c227c311740a0a8a99d1afc835e31457fd7817d` |
| `docs/guidelines/DOCUMENT-CREATION-WORKFLOW.md` | `ZG9jcy9ndWlkZWxpbmVzL0RPQ1VNRU5ULUNSRUFUSU9OLVdPUktGTE9XLm1k` | `1-221` | 0 | `d99bb393271992209f7b2e50c9367a1d37e15e56` |

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

- P2/proven: `B170-001` — Canonieke agentrichtlijn staat kleine verwijderingen en bestaande-bestandsformattering zonder toestemming toe.
- P2/proven: `B170-002` — Centraal geïndexeerde frontendprompt laat AI een niet-bestaande Next.js-stack en backend-authcontract bouwen.
- P2/proven: `B170-003` — Ontologie-integratievoorbeelden importeren niet en gebruiken daarna incompatibele async- en requestcontracten.
- P2/proven: `B170-004` — Actieve AI-configuratiegids beschrijft een OpenAI- en multi-environmentconfiguratie die niet bestaat.
- P2/proven: `B170-005` — Verplichte documentcreatieworkflow verwijst naar afgeschaft backlog- en architectuurbeleid.
- P3/proven: `B170-006` — Dormant synoniemvoorbeeld faalt op de enrichmentroute en negeert geldige nulwaarden.

## Resultaat

Geverifieerd door twee verschillende reviewers. Alle 16 toegewezen bereiken, 5847 fysieke regels en 29 symbolen zijn line-by-line beoordeeld; reproducties en beperkingen staan in het bewijsdossier.
