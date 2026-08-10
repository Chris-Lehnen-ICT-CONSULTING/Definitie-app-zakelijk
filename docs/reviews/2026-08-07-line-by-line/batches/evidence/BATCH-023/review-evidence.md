# BATCH-023 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-hypatia`
- Onafhankelijke verifier: `codex-root`
- Scope: 11/11 blobs, 3.501/3.501 fysieke regels en 123/123 Python-symbolen

Alle regels en symbolen zijn uit immutable object-ID's gelezen. De primaire
selectie omvatte 136 geslaagde tests; Ruff en Black waren schoon. Repro's
gebruikten uitsluitend mocks en lokale input.

## Bevindingen

### B023-001 — P1 — soft floor overrulet gefaalde kritieke gates

`src/services/validation/modular_validation_service.py:644-694` berekent
critical-, overall- en categoriegates, maar accepteert daarna via score >=0,60
wanneer de errorcode niet op een korte allowlist staat. Een gepatchte kritieke
ESS-999 gaf score 0,93, `gates_failed`, maar `is_acceptable=True`. Aanbevolen:
één autoritatief gatebeleid; critical/error nooit via soft floor overrulen.

### B023-002 — P1 — gedegradeerde fallback crasht bij eerste validatie

`modular_validation_service.py:181-183,212-232,258-321,996` maakt fallbackregels
maar initialiseert twee compiled caches niet. Een lege manager gaf bij eerste
validatie `AttributeError: _compiled_json_cache`. Aanbevolen: caches vóór alle
loadpaden initialiseren en empty/throwing-managerregressies toevoegen.

### B023-003 — P1 — categorie en context verdwijnen uit actieve validatieflow

`modular_validation_service.py:348-404,1377-1407,1535-1608` negeert de categorie
en verwacht contextmarkers; de actieve wrapper geeft alleen correlation-ID door.
TYPE en PROCES werden byte-identiek en duplicate/contextpolicy kan niet correct
werken. Aanbevolen: wrapperverrijking werkelijk toepassen, metadata veilig mergen
en categorie als expliciet contextveld doorgeven.

### B023-004 — P2 — cleaningconfigflags hebben geen effect

`src/services/cleaning_service.py:23-30,93-176` gebruikt `enable_cleaning` en
`track_changes` niet. Met beide False werd GPT-tekst toch opgeschoond en tracking
gevuld. Aanbevolen: disabled early no-op en conditionele trackingtests.

### B023-005 — P2 — schemahelper accepteert willekeurige vorm

`src/services/validation/mappers.py:180-200` cast iedere dict met `version` en
`system`. Bogus version, stringscore en ontbrekende verplichte velden kwamen
ongewijzigd door. Actieve orchestrators gebruiken deze helper. Aanbevolen:
volledige required/type/version/schema-validatie op een genormaliseerde copy.

### B023-006 — P2 — raw exceptiondetail komt in clientresponse

`mappers.py:234-260` zet exceptiontekst in violationmessage en `system.error`;
de actieve wrapper geeft `str(e)` door. Dummy `API_KEY=review-secret` verscheen
tweemaal. Aanbevolen: generieke clientcode plus correlation-ID; details alleen
geredigeerd server-side loggen.

### B023-007 — P2 — publieke batchvalidatie breekt haar contract

`modular_validation_service.py:1697-1767` deadlockt bij concurrency 0, laat één
malformed item de hele batch afbreken en retourneert een UUID die directe JSON-
serialisatie breekt. Geen directe productiecaller gevonden. Aanbevolen: minimum
1 valideren, per-item degraded errors en publieke contextserialisatie.

### B023-008 — P3 — ContextValidator crasht op ongeldige roottypen

`src/services/validation/context_validator.py:82-104,145-159,250-263` gaat na
structure-errors door; een list crasht op `.get` en een integeritem op `.strip`.
Geen productiecaller gevonden. Aanbevolen: early return en type-invalid velden
overslaan na een duidelijke validation error.

### B023-009 — P3 — lege wettelijke referentie crasht ASTRAValidator

`src/services/validation/astra_validator.py:201-217,264-270` indexeert `ref[0]`
na strip. `{'wettelijk':['']}` gaf `IndexError`; geen productiecaller gevonden.
Aanbevolen: lege/whitespacewaarden eerst afwijzen.

### B023-010 — P3 — concrete cleaningservice wordt verkeerd aangeroepen

`modular_validation_service.py:364-389` roept `clean_text(text)` aan, terwijl
`cleaning_service.py:93` ook `term` vereist. De TypeError wordt verborgen en raw
tekst gevalideerd; eigen spy bleef onaangeroepen. Productie injecteert hier nu
geen concrete cleaner. Aanbevolen: `await clean_text(text, begrip)`.

### B023-011 — P3 — fallbackregex gebruikt letterlijke backslashes

`modular_validation_service.py:316-319` bevat raw patronen met `\\b`. Na
handmatige cache-initialisatie passeerde `iets simpel ... complex`. Aanbevolen:
echte woordgrenzen `\b` en een gedragstest; dit pad is latent achter B023-002.

## Niet getest

- Geen externe services, echte productie-batchcaller of browser/UI-flow.
- Eén verouderde category-regenerationintegratietest faalde buiten runtimepad.
