# BATCH-161 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Vastgelegde reviewer: `codex-galileo`
- Onafhankelijke verifier: `codex-hypatia`
- Scope: 24/24 bereiken, 5980/5980 fysieke regels en 1/1 Python-symbolen

Alle regels zijn rechtstreeks uit immutable Git-objecten gelezen; de bronbestanden zijn niet gewijzigd.

## Verificatie

- Alle immutable bronnen zijn gelezen; reset-script-, AST-, Ruff-, Black-, secret-, link- en gecontroleerde false-successreproducties zijn uitgevoerd.
- Object-ID, range, line owner en reviewerpair matchten het batchmanifest exact.

## Bevindingen

### B161-001 — P2 — Als actueel en canoniek gemarkeerde handover schrijft ongeborgde verwijdering van de standaarddatabase voor

**Bewijs:** De frontmatter noemt het document canonical: true, status: active en toepasselijk op definitie-app@current. Regels 35-46 stellen zonder bewijs dat alle huidige data testdata is en instrueren `bash scripts/db/reset_context_model_v2.sh`. De eveneens canonieke docs/architectuur/CONTEXT_MODEL_V2.md:23-40 autoriseert dezelfde DROP/CREATE-aanpak vanuit die onbewezen aanname. Het immutable resetscript verwijdert op regels 4-12 zonder bevestiging, backup of postcondition `data/definities.db` plus WAL/SHM en bouwt daarna een lege database; dat pad is de productiestandaard van onder meer DefinitieRepository, Container en SynonymRegistry. Twee andere active/current handovers herhalen de opdracht.

**Reproductie:** Voer het immutable resetscript uit met alleen `rm` en `sqlite3` vervangen door loggende shellfuncties. De trace meldt exact dat `data/definities.db`, `data/definities.db-shm` en `data/definities.db-wal` zouden worden verwijderd en daarna 19.414 schemabytes naar een nieuwe database zouden gaan. Traceer daarnaast CONTEXT_MODEL_V2.md:23-40 naar dezelfde defaultdatabase; er is geen identity-, disposable-data-, backup- of postconditiongate.

**Aanbevolen oplossing:** Trek de canonical/active-markering in en verwijder de reset uit iedere smokeprocedure. Laat destructieve reset alleen een expliciet opgegeven tijdelijke database accepteren, weiger het standaardpad zonder dubbele bevestiging, controleer repository-root en actieve processen, maak en verifieer een herstelbare backup en test postconditions. Gebruik voor smoke-tests altijd een geïsoleerde tijdelijke databasefixture.

### B161-002 — P3 — Gearchiveerde quick test gebruikt ambient imports, schrijft een CWD-database en eindigt succesvol na expliciete fouten

**Bewijs:** De rootberekening op regels 7-9 wijst na archivering naar `docs/archief`, waar geen src-map bestaat. Alle vijf checks vangen elke Exception en regels 62 printen onvoorwaardelijk voltooiing zonder foutstatus. De databasecheck opent bovendien het relatieve pad `test.db` zonder cleanup. Een credentialvrije run vanuit /private/tmp importeerde enkele modules toevallig uit de venv, schreef daar een database van 233.472 bytes, meldde twee importfouten en retourneerde toch exitcode 0.

**Reproductie:** Voer het bestand credentialvrij met project-Python vanuit een lege tijdelijke werkmap uit en schakel bytecode/cache uit. Observeer `No module named ai_toetser`, `No module named services.definition_service`, de afsluitende tekst `Quick test compleet`, exitcode 0 en een nieuw relatief `test.db`; bereken daarnaast dat de ingevoegde src-map `docs/archief/src` niet bestaat.

**Aanbevolen oplossing:** Maak dit archivebestand niet langer uitvoerbaar of vervang het door een onderhouden pytest-smoke. Resolveer de repository/package-root expliciet, injecteer tmp_path voor iedere database, sluit en verwijder fixtures via teardown, eis precieze functionele assertions en laat iedere mislukte of niet-uitgevoerde check de exitcode blokkeren.

## Deduplicaties en afwijzingen

- B163-003 is als aanvullend bewijs samengevoegd in B161-001; de resetroot is éénmaal geteld.

## Niet getest

- Geen echte database-reset/productiedata, live concurrente clients, netwerk, credentials of browser/screenreader/touch/responsive runtime.
