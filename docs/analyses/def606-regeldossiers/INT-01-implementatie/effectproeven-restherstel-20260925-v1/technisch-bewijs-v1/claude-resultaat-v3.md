# DEF-770 restherstel — resultaat Claude-uitvoerder (v3, beleidsbinding T20)

25 september 2026. Claude Code CLI, sessie `442a98fb-a377-403f-996e-433cf4a664fc`.

Dit is een expliciet geautoriseerde beleidsafronding, geen derde heuristische correctiepoging. Er is geen product-, domein- of promptcode gewijzigd.

Leidend: `docs/analyses/def606-regeldossiers/INT-01-implementatie/herstel-20260924-v1/restherstel-titelbesluit-v1.md`. Chris: “Ja, deze twijfelgevallen inhoudelijk beoordelen (advies)”. Daarnaast `logs/def770-restherstel/astra-review-v2.md`, volledig gelezen.

Niet gedaan:
- agents, reviewers of extra CLI-sessies gestart;
- commits, pushes of betaalde calls;
- de nieuwe maker of de nieuwe proefset gelezen;
- de volledige suite herhaald.

Vorige rapporten v1 en v2 blijven ongewijzigd.

## Beleidsscope

**Wat het besluit regelt.** Een titel of citaat met interne zinseindpunctuatie, gevolgd door een naamwoordelijke voortzetting, gaat automatisch naar `review_required` als de samenhang afhangt van woordrollen in een uitgebreide voorzetselgroep, zoals een lidwoord met een extra woord vóór de kern (‘van de bijbehorende opdracht’).
- Dit is een beperking van de automatische dekking, geen normatief verbod.
- De normatieve referentie van T20 blijft **pass**.
- Het historische label en de oude 23/24-uitslag blijven onaangeroerd.
- Er komt geen retroactieve 24/24-claim.
- Bestaande onderbouwde grenzen houden hun beoordeling.

**Runtime.** Ongewijzigd ten opzichte van kandidaat v2; die gaf dit gedrag al (astra-review-v2: `_voorzetselgroepen` is AST-gelijk aan de base). Contract `def770-int01/7` blijft geldig.

## Wijzigingen

1. **`tests/unit/validation/test_def770_restherstel_zinsgrenzen.py`**
   - `T20_OPEN` en de twee strikte xfails zijn verwijderd.
   - Nieuw: `REFERENTIE_NORMATIEF = {"T20": "pass"}` en `BESLUIT_AUTOMATISCH = {"T20": "review_required"}`, met trace naar restherstel-titelbesluit-v1.
   - `test_a_t20_besluitverwachting_en_normatieve_referentie` leest de verzegelde `t24-adjudicatie-v1.json` (alleen lezen) en toetst:
     - dat de normatieve referentie `pass` is, dus zichtbaar en onveranderd;
     - dat de automatische status `review_required` is;
     - dat er geen zinsstructuur-pass is en een onzekere grens als onderdeel.
   - Het segmentatiegeval `a-T20-huidig` heet nu `a-T20-besluit` (0/1). De service-verwachting (beide laadpaden) draagt een besluittrace in het commentaar.
   - Docstring bijgewerkt.
   - SHA256 `9a5635a15b7e942dda8feb7f5b6546b74a554197dd2ebbb39025a3b39c71e610`
2. **Skills `skills/definitie-toetsregels/reference.md`**
   - De T20-zin is uitgelijnd op het expliciete beleid: automatisch inhoudelijke beoordeling bij woordrollen in een uitgebreide voorzetselgroep, ook als het normatief één formulering is.
   - Het is uitdrukkelijk een dekkingsbeperking en geen verbod. Een ontbrekende persoonsvorm, een woorduitgang of veronderstelde grammaticale correctheid geeft geen extra zekerheid.
   - SHA256 `d053f336a0d8c02a5d653122538e60574d946210f2bdf8772f4b87569ccaea2e`

Diffs ten opzichte van herstelkopie-v3: `v3-diff-app.log` (109 regels) en `v3-diff-skills.log` (11 regels). Er zitten alleen deze beleidswijzigingen in.

## Bewijs dat productcode en oude proef ongewijzigd zijn

`herstelkopie-maken-v3.py voor/na`: 18 SHA256-hashes vóór en na vergeleken. Uitkomst: **18/18 ONGEWIJZIGD** (`v3-ongewijzigd.log`, nulmeting `herstelkopie-v3/hashes-voor.json`). De vergelijking omvat:
- **domein en evaluator:** `zinsgrenzen.py`, `opslag.py`, `sentence_boundary.py`;
- **promptmodules:** de drie modules;
- **tests:** `test_def770_herstel_zinsgrenzen.py`, `test_def770_vervolg_zinsgrenzen.py` en `test_def770_restherstel_promptbehoud.py`;
- **NL-definities-skill:** `SKILL.md` en `reference.md`;
- **verzegelde vervolgproef:** `t24-gevallen`, `t24-adjudicatie`, `t24-referentie-A` en `-B`, `t24-resultaat-nieuw`, `t24-vergelijking` en `t24-rapport`.

De T24-ontwikkelregressie blijft **23/24** (`t24-ontwikkelregressie-v3.log`). T20 wijkt af van de normatieve pass volgens het besluit; dat is geen nieuwe claim.

## Gerichte tests en lint (`logs/def770-restherstel/`)

| Stap | Log | Uitkomst |
|---|---|---|
| Classifier, service (beide laadpaden), opslag, keten, editorbinding | `v3-beleid-gericht.log` en `.xml` | 440 tests, 0 failures, 0 skips/xfails, exit 0 |
| Na importsortering (herhaling) | `v3-beleid-gericht-2.log` en `.xml` | 440 tests, 0 failures, exit 0 |
| Black | `v3-black.log`, `v3-black-2.log` | exit 0 |
| Ruff 0.16.5 (gepind) | `v3-ruff-0165.log` (I001 importvolgorde, hersteld), `v3-ruff-0165-2.log` | All checks passed |
| make lint | `v3-make-lint.log` | exit 0 |

De volledige unit-suite van de coördinator op kandidaat v2 blijft geldig voor de ongewijzigde productcode. Alleen dit testbestand en de skilltekst zijn nieuw.

## Rest

- De coördinator bouwt de bundel voor `definitie-toetsregels` opnieuw.
- Beide gewijzigde bestanden gaan terug naar dezelfde Codex-reviewer.
- Nieuwe onafhankelijke referenties gebruiken dit aangevulde contract vóór de appuitvoering.
- Het generatie-effect blijft onbewezen tot een nieuwe meting.
