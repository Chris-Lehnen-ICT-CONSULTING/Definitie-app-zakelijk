# Herbruikbare startopdrachten voor toetsregelonderzoek

Gebruik de Codex-opdracht voor één volledig onderzoek. Vul de invoervelden in uit de gebruikersopdracht en geverifieerde projectinformatie; stel alleen vragen over wat werkelijk ontbreekt. De korte startzin hieronder is ook bruikbaar. Codex maakt daarna de concrete Cowork-overdracht. Deze templates voorbereiden of aanpassen start geen sessies en verstuurt geen berichten.

## Korte startzin

> Onderzoek {REGEL-ID} met $toetsregel-onderzoek. Voer het volledige onderzoek samen met Claude Cowork uit, inclusief onafhankelijke eerste onderzoeken, wederzijdse review, verwerking door beiden en synthesecontrole. Gebruik het bestaande dossier en actuele besluiten. Organiseer de Cowork-overdracht volgens de startprocedure van de skill en werk binnen mijn gegeven toestemming. Lever concrete verbeteringen en beslispunten; implementeer niets.

## Codex — volledige startopdracht

```text
Lees tevens references/genereren-en-toetsen.md uit dezelfde skillmap. Werk binnen Q1–Q6 voor de actieve regel de gemeenschappelijke norm, veldrollen, generatie-instructie (G), toetsinstructie (T), begrensde terugkoppeling (H) en gekoppelde acceptatiegevallen uit. Beoordeel in de kruisreview en synthesecontrole expliciet de aansluiting tussen G en T en herstel zonder betekenisverlies. Bij bestaand afgerond onderzoek behandel je alleen de ontbrekende aanvulling; behoud de besluiten en eerdere bewijsgrenzen.

Onderzoek {REGEL-ID} in {PROJECT}. Gebruik $toetsregel-onderzoek en lees de actuele SKILL.md, references/werkcontract.md en references/startopdracht.md. Gebruik de werkelijk geïnstalleerde skilllocatie; op deze Mac is dat /Users/chrislehnen/.codex/skills/toetsregel-onderzoek/.

Invoer:
- Projectmap: {PROJECTMAP}
- Bestaand regeldossier en relevante kaders/besluiten: {BRONPADEN}
- Gedeelde onderzoeksmap: {WERKMAP}
- Cowork-sessie: {BESTAANDE SESSIE OF NOG AAN TE WIJZEN}
- Mijn toestemming voor Cowork: {REEDS GEGEVEN TOESTEMMING OF NOG TE REGELEN}

Dit is volledig onderzoek door Codex én een afzonderlijke Claude Cowork-sessie. Codex coördineert. Gebruik de aangewezen sessie en draag taakrelevante opdrachten en bestanden over voor zover ik dat heb toegestaan. Als ik het starten van een nieuwe Cowork-sessie al heb toegestaan, voer dat uit met beschikbare toegestane middelen. Vraag niet opnieuw om gegeven toestemming. Ontbreekt toegang of toestemming: maak eerst een ingevulde Cowork-opdracht en een concrete gedeelde feitenbasis, en leg vroeg precies de ontbrekende actie aan mij voor. Schakel niet stil over op alleen Codex en hergebruik geen Cowork-sessie van een andere regel.

Begin met bestaande dossiers en rechtstreeks relevante actuele besluiten. Hergebruik geldig bewijs en verdiep open vragen, tegenstrijdigheden en ontbrekend bewijs. Alleen deze regel is actief; voorstellen uit andere dossiers zijn geen goedgekeurde norm. Beantwoord Q1–Q6 uit de skill zelfstandig. Bewaar beide volledige eerste onderzoeken voordat jullie nieuwe conclusies uitwisselen. Een bestaande Codex-v1 kan behouden blijven; geef Cowork dan eerst alleen dezelfde historische feitenbasis.

Voer daarna de wederzijdse review uit: ieder beoordeelt het volledige onderzoek en relevante bijlagen van de ander, en ieder verwerkt alle ontvangen punten zichtbaar. Codex maakt de geïntegreerde synthese; Cowork controleert die; Codex verwerkt die controle. Controleer werkelijke ontvangst bij elke overdracht. Gebruik één geïntegreerd casusregister met stabiele IDs. Lever concrete voorstellen voor regeltekst, appgedrag, meldingen, skills/prompts en acceptatie, met een korte besluitnotitie.

Een volledige oplevering vereist beide onderzoeken, beide reviews, beide verwerkingen en de verwerkte Cowork-synthesecontrole. Bij een ontbrekende bijdrage: hervatbare tussenstand met exacte blokkade en volgende actie. Bij hervatten werk je verder vanaf de laatst bewezen fase; geen onnodige nieuwe algemene reviewronde.

Dit is onderzoek en een besluitvoorstel. Implementeer niets, wijzig geen bestaande app/regels/skills, maak geen issues, PR of automatisering en ga niet naar een volgende regel. Bewaar nieuwe onderzoeksversies met behoud van eerdere bijdragen en de gebruikerswerkboom.
```

Bij het invullen van toestemming kan de gebruiker bijvoorbeeld expliciet kiezen: “Gebruik sessie {SESSIE} en wissel daar de taakrelevante onderzoeksopdrachten en bestanden uit”, of “Start voor deze regel één nieuwe Cowork-sessie en wissel daar de taakrelevante onderzoeksopdrachten en bestanden uit.” Neem zulke toestemming niet zelf aan of over uit een opdracht voor een andere regel.

## Cowork — opdracht voor de onafhankelijke tweede lijn

Codex vult onderstaande opdracht volledig in en levert de genoemde bestanden daadwerkelijk mee of maakt ze leesbaar via de gedeelde map. Geen oningevulde velden naar Cowork sturen. Voeg de volledige skill met referenties toe wanneer die daar niet is geïnstalleerd. Gebruik bij hervatten alleen de nog open fase.

```text
Lees tevens references/genereren-en-toetsen.md uit dezelfde skillmap. Werk binnen Q1–Q6 voor de actieve regel de gemeenschappelijke norm, veldrollen, generatie-instructie (G), toetsinstructie (T), begrensde terugkoppeling (H) en gekoppelde acceptatiegevallen uit. Beoordeel in de kruisreview en synthesecontrole expliciet de aansluiting tussen G en T en herstel zonder betekenisverlies. Bij bestaand afgerond onderzoek behandel je alleen de ontbrekende aanvulling; behoud de besluiten en eerdere bewijsgrenzen.

Onderzoek {REGEL-ID} in {PROJECT} als afzonderlijke Claude Cowork-onderzoeker. Codex voert parallel een eigen onderzoek uit en coördineert de uitwisseling. Lees de bijgeleverde toetsregel-onderzoek/SKILL.md en references/werkcontract.md en pas die inhoudelijk toe.

Jouw toegang:
- Project/bronmap in jouw omgeving: {COWORK-PROJECTPAD}
- Gedeelde onderzoeksmap in jouw omgeving: {COWORK-WERKMAP}
- Historische dossiers, actuele besluiten en bronversies: {CONCRETE BRONNENLIJST}
- Codex-sessie en overdrachtsroute: {IDENTITEIT EN ROUTE}
- Huidige fase en jouw eerstvolgende bijdrage: {FASE EN BIJDRAGE}

Controleer toegang tot de genoemde bestanden en meld exact wat niet leesbaar is. Een pad op de computer van Codex bewijst geen toegang vanuit Cowork.

Voor jouw eerste onderzoek: beantwoord Q1–Q6 uit de skill zelfstandig op basis van de gedeelde historische bronnen en actuele besluiten. Bewaar jouw volledige eerste versie vóór het lezen van nieuwe Codex-conclusies, kruisreviews of synthese. Lees die pas nadat beide eerste versies opgeslagen zijn. Werk concrete voorstellen uit voor norm, appgedrag, meldingen, skills/prompts en onderscheidende acceptatiegevallen; scheid feiten, besluiten, interpretaties en voorstellen. Hergebruik geldig bewijs. Geef bestand, versie en relevante bijlagen door via de afgesproken route.

Na de expliciete overdracht van beide eerste versies review je het volledige Codex-onderzoek en relevante bijlagen. Lever per punt: claim/versie, oordeel, bron of tegenbewijs, gevolg en correctie. Verwerk de ontvangen Codex-review op jouw onderzoek punt voor punt als overgenomen, gedeeltelijk overgenomen, afgewezen met grond of open, met vindplaats in jouw herziene advies. Behoud jouw eerste versie.

Controleer daarna op verzoek de volledige Codex-synthese op weglatingen, correcte standpuntweergave, resterende tegenspraken en betekenisverlies. Lever concrete punten terug. Eén wederzijdse review en één synthesecontrole; alleen gerichte vervolgbeoordeling bij materiële wijzigingen. Ontbrekende bijdragen blijven open, beleidskeuzes zijn voor de gebruiker.

Onderzoek alleen {REGEL-ID}. Implementeer niets en wijzig geen app, regels, skills of bestaande onderzoeksversies. Maak geen issues, PR, andere sessies of automatisering. Meld per bijdrage de werkelijk opgeleverde bestanden en de volgende benodigde overdracht. Claim geen gezamenlijk afgerond onderzoek zolang een verplichte bijdrage of verwerking ontbreekt.
```
