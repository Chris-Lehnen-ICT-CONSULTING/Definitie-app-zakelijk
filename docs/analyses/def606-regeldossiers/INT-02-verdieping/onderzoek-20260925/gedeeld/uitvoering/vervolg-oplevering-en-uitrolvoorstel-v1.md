# DEF-771 — vervolgverificatie en voorstel voor oplevering

## Besluiten en status

26 september 2026. Chris gaf akkoord op skill-CI en aanvullende ketenverificatie. De skillworkflow CI (id245866626) is na expliciet akkoord uitgeschakeld en door de API bevestigd als disabled_manually. De drie eerdere jobs waren door GitHub-billing vóór uitvoering geblokkeerd; geen groene-CI-claim. De app-Actions blijven actief.

Chris heeft de grens van100 regels voor noodzakelijk INT-02-werk expliciet verruimd (akkoord-int02-omvangverruiming-v1.md). De CLI-rolverdeling, inhoudelijke review en overige toestemmingsgrenzen blijven gelden.

## Bewezen resultaat

- 19 bestaande gerichte tests geslaagd; geen nieuwe volledige suite, omdat src/tests ongewijzigd zijn sinds de eerder beoordeelde en geteste code9ff3eac1.
- Ketenproef v3: C83 (RR met marker), C105 (RR zonder marker) en C56 (NE zonder context) slagen. Twee routes per casus: herladen synthetische invoer met verse validatie/renderer, en een werkelijk toegepast CON-02-bronvoorstel met opslag en teruglezing van de volledige kandidaatvalidatie.
- Route B bewaart INT-02 met status, reden, signalen en deelmelding. De nieuwe controle vergelijkt teruggelezen en verse velden; exacte NE-melding gecontroleerd.
- De normale proef geeft exit0. Drie geïnjecteerde fouten leveren ieder eindstatus1: route niet uitgevoerd, ontbrekende registratie, verkeerde teruggelezen NE-melding. Ruff en Black groen.
- De geteste expertlezing en JSON-recordexport gebruiken de bewaarde voorstelvalidatie niet als INT-02-uitkomst. JSON-export met expliciet aangeleverde toetsresultaten bevat INT-02 wel. Export zonder gate was uitsluitend diagnostisch.
- Route A schrijft geen validatieresultaat; behoud bij gewone opslag is niet onderzocht. Route B bewijst opslag bij toepassing van een bronvoorstel. Geen algemene opslagverliesclaim.
- Geen browser-/knopbediening of geslaagde vaststelling uitgevoerd. De previews blokkeren op bestaande voorwaarden, waaronder ontbrekend validatieresultaat; geen bewijs van algemene poortonafhankelijkheid. B5 blijft het besluit: geen zelfstandige INT-02-poort.

Claude Code CLI: a4b588d6-e4a1-4fd6-8f80-0aac55013d90. Dezelfde Codex CLI-reviewer: 01a0dc44-26c6-7de3-b2f9-b0f79e5a27ff. Reviewv1 vond drie bewijsproblemen; correctiereview sloot UI/poort/export en liet twee punten open; slotreview sluit beide. Geen resterende materiële bevinding in v3. De eerdere productiecodereview blijft geldig.

Leidend bewijs: vervolg-keten-rapport-v3.md, vervolg-keten-replay-v3.py/.json/.log, vervolg-keten-negatieve-controle-v1.log en vervolg-keten-codex-slotreview-v1.md. Script-SHA256 d36c4b5fe86b759ea002f6759492ff6ba3667149cbc2630de82c591a31df2fe3; JSON-SHA256 a40371204fadf4f3c70c29bef1ab94d115d284ebe592a9c5afe6daeb12217ebd. Historische proefscripts v1/v2, tussenrapporten, meetscript en ruwe CLIstreams blijven lokaal behouden; ze zijn geen actuele uitvoerbare oplevering. Alle volledige opdrachten en gerichte reviewrapporten worden wel gepubliceerd, plus het geaccepteerde v3-bewijs.

## Voorstel voor merge en actieve uitrol — nog niet geautoriseerd of uitgevoerd

1. Lever de huidige O1-implementatie via app-PR483 en skill-PR358, met bovenstaande ketengrenzen. Geen samengestelde volledige-ketenacceptatie afvinken.
2. Maak vóór actieve publicatie een controleerbare kandidaat die uitsluitend de INT-02-delta toepast op de dan actuele skills. De actieve bestanden bevatten INT-03 uit DEF-772; de huidige skillbranch bevat die wijzigingen niet. Hele bestanden uit deze branch kopiëren zou INT-03 terugdraaien en is dus geen aanvaardbare uitrolroute. Behoud INT-03 en andere bestaande inhoud; laat de concrete publicatieverschillen controleren.
3. De inhoudelijke bronset bestaat uit zes bestanden: voor definitie-toetsregels en definitie-nederlandse-definities elk SKILL.md, reference.md en references/int02-beslisregel.md. Actieve doelroots zijn /Users/chrislehnen/.agents/skills en /Users/chrislehnen/.claude/skills: twaalf doelbestanden (acht bestaande teksten, vier nieuwe contractkopieën). Geen brede install.sh-run. Vooraf unieke herstelkopieën; geen bestanden verwijderen. De contractkopieën moeten bytegelijk zijn aan def771-int02/2, SHA256 bc16c128c43e247b25db996d25059af48fe56dccea5cdc4012ceb401746b043c.
4. Vraag pas akkoord voor de daadwerkelijke merge/publicatie wanneer die concrete kandidaat is gecontroleerd. Gewone merges, geen squash/rebase/force. Controleer daarna actieve contractbinding en gerichte functionaliteit opnieuw.

Voor volledige ketenoplevering is daarnaast behoud en ontsluiting van validatiebewijs nodig. De gedeelde richting staat in DEF-626: append-only snapshots, atomair met definitieversies. Het losse int02/opslag.py-idee is ingetrokken; het was geen vastgesteld ontwerp. DEF-626-implementatie en nieuwe schema-/resultaatcontractbesluiten vallen buiten de huidige opdracht. O2 blijft apart DEF-835; effectmeting vraagt aparte autorisatie. DEF-830 en CON-01-keuze in DEF-831 blijven open.
