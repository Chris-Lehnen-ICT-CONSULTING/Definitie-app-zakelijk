# BATCH-032

- Status: `verified`
- Reviewgroep: `7` — Validatie, toetsregels, opschoning en sanitization
- Review-base: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Membership-SHA256: `57305794dc9493cb6adc33040017e1e7606879c89cc425e2ed163e1530811ddd`
- Bestanden: `20`
- Fysieke regels: `2712`
- Python-symbolen: `120`
- Reviewer: `codex-hypatia`
- Onafhankelijke verifier: `codex-root`

## Scope

| Pad | path_b64 | Regelbereik | Symbolen | Object-ID |
|---|---|---:|---:|---|
| `src/toetsregels/validators/INT_08.py` | `c3JjL3RvZXRzcmVnZWxzL3ZhbGlkYXRvcnMvSU5UXzA4LnB5` | `1-172` | 6 | `6dfb1958c58061a6d02a40442fa147254affbbc8` |
| `src/toetsregels/validators/INT_09.py` | `c3JjL3RvZXRzcmVnZWxzL3ZhbGlkYXRvcnMvSU5UXzA5LnB5` | `1-159` | 6 | `31e596152e1cbf2f58832e1285d7b50a5d73a48e` |
| `src/toetsregels/validators/INT_10.py` | `c3JjL3RvZXRzcmVnZWxzL3ZhbGlkYXRvcnMvSU5UXzEwLnB5` | `1-148` | 6 | `c249249029c0ee534f3b7f29dd5029b663b58e86` |
| `src/toetsregels/validators/SAM_01.py` | `c3JjL3RvZXRzcmVnZWxzL3ZhbGlkYXRvcnMvU0FNXzAxLnB5` | `1-159` | 6 | `96aa518dfbe03590a9cef1a5246c7804362cdc24` |
| `src/toetsregels/validators/SAM_02.py` | `c3JjL3RvZXRzcmVnZWxzL3ZhbGlkYXRvcnMvU0FNXzAyLnB5` | `1-129` | 6 | `dfa89d1e6ace627c9f3f15bb88eb83c5bcf897cd` |
| `src/toetsregels/validators/SAM_03.py` | `c3JjL3RvZXRzcmVnZWxzL3ZhbGlkYXRvcnMvU0FNXzAzLnB5` | `1-114` | 6 | `9dd864d7d76fa356f809fa2817d75b9e05fd883d` |
| `src/toetsregels/validators/SAM_04.py` | `c3JjL3RvZXRzcmVnZWxzL3ZhbGlkYXRvcnMvU0FNXzA0LnB5` | `1-123` | 6 | `004fa8c3b7cff40da21f7c1954477570cfab3a6e` |
| `src/toetsregels/validators/SAM_05.py` | `c3JjL3RvZXRzcmVnZWxzL3ZhbGlkYXRvcnMvU0FNXzA1LnB5` | `1-126` | 6 | `55ab02ab0f0f56a5861f0775327c36bea3511034` |
| `src/toetsregels/validators/SAM_06.py` | `c3JjL3RvZXRzcmVnZWxzL3ZhbGlkYXRvcnMvU0FNXzA2LnB5` | `1-133` | 6 | `1b3f122055bc86a5d80c356b1cd7960427f2d95f` |
| `src/toetsregels/validators/SAM_07.py` | `c3JjL3RvZXRzcmVnZWxzL3ZhbGlkYXRvcnMvU0FNXzA3LnB5` | `1-130` | 6 | `eef64799372d6eb909d3ecfdccfe4116e43e850c` |
| `src/toetsregels/validators/SAM_08.py` | `c3JjL3RvZXRzcmVnZWxzL3ZhbGlkYXRvcnMvU0FNXzA4LnB5` | `1-129` | 6 | `5c8f8e33070ce8e2eb37e5d07bde746c224600d0` |
| `src/toetsregels/validators/STR_01.py` | `c3JjL3RvZXRzcmVnZWxzL3ZhbGlkYXRvcnMvU1RSXzAxLnB5` | `1-125` | 6 | `d30df51f469bb3720087ed3abc520e5117f7953d` |
| `src/toetsregels/validators/STR_02.py` | `c3JjL3RvZXRzcmVnZWxzL3ZhbGlkYXRvcnMvU1RSXzAyLnB5` | `1-128` | 6 | `7264acf9d9f912e54107dd5471043567702eff47` |
| `src/toetsregels/validators/STR_03.py` | `c3JjL3RvZXRzcmVnZWxzL3ZhbGlkYXRvcnMvU1RSXzAzLnB5` | `1-134` | 6 | `59b72a114dc3c887e27de4c2b4e8f583298bf658` |
| `src/toetsregels/validators/STR_04.py` | `c3JjL3RvZXRzcmVnZWxzL3ZhbGlkYXRvcnMvU1RSXzA0LnB5` | `1-128` | 6 | `8acf06460e02878880de00e4af4c13c9517efb92` |
| `src/toetsregels/validators/STR_05.py` | `c3JjL3RvZXRzcmVnZWxzL3ZhbGlkYXRvcnMvU1RSXzA1LnB5` | `1-127` | 6 | `27be94ee86c6951f3ec3c20ea64f2fea41bc38cb` |
| `src/toetsregels/validators/STR_06.py` | `c3JjL3RvZXRzcmVnZWxzL3ZhbGlkYXRvcnMvU1RSXzA2LnB5` | `1-131` | 6 | `1b94651c9f6e570e88151f2bb3aaeac2eeea0fa1` |
| `src/toetsregels/validators/STR_07.py` | `c3JjL3RvZXRzcmVnZWxzL3ZhbGlkYXRvcnMvU1RSXzA3LnB5` | `1-124` | 6 | `b36b087ddffbc5335e86ab96381a56d5cf481c2c` |
| `src/toetsregels/validators/STR_08.py` | `c3JjL3RvZXRzcmVnZWxzL3ZhbGlkYXRvcnMvU1RSXzA4LnB5` | `1-148` | 6 | `406f9dfa5450d52c2a911976f62c8f64783b783a` |
| `src/toetsregels/validators/STR_09.py` | `c3JjL3RvZXRzcmVnZWxzL3ZhbGlkYXRvcnMvU1RSXzA5LnB5` | `1-145` | 6 | `408c0a6fef8486c54ebb72fe474e8e782a8ebdc9` |

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

- P2/proven: `B032-001` — INT-08 lets multiple invalid negations pass together.
- P3/proven: `B032-002` — INT-09 makes period-ending regexes unmatchable.
- P2/proven: `B032-003` — Six SAM validators implement a different contract.
- P3/proven: `B032-004` — STR-01 and STR-02 miss capitalization and term kick-off.
- P3/proven: `B032-005` — STR-08 and STR-09 create false positives and misleading labels.
- Volledig bewijs en niet-geteste onderdelen: `evidence/BATCH-032/review-evidence.md`.

## Resultaat

Geverifieerd door twee verschillende reviewers. Alle 20 bestanden, 2712 fysieke regels en 120 symbolen zijn line-by-line beoordeeld; gerichte tests, veilige reproducties en beperkingen staan in het bewijsdossier.
