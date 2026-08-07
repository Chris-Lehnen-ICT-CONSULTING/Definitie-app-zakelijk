# BATCH-029

- Status: `pending`
- Reviewgroep: `7` — Validatie, toetsregels, opschoning en sanitization
- Review-base: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Membership-SHA256: `b33161a4b7a4cb6c39fb2c4f10071991460bdd3d6b06d024966b3bfca18f1a38`
- Bestanden: `20`
- Fysieke regels: `1550`
- Python-symbolen: `57`
- Reviewer: ``
- Onafhankelijke verifier: ``

## Scope

| Pad | path_b64 | Regelbereik | Symbolen | Object-ID |
|---|---|---:|---:|---|
| `src/toetsregels/regels/STR-06.py` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9TVFItMDYucHk=` | `1-131` | 6 | `1b94651c9f6e570e88151f2bb3aaeac2eeea0fa1` |
| `src/toetsregels/regels/STR-07.json` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9TVFItMDcuanNvbg==` | `1-32` | 0 | `74c781e796b1d3fe976ed9ba93e3bfb375f3c344` |
| `src/toetsregels/regels/STR-07.py` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9TVFItMDcucHk=` | `1-124` | 6 | `b36b087ddffbc5335e86ab96381a56d5cf481c2c` |
| `src/toetsregels/regels/STR-08.json` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9TVFItMDguanNvbg==` | `1-31` | 0 | `28429bc8cd00917f630f362d7dba8cad0c0bb3d8` |
| `src/toetsregels/regels/STR-08.py` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9TVFItMDgucHk=` | `1-148` | 6 | `406f9dfa5450d52c2a911976f62c8f64783b783a` |
| `src/toetsregels/regels/STR-09.json` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9TVFItMDkuanNvbg==` | `1-31` | 0 | `4eb44ad1d5c4e8fb012f2bf0ba526175853e9afc` |
| `src/toetsregels/regels/STR-09.py` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9TVFItMDkucHk=` | `1-145` | 6 | `408c0a6fef8486c54ebb72fe474e8e782a8ebdc9` |
| `src/toetsregels/regels/STR-ORG-001.json` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9TVFItT1JHLTAwMS5qc29u` | `1-17` | 0 | `2b469ab31263659ede76596a0ac56035cfa8fe76` |
| `src/toetsregels/regels/STR-TERM-001.json` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9TVFItVEVSTS0wMDEuanNvbg==` | `1-12` | 0 | `1c9fa4f109c79f1c0e77843d795e2918c311fc6d` |
| `src/toetsregels/regels/VAL-EMP-001.json` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9WQUwtRU1QLTAwMS5qc29u` | `1-12` | 0 | `d96813c8a6ff0ad2f2dec46206a72e7410f7dbef` |
| `src/toetsregels/regels/VAL-LEN-001.json` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9WQUwtTEVOLTAwMS5qc29u` | `1-13` | 0 | `989afdb05efe6e49018e52d12e0cd28c0dea4e1a` |
| `src/toetsregels/regels/VAL-LEN-002.json` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9WQUwtTEVOLTAwMi5qc29u` | `1-13` | 0 | `e0f7f6ba4ba2fbf1352afb519664d6b088a15210` |
| `src/toetsregels/regels/VER-01.json` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9WRVItMDEuanNvbg==` | `1-29` | 0 | `80529d01926b03dd5fc1d952bcd7fad19a8fcf66` |
| `src/toetsregels/regels/VER-01.py` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9WRVItMDEucHk=` | `1-111` | 6 | `c70574879746405cb70cc3e119bf8d62b0f1400e` |
| `src/toetsregels/regels/VER-02.json` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9WRVItMDIuanNvbg==` | `1-34` | 0 | `c050ef752b913f8b26f2da870ecda3fb0c25d8c8` |
| `src/toetsregels/regels/VER-02.py` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9WRVItMDIucHk=` | `1-137` | 6 | `9ba555226ecffa1ce13f0abd0a640bdb48684c08` |
| `src/toetsregels/regels/VER-03.json` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9WRVItMDMuanNvbg==` | `1-30` | 0 | `e3db142f900469f24a1d9e1b8ebcd9af7d33127a` |
| `src/toetsregels/regels/VER-03.py` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9WRVItMDMucHk=` | `1-117` | 6 | `078d306d626e4b5e938095161590a1215dbb7517` |
| `src/toetsregels/regels/__init__.py` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9fX2luaXRfXy5weQ==` | `1-1` | 1 | `25b6da9cb3821c62e3204aafb6e70a854d55f5e0` |
| `src/toetsregels/rule_cache.py` | `c3JjL3RvZXRzcmVnZWxzL3J1bGVfY2FjaGUucHk=` | `1-382` | 14 | `35fbc435b6f1ed2224b941baa34a5f034862a2fe` |

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
