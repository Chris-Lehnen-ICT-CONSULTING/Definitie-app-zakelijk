# DEF-835 — WP5a correctie F2/F3: verslag Claude Code CLI-uitvoerder (v1)

28 september 2026. Uitvoerder: Claude Code CLI, sessie `914fccdd-7899-4d5c-8aa0-1c9ab334d7d4`. Opdracht: `wp5a-opdracht-claude-F23-v1.md`. Akkoord: `wp5a-F23-akkoord-v1.md`, op het voorstel `wp5a-reviewcorrectie-uitbreiding-v1.md`. Bevindingen: `wp5a-codex-review-v1.md` (F2, F3) en `wp5a-codex-F1-herreview-v1.md`, waarin F1 gesloten is.

Werkboom op HEAD `d769276041e619103ace7bc66e65419d480dae99`, index leeg. `src/` en `tests/` zijn tussen `979ca05` en `d769276` gelijk (`git diff --quiet`, exit 0).

Er zijn geen agents, reviewers of extra CLI-sessies gestart. Geen modelcalls, productiedata of Actions. Geen gitmutatie: geen stage, commit, write-tree, push of merge.

## Uitkomst

**F2** is gecorrigeerd volgens het geaccordeerde voorstel.
- `Int02AssessmentService` heeft een additieve publieke methode `configuratie()`. Die levert een onafhankelijke, volledige WP1-`Configuratie`-snapshot zonder modelaanroep.
- De wrapper legt deze snapshot vast vóór `assess`. Daarna eist hij `document.invoer == verse invoer` én `document.binding == bereken_binding(verse invoer, snapshot)`. De evaluator krijgt de snapshot, niet de documentconfiguratie.
- Een ontbrekende, niet-aanroepbare, ongeldige of falende snapshot geeft `error` zonder aanroep.
- Een afwijkende binding geeft `error` zonder oordeel, ook als de afwijking door een wijziging rond de aanroep ontstaat.

**F3** is gecorrigeerd. De bestaande test `test_dienst_wordt_niet_door_de_container_aangemaakt` blijft onder dezelfde naam bestaan en is herijkt van tekstguard naar gedragsguard:
- De normale container bouwt of injecteert de dienst niet vanzelf en doet geen modelaanroep.
- De expliciete factory heeft keyword-only `profiel` en `budget` zonder default. `profiel=None` wordt geweigerd.
- Een geldige expliciete aanroep bouwt de dienst precies één keer, zonder modelcall.

F1 blijft behouden: `modular_validation_service.py` is byte-gelijk aan manifest-v2.

## Scope: negen bestanden

| Bestand | SHA-256 nu | T.o.v. herstelkopie `wp5a-F23-vooraf-v1` |
| --- | --- | --- |
| `src/services/container.py` | `32a5ae789a0f131a036e4f1aa66d98cd05e4ea99ca1e77545529592de781e42a` | ongewijzigd |
| `src/services/orchestrators/definition_orchestrator_v2.py` | `db1093e54c6c917fb6b37f49b153cdd1f2465274da94fb1bb74bfe1ef724d4ca` | ongewijzigd |
| `src/services/orchestrators/validation_orchestrator_v2.py` | `1d592767c6d946b924f5eaf617fb76d4aca537b44ab78324bf7628e229ff354e` | F2: +20/−6 |
| `src/services/validation/modular_validation_service.py` | `84a9e330c263afeea519363e1ac692950c93df3c1c15a2634fef5d5d722ab6c2` | ongewijzigd (F1) |
| `src/services/validation/int02_assessment_service.py` | `99f1381ed4d2c8c2505a4acb5daeae809ccaabb840be7e0bc0424601e6b87b3a` | F2: +12 (vóór: `dda9d274…c049e` = HEAD) |
| `tests/unit/services/orchestrators/test_def835_int02_wrappers.py` | `17446549d6f1688cf5af0efd9bddb6b926b402ce40b19f92db328fdf0b7de90f` | F2: +215/−5 |
| `tests/unit/validation/test_def835_int02_modular.py` | `ca09aa5220b4e25cc55f8d90831abfc03a69034328b259b11d1227afcb799400` | ongewijzigd |
| `tests/unit/services/test_def835_int02_container.py` | `5048a1c4bf68fe58d8315a85129269e3eff27737e0b833b6bef177e2c3f69ae9` | ongewijzigd |
| `tests/unit/validation/test_def835_int02_assessment_service.py` | `1dcc0f9d99a297d119107b0b936ac302677b9d57c999f58998561f47a8b14e17` | F2+F3: +152/−4 (vóór: `ca82cce1…0c1b` = HEAD) |

De correctie is productie +32/−6 en tests +367/−9. Dat is meer testregels dan de raming van 40–100 extra regels, vooral door de geparametriseerde mismatchtests over beide routes. Er zijn geen testgevallen verwijderd: het oude testnamenoverzicht is een deelverzameling van het nieuwe, met 6 nieuwe wrappertests en 5 nieuwe WP2-tests. Alle `−`-regels in de delta zijn vervangen regels:
- het oude docstringdeel en de controle `document.binding.configuratie()`;
- de oude `FakeDienst`-kop;
- de oude body van de tekstguard.

Geen dependency, schemawijziging of resultaatcontractversie (blijft 2.3.0). Het WP1-document en `domain/int02/contract.py` zijn ongewijzigd.

### Kern van de productiewijziging

- **`int02_assessment_service.py`** — nieuwe publieke methode:

  ```python
  def configuratie(self) -> Configuratie:
      return self._configuratie(self._route(), PROMPT_VERSION)
  ```

  Dat is dezelfde berekening als `assess` bindt. Zij omvat:
  - de normhash en normversie;
  - de op leesmoment geldende `PROMPT_VERSION`;
  - de routeringshash over taak, routeruitkomst, capability-beleid, profiel en budget;
  - de gevraagde provider en het gevraagde model.

  Het is alleen een routerlookup, geen modelaanroep. Elke aanroep geeft een nieuwe, frozen `Configuratie`. Private velden worden alleen binnen de eigen klasse gelezen.
- **`validation_orchestrator_v2.py`** — `_beoordeel_int02` voert na de invoer- en NE-controle en vóór `assess` de volgende stappen uit:
  1. `getattr(dienst, "configuratie", None)` ophalen. Is dat niet aanroepbaar, dan `configuration_unavailable`.
  2. `verwacht = snapshot()` uitlezen. Is het resultaat geen `Configuratie`, dan `invalid_configuration`.
  3. Na `assess` de volledige binding vergelijken met `bereken_binding(invoer, verwacht)`, naast de controle op de invoer. Bij verschil volgt `binding_mismatch`.
  4. `METADATA_CONFIGURATIE = verwacht` zetten.

  Uitzonderingen geven, zoals voorheen, alleen het type in de log en `error`. Op de dienst wordt geen privé-attribuut ingezien.

## RED → GREEN

| Log (`bewijs/`) | Wat | Uitkomst | SHA-256 |
| --- | --- | --- | --- |
| `wp5a-F23-rood-v1.log` | Nieuwe en herijkte tests tegen bestaande WP5a-code. Productiehashes controleerbaar gelijk aan `wp5a-F23-vooraf-v1`; testhashes gelijk aan de eindtests | **32 failed, 8 passed, exit 1** | `630ae134a30b6aa36c52ffd18dfc1e6fc48cf43d25956d1d2e627b2352ac87e2` |
| `wp5a-F23-groen-v1.log` | Alle WP5a-tests plus volledige WP2-dienstentests (221), en de RED-selectie apart (40) | **221 passed, exit 0; 40 passed, exit 0** | `c4086419ce80c8d45008fafbd56566b50e491cf4060b762669a5fa6d650de9fa` |
| `wp5a-F23-regressie-v1.log` | Zelfde gerichte set als bij F1 (orchestrators, heel `tests/unit/validation` incl. DEF-771-O1 en WP2, containers, modular, INT-01/03/ESS-03, DEF-771-view); niets gedeselecteerd | **2.941 passed, 11 skipped, 0 failed, exit 0** (F1: 2.908 + F3 failed) | `c051c0effdde2c60ceba6bc7735e53f9f9d200c25abd31b5af55df03d42f3ac6` |
| `wp5a-F23-f3-mutatie-v1.log` | Herijkte F3-guard: zonder mutatie en met één naïeve in-memory mutatie (`orchestrator()` bouwt zelf een dienst; plugin buiten de repo `/tmp/wp5a_f23_mutatie/`) | zonder: 1 passed, exit 0; **met: 1 failed, exit 1** | `832abd820fdc6d083249b414acbb3c1f5065d943f27fa8bce6794980c8e364c2` |
| `wp5a-F23-lint-v1.log` | black 26.5.1, ruff 0.15.17 en ruff 0.16.5 op alle negen bestanden | alle exit 0 | `024c28bb7f080ea343961f9e0eae726db50fa9b30b19198444e4f004c4e15596` |
| `wp5a-F23-mypy-v1.log` | `mypy src/ --check-untyped-defs --no-incremental` | 13 fouten in 2 bestanden, dezelfde als de baseline (`contract.py` 7, `int02_assessment_service.py` 6); twee regelnummers +12 verschoven door de nieuwe methode; niet opgelost | `dfae0d3cf69d2ae86e713b7772f204c161e1de1086ecfe37ceb8f94419bd298a` |

De RED-oorzaken (32):
- **15× `'pass' == 'error'`:**
  - het reviewerrepro;
  - binding wijkt af op normhash, normversie, promptversie, routeringshash, provider of model, telkens voor tekst- en recordroute (12);
  - wijziging tijdens de aanroep (2).
- **10× aanroep ondanks een ontbrekende, niet-aanroepbare, `None`-, dict- of falende snapshot**, over beide routes.
- **5× `configuratie()` ontbreekt** (WP2-snapshottests).
- **1× snapshot niet vóór `assess`** (`[0] == [1]`).
- **1× routerwissel tussen snapshot en aanroep niet als `error`** (`assert 1 == 0`).

De 8 groene tests in de RED-selectie zijn:
- de **herijkte F3-guard**: de WP5a-code was hier al correct, alleen de oude tekstguard was fout. Het rood van die oude guard tegen deze code staat in `wp5a-F1-regressie-v1.log`, en het onderscheidend vermogen van de nieuwe guard in `wp5a-F23-f3-mutatie-v1.log`;
- 7 bestaande WP2-tests die toevallig `f2_` in hun naam hebben (capability-beleid uit de WP2-review).

Alle log-hashregels zijn met `shasum -c` gecontroleerd tegen de huidige bestanden: GREEN, regressie en lint 9/9 OK. De RED-testhashes zijn gelijk aan de eindtests. Na de RED is aan de tests niets meer gewijzigd; black is vóór de RED gedraaid.

## Acceptatiepunten

| Punt | Bewijs |
| --- | --- |
| Reviewerrepro (dienst voor `fake-new-model` geeft een oud coherent document voor `fake-int02-model`) | `test_f2_reviewerrepro_oud_document_voor_ander_model_is_error`: `error`, `MELDING_E`, `review.actuality=None`, assessment `None`, nieuwe FakeAI 0 calls |
| Mismatch op norm, prompt, provider, model en routering | `test_f2_documentbinding_afwijkend_van_snapshot_is_error` over 6 velden × 2 routes: telkens `error`, precies 1 aanroep, geen oordeel |
| Ontbrekende of ongeldige snapshot | `test_f2_ontbrekende_of_ongeldige_snapshot_is_error_zonder_aanroep` (ontbreekt / niet-aanroepbaar / `None` / dict / uitzondering × 2 routes): `error`, 0 aanroepen, uitzonderingstekst niet in de log |
| Wijziging rond de aanroep nooit stil pass/current | `test_f2_snapshotwijziging_tijdens_aanroep_is_nooit_current` (× 2 routes) en `test_f2_routerwissel_tussen_snapshot_en_aanroep_is_error` (echte dienst, router wisselt na de snapshot → `error`, FakeAI 0 calls) |
| Snapshot vóór `assess`; verwachting nooit uit het retourdocument | `test_f2_snapshot_wordt_voor_de_aanroep_vastgelegd` (`snapshots_voor_assess == [1]`, geldig pad blijft pass/current met exact document); de mismatchtests bewijzen dat de documentconfiguratie niet als verwachting telt |
| Snapshot = exact wat `assess` bindt | `test_f2_snapshot_is_exact_de_configuratie_die_assess_bindt`, `test_f2_snapshot_ook_bij_blokkade_gelijk_aan_de_binding` (router weg; profiel `None`). De bestaande C105/C107/C112/C117-ketentests met de echte dienst blijven groen |
| Volledigheid: norm, prompt, profiel, budget, routering | `test_f2_snapshot_bevat_norm_prompt_profiel_budget_en_routering`: elke variant geeft een andere snapshot; `PROMPT_VERSION` wordt op het leesmoment gelezen |
| Kopie-isolatie | `test_f2_snapshot_is_een_onveranderlijke_losse_kopie`: frozen (`FrozenInstanceError`); geforceerde mutatie van een snapshot raakt de dienst niet; een latere routerwijziging raakt een eerdere snapshot niet |
| Nul calls bij uitlezen | `test_f2_snapshot_uitlezen_doet_geen_modelaanroep`: FakeAI 0 calls, router alleen `get_model("validation")` |
| F3 gedragsguard | Herijkte `test_dienst_wordt_niet_door_de_container_aangemaakt` plus mutatiebewijs |
| O1 en F1 behouden | Regressie groen, inclusief `test_def771_int02_o1.py`, de F1-tests en `test_def835_int02_modular.py` (ongewijzigd) |

## Diffs

- Correctiediff t.o.v. `wp5a-F23-vooraf-v1` (vier gewijzigde bestanden): `bewijs/wp5a-F23-correctiediff-v1.patch`, 528 regels, SHA-256 `02d0502166249f565fbb6efb9396cb16995a4b631a14c550eebc37fd298e634d`.
- Volledige negenbestandenpatch t.o.v. HEAD `d769276`: `bewijs/wp5a-F23-werkboomdiff-v1.patch`, 2.128 regels, SHA-256 `2c8638723a4aff213ad90333769b20f16a22a32041c5ff30004bca43f93b623a`. Zes gewijzigde bestanden via `git diff HEAD`; drie ongetrackte tests via `git diff --no-index /dev/null`.

## Git-staat

HEAD is `d769276041e619103ace7bc66e65419d480dae99`, ongewijzigd. De index is leeg (0 gestagede bestanden) en is niet aangeraakt. Gewijzigd in de werkboom: de zes getrackte bestanden uit de tabel (vier daarvan al sinds WP5a-v1) en de drie ongetrackte WP5a-testbestanden. Mijn nieuwe dossierbestanden zijn de zeven `bewijs/wp5a-F23-*`-logs en -patches plus dit verslag. De coördinatorbestanden `wp5a-F23-claude-stream-v1.jsonl`, `wp5a-F23-claude-stderr-v1.log` en de herstelkopieën heb ik niet aangeraakt. Buiten de repository staat het mutatieplugin `/tmp/wp5a_f23_mutatie/`; daar is niets verwijderd.

## Resterende beperkingen

1. **Controle aan de grens, geen providerattestatie.** De snapshot bindt de *gevraagde* provider en het gevraagde model, gelijk aan de binding in WP2. Dat attesteert niet welk model werkelijk antwoordde (zie de WP2-documentatie over attributie). F2 sluit de binding tussen document en dienstconfiguratie op de integratiegrens, niet de providerattestatie.
2. **Wijzigingsvenster.** Een wijziging tussen snapshot en `assess` wordt als `error` gevangen: de binding verschilt en de wrapper vergelijkt met de snapshot. Een wijziging die in `assess` zelf ná de interne routering plaatsvindt, raakt dat document niet, want het document hoort dan bij de configuratie vóór die wijziging. Bij een volgende validatie telt de nieuwe snapshot.
3. **Geen onafhankelijke controle van een kwaadwillende dienst.** De snapshot komt van de geïnjecteerde dienst zelf. Een dienst die zowel de snapshot als het document consistent vervalst, wordt niet gedetecteerd. Dat valt buiten het dreigingsmodel van expliciete DI; de reviewersrepro, een inconsistente dienst, wordt wel gevangen.
4. **mypy.** De 13 fouten in WP1/WP2 blijven open en `make mypy-check` blijft rood, net als op HEAD. De twee `performance_tracker`-fouten uit de volledige suite zijn eerder als bestaand aangetoond. De volledige unit-suite is niet opnieuw gedraaid, omdat er geen concrete aanleiding was.
5. **Omvang.** Het testdeel is groter dan de raming.
6. **Niet in dit pakket:** opslag, herladen en C118, UI, activering en modelkwalificatie.

Hierna stop ik voor de onafhankelijke herreview van de delta.

## Bronnen

- `wp5a-reviewcorrectie-uitbreiding-v1.md`, `wp5a-F23-akkoord-v1.md`, `wp5a-codex-review-v1.md` (F2 r.26-40, F3 r.42-50), `wp5a-codex-F1-herreview-v1.md`
- `bewijs/wp5a-reviewmanifest-v2.json`, `bewijs/wp5a-F23-vooraf-v1/`
- `src/services/validation/int02_assessment_service.py` (`assess`, `_route`, `_configuratie`, nieuwe `configuratie`)
- `src/services/orchestrators/validation_orchestrator_v2.py` (`_beoordeel_int02`)
- `src/domain/int02/contract.py` (`Configuratie`, `bereken_binding`, `toets_actualiteit`)
