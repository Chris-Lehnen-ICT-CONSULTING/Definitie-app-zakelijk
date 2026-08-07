# BATCH-030

- Status: `pending`
- Reviewgroep: `7` — Validatie, toetsregels, opschoning en sanitization
- Review-base: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Membership-SHA256: `5467d9a6a8a26c57d85da5da67dbcebac008f66b1df3618e3626061e767e8427`
- Bestanden: `20`
- Fysieke regels: `644`
- Python-symbolen: `16`
- Reviewer: ``
- Onafhankelijke verifier: ``

## Scope

| Pad | path_b64 | Regelbereik | Symbolen | Object-ID |
|---|---|---:|---:|---|
| `src/toetsregels/sets/__init__.py` | `c3JjL3RvZXRzcmVnZWxzL3NldHMvX19pbml0X18ucHk=` | `1-1` | 1 | `df6c233fd3e6e91e02e1cfff83cfd3f0f3baf7a5` |
| `src/toetsregels/sets/per-categorie/__init__.py` | `c3JjL3RvZXRzcmVnZWxzL3NldHMvcGVyLWNhdGVnb3JpZS9fX2luaXRfXy5weQ==` | `1-1` | 1 | `d273ba552d63bf03033f0d3eda0a30a9e2de2c90` |
| `src/toetsregels/sets/per-categorie/arai.json` | `c3JjL3RvZXRzcmVnZWxzL3NldHMvcGVyLWNhdGVnb3JpZS9hcmFpLmpzb24=` | `1-15` | 0 | `4b3c440856f747a5a7f00dfe38e5173afc95dc8a` |
| `src/toetsregels/sets/per-categorie/context.json` | `c3JjL3RvZXRzcmVnZWxzL3NldHMvcGVyLWNhdGVnb3JpZS9jb250ZXh0Lmpzb24=` | `1-8` | 0 | `d10f87b63f3277ad040a198ce342fa1cd783c5c1` |
| `src/toetsregels/sets/per-categorie/essentie.json` | `c3JjL3RvZXRzcmVnZWxzL3NldHMvcGVyLWNhdGVnb3JpZS9lc3NlbnRpZS5qc29u` | `1-11` | 0 | `ae6ab6b90403c3bb00c4302bfc9abdd250202d69` |
| `src/toetsregels/sets/per-categorie/interne.json` | `c3JjL3RvZXRzcmVnZWxzL3NldHMvcGVyLWNhdGVnb3JpZS9pbnRlcm5lLmpzb24=` | `1-15` | 0 | `85925aba3edeee1c973251905400505ef021e9b9` |
| `src/toetsregels/sets/per-categorie/samenhang.json` | `c3JjL3RvZXRzcmVnZWxzL3NldHMvcGVyLWNhdGVnb3JpZS9zYW1lbmhhbmcuanNvbg==` | `1-14` | 0 | `5110206c5cb0f41a1e00b8c0fdab566d35bed053` |
| `src/toetsregels/sets/per-categorie/structuur.json` | `c3JjL3RvZXRzcmVnZWxzL3NldHMvcGVyLWNhdGVnb3JpZS9zdHJ1Y3R1dXIuanNvbg==` | `1-15` | 0 | `95a75b532c07aab82c61983bfce685f4bdba49b3` |
| `src/toetsregels/sets/per-context/__init__.py` | `c3JjL3RvZXRzcmVnZWxzL3NldHMvcGVyLWNvbnRleHQvX19pbml0X18ucHk=` | `1-1` | 1 | `e0ed3084cf8f09d79406ce19d701d80c797ca4dd` |
| `src/toetsregels/sets/per-context/exemplaar-regels.json` | `c3JjL3RvZXRzcmVnZWxzL3NldHMvcGVyLWNvbnRleHQvZXhlbXBsYWFyLXJlZ2Vscy5qc29u` | `1-43` | 0 | `bb234cd8796c66791c913cd66be25cf413eda59d` |
| `src/toetsregels/sets/per-context/proces-regels.json` | `c3JjL3RvZXRzcmVnZWxzL3NldHMvcGVyLWNvbnRleHQvcHJvY2VzLXJlZ2Vscy5qc29u` | `1-43` | 0 | `a6bbba99706389adfa9092e48c280353d6289d9f` |
| `src/toetsregels/sets/per-context/resultaat-regels.json` | `c3JjL3RvZXRzcmVnZWxzL3NldHMvcGVyLWNvbnRleHQvcmVzdWx0YWF0LXJlZ2Vscy5qc29u` | `1-43` | 0 | `dca4b865217f8308358ebced69f6af1207f03936` |
| `src/toetsregels/sets/per-context/type-regels.json` | `c3JjL3RvZXRzcmVnZWxzL3NldHMvcGVyLWNvbnRleHQvdHlwZS1yZWdlbHMuanNvbg==` | `1-43` | 0 | `efda85959a6ff16705fe8bc35a1a90955ce1c0ef` |
| `src/toetsregels/sets/per-prioriteit/__init__.py` | `c3JjL3RvZXRzcmVnZWxzL3NldHMvcGVyLXByaW9yaXRlaXQvX19pbml0X18ucHk=` | `1-1` | 1 | `14cbffb40a206c6eb0d892da0f944ae0587d177b` |
| `src/toetsregels/sets/per-prioriteit/hoog.json` | `c3JjL3RvZXRzcmVnZWxzL3NldHMvcGVyLXByaW9yaXRlaXQvaG9vZy5qc29u` | `1-28` | 0 | `6c2ddf37ff1c294a27ffb62abc424382c9f3edb4` |
| `src/toetsregels/sets/per-prioriteit/verplicht-hoog.json` | `c3JjL3RvZXRzcmVnZWxzL3NldHMvcGVyLXByaW9yaXRlaXQvdmVycGxpY2h0LWhvb2cuanNvbg==` | `1-28` | 0 | `06af13a1d38fc5207442d76c4e66fedb080969df` |
| `src/toetsregels/sets/per-prioriteit/verplicht.json` | `c3JjL3RvZXRzcmVnZWxzL3NldHMvcGVyLXByaW9yaXRlaXQvdmVycGxpY2h0Lmpzb24=` | `1-40` | 0 | `49df471b2ec4cf6c1d4d970b608902e5ba4d332c` |
| `src/toetsregels/toetsregels-manager.json` | `c3JjL3RvZXRzcmVnZWxzL3RvZXRzcmVnZWxzLW1hbmFnZXIuanNvbg==` | `1-37` | 0 | `fe2b30c3572907c6238a5926e6a82d38997522e9` |
| `src/toetsregels/validators/ARAI01.py` | `c3JjL3RvZXRzcmVnZWxzL3ZhbGlkYXRvcnMvQVJBSTAxLnB5` | `1-130` | 6 | `1c121693f4e0951b914c60f6187a16b2ed25dc09` |
| `src/toetsregels/validators/ARAI02.py` | `c3JjL3RvZXRzcmVnZWxzL3ZhbGlkYXRvcnMvQVJBSTAyLnB5` | `1-127` | 6 | `6190da53779cbb2b8c7ca1be4882992592cdfd82` |

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
