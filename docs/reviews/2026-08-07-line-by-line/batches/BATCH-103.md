# BATCH-103

- Status: `verified`
- Reviewgroep: `15` — Operationele scripts en shellcode
- Review-base: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Membership-SHA256: `d91d964c2595ca7abbad0af0b65c980e4c27fb1472a9d8d9befcfa7e7d92bf85`
- Bestanden: `19`
- Fysieke regels: `3979`
- Python-symbolen: `102`
- Reviewer: `codex-kierkegaard`
- Onafhankelijke verifier: `codex-root`

## Scope

| Pad | path_b64 | Regelbereik | Symbolen | Object-ID |
|---|---|---:|---:|---|
| `scripts/maintenance/remove_history_tab.py` | `c2NyaXB0cy9tYWludGVuYW5jZS9yZW1vdmVfaGlzdG9yeV90YWIucHk=` | `1-357` | 13 | `952dbde324257c4fb3254676d11769f1d3965fd5` |
| `scripts/maintenance/remove_history_tab.sh` | `c2NyaXB0cy9tYWludGVuYW5jZS9yZW1vdmVfaGlzdG9yeV90YWIuc2g=` | `1-248` | 0 | `2e6c4da63f14d9e74680c34daa6aa75a15984e84` |
| `scripts/maintenance/remove_legacy_methods.py` | `c2NyaXB0cy9tYWludGVuYW5jZS9yZW1vdmVfbGVnYWN5X21ldGhvZHMucHk=` | `1-98` | 3 | `183a7f36eb480c1449aec58f1f1d94fc199e36c4` |
| `scripts/maintenance/security_review.py` | `c2NyaXB0cy9tYWludGVuYW5jZS9zZWN1cml0eV9yZXZpZXcucHk=` | `1-76` | 2 | `c995326a4ca5b1a15a192d0135d59b616dd3aaa0` |
| `scripts/maintenance/verify_history_removal.py` | `c2NyaXB0cy9tYWludGVuYW5jZS92ZXJpZnlfaGlzdG9yeV9yZW1vdmFsLnB5` | `1-230` | 12 | `7bdc3dddfce3e084e5f560ca7bdf0f1178b9e5c7` |
| `scripts/maintenance/web_lookup_debug.py` | `c2NyaXB0cy9tYWludGVuYW5jZS93ZWJfbG9va3VwX2RlYnVnLnB5` | `1-148` | 2 | `46e4299683a0b11e72d70aef5283ce78d9aca3d6` |
| `scripts/measure_lazy_loading_impact.py` | `c2NyaXB0cy9tZWFzdXJlX2xhenlfbG9hZGluZ19pbXBhY3QucHk=` | `1-211` | 7 | `20842c62969d8393ceb7fc2f320619cb3666c537` |
| `scripts/measure_sru_circuit_breaker_performance.py` | `c2NyaXB0cy9tZWFzdXJlX3NydV9jaXJjdWl0X2JyZWFrZXJfcGVyZm9ybWFuY2UucHk=` | `1-176` | 3 | `bb1036c5d89d993a79ac132bf7d27ee552391afa` |
| `scripts/measure_startup_performance.py` | `c2NyaXB0cy9tZWFzdXJlX3N0YXJ0dXBfcGVyZm9ybWFuY2UucHk=` | `1-228` | 6 | `641116ad7e143107955cbf0f9b16460242a45157` |
| `scripts/migrate_data.py` | `c2NyaXB0cy9taWdyYXRlX2RhdGEucHk=` | `1-619` | 12 | `d5d9deaa86f679f871005e509f8b08e430b09539` |
| `scripts/migrate_synonym_tables.py` | `c2NyaXB0cy9taWdyYXRlX3N5bm9ueW1fdGFibGVzLnB5` | `1-162` | 2 | `815519cca2fa2e7568a5adde3ddaac3a983af221` |
| `scripts/migrate_synonyms_to_registry.py` | `c2NyaXB0cy9taWdyYXRlX3N5bm9ueW1zX3RvX3JlZ2lzdHJ5LnB5` | `1-914` | 18 | `e44834ac45186d373cb61bb53192168462cf57d9` |
| `scripts/monitoring/monitor_app.sh` | `c2NyaXB0cy9tb25pdG9yaW5nL21vbml0b3JfYXBwLnNo` | `1-19` | 0 | `fffb992ceff2a705add447051a73100f6afb721b` |
| `scripts/monitoring/websocket_monitor.py` | `c2NyaXB0cy9tb25pdG9yaW5nL3dlYnNvY2tldF9tb25pdG9yLnB5` | `1-160` | 9 | `0b3db0a522d557bad30adde5983f0ae28536eb9d` |
| `scripts/mypy_baseline.txt` | `c2NyaXB0cy9teXB5X2Jhc2VsaW5lLnR4dA==` | `1-1` | 0 | `573541ac9702dd3969c9bc859d2b91ec1f7e6e56` |
| `scripts/mypy_overrides_baseline.txt` | `c2NyaXB0cy9teXB5X292ZXJyaWRlc19iYXNlbGluZS50eHQ=` | `1-1` | 0 | `0cfbf08886fca9a91cb753ec8734c84fcbe52c9f` |
| `scripts/mypy_overrides_ratchet.py` | `c2NyaXB0cy9teXB5X292ZXJyaWRlc19yYXRjaGV0LnB5` | `1-122` | 5 | `83f60b5f74f1cf82b5dcaaad0c2a474b1a9bb02f` |
| `scripts/mypy_ratchet.py` | `c2NyaXB0cy9teXB5X3JhdGNoZXQucHk=` | `1-138` | 5 | `be569a61875c37c98db504add6960dc39b9392b1` |
| `scripts/perf/check_query_plans.py` | `c2NyaXB0cy9wZXJmL2NoZWNrX3F1ZXJ5X3BsYW5zLnB5` | `1-71` | 3 | `131a86e359e9db2d0f3882c7bdee0de92385620b` |

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

- P2/proven: `B103-001` — Default migration can self-migrate and report a successful no-op.
- P3/proven: `B103-002` — Migration CLI opens its log before creating logs/.
- P1/proven: `B103-003` — Synonym migration rollback deletes unrelated human data and leaves migrated data behind.
- P2/proven: `B103-004` — Presence of one synonym table skips the entire table migration.
- P2/proven: `B103-005` — History-tab maintenance scripts target the original checkout.
- P3/proven: `B103-006` — Monitoring cleanup trap is installed after blocking tail.

## Resultaat

Geverifieerd door twee verschillende reviewers. Alle 19 bestanden, 3979 fysieke regels en 102 symbolen zijn line-by-line beoordeeld; gerichte tests, veilige reproducties en beperkingen staan in het bewijsdossier.
