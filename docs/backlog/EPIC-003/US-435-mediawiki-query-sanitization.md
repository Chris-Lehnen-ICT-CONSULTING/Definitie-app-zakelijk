id: US-435
titel: MediaWiki query-sanitization (org-token stripping, juridische normalisatie)

Doel
- Pariteit met SRU-pad: verwijder organisatorische tokens (OM, DJI, ZM, Justid, e.d.) en normaliseer juridische/wet-tokens (Sv/Sr/Awb/Rv en voluit) vóór Wikipedia/Wiktionary queries.

Waarom
- Logs tonen dat queries als “vonnis OM Strafrecht” minder recall geven in MediaWiki (geen pagina), terwijl SRU-pad deze tokens al stript. Dit schaadt web lookup kwaliteit en consistentie.

Scope
- modern_web_lookup_service._classify_context_tokens hergebruiken voor MediaWiki pad.
- Querystrategie: eerst term-only; dan jur/wet toevoegingen; disambiguation skip.
- Taal NL; fallback hyphen/suffix-strip behouden.

Acceptatiecriteria
- “vonnis OM Strafrecht” → initieel “vonnis” query; ≥ baseline recall op testsuite.
- Disambiguation wordt overgeslagen; resultaat confidence weegt provider weight mee.
- Unit tests voor stripping en stage-logica.

Notities
- Zie ook EPIC-003: WEB-LOOKUP-ANALYSIS-REPORT en logging_vonnis_weblookup.

