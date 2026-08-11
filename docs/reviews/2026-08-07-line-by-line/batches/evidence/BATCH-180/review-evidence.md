# BATCH-180 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Vastgelegde reviewer: `codex-hypatia`
- Onafhankelijke verifier: `codex-kierkegaard`
- Scope: 16/16 bereiken, 5898/5898 fysieke regels en 0/0 Python-symbolen

Alle regels zijn rechtstreeks uit immutable Git-objecten gelezen; de bronbestanden zijn niet gewijzigd.

## Verificatie

- Alle immutable documenten zijn gelezen; privacy-, schema-, API-, teststrategie- en gerichte pytestreproducties zijn uitgevoerd.
- Object-ID, range, line owner en reviewerpair matchten het batchmanifest exact.

## Bevindingen

### B180-001 — P2 — Actieve observabilitygids verklaart validatie AVG/GDPR-compliant terwijl alle vereiste privacy- en securitycontrols openstaan

**Bewijs:** De gids markeert zichzelf ACTIEF en AVG/GDPR Compliant en zegt dat alle logging en metrics privacy-by-design zijn (regels 1-10). Dezelfde gids laat echter alle vijf AVG-controls en alle vijf securitycontrols onbevestigd, waaronder PIA, encryptie en dashboardtoegang (296-310). Repositorybreed bestaan geen validation_request_total/validation_duration_seconds Prometheusimplementatie en geen gedocumenteerde /metrics, /ready, /live of /debug/trace-routes, hoewel regels 216-268 en 328-343 die als implementatie/endpoints presenteren. Het document wordt door de validation-rollout en errorcatalogus als monitoringreferentie gebruikt.

**Reproductie:** Lees regels 1-10, 216-268 en 296-343 uit de immutable blob. Voer git grep uit naar validation_request_total, validation_duration_seconds, prometheus_client en de genoemde routes onder src en dependencies; er zijn geen implementatiematches. Observeer bovendien dat alle compliancechecklistitems letterlijk [ ] zijn.

**Aanbevolen oplossing:** Wijzig de status naar proposed/non-compliant totdat controls aantoonbaar zijn. Implementeer en test gestructureerde redactie, retentie, encryptie, autorisatie en auditlogging voordat compliance wordt geclaimd; genereer endpoint-/metricdocumentatie uit runtime discovery en koppel elk checklistitem aan een eigenaar, test en bewijsdatum.

### B180-002 — P3 — Geïmplementeerde weighted-synonyms API-documentatie gebruikt een niet-bestaande klasse en methode

**Bewijs:** De als Implemented gemarkeerde API-sectie instrueert gebruikers JuridischeSynoniemlService te construeren en get_best_synonyms(term, threshold) aan te roepen (regels 103-149); dezelfde onjuiste klasse en methode worden verderop herhaald. AST-inspectie van src/services/web_lookup/synonym_service.py toont alleen JuridischeSynoniemService, wel get_synonyms_with_weights maar geen get_best_synonyms. Semantic-clusters.md en web_lookup_synoniemen.md herhalen de klassenaamtypefout.

**Reproductie:** Parse de immutable synonym_service.py met ast en inventariseer de class- en methodenamen: typo_class=False, get_best_synonyms=False en get_synonyms_with_weights=True. Het letterlijk kopiëren van het voorbeeld zou daardoor al bij import/attribuutopzoeking falen; een normale import is bovendien door de reeds bekende B017-001 import-time logfile-side-effect geblokkeerd en is niet als nieuw defect geteld.

**Aanbevolen oplossing:** Genereer de API-referentie uit de werkelijke publieke façade, vervang de klassenaam, documenteer thresholdfiltering via een werkelijk ondersteund contract of implementeer en test get_best_synonyms. Voeg executable doctests toe voor ieder voorbeeld en consolideer de drie overlappende synoniemdossiers.

### B180-003 — P2 — Canonieke toetsregelhandleiding start met een afwezig generator-script en levert een stil genegeerde validator-template

**Bewijs:** De handleiding schrijft cd src/toetsregels gevolgd door python create_regel_module.py voor (regels 29-40), maar src/toetsregels/create_regel_module.py ontbreekt. De handmatige template noemt class TEST01Validator (78), terwijl ModularToetsregelLoader voor TEST-01 uitsluitend create_validator, validate_test_01 of TEST_01Validator ontdekt (src/toetsregels/modular_loader.py:88-110). Bij geen match valt de loader stil terug op regexvalidatie (118-120), zodat geschreven customlogica niet wordt uitgevoerd. Regel 40 plaatst de template bovendien onder regels/ terwijl 19-27 validators/ als voorkeurslocatie noemt.

**Reproductie:** Controleer met git cat-file -e dat src/toetsregels/create_regel_module.py ontbreekt. Maak in een tijdelijke directory TEST-01.json plus validators/TEST_01.py met exact de gedocumenteerde TEST01Validator en laad die met ModularToetsregelLoader: documented_class_loaded=False en de fallback retourneert (False, 'Regel niet voldaan', 0.0) in plaats van de custom validator.

**Aanbevolen oplossing:** Herstel een geteste generator of verwijder het commando; laat templates exact create_validator of TEST_01Validator produceren in validators/. Laat onbekende Pythonmodules fail-loud in plaats van stil fallbacken en voeg een end-to-end authoringtest toe die genereert, laadt en bewezen de custom validate-methode uitvoert.

## Deduplicaties en afwijzingen

- Bestaande logging-, BDD- en synonymdefecten zijn niet dubbel geteld; de actieve compliance- en authoringclaims blijven afzonderlijk.

## Niet getest

- Geen live GitHub/Prometheus/AI/netwerk/credentials, productiedata, juridische AVG-certificering of Streamlit/browser/a11y-runtime.
