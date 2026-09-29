**F1 en F2 zijn gesloten. F3 blijft gedeeltelijk open en blokkerend.** Q1 kan daarmee nog niet worden vrijgegeven.

1. **F1 — gesloten.**  
   In [def835_int02_modelproef.py:1940](/Users/chrislehnen/.codex/worktrees/def835-q1-review/Definitie-app/scripts/analysis/def835_int02_modelproef.py:1940) worden onder het exclusieve slot de actuele stand, fasetoelaatbaarheid en ruimte opnieuw gecontroleerd. Het slot omvat transport, bewijsopslag en afronding.

   Mijn aangepaste twe processenprobe gaf **24 inferenties/24 tokenmetingen voor één uitvoerder**, en **nul transport voor de tweede**, met `proefmap_in_gebruik`. Het grootboek bleef geldig op cumulatief **27/27**; het slotbestand bleef bestaan. De vroege controle buiten het slot bestaat nog, maar autoriseert geen transport op een verouderde stand.

2. **F2 — gesloten.**  
   [def835_int02_modelproef.py:1762](/Users/chrislehnen/.codex/worktrees/def835-q1-review/Definitie-app/scripts/analysis/def835_int02_modelproef.py:1762) controleert volledigheid, geldigheid en de bevroren p95-grens. Mijn oorspronkelijke 91-secondenprobe geeft nu `p95_ms=91000`, `mechanisch_geslaagd=false`, `p95_boven_grens` en `holdout=false`.

   Het geldige testbewijs dekt daarnaast exact **90000 toegestaan / 90001 geweigerd**, ontbrekende metingen en ongeldige waarden.

3. **F3 — nog open: hoog, dispositie ‘fix nu’.**  
   De oorspronkelijke artefactfouten zijn opgelost: afzonderlijke fouten op bundel en resultaat geven nu `bewijsopslag_mislukt`, een mislukte fase en **nul vervolgcalls**. Dit heb ik opnieuw geverifieerd.

   **Resterende locatie:** [def835_int02_modelproef.py:2021](/Users/chrislehnen/.codex/worktrees/def835-q1-review/Definitie-app/scripts/analysis/def835_int02_modelproef.py:2021), de afrondingsaanroep; [regel 509](/Users/chrislehnen/.codex/worktrees/def835-q1-review/Definitie-app/scripts/analysis/def835_int02_modelproef.py:509), `fsync` na `flush`.

   **Reproduceerbare trace:** laat drie regressies slagen en injecteer uitsluitend bij `fsync` van de zojuist geflushte `fase_einde`-regel een `OSError(EIO)`. De run breekt af, maar de regel is al leesbaar met `mechanisch_geslaagd=true` en `bewijs_opgeslagen=true`. Een nieuwe grootboeklezing geeft `regressie=true`, `open_fase=null`. De aansluitende ontwikkelrun verstuurt vervolgens **24 calls** en slaagt.

   **Geschonden:** een fout bij grootboekafronding moet de fase mislukt of open laten en vervolgtransport blokkeren. De nieuwe test injecteert vóór het schrijven en mist dit foutmoment.

   **Kleinste herstel:** borg bij een mislukte afronding een blijvende blokkade die herstart vóór transport controleert; een reeds leesbare succesregel mag die blokkade niet opheffen. Voeg een gerichte test toe voor `fsync`-falen ná `flush`.

Het POSIX-slot past bij deze lokale macOS-uitvoering. Ontbrekende directory-fsync onderbouwt geen garantie bij systeem- of stroomuitval; daarvoor rapporteer ik geen aanvullende, onbewezen bevinding. Het resterende F3-probleem is rechtstreeks offline gereproduceerd en vereist geen systeemcrash.

Het coördinatorbewijs van **171 geslaagde tests en Ruff/Black exit 0** is hergebruikt. Aanvullende [probe](/private/tmp/def835-q1-herreview-mFxx7E/probe.py) en [uitvoer](/private/tmp/def835-q1-herreview-mFxx7E/probe.log) staan tijdelijk buiten de repository. Alle probes gebruikten offline-bootstrap en neptransporten. De drie opgegeven SHA-256-hashes zijn vóór en na de herreview identiek; bronbestanden, tests en configuratie zijn niet gewijzigd.