# INT-02 — verwerking door onderzoekslijn A van de review van B (v1)

25 september 2026 · DEF-771 · fase **verwerking door beiden** · onderzoekslijn A (Claude Code CLI).
Verwerkt:
- `b-codex-cli/review-b-op-a-v1.md` (RB-A-01…26);
- `b-codex-cli/review-b-op-a-v1-erratum.md`, dat de vindplaats bij RB-A-13 corrigeert naar `modular_validation_service.py:1920–1921`;
- A's eigen aangekondigde correcties uit `review-a-op-b-v1.md`: RA-B-02, -04, -06, -13 en -25.

Het herziene advies staat in [`onderzoek-a-v2.md`](onderzoek-a-v2.md) en [`casusregister-a-v2.md`](casusregister-a-v2.md). Gewijzigde passages zijn gemarkeerd met "(v2: …)". `onderzoek-a-v1.md` en `casusregister-a-v1.md` blijven ongewijzigd.

**Gerichte broncontrole bij feitelijke tegenspraak** (geen nieuwe proef nodig):
- RB-A-15: `docs/analyses/2026-09-15-DEF-606-besluit-geen-totaalscore-v1.md:27` — "Het wijzigt niet automatisch de norm, toepasselijkheid, ernst, individuele scorepolicy of reviewplicht … concrete vaststel-/exportvoorwaarden volgen hun eigen contract." → B heeft gelijk.
- RB-A-16: `csv_importer.py:273-275` (no-op) heb ik in de reviewfase al nagekeken. `definition_import_service.py:67-112` is door B gelezen en niet door A nagecontroleerd; overgenomen als B-bronfeit.
- RB-A-20: de logische analyse is zelf nagegaan. "X is even indien X deelbaar is door 2" geeft een voldoende voorwaarde. C05 voegt het domein "geheel getal" toe. → B heeft gelijk.

Oordelen: **O** = overgenomen · **GO** = gedeeltelijk overgenomen · **AG** = afgewezen met grond · **OP** = open.

| Punt | Oordeel | Grond | Vindplaats in v2 |
|---|---|---|---|
| RB-A-01 (ASTRA-kern, lokale verruiming, bronvermelding) | O | Bevestiging. Bronvermelding wordt "ASTRA (verwijst naar DBT §4.2; DBT niet rechtstreeks onderzocht)". Een afleidingsregel *voldoet*; het is geen niet-toepasselijkheidsklasse | v2 §1.3 (rij brondocument), §5.1 (`brondocument`) |
| RB-A-02 (geen universeel determinisme) | O | Dezelfde strekking als A's eigen RA-B-02. ESS-04-N2 en B-C55. "Vaststaan" = geldt voor de bedoelde instanties, geen algoritme- of eensluidendheidseis. B's zinnen letterlijk opgenomen | v2 §1.2, §1.4, §5.1 (uitleg/toelichting), §5.2 (G) |
| RB-A-03 (actorvoorschrift als lokale operationalisering) | O | Zelfde als RA-B-03. ASTRA gebruikt "lijkt op" en de redactievraag laat de categorieverhouding open. N-b = lokale operationalisering met bronsteun; keuze van Chris (K1) | v2 §1.2, §8 (K1) |
| RB-A-04 (beschrijven van discretie of rechtsgevolg ≠ voorschrijven) | O | T-VN(N-a) "hoort in de regelgeving" was te breed. C12 is een synthetische bewerking van het Ppw-voorbeeld. De zin van B is letterlijk opgenomen in N/G/T/skill. C13 krijgt de voorwaarde "als actorinstructie bedoeld" | v2 §1.4, §5.1, §5.2, §5.3; casusregister v2 C12/C13/C16/C30 |
| RB-A-05 (paar, modaliteit, rolomkering) | GO | Rolomkering: A had die al als onvoldoende bewezen aangemerkt (RA-B-22). Overgenomen: C02 is geen veilige reparatie naar C01; "moet" bewijst geen discretie; de bronpaar-policy blijft. **Deels afgewezen:** A houdt vast aan een gecorrigeerde `example_pair_reason`, omdat de huidige tekst ("uitsluitend … de norm van ARAI-04") de INT-02-functie juist wegschrijft. A neemt B's voorgestelde reden letterlijk over. Die noemt de mogelijke verplichting zonder die als bewezen voor te stellen, dus het verschil verdwijnt | v2 §1.2, §5.1 (`example_pair_reason` = tekst van B); casusregister v2 C02 |
| RB-A-06 (contextplicht K-9) | O | Zelfde als RA-B-06. `ESS-05-…/besluiten-v1.md:16`. Context verplicht vóór G/T: ontbrekend = niet uitgevoerd. Geen keuze voor Chris. B-C60 (bronconflict) toegevoegd als koppelcasus | v2 §2 (matrix + tekst), §4, §8; casusregister v2 C29 |
| RB-A-07 (veldrollen aanvullen) | O | De rollen voor ontologische relaties, praktijkvoorbeeld, positieve/tegen-/grensgevallen, synoniem/homoniem, bedoeling/toelichting en reviewmetadata zijn overgenomen. "Synoniemen niet relevant" is ingetrokken | v2 §2 (matrix) |
| RB-A-08 (relaties niet als exclusieve schotten) | O | ESS-05-K-8: elke regel motiveert zelf. H beschermt negatie, uitzondering, EN/OF en constitutieve doelrelaties. "Geen relatie behalve vorm" bij INT-08 geschrapt (B-C58) | v2 §3 (rijen INT-08, STR-06), §5.4 |
| RB-A-09 (bronbinding: exit afgeleid, model/CLI-versie ontbreekt) | O | Juist. Exit 0 is "gerapporteerd/afgeleid uit tooluitvoer". Model: claude-opus-5-5 (omgevingsgegeven van deze sessie); CLI-versie niet vastgesteld. Aanbeveling om bij volgende rondes echte exit en versies machinaal vast te leggen | v2 §0, §7 |
| RB-A-10 (C21/C15-voorspellingen) | O | Preciezer: C21 raakt V3 en C15 raakt V6. "Alle andere 23" vermengde twee voorspellingen. Oorspronkelijke verwachtingen blijven, afwijkingen gemarkeerd | v2 §7 |
| RB-A-11 (historisch hergebruik) | O | Bevestiging; smalle claim blijft | v2 §0 (ongewijzigd) |
| RB-A-12 (prompt, ESS-03/STR-09-spanning) | O | Preciseren: "in standaard geregistreerde promptmodules (module-niveau)". Verzending en modelrespons niet gemeten | v2 §3, §4 |
| RB-A-13 (INT-10 scoort `\bindien\b`) | O | Bevestiging met erratum-vindplaats `MVS:1920–1921` voor de suggestietekst. **Status volgens instructie van Chris (25-09):** geparkeerde waarneming voor het INT-10-dossier. Het ketenfeit blijft staan, maar is geen besluit in dit onderzoek | v2 §3 (INT-10), §4, §8 (geparkeerd) |
| RB-A-14 (UI-claim is statisch) | O | "0 van 25" wordt "statische codebevinding; geen browserproef". Tupletoevoeging alleen zinvol met de nieuwe passagehulp | v2 §4, §5.5, §6 |
| RB-A-15 (geen-gate niet uit het besluit van 15-09) | O | Broncontrole: besluit r. 27 bevestigt B. De tekst van B is letterlijk opgenomen. Poortbeleid wordt K4 | v2 §4 (vaststellen), §5.3, §8 (K4) |
| RB-A-16 (import, review, opslag, export) | O | Twee importroutes. `expert_review_tab.py:1079` = CON-02, geen INT-02-bewijs. Opslaghelper neemt alleen violations over (`models.py:147`, door A gecontroleerd). Exportgate volgens B (niet door A nagekeken). Opslag en export blijven open bewijs | v2 §4 |
| RB-A-17 (leeg/alleen term) | O | "Toegang:" is niet leeg. Kernherkenning bij alleen-term moet begrensd zijn; NE blijft een ontwerp | v2 §5.3; casusregister v2 C06/C23 |
| RB-A-18 (uitkomstenschema) | O | Zelfde als RA-B-15. Precies V/VN/NA/OI (+één vraag), daarnaast niet uitgevoerd en technisch mislukt, zonder inhoudelijk oordeel. NA alleen met reikwijdtegrond | v2 §5.3 |
| RB-A-19 (N–G–T synchroon; voorlopige kandidaat; VN-tekst) | GO | Overgenomen: de G-zin over een voorlopige kandidaat en de nieuwe T-VN-tekst van B. Het minimale recordalternatief volstaat niet los. **Aangepast aan RA-B-13:** B's G-zin "geef de ontbrekende keuze afzonderlijk aan" botst met het uitvoercontract van één zin (`json_based_rules_module.py:335-339, 348-354`). A formuleert daarom volgens het ESS-03-patroon: geen melding in de zin, de vraag loopt via T (OI). **Open:** vervangen van signalen (coördinator) of uitbreiden (A) → keuze K2-detail | v2 §5.1, §5.2, §5.3, §8 |
| RB-A-20 (geen bewezen gelijkwaardigheid) | O | Zelfde als RA-B-04; logica nagegaan. Het C04→C05-"stijlvoorstel" is ingetrokken. Hetzelfde geldt voor C17→C18 en C11→C10: zelfde toegestane functie, niet dezelfde afbakening | v2 §5.2 (voorbeeld), §5.4, §5.5 (skillvoorbeeld); casusregister v2 |
| RB-A-21 (H bij C02/C12/C13/C14) | O | "Menselijke bevestiging maakt betekenissen niet gelijk." H-tekst van B letterlijk opgenomen. B-C64 is het positieve H-geval; C31/C32 blijven negatief | v2 §5.4; casusregister v2 C02/C12/C13/C14 |
| RB-A-22 (H-diagnose transport; hertoetslijst) | O | Transport- of cleaningverlies wordt een aparte diagnose. Een vaste hertoetslijst wordt "alle geraakte regels; bij onbekende afhankelijkheid alle toepasselijke" | v2 §5.4 |
| RB-A-23 (casusverwachtingen) | O | Per rij verwerkt. C24/C25: een deterministisch voorschrift kan onder de brede norm ook VN zijn. B-C55/C58/C60/C61/C64/C65/C67 als koppelcasussen, zonder nieuwe IDs | casusregister v2 |
| RB-A-24 (effectevaluatie, H-effect) | O | Aparte H-effectvergelijking toegevoegd. Tellingen zijn N-A1-verwachtingen, geen semantische nulmeting | v2 §6 |
| RB-A-25 (dekking veertien onderdelen) | O | Dekkingstabel bijgewerkt met de lacunes uit B | v2 §9 |
| RB-A-26 (besluiten A ↔ B) | O | Samengevoegde nummering K1–K5 van B, met koppeling naar B-1…B-9. B-7 = geparkeerd (instructie van Chris) | v2 §8 |

**Eigen aangekondigde correcties (review-a-op-b-v1):**

| Punt | Verwerking | Vindplaats |
|---|---|---|
| RA-B-02 | Determinisme- of eensluidendheidsformulering vervalt (= RB-A-02) | v2 §1.2, §5.1 |
| RA-B-04 | C04/C05-equivalentie ingetrokken (= RB-A-20) | v2 §5.4; casusregister v2 |
| RA-B-06 | K-9-contextplicht toegepast (= RB-A-06) | v2 §2, §4 |
| RA-B-13 | G blijft binnen het uitvoercontract van één zin; de verduidelijkingsvraag loopt via T | v2 §5.2 |
| RA-B-25 | K4 (poort) toegevoegd; B-2/B-6 opgegaan in K1; B-8 = uitvoering van bestaand beleid | v2 §8 |

## Open punten

- **Signaalbeleid (RB-A-19, RA-B-17).** Vervangen (coördinator), uitbreiden (A) of alleen hulpmiddel (B). Dit is een keuze binnen K2 en niet met de huidige proeven te beslissen. Een effectmeting met reviewers moet het uitwijzen.
- **B-routeclaims die A niet heeft nagecontroleerd.** Dat zijn `definition_import_service.py:67-112`, `export_service.py:400-472` en de stelling dat `definitie_origineel` al is opgeschoond. Ze zijn als B-bronfeit overgenomen; routebewijs (UI → opslag → export) ontbreekt.
- **Gate-transport van INT-10-ernst** (`severity` tegenover `severity_level`). Onbewezen; hoort bij het INT-10-dossier en DEF-630.
- **DBT §4.2 (Ross) en de ASTRA-revisie.** Niet gelezen; blijft een bewijsleemte.
- **Juridische geldigheid van de synthetische casussen.** Niet onderzocht.

## Besluiten bij Chris (samengevoegde nummering)

| K | Inhoud | Koppeling A | Voorkeur A en B | Beslissende casus |
|---|---|---|---|---|
| **K1** | Functiegrens: brede variant (N-B1: actorvoorschrift/procedure + discretionaire beslisregel) of enge variant (N-A: alleen discretie). Beschreven rechtsgevolg of bevoegdheid voldoet; criteria in voorwaardelijke vorm voldoen | B-1, B-2, B-3, B-6 | Beiden de brede variant, als lokale operationalisering | C02 (onder de enge variant geen VN), C03/C15/B-C52 tegenover C16/B-C53/C69 |
| **K2** | Evaluator: O1 (passagehulp, menselijke review) nu, O2 (AI-beoordeling) als apart besluit; inclusief signaalbeleid en zichtbare reden | B-4, B-9 | Beiden O1 nu | C13, C83, B-C52, B-C55 |
| **K3** | Eén versiegebonden contract voor record, prompt, skills en voorbeelden; bronpaar behouden met gecorrigeerde `example_pair_reason` en extra functievoorbeelden | B-5 | Gelijk (reden volgens de tekst van B) | C02, C10, C12 |
| **K4** | Wel of geen zelfstandige INT-02-poort voor vaststellen of export | (nieuw; was in A v1 ten onrechte afgeleid) | Beiden: geen eigen blokkade, open of negatieve uitkomst zichtbaar | B-C67 |
| **K5** | H: niet activeren; later hoogstens één poging onder DEF-638, met effectacceptatie | (A §5.4) | Gelijk | C14, C31/C32, B-C64/C65 |

**Geen keuze meer (bestaand beleid uitvoeren):**
- contextplicht K-9;
- geen totaalscore;
- toetsen wijzigt de tekst niet;
- lege of ontbrekende kern → niet uitgevoerd (A's B-8).

**Geparkeerd:** A's B-7 (`\bindien\b` in INT-10, en de overlap met INT-01) gaat als waarneming naar het latere INT-10-dossier. Het INT-01-deel loopt via het open INT-01-besluit.
