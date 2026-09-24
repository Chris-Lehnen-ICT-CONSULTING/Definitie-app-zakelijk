**Nog geen akkoord: twee bevestigde regressies, beide fix-nu.**

1. **Important — werkwoordtoken bewijst geen zelfstandige zin.**  
   [zinsgrenzen.py:467](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/src/domain/int01/zinsgrenzen.py:467) accepteert ieder genoemd werkwoord na het eerste token. Rechtstreeks gereproduceerd:
   - `regeling. om te worden toegepast` → `fail`, terwijl `worden` hier een infinitief is.
   - `regeling. die kan worden toegepast` → `fail`, hoewel het vervolg ook een bijzin kan zijn.
   - `regeling. zonder de verplichting die blijft gelden` → eveneens `fail`.

   De melding claimt telkens een bewezen zelfstandige tweede zin. De oude code hield deze grenzen onzeker. **Herstel:** laat infinitiefconstructies, bijzinnen en onbesliste contexten onzeker; onderbouw de zekerheid voor werkelijk zelfstandige vervolgzinnen. Voeg deze tegenhangers toe en behoud het correcte T24-resultaat bij `bundeling. controle volgens zqv. blijft vereist`.

2. **Important — citaatafsluiting verbergt een mogelijke buitenste zinsgrens.**  
   [zinsgrenzen.py:334](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/src/domain/int01/zinsgrenzen.py:334) negeert het slotteken vóór een sluitend aanhalingsteken zodra het vervolg klein begint. Repro:
   `code met de melding “Gereed.” controle blijft vereist`
   → nul zekere én onzekere grenzen, **zinsstructuur `pass`**. Met `Controle` blijft de grens wel onzeker. De totale INT-01-status blijft open, maar het zinsstructuurdeel wordt onterecht groen. **Herstel:** onderscheid interne citaatpunctuatie van een citaatafsluiting met mogelijk zelfstandig vervolg; behoud daar onzekerheid met passage. Bescherm tegelijk de geldige voortzetting `code die de melding “Gereed.” toont`.

**Dispositie oorspronkelijke zes afwijkingen:** T15, T17, T19, T22, T23 en T24 geven voor hun oorspronkelijke teksten nu de verwachte uitkomst. T17 en T24 zijn nog niet veilig afgesloten vanwege bovenstaande regressies. Geen aanvullende concrete afwijking gevonden in de onderzochte promptdoorwerking, overige INT/SAM-toepasselijkheid, betekenisbehoudinstructie of `/1`→`/2`-opslag/weergavebinding.

**Bewijs:** gelezen RED-log bevat 40 failures; gerichte JUnit bevat 64 geslaagde tests. `green-make-test-v2.log` is daadwerkelijk voltooid: **7135 passed, 75 skipped, 1 xfailed, exit 0**. Lint en afzonderlijke testformattering zijn groen. Zelf uitsluitend 13 directe, schrijfvrije segmentatieproeven en hash/patchcontroles uitgevoerd; geen brede suite herhaald.

Alle acht bestandshashes kloppen vóór en na review; geen drift. De 849 gecontroleerde nieuwe/contextregels uit de patch sluiten aan op de werkboom. Beoordeelde SHA256:
`c9f1c0d6e8d0f4e8d8b1ab1582c1144c919b37f61e1fe7120c69281d5e566bb7`.

Geen edits, agents of betaalde calls. Geen effectwinstclaim; skills vallen buiten dit oordeel.

Een aanvullende uitvoering van de oude module werd door de PreToolUse-hook geweigerd wegens een pipe naar een interpreter. Die actie is gestopt; de vergelijking met oud gedrag berust op de vastgelegde diff.