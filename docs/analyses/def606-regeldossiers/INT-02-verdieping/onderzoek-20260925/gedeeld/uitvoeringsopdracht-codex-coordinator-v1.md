# Opdracht voor Codex — coördineer de uitvoering van de INT-02-besluiten (DEF-771)

Je bent de **coördinator** van de uitvoering van de INT-02-besluiten in de repo `/Users/chrislehnen/Projecten/Definitie-app`. Je implementeert niet zelf op eigen initiatief: je plant, verdeelt, laat implementeren en reviewen, verifieert en rapporteert. Alles in het Nederlands. Tijd is belangrijk, maar zorgvuldigheid gaat voor: één werkpakket tegelijk, met terugkoppeling aan Chris vóór elke stap die zijn akkoord vraagt.

## 0. Bronnen (eerst volledig lezen, niets uit het hoofd citeren)

Dossiermap: `docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/`

1. `gedeeld/besluiten-chris-v1.md` — de besluiten B1–B6 (K1 breed · K2 O1 nu, O2 inplannen · K2b S1 · K3 één contract · K4 geen poort/DEF-831 · K5 geen herstel/DEF-832). **Dit is de opdrachtbasis.**
2. `gedeeld/gezamenlijke-synthese-v5.md` — §2 normtekst, §3 exacte G-tekst, §4 T-tekst + reviewerhulp + appmeldingen + statusmapping + signaalbeleid, §6 vervangtabel per vindplaats (record, prompt, evaluator, UI, skills, tests), §10 bewijsgrenzen.
3. `gedeeld/gezamenlijk-casusregister-v5.md` — 76 casus-ID's met verwachte uitkomst; de bron voor tests.
4. `gedeeld/besluitnotitie-chris-v5.md` — context en "bestaand beleid".
5. Linear: DEF-771 (rolverdeling en acceptatiecriteria), DEF-831, DEF-832, DEF-624 (resultaatcontract), DEF-830 (legacy .py-laag opruimen — niet in deze opdracht).
6. Repo-regels: `CLAUDE.md` en `.claude/rules/` van de repo; de skills `definitie-toetsregels` en `definitie-nederlandse-definities` (bron van waarheid: de map die het INT-03-besluit van 25-09 aanwijst, `_claude-global-setup/skills`; controleer dat pad vóór je schrijft en meld het als het afwijkt van wat synthese §6 noemt, `~/.agents/skills/...`).

Verifieer bij het lezen: regelnummers in synthese §6 (`json_based_rules_module.py:377`, `judgment_review.py:73–82`, `validation_view.py:807`, `runtime_cases.yaml:367`) gelden voor main `26f2374d`. Zoek de actuele plek op met grep; citeer wat je werkelijk aantreft.

## 1. Harde regels

- `git branch --show-current` eerst. **Nooit op `main` werken.** Maak `feature/DEF-771-int02-contract-o1` vanaf actuele `main` (noteer de commit-hash in je plan).
- **Vraag Chris vooraf akkoord** voor: het plan (stap 2), elk werkpakket dat >100 regels wijzigt of >5 bestanden raakt, elke nieuwe dependency, schemawijziging of wijziging van een API-/resultaatcontract. Verwacht dat WP1 en WP3 samen die drempel halen: leg ze apart voor.
- **Niets verwijderen** (bestanden, testgevallen, dode code) zonder expliciete toestemming van Chris. De dode `IntegrityRulesModule` en `.py`-validators laat je staan (DEF-830).
- **Geen live modelaanroepen, geen productiedata.** Alle tests offline en deterministisch. Effectmeting met echte generatie (synthese §8) valt buiten deze opdracht; die vraagt aparte autorisatie.
- Verificatie-eerst: lees bestanden met de tools, parafraseer niet; Linear-issues ophalen via de Linear-koppeling, niet uit geheugen.
- Max. 3 pogingen per actie; daarna stoppen en melden.
- Prompts die je aan Claude Code CLI of aan een review-sessie geeft, sla je **volledig** op in de dossiermap (`gedeeld/uitvoering/`) én in de Prompt Forge-database (single source of truth voor prompts).
- Rolverdeling uit DEF-771: **jij coördineert, Claude Code CLI implementeert, een afzonderlijke verse Codex CLI-sessie reviewt de concrete diff.** Geef Claude Code CLI per werkpakket een schriftelijke opdracht (`claude -p` in de repo, met de opdrachttekst uit `gedeeld/uitvoering/wp-N-opdracht-claude.md`). Is Claude Code CLI in jouw omgeving niet aanroepbaar, meld dat dan aan Chris en vraag of je zelf mag implementeren; besluit dat niet zelf.

## 2. Werkwijze — eerst een plan, dan pas code

**Stap 1 — inventarisatie (geen wijzigingen).** Lees de bronnen. Maak `gedeeld/uitvoering/plan-v1.md` met per werkpakket: doel, exacte bestanden en huidige regels (geciteerd), verwachte omvang (regels/bestanden), tests die eerst rood moeten zijn, acceptatiecriterium uit de synthese, en de casus-ID's die het pakket bewijst. Noteer afwijkingen tussen dossier en actuele code. Leg het plan aan Chris voor en **wacht op zijn akkoord**.

**Stap 2 — uitvoering per werkpakket, in deze volgorde.** Per pakket: opdracht schrijven → Claude Code CLI laat tests eerst rood schrijven (TDD), dan implementeren → jij verifieert (tests draaien, diff lezen, casussen nalopen) → Chris kort terugkoppelen → volgende pakket.

### WP1 — Eén versiegebonden INT-02-contract (B4, K3)
- Nieuw canoniek bestand `references/int02-beslisregel.md` in de skill `definitie-toetsregels`: normtekst (§2, brede variant, met de bronannotatie "lokale operationalisering; ASTRA benoemt discretionaire beslisregels en staat afleidingsregels toe, verplicht bij afleidbare begrippen"), veldrollen (B3 V02), G (§3), T (§4 incl. statusmapping), H alleen als specificatie van het toelichtingsvoorstel (§5, met verwijzing naar DEF-832: geen herstelroute), voorbeelden ✅ C10/C05/C19/C53/C112/C113/C116 ❌ C02/C12/C52/C105/C114, grens C16/C24/C55/C58/C107, besluitstatus (besluiten-chris-v1.md), bronherkomst, **versienummer en datum**. Byte-gelijke kopie in `definitie-nederlandse-definities/references/`.
- `src/toetsregels/regels/INT-02.json`: `uitleg`, `toelichting`, `toetsvraag`, `type` → "gehele definitie", `brondocument` → "ASTRA (verwijst naar DBT §4.2; DBT niet rechtstreeks onderzocht)", `example_pair_reason` → de gezamenlijke tekst uit §6, voorbeelden: ASTRA-paar letterlijk behouden (`review_policy`) + functievoorbeelden met herkomst, en een veld dat de contractversie bindt. Exacte teksten: synthese §6, rijen `INT-02.json`. Voeg niets toe dat niet in §6 staat.
- Skillzinnen vervangen: `definitie-toetsregels/reference.md` (rij "Vermijd voorwaardelijke formuleringen…") en `definitie-nederlandse-definities/reference.md` (rij "Voorwaardelijke formuleringen: indien, mits…") door de exacte vervangteksten uit §6 (versie na SC-C-02); in beide `SKILL.md` het blok "INT-02 — begripscriterium tegenover beslisregel" met de gerichte duiding uit §6 (geen kwaliteitscijfer; totaalscore vervallen 15-09-2026; het JSON-runtimecontract bepaalt de evaluator).
- Test: een contracttest die bewijst dat record-uitleg, toetsvraag en de skillkopie uit hetzelfde contract komen (byte-gelijk of uit één bron gerenderd) en dat de versie in record en contract overeenkomt.

### WP2 — Generatie-instructie G (B4, K3)
- `json_based_rules_module.py` (huidig regel ~377: "Vermijd voorwaardelijke formuleringen zoals 'indien', 'mits', 'tenzij', 'alleen als'"): vervangen door de exacte G-tekst uit synthese §3 (versie v5, na SC-C-02), binnen het bestaande één-zin-uitvoercontract; geen extra uitvoer (geen vraag, bron of toelichting in de zin).
- Test: promptrendering op moduleniveau (zoals proef P2 in `a-claude-cli/bewijs/` en `c-codex-app/bewijs/`) bewijst dat de oude zin niet meer voorkomt en de nieuwe G letterlijk wordt gerenderd, met en zonder voorbeelden. Controleer en rapporteer (zonder te wijzigen buiten INT-02) of het INT-01/INT-02-voorbeeldconflict (DEF-612: INT-01.json gebruikt dezelfde "moet ondersteunen"-zin als goed voorbeeld) nog bestaat.

### WP3 — Toetsing O1 met passagehulp en S1-signalen (B2, B3)
- `judgment_review.py` (INT-02-tak, huidig ~73–82): nieuwe `_int02_reden` naar het ESS-04-patroon: reden = de nieuwe toetsvraag; per treffer de neutrale functievraag met het **volledige zinsdeel en positie** (niet `hit.group()` als los woord); zonder treffer de waarschuwingstekst; exacte teksten: synthese §4 "Reviewerhulp (O1, exacte tekst)". Lege kern of ontbrekende context → `not_evaluated` met de NE-melding uit §4 (bestaand beleid K-9). Status blijft `review_required` voor de menselijke beoordeling; nooit `pass`/`fail` uit een signaal. Geen score (`excluded_from_score` blijft).
- Signalen S1: de zeven bestaande patronen blijven; voeg een **beperkte** set discretie-/voorschriftmarkers toe. Stel de lijst eerst voor aan Chris (kandidaten: "van oordeel is", "naar eigen inzicht", "redelijk acht", "kan … besluiten", "moet/dient …"), getoetst op C13 (bevat de voorbeeldmarkers niet — meld dat), C83 (moet treffen), C59 (definitie *van* "beslisregel": vals-alarmrisico benoemen), C105 (voorschrift zonder signaalwoord: blijft signaalloos → waarschuwingstekst). Pas de lijst pas toe na zijn akkoord. Markeer patronen in het record expliciet als leeshulp, niet normatief.
- `validation_view.py` (huidig ~807, tuple `("ESS-01","ESS-02","ESS-04")`): "INT-02" toevoegen zodat reden en passagehulp zichtbaar zijn. Geen andere UI-wijziging.
- Tests (eerst rood): C04/C50/C54 → RR mét signaal en neutrale vraag, nooit fail; C02/C83/C105 → RR met waarschuwingstekst (C83 met S1-marker); C06/C23/C56 → `not_evaluated`; C13 → geen valse S1-claim; C59 → geen afkeur. Herhaal `a-cowork/bewijs/proef-c1-run.py` en leg de nieuwe uitkomsten vast als `proef-c1-uitvoering-na-o1.json` (verwacht: statussen ongewijzigd RR/NE, reden en signaalvorm gewijzigd).
- **Niet doen:** geen INT-02-poort (DEF-831), geen herstelroute (DEF-832), geen O2-modelaanroep, geen wijziging aan de issues-helper of de expertreview-herlaadroute (DEF-626; wel melden als je iets tegenkomt).

### WP4 — Bestaande tests herijken (B4)
- `test_v2_golden_int_more.py::test_int02_no_decision_rules_fail` en `runtime_cases.yaml` (regel ~367, probe "korting: verlaging indien tijdig betaald"): herijken naar de brede norm: de uitkomst is `review_required` (functieafhankelijk, C24/C25), geen `fail`. Hernoem de test zodat de naam niet meer "fail" belooft. Geen testgeval verwijderen.

### WP5 — Review en verificatie
- Verse Codex CLI-sessie (`codex exec`, workspace-write, aparte werkroot) reviewt de volledige diff van de branch tegen `gedeeld/besluiten-chris-v1.md` en synthese §3/§4/§6: exacte teksten letterlijk, geen betekenisverlies, geen scope-creep, tests eerst rood dan groen, niets verwijderd. Bevindingen verwerk je met rigor (niet blind overnemen, niet blind afwijzen); leg per punt vast wat je deed.
- Verification-before-completion: volledige testsuite draaien (`pytest`), resultaat letterlijk in het verslag; drie omgevingsgebonden failures uit de cloudomgeving gelden niet op de Mac — meld elke failure met oorzaak.

### WP6 — Oplevering (geen merge zonder Chris)
- Eén PR vanaf de featurebranch met beschrijving: besluiten (B1–B6), per WP wat gewijzigd, bewijs (testuitvoer, proef-c1-na-o1, promptrendering), bewust niet gedaan (O2, herstel, poort, DEF-626, DEF-830, effectmeting), bewijsgrenzen.
- Oplevercomment op DEF-771 met dezelfde inhoud en de SHA-256 van `references/int02-beslisregel.md`; koppel DEF-831/DEF-832. Vink alleen acceptatiecriteria af die je met bewijs kunt dekken.
- Vervolgissue O2 (B2) **na akkoord van Chris** aanmaken: "[STORY] INT-02 — AI-beoordeling (O2) met goldset", inhoud: onafhankelijke goldset (de 76 ontwerp-ID's zijn geen hold-out), model-/promptversie (DEF-815), kosten, privacy, foutbeleid (ADR-001), citaatcontrole (C117), statusmapping uit §4, poortbeleid volgt DEF-831; gerelateerd aan DEF-771, DEF-766, DEF-768.

## 3. Stopregels (stoppen en melden, niet improviseren)

- Dossier en code spreken elkaar tegen op iets wat een besluit raakt (bijv. het record heeft al andere velden, de evaluator is intussen anders gebouwd) → melden met citaat, voorstel, wachten.
- Een exacte tekst uit de synthese past niet in het bestaande contract (bijv. lengte, één-zin-eis, velden die niet bestaan) → melden, niet zelf inkorten.
- Een test uit het casusregister kan niet deterministisch worden gemaakt zonder model → overslaan en als bewijsleemte noteren.
- De S1-markerlijst, de O2-issue en elke verwijdering vragen expliciet akkoord van Chris.

## 4. Rapportage

Houd `gedeeld/uitvoering/processtatus-uitvoering.md` bij (tijd, WP, bestanden, tests rood→groen, open punten). Sluit af met een kort eindbericht aan Chris: branch en commit-hashes, PR-link, wat is gedaan, wat bewust niet, welke acceptatiecriteria van DEF-771 met bewijs zijn afgedekt, en wat er nog open staat (O2, effectmeting, DEF-626, DEF-830, CON-01-keuze in DEF-831).
