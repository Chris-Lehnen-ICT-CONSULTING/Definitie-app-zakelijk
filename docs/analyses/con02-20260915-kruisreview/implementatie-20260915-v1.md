# DEF-743 — uitvoering na de drie besluiten

Leidend: synthese-v2.md plus besluiten-20260915-v3.md. Chris gaf na de keuzes opdracht: “ok implementeer nu”. Het onderzoek met Cowork is afgerond; dit document volgt de implementatie. Een technische test is geen deskundige acceptatie van de norminterpretatie of meting van modelkwaliteit.

## Werkverdeling

| Pakket | Verantwoordelijkheid | Stand |
| --- | --- | --- |
| A/B | Korte geselecteerde documenten, brontransport, neutrale bestaande bronweergave | Geïmplementeerd en onafhankelijk gereviewd; bewijs in uitvoering-v1.md |
| C | Broncontract, drie deelbeoordelingen, AI-gronding, actieve evaluator, geen cijfer, validatie-ingangen | Claude Code CLI voert uit |
| E | Generatie-instructies en bewijs van daadwerkelijke promptopname na budgettering | Claude Code CLI voert uit |
| D | Duurzaam bron-/beoordelingsbewijs, versiegebonden deskundige uitzondering, herladen en export | Claude Code CLI voert uit |
| F | Editorpariteit, deskundigenbediening, voorstel op verzoek en hertoets, status-/dekkingweergave | Aansluiten na publicatie van de gedeelde interfaces |
| Integratie | Onafhankelijke Codex CLI-review, gerichte herstelronde indien nodig, relevante ketentests en volledige unit-/lintgate | Na integratie van de pakketten |

Claude Code CLI schrijft app- en testcode. Codex coördineert, analyseert de bestaande aansluitingen en controleert bewijs; Codex CLI doet de onafhankelijke code-review. De actieve CLI-sessies hebben alleen Read/Glob/Grep/Edit/Write/Bash en geen MCP- of delegatietools.

## Te bewijzen ketens

- Geselecteerde bron en feitelijk gebruikte promptpassage blijven onderscheiden, inclusief weglating door budget of technische fout.
- Dezelfde kandidaat, drie contextlijsten en bronversies bereiken generatievalidatie en beide editorroutes.
- Brongezag/toepasselijkheid, betekenissteun en verwijskwaliteit houden elk hun status, bewijs en onzekerheid; een fail wist open onderdelen niet.
- Een bronwoord, hoge zoekscore of aanvoerroute levert geen pass; verzonnen bron-ID's of citaten worden geweigerd.
- ID-only herladen en individuele/beheerexport halen hetzelfde bewijs uit de opslag, zonder generatiesessie.
- Tekst-, context- of bronwijzigingen maken eerdere beoordeling herkenbaar verouderd; eerder bewijs blijft bewaard.
- Een deskundige uitzondering heeft actor, reden, actuele binding en noodzakelijke bron- of zoekgegevens; zij is geen gewone positieve bronbeoordeling.
- Een voorstel ontstaat alleen op verzoek, blijft afzonderlijk van de oorspronkelijke tekst en wordt alleen op gebruikerskeuze toegepast met hertoets en versiecontrole.
- De gebruikersweergave toont regeloordelen en beoordelingsdekking zonder totaalcijfer of vervangende deelscore.

## Bestaande grenzen

Geen automatische CON-02-herstelactivatie. De maximale ene repaircall en DEF-606-volgorde blijven intact. Gedeelde algemene snapshot-, score- en vaststelpoortontwikkeling blijft bij de bestaande eigenaren; de aansluiting voor CON-02 wordt gericht uitgevoerd. Bestaande score-afhankelijke vaststelblokkades mogen niet stil worden weggehaald om een positieve demo te verkrijgen.

De 94 onderzoeksscenario's zijn geen 94 uitgevoerde tests of deskundige goldset. Technische uitvoering en resterende inhoudelijke acceptatie worden bij oplevering afzonderlijk gerapporteerd. Geen productie- of geïnstalleerde-releaseclaim zonder afzonderlijk uitvoeringsbewijs.
