# DEF-770 — herstelanalyse v6 (contract def770-int01/3, conservatieve beoordeling)

Leidend: `conservatieve-beoordeling-besluit-v1.md` (Chris, richting 1, 24 september 2026). Dit is een contractbesluit en geen vierde herstelpoging binnen de verworpen aanname. v1–v5 blijven ongewijzigd als bewijs. Basis-HEAD: `1c879427b729c6aaa26f830565a83ea55d6a2250`.

## Wijziging

- **`src/domain/int01/zinsgrenzen.py`**
  - `_onderwerp_herkend` kent nog maar één positief patroon: de lidwoordgroep. Het r4-patroon P2 is verwijderd (besluit punt 3). Dat was "één woord met een eigen voorzetselgroep", dat berustte op de aanname van grammaticaal correcte invoer.
  - `CONTRACTVERSIE` gaat van `def770-int01/2` naar `def770-int01/3` (punt 5).
  - Docstrings zijn afgestemd.
  - Er is geen adverbiumlijst, proefwoordlijst of corpuswhitelist toegevoegd.
- **`tests/unit/validation/test_def770_herstel_zinsgrenzen.py`:** de verwachtingen zijn aangepast met besluitbinding (zie hieronder).
- **Skills:** `skills/definitie-toetsregels/reference.md` verwijst nu naar `/3` en vat het beleid samen. `nederlandse-definities/reference.md` noemt geen versie en spreekt `/3` niet tegen, dus die is ongewijzigd. Bundels worden later door root herbouwd.
- **Ongewijzigd:** promptbuilders, JSON, schema, opslag- en weergavecode. De opslagbinding werkt met de bestaande contractvergelijking.

## Patroonbereik onder /3 (exact)

**Zekere fail (tweede zin)** alleen bij:
1. `.`, `?` of `!` gevolgd door witruimte en een hoofdletter of cijfer, buiten een ingesloten citaat of haakjes, en niet na een bekende afkorting, initiaal of titel. Dit gedrag is ongewijzigd.
2. Een punt met een kleine letter erna, als alle volgende voorwaarden gelden:
   - het woord vóór de punt eindigt op een productief achtervoegsel voor zelfstandige naamwoorden (`-ing`, `-heid`, `-schap`, `-iteit`, `-tie`, `-isme`, met meervoud);
   - het vervolg begint met een lidwoordgroep (`de/het/een/deze/dit/elke/ieder/iedere/alle` plus ten minste één woord);
   - daarna volgt een ondubbelzinnig vervoegde persoonsvorm uit de gesloten lijst, met een aanvulling erachter;
   - er staat geen bijzin- of infinitiefmarkering vóór die persoonsvorm, geen `te` direct ervoor en geen deelwoordvorm.

**Zekere zinsstructuur-pass** (onderdeel `zinsstructuur: pass`, regel blijft `review_required`) alleen als geen enkele kandidaat een zekere of onzekere grens oplevert. Voortzetting na een citaatslot telt alleen met de bewezen vormen uit r4:
- een volledige korte slotgroep;
- na een open bijzin (`die de/een` plus woord): het slotwerkwoord of een vervolg dat met een voorzetsel begint.

**Bewust onzeker (`review_required`, met passage, positie en reden):**
- een kaal woord vóór de persoonsvorm, met of zonder voorzetselgroep (`opnieuw wordt …`, `toezicht op naleving is …`, **oude T24** `controle volgens zqv. blijft vereist`);
- een onbekende afkorting;
- een persoonsvorm vooraan in het vervolg;
- een infinitief-homograaf;
- een persoonsvorm achteraan;
- een onbewezen voortzetting of onvolledige woordgroep na een citaat;
- een label met dubbele punt, een beletselteken met vervolg, een lijst zonder inleidend teken, een alinea-overgang.

Nooit een volledige INT-01-pass: compactheid en begrijpelijkheid blijven altijd open.

## Gewijzigde testverwachtingen (besluitbinding)

| Test | Onder /2 | Onder /3 | Grond |
|---|---|---|---|
| `test_segmentatie[T24-automatisch-onzeker-onder-3]` | 1 zeker, 1 onzeker | 0 zeker, 2 onzeker | Besluit punt 3. Het normatieve fail-label van T24 in het historische corpus blijft ongewijzigd; alleen de automatische dispositie is nu doorverwijzing. |
| `test_t24_onder_contract_3_onzeker_met_passage_en_positie` (vervangt `test_t24_grens_en_passage`) | zekere grens | onzekere grens bij `bundeling.` met positie en reden; regel `review_required`, geen zinsstructuur-pass | punt 2 en 3 |
| `test_service_uitkomst_beide_laadpaden[T24]` | `fail` | `review_required` met `zinsgrens_onzeker_1/2` | punt 3, beide laadpaden |
| `test_opslag_en_teruglezen[T24]` | `fail` | `review_required` | punt 3 |
| `c3-woord-met-pp` (was `r4-woord-met-pp`) | 1 zeker | onzeker | punt 3 |
| nieuw: `c3-bijwoord-met-pp` (`opnieuw volgens protocol wordt toegepast`) | zeker (vals) | onzeker | punt 3; restgrens uit v5 opgelost |
| nieuw: `c3-lidwoord-met-pp`, `ZEKER_FAIL`, `test_zekere_kleine_letter_grens_blijft_met_lidwoordgroep`, servicegeval en opslaggeval `zeker-fail` | — | `fail` | punt 4: zinvolle zekere fail blijft |
| `test_contractversie_is_3_na_conservatief_besluit` | `!= /1` | `== /3` | punt 5 |
| `test_uitkomst_onder_oude_contractversie_geldt_niet_als_actueel` | alleen `/1` | `/1` en `/2` × T24 en zeker-fail: niet toepasbaar, weergave alleen `tekstbinding`, volgende schrijfactie geeft een verse `/3` met historie | punt 5, bestaande herbeoordelingsroute |

Ongewijzigd groen, dus behouden:
- R2/R3-regressies (citaatslot, IndexError);
- T15, T17, T19, T22, T23;
- zekere pass-gevallen (`zinsstructuur: pass` bij T15, T17, T19);
- alle gevallen in `test_def770_int01_zinsgrenzen.py`.

## Bewijs (logs onder `logs/def770-herstel/`)

- **Herstelkopie:** `herstelkopie-conservatief-v1/` (zinsgrenzen.py, twee testbestanden, toetsregels-reference), vier bestanden bytegelijk gecontroleerd met `cmp`.
- **RED:** `conservatief-v1-red.log` en `.xml` — beide zinsgrens-testbestanden, 184 tests, 11 failures, exit 1.
- **GREEN:** `conservatief-v1-green.log` en `.xml` — 184 tests, 0 failures, exit 0.
- **Lint:** `conservatief-v1-make-lint.log` — ruff en black op `src/`, exit 0.
- **Diffs:** `conservatief-v1-appdiff.patch` (ten opzichte van HEAD) en `conservatief-v1-skillsdiff.patch`.
- **Niet door mij uitgevoerd** (vraagt goedkeuring, niet omzeild): de bredere set INT-01-contracttests (opslag, keten, promptdoorwerking, UI-binding, golden) en ruff/black op het testbestand. Zie het eindrapport voor de exacte commands.

## Resterende beperkingen

- De dekking van zekere fail bij een kleine beginletter is bewust smal. Een echte tweede zin met een kaal onderwerp of een onderwerp zonder lidwoord (bijvoorbeeld een eigennaam) wordt doorverwezen. Dat is geen fout onder /3, maar kost automatische dekking. De nieuwe T24 meet die dekking vooraf verzegeld (besluit, Uitvoering en bewijs).
- De lidwoordgroep veronderstelt dat `de/het/een …` een onderwerp opent. `het` kan ook een voornaamwoord zijn. In `het` plus woord plus persoonsvorm met aanvulling is dat onschadelijk, maar het blijft een vormheuristiek zonder taalgarantie.
- Het achtervoegselbewijs voor een volledig woord en de gesloten persoonsvormlijst zijn ongewijzigd uit v2–v4 overgenomen.

Geen effectclaim en geen nieuwe proeven of betaalde calls.
