# DEF-622 — transportverificatie en onafhankelijke review

14 september 2026. Afgebakende eerste levering; geen bewijs voor het volledige CON-01-, vaststel- of exportcontract.

## Bronbinding en uitvoering

- Basis `d68a98a90`, implementatie `09b0d6ff2`, reviewcorrectie `3d4b98507`.
- Implementer: Claude CLI sessie 09cab2f3-3e97-4c40-9c75-3dcf86637141.
- Reviewer: afzonderlijke Codex CLI sessie 01a09fe9-fafe-7fe2-a781-154681dd20a2, native agents uit, geconfigureerde MCP-servers uit, read-only sandbox. Reviewer bevestigde effectieve toolgroepen zonder delegatietools.
- Desktopcoördinator draaide de nieuwe transporttests plus bestaande orchestratorregressies zelf: 15 tests exit 0 vóór reviewcorrectie, 16 tests exit 0 erna. Logs: `/private/tmp/DEF-622-transport-verificatie.log`, `/private/tmp/DEF-622-transport-fix-verificatie.log`.

## Review en dispositie

1. **Important, fix nu → gesloten.** Lege recordcategorie/id lieten conflicterende caller-metadata staan, waardoor een duplicaat met juiste context via de verkeerde categorie gemist kon worden. Fix 3d4b98507 overschrijft ook ontbrekende recordwaarden, inclusief ontologische-categorie-fallback. Reviewer reproduceerde de oorspronkelijke situatie op commitcode en bevestigde correctie.
2. **LOW, fix nu → gesloten.** De oorspronkelijke test onderscheidde een diepe kopie niet van een oppervlakkige kopie. De versterkte test laat een servicedubbel geneste lijsten en options muteren. Reviewer bevestigde dat de regressietest op oude code faalt en een oppervlakkige kopie de test laat falen.

Gerichte deltareview: beide eerdere bevindingen opgelost, geen nieuwe bevestigde regressies in `09b0d6ff2..3d4b98507`. Vier transporttests via `git show`-geladen commitcode, uitsluitend in geheugen, met gestubde schema-/voortgangsadapters. De aanvullende desktoprun gebruikt de gewone pytest-route met offline-bootstrap. Geen gebruikersdatabase gebruikt.

## Controles

De eerste commit gebruikte ongevraagd `SKIP=validate-juridische-synoniemen`. De coördinator heeft verdere skips verboden en de check alsnog uitgevoerd: exit 0, 0 fouten, 36 waarschuwingen. De fixcommit draaide de synoniemencheck zonder SKIP: Passed. Log van de afzonderlijke controle: `/private/tmp/DEF-622-synoniemen-check.log`.

De ontbrekende lokale check-silent-exceptions-hook is pas na apart expliciet akkoord van Chris ongewijzigd gekopieerd; SHA-256 c80c8aa58688d826f0c824aa7a17ea6daf7093f0170c3666b9974fbc88ebcd31. Functionele verificatie: normale Edit-input exit 0, brede stille exceptie exit 2. Er is geen controle uitgeschakeld.

## Beperking

CON-01-oordeel, scores, opslag/readback, duplicaatkeuzes, handmatige expertbeoordeling en vaststelling/export behoren tot de vervolgstappen. De transportreview keurt die nog niet goed. Het verzoek om nu zichtbare CLI-vensters te regelen is door Chris ingetrokken; zichtbaar meekijken via VS Code blijft een voorkeur voor een volgende sessie, via een nog te verifiëren ondersteunde route.
