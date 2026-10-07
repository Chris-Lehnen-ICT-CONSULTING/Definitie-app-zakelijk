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
