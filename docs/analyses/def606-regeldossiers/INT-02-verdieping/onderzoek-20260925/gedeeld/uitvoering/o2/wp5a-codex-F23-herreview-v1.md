**F2 blijft open; F3 is gesloten. F1 blijft gesloten.** De oorspronkelijke F2-repro is opgelost, maar de correctie voldoet nog niet volledig aan het geaccordeerde wijzigings- en foutbeleid.

1. **F2-restpunt — Important; dispositie: fix nu. Configuratiewijziging tijdens de call kan alsnog `pass/current` opleveren.**

   Locatie: [validation_orchestrator_v2.py:745](/private/tmp/def835-wp2-review-20260927/src/services/orchestrators/validation_orchestrator_v2.py:745). Na `assess` wordt uitsluitend tegen de vooraf vastgelegde configuratie vergeleken.

   De [zelfstandige offline repro](/private/tmp/wp5a-codex-F23-repro-20260928-v1.py) gebruikt de echte `Int02AssessmentService`. Tijdens de FakeAI-aanroep, ná de interne routering, verandert het routerbeleid `thinking_default_on`. Op zowel tekst- als recordroute:

   - verschillen de configuraties vóór en na de call;
   - noemt WP1 het document tegen de actuele configuratie `review_required/historical`;
   - publiceert de wrapper toch **`pass/current`**.

   Dit bevestigt de beschreven beperking, maar sluit haar niet: het geaccordeerde voorstel vereist expliciet **“Een wijziging gedurende de aanroep mag nooit stil pass/current worden.”** De nieuwe wijzigingstest verandert de configuratie vóór het binden van het retourdocument en dekt dit latere wijzigingsvenster niet.

   **Minimale correctierichting:** borg configuratiestabiliteit gedurende de beoordeling of controleer vóór publicatie opnieuw de actuele configuratie. Een aangetoonde wijziging moet zonder oordeel naar `error`. Alleen vastleggen dat `current` de startsituatie betekent, voldoet niet aan het huidige akkoord.

2. **F4 — Important; dispositie: fix nu. Fout bij het ophalen van de snapshotfunctie ontsnapt aan de veilige foutafhandeling.**

   Locatie: [validation_orchestrator_v2.py:736](/private/tmp/def835-wp2-review-20260927/src/services/orchestrators/validation_orchestrator_v2.py:736). `getattr(dienst, "configuratie", None)` staat buiten het `try`-blok.

   De repro injecteert een dienst waarvan de `configuratie`-property een `RuntimeError` met synthetische uitzonderingstekst opwerpt. Beide routes leveren:

   - nul `assess`-aanroepen;
   - `validation_unknown`, zonder INT-02-deeluitkomst;
   - **ruwe uitzonderingstekst in zowel log als resultaat** via de buitenste wrapperafhandeling.

   Dit is foutinjectie op de dienstgrens, geen claim dat de standaarddienst zo’n property heeft. Het bewijst wel dat de nieuwe snapshotgrens niet alle ophaalfouten volgens het afgesproken beleid opvangt.

   **Minimale correctierichting:** plaats ook het ophalen van de snapshotfunctie binnen de bestaande veilige foutgrens. Geef INT-02 `error` zonder oordeel en log uitsluitend foutcategorie/type. Voeg deze variant aan de gerichte fouttests toe.

**F3 gesloten:** het bestaande testgeval is onder dezelfde naam behouden en controleert nu gedrag: geen automatische constructie/injectie, geen modelcall, verplicht expliciet profiel/budget en toegestane expliciete factory. Het behouden mutatiebewijs is onderscheidend: normale code slaagt; geïnjecteerde automatische constructie laat de guard falen. De pluginhash en test-/bronhashes passen bij dat bewijs.

Bronidentiteit gecontroleerd:

- Reviewbasis: `979ca0585100d94b613829d924c6d8bba4f24f1b`.
- Bronwerkboombasis: `d769276041e619103ace7bc66e65419d480dae99`; `git diff --quiet … -- src tests` geeft exit 0.
- Manifest-v3: **9/9 hashes correct**, ook na verificatie en gelijk aan coördinator `before`/`after`.
- Correctiedelta: `02d0502166249f565fbb6efb9396cb16995a4b631a14c550eebc37fd298e634d`.
- Volledige patch: `2c8638723a4aff213ad90333769b20f16a22a32041c5ff30004bca43f93b623a`.

De volledige patch is exact gereconstrueerd. Terugrekening van de vierbestandsdelta levert de eerder beoordeelde bronversies op; F1 is bytegelijk behouden.

Zelf uitgevoerd:

```bash
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 \
/Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python -m pytest \
-q -p no:cacheprovider -p no:randomly -o addopts='' \
tests/unit/validation/test_def835_int02_assessment_service.py \
tests/unit/services/orchestrators/test_def835_int02_wrappers.py \
-k 'f2_ or dienst_wordt_niet_door_de_container'
```

**Exit 0: 40 passed, 155 deselected**, inclusief oorspronkelijke F2-repro en F3-gedragsguard.

```bash
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 \
/Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python \
/private/tmp/wp5a-codex-F23-repro-20260928-v1.py
```

**Exit 0:** vier bevestigende reproscenario’s voor bovenstaande bevindingen, uitsluitend lokale fakes. Script-SHA256: `8b8298df41f2281296e9e5436fef5db6753b9a65858708aeee26517e5ca44434`.

Behouden bewijs gecontroleerd op hashes en bronbinding:

| Bewijs | Resultaat |
|---|---|
| RED tegen correctiebasis | Exit 1: 32 failed, 8 passed; eindtests bytegelijk |
| GREEN | Exit 0: 221 passed; RED-selectie 40 passed |
| Gerichte regressie | Exit 0: 2.941 passed, 11 skipped |
| Coördinatortests | Exit 0: 279 passed |
| Negenbestandslint | Ruff en Black exit 0 |
| Mypy | Exit 1: dezelfde 13 fouten in twee WP1/WP2-bestanden; blijft open |

Geen bron-/testwijzigingen, livecalls of gitmutaties uitgevoerd. Geen volledige suite herhaald. Providerattestatie, opslag/C118 en modelkwalificatie zijn hiermee niet bewezen; geheel WP5a/O2 is niet afgerond.