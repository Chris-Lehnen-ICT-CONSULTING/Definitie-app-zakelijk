# Claude Code CLI — DEF-771, uitsluitend WP2

Jij bent de Claude Code CLI-uitvoerder. Voer deze opdracht zelf uit; start geen agents, reviewers of extra CLI-sessies. Coördinator verifieert; Codex CLI reviewt later de concrete volledige diff in een afzonderlijke sessie. Alle rapportage Nederlands. WP2 valt onder het ontvangen planakkoord; start pas wanneer de coördinator deze opdracht na WP1 aan je geeft.

## Werkbasis en eigenaarschap

App: /Users/chrislehnen/Projecten/Definitie-app, branch feature/DEF-771-int02-contract-o1, basis 0d26f0f4f5b2ebebe1c7d71fbff5e4ddb66b8c0d met de reeds geleverde WP1-wijzigingen. Je bent niet alleen in de repositories; behoud bestaande andere wijzigingen. Geen nieuwe inventarisatie: hergebruik de gelezen besluiten, synthese v5 en het casusregister.

Dossier: docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/. Bewijsmap: gedeeld/uitvoering/. Leidende bronnen: gedeeld/besluiten-chris-v1.md (B4/K3), gedeeld/gezamenlijke-synthese-v5.md §3 en §6. De canonieke WP1-skillbron staat in /Users/chrislehnen/Projecten/_claude-global-setup/.worktrees/DEF-771-int02-skills/skills/definitie-toetsregels/references/int02-beslisregel.md; in WP2 alleen lezen.

## Scope

1. src/services/prompts/modules/json_based_rules_module.py — uitsluitend de INT-02-generatie-instructie, nu op regel 453.
2. Nieuw tests/unit/services/prompts/test_def771_int02_promptnorm.py.

Raming 35–100 regels, twee inhoudelijke bestanden. Houd de test gericht; de exacte verwachte G kan uit de getrackte synthese §3 worden gelezen om een tweede lange tekstkopie te vermijden. Verwacht je meer dan 100 gewijzigde regels of een extra inhoudelijk bestand, leg dat vóór die uitbreiding aan de coördinator voor. Bewijslogs onder gedeeld/uitvoering/ zijn apart toegestaan. Geen afhankelijkheden, schema- of API/resultaatcontractwijzigingen. Maak vóór wijziging een unieke herstelkopie. Geen bestanden/testgevallen verwijderen, geen live toepassingsmodelcalls of productiedata. Maximaal drie pogingen per actie.

## RED → GREEN

Schrijf eerst tests op moduleniveau met echte JSONBasedRulesModule.execute, naar het patroon van tests/unit/services/prompts/test_def770_int01_promptnorm.py. Module.initialize accepteert include_examples. Test zowel true als false en controleer de werkelijk gerenderde INT-02-sectie:

- De volledige exacte G-paragraaf uit synthese v5 §3, na SC-C-02, staat letterlijk in de uitvoer; niet inkorten of samenvatten.
- De oude instructie “Vermijd voorwaardelijke formuleringen zoals 'indien', 'mits', 'tenzij', 'alleen als'” is afwezig.
- Het bestaande één-zin-uitvoercontract blijft expliciet: alleen definitiekern, zonder vraag, bronverantwoording, onzekerheidsmelding of toelichting in de generatie-uitvoer.
- Voorbeelden zijn werkelijk aan respectievelijk uit; de recorduitleg blijft aanwezig.

Bewaar de RED-uitvoer met commando en exitstatus vóór wijziging van de module. Vervang daarna uitsluitend de oude INT-02-instructie door de exacte G-tekst. Python-stringopdeling mag, de gerenderde tekst blijft bytegelijk. Geen andere promptinstructies wijzigen.

Draai GREEN voor de nieuwe tests en de bestaande INT-01-prompttests. Draai Ruff en Black-check op de twee WP2-bestanden. Bewaar per run nieuwe logs en de gerenderde INT-02-secties met en zonder voorbeelden. Geef bron-/diff-identiteit mee. Geen brede suite herhalen zonder concrete nieuwe aanleiding; de bekende test_no_negative_commands_in_guide-failure is al op de basis bewezen en staat buiten WP2.

## Conflict en bewijsgrenzen

Controleer en rapporteer het bestaande INT-01/INT-02-voorbeeldconflict (DEF-612): INT-01.json gebruikt “moet ondersteunen” als goed voorbeeld; INT-02 bewaart het ASTRA-foutvoorbeeld met die woorden. Wijzig INT-01 of het bronpaar niet. Casusfamilies uit §3: C04/C50/C54, C12/C51, C03/C15/C52, C107 en C33/C60. Deze tekstcontrole bewijst alleen rendering op moduleniveau, geen beter modelgedrag, juridische juistheid of volledige verzonden prompt.

Als de exacte tekst niet in het uitvoercontract past, stop en citeer bron/code; niet zelf inkorten. Geen WP3, S1-markerwijziging, evaluator/UI-wijziging, commit, push, PR, Linear-mutatie of actieve skillpublicatie. Lever diffstat, test-/lintbewijs, rendering en resterende beperkingen aan de coördinator.
