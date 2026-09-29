# ESS-05 — beperkt bewijscontract `ess05-bewijsregels/7` (DEF-768): delta op v6

**Status:** robuustheidsronde na de echte P1-rooktest. Geen appgarantie; het modelgedrag onder prompt /5 is niet getest (dat doet de P1-herhaling, na een expliciete start).

Dit is uitsluitend een delta. Alles wat hier niet staat, is gelijk aan [v6](ess05-bewijsregels-contract-v6.md). v6 blijft ongewijzigd als historie (sha256 `8825eebf9925c2850a18db58ac20443a3f9e26065c21e5feaf3d0d2254dd12c2`).

**Grondslag:** besluit Chris van 29-09-2026 (punten 1–4, alle vier akkoord) na de echte P1-run `logs/def768/echte-test-v1/echt-p1-v1` (samenvatting sha256 `203eafc6…`). Daarin gaven alle drie records ERROR:

| Record | Fout |
|---|---|
| 277 | `betekenisfout` |
| 365 | `schemafout`: `voorwaarden` ontbreekt |
| 278 | `kerndekking_onvolledig`: de ruis "Soort" en "[Bron n]" |

| Onderdeel | Versie |
|---|---|
| Regelversie | `/6` → `ess05-bewijsregels/7` |
| Prompt | `/4` → `ess05-interpretatie-prompt/5` (systeemprompt sha256 `fa7bb2651f8de1289631d08321b510394f63d6866de27ccdc58611d0bc0b73c5`) |
| Schema `ess05-interpretatie/3`, render `/2`, documentcontract `ess05/3`, regels (`pas_regels_toe`), lokale controle `ess05-local-verify/1` | ongewijzigd |

## Gewijzigd: ontbrekende `voorwaarden` (punt 1)

- Een antwoord zonder de sleutel `voorwaarden` telt als `voorwaarden: []`.
- Dat geldt alleen voor dit veld. Elk ander ontbrekend of onbekend veld blijft een `schemafout`.

## Gewijzigd: definitieruis geneutraliseerd (punt 2)

- `domain.ess05.definitieruis.neutraliseer_definitieruis` haalt vóór ESS-05 twee soorten ruis uit de tekst:
  - één categorie-voorregel aan het begin van de tekst;
  - elk bronlabel `[Bron n]`, inclusief de witruimte ervoor.
- De functie werkt op de definitie én op de buurdefinities. De enige plek is `contract.beoordelingsmateriaal`. Het model krijgt dus dezelfde tekst als de dekkings- en citaatcontrole.
- Vaste patronen (hoofdletterongevoelig; `<cat>` ∈ soort, proces, resultaat, exemplaar). Een voorregel telt alleen als hij een eigen regel is:
  - `- Ontologische categorie: <cat>`
  - `**Ontologische categorie: <cat>**`
  - `**<cat>**`
  - `<cat>`
- Er is geen vrije heuristiek.
- Inventaris van de echte database (read-only, 29-09, 183 records):

  | Variant | Records |
  |---|---|
  | `- Ontologische categorie: soort` | 19 |
  | `- Ontologische categorie: proces` | 3 |
  | `- Ontologische categorie: resultaat` | 1 |
  | `**Ontologische categorie: …**` | 1 |
  | `**<Cat>**` | 1 |
  | alleen `<Cat>` | 3 |
  | `[Bron n]` | 2 |

- De opgeslagen data blijft ongewijzigd. De vingerafdruk bindt de opgeslagen tekst; de materiaalhashes binden de geneutraliseerde tekst.

## Gewijzigd: herkomst van `buiten_kern` (punt 3)

- **Prompt /5 (3a).** `buiten_kern` bevat alleen kenmerken die de bedoelde betekenis of een bron van het doelbegrip aan het begrip toekent en die de definitie niet uitdrukt. Zonder zo'n betekenis of bron is `buiten_kern` leeg. Kenmerken uit een buurbeschrijving of uit eigen kennis horen er nooit in.
- **Vangnet in code (3b).** Een M-kenmerk waarvan het doelantwoord niet `bevestigd` is, wordt weggelaten in plaats van `betekenisfout` te geven. Ook alle antwoorden over dat kenmerk vallen weg.
  - Elke weglating krijgt een diagnostische notitie in `interpretation.notes`, in de vorm: `M1 (<kenmerk>: <waarde>) weggelaten: geen bevestiging in de doelbetekenis …`.
  - De overige kenmerken en antwoorden worden gewoon beoordeeld.

## Gewijzigd: eerlijke melding bij onbruikbare modeluitvoer (punt 4)

- Gaat een `ess05/3`-beoordeling mis op inhoudelijk onbruikbare modeluitvoer, dan geeft de evaluator `review_required`. De reden luidt: "De AI kon dit niet betrouwbaar automatisch beoordelen; beoordeel handmatig. Reden: <korte reden> (<type>)." Daarbij hoort een handmatige vervolgstap.
- Het document zelf blijft `status: error` met het fouttype. De samenvatting draagt `unusable: true`. De UI toont "AI-beoordeling niet bruikbaar" in plaats van "technisch mislukt".
- Onbruikbaar (vaste tabel `contract._ONBRUIKBAAR`):
  - `malformed_response`;
  - alle geldigheidsfouten: `schemafout`, `citaatfout`, `onderwerpfout`, `contextfout`, `kerndekking_onvolledig`, `doeldekking_onvolledig`, `betekenisfout`, `buiten_bereik`, `inconsistent` en `dekking_ontbreekt`;
  - een lokale controle die niet `supported` geeft;
  - een onbruikbaar controleantwoord.
- **Fail-closed:** elk ander type blijft technisch en dus `error` / "Technisch probleem". Dat zijn `timeout`, `rate_limit`, `connection`, `unknown`, `truncated_response`, `refusal`, `input_truncated`, buren-lookup en teller.
- ESS-05 blijft zonder cijfer (`no_score`).

## §7: aanvulling op de garantietabel

| Wat | Hoe | Garantie |
|---|---|---|
| Voorregel en `[Bron n]` weg vóór model en controle | vaste patronen | deterministisch, alleen voor de geïnventariseerde vormen |
| M-kenmerk zonder bevestigde doelbetekenis telt niet mee | vaste code | deterministisch |
| `buiten_kern` komt echt uit doelbetekenis of doelbron (en niet uit een buur) | prompt + doelantwoord | **niet bewezen**: het vangnet toetst de toestand, niet de herkomst van het bewijs |
| Onbruikbare uitvoer ≠ storing | vaste tabel, fail-closed | deterministisch |

## Bekende grenzen

- **`buiten_bereik` en kerndekking (278).** Een definitiedeel onder `buiten_bereik` telt niet mee in de kerndekking, en een niet-lege `buiten_bereik` is zelf al een fout. De echte 278-respons blijft daardoor onbruikbaar, maar toont nu eerlijk `review_required`. Wijziging vraagt een apart besluit.
- **`input_truncated`** blijft technisch (`error`): het is een invoerlimiet, geen modeluitvoer.
- Nieuwe ruisvormen buiten de inventaris worden niet herkend. Dat is bewust: er is geen heuristiek.

**Historie.** R18 is gepind op v6 / prompt /4 en wordt, net als R16 en R17, door de runner fail-closed geweigerd. De R18-invoer, -uitvoer, -freezes en -grootboeken zijn ongewijzigd.
