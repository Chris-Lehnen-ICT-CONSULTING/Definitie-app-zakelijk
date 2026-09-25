# Vooraf vastgelegde gerichte proeven — INT-02 B

25-09-2026. Basis HEAD 26f2374d302fc66fc0b12ed29dc34585f7c0a5c3. Geen netwerk/modelcalls, productiegegevens of opslag buiten deze uitvoermap. Historische C01–C06 worden niet opnieuw uitgevoerd: recordvergelijking en relevante evaluatordiff onderbouwen hergebruik van uitsluitend status/reden/signalen, niet van actuele volledige appketen.

P1 — ModularValidationService met echte ToetsregelManager, cleaning=None, repository=None. Nieuwe functiecontrasten C50–C56: allemaal review_required, geen INT-02-violation of pass, reden gelijk aan record-toetsvraag; signalen uitsluitend woordpatronen. Grond: judgment_review.evaluate en _signalen; context verandert INT-02 niet. C50 deterministische afleiding indien → indien; C51 discretionaire actie tenzij → tenzij; C52 procedure zonder conditioneel woord → geen; C53 rechtsgevolgbeschrijving → geen; C54 lidmaatschap alleen als → alleen als; C55 kwalitatief criterium → geen; C56 geen context → indien. Serviceproef bewijst geen inhoudelijke classificatie, UI, snapshot of generatiekwaliteit.

P2 — Werkelijke JSONBasedRulesModule._format_rule op het ongewijzigde record, voorbeelden aan en uit. Verwacht uitleg 'geen beslisregels of voorwaarden' plus hardcoded 'Vermijd voorwaardelijke formuleringen…', geen toetsvraag of afleidingsexceptie; voorbeeldpaar alleen bij aan. Grond: _format_rule 228–281, instruction_map 377. Dit is echte formatteruitvoer, geen volledige orchestrator/modelproef; registratie gecontroleerd in modular_prompt_adapter 109–116.

P3 — CleaningService.clean_text op C50 met label/ontologische kop en C52 met label. Verwacht kop/label verwijderd, hoofdletter/slotpunt, inhoudelijke 'indien' resp. 'moet' behouden. Grond: opschonen_enhanced → opschonen, voorwaarden geen algemene verwijderregel. Bewaart raw, cleaned, metadata; geen persistentieclaim.

P4 — Historische bronbinding: git diff oud→HEAD voor record/evaluator, recordhash vergelijken met uitkomsten.json, AST-vergelijking _signalen. Verwacht bytegelijk record en identieke _signalen; evaluate heeft alleen branches voor andere regels erbij. Volledig evaluatorbestand is dus NIET bytegelijk. Dit bepaalt de smalle hergebruikgrens.

Verwachte normuitkomsten onder voorstel N-B1 zijn apart in casusregister: afleiding/criterium/beschreven rechtsgevolg voldoen aan INT-02; actorvoorschrift/discretie niet; ontbrekende context blokkeert de beoogde appaanroep volgens K-9. Die normverwachtingen zijn geen verwachte huidige software-uitkomsten.
