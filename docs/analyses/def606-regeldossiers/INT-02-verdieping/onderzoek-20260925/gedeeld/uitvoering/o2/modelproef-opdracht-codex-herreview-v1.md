# DEF-835 — gerichte herreview proefrunner

Jij bent dezelfde Codex CLI-reviewer (sessie 01a0e76c-9ee2-7ce1-be3c-e6a9d39b3417). Voer deze opdracht zelf uit; start geen agents, reviewers of extra CLI-sessies. Wijzig geen bronbestanden. Geen live appmodelcalls/sleutels/productiegegevens/Actions/push/merge/activering. Gebruik dezelfde aparte werkroot `/private/tmp/def835-wp2-review-20260927`.

Beoordeel alleen de correctiediff **dff713fd45a2c87b6d3b646e500e108b5cd61b03..979ca0585100d94b613829d924c6d8bba4f24f1b** en eventuele concrete doorwerking. Verifieer HEAD en schone werkboom. Geen nieuwe algemene review of mutatiematrix.

Dossier blijft `/Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-835-int02-o2/docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2/`.
Lees jouw eerste rapport, `modelproef-opdracht-claude-correctie-v1.md`, `modelproef-providercontrole-v1.md`, en het nieuwe `modelproef-claude-correctieverslag-v1.md` zodra aanwezig. De coördinator heeft jouw R1 en R2 bevestigd en voor fix teruggegeven. Daarnaast zijn de reeds bestaande officiële SDK-usagevelden inference_geo/output_tokens_details onderzocht; zie de bronnotitie. Geen algemene openstelling voor onbekende velden, geen optelling van detailtokens bij het inclusieve output_tokens-totaal.

Bewijs: `bewijs/modelproef-correctie-rood-v2.log` (34 failed, 41 passed op oude runner, gedragsmatige RED), `-groen-v1.log` (75 passed op nieuwe runner), `-lint-v1.log`, `-commit-v1.log`, `-dryrun-v1.log`, nieuw manifest/payloads-v2.json. De oorspronkelijke collectionRED blijft als beperking benoemd; de correctieronde heeft eigen echte gedragsmatige RED. Bestaande 478 overige regressietests zijn niet veranderd/herhaald; productiecode blijft ongewijzigd.

Herbeoordeel R1 model-/prijsbinding en R2 transportconfiguratie, testbewijs en de nieuwe ondersteunde usagevormen/deadlinetest. Eén gerichte offline testrun of repro wanneer nodig. Geef per punt gesloten/open met concreet bewijs; beoordeel of dit pakket klaar is voor de beperkte technische live proef zodra profiel/budgetakkoord binnen is. Geen modelkwalificatie- of productieclaim. De vragen aan Chris over het USD1-profiel en WP5a staan nog open; jij maakt geen akkoord.

Rapporteer nieuwe concrete bevindingen alleen indien aangetoond en relevant voor deze correcties. Verander geen tests of runner zelf. Eindantwoord vormt het volledige herreviewrapport, met commit, opdracht/commando, resultaat en beperkingen.
