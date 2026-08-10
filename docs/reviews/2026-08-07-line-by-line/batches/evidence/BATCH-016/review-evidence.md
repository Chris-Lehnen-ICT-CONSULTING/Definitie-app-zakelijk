# BATCH-016 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-root`
- Onafhankelijke verifier: `codex-hypatia`
- Scope: 14/14 blobs, 3.690/3.690 fysieke regels en 150/150 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit de immutable Git-objecten gelezen.
Callers en foutpaden zijn gevolgd; applicatiebestanden zijn niet gewijzigd.

## Verificatie

- 89 relevante tests slaagden in de primaire review; 27 tests in de kruisverificatie.
- Ruff en Black waren schoon voor alle Pythonbestanden in scope.
- Alleen lokale fakes en publieke configuratie; geen provider, netwerk of credentials.

## Bevindingen

### B016-001 — P1 — essentieel promptmodulefalen wordt stil weggelaten

`src/services/prompts/modules/prompt_orchestrator.py:143-159,229-282,323-364`
belooft een `ModuleExecutionError`, maar zet validatie-, exception- en
uitvoerfalen om naar `success=False` en combineert alleen geslaagde output. Een
fake `definition_task`-failure leverde exact `ROLE` op zonder finale taak.
Aanbevolen: kritieke modules en finale taak als invariant behandelen, typed
fail-loud vóór promptreturn en alle failurevormen testen.

### B016-002 — P2 — raw begrip blijft in procesglobale uitvoermetadata

`prompt_orchestrator.py:208-225` bewaart het raw begrip in mutable metadata van
de singleton-orchestrator; `modular_prompt_adapter.py:30-50,331-375` kan de
laatste uitvoering exposen. Een capture zonder bootstrapfilter bevatte de raw
waarde. De productiebootstrap redigeert e-mailachtige waarden in handlerlogs;
een productieconsumer van de metadata is niet gevonden. Aanbevolen: alleen
request-ID/hash bewaren en metadata per request isoleren.

### B016-003 — P2 — feedbackhistorie wordt genegeerd maar als geïntegreerd gemeld

`src/services/prompts/prompt_service_v2.py:106-195` gebruikt
`feedback_history` alleen voor bool/count. ALPHA- en BETA-histories leverden
byte-identieke prompts zonder feedbacktekst, met `feedback_integrated=True`.
Aanbevolen: een gesaniteerde feedbackmodule implementeren of het veld expliciet
unsupported/false rapporteren.

### B016-004 — P2 — gedocumenteerde tokenlimiet wordt niet gehandhaafd

`prompt_service_v2.py:47-55,106-204` noemt `max_token_limit` een harde limiet,
maar controleert die niet. Limiet 1 met een fake prompt van 1.000 woorden gaf
1.300 gerapporteerde tokens en de volledige output. Aanbevolen: pre-/postbudget,
gereserveerde ruimte voor kritieke instructies en fail-loud bij onmogelijk budget.

### B016-005 — P2 — resultaatcategorie krijgt een maatregeltemplate

`prompt_service_v2.py:136-159` mappt resultaat/uitkomst naar `Maatregel`. Een
echte lokale build bevatte tegelijk `RESULTAAT CATEGORIE`, `Template voor
Maatregel` en `[Interventie/actie]`. Aanbevolen: aparte Resultaat-template en
inhoudelijke contracttests per categorie.

### B016-006 — P2 — autoriteitsselectie vertrouwt URL-substrings

`prompt_service_v2.py:389-414` zoekt trusted namen in provider plus volledige
URL. `https://wetten.overheid.nl.attacker.example/x` met score 0,1 werd boven
een geldige bron met 0,99 als enige geselecteerd. Aanbevolen: `urlsplit`, exact
hostname/toegestane subdomeinen en een interne provider-enum.

### B016-007 — P2 — één ongeldige score verwijdert alle geldige webbronnen

Sorteren en formatteren vallen onder één outer try op `prompt_service_v2.py:
367-487`. Een bron met score `broken` gevolgd door score 0,9 resulteerde in een
lege lijst. Aanbevolen: per-item finite parsing, alleen de ongeldige bron skippen
en een gestructureerde waarschuwing loggen.

### B016-008 — P2 — NaN wordt maximale synoniemconfidence

`src/services/prompts/synonym_response_parser.py:67-79` doet float+clamp zonder
`isfinite`. Zowel string `NaN` als JSON NaN gaf confidence 1,0. Aanbevolen:
finite validatie vóór clamp en regressies voor NaN en plus/min oneindig.

## Niet getest

- Geen echte AI-provider, webresponse, credentials of netwerk.
- Geen bewezen UI-consumer van de procesglobale metadata.
- Geen browser-, toegankelijkheids- of responsive flow in deze servicebatch.
