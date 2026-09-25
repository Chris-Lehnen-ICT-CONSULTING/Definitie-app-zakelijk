**T18 is een bevestigde functionele fout. T17/T20 zijn conservatieve dekkingsgrenzen, maar blijven afwijkingen van het verzegelde automatische proefcontract. Geen vrijgave als geslaagde eindproef.**

| Geval | Normatieve referentie | Automatisch verwacht | App-zinsstructuur |
|---|---|---|---|
| T17 | pass | pass | onzeker |
| T18 | fail | onzeker | **pass** |
| T20 | pass | pass | onzeker |

**T18 — Important, fix-nu.**  
Bij `register voor tijdelijke proefboekingen (De beheerder wist deze na de oefening.)` slaat [zinsgrenzen.py:295](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/src/domain/int01/zinsgrenzen.py:295) het sluitende haakje over. Omdat daarna geen tekst resteert, wordt de punt weggefilterd. Er ontstaat geen kandidaat; vervolgens betekent “geen grenzen gevonden” zinsstructuur-pass. Dit is in beide laadpaden én opgeslagen readback bevestigd. Toevoeging van ` per proef` maakt dezelfde haakjespunt wél onzeker: de eindpositie veroorzaakt het gemiste signaal.

Begrensd herstel: beoordeel zinsachtige punctuatie binnen een afsluitend haakjesdeel ook zonder buitenste vervolg. Geef bij onvoldoende bewijs **onzekerheid met passage/positie**, geen automatische fail. Bescherm gewone haakjesbepalingen, afkortingen en getallen. Verifieer beide laadpaden en opslag; voorkom dat opgeslagen `/3`-oordelen na gewijzigde beslisbetekenis actueel blijven.

**T17/T20 — Important voor proefacceptatie; fix-nu vóór een geslaagde proefclaim.**  
Het zijn geen onterechte zekere normoordelen:

- T17: [regel 420](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/src/domain/int01/zinsgrenzen.py:420) ziet alleen `bediener de melding`; de eerdere bijzinmarkering `waarmee` valt buiten het herkenningsvenster. `die de melding … bevestigt` passeert wel.
- T20: [regel 540](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/src/domain/int01/zinsgrenzen.py:540) accepteert uitsluitend korte slotgroepen; `voor het reconstrueren van een vaarvolgorde` valt erbuiten.

Doorverwijzen past bij conservatieve onbekende syntaxis. Het voldoet hier echter niet aan de vooraf verwachte automatische pass. Verbreed alleen met algemeen onderbouwde inbeddingsherkenning en negatieve tegenhangers; geen corpuswoordenlijst of ruimere lengtegrens als surrogaat voor bewijs. Zolang dat niet veilig kan, blijven deze proefverwachtingen onvervuld. **Geen labelwijziging, waiver of criteriumverlaging.**

Alle drie houden totaalstatus `review_required`; dat verbergt het verschil op zinsstructuur niet.

**G24:** een uitsluitend classifiergerichte correctie verandert de bevroren prompts, instellingen en providerantwoorden niet. De blinde inhoudelijke beoordeling kan doorgaan. Automatische evaluatorresultaten blijven gebonden aan de oude classifier; eventuele nieuwe offline beoordeling moet afzonderlijk worden vastgelegd. Geen nieuwe generatiecalls nodig voor dit herstel.

Bewijsbinding: HEAD `6c18ce7127f0a785fefdd6bc952175a030be8643`; verzegelde gevallen, adjudicatie en proefafspraken gecontroleerd, evenals bronhashes. Beide laadpaden en readback stemmen overeen. Zes schrijfvrije repro’s uitgevoerd; geen edits of brede herreview. Geen effectclaim.