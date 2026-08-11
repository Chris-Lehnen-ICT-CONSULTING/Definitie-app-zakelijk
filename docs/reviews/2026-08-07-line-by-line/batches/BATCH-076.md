# BATCH-076

- Status: `verified`
- Reviewgroep: `13` — Unit-tests gekoppeld aan productieonderdelen
- Review-base: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Membership-SHA256: `8f1301ce860485f33edcc52bc21d17b64889edd111d4700a9a0abc5991db7231`
- Bestanden: `5`
- Fysieke regels: `1513`
- Python-symbolen: `117`
- Reviewer: `codex-hypatia`
- Onafhankelijke verifier: `codex-kierkegaard`

## Scope

| Pad | path_b64 | Regelbereik | Symbolen | Object-ID |
|---|---|---:|---:|---|
| `tests/unit/test_story_2_4_unit.py` | `dGVzdHMvdW5pdC90ZXN0X3N0b3J5XzJfNF91bml0LnB5` | `1-543` | 35 | `416a0e0ac67614ef772d8d6655ca05ef97b18a1a` |
| `tests/unit/test_story_31_sources_metadata.py` | `dGVzdHMvdW5pdC90ZXN0X3N0b3J5XzMxX3NvdXJjZXNfbWV0YWRhdGEucHk=` | `1-264` | 15 | `cf228f1553e9613cebe01eeacaebcf6cc8426a54` |
| `tests/unit/test_tool_pins.py` | `dGVzdHMvdW5pdC90ZXN0X3Rvb2xfcGlucy5weQ==` | `1-67` | 13 | `6dc5c009263c6d479e8fbabda1f731a4dc564700` |
| `tests/unit/test_unified_voorbeelden_routing.py` | `dGVzdHMvdW5pdC90ZXN0X3VuaWZpZWRfdm9vcmJlZWxkZW5fcm91dGluZy5weQ==` | `1-186` | 23 | `a6919d03b84a166e2573ff0d6b84aea551cb1c6c` |
| `tests/unit/test_us041_context_field_mapping.py` | `dGVzdHMvdW5pdC90ZXN0X3VzMDQxX2NvbnRleHRfZmllbGRfbWFwcGluZy5weQ==` | `1-453` | 31 | `2ad271af04d19b1b8f25fc4c25b3fc2b5cad1675` |

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

- P2/proven: `B076-001` — US041 tests invoke the intentionally removed synchronous prompt API.
- P2/proven: `B076-002` — Rechtspraak ECLI metadata is dropped before provenance construction.

## Resultaat

Geverifieerd door twee verschillende reviewers. Alle 5 bestanden, 1513 fysieke regels en 117 symbolen zijn line-by-line beoordeeld; gerichte tests, veilige reproducties en beperkingen staan in het bewijsdossier.
