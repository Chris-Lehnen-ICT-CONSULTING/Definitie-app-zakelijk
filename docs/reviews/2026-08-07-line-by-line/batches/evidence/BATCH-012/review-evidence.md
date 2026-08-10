# BATCH-012 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-hypatia`
- Onafhankelijke verifier: `codex-root`
- Scope: 6/6 blobs, 1.714/1.714 fysieke regels en 87/87 Python-symbolen

Alle toegewezen regels en symbolen zijn rechtstreeks uit de immutable
Git-objecten gelezen. Er zijn geen applicatiebestanden gewijzigd.

## Verificatie

- Primaire gerichte suite: 191 tests geslaagd, 1 verwachte xfail.
- Onafhankelijke hermetische base-exportselectie: 105 tests geslaagd, 1 xfail.
- Ruff en Black: geslaagd.
- Deterministische subprocess-, thread-, fake-client- en fake-containerrepro’s;
  geen echte providercall of credential gebruikt.

## Bewezen bevindingen

### B012-001 — P1 — gesanitized wrapper houdt raw SDK-cause en traceback

`src/services/ai/openai_client.py:84-96` en `anthropic_client.py:137-149`
sanitizen de wrapper maar doen `raise ... from exc`; de orchestrator logt op
`definition_orchestrator_v2.py:1286-1287` met `exc_info=True`. Fake secret:
wrapper bevatte hem niet, `__cause__` en formatted traceback wel. Aanbevolen:
exceptionchains vóór logging sanitiseren of een nieuwe exception zonder raw
cause buiten de providerboundary laten ontsnappen; secret-redactiontest op
wrapper, cause, traceback en logs.

### B012-002 — P1 — provider/keyreset laat singletonconfig op oude waarde staan

`src/services/container.py:108-125,978-1027` reset containers, maar niet de
singleton ConfigManager; `model_router.py:128-136` leest daaruit. Subprocess:
environment wijzigde naar OpenAI, terwijl manager/container/router Anthropic en
de oude key hielden. Dit is een andere stale-cacheoorzaak dan PILOT-014.
Aanbevolen: één versioned, session-scoped configuratiebron en atomaire invalidatie
van ConfigManager, container, router en adapter; secrets niet procesglobaal.

### B012-003 — P2 — singletonfactories zijn racegevoelige check-then-create

`container.py:177-202,659-671,961-975` heeft geen synchronisatie. Een
deterministisch georkestreerde two-threadrepro construeerde en retourneerde twee
instanties. Aanbevolen: lock/context-local lifecycle of dependency-injectie met
expliciete request-/sessiescope en concurrencytest.

### B012-004 — P2 — containerreset sluit clients en resources niet

`container.py:879-883,986-1023` wist dictionaries, terwijl `base_client.py:106-108`
een closecontract definieert. Aanbevolen: async/sync teardownprotocol dat iedere
geïnitialiseerde resource exact eenmaal sluit vóór cacheclear, met testdoubles.

### B012-005 — P2 — providerresponse-edgecases lekken als fout of leeg succes

`openai_client.py:98-110` indexeert `choices[0]`; fake `choices=[]` gaf raw
IndexError. `anthropic_client.py:151-166` filtert non-text blocks en retourneerde
een succesvolle lege ChatResponse. Het mechanisme is bewezen; een echte provider-
response met deze vorm is niet getest. Aanbevolen: responsevorm expliciet
valideren en een typed providerprotocolfout retourneren.

### B012-006 — P2 — één weblookup-initfout wordt permanent als None gecachet

`container.py:449-468` cachet de eerste mislukking. Repro: eerste aanroep None,
tweede None en constructor_calls bleef 1, hoewel de dependency daarna beschikbaar
was. Aanbevolen: fouten niet als singletonwaarde cachen; retry/backoff of expliciete
failed-state met reset en observability.

### B012-007 — P2 — shallow configmerge breekt gedeeltelijke providerconfig

`model_router.py:94-116,138-167` overschrijft de hele nested providersectie.
Een gedeeltelijke override mist vereiste siblingvelden en crasht pas bij een
gebruikersactie. De actuele repositoryconfig is compleet. Aanbevolen: deep merge
met strikt configschema en startupvalidatie.

### B012-008 — P3 — onbekend model krijgt stil plausibele defaultkosten

`model_router.py:160-167` retourneert defaultprijzen voor ieder onbekend model.
De fout is conditioneel, maar bewezen. Aanbevolen: onbekend model expliciet
markeren/fail-loud, of kosten als onbekend publiceren zonder financieel getal.

### B012-009 — P3 — fallbackimport importeert exact dezelfde registry

`container.py:477-483` importeert in try en except dezelfde SynonymRegistry en
kan dus geen compatibiliteitsfallback bieden. Aanbevolen: echte alternatieve
dependency importeren of de dode fallback verwijderen.

## Niet getest

- Echte AI-responses, providerkosten, weblookup, credentials en netwerk.
- Twee echte Streamlit-browsersessies; races zijn gecontroleerd met threads.
- Visuele UI/a11y/responsive aspecten zijn niet op deze servicebatch getest.
