# DEF-835 — eerste echte technische modelproef

28 september 2026. Geaccordeerd via Chris' chatantwoord “akkoord”, vastgelegd in besluit-proef-en-wp5a-v1.md. Gereviewde runner 979ca0585100d94b613829d924c6d8bba4f24f1b, manifest v2, akkoordbestand bewijs/modelproef-akkoord-v1.json. Geen productiegegevens.

## Uitvoering

Eerste processtart gaf exit 2, `sleutel_ontbreekt`, vóór enige verzending. De aparte werkboom heeft geen .env en het proces had geen ANTHROPIC_API_KEY. Alleen de bestaande Anthropic-sleutel uit de lokale project-.env is vervolgens in de child-environment meegegeven; niet in argumenten, uitvoer of bewijs opgenomen. Geen configuratiebestand gewijzigd. De tweede start gebruikte dezelfde runner, hetzelfde akkoord en dezelfde manifestidentiteit.

Echte run: 11:20:49–11:21:05 UTC, **16,525 seconden**, drie tokenmetingen en **drie inferencecalls**. Provider/model in alle antwoorden: anthropic / claude-opus-5, standaardtier, global, end_turn. Geen retries, fallback of cache. Gemeld: 9.823 invoertokens en 1.161 uitvoertokens. **Berekende kosten US$0,07814**, geen onzekere kostenregistraties; dit is een berekening op gemelde usage, geen providerfactuur.

Runner-exit **3**, stopreden **invalid_citation** op het derde geval. Het geaccordeerde maximum van drie inferencecalls is daarmee gebruikt; geen extra call/herstelronde uitgevoerd.

| Geval | Verwachting ontwikkelfixture | Geobserveerd | Betekenis van het bewijs |
| --- | --- | --- | --- |
| C105 | fail | fail, geldig document/citaten | Technische keten en uitkomst sluiten op dit geval aan |
| C107 | review_required / insufficient_information | fail, geldig document/citaten; model meldt geen onzekerheid | Inhoudelijke afwijking: model kiest discretionaire beslisregel terwijl bedoeling ontbreekt en fixture menselijke beoordeling verwacht |
| C112 | pass | Model schreef pass, maar keten geeft error / invalid_citation | Citaatcontrole houdt ongeldig bewijs tegen; geen geaccepteerd pass-oordeel |

De bestaande fixturelabels zijn niet aangepast. Deze drie gevallen zijn bekend ontwikkelmateriaal, geen onafhankelijke goldset of hold-out. Geen algemene kwaliteitspercentages of modelkwalificatie afleiden uit deze proef.

## Citaatdiagnose C112

De modeltekst zelf komt voor in de bron, maar de posities kloppen niet:

- Kerncitaat: start 0, end 70, terwijl het volledige opgegeven citaat 73 tekens omvat.
- Bedoelingscitaat: start 0, end 46, terwijl het opgegeven citaat 47 tekens omvat.

De exacte slices wijken af. De bestaande controle weigert terecht het document. Er is niets automatisch hersteld of ingekort en geen herstellende modelcall gedaan. De vergelijking staat in bewijs/modelproef-live-citaatcontrole-v1.json.

## Vervolg en grenzen

Technische providerbereikbaarheid, request/responsebinding, usage en citaatafwijzing zijn nu echt waargenomen. Drie geldige inhoudelijke uitkomsten zijn niet behaald. C107 en C112 blijven expliciete bevindingen voor model-/promptkwalificatie; het exacte norm/T-contract is niet gewijzigd. Verdere experimenten vragen een nieuw begrensd proefpakket; de huidige drie calls zijn gebruikt.

WP5a is afzonderlijk geaccordeerd en kan offline doorgaan met fake beoordeling en O1 actief. De echte proef is geen toestemming voor productieactivering en geen bewijs van inhoudelijke modelgeschiktheid. Gedeelde opslag en onafhankelijke goldset blijven open. Actions blijven uit; niets gepusht, gemergd of geactiveerd.

Bewijs: modelproef-live-cli-v1.log (geen verzending), modelproef-live-cli-v2.log, modelproef-live-resultaat-v2.json, modelproef-live-payloads-v2.json en modelproef-live-citaatcontrole-v1.json, alle onder bewijs/. Volledige synthetische modelantwoorden staan alleen in het aangewezen bewijsbestand.
