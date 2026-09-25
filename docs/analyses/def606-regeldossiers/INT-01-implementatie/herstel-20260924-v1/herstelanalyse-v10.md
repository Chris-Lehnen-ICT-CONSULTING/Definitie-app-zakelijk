# DEF-770 — herstelanalyse v10 (eindproef-correctie v3, contract /4)

**Aanleiding:** `logs/def770-herstel/astra-eindproef-review-v2.md`, R1 (Important, fix-nu). R2/T23 en T17/T20 zijn gesloten en niet aangeraakt.

**Pogingen:** dit is de derde en laatste gerichte herstelpoging voor T18 (maximum 3). Een vierde uitzondering volgt niet. Resterende onzekerheid is hieronder concreet benoemd.

**Ongewijzigd:**
- `CONTRACTVERSIE` blijft `def770-int01/4`.
- Historische labels en de eindproef zijn niet opnieuw geëtiketteerd.
- v1–v9 zijn ongewijzigd.

**Basis:** HEAD `6c18ce71`. De herstelkopie van de v2-stand staat in `logs/def770-herstel/herstelkopie-eindproef-correctie-v3/`.

## Oorzaak

`_fragmentdeel` (v2) telde elke vorm zonder klinker als afkortingsfragment. Daardoor kregen `(Psst!)` en `(Brr!)` een zinsstructuur-pass zonder onzekerheidsdeel. De vorm `Psst` bewijst geen afkortingsfunctie. Hetzelfde geldt voor een losse letter (`(O!)`) en voor een bekende afkorting zonder haar punt (`(bijv!)`).

## Herstel (minimaal, generiek)

- `_fragmentdeel` telt nog maar twee soorten tokens als fragment:
  - een getal (`_GETAL`);
  - een bekende afkorting mét haar punt: functie `titel`, `verwijzing`, `mogelijk_zinslot` of `afkorting` volgens de bestaande lijsten en het bestaande patroon voor gestippelde afkortingen.
- Niet meer als fragment:
  - een vorm zonder klinker;
  - een losse letter (initiaal of lijstletter);
  - een afkorting zonder punt.
- `_classificeer_haakjesslot` krijgt het slotteken mee. Daardoor telt de punt van een slotafkorting (`st.)`) mee en een `!` of `?` niet.
- Een getal maakt een volgend onbekend woord geen eenheid.
- Er is geen blacklist voor uitroepen en er zijn geen nieuwe woordlijsten, parser of dependency.
- `_ZONDER_KLINKER` blijft alleen de T23-detectie van onzekerheid in de gewone hoofdlettergrens. Het is geen bewijs meer voor een pass.

## Testverwachtingen (besluitbinding: review-v2 R1)

| Geval | v2 | v3 |
|---|---|---|
| `(ca. 5 mm.)` (ontwikkeltest, geen proeflabel) | 0/0 | 0/1 |
| nieuw `(Psst!)`, `(Brr!)`, `(Psst.)`, `(Brr?)` | — | 0/1 |
| nieuw `(O!)` | — | 0/1 |
| nieuw `(bijv!)` | — | 0/1 |
| nieuw `(bijv.)`, `(max. 5 st.)` | — | 0/0 |
| bestaand `(o.a.)`, `(3.)`, `(max. 5 st.) per proef` | 0/0 | 0/0 |

**Transparante beperking:** `(ca. 5 mm.)` bleef in v2 alleen 0/0 door de aanname dat een vorm zonder klinker (of een woord na een getal) een eenheid is. Die aanname is onbewezen. Een onbekende eenheid in een afsluitend haakjesdeel wordt daarom doorverwezen (onzeker, nooit fail). Alleen eenheden die in de bestaande afkortingslijsten staan, zijn beschermd.

## Bewijs (logs onder `logs/def770-herstel/`)

- **RED** op de v2-bron: `eindproef-correctie-v3-red.log` en `.xml` — 267 tests, 7 failures, exit 1. Alle zeven zijn de nieuwe of aangepaste tegenhangers; de beschermingsgevallen slaagden al.
- **GREEN:** `eindproef-correctie-v3-green.log` en `.xml` — 267 tests, 0 failures, exit 0.
- **Black op het testbestand** (venv-Black): `eindproef-correctie-v3-black-test.log` — "1 file left unchanged", exit 0. De GREEN-run hoort dus bij de definitieve testtekst.
- **`make lint`** (ruff en black op `src/` en `config/`): `eindproef-correctie-v3-make-lint.log`, exit 0.
- **Niet door mij uitgevoerd** (vraagt goedkeuring): `/Users/chrislehnen/Projecten/Definitie-app/.venv/bin/ruff check tests/unit/validation/test_def770_herstel_zinsgrenzen.py`.
- **Diffs:**
  - ten opzichte van `6c18ce71`: `eindproef-correctie-v3-appdiff.patch`;
  - correctiedelta ten opzichte van de v2-stand: `eindproef-correctie-v3-correctiedelta-zinsgrenzen.patch` en `-test.patch`.
- **Skills:** geen wijziging door mij in deze ronde.

## Resterende onzekerheid (geen vierde uitzondering)

- Een haakjesdeel met iets anders dan getallen en bekende afkortingen met punt is bij een afsluitend slotteken altijd onzeker. Dat geldt ook voor gewone bepalingen die een lezer direct als bepaling herkent, zoals `(ca. 5 mm.)` en `(zie art. 3.)`. Dat is bewust conservatief.
- De bekende afkortingslijsten zijn niet uitgebreid. Een afkorting met klinker buiten de lijst (`afd.`, `gem.`) vóór een hoofdletter blijft in de gewone grens een zekere fail. Dat staat al als beperking in v9. Oplossen vraagt een woordenlijst of parser, en dat valt buiten het mandaat.

Geen effectclaim. Geen proefdata ingezien, geen generatiecalls.
