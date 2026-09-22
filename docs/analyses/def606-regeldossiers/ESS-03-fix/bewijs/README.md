# DEF-766 — ESS-03: bewijsarchief

Duurzame kopie van het bewijs dat tijdens DEF-766 is verzameld in de git-ignored map `reports/` van de uitvoeringswerkboom (`~/.codex/worktrees/2075/Definitie-app`). Vastgelegd op 22 september 2026 (punt K6 uit PR #467), zodat het bewijs de opruiming van die werkboom overleeft. De bestanden zijn verbatim kopieën; er is niets inhoudelijk aan gewijzigd of aangevuld.

## Mappen

| Map | Oorsprong | Wat erin staat |
| -- | -- | -- |
| `2026-09-18-uitvoering/` | `reports/DEF-766-20260918/` | Eerste ESS-03-fix (regelkaart, scoreloos, menselijke beoordeling): implementatiebrief en -rapport, onafhankelijke app- en skillreviews, contract-gap-analyse, proef na fix, diff- en skillpatches, RED/GREEN- en lintlogs. Het verslag daarvan staat in `../2026-09-18-uitvoering-v1.md`. |
| `2026-09-18-publicatie/` | `reports/DEF-766-20260918-publicatie/` | Publicatie van die fix (PR #465 en skill-PR #334): modelproef met vier gevallen, publicatieverslag, PR-teksten, commit-/mergeverificatie, zipverificatie en inventaris van de skillinstallatie. |
| `2026-09-21-ai-beoordeling/` | `reports/DEF-766-AI-20260921/` | ESS-03 als AI-beoordeling in de app (PR #467, `main` `45439aa58`). `uitvoerder/`: implementatie- en correctiebriefs v1–v4, rapporten, manifesten en exitcodes, ontwikkelruns, rookproef Opus 5, browsercontroles v1–v3 met opgeslagen records, en `heldout/` (verzegelde onafhankelijke eindset, gevallenbestanden, runs, resultaten en rapport). `onafhankelijk/`: reviewcriteria, briefs en de onafhankelijke reviews (fase 1, ontwikkel-v2, delta v1, v3, eindtest, v4), plus het zegel van de eindset. |

Belangrijkste documenten om mee te beginnen: `2026-09-21-ai-beoordeling/uitvoerder/heldout/heldout-report-v1.md` (inhoudelijke eindtest: 19/20 zoals vooraf vastgelegd, 0 onterechte goedkeuringen, 113/113 citaten letterlijk), `2026-09-21-ai-beoordeling/onafhankelijk/review-heldout-v1.md` en `review-v4.md` (onafhankelijke reviews), `2026-09-21-ai-beoordeling/uitvoerder/browser-verification-v3.md` (gebruikerspad op Opus 5) en `2026-09-21-ai-beoordeling/uitvoerder/correction-report-v3.md` (thinking-guard en afkapping).

De eindset `heldout-cases-v1.md` heeft sha256 `f96378d2cc5ffefe8f9db67f9d52e8a1f177747377b66726e077761d0f1f523e`, gelijk aan het zegel in `onafhankelijk/heldout-seal-v1.json`. Het is een beperkte synthetische set, geen deskundigen-goldset; er wordt geen statistische claim gedaan.

## Wat niet is opgenomen, en waarom

`MANIFEST-sha256.tsv` bevat voor **elk** bestand uit de drie oorspronkelijke mappen het oorspronkelijke pad, de grootte, de sha256 en of het is opgenomen. Niet opgenomen zijn:

- ruwe CLI-sessielogs (`*.jsonl`) en `*.stderr`: groot en alleen machineleesbaar; de rapporten en eindantwoorden die eruit volgen staan wel in dit archief;
- `2026-09-21-ai-beoordeling/uitvoerder/base-src/`: momentopname van de broncode vóór de wijziging, reproduceerbaar uit git;
- bestanden groter dan 250 kB (volledige `make test`- en CI-logs);
- `browser-v2-input-and-source-seal.json`: de secrets-scan (gitleaks, regel `generic-api-key`) ziet een bestandshash naast de naam `anthropic_client.py` voor een sleutel. Het bestand bevat geen geheim; het is buiten het archief gehouden om de scanregels niet te hoeven verruimen. De hash staat in het manifest.

De niet-opgenomen bestanden blijven bestaan in de werkboom zolang die niet is opgeruimd; hun sha256 in het manifest maakt een later teruggevonden kopie controleerbaar.

## Eén aanpassing in de bestandsnaam

Pythonbestanden (`*.py`) zijn opgeslagen als `*.py.txt`. Anders zouden ruff en black in de pre-commit ze herformatteren en zou de kopie niet meer byte-gelijk zijn aan het origineel. De inhoud is ongewijzigd; de sha256 in het manifest is die van het origineel en van de kopie.

## Controleren

Vanuit deze map: voor elke regel met status `opgenomen` moet `shasum -a 256 <doel>` gelijk zijn aan de kolom `sha256`.

Absolute paden in de bestanden (`/Users/chrislehnen/...`, `/tmp/def766-...`) verwijzen naar de oorspronkelijke werkomgeving en zijn historisch. Alle gegevens zijn synthetisch; er staan geen API-sleutels in (alleen de dummywaarden die de testgates gebruiken).
