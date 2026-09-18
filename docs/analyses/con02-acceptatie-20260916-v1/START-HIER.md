# START HIER — CON-02 deskundige-acceptatiepakket v1

16 september 2026 · branch `feature/DEF-743-con02-acceptatie` · basis `29b0900d4` · DEF-743

## Wat dit is

Een zelfstandig leesbaar pakket om de 31 CON-02-praktijkcasussen (C02-P01–P31) door een deskundige te laten **accepteren of afwijzen als acceptatiecriterium**. Het pakket bevat de ongewijzigde historische scenario-input, de bijbehorende bronfixtures (byte-identiek, met SHA256), de historische brongebonden onderbouwing en vragen, en een aparte laag met de projectbesluiten van 15 september 2026.

## Wat dit uitdrukkelijk NIET is

- **Geen echte appketenuitvoering.** Geen enkele casus is door de app gedraaid; "bestand aanwezig in dit pakket" is iets anders dan "feitelijk door de app/het model ontvangen". Dat laatste is nergens vastgesteld.
- **Geen bewijs van modelkwaliteit.** Er is geen generatie- of validatierun; scores en retrievalrangordes in de casussen zijn synthetische testinput.
- **Geen goldset, geen menselijke oordelen.** Alle 94 IDs staan op `status: pending`, `actor: null`, `datum: null`, `besluit: null`, `motivering: null`. Historische labels (T/G/H, "then") zijn ontwerpverwachtingen en zijn **niet** gepromoveerd naar een nieuwe pass.
- **Geen productiecode, geen wijziging van de historische basis.** De historische mappen (`praktijk-20260914-v1`, `con02-20260915-kruisreview`) zijn alleen gelezen. Van de 7 gelezen bronbestanden staat een byte-identieke snapshot in `basis/`; hun sha256 en oorspronkelijke herkomst (alleen provenance) staan in `acceptatie-register.json → gelezen_bronnen`. Het pakket is daardoor op elke checkout verifieerbaar zonder de externe 3bce-werkboom.

De inhoudelijke voorbeoordeling door Codex/Cowork volgt apart (`codex-voorbeoordeling-v1.md` staat al in deze map; die is niet in het register verwerkt — veld `voorbeoordeling_codex_cowork` is `null`).

## Voorgestelde eerste zes

Begin met **P01, P02, P04, P11, P16, P31** (gemarkeerd met ★ in het formulier):

| ID | Waarom eerst |
|---|---|
| C02-P01 | Kernscenario: echte Awb-bron, passende definitie — ijkpunt voor bronbasis + verwijskwaliteit |
| C02-P02 | Zelfde bron, ontbrekend bepalend kenmerk — ijkpunt voor betekenissteun "voldoet niet" |
| C02-P04 | Bestaand upload zonder herkomst — raakt besluit 1 (uitzondering is níet automatisch) |
| C02-P11 | RAG met volledige relevante retrieval (BW3 dieren) — positief retrievalpad |
| C02-P16 | Synthetische wiki-mutant met behouden reviewed-label — negatieve test op labels |
| C02-P31 | Vindplaats compleet, beschikbare hyperlink leeg — besluit 1 uitdrukkelijk **niet** automatisch van toepassing |

## Twee expliciete aandachtspunten

- **P28** — de "testscore 0.99" is en blijft synthetische historische input. De huidige verwachting (besluit 3) toont **geen totaalcijfer**; er is dus geen cijfer dat ontbrekend bronbewijs kan opheffen, en ontbrekend bewijs/review vervalt niet.
- **P31** — de link naar art. 1:3 Awb is beschikbaar (origin-URL in het manifest). De deskundige verwijzingsuitzondering (besluit 1) geldt alleen voor een bron **zonder** bruikbare hyperlink en is hier **niet automatisch van toepassing**.

## Bestanden

| Bestand | Inhoud |
|---|---|
| `deskundigenformulier.md` | 31 casussen: input, exacte bronpassages met locator/hash/link, historische onderbouwing en vraag, huidige laag (besluiten), lege oordeelvelden |
| `acceptatie-register.json` | Machineleesbaar: per casus lagen `historisch_ongewijzigd` / `historische_verwachtingen` / `huidige_laag_projectbesluiten` / `bewijsstatus` / `expert`; plus `overzicht_94` |
| `overzicht-94-ids.md` | Alle 94 IDs (31 P + 63 overige ontwerpcases), allemaal pending |
| `bronmanifest-sha256.json` | 13 fixtures: sha256, bytes, kind, bronversie, origin, locators, synthetisch-label, letterlijke passages |
| `bronfixtures/` | De 13 fixtures, byte-identiek gekopieerd (mutanten onder `mutanten/`, hernoemde kopie onder `hernoemd/`) |
| `basis/` | Byte-identieke snapshots van de 7 gelezen historische bronbestanden — de enige bron voor verificatie |
| `bouw_pakket.py` | Herhaalbare bouwer (stdlib). Standaard bouwt hij vanuit `basis/` + `bronfixtures/` naar een **nieuwe, niet-bestaande** versiemap; `--hist DIR` leest de historische map; `--dry-run` toont alleen de beslissing. **Er is geen overschrijfroute**: een doelmap die al inhoud heeft wordt altijd geweigerd, ongeacht die inhoud, vóór enige write; onbekende opties worden geweigerd. Een bestaand pakket — en dus ook ingevulde formulieren/oordelen — kan door de bouwer nooit gewijzigd of genulstelde worden. |
| `verifieer_pakket.py` | Integriteitscheck — **geen acceptatietest** |

## Verificatie draaien

```bash
python3 docs/analyses/con02-acceptatie-20260916-v1/verifieer_pakket.py            # integriteit
python3 docs/analyses/con02-acceptatie-20260916-v1/verifieer_pakket.py --zelftest # bewijs dat de check discrimineert
```

Controleert, uitsluitend via `basis/` en relatieve paden (geen extern historisch pad wordt geopend): structuur · 31 P + 94 unieke IDs · exacte input-gelijkheid met basis/v6 en basis/v2 (hash-reproductie) · **per casussectie** in het formulier ieder inputveld, gegeven/wanneer, vraag, hashes en letterlijke passages (een verwisselde definitie tussen twee casussen wordt gedetecteerd) · 13 fixture-hashes = basis/bronmanifest-v3 · alle oordelen leeg: in het register `pending`/`null`, en in het formulier het **volledige beoordelingsblok** (kop "### 6." tot het einde van de casussectie) regel-voor-regel gelijk aan de lege template, zodat ook een motivering op een vervolgregel of een alinea na "Datum" als ingevuld telt · basis-snapshots ongewijzigd; de getrackte repo-kopieën van de kruisreviewbestanden worden, indien aanwezig, tegen de snapshot-hash gecontroleerd. Exit 0 = integer.

`--zelftest` schrijft niets: het muteert het geladen pakket in het geheugen (o.a. P01-definitie vervangen door de P02-definitie, definities P01/P02 verwisseld, passage uit de verkeerde sectie, register-input, fixturebytes, ingevuld oordeel in register, aangevinkt vakje, motivering op een vervolgregel onder een leeg label, extra alinea na "Datum", ingevulde motivering in de laatste sectie, gewijzigde basis-snapshot) en eist dat elke mutant rood en het ongewijzigde pakket groen is.

## Bronnen

- `docs/analyses/con02-20260915-kruisreview/besluiten-20260915-v3.md` (besluiten 1–3)
- `docs/analyses/con02-20260915-kruisreview/casusregister-geintegreerd-v2.json` (94 IDs, GTH-v1)
- `…/con02-20260912-samenwerking/praktijk-20260914-v1/` (worktree 3bce): `actief-pakket-v1.json`, `praktijktestgevallen-v4.md`, `bronmanifest-v3.json`, `casusregister-geintegreerd-v6.json`, `retrieval-fixtures-v1.json`, `fixtures/`
- Hash-recept `scenario_input_sha256`: `gth-20260914-v1/bouw-casusregister-codex-v1.py` r.72 (gereproduceerd 31/31)
