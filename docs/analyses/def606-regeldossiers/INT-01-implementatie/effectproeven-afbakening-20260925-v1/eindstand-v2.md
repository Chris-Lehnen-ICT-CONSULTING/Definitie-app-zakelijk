# INT-01 — afbakeningen verwerkt; T24 en G24 geaccepteerd binnen de proefomvang

25 september 2026. De twee met Chris besproken afbakeningen zijn vastgelegd en doorgevoerd in de appregel en de toetsingsskill. De nieuwe onafhankelijke T24 haalt 24/24 volledige conformiteit. Het bestaande geslaagde G24-bewijs blijft geldig. Dit zijn kleine synthetische AI-proeven, geen menselijke validatie of garantie van algemeen foutloze generatie. Geen merge of live skillsactivatie uitgevoerd.

## Besluiten en bron

- Citaat zonder interne zinseindpunctuatie: een vervolg is op zichzelf geen reden voor doorverwijzing; concrete grenzen en afbreking behouden hun beoordeling.
- Onbekende afkorting aan het teksteinde zonder vervolg: onbekende betekenis geeft op zichzelf geen zinsstructuuronzekerheid. Toegankelijkheid hoort bij INT-07. Het punt bij een afkorting mét vervolg kan wel een onzekere grens zijn.
- [Gebruikersbesluiten](afbakening-besluit-v1.md) en [vooraf vastgesteld referentiecontract](referentie-contract-v1.md).
- Getoetste appbron: `3c2535361be6851a779372926302d1d027897d4b`; runtimecontract `def770-int01/10` ongewijzigd.
- Skillsbron: `263038b7cddcf9742a909bace86a03b2a7f254ad`.
- Leidende [runbinding v2](runbinding-v2.json), [bronfreeze v2](bronfreeze-v2.json) en [uitvoerbinding](bronbinding-v1.json). `runbinding-v1.json` en `bronfreeze-v1.json` zijn voorbereidingssnapshots van vóór de tekstafstemming en worden door deze versies opgevolgd. Hun oude bronverwijzing is geen verwijzing naar de uitgevoerde proef. Historische proefuitslagen en labels blijven intact.

## Uitvoering en onafhankelijke review

Claude Code CLI, sessie `442a98fb-a377-403f-996e-433cf4a664fc`, wijzigde uitsluitend de toelichting in INT-01.json en de overeenkomstige toetsingspassage in de skill. Runtimecode, tests, generatie-instructies en INT-07 zijn ongewijzigd. Dezelfde onafhankelijke Codex CLI-reviewer, sessie `01a0cfac-ea05-7700-ba73-8b5659751c1c`, controleerde met Astra/high de contractoverdracht, concrete tekstdiff en acceptatie-uitkomsten. [Tekstcorrectie](technisch-bewijs-v1/tekstafstemming-v1.patch), [reviewvrijgave](technisch-bewijs-v1/tekstafstemming-review-v1.md).

De genoemde LOW-registratiebevinding uit de acceptatiereview is verwerkt via `runbinding-v2.json`: juiste commit, archiefhash en skillscommit, expliciete opvolging van v1, criteria ongewijzigd. De uitvoer en referenties zijn niet gewijzigd. De gerichte sluitingscontrole staat na beschikbaarheid in `registratie-sluitingsreview-v1.md`.

## T24 — nieuwe onafhankelijke proef

Een nieuwe maker, twee afzonderlijke referentiebeoordelaars en een afzonderlijke adjudicator werkten in vier unieke Astra/high-sessies zonder tools. Bron en referenties zijn vóór appuitvoering verzegeld; geen open disputen. De bestaande offline runner voerde alle 24 gevallen uit op oude en nieuwe bron, via beide laadpaden en de gewone opslagroute.

- **24/24 evalueerbaar en volledig conform**, inclusief status, reden, grenspositie/passages en broncitaat.
- 11 zinsstructuur-passes, 7 fails, 5 doorverwijzingen, 1 lege tekst.
- 18/23 niet-lege gevallen automatisch beslist (78,26%); alle 18 normatief ondersteund.
- Oud naar nieuw: 14 verbeterd, 10 gelijk binnen de vergelijkbare zinsstructuur/diagnostiek; geen nieuwe zekere fout. Ontbrekende oude onderdelen zijn niet als gemeten inhoudelijk oordeel geteld.
- Beide laadpaden en opslag 24/24 consistent; oorspronkelijke tekst behouden; nul uitvoeringsfouten en nul volledige INT-01-passes. Compactheid en begrijpelijkheid blijven bij niet-lege teksten afzonderlijk inhoudelijk open.

Alle 24 rijen met motivering staan in de [onafhankelijke bewijsreview](t24-onafhankelijke-bewijsreview-v1.md); [ruwe nieuwe uitkomsten](t24-resultaat-nieuw-v1.json), [oude uitkomsten](t24-resultaat-oud-v1.json), [vergelijking](t24-vergelijking-v1.json), [voorafgaande verzegeling](t24-referenties-verzegeling-v1.json), [rollenbinding](rollenbinding-v1.json). Deze verse set bevat geen rechtstreeks nieuw geval van beide zojuist verduidelijkte categorieën; daarvoor wordt geen aanvullende afzonderlijke dekking geclaimd. De afbakeningen zijn wel vóór de proef in het referentiecontract vastgelegd.

## G24 en technisch bewijs

G24 blijft behouden: drie paren inhoudelijk beter, negen gelijk, geen waargenomen nieuwe betekenis-/bronfout of verslechtering. De zes volledige generatieprompts en API-verzoeken zijn exact gelijk; de getoetste tekstvariant bevat dezelfde 3322 reguliere archiefbestanden als de nieuwe commit. Runtime bleef gelijk, zodat het bestaande bewijs van 96 service-uitkomsten en 48 opslagcontroles geldig blijft. [Behoudbinding](g24-en-testbewijs-behoud-v1.json), [promptpariteit](technisch-bewijs-v1/promptpariteit-publicatie-v1.txt).

De eerdere beperkingen blijven gelden: gedeeld betekenisverlies G04 en actoronzekerheid G02. Geen nieuwe betaalde generatiecalls. Cumulatief generatiebudgetgebruik blijft US$7,533075 van US$8,10.

- Nieuwe gerichte appcontrole: **939 geslaagd, 5 overgeslagen**, nul fouten; exit 0. JUnit telt 944 totaal, niet 944 geslaagd.
- JSON, beide regellaadpaden en geraakte lint gecontroleerd; exit 0.
- Canonieke en aliasbundel opnieuw opgebouwd: **96 tests en 2 subtests geslaagd**. De aanvankelijke ene ZIP-driftfout is hiermee opgelost; de oorspronkelijke mislukte controle blijft zichtbaar in het bewijs.
- Eerder breed unitbewijs op runtime /10: 7567 geslaagd, 75 skips, één bestaande xfail en 21 subtests. Dit is behouden bewijs op ongewijzigde uitvoerbare code en tests, geen nieuwe volledige suite op de tekstcommit.

[Technische bewijsindex](technisch-bewijs-binding-v2.json). Actuele PR-/CI-status wordt bij publicatie afzonderlijk teruggelezen. Dit rapport voert geen merge uit en activeert geen skills; de bestaande activatiestop ALG-391 blijft gelden.

## Publicatiekopie van het pariteitslog

De geheimenscanner blokkeerde zes waarden in het oorspronkelijke pariteitslog. Alle zes zijn zelfstandig herberekend als SHA-256-vingerafdruk van de synthetische API-verzoekbody. Voor publicatie zijn uitsluitend die zes waarden zichtbaar geredigeerd; alle overige bytes en uitkomsten blijven gelijk. Het origineel blijft lokaal bewaard. Scannerconfiguratie, allowlist en hooks zijn ongewijzigd. [Redactiebinding](publicatie-redactie-v1.json). Deze eindstand v2 en technische bewijsbinding v2 volgen de eerdere versies op; v1 verwees nog naar het uitsluitend lokaal bewaarde oorspronkelijke pariteitslog.
