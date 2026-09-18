# CON-02 — onafhankelijke Codex-voorbeoordeling

16 september 2026. **AI-voorstel voor menselijke beoordeling; geen deskundige acceptatie en geen uitgevoerde app-test.** Opgesteld vóór ontvangst van Coworks nieuwe voorbeoordeling. De juridische vergelijking geldt voor de bewaarde transcripties en gekozen context, niet als onderzoek naar het actuele volledige recht.

## Grondslag en leesregel

- Historische invoer: [94-casusregister](../con02-20260915-kruisreview/casusregister-geintegreerd-v2.json), `historisch_record_ongewijzigd` van C02-P01–P31.
- Actueel projectbeleid: [drie goedgekeurde besluiten](../con02-20260915-kruisreview/besluiten-20260915-v3.md). Historische open keuzes worden niet opnieuw voorgelegd.
- Broninhoud: de 13 vastgelegde fixtures uit `praktijk-20260914-v1/bronmanifest-v3.json`, geraadpleegd in de historische onderzoekswerkboom; byte-identieke lokale exemplaren horen in dit pakket.
- De drie beoordelingen zijn **B** = brongezag/toepasselijkheid, **M** = betekenissteun, **V** = verwijskwaliteit. G/T/H in het oude register betekenen generatie/toetsing/herstel, niet deze drie deeloordelen.

Een positief inhoudelijk voorstel veronderstelt dat de genoemde passage en bronversie werkelijk bij de beoordelaar aankomen. Een bestand in dit dossier bewijst dat niet voor de app. Waar een scenario geen concrete verwijzing of ontvangen bronset vastlegt, blijft dat onderdeel voor de uitvoering open. Een positieve AI-beoordeling is toegestaan; menselijke goldsetacceptatie en algemene vaststelling zijn afzonderlijke zaken.

## Eerste zes beslissingen

### C02-P01 — volledige definitie van besluit

**Definitie:** schriftelijke beslissing van een bestuursorgaan, inhoudende een publiekrechtelijke rechtshandeling.

**Bron:** S-AWB13, Awb-versie 2026-08-15, art. 1:3 lid 1. De transcriptie noemt exact schriftelijk, bestuursorgaan en publiekrechtelijke rechtshandeling.

**Voorstel:** B positief binnen het Awb-profiel; M positief. V positief uitsluitend wanneer versie, precieze vindplaats en bruikbare gerichte hyperlink zijn vastgelegd; de gegeven opdracht tot registreren is nog geen uitvoeringsbewijs. Geen tekstherstel nodig.

**Te beslissen:** ondersteunt de aangewezen passage de volledige definitie in deze context? Menselijk besluit: **open**.

### C02-P02 — te ruime definitie

**Definitie:** beslissing van een bestuursorgaan.

**Bron:** dezelfde S-AWB13 en lid 1 als P01.

**Voorstel:** B positief; M negatief omdat schriftelijkheid en de publiekrechtelijke rechtshandeling ontbreken. V afzonderlijk beoordelen zoals P01. Een goede verwijzing herstelt de te ruime betekenis niet. Alleen op verzoek een voorstel, met expliciete overname en hertoetsing.

**Te beslissen:** maakt deze weglating het begrip te ruim? Menselijk besluit: **open**.

### C02-P04 — bruikbare tekst, ontbrekende herkomstgegevens

**Definitie:** plicht van het bestuursorgaan om bij besluitvoorbereiding de nodige kennis over relevante feiten en af te wegen belangen te vergaren.

**Bron:** alleen S-UPLOAD32; de meegegeven wetszin bevat de relevante feiten én af te wegen belangen. Het bestand heeft zelf geen versie of URL. De dossiervergelijking met S-AWB32 wordt volgens het scenario niet automatisch aan de app verstrekt.

**Voorstel:** B nog te beoordelen op basis van de werkelijk aangeleverde herkomst; M inhoudelijk ondersteund door de aangeleverde zin, maar de afleiding van norm naar begripsomschrijving vraagt een expliciet oordeel. V onvoldoende onderbouwd. Een ontbrekend transportveld is een technische/onbekende situatie; een aantoonbaar ontbrekende vereiste verwijzing is een verwijstekort. Geen versie of gezag uit de bestandsnaam afleiden. Niet automatisch als deskundige uitzondering accepteren.

**Te beslissen:** is de begripsafleiding juist, los van het herkomst- en verwijstekort? Menselijk besluit: **open**.

### C02-P11 — dieren ten onrechte als zaken

**Definitie:** voor menselijke beheersing vatbaar stoffelijk object, waaronder een dier.

**Bron:** S-BW3, versie 2025-07-01, art. 2 en 2a beide leden. Art. 2a lid 1: “Dieren zijn geen zaken.” Lid 2 verklaart zakenbepalingen onder beperkingen toepasselijk.

**Voorstel:** B positief voor deze juridische context; M negatief. Toepasselijkheid van bepalingen maakt dieren niet tot zaken. V afhankelijk van de werkelijke registratie van de volledige passage. Dit verschilt van P10, waar de beperking buiten de opgehaalde top vijf valt.

**Te beslissen:** bevestig het onderscheid tussen kwalificatie en toepasselijke bepalingen. Menselijk besluit: **open**.

### C02-P16 — bronkenmerk omgekeerd

**Definitie:** kennisbank van onderling gelinkte markdown-pagina's die door een taalmodel wordt geschreven en onderhouden op basis van een verzameling bronnen die het taalmodel tijdens onderhoud herschrijft.

**Bron:** originele S-RAW, capture 2026-07-08, `Architecture / Raw sources`; noemt onveranderlijke bronnen die het model leest maar niet wijzigt. M-WIKI is een opzettelijke testmutatie.

**Voorstel:** B van de originele raw-capture passend bij het gekozen auteursconcept, mits de authenticiteitsbinding klopt; de mutant is geen onafhankelijke gezaghebbende bron. M negatief: brononderhoud door herschrijven keert het kernkenmerk om. V afzonderlijk aan raw-capture en locator binden. Oude `reviewed/high`-frontmatter maakt de gewijzigde tekst niet beoordeeld.

**Te beslissen:** is dit een inhoudelijke tegenspraak ondanks de bestaande frontmatterlabels? Menselijk besluit: **open**.

### C02-P31 — juiste betekenis, ontbrekende beschikbare link

**Definitie:** dezelfde volledige besluitdefinitie als P01. Label: `art. 1:3 lid 1 Awb`; hyperlink leeg.

**Bron:** S-AWB13 met vastgelegde versie. Het scenario stelt expliciet dat de primaire online bron gevonden is.

**Voorstel:** B en M positief binnen deze bronbasis; V negatief wegens de ontbrekende bruikbare gerichte hyperlink. De goedgekeurde verwijzingsuitzondering voor een bron zonder bruikbare hyperlink geldt hier niet automatisch: de link is juist beschikbaar. Repareer de verwijzing, niet de inhoudelijke definitie.

**Te beslissen:** bevestig dat alleen het verwijsonderdeel tekortschiet. Menselijk besluit: **open**.

## Dekking van alle 31 praktijkgevallen

Onderstaande verwachtingen zijn concrete aandachtspunten voor de uitvoering. **Geen rij is hiermee uitgevoerd of deskundig geaccepteerd.**

| Casus | Te beoordelen onderscheid / voorgestelde verwachting |
| --- | --- |
| P01 | Volledige Awb-betekenis kan positief zijn; verwijzing apart bewijzen. |
| P02 | Passende bron, te ruime betekenis door weglatingen. |
| P03 | BW3 is gezaghebbend maar niet toepasselijk als steun voor het Awb-besluitbegrip. |
| P04 | Tekststeun onderscheiden van onbekende herkomst en ontbrekende verwijzing. |
| P05 | Expliciete koppeling aan S-AWB32 maakt herkomst controleerbaar; normzin naar begrip blijft een afleiding. |
| P06 | Identieke bytes onder andere naam leveren geen onafhankelijke tweede bevestiging. |
| P07 | Gewijzigde tekst/hash onder dezelfde naam mag geen oude review erven; belangen zijn weggelaten. |
| P08 | Volledig lid 4 ondersteunt de beleidsregelparafrase, inclusief uitsluiting van algemeen verbindend voorschrift. |
| P09 | Lid 1 en score 0,99 bewijzen het beleidsregelbegrip niet; ontbrekend lid 4 niet als ontvangen aanmerken. |
| P10 | Buiten top vijf aanwezige dierenuitzondering is geen ontvangen bewijs; bevestiging inclusief dieren is niet gerechtvaardigd. |
| P11 | Volledige bron toont tegenspraak: dieren zijn geen zaken. |
| P12 | Ontbrekend letterlijk trefwoord sluit betekenissteun niet uit; daadwerkelijk meegestuurde passage vastleggen. |
| P13 | Werkelijke document-/chunk-ID, lid, versie en passage volgen door de keten; adaptertoevoegingen expliciet labelen. |
| P14 | Afgeleide wiki verwijst naar bronnen die niet zijn meegeleverd; primaire binding blijft onopgelost. |
| P15 | Gecontroleerde raw ondersteunt de afgebakende wiki-definitie; niet meegeleverde tweede bron niet als gelezen tellen. |
| P16 | Herschrijven van raw keert onveranderlijkheid om; oude kwaliteitslabels zijn geen bewijs. |
| P17 | Hashafwijking blokkeert de claim dat dit dezelfde gecontroleerde capture is. |
| P18 | Niet meegeleverde bron expliciet onopgelost; afzonderlijke claim kan op aanwezige raw beoordeeld worden. |
| P19 | Beschikking behoudt expliciete inclusie van afwijzing van een aanvraag daarvan. |
| P20 | Willekeurige persoon verbreedt aanvraag ten opzichte van belanghebbende. |
| P21 | Goed omvat zaken én vermogensrechten; definitie van zaak is te beperkt. |
| P22 | Geen zaken betekent niet dat zakenbepalingen nooit gelden; geen volledige biologische definitie uit art. 2a afleiden. |
| P23 | Upload/RAG/wiki zijn drie routes naar mogelijk dezelfde bron, geen drie onafhankelijke bronnen. |
| P24 | Echte eerdere review is voorwaarde; nieuwe bronbytes vallen niet onder oud oordeel. |
| P25 | Echte eerdere review van P01 is voorwaarde; gewijzigde definitie erft die niet. |
| P26 | `reviewed=true` zonder actor/bewijs/datum is geen bevoegde menselijke review. |
| P27 | Volledige binding bewaren bij opslag/herladen/export; zonder vereiste echte review alleen herkenbare draft, overige poorten blijven gelden. |
| P28 | Historische synthetische score blijft als input behouden; huidig beleid toont geen totaalcijfer en laat ontbrekend bewijs niet vervallen. |
| P29 | Algemene startpagina en label Awb zijn onvoldoende precies; betekenis kan correct blijven. |
| P30 | Verwijzing is precies, maar citeervorm volgens dossiernorm onnodig lang; verkorten zonder semantische afkeuring. |
| P31 | Beschikbare gerichte link ontbreekt: verwijstekort, geen automatische uitzondering. |

## Wat menselijke acceptatie vastlegt

Per geselecteerd geval: identiteit en rol van de beoordelaar, exact casus-ID en pakketversie, akkoord/afwijzing/aanpassing per relevant deeloordeel, motivering en datum. Een algemeen akkoord op voortgang is geen acceptatie van alle 31 of 94 gevallen. Bij echte afwijking wordt een nieuwe verwachtingsversie toegevoegd; historische scenario's blijven behouden.

Er zijn nog geen menselijke oordelen ontvangen. De appketenuitvoering en vergelijking met live modeloordelen volgen op vastgestelde verwachtingen; technische regressiebewijzen van PR454 blijven afzonderlijk beschikbaar.
