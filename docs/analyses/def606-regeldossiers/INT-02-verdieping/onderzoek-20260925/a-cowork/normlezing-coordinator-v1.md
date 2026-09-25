# INT-02 — normlezing van de coördinator (onderzoeker A / Cowork) — v1

25 september 2026 · DEF-771 · **interpretatie**, geen besluit en geen normbewijs. Opgesteld op verzoek van Chris ("onderzoek ook wat de intentie van deze regel is volgens jou") nadat beide onderzoekslijnen waren gestart; niet gedeeld met A-CLI of B vóór opslag van hun v1. Bronnen: `gedeeld/bronnen/astra-INT-02-raw.wikitext`, `astra-Beslisregel-raw.wikitext`, `astra-Afleidingsregel-raw.wikitext`; lokaal record `src/toetsregels/regels/INT-02.json`; proef C1 (`a-cowork/bewijs/`). DBT §4.2 (Ross) is niet gelezen; alles wat hieronder over Ross staat komt uit de ASTRA-tekst zelf.

## 1. Wat de bron beschermt (lezing)

ASTRA zegt letterlijk: *"Een definitie mag niet geformuleerd worden als een beslisregel."* Het woord dat het werk doet is **beslisregel**, en ASTRA definieert dat zelf: *"Algoritme waarvoor oordeelsvorming nodig is"* — de uitkomst is "niet 100% deterministisch", de bron is "vaak wet of beleid, waar dus kennelijk een discretionaire bevoegdheid is opengelaten". Daartegenover zet ASTRA de **afleidingsregel**: een "geheel deterministisch algoritme" dat een afgeleid feit uitrekent. Die vorm is niet alleen toegestaan, ASTRA maakt haar verplicht: *"een afleidbaar begrip MOET gedefinieerd worden in termen van een afleidingsregel"* (voorbeeld: stelselmatige dader = drie onherroepelijke veroordelingen wegens misdrijf in vijf jaar).

Mijn lezing van de intentie, in één zin: **een definitie moet een deterministisch afbakeningscriterium zijn — zij vertelt wat als geval van het begrip telt, zó dat twee bevoegde lezers tot hetzelfde antwoord komen — en mag niet de vorm krijgen van een regel die (a) actoren iets voorschrijft of (b) de uitkomst aan iemands afweging overlaat.**

Daar zitten twee assen in, die ASTRA allebei aanraakt:

| As | Wat ASTRA zegt | Waar het misgaat | Voorbeeld |
|---|---|---|---|
| **Voorschrift** (behavioral business rule, "obligation concerning conduct, action, practice, or procedure", Ross blz. 260; DEMO-actieregel: "richtlijn voor actor") | Achtergrond + het voorbeeldpaar | De zin legt een verplichting of handeling op in plaats van het begrip te beschrijven | ONJUIST "eis die een organisatie **moet ondersteunen**" ↔ JUIST "eis die een organisatie **ondersteunt**". Let op: het "moet" draait ook de rollen om (organisatie moet de eis steunen ↔ de eis steunt de organisatie); de ONJUISTE zin is een gedragsregel voor organisaties, niet een omschrijving van de eis |
| **Discretie / oordeelsvorming** (beslisregel; niet-deterministisch) | Regel + Toelichting + begrip Beslisregel | De classificatie hangt af van een afweging ("van oordeel is dat…", "redelijk", "naar eigen inzicht", "onevenredig") | Ppw-voorbeeld bij Beslisregel: "…**tenzij hij van oordeel is** dat de aanvrager onevenredig zou worden benadeeld" |

Wat de bron uitdrukkelijk **niet** verbiedt: voorwaardelijke zinsvorm. "Indien/mits/tenzij/voor zover" kunnen precies de deterministische afleidingsregel dragen die ASTRA wil ("is stelselmatige dader **als** … drie maal … veroordeeld"). De vorm "X is een Y als Z" is de kern van definiëren (genus + differentia, lidmaatschapscriterium); het woord is onschuldig, de **functie** van de zin beslist. Ross' *definitional rule* — "a definitional criterion that is necessarily true for each instance of a concept" — is dus geen tegenhanger van INT-02 maar het ideaalbeeld ervan.

## 2. Waarom de lokale versie van de norm afwijkt (lezing)

Het lokale record maakt van een functieregel een woordregel: "geen beslisregels **of voorwaarden**", toelichting "onder welke voorwaarden het geldig is … horen thuis in regelgeving", en zeven regexen. Dat is een lokale toevoeging (ASTRA kent geen patronen; geheugen `astra-normatieve-bron`). Gevolg, gemeten in proef C1 op main `26f2374d`:

- **Gemist**: de twee echte overtredingsvormen geven géén signaal — C02 ("moet ondersteunen", ASTRA's eigen ONJUIST-voorbeeld) en C83 ("naar eigen inzicht … redelijk acht", discretie zonder patroonwoord).
- **Ten onrechte aangewezen**: deterministische criteria in voorwaardelijke vorm krijgen wél een signaal — C04/C81 ("indien … door twee deelbaar", "indien … drie maal veroordeeld"), C84 ("voor zover … drempelbedrag").
- De evaluator (`judgment_review`) keurt nooit automatisch af — dat vangt de schade op — maar de reviewer wordt naar de verkeerde passages gestuurd en de **generatieprompt** zegt letterlijk "Vermijd voorwaardelijke formuleringen". Dat instrueert het model om precies de deterministische afbakening te vermijden die ESS-03/ESS-04/ESS-05 vragen. Dat is, denk ik, de spanning die DEF-771 aanduidt als "Begripscriterium tegenover voorschrift of procedure beoordelen".

Mogelijke herkomst van "voorwaarden" (niet bewezen): een oudere lezing van DBT of de skill `nederlandse-definities` ("Vermijden: voorwaardelijke formuleringen") die in het record is teruggevloeid. DBT §4.2 moet gelezen worden om dit te sluiten (open bewijs; DEF-625).

## 3. Afgrenzing van de buurregels (lezing van eigenaarschap)

- **ARAI-04 (modaliteit)** bezit de *woordvorm* moet/kan/mag; INT-02 bezit de *zinsfunctie* (beschrijving versus voorschrift). Het ASTRA-paar is daardoor tegelijk een ARAI-04- en een INT-02-geval; het record-`example_pair_reason` ziet dat terecht. Eén "moet" is een ARAI-04-signaal; "de zin schrijft een handeling voor" is het INT-02-oordeel.
- **ESS-04 (toetsbaarheid)** bezit de vraag of een criterium navolgbaar toepasbaar is; INT-02's discretie-as raakt daaraan, maar is smaller: INT-02 vraagt of de *definitie zelf* een afweging in de uitkomst inbouwt ("tenzij hij van oordeel is"), ESS-04 of het criterium überhaupt toepasbaar is. Overlap, geen conflict; bij twijfel is de discretie-passage het INT-02-onderwerp en de toepasbaarheid het ESS-04-onderwerp.
- **ESS-05/ESS-03** vragen juist scherpe, deterministische afbakening; de huidige INT-02-instructie werkt daar tegenin. Na herstel van de norm verdwijnt dat conflict.
- **INT-01** deelt het woord `indien` alleen als patroon; INT-01 (één zin) heeft er inhoudelijk niets mee te maken. Het INT-01-voorstel om de woordlijst te laten vervallen is consistent met deze lezing.
- **STR-06 (doel/functie)** en **INT-08 (negatief)** raken andere assen; geen relatie behalve dat "wordt afgewezen indien" naast INT-02 ook een STR-06-signaal (procedure i.p.v. wezen) kan zijn.

## 4. Wat dit voor de app zou betekenen (voorstel-richting, geen besluit)

Norm (concept): *De definitie beschrijft wat een geval van het begrip is en is als afbakening deterministisch toepasbaar. Zij schrijft geen handeling, verplichting of procedure voor en laat de uitkomst niet afhangen van een afweging of oordeel. Voorwaardelijke zinsvorm is toegestaan wanneer zij een deterministisch criterium uitdrukt; voor een afleidbaar begrip is die vorm de aangewezen vorm.*

- **T**: oordeelregel blijft (menselijk oordeel of, naar ESS-03/ESS-05-precedent, een scoreloze AI-beoordeling met vier uitkomsten + één vraag); signalen omgedraaid: voorschrift-signalen (moet/dient/verplicht/wordt … [handeling]), discretie-signalen (van oordeel is, redelijk, naar eigen inzicht, kan … besluiten, onevenredig, passend) in plaats van `indien/mits/tenzij`; een treffer is nooit fail, geen treffer nooit pass.
- **G**: instructie omdraaien: "Beschrijf wat een geval van het begrip is, als deterministisch toepasbaar criterium; schrijf geen handeling of verplichting voor en laat niets aan een afweging over. Een voorwaardelijke vorm mag als zij een deterministisch criterium uitdrukt."
- **H**: geen automatische verwijdering van "indien" (zou betekenis vernietigen); herstel alleen op verzoek, met betekenisbehoud; een "moet"-zin herschrijven naar beschrijving verandert vaak de rol van de actor — reviewer nodig.
- Record: uitleg/toelichting/toetsvraag naar ASTRA; `type` → "gehele definitie"; "of voorwaarden" schrappen; ASTRA-paar behouden plus een sprekender SRK-paar (ASTRA's redactie vraagt daar zelf om) — bijv. stelselmatige dader (JUIST, afleidingsregel met voorwaarde) versus een Ppw-achtige "tenzij … van oordeel is"-variant (ONJUIST).

## 5. Wat ik hier níet claim

Geen gelezen DBT §4.2; geen gevalideerde juridische praktijkgevallen (C80–C86 zijn synthetisch); geen bewijs over generatiekwaliteit; geen UI/opslag/export-proef. Deze lezing is invoer voor de synthese en moet door de kruisreview (A-CLI en B) worden bevestigd, aangevuld of tegengesproken; waar A-CLI of B tot een andere normlezing komt, staan beide standpunten in de besluitnotitie.
