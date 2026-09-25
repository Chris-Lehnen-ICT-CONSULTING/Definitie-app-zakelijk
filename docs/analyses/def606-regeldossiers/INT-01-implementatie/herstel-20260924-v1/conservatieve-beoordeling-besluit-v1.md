# INT-01 — conservatieve automatische beoordeling

24 september 2026. Leidend besluit na de blokkade in astra-correctiereview-v3. Bron: Chris koos na de stapsgewijze bespreking richting 1 en gaf opdracht: “ok helder werk dat uit en doe dat”. Dit autoriseert een nieuwe aanpak; geen vierde uitzondering binnen de verworpen aanname.

## Afspraak

1. De inhoudelijke norm blijft één compacte, begrijpelijke formulering. Een naamwoordelijke kern met noodzakelijke bepalingen kan daaraan voldoen. Compactheid, begrijpelijkheid en eventuele broncitaatbeoordeling blijven afzonderlijk open; een automatische zins-pass is nooit een volledige INT-01-pass.
2. De app beslist alleen over zinsstructuur binnen ondersteunde herkenningspatronen. Een voldoende ondersteunde tweede zelfstandige zin geeft fail. Onvoldoende bewijs geeft review_required met vindbare passage, positie en reden. Lege invoer blijft not_evaluated.
3. Een kaal woord plus voorzetselgroep vóór een werkwoord bewijst geen onderwerp. Dit patroon wordt onzeker. Dit geldt ook voor de oude T24-tekst, waarvan het normatieve fail-label ongewijzigd blijft. Het automatische verwachte gedrag wordt expliciet anders onder dit nieuwe contract. Geen proefwoordlijsten, geen aannames dat invoer grammaticaal correct is.
4. De bestaande positief ondersteunde patronen blijven bruikbaar binnen hun beperkte bereik. Onbekende syntaxis blijft onzeker. Geen nieuwe NLP-afhankelijkheid. De implementator beschrijft exact welke patronen nog automatische zekerheid krijgen; de reviewer controleert die claim met gerichte tegenhangers.
5. De evaluatieversie stijgt van /2 naar /3, omdat de beslisbetekenis wijzigt. Opgeslagen /1- en /2-resultaten mogen niet als actuele /3-beoordeling worden getoond. Bestaande herbeoordelingsroute gebruiken, geen schemawijziging.

## Uitvoering en bewijs

- Dezelfde Claude Code CLI-uitvoerder past classifier, relevante tests en zo nodig gekoppelde skillreferenties aan. Eerst gerichte RED, daarna GREEN en lint; unieke herstelkopieën. Historische proefsets, labels, resultaten en eerdere reviews blijven intact.
- Dezelfde Codex CLI-reviewer (Astra/high) controleert de nieuwe concrete delta en de open R1; eerdere ongewijzigde reviewbewijzen blijven geldig. Root voert de brede unitgate eenmaal uit op de uiteindelijke bron.
- Skillsbundels alleen bij bronwijziging opnieuw bouwen en controleren. Geen live activatie wegens ALG-391. Bestaande conceptPRs 474/356 actualiseren; dit besluit autoriseert geen merge.
- Nieuwe T24: vooraf nieuwe set door onafhankelijke maker; A/B en adjudicator beoordelen vóór uitvoering zowel normatieve zinsstatus als verwachte automatische dispositie volgens dit besluit. De referentie houdt deze twee assen uit elkaar. Onzekerheid mag niet achteraf als goed gerekend worden wanneer vooraf een automatische beslissing verwacht werd.
- T24 rapporteert: automatische pass/fail ten opzichte van normatieve referentie; automatische dekking (pass+fail / niet-lege gevallen); aantal doorverwijzingen en hun normatieve verdeling; contractconformiteit inclusief beide laadpaden/opslag. Geen retroactieve herwaardering van oude 18/24. Vrijgave vraagt nul onjuiste zekere beslissingen, overeenstemming met alle vooraf verzegelde automatische verwachtingen en aantoonbaar zowel zinvolle pass- als fail-beslissingen. Geen claim van bewezen bruikbare dekking of algemene taalkundige betrouwbaarheid op basis van slechts 24 gevallen. Geen drempel uit de uitkomsten kiezen.
- G24 behoudt eerdere effectcriteria: minstens één inhoudelijke verbetering, geen nieuwe bron-/betekenisfout, geen verslechtering per gepaarde invoer. Nieuwe blinde A/B-beoordeling en adjudicatie. Uitkomst die niet voldoet wordt als zodanig gerapporteerd.
- Betaalde proefkosten blijven cumulatief onder het eerder goedgekeurde US$5-plafond: al besteed US$1.940235, resterend US$3.059765. Eerst manifest en tokentelling. Geen betaalde calls zonder passende raming binnen dit restant.

## Reikwijdte

Dit besluit vervangt voor deze nieuwe proef de eis dat elke inhoudelijk meerzinnige tekst automatisch fail moet krijgen. Het wijzigt geen historische normatieve labels en geeft geen vrijbrief voor altijd-doorverwijzen. De eerdere proefafspraken-v1 blijven historisch; deze delta moet vóór de nieuwe referentiebeoordeling zijn vastgelegd.
