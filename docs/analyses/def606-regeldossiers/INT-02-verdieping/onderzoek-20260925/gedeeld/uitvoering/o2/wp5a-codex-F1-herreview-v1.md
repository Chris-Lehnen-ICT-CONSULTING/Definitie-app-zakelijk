**F1 gesloten. Geen nieuwe bevindingen in de correctiedelta. F2 en F3 blijven open.**

De wijziging in [modular_validation_service.py:1487](/private/tmp/def835-wp2-review-20260927/src/services/validation/modular_validation_service.py:1487) laat uitsluitend `decision_rule_assessment` zijn eigen WP1-invoercontrole uitvoeren. De gerichte verificatie bevestigt:

- Exacte NE-melding op basis van de oorspronkelijke kern, ook wanneer cleaning de kern leegmaakt of invult.
- Ongeldige aanwezige recordkern `None` en bedoeling `42` zonder context geven `error`.
- Correcte O2-documentvorm: `def835-int02-assessment/1`, onderdeel `beoordeling`, `review.actuality=null`, `assessment=null`.
- Nul dienstaanroepen bij deze wrappergevallen.
- Behoud van het bestaande O1-gedrag.

Patroonsignalen bij NE/error blijven bestaande S1-leeshulpen. In deze delta is geen contractconflict aangetoond; geen wijziging van dat beleid nodig.

**Bronidentiteit gecontroleerd:**

- Basis: `979ca0585100d94b613829d924c6d8bba4f24f1b`.
- `wp5a-reviewmanifest-v2.json`: alle zeven bestandshashes kloppen, ook met het coördinatorbewijs en na de tests.
- F1-delta: `29517a408175bf71a0e4c72166e4f6adac7b6948fca03cbf86dda2123027b2a4`.
- Volledige snapshotpatch: `a577e702f9b488e55516456e414810fcb504120840c86a68c550ce7df250d6d1`.

De volledige patch is exact gereconstrueerd. Omgekeerde toepassing van de F1-delta levert voor alle drie gewijzigde bestanden exact de v1-hashes op. Geen testgevallen verwijderd.

Zelf uitgevoerd:

```bash
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 \
/Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python -m pytest \
-q -p no:cacheprovider -p no:randomly -o addopts='' \
tests/unit/validation/test_def835_int02_modular.py::test_f1_ne_volgt_de_oorspronkelijke_kern_in_o2_vorm \
tests/unit/validation/test_def835_int02_modular.py::test_f1_ongeldige_metadata_zonder_context_is_error \
tests/unit/services/orchestrators/test_def835_int02_wrappers.py::test_f1_zonder_context_beslist_de_o2_evaluator_zonder_aanroep \
tests/unit/validation/test_def771_int02_o1.py
```

**Exit 0: 53 passed** — tien F1-tests en 43 bestaande O1-tests.

Behouden bewijs gecontroleerd op hashes, bronbinding en resultaten:

| Bewijs | Resultaat |
|---|---|
| F1 RED-v2 tegen v1-productie | Exit 1: 9 failed, 1 passed; concrete meldings-, status- en vormfouten |
| F1 GREEN | Exit 0: 59 passed |
| Gerichte regressie | Exit 1: 2.908 passed, 11 skipped, uitsluitend F3 gefaald |
| Coördinator: 59 WP5a- plus O1-tests | Exit 0 |
| Ruff en Black op de drie gewijzigde bestanden | Exit 0 |

Het verschil tussen de RED-v2-testhash en de definitieve modular-testhash bestaat aantoonbaar uitsluitend uit de twee genoemde commentaarregels. De wrappertests zijn bytegelijk. Volledige unit-suite en mypy niet herhaald; het eerdere bewijs blijft behouden.

**Bestaande dispositie blijft:** F2 **Important — fix nu**, met onafhankelijke configuratiebinding; F3 **Important voor de testpoort — fix nu**, met gedragsgerichte herijking van de bestaande guard. Beide wachten op Chris’ akkoord voor de gebundelde uitbreiding naar negen bestanden/dienst-API.

Geen bron-/testwijzigingen of modelcalls uitgevoerd. Dit oordeel sluit uitsluitend F1; geheel WP5a en O2 zijn hiermee niet afgerond of modelgekwalificeerd.