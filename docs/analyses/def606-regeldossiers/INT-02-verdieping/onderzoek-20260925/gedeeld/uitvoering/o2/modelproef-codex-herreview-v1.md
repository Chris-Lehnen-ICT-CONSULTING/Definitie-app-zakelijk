**Oordeel: R1 en R2 gesloten; geen nieuwe bevestigde bevindingen.** Dit pakket is technisch gereed voor de beperkte live proef zodra het profiel-/budgetakkoord herleidbaar aan **manifest v2** is gekoppeld. Deze review verleent geen toestemming voor uitvoering.

Beoordeeld: uitsluitend correctiediff  
`dff713fd45a2c87b6d3b646e500e108b5cd61b03..979ca0585100d94b613829d924c6d8bba4f24f1b`.

HEAD vóór en na review bevestigd; werkboom schoon, detached HEAD. Alleen runner en eigen tests gewijzigd. Zelfstandig gereviewd, zonder delegatie of extra CLI-sessies.

**Beoordeling per punt**

| Punt | Status | Concreet bewijs |
|---|---|---|
| **R1/P1 — model-/prijsbinding** | **Gesloten** | [Modelcontrole op regel 508](/private/tmp/def835-wp2-review-20260927/scripts/analysis/def835_int02_modelproef.py:508) vereist exact `claude-opus-5`. Zes afwijkingsvarianten stoppen na één telling en één inference, zonder WP1-oordeel. Tokens blijven geregistreerd; kosten worden expliciet onbekend, zonder Opus-prijs toe te kennen. |
| **R2/P2 — transportconfiguratie** | **Gesloten** | [SDK-controle op regel 696](/private/tmp/def835-wp2-review-20260927/scripts/analysis/def835_int02_modelproef.py:696) en [requestcontrole op regel 400](/private/tmp/def835-wp2-review-20260927/scripts/analysis/def835_int02_modelproef.py:400) weigeren afwijkende bestemming, poort, gebruikerinfo en headers/authvarianten. De eerdere reproductie en afzonderlijke varianten geven nul verzendingen. Telling en inference behouden dezelfde API-key/API-versie; extra Authorization wordt geweigerd. Transportidentiteit staat in het manifest. |
| **Ondersteunde usagevormen** | **Gesloten** | [Usagecontrole op regel 531](/private/tmp/def835-wp2-review-20260927/scripts/analysis/def835_int02_modelproef.py:531) ondersteunt de onderzochte SDK-velden. Alleen aantoonbaar `standard`/`global` krijgt een prijs. Onbekende velden en afwijkende vormen stoppen verdere calls. De test met 37 thinking-tokens bevestigt dat uitsluitend het inclusieve `output_tokens` wordt gefactureerd in de berekening. |
| **Deadline/cancellation** | **Gesloten voor het gevraagde scenario** | De hangende fake-inference wordt met een geïnjecteerde deadline van 0,05 seconde afgebroken. Test bevestigt `timeout`, één telling/inference, `CancelledError`, geen vervolgcall en geen ruwe fouttekst of sleutel in de gecontroleerde uitvoer. |

**Onafhankelijke verificatie**

Uitgevoerd vanuit de reviewwerkroot:

```sh
env -u ANTHROPIC_API_KEY -u OPENAI_API_KEY \
  DEFINITIE_DISABLE_DOTENV=1 PYTHONDONTWRITEBYTECODE=1 \
  /Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python \
  -m pytest tests/unit/validation/test_def835_int02_modelproef.py \
  -p no:cacheprovider --tb=short
```

Resultaat: **75 passed in 3.26s, exit 0**, met de bestaande offline gates en fake providergrens.

Eerste rapport, correctieopdracht, providercontrole, correctieverslag en aangewezen bewijslogs gecontroleerd:

- **RED-v2:** 34 failed, 41 passed, exit 1 op de oude runner. R1 faalt daadwerkelijk op drie inferencecalls tegenover één verwacht. Dit is gedragsmatige RED.
- **GREEN-v1:** 75 passed, exit 0; runner- en testhash komen overeen met de beoordeelde commit. Tussen RED en GREEN is het testbestand geformatteerd; de bytes zijn dus niet identiek.
- **Lint/commit/dry-run:** dossierbewijs toont geslaagde Black/Ruff-controles en commit-hooks, normale voorbereiding exit 0 en weigering van de transportreproductie exit 2.
- Alle **13 bronhashes**, manifestidentiteit en drie payloadhashes/lengtes kloppen. De modelpayloads zijn gelijk aan v1.

Manifest v2 staat op **pending** en heeft SHA-256:

```text
54c75b43b2b55a132e58a896f2d5d909bebf97b521a26ff0d77bb783a0df35c8
```

**Beperkingen**

De oorspronkelijke collection-RED blijft onvoldoende bewijs voor gedragsmatige TDD van de eerste ronde. De correctieronde heeft dat bewijs wel. De 478 overige regressietests zijn niet herhaald: productiecode en gedeelde fixtures zijn ongewijzigd; geen concrete doorwerking vastgesteld. Geen nieuwe mutatiematrix uitgevoerd.

Model-ID, tier en geografie worden pas **na het antwoord** gecontroleerd. Een afwijkende call kan dus al kosten hebben veroorzaakt; deze worden als onzeker geregistreerd. De reservering is geen factuurgarantie. Echte provideracceptatie, alle deadlinepaden, modelkwaliteit en productiegeschiktheid zijn hiermee niet bewezen.

Geen bronwijzigingen, echte modelcalls, echte sleuteltoegang, productiegegevens of activering uitgevoerd. USD1-profielakkoord en WP5a blijven open; ik heb geen akkoord gemaakt. De automatische handover is volgens de sessie-instructie gearchiveerd.