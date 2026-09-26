# Onafhankelijke Codex CLI-review — DEF-771

Jij bent de afzonderlijke, verse Codex CLI-reviewer. Claude Code CLI implementeerde; de hoofdsessie coördineert. Voer deze opdracht zelf uit; start geen agents, reviewers of extra CLI-sessies. Review zelf, wijzig geen bronbestanden, tests, prompts of configuratie. Nederlands. Pas requesting-code-review toe als reviewer; de dispatch-instructie is uitsluitend voor de coördinator, niet voor jou. Geen live modellen/productiedata, netwerkonderzoek, commits, issues, PR's of publicatie.

Werkroot van jouw sessie: /private/tmp/def771-codex-review-1ZSCEP. Je draait met workspace-write. Je mag in deze tijdelijke werkroot een eigen reviewnotitie of diagnostisch bewijs opslaan; de repositories hieronder zijn alleen leesbronnen. De coördinator bewaart je volledige opdracht en uitvoer in het dossier. Geen globale instellingen aanpassen; native agents en MCP-delegatie zijn voor deze sessie uitgeschakeld. Meld de beschikbare delegatiemogelijkheden als die toch zichtbaar zijn; roep ze niet aan.

## Concrete reviewbasis

Apprepo: /Users/chrislehnen/Projecten/Definitie-app
- branch feature/DEF-771-int02-contract-o1;
- base 0d26f0f4f5b2ebebe1c7d71fbff5e4ddb66b8c0d;
- head d5bf3a0e674febd09be94659b8b772e48a231b18;
- SHA-256 van `git diff base..head --binary`: e495f3eb7a61cbdb291a3fb29ab1a0c6634e9fffa07ffd27bac82d0f06b27fa0.

Skillrepo/werkboom: /Users/chrislehnen/Projecten/_claude-global-setup/.worktrees/DEF-771-int02-skills
- branch feature/DEF-771-int02-contract-o1;
- base 1e27a2da7668437423af3962cce48af5f1bc591b;
- head 750068253a7389e201daedc5b9aa0afd5c0be032;
- SHA-256 van `git diff base..head --binary`: 35e40ddbc4caffe65df3d45b7a06d5313c036cde04e29f43b84e5da12e19174a.

Beide werkbomen zijn voor inhoudelijke wijzigingen stilgezet tijdens je review. Er zijn andere ongetrackte werkstukken in de apprepo: die vallen buiten je scope en mogen niet worden aangeraakt. De hoofdcheckout van de skillrepo heeft werk van andere taken en is geen schrijfdoel. De normale skill-commit-hook heeft twee Cowork-ZIP's opnieuw gegenereerd en gestaged; beoordeel ook of die bij de gewijzigde skills horen.

## Bronnen en geldige besluiten

Dossier relatief aan apprepo: docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/.

Lees volledig gedeeld/besluiten-chris-v1.md (B1–B6). Lees de relevante exacte teksten en bewijsgrenzen in gedeeld/gezamenlijke-synthese-v5.md, vooral §2–§6 en §10; raadpleeg casusregister-v5 voor de genoemde ID's. Lees repo CLAUDE.md en toepasselijke .claude/rules. Geen heropening van het afgeronde normonderzoek.

Goedgekeurd uitvoeringsplan en delta's onder gedeeld/uitvoering/:
- plan-v1.md;
- akkoord-wp2-wp3-s1.md: WP2-omvang, WP3 en zes concrete markers;
- wp3-transportbesluit-v1.md plus akkoord-wp3-ne-transport.md: vijftien bestanden, gerichte publieke NE-doorgifte via bestaande rule_results/UI en additief resultaatcontract 2.2.0;
- wp-1-opdracht-claude-v2.md, wp-2-opdracht-claude.md, wp-3-opdracht-claude.md, wp-3-vervolgopdracht-ne-claude.md, wp-4-opdracht-claude.md voor concrete eigendom/acceptatie.

De tijdstempels/statuszinnen in oudere plannen zijn historische processtanden, geen tegenbewijs tegen latere expliciete akkoorden. Actuele voortgang: processtatus-uitvoering-v3.md. De omvang van WP3 is 865 regels binnen de vijftien afgesproken bestanden. WP4 is 22 regels in twee bestanden. Beide repositories/gekoppelde PR's zijn goedgekeurd. Geen merge of actieve skillpublicatie is uitgevoerd.

## Wat je moet beoordelen

1. De volledige concrete diff tegen B1–B6: brede norm, één versiegebonden N/G/T/H-contract, bronannotatie en ASTRA-paar letterlijk behouden, exacte §6-record/skillvervangingen, bytegelijke skillkopie en binding aan def771-int02/2. Geen betekenisverlies of ongeautoriseerde normwijziging.
2. G letterlijk synthese §3, met en zonder voorbeelden, binnen het één-zincontract. Geen extra output, vraag/bron/toelichting. Bekend DEF-612-voorbeeldconflict alleen gemeld; buurregel ongemoeid.
3. O1: exacte toetsvraag, per volledig dragend zinsdeel/zin de exacte neutrale vraag met controleerbare positie. Signalen leveren nooit automatisch pass/fail of score. Onzekere grenzen mogen de hele kern citeren. Beoordeel citeerbaarheid bij leestekens, herhaling en raw/cleaned-verschil, zonder fictieve broncitaten.
4. Zeven oude patronen blijven bytegelijk; exact zes goedgekeurde S1-markers. C02 moet treft; C83 treft; C13/C59/C105 blijven signaalloos. Beschrijvende markergevallen krijgen geen afkeur. Geen signaal heeft de exacte waarschuwing.
5. C06/C23/C56: NE met exacte melding, publieke doorgifte, schemaacceptatie, conversie en zichtbare bestaande UI-waarschuwing. Scorepolicy blijft excluded_from_score; geen nieuwe poort of herstel. Resultaatcontract 2.2.0 is additief. De serviceguard en directe evaluator moeten consistent blijven.
6. UI-productiecode alleen INT-02 toevoegen aan bestaande RR-tuple; NE gebruikt bestaande renderer. Geen issues-helper/expertreview-herlaadroute/DEF-626, DEF-830-legacycode, O2-modelaanroep of effectmeting gewijzigd.
7. Testgevallen behouden; WP4 hernoemt de misleidende fail-naam en geeft C24/C25 synthetische context voor RR. TDD-bewijs per pakket, normale branch-/hookregels, geen verwijderingen.
8. Beoordeel ook de nieuwe uitvoerbare dossierproeven/opbouwscripts op hun geclaimde bewijs; historische WP1-opbouwscript is geen actuele contractgenerator en mag /2 niet overschrijven. De actuele replay bewijst offline status/teksttransport, geen inhoudelijk normoordeel of kwaliteitswinst.

## Beschikbaar bewijs en grenzen

Onder gedeeld/uitvoering/:
- WP1: wp1-red-contracttest.log → wp1-na-formattering-verificatie.log; 18 tests en lint.
- WP2: wp2-red-promptnorm.log → wp2-green-promptnorm-v2.log, wp2-coordinator-verificatie.log; zes tests en letterlijke rendering.
- WP3: wp3-red.log; transport-RED in wp3-transport-red-v2.log (7 failed, 26 passed), na opmaak wp3-transport-green-v2.log (146 PASSED-regels, exit 0), wp3-transport-lint-v2.log (Ruff/Black/make lint 0).
- C1 actueel: proef-c1-uitvoering-na-o1-run2.json/.log, 36/36 en exit 0, hashes na definitieve formattering. De eerste run draaide vóór Black en blijft historisch bewijs.
- WP4: wp4-red.log, wp4-red-probestatus.log → wp4-green.log (437 PASSED-regels, exit 0), wp4-green-probestatus.log (RR), wp4-lint.log (0).
- Contracttests vereisen DEF771_SKILLS_ROOT naar de genoemde skillwerkboom/skills; anders zijn tien controles overgeslagen.

De coördinator draait nu de verplichte unitgate en daarna de volledige offline pytest-suite. Start zelf geen brede testronde. Bestaand testbewijs hergebruiken; alleen bij een concrete onbeantwoorde vraag gericht offline reproduceren, zonder wijzigingen aan bron/testbestanden. Python: apprepo/.venv/bin/python; netwerk/data altijd via bestaande tests/offline_bootstrap vóór appimports. Een tijdelijke diagnostische proef mag in jouw werkroot.

Bekende, op schone basis bewezen beperkingen: test_no_negative_commands_in_guide (12 < 10; wp1-basiscontrole-definition-task.log), en het algemene validatieschema accepteert bestaande violation-codes niet (wp3-schema-basiscontrole.log). De nieuwe schematests richten zich daarom op rule_results. Dat is geen volledig-schema-groenclaim. Het contractdocument miste reeds 2.1.0-changeloginformatie. Meld alleen nieuw of relevant resterend effect; geef geen oplossing buiten scope als voldongen opdracht.

## Oplevering

Rapporteer onderbouwde bevindingen met ernst, exact pad/regel, concreet scenario/bewijs en aanbevolen minimale correctie. Scheid echte regressies, acceptatieleemten en bestaande beperkingen. Geen hypothetische of uitsluitend stilistische bevindingen. Geef per acceptatiegebied je conclusie en sluit af met een oordeel of deze diff inhoudelijk gereed is, met expliciete bewijsgrenzen. Ook nul bevindingen expliciet melden. Geef base/head-identiteiten en je sessie-ID indien beschikbaar. Stop daarna; alleen de coördinator vraagt jou om een gerichte correctiereview in dezelfde sessie.
