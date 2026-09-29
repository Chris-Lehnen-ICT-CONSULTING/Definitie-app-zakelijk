# DEF-771 — integreer actuele main, behoud INT-02 en INT-03

Jij bent dezelfde Claude Code CLI-uitvoerder a4b588d6-e4a1-4fd6-8f80-0aac55013d90. Voer deze opdracht zelf uit; start geen agents, reviewers of extra CLI-sessies. Nederlands. Je bent niet alleen in de codebase: ander ongetrackt werk niet aanraken, geen wijzigingen terugdraaien. Lees de actuele /Users/chrislehnen/Projecten/_claude-global-setup/rules/codex-programmeerwerk.md. Geen echte modelaanroepen, productiedata, nieuwe dependencies of nieuwe schema-/API-besluiten. Geen commits, push, PR-merge of actieve uitrol. De coördinator commit en verifieert later; dezelfde Codex-reviewer controleert de concrete integratiediff.

Chris vroeg of we al kunnen/moeten mergen. De coördinator bereidt beide bestaande PR’s voor; echte PR-merge is nog niet geautoriseerd. De oorspronkelijke implementatie en bronnen zijn goedgekeurd; de100-regelsgrens is expliciet verruimd voor noodzakelijk INT-02-werk. Dit is integratie met inmiddels geaccordeerd main-werk, geen herontwerp of nieuwe norm. Oude bewijsbevindingen in ketenproefv3 zijn gesloten (vervolg-keten-codex-slotreview-v1.md); niet opnieuw wijzigen/onderzoeken.

## Bevroren identiteiten

Apprepo /Users/chrislehnen/Projecten/Definitie-app, feature/DEF-771-int02-contract-o1:
- eigen HEAD b56e2878268f744f224e8d1326c9198378b025bc;
- opgehaalde origin/main 076c916671e4e7e9f2843d22669df38eeb79e170 (incl. INT-03 PR484).
Skillwerkboom /Users/chrislehnen/Projecten/_claude-global-setup/.worktrees/DEF-771-int02-skills, dezelfde branchnaam:
- eigen HEAD750068253a7389e201daedc5b9aa0afd5c0be032;
- opgehaalde origin/main770de55ece429fec826c9d53fd873a109ed8e670.
Controleer HEAD/ref en schone getrackte werkboom vóór iedere merge. Stop bij afwijkingen of wijzigingen van derden. De vele ongetrackte dossierstukken zijn geen conflict en blijven staan.

## Opdracht en eigendom

Voer in beide FEATURE-werkbomen een gewone merge van exact bovenstaande main-commit uit met --no-commit --no-ff. Nooit checkout main, rebase, reset/force of bestanden verwijderen. Het is toegestaan de merge in voorbereiding te laten staan voor coördinatorcontrole/commit. Geen eigen mergecommit maken.

App: er is volgens merge-tree precies één handmatig conflict in src/services/prompts/modules/json_based_rules_module.py. Behoud de exacte nieuwe INT-02-G uit onze branch én de exacte nieuwe INT-03-G uit main. De oude INT-02-verbodszin uit main mag niet terugkomen, de oude INT-03-'dezelfde zin'-zin uit onze branch evenmin. Neem de overige mainwijzigingen normaal mee, inclusief ESS-01. Corrigeer alleen het conflict en indien nodig de bijbehorende commentaarbinding naar het bestaande contract def771-int02/2. Geen norm inkorten of aanpassen.

Skills: handmatige conflicten in:
- skills/definitie-toetsregels/SKILL.md
- skills/definitie-toetsregels/reference.md
- skills/definitie-nederlandse-definities/SKILL.md
- skills/definitie-nederlandse-definities/reference.md
- cowork-exports/definitie-toetsregels.zip
- cowork-exports/definitie-nederlandse-definities.zip
Integreer INT-02-delta in de nieuwste mainteksten. Behoud INT-03 en alle andere mainteksten/versiehistorie. Canonieke INT-02-contracten en kopie blijven bytegelijk def771-int02/2, SHA256bc16c128c43e247b25db996d25059af48fe56dccea5cdc4012ceb401746b043c. De twee binaire conflicten oplossen door de normale bestaande bundelgenerator te gebruiken voor uitsluitend die twee betrokken bundels; geen willekeurige keuze ‘ours/theirs’ voor inhoud. Inspecteer de generatoropties; start geen brede install/publicatieroute. Niets uit actieve ~/.agents- of ~/.claude-skills overschrijven.

Nieuwe maintekst is geen opdracht om extra software te bouwen. Als automatisch samengevoegde code de eerder goedgekeurde INT-02-statusmapping/NE, passages, signalen, G of contractbinding werkelijk breekt: leg exacte plek/scenario en minimale oplossing vast vóór een extra productiewijziging. Geen algemene reparaties aan andere dossiers. Behoud eventuele nieuwere resultaatcontractversie uit main; introduceer zelf geen versie/schemawijziging.

## Verificatie vóór opleveren aan coördinator

1. Geen conflictmarkers of unmerged indexentries meer. Exact INT-02-G en main INT-03-G beide bewijzen met gerichte rendering-/contracttests. DEF771_SKILLS_ROOT naar de skillwerkboom/skills.
2. Draai de bestaande relevante INT-02-contract/O1/NE/UI/prompttests en de op main toegevoegde INT-03-prompt/validatie/UI-contracttests die deze integratie raken, volledig offline met bestaande bootstrap. Lees concrete bestandsnamen met rg. Neem bestaande ESS-01-promptbehoudtests mee indien relevant; geen algemene nieuwe tests ontwerpen.
3. Herhaal ketenproefv3 (script ongewijzigd) op deze geïntegreerde code met nieuwe outputnamen vervolg-integratie-keten-v1.json/.log. Bestaande JSON/logs niet overschrijven. Leg bronhashes vast; dit bewijs heeft de beide main-commitidentiteiten plus werkboomdiff als bron, nog geen mergecommit.
4. Ruff/Black voor geraakte Pythonbestanden en relevante normale lintchecks. Twee contractkopieën en twee ZIP-inhouden bytegelijk bewijzen. Geen volledige pytest-suite starten; die coördineert de hoofdsessie vanwege gewijzigde gedeelde code.
5. Leg volledige opdrachten/output/exitcodes vast in nieuwe vervolg-integratie-*. Rapporteer precies wat handmatig is opgelost, gewijzigde bestanden en staged diff ten opzichte van main versus onze vorige HEAD. Stage alleen echte conflictoplossingen binnen de genoemde bestanden; bestaand merge-index bevat inkomend mainwerk. Geen ander ongetrackt bestand stagen. Stop daarna met de voorbereide merges.

Deze integratie raakt de al goedgekeurde INT-02-app-/skillbestanden en hun normale bundels. De bestaande UI-/opslag-/exportgrenzen uit ketenrapportv3 blijven expliciet; geen volledige ketenoplevering claimen. Maximaal drie pogingen per concrete actie. Meld echte blokkade, geen extra review/agent starten.
