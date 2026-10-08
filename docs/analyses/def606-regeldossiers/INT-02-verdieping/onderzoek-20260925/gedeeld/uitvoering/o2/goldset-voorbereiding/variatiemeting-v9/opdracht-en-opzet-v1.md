# INT-02 O2 — variatiemeting v9: opdracht en opzet

8 oktober 2026. Opgesteld door Claude bij besluit 21 (`../../besluit-chris-promptcorrectie-en-v3-v1.md`). Uitslag van v9: `../goldset-freeze-v1/kwalificatieproef-v9-uitslag-v1.md`.

## Doel

Meten hoe sterk het model per run verschilt bij het labelen van bronnen, en wat dat doet met de uitkomst. Aanleiding: v8 en v9 hadden elk één onterechte pass, steeds bij een ander geval (G045, G050). Bij G050 en G030 labelde het model één bron anders dan in v8, terwijl de invoer gelijk was. Eén run per versie laat niet zien of dat toeval is of een vast patroon.

De meting beantwoordt per ontwikkelgeval:
- of de status over de runs gelijk blijft;
- welke bronfunctie per bron wisselt;
- hoeveel onterechte passes elke run heeft.

Er wordt niets gerepareerd. Contract, prompt, dienst en runner blijven ongewijzigd.

## Kader

- **Buiten het kwalificatieprotocol.** Geen kwalificatie, geen herhaling van een kwalificatiefase en geen DEF-815-claim. Er komt geen nieuw manifest of akkoord, en het grootboek van v9 wordt niet gelezen of aangevuld.
- **Consistentietoets 7A.** De ontwikkelgevallen waren zichtbaar bij het ontwerp van contract /4. Wat de meting laat zien, geldt voor deze gevallen en is geen onafhankelijk bewijs.
- **Hold-out dicht.** Het script leest uitsluitend `../goldset-freeze-v1/ontwikkeling-v1.json` als invoer. Het weigert vóór het openen elk bestand met `holdout`, `hold-out` of `hold_out` in de naam. Dat geldt ook voor de payload- en gevallenbestanden van de kwalificatie, want die bevatten hold-outinvoer.
- **Ijkpunten.** Manifest v9 (`30129863…d09d`, alleen de ontwikkeldelen) en de bewaarde v9-uitkomsten van fase 2 (`kwalificatieproef-v9/ontwikkeling-resultaat.json`) worden alleen gelezen.

## Opzet

**Script:** `variatiemeting_v9.py`, naar het patroon van `../variatiemeting-c107-v1/variatiemeting.py`. Tests: `tests/unit/validation/test_def835_int02_variatiemeting_v9.py`.

**Keten.** Per call precies dezelfde dienst als de runner: `Int02AssessmentService` via `runner._bouw_dienst` en de `Waarnemer` aan de httpx-grens. Profiel `def835-kwalificatieproef-opus5-v1`, `claude-opus-5`, de router uit `config.yaml`, `max_tokens` 6.000, deadline 120 s, `use_cache=False`, geen SDK-retry.

Eén bewuste afwijking van de kwalificatieconstructie zit in de rate limiter van AIServiceV2. Die volgt `max_inferentie` en staat in de kwalificatie op 43 per minuut én 43 per uur. Bij 48 calls zou call 44 op de uurgrens wachten tot de deadline van 120 s verloopt. Het script bouwt de dienst daarom met 48. Payload en `max_tokens` hangen daar niet van af.

**Controles vóór de eerste call.** Bij elke afwijking stopt het script met code 2, zonder enige call:
1. Manifest v9 heeft exact SHA-256 `30129863…d09d` en een consistente identiteit.
2. Promptversie `def835-int02-prompt/6`.
3. Schemahash `d3ad029e24b6b96242f4730686d3a4ebfebd9f46993607e41016761bc7fce715`. Getoetst in het contract én in de dienstmodule, als pin en als hash van het schema zelf.
4. De routeruitkomst `anthropic`/`claude-opus-5`, de prijzen gelijk aan manifest v9 (US$5 en US$25 per miljoen tokens) en alle 13 ketenbestanden byte-gelijk aan manifest v9.
5. Precies de 24 ontwikkelgevallen van manifest v9. Een ander geval-ID, zoals een hold-out-ID, wordt geweigerd.
6. Per geval zijn de invoer-, systeemprompt-, dataprompt- en payloadhash en de payloadgrootte gelijk aan manifest v9. Het verzoek is dus byte-gelijk aan dat van kwalificatieproef v9.

**Volgorde.** Eerst ronde 1 over alle 24 gevallen (`h1`), daarna ronde 2 (`h2`), steeds in de volgorde van manifest v9. Die volgorde was ook die van fase 2.

**Stopgedrag.** Er is geen automatische herhaling: één poging per call.
- **Stop** bij een afwijking van transport, provider, model of kosten (de stopredenen van de waarnemer), bij een uitzondering, bij een technische fout of timeout van de dienst en bij een gecachet antwoord.
- **Geen stop** bij een citaat- of uitvoerfout van het model (`invalid_citation`, `invalid_output`). Die wordt vastgelegd en de meting gaat door, want zo'n fout is zelf modelvariatie. Dit wijkt bewust af van de kwalificatie en van C107, die bij elke fout stopten.

**Sleutel.** Alleen live, en alleen uit de omgevingsvariabele `ANTHROPIC_API_KEY`. Het script leest geen `.env` en logt of bewaart de sleutel nooit. De sleutel wordt gelezen vóór de keten iets laadt. Live weigert als `DEFINITIE_DISABLE_DOTENV` niet aan staat; het script zet die variabele niet zelf.

## Kostenplafond

- **Hard plafond US$3,00**, met de prijzen uit manifest v9. Maximaal 48 calls (24 gevallen × 2 herhalingen); `--herhalingen` is 1 of 2.
- **Reservering per call** US$0,23: 16.000 invoertokens × US$5/M + 6.000 uitvoertokens × US$25/M.
- **Vóór elke call** moet de conservatieve besteding plus die volle reservering binnen US$3,00 blijven. Anders stopt de meting met stopreden `kostenplafond`, en die call gaat niet uit. De conservatieve besteding is de gemelde usage × prijzen; een call zonder betrouwbare boeking telt voor de volle reservering.
- **Raming:** ongeveer US$2,10. Dat is 2 × de gemeten v9-kosten per geval (US$0,744 voor 17 gevallen), plus het v9-gemiddelde van US$0,0438 voor de 7 gevallen die in v9 niet draaiden.
- **Slechtste geval:** zou elke call zijn volle reservering kosten, dan stopt het plafond de meting na 13 calls.

## Uitvoer (live)

In een nieuwe map. Het script weigert als die map al bestaat.
- `herkomst.json`: git-HEAD, script-, manifest-, ontwikkelset- en v9-resultaathash, profiel, promptversie, contractversie, schemahash, limieten, plafond, prijzen, raming en per geval de hashes.
- `calls.jsonl`: één regel per call, met fsync. Velden:
  - geval, herhaling, label (lokaal), status, modelverdict, modelstatus, onzekerheid;
  - per passage de kernvorm en de bronfuncties (bron, functie);
  - afleiding, omzetting, foutcategorie;
  - juist, onterechte en kritieke pass;
  - kosten, duur, usage, request-ID en payloadhash;
  - het ruwe antwoord van de API.
- `samenvatting.json` en `samenvatting.md`:
  - per geval de statussen over v9-fase 2 (indien gedraaid), `h1` en `h2`;
  - of het label stabiel is;
  - welke bronfunctie per bron wisselt;
  - in totaal: het aantal gevallen met een wisselende status, de onterechte en kritieke passes per run en het aantal gevallen met wisselende bronfuncties.

Definities in de samenvatting:
- **Stabiel** betekent dat alle waargenomen statussen gelijk zijn, met minstens twee waarnemingen.
- **Bronfunctie per bron** is de reeks functies over de passages, in passagevolgorde. Een ander aantal passages telt dus ook als wissel.
- Runs zonder oordeel, zoals een foutdocument, tellen niet mee voor de bronfuncties.

## Live starten (coördinator)

De coördinator start de live run, met de sleutel uit de `.env` van de hoofdcheckout. Hij toont die sleutel niet en zet hem niet in de werkboom. Vooraf moeten in de shell `ANTHROPIC_API_KEY` (uit de hoofdcheckout) en `DEFINITIE_DISABLE_DOTENV=1` gezet zijn. Vanuit de werkboom `DEF-835-int02-o2`:

```bash
/Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python \
  docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2/goldset-voorbereiding/variatiemeting-v9/variatiemeting_v9.py \
  --live --herhalingen 2 \
  --uitvoer docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2/goldset-voorbereiding/variatiemeting-v9/live-v1 \
  > docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2/goldset-voorbereiding/variatiemeting-v9/live-v1.log 2>&1
```

De droge run is hetzelfde commando zonder `--live` en zonder `--uitvoer`. Hij heeft geen sleutel nodig en schrijft alleen naar het log, bijvoorbeeld `dryrun-v1.log`.

Exitcodes:
- 0: volledig uitgevoerd;
- 2: geweigerd vóór de eerste call;
- 3: gestopt, met de stopreden in het log en in `samenvatting.json`.

## Wat de meting niet bewijst

- Geen kwalificatie en geen uitspraak over de hold-out.
- Twee extra runs geven een eerste beeld van de variatie, geen nauwkeurige kans. Bij 3 waarnemingen per geval is "stabiel" ook verenigbaar met een flinke foutkans.
- Kosten zijn gemelde usage × prijzen, geen providerfactuur.
