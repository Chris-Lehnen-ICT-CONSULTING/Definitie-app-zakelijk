**Oordeel: nog niet vrijgeven voor live uitvoering.** Twee bevestigde bevindingen raken de model-/prijsbinding en de controle op transportconfiguratie. Offline voorbereiding en de bestaande tests werken.

Beoordeeld: exact `558b50c3f161f819cda6c445f7f81b70888918ac..dff713fd45a2c87b6d3b646e500e108b5cd61b03`. HEAD gecontroleerd vóór en na review; werkboom schoon, detached HEAD. De diff bevat uitsluitend de twee nieuwe bestanden, 1.539 regels. Review zelfstandig uitgevoerd; geen delegatietools aangetroffen of extra CLI-sessies gestart.

1. **P1 — Afwijkende provider-model-ID stopt de proef niet.**  
   Locatie: [def835_int02_modelproef.py:384](/private/tmp/def835-wp2-review-20260927/scripts/analysis/def835_int02_modelproef.py:384), kostenboeking op regel 403.

   De waarnemer registreert `data["model"]`, maar vergelijkt die niet met het goedgekeurde model. De bestaande dienstcontrole vangt dit niet alsnog af: `AIServiceV2` retourneert bij `model` het **aangevraagde** model en geeft de ontvangen model-ID niet door.

   **Reproductie:** gebruik de bestaande `NepProvider` met de drie geldige fixtureantwoorden, maar zet hun responseveld `model` op `"ander-model"`. Roep de echte runnerketen aan met `httpx.MockTransport`, een offline testakkoord en een synthetische sleutel.

   Waargenomen, reproductie exit **0**:

   ```text
   stopreden: null
   inferenties: 3; telverzoeken: 3
   gerapporteerd_model: ander-model (alle drie)
   statussen: fail, review_required, pass
   kosten_usd_berekend: 0.052500000000000005
   ```

   **Impact:** na een aantoonbare modelafwijking volgen nog twee inferencecalls. Bovendien worden kosten berekend met het Opus-profiel terwijl het gerapporteerde model daarvan afwijkt. Daarmee ontbreken de vereiste stop op binding en betrouwbare prijsbinding.

   **Dispositie: corrigeren vóór live gebruik**, door de aangewezen uitvoerder.

2. **P2 — Transportconfiguratie kan buiten het akkoord veranderen; authenticatie van telling en inference kan verschillen.**  
   Locaties: [bestemmingscontrole:298](/private/tmp/def835-wp2-review-20260927/scripts/analysis/def835_int02_modelproef.py:298), [telheaders:333](/private/tmp/def835-wp2-review-20260927/scripts/analysis/def835_int02_modelproef.py:333), [manifestidentiteit:633](/private/tmp/def835-wp2-review-20260927/scripts/analysis/def835_int02_modelproef.py:633).

   De geïnstalleerde SDK leest `ANTHROPIC_BASE_URL` en `ANTHROPIC_CUSTOM_HEADERS`. Het manifest bindt deze effectieve transportinstellingen niet. De bestemmingscontrole controleert geen poort. De tokenmeting kopieert slechts drie headers, waardoor een extra Authorization-header verdwijnt.

   **Reproductie:** maak eerst een standaardmanifest. Zet daarna, uitsluitend binnen de offline reproductie:

   ```text
   ANTHROPIC_BASE_URL=https://api.anthropic.com:8443
   ANTHROPIC_CUSTOM_HEADERS=
     anthropic-version: 2099-01-01
     Authorization: Bearer SYNTHETIC-REVIEW
   ```

   Met hetzelfde manifest en een fake transport accepteerde de runner alle zes requests, exit **0**, `stopreden=null`. Alle requests gebruikten poort 8443 en de gewijzigde API-versie. Authorization was aanwezig bij inference en afwezig bij tokenmeting.

   **Impact:** het akkoord weigert deze configuratiedrift niet; telling en inference hebben niet noodzakelijk dezelfde authenticatiecontext. Dit bewijst niet dat de echte provider deze requests accepteert, maar wel dat de runner ze doorlaat tot de verzendgrens.

   **Dispositie: corrigeren vóór live gebruik.** Begrens of bind de effectieve transportinstellingen en weiger niet-ondersteunde authenticatievarianten vóór verzending.

**Verificatie en bronbinding**

Onafhankelijk uitgevoerd:

```sh
env -u ANTHROPIC_API_KEY -u OPENAI_API_KEY \
  DEFINITIE_DISABLE_DOTENV=1 PYTHONDONTWRITEBYTECODE=1 \
  /Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python \
  -m pytest tests/unit/validation/test_def835_int02_modelproef.py \
  -p no:cacheprovider --tb=short
```

Resultaat: **40 passed in 2.12s, exit 0**. De aanvullende reproducties gebruikten de bestaande offline bootstrap, geblokkeerd netwerk en fake HTTP-transport.

Het voorstel, de uitvoerdersopdracht, het verslag en de aangewezen eindlogs zijn gelezen. De runner- en testhash komen overeen met groen-v2 en commit-v1. Alle **13 bronhashes**, de manifestidentiteit en de hashes/lengtes van de drie opgeslagen payloads zijn gecontroleerd en kloppen.

Regressie-v2 rapporteert **518 passed, exit 0**, inclusief de 40 nieuwe tests: dus **478 overige tests**, niet 518 extra. Lint-v2 vermeldt geslaagde Black- en beide Ruff-controles. Deze regressie- en lintuitkomsten zijn dossierbewijs; ik heb ze niet opnieuw uitgevoerd.

**Bewijskracht en grenzen**

- De echte keten en bestaande prompt worden gebruikt. De requestbody wordt aan het manifest gebonden; uitsluitend de invoer van C105/C107/C112 gaat mee. Het experimentele profiel claimt geen modelkwalificatie.
- De budgeteenheden zijn consistent: maximaal **$0,23 per call**, **$0,69 voor drie calls**, binnen $1. Dit is geen factuurgarantie.
- De eerste RED is uitsluitend een collection error door de ontbrekende runner. **Gedragsmatige RED is daarmee niet bewezen.**
- Mutatie-v2 meldt 10/10 gedood, maar betreft tien handmatige mutaties. M2 verwijdert de teller volledig; hij verplaatst die niet naar “na succes”. M9 strandt op de SDK-initialisatiecontrole en bewijst daarmee geen uitgevoerde retry. M7 faalt op de verwachte stopcategorie; de payloadhash vormt daarnaast nog een blokkade. De matrix bewijst dus geen volledige guarddekking.
- Deadlinepaden zijn niet afzonderlijk dynamisch gereproduceerd. Echte provideracceptatie, actuele facturering en modelkwaliteit zijn niet getest. Onbekende usagevelden stoppen bewust na de betreffende call.

Geen broncorrecties, echte modelcalls, echte sleuteltoegang, productiegegevens, externe berichten, Actions, push/merge of activering uitgevoerd. WP5a valt buiten deze review. Alleen de ingelezen automatische handover is volgens de sessie-instructie gearchiveerd.