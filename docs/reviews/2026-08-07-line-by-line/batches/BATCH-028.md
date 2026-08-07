# BATCH-028

- Status: `pending`
- Reviewgroep: `7` — Validatie, toetsregels, opschoning en sanitization
- Review-base: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Membership-SHA256: `a4ea2ca85234ba7a618e0cc379c9f49333ad9a2d8ed5d5d6ad08f9f7081cef11`
- Bestanden: `20`
- Fysieke regels: `1595`
- Python-symbolen: `60`
- Reviewer: ``
- Onafhankelijke verifier: ``

## Scope

| Pad | path_b64 | Regelbereik | Symbolen | Object-ID |
|---|---|---:|---:|---|
| `src/toetsregels/regels/SAM-04.py` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9TQU0tMDQucHk=` | `1-123` | 6 | `004fa8c3b7cff40da21f7c1954477570cfab3a6e` |
| `src/toetsregels/regels/SAM-05.json` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9TQU0tMDUuanNvbg==` | `1-26` | 0 | `9c7634e933df5fb87c512fb5e6e683fd6fce4b8f` |
| `src/toetsregels/regels/SAM-05.py` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9TQU0tMDUucHk=` | `1-126` | 6 | `55ab02ab0f0f56a5861f0775327c36bea3511034` |
| `src/toetsregels/regels/SAM-06.json` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9TQU0tMDYuanNvbg==` | `1-22` | 0 | `a56280d30979d19ff5526ccb582a261b9a5bf2db` |
| `src/toetsregels/regels/SAM-06.py` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9TQU0tMDYucHk=` | `1-133` | 6 | `1b3f122055bc86a5d80c356b1cd7960427f2d95f` |
| `src/toetsregels/regels/SAM-07.json` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9TQU0tMDcuanNvbg==` | `1-35` | 0 | `4470271a48afd7f0d359509106a850216c14a816` |
| `src/toetsregels/regels/SAM-07.py` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9TQU0tMDcucHk=` | `1-136` | 6 | `f6ca9d5c70afc972b9b30336e581e2d9517ec41e` |
| `src/toetsregels/regels/SAM-08.json` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9TQU0tMDguanNvbg==` | `1-31` | 0 | `19de89e97343c019467eef48c34d4b6951ad303c` |
| `src/toetsregels/regels/SAM-08.py` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9TQU0tMDgucHk=` | `1-129` | 6 | `5c8f8e33070ce8e2eb37e5d07bde746c224600d0` |
| `src/toetsregels/regels/STR-01.json` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9TVFItMDEuanNvbg==` | `1-35` | 0 | `c89787970542e819710167162b1c32ac63a0ea65` |
| `src/toetsregels/regels/STR-01.py` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9TVFItMDEucHk=` | `1-125` | 6 | `d30df51f469bb3720087ed3abc520e5117f7953d` |
| `src/toetsregels/regels/STR-02.json` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9TVFItMDIuanNvbg==` | `1-29` | 0 | `d0e649527e2a9d6b3b357ea88fe492bc1ad2039a` |
| `src/toetsregels/regels/STR-02.py` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9TVFItMDIucHk=` | `1-128` | 6 | `7264acf9d9f912e54107dd5471043567702eff47` |
| `src/toetsregels/regels/STR-03.json` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9TVFItMDMuanNvbg==` | `1-30` | 0 | `35106c744fa7ab2165d86c01a58c1ae8dee3e34f` |
| `src/toetsregels/regels/STR-03.py` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9TVFItMDMucHk=` | `1-134` | 6 | `59b72a114dc3c887e27de4c2b4e8f583298bf658` |
| `src/toetsregels/regels/STR-04.json` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9TVFItMDQuanNvbg==` | `1-30` | 0 | `2cf823863d7eec23715dcfc3a5e0ff0a3a59aeb4` |
| `src/toetsregels/regels/STR-04.py` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9TVFItMDQucHk=` | `1-128` | 6 | `8acf06460e02878880de00e4af4c13c9517efb92` |
| `src/toetsregels/regels/STR-05.json` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9TVFItMDUuanNvbg==` | `1-34` | 0 | `76392d4e4e48583417b951b16415f6713c78b48d` |
| `src/toetsregels/regels/STR-05.py` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9TVFItMDUucHk=` | `1-127` | 6 | `27be94ee86c6951f3ec3c20ea64f2fea41bc38cb` |
| `src/toetsregels/regels/STR-06.json` | `c3JjL3RvZXRzcmVnZWxzL3JlZ2Vscy9TVFItMDYuanNvbg==` | `1-34` | 0 | `9913fce523651e6d00ba0675deb5fc25eddbe91b` |

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
