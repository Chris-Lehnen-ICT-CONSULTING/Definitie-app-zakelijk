# BATCH-031

- Status: `pending`
- Reviewgroep: `7` — Validatie, toetsregels, opschoning en sanitization
- Review-base: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Membership-SHA256: `7a588d9570118b2252dfc40884701d53a015305f2d4255f7e9d0ef66b6b50430`
- Bestanden: `20`
- Fysieke regels: `3050`
- Python-symbolen: `129`
- Reviewer: ``
- Onafhankelijke verifier: ``

## Scope

| Pad | path_b64 | Regelbereik | Symbolen | Object-ID |
|---|---|---:|---:|---|
| `src/toetsregels/validators/ARAI02SUB1.py` | `c3JjL3RvZXRzcmVnZWxzL3ZhbGlkYXRvcnMvQVJBSTAyU1VCMS5weQ==` | `1-131` | 6 | `70c38ecfc4695addfc54a88b176a8dafe23c67db` |
| `src/toetsregels/validators/ARAI02SUB2.py` | `c3JjL3RvZXRzcmVnZWxzL3ZhbGlkYXRvcnMvQVJBSTAyU1VCMi5weQ==` | `1-133` | 6 | `34059caea857bc47041a77f75a5358e6de52fde9` |
| `src/toetsregels/validators/ARAI03.py` | `c3JjL3RvZXRzcmVnZWxzL3ZhbGlkYXRvcnMvQVJBSTAzLnB5` | `1-127` | 6 | `440ace30ad850381f504f0b9a6247cc3fc37eb26` |
| `src/toetsregels/validators/ARAI04.py` | `c3JjL3RvZXRzcmVnZWxzL3ZhbGlkYXRvcnMvQVJBSTA0LnB5` | `1-126` | 6 | `e651205347a1dfab226de03833ee507a9fb43cea` |
| `src/toetsregels/validators/ARAI04SUB1.py` | `c3JjL3RvZXRzcmVnZWxzL3ZhbGlkYXRvcnMvQVJBSTA0U1VCMS5weQ==` | `1-131` | 6 | `47f5b53ee24ca36a552543a4ba164ff6f2639f5f` |
| `src/toetsregels/validators/ARAI05.py` | `c3JjL3RvZXRzcmVnZWxzL3ZhbGlkYXRvcnMvQVJBSTA1LnB5` | `1-126` | 6 | `3f3d0b848658dfa00871df738499f091f5eac738` |
| `src/toetsregels/validators/ARAI06.py` | `c3JjL3RvZXRzcmVnZWxzL3ZhbGlkYXRvcnMvQVJBSTA2LnB5` | `1-142` | 6 | `5ee8ad28f0c165f790ff573992dc83b6c5162683` |
| `src/toetsregels/validators/CON_01.py` | `c3JjL3RvZXRzcmVnZWxzL3ZhbGlkYXRvcnMvQ09OXzAxLnB5` | `1-273` | 12 | `309da7252936fed2fa8af870f596987e7ef02ad8` |
| `src/toetsregels/validators/CON_02.py` | `c3JjL3RvZXRzcmVnZWxzL3ZhbGlkYXRvcnMvQ09OXzAyLnB5` | `1-153` | 6 | `13955e0c265cf640b40a43c38611ba2444b9e44d` |
| `src/toetsregels/validators/ESS_01.py` | `c3JjL3RvZXRzcmVnZWxzL3ZhbGlkYXRvcnMvRVNTXzAxLnB5` | `1-117` | 6 | `3c0a49953f59e3083f59b9405d2be11328dcb575` |
| `src/toetsregels/validators/ESS_02.py` | `c3JjL3RvZXRzcmVnZWxzL3ZhbGlkYXRvcnMvRVNTXzAyLnB5` | `1-231` | 6 | `d7941f0ad69056b0c4ae437a5ac774c1fda473ea` |
| `src/toetsregels/validators/ESS_03.py` | `c3JjL3RvZXRzcmVnZWxzL3ZhbGlkYXRvcnMvRVNTXzAzLnB5` | `1-169` | 9 | `716f58733e197e04928d178c5f0cd3379c0e7e8f` |
| `src/toetsregels/validators/ESS_04.py` | `c3JjL3RvZXRzcmVnZWxzL3ZhbGlkYXRvcnMvRVNTXzA0LnB5` | `1-155` | 6 | `27a2147d4a34f57845609bf68e99055870c2ffa8` |
| `src/toetsregels/validators/ESS_05.py` | `c3JjL3RvZXRzcmVnZWxzL3ZhbGlkYXRvcnMvRVNTXzA1LnB5` | `1-156` | 6 | `eee85ff3fd46d9cc6f882dcad9be72d56548be7d` |
| `src/toetsregels/validators/INT_01.py` | `c3JjL3RvZXRzcmVnZWxzL3ZhbGlkYXRvcnMvSU5UXzAxLnB5` | `1-164` | 6 | `5b906c6411f828ff56ccf945360b10ec18381fd0` |
| `src/toetsregels/validators/INT_02.py` | `c3JjL3RvZXRzcmVnZWxzL3ZhbGlkYXRvcnMvSU5UXzAyLnB5` | `1-136` | 6 | `865537c72b988e7887cc422298cae62a4f8b243a` |
| `src/toetsregels/validators/INT_03.py` | `c3JjL3RvZXRzcmVnZWxzL3ZhbGlkYXRvcnMvSU5UXzAzLnB5` | `1-148` | 6 | `af80f99ab7895bd55d49449d06b7327ce4d0d44d` |
| `src/toetsregels/validators/INT_04.py` | `c3JjL3RvZXRzcmVnZWxzL3ZhbGlkYXRvcnMvSU5UXzA0LnB5` | `1-145` | 6 | `b4c6b90a6a5a48edcb51acd6b296db78f34bb768` |
| `src/toetsregels/validators/INT_06.py` | `c3JjL3RvZXRzcmVnZWxzL3ZhbGlkYXRvcnMvSU5UXzA2LnB5` | `1-139` | 6 | `15722b14764618f60032ee8d98078e665cc5d5a8` |
| `src/toetsregels/validators/INT_07.py` | `c3JjL3RvZXRzcmVnZWxzL3ZhbGlkYXRvcnMvSU5UXzA3LnB5` | `1-148` | 6 | `e4306337069c307fc5b30e2fb77795266f900f57` |

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
