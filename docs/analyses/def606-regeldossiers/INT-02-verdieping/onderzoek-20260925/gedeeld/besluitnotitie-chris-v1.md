# INT-02 — Geen beslisregel · besluitnotitie voor Chris (v1)

25 september 2026 · DEF-771 · onderzoek A (Cowork + Claude Code CLI) en B (Codex CLI), wederzijdse review, beide verwerkingen; synthesecontrole door B volgt op deze v1. Volledige onderbouwing: `gezamenlijke-synthese-v1.md`, `gezamenlijk-casusregister-v1.md`, beide onderzoeken, reviews en verwerkingen in dezelfde map. Codebasis main `26f2374d`.

## Wat er aan de hand is (bewezen)

ASTRA verbiedt dat een definitie een **beslisregel** is — een regel waarvan de uitkomst afhangt van iemands afweging ("…tenzij hij van oordeel is dat…") — en staat een **afleidingsregel** (deterministisch criterium, ook met "indien") uitdrukkelijk toe; voor afleidbare begrippen is die vorm zelfs verplicht ("stelselmatige dader = drie onherroepelijke veroordelingen in vijf jaar"). Het eigen ASTRA-voorbeeld ("eis die een organisatie *moet ondersteunen*") laat daarnaast zien dat een **verplichting** in de definitiezin fout is.

De app heeft daar een woordregel van gemaakt: "geen beslisregels **of voorwaarden**", zeven regexen op indien/mits/tenzij, en in de generatieprompt letterlijk "Vermijd voorwaardelijke formuleringen". Gemeten op main in 45 synthetische gevallen door drie onafhankelijke lijnen:

- INT-02 geeft altijd "nog te beoordelen" (nooit pass, nooit fail) — dat vangt de schade op, maar de reviewer ziet in de app alleen de regelcode, geen reden of passage.
- De signalen wijzen de verkeerde kant op: ze markeren juist de toegestane criteria ("even indien deelbaar door twee", "stemgerechtigd indien ingeschreven vóór 1 januari") en missen álle echte overtredingsvormen — ASTRA's eigen foutvoorbeeld ("moet"), discretie zonder patroonwoord ("naar eigen inzicht … redelijk acht"), procedure zonder patroonwoord.
- De prompt stuurt het model weg van precies de scherpe afbakening die ESS-03/04/05 vragen, en spreekt de ESS-03-instructie ("behoud … voorwaarden") en het STR-09-voorbeeld (mét "indien") in dezelfde prompt tegen.
- Keten: de vaststelgate kijkt niet naar INT-02; een open INT-02-review reist niet mee in het opslagkanaal voor issues; de directe service toetst ook zonder context (tegen je K-9-besluit in); CSV-beheerimport valideert niet. (Codelezing, niet getest.)
- Geparkeerd tot het INT-10-onderzoek: INT-10 keurt het woord "indien" gescoord af ("herschrijf zodat de patronen niet voorkomen").

## Voorstel (A, B en coördinator eens)

**Norm:** functie in plaats van woordvorm. Een definitie beschrijft het begrip met de kenmerken die bepalen wat ertoe behoort; zij laat de uitkomst niet aan een afweging over en schrijft geen handelen voor. Criteria, voorwaarden, uitzonderingen en deterministische afleidingen zijn toegestaan, ook met "indien/mits/tenzij/alleen als/voor zover". Een kwalitatief kenmerk dat een mens moet waarnemen is geen beslisregel; een bevoegdheid, beslissing of rechtsgevolg mag als kenmerk worden beschreven. Exacte tekst: synthese §2.

**Record:** "of voorwaarden" en de voorwaardenzin vervallen; toetsvraag naar de functie; `type` → "gehele definitie"; bron → "ASTRA (verwijst naar DBT §4.2)"; ASTRA-paar behouden plus sprekender functievoorbeelden (✅ stelselmatige dader, ❌ Ppw-discretie); patronen alleen als leeshulp, nooit als afkeur.

**App (T):** nu de bestaande reviewroute met INT-02-passagehulp naar het ESS-04-model (nieuwe toetsvraag, per passage de neutrale functievraag, ook een waarschuwing zonder signaal, volledig zinsdeel citeren), reden zichtbaar in de UI, lege kern of ontbrekende context → "niet uitgevoerd". Geen cijfer. Een AI-beoordeling naar het ESS-03/ESS-05-patroon is een aparte latere keuze. Exacte meldingen: synthese §4.

**Prompt en skills (G):** de instructie omdraaien — criteria en afleidingen behouden, geen voorschrift of afweging in de kern — binnen het bestaande één-zin-uitvoercontract; nieuw skillcontract `references/int02-beslisregel.md` (N/G/T/H) in `toetsregels` en `nederlandse-definities`; de regel "vermijd voorwaardelijke formuleringen" in beide skills vervangen. Exacte teksten: synthese §3 en §6.

**Herstel (H):** niet activeren; ontwerp onder DEF-638: alleen op verzoek, één poging, alleen een niet-begripsbepalende proceszin afsplitsen; stoppen bij elk criteriumverlies of betekenisverschuiving ("moet" schrappen, "indien" schrappen en "geheel getal" toevoegen zijn géén stijlcorrecties).

## Jouw keuzes

| K | Vraag | Voorkeur A+B | Alternatief en gevolg | Onderscheidende casus |
|---|---|---|---|---|
| **K1** | Normbereik: alleen discretionaire beslisregels (eng, letterlijk ASTRA's Beslisregel-definitie) of ook zelfstandige actorvoorschriften/procedures (breed)? Beschreven rechtsgevolg/bevoegdheid en criteria in voorwaardelijke vorm voldoen onder beide | **Breed** — ASTRA's Achtergrond én het eigen ASTRA-foutvoorbeeld (een verplichting zonder discretie) steunen dit; B noemt het eerlijk een lokale operationalisering | Eng → ASTRA's eigen voorbeeld en "aanvraag die de behandelaar moet afwijzen…" zijn geen INT-02-fout meer (hooguit ARAI-04 of niets) | C02, C52, C15 (alleen breed VN) ↔ C12, C13 (beide VN) |
| **K2** | Evaluatorstrategie | **O1 nu** (menselijke passagehulp, reden zichtbaar, geen model); O2 (AI-beoordeling) later als eigen besluit met goldset | O2 direct → prompt-/modelversie, kosten, privacy, foutbeleid nu beslissen (DEF-815, ADR-001) | C12, C13, C55, C59 |
| **K2b** | Signalen (detail van K2) | **S1 (A én B na verwerking)**: bestaande patronen blijven leeshulp, beperkt aangevuld met zinsdeelmarkers voor discretie ("van oordeel is", "naar eigen inzicht"), met citaat en positie; zonder "moet" en zonder losse woorden als "acht/redelijk"; nooit afkeur op een signaal. Jij kiest alleen de concrete markerlijst | S0 (alleen bestaande patronen) → C13/C83 blijven signaalloos; brede lijst → woord→verdacht-risico | C13, C83, C59 |
| **K3** | Record, voorbeelden, prompt en skills als één versiegebonden contract (ESS-03-patroon); ASTRA-paar behouden met de gecorrigeerde `example_pair_reason` (tekst van B, door A overgenomen) en extra functievoorbeelden | **Ja** | Alleen prompt → G en T blijven uiteenlopen; alleen record → de hardcoded G blijft | C02, C10, C12, C50 |
| **K4** | Zelfstandige INT-02-blokkade van vaststellen/export? | **Nee, als expliciet besluit** (open/negatief zichtbaar; integrale expertvaststelling apart). Let op: het is nú geen besluit — de gate leest INT-02 toevallig niet | Wel een poort → apart productbesluit met betrouwbare snapshot vooraf (DEF-624/626/630) | C67 |
| **K5** | Herstel (H) | **Niet activeren**; ontwerp met de stopregels uit synthese §5 onder DEF-638 | Activeren → eerst diagnose-, semantiek- en snapshotacceptatie | C31, C32, C63, C64, C65 |

**Bestaand beleid uitvoeren (geen keuze):** context verplicht vóór toetsen (K-9 ESS-05) → "niet uitgevoerd" zonder context; lege kern → "niet uitgevoerd"; INT-02-reden zichtbaar in de UI; geen totaalscore; toetsen wijzigt nooit tekst. **Wat bestaand beleid herstelt zonder nieuw normbesluit:** record naar ASTRA (type, bron, "of voorwaarden" weg), O1-passagehulp, UI-zichtbaarheid, restanten markeren. **Wat een nieuw normbesluit vraagt:** K1, K3, K4 (en K2b als detail).

**Geparkeerd (buiten dit besluit):** INT-10 `indien` (eigen onderzoek volgt); INT-01-woordlijst (K1–K-S bij DEF-770); open review niet in `issues_uit_validatieresultaat` (DEF-626); dode `IntegrityRulesModule` en `.py`-restanten (DEF-624/625); DBT §4.2 lezen (DEF-625).

## Bewijsgrenzen

Synthetische gevallen (geen gevalideerd recht); serviceproeven en promptrendering op moduleniveau; geen UI-, opslag-, gate-, export- of modelproef; geen beoordelaarstest; DBT niet gelezen. Overeenstemming van drie modellen is geen normbewijs; een promptwijziging bewijst geen betere generatie.

## Niet gedaan (bewust)

Geen implementatie, normwijziging, skillwijziging, Linear-issue of -publicatie, geen overgang naar INT-03 (loopt in je andere sessie). Publicatie bij DEF-771 kan na jouw akkoord.
