# DEF-835 — uitvoeringsplan O2 v1

26 september 2026 · status: ter akkoord; alleen inventarisatie uitgevoerd.

## Doel en startpunt

O2 beoordeelt de functie van passages in een definitie: begripscriterium of deterministische afleiding tegenover actorvoorschrift, procedure of discretionaire beslisregel. Het oordeel is scoreloos, met controleerbare citaten, versiegebonden gronden en expliciete onzekerheid. De norm uit besluiten B1–B6 blijft leidend.

Chris gaf opdracht “Start o2”. DEF-835 staat op In Progress. Branch: `feature/DEF-835-int02-o2`, aangemaakt vanaf opgehaalde `origin/main` `84bdc8c1b060ab50a1bd1428aed778bb2ed6007f`. Werkboom: `.claude/worktrees/DEF-835-int02-o2`. De bestaande O1-werkboom is behouden.

Dit plan vraagt akkoord op het eerste offline bouwpakket en diens nieuwe interne contract. De vervolgpakketten vormen de route naar volledige oplevering; hun afzonderlijke contract- en activeringsbesluiten zijn nog open. De verruiming van 100 regels voor INT-02 blijft gelden. Geen nieuwe dependencies voorzien.

## Bronnen en actuele vindplaatsen

Regels hieronder zijn gecontroleerd op de genoemde basiscommit, niet overgenomen van onderzoeks-main 26f2374d.

| Bron | Aangetroffen tekst / betekenis voor O2 |
| --- | --- |
| `src/toetsregels/regels/INT-02.json`, runtime_contract | `"evaluator": "judgment_review"`, `"score_policy": "excluded_from_score"`; vereist `definition_text` en `context_lists`. Normversie `def771-int02/2`. |
| `src/services/validation/evaluators/judgment_review.py:76` | “exacte meldingen uit synthese v5 §4”; O1 bevat passagehulp, waarschuwing zonder signaal en NE-melding. |
| `src/services/validation/modular_validation_service.py:1466` | “INT-02 geeft de exacte NE-melding (kern en/of context).” Dit pad moet behouden blijven. |
| `src/services/validation/int03_assessment_service.py:301` e.v. | Bestaand patroon: `TASK_TYPE = "validation"`, AIService, norm uit record, gestructureerde uitvoer en gevalideerde cache. Maximaal 5000 uitvoertokens is een INT-03-besluit, geen O2-budget. |
| `src/services/orchestrators/validation_orchestrator_v2.py:552` | “Een door de aanroeper meegegeven int03_assessment wordt weggegooid”. O2 mag evenmin een onbewezen meegegeven oordeel vertrouwen. |
| `src/services/validation/evaluators/pronoun_reference_assessment.py:86` | Beoordeelt exacte `record_text`; signalen zijn zoekhulp en de AI-route wordt door een async wrapper voorbereid. |
| `src/toetsregels/runtime_contract.py:95` | Gesloten evaluator-enum; toevoegen van een evaluator is een contractuitbreiding. |
| `docs/architectuur/contracts/schemas/validation_result.schema.json:349` | `assessment` en `signals` alleen bij INT-03; `unevaluatedProperties: false`. O2 mag geen extra velden stil invoegen. |
| `docs/architectuur/contracts/validation_result_contract.md:36` | Versie 2.2.0 beschrijft O1-NE en INT-03. Voor publieke O2-uitvoer wordt een additieve versie 2.3.0 voorgesteld, na akkoord. |
| `src/services/ai/model_router.py:121` | “Unknown tasks default to 'critical'”. Geen nieuwe onbekende taaknaam gebruiken als impliciete modelkwalificatie. |
| `src/database/definitie_crud.py:1416` | INT-03 bewaart beoordelingen onder lock in dezelfde UPDATE met historie. Dit is een bestaand specifiek patroon, geen bewijs dat de volledige DEF-626-snapshotketen geleverd is. |
| Linear DEF-626, opgehaald 26-09 | Backlog; eist één gezaghebbend append-only mechanisme en atomaire opslag. Geen nieuwe parallelle INT-02-historieroute bouwen onder dit plan. |
| Linear DEF-815, opgehaald 26-09 | Modelkwalificatie, versiebeleid en prerequisites (o.a. DEF-639) zijn open. Offline technische voorbereiding kan plaatsvinden; modelkeuze en activering niet als bewezen presenteren. |

Normbronnen in het onderzoeksdossier: `gedeeld/besluiten-chris-v1.md`, `gedeeld/gezamenlijke-synthese-v5.md` §2–4, §8–10 en `gedeeld/gezamenlijk-casusregister-v5.md`. Verder ADR-001, project-CLAUDE, patterns.md en de globale programmeerregels. Linear DEF-835 en zijn gekoppelde specificatie zijn opnieuw gelezen.

### Skillbron en nulmeting

De skillrepo-hoofdcheckout staat op een oudere featurebranch en bevat het INT-02-contract nog niet. Gecontroleerde bron is de bestaande werkboom:
`/Users/chrislehnen/Projecten/_claude-global-setup/.worktrees/DEF-771-int02-skills/skills/`.
Het canonieke `definitie-toetsregels/references/int02-beslisregel.md` en de actieve kopie onder `~/.agents/skills` hebben dezelfde SHA-256:
`bc16c128c43e247b25db996d25059af48fe56dccea5cdc4012ceb401746b043c`.
De actieve kopie is geen nieuwe bron van waarheid. O2 verandert in WP1 geen skill.

Nulmeting van O1-contract, passagehulp, UI, generatieprompt, INT-03-assessmentservice en resultaat-schema: **120 passed in 1.45s**, exit 0. Bewijs: `bewijs/baseline-v2.log`. De eerste run gebruikte ten onrechte de oude skillrepo-hoofdcheckout en gaf vier failures en zeven setup-errors voor ontbrekende/verouderde skillbestanden; die uitvoer blijft bewaard in `baseline-v1.log`. Er is geen code aangepast om deze fouten te laten verdwijnen.

Dit is een gerichte basiscontrole, geen volledige suite en geen O2-kwaliteitsbewijs. De bestaande offline-bootstrap blokkeert netwerk, neutraliseert providerkeys en isoleert SQLite.

## Ontwerpvoorstel: intern beoordelingscontract

Voorgestelde versie: `def835-int02-assessment/1`, apart van normversie `def771-int02/2`. Het model bepaalt semantische functies; code controleert structuur, citaatposities, binding, statusconsistentie en technische fouten.

1. **Invoer:** begrip, exacte kern, bevestigde bedoeling (ook expliciet onbekend), de drie bestaande contextlijsten, expliciet aangeleverde bronpassages met ID en tekst. Een bron is ondersteunende betekenisgrond; de overtredende passage moet in de kern staan. Geen webophaling of verborgen bronaanvulling.
2. **Binding:** contractversie, normversie en hash, promptversie, routeringsconfiguratie-hash, gevraagde provider/model-ID, gerapporteerde modelversie (of expliciet onbekend), hashes van kern/betekenis/context/bronnen. Exacte beoordeelde input als onveranderlijke snapshot bij het beoordelingsdocument; geen ruwe tekst in logs.
3. **Modeluitvoer:** gesloten velden `verdict`, `passages`, `reason`, `question`, `uncertainty`, `scope_reason`, `coverage`. Elke passage bevat exact citaat met start/eind (nulgebaseerd, einde exclusief), functie en grond. Grond verwijst naar een invoerveld/bron-ID en waar geciteerd naar exacte tekstposities. Voor functies: criterium, afleiding, actorvoorschrift/procedure, discretionaire beslisregel of onduidelijk.
4. **Uitvoeringsmetadata:** actor (AI of mens), uitvoeringsstatus, tijdstip, foutcategorie, transportpogingen, tokengebruik, duur en bekende kosten. Afwezige providergegevens expliciet onbekend; nooit verzonnen.
5. **Statusmapping:** pass alleen na beoordeelde passages zonder gebrek/beslissende onzekerheid; fail bij minstens één onderbouwd gebrek, ook met andere open vragen; inhoudelijk onvoldoende informatie geeft review_required met precies één gerichte vraag. Nog niet beoordeeld en historisch zijn afzonderlijke uitvoeringsredenen. Kern/context ontbreekt → not_evaluated; technische fout/ongeldig citaat → error; not_applicable alleen met expliciete reikwijdtegrond. Geen score.
6. **Passagecontrole:** lege of niet-herleidbare bewijsvoering kan geen pass/fail dragen. Een `coverage`-verklaring is een modelclaim; code kan semantische volledigheid niet bewijzen. Juist die beperking wordt in de onafhankelijke goldset gemeten.
7. **Herbinding:** wijziging in één betekenisgrond of norm/prompt/modelconfiguratie maakt het oude document niet-toepasbaar; het document zelf blijft ongewijzigd. Geen hash-only claim van bewaarde exacte tekst.

De appmeldingen worden letterlijk als sjabloon uit synthese §4 overgenomen. De O2-prompt bevat de T-tekst letterlijk, met het JSON-uitvoercontract aanvullend. G en N veranderen niet. Geen automatisch herstel of INT-02-vaststel/exportpoort.

## Werkpakketten en aftekenpunten

Elk codepakket: volledige opdracht in deze dossiermap → echte Claude Code CLI schrijft tests en toont rood → implementeert → coördinator draait tests/leest diff → verse Codex CLI reviewt concrete diff → bevindingen terug naar dezelfde uitvoerder → gerichte herverificatie. Geen werkpakket tegelijk met een ander codepakket.

### WP1 — zuiver domeincontract, offline regressiegevallen (eerst ter akkoord)

**Doel:** bovenstaande structuur, binding, citaten en statusmapping mechanisch bewaken zonder een model of actieve app-route.

Nieuwe bestanden (exact vijf, circa 650–950 regels inclusief tests):
- `src/domain/int02/__init__.py`
- `src/domain/int02/contract.py`
- `tests/unit/domain/test_def835_int02_contract.py`
- `tests/fixtures/def835_int02_ontwerpgevallen.json`
- `docs/architectuur/contracts/int02_assessment_contract_v1.md`

Geen bestaande productiecode wijzigt in WP1. Geen database- of publiek resultaat-schema wijzigt in WP1. Het nieuwe interne contract zelf vraagt expliciet akkoord.

**Eerst rood:** geldige en ongeldige citaten/offsets, alle statuspaden, één vraag bij onzekerheid, fail met daarnaast onzekerheid, onbewezen pass, onterechte NA voor een afleiding, elk bindingsveld apart gewijzigd, exacte input behouden, score verboden. C06/C23/C56 (NE), C105 (voorschrift zonder signaalwoord), C107 (onduidelijke constitutieve functie), C112 (verplichting als begrip), C115 (noodzakelijke voorwaarde), C116 (afleiding), C117 (fout citaat), C118 (historisch). Betekenisafhankelijke labels worden met de exacte context/bedoeling vastgelegd; geen algemene labelclaim op alleen de verkorte casuszin.

**Acceptatie:** met handmatig ingevulde modelresponsen is contractgedrag bewezen, inclusief behoud van B1–B6; geen claim dat een model de juiste functie kiest.

Commando, vanuit de O2-werkboom:
`/Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python -m pytest tests/unit/domain/test_def835_int02_contract.py -o addopts= -q -ra`.
Bewaar afzonderlijk rode en groene uitvoer; voer Ruff uit op de nieuwe Pythonbestanden.

### WP2 — begrensde AI-service en exacte T-prompt (offline)

Nieuwe bestanden:
- `src/services/validation/int02_assessment_service.py`
- `tests/unit/validation/test_def835_int02_assessment_service.py`
- `tests/unit/services/prompts/test_def835_int02_prompt.py`

Raming: 450–750 regels. Hergebruik de providerinterface en bestaande transporthulpen na controle van hun interface; geen brede refactor van INT-03/ESS-03. Alleen een expliciet geïnjecteerde fake en router in de tests. De dienst wordt nog niet door de container aangemaakt.

**Eerst rood:** norm/T letterlijk gerenderd, materiaal uitsluitend als gegevens, C117 timeout/verzonnen citaat, afgekapt of ongeldig JSON, router/modelmismatch, geen gekwalificeerd profiel, budgetlimiet, logging zonder ruwe invoer, één transportpoging, geen herstelcall, cache uitsluitend na geldig resultaat en volledige binding. Ontbrekende kern/context roept de fake niet aan.
**Acceptatie:** veilige foutafhandeling en versieattributie. Nog geen semantische kwaliteitsclaim.
Testcommando: hetzelfde Python/pytest-commando op de twee nieuwe testbestanden.
Voorlopige offline testlimieten zijn fixtures; een echt modelbudget moet later worden vastgesteld.

### WP3 — evaluator en publiek resultaatcontract (apart akkoord)

Voorgestelde bestanden:
- nieuw `src/services/validation/evaluators/decision_rule_assessment.py`
- `src/toetsregels/runtime_contract.py`
- `src/services/validation/evaluators/__init__.py`
- `docs/architectuur/contracts/validation_result_contract.md`
- `docs/architectuur/contracts/schemas/validation_result.schema.json`
- nieuw `tests/unit/validation/test_def835_int02_evaluator.py`
- `tests/integration/contracts/test_validation_result_schema.py`

Raming: 7 bestanden, 300–550 regels. Nieuw evaluatortype `decision_rule_assessment`; voorgestelde publieke contractversie 2.3.0 met `rule_results["INT-02"].assessment` en `signals`, alleen voor die regel. Onbekende velden blijven geweigerd. Runtime-record blijft O1 totdat activering expliciet is goedgekeurd. Tests kiezen een tijdelijk record via de bestaande registry.

**Eerst rood:** fake-oordelen pass/fail/RR/NE/error/NA door evaluator én schema; fail is adviserend en scoreloos; ontbrekend oordeel geeft open beoordeling; signalen leveren nooit oordeel; onbekende velden en niet-INT-02-regels accepteren de uitbreiding niet.
**Acceptatie:** publieke uitvoer heeft precies de afgesproken betekenis en teksten; O1-regressie blijft groen.
Commando: pytest op nieuwe evaluatortests, bestaande schematests en `test_def771_int02_o1.py`.

### WP4 — goldset en gecontroleerde modelevaluatie (apart besluit)

Eerst een protocol vaststellen, vervolgens nieuwe gevallen laten opstellen en onafhankelijk laten labelen. Voorstel: Chris is acceptatie-eigenaar en benoemt twee inhoudelijke beoordelaars. De 76 bestaande ontwerp-ID’s blijven ontwikkel-/regressiemateriaal. Een aparte hold-out blijft buiten promptontwikkeling; modelresponsen zijn nooit de goldlabels.

Voorstel ter latere vaststelling: 40 nieuwe gevallen, 24 ontwikkelgevallen en 16 bevroren hold-outs, gespreid over criteria/afleiding, voorschrift/discretie, normatieve begrippen, constitutieve kenmerken en onvoldoende betekenisgrond. Aantallen zijn een ontwerpvoorstel, geen statistisch kwaliteitsbewijs. Twijfellabels worden vóór de proef beslecht of expliciet als onbeslist gerapporteerd.

Protocol legt vooraf labelaar, herkomst, selectie, norm, exacte input, verwacht oordeel, passage/grond en adjudicatie vast. Freeze-manifest met hashes en gescheiden toegang; als de implementator hold-outs heeft gezien, vervalt hun onafhankelijkheid en worden nieuwe geselecteerd.

Vóór echte calls volgt één concreet evaluatievoorstel met modelprofiel volgens DEF-815/639, kostenplafond, maximale calls/tokens/duur, bewaartermijn en privacy. Huidig livebudget: **€0, nul calls**. Alleen synthetische/openbare invoer; geen productiedata. Geen ongekwalificeerde fallback.

Voorlopig kwaliteitsvoorstel: nul onterechte goedkeuringen op vooraf als kritieke overtreding gelabelde hold-outs, nul acceptaties van ongeldige citaten, nul toepassen van historische oordelen; onterechte afkeur, onthouding, technische fouten en latency apart met aantallen en noemers rapporteren. Grens voor semantische foutpercentages en acceptabele onthouding wordt vooraf door eigenaar vastgesteld, niet na het zien van resultaten. Een kleine foutloze set bewijst geen algemene betrouwbaarheid.

### WP5 — integratie, opslag en herladen (afgebakend vervolgplan vereist)

Actuele aansluitpunten:
`src/services/container.py`,
`src/services/orchestrators/validation_orchestrator_v2.py`,
`src/services/orchestrators/definition_orchestrator_v2.py`,
`src/ui/components/validation_view.py`.
Voor duurzame opslag/herbinding:
`src/services/definition_repository.py`,
`src/database/definitie_crud.py`,
`src/database/models.py`,
`src/services/definition_edit_service.py`,
`src/services/data_aggregation_service.py`,
`src/services/export_service.py`,
`src/ui/components/definition_edit_tab.py`.

Dit zijn onderzochte aansluitpunten, geen goedgekeurde bestandswijzigingen. Definitieve omvang is afhankelijk van de gezamenlijke DEF-626-opslagvoorziening. De eerder afgewezen parallelle INT-02-opslagroute wordt niet alsnog gebouwd. WP1–3 kunnen zonder die voorziening; volledige historische ketenacceptatie en productieactivering niet als geleverd afvinken zolang de vereiste opslag ontbreekt. Als een smallere aansluiting op een inmiddels geleverde voorziening mogelijk blijkt, eerst concreet plan/diffbereik voorleggen.

**Vereist bewijs vóór activering:** C118 via echte save→reload met tijdelijke SQLite, oude documentinhoud ongewijzigd, gewijzigde kern/betekenis/context/bron/norm niet actueel tonen; foutopslag geen geldig oordeel; UI en export tonen de juiste binding; geen herladen dat een modelcall verstopt start; kern bytegelijk. Bij geen gedeelde route blijft dit een benoemde leemte.

### WP6 — onafhankelijke review, verificatie en activering

Verse Codex CLI in aparte reviewwerkroot, workspace-write maar opdracht uitsluitend reviewen: concrete branchdiff tegen dit plan en B1–B6/synthese; citeer bestand/regel, impact en bewijs. Geen bronbestanden laten wijzigen. Coördinator verwerkt ieder punt via Claude CLI of gemotiveerde afwijzing met bewijs.

Na integratie: lokale relevante tests, lint, schema-/contractgate en verplichte offline profielen uit `scripts/testing/run_profile.py` (`unit`, `integration`, `acceptance-smoke`); geen liveprofiel. Volledige-suiteclaim alleen bij werkelijk uitgevoerde suite met exacte selectie en alle failures benoemd.

Voor activering apart concreet voorstel: record `INT-02.json` kiest nieuwe evaluator, de container/wrappers verbinden de dienst, contract/skills beschrijven de nieuwe uitvoeringsstatus en bestaande O1-tests worden inhoudelijk herijkt met behoud van cases. Dan pas PR(s), finale evidence en afzonderlijk geaccordeerde productieactivering. Actions blijven uit, geen merge zonder geldige autorisatie voor deze nieuwe oplevering.

## Gevraagde beslissing nu

Akkoord op **WP1**: het interne beoordelingscontract hierboven en de vijf genoemde nieuwe bestanden, offline met Claude Code CLI als implementator en Codex CLI als onafhankelijke reviewer. Dit omvat circa 650–950 regels; de reeds verleende omvangverruiming geldt.

WP2 en WP3 worden na WP1 concreet overgedragen; WP3 vraagt afzonderlijk akkoord op de publieke schema-/resultaatcontractuitbreiding en zeven bestanden. Goldseteigenaar/beoordelaars, definitieve kwaliteitsgrenzen, modelbudget en opslagroute zijn beslispunten vóór hun afhankelijke stappen. Zij blokkeren het offline WP1-contract niet.

## Proces en bewijsgrenzen

Prompts volledig bewaren onder deze dossiermap met vrije versienummers. De Prompt Forge-bereikbaarheidscheck is door de lokale securityhook geweigerd (“netwerk-tool curl — Netwerk-tool kan data exfiltreren”); geen omzeiling, gebruik de eerder toegestane dossierfallback. Tot nu toe is geen O2-implementatieprompt verstuurd.

Claude Code CLI 2.1.283 en Codex CLI 0.157.1 beschikbaar; beide ingelogd gecontroleerd. Alle acceptatiecriteria van DEF-835 blijven open tot hun eigen bewijs bestaat. Inventarisatie en een groene O1-basis zijn geen O2-implementatie of kwaliteitsbewijs.
