# DEF-835 — WP3 afgerond: evaluator en resultaatcontract 2.3.0

28 september 2026. Het offline WP3-pakket is afgerond na implementatie, coördinatorverificatie en onafhankelijke review. De eerdere tussenoplevering en scopevoorstellen blijven historisch bewijs; het vijfbestanden-akkoord is verwerkt.

## Geleverd

- Synchrone, pure decision_rule_assessment-evaluator met WP1-controle van invoer, binding, citaten en actualiteit; zes statuspaden, geen score en adviserend fail.
- Registratie in enum/registry en root-SSOT.
- Publiek resultaatcontract 2.3.0, met assessment/signals uitsluitend voor INT-02 en bestaande INT-03; overige velden blijven gesloten.
- Nieuwe evaluator- en schematests plus herijkte bestaande contracttests. O1-uitkomsten en exacte NE-meldingen blijven behouden.
- WP3-R1 opgelost: een aanwezige ongeldige record_text geeft error; alleen een ontbrekende sleutel valt terug op raw_text.

De gebruiker accordeerde negen inhoudelijke bestanden en vervolgens vijf aanvullende bestaande testbestanden met "akkoord om het te fixen". Geen bestaande testgevallen of bestanden verwijderd. De vijf aanvullende bestanden wijzigden met +31/−11, uitsluitend testverwachtingen/commentaren en één passende functienaam.

## Rollen en commits

- Branch feature/DEF-835-int02-o2; werkboom .claude/worktrees/DEF-835-int02-o2.
- WP3-basis 2be81c577653f8efbab6fa2c3794598556d32d13.
- Eerste implementatie d3fc53eaed14e6a303605146b7e5f8b9ea3cef5e.
- Geaccepteerde productiecode na R1: 9769730d6e4a68dda9834c21c384f140e16c75e4.
- Geaccepteerde testherijking/eindstand: 4f28badee67c5f351235ac2b5cbb273f4bbc5721.
- Claude Code CLI claude-opus-5-5 implementeerde en corrigeerde in sessie c75abf0d-3c01-4c02-a672-536d75daa15a.
- Codex CLI gpt-6-astra/high reviewde onafhankelijk in aparte werkroot, sessie 01a0e4f2-9a94-70b2-9dcd-87202e24b697; dezelfde reviewer controleerde de correcties.
- Coördinator las diff/bewijs, draaide eigen tests en maakte lokale commits. Geen productie-/testcode door de coördinator geschreven.

## Test- en reviewbewijs

| Stap | Resultaat |
| --- | --- |
| Oorspronkelijke WP3 RED → GREEN | 92 failed / 19 passed → 111 passed, bytegelijke tests |
| Reviewcorrectie R1 RED → GREEN | 8 failed / 111 passed → 119 passed, bytegelijke tests |
| Herijking vijf bestaande testbestanden RED → GREEN | 8 failed / 113 passed → 121 passed |
| Uitvoerder: gerichte regressie over elf bestanden | 555 passed, exit 0 |
| Coördinator: dezelfde gerichte regressie | **555 passed in 3.04s**, exit 0 |
| Onafhankelijke reviewer: vijf herijkte bestanden | **121 passed in 1.66s**, exit 0 |
| Lint en normale lokale commitcontroles | Ruff, Black en overige gates geslaagd |

De reviewer bevestigde dat RED bij de oorspronkelijke bronversie hoort en GREEN/regressielogs bij de uiteindelijke bestanden. Geen skip/xfail/filter als oplossing. De twee oorspronkelijke INT-02-veldcases zijn behouden, met de geaccordeerde nieuwe verwachting; ongeldige typen, onbekende velden en die velden bij CON-01 worden expliciet geweigerd.

[Eindreview testherijking](wp3-codex-review-testherijking-v1.md), [R1-herreview](wp3-codex-herreview-r1-v1.md), [uitvoerdersverslag](wp3-claude-testherijking-verslag-v1.md), [coördinatorlog](bewijs/wp3-coordinator-testherijking-v1.log). Alle volledige prompts en logs staan in dit dossier. Prompt Forge-fallback blijft gelden.

## Open punten en bewijsgrenzen

Geen open WP3-bevindingen: R1 en de acht oude testfailures zijn gesloten. Dit is gerichte offline verificatie, geen volledige groene-suiteclaim. De eerder waargenomen afzonderlijke performance-tracker/importproblemen uit de brede unitrun zijn niet in deze testherijking opgelost of opnieuw onderzocht.

Het actieve INT-02-record blijft O1. Geen appmodelcalls, productiedata, Actions-wijziging, push, PR, merge of activering. Geen semantische modelkwaliteitsclaim.

Nog open voor volledige O2: WP4 onafhankelijke goldset en inhoudelijke modelevaluatie, WP5 appintegratie/gedeelde opslag/herladen en ketenlogging/backendmetadata, WP6 finale gates/PR/afzonderlijke activering. Voor de al toegestane echte technische modelproef staan profiel en kostenplafond nog open. De ModularValidationService-boekhouding blijft onderdeel van WP5.
