## Doel en afbakening

Technische deeloplevering voor DEF-835: versiegebonden, scoreloze INT-02 O2-beoordeling, expliciete optionele integratie en een begrensde proefrunner. DEF-835 wordt met deze PR niet gesloten. Het actieve INT-02-record blijft `judgment_review` (O1); deze PR activeert O2 niet en veroorzaakt geen automatische modelaanroepen.

## Wijzigingen

- WP1: getypeerd O2-beoordelingscontract, statusmapping, mechanische citaatcontrole en binding aan invoer, context, bronnen en normversie.
- WP2: T-prompt en beoordelingsdienst met expliciet modelprofiel, budget, deadline en foutbeleid.
- WP3: evaluator en resultaatcontract 2.3.0; bijbehorende contracttests herijkt.
- Technische proefrunner: expliciete transport- en responsemodelbinding, lokale kosten-/uitvoeringsregistratie; nauw begrensde bronhashuitzondering met tests.
- WP5a: optionele injectie in validatieketen, configuratiesnapshot en hercontrole vóór publicatie; typecorrecties.
- Q1: duurzame fasecontrole, budgetcontrole bij parallelle aanvragen, p95 en veilige afhandeling van onvolledige afronding.

## Bewijs en onafhankelijke rollen

Claude Code CLI implementeerde; afzonderlijke Codex CLI-sessies reviewden de concrete werkpakketten. Opdrachten, reviews en testlogs staan onder `docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2/`.

- WP5a/typecorrecties: 526 tests geslaagd; mypy zonder fouten in 411 bronbestanden; Ruff/Black groen. Brede eerdere selectie: 2966 geslaagd, vóór de typecorrecties.
- Q1: 176 tests geslaagd; F1/F2/F3 gesloten in de onafhankelijke herreviews. De finale F3-probe bewijst dat een onvolledige afronding vervolgtransport weigert.
- Bij mergevoorbereiding zijn de 10 WP5a- en 3 Q1-bestanden opnieuw vergeleken met de bewijsmanifesten: alle hashes gelijk.
- Verse canonieke offline unitgate en controle met nieuwste main: nog in uitvoering. Dit concept claimt geen groene eindgate.

## Open en bewust uitgesteld

- Onafhankelijke gelabelde goldset/hold-out, freeze en modelkwalificatie zijn nog niet afgerond. De ontwerpgevallen bewijzen geen hold-outprestatie; de eerdere driecallproef kwalificeerde het model niet.
- Verdere appintegratie/ketenverificatie en afzonderlijke productieactivering blijven open binnen DEF-835.
- DEF-626: opslag/snapshots/herladen is expliciet uitgesteld. De ongecommitte DEF-626/S1-wijzigingen in een andere werkboom maken geen deel uit van deze PR.
- Geen herstelroute (DEF-832), zelfstandige poort (DEF-831), legacy-opruiming (DEF-830), nieuwe dependency of productiedata.

## Mergevoorwaarden

GitHub Actions blijven uit (`enabled=false`). De tien vereiste Actions-statuschecks worden daardoor niet uitgevoerd. Branchbescherming blijft ongewijzigd. Eventuele reguliere beheerdersmerge volgt pas op een concreet mergebesluit; geen squash/rebase en geen branchverwijdering.

Gerelateerd: DEF-835, DEF-771, DEF-624, DEF-831, DEF-832, DEF-626.
