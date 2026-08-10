# BATCH-014 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-kierkegaard`
- Onafhankelijke verifier: `codex-galileo`
- Scope: 4/4 blobs, 1.901/1.901 fysieke regels en 132/132 Python-symbolen

Alle inhoud is rechtstreeks uit de immutable Git-objecten gelezen. Er zijn geen
applicatiebestanden gewijzigd.

## Verificatie

- De primaire gecombineerde regressierun: 126 tests geslaagd.
- De onafhankelijke adversarial selectie valt binnen 42 geslaagde tests.
- Ruff en Black: geslaagd.
- Veilige fake-backends zijn gebruikt; geen echte Redis, AI of netwerkcall.

## Bewezen bevindingen

### B014-001 — P1 — Redis-cache deserialiseert aanvallerbytes met pickle

`src/services/definition_generator_cache.py:199-223` voert `pickle.loads`
rechtstreeks uit op bytes van `redis.get`. Een veilige fake-Redisrepro bewees
de exacte byteflow; de primaire repro liet een `__reduce__`-marker uitvoeren
vóór de methode `None` retourneerde. Exploitatie vereist schrijfcontrole over
de Redis/prefix en live deployment is niet getest. Aanbevolen: verwijder pickle
en gebruik een strikt, versieerbaar JSON/msgpack-schema; ACL/TLS/netwerkisolatie
blijven alleen defense-in-depth.

### B014-002 — P1 — cache-identiteit en invalidatie behandelen contextvarianten fout

`src/services/definition_generator_cache.py:333-338,404-444,475-513` laat
juridische, wettelijke, organisatorische en documentcontext, instructies,
categorieën, options, tenant en werkelijk model uit de key. Twee semantisch
verschillende requests kregen `term|gpt4`. Een entry opgeslagen met
`context={"doc":"A"}` kon met `invalidate_cache(request)` niet worden verwijderd
en bleef opvraagbaar; een gedeeltelijke hybrid delete kan stale Redis laten
terugkeren. De cache is geëxporteerd maar momenteel niet productie-geïnstantieerd.
Aanbevolen: canonieke, schema-versioned serialisatie van alle outputbepalende
velden en één identieke identity-input voor get/set/delete, met expliciete
partial-failuresemantiek.

### B014-003 — P1 — document-only context verdwijnt uit de actieve prompt

`src/services/definition_generator_context.py:70-107,162-171,202-256` neemt
sources wel op in tekst, maar niet in `has_any_context`. De UI levert document-
context via `definition_generation_handler.py:277-335`; `prompt_service_v2.py`
bouwt de source, waarna `prompt_orchestrator.py:452-459` de contextmodule
overslaat. Reproductie: source `document: SENTINEL` staat in
`get_all_context_text()`, maar `has_any_context()==False` en de module ontbreekt.
Aanbevolen: één presence-check over alle niet-lege base-items en bruikbare
sources, met een end-to-end prompttest voor alleen documentcontext.

### B014-004 — P2 — linguïstische enhancement valt altijd uit met regexfout

`src/services/definition_generator_enhancement.py:303-360` gebruikt raw
replacement `r'(\w+) wordt'`; Python behandelt `\w` daarin als ongeldige
replacementescape. Zelfs een gewone enhance-aanroep geeft `PatternError`; de
coordinator slikt dit op regels 417-426. De concrete enhancer is niet als live
productie-implementatie aangetroffen. Aanbevolen: geldige backreferences of,
veiliger, deze semantisch riskante automatisch actief-makende herschrijving
verwijderen; test een echte match en het foutpad.

### B014-005 — P2 — latere enhancements overschrijven eerdere resultaten

Alle strategieën draaien in `definition_generator_enhancement.py:417-440` op de
originele Definition; vervolgens worden volledige teksten achtereenvolgens
toegepast. Een clarity-resultaat verdween toen completeness als laatste zijn
variant van het origineel instelde, terwijl metadata beide als toegepast meldde.
Aanbevolen: iedere stap tegen de actuele tekst herberekenen of patches met
base-fingerprint en conflictdetectie modelleren.

### B014-006 — P2 — reconstructie van Definition verliest domein- en auditvelden

`definition_generator_enhancement.py:458-480` kopieert slechts vier à vijf
velden. Een volledig object verloor onder meer `id`, toelichting, contextlijsten,
synoniemen, categorie, validatie, actor en timestamps. Aanbevolen:
`dataclasses.replace(definition, definitie=...)`, deep-copy van mutabele metadata
en een preservationtest over ieder veld.

### B014-007 — P2 — completeness-heuristiek fabriceert niet-brongebaseerde feiten

`definition_generator_enhancement.py:259-294` voegt bij defaultdrempel `0.6`
stellige procedure- en toepassingsgebiedclaims toe zonder wet, document of
modelinput. `Vergunning: Een toestemming` werd onder meer “Het vergunning heeft
een specifiek doel en volgt een bepaalde procedure.” Aanbevolen: uitsluitend
reviewsuggesties genereren, of inhoud alleen uit citeerbare context afleiden en
daarna juridisch her-valideren.

### B014-008 — P2 — expliciete nested configuratie wordt stil overschreven

`src/services/definition_generator_config.py:237-242,330-351` vervangt onder
meer expliciet REDIS/WARNING/false door MEMORY/DEBUG/true; environmentfactory’s
verschillen hoofdzakelijk in label en roepen post-init opnieuw. Aanbevolen:
defaults in field factories zetten, expliciete waarden respecteren en post-init
niet handmatig opnieuw uitvoeren.

## Niet getest

- Echte Redisconfiguratie, ACL/TLS, Redis-compromittering en cross-tenant
  exploitatie; echte AI/providerresponses en netwerkverkeer.
- Productiereachability van de momenteel ongekoppelde cache/enhancer.
- Visuele UI/a11y/responsive aspecten; deze batch rendert geen UI.
