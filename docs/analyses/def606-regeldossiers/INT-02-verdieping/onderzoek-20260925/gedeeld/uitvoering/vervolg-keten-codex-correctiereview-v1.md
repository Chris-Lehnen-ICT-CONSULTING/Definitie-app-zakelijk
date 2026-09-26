**V2 sluit de eerdere bevindingen gedeeltelijk. Twee bewijsleemten blijven open; ik constateer geen nieuwe productiecoderegressie.**

1. **Schrijfroute — gedeeltelijk gesloten.** Route B voert daadwerkelijk een bestaande productieschrijfroute uit op synthetische SQLite en leest de voorstelregistratie terug. Dit betreft toepassing van een CON-02-bronvoorstel, zoals het rapport nu correct onderscheidt.

   **Resterend, middel:** de conclusie onder ‘Gewone opslag’ in [rapport-v2.md:58](/Users/chrislehnen/Projecten/Definitie-app/docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/vervolg-keten-rapport-v2.md:58) presenteert een opslagleemte als aangetoond. Route A schrijft echter geen validatieresultaat en onderzoekt daarmee niet of gewone opslagroutes dat kunnen bewaren.

   **Minimale correctie:** formuleer: “Route A schrijft geen validatieresultaat; behoud bij gewone opslag is niet onderzocht. Route B bewijst opslag bij toepassing van een bronvoorstel.”

2. **RR/NE-controle — gedeeltelijk gesloten.** De herhaalde validatie in route A vergelijkt nu status, reden, signalen en deelmelding. Het eerdere `None==None`-probleem is daar verholpen. In de geldige JSON komen ook de teruggelezen INT-02-velden van route B voor alle drie casussen overeen met de verse uitkomst, inclusief de exacte NE-melding.

   **Resterend, belangrijk:** [replay-v2.py:256](/Users/chrislehnen/Projecten/Definitie-app/docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/vervolg-keten-replay-v2.py:256) controleert uitsluitend de verse uitkomst. De teruggelezen registratie wordt vastgelegd, maar niet gecontroleerd of vergeleken. Bovendien leveren niet-uitgevoerde routes op regels 241–248 geen fout op; de aggregatie op [regel 294](/Users/chrislehnen/Projecten/Definitie-app/docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/vervolg-keten-replay-v2.py:294) behandelt ontbrekende fouten als groen.

   Een kleine diagnose met uitsluitend de bestaande exitlogica bevestigt: ontbrekende teruggelezen registratie, een verkeerde teruggelezen NE-melding en `uitgevoerd=False` blijven alle drie exitstatus 0 opleveren. De claim “De proef faalt bij afwijking” dekt terugleesbehoud dus niet.

   **Minimale correctie, na autorisatie:** laat niet-uitgevoerde route B falen en controleer de teruggelezen vier INT-02-velden tegen verwachting én verse uitkomst. Tot die tijd mag het rapport uitsluitend spreken van **waargenomen gelijkheid in deze run**, niet van een automatische terugleescontrole.

3. **UI-/poort-/exportclaims — gesloten.** Het rapport begrenst het bewijs nu terecht tot rendererfunctie, preview en uitgevoerde exportroutes. Er is geen browser-, knop- of succesvolle-vaststellingbewijs. De geteste expertlezing en recordexport tonen het bewaarde voorstelresultaat niet als INT-02; expliciet aangeleverde `toetsresultaten` brengen INT-02 wel in de JSON-export. Export zonder gate blijft expliciet diagnostisch.

De synthetische isolatie en genoemde FakeAI/FakeBronbeoordeling-grenzen passen bij de proef. Het losse `int02/opslag.py`-voorstel is terecht teruggetrokken ten gunste van een afzonderlijk gedeeld DEF-626-ontwerpbesluit.

Alle vier opgegeven SHA-256-identiteiten komen overeen. App-HEAD is `e9a865b856ca6dba85ee73bedc0e303f05fa86fb`; src/tests zijn onveranderd sinds `9ff3eac1`. Skill-HEAD is ongewijzigd. De geldige run2 en lintlogs zijn gebruikt; geen brede suite uitgevoerd. De omvangmeting bevestigt 165 gewijzigde coderegels en 273 totaal. Deze review verleent daarvoor geen opnameakkoord.

**Voor het merge-/uitrolvoorstel:** de proef ondersteunt de concrete waarnemingen hierboven, maar nog geen volledig gesloten ketenacceptatie of algemene opslagverliesclaim. De eerdere productiecodereview blijft geldig; corrigeer de resterende bewijsclaims voordat v2 als afgerond acceptatiebewijs wordt gebruikt.

Sessie: `01a0dc44-26c6-7de3-b2f9-b0f79e5a27ff`.