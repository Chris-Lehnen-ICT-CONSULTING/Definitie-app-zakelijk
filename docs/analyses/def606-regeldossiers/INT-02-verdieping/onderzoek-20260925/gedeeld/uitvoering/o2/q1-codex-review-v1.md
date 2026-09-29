**Q1 voldoet nog niet aan het protocol: drie bevestigde, blokkerende bevindingen.** Voor alle drie is de voorgestelde dispositie **fix nu**, door dezelfde Claude-uitvoerder.

1. **Hoog — gelijktijdige vervolgfasen omzeilen het cumulatieve callplafond.**  
   Locatie: [def835_int02_modelproef.py:1853](/Users/chrislehnen/.codex/worktrees/def835-q1-review/Definitie-app/scripts/analysis/def835_int02_modelproef.py:1853), regels 1853–1864; grootboekschrijven op regel 498.

   **Reproductie:** voer de regressiefase succesvol uit. Start vervolgens twee ontwikkelruns op hetzelfde manifest en synchroniseer beide direct na hun tweede `Grootboek.lees`, vóór `fase_start`. Beide accepteren dezelfde beginstand en versturen ieder 24 inferenties en 24 tokenmetingen. De offline probe registreerde **51 inferenties en 51 tokenmetingen cumulatief**. Eén run rapporteerde succes; de andere kreeg pas bij resultaatopslag `FileExistsError`. Achteraf werd het gezamenlijke grootboek als ongeldig geweigerd.

   **Geschonden:** maximaal 43 calls/43 tokenmetingen; dubbelrunveiligheid en reservering vóór transport. Een achteraf geconstateerd corrupt grootboek voorkomt de extra calls niet.

   **Kleinste correctie:** verkrijg een exclusief processlot per proefmap vóór het lezen/controleren van de actuele stand; houd dit vast tot en met duurzame faseafronding. Weiger een tweede uitvoerder vóór transport.

2. **Hoog — hold-out-p95 boven 90 seconden wordt toch goedgekeurd.**  
   Locatie: [def835_int02_modelproef.py:1882](/Users/chrislehnen/.codex/worktrees/def835-q1-review/Definitie-app/scripts/analysis/def835_int02_modelproef.py:1882); afzonderlijke latencyrapportage op regel 1926.

   **Reproductie:** laat regressie en ontwikkeling slagen. Geef alle 16 hold-outs correcte antwoorden en simuleer via de klok 91 seconden inferentieduur per antwoord. Uitkomst: `p95_ms=91000`, `mechanisch_geslaagd=true`, `redenen=[]` en `holdout=true` in het grootboek. De CLI bepaalt haar succescode uitsluitend uit deze geslaagdstatus.

   **Geschonden:** de vooraf vastgestelde operationele toelatingsgrens **hold-out-p95 ≤90 seconden**. `_beoordeel_fase` ontvangt geen latencygegevens.

   **Kleinste correctie:** neem de p95-grens op in de bevroren criteria en fase-evaluatie vóór grootboekafronding. Overschrijding of ontbrekende vereiste metingen moet toelating blokkeren. Dit bewijs betreft grenshandhaving, geen gemeten providerperformance.

3. **Hoog — opslagfalen verliest proefbewijs maar laat de volgende fase doorgaan.**  
   Locatie: [def835_int02_modelproef.py:1885](/Users/chrislehnen/.codex/worktrees/def835-q1-review/Definitie-app/scripts/analysis/def835_int02_modelproef.py:1885); artefactopslag volgt pas op regels 1930–1941.

   **Reproductie:** injecteer `OSError` bij het schrijven van `regressie-resultaat.json`, nadat drie correcte regressieantwoorden zijn ontvangen. De proefmap bevat daarna uitsluitend `grootboek.jsonl`; daarin staat `regressie=true`, zonder open fase. Na herstel van de schrijffunctie accepteert de runner ontwikkeling en verstuurt **24 nieuwe calls**, ondanks ontbrekende regressieresultaten en request-/responsebundel.

   **Geschonden:** volledige synthetische proefartefacten behouden en bij fouten gesloten blijven. De succesvolle faseovergang wordt duurzaam vastgelegd vóór het bewijs.

   **Kleinste correctie:** bewaar het beschikbare request-/response- en resultaatbewijs duurzaam vóór een succesvolle `fase_einde`. Een publicatiefout moet de fase geblokkeerd laten en vervolgtransport verhinderen.

Beoordeeld tegen basis `f9bb9e6973926a3cf768995f5d879f6edfd6322d`; de drie opgegeven bestandshashes zijn vóór en na de review gelijk. Bestaande testcases zijn behouden. Het aangeleverde bewijs van **156 geslaagde tests en schone Ruff/Black-controles** is hergebruikt. De drie aanvullende probes draaiden met de projectvenv, vooraf geïnstalleerde offline-bootstrap en uitsluitend neptransporten. [Probe](/private/tmp/def835-q1-review-qjykDS/probe.py) en [uitvoer](/private/tmp/def835-q1-review-qjykDS/probe.log) staan tijdelijk buiten de repository.

De scheiding tussen mechanische statusvergelijking en inhoudelijke beoordeling is expliciet aanwezig: Chris’ oordeel blijft `open`. Na correctie blijven de geaccepteerde echte goldset, inhoudelijke grondenbeoordeling en modelkwalificatie afzonderlijk te bewijzen. De echte conceptgoldset is niet gelezen; deze review geeft geen volledige-appsuiteclaim of activeringsakkoord.