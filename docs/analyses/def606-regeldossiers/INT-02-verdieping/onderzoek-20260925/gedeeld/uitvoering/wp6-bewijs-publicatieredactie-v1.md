# Publicatiekopieën van pytest-XML

De normale secretscanner blokkeerde de bewijscommit met zes treffers in twee volledige pytest-XML-bestanden. Alle zes zijn bytegelijk aan de expliciet verzonnen projectfixture uit `tests/unit/utils/test_pii_redaction_api_keys.py`; ze staan in geparametriseerde testnamen. Geen credentialincident vastgesteld. De scannerkolommen bevatten het voorafgaande plusteken van de staged diff.

De oorspronkelijke XML-bestanden blijven lokaal behouden en worden niet gestaged. Nieuwe publicatiekopieën vervangen uitsluitend de drie expliciet verzonnen API-testwaarden door benoemde placeholders. Aantallen testgevallen en testsuite-attributen zijn gelijk; uitslagen en foutteksten blijven beschikbaar. Bestaande rapportverwijzingen naar de oorspronkelijke XML horen voor de PR bij de hieronder genoemde publicatiekopieën. Geen scannerconfiguratie, uitzondering of hook gewijzigd.

```json
[
  {
    "bron": "wp5-pytest-volledig.xml",
    "publicatie": "wp5-pytest-volledig-publicatie-v1.xml",
    "vervangingen": {
      "_OUDE_OPENAI_KEY": 3,
      "_PROJECT_OPENAI_KEY": 3,
      "_ANTHROPIC_KEY": 3
    },
    "bron_sha256": "58b26c3c596eb910f26fd049cce6bb22d3b9e7bd0a0857b1688ae1e1539d76b7",
    "publicatie_sha256": "e6dfc1ff9c7d27485fdd6ade026ac1cdbb70c23a3941992e25c5e1491fc2ea74"
  },
  {
    "bron": "wp5-pytest-na-r1.xml",
    "publicatie": "wp5-pytest-na-r1-publicatie-v1.xml",
    "vervangingen": {
      "_OUDE_OPENAI_KEY": 3,
      "_PROJECT_OPENAI_KEY": 3,
      "_ANTHROPIC_KEY": 3
    },
    "bron_sha256": "438479b790149f74f5c3b054a4c6ab421ec85464ab6a8a139f7c488c6e96eeb2",
    "publicatie_sha256": "594a719bf0dbe1fa6e0d3c88245cdd7576bfdab6e1db00f1407d32f524e16df2"
  }
]
```
