# CON-02 — browserbewijs generatie en teruglezen, 17 september 2026

## Scope
Echte Streamlit-generatie op commit `d17ea9c30915452914e450be315620e314c03468`, eigen tijdelijke database, model `anthropic/claude-opus-4-8`. Generatie `6e6f8d00-83c0-42e3-b696-ce361cc8cb2d`, record 4. Dit is een van P01 afgeleide generatieprobe; de gegenereerde definitie wijkt af van de vaste casus. Geen volledige P01-pass en geen deskundige acceptatie.

## Invoer en waarneming
- Begrip: besluit; juridische context: Bestuursrecht; wettelijke basis: Algemene wet bestuursrecht.
- Exacte upload `awb-1-3-20260815.txt`: 708 tekens, geselecteerd voor documentcontext.
- UI: documentcontext gebruikt, vier fragmenten in de generatieprompt; weblookup leverde geen resultaat door timeout (10 seconden).
- Generatie geeft: “Resultaat van besluitvorming door een bestuursorgaan in de vorm van een schriftelijke beslissing die een publiekrechtelijke rechtshandeling inhoudt.”
- UI generatie: alle drie CON-02-onderdelen “Voldoet”, herkenbaar als AI, zonder totaalcijfer. De algemene vaststellingsgate blijft geblokkeerd vanwege andere regels.
- Daarna navigatie naar Bewerk en openen van “Bronbasis (CON-02) — opgeslagen record”. Hetzelfde positieve CON-02-oordeel wordt uit het opgeslagen record getoond.
- Readback toont: “Brontransport (kwitantie): rag: 0 van 0 aangeleverd in prompt (aan) · web: 0 van 0 aangeleverd in prompt (aan) · document: 4 van 4 aangeleverd in prompt (aan)”.
- Eerste bron: `doc:01e121c20018eed2#7118848e`; UI: versie onbekend, vindplaats onbekend, gedeclareerd profiel onbekend. Geen bronhyperlink.
- Verwijskwaliteit: voldoet, reden dat regeling, artikel en lid in de passage genoemd worden. Expliciete onzekerheid: exacte versiedatum/geldigheid op peildatum is niet af te leiden.
- Opgeslagen JSON bevestigt: alle bron-URLs null; alle bronversies null; peildatum null; geen deskundige uitzondering. Zie `generatie-record4-v1.json`.

## Beoordeling van het bewijs
Het ontbreken van een bronlink leidt hier niet tot een open verwijsoordeel. Een exacte tekstuele vindplaats wordt als voldoende behandeld. Dit is de te triëren contractafwijking. Onbekende versie/geldigheid blijft apart van de hyperlinkfout; deze run bewijst niet dat de passage inhoudelijk onjuist is. De UI en het opgeslagen record stemmen overeen. Export, formele vaststelling en volledige herstart zijn met deze probe nog niet getest.

Vastgelegd door Codex op basis van Playwright-DOM-waarnemingen en een alleen-lezen SQLite-extract. Geen deskundigennaam of akkoord ingevoerd. Geen broncode gewijzigd.
