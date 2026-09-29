# Q1 — offline kwalificatieproefrunner (DEF-835)

Jij bent de Claude Code CLI-uitvoerder. Voer deze opdracht zelf uit; start geen agents, reviewers of extra CLI-sessies. De hoofdsessie coördineert; een afzonderlijke Codex CLI reviewt jouw diff. Alles in het Nederlands.

## Mandaat en werkplek

Chris antwoordde op 28 september 2026 letterlijk "akkoord! go" op de concrete opslag-/UI-pakketten en het kwalificatieprotocol met maximaal 43 appcalls/43 tokenmetingen en US$12. Deze opdracht is uitsluitend Q1 OFFLINE. Het geaccordeerde budget geeft jou geen opdracht tot livecalls. Geen productiedata, netwerkproef, migratie, activering, push of merge. Actions blijven uit.

Werkboom: /Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-835-int02-o2
Branch: feature/DEF-835-int02-o2
Basis: f9bb9e6973926a3cf768995f5d879f6edfd6322d
Dossier U: /Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-835-int02-o2/docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2

Lees CLAUDE.md, relevante .claude/rules en globale programmeerregels. Jouw rol is reeds toegewezen, geen herdelegatie. Gebruikersmandaat en expliciete technische dossierbestemming gaan vóór afwijkende lokale standaardpaden. Geen bestanden/testgevallen verwijderen. Maak vóór wijzigingen unieke herstelkopieën van de twee bestaande doelbestanden onder U/bewijs/q1-herstel-v1/, niet via git-stash/reset. Laat andermans documenten/wijzigingen intact.

## Leidende bronnen

- U/kwalificatieprotocol-v1.md, volledig; nu geaccordeerd via U/vervolg-akkoord-v1.md.
- U/modelproef-live-verslag-v1.md en technische-modelproef-voorstel-v1.md: historische proefgrenzen en veiligheidsketen.
- scripts/analysis/def835_int02_modelproef.py en tests/unit/validation/test_def835_int02_modelproef.py volledig lezen.
- Nieuwe prompt/T/normwijzigingen vallen BUITEN Q1. Geen inhoudelijke modelcorrectie improviseren. Goldset bestaat nog niet; maak GEEN echte goldset of hold-out.

## Exacte schrijfscope

1. scripts/analysis/def835_int02_modelproef.py
2. tests/unit/validation/test_def835_int02_modelproef.py
3. tests/fixtures/def835_int02_kwalificatie_runner.json (nieuw)
4. Eigen bewijs/verslag uitsluitend onder U/bewijs/q1-* en U/q1-uitvoering-v1.md.

Raming 250–450 regels is geen maximum; INT-02 mag >100 regels. Geen extra bronbestanden/dependencies/schema/APIwijzigingen. Meld concrete echte blokkades vóór uitbreiden; niet stoppen voor routinekeuzes binnen mandaat.

## Gevraagde uitbreiding

Behoud bestaande driecasusmodus en oude manifestvalidatie. Voeg expliciet nieuw kwalificatieprofiel toe dat een bevroren extern manifest met synthetische gevallen leest. Nieuwe akkoord-/freeze-identiteit moet strikt gebonden zijn aan input, labels, splitsing, protocol, prompt/norm, model/router en bronhashes. Oude verbruikte driecallautorisatie mag nooit als nieuwe kwalificatieautorisatie tellen.

Profile: bestaande Anthropic claude-opus-5 / standard/global zonder upgrade; maximaal 43 inferenties en43 tokenmetingen, 16.000 input/6.000 output,120s per call,6000s cumulatieve proeftijd, US$12 cumulatief over fasen. Gebruik bestaande router/provider-/budgetveiligheid; geen tweede directe transportstack. Geen retries/fallback/tools/cache/batch/fast. De nieuwe testfixture is alleen technisch, zichtbaar niet als goldset aan te merken.

Fasen:
1. regressie C105/C107/C112, alle3 juiste status en geldige citaten;
2. ontwikkeling24, minimum21/24 juiste status, nul false-pass op fail en nul technische/citaatfouten;
3. hold-out16, onveranderd bevroren profiel:4/4fail,7/8pass,3/4RR en14/16 totaal.
Overgangen mogen geen verborgen calls uitvoeren. Stop direct na technische/citaatfout of kritieke false-pass. Geen retry; calls tellen mee. Bij een onjuiste regressiestatus stoppen vóór volgende fase. Niet alle modelkwaliteit kan mechanisch worden vastgesteld: rapporteer dat inhoudelijke passagegronden door Chris worden beoordeeld; de runner mag daarvoor geen fictief akkoord invullen.

Volledig extern manifest vóór liveuitvoering geaccepteerd/bevroren; labels NOOIT in modelrequest, alleen in lokale evaluatie. Geen kernel/synthetische teksten in algemene logs; bewaarbundels in gekozen eigen nieuwe proefmap. Oude uitvoer niet overschrijven.

Voor fasen/herstart: budget-/calladministratie mag niet resetten door een nieuwe run met hetzelfde mandaat. Leg gebruikte calls/reserveringen vóór transport duurzaam vast; een afgebroken/onzekere call nooit gratis opnieuw starten. Houd bewijsvormen helder; als dit met bestaande structuur een groter technisch punt blijkt, implementeer minimaal veilig weigeren van mandaat-hergebruik in plaats van een onbewezen hervatfunctie. Geen claim van providerfactuurplafond.

Geen nieuwe echte APIcalls of tokenmetingen tijdens deze opdracht. Tests gebruiken uitsluitend geïnjecteerde fakes en bestaande offline-bootstrap.

## TDD en bewijs

1. Lees huidige code. Leg korte gekozen technische invulling en doelpaden vast in eigen verslag.
2. Schrijf betekenisvolle nieuwe tests EERST; bewaar rode uitvoer U/bewijs/q1-red-v1.log. Geen alleen implementatiespiegel.
3. Test ontbrekend akkoord/freeze; wijziging aan input/label/split/config; labellekkage; call/token/kosten/tijdlimiet; verkeerde fasevolgorde; foutstop; oud mandaat geweigerd; hergebruik/reservering; dry-run zonder netwerk; oude driecasusmodus.
4. Implementeer minimaal. Bewaar groen U/bewijs/q1-green-v1.log, Ruff/Black uitvoer en concrete diff.
5. Testcommando met projectvenv:
   /Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python -m pytest tests/unit/validation/test_def835_int02_modelproef.py -o addopts= -q -ra
   Borg bestaande offline-bootstrap vóór pytest-import; alle providersleutels neutraal in testsubprocess. Geen productiedb.
6. Ruff en Black uitsluitend gewijzigde Pythonbestanden. Geen brede autofix. Draai geen volledige suite; die is voor latere integratie.
7. Rapporteer aantallen rood/groen, gekozen interface, beperkingen en exacte gewijzigde bestanden. Geen gitcommit/stage: coördinator verifieert en laat eerst reviewen.

