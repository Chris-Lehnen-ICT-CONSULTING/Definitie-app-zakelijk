# Gerichte bewijscontrole vóór uitvoering

Open vraag: kloppen bronbinding, P1-invoer/uitvoer en de tellingen waarmee A de nieuwe claims onderbouwt?
Verwachting op grond van A-proeflog en gelezen scripts: 25 identieke input/output-casussen; 25 INT-02-review_required, nul pass/fail; 11 signaalgevallen; acht INT-10-fails precies bij indien; A meldt 20 INT-01-fails; C1 13 overeenkomende verwachtingen. Alle eerder gehashte A-bronnen ongewijzigd. Dit is een artefactcontrole, geen nieuwe appproef of modelkwaliteitsmeting.
Commando: python3 bewijs/review-audit-v1.py vanuit b-codex-cli. Alleen lezen in A/repo; nieuwe uitvoer in bewijs/. HEAD verwacht 26f2374d302fc66fc0b12ed29dc34585f7c0a5c3. Exitstatus apart geregistreerd door aanroeper. Afwijking in aantallen wordt gemeld, niet stil gecorrigeerd.
