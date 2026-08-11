# BATCH-106

- Status: `verified`
- Reviewgroep: `15` — Operationele scripts en shellcode
- Review-base: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Membership-SHA256: `f7f42094e1caae39eb060a541e360dee151f60248c72d6d13683289ae5598e00`
- Bestanden: `16`
- Fysieke regels: `3976`
- Python-symbolen: `89`
- Reviewer: `codex-hypatia`
- Onafhankelijke verifier: `codex-kierkegaard`

## Scope

| Pad | path_b64 | Regelbereik | Symbolen | Object-ID |
|---|---|---:|---:|---|
| `scripts/testing/test_consolidation.sh` | `c2NyaXB0cy90ZXN0aW5nL3Rlc3RfY29uc29saWRhdGlvbi5zaA==` | `1-84` | 0 | `d584f4004c5631cc1b144752fa4551671c50d20f` |
| `scripts/testing/test_web_lookup.py` | `c2NyaXB0cy90ZXN0aW5nL3Rlc3Rfd2ViX2xvb2t1cC5weQ==` | `1-61` | 2 | `31f3a50d80c5191ddde51f2714a5ebc395047ab3` |
| `scripts/testing/verify-v2-migration.sh` | `c2NyaXB0cy90ZXN0aW5nL3ZlcmlmeS12Mi1taWdyYXRpb24uc2g=` | `1-201` | 0 | `9cdac17d1c9730c558e9dd37c1ef882ab1129b03` |
| `scripts/testing/verify_history_removal.py` | `c2NyaXB0cy90ZXN0aW5nL3ZlcmlmeV9oaXN0b3J5X3JlbW92YWwucHk=` | `1-557` | 18 | `2ca2ef7cc61a8ce15ee12ad7d0cba9e67c5ed37b` |
| `scripts/testing/verify_history_removal.sh` | `c2NyaXB0cy90ZXN0aW5nL3ZlcmlmeV9oaXN0b3J5X3JlbW92YWwuc2g=` | `1-394` | 0 | `4a805f2d55c7e1b1fc5e5505a6e5551803c42602` |
| `scripts/testing/verify_requirements_fix.py` | `c2NyaXB0cy90ZXN0aW5nL3ZlcmlmeV9yZXF1aXJlbWVudHNfZml4LnB5` | `1-170` | 5 | `c121aa2650d14133d2b94d3fcd4b850c303b41b7` |
| `scripts/testing/verify_smart_criteria.py` | `c2NyaXB0cy90ZXN0aW5nL3ZlcmlmeV9zbWFydF9jcml0ZXJpYS5weQ==` | `1-207` | 4 | `11129c879a1577968a12ffaea6c356898cd2d891` |
| `scripts/testing/verify_tabbed_interface_caching.py` | `c2NyaXB0cy90ZXN0aW5nL3ZlcmlmeV90YWJiZWRfaW50ZXJmYWNlX2NhY2hpbmcucHk=` | `1-183` | 6 | `064ec3776acc7932baa6c0aba7d4b9e27101f517` |
| `scripts/update_us_titles.py` | `c2NyaXB0cy91cGRhdGVfdXNfdGl0bGVzLnB5` | `1-147` | 4 | `06c7dc43d80ab8bdc368d23886ad0b1f88d4f79e` |
| `scripts/validate_juridisch_keywords_migration.py` | `c2NyaXB0cy92YWxpZGF0ZV9qdXJpZGlzY2hfa2V5d29yZHNfbWlncmF0aW9uLnB5` | `1-332` | 7 | `9a6e2a44a9bf3e78e97698b2983141306a042fca` |
| `scripts/validate_provider_weighting.py` | `c2NyaXB0cy92YWxpZGF0ZV9wcm92aWRlcl93ZWlnaHRpbmcucHk=` | `1-131` | 4 | `722a893d3fb52bf18a3fff027056d454947fa0e6` |
| `scripts/validate_synonym_registry.py` | `c2NyaXB0cy92YWxpZGF0ZV9zeW5vbnltX3JlZ2lzdHJ5LnB5` | `1-296` | 11 | `344ce43f044ce12340d7d4809506eef21e437519` |
| `scripts/validate_synonyms.py` | `c2NyaXB0cy92YWxpZGF0ZV9zeW5vbnltcy5weQ==` | `1-717` | 16 | `392587913d0b08e7d7aa62ba731a78493a94d8e8` |
| `scripts/validate_week1.sh` | `c2NyaXB0cy92YWxpZGF0ZV93ZWVrMS5zaA==` | `1-37` | 0 | `30b5decc792fa41e35f0830b73cc0cb10a324b44` |
| `scripts/validation/validation-status-updater.py` | `c2NyaXB0cy92YWxpZGF0aW9uL3ZhbGlkYXRpb24tc3RhdHVzLXVwZGF0ZXIucHk=` | `1-306` | 12 | `10572aa00683ac145ee95c8d1fa861f59f515e73` |
| `scripts/verify_classification_refactor.sh` | `c2NyaXB0cy92ZXJpZnlfY2xhc3NpZmljYXRpb25fcmVmYWN0b3Iuc2g=` | `1-153` | 0 | `07d65448276e9bfa58e6685737835231f2bb6399` |

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

- P3/proven: `B106-001` — Consolidation-runner gebruikt verwijderde testpaden en stopt voor rapportage.
- P2/proven: `B106-002` — History-removal-verificatie muteert standaard de live applicatiedatabase.
- P3/proven: `B106-003` — Requirements-verifier is checkout-gebonden en crasht op de verdwenen scope.
- P3/proven: `B106-004` — Een kopje Acceptatiecriteria maakt alle vijf SMART-criteria waar.
- P3/proven: `B106-005` — Bulk title updater schrijft ongeldige YAML bij aanhalingstekens.
- P3/proven: `B106-006` — Afwijkende juridische boostfactoren worden gewaarschuwd maar goedgekeurd.
- P3/proven: `B106-007` — Geen webresultaten geldt als bewijs dat double-weighting is opgelost.
- P3/proven: `B106-008` — Negatieve SynonymRegistry-contractchecks kunnen falen terwijl de suite slaagt.
- P2/proven: `B106-009` — SynonymRegistry-validatie persisteert fixtures in de standaarddatabase zonder cleanup.
- P2/proven: `B106-011` — Niet-eindige synonym weights passeren de validator.
- P3/proven: `B106-012` — Week1-validator retourneert succes wanneer alle controles falen.
- P2/proven: `B106-013` — Make validation-status draait een verwijderd testpad en schrijft niet naar de geclaimde locatie.
- P2/proven: `B106-014` — V2-migratieverificatie negeert een ontbrekende of falende smoke-test.

## Resultaat

Geverifieerd door twee verschillende reviewers. Alle 16 toegewezen bereiken, 3976 fysieke regels en 89 symbolen zijn line-by-line beoordeeld; gerichte tests, veilige reproducties en beperkingen staan in het bewijsdossier.
