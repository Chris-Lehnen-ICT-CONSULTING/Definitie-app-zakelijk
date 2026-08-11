# BATCH-131 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Vastgelegde reviewer: `codex-hypatia`
- Onafhankelijke verifier: `codex-kierkegaard`
- Scope: 9/9 bereiken, 4619/4619 fysieke regels en 0/0 Python-symbolen

Alle regels zijn rechtstreeks uit immutable Git-objecten gelezen; de bronbestanden zijn niet gewijzigd.

## Verificatie

- Lossless JSON-/graphgates, lokale Git-tree-linkcontrole, launcherreproductie, HTML-parsercontrole en statische WCAG-contrast-/motionchecks zijn uitgevoerd.
- Object-ID, range, line owner en reviewerpair matchten het batchmanifest exact.

## Bevindingen

### B131-001 — P2 — Actieve README geeft een quickstart en projectstatus die niet bij de huidige runtime of repository passen

**Bewijs:** De aanbevolen start op regels 18-23/118-143 configureert uitsluitend OpenAI en `run_app.sh` weigert op regels 4-12 te starten zonder OPENAI_API_KEY, terwijl ConfigManager.ai_provider en de UI standaard `anthropic` kiezen. Een offline aanroep met `AI_PROVIDER=anthropic` en een dummy ANTHROPIC_API_KEY stopt daarom met exit 1 vóór het doorgegeven commando. Verder noemt dezelfde actieve README op regels 303-387 45/46 regels, 919 tests en zes disabled tests, in tegenspraak met regels 8 en 91-100 (2500+/53) en CHANGELOG.md:26; vijf van de zes genoemde pytest-bestanden bestaan niet. README regels 152-160 noemt daarnaast twee pytest-filterexpressies equivalent, maar de Makefile-expressie selecteert nul contracttests (exit 5) en de README-expressie één test (exit 0).

**Reproductie:** Pipe de immutable `scripts/deployment/run_app.sh`-blob naar `env -u OPENAI_API_KEY -u OPENAI_API_KEY_PROD ANTHROPIC_API_KEY=sk-ant-dummy AI_PROVIDER=anthropic bash -s -- true`; dit print dat OPENAI_API_KEY ontbreekt en retourneert 1. Vergelijk daarna README.md:303-387 met :8/:91-100 en controleer de zes testpaden op :363-377 met `git cat-file -e`; vijf leveren exit 128.

**Aanbevolen oplossing:** Maak de quickstart provider-neutraal: laat de launcher de gekozen/default provider valideren en documenteer zowel Anthropic als OpenAI. Verplaats historische status naar een gedateerd archief en genereer actuele aantallen/testcommando's uit CI. Voeg een executable docs-test toe voor quickstart, paden en onderlinge statusclaims.

### B131-002 — P2 — README belooft documentnavigatie en integriteitsbewaking die in de base ontbreken of advisory zijn

**Bewijs:** De links op 393-410/507 wijzen naar zes niet-bestaande unieke doelen (requirements, twee architectuurdocumenten, epics-index, EPIC-006 en master-stories). Elders ontbreken ook het op regel 46 genoemde CONTRIBUTING.md en de portal op regel 70. Toch claimen regels 527-544 dat CI broken canonical links blokkeert en de portal genereert; `.github/workflows/docs-integrity.yml:27-38` zet de linkcheck op `continue-on-error: true` en verklaart portalgeneratie deprecated, terwijl `docs/portal/index.html` en `scripts/docs/run_portal_generator.sh` ontbreken.

**Reproductie:** Controleer de README-doelen met `git cat-file -e b958ddb:<doel>`; ten minste acht expliciet genoemde unieke lokale doelen ontbreken. Lees vervolgens de immutable docs-integrity workflow regels 27-38: de linkstap is advisory en portalgeneratie is uitgecommentarieerd/deprecated, ondanks de README-claim.

**Aanbevolen oplossing:** Vervang links door bestaande canonieke locaties of verwijder de claims. Maak de root-README onderdeel van een fail-closed Git-tree-linkcheck en beschrijf de werkelijke advisory status. Verwijder de portalinstructies of herstel een gegenereerde portal met een CI-driftguard.

### B131-003 — P3 — Gearchiveerd architectuurdashboard toont kapotte en gesimuleerde interacties

**Bewijs:** Zes aangeboden cross-reference-acties op regels 481-506 hebben alleen href='#'; de twee documentlinks op 516-517 resolven relatief naar niet-bestaande docs/ARCHIEF/docs/architectuur-doelen; Export Report op 518/557-559 toont uitsluitend een alert en exporteert niets. De metricbron bevat bovendien ongeldig '<2s': parsers herstellen dit verschillend, zodat alleen de markup-onrobuustheid statisch bewezen is; daadwerkelijk browserverlies van het kleiner-dan-teken is niet getest. Het bestand is via ARCHIVE_NOTES als archief aangemerkt en dus dormant.

**Reproductie:** Parseer de blob met Python `html.parser`: er zijn acht `href='#'`-links totaal, de `<2s`-bron komt als `2s`-data terug, en resolveer 516-517 relatief aan `docs/ARCHIEF/`; beide doelen ontbreken in `git ls-tree -r b958ddb`. Klikken op Export Report kan volgens de inline functie alleen de alert uitvoeren.

**Aanbevolen oplossing:** Maak het archief expliciet niet-interactief of herstel de doelen, gebruik `&lt;2s`, en implementeer/disable de exportactie met eerlijke feedback. Voeg een statische HTML-link- en markupcheck toe voor publiceerbare dashboards.

### B131-004 — P3 — Dashboard laat een oneindige rotatie lopen zonder pauze of reduced-motion alternatief

**Bewijs:** `.rotating` krijgt `animation: rotate 2s linear infinite`; het stylesheet bevat geen `prefers-reduced-motion`-regel en de pagina biedt geen pauze/stopbediening. De spinner staat naast inhoud en draait onbeperkt, in strijd met de WCAG 2.1 AA-verwachting voor niet-essentiële automatisch bewegende content (2.2.2). Reachability is dormant omdat dit een expliciet gearchiveerd dashboard is.

**Reproductie:** Zoek in de immutable HTML-blob naar `animation`, `infinite` en `prefers-reduced-motion`: regel 297 bevat de oneindige animatie en er is geen reduced-motion override of pauzecontrol in de 573 regels. Openen in een browser is voor deze statische codeclaim niet vereist; toetsenbord/screenreadergedrag is niet getest.

**Aanbevolen oplossing:** Stop de animatie na een korte duur of bied een pauzeknop; voeg minimaal `@media (prefers-reduced-motion: reduce) { .rotating { animation: none; } }` toe en verifieer handmatig met reduced-motion en screenreader.

### B131-005 — P3 — Gearchiveerd dashboard gebruikt linkkleuren onder de WCAG-contrastgrens

**Bewijs:** Normale .view-button-tekst gebruikt wit (#ffffff) op --secondary-color #3498db, een contrast van 3,153:1. .reference-link gebruikt #3498db op --bg-color #f5f6fa, een contrast van 2,920:1. Beide combinaties blijven onder de vereiste 4,5:1 voor normale tekst in WCAG 2.1 AA criterium 1.4.3. De pagina staat onder docs/ARCHIEF en is daarom dormant.

**Reproductie:** Lees de immutable CSS-regels 205-261 en de kleurvariabelen op regels 7-14, zet de sRGB-kanalen om naar relatieve luminantie volgens WCAG en bereken (L1+0,05)/(L2+0,05); de uitkomsten zijn respectievelijk 3,153 en 2,920.

**Aanbevolen oplossing:** Gebruik donkerdere link- en knopkleuren die in normale en hover/focusstatus minimaal 4,5:1 halen, behoud daarnaast een zichtbare focusindicator en voeg een geautomatiseerde contrastcontrole plus handmatige browsercontrole op lichte en donkere thema's toe.

## Deduplicaties en afwijzingen

- De encodingfout dedupeert naar INV-ENCODING-D2C4CCDFC47C; model/view-afwijkingen dedupliceren naar B111/B114/B115/B116/B118-B121.

## Niet getest

- Geen echte AI-provider/credentials of Streamlit-start; geen browser, keyboard, screenreader, reduced-motion, zoom, touch- of responsive-runtimecontrole.
