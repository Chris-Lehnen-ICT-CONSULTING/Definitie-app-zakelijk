# DEF-835 WP1 — rapport Claude Code CLI, RED v1

26 september 2026 · uitvoerder: Claude Code CLI (Opus 5.5) · opdracht: `wp1-opdracht-claude-v1.md` · leidend: `plan-v1.md` §Ontwerpvoorstel en §WP1, `akkoord-wp1-v1.md`.

**Status: RED gereed; wacht op coördinator voor GREEN.** Er is geen contractlogica geïmplementeerd. Er is niets gecommit of gepusht en er is geen PR gemaakt. Er is geen netwerk gebruikt, geen `.env` gelezen en geen productiedata aangeraakt.

## Werkboom en bestanden

Werkboom `.claude/worktrees/DEF-835-int02-o2`, branch `feature/DEF-835-int02-o2`, HEAD `84bdc8c1b060ab50a1bd1428aed778bb2ed6007f`, geen getrackte wijzigingen (`git diff --stat` leeg).

| Bestand | Regels | SHA-256 | Inhoud |
|---|---|---|---|
| `src/domain/int02/__init__.py` | 6 | `7c581491…e8e961cb` | pakketdocstring |
| `src/domain/int02/contract.py` | 109 | `891d8320…38b22` | alleen API-stubs; elke aanroep geeft `NotImplementedError` (behalve de lege exceptieklasse) |
| `tests/unit/domain/test_def835_int02_contract.py` | 1104 | `989ac11c…29e4` | 162 tests (na `ruff format`) |
| `tests/fixtures/def835_int02_ontwerpgevallen.json` | 414 | `e18adb97…867d` | 12 ontwerpgevallen met herkomst en bronhashes |
| `docs/architectuur/contracts/int02_assessment_contract_v1.md` | — | — | **nog niet geschreven**: hoort bij GREEN; de RED-run toont dat het ontbreekt |

Bewijs:
- `bewijs/wp1-rood-v1.log` (SHA-256 `448a3d32…6bec`) — **mislukte aanroep**, bewust bewaard: het commando stond in een zsh-variabele en werd niet gesplitst, exit 127, geen test gedraaid. Het is geen RED-bewijs.
- `bewijs/wp1-rood-v2.log` (SHA-256 `fb0bc657…12bd`, 6357 regels) — de geldige RED-run met commando, tijdstip, branch, HEAD, volledige uitvoer en exitcode.

**Omgevingsartefact buiten het eigendom, te melden.** Elke `Write` faalde eerst omdat de PreToolUse-hook `$CLAUDE_PROJECT_DIR/.claude/hooks/check-silent-exceptions.py` niet in deze werkboom staat. Dat is een technische hookfout, geen security-afwijzing (projectmemory `worktree-mist-claude-hooks`). Om de hook niet te omzeilen heb ik een symlink aangelegd: `.claude/hooks/check-silent-exceptions.py` → `/Users/chrislehnen/Projecten/Definitie-app/.claude/hooks/check-silent-exceptions.py`.

Die symlink is **niet** git-ignored, want `.gitignore:188` heeft `!.claude/hooks/`. Hij staat dus als `??` in `git status`. **Niet committen.** Laten staan of verwijderen is een besluit van de coördinator; ik heb niets verwijderd.

Lint: `python -m ruff check src/domain/int02 tests/unit/domain/test_def835_int02_contract.py` geeft "All checks passed!". Eerder vond Ruff N818 en E741; die heb ik opgelost met de hernoemingen `Int02ContractError` en `ONVOLDOENDE`. `ruff format` is alleen toegepast op mijn eigen nieuwe bestanden.

## RED-uitkomst

Commando, vanuit de werkboom:
`/Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python -m pytest tests/unit/domain/test_def835_int02_contract.py -o addopts= -q -ra`

Resultaat: **162 failed, 0 passed, 0 errors in 2.75s, exit 1.** Er waren geen collectie- of setupfouten. De failures hebben twee oorzaken:
- **161×** `NotImplementedError` uit de stubs: de functionele logica ontbreekt;
- **1×** `FileNotFoundError` op `docs/architectuur/contracts/int02_assessment_contract_v1.md`: het contractdocument ontbreekt.

Elke test roept eerst de API aan of leest het document. Een test die in RED zou slagen, bijvoorbeeld een losse fixture-metacontrole, heb ik niet opgenomen. De fixturemetadata wordt daarom binnen de gevalstest gecontroleerd.

| Groep | Aantal | Welk ontbreken dit aantoont |
|---|---|---|
| Ontwerpgevallen (fixture) + C118 | 12 | Er is geen statusmapping voor C06/C23/C56 (NE), C105 (VN zonder signaalwoord), C107 (O met één vraag), C112/C115/C116 (V), C117 (verzonnen citaat → error invalid_citation; timeout → error timeout) en C101 (discretie). C118 laat zien dat er geen historische replay is. |
| Exacte, onveranderlijke invoer | 14 | Er is geen bytegelijke snapshot (NBSP, CRLF, randwitruimte), geen defensieve kopie en geen frozen invoer. Een onbekende bedoeling wordt nog niet expliciet als `null` bewaard. Er is geen closed-world invoercontrole: typen, bool in lijst, bronvelden, lege of dubbele bron-ID. |
| Binding, historie en replay | 27 | Er is geen binding met contract-/normversie, normhash, promptversie, routeringshash, provider/model en hashes. Elk van de 15 componenten apart (begrip, kern (alleen witruimte), bedoeling, 3 contextlijsten, brontekst, bron-ID, extra bron, normversie, normhash, promptversie, routeringshash, provider, model) moet precies zijn eigen bindingsveld wijzigen en het oude oordeel historisch maken. Ook ontbreken nog: replay bij ongewijzigde binding, "nog niet beoordeeld" (geen document of `not_executed`), NE vóór replay en configuratievalidatie. |
| Onveranderlijk document en integriteit | 6 | `oordeel` wordt nog niet als kopie teruggegeven en de meegegeven respons wordt niet onaangeroerd gelaten. Het document is niet frozen. Een gemanipuleerde status, melding of invoer wordt bij replay niet als `error` herkend. JSON-serialisatie zonder score- of cijferveld ontbreekt. |
| Gesloten modeluitvoer (structuur) | 26 | Er is geen closed-world-validatie. De 24 mutaties omvatten ontbrekend veld, onbekend veld `score`, enums, lijst/objecttypen, positie als float/str, bool-positie in grond, gedeeltelijk grondcitaat en `ref` bij kern. Daarnaast: bool `False` als passagestart 0, en een voltooide uitvoering zonder uitvoer → error `invalid_output`. |
| Citaten en gronden | 22 | Er is geen exacte citaatcontrole op nulgebaseerde posities met exclusief einde: verschoven, inclusief einde, voorbij de kern, negatief, leeg, hoofdletterverschil, niet in kern, of genormaliseerde witruimte. Er is geen grondcontrole: bron-ID bestaat, broncitaat op positie, contextindex int (geen bool of str) binnen de lijst, en een grond op een onbekende bedoeling is niet herleidbaar. Ook ontbreekt acceptatie van herleidbare gronden. |
| Statusmapping en exacte meldingen | 29 | De meldingen V, VN, discretievariant, O en NA ontbreken; de verwachte teksten worden letterlijk uit synthese §4 gelezen. Fail blijft fail met open vraag, beslissende onzekerheid en gedeeltelijke dekking. De 21 inconsistente oordelen moeten error `invalid_output` geven, zonder reparatie: onbewijsbare pass, fail zonder gebrek, O zonder precies één vraag of met bewezen gebrek, NA zonder reikwijdtegrond of voor een afleiding. Een niet-beslissende onzekerheid mag pass niet blokkeren. |
| Niet uitgevoerd en technische fout | 9 | Er is geen `ontbrekende_invoer`: leeg, witruimte, label "Toegang:", geen context, of beide. Een NE moet een meegegeven oordeel negeren; een label geeft NE, ook als de uitvoer NA zegt. Een transportfout moet de meegegeven uitvoer negeren. |
| Woordpatronen niet normatief | 2 | Er is nog geen bewijs dat "indien" geen afkeur geeft en dat de code een modelfunctie niet op woorden overrulet. |
| Uitvoeringsmetadata | 14 | Standaardwaarden zijn nog niet expliciet `unknown`. Gerapporteerde metingen blijven niet bewaard; kosten zouden als Decimal-string "0.0042" moeten worden vastgelegd. Er is geen validatie: bool, negatief, str, float, tijdstip-type, actor, status, een fout zonder categorie, voltooid mét categorie, en een codecategorie als transportfout. |
| Contractdocument | 1 | Het document met versies en alle exacte meldingen ontbreekt. |
| **Totaal** | **162** | |

## Voorgenomen API (`domain.int02.contract`)

Klein en zonder generieke infrastructuur. De tests gebruiken letterlijke verwachte waarden en geen constanten uit de implementatie.

- `maak_invoer(*, begrip, kern, bedoeling, organisatorische_context, juridische_context, wettelijke_basis, bronnen) -> Int02Invoer`
  - Levert een frozen snapshot: lijsten worden tuples, bronnen worden `(id, tekst)`-objecten.
  - `bedoeling=None` betekent expliciet onbekend.
  - Ongeldige invoer geeft `Int02ContractError(ValueError)`.
- `Configuratie(normversie, normhash, promptversie, routeringshash, provider, model)`
  - Hashes zijn 64 hex-tekens.
  - Lege of niet-string waarden worden geweigerd.
- `Uitvoering(actor, status, foutcategorie=None, tijdstip, transportpogingen, invoertokens, uitvoertokens, duur_ms, kosten, modelversie)`
  - Alle meetvelden hebben standaardwaarde `"unknown"`.
  - `actor` is `ai` of `human`.
  - `status` is `completed`, `failed` of `not_executed`.
  - Transportcategorieën zijn `timeout`, `transport` en `provider`. `invalid_output` en `invalid_citation` zijn uitsluitend codecategorieën.
- `bereken_binding(invoer, configuratie) -> Binding`
  - Velden: `contractversie`, `normversie`, `normhash`, `promptversie`, `routeringshash`, `provider`, `model`, `begrip_hash`, `kern_hash`, `bedoeling_hash`, `context_hash` en `bronnen_hash`.
- `ontbrekende_invoer(invoer) -> "kern" | "context" | "kern en context" | None`
  - Hiermee kan de WP2-dienst NE vaststellen zonder modelcall.
- `beoordeel(invoer, configuratie, modeluitvoer, uitvoering) -> Beoordelingsdocument`
  - Volgorde: NE → transportfout → niet uitgevoerd → structuur → citaten/gronden → consistentie → status.
  - Het document bevat `contractversie`, `invoer`, `binding`, `uitvoering`, `status`, `reden`, `melding`, `vraag`, `foutcategorie`, `oordeel` (kopie of `None`) en `als_dict()`.
  - Een integriteitshash over de inhoud laat manipulatie bij replay zien.
  - De gerapporteerde modelversie staat in `uitvoering` en telt mee in de integriteitshash. Zij hoort niet bij de replay-vergelijking, want vóór een nieuwe call is zij onbekend.
- `toets_actualiteit(document | None, invoer, configuratie) -> Actualiteit(status, reden, melding)`
  - Volgorde: NE → geen document ("nog niet beoordeeld") → integriteit (error) → andere binding (historisch) → anders het bewaarde oordeel.

Gesloten modeluitvoer:
- Veld `verdict`: `pass`, `fail`, `insufficient_information` of `not_applicable`.
- Veld `passages[]`: elk element heeft `quote`, `start`, `end`, `function` en `ground`.
  - `function` is `criterion`, `derivation`, `actor_prescription`, `discretionary_decision_rule` of `unclear`.
  - `ground` heeft `field`, `ref`, `quote`, `start` en `end`.
  - `field` is `kern`, `begrip`, `bedoeling`, een van de drie contextlijsten, of `bron`.
  - `ref` is `null` bij scalaire velden, een int-index bij een contextlijst en een bron-ID bij `bron`.
  - Een grondcitaat heeft alle drie de velden `quote`, `start` en `end`, of geen ervan.
- Overige velden:
  - `reason`: een niet-lege string;
  - `question`: `null` of precies één vraag, eindigend op het enige `?`;
  - `uncertainty`: `none`, `non_decisive` of `decisive`;
  - `scope_reason`: `null` of een string;
  - `coverage`: `complete`, `partial` of `none`.

Statusregels:
- **pass**: minstens één passage, alleen criterium of afleiding, `coverage complete`, geen beslissende onzekerheid, geen vraag en geen reikwijdtegrond.
- **fail**: minstens één voorschrift of discretie; een open vraag, onzekerheid en gedeeltelijke dekking zijn toegestaan.
- **insufficient_information**: geen bewezen gebrek, precies één vraag en beslissende onzekerheid. Status `review_required` met reden `insufficient_information`.
- **not_applicable**: reikwijdtegrond, geen passages, `coverage none`, geen vraag.
- Structuurfouten geven `invalid_output`, positie- en herleidingsfouten `invalid_citation`. Beide geven altijd status `error` met melding E en `oordeel` gelijk aan `None`.
- Een review_required heeft een van drie redenen: `insufficient_information`, `not_assessed` of `historical`.

## Punten ter beoordeling door coördinator/reviewer

Synthese §4 heeft hiervoor geen letterlijk sjabloon. Ze zijn in de tests vastgelegd en daarmee zichtbaar:

1. **Nog niet beoordeeld**: `INT-02 — Nog te beoordelen — beoordeling niet uitgevoerd.` De term komt uit de T-tekst ("nog te beoordelen — beoordeling niet uitgevoerd"); het voorvoegsel en de zinsvorm zijn van mij.
2. **Niet van toepassing**: `INT-02 — Niet van toepassing. {reikwijdtegrond}. Er is geen oordeel over de definitiekern.` Dit is een eigen formulering; §4 noemt alleen "NA→not_applicable … alleen met grond".
3. **Discretievariant**: de VN-melding met `{handeling/afweging}` = "een afweging", gevolgd door een spatie en de letterlijke discretievariant. §4 noemt deze variant tussen haakjes zonder te zeggen of zij de VN-tekst vervangt of aanvult. Ik koos aanvullen, zodat "INT-02 — Voldoet niet" en de grond zichtbaar blijven.
4. **Invulling van plaatshouders**:
   - `{criterium/afleiding/kenmerk}` wordt "een criterium" of "een afleiding";
   - `{handeling/afweging}` wordt "een handeling" of "een afweging";
   - `{grond}` wordt het veldlabel ("de bevestigde bedoeling", "bronpassage B1", …), met bij een citaat ` ('<citaat>')` erachter;
   - bij O en NA vervalt een afsluitende punt van reden of reikwijdtegrond, zodat er geen dubbele punt ontstaat;
   - V en VN citeren de eerste passage (V) of de eerste gebrekkige passage (VN), gerekend op startpositie.
5. **Vraagtelling**: "precies één vraag" wordt mechanisch benaderd als "één niet-lege string die eindigt op het enige vraagteken". De code bewijst niet dat de vraag gericht is.
6. **Omvang**: de tests (1104 regels na formattering) en de fixture (414 regels) samen liggen al boven de raming van 650–950 regels. Oorzaak: de parametrisering per bindingscomponent, structuurmutatie, citaatfout en inconsistentie, en de ingevulde responsen met herkomst in de fixture. Ik heb geen noodzakelijke test weggelaten. Implementatie en document komen er in GREEN nog bij.

## Bronnen van de casussen

Bronbasis: `docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/`. De SHA-256 van elk bronbestand staat in de fixture.

| Geval | Exacte invoer uit | Ontwerpaanvulling (in fixture gemarkeerd) |
|---|---|---|
| C06 | `a-claude-cli/bewijs/p1-invoer.json` INT02-C06 (`""`, context `{}`) | — (NE "kern en context", want de bron heeft geen context) |
| C23 | idem INT02-C23 (`"Toegang:"`, context `{}`) | — |
| C56 | `b-codex-cli/bewijs/proeven-b-v1.py:28` (C50-tekst, context `{}`) | — |
| C105 | `c-codex-app/bewijs/proefopzet-v1.json` INT02-C105 (term, tekst, context, bedoeling) | modelrespons |
| C107 | `c-codex-app/casusregister-c-v1.md` INT02-C107 (tekst) | begrip, context; bedoeling expliciet onbekend, zodat het O-label bij de onduidelijke functie hoort |
| C112, C115, C116 | `casusregister-c-v1.md` (tekst en bedoeling) | begrip, context |
| C117 | invoer INT02-C100 uit `proefopzet-v1.json`; scenario `casusregister-c-v1.md` | verzonnen citaat "twee maal wegens een misdrijf" |
| C101 | `proefopzet-v1.json` INT02-C101 | extra geval voor de discretievariant |
| C118 | versie 1 = C106-tekst uit `casusregister-c-v1.md`; versie 2 = C102 uit `proefopzet-v1.json` | begrip en context van versie 1 |

Referentielabels komen uit `gedeeld/gezamenlijk-casusregister-v5.md` en gelden alleen met de vastgelegde bedoeling en context. De modelresponsen zijn handmatig ingevuld: het zijn geen goldlabels en ze vormen geen hold-out.

## Niet gedaan

GREEN-implementatie, contractdocument, commit, push, PR, Linear en processtatus: die zijn niet aan mij. Ik heb geen bestaande bestanden gewijzigd en niets verwijderd.

**RED gereed; wacht op coördinator voor GREEN.**
