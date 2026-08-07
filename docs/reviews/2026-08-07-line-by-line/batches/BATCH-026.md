# BATCH-026

- Status: `pending`
- Reviewgroep: `7` — Validatie, toetsregels, opschoning en sanitization
- Review-base: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Membership-SHA256: `7b474266e61c420b55c10aff43b27f4e91e5638e7ce21ef7da561e6bf581f150`
- Bestanden: `20`
- Fysieke regels: `1820`
- Python-symbolen: `58`
- Reviewer: ``
- Onafhankelijke verifier: ``

## Scope

| Pad | path_b64 | Regelbereik | Symbolen | Object-ID |
|---|---|---:|---:|---|
| `src/toetsregels/regels/CON-02.py` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9DT04tMDIucHk=` | `1-153` | 6 | `13955e0c265cf640b40a43c38611ba2444b9e44d` |
| `src/toetsregels/regels/CON-CIRC-001.json` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9DT04tQ0lSQy0wMDEuanNvbg==` | `1-12` | 0 | `ce2a2f54937a7c429d0b197c45578ba5012b7e01` |
| `src/toetsregels/regels/DUP_01.json` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9EVVBfMDEuanNvbg==` | `1-22` | 0 | `c816df01a5896ab34c3d09365f216b7b2591a3ae` |
| `src/toetsregels/regels/DUP_01.py` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9EVVBfMDEucHk=` | `1-169` | 7 | `b178c4b92c7022c7dc7660cd1398d78383bb5865` |
| `src/toetsregels/regels/ESS-01.json` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9FU1MtMDEuanNvbg==` | `1-38` | 0 | `97240a480b7be36caf1511b06762b30446331e90` |
| `src/toetsregels/regels/ESS-01.py` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9FU1MtMDEucHk=` | `1-117` | 6 | `3c0a49953f59e3083f59b9405d2be11328dcb575` |
| `src/toetsregels/regels/ESS-02.json` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9FU1MtMDIuanNvbg==` | `1-65` | 0 | `395b46dcc4f7a77cc4cd7b31880419042599c5dd` |
| `src/toetsregels/regels/ESS-02.py` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9FU1MtMDIucHk=` | `1-231` | 6 | `d7941f0ad69056b0c4ae437a5ac774c1fda473ea` |
| `src/toetsregels/regels/ESS-03.json` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9FU1MtMDMuanNvbg==` | `1-30` | 0 | `8ec8229a74a1b7d4de705aea6aab671c86d466bd` |
| `src/toetsregels/regels/ESS-03.py` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9FU1MtMDMucHk=` | `1-169` | 9 | `716f58733e197e04928d178c5f0cd3379c0e7e8f` |
| `src/toetsregels/regels/ESS-04.json` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9FU1MtMDQuanNvbg==` | `1-43` | 0 | `a634162d717779af730242eceee2d38fe14505f7` |
| `src/toetsregels/regels/ESS-04.py` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9FU1MtMDQucHk=` | `1-155` | 6 | `27a2147d4a34f57845609bf68e99055870c2ffa8` |
| `src/toetsregels/regels/ESS-05.json` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9FU1MtMDUuanNvbg==` | `1-36` | 0 | `40345d1371c274ad0e82978b90e9115f5bfb2443` |
| `src/toetsregels/regels/ESS-05.py` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9FU1MtMDUucHk=` | `1-156` | 6 | `eee85ff3fd46d9cc6f882dcad9be72d56548be7d` |
| `src/toetsregels/regels/ESS-CONT-001.json` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9FU1MtQ09OVC0wMDEuanNvbg==` | `1-12` | 0 | `9f74ff3d61c57f168309b3d79cb7707122c62d18` |
| `src/toetsregels/regels/INT-01.json` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9JTlQtMDEuanNvbg==` | `1-39` | 0 | `e1ca29b5e2a66734a20fd8ae28e2532ee9d8b64c` |
| `src/toetsregels/regels/INT-01.py` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9JTlQtMDEucHk=` | `1-164` | 6 | `5b906c6411f828ff56ccf945360b10ec18381fd0` |
| `src/toetsregels/regels/INT-02.json` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9JTlQtMDIuanNvbg==` | `1-35` | 0 | `4de6c210e5bfbed2e428905741dc055443628c70` |
| `src/toetsregels/regels/INT-02.py` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9JTlQtMDIucHk=` | `1-136` | 6 | `865537c72b988e7887cc422298cae62a4f8b243a` |
| `src/toetsregels/regels/INT-03.json` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9JTlQtMDMuanNvbg==` | `1-38` | 0 | `b3c8363878be516751f5a5d96c3e0f29b4c8f161` |

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
