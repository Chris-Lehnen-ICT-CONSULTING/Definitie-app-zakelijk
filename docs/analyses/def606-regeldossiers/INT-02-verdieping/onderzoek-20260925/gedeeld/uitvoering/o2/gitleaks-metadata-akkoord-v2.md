# DEF-835 — akkoord exacte metadata-uitzonderingen na gitleaks-blokkade (v2)

7 oktober 2026. Vastgelegd door Claude Code na het besluit van Chris (eigenaar uitzonderingen volgens `docs/technisch/def522-secret-scan-runbook.md`). Vervangt `gitleaks-metadata-akkoord-v1.md` niet; v1 blijft gelden voor uitzondering 3.

## Aanleiding

De staged commit uit besluit 4 van `besluit-chris-promptcorrectie-en-v3-v1.md` (459 bestanden) werd door de gitleaks-hook (`scripts/ci/secret_scan_precommit.py`, gepinde Gitleaks 8.29.1) geblokkeerd met 26 bevindingen. Alle 26 zijn false positives:

- 12× `generic-api-key` op een SHA-256 van een repo-bestand in een hash- of manifestregel;
- 2× `generic-api-key` op een JSONL-commandologregel waarin een bestandsnaam na het woord secret als sleutel wordt gelezen;
- 12× `openai-api-key-new-format` op de nep-fixture uit `tests/unit/utils/test_pii_redaction_api_keys.py`, overgenomen in vier gate-uitvoerbestanden van de mergevoorbereiding.

## Besluit Chris

**Optie A**, gekozen in Cowork op 07-10-2026:

1. Exacte uitzonderingen volgens het runbook voor de 12 hashregels en de 2 streamregels: per bestand een eigen `[[allowlists]]`-blok met `condition = "AND"`, exact pad (verankerde regex) én de exacte, volledige regelinhoud (`regexTarget = "line"`, verankerd, ge-escaped), `targetRules` beperkt tot `generic-api-key`. Geen map-, prefix- of wildcardregel, geen globale allowlist, geen scopewijziging. Vorm gelijk aan uitzondering 3 in `.gitleaks.toml`.
2. De 4 gate-uitvoerbestanden worden niet gecommit: unstaged, lokaal bewaard.

## Uitzonderingen in `.gitleaks.toml` (4 tot en met 13)

Paden relatief aan `o2/` = `docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2/`. Regel-ID steeds `generic-api-key`. De hashwaarden staan alleen in de config (eerste hexteken als tekenklasse), niet in dit document. "Gelijk bevonden" betekent: SHA-256 van het genoemde bestand op 07-10-2026 nagerekend en identiek aan de waarde in de regel.

| Nr | Pad | Regel | Waarom false positive |
|---|---|---|---|
| 4 | `bewijs/gitleaks-coordinator-v1.json` | r5 | SHA-256 van `docs/technisch/def522-secret-scan-runbook.md` (gelijk bevonden); de bronnaam bevat `secret` |
| 5 | `bewijs/gitleaks-correctie-coordinator-v1.json` | r5 | SHA-256 van `docs/technisch/def522-secret-scan-runbook.md` (gelijk bevonden) |
| 5 | `bewijs/gitleaks-correctie-coordinator-v1.json` | r7 | SHA-256 van `scripts/ci/test_secret_scan_metadata.py` (gelijk bevonden); de bronnaam bevat `secret` |
| 6 | `bewijs/gitleaks-commit-index-v1.json` | r51 | SHA-256 van `docs/technisch/def522-secret-scan-runbook.md` (gelijk bevonden) |
| 6 | `bewijs/gitleaks-commit-index-v1.json` | r53 | SHA-256 van `scripts/ci/test_secret_scan_metadata.py` (gelijk bevonden) |
| 7 | `bewijs/gitleaks-reviewmanifest-v1.json` | r6 | SHA-256 van `docs/technisch/def522-secret-scan-runbook.md` (gelijk bevonden) |
| 8 | `bewijs/gitleaks-reviewmanifest-v2.json` | r6 | SHA-256 van `docs/technisch/def522-secret-scan-runbook.md` (gelijk bevonden) |
| 8 | `bewijs/gitleaks-reviewmanifest-v2.json` | r8 | SHA-256 van `scripts/ci/test_secret_scan_metadata.py` (gelijk bevonden) |
| 9 | `goldset-voorbereiding/goldset-freeze-v1/kwalificatie-manifest-v1.json` | r110 | SHA-256 van de huidige `src/utils/async_api.py` (gelijk bevonden); de bronnaam bevat `api` |
| 10 | `goldset-voorbereiding/goldset-freeze-v1/kwalificatie-manifest-v2.json` | r110 | idem |
| 11 | `goldset-voorbereiding/goldset-freeze-v1/kwalificatie-manifest-v3.json` | r110 | idem |
| 12 | `gitleaks-metadata-uitzondering-voorstel-v1.md` | r17 | SHA-256 van `src/utils/async_api.py` in commit `45439aa58d50` (gelijk bevonden); dezelfde regel als uitzondering 3, hier geciteerd in het voorstel van 28-09 |
| 13 | `bewijs/gitleaks-codex-stream-v1.jsonl` | r25 | JSONL-commandolog (Codex, item_13, gestart): `generic-api-key` leest de bestandsnaam `gitleaks-mutatieproef-v3.py`, die volgt op de bestandsnaam `gitleaks-make-test-secret-scan-v3.log`, als sleutelwaarde |
| 13 | `bewijs/gitleaks-codex-stream-v1.jsonl` | r26 | idem (zelfde commando, afgerond; de uitvoer bevat SHA-256-waarden van repo-bestanden) |

Elke uitzondering verwijst in haar `description` naar DEF-835, dit besluit (07-10-2026, eigenaar Chris Lehnen) en dit bestand. Herbeoordelen op 2027-01-07, of eerder als een regel of pad wijzigt.

## Bewust niet gecommit

De volgende 4 gate-uitvoerbestanden zijn met `git restore --staged` uit de index gehaald en staan ongetrackt lokaal in de werkboom. Ze bevatten de nep-fixture uit `tests/unit/utils/test_pii_redaction_api_keys.py` (12 bevindingen `openai-api-key-new-format`):

- `o2/bewijs/mergevoorbereiding-v1/gates/unit-inventaris.json`
- `o2/bewijs/mergevoorbereiding-v1/gates/unit-junit.xml`
- `o2/bewijs/mergevoorbereiding-v1/samengevoegde-gates/unit-inventaris.json`
- `o2/bewijs/mergevoorbereiding-v1/samengevoegde-gates/unit-junit.xml`

Back-up van de stand vóór de wijziging: `backups/def835-backup-20261007/` in de werkboom (git-ignored via `backups/`). Daarin `gitleaks.toml.voor-wijziging` en `o2-en-code.zip` (hele o2-map, inclusief de 4 bestanden hierboven, plus `src/services/validation/int02_assessment_service.py` en `tests/unit/services/prompts/test_def835_int02_prompt.py`; 889 bestanden). De gevraagde map `Claude outputs/def835-backup-20261007` buiten de werkboom kon in deze sessie niet worden beschreven (geen schrijfrecht buiten de werkboom).

## Uitkomst

Er zijn geen echte credentials gevonden. Er is niets ingetrokken, geroteerd of vervangen. De normale staged-gate blijft verplicht en wordt niet omzeild.

## Regressiebewijs (07-10-2026)

Uitgevoerd door een Claude Code CLI-job in deze werkboom vóór de commit; hulpbestanden staan buiten git in `backups/def835-werk/` (git-ignored), de volledige configdiff in `backups/def835-backup-20261007/gitleaks-diff-20261007.patch`.

- **Bestaande secret-scan-tests:** `pytest -o addopts= --import-mode=importlib -q scripts/ci` met de gepinde gitleaks 8.29.1 van pre-commit: 250 geslaagd, 489 subtests geslaagd.
- **Staged gate zoals de hook:** `pre-commit run gitleaks`: Passed; `{"code": "ok", "finding_count": 0, "status": "clean"}`.
- **Mutatieproef** in tijdelijke fixture-repo's met kopieën van de echte bestanden in de index en de staged gate:

| Scenario | Uitkomst |
|---|---|
| A: exacte bestanden op het exacte pad | clean, 0 bevindingen |
| B: per uitgezonderde regel één teken anders (13× één hexteken; stream-r25 `item_13` → `item_14`) | blocked, 14 (elke regel apart gemeld) |
| C: zelfde inhoud, pad + `.kopie` | blocked, 14 |
| D: zelfde inhoud onder map `kopie/` | blocked, 14 |

- **Onafhankelijke review:** verse Codex CLI-sessie (read-only, 07-10): geen blokkerende bevindingen; alle tien blokken exact verankerd, `condition = "AND"`, alleen `generic-api-key`; 127 negatieve regexproeven geweigerd; alle 12 SHA-256-waarden nagerekend met `shasum -a 256` (de historische tegen commit `45439aa58d50`); streamregels 25/26 zonder credentialvorm; geen andere credentialvormen in de staged bestanden buiten bekende synthetische testfixtures. Belangrijk (niet blokkerend): uitzondering 4–13 hebben geen vaste canary-tests.

Opmerking: de hashes van `docs/technisch/def522-secret-scan-runbook.md` in uitzondering 4–8 zijn historische metadata uit de bewijsbestanden. Ze waren gelijk aan het runbook vóór de bijwerking van 07-10-2026; door die bijwerking (dertien uitzonderingen) wijkt de huidige runbookhash af. De uitzonderingen blijven geldig omdat ze op de vastgelegde metadataregel matchen, niet op het runbook.

## Aanvulling: uitzondering 14 (besluit 8, 07-10-2026)

Bij het stagen van manifest v4 (`besluit-chris-promptcorrectie-en-v3-v1.md`, besluit 8) meldde de gitleaks-hook 1 bevinding. Het is dezelfde soort als uitzondering 9–11: r110 van het nieuwe manifest is byte-gelijk aan r110 van manifest v3.

| Nr | Pad | Regel | Waarom false positive |
|---|---|---|---|
| 14 | `goldset-voorbereiding/goldset-freeze-v1/kwalificatie-manifest-v4.json` | r110 | SHA-256 van de huidige `src/utils/async_api.py` (gelijk bevonden, werkboom en HEAD); de bronnaam bevat `api` |

Zelfde constructie als 9–11: exact pad én exacte volledige regel, `condition = "AND"`, alleen `generic-api-key`. Eigenaar Chris Lehnen, herbeoordelen op 2027-01-07. `kwalificatie-payloads-v4.json` en `kwalificatie-akkoord-v4.json` gaven geen bevindingen. De kopteksten in `.gitleaks.toml` zijn van "van 13" naar "van 14" gezet; de blokken 1–13 zelf zijn ongewijzigd. De regex van 14 is gelijk aan die van 9–11; voor 14 is geen eigen mutatieproef gedraaid.

## Aanvulling: uitzondering 15 (besluit 10, 07-10-2026)

Bij het stagen van manifest v5 (`besluit-chris-promptcorrectie-en-v3-v1.md`, besluit 10) meldde de gitleaks-hook 1 bevinding. Het is dezelfde soort als uitzondering 9–11 en 14: r110 van manifest v5 is byte-gelijk aan r110 van manifest v4.

| Nr | Pad | Regel | Waarom false positive |
|---|---|---|---|
| 15 | `goldset-voorbereiding/goldset-freeze-v1/kwalificatie-manifest-v5.json` | r110 | SHA-256 van de huidige `src/utils/async_api.py` (gelijk bevonden, werkboom en HEAD `f83959eb0`); de bronnaam bevat `api` |

Zelfde constructie als 14: exact pad én exacte volledige regel, `condition = "AND"`, alleen `generic-api-key`. Eigenaar Chris Lehnen, herbeoordelen op 2027-01-07. De hookuitvoer geeft alleen het aantal; dat de bevinding precies r110 was, blijkt uit de herhaalde hookrun: met alleen dit exacte blok erbij daalde de telling van 1 naar 0. `kwalificatie-payloads-v5.json`, `kwalificatie-akkoord-v5.json` en de bijgewerkte besluitnotitie gaven dus geen bevindingen. De kopteksten in `.gitleaks.toml` zijn van "van 14" naar "van 15" gezet; de blokken 1–14 zelf zijn ongewijzigd. De regex van 15 is gelijk aan die van 9–11 en 14; voor 15 is geen eigen mutatieproef gedraaid.

## Aanvulling: uitzondering 16 (besluit 13, 07-10-2026)

Bij het stagen van manifest v6 (`besluit-chris-promptcorrectie-en-v3-v1.md`, besluit 13) meldde de gitleaks-hook 1 bevinding. Het is dezelfde soort als uitzondering 9–11, 14 en 15: r110 van manifest v6 is byte-gelijk aan r110 van manifest v5.

| Nr | Pad | Regel | Waarom false positive |
|---|---|---|---|
| 16 | `goldset-voorbereiding/goldset-freeze-v1/kwalificatie-manifest-v6.json` | r110 | SHA-256 van de huidige `src/utils/async_api.py` (gelijk bevonden, werkboom en HEAD `8c6bf74d2`); de bronnaam bevat `api` |

Zelfde constructie als 15: exact pad én exacte volledige regel, `condition = "AND"`, alleen `generic-api-key`. Eigenaar Chris Lehnen, herbeoordelen op 2027-01-07. De hookuitvoer geeft alleen het aantal; dat de bevinding precies r110 was, blijkt uit de herhaalde hookrun: met alleen dit exacte blok erbij daalde de telling van 1 naar 0. `kwalificatie-payloads-v6.json`, `kwalificatie-akkoord-v6.json` en de bijgewerkte besluitnotitie gaven dus geen bevindingen. De kopteksten in `.gitleaks.toml` zijn van "van 15" naar "van 16" gezet; de blokken 1–15 zelf zijn ongewijzigd. De regex van 16 is gelijk aan die van 9–11, 14 en 15; voor 16 is geen eigen mutatieproef gedraaid.

## Aanvulling: uitzondering 17 (besluit 15, 07-10-2026)

Bij het stagen van manifest v7 (`besluit-chris-promptcorrectie-en-v3-v1.md`, besluit 15) meldde de gitleaks-hook 1 bevinding. Het is dezelfde soort als uitzondering 9–11 en 14–16: r112 van manifest v7 is byte-gelijk aan r110 van manifest v6. De regel schoof twee posities op doordat de router in v7 twee velden meer heeft (`supports_structured_outputs`, `antwoordschema_sha256`).

| Nr | Pad | Regel | Waarom false positive |
|---|---|---|---|
| 17 | `goldset-voorbereiding/goldset-freeze-v1/kwalificatie-manifest-v7.json` | r112 | SHA-256 van de huidige `src/utils/async_api.py` (gelijk bevonden, werkboom en HEAD `2081899ea`); de bronnaam bevat `api` |

Zelfde constructie als 16: exact pad én exacte volledige regel, `condition = "AND"`, alleen `generic-api-key`. Eigenaar Chris Lehnen, herbeoordelen op 2027-01-07. De hookuitvoer geeft alleen het aantal; dat de bevinding precies r112 was, blijkt uit de herhaalde hookrun: met alleen dit exacte blok erbij daalde de telling van 1 naar 0. `kwalificatie-payloads-v7.json`, `kwalificatie-akkoord-v7.json`, de bijgewerkte besluitnotitie, `kwalificatieproef-v6-uitslag-v1.md` en de bestanden in `kwalificatieproef-v6/` gaven dus geen bevindingen. De kopteksten in `.gitleaks.toml` zijn van "van 16" naar "van 17" gezet; de blokken 1–16 zelf zijn ongewijzigd. De regex van 17 is gelijk aan die van 9–11 en 14–16; voor 17 is geen eigen mutatieproef gedraaid.

## Aanvulling: uitzondering 18 (besluit 18, 08-10-2026)

Bij het stagen van manifest v8 (`besluit-chris-promptcorrectie-en-v3-v1.md`, besluit 18) meldde de gitleaks-hook 1 bevinding. Het is dezelfde soort als uitzondering 9–11 en 14–17: r113 van manifest v8 is byte-gelijk aan r112 van manifest v7. De regel schoof één positie op doordat de identiteit in v8 het veld `contractversie` heeft.

| Nr | Pad | Regel | Waarom false positive |
|---|---|---|---|
| 18 | `goldset-voorbereiding/goldset-freeze-v1/kwalificatie-manifest-v8.json` | r113 | SHA-256 van de huidige `src/utils/async_api.py` (ongewijzigd sinds v4); de bronnaam bevat `api` |

Zelfde constructie als 17: exact pad én exacte volledige regel, `condition = "AND"`, alleen `generic-api-key`. Eigenaar Chris Lehnen, herbeoordelen op 2027-01-07. De kopteksten in `.gitleaks.toml` zijn van "van 17" naar "van 18" gezet; de blokken 1–17 zelf zijn ongewijzigd. De regex van 18 is gelijk aan die van 9–11 en 14–17; voor 18 is geen eigen mutatieproef gedraaid. Kopie van de oude staat: `backups/def835-werk/gitleaks.toml.voor-uitzondering-18` (niet in git).

## Aanvulling: uitzondering 19 (besluit 20, 08-10-2026)

Bij het stagen van manifest v9 (`besluit-chris-promptcorrectie-en-v3-v1.md`, besluit 20) meldde de gitleaks-hook 1 bevinding, dezelfde soort als 18: r113 van manifest v9 is byte-gelijk aan r113 van manifest v8 (SHA-256 van `src/utils/async_api.py`, ongewijzigd; de bronnaam bevat `api`).

| Nr | Pad | Regel | Waarom false positive |
|---|---|---|---|
| 19 | `goldset-voorbereiding/goldset-freeze-v1/kwalificatie-manifest-v9.json` | r113 | SHA-256 van de huidige `src/utils/async_api.py`; geen sleutel |

Blok 19 is mechanisch afgeleid van blok 18 (alleen nummer, besluit en `v8` → `v9` in pad en beschrijving). Eigenaar Chris Lehnen, herbeoordelen op 2027-01-07. Kopteksten "van 18" → "van 19"; blokken 1–18 ongewijzigd. Kopie van de oude staat: `backups/def835-werk/gitleaks.toml.voor-uitzondering-19` (niet in git).
