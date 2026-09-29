**F2 en F4 gesloten. Geen nieuwe bevindingen in deze correctiedelta. F1 en F3 blijven gesloten.**

De herhaalde echte-dienstrepro bevestigt op tekst- én recordroute:

- **F2:** een routerbeleidswijziging tijdens de FakeAI-call, ná de interne routering, geeft nu INT-02 `error`, `MELDING_E` en geen assessment. Eén FakeAI-call; geen extra modelcall.
- **F4:** een uitzondering bij het ophalen van `configuratie` geeft nu een herkenbare INT-02-error binnen `validation_status="validated"`, zonder `assess`-aanroep en zonder ruwe uitzonderingstekst in log of resultaat.
- De gerichte tests bevestigen bovendien dat stabiele configuratie `pass/current` behoudt en ongeldige, afwijkende of falende na-snapshots worden afgewezen.

De controle betreft de publieke configuratie direct vóór publicatie. Zij bewijst geen providerattestatie of detectie van een volledig teruggedraaide tussentijdse wijziging; deze meetgrens blijft expliciet behouden.

Bronidentiteit gecontroleerd:

- Reviewbasis: `979ca0585100d94b613829d924c6d8bba4f24f1b`.
- Bronwerkboombasis: `d769276041e619103ace7bc66e65419d480dae99`; `src/tests` zijn tussen beide bases gelijk.
- Manifest-v4: **9/9 bestandshashes correct**, ook na verificatie en gelijk aan coördinator `before`/`after`.
- Correctiedelta: `3db38e9fe4b69f0ed292c74258e76cd61c8a7b6a54e2995a983b96e7983866cc`.
- Volledige patch: `052ab21212d7122419e64a1a12a8915639193a7dd7634ecaf083b06eeae2f1cd`.

De volledige patch is exact gereconstrueerd. Terugrekening van de delta levert manifest-v3 op: uitsluitend de twee opgegeven bestanden gewijzigd, overige zeven bytegelijk.

Zelf uitgevoerd, steeds met `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1`:

```bash
/Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python \
/private/tmp/wp5a-codex-F24-repro-20260928-v1.py
```

**Exit 0:** vier reproscenario’s geslaagd. In deze nieuwe tijdelijke versie zijn uitsluitend de oude foutverwachtingen aangepast; het oorspronkelijke reprobestand is behouden.

```bash
/Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python -m pytest \
tests/unit/services/orchestrators/test_def835_int02_wrappers.py \
-k 'beleidswijziging_tijdens_modelcall or stabiele_configuratie_blijft or na_snapshot or f4_' \
-q -p no:cacheprovider -p no:randomly -o addopts=''
```

**Exit 0: 14 passed, 60 deselected.**

Behouden bewijs gecontroleerd:

| Bewijs | Resultaat |
|---|---|
| RED-v2, v3-productie en definitieve testhash | Exit 1: 12 failed, 2 passed; gedragsmatige fouten |
| GREEN-v2 | Exit 0: 14 passed |
| Gerichte set en coördinatorverificatie | Exit 0: 293 passed |
| Brede gerichte regressielog | Exit 0: 2.966 passed, 0 skipped |
| Negenbestandslint, inclusief coördinatorbewijs | Ruff en Black exit 0 |

GREEN-v1 met exit 127 was een padfout, **geen testrun**. De bestaande dertien mypy-fouten blijven open; mypy en de volledige unit-suite zijn niet herhaald.

Geen bron-/testwijzigingen, gitmutaties of livecalls uitgevoerd. Dit sluit de beoordeelde F2/F4-bevindingen; het verklaart niet heel O2 gereed of het model gekwalificeerd.