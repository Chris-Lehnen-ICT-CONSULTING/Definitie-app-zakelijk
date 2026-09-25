**Technisch akkoord voor publicatie als onvoltooide kandidaat op de draft-PR, na de aangekondigde gates en bundelcontrole. Geen merge- of acceptatievrijgave: T20 blijft Important/open.**

- **R1-regressie gesloten.** `_voorzetselgroepen` is AST-gelijk aan de base; de onveilige uitbreiding is verwijderd. Eigen reproducties van `met het regent hard` en `tijdens de proef wacht` geven weer onzekerheid met passage en reden, zonder zinsstructuur-pass.
- **T20-dekkingsblok blijft open binnen DEF-770, zonder waiver.** De referentieverwachting blijft pass. De twee [strikte xfails](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/tests/unit/validation/test_def770_restherstel_zinsgrenzen.py:65) registreren dit zichtbaar; tests voor het huidige onzekere gedrag vervangen die verwachting niet.
- **T22 blijft gesloten binnen de eerder beoordeelde scope.** Labelherkenning, onderdeel `formulering` en melding zijn AST-gelijk aan v1. Contract `/7`, opslag en uitsluiting van oudere uitkomsten blijven gedekt.
- **LOW-verslagbevinding gesloten.** Rapport v2 corrigeert de ESS-01-weergave en trekt de noodzakelijkheid van een extra modelaanroep terecht in.

**Generatiebroncorrectie akkoord binnen deze scope; effect onbewezen.** De [vierpuntscontrole](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/src/services/prompts/modules/definition_task_module.py:299), begrensde contextinstructie, INT-01-kaart en drie skillteksten sluiten op elkaar aan. Bronafbakening blijft leidend; de voorrang betreft stijlvoorkeuren. Ik vond geen concrete nieuwe prioriteitsbreuk of proefinhoudlek. ESS-01-record, configuratie en providerroute zijn ongewijzigd. De echte PromptServiceV2-tests tonen doorwerking zonder context, met organisatorische context, juridische context en organisatie plus wet; zij bewijzen geen betekenisverbetering.

De twee vervolgrichtingen voor T20 zijn beslisopties, geen bewezen oplossingen:

- Conservatief reviewbeleid vraagt expliciet akkoord van Chris; historische labels blijven intact en nieuwe automatische verwachtingen moeten vooraf worden vastgelegd.
- Een POS-tagger of lexicon levert aanvullende aanwijzingen, geen garantie voor woordrollen of zinsgrenzen—zeker niet bij ongrammaticale tekst. De noodzaak of toereikendheid daarvan is nog niet aangetoond.

Gelezen bewijs: classifier **410 passed/2 xfail**, prompt **38 passed** na **13 RED-failures**, regressie **1313 passed/5 skipped/2 xfail**, integratie **27 passed/1 skipped**, gepinde Ruff/Black en lint groen. Zelf uitgevoerd: vijf classifierprobes, AST-vergelijkingen en patch-/hashcontroles. Geen brede suite herhaald.

Bases: app `e38ad95796fea35154482da8d8568e3663be4c36`; skills `a048806c67a441103a2d229d0247f3c8c26f326b`. Alle tien manifestbestanden en beide nieuwe tests zijn door de patches gedekt; hashes vóór/na gelijk.

- Appdiff: `3c90528bb60c4a22151773634bd92872858a9e464985a069dd4b1da651695c28`
- Skillsdiff: `cd4edacd6a30bdcc5d6fb59b664febd9152c2414f559aff26950419e00f42ee7`

Geen edits, betaalde calls of afgeschermde proefdata gelezen.