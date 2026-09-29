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
- Gecombineerde bron met actuele main e51610461: 936 gerichte tests geslaagd, 11 skilltests aanvankelijk overgeslagen; lint groen. De 1.379 gecontroleerde bron-, test- en configuratiebestanden zijn bytegelijk aan feature-head 7c9936dc9.
- De eerste canonieke unitgate vond één echte testfout: een cwd-assertie veronderstelde de repository als startmap. Claude corrigeerde alleen die test, met RED→GREEN, twee startmappen en mutatiebewijs; oorspronkelijke Codex-reviewer akkoord, 177 tests groen. Commit 2c07bbd95.
- De volledige unitrun op de gecombineerde bron rapporteerde letterlijk: **5 failed, 8775 passed, 75 skipped, 1 xfailed, 7 errors, 21 subtests passed**; make-exit 2. Elf foutnodes kwamen door mijn verkeerd ingestelde skillbronpad; één doordat de tijdelijke bronkopie geen Git-werkboom was. Op bytegelijke bron, in de echte featurewerkboom en met de juiste skillbron, zijn alle twaalf foutnodes gericht opnieuw uitgevoerd: **16 passed, exit 0** (inclusief vier reeds geslaagde recordtests). De JUnit-koppeling in bewijs/mergevoorbereiding-v1/foutsluiting.json toont nul onopgeloste foutnodes. Dit is bewijs uit een brede run plus gerichte hercontrole, geen claim dat één volledige run exit 0 gaf.
- De oudere performance_tracker-fouten traden in de canonieke runs niet op. Geen modelcalls of productiedata gebruikt.

## Open en bewust uitgesteld

- Onafhankelijke gelabelde goldset/hold-out, freeze en modelkwalificatie zijn nog niet afgerond. De ontwerpgevallen bewijzen geen hold-outprestatie; de eerdere driecallproef kwalificeerde het model niet.
- Verdere appintegratie/ketenverificatie en afzonderlijke productieactivering blijven open binnen DEF-835.
- DEF-626: opslag/snapshots/herladen is expliciet uitgesteld. De ongecommitte DEF-626/S1-wijzigingen in een andere werkboom maken geen deel uit van deze PR.
- Geen herstelroute (DEF-832), zelfstandige poort (DEF-831), legacy-opruiming (DEF-830), nieuwe dependency of productiedata.

## Mergevoorwaarden

GitHub Actions blijven uit (`enabled=false`). De tien vereiste Actions-statuschecks worden daardoor niet uitgevoerd. Branchbescherming blijft ongewijzigd. Chris gaf op 29 september expliciet akkoord voor de beheerdersuitzondering voor de ontbrekende Actions-checks. Reguliere merge met gebonden head; geen squash/rebase en geen branchverwijdering. Lokale testfouten zijn niet genegeerd: de foutsluiting en bronbinding staan in het bewijs.

Gerelateerd: DEF-835, DEF-771, DEF-624, DEF-831, DEF-832, DEF-626.

## Nieuwe mergevoorbereiding

Hoofdbron: `bewijs/mergevoorbereiding-v1/finale-bronbinding.json`; foutsluiting: `bewijs/mergevoorbereiding-v1/foutsluiting.json`. Claude CLI-sessie 585f02d8-1256-466a-a2ac-ae45d7cbc746; Codex CLI-review 01a0e8ca-2df9-7780-ba7a-b18c26caefe7. De volledige nieuwe opdrachten en beide verslagen zijn gecommit naast dit document. Historische logs en lokale herstelkopieën blijven behouden.
