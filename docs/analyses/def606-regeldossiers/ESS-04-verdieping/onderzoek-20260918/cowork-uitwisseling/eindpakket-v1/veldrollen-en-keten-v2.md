# ESS-04 — geïntegreerde veldrollen en ketengrenzen

18 september 2026. Herziene uitwerking van beide Q2/Q4-onderzoeken en hun kruisreviews. TO=toetsobject; B=bewijs; G=mogelijk generatievoorstel; P=presentatie. Alleen de definitiekern is het ESS-04-toetsobject; bewijsvelden worden niet stil aan die kern toegevoegd. Dezelfde inhoudelijke norm geldt bij genereren en uitsluitend toetsen.

| Veld | Rol en noodzaak | G/T/H-grens |
|---|---|---|
| Term/begrip | Identificeert bedoelde betekenis; geen trefwoordbewijs | G gebruikt bevestigde betekenis; T verandert term niet; H vraagt verduidelijking bij homoniem. |
| Definitiekern | TO, verplichte inhoud voor criteriumbeoordeling | G formuleert criteria; T beoordeelt exact ontvangen kern; H uitsluitend apart voorstel. Leeg→geen inhoudelijk ESS-04-oordeel. |
| Gestructureerde context | B; nodig waar zij betekenis/toepassing beslist | Geen registratiecontext herhalen zonder betekenisfunctie. CON-01 bepaalt identiteit/contextgrens; noodzakelijke naam blijft mogelijk. |
| Definitiebronnen | B; betekenisgrond voor drempel/criterium, status volgens CON-02 | Geen getal/bron verzinnen. Publicatiedatum, geldigheid en gevalstijd uiteenhouden; recency is geen automatische voorrang. |
| Ontologie/relaties | B/G; helpen object, verhouding en telpopulatie bepalen | Geen compleet UFO-model eisen voor eenvoudige definitie. ESS-02 niveau/aard en ESS-03 instantie-identiteit niet vervangen door ESS-04. |
| Praktijkvoorbeelden | B als scenario en beslissende gegevens controleerbaar zijn en verwacht oordeel onafhankelijk gegrond is | Persoonsidentificatie niet vereist. Onderzoeksbeperking apart: hier uitsluitend synthetisch, geen productiegevallen. |
| Tegenvoorbeelden | B/G; tonen een concreet falend criterium, geen universeel bewijs | Geen willekeurig ver verwijderd begrip; label vooraf op betekenisgrond, geen modelconsensus als gold. |
| Grensgevallen | B/G; op en naast grens of relevant interpretatiepunt | Ook eenduidige grenscase is grenscase. Geen voorbeeld nodig om reeds expliciet minimaal als inclusief te lezen; voorbeelden helpen controleren. |
| Synoniemen | B/G/P waar betekenisidentiteit relevant is | Geen ESS-04-verplichting om lijst te vullen. Gedeelde criteria aantonen; overeenkomstig woord geen bewijs. |
| Homoniemen | B/G waar meerdere betekenissen spelen | Geen bank-meubelbewijs gebruiken voor bank-instelling. H verandert betekenis niet stil. |
| Toelichting | B/P/G voor methode en bewijsplaats | Essentiële noemer/populatie/beperking niet uitsluitend hier verstoppen. Methodische verduidelijking mag apart. T beoordeelt geen samengeplakte andere kern. |
| Meet-/toepassingsmetadata | B wanneer interpretaties andere uitkomsten geven | Teller/noemer, uitsluitingen, afronding, inclusie, startmoment, tijdzone, dagconventie alleen waar relevant. 0/0 zonder conventie open; geen standaard0/100. |
| Review-/versiemetadata | Registratie van daadwerkelijk oordeel, geen inhoudelijk vervangbewijs | Passage/grond/conclusie, relevante onzekerheid, actor/rol/tijd en tekst/context/bron/normbinding. Callerstring of modeltekst geen bevoegd oordeel. |

Betekenisgrond bepaalt wat criterium bedoelt; toepassingsgrond ondersteunt de beoordeling van een geval; reviewregistratie legt vast wie wat beoordeelde. Geen van deze lagen vervangt een andere. Voorstelvelden zijn geen opgeslagen, vertrouwde brongegevens.

## Relevante ingangen

| Ingang | Aangetoond | Nog nodig / gevolg |
|---|---|---|
| Genereren | Echte module-aanroep P03 blijft cijfergericht; één ruwe tekst P04 extractie/cleaning behoudt grens | Volledige eindprompt, brontransport, modeluitvoer en opslag. Ondersteunde verduidelijkingsroute vóór G2-uitrol. |
| Losse tekst/Definition toetsen | P01 directe evaluator, actuele orchestratorcode behoudt invoer;14caseproef | Volledige UI-/serviceketen niet uitgevoerd. Uitsluitend toetsen verandert kern niet. |
| Import | Gelezen import_single valideert preview, gebruikt preview.ok niet als ESS-04-poort; geen eigen cleaningaanroep | Geen ESS-04-readback/UI-proef. Conceptimport is niet vaststellen; geen absolute scoreNone-blokkade claimen. |
| Bewerken | Algemene editroutes aanwezig; menselijke review moet aan versie binden | Geen actuele ESS-04-stale-proef. Niet uit afwezige ESS-04-string afleiden dat generieke invalidatie ontbreekt. |
| Menselijke review | Automatische status vereist review; CON-01/02 concrete routes en algemene expertbeoordeling aanwezig | Geen aangesloten actuele ESS-04-schrijf-/readbackroute aangetoond; geen twee menselijke reviewers uitgevoerd. |
| Conceptopslag | Generieke conceptpaden gelezen | Notitie/JSON niet automatisch vertrouwde review; exacte opslag en herladen testen. |
| Vaststellen | Gelezen gate heeft CON-voorwaarden/context/score/issues, geen algemene review_required-check; YAML override true | Algemene DEF-630-eis uitvoeren met regellokale besluiten; actieve overlay en runtimeketen niet getest. Geen ESS-04-eigen positief akkoord afleiden. |
| Export/herbeoordeling | Exportgate conditioneel; huidige normalisatie bewaart reviewvelden | Alle formele exportpaden, open/negatieve status, versie-/actorbinding en stale na wijziging nog uitvoeren. Geen exportclaim op basis van één helper. |

## Diagnose vóór herstel

| Diagnose | Benodigd onderscheidend bewijs | Vervolg |
|---|---|---|
| Generatieovertreding | Bron/instructie aantoonbaar ontvangen; ruwe output wijkt af | Apart voorstel met bekende grond. |
| Tegenstrijdige instructies | Volledige prompt eist onverenigbare criteria | Eerst instructiecontract herstellen. |
| Invoer-/transportverlies | Invoer verschilt van verzonden prompt/toets-/opslagobject | Transport herstellen, geen bron verzinnen. |
| Foutpositief signaal/oordeel | Signaal zonder normschending, of onterecht negatief inhoudelijk oordeel | Signaal en oordeel afzonderlijk corrigeren; geen cijfer toevoegen. Huidige ESS-04-evaluator geeft geen inhoudelijke fail. |
| Ontbrekende grond | Betekenis-/methodegrond versus gevalsgegevens afzonderlijk vastgesteld | Benoem wat ontbreekt; geen automatische definitierepair. |
| Technische fout | Dienst-/schema-/runtimefout | Error en kandidaat bewaren; geen inhoudelijke fail. |
| Schadelijke nabewerking | Correcte ruwe output, latere kandidaat verschuift criterium | Lokaliseer verschil; hertoets werkelijk opgeslagen kandidaat. P04 bewijst dit defect niet. |

Twee beoordelaars kunnen verschillen door betekenis-/bronkeuze, gevalsbewijs, toepassingsfout of resterende beoordelingsruimte. Kalibratie legt oorspronkelijke oordelen vast; meerderheid is geen normbesluit. Automatische repair blijft afzonderlijk beleid onder DEF-638, maximaal één poging indien later geactiveerd, stop bij conflict/ontbrekend bewijs/betekenisverlies/herhaling. Geen totaalscore als doel.
