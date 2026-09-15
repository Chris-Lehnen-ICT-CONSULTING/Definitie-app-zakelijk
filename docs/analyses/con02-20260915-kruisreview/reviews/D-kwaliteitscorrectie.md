# DEF-743 — kwaliteitsronde pakket D (complexiteit/mypy + receipt-fixture)

15 september 2026 · Claude Code CLI (implementer D) · branch `feature/DEF-743-con02-bronbasis`, worktree `/Users/chrislehnen/.codex/worktrees/8b34/Definitie-app`. Mutaties gestart ná `/tmp/DEF-743-final-make-test.exit` (inhoud `2`). Uitsluitend D-eigendom: `src/database/definitie_crud.py`, `src/services/definition_repository.py`, `src/export/export_txt.py`, `src/services/export_service.py`, `tests/unit/services/test_def743_bronbewijs_{persistentie,export}.py`. Geen baseline/config/hook/dependency-wijziging, geen `noqa`/`type: ignore`/`cast`-onderdrukking, geen skips, geen symboolhernoeming, niets verwijderd/gecommit/gepusht, geen agents/CLI/MCP/netwerk. **Bevroren na dit rapport.**

## 1. Integratiefout (make test v1: 5789/1) — `TestAssessmentReceiptRoundtrip`

Root-analyse bevestigd: de fixture volgde niet C's §5a-contract (int-`version`, geen `hash_algorithm`, cap 4000 met afgekapte inhoud en per-item-cap). C's guard wees dat terecht af; niets aan C of aan D-projectie gewijzigd.

Fix (alleen testbestand): `_geldige_ontvangst()` bouwt de kwitantie in exact de vorm van C's `SourceAssessmentService` met C's eigen helpers (`canoniseer_bronnen`, `bereken_inhoudshash`): `version "1"`, globale `max_passage_chars` 40, `hash_algorithm "sha256-utf8-hex"`, per bron `source_id`/`original_content_hash` (= canonieke hash)/`content == passage[:40]`/`content_hash`/`truncated == len > 40`/`source_version` (= bronversie). Het citaat ligt binnen het werkelijk verzonden prefix.
- `test_roundtrip_via_opslag_herladen_en_json_export`: exact roundtrip save → nieuwe repository, ID-only reload → JSON-export (metadata, bewijsdocument, `bronnen.bronbewijs`), onafhankelijke kopie, én `source_assessment_status.applicable is True` + `source_authority: pass` via de replay.
- Nieuw `test_ongeldige_kwitantie_blijft_ruw_bewaard_maar_is_niet_toepasbaar`: de oude ongeldige vorm blijft ruw en exact bewaard (historisch) maar is niet toepasbaar met reden; geen onderdeel wordt pass.
- Log: `/tmp/DEF-743-quality-D-receipt.log` — 2 passed, exit 0.

## 2. Complexiteit (pinned ruff 0.16.5, regels C901/PLR0911/PLR0912/PLR0915, projectconfig)

Werkwijze: HEAD-versies van de vier D-bestanden apart gemeten (`git show HEAD:…`, `/tmp/def743-head/`), zodat alleen echte groei is aangepakt. Mechanische helper-extractie; volgorde, fail-closed-gedrag en transactiegrenzen ongewijzigd.

| Functie | vóór (prequality) | HEAD | ná | Extractie |
|---|---|---|---|---|
| `definitie_crud._meegroeiende_bronbeoordeling` | PLR0911 7 | — | 0 | module-helper `_geparste_issuelijst` |
| `definitie_crud.set_source_review` | C901 11 | — | 0 | `_geldige_bronreviewinvoer` (payloadcontrole vóór mutatie), `_gebonden_bronreview` (ónder de lock: vingerafdruk → None/False, kernvalidatie → ValueError, opslagversie) |
| `definitie_crud._technische_validatiefout` | C901 13, PLR0911 7 | — | 0 | module-helpers `_technische_resultaatfout` (status/readiness/dekking) + `_technische_regelfout` (regelstatus/-resultaat); SAM-`not_evaluated`-lezing ongewijzigd |
| `definitie_crud.apply_source_proposal` | C901 15, PLR0911 14, PLR0912 14 | — | 0 | `_beoordeling_voor_toepassing` (vóór transactie), `_vind_toepasbaar_voorstel` + `_controleer_origineel_en_binding` (ónder de lock, zelfde volgorde/redenen), `_registratie_na_toepassing` (bewijs/voorstel/issues), `_Toepassingsinvoer` (frozen dataclass); één UPDATE onder dezelfde versieguard |
| `definitie_crud.update_definitie` | C901 13 | ≤10 | 0 | `_verwerk_bewijsinvoer` (bewijssamenvoeging ónder de lock, "niets te schrijven" ⇒ False), `_behoud_bronbinding` (CON-02-behoudregel) |
| `definition_repository._definition_to_updates` | C901 11 | ≤10 | 0 | module-helper `_voeg_bewijsinvoer_toe` |
| `definition_repository._definition_to_record` | C901 16, PLR0912 15 | C901 14, PLR0912 13 | C901 12 | `_promptregistratie` (DEF-151-blok, zelfde warning-gedrag) + `_generatieregistratie_voor_record` (bewijs; serialisatiefout blijft ValueError → RepositoryError) — onder HEAD, PLR0912 weg |
| `definition_repository.save` | 19/17/54 | 19/17/54 | 19/17/54 | ongewijzigd (pre-existing, niet aangeraakt) |
| `export_service._build_export_row` | C901 13, PLR0912 13 | C901 12 | 0 | `_exportwaarde_voor_veld` (identieke per-veld-afhandeling) |
| `export_txt.bronbewijs_regels` | C901 55, PLR0912 55, PLR0915 137 | — | 0 | sectiehelpers in vaste volgorde: `_statusregels`, `_bronregel`/`_bronregels`, `_replay_deelregels`/`_replay_reviewregels`/`_replayregels`, `_beoordeling_deelregels`/`_beoordelingsregels`, `_reviewdetailregels`/`_reviewregels`, `_reviewhistorieregels`, `_bewijshistorie_en_voorstelregels` |
| `export_txt.exporteer_naar_txt` | PLR0915 63 | PLR0915 60 | PLR0915 58 | `_bronsecties` (secties "Gebruikte bronnen" + "Bronbeoordeling (CON-02)", zelfde tekst) — onder HEAD |

D-scope totaal: prequality 20 bevindingen → ná 5, HEAD 7 (alle 5 resterende zijn pre-existing functies zonder netto groei; twee HEAD-bevindingen verdwenen). Logs: `/tmp/DEF-743-quality-D-lint.log` (complexiteit ná + HEAD-baseline), `/tmp/DEF-743-quality-D-prequality-complexity.log` (vóór).

**Uitvoergelijkheid TXT** (`/tmp/DEF-743-quality-D-txt-equivalence.log`, exit 0): oude module (`/tmp/def743_export_txt_before.py`) vs nieuwe, `bronbewijs_regels` én volledige `exporteer_naar_txt`-uitvoer byte-identiek voor uitzondering+reviewhistorie, geldige kwitantie, ongeldige kwitantie, stale, reference-only en 4 synthetische randgevallen (None/{}/invalid/gemengd).

## 3. mypy (pinned 2.3.1)

`/tmp/DEF-743-mypy-pinned.log`: 0 van de 66 fouten in D-scope (E/F/C-bestanden). Ná refactor: `Success: no issues found in 4 source files` (nieuwe helpers volledig geannoteerd; narrowing via `isinstance(…, Voorsteltoepassing)`/`_Toepassingsinvoer`, geen `cast`/`Any`-onderdrukking).

## 4. Bewijs (exacte exitcodes)

| Bewijs | Uitkomst | Log |
|---|---|---|
| Receipt-fixture (2 tests) | 2 passed, exit 0 | `/tmp/DEF-743-quality-D-receipt.log` |
| Gerichte suites: D-persistentie (109) + D-export (15) + F-workflow op D-primitieven (41) + buren (aggregation, export×5, definition_repository×2, database/*, DEF-622 readback/export/koppelingen/vaststelconflict, workflow-atomiciteit/status/workflow_service) | **790 passed, 1 skipped (bestaand)**, exit 0 | `/tmp/DEF-743-quality-D-tests.log` |
| Pinned complexiteit D-bestanden (+ HEAD-baseline), ruff normaal (0), mypy (0), black (0) | zie §2/§3 | `/tmp/DEF-743-quality-D-lint.log` |
| TXT-equivalentie oud/nieuw | FOUTEN: 0, exit 0 | `/tmp/DEF-743-quality-D-txt-equivalence.log` |
| SHA256-manifest D-bestanden ná | | `/tmp/DEF-743-quality-D-hashes.log` |

```text
8be7e091c5105980f0aabef6aa9011ab2f730ef726d434736850a7adc18fe1c3  src/database/definitie_crud.py
41e8611eda3b830ee9b7e9269c1e94ff71b32e688465e2672983861623f8174a  src/services/definition_repository.py
ed44a8dd446c1994a30559425ebea1d80cfb82274888b1c4da2a0dc6767e6658  src/export/export_txt.py
37f228433b6a36734d9bc9da394f845323d506a3a073864ab3a878a4cf14d0db  src/services/export_service.py
84041331985c3e7193d9d9b823c4ae87b7d6baac33ad17986d1e07ab592ba994  tests/unit/services/test_def743_bronbewijs_persistentie.py
87b5d1470ae635d3140bc5b14c781490f104b9ac70bf05b4af2b7fcf0ef187ff  tests/unit/services/test_def743_bronbewijs_export.py
```

## 5. Grenzen

Geen brede unit-run (root-instructie); `PerformanceTracker`/tracker-tests niet aangeraakt. Geen productgedrag gewijzigd: contracten (bronbewijs, kwitanties/vingerafdrukken/citaten/metadata, reviews/uitzonderingen/historie, één poging, expliciet toepassen, atomaire transacties/versieguard) blijven exact; alle eerder gesloten D-reviewfixes staan. Geen expertgoldset-/feature-gereed-claim.
