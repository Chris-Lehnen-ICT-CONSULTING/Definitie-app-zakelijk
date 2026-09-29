# DEF-771 — gerichte correctie R1 na onafhankelijke review

Je bent dezelfde Claude Code CLI-uitvoerder, sessie a4b588d6-e4a1-4fd6-8f80-0aac55013d90. Voer zelf uit; start geen agents, reviewers of extra CLI-sessies. De hoofdsessie coördineert; dezelfde afzonderlijke Codex-reviewer controleert daarna alleen deze correctie. Alles Nederlands, offline en zonder productiedata/modelaanroepen. Geen commits, push, PR of wijzigingen aan globale configuratie.

## Goedgekeurde verantwoordelijkheid en grens

Werk in /Users/chrislehnen/Projecten/Definitie-app, branch feature/DEF-771-int02-contract-o1, uitgangs-HEAD 5fb535ee45671007e5cb4557509560c793eec290. Je bent niet alleen in de codebase: raak ander werk niet aan en draai geen wijzigingen van anderen terug.

Je mag uitsluitend deze twee bestaande inhoudelijke bestanden wijzigen:

1. src/services/validation/evaluators/judgment_review.py — alleen de INT-02-passageafbakening en bijbehorende uitleg.
2. tests/unit/validation/test_def771_int02_o1.py — gerichte regressiegevallen en passende behoudasserties.

Raming 40–90 gewijzigde bron-/testregels, maximaal 100 totaal over deze twee bestanden. Als dit niet haalbaar is: stop vóór verdere wijzigingen en leg een concreet voorstel voor. Geen dependency, API-/resultaatcontract, normtekst, markerlijst, record, skill, UI of andere evaluator wijzigen. Niets verwijderen: alle bestaande testgevallen blijven aanwezig. Nieuwe bewijslogs en replayresultaten in gedeeld/uitvoering/ vallen onder de bestaande bewijsopdracht.

## Bevestigde bevinding

Lees het volledige wp5-codex-review-v2.md in de uitvoeringsmap. R1 is door de coördinator bevestigd aan de hand van de concrete code en reviewerreproductie. De overige acceptatiegebieden zijn door de reviewer akkoord bevonden binnen de gemelde grenzen.

De bestaande komma-/puntkomma-/dubbele-puntgrens rond een marker kapt relevante inhoud af:

- `Handeling die moet, na toestemming van de rechter, worden verricht.` citeert `Handeling die moet`.
- `Aanvraag die moet worden beoordeeld op: volledigheid, juistheid en tijdigheid.` citeert `Aanvraag die moet worden beoordeeld op`.
- Controleer ook `Persoon die, indien het inkomen lager is dan de grens, recht heeft op een toeslag.`: een relevant criterium mag niet los van zijn dragende zin worden behandeld.

De offsets zijn wel echte uitsneden en RR blijft correct, maar B2/WP3 vereist een volledig dragend zinsdeel. Bij onzekere grenzen is de volledige dragende zin of kern toegestaan. Implementeer de kleinste conservatieve correctie; geen nieuwe semantische parser of heuristische normbeoordeling. Herhaalde passages in verschillende zekere zinnen houden afzonderlijke posities. Markers in dezelfde volledige zin mogen één vraag delen.

## TDD en behoud

1. Schrijf eerst gerichte regressieasserties voor de drie bovenstaande invoeren. RR, geen score, volledige dragende passage en letterlijke offsets verplicht. Laat deze tests vóór productieaanpassing rood draaien en bewaar echte exitcode/output in wp5-r1-red.log.
2. Corrigeer alleen de passagegrenzen. Pas bestaande afkapverwachtingen aan waar die aantoonbaar met R1 conflicteren, maar behoud hun invoergevallen. Het bestaande komma-herhalingsgeval blijft getest; voeg daarnaast het tweezinnengeval `Handeling die moet volgen. Handeling die moet volgen.` toe voor afzonderlijke posities. Geen test verwijderen om groen te worden.
3. Draai de relevante DEF-771-contract-, prompt-, O1-, publieke NE-/UI-tests en de bestaande ESS-01/02/04-behoudselectie; gebruik het eerder vastgelegde 146-testcommando als uitgangspunt. DEF771_SKILLS_ROOT blijft wijzen naar /Users/chrislehnen/Projecten/_claude-global-setup/.worktrees/DEF-771-int02-skills/skills. Bewaar groen en exitcode in wp5-r1-green.log.
4. Ruff en Black op de twee geraakte bestanden, plus bestaande make lint; log wp5-r1-lint.log. Leg uiteindelijke aantallen gewijzigde regels vast.
5. Herhaal na definitieve formattering de bestaande C1-uitvoeringsreplay met vrije nieuwe outputnaam proef-c1-uitvoering-na-o1-run3.json en bijbehorende .log. Geen replaybron wijzigen, geen eerdere resultaten overschrijven. Statussen 36/36 en hashes moeten bij de definitieve evaluator horen.

Alle bewijsbestanden moeten vrije nieuwe namen hebben. Bij bestaande naam kies een volgende versie. Geen volledige pytest-suite starten: die coördineert de hoofdsessie na de definitieve correctie/review. Rapporteer de concrete diff, RED→GREEN-exitcodes, lint, C1-resultaat en eventuele resterende punten. Stop daarna.
