# DEF-835 — processtatus uitvoering v9

28 september 2026. Branch feature/DEF-835-int02-o2, HEAD 979ca0585100d94b613829d924c6d8bba4f24f1b. Vervangt v8 voor deze voortgang.

## Akkoorden en live proef

Chris heeft het concrete proefprofiel/budget en WP5a geaccordeerd. Manifest v2 is aan het akkoord gebonden. De proef deed drie inferencecalls en drie tokenmetingen; berekende kosten US$0,07814. C105 leverde de verwachte fail; C107 leverde een inhoudelijk afwijkende fail; C112 leverde error/invalid_citation door verkeerde posities. Zie modelproef-live-verslag-v1.md en bijbehorend bewijs. Geen geslaagde modelkwalificatie, geen nieuwe calls binnen dit verbruikte driecallmandaat.

Chris heeft daarnaast uitsluitend de twee exacte bronhashmetadata-combinaties met tests geaccordeerd; zie gitleaks-metadata-akkoord-v1.md. Uitvoering daarvan volgt na de huidige WP5a-review. De vaste Makefile-testselectie krijgt de nieuwe test erbij zodat de regressie blijvend wordt bewaakt; geen bestaande suite verdwijnt.

## WP5a

Claude Code CLI sessie 914fccdd-7899-4d5c-8aa0-1c9ab334d7d4 heeft zeven bestanden gewijzigd. Verslag wp5a-claude-verslag-v1.md, diff bewijs/wp5a-werkboomdiff-v1.patch, SHA256 aeaa6dce27700c0b19eaf771a899e7a1362d176a05fc2f418746307f82a57e48. Productie +181/-1 regels; drie nieuwe testbestanden samen 1182 regels, meer dan de raming. Geen extra softwarebestanden, dependencies, schema of activering.

RED: 44 failed, 5 passed op ongewijzigde productie; dezelfde eindtests opnieuw tegen HEAD-export leveren 44/5. Tussen-RED bewijst caller-pass. GREEN: 49/49 nieuwe tests. Coördinator herhaalde die tests plus Ruff en Black: alle exits 0, hashes exact gelijk aan de finale reviewmanifestbestanden.

Gerichte regressie: 2898 passed, 11 skipped, 1 failed. Volledige unitrun: 8554 passed, 86 skipped, 1 xfailed, 3 failed. Twee performance_tracker-fouten ontstaan door OfflineGateError op data/definities.db en komen ook op HEAD voor; de derde is de bestaande WP2-tekstguard die elke containervermelding van INT-02 verbiedt. Dertien mypy-fouten uit WP1/WP2 zijn ook op HEAD aanwezig. Geen volledige groene-suiteclaim.

De concrete herijking van die bestaande teksttest is aan Chris voorgelegd (achtste bestand buiten het geaccordeerde zevental); antwoord nog niet ontvangen. Geen test verwijderd of gewijzigd om de failure weg te werken.

Verse Codex CLI-review is gestart in /private/tmp/def835-wp2-review-20260927, sessie 01a0e7dd-2c5e-79a0-b228-3e468c198944 (gpt-6-astra/high). Opdracht wp5a-opdracht-codex-review-v2.md. Alleen de bytegelijke zevenbestandsdiff, geen bronwijzigingen; resultaat volgt in wp5a-codex-review-v1.md. Reviewer classificeert ook de open punten rond het NE-pad en configuratiebinding.

## Grenzen

De index is exact intact: 38 staged bewijsbestanden, patchhash 941070627b508626b13b3c4d13b00bf5000966a8f728d0425802ed7b9fd5d214. Geen commit, push, merge, productieactivering of Actions. O1 blijft actief. Goldset/inhoudelijke kwalificatie, DEF-626-opslag, herladen/C118, UI/export en finale activering blijven open.
