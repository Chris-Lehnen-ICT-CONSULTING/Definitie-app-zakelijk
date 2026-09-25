**T20 en T24 zijn materiële acceptatieafwijkingen. T18 is alleen redundante diagnostiek. Geen volledige acceptatie-/effectvrijgave.**

1. **T20 — Important: onnodige doorverwijzing.**  
   De verzegelde referentie verwacht zinsstructuur-pass vanwege de expliciete titelcontext en aansluitende bijzin met *waarop*. [zinsgrenzen.py:469](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/src/domain/int01/zinsgrenzen.py:469) herkent alleen een vóór het citaat geopende bijzin of aansluitende voorzetselgroepen. Dit geval valt daardoor terug op onzekerheid. Beide laadpaden tonen datzelfde resultaat.  
   **Dispositie:** open acceptatiebevinding binnen DEF-770; telt als afwijkend automatisch label. Het conservatieve beleid rechtvaardigt geen achteraf gewijzigde referentie. Dit is geen onjuiste zekere beslissing.

2. **T24 — Important: juiste status, onjuiste onderbouwing.**  
   `v.qr.` is lokaal verklaard, maar wordt niet herkend door het afkortingspatroon op [regel 109](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/src/domain/int01/zinsgrenzen.py:109). De terugvalregels melden vervolgens onzekerheid bij de afkortingspunten vóór `=` en `bepaalt`. De referentie verlangt onzekerheid wegens de **onduidelijke aansluiting na het haakje**. Overlap van de tweede passage maakt die andere reden niet correct.  
   **Dispositie:** open acceptatiebevinding binnen DEF-770; statusconform, maar niet volledig contractconform. Alleen de meldingen verwijderen en vervolgens pass geven zou evenmin voldoen.

3. **T18 — Minor: dubbele diagnostiek, geen afzonderlijke acceptatieblokkade.**  
   De gewone grens na `zaaibak.` draagt de correcte fail. Het terminale haakjessignaal beoordeelt dezelfde vervolgzin nogmaals onzeker; het trekt de fail niet in en bewijst geen extra derde zin. [Regel 808](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/src/domain/int01/zinsgrenzen.py:808) behoudt terecht fail.  
   **Dispositie:** diagnostische redundantie; geen extra contractafwijking meetellen op dit bewijs.

De voorlopige **23/24 labelconform en 22/24 volledig conform** past bij deze drie beoordelingen, mits de overige gevallen conform roots controle zijn. Ik heb die overige gevallen niet opnieuw beoordeeld.

Commit `c7f5d7dc921740f85a10d932480da338f9c2c276`, bronhashes, verzegelde referentiebestanden en criteria komen overeen; geen bron-/testdiff. De eerdere **bronvrijgave blijft historisch geldig**, maar bewijst geen volledige proefacceptatie. Het afzonderlijke onvoldoende G24-resultaat wordt hierdoor niet opgelost.

Geen labels gewijzigd, vervolgfix gestart, testsuite herhaald of modelcalls gedaan.