# INT-02 — gezamenlijk casusregister v1

25 september 2026 · DEF-771 · samengesteld door onderzoeker A (Cowork, coördinator) uit `a-claude-cli/casusregister-a-v1.md` (C01–C06, C10–C33), `b-codex-cli/casusregister-b-v2.md` (C01–C06, C50–C69) en `a-cowork/bewijs/proef-c1-*` (C80–C86). IDs zijn stabiel; de volledige G/H-kolommen staan in de bronregisters. Alle gevallen zijn synthetisch of ASTRA-bronvoorbeelden; geen gevalideerde juridische praktijkgevallen.

**Normversies.** N-B1 (voorkeur van beide onderzoekers en de coördinator): geen actorvoorschrift/procedure en geen discretionaire beslisregel als definitiekern; begripscriteria en deterministische afleidingen zijn toegestaan, ook in voorwaardelijke zinsvorm. N-A (enge variant, B §Q1): alleen discretionaire beslisregels uitgesloten. Waar N-A anders uitkomt staat dat erbij. **Huidig** = gemeten gedrag op main `26f2374d` (P1 A, P1 B, C1 coördinator): INT-02 altijd `review_required` (RR); "sig" = regexsignaal.

**T-referentie:** V = voldoet · VN = voldoet niet · O = onvoldoende informatie/nog te beoordelen (+ één vraag) · NE = niet uitgevoerd (lege kern/ontbrekende context) · E = technische fout.

| ID | Kern (verkort) en bedoeling | T-referentie N-B1 (N-A indien anders) | Huidig main | Onderscheidt | Herkomst / bewijs |
|---|---|---|---|---|---|
| C01 | transitie-eis: eis die een organisatie **ondersteunt** om migratie … (ASTRA JUIST) | V | RR, geen sig | K-3 (paar behouden) | ASTRA; hist. 11-09; P1-A; P1-B (hergebruik); C1 |
| C02 | … eis die een organisatie **moet ondersteunen** … (ASTRA ONJUIST) | VN (verplichting = gedragsvoorschrift; N-A: geen INT-02-fail) | RR, **geen sig**; ARAI-04/SUB1 fail | K-1 (N-A ↔ N-B1), K-3 | ASTRA; P1-A; C1 |
| C03 | Aanvraag die wordt afgewezen indien een bijlage ontbreekt. (procedure) | VN (N-A: O — geen discretie aangetoond) | RR, sig indien; INT-10 + INT-01 fail | K-1 | hist.; P1-A; C1 |
| C04 | Getal dat even is indien het zonder rest door twee deelbaar is. (criterium, voorwaardelijke vorm) | V (vorm = INT-01/STR-01/ARAI-06) | RR, sig indien; INT-10 + INT-01 + INT-08 fail | K-2 (lidmaatschapscriteria) | hist.; P1-A; C1 |
| C05 | Geheel getal dat zonder rest door twee deelbaar is. | V | RR, geen sig | K-2 | hist.; P1-A; C1 |
| C06 | "" (leeg) | NE (geen kern) | RR (reviewvraag over niets) | K-8 (leeg → NE) | hist.; P1-A; C1 |
| C10 | stelselmatige dader: persoon die in de vijf jaar … drie maal … onherroepelijk is veroordeeld (ASTRA-afleiding, kenmerkvorm) | V (afleidingsregel; voor afleidbaar begrip verplicht) | RR, geen sig; INT-01 fail | K-1, K-2 | ASTRA Afleidingsregel; P1-A (= C80 coördinator) |
| C11 | idem met "geldt **indien** …" | V | RR, sig indien; INT-10 fail | K-2, K-7 (INT-10) | P1-A (= C81 coördinator, = C50 B) |
| C12 | besluit waarmee de bevoegde autoriteit een aanvraag afwijst, **tenzij** zij van oordeel is dat … onevenredig … (discretie, Ppw) | VN (beide varianten) | RR, sig tenzij; ARAI-04 fail | K-3 (nieuw fout-voorbeeld) | ASTRA Beslisregel; P1-A (= C82 coördinator, ≈ C51 B) |
| C13 | … intrekt **wanneer** zij dat na afweging … evenredig acht (discretie zonder patroonwoord) | VN (beide varianten) | RR, **geen sig** | K-4 (evaluator: signalen missen) | P1-A (≈ C83 coördinator) |
| C14 | verklaring die een getuige … **moet** afleggen bij de politie (gedragsverplichting) | VN (N-A: geen INT-02-fail) | RR, geen sig; ARAI-04/SUB1 fail | K-1 | P1-A |
| C15 | verzoek dat de behandelaar binnen zes weken beoordeelt en bij een ontbrekende bijlage afwijst (procedure zonder patroonwoord) | VN (N-A: O) | RR, **geen sig** | K-1, K-4 | P1-A (≈ C52 B) |
| C16 | bestuurlijke boete die wordt opgelegd **wanneer** een aangifte niet tijdig is gedaan (rechtsgevolg/grond) | V (grond als kenmerk; A-voorkeur) — alternatief VN als "wordt opgelegd" als plicht van het orgaan wordt gelezen | RR, geen sig; INT-08 fail | K-6 (rechtsgevolg) | P1-A |
| C17 | Een lid is stemgerechtigd indien ingeschreven vóór 1 januari. (claude-grensgeval A, 11-09) | V (statusafleiding); vorm elders | RR, sig indien; INT-10, ARAI-06/STR-01 fail | K-2 | claude-review 11-09; P1-A (≈ C54 B) |
| C18 | lid dat vóór 1 januari … is ingeschreven | V | RR, geen sig | K-2 | P1-A |
| C19 | Een document geldt als gewaarmerkt **mits** voorzien van handtekening en datum. (claude-grensgeval B) | V | RR, sig mits; INT-10 pass | K-2 | claude-review 11-09; P1-A |
| C20 | deel van de zorgkosten … **voor zover** … onder de basisverzekering vallen (reikwijdtecriterium) | V | RR, sig voor zover | K-2 | P1-A (≈ C84 coördinator) |
| C21 | term "tenzij-clausule", kern zonder patroonwoord | V | RR, geen sig | — (term ≠ kern) | P1-A |
| C22 | aangifte die binnen vijf werkdagen na het feit is gedaan (toetsbaar criterium) | V | RR, geen sig | — (ESS-04-overlap) | P1-A |
| C23 | "Toegang:" (alleen term) | NE | RR | K-8 | P1-A |
| C24 | Toegang: toestemming verleend door een bevoegde autoriteit, indien alle voorwaarden zijn vervuld. (unit-testtekst; dode module noemt het ❌) | O (welke voorwaarden? — ESS-04/INT-10-vraag); VN alleen bij afweging | RR, sig indien; INT-10 fail | K-4, test-herijking | test_v2_golden_int_more; P1-A; C86 (hoofdletters) |
| C25 | korting: verlaging indien tijdig betaald (fixture-probe) | V (criterium) of O bij toekenningsregel-context | RR, sig indien; INT-10 fail | K-2 | runtime_cases.yaml; P1-A |
| C26 | Een persoon met een paspoort of, indien niet beschikbaar, een identiteitskaart (STR-09-✅ in dezelfde prompt) | V | RR, sig indien; INT-10 fail | G-conflict STR-09 | P1-A, P2-A |
| C27 | aantal volledige jaren tussen geboortedatum en peildatum (ASTRA-afleiding leeftijd) | V | RR, geen sig | K-1 | P1-A |
| C28 | C04 als gegenereerde kandidaat én als aangeleverde tekst | V in beide routes; alleen G mag C05-vorm voorstellen | service-oordeel tekstgebonden gelijk; G niet gemeten | zelfde norm beide routes | ontwerp (A) |
| C29 | C03 + context/wettelijke basis | VN; context verandert de functie hier niet | RR, sig indien — identiek aan C03 | Q2 (context ondersteunend) | P1-A |
| C30 | toestemming van het bevoegd gezag die vereist is om een bouwwerk op te richten | V (verwijst naar norm als kenmerk) | niet uitgevoerd | K-6 | ontwerp (A) |
| C31 | H: C04 → "Getal dat even is." (indien geschrapt) | **stop**: criterium verloren | — | K-5 (H-grenzen) | ontwerp (A) |
| C32 | H: C12 → discretie vervangen door verzonnen "10% nadeel" | **stop**: verzonnen grond | — | K-5 | ontwerp (A) |
| C33 | bron bevat alleen de procedure, geen betekenis van "aanvraag" | G: geen kern verzinnen; hoogstens voorlopige kandidaat | — | K-5, Q2 | ontwerp (A) |
| C50 | Persoon die als stelselmatige dader geldt indien … (context "Synthetisch ASTRA-model") | V | RR, sig indien (P1-B); P3-B: opschoning behoudt indien | K-1, K-2 | P1-B, P3-B (= C11/C81) |
| C51 | De bevoegde autoriteit weigert het document, tenzij hij van oordeel is dat … | VN (beide varianten) | RR, sig tenzij | K-4 | P1-B (≈ C12/C82) |
| C52 | Aanvraag die de behandelaar **moet** afwijzen bij een ontbrekende bijlage. (verplichting zonder patroonwoord) | VN (N-A: geen fail) | RR, geen sig; P3-B: opschoning behoudt moet | K-1, K-4 | P1-B, P3-B (≈ C15) |
| C53 | vernietiging: Rechtshandeling waardoor de rechtsgevolgen van een eerdere rechtshandeling vervallen. | V (rechtsgevolg beschrijven ≠ voorschrijven) | RR, geen sig | K-6 | P1-B |
| C54 | Lid dat stemgerechtigd is **alleen als** het vóór 1 januari is ingeschreven. (noodzakelijk criterium) | V (volledigheid = ESS-05) | RR, sig alleen als | K-2; H: "alleen als" ≠ "als" | P1-B (≈ C17) |
| C55 | beschadigd voorwerp: Voorwerp met een waarneembare onderbreking van het oppervlak. (kwalitatief) | V (waarneming ≠ discretie) | RR, geen sig | K-1 (kwalitatief ≠ beslisregel), ESS-04 | P1-B |
| C56 | C50 zonder context (`context={}`) | NE gewenst (K-9) | RR, sig indien; run `validated` — context niet afgedwongen | K-9-uitvoering (bestaand besluit) | P1-B |
| C57 | even getal: "… even is als en slechts als …" (beoogd equivalent, maar logisch niet) | V voor INT-02; betekenisverruiming = ESS-01/05 | niet uitgevoerd | H: INT-02-V ≠ betekenisbehoud | ontwerp (B, v2-correctie) |
| C58 | Voertuig dat niet over rails rijdt, tenzij het voor onderhoud op een railwagen wordt vervoerd. | V (uitzondering als criterium) | niet uitgevoerd | K-2, INT-08 | ontwerp (B) |
| C59 | beslisregel: Algoritme waarvoor oordeelsvorming nodig is. (ASTRA-definitie zelf) | V (begrip *over* beslisregels definiëren is geen beslisregel) | niet uitgevoerd | K-4 (O3 afgeraden) | ontwerp (B) |
| C60 | C54 met twee strijdige bronpassages | O (bronconflict; één vraag) | niet uitgevoerd | Q2 (strijdige informatie) | ontwerp (B) |
| C61 | C50 ruw → getransporteerd zonder tijdvak/aantal | INT-02 V op beide; verlies = CON-02/ESS-05/DEF-626 (transportdiagnose) | niet uitgevoerd | H-diagnose | ontwerp (B) |
| C62 | C50 met hypothetische evaluator die VN geeft op "indien" | referentie V; evaluatorfout | huidige judgment geeft geen fail | K-4 | ontwerp (B) |
| C63 | H: C52 → "moet" geschrapt ("Aanvraag die de behandelaar afwijst …") | niet als V boeken; plicht → feit = betekenisverschuiving | — | K-5 | ontwerp (B) |
| C64 | "Digitaal formulier waarmee een verzoek wordt ingediend; de behandelaar wijst het af indien …" (kern + procesvoorschrift) | volledige invoer VN (N-B1); kernvoorstel V | niet uitgevoerd | K-5 (positief herstelgeval) | ontwerp (B) |
| C65 | C64 na één poging die de instructie laat staan | VN blijft; stop | — | K-5 (één poging, DEF-638) | ontwerp (B) |
| C66 | C50 met beoordelingsdienst-timeout (O2) | E | — | K-4 (O2-foutbeleid) | ontwerp (B) |
| C67 | C54 beoordeeld, daarna tekst/context gewijzigd | oud oordeel historisch; hertoetsen | niet uitgevoerd | DEF-626 | ontwerp (B) |
| C68 | C05 met betekenis/context maar zonder externe bron | V mogelijk (intrinsiek duidelijk); CON-02 apart | niet uitgevoerd | Q2 (bron ondersteunend) | ontwerp (B) |
| C69 | afgewezen aanvraag: Aanvraag waarover een besluit tot afwijzing is genomen. | V (besluituitkomst als kenmerk) | niet uitgevoerd | K-6 | ontwerp (B) |
| C80 | = C10 (kenmerkvorm stelselmatige dader) | V | RR, geen sig | K-1 | C1 coördinator |
| C81 | = C11 | V | RR, sig indien | K-2 | C1 |
| C82 | weigering: … afwijst, tenzij zij van oordeel is … | VN | RR, sig tenzij | K-4 | C1 |
| C83 | passende maatregel: maatregel die de rechter naar eigen inzicht oplegt wanneer hij dat redelijk acht (discretie zonder patroonwoord) | VN | RR, **geen sig** | K-4 | C1 (≈ C13) |
| C84 | eigen bijdrage: bedrag voor zover dat het drempelbedrag overschrijdt | V | RR, sig voor zover | K-2 | C1 (≈ C20) |
| C85 | spoedaanvraag: … alleen als … op voorwaarde dat de aanvrager de spoed aantoont (twee patronen) | O (criterium of toekenningsregel? — één vraag) | RR, sig alleen als + op voorwaarde dat | K-4 | C1 |
| C86 | = C24 met "INDIEN" in hoofdletters | O (als C24) | RR, sig indien (IGNORECASE bevestigd) | — | C1 |

## Samenvatting van de metingen op main (drie onafhankelijke proefsets, alle exit 0)

- **Alle** gevallen: INT-02 = `review_required`, nooit pass, nooit violation, ook bij lege tekst en ongeacht context (A: 25 gevallen; B: 7; coördinator: 13; historisch 6 op `d68a98a9` opnieuw bevestigd).
- **Signalen wijzen de verkeerde kant op:** treffers op criteria/afleidingen (C04, C11, C17, C19, C20, C25, C26, C50, C54, C81, C84 — onder N-B1 allemaal V of O), géén treffer op de echte overtredingen C02, C13, C14, C15, C52, C83 (VN).
- **INT-10** (`\bindien\b`, gescoord) faalt op alle acht `indien`-teksten van A (C03, C04, C11, C17, C24, C25, C26, C29); INT-01 faalt op 20 van 25 (eigen woordlijst).
- **Generatieprompt** (P2-A, P2-B, C1): letterlijk "Een definitie bevat geen beslisregels of voorwaarden." + "Vermijd voorwaardelijke formuleringen zoals 'indien', 'mits', 'tenzij', 'alleen als'"; in dezelfde prompt ESS-03 "behoud … voorwaarden" en STR-09-✅ met "indien".
- **Opschoning** (P3-B): "indien" en "moet" blijven staan; label/kop weg, slotpunt erbij.
- **Niet gemeten:** UI, opslag/snapshot, gate, import, export, echte modeluitvoer, menselijke beoordeling.
