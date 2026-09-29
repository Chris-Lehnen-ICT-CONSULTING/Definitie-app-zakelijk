# Opdracht — DEF-835 technische proefrunner, offline bouwen

Jij bent de Claude Code CLI-uitvoerder. Voer deze opdracht zelf uit; start geen agents, reviewers of extra CLI-sessies. De coördinator reviewt niet in jouw plaats; aparte Codex CLI volgt. Alles rapporteren in het Nederlands.

Werkboom `/Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-835-int02-o2`, branch `feature/DEF-835-int02-o2`, basis `558b50c3f161f819cda6c445f7f81b70888918ac`. Lees CLAUDE.md, relevante .claude/rules en de bestaande WP2-service/contracttests. Lees `technische-modelproef-voorstel-v1.md` in deze dossiermap volledig; dit zijn de acceptatiecriteria. Algemene toestemming echte modelcalls bestaat, maar jij voert NU GEEN ECHTE PROVIDERCALLS uit: offline voorbereiding, tests en dry-run. Geen keys lezen nodig.

Eigenaarschap uitsluitend twee nieuwe bestanden:
- scripts/analysis/def835_int02_modelproef.py
- tests/unit/validation/test_def835_int02_modelproef.py

Daarnaast nieuw verslag `modelproef-claude-verslag-v1.md` en bewijs `bewijs/modelproef-*` in deze dossiermap. Geen bestaande bestanden veranderen/verwijderen, geen globaleconfig/Actions/DB/dependencies wijzigen, geen appactivering, geen git push/merge. Geen verdere delegatie. >100 regels INT-02 is toegestaan; blijf minimaal en binnen twee softwarebestanden. Stop met concreet voorstel als dit niet kan.

TDD: falende gedragstest eerst, RED-uitvoer bewaren vóór implementatie, dan groen en relevante lint/formatterchecks. Python/testtools uit `/Users/chrislehnen/Projecten/Definitie-app/.venv/bin/`. Bewijs volledige commando's + exits. Laat nieuwe tests doorlopen met WP1/WP2/WP3 gerichte tests waar dit de gebruikte keten raakt, geen volledige suite nodig voor deze geïsoleerde runner.

Ontwerprichting (jij beslist details): AIServiceV2 accepteert ai_client/model_router en RateLimitConfig; echte AnthropicClient accepteert router en max_retries. Een observer bij SDK/HTTP-grens kan exact request, count_tokens en echte usage meten, want ChatResponse bevat alleen totale tokens. Gebruik geen alternatieve prompt-/modelimplementatie. De bestaande keten blijft intact, de observatie/guards zitten uitsluitend in de runner. Een fake transport injecteren voor offline tests is toegestaan. Vermijd duplicatie van capabilitybeleid; begrens de daadwerkelijk verstuurde payload, inclusief uitsluiten caches/tools/etc. Als SDK-interceptie niet betrouwbaar kan, meld dit concreet.

Default voorbereiden zonder netwerk/sleutels: maak een nieuw manifest van exacte synthetische input, norm/T-prompt en configuratie/hashes, profiel/limieten en toestemmingpending. Maak live uitvoerbaar met expliciet akkoordmanifest dat deze identiteit bindt; geen zelfgemaakte toestemming. Beschrijf benodigde akkoordvelden in verslag. Geen waarden uit fake kwalificatie meenemen als productiekwalificatie. Proefautorisatie heet expliciet experimenteel, geen DEF-815-kwaliteitsclaim.

Provider-tokenmeting maximaal 3, inference maximaal 3; alle verborgen SDK/appretries uit, nofallback/cache. Werkelijke input/output-usage registreren; maxoutput6000, geschatte input16000, budgetUSD1 met marge en conservatieve reservering. Een tokenestimate is geen factuurgarantie. Ontbrekende usage of nietstandaardkostenvariant stopt verderecalls. Stopvoorbudget/inhoudhashmismatch, technische fout, truncatie, citation-invalid. Hardcalllimiet hoort ook bij foutcalls te tellen. Geen kunstmatige proef-passes. Geen autoherhaling bij semantisch onverwacht verdict.

Zorg dat monitoring/cache geen productiegegevens leest: tijdelijke scratch-cwd, repo/config/norm/fixturepaden expliciet afleiden. Onderdruk rawproviderexception-logging uitsluitend in dit losse proces, bewaar fouttype/categorie zonder str(exc). Synthetische volledige payloads alleen expliciet onder nieuw bewijsdoel. Geen bestaand bestand overschrijven. Geheimen alleen live ophalen uit bestaande lokale configuratie; sleutel nooit rapporteren. Geen eigenretentieclaims overprovider.

Lees alleen invoervelden uit fixture C105/C107/C112 voor verzoek; handmatigmodelrespons/verwacht niet versturen. Tests bewijzen echte offline keten met fake SDK/transport, geen parallel fake assessment. Bewaar eindmanifest/dry-run; noteer hashes, testresultaten, beperkingen en eventuele open bevindingen. Max3pogingen peractie; meld echte blokkade.

Commit uitsluitend de twee nieuwe softwarebestanden na checks met normale hooks, geen skips of bypass; coördinator commit dossier later. Laat overige werk ongemoeid. Rapporteer commitSHA en eindig.
