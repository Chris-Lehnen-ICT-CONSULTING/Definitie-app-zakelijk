**R1 is aantoonbaar gesloten. Geen nieuwe bevindingen in de correctiediff.**

De helper gebruikt uitsluitend zekere zinsgrenzen. Mijn eerdere offline diagnose bevestigt nu volledige citaten voor tussenzinnen, opsommingen en ingebedde criteria, met correcte offsets. Herhaalde zinnen behouden afzonderlijke posities: `0–25` en `27–52`. Status blijft `review_required`. [Reproductiebewijs](/private/tmp/def771-codex-review-1ZSCEP/diagnose_passages_r1_correctie.json).

Gecontroleerd bewijs:

- RED: **6 failed, 28 passed**, exit 1.
- GREEN: **149 passed**, geen failures of skips, exit 0.
- Ruff, Black, `make lint` en normale commithooks geslaagd.
- C1-run3: **36/36**, geen citaatfouten, exit 0; bronhashes komen overeen met de huidige code.
- Scope: uitsluitend de twee opgegeven bestanden, **+28/−10**; bestaande invoercasussen behouden.

Gecontroleerde identiteit:

- Base: `5fb535ee45671007e5cb4557509560c793eec290`
- Head: `9ff3eac199c3eb6e77a44ee47220f91226ffed44`
- Diff-SHA-256: `bae61e43834952859e64ddf5eaef4535dd2c0ca24ea4350f0facd5fd2dd3babc`
- Reviewsessie: `01a0dc44-26c6-7de3-b2f9-b0f79e5a27ff`

**Oordeel: correctie akkoord; R1 blokkeert niet meer.** De eerdere review blijft voor ongewijzigde onderdelen geldig. De nieuwe volledige pytest-run valt buiten dit oordeel; de eerdere 67 basisfailures bewijzen niets over de uitkomst daarvan. Geen bronbestanden gewijzigd of brede tests uitgevoerd.