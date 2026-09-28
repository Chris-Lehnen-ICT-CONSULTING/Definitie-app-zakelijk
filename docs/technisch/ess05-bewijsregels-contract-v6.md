# ESS-05 — beperkt bewijscontract `ess05-bewijsregels/6` (DEF-768): delta op v5

**Status:** mechanisme voor een begrensde proef, niet actief in de standaard ESS-05-keten. Geen appgarantie.

Dit is uitsluitend een delta. Alles wat hier niet staat, is gelijk aan [v5](ess05-bewijsregels-contract-v5.md). v5 blijft ongewijzigd als historie (sha256 `a44e2b1c64d9208f9a5def5c791c16cd7e996b94ee0dd063faa8d14eff096116`).

**Grondslag:** `reports/DEF-768-AI-20260928-R17/oorzakenonderzoek-ess05-v1.md` §5, optie O2 (akkoord Chris, 28-09-2026). Plan: `docs/plans/2026-09-28-DEF-768-ess05-bewijseenheden-plan-v1.md`, deel A. In R17 strandden juiste interpretaties op de bewijsvorm: het letterlijk kopiëren van brontekst en de dubbelzinnige zin "precies één keer".

| Onderdeel | Versie |
|---|---|
| Regelversie | `/5` → `ess05-bewijsregels/6` |
| Schema | `ess05-interpretatie/2` → `ess05-interpretatie/3` |
| Prompt | `/3` → `ess05-interpretatie-prompt/4` |
| Render, regels (`pas_regels_toe`), kerntekstdekking, `dekking_ontbreekt`, lokale controle (R15-gepind) | ongewijzigd |

## Gewijzigd: bewijs via eenheden

- De app deelt elk bewijsmateriaal (bronnen, bedoelde betekenis, buurbeschrijvingen) op in **eenheden**: zinnen, genummerd `U1`, `U2`, … in de volgorde van de prompt (gesorteerd materiaal-ID). Een zin loopt tot en met `.`, `!` of `?` gevolgd door witruimte, of tot het einde van de tekst; een `;` splitst niet.
- **Definitie en context hebben geen eenheden.** Ze zijn dus nooit als bewijs voor een antwoord te noemen.
- Een antwoord en een deelgroep noemen in `citaten` een lijst eenheidsnummers (`["U3"]`), geen letterlijke tekst. Een onbekend nummer of een ander type (zoals een citaatobject) is een `citaatfout`. Een eenheid uit materiaal dat niet bij het onderwerp hoort, is een `onderwerpfout` (toegestaan materiaal per onderwerp: ongewijzigd).
- De validator zet de nummers om naar de bestaande `Citaatverwijzing`. Controlepakketten en weergave veranderen daardoor niet van vorm.
- **Hergebruik is toegestaan.** Eén eenheid mag bij meerdere antwoorden staan; binnen één antwoord telt een dubbel nummer één keer.
- **Positieve toestanden** (`bevestigd`, `ontkend`, `gemengd`, `deels`) vereisen ≥ 1 eenheid. `onbesproken` noemt er geen.
- **Ongewijzigd letterlijk:** de kern citeert de definitie letterlijk, met precies één vindplaats per citaat. `buiten_bereik` citeert letterlijk (`citaat in tekst`).

## Gewijzigd: onderwerpbinding (negatief anker)

- Noemt een bron (`source:…`) meer dan één geregistreerd begrip, dan weigert de app een eenheid die een **ander** begrip noemt en het eigen onderwerp niet (`onderwerpfout`). Dat gebeurt hoofdletterongevoelig, op hele woorden, zonder prefixmatching (v5).
- **Vervallen:** het positieve anker uit v5, dat vereiste dat het citaat de eigen naam bevat.
- Een eenheid **zonder** begripsnaam gaat door naar de semantische controle. Een eenheid **met beide** namen gaat ook door.

## Gewijzigd: prompt /4

- Paragraaf 5 heet nu "bewijs". Het materiaal (behalve definitie en context) staat genummerd in de prompt als `[Un] <zin>`. Positieve antwoorden noemen minstens één eenheidsnummer. Hergebruik staat er expliciet: "Hetzelfde nummer mag bij zoveel antwoorden staan als het draagt". Een eenheid die alleen een ander begrip noemt, is geen bewijs. Wijst een eenheid terug naar een eerdere, dan noemt het model beide.
- Kern (paragraaf 1): een letterlijk citaat dat maar één keer in de definitie voorkomt. De dubbelzinnige zin "precies één keer" (R17) is verwijderd.
- Deelgroepen (paragraaf 3) noemen eenheden. Het schema toont `"citaten": ["U<n>"]`.

## Evaluatie (geen productiepad)

- `bewijsdiagnose(ruw, invoer)` verzamelt alle bewijsfouten per antwoord en deelgroep, zonder bij de eerste te stoppen. Dit dient alleen voor de evaluatie van een proef. Het productiepad blijft `valideer_interpretatie`: de eerste fout geeft `error`.
- `Ess05BewijsregelService.interpreteer()` voert alleen stap 1 en 2 uit (interpretatie en geldigheid). `beoordeel()` gebruikt dezelfde stap en is verder ongewijzigd.

## §7: aanvulling op de garantietabel

| Wat | Hoe | Garantie |
|---|---|---|
| Eenheid bestaat en komt uit materiaal dat bij het onderwerp hoort | vaste code | deterministisch |
| Eenheid die alleen een ander begrip noemt, is geen bewijs (bron met meerdere begrippen) | vaste code | deterministisch, alleen als tekstanker |
| Toeschrijving en draagkracht van een eenheid **zonder** begripsnaam (bijv. een inleidende zin of een losse teruggaafzin) | geïsoleerde LLM-controle | **niet bewezen** |
| Een eenheid die het kenmerk werkelijk draagt (en niet alleen hergebruikt wordt) | geïsoleerde LLM-controle | niet bewezen |

## Bekende grenzen

- Afkortingen zoals "bijv. een" splitsen een zin. De eenheid wordt dan korter, maar blijft vindbaar.
- Een materiaal dat uit één zin bestaat, heeft één eenheid gelijk aan de volledige tekst. In het controlepakket krijgt die eenheid daardoor de omvang "volledige tekst" in plaats van "fragment".
- Tabellen, opsommingen, bronnen zonder labels en verbogen begripsnamen zijn niet getoetst. Dit blijft een open vraag.

**Historie.** R16 en R17 zijn gepind op respectievelijk v3 en v5 en worden door de runner fail-closed geweigerd. Hun invoer, uitvoer, freezes en grootboeken zijn ongewijzigd. Het gedrag van het model onder prompt /4 is niet getest; daarvoor dient deel C van het plan, na een expliciet besluit.
