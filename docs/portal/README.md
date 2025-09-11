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
  - portal-index.json    (optioneel: losse JSON export)

Gebruik
1) Genereer de portaldata:
   python scripts/docs/generate_portal.py

2) Open de pagina:
   - Dubbelklik op docs/portal/index.html (offline werkt, data is inline)
   - Of serveer statisch: (optioneel)
     cd docs/portal && python -m http.server 8080
     open http://localhost:8080

Automatisering (aanbevolen)
- Pre‑commit: draai de generator bij wijzigingen in docs/**.
- CI: draai de generator bij iedere push/merge naar main.

Configuratie
- Pas docs/portal/config/sources.yaml aan om extra paden in/uit te sluiten of types te mappen.
- Voor meerdere projecten (aggregator/hub): gebruik dezelfde generator met een sources.yaml die meerdere bronnen definieert.

Let op
- Dit is een MVP‑skelet. portal.js/portal.css en de generator kunnen stapsgewijs uitgebreid worden (zoek, filters, badges, multi‑repo, etc.).

