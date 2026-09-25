# DEF-770 restherstel — resultaat Claude-uitvoerder (v2, correctiepoging 2)

25 september 2026. Claude Code CLI, sessie `442a98fb-a377-403f-996e-433cf4a664fc`. Verwerkt: `logs/def770-restherstel/astra-review-v1.md` (volledig gelezen). Vorig rapport `claude-resultaat-v1.md` blijft ongewijzigd staan.
Niet gedaan:
- agents, reviewers of extra CLI-sessies gestart;
- commits, pushes, merges of betaalde calls;
- de nieuwe maker of de nieuwe proefset gelezen;
- ESS-01-record, labels of historische proefdata gewijzigd.

## 1. T20 — eerlijke status: open dekkingsblokkade

**Poging 2, oorzaak.** De eerste kandidaat liet één extra woord in een voorzetselgroep toe. De onderbouwing daarvan steunde op grammaticale correctheid: ‘het’ na een voorzetsel zou lidwoord zijn, en een ontbrekend onderwerp zou uitsluiten dat er een nieuwe zin begint. Het contract veronderstelt die correctheid niet. De reviewer liet zien dat ‘met het regent hard’ en ‘tijdens de proef wacht’ daardoor ten onrechte pass werden.

Het enige verschil met ‘van de bijbehorende opdracht’ is de woordrol van het extra woord: bijvoeglijk naamwoord tegenover persoonsvorm of bijwoord. Die rol is niet te bewijzen zonder woordsoortkennis. Morfologie (-e, -n) is uitgesloten: dat is het afgewezen woordrolargument. Een woordlijst is een fixture- of blacklistroute. Daarom valt er binnen de bestaande architectuur geen veilige variant te maken, en heb ik geen derde onbewezen variant gebouwd.

**Uitgevoerd.**
- De uitbreiding is volledig verwijderd uit `src/domain/int01/zinsgrenzen.py`: `_groep_met_extra_woord`, `_VOORZETSELS_ZONDER_BIJFUNCTIE` en `_ZUIVERE_LIDWOORDEN`.
- `_voorzetselgroepen` is bytegelijk teruggezet naar de base (herstelkopie-v1).
- De reviewerregressies en exacte T20 zijn onzeker, met passage en citaatreden.
- De referentieverwachting (pass) staat als **strikte xfail** (`T20_OPEN`, 2 gevallen) in `test_def770_restherstel_zinsgrenzen.py`. Dat is een zichtbare blokkade, geen waiver en geen relabel.
- Contract `/7` bevat nu alleen de T22-wijziging; commentaar en docstrings zijn daarop aangepast.
- De skillsreferentie beschrijft nu feitelijk dat de app alleen groepen met hooguit lidwoord plus één woord herkent. De rest blijft open, terwijl het normatief één formulering kan zijn.

**Twee opties ter beslissing:**
1. **Beleidsbesluit (zoals het titelbesluit).** Een nominale voortzetting na een titel of citaat, met een woord dat niet direct door een voorzetsel of lidwoord is gemarkeerd, gaat automatisch naar inhoudelijke beoordeling. Het referentielabel blijft pass en de automatische verwachting wordt `review_required`, met besluittrace. De strikte xfail wordt dan een geldende verwachting. Kosten: geen code; wel bewust dekkingsverlies.
2. **Woordrolbewijs toevoegen.** Een Nederlandse woordsoortbron: een POS-tagger of lexicon als nieuwe dependency, of een beheerde lijst van attributieve bijvoeglijke naamwoorden als configuratie. Alleen een bewezen attributief bijvoeglijk naamwoord tussen lidwoord en kern zou dan tellen; onbekende woorden blijven onzeker. Kosten: dependency of beheerd lexicon, en een nieuwe review- en testronde. Dit vraagt goedkeuring voor een nieuwe dependency of bron.

Ontwikkelregressie op de verzegelde T24-set (`t24-ontwikkelregressie-v2.log`): **23/24** conform op de zinsstructuuras. T20 is de enige afwijking (ref pass, app review_required). T22 is conform.

**T22** is door de reviewer gesloten binnen de beperkte scope en ongewijzigd behouden.

## 2. Correctie van de LOW-rapportbevinding (v1 §3)

In v1 stond dat gevolgen “zonder beslisregel” zouden wegvallen, mede door ESS-01. Dat was te sterk:
- ESS-01 sluit alleen **niet-begripsbepalende** doelen of effecten uit. Een functie of rol die het begrip mede bepaalt, blijft behouden als herleidbare domeininformatie dat onderbouwt (`ESS-01.json`, `uitleg`).
- De finale bronneninstructie vraagt al behoud van “bepalende kenmerken, beperkingen en uitzonderingen”, ook als een regel dan faalt.

Wat wél ontbrak: de eindcontrole toetste handeling, relatie en modaliteit, maar niet de koppeling voorwaarde–gevolg per alternatief of het ontkende gevolg. De losse weglaatzin gaf ook geen criterium voor een eigenschap die volgens de bron mag wisselen. Verder stond MECHANISME 2 (“Vernauw begrippen met domein-qualifiers”) naast INT-01 (“maak de betekenis niet smaller”), zonder grens bij de bronafbakening.

Mijn conclusie in v1 dat een extra semantische modelaanroep nodig zou zijn, trek ik in als voorwaarde. De reviewer toonde aan dat stochastiek een zinvolle promptverbetering niet uitsluit, en de acceptatie vraagt geen garantie. Het effect blijft onbewezen tot een nieuwe onafhankelijke meting.

## 3. Generatieherstel (uitgevoerd, zonder extra call, dependency of schema)

Gerichte vervangingen, geen extra losse waarschuwingen:
- **`definition_task_module.py` (KWALITEITSCONTROLE):**
  - “drie punten” wordt “vier punten”. Het nieuwe punt **voorwaarde en gevolg**: een afbakenende voorwaarde houdt het gevolg dat de bron eraan koppelt, en elk alternatief houdt zijn eigen gevolg (niet samenvoegen tot één ‘of’ zonder dat gevolg). Een afbakenend ontkend gevolg of een uitzondering blijft ook behouden. Zo'n gevolg is een kenmerk, geen doel of effect in de zin van ESS-01.
  - De weglaatzin (“Een werkafspraak of mogelijkheid … laat je weg …”) is **vervangen** door het criterium: laat weg wat de bron niet als afbakening draagt, inclusief een eigenschap die volgens de bron mag wisselen zonder dat het begrip verandert; neem die niet op als eis of vaste beperking.
  - De voorrang vóór stijlvoorkeuren is ongewijzigd.
- **`context_awareness_module.py` (MECHANISME 2):** “Vernauw begrippen met domein-qualifiers.” is vervangen door “Kies het domeinspecifieke woord binnen de afbakening die de bron geeft; maak de betekenis niet smaller dan de bron met een extra qualifier, zoals een eigenschap die volgens de bron mag wisselen.” De bestaande woordvoorbeelden blijven.
- **`json_based_rules_module.py` (INT-01-kaart):**
  - “formuleer een afbakenende toepassings- of eindvoorwaarde, **met het gevolg dat de bron eraan koppelt**, als kenmerk …”;
  - “Neem bronbijzaken … niet op, **ook geen eigenschap die volgens de bron mag wisselen**.”
- **Skills (werkboom, niet live):**
  - NL-definities `SKILL.md`: dezelfde vier punten en hetzelfde weglaatcriterium.
  - NL-definities `reference.md`: de compact-rij is uitgelijnd.
  - `definitie-toetsregels/reference.md`: de alinea “Norm en generatie” is uitgelijnd.
- **Niet gewijzigd:**
  - ESS-01-record en `config/`: `git diff` leeg.
  - De 500/800-snippetlimieten.
  - Er staan geen proeftermen of ideaalantwoorden in de productieprompt; dat is getest.

## 4. RED/GREEN en logs (`logs/def770-restherstel/`)

| Stap | Log | Uitkomst |
|---|---|---|
| Herstelkopieën | `herstelkopie-v2/` (11 bestanden, `herstelkopie-maken-v2.py`) | GELIJK vóór de edits |
| RED T20 | `int01-red-v2.log` en `.xml` | 412 tests, **15 failures**, waaronder `r1-het-regent-hard` en `r1-tijdens-wacht` (pass in plaats van onzeker) en de strikte T20-xfail als XPASS |
| GREEN T20 | `int01-green-v2.log` en `.xml` | 410 passed, 2 strikte xfails (T20-referentie), exit 0 |
| RED prompt | `prompt-red-v2.log` en `.xml` | 38 tests, **13 failures**: eindcontrole (4 contexten plus bronvariant), MECHANISME 2 (3 contexten plus aanwezigheid) en INT-01-kaart (4 contexten); de ESS-01-ongewijzigd- en lektermtests waren al groen |
| GREEN prompt | `prompt-green-v2.log` en `.xml` | 38 passed, exit 0 |
| Gerichte regressie | `v2-gericht-regressie.log` en `.xml` | **1320 tests, 0 failures**, 7 skipped (5 bestaande plus 2 strikte xfails), exit 0 |
| Integratie offline | `v2-integratie.log` en `.xml` | 28 tests, 0 failures, 1 skip |
| T24-ontwikkelregressie | `t24-ontwikkelregressie-v2.log` | 23/24 (T20 open) |
| Black | `v2-black.log`, `v2-black-2.log` | exit 0 |
| Ruff 0.16.5 (gepind) | `v2-ruff-0165.log` (1× ISC004 in de nieuwe test, hersteld), `v2-ruff-0165-2.log` | All checks passed |
| make lint | `v2-make-lint.log` | exit 0 |
| Diffs | `v2-diff-app-base.log`, `v2-diff-skills-base.log` (volledige kandidaat t.o.v. de base) en `v2-diff-app-delta.log`, `v2-diff-skills-delta.log` (t.o.v. kandidaat v1) | — |

## 5. Gewijzigde bestanden (SHA256)

App (base `e38ad957…`):

| Bestand | SHA256 |
|---|---|
| `src/domain/int01/zinsgrenzen.py` | `7f1216d3825caec0beca7f405a0931ecf9e7dbd26f8f41b3630e984665574bb0` |
| `src/services/prompts/modules/context_awareness_module.py` | `45e9964778ddeab1729fecb4a1d9ad5ef54dd3e69d5a23a055041fb8462fc105` |
| `src/services/prompts/modules/definition_task_module.py` | `416bc336bd734d6586324ba3e23c931ee6bde341f9a5e51eb949e44fb571c479` |
| `src/services/prompts/modules/json_based_rules_module.py` | `c5b464ee79e5bea853b6cf446468b95b63b49f380d92ba1f98cd4e9559cbeae9` |
| `tests/unit/validation/test_def770_herstel_zinsgrenzen.py` | `b858f645a7db4b1f86b6eddf40c57854deccb917afbdd640a8f12b11ab31ff7e` |
| `tests/unit/validation/test_def770_restherstel_zinsgrenzen.py` (nieuw) | `658b7ae559f3266f716fefec1cf607091dd0cef700a173c9928d487ed53a25ed` |
| `tests/unit/services/prompts/test_def770_restherstel_promptbehoud.py` (nieuw) | `99486f6167c2a776040600321c6b1b1bb1c0e5fe1250ef4f8e349c93e33681f6` |

Skills (base `a048806c…`):

| Bestand | SHA256 |
|---|---|
| `skills/definitie-toetsregels/reference.md` | `9e926cb560a8866c5c3ff141e60de1796985e6ef2657ad479efacc11580d41dc` |
| `skills/definitie-nederlandse-definities/SKILL.md` | `b94073cdcf109b408c0bc7caebffbe3beac3aad84d65d89ba819e9859ede4af2` |
| `skills/definitie-nederlandse-definities/reference.md` | `483c291fa854912af908b623369f336356024780d9b2fa080c8e089abc0b0ede` |

## 6. Resterende beperkingen

- **T20:** open dekkingsblokkade; beslissing tussen optie 1 en 2 nodig (§1).
- **Generatie:** promptdoorwerking is aangetoond; een effect op de generaties niet. Nodig is een nieuwe onafhankelijke effectmeting na de bronreview. De coördinator bereidt manifest, telling en eventueel budgetvoorstel voor.
- **Bekende beperkingen, door de reviewer als bestaand bevestigd:** meerwoordige labels en grenzen zonder leesteken (‘… uit het regent’). Geen waiver van mijn kant.
- **Productie-snippetlimieten (500/800):** een los onderwerp, bewust buiten dit herstel.
- **Nog te doen door anderen:** de bronreview door dezelfde Codex-reviewer, daarna de volledige unit-suite en de bundels door de coördinator.

Bronnen: `logs/def770-restherstel/astra-review-v1.md`, `claude-resultaat-v1.md`, `src/toetsregels/regels/ESS-01.json`, `analyse-prompt-G05-nieuw-v1.txt` (r162–163, r245, r269–272, r283–288), `effectproeven-vervolg-20260924-v1/g24-adjudicatie-v1.json`.
