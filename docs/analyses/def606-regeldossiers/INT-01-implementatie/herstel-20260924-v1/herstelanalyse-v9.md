# DEF-770 — herstelanalyse v9 (eindproef-correctie v2, contract /4)

Aanleiding: `logs/def770-herstel/astra-eindproef-review-v1.md`, twee Important-bevindingen, beide fix-nu. Dit is de tweede gerichte herstelpoging (maximaal drie).

T17/T20 en de /4-binding zijn gesloten en niet opnieuw ontworpen. `CONTRACTVERSIE` blijft `def770-int01/4`, omdat /4 nog niet gepubliceerd is. Historische labels, de proefset en de resultaten zijn niet gewijzigd. v1–v8 zijn ongewijzigd. Basis: HEAD `6c18ce71`. Herstelkopie van de v1-correctiestand: `logs/def770-herstel/herstelkopie-eindproef-correctie-v2/`.

## R1 — T18: vals zinsstructuur-pass bij haakjesslot

**Oorzaak.** Onder de v1-correctie golden twee dingen als bewijs tegen een zelfstandige zin:
- een haakjesdeel van één woord, zoals `(Stop!)` en `(Wacht.)`;
- een bekende slotafkorting, zoals `(De registratie sluit in dec.)`.

Geen van beide bewijst dat. Een imperatief kan één woord zijn, en een afkortingspunt kan ook een zin afsluiten.

**Herstel.**
- `_gesloten_haakjesdeel` levert voor elk slotteken dat direct een haakjesdeel sluit de inhoud op. Er geldt geen minimum aantal woorden en het maakt niet uit wat er buiten de haakjes volgt.
- `_classificeer_haakjesslot` geeft altijd `onzeker`, met passage en positie. De enige uitzondering: het haakjesdeel bestaat geheel uit getallen, bekende afkortingen of vormen zonder klinker (`_fragmentdeel`, bijvoorbeeld `(max. 5 st.)`, `(o.a.)`, `(3.)`, `(ca. 5 mm.)`). Zo'n fragment bevat geen woord dat een zin kan dragen.
- Er is geen lijst met imperatieven of maandnamen. `dec` blijft een bekende afkorting, maar telt alleen als fragment wanneer het haakjesdeel verder ook alleen uit fragmenten bestaat.

**Gewijzigde verwachtingen** (besluitbinding: reviewbevinding R1):
- `(onder leiding van prof.)` en `(sic!)`: van 0/0 naar 0/1.
- Nieuw:
  - `(Stop!)` en `(Wacht.)`: 0/1;
  - `(De registratie sluit in dec.)`, met en zonder vervolg: 0/1;
  - de beschermingsgevallen `(o.a.)`, `(3.)` en `(ca. 5 mm.)`: 0/0;
  - bestaand: `(max. 5 st.) per proef` en `(lengte 2.5 cm)`: 0/0.

## R2 — T23: hoofdletterbeperking

**Oorzaak.** `_ZONDER_KLINKER` herkende alleen kleine letters. Daardoor gaven `Chr. Huygens`, `Nvr. Nieuwe` en `NVR. Nieuwe` een zekere fail.

**Herstel.** De regex is hoofdletterongevoelig (`re.IGNORECASE`). Een vorm van twee of meer letters zonder klinker (a, e, i, o, u, y) vóór een punt met een hoofdletter of cijfer erna is onzeker, ongeacht de schrijfwijze. De acroniemredenering uit v8 is vervallen. Er is geen corpuswhitelist.

**Gewijzigde verwachtingen:**
- `NVR. Nieuwe …`: van 1/0 naar 0/1.
- Nieuw: `Chr. Huygens`, `chr. Huygens` en `Nvr. Nieuwe …`: 0/1.
- Tegenhangers met een klinker blijven zeker fail: `regeling. Nieuwe`, `Regeling. Nieuwe` en `rit. Nieuwe`.

## Tests en bewijs (logs onder `logs/def770-herstel/`)

- **RED** op de v1-correctiebron: `eindproef-correctie-v2-red.log` en `.xml` — 259 tests, 17 failures, exit 1. Alle failures zijn nieuwe of gewijzigde verwachtingen, en de beschermingsgevallen slaagden al.
- **GREEN:** `eindproef-correctie-v2-green.log` en `.xml` — 259 tests, 0 failures, exit 0.
- **Black op het testbestand** (venv-Black): `eindproef-correctie-v2-black-format.log` — 1 file reformatted, exit 0. Een tweede run (`eindproef-correctie-v2-black-herhaling.log`) meldt "1 file left unchanged", exit 0. `black --check` en `ruff check` op het testbestand vroegen goedkeuring en zijn niet door mij gedraaid.
- **GREEN na opmaak:** `eindproef-correctie-v2-green-definitief.log` en `.xml` — 259 tests, 0 failures, exit 0.
- **`make lint`** (ruff en black op `src/` en `config/`): `eindproef-correctie-v2-make-lint.log`, exit 0.
- **Diffs:**
  - volledig ten opzichte van `6c18ce71`: `eindproef-correctie-v2-appdiff.patch`;
  - correctiedelta ten opzichte van de v1-stand: `eindproef-correctie-v2-correctiedelta-zinsgrenzen.patch` en `-test.patch`.
- **Skills:** geen nieuwe wijziging; de versieregel /4 uit v1 blijft staan.

## Beperkingen

- Elk haakjesdeel met minstens één gewoon woord en een afsluitend slotteken is nu onzeker. Daarvoor is gekozen, omdat er zonder woordsoortkennis geen positief bewijs voor een bepaling is.
- Een woord met een klinker vóór een punt met hoofdletter erna blijft een zekere fail. Een onbekende afkorting met een klinker (bijvoorbeeld `afd.` buiten de lijst, of `gem. De …`) wordt dus nog steeds als zekere grens gezien. Dit is niet op te lossen zonder woordenlijst of parser, en valt daarom buiten dit mandaat.
- Geen effectclaim. Ik heb geen proefdata ingezien en geen generatiecalls gedaan.
