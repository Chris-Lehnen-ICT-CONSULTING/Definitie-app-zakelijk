# BATCH-154 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Vastgelegde reviewer: `codex-hypatia`
- Onafhankelijke verifier: `codex-galileo`
- Scope: 14/14 bereiken, 5567/5567 fysieke regels en 0/0 Python-symbolen

Alle regels zijn rechtstreeks uit immutable Git-objecten gelezen; de bronbestanden zijn niet gewijzigd.

## Verificatie

- Alle immutable documentatie is gelezen; offline service-, import-, Config- en shellsentinelreproducties plus gerichte validatietests zijn uitgevoerd.
- Object-ID, range, line owner en reviewerpair matchten het batchmanifest exact.

## Bevindingen

### B154-001 — P2 — Web-lookup-startgids presenteert teruggedraaide Rechtspraak-tekstzoeking en een uitgevoerde schemawijziging als nog te implementeren

**Bewijs:** De gids noemt Rechtspraak-tekstzoeking perfect werkend (regels 19-22 en 50-54), markeert het verouderde consensusrapport als START HIER en draagt developers op record_schema naar gzd te wijzigen. De latere finale analyse in dezelfde scope zegt expliciet dat tekstzoeking is verwijderd en alleen ECLI wordt ondersteund (web-lookup-implementatie-final.md:83-111,143-153); de immutable implementatie retourneert voor iedere niet-ECLI vóór netwerktoegang None (src/services/web_lookup/rechtspraak_rest_service.py:139-160) en SRUService gebruikt al gzd (src/services/web_lookup/sru_service.py:130-141). De genoemde uppercase bestandsnaam WEB_LOOKUP_CONSENSUS_RAPPORT.md bestaat bovendien niet case-sensitive; alleen web-lookup-consensus-rapport.md bestaat.

**Reproductie:** Roep rechtspraak_lookup offline aan met onherroepelijk vonnis, strafrecht en hoger beroep; alle drie retourneren None zonder netwerk. Vergelijk daarna de quick-start met _setup_endpoints: wetgeving_nl.record_schema is al gzd, en controleer de genoemde START-HIER-bestandsnaam met git cat-file -e op base b958ddb.

**Aanbevolen oplossing:** Markeer de gids als superseded door web-lookup-implementatie-final.md of herschrijf hem naar de actuele ECLI-only- en configuratiegestuurde architectuur; verwijder de uitgevoerde quick-fix, corrigeer het case-sensitive pad en maak offline contracttests de bron voor capabilityclaims en live scripts expliciet opt-in.

### B154-002 — P2 — API-key-herstelgids laat gebruikers geheimen tonen en als platte tekst in shellconfig opslaan

**Bewijs:** De als USER ACTION REQUIRED gemarkeerde procedure voert echo $OPENAI_API_KEY_PROD vóór en na rotatie uit en adviseert de volledige productiesleutel met export in ~/.zshrc of ~/.bashrc te bewaren. Daardoor verschijnt het geheim in terminaloutput/scrollback en staat het blijvend als platte tekst in een algemeen shellstartbestand; dit botst met de eigen les op regels 109-113 en de projectregel dat API keys alleen via beschermde omgevingsconfiguratie mogen lopen.

**Reproductie:** Zet lokaal alleen voor één proces OPENAI_API_KEY_PROD=sk-proj-REVIEW-SENTINEL-123 en voer het gedocumenteerde echo-commando uit; stdout bevat de volledige sentinel. Inspecteer de voorgestelde export-regel zonder hem uit te voeren: daarin staat de volledige sleutel letterlijk in het shellconfigbestand.

**Aanbevolen oplossing:** Laat gebruikers nooit sleutelwaarden echoën, gebruik een aanwezigheid-/laatste-vier-controle met redactie, verwijs naar een niet-getrackte .env met strikte rechten of OS-secret store/deployment secrets, documenteer rotatie en revocation, en verwijder OPENAI_API_KEY_PROD-specifieke herstelstappen uit deze historische provideranalyse.

## Deduplicaties en afwijzingen

- De API-keyinstructie is geen duplicate van B101-005: dit is een handmatige herstelgids, niet het actieve cleanupscript.

## Niet getest

- Geen live SRU/Rechtspraak/OpenAI, echte credentials, destructive cleanup, browser/rendering of externe hyperlinks.
