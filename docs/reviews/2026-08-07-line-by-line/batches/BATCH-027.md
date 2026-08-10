# BATCH-027

- Status: `verified`
- Reviewgroep: `7` — Validatie, toetsregels, opschoning en sanitization
- Review-base: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Membership-SHA256: `b6ab213f748e72dfcce27c1330b4dde995d56605978f526e3c483b364135e65e`
- Bestanden: `20`
- Fysieke regels: `1789`
- Python-symbolen: `60`
- Reviewer: `codex-kierkegaard`
- Onafhankelijke verifier: `codex-galileo`

## Scope

| Pad | path_b64 | Regelbereik | Symbolen | Object-ID |
|---|---|---:|---:|---|
| `src/toetsregels/regels/INT-03.py` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9JTlQtMDMucHk=` | `1-148` | 6 | `af80f99ab7895bd55d49449d06b7327ce4d0d44d` |
| `src/toetsregels/regels/INT-04.json` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9JTlQtMDQuanNvbg==` | `1-30` | 0 | `3bc17820796edcef2e883cccdd544b8470e54468` |
| `src/toetsregels/regels/INT-04.py` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9JTlQtMDQucHk=` | `1-145` | 6 | `b4c6b90a6a5a48edcb51acd6b296db78f34bb768` |
| `src/toetsregels/regels/INT-06.json` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9JTlQtMDYuanNvbg==` | `1-33` | 0 | `d291da0c0fe00f3d44b98308fc71850a05a7de29` |
| `src/toetsregels/regels/INT-06.py` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9JTlQtMDYucHk=` | `1-139` | 6 | `15722b14764618f60032ee8d98078e665cc5d5a8` |
| `src/toetsregels/regels/INT-07.json` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9JTlQtMDcuanNvbg==` | `1-37` | 0 | `6ce333d24321d76e8657a46a0feb3ceb95c7efcf` |
| `src/toetsregels/regels/INT-07.py` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9JTlQtMDcucHk=` | `1-148` | 6 | `e4306337069c307fc5b30e2fb77795266f900f57` |
| `src/toetsregels/regels/INT-08.json` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9JTlQtMDguanNvbg==` | `1-35` | 0 | `b03f69b10f2951169279d7dec9beac934f5da935` |
| `src/toetsregels/regels/INT-08.py` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9JTlQtMDgucHk=` | `1-172` | 6 | `6dfb1958c58061a6d02a40442fa147254affbbc8` |
| `src/toetsregels/regels/INT-09.json` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9JTlQtMDkuanNvbg==` | `1-38` | 0 | `4c41244b769440b7c51e755c4e3829cc4d95e6b4` |
| `src/toetsregels/regels/INT-09.py` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9JTlQtMDkucHk=` | `1-159` | 6 | `31e596152e1cbf2f58832e1285d7b50a5d73a48e` |
| `src/toetsregels/regels/INT-10.json` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9JTlQtMTAuanNvbg==` | `1-37` | 0 | `612ba8a89c4e76bd12062f150185759caab3113a` |
| `src/toetsregels/regels/INT-10.py` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9JTlQtMTAucHk=` | `1-148` | 6 | `c249249029c0ee534f3b7f29dd5029b663b58e86` |
| `src/toetsregels/regels/SAM-01.json` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9TQU0tMDEuanNvbg==` | `1-33` | 0 | `7bae36ec6e42455e58e3f687ccbec5c292b91aed` |
| `src/toetsregels/regels/SAM-01.py` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9TQU0tMDEucHk=` | `1-159` | 6 | `96aa518dfbe03590a9cef1a5246c7804362cdc24` |
| `src/toetsregels/regels/SAM-02.json` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9TQU0tMDIuanNvbg==` | `1-27` | 0 | `a6c22ea0c15bc1a790d3dad80c83fc915763d176` |
| `src/toetsregels/regels/SAM-02.py` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9TQU0tMDIucHk=` | `1-129` | 6 | `dfa89d1e6ace627c9f3f15bb88eb83c5bcf897cd` |
| `src/toetsregels/regels/SAM-03.json` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9TQU0tMDMuanNvbg==` | `1-31` | 0 | `fb8c7ccb6d7d9e4fd5e39cc7c909590ccd61645f` |
| `src/toetsregels/regels/SAM-03.py` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9TQU0tMDMucHk=` | `1-114` | 6 | `9dd864d7d76fa356f809fa2817d75b9e05fd883d` |
| `src/toetsregels/regels/SAM-04.json` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9TQU0tMDQuanNvbg==` | `1-27` | 0 | `e63536bf92848a60e823b8d5da29ca724317dba3` |

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

- P1/proven: `B027-001` — INT-07 flags ordinary lowercase words as abbreviations.
- P2/proven: `B027-002` — SAM-04 only works for colon-prefixed definitions.
- P3/proven: `B027-003` — INT-09 cannot match the abbreviation o.a..
- P3/proven: `B027-004` — Legacy SAM validators implement different JSON contracts.
- Volledig bewijs en niet-geteste onderdelen: `evidence/BATCH-027/review-evidence.md`.

## Resultaat

Geverifieerd door twee verschillende reviewers. Alle 20 bestanden, 1789 fysieke regels en 60 symbolen zijn line-by-line beoordeeld; gerichte tests, veilige reproducties en beperkingen staan in het bewijsdossier.
