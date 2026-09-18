# CON-02: deelchecks, grenzen en scorebeleid

## Geldende basis

Deze uitvoeringsindeling volgt het vastgelegde CON-02-contract uit `../con02-acceptatie-20260916-v1/basis/besluiten-20260915-v3.md`, het bestaande casusregister en `../con02-acceptatie-20260916-v1/synthese-en-beslispunten-v1.md`. Dit document voegt geen nieuwe normbesluiten of deskundige akkoorden toe. Geteste appcommit: `d17ea9c30915452914e450be315620e314c03468`.

| Deelcheck | Invoer | Uitvoerder en automatisering | Grens / ontbrekende informatie | Scorebeleid |
|---|---|---|---|---|
| Feitelijke bronaanvoer | Ontvangen passages, kanaal, inhoudshash, generatie- en beoordelingskwitanties | Deterministische controle van identiteit, inhoud en daadwerkelijke doorgifte | Een gevonden/uploadbare bron is nog niet ontvangen bewijs; zoekscore of route bewijst geen gezag | Geen inhoudelijke pass door alleen transport; geen cijfer |
| Brongezag en toepasselijkheid | Identificeerbare bron, herkomst, versie, context, gekozen betekenis en relevante peildatum | Toegestane AI-inhoudsbeoordeling met herleidbare citaten; deskundige kan beoordelen/corrigeren | Bronlabel, wetnaam of bestandsdatum bewijst geen authenticiteit of geldigheid; onzekerheid expliciet maken | Afzonderlijke uitkomst, geen deel- of totaalcijfer |
| Betekenissteun | Definitieversie en bepalende kenmerken/beperkingen/uitzonderingen tegenover ontvangen passages | Toegestane AI-claimvergelijking, citaten deterministisch controleren; deskundige acceptatie apart | Ontbrekende passage is niet hetzelfde als bewijs van onjuistheid; volledige corpuskennis is niet automatisch modelinvoer | Afzonderlijke uitkomst, geen deel- of totaalcijfer |
| Verwijskwaliteit | Precieze/beknopte vindplaats, bronversie en gerichte bruikbare hyperlink bij het record | Brondata + deterministische aanwezigheid/binding; inhoudelijke precisie/compactheid via AI of deskundige | Tekstuele locator vervangt de vereiste link niet. DEF-806 toont een tekort in de huidige positieve controle | Afzonderlijke uitkomst; uitzondering blijft uitzondering; geen cijfer |
| Geen passende bron | Gedocumenteerde zoekinspanning, context/versiebinding, motivering en expliciete acceptatie | Alleen bevoegde deskundige; technische binding deterministisch | Geen automatisch akkoord en niet afleiden uit een enkele mislukte zoekactie | Zichtbare uitzondering, geen gewone pass |
| Bron zonder bruikbare hyperlink | Bestaande bron, bewaarde versie, stabiele bronidentiteit, exacte locator, motivering | Alleen bevoegde deskundige; technische voorwaarden/binding controleren | Niet toepasbaar wanneer bruikbare link beschikbaar is (P31); ontbreken in record is geen onbeschikbaarheid | Zichtbare uitzondering, geen gewone pass |
| Herstelvoorstel | Vastgestelde concrete tekortkoming en voldoende bronbewijs | Alleen op verzoek maximaal één voorstel; menselijke toepassing en hertoetsing | Verwijstekort is geen reden om automatisch de definitiezin te wijzigen; geen verzonnen bronbewijs | Geen automatische acceptatie of scorewinst |
| Vaststelling / export | Alle relevante regeluitkomsten, ontbrekende beoordelingen en actuele versie | Bestaande appgate + menselijke vaststelling | CON-02-pass heft andere blokkades niet op; draft herkenbaar concept | CON-02 zonder cijfer; geen samengestelde kwaliteitsscore |

## Huidige bewijsstatus

- De echte generatieprobe en editorreadback tonen drie afzonderlijke AI-oordelen zonder totaalcijfer.
- Zonder bronbewijs bleven de drie onderdelen in de browser open; dit is een beperkte invarianttest met een onvolledige importpreconditie.
- DEF-806 bevestigt dat de verwijzingscontrole de gewenste grens nog niet afdwingt.
- De 31 casussen zijn een te beoordelen set, geen vooraf goedgekeurde goldset. Alle deskundigenvelden blijven open totdat een persoon ze expliciet invult.
- Positieve CON-02-acceptatie: **no-go** totdat DEF-806 is hersteld en hertoetst, volledige vereiste ketendekking is aangetoond en de deskundige oordelen zijn vastgelegd.
