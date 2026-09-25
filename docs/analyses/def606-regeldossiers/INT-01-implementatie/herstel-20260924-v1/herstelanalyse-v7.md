# DEF-770 — herstelanalyse v7 (contract /3: punt + kleine letter altijd onzeker)

Leidend zijn `conservatieve-beoordeling-besluit-v1.md` en de actuele afbakening `conservatieve-beoordeling-uitwerking-v2.md`. Aanleiding is `logs/def770-herstel/astra-conservatief-review-v1.md`, R1 (Important): `de hele dag`, `elke dag` en `deze week` zijn lidwoordgroepen die geen onderwerp bewijzen, maar gaven `fail`. v1–v6 blijven ongewijzigd.

## Wijziging

- **`src/domain/int01/zinsgrenzen.py`**
  - `_classificeer_punt`: een punt gevolgd door een kleine letter (buiten de bestaande afkortings-, getal- en initiaalfuncties) is altijd `onzeker`. De positieve grammaticaheuristiek voor die tak is verwijderd. Er is geen blacklist en geen nieuwe miniheuristiek.
  - **Verwijderd,** omdat ze alleen in die tak gebruikt werden (gecontroleerd met `git grep` in `src/` en `tests/`: geen andere verwijzingen):
    - `_eigen_onderwerp_en_persoonsvorm`
    - `_bewezen_persoonsvorm`
    - `_onderwerp_herkend`
    - `_VOLLEDIG_WOORD`
    - `_INFINITIEF_HOMOGRAAF`
    - `_WERKWOORDELIJKE_VORM`
    - `_ONDERWERP_LIDWOORDEN`
    - `_GEEN_ONDERWERPSBEGIN`
    - `_BIJZIN_OF_INFINITIEF`
  - **Behouden,** omdat ze nog nodig zijn voor de citaatslotroute uit R2/R3:
    - `_PERSOONSVORMEN`
    - `_ONDERSCHIKKEND`
    - `_VOORZETSELS`
    - `_LIDWOORDEN`
    - `_ZEKER_ZINSBEGIN`
    - `_woorden_tot_zeker_zinsbegin`
    - `_korte_slotgroep`
    - `_open_bijzin`
  - De docstrings en commentaren van die constanten zijn aangepast aan hun resterende functie.
  - `CONTRACTVERSIE` blijft `def770-int01/3`: de kandidaat is niet vrijgegeven, geactiveerd of beproefd (uitwerking-v2).
- **`tests/unit/validation/test_def770_herstel_zinsgrenzen.py`:** de verwachtingen zijn aangepast (zie hieronder).
- **Skills:** in `definitie-toetsregels/reference.md` noemt de `/3`-toelichting nu dat een mogelijke grens bij een punt met kleine beginletter in de app altijd open blijft. `nederlandse-definities/reference.md` is ongewijzigd, want daar staat geen app-zekerheidsclaim. Bundels worden later door root herbouwd.

## Automatische uitkomst onder /3 (exact)

**Zekere fail**
- Een zinseindteken gevolgd door witruimte en een hoofdletter of cijfer. Deze tak is ten opzichte van v6 niet gewijzigd.
- Uitgezonderd (die blijven onzeker, zoals voorheen):
  - na een bekende afkorting, titel of initiaal volgens de bestaande regels;
  - binnen haakjes;
  - binnen een ingesloten citaat.

**Zinsstructuur-pass** (de regel blijft `review_required`): alleen een ononderbroken formulering zonder zekere of onzekere kandidaat. Een voortzetting na een citaatslot telt alleen met de bewezen vormen uit r4 (korte slotgroep; open bijzin `die de/een` plus woord).

**Altijd onzeker** (met passage, positie en reden):
- elke punt met een kleine beginletter erna, dus ook een voor een mens duidelijke tweede zin;
- onbekende afkortingen;
- een onbewezen voortzetting of onvolledige woordgroep na een citaat;
- een label met dubbele punt;
- een beletselteken met vervolg;
- lijst- of alineastructuur zonder inleidend teken.

Nooit een volledige INT-01-pass.

## Gewijzigde testverwachtingen (besluitbinding: uitwerking-v2)

| Geval | v6 | v7 |
|---|---|---|
| `ingen-meervoud` (`bundelingen. de controle blijft vereist`) | 1 zeker | 0 zeker, 1 onzeker |
| `heid-woord` (`veiligheid. het toezicht is vereist`) | 1 zeker | 0 zeker, 1 onzeker |
| `r1-onderwerp-lidwoord`, `r4-lidwoordgroep` (`regeling. de controle blijft vereist`) | 1 zeker | 0 zeker, 1 onzeker |
| `r3-verleden-meervoud` (`regeling. de controles werden uitgevoerd`) | 1 zeker | 0 zeker, 1 onzeker |
| `c3-lidwoord-met-pp` | 1 zeker, 1 onzeker | 0 zeker, 2 onzeker |
| nieuw `c4-tijdsbepaling-de/elke/deze` (review-repro's) | — (was fail) | 0 zeker, 1 onzeker |
| nieuw `c4-hoofdletter-fail` (`regeling. De controle blijft vereist.`) | — | 1 zeker |
| nieuw `c4-ononderbroken` (`regeling die elke dag wordt toegepast`) | — | 0, 0 (zinsstructuur-pass) |
| `test_zekere_kleine_letter_grens_blijft_met_lidwoordgroep` | fail | vervangen door `test_kleine_letter_na_punt_altijd_onzeker_met_passage_en_positie` (twee teksten: onzeker, positie op de punt, reden "kleine letter", regel `review_required`) |
| `ZEKER_FAIL` (service beide laadpaden, opslag, oude-versietest) | kleine-lettertekst | gewone duidelijke grens `strook voor tijdelijke bundeling. De controle blijft vereist.` → `fail`; plus `test_hoofdlettergrens_blijft_zekere_fail` |

Historische normatieve labels zijn niet gewijzigd (T24 normatief fail, automatisch onzeker). Ongewijzigd zijn:
- T15, T17, T19, T22, T23;
- R2/R3-regressies;
- de `/1`- en `/2`-niet-actueel-tests;
- `test_def770_int01_zinsgrenzen.py`: niet aangepast en groen.

## Bewijs (logs onder `logs/def770-herstel/`)

- **Herstelkopie:** `herstelkopie-conservatief-v2/` (zinsgrenzen.py, twee testbestanden, beide skillreferenties), vijf bestanden bytegelijk gecontroleerd met `cmp`.
- **RED** op de ongewijzigde bron: `conservatief-v2-red.log` en `.xml` — 191 tests, 11 failures, exit 1.
- **GREEN:** `conservatief-v2-green.log` en `.xml` — 191 tests, 0 failures, exit 0.
- **Lint:** `conservatief-v2-make-lint.log` — ruff en black op `src/`, exit 0.
- **Diffs:**
  - correctiedelta ten opzichte van de reviewstand: `conservatief-v2-correctiedelta-zinsgrenzen.patch` en `conservatief-v2-correctiedelta-test.patch`;
  - volledige diff ten opzichte van HEAD: `conservatief-v2-appdiff.patch`;
  - skills: `conservatief-v2-skillsdiff.patch`.
- **Niet door mij uitgevoerd** (vraagt goedkeuring): ruff en black op het testbestand. Geen brede gate.

## Resterende beperkingen

- De automatische fail-dekking is beperkt tot duidelijke hoofdletter- en cijfergrenzen. Tweede zinnen met kleine beginletter worden altijd doorverwezen. Dat is de bewuste conservatieve grens van de huidige techniek (uitwerking-v2), geen fout.
- De afkortings- en initiaalregels (lijst plus onzekerheid) en de citaatslotroute (R2/R3) zijn ongewijzigd.

Geen effectclaim en geen nieuwe proefdata ingezien.
