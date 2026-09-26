# DEF-771 — afvinkbare takenlijst

Bijgewerkt: 25 september 2026. Basis: [plan-v1.md](plan-v1.md); korte werkstaat: [processtatus-uitvoering.md](processtatus-uitvoering.md).

Branch: `feature/DEF-771-int02-contract-o1`. Basiscommit: `0d26f0f4f5b2ebebe1c7d71fbff5e4ddb66b8c0d`.

**Huidige fase:** voorbereiding afgerond; wacht op akkoord van Chris in deze chat. **Volgende taak:** A01. Er is nog geen implementatie gestart.

De coördinator houdt deze lijst bij na iedere afgeronde stap. Een vinkje betekent dat de genoemde voltooiingsvoorwaarde met bewijs is gehaald. Bij afvinken worden datum en bewijsverwijzing toegevoegd; lopende taken krijgen `BEZIG`, geblokkeerde taken krijgen de concrete oorzaak. Voor elke wijziging wordt een unieke herstelkopie bewaard. Planinhoud en eerder gegeven akkoord worden niet door het afvinken uitgebreid. Eén werkpakket tegelijk; de lijst maakt geen achtergrondmonitor of automatische uitvoering actief.

## Voorbereiding — uitgevoerd

- [x] V01 — Actuele `origin/main` ophalen en featurebranch daarvan maken. Bewijs: fetch en branchcontrole op 25-09; basiscommit hierboven.
- [x] V02 — Besluiten, synthese v5, casusregister v5, besluitnotitie en opdrachttekst lezen; opdracht-SHA controleren. Bewijs: inventarisatie en SHA in plan-v1.
- [x] V03 — DEF-771, DEF-831, DEF-832, DEF-624 en DEF-830 via Linear ophalen. Bewijs: actuele status en bronverwijzingen in plan-v1.
- [x] V04 — Actuele codeplaatsen, projectregels, beheerde skillbron en afwijkende lokale kopieën controleren. Bewijs: geciteerde plaatsen en hashes in plan-v1.
- [x] V05 — Uitvoeringsplan met werkpakketten, omvang, tests, casussen en open keuzes vastleggen. Bewijs: plan-v1.md; processtatus-uitvoering.md.

## Akkoord en startvoorwaarden

- [ ] A01 — Akkoord van Chris op plan en vervolg ontvangen en met datum/bericht vastleggen. De vraag om deze takenlijst is nog geen uitvoeringsakkoord.
- [ ] A02 — Publicatie van skillwijzigingen in de tweede repository vastleggen: voorstel is een geïsoleerde skillbranch met gekoppelde tweede PR. Ook afhandeling van afwijkende actieve skillkopieën bepalen vóór publicatie.
- [ ] A03 — Contractkeuze voor verplichte context vastleggen: voorstel `context_lists` plus exacte INT-02-NE-melding; betreft de extra servicewijziging uit plan-v1.
- [ ] A04 — Nieuwe C1-proefversie vastleggen: oud script en bewijs behouden; context voor RR-gevallen, aparte NE-gevallen en nieuw resultaatbestand. Verschil met de historische proef expliciet maken.
- [ ] A05 — Voor de eerste uitvoerdersopdracht beide CLI's op bruikbare toegang controleren; versies zijn al vastgesteld. Werkboom, scope, herstelkopieën en schrijverschap vastleggen. Geen toepassingsmodelcall voor deze controle.

## WP1 — canoniek contract

- [ ] W1.1 — Afzonderlijk akkoord voor WP1 vastleggen: acht bestanden, geraamd 220–340 regels, verspreid over app en beheerde skills. Gebruik een al gegeven expliciet akkoord; vraag het niet opnieuw.
- [ ] W1.2 — Volledige Claude-opdracht opslaan als `wp-1-opdracht-claude.md`; Prompt Forge alleen gebruiken bij bereikbare backend, anders dossieropslag volstaat. Rol, scope en verbod op verdere delegatie opnemen.
- [ ] W1.3 — Claude laat contracttests eerst falen; RED-log met testcommando, bronversie en exitstatus bewaren.
- [ ] W1.4 — Claude levert canoniek N/G/T/H-contract, bytegelijke skillkopie, exacte recordteksten, versie/datum, bronannotatie, voorbeelden en beide skillblokken volgens B1/B4 en synthese §2–§6.
- [ ] W1.5 — Contracttests en relevante lintcontrole groen; coördinator controleert letterlijke tekst, versiebinding, ASTRA-paar, beide kopieën en casus-ID's. Bewijs en diff-identiteit vastleggen; Chris kort terugkoppelen.

## WP2 — generatie-instructie

- [ ] W2.1 — Volledige opdracht `wp-2-opdracht-claude.md` opslaan en Claude de promptrenderingtests eerst rood laten uitvoeren; RED-log bewaren.
- [ ] W2.2 — Claude vervangt uitsluitend de INT-02-G-instructie door de exacte tekst uit synthese §3, binnen het bestaande één-zin-uitvoercontract.
- [ ] W2.3 — Modulerendering met en zonder voorbeelden bewijst exact nieuwe G en afwezigheid oude zin; relevante lintcontrole groen. INT-01/INT-02-voorbeeldconflict rapporteren; diff en bewijs vastleggen; Chris kort terugkoppelen.

## WP3 — O1 en S1

- [ ] W3.1 — Concrete S1-markerlijst met verwachte treffers en vals-alarmrisico bij C13/C59/C83/C105 aan Chris voorleggen en zijn expliciete akkoord vastleggen. De kandidaten in plan-v1 zijn nog niet goedgekeurd.
- [ ] W3.2 — Afzonderlijk omvang- en resultaatcontractakkoord voor WP3 vastleggen, inclusief A03/A04 en de definitieve bestandenlijst. Volledige opdracht `wp-3-opdracht-claude.md` opslaan.
- [ ] W3.3 — Claude schrijft en draait falende tests voor RR/NE, exacte reden, volledig zinsdeel en positie, markergrenzen en zichtbare UI-reden; RED-log bewaren.
- [ ] W3.4 — Claude implementeert O1, de goedgekeurde S1-lijst en de contextafhandeling. Zeven bestaande signalen blijven leeshulp; geen pass/fail of score uit signalen; geen poort, herstel of O2.
- [ ] W3.5 — Gerichte tests en lint groen; coördinator controleert C02/C04/C06/C13/C23/C50/C54/C56/C59/C83/C105 en ongewijzigde tekst. De definitieve S1-lijst bepaalt of C02 een signaal krijgt; de signaalloze waarschuwing blijft in elk geval bewezen met C105.
- [ ] W3.6 — Goedgekeurde nieuwe C1-proef uitvoeren; verwacht/werkelijk, contextvariant, passage, positie, status, bronversie en exitstatus bewaren in `proef-c1-uitvoering-na-o1.json`. Historisch bewijs behouden; Chris kort terugkoppelen.

## WP4 — bestaande tests herijken

- [ ] W4.1 — Opdracht `wp-4-opdracht-claude.md` opslaan; vastleggen welke bestaande verwachting na de contextwijziging rood wordt. Een al groene test niet kunstmatig rood maken.
- [ ] W4.2 — Claude hernoemt `test_int02_no_decision_rules_fail` en herijkt C24/C25 met expliciete context en brede norm; fixturetoelichting actualiseren. Geen geval verwijderen; contextloze NE-dekking behouden.
- [ ] W4.3 — Gerichte golden- en runtime-matrixtests groen; C24/C25 geven met context RR en geen automatische afkeur op “indien”. Diff, lint en bewijs controleren; Chris kort terugkoppelen.

## WP5 — verificatie en onafhankelijke review

- [ ] W5.1 — Definitieve diff, base/head of hashes en RED/GREEN-bewijs vastleggen. Reviewopdracht volledig opslaan; ook de skilldiff uit de tweede repository opnemen als die is goedgekeurd.
- [ ] W5.2 — Verse afzonderlijke Codex CLI-sessie in aparte werkroot laten reviewen tegen B1–B6 en synthese §3/§4/§6; reviewer wijzigt geen bronbestanden. Sessieverwijzing en reviewrapport bewaren.
- [ ] W5.3 — Iedere bevinding inhoudelijk beoordelen en afhandelen. Bevestigde correcties door dezelfde Claude-uitvoerder; dezelfde Codex-reviewer controleert de correctiediff. Bewijs moet bij de uiteindelijke bestanden horen.
- [ ] W5.4 — `make test`, `make lint` en volledige offline `pytest` uitvoeren; letterlijke uitkomsten en oorzaak per failure bewaren. Geen live modelcalls of productiedata; eventuele blokkade zichtbaar laten.
- [ ] W5.5 — Eindcontrole op contractgelijkheid, casusdekking, tekstbehoud, geen verwijderingen en geldige actieve skillversies. Bewijsgrenzen expliciet houden; geen claim op generatiekwaliteit of volledige opslag-/exportketen zonder bewijs.

## WP6 — oplevering

- [ ] W6.1 — App-PR en eventueel goedgekeurde gekoppelde skill-PR maken met besluiten, wijzigingen, bewijs en uitgesloten werk; PR-links vastleggen. Geen merge zonder Chris.
- [ ] W6.2 — Oplevercomment op DEF-771 plaatsen met dezelfde bewijsbasis, contract-SHA-256 en DEF-831/832-koppelingen; uitsluitend bewezen acceptatiecriteria afvinken.
- [ ] W6.3 — O2-vervolgissue pas na expliciet akkoord van Chris aanmaken; goldset, versies, kosten, privacy, foutbeleid, citaatcontrole en relaties opnemen. Bij uitgesteld akkoord deze taak open laten.
- [ ] W6.4 — Eindbericht met branch/commits, PR's, werkelijk gebruikte CLI-sessies, testresultaten en open vervolgwerk: O2, effectmeting, DEF-626, DEF-830 en CON-01-keuze in DEF-831.

## Bewijs en hervatten

Volledige opdrachten, testlogs, reviewrapporten en proefuitvoer worden eenmaal opgeslagen onder `gedeeld/uitvoering/`, met verwijzingen vanuit de afgevinkte taak. Bij hervatten eerst deze lijst, de korte processtatus, het geldige akkoord en de laatste diff-identiteit lezen. Alleen gewijzigde of nog open onderdelen opnieuw onderzoeken. Een geopende PR of een positieve review vervangt geen functioneel testbewijs.
