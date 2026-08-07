# BATCH-025

- Status: `pending`
- Reviewgroep: `7` — Validatie, toetsregels, opschoning en sanitization
- Review-base: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Membership-SHA256: `5a8042a4f60956351089fe8aec031c53e39f3caff50c24981de8d51527b2bef7`
- Bestanden: `20`
- Fysieke regels: `1781`
- Python-symbolen: `61`
- Reviewer: ``
- Onafhankelijke verifier: ``

## Scope

| Pad | path_b64 | Regelbereik | Symbolen | Object-ID |
|---|---|---:|---:|---|
| `src/toetsregels/regels/ARAI-01.py` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9BUkFJLTAxLnB5` | `1-136` | 6 | `65960370b2ed6aa939cf280ac93267c16e3b2a46` |
| `src/toetsregels/regels/ARAI-02.json` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9BUkFJLTAyLmpzb24=` | `1-37` | 0 | `f34ceeb8600aec2bf0e6d0e5c10b101ca1cbdc3c` |
| `src/toetsregels/regels/ARAI-02.py` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9BUkFJLTAyLnB5` | `1-127` | 6 | `6190da53779cbb2b8c7ca1be4882992592cdfd82` |
| `src/toetsregels/regels/ARAI-02SUB1.json` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9BUkFJLTAyU1VCMS5qc29u` | `1-27` | 0 | `2a4194f9c6a6461a0081f01b7bfa8ec3484e21f4` |
| `src/toetsregels/regels/ARAI-02SUB1.py` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9BUkFJLTAyU1VCMS5weQ==` | `1-131` | 6 | `70c38ecfc4695addfc54a88b176a8dafe23c67db` |
| `src/toetsregels/regels/ARAI-02SUB2.json` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9BUkFJLTAyU1VCMi5qc29u` | `1-28` | 0 | `24af146a47c0046bf09c5e5177f649dd6d0242cf` |
| `src/toetsregels/regels/ARAI-02SUB2.py` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9BUkFJLTAyU1VCMi5weQ==` | `1-133` | 6 | `34059caea857bc47041a77f75a5358e6de52fde9` |
| `src/toetsregels/regels/ARAI-03.json` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9BUkFJLTAzLmpzb24=` | `1-37` | 0 | `662f1dae6e10b9d19f3cac45a75b153ecce41863` |
| `src/toetsregels/regels/ARAI-03.py` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9BUkFJLTAzLnB5` | `1-127` | 6 | `440ace30ad850381f504f0b9a6247cc3fc37eb26` |
| `src/toetsregels/regels/ARAI-04.json` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9BUkFJLTA0Lmpzb24=` | `1-38` | 0 | `367be63ffff23fe11c28bc1d3b0bbe5c74e30e0c` |
| `src/toetsregels/regels/ARAI-04.py` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9BUkFJLTA0LnB5` | `1-126` | 6 | `e651205347a1dfab226de03833ee507a9fb43cea` |
| `src/toetsregels/regels/ARAI-04SUB1.json` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9BUkFJLTA0U1VCMS5qc29u` | `1-35` | 0 | `1e137b6a096c270230de0af9a6b97ba061f7e2e0` |
| `src/toetsregels/regels/ARAI-04SUB1.py` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9BUkFJLTA0U1VCMS5weQ==` | `1-131` | 6 | `47f5b53ee24ca36a552543a4ba164ff6f2639f5f` |
| `src/toetsregels/regels/ARAI-05.json` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9BUkFJLTA1Lmpzb24=` | `1-33` | 0 | `478bde817771212ade6b2bc72f1635a14e856483` |
| `src/toetsregels/regels/ARAI-05.py` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9BUkFJLTA1LnB5` | `1-126` | 6 | `3f3d0b848658dfa00871df738499f091f5eac738` |
| `src/toetsregels/regels/ARAI-06.json` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9BUkFJLTA2Lmpzb24=` | `1-38` | 0 | `c05f857bef3623e6e10e23b16524258a42d4f721` |
| `src/toetsregels/regels/ARAI-06.py` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9BUkFJLTA2LnB5` | `1-142` | 6 | `5ee8ad28f0c165f790ff573992dc83b6c5162683` |
| `src/toetsregels/regels/CON-01.json` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9DT04tMDEuanNvbg==` | `1-52` | 0 | `7e978ba3bb60acf269c49558a01c00fe96babb06` |
| `src/toetsregels/regels/CON-01.py` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9DT04tMDEucHk=` | `1-217` | 7 | `c757097908627da4512d66cb672e1bd3b3a9bbeb` |
| `src/toetsregels/regels/CON-02.json` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9DT04tMDIuanNvbg==` | `1-60` | 0 | `abb1bf8d1a30c6e2b75c5727266b3f4593e56d48` |

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
