# BATCH-024 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-kierkegaard`
- Onafhankelijke verifier: `codex-galileo`
- Scope: 11/11 blobs, 2.974/2.974 fysieke regels en 150/150 Python-symbolen

Alle toegewezen regels en symbolen zijn rechtstreeks uit base-OID's gelezen.
209 relevante unittests waren effectief groen; kruisverificatie gaf 124/125
groen met één volgordegevoelige, vooraf gevulde Streamlit-cachetest.

## Bevindingen

### B024-001 — P3 — dormant schemafactories valideren alleen key presence

`src/services/validation/types.py:222-350,465-476,761-788` accepteert score 2,0
als valid; JSON Schema meldt vijf maximumfouten. Normalisatie accepteert ook
verkeerde version-, bool-, score- en UUID-typen. Geen productie-importer gevonden.
Aanbevolen: centrale schema/Pydantic-validatie met ranges, enums en UUID.

### B024-002 — P3 — compatibilityvalidator laat iedere invoer slagen

`src/toetsregels/adapter.py:125-158` laadt regels maar voert ze niet uit. Lege
tekst met ARAI-01 gaf `rules_checked=1, violations=[], passed=True`. Alleen een
lokale demo is caller. Aanbevolen: echte validator delegeren of expliciet
`NotImplementedError`; nooit fail-open.

### B024-003 — P2 — cached manager is geen drop-in replacement

`src/toetsregels/cached_manager.py:4-5,17-23,76-86,118-150` verandert
semantiek: origineel/gecached kritieke regels 21/39, categorie TYPE 36/0 en
`validate_regel({})` vijf errors versus leeg. Actieve code gebruikt momenteel
alleen `get_all_regels`; verdere impact is vermoed. Aanbevolen: delegeren naar
canonieke logica en parity-contracttests voor elke publieke methode.

### B024-004 — P2 — kritieke ARAI-06 valt door ID-mismatch weg

`src/toetsregels/manager.py:143-178,246-258` zoekt `ARAI06.json`, terwijl de
blob `ARAI-06.json` heet. Kritieke selectie geeft 21/22 en categorieën missen de
regel. Een verdere productiecaller van `DefinitieValidator` is niet gevonden.
Aanbevolen: één canonieke ID-notatie en startupvalidatie van alle setreferenties.

### B024-005 — P3 — dormant modular loader keert ARAI-01 om

`src/toetsregels/modular_loader.py:49-77,118-161` zoekt `ARAI_01.py`, mist de
bestaande naamvarianten en behandelt een verboden patroonmatch als succes. Het
foute voorbeeld passeerde; het goede faalde. Geen productiecaller gevonden.
Aanbevolen: canonieke resolver en parametrische goede/foute contractvoorbeelden.

### B024-006 — P3 — EvaluationContext-metadata is niet readonly

`src/services/validation/types_internal.py:51-107` noemt metadata immutable,
maar directe constructie aliast dezelfde dict en `from_params` maakt alleen een
ondiepe outer copy. De service muteert metadata bewust als accumulator.
Aanbevolen: immutable/deep-copied metadata plus aparte accumulator, of de
readonly/frozencontractclaim expliciet verwijderen.

## Niet getest

- Geen externe consumers van dormant compatibility-API's of UI-flow.
- Geen netwerk, credentials of echte Prompt Forge-run.
