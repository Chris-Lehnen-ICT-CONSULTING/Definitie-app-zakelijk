# BATCH-034 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-root`
- Onafhankelijke verifier: `codex-hypatia`
- Scope: 4/4 blobs, 875/875 fysieke regels en 50/50 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit immutable Git-objecten gelezen;
security-middlewarecallers en tests zijn gevolgd, zonder applicatiewijzigingen.

## Verificatie

- 46 gerichte tests en de drie module-smokeflows slaagden.
- Ruff en Black waren schoon.
- Reproducties gebruikten alleen dummyinvoer en een nieuw tijdelijk uitvoerpad.

## Bevindingen

### B034-001 — P2 — top-level typefout laat `is_valid` fail-open slagen

`input_validator.py:498-564` vangt een `data=None`-AttributeError en retourneert
een lege resultatenlijst. `is_valid` op `:646-653` beoordeelt `all([])` als True.
De class wordt door security middleware gebruikt, al is deze exacte trigger in
de huidige flow latent. Aanbevolen: top-level typecheck als expliciete error en
nooit lege validatieresultaten als geldig accepteren.

### B034-002 — P3 — ingebouwde regex wijst geldige Nederlandse invoer af

`input_validator.py:250-292` laat alleen ASCII-letters toe voor begrip en
voorsteller. Een geldig begrip `beëindiging` faalt de patternregel. Aanbevolen:
Unicode-lettercategorieën of een expliciete Nederlandse naam-/termvalidator.

### B034-003 — P3 — rapportexporters kunnen buiten `reports/` schrijven

`input_validator.py:721-747` combineert `Path("reports")` met een ongevalideerde
filename; een absoluut pad verwerpt de basisdirectory. Hetzelfde patroon staat in
`dutch_text_validator.py:618-643`. Beide sinks zijn bewezen, maar er is geen
productiecaller of user-controlled filename aangetoond. Aanbevolen: basename
allowlist, resolve+containmentcheck en veilige create-new/atomic write.

## Niet getest

- Geen exploitabele productiecaller voor de rapportfilename gevonden.
- Geen browser-, externe provider-, netwerk- of credentialflow.
