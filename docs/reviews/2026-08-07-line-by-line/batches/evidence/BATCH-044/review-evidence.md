# BATCH-044 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-root`
- Onafhankelijke verifier: `codex-hypatia`
- Scope: 3/3 blobs, 1175/1175 fysieke regels en 56/56 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit immutable Git-objecten gelezen. Callers, foutpaden en relevante tests zijn gevolgd; applicatiebestanden zijn niet gewijzigd.

## Verificatie

- 176 primaire gerichte tests en 56 onafhankelijke crosstests groen; metrics/AppTest toonde de credential-eager fout; Ruff en Black schoon.
- De onafhankelijke verifier heeft alle kandidaten gedisponeerd en de P1-codepaden opnieuw beoordeeld.

## Bevindingen

### B044-001 — P2 — Empty RAG selection is converted to the default document set

**Bewijs:** An explicit empty selection becomes None, and the orchestrator interprets falsy input as use session defaults.

**Reproductie:** Select no documents while defaults exist; the handler receives None and default documents are included.

**Aanbevolen oplossing:** Preserve tri-state semantics: None means default and an empty list means none.

### B044-002 — P3 — Timeout metric counts events outside the selected time window

**Bewijs:** timeout_count is incremented before timestamp parsing and cutoff filtering.

**Reproductie:** Parse a log containing only a timeout from 2000 with a 24-hour window; total is zero but timeout_count is one.

**Aanbevolen oplossing:** Parse and filter timestamps before updating any metric counter.

### B044-003 — P2 — Tabbed UI exposes raw exception details

**Bewijs:** The general exception wrapper shows type and message to every user and logs exc_info without a role gate.

**Reproductie:** Raise RuntimeError containing API_KEY=review-secret; the sentinel appears in st.code and logs.

**Aanbevolen oplossing:** Show a generic correlation-ID message and restrict sanitized diagnostics to authorized debug tooling.

### B044-004 — P2 — Cache metrics eagerly require an AI credential

**Bewijs:** A cache-only dashboard requests the full synonym orchestrator, which constructs an AI service.

**Reproductie:** Open metrics with a fake registry and no provider keys; initialization raises API key is required.

**Aanbevolen oplossing:** Expose a credential-free metrics/cache service and initialize AI enrichment lazily.

### B044-005 — P3 — Drie actieve light-theme tekstcombinaties missen WCAG AA-contrast

**Bewijs:** Streamlit 1.58 is gepind en de repo heeft geen app-theme override. In de framework-lightpalette gebruikt st.success tekst #158237 op een 10%-blend van #21c354: in de sidebar op #f0f2f6 is dat 4.044331:1 voor ai_provider_sidebar.py:107-109; in main op #ffffff 4.495615:1 voor tabbed_interface.py:325-327. De primaire knop op tabbed_interface.py:446-451 gebruikt wit op #ff4b4b: 3.301871:1. Alle zijn normale tekst en blijven onder WCAG 2.1 AA 1.4.3 >=4.5:1.

**Reproductie:** Bereken sRGB-relatieve luminantie voor de Streamlit 1.58 light-theme foreground/backgroundparen, inclusief alpha-compositie van green70 met main/sidebarachtergrond; uitkomsten 4.044331, 4.495615 en 3.301871. Render de drie calls in light theme voor visuele bevestiging.

**Aanbevolen oplossing:** Configureer of override semantische light-theme tokens zodat normale tekst in elke state minimaal 4.5:1 haalt. Voeg automatische contrasttests op main/sidebar plus handmatige light/dark-, 200%-zoom-, forced-colors- en screenreadertests toe.

### B044-006 — P3 — Negen actieve Streamlit-calls gebruiken de verwijderingsgevoelige use_container_width-API

**Bewijs:** Een AST-sweep over immutable src vindt exact negen use_container_width=True-calls in vijf bestanden. Onder Streamlit 1.58 geven drie st.plotly_chart-, twee st.dataframe- en twee st.data_editor-calls daadwerkelijk de waarschuwing dat de parameter na 2025-12-31 wordt verwijderd; de twee st.button-calls zijn eveneens deprecated maar vertalen stil naar width=stretch. Het betreft dus zeven warning-emitting en negen deprecated calls. De anchor bevat vier emitting calls; overige locaties zijn csv_importer.py:90, definition_edit_tab.py:338-364/990-994, expert_review_tab.py:238-280 en synonym_admin.py:192.

**Reproductie:** Parse alle base src-Python-AST-calls op keyword use_container_width=True: count=9/files=5. Patch show_deprecation_warning en roep st.plotly_chart, st.dataframe en st.data_editor aan: elk waarschuwt; inspecteer st.button: geen warninghook, wel width=stretch.

**Aanbevolen oplossing:** Vervang alle negen argumenten door width='stretch' en voeg een source/AST-gate toe die nieuwe use_container_width-gebruiken blokkeert; test de relevante tabellen, editors, grafieken en knoppen op layoutbehoud.

## Niet getest

- Geen externe AI-call of productie-logbestand gebruikt.
- Visueel contrast, toetsenbord, screenreader, touch en responsive viewports zijn niet met een browserbackend getest.
