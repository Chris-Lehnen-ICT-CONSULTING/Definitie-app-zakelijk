# DEF-743 — technische oplevering CON-02

15 september 2026. Implementatie in `feature/DEF-743-con02-bronbasis`, gebaseerd op `dc7a70e80a47b750d8800c334805a968857bbd7b`. De wijzigingen zijn **niet gecommit, gepusht of gemerged**. De actieve werkboom en het auditdossier zijn behouden.

## Uitkomst

De drie goedgekeurde keuzes zijn geïmplementeerd. Claude Code CLI schreef de code en tests; Codex CLI voerde onafhankelijke reviews uit. Codex en Claude Cowork leverden het eerder afgeronde onderzoek en de analyse. Alle concrete technische reviewbevindingen zijn verwerkt en gesloten. Deskundige inhoudelijke acceptatie staat nog open; daarom blijft DEF-743 In Progress.

| Goedgekeurde keuze | Geïmplementeerd gedrag |
| --- | --- |
| Onderbouwde bronuitzondering | CON-02 beoordeelt brongezag/toepasselijkheid, betekenissteun en verwijskwaliteit afzonderlijk. Een referentie-uitzondering vraagt een bewaarde bronversie, stabiele identificatie, exacte vindplaats en expliciete deskundige acceptatie met actor en motivering. Een bruikbare interne verwijzing volstaat. De uitzondering blijft zichtbaar en wordt geen gewone positieve beoordeling. Ook expliciet gedocumenteerd ontbreken van een passende bron en correctie van één onderdeel zijn vastgelegd. |
| Herstel alleen op verzoek | Eén duurzame voorstelpoging per oorspronkelijke generatie. Diagnose en gebonden bewijs gaan vooraf aan reservering en modelaanroep. Het voorstel staat los van de oorspronkelijke tekst. Alleen expliciet toepassen schrijft de kandidaat na herbeoordeling op; versieconflicten, onopgeslagen wijzigingen, ongeldig bewijs en technische fouten blokkeren. De oorspronkelijke tekst, voorstellen en deskundigenreviews blijven in de historie. |
| Geen totaalcijfer | De weergave en export tonen beoordelingen per regel, dekking, onbekende/foutuitkomsten en uitzonderingen. CON-02 telt niet mee in categorie- of totaalscore. Er wordt geen vervangend gedeeltelijk kwaliteitscijfer gepresenteerd. Classificatie- en zoekmatchmetingen behouden hun eigen betekenis. |

### Bewijs door de keten

Bronidentiteit, versie, inhoud, vindplaats en werkelijk meegestuurde passages worden bewaard en gekoppeld aan de beoordeelde definitie en context. De bronbeoordeling gebruikt de bestaande AI-service en modelrouter. Niet-geleverde, afgekorte, tegenstrijdige of onleesbare informatie krijgt een expliciete uitkomst. Een oud sessieoordeel wordt opnieuw bepaald met de actuele opgeslagen deskundigenreview en recordversie. Opslaan, opnieuw laden, de editor en JSON/TXT-export gebruiken hetzelfde contract. Historisch ontbrekend bewijs wordt niet achteraf verzonnen.

De drie bijbehorende definitie-skills en hun canonieke ZIP-exporten zijn aangepast in de aparte werkboom `feature/DEF-743-con02-skills`:

`/Users/chrislehnen/Projecten/_claude-global-setup/.worktrees/DEF-743-con02-skills`

Daar zijn zes Markdown-bestanden en drie ZIP-bestanden gereviewd. De negen SHA-256-hashes zijn bij oplevering opnieuw gecontroleerd. De wijzigingen zijn nog lokaal; geen live synchronisatie, installatie of upload uitgevoerd.

## Eindverificatie

Alle onderstaande uitkomsten gelden voor dezelfde 82 gewijzigde code-, test- en contractbestanden. De SHA-256-manifesten vóór en na de eindrun zijn identiek.

| Controle | Resultaat |
| --- | --- |
| Canonieke `make test-cov-ci` | **5.807 geslaagd**, 75 overgeslagen, 721 buiten de unitselectie, 1 verwachte mislukking en 21 geslaagde subtests; exit 0. Duur 379,20 seconden. Dit is dezelfde volledige unitselectie, inclusief langzame tests, als `make test`, aangevuld met de coveragegrens. |
| Unitcoverage | **61,13%**, boven de vereiste 45%; 24.789 van 40.548 regels geraakt. |
| Echte offline kernjourney | **3 geslaagd**, exit 0. Generatie, bewerken, review, bronuitzondering, status/versie teruglezen en export worden doorlopen. |
| Ruff en Black | Schoon voor productiecode en configuratie; 390 bestanden gecontroleerd. |
| Mypy | **0 fouten**. |
| Complexiteitsgrens | **194**, toegestaan maximaal 201. Geen grens verhoogd of controle onderdrukt. |
| Overige gecontroleerde grenzen | Verweesde modules 0; stille foutafhandeling 55 bij grens 57; mypy-uitzonderingslijst 2; alle 421 testbestanden hebben markers; blokkerende grep-bevindingen 0. |
| Diffcontrole | `git diff --check`: exit 0. |
| Skills | 80 gerichte checks geslaagd; negen definitieve artefacthashes gelijk aan het gereviewde manifest. |

De gerichte tests bevatten echte Streamlit AppTests voor voorstel aanvragen/toepassen/herladen, behoud van onopgeslagen invoer, deskundigencorrecties en bronweergave. De eerdere pakkettestaantallen overlappen en zijn niet bij de bovenstaande totale unituitkomst opgeteld.

De eindrun had bestaande en nieuwe waarschuwingsuitvoer (onder andere resource- en deprecationmeldingen). Er is geen waarschuwingsvrije of volledige externe integratieclaim. De 75 skips en 1 xfail zijn in de onverkorte testlog bewaard; voor deze oplevering zijn geen tests overgeslagen om een fout te verbergen.

### Onafhankelijke sluitreviews

- [Bronkern — functionele review](reviews/C-bronkern-sluitreview.md), [laatste kwaliteitsdelta gesloten](reviews/C-kwaliteit-sluitreview.md).
- [Opslag — functionele review](reviews/D-opslag-sluitreview.md), [kwaliteit en exportfixture gesloten](reviews/D-kwaliteit-sluitreview.md).
- [Editor — laatste kwaliteitsdelta gesloten](reviews/F-kwaliteit-sluitreview.md); eerdere Apply-, cache-, claim- en bronweergavebevindingen zijn daarin behouden als gesloten.
- [Prompts](reviews/E-prompt-sluitreview.md) en [skills](reviews/G-skills-review.md).

De reviewers controleerden code en bewaarde testbewijzen met eigen begin- en eindhashes. De gecombineerde eindtests zijn daarnaast door Codex uitgevoerd. Na de laatste twee gerichte correcties is opnieuw de gehele canonieke unit/coveragecontrole gedraaid; eerdere rode of gestopte runs gelden niet als opleverbewijs.

## Grenzen en resterende acceptatie

1. **Deskundige goldsetacceptatie is niet uitgevoerd.** De 94 geregistreerde scenario’s zijn ontwerpen, geen 94 uitgevoerde deskundigentests. De technische tests gebruiken waar nodig gecontroleerde AI-antwoorden; ze bewijzen geen kwaliteit van live modeloordelen.
2. **De algemene vaststelpoort bij ontbrekende score blijft de aparte DEF-630-afhankelijkheid.** Deze is niet omzeild. De offline journey controleert zowel de CON-02-blokkade/uitzondering als het behoud van deze algemene poort en de rolcontrole.
3. **Lokale runtime:** Python 3.13.15, pytest 9.0.3, coverage 7.12.0 en Streamlit 1.58.0. De AppTests zijn dus geen bewijs voor de exact vastgepinde Streamlit 1.62-omgeving. Ruff 0.16.5 en mypy 2.3.1 zijn wel met de projectpins gedraaid in een tijdelijke omgeving; projectdependencies zijn niet gewijzigd.

Er is geen SQL-migratie toegevoegd. De eerder bestaande ontbrekende `definitie_drafts`-tabel in een verse schemaopzet is niet als onderdeel van dit broncontract aangepast. Ontbrekende historische passages of beoordelingen blijven zichtbaar onbekend; een bewaard receipt is geen cryptografische attestatie tegen een volledig herschreven opslagdocument.

## Bewijsbestanden

- [Bestandshashes van de definitieve implementatie](implementatie-sha256-20260915-v1.json).
- [Gecomprimeerd verificatiebewijs](verificatie-20260915-v1.zip): onverkorte definitieve test- en kwaliteitslogs, exitcodes, JUnit, coverage-XML, testinventaris en begin/eindmanifesten. Alle 15 opgenomen bestanden en de ZIP zijn op integriteit gecontroleerd.
- ZIP SHA-256: `436368746b2170125467d125432cbd962293bfa5a0441f3195b5e202f231febf`.
- [Goedgekeurde beslissingen](besluiten-20260915-v3.md), [implementatieplan](implementatie-20260915-v1.md) en [onderzoekssynthese](synthese-v2.md).

[DEF-743 in Linear](https://linear.app/definitie-app/issue/DEF-743/story-implementeer-con-02-bronbasis-betekenissteun-en-herleidbare) blijft open voor de genoemde acceptatie. Voortgangsregistratie volgt het issue-workflow-protocol.
