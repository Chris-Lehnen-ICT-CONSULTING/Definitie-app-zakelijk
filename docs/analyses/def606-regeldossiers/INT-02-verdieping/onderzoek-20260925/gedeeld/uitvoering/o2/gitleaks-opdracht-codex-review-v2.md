# DEF-835 — onafhankelijke review exacte scanneruitzondering

Jij bent de Codex CLI-reviewer. Voer deze opdracht zelf uit; start geen agents, reviewers of extra CLI-sessies. Review alleen deze concrete correctie, wijzig geen bronbestanden of tests. Nederlands verslag. Geen echte modelcalls, credentials, productiedata, staging/commit/push/merge of Actions.

Werkroot /private/tmp/def835-wp2-review-20260927, basis 979ca0585100d94b613829d924c6d8bba4f24f1b. De eerder afzonderlijk beoordeelde WP5a-diff staat mogelijk ook in de werkroot; deze hoort NIET bij jouw nieuwe review. De te beoordelen vier bestanden en SHA256/patchidentiteit staan in bewijs/gitleaks-reviewmanifest-v1.json, controleer die eerst.

Origineel dossier:
/Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-835-int02-o2/docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2

Lees gitleaks-metadata-uitzondering-voorstel-v1.md, gitleaks-metadata-akkoord-v1.md, gitleaks-opdracht-claude-v3.md en gitleaks-claude-verslag-v1.md. Chris autoriseerde uitsluitend de exacte twee manifestpaden EN volledige bronhashregel, met regressietests. DEF-522-runbook en bestaande exceptionconstructie blijven leidend. Scope .gitleaks.toml, scripts/ci/test_secret_scan_def835_metadata.py alleen de aanvullende vaste testregel/telling in Makefile en het corresponderende uitzonderingenoverzicht in docs/technisch/def522-secret-scan-runbook.md. De nieuwe test aan het vaste target toevoegen borgt de geaccordeerde regressietests; geen bestaande suites/vlaggen of scanbereik weghalen.

Controleer dat de rule-scoped AND voor generic-api-key daadwerkelijk geldt voor exact twee volledige manifestpaden en exact de regelinhoud uit het voorstel, inclusief zes spaties, dubbele quotes en komma. Uitsluitend bekende optionele voorafgaande newline. Geen prefix/suffix/wildcard/padskip/generieke regelversoepeling, disablement of credentialrotatieclaim. Eigenaar Chris en herreviewdatum vastgelegd.

TDD-bewijs moet gedragsmatige RED en GREEN met de echte gepinde Gitleaks op actuele projectconfig aantonen. Positief beide exacte combinaties; negatief ander pad, gewijzigde hash, extra tekst, synthetische credential op hetzelfde pad en een extra credential op een andere regel van hetzelfde bestand. Bestaande canaries blijven slagen, config blokkeert zichzelf niet. Geen ruwe secretbevindingen afdrukken; uitsluitend veilige status/regel-ID/pad/tellingen. Pinned binary /Users/chrislehnen/.cache/pre-commit/repo1h6yag49/golangenv-default/bin/gitleaks, Python /Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python. Gebruik een eigen nieuwe fixturemap zodat bestanden uit uitvoerdersbewijs behouden blijven. Herhaal relevante daadwerkelijke tests, geen bredere securityaudit zonder concrete vraag.

Rapporteer bevestigde bevindingen met ernst, locatie, bewijs en minimale correctierichting. Geen stilistische blocker. Geef oordeel over beperkte uitzondering en regressiebehoud; een geslaagde lokale canary is geen full-history-cleanclaim. Coördinator hervat na jouw review de normale staged-gate op de volledige index. Je mag die index niet wijzigen. Maximaal drie pogingen per actie.

Eindrapport via --output-last-message: gitleaks-codex-review-v1.md. Benoem exacte diff/manifestidentiteit en geteste reikwijdte. Geen bronwijzigingen en geen herdelegatie.

Het runbook noemt nu de derde uitzondering en nieuwe test. Controleer dat alle eerdere uitzonderingen en gatevoorwaarden behouden zijn en dat de tekst geen ruimere werking suggereert. Dit verandert het exact geaccordeerde detectiebereik niet.
