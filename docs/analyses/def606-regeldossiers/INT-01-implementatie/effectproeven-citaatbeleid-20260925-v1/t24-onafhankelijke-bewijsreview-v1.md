**Acceptatie niet vrijgegeven. Twee Important-bevindingen en één LOW-diagnostiekbevinding zijn bevestigd; geen referentieprobleem aangetoond.**

1. **Important — T15: lijstcontext gaat na het eerste opsommingslid verloren. Dispositie: fix nu.**  
   [zinsgrenzen.py:702](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/src/domain/int01/zinsgrenzen.py:702) kijkt uitsluitend naar het teken onmiddellijk vóór iedere regelovergang. De dubbele punt beschermt daardoor alleen het eerste lid. T15 krijgt twee onzekere grenzen, terwijl beide referenties en adjudicatie één samenhangende opsomming vaststellen.  
   Minimale reproductie: `lagen:\n- bovenlaag\n- onderlaag` → onzeker; met een puntkomma na `bovenlaag` → zinsstructuur-pass.  
   **Begrensd herstel:** behoud de expliciete lijstinleiding gedurende het aaneengesloten opsommingsblok. Behoud beoordeling van werkelijke zinseindtekens en onderscheid niet-ingeleide lijsten, blokonderbrekingen en zelfstandige vervolgtekst. Hiervoor is geen nieuwe woordrolheuristiek nodig.

2. **Important — T17 en T20: komma na citaatslot verwijdert de kandidaat. Dispositie: fix nu.**  
   [zinsgrenzen.py:325](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/src/domain/int01/zinsgrenzen.py:325) slaat de kandidaat over wanneer na het sluitende aanhalingsteken geen witruimte staat. Bij `!’, dat` staat daar een komma; de beleidsroute wordt nooit bereikt.  
   Minimale reproductie: `bord met de tekst ‘kom terug!’, dat verschijnt` → zinsstructuur-pass; zonder komma → onzeker. Dit schendt het expliciete algemene citaatbeleid.  
   T20 heeft dezelfde oorzaak: de uiteindelijke fail klopt, maar de expliciet vereiste onzekere passage `‘Wie luistert?’, waarop een geluid` ontbreekt.  
   **Begrensd herstel:** herken deze citaatslotovergang ook met de tussenliggende komma en stuur haar naar de bestaande onzekerheidsroute, met oorspronkelijke bewijspositie. Behoud citaten zonder slotteken, interne citaatpunctuatie en latere zekere grenzen. Geen grammaticale pass-herkenning toevoegen.

3. **LOW — T08: onterechte extra onzekerheid bij intern `bijv.`. Dispositie: fix nu, afzonderlijk diagnostisch afbakenen.**  
   [zinsgrenzen.py:640](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/src/domain/int01/zinsgrenzen.py:640) meldt uitsluitend wegens de hoofdletter van `R7` een mogelijke grens na `bijv.`. Beide referenties herkennen hier expliciet een voorbeeldcode; de werkelijke grens ligt na `R7.`. De fail blijft terecht, maar de aanvullende reden is niet contractconform. Behoud bij herstel de echte grens; geen algemene vrijstelling voor afkortingen vóór hoofdletters.

De oorzaken zijn **reeds aanwezig op directe base `c8e8997…` (/7)**: minimale probes geven dezelfde uitkomsten en de drie betrokken functies zijn AST-gelijk. Dit zijn dus geen nieuw geïntroduceerde codepaden van /8. Tegen de oorspronkelijke proefbase `26f2374…` verslechtert T15 van pass naar onzeker; T17 verandert van fail naar een volgens het huidige automatische beleid onbewezen pass. Dat T17 normatief pass is, maakt die automatische zekerheid niet toegestaan.

De telling **22/24 zinsstatussen** klopt: 10 pass, 9 fail, 4 review, 1 leeg. Vanwege T08 en T20 zijn **20/24 gevallen volledig conform qua status én diagnostiek**. De overige twintig hebben passende redenen, grenspassages en broncitaatstatus. Beide laadpaden en opslag zijn 24/24 consistent; geen fouten of volledige INT-01-passes. **19/19 normatief ondersteunde automatische beslissingen betekent hier niet 19/19 beleidsconforme beslissingen.**

Bronfreeze, beide referentieseals, archief en commitbinding gecontroleerd; geen drift. Beoordeeld: `ad4be749b2e38b968a22605f3842e244e6a766b7`. Resultaat-SHA256: `d8eaa80387cf30c32523ed06baf24e70c00a6caf56958a6089d199744b69fd2a`.

Alleen schrijfvrije controles uitgevoerd. Labels ongewijzigd; geen implementatie, brede suite of betaalde calls gestart. Generatie-effect staat buiten dit oordeel.