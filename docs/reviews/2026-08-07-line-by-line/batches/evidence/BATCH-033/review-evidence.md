# BATCH-033 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-root`
- Onafhankelijke verifier: `codex-hypatia`
- Scope: 10/10 blobs, 3.034/3.034 fysieke regels en 129/129 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit immutable Git-objecten gelezen.
Actieve generator-, edit- en expert-reviewcallers zijn gevolgd; applicatiebestanden
zijn niet gewijzigd.

## Verificatie

- 46 gerichte tests slaagden; drie module-smokeflows exit 0.
- Ruff en Black waren schoon.
- Veilige Streamlit-function mocks bewezen foutfeedback; geen echte secret gebruikt.

## Bevindingen

### B033-001 — P2 — malformed score crasht rendering en wordt raw getoond

`validation_view.py:230` doet onbeschermd `float(overall_score)`. De actieve
`ValidationRenderer` vangt dit en toont `str(exception)` op
`validation_renderer.py:27-44`. Een dummywaarde `API_KEY=review-secret` verscheen
exact in `st.error`. Aanbevolen: strict finite score 0..1 aan de boundary en een
generieke UI-melding met correlation ID.

### B033-002 — P2 — dezelfde regel kan 100% geslaagd én gefaald tonen

`validation_view.py:127-147` en de dubbele rendererimplementatie tellen passed en
failed apart, maar de noemer als unie. ESS-01 in beide sets geeft total=1,
passed=1, failed=1, percentage=100%. Normale service-uitvoer is disjunct; adapters
valideren die invariant niet. Aanbevolen: schema-invariant afdwingen en overlap
fail-closed uit `passed_rules` verwijderen.

### B033-003 — P3 — hoofdletterregel matcht normale lowercase woorden

`dutch_text_validator.py:97-104` definieert `[A-Z]{4,}`, maar alle regels worden
op `:373-388` met `IGNORECASE` uitgevoerd. Een normale Nederlandse zin kreeg
waarschuwingen voor `normale` en `Nederlandse`. Aanbevolen: flags per regel en
een case-sensitive hoofdletterdetector.

### B033-004 — P3 — standaard consistentiecontrole wijst naar niet-bestaand pad

`definitie_validator.py:754-780` resolveert standaard naar
`src/config/toetsregels/regels`, terwijl de regels onder `src/toetsregels/regels`
staan. De module-smoke retourneert altijd een directory-error. Aanbevolen: pad
relatief aan de canonieke package-root en een default-path-test.

### B033-005 — P3 — cwd-afhankelijke regelhints verdwijnen buiten repo-root

De actieve renderers lezen `Path("src/toetsregels/regels")`. Vanuit een andere
werkdirectory worden naam, uitleg en voorbeelden leeg. De gedocumenteerde
repo-rootstart werkt vermoedelijk; deploymentimpact is daarom `suspected`.
Aanbevolen: `importlib.resources` of een package-relative absoluut pad.

## Niet getest

- Actieve upstream-trigger voor overlappende pass/fail-sets is niet aangetoond.
- Browsercontrast, toetsenbord, screenreader, touch en responsive viewports zijn
  in deze functionele review niet getest.
