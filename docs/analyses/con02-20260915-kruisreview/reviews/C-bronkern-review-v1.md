## Bevindingen

1. **P1 — Een citaat laat tegenstrijdige of onvolledige deelbeoordelingen slagen.**
   [contract.py:517](/Users/chrislehnen/.codex/worktrees/8b34/Definitie-app/src/domain/sources/contract.py:517): na citaatverificatie blijft `status="pass"` behouden, ook bij uitsluitend `applicable=null/false`, `locatable=false`, lege bronoordelen of claims met `supported=false/null`. Ook een afgewezen profiel verhindert die pass niet. Hierdoor kan CON-02 volledig slagen terwijl de gestructureerde onderbouwing dat tegenspreekt. Controleer de samenhang tussen status, toepasselijke bronnen, claims en bewijs; behoud negatieve en open onderdelen.

2. **P1 — Feitelijke bronmetadata bereikt de beoordelende AI niet.**
   [source_assessment_service.py:149](/Users/chrislehnen/.codex/worktrees/8b34/Definitie-app/src/services/validation/source_assessment_service.py:149): de prompt bevat enkele canonieke attributen en de passage, maar geen `bron.identity`. Bijvoorbeeld vaststellingsstatus, uitgever en rechtsgebied worden wel gehasht, maar niet beoordeeld. Alleen zo’n metadatawijziging produceert dezelfde AI-prompt; de onderliggende AIService-cache kan vervolgens hetzelfde antwoord teruggeven onder een nieuwe fingerprint. Transporteer relevante feitelijke metadata als brongegevens en bind de modelaanroep daaraan.

3. **P2 — Een foutkwitantie verdwijnt bij een lege bronset.**
   [validation_orchestrator_v2.py:285](/Users/chrislehnen/.codex/worktrees/8b34/Definitie-app/src/services/orchestrators/validation_orchestrator_v2.py:285): met `provenance_sources=[]` en een receipt met `status="error"` retourneert de wrapper vóór receiptcontrole `None`. CON-02 wordt gewoon open. Bovendien behandelt [contract.py:1008](/Users/chrislehnen/.codex/worktrees/8b34/Definitie-app/src/domain/sources/contract.py:1008) geen bronnen vóór een aanwezige technische fout. Laat foutcontrole op beide grenzen voorgaan, zodat verzamelfouten herkenbaar blijven.

4. **P2 — Onvolledige model-JSON wordt als geslaagde beoordeling gecachet.**
   [source_assessment_service.py:416](/Users/chrislehnen/.codex/worktrees/8b34/Definitie-app/src/services/validation/source_assessment_service.py:416): `{}` of JSON met ontbrekende onderdelen wordt via `_valideer_deel` omgezet naar inhoudelijk open oordelen, krijgt `status="assessed"` en wordt gecachet. Dit maskeert een technisch onbruikbaar antwoord als reguliere onzekerheid. Valideer de vereiste antwoordstructuur; behoud technische fouten afzonderlijk en cache die niet.

5. **P2 — De werkelijk verzonden beoordelingspassages worden niet vastgelegd.**
   [source_assessment_service.py:419](/Users/chrislehnen/.codex/worktrees/8b34/Definitie-app/src/services/validation/source_assessment_service.py:419): bewijs wordt gecontroleerd tegen `verzonden`, maar het beoordelingsdocument gebruikt de oorspronkelijke `bronnen`. Bij afkapping ontbreken de verzonden passage, bijbehorende hash en afkapgrens; `sources` bevat alleen bronidentiteiten. De generatiekwitantie beschrijft een andere aanroep. Bewaar afzonderlijk welke passages deze beoordeling daadwerkelijk ontving, inclusief afkapping.

6. **P2 — `validate_text` beoordeelt de ondersteunde bronalias niet.**
   [validation_orchestrator_v2.py:268](/Users/chrislehnen/.codex/worktrees/8b34/Definitie-app/src/services/orchestrators/validation_orchestrator_v2.py:268): context met alleen `sources=[…]` veroorzaakt geen AI-beoordeling, omdat deze helper uitsluitend `provenance_sources` leest. De evaluator leest later wél `sources` en rapporteert ontbrekende beoordeling. Normaliseer de alias en controleer conflicterende lijsten ook voor `validate_text`, zoals bij recordvalidatie.

7. **P2 — Het bestuursorgaanvoorbeeld maakt een disjunctvoorwaarde algemeen.**
   [CON-02.json:11](/Users/chrislehnen/.codex/worktrees/8b34/Definitie-app/src/toetsregels/regels/CON-02.json:11): de afkeurreden verlangt algemeen “krachtens publiekrecht ingesteld”, terwijl het goede voorbeeld expliciet een alternatief persoon/college met openbaar gezag bevat. Die reden onderbouwt de gestelde tekortkoming dus niet. Vervang haar door een voorbeeld met aantoonbaar verlies van een toepasselijk kenmerk, zonder voorwaarden over alternatieven heen te trekken.

## Bewijsgrenzen

Statische review tegen `dc7a70e80`; geen wijzigingen of tests uitgevoerd. De aangeleverde logs melden **1596 passed, 21 subtests** en schone lint. Mutatielogs tonen discriminatie, geen chronologisch RED-before-GREEN.

Hashes: **34/34 gelijk bij start, 32/34 bij einde**. Alleen `test_def743_bronbewijs_export.py` en `test_def743_bronbewijs_persistentie.py` wijzigden tijdens de review. De genoemde C-productiecode bleef gelijk. Geen oordeel over afronding van D/F, DEF-630 of daadwerkelijke modelkwaliteit.
