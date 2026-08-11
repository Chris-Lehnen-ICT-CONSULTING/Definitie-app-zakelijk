# BATCH-182 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Vastgelegde reviewer: `codex-galileo`
- Onafhankelijke verifier: `codex-hypatia`
- Scope: 17/17 bereiken, 5822/5822 fysieke regels en 0/0 Python-symbolen

Alle regels zijn rechtstreeks uit immutable Git-objecten gelezen; de bronbestanden zijn niet gewijzigd.

## Verificatie

- Alle immutable documenten en binaire objecten zijn equivalent beoordeeld; stale pytest-, SQLite-, HTML/a11y-, PDF-, tar- en screenshotgates zijn uitgevoerd.
- Object-ID, range, line owner en reviewerpair matchten het batchmanifest exact.

## Bevindingen

### B182-001 — P2 — Web-lookuptestsign-off rapporteert verdwenen suites als 129 groene tests

**Bewijs:** Het document verklaart 129/129 tests, circa 95% coverage en READY FOR INTEGRATION, maar alle vier opgegeven bewijsbestanden op regels 426-431 ontbreken in de immutable tree. De bijbehorende quick reference herhaalt dezelfde paden en het verwachte resultaat 129 passed op regels 5-20 en 384-393. De teststructuur is inmiddels verplaatst en opgesplitst; zo staat juridisch_ranker onder tests/unit/services/web_lookup en zijn er meerdere andere integratiesuites. Daardoor bewijst de gepubliceerde sign-off noch de huidige suite noch de genoemde coverage.

**Reproductie:** Voer vanuit base b958ddb de letterlijk gedocumenteerde opdracht `pytest tests/services/web_lookup/ tests/integration/test_improved_web_lookup.py -q` uit; pytest stopt met exitcode 4 omdat tests/services/web_lookup niet bestaat. `git cat-file -e` faalt tevens voor test_synonym_service.py, test_juridisch_ranker.py, test_improved_web_lookup.py en web_lookup_fixtures.py op de gedocumenteerde locaties.

**Aanbevolen oplossing:** Genereer testdocumentatie uit een gepinde pytest-collectie en coverage-artefact, vermeld commit en datum, verwijs uitsluitend naar actuele paden en laat CI de gedocumenteerde opdracht in een schone checkout uitvoeren; verwijder historische pass- en coveragetellingen zodra het bewijs niet meer reproduceerbaar is.

### B182-002 — P3 — Zeven VALOR-tabs zijn muis-only en missen tabsemantiek en programmatische staat

**Bewijs:** De zeven bedieningen zijn gewone div-elementen met alleen data-tab en een pointercursor; ze hebben geen button, role=tab, tabindex, aria-selected of aria-controls. Het script registreert uitsluitend click-events en kent geen keydown/keyup/keypress-handler. De panelen worden met display:none gewisseld zonder role=tabpanel of focusbeheer. Deze bronfeiten zijn bewezen; daadwerkelijke browser-, toetsenbord- en screenreaderinteractie is niet uitgevoerd en een base-treezoekactie vond geen caller of link naar dit losse HTML-bestand.

**Reproductie:** Parseer de immutable HTML en tel zeven `.tab`-divs, nul buttons en nul role/tabindex/aria-attributen; zoek de handlers op regels 694-699 en vind alleen `addEventListener('click', ...)`. Probeer de tabs vervolgens met Tab, Enter, Space en pijltjestoetsen in een offline browser; dat laatste is in deze read-only review niet uitgevoerd.

**Aanbevolen oplossing:** Gebruik native buttons en implementeer het ARIA-tabs-patroon met tablist/tab/tabpanel, aria-selected/aria-controls, roving tabindex en pijltjestoetsen; geef ieder gegenereerd diagram een toegankelijke naam of tekstalternatief en voeg keyboard-, axe- en screenreadertests toe als de pagina behouden blijft.

### B182-003 — P3 — Kleine tekst op beide VALOR-pagina's haalt WCAG AA-contrast niet

**Bewijs:** Op de architectuurpagina wordt normale 0,85rem-koptekst #5c6bc0 op #1a1d27 weergegeven met contrast 3,46:1 en de 0,8rem-footer #555 op #0f1117 met 2,53:1; beide blijven onder 4,5:1. De companion linked-data-pagina gebruikt voor zijn 0,75rem-footer #484f58 op #0d1117, slechts 2,28:1. De kleurwaarden en berekeningen zijn bronmatig bewezen; browserzoom en visuele regressietests zijn niet uitgevoerd.

**Reproductie:** Bereken voor elk foreground/background-paar de WCAG-relatieve luminantie en `(Lmax+0.05)/(Lmin+0.05)`: de resultaten zijn respectievelijk 3,46, 2,53 en 2,28. Vergelijk ze met de AA-eis 4,5:1 voor normale tekst.

**Aanbevolen oplossing:** Vervang de gedempte tekstkleuren door design tokens die minimaal 4,5:1 halen op hun werkelijke achtergrond en voeg een geautomatiseerde contrastcontrole plus handmatige controle bij 200% zoom toe.

## Deduplicaties en afwijzingen

- De concrete VALOR-keyboard- en contrastdefecten zijn andere bestanden/criteria dan eerdere archived-dashboardbevindingen.

## Niet getest

- Geen netwerk/credentials, echte provider- of productiedataflow, browser/screenreader/zoomruntime, externe links of uitvoering van binaire artefacten.
