# BATCH-035 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-galileo`
- Onafhankelijke verifier: `codex-kierkegaard`
- Scope: 11/11 blobs, 3.902/3.902 fysieke regels en 125/125 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit immutable Git-objecten gelezen.
Document-UI-, RAG-, ranking- en orchestratorcallers zijn gevolgd; applicatiebestanden
zijn niet gewijzigd.

## Verificatie

- Onderdeel van 206 primaire gerichte tests; Ruff en Black waren schoon.
- Offline mocks, in-memory DOCX en lokale token-counter stubs bewezen de defecten.
- Geen netwerk, credentials of destructieve stresspayloads.

## Bevindingen

### B035-001 — P2 — metadata-partial-write wordt als documentsucces gemeld

`document_processor.py:576-596` truncateert de live JSON vóór `json.dump` en
slikt schrijfproblemen. Na een gesimuleerde partial write bleef verwerking
succesvol, maar een nieuw proces laadde nul documenten; de UI toont algemeen
succes. Aanbevolen: temp+fsync+atomic replace/backup en save-uitkomst propagateren.

### B035-002 — P3 — foutcache negeert MIME en verhindert retry

De cachekey bevat alleen content+filename en cachet ook failures. Dezelfde bytes
en naam faalden als octet-stream en bleven daarna als text/plain dezelfde fout
retourneren. Aanbevolen: effectieve MIME/extractorversie in de key of alleen
successen cachen, plus expliciete invalidatie.

### B035-003 — P2 — `.doc` wordt geadverteerd maar niet ondersteund en DOCX verliest tabellen

Extractor en upload-UI noemen `.doc`, maar dat pad retourneert altijd een
unsupported-placeholder. DOCX leest alleen paragrafen; een table-only document
werd leeg. Aanbevolen: `.doc` claim verwijderen of implementeren en DOCX-body
in documentvolgorde inclusief tabellen en benodigde parts verwerken.

### B035-004 — P2 — documentextractie heeft geen resourcecaps

Raw size, ZIP-decompressieratio, pagina-, tekst- en tijdlimieten ontbreken en de
UI leest uploads synchroon volledig. PDF-/ZIP-bombuitputting is `suspected`; een
destructieve stressrepro is bewust niet uitgevoerd. Aanbevolen: gelaagde caps en
een geïsoleerde worker met timeout.

### B035-005 — P2 — RAG-overlap en maximale chunkgrootte zijn niet effectief

Generieke overlap staat alleen in metadata terwijl embedding alleen `tekst`
gebruikt. Legal chunks voegen overlap na budgeting toe en één oversized
letterblok wordt niet verder gesplitst. Stub-repro's leverden chunks boven max.
Aanbevolen: één effectieve embeddingtekst, overlapbudget reserveren en recursief
splitsen met `token_count <= max` als invariant.

### B035-006 — P2 — duplicate URL reconstructeert ranked resultaten verkeerd

Ranking houdt twee records met dezelfde URL maar andere content, waarna lookup
de originelen opnieuw indexeert op URL/hash en de laatste overschrijft. Twee
outputrijen werden zo beide de lage-kwaliteit Wiktionary-record. Aanbevolen:
stabiele record-ID/canonical-URL-dedup en het ranked origineel direct retourneren.

### B035-007 — P2 — substring `sr` classificeert bestuursrecht als strafrecht

Contextdetectie gebruikt substrings voor korte afkortingen. `bestuursrecht`
leverde `Wetboek van Strafrecht` en `Sr`. Aanbevolen: exacte tokens/woordgrenzen,
langste frases eerst en aliascontracttests.

### B035-008 — P2 — singleton webdebug mengt gelijktijdige requests

`_last_attempts/_last_debug/_last_error` zijn gedeelde mutable servicevelden en
de container is procesglobaal. Een ALICE/BOB-interleaving liet BOB attempts van
beide requests bevatten. De race is proven; cross-user privacy-impact is
deploymentafhankelijk. Aanbevolen: request-local accumulator in het resultaat.

### B035-009 — P3 — iedere lookupfase krijgt opnieuw het volledige timeoutbudget

Vier sequentiële contexten met timeout 0,01 duurden circa 0,044 seconde. De
actieve orchestrator heeft een outer timeout, dus de hoofdflow is gemitigeerd.
Aanbevolen: absolute deadline/outer `asyncio.timeout` en resterend budget per fase.

### B035-010 — P2 — embeddingzoekpad materialiseert de volledige collectie tweemaal

Het pad laadt alle BLOBs, bouwt een tweede dense matrix en sorteert volledig.
50k×3072 float32 is al circa 586 MiB; met BLOBs en kopie ligt de ondergrens boven
1,1 GiB, strijdig met de circa-200ms-claim. Aanbevolen: ANN/vectorindex of gepaged,
gecapte search met benchmarkgate.

### B035-011 — P2 — globale documentprocessor kan sessiedata delen

Een procesglobale processor bewaart alle documenten en de UI rendert die lijst.
Multi-session bestandsnamen/selecties/verwijdering kunnen daardoor delen; dit is
`suspected` omdat de app als single-user is gedocumenteerd en geen tweesessietest
is uitgevoerd. Aanbevolen: session-/user-scoped cache en eigenaarschap.

### B035-012 — P3 — upload-UI telt foutrecords als succesvol verwerkt

Zodra de resultatenlijst niet leeg is, toont de renderer `✅ N documenten
verwerkt`, ook als records alleen errors bevatten; pas daarna volgt per-file fout.
Aanbevolen: afzonderlijke success/failuretellingen en partial/error overall state.

## Niet getest

- Geen echte PDF-/ZIP-bomb, 50k-embeddingbenchmark of multi-user browserflow.
- Geen externe MediaWiki/Brave/Google-, AI- of credentialcalls.
- Visueel contrast, toetsenbord, screenreader, touch en responsive viewports niet getest.
