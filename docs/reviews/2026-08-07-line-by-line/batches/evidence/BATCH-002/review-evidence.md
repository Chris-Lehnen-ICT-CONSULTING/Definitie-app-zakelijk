# BATCH-002 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Vastgelegde reviewer: `codex-kierkegaard`
- Onafhankelijke verifier: `codex-hypatia`
- Scope: 20/20 bereiken, 1995/1995 fysieke regels en 0/0 Python-symbolen

Alle regels zijn rechtstreeks uit immutable Git-objecten gelezen; de bronbestanden zijn niet gewijzigd.

## Verificatie

- Alle 20 immutable workflow-/templateblobs zijn gelezen; 19 YAML-bestanden, 67 shellblokken en de zes gate-/feedbackreproducties zijn veilig offline gecontroleerd.
- Object-ID, range, line owner en reviewerpair matchten het batchmanifest exact.

## Bevindingen

### B002-001 — P2 — Branchnaam wordt als shellcode in de validatiestap geïnterpoleerd

**Bewijs:** De pull_request-waarde github.head_ref wordt op regel 114 rechtstreeks binnen een dubbelgequote shelltoewijzing gerenderd. Een syntactisch geldige maar speciaal gevormde Git-ref liet in een geïsoleerde, onschadelijke rendercheck shellinhoud uitvoeren en beëindigde de stap met exit 0 voordat de regexvalidatie werd bereikt.

**Reproductie:** Render de gepinde run-sectie met een onschadelijke Git-geldige branchnaam die shellmetatekens bevat; voer uitsluitend in een geïsoleerde shell uit en assert dat de normale tekst 'Validating branch name' als eerste controle wordt bereikt zonder inhoud uit de branchnaam uit te voeren.

**Aanbevolen oplossing:** Geef github.head_ref via een step-level env-variabele door en behandel die in de shell uitsluitend als data; voeg een regressietest toe met ongebruikelijke geldige refnamen en eis dat iedere ongeldige conventienaam niet-nul eindigt.

### B002-002 — P2 — Preflight-scans zijn afhankelijk van stdin en scannen niet deterministisch de repository

**Bewijs:** De hardcoded-secret- en TODO-aanroepen geven rg geen pad. Met niet-interactieve lege stdin eindigde de exacte fallback groen zonder repositoryscan; vanuit een terminal doorzocht dezelfde secretregex de werkboom en matchte gewone os.getenv-aanroepen en testwaarden. De gate kan daardoor zowel stil niets controleren als vals blokkeren, afhankelijk van stdin/TTY.

**Reproductie:** Voer de twee gepinde rg-aanroepen eenmaal met lege niet-interactieve stdin en eenmaal met een expliciet repositorypad uit; vergelijk exitcodes en treffers en verifieer dat de workflowvariant geen vast doelpad heeft.

**Aanbevolen oplossing:** Geef altijd een expliciet, gevalideerd doelpad zoals src tests scripts door, onderscheid rg-exitcodes 0/1/>1, gebruik de canonieke secretscanner voor echte geheimen en voeg headless-runnerfixtures toe voor nul treffers, echte treffers en toolfouten.

### B002-003 — P2 — Epic- en storyworkflow valideert geen huidige documenten en heeft tegenstrijdige gates

**Bewijs:** De base bevat nul docs/epics/EPIC-*.md en nul docs/stories/US-*.md; docs/stories ontbreekt volledig. De frontmatterloops melden daardoor groen na nul controles. Een document met uitsluitend `id:` voldoet al aan de vijf-veldenpredicate; de uniqueness-stap eindigt onder bash -e/pipefail met exit 2 en, na reparatie daarvan, crasht de cross-referencecontrole op de ontbrekende storydirectory.

**Reproductie:** Voer de gepinde run-secties offline uit tegen de immutable base en tel vooraf de EPIC-/US-globs. Test de frontmatterpredicate met alleen `id:` en voer daarna de uniqueness- en cross-referenceblokken uit; zij eindigen respectievelijk met exit 2 en een ontbrekende-directoryfout.

**Aanbevolen oplossing:** Inventariseer bestanden NUL-veilig vanuit één canonieke pad-/naamconventie, faal expliciet op een onverwacht lege scope, parse YAML-frontmatter structureel en vereis iedere sleutel afzonderlijk; test nul, één en meerdere bestanden plus duplicate IDs.

### B002-004 — P2 — CI voert externe acties uit via wijzigbare refs, inclusief een actie met een secret

**Bewijs:** Alle 40 `uses:`-verwijzingen in de veertien toegewezen workflows gebruiken tags of branches en nul een volledige commit-SHA. Twee codecov/codecov-action@v7-stappen ontvangen CODECOV_TOKEN; mutable labeler-, github-script- en PR-size-acties draaien met write-capable GitHub-tokens. security.yml downloadt bovendien gitleaks zonder checksum of signature. De werkelijk uitgevoerde externe code is dus niet aan de review-base gebonden.

**Reproductie:** Inventariseer de veertig `uses:`-waarden uit de gepinde workflowblobs en classificeer alleen refs met exact veertig hextekens als immutable; het resultaat is 0/40. Traceer vervolgens de token-, permissions- en ongeverifieerde binarydownloadstappen.

**Aanbevolen oplossing:** Pin iedere actie op een gereviewde volledige commit-SHA met een versiecommentaar, beperk permissions per job tot het minimum en laat Dependabot gecontroleerde SHA-updates voorstellen; verifieer gedownloade binaries met een onafhankelijk gepinde checksum of signature.

### B002-005 — P3 — Always-run epicrapport claimt succes na gefaalde of overgeslagen controles

**Bewijs:** De rapportstap en uploadstap gebruiken if: always(). Het rapport schrijft onvoorwaardelijk drie groene succesregels voor frontmatter, uniqueness en cross-references. Op de immutable base faalt de uniqueness-stap aantoonbaar met exit 2, maar het geüploade rapport zou desondanks alle drie als geslaagd markeren.

**Reproductie:** Laat een voorafgaande validatiestap in een offline workflowmodel niet-nul eindigen en evalueer daarna de letterlijke always-run rapportsectie; vergelijk de vaste groene regels met de werkelijke step outcomes.

**Aanbevolen oplossing:** Leg iedere step outcome en telling machineleesbaar vast, genereer het rapport daaruit, markeer failed/skipped correct en laat de upload wel altijd lopen zonder de resultaten als groen te fabriceren.

### B002-006 — P3 — Gefaalde contracttest kan een groene PR-comment plaatsen

**Bewijs:** De PR-commentstap draait met `if: always()` en controleert alleen of pytest.xml bestaat. Pytest schrijft dat bestand ook bij failures en collection errors; de body gebruikt dan nog steeds een groen vinkje en dezelfde 'completed'-tekst, zonder failurestatus of aantallen, terwijl de workflowjob rood kan zijn.

**Reproductie:** Gebruik een geïsoleerd JUnit-bestand met een failure en één met een collection error. Evalueer de gepinde JavaScriptvoorwaarde: alleen file-existence wordt gelezen en in beide gevallen wordt dezelfde groene completed-body gekozen.

**Aanbevolen oplossing:** Parse de JUnit-totalen of gebruik job.status, kies expliciete pass/fail/blocked feedback met aantallen en runlink, en voorkom een groen succesicoon wanneer failures of collection errors aanwezig zijn.

## Deduplicaties en afwijzingen

- Oude repository-identiteitslinks relateren aan B176-001; PCRE/fail-open gatefouten in epic-010 zijn B097-007 en niet opnieuw geteld.

## Niet getest

- Geen live GitHub Actions, branch protection, repositoryrechten, echte secrets, externe action-inhoud of PR-comments; geen netwerk gebruikt.
