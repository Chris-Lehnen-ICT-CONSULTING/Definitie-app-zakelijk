# BATCH-012

- Status: `verified`
- Reviewgroep: `5` — AI-clients, interfaces, container en modelrouter
- Review-base: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Membership-SHA256: `784983ae1f98f9a76010a116e3a8d867d059caebf2eb3f7bf8ff34712441a89c`
- Bestanden: `6`
- Fysieke regels: `1714`
- Python-symbolen: `87`
- Reviewer: `codex-hypatia`
- Onafhankelijke verifier: `codex-root`

## Scope

| Pad | path_b64 | Regelbereik | Symbolen | Object-ID |
|---|---|---:|---:|---|
| `src/services/ai/__init__.py` | `c3JjL3NlcnZpY2VzL2FpL19faW5pdF9fLnB5` | `1-83` | 2 | `364ca8e93dd828f78d5295a5f693ad6b0bb6b174` |
| `src/services/ai/anthropic_client.py` | `c3JjL3NlcnZpY2VzL2FpL2FudGhyb3BpY19jbGllbnQucHk=` | `1-169` | 7 | `cb014febc54e71c4b5e36300de6113d78f5444c0` |
| `src/services/ai/base_client.py` | `c3JjL3NlcnZpY2VzL2FpL2Jhc2VfY2xpZW50LnB5` | `1-108` | 12 | `5a8c3b5e7f617cefdd805de59274b39f465bc6cd` |
| `src/services/ai/model_router.py` | `c3JjL3NlcnZpY2VzL2FpL21vZGVsX3JvdXRlci5weQ==` | `1-174` | 12 | `bbbd181b8c224d7dd7d9d210284aa787bac8de5c` |
| `src/services/ai/openai_client.py` | `c3JjL3NlcnZpY2VzL2FpL29wZW5haV9jbGllbnQucHk=` | `1-113` | 6 | `5833a6f63c51545368073b13d929ceabb62ca502` |
| `src/services/container.py` | `c3JjL3NlcnZpY2VzL2NvbnRhaW5lci5weQ==` | `1-1067` | 48 | `11b5066fa996f04106dea4fc615cd1625815d585` |

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

- P1/proven: `B012-001` — Sanitized AI errors retain the raw SDK cause.
- P1/proven: `B012-002` — Provider reset leaves singleton configuration stale.
- P2/proven: `B012-003` — Container singleton factories race during construction.
- P2/proven: `B012-004` — Container reset discards resources without closing them.
- P2/proven: `B012-005` — Malformed provider responses escape consistent handling.
- P2/proven: `B012-006` — Web lookup initialization failure is cached permanently.
- P2/proven: `B012-007` — Shallow provider configuration merge breaks partial overrides.
- P3/proven: `B012-008` — Unknown models receive plausible default pricing.
- P3/proven: `B012-009` — Synonym registry fallback imports the same implementation.
- Volledig bewijs en niet-geteste onderdelen: `evidence/BATCH-012/review-evidence.md`.

## Resultaat

Geverifieerd door twee verschillende reviewers. Alle 6 bestanden en 87 symbolen zijn line-by-line beoordeeld; functionele beperkingen en niet-geteste externe of visuele flows staan expliciet in het bewijsdossier.
