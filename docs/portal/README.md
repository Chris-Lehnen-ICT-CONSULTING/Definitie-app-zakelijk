Central Documentatie‑Portal (MVP)

Doel
- Eén centrale, interactieve pagina in deze repo om backlog (REQ/EPIC/US/Bug) en relevante documentatie (architectuur, richtlijnen, testing, compliance) te raadplegen.
- Data wordt gegenereerd uit frontmatter + mappenstructuur en inline in de pagina opgenomen (offline te openen).

Structuur
- docs/portal/
  - config/sources.yaml  (config voor te scannen paden)
  - index.html           (UI + inline data placeholder)
  - portal.js            (client‑side renderen/filters)
  - portal.css           (stijl)
  - viewer.html          (documentviewer met Terug‑naar‑Portal knop)
  - portal-index.json    (optioneel: losse JSON export)
  - rendered/            (gegenereerde HTML van Markdown documenten)

Gebruik
1) Genereer de portaldata:
   python scripts/docs/generate_portal.py

2) Open de pagina:
  - Dubbelklik op docs/portal/index.html (offline werkt, data is inline)
  - Of serveer statisch: (optioneel)
    cd docs/portal && python -m http.server 8080
    open http://localhost:8080

Navigatie terug naar de Portal
- Documenten openen via `viewer.html?src=…` in hetzelfde tabblad met bovenin een knop “Terug naar Portal”.
- In de viewer kun je ook “Open direct” (zelfde tab) of “Open in nieuw tabblad” gebruiken.

Rendering (MD/PDF/DOCX)
- Markdown (.md): generator pre-rendert naar HTML met portal‑stijl; portal links verwijzen automatisch naar de gerenderde pagina voor prettige leesbaarheid en zichtbare links.
- PDF (.pdf): wordt door de browser weergegeven in de viewer (iframe) met zoom/navigatie (browserafhankelijk).
- Word (.docx): niet native in de browser; viewer biedt “Open direct”/“Nieuw tabblad” als fallback (openen/download in native app).
- Feature‑flag: zet `PORTAL_RENDER_MD=0` om MD pre‑rendering uit te schakelen.

Views
- Alles: volledige lijst met zoek/filters/sort (titel/prioriteit/planning)
- Planning: EPIC → US → BUG hiërarchie (sprint‑agnostisch); sprintfilter verschijnt alleen als sprints bestaan
- Requirements: REQ‑overzicht met klikbare EPIC/US chips; tellen/traceability zichtbaar
- REQ Matrix: per EPIC alle REQs als chips
- Mijn Werk: open US/BUG gefilterd op owner/status/prioriteit; deeplinks via `#view=work&owner=…&wstatus=…&wprio=…&wonlyus=1`

Snel‑filters en deeplinks
- Type/status/prioriteit filters via UI; vrije zoek in titel/frontmatter
- Chips (EPIC/US/REQ): direct openen; uitbreidbaar met filterdeeplinks `#q=…`

Automatisering (aanbevolen)
- Pre‑commit: draai de generator bij wijzigingen in docs/**.
- CI: draai de generator bij iedere push/merge naar main.

Configuratie
- Pas docs/portal/config/sources.yaml aan om extra paden in/uit te sluiten of types te mappen.
- Voor meerdere projecten (aggregator/hub): gebruik dezelfde generator met een sources.yaml die meerdere bronnen definieert.

Privacy & A11y
- NFR’s: geen PII/secrets; sanitization; respecteer canonical/archived filters waar nodig
- Basis A11y: toetsenbordnavigatie, aria‑labels; contrast (AA)
