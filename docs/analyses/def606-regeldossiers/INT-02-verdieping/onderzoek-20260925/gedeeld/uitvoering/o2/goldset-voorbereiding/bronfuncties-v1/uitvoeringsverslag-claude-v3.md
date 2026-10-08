# Uitvoeringsverslag v3: besluit 19 (kaal bron-ID en prompt /6)

DEF-835 · INT-02 O2 · 08-10-2026 · Claude. Werkboom op branch `feature/DEF-835-int02-o2`, HEAD `c9e75ecb2`.

**Alles staat nog ongecommit.** Er zijn geen API- of netwerkcalls gedaan, `.env` is niet gelezen en er zijn geen hold-outbestanden geopend. Er staat geen `print()` in `src/`. Er is niets verwijderd.

Opdracht: besluit 19 van Chris na de uitslag van kwalificatieproef v8 (keuze 1A voor G060, keuze 2A voor G045). Eerst rood, dan groen.

## 1. Wijzigingen per bestand

### Keuze 1A: kaal bron-ID (alleen de /4-route)

**`src/domain/int02/contract.py`**
- r.47–55 (moduledocstring, punt "grondbronnen"): de aliasregel.
- r.374–375: commentaar bij `ANTWOORDSCHEMA_SHA256`: het schema hoort bij prompt /5 en /6.
- r.609–613: nieuw `_gereserveerd(sleutel)`. Waar bij `bedoeling` en bij een sleutel die begint met `organisatorische_context/`, `juridische_context/`, `wettelijke_basis/` of `bron/`.
- r.616–629: nieuw `_canonieke_sleutel(sleutel, invoer, bronnen)`:
  - is de sleutel een grondbron of een gereserveerde vorm, dan blijft hij ongewijzigd;
  - anders: precies één bron met exact dat ID → `bron/<id>`;
  - in alle andere gevallen blijft hij ongewijzigd. Dan faalt daarna de bestaande controle met `grond_niet_herleidbaar`.
- r.1133 (docstring `_met_posities_v4`): de aliasstap genoemd.
- r.1151: in `_met_posities_v4` gaat elke sleutel eerst door `_canonieke_sleutel`, vóór `sleutel in bronnen`.
- r.1170: de bewaarde bronfunctie krijgt `"bron": sleutel`, dus de canonieke sleutel. De dubbelecontrole (r.1175) en de afleiding lezen daardoor ook de canonieke sleutel.

Ongemoeid: `_controleer_structuur_v4`, het schema, de routes /1–/3 (die kennen geen sleutels) en de runner.

**Waarom "precies één bron" en de reservering.** Bron-ID's zijn uniek (`Int02Invoer`, r.527–528), dus een exacte match geeft hooguit één treffer. De reservering voorkomt de enige echte dubbelzinnigheid: een bron met ID `bedoeling` of `juridische_context/0` bij een onbekende bedoeling of een lege lijst. Het model kan met die sleutel ook de bedoeling of het contextitem bedoelen. Dat gaat iets verder dan de letterlijke opdracht. Het is een invulling van "geen dubbelzinnige mapping"; Chris kan het terugdraaien.

### Keuze 2A: prompt /6

**`src/services/validation/int02_assessment_service.py`**
- r.156–161: `PROMPT_VERSION = "def835-int02-prompt/6"`, met de versiegeschiedenis in het commentaar.
- r.441–447: nieuwe constante `_HERHALINGSREGEL`:
  > Herhaalt een grondbron alleen dezelfde formulering als de passage, zonder te laten zien of die inhoud bepaalt wat tot het begrip behoort of een handeling voorschrijft, dan is die herhaling geen bewijs voor "criterion"; kies dan "unclear".
- r.551: de zin staat in de regel `"function"`, direct na de betekenislijst van de bronfuncties (`… {_betekenis(_BRONFUNCTIEBETEKENIS)}. {_HERHALINGSREGEL}`).

Verder is niets aan de prompt gewijzigd. Een test bewijst dat: zonder de nieuwe zin is de systeemprompt bytegelijk aan /5. De alias staat niet in de prompt.

### Tests

**`tests/unit/domain/test_def835_int02_bronfuncties.py`**, nieuwe sectie K (r.1785–2001):

| Test | Wat |
|---|---|
| `test_19_g060_tegenhanger_met_kale_ids_is_review_conflict` (r.1823) | synthetische tegenhanger van G060 (beschrijvende kern, B1 `actor_prescription`, B2 `criterion`) met "B1" en "B2", voor drie modelverdicts: `review_required` / `conflict`, vaste vraag, beide bronnen in de reden; het document is gelijk aan dat met de juiste sleutels |
| `test_19_alle_bron_ids_kaal_en_meer_passages` (r.1848) | alle bron-ID's kaal, twee passages: pass, canonieke sleutels |
| `test_19_onbekend_id_en_elke_andere_afwijkende_sleutel_blijft_niet_herleidbaar` (r.1885) | 17 sleutels: "B9", "b1", " B1", "B1 ", "B11", "B", "1", "bron/b1", "Bron/B1", "bron B1", "bron:B1", "/B1", "bron//B1", "bron/bron/B1", "bedoeling/B1", "organisatorische_context/B1" en "bron/B9" → `grond_niet_herleidbaar` |
| `test_19_kaal_id_en_canonieke_sleutel_samen_is_een_dubbele_grondbron` (r.1897) | "B1" naast "bron/B1" → `invalid_output` |
| `test_19_gereserveerde_sleutelvorm_wordt_nooit_als_bron_gelezen` (r.1919) | bron-ID's `bedoeling`, `juridische_context/0`, `wettelijke_basis/1` en `bron/B1`: de juiste sleutel werkt, de kale vorm niet |
| `test_19_alias_is_exact_en_hoofdlettergevoelig_zonder_verwarring` (r.1937) | bronnen "B1" en "b1" naast elkaar; dubbele ID's weigert de invoer al |
| `test_19_hercontrole_van_het_genormaliseerde_document_is_het_bewaarde_oordeel` (r.1954) | `toets_actualiteit` geeft het bewaarde oordeel terug, met en zonder omzetting |
| `test_19_bewaard_oordeel_met_kale_sleutel_is_error_bij_hercontrole` (r.1969) | een kale sleutel in het bewaarde oordeel → `error` |
| `test_19_sleutels_van_bedoeling_en_context_blijven_ongewijzigd` (r.1991) | de alias raakt alleen bron-ID's |

**`tests/unit/domain/test_def835_int02_papertest.py`**
- r.315: `test_g060_met_kale_bron_ids_volgt_het_label_via_conflict`, voor drie modelverdicts. G060 uit de ontwikkelset met "B1" en "B2" → `review_required` / `conflict`, en het document is gelijk aan dat met de juiste sleutels.
- `test_g045_blijft_een_false_pass_als_het_model_b1_als_criterium_invult` blijft ongewijzigd groen: de beslisregel is voor G045 niet veranderd.

**Prompt /6 en hashpins**
- `tests/unit/services/prompts/test_def835_int02_prompt.py`:
  - r.245 en r.464–467: de versie is `/6`;
  - r.471–475: de /5-pin als historische controle;
  - r.478–483: de verwachte zin, onafhankelijk van de code;
  - r.486: de zin staat precies één keer, direct na de betekenis van `not_addressed`;
  - r.495: zonder de zin is de prompt bytegelijk aan /5;
  - r.505: de zin noemt geen geval en geen alias.

  De bestaande test op casusmateriaal (vijfwoordreeksen uit de ontwikkelset) dekt de nieuwe zin ook, en is groen.
- `tests/unit/domain/test_def835_int02_dienstregel.py`:
  - r.96–104: de /5-pin blijft als historische controle, plus een nieuwe exacte /6-pin;
  - r.761–770: de digest is ≠ /3, ≠ /5 en = /6;
  - r.799: de promptversie `/6`.
- `tests/unit/validation/test_def835_int02_schemaroute.py`:
  - r.86–94: dezelfde twee pins;
  - r.693–703: de digest is ≠ /3, ≠ /5 en = /6, en de schemahash blijft `d3ad029e…`.
- Alleen de versie aangepast naar `/6` (de identiteit volgt de live `PROMPT_VERSION`):
  - `tests/unit/validation/test_def835_int02_modelproef.py` r.1758 en r.1770 (de testnaam zegt nu "prompt_zes"), en r.2616;
  - `tests/unit/validation/test_def835_int02_variatiemeting.py` r.255 en r.363.

**Mutatieplugin** (`mutatie/mutatie_plugin.py` r.130–146): drie nieuwe mutanten. Zie §2.

**Documentatie**
- `docs/architectuur/contracts/int02_assessment_contract_v4.md`:
  - de statusregel en de promptversie bovenaan;
  - de nieuwe sectie "Besluit 19: kaal bron-ID (aliasregel)", met de onderbouwing van /4;
  - de controlevolgorde, stap 3.1;
  - de canonieke sleutel in het bewaarde oordeel;
  - een extra replay-grond;
  - het restrisico G045 bij de bewijsgrenzen;
  - de testlijst.
- `goldset-freeze-v1/kwalificatieproef-v8-uitslag-v1.md` (nieuw).
- `o2/besluit-chris-promptcorrectie-en-v3-v1.md`: het nieuwe hoofdstuk "Besluit 19".

**Hulpbestanden** (niet in de testsuite):
- `hulp/replay_v8_besluit19_test.py`: offline herbeoordeling van de 22 ruwe v8-antwoorden;
- `mutatie/draai_besluit19.py`: niet gebruikt (zie §4).

## 2. Testuitkomsten

| Meting | Uitkomst | Log |
|---|---|---|
| Rood, vóór de implementatie | 23 gefaald, alle bedoeld: 9 in sectie K, 3 papertest-varianten, 4 prompt, 2 dienstregel, 1 schemaroute, 2 modelproef, 2 variatiemeting. De 21 tests op afwijkende en gereserveerde sleutels waren al groen: zij leggen bestaand gedrag vast, en de mutanten bewijzen dat ze iets vangen. | `besluit19-rood.log` |
| Gericht (bronfuncties, papertest, dienstregel, prompt, schemaroute, modelproef, variatiemeting, dienst) | 974 geslaagd | `besluit19-groen-0-gericht.log` |
| `-k "def835 or int02" tests/unit` | 1477 geslaagd, 11 overgeslagen (DEF771_SKILLS_ROOT) | `besluit19-groen-1-def835-int02.log` |
| INT-03 / ESS-03 (`-k "int03 or ess03"`) | 786 geslaagd | `besluit19-groen-2-int03-ess03.log` |
| ruff `src tests` | All checks passed | `besluit19-ruff.log` |
| black `--check src tests` | 1006 bestanden ongewijzigd | `besluit19-black.log` |
| Papieren toets | 89 geslaagd: 27/27 met 6/6 review (ongewijzigd), plus 3 varianten van G060 met kale ID's | `besluit19-papertest.log` |
| Mutatiecontrole | 21/21 gedood, nulmeting 570/570 | `besluit19-mutatie.log`, `mutatie/resultaten/besluit19-*.xml` |
| Offline herbeoordeling v8 (22 ruwe antwoorden) | alleen G060 verandert (`error` → `review_required` / `conflict`); de andere 21 houden hun v8-status, ook G045 (pass) en G050 (review) | `besluit19-replay-v8.log` |

**De nieuwe mutanten:**
- `alias_weg_b19` (zonder alias): 12 tests gefaald, waaronder alle G060-varianten en de hercontrole;
- `alias_te_ruim_b19` (ook "1", "/B1", "bedoeling/B1" en "Bron/B1"): 4 gefaald;
- `alias_zonder_reservering_b19` (extra): 4 gefaald.

**Hashes:**
- ANTWOORDSCHEMA: `d3ad029e24b6b96242f4730686d3a4ebfebd9f46993607e41016761bc7fce715`, **ongewijzigd** (gepind en groen in de schemaroute- en modelproeftests).
- Systeemprompt /6: `a8f701ac3ec262f44efa3415d34e4931f4b637eb4d430b33aa8694d77e89d8e7`. Eerst rood bewezen met een placeholder; de route direct en de route via de schemaroute geven dezelfde digest.
- Systeemprompt /5 (historisch): `3047bb1a34f878e77bd434d668d870f0dfcfb92e3e948ac0caee77af9c2d2b70`. Ook gelijk aan de /6-prompt zonder de nieuwe zin.

## 3. Contractversie: /4 blijft

De aliasregel verruimt alleen wat geldige invoer is. Op een canonieke sleutel is `_canonieke_sleutel` de identiteit.

- **Eerder geldige /4-documenten** bevatten alleen canonieke sleutels, want een kale sleutel werd geweigerd. Hun replay leidt dus exact hetzelfde af. De tests `test_geldig_document_is_bij_hercontrole_het_bewaarde_oordeel` en sectie F zijn ongewijzigd groen.
- **Eerdere /4-foutdocumenten** met een kale sleutel geeft `toets_actualiteit` zonder replay terug als `error`.
- **Conclusie:** geen bestaand /4-document wordt anders beoordeeld. Een ophoging naar /5 is dus niet nodig.
- **Onderscheid voor nieuwe documenten:** de promptversie `/6` in de binding.
- **Kanttekening:** een *nieuwe beoordeling* van een ruw v8-antwoord (zoals dat van G060) geeft nu wel een andere uitkomst dan in v8. Dat is geen replay van een bewaard document.

## 4. Afwijkingen en beperkingen

- **Rood-log en de dubbeltest.** `besluit19-rood.log` bevat een eerste versie van `test_19_kaal_id_en_canonieke_sleutel_samen_is_een_dubbele_grondbron`. Daarin droeg het hernoemde item nog het B2-citaat, waardoor na de implementatie eerst de citaatcontrole (`niet_gevonden`) afging in plaats van de dubbelecontrole. Ik heb de test gecorrigeerd: het item zwijgt nu. Hij is daarna groen. Vóór de implementatie is hij ook in de gecorrigeerde vorm rood ("B1" was toen onbekend: `grond_niet_herleidbaar` ≠ `invalid_output`), maar dat is niet apart gelogd.
- **Mutatieruns.** Shellvariabelen, een `for`-lus en het starten van een eigen driverscript (`mutatie/draai_besluit19.py`) werden geweigerd. Elke mutant is daarom als los `python -m pytest`-commando gedraaid. Het driverscript blijft ongebruikt staan.
- **Volgorde.** De mutatieruns liepen vóór de laatste commentaarwijziging in `contract.py` (r.374–375, alleen commentaar). Gericht, `-k`, INT-03/ESS-03, ruff en black zijn daarna opnieuw gedraaid op de eindstand. De papieren toets en de v8-herbeoordeling liepen ook vóór die commentaarwijziging.
- **Interpreter.** Er is geen `.venv` in de werkboom. Alle runs gebruikten `/Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python`. Dat de werkboom-`src` geladen is, blijkt uit de nieuwe tests en uit de fragmentcontrole van de mutatieplugin.
- **Niet gedraaid:**
  - pre-commit-ruff v0.16.5;
  - de volledige unit-suite (`-m unit`);
  - een live-run met prompt /6. Of de herhalingsregel G045 werkelijk naar `unclear` brengt, blijkt pas in fase 2 van v9.
- **Restrisico van prompt /6.** De zin kan ook een terechte `criterion` bij een letterlijk overeenkomende bron naar `unclear` duwen. Dan volgt een onterechte review bij een pass-geval. Of er in de ontwikkelset pass-gevallen zijn waarin een bron de kern vrijwel letterlijk herhaalt, heb ik niet nagegaan. De papieren toets kan dit risico niet meten, want die synthetiseert de modeluitvoer.

## 5. Wat nodig is voor manifest v9

**Identiteit:**
- `contractversie`: `def835-int02-assessment/4`, ongewijzigd;
- `profiel.promptversie`: `def835-int02-prompt/5` → `def835-int02-prompt/6`;
- `router.antwoordschema_sha256`: `d3ad029e…e715`, ongewijzigd.

**Nieuwe hashes**, in de offline dry-run van de runner te berekenen en te vergelijken met:
- systeemprompt `a8f701ac3ec262f44efa3415d34e4931f4b637eb4d430b33aa8694d77e89d8e7` (voor alle gevallen gelijk; de prompt is invoeronafhankelijk);
- daardoor per geval nieuwe payload- en telpayloadhashes. De dataprompt verandert niet: alleen het veld `system` wordt langer.
- bestandshashes (stand van dit verslag, nog ongecommit):
  - `src/domain/int02/contract.py`: `1ee52782fc63d1a573932bf516c0a3d3140faa51ed59a3b9be416c2501cf94cf`;
  - `src/services/validation/int02_assessment_service.py`: `3a69a4d87cac37c3b09a06332999fea27ffdaf19455c5942ff513f71a9381684`;
  - ongewijzigd: `src/toetsregels/runtime_contract.py` `b520dcb9…de4d` en de runner `scripts/analysis/def835_int02_modelproef.py` `4bd076f3…e964`.
- `proefmap` `kwalificatieproef-v9`, `identiteit_sha256` en `aangemaakt`.

**Ongewijzigd:** de gevallen (`af1ab46c…6953`), de criteria (21/24, `max_false_pass` 0 in alle fasen), het model, de SDK, de limieten en de prijzen.

**Let op bij de kosten.** De systeemprompt groeit met één zin, dus per call iets meer invoertokens dan in v8 (5.487–6.085).

**Volgorde:**
1. Een onafhankelijke review van deze diff, met aandacht voor de reservering van sleutelvormen (§1) en het restrisico van de prompt (§4).
2. Commit, na akkoord. De logs met `git add -f`. Let op: de map `kwalificatieproef-v8/` en de uitslag v8 zijn nog ongetrackt.
3. Manifest v9 offline.
4. Een apart akkoord van Chris op v9.
5. Fase 1 en 2 (consistentietoets 7A).
6. De hold-out, met een eigen akkoord.
