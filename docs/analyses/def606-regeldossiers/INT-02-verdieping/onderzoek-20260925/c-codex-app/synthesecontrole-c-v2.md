# INT-02 — gerichte synthesecontrole C v2

25 september 2026 · DEF-771 · onderzoeker C.

**Eindoordeel: het gezamenlijke onderzoek A+B+C kan inhoudelijk worden afgerond met de door Chris besliste K1–K5 (inclusief K2b) en de expliciete bewijsleemten. SC-C-02 is gesloten; geen materieel onderzoekspunt resteert.** Niet alle redactionele correcties zijn volledig verwerkt: SC-C-09, SC-C-10 en SC-C-12 zijn gedeeltelijk verwerkt. De hieronder aangegeven tekstcorrecties zijn bestemd voor de coördinator vóór publicatie; dit is geen onvoorwaardelijke goedkeuring van iedere formulering in v4.

## Controlebasis

[Eigen synthesecontrole v1](synthesecontrole-c-v1.md) volledig gelezen; daarna de [verwerking door de coördinator](../a-cowork/verwerking-synthesecontrole-c-v1.md) en gericht de wijzigingen en betrokken passages in:

- **S:** [gezamenlijke synthese v4](../gedeeld/gezamenlijke-synthese-v4.md).
- **D:** [besluitnotitie v4](../gedeeld/besluitnotitie-chris-v4.md).
- **R:** [gezamenlijk casusregister v4](../gedeeld/gezamenlijk-casusregister-v4.md).
- **B:** [besluiten Chris v1](../gedeeld/besluiten-chris-v1.md), uitsluitend voor de scheiding tussen vastgelegd besluit en onderzoeksvoorstel; de keuzes zelf zijn niet beoordeeld.

Vindplaatsen hieronder zijn fysieke regelnummers in deze versies, naast sectie/rij. Geen tweede volledige review, nieuw brononderzoek, nieuwe proeven of herbeoordeling van eerder gesloten inhoud. Alle dertien bestanden uit manifest-c-v2 hebben nog hun geregistreerde hash: het eerdere C-bewijs blijft bruikbaar binnen zijn oorspronkelijke bereik. De onderzoeksbestemming is expliciet door de opdracht bevestigd.

## Per SC-C-punt

| Punt | Traceerbaar en zonder betekenisverlies? | Exacte vindplaats en oordeel |
|---|---|---|
| SC-C-01 | **Ja** | S §2:28–36, §4:55 en §6:75–88. Norm en beschrijvende uitzonderingen behouden; geen nieuwe inhoudelijke wijziging vereist. |
| SC-C-02 | **Ja** | S §3:42/44, §6:88, §9:115; D “Prompt en skills (G)”:38. G en de skillzin bevatten de gevraagde functiegrens en beschermen kwalitatieve/constitutieve kenmerken. Zie de expliciete casuscontrole hieronder. |
| SC-C-03 | **Ja** | S §4:55: “de regeluitkomst blijft dan VN en andere open punten worden erbij vermeld”. De toevoeging behoudt de grond voor VN en onderscheidt haar van O, NE en E. |
| SC-C-04 | **Ja** | S §5:69 bevat “onbesliste toepasselijke normkeuze” als stopreden. De eerdere betekenisbescherming blijft intact. Het nieuwe K5-kader op regel 65 vraagt wel terminologische verduidelijking; zie V4-C-01. |
| SC-C-05 | **Ja** | S §10:121, D “Bewijsgrenzen”:61, R “Niet gemeten / beperkt gemeten”:100. P5 is een geëxtraheerde UI-helper met geïnjecteerd resultaat; P6 een geïsoleerde gate met vervangen hulpfuncties/interfaces. Score 0,9 met/zonder reviewitem gelijk; None blokkeert. Geen volledige route-, scherm-, bevoegdheids- of databaseclaim. |
| SC-C-06 | **Ja** | S §1:19 en D “Geparkeerd”:57. Herlaad-/exportgrenzen en DEF-626 blijven staan; parkeren sluit uitvoeringsacceptatie niet. Geen nieuwe correctie. |
| SC-C-07 | **Ja** | R-C108:80: “een onder de gekozen norm zelfstandig aangetoonde overtreding blijft VN, met de overige open punten erbij”. De variantbeperking is expliciet; C100–C118 blijven aanwezig (R:72–90). |
| SC-C-08 | **Ja** | S §6:80 en R-C02:16 zijn inhoudelijk ongewijzigd ten opzichte van de gecontroleerde v3. Bronlabel, voorschriftlezing en variantverwachting blijven onderscheiden. |
| SC-C-09 | **Gedeeltelijk** | S §9-kop:100, standpuntalinea:117, signaalrij:111 en §4:61 zijn juist. C staat nu in de Kern-kop (§1:22), N-breed-voorkeur (§2:30) en O1-voorkeur (§4:48/51). D:30/44 en R:5 missen C nog. Nergens wordt C een S1- of vervangen-voorkeur toegeschreven. Exacte aanvulling hieronder. |
| SC-C-10 | **Gedeeltelijk** | D:5–16 scheidt de genomen besluiten als tabel af; concordantie:53 en bestaand beleid/geparkeerd:55–57 behouden de eerder gecontroleerde inhoud. De kop “Voorstel”:30 is herkenbaar, maar “Jouw keuzes”:42 en actuele bewoordingen in 47/50/55 botsen redactioneel met de nieuwe tabel. Zie V4-C-02; geen beoordeling van Chris’ keuzes. |
| SC-C-11 | **Ja** | S §7-kop:92 luidt “Relaties en resterende buurregelspanning”; §7:94 en R-C116:88 behouden de ESS-04-spanning zonder INT-02-uitzondering of criteriumverwijdering. |
| SC-C-12 | **Gedeeltelijk** | S §1:13 en R-samenvatting:94 bevatten P1–P6, inclusief P2, en P0 als historisch hergebruik; 76 = 57 + 19. S §13:142 noemt 19 nieuwe casussen naast zes historische. D-inleiding:3 houdt echter “19 casussen”; D:22 noemt alleen de eerdere 45 + 2 waarnemingen. Exacte aanvulling hieronder. |
| SC-C-13 | **Ja** | S §10:121 maakt de verwachting-/exitbeperkingen lijnspecifiek; C’s exit 0, uitgevoerd=true, tijden en opzethash zijn lokaal, niet extern geattesteerd bewijs. P3 bewijst regelvelden, niet de gehele-runstatus; oldid 8695 is niet aantoonbaar gelijk aan de snapshot. D:61 en R:100 wissen P5/P6 niet langer uit en voegen geen sterkere bewijsclaim toe. |
| SC-C-14 | **Ja** | S §8:98 noemt C’s twaalf G-scenario’s × drie runs en vier ongebruikte gevallen, de keuze voor twee runs/minimaal zes hold-outs zonder bewezen equivalentie, verplichte dekking C105/C107/C112/C115/C116 en fout-/bindingsacceptatie C117/C118. Eigenaar en selectie blijven vóór uitvoering vast te leggen. |

### SC-C-02: expliciete functie- en casuscontrole

S-G:42 verbiedt een discretionaire beslisregel **die voorschrijft** en beschermt het beschreven kwalitatieve/constitutieve kenmerk; dat sluit aan op N:28 en T:55. De zelfstandig over te nemen skillzin (S:88) zegt eveneens dat menselijke beoordeling op zichzelf geen beslisregel is. D:38 neemt die begrenzing over. S:44 voegt C107 als G-toetsgeval toe en §9:115 registreert de correctie.

R-C107:79 blijft O bij onduidelijke functie, zonder verzonnen numerieke grens. G schrijft behoud van het constitutieve oordeel voor, geen automatische V bij functietwijfel. R-C101:73 blijft VN onder beide varianten **bij de discretionaire instructiepremisse**; C102:74 en C105:77 blijven alleen onder N-breed VN. De G-correctie verliest dus geen overtredingsgeval en introduceert geen verbod op louter menselijke beoordeling.

### Resterende exacte correcties SC-C-09 en SC-C-12

**SC-C-09 — coördinator, redactioneel vóór publicatie:**

- D:30 vervangen door `## Onderzoeksvoorstel vóór de besluitvorming (A, B, coördinator en C eens over de hoofdlijn)`.
- D:44 kolomkop `Voorkeur A+B` vervangen door `Onderzoeksvoorkeuren (A, B, CO en C; verschillen per rij)`; in K2b:48 toevoegen: `C legt geen voorkeur voor S0, S1 of vervangen vast; signalen zijn uitsluitend passagehulp.` Daarmee wordt de signaalkeuze niet alsnog gezamenlijk toegeschreven.
- R:5 vervangen: `voorkeur van A, B en CO` → `voorkeur van A, B, CO en C`.

**SC-C-12 — coördinator, redactioneel vóór publicatie:**

In D:3 vervangen: `6 proeven, 19 casussen` → `6 proeven en 19 nieuwe casussen, naast zes historische casussen in C’s eigen register`.

Vervang in D:22 de twee zinnen vanaf “Gemeten op main:” door:

> Gemeten op main: A+B+CO: 45 servicewaarnemingen over 39 unieke casus-ID’s, plus twee A-P3-waarnemingen. C: zes evaluatorwaarnemingen (P1), INT-02-formatteruitvoer met voorbeelden aan/uit (P2), twee servicewaarnemingen (P3), twee cleaninggevallen (P4), één UI-helperproef (P5) en één geïsoleerde gateproef met drie gecontroleerde condities (P6). C hergebruikt bovendien twaalf historische route-uitkomsten (P0); die tellen niet als nieuwe metingen. Het gezamenlijke ontwerpregister bevat 76 ID’s: 57 bestaande en 19 nieuwe C-ID’s; niet alle zijn uitgevoerd. Alle proeven zijn offline en synthetisch.

De telling is rechtstreeks op R geverifieerd: 76 unieke rij-ID’s, waarvan precies C100–C118 de 19 nieuwe C-ID’s vormen.

## Door v4 ontstane tekstspanningen

**V4-C-01 — S §5:65 tegenover §5:69; redactioneel, geen heropening van K5.** Het kader sluit INT-02-tekstherstel uit en duidt het ontwerp als toelichtingsvoorstel. Daaronder blijven “Herstel alleen op verzoek”, “Na een wijziging” en “Algemene activeringsvoorwaarde” staan. Gelezen binnen het kader is geen INT-02-herstel geautoriseerd; los overgenomen kan de ontwerptekst dat wel suggereren. Ook §8:98 spreekt nog van “vóór en na herstel”. De beschermde grenzen ontbreken niet, maar de benaming moet aansluiten op de nieuwe status.

Exact voorstel aan de coördinator: vervang in S:69 de eerste twee zinnen door:

> Voor INT-02 betreft H uitsluitend een afzonderlijk gevraagd toelichtingsvoorstel als nieuw concept: maximaal één poging, alleen als de beschikbare bron en bedoeling een passende afbakening dragen. Een aantoonbaar niet-begripsbepalend procesvoorschrift kan daarin apart worden toegelicht (C64 onder N-breed); de bestaande definitietekst blijft ongewijzigd. Dit is geen INT-02-tekstherstelroute en geen onderdeel van G’s één-zin-uitvoer. De onderstaande wijzigings- en hertoetsregels betreffen het nieuwe concept; activering van automatisch tekstherstel betreft uitsluitend vormregels overeenkomstig K5/DEF-832.

Vervang op dezelfde regel `Algemene activeringsvoorwaarde:` door `Voor automatisch tekstherstel bij vormregels geldt als noodzakelijke, niet voldoende activeringsvoorwaarde:`. Vervang in S:98 `(4) **H** vóór en na herstel` door `(4) **H** origineel en afzonderlijk toelichtingsvoorstel`. Behoud alle overige stop-, bindings- en bewijsvoorwaarden. Dit concretiseert het reeds vastgelegde kader en vraagt geen nieuw besluit.

**V4-C-02 — D besluitentabel tegenover voorstel-/keuzetekst; redactioneel, gekoppeld aan SC-C-10.** De tabel D:9–14 is duidelijk als besluit gemarkeerd. Daaronder staan echter nog “geen genomen besluit” (47), “het is nú geen besluit” (50), “Activeren” als alternatief (51) en “Nieuw besluit nodig” (55). Dit zijn achtergebleven voorstelteksten, geen geldige weergave van de huidige besluitstatus. S heeft daarvoor al een expliciet algemeen kader (S:3); D mist zo’n volledige afbakening van de oude keuzetabel.

Exact voorstel: vervang D:42 door `## Keuzeafwegingen vóór het besluit (ter verantwoording)` en plaats eronder:

> De onderstaande voorkeuren, alternatieven en formuleringen “geen genomen besluit” en “nieuw besluit nodig” documenteren het onderzoeksvoorstel vóór 25 september 2026. De tabel “Besluiten van Chris” hierboven en besluiten-chris-v1.md bepalen de actuele besluitstatus. O1 is gekozen, O2 wordt als vervolg ingepland, S1 is gekozen en INT-02-tekstherstel is uitgesloten; het oude activeringsalternatief is geen actuele uitvoeringsoptie. Deze afwegingen vormen geen implementatieopdracht.

De vervanging van D:30 bij SC-C-09 markeert ook het voorafgaande voorstelblok. Chris’ besluiten worden hiermee niet veranderd of opnieuw getoetst.

## Afronding, bewijsgrenzen en oplevering

**Ja, A+B+C is inhoudelijk afgerond binnen het afgesproken onderzoeksbereik.** De ene materiële v1-bevinding is aantoonbaar verwerkt. De resterende bevindingen betreffen onvolledige redactionele doorwerking en het onderscheiden van historische voorstellen van genomen besluiten; zij vragen bovenstaande gerichte tekstverwerking door de coördinator, geen nieuwe onderzoeks- of volledige reviewronde. De claim uit de verwerkingstabel dat alles is overgenomen betekent dus niet dat iedere gevraagde vindplaats al is bijgewerkt.

Dit oordeel bewijst geen volledige UI-/opslag-/import-/vaststel-/exportketen, model-, gebruikers- of herstelwinst, juridische actualiteit of rechtstreeks gelezen DBT §4.2. De ESS-04-relatie en ketenuitvoering blijven zichtbaar geparkeerd. K1–K5/K2b zijn beslist volgens B en D; publicatie en implementatie blijven afzonderlijk.

Deze controle implementeert niets, verandert geen bestaande onderzoeksversies en start geen agents. Het rapport wordt volledig teruggelezen; hashes, bronbinding en bestandscontrole staan in [manifest-c-v3.json](manifest-c-v3.json). Dat manifest omvat alle onderzoeksbestanden in C, met de eigen manifesthash afzonderlijk in het eindbericht om een circulaire zelfhash te vermijden. De gelezen automatische handover is volgens de sessie-instructie binnen C gearchiveerd; dit wijzigt geen onderzoeksversie.

Gebruikte vaardigheden: analysis-mode en verification-before-completion. De automatische goedkeuringscontrole weigerde research-dispatch wegens mogelijk starten van een achtergrondagent en requesting-code-review wegens mogelijk starten van een reviewer/achtergrondproces. Die acties zijn niet omzeild; de gerichte documentcontrole bleef uitvoerbaar.
