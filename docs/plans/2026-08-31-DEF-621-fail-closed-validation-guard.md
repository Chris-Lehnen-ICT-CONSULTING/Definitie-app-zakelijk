# Fail-closed validatieguard (DEF-621) Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Een incomplete of ongeldige toetsregelset kan nooit meer als complete validatie worden gepresenteerd; de validatie stopt vóór evaluatie en retourneert `validation_unknown`.

**Architecture:** Eén guard aan het enige chokepoint (`ModularValidationService.validate_definition`), gevoed door een **atomair gepubliceerde runtime-snapshot** die alle ruleset-afhankelijke gegevens van één generatie draagt. Readiness is verzamelingsgelijkheid tussen de geladen regel-ID's en de contractuele ID-set uit de root-SSOT. Een fingerprint over de regelbestanden én de contract-SSOT detecteert beide overgangen — compleet→incompleet en incompleet→hersteld — ongeacht de TTL. Het resultaatcontract wordt additief uitgebreid op het actieve TypedDict in `services/validation/interfaces.py`.

**Tech Stack:** Python 3.13 · `@dataclass(frozen=True)` + `threading.Lock` · TypedDict/`Literal` · JSON Schema draft 2020-12 · pytest (marker `unit`) · Streamlit

---

**Datum:** 31 augustus 2026 (tweede herziening) · **Issue:** DEF-621 (In Progress)
**Basis:** `origin/main` @ `a526514e` · **Branch:** `feature/DEF-621-validation-guard`
**Worktree:** `~/Projecten/Definitie-app.worktrees/DEF-621-validation-guard`

> **Status: nog niet uitgevoerd.** Vraagt eerst review en de vier toestemming-gates uit §11.

## 1. Doel en afbakening

Zes verplichte punten, alle geverifieerd afwezig op `a526514e`: (1) centrale guard vóór evaluatie, scoring en acceptability; (2) volledigheid op de exacte contractuele regel-ID-set; (3) uitkomst `validation_unknown`; (4) reden `ruleset_incomplete`; (5) een daadwerkelijk gebruikt readiness-oppervlak; (6) cacheherstel binnen een niet-verlopen TTL.

**Buiten scope, hard:** DEF-622-contexttransport · DEF-623-semantiek · DEF-624-scorewerk · DEF-700 · prompt builders · database · dependencies · elke schemawijziging buiten `validation_result.schema.json`. Er wordt niets verwijderd.

## 2. Contractbestanden — definitief

| Bestand | Rol in dit plan |
| -- | -- |
| `src/services/validation/interfaces.py` | **Het actieve TypedDict-contract.** `CONTRACT_VERSION = "1.1.0"` (`:27`), `ValidationResult` (`:35`). Geïmporteerd door `modular_validation_service.py:20` en `mappers.py:17`. **Wordt gewijzigd.** |
| `src/services/validation/modular_validation_service.py` | **Maakt het unknown-resultaat.** Wordt gewijzigd. |
| `src/services/validation/mappers.py` | **Blijft ongewijzigd.** Het resultaat van `validate_definition` gaat rechtstreeks naar de orchestrator; de mapper vertaalt uitsluitend het legacy dataclass-pad en raakt de nieuwe velden niet. |
| `src/services/validation/types.py` | **Volledig buiten scope.** Gedrifte tweede representatie op `CONTRACT_VERSION = "2.0.0"` (`:37`) die door **niemand** in `src/` wordt geïmporteerd — alleen een zelfverwijzing in de eigen docstring op `:19`. De drift gaat met deze meting als notitie naar DEF-624; er wordt hier geen regel aan veranderd. |

Exacte, niet-onderhandelbare waarden:

```
validation_status  = "validation_unknown"     # anders: "validated"
unknown_reason     = "ruleset_incomplete"
validation_readiness                          # veldnaam van het readiness-object
```

## 3. Uitgangssituatie — gemeten op `a526514e`

| Bevinding | Locatie |
| -- | -- |
| Contract-ID-set, manifest zonder glob en zonder fallback | `modular_validation_service.py:203` → `root_contract_policy().rule_ids` |
| **Volledigheid tautologisch** — bij nul bestanden geldt `0 == 0` | `rule_cache.py:400` → `len(all_rules) == files_on_disk` |
| Enige chokepoint naar evaluatie | `modular_validation_service.py:406` |
| Score, gate en `is_acceptable` liggen ruim daarna | `:687` · `:722` · `:769`/`:818-853` |
| `get_health_status()` bestaat, **nul call-sites** in `src/` | `:386` |
| Regels worden **eenmalig in `__init__`** geladen | `__init__:112` → `_load_rules_from_manager()` |
| `RuleContractError` wordt opnieuw opgegooid | `:257-260` |
| Instantie-memo + module-cache, beide TTL 3600 | `rule_cache.py:24,98,147,238` |
| `validation_unknown`, `ruleset_incomplete`, `validation_readiness` | nul voorkomens in `src/` én `tests/` |

## 4. Atomische, thread-safe statewissel

`ModularValidationService` kan concurrent worden gebruikt. Een herlaadpoging mag nooit een venster openen waarin een validatie op een half vernieuwde of ten onrechte "ready" staat draait.

### 4.1 Atomair gepubliceerde runtime-snapshot

Eén snapshot draagt **alle ruleset-afhankelijke gegevens van één generatie**. Een `frozen=True`-dataclass maakt geneste dictionaries niet immutable; daarom worden de collecties bij de bouw als alleen-lezen vastgelegd en na publicatie nooit meer gemuteerd.

```
@dataclass(frozen=True)
class RuntimeSnapshot:
    # identiteit van de generatie
    fingerprint: str | None
    readiness: ValidationReadiness

    # ruleset-afhankelijke gegevens — alle van dezelfde generatie
    contract_rule_ids: tuple[str, ...]
    internal_rules: tuple[str, ...]                       # was list, werd gemuteerd (:313-314)
    rule_records: Mapping[str, RuleRecord]                # MappingProxyType
    json_rules: Mapping[str, dict[str, Any]]              # MappingProxyType
    default_weights: Mapping[str, float]                  # MappingProxyType
    pattern_cache: dict[str, Any]                         # per generatie een eigen dict

    # afgeleide telling en degraded-informatie van dezelfde generatie
    rules_loaded_count: int
    rules_expected_count: int
    is_degraded_mode: bool
    degradation_reason: str | None
```

**Eisen die dit afdwingt:**

* `internal_rules` en `contract_rule_ids` zijn **tuples**. `_internal_rules` werd gemuteerd via `append` (`:313-314`); die mutatie verhuist naar de lokale opbouw vóór publicatie.
* `rule_records`, `json_rules` en `default_weights` zijn `MappingProxyType`-views over state-owned dicts. Zij worden na publicatie aantoonbaar niet gemuteerd; een schrijfpoging faalt met `TypeError`.
* `pattern_cache` is **per generatie een eigen dict**. Een herbouwde regelset erft nooit gecompileerde patronen van de vorige generatie. Dit is de enige bewust muteerbare collectie: hij is generatie-eigen en wordt met de snapshot weggegooid.

**Waar wat woont.** `RuntimeSnapshot` is een puur datatype en staat in `readiness.py`, naast `ValidationReadiness`. De fabrieksmethoden `_lege_snapshot()` en `_bouw_snapshot()` staan op `ModularValidationService`, omdat zij servicestaat lezen (manager, regelpad, contractpolicy).

**Buiten de snapshot** blijven registry, repository, thresholds, cleaning-service en overige onveranderlijke serviceconfiguratie. Die hangen niet aan de regelset.

**Na `state = self._ververs_state_indien_nodig()` leest de evaluatielus geen ruleset-afhankelijk `self._…`-veld meer.** De snapshot wordt expliciet doorgegeven aan of gebruikt door:

| Plek | Gebruikt uit de snapshot |
| -- | -- |
| gewichtsopbouw (`:483-488`) | `default_weights` |
| iteratie over regels (`_get_rule_evaluation_order`, `:381-384`) | `internal_rules` |
| score-policycontrole | `rule_records`, `internal_rules` |
| `_evaluate_rule` (`:904`) | `rule_records`, `pattern_cache` |
| `_evaluate_via_registry` (`:916`) | `rule_records`, `pattern_cache` |
| `_outcome_naar_violation` (`:1005`) | `rule_records`, `json_rules` |
| `_verwerk_uitkomst` (`:1054`) | `rule_records` |
| `_vul_niet_uitgevoerde_regels` (`:1171`) | `contract_rule_ids` |
| `get_health_status` (`:386`) | `rules_loaded_count`, `rules_expected_count`, `is_degraded_mode`, `degradation_reason`, `readiness` |

Conform projectregel 4 (*geen backwards compatibility, refactor in place*) worden de ruleset-afhankelijke `self._…`-attributen **vervangen**, niet gedupliceerd als alias. Lezers die ze vandaag gebruiken — inclusief bestaande tests — gaan mee naar de snapshot. Alleen `get_health_status()` blijft als publieke methode zijn eigen dict opleveren, gevuld uit de actieve snapshot.


### 4.2 Synchronisatiegrens

Eén `threading.Lock` (`self._state_lock`) omsluit **precies** de fingerprintcontrole plus de statewissel:

```
def _ververs_state_indien_nodig(self) -> RuntimeSnapshot:   # volledig synchroon
    fp = bereken_fingerprint(self._fingerprint_bronnen)      # buiten de lock
    snap = self._snapshot
    if fp == snap.fingerprint:
        return snap
    with self._state_lock:
        snap = self._snapshot                                # dubbelcheck ná lock
        if fp == snap.fingerprint:
            return snap
        try:
            nieuw = self._bouw_snapshot(fp)                  # ALLE velden lokaal
        except Exception as exc:
            self._snapshot = self._lege_snapshot(fp, exc)    # één toewijzing
            return self._snapshot
        self._snapshot = nieuw                               # één toewijzing
        return self._snapshot
```

Vier eigenschappen die dit garandeert:

1. **Volledige lokale opbouw.** `_bouw_snapshot()` bouwt elk veld uit §4.1 — records, json_rules, weights, internal_rules, tellingen, degraded-informatie en een verse `pattern_cache` — in lokale variabelen, en valideert het contract, vóór enige publicatie. Een half opgebouwde generatie wordt nooit zichtbaar.
2. **Publicatie met één attribuuttoewijzing.** `self._snapshot = nieuw` is in CPython atomair. Lezers nemen aan het begin van hun aanroep één snapshot (`state = self._ververs_state_indien_nodig()`) en zien daarna een volledig consistente generatie.
3. **Fout ⇒ volledige unready snapshot, ook met één toewijzing.** `_lege_snapshot()` levert een compleet ingevuld object: lege collecties, een verse lege `pattern_cache`, `readiness.ready is False`, reden `ruleset_incomplete`. De oude ready-generatie blijft niet staan; er is geen venster waarin op een verouderd positief oordeel wordt gevalideerd.
4. **Geen lock over een `await`.** `_ververs_state_indien_nodig()` is volledig synchroon — fingerprint, `clear_cache()`, `get_all_regels()` en contractvalidatie zijn alle blocking IO/CPU. `validate_definition` roept hem aan vóór het eerste `await`. De lock wordt nooit over een suspensiepunt gehouden.

De dubbelcheck ná het nemen van de lock voorkomt dat twee gelijktijdige aanroepen dezelfde herlaadpoging dubbel uitvoeren.

## 5. Fingerprint

**Bronnen — beide, expliciet:**

1. alle `*.json` in de regelmap (`_regelpad()`, zie §6);
2. `ROOT_SSOT_PAD` — `config/toetsregels/toetsregels_config.yaml`, de contract-SSOT.

**De bronlijst wordt bij iedere controle opnieuw opgebouwd**, met een verse glob over de regelmap plus `ROOT_SSOT_PAD`:

```
def _fingerprintbronnen(self) -> tuple[Path, ...]:
    regelmap = self._regelpad()
    regels = tuple(sorted(regelmap.glob("*.json"))) if regelmap else ()
    return (*regels, ROOT_SSOT_PAD)
```

Een bij constructie opgeslagen padlijstje is **fout**: een nieuw, onverwacht regelbestand staat er dan niet in en blijft daardoor onzichtbaar, terwijl juist zo-n bestand de geladen ID-verzameling ongelijk maakt aan het contract. De glob moet dus per controle draaien, niet eenmalig.

Per bron `(pad, st_size, st_mtime_ns)`, gesorteerd, naar één stabiele hash. Daardoor wordt **zowel beschadiging als herstel van de regelbestanden én van de contract-SSOT** gedetecteerd. Verdwijnt of wijzigt de YAML, dan verandert de fingerprint en volgt een herlaadpoging met dezelfde foutgrens.

**Prestatietarget, te meten:** de fingerprint moet ruim onder de validatiebegroting blijven; richtwaarde sub-milliseconde bij ~54 bronnen. Dit is een **target dat in commit 4 wordt gemeten**, geen reeds bewezen feit. Blijkt het duurder, dan wordt de meting in het oplevercomment vastgelegd en het ontwerp heroverwogen.

**Bekende grens, uitsluitend vastgelegd:** een bestand dat corrupt raakt met identieke grootte én mtime ontsnapt aan de fingerprint. Er wordt **geen inhoudshash per validatie** gebouwd; de kosten daarvan staan niet in verhouding tot dat randgeval. De contractvalidatie bij het herlezen blijft de inhoudelijke autoriteit.

## 6. Herstelgedrag per managerpad — exact

Er wordt **geen** generieke `rule_cache.invalidate()` gebruikt; die bestaat niet. De service gebruikt de bestaande publieke API van de manager die hij al heeft, via één kleine private helper — geen nieuw protocol, geen adapter.

```
def _regelpad(self) -> Path | None:
    m = self.toetsregel_manager
    if m is None:
        return None
    d = getattr(m, "regels_dir", None)                       # ToetsregelManager:102
    if d is None:
        cache = getattr(m, "cache", None)                    # CachedToetsregelManager:32
        d = getattr(cache, "regels_dir", None)               # RuleCache.regels_dir
    return Path(d) if d else None
```

| Pad | Bronpad | Invalidatie | Herladen |
| -- | -- | -- | -- |
| `ToetsregelManager` | `manager.regels_dir` (`manager.py:102`) | `manager.clear_cache()` (`manager.py:429`) | `manager.get_all_regels()` (`manager.py:388`) |
| `CachedToetsregelManager` | `manager.cache.regels_dir` (`cached_manager.py:32` → `RuleCache.regels_dir`) | `manager.clear_cache()` (`cached_manager.py:96`) → `self.cache.clear_cache()` (`:98`) | `manager.get_all_regels()` (`cached_manager.py:57`) → `self.cache.get_all_rules()` (`:65`) |
| `manager is None` | **geen herstelbaar bronpad** | n.v.t. | n.v.t. — blijft permanent `validation_unknown` |

**Bewijs dat `clear_cache()` op het productiepad beide cachelagen leegt** — uit de bestaande implementatie, `rule_cache.py:359-381`:

* `self._rules_memo = None` en `self._rules_memo_ts = 0.0` → de instantie-memo uit `:238` is weg;
* `_global_cache_clear()` → de decoratorcaches van `@cached(ttl=3600)` op `:98` en `:147` zijn geleegd.

Beide lagen dus, met de bestaande publieke methode. De transitietest bewijst dit gedrag ook empirisch, niet alleen op basis van deze codelezing.

## 7. Foutgrens: runtime versus CI-gate

**De directe loaders blijven ongewijzigd `RuleContractError` gooien.** `ToetsregelManager.get_all_regels()` roept `valideer_regelset(...)` aan (`manager.py:420`) en vult de cache pas ná een geslaagde validatie (`:422`). Daar verandert niets.

**Alleen `ModularValidationService` vertaalt die fout naar `validation_unknown`**, zodat de applicatie beschikbaar blijft. Dat is exact het productbesluit op DEF-621 van 11 augustus: *"Startup van de hoofdapplicatie mag doorgaan; liveness blijft positief. Validation readiness wordt negatief."*

### Welke suites hard rood blijven bij repositorydrift

Deze draaien tegen de **échte** regelmap en veranderen niet mee:

| Suite | Wat rood blijft |
| -- | -- |
| `tests/unit/validation/test_rule_loader_failclosed.py` | beide échte laders op een kapotte set, geparametriseerd over `ToetsregelManager` en `CachedToetsregelManager` |
| `tests/unit/validation/test_rule_cache_runtime_contract.py` | `RuleCache` tegen de echte regelset |
| `tests/unit/validation/test_contractinvarianten_def676.py` | de zeven contractinvarianten |
| `tests/unit/validation/test_root_ssot_contract.py` | bindendheid van `toetsregels_config.yaml` als root-SSOT |
| `tests/unit/validation/test_rule_runtime_matrix.py` | de 53×-runtimematrix |

De runtimegrens maakt de **applicatie** beschikbaar; zij maakt de **repository** niet groen. Drift blijft in CI hard falen.

## 8. Veilige constructorstaat

Alle velden die het unknown-pad, `get_health_status()` en `validate_definition` nodig hebben, worden **vóór** de `try` geïnitialiseerd. Een `RuleContractError` in `_contractregel_ids()` (`:139`, vóór het laden) of in `_load_rules_from_manager()` mag nooit tot een ontbrekend attribuut leiden.

```
# __init__ — eerst een volledige, faalvrije beginsnapshot.
# Geen losse rulesetvelden meer: elk ruleset-afhankelijk gegeven zit in de
# snapshot, zodat er nooit een mengsel van twee generaties kan ontstaan.
self._state_lock = threading.Lock()
self._snapshot = self._lege_snapshot(fingerprint=None, oorzaak=None)

# dan pas de faalbare opbouw — één toewijzing, of hij lukt of hij lukt niet
try:
    self._snapshot = self._bouw_snapshot(
        fingerprint=bereken_fingerprint(self._fingerprintbronnen()),
    )
except RuleContractError as exc:
    logger.critical(...)                 # ongewijzigd niveau
    self._snapshot = self._lege_snapshot(fingerprint=None, oorzaak=exc)
    # bewust géén re-raise
```

`_lege_snapshot()` levert een **volledig ingevuld** `RuntimeSnapshot` met benoemde argumenten — lege collecties, een verse eigen `pattern_cache`, `readiness.ready is False` en reden `ruleset_incomplete`:

```
def _lege_snapshot(self, *, fingerprint, oorzaak) -> RuntimeSnapshot:
    return RuntimeSnapshot(
        fingerprint=fingerprint,
        readiness=bepaal_readiness(expected=(), loaded=()),
        contract_rule_ids=(),
        internal_rules=(),
        rule_records=MappingProxyType({}),
        json_rules=MappingProxyType({}),
        default_weights=MappingProxyType({}),
        pattern_cache={},
        rules_loaded_count=0,
        rules_expected_count=0,
        is_degraded_mode=True,
        degradation_reason=None if oorzaak is None else str(oorzaak),
    )
```

`_bouw_snapshot()` doet hetzelfde met de werkelijke generatie, eveneens met benoemde argumenten. **Alle drie de toestanden — beginstaat, succesvolle staat en foutstaat — worden met precies één toewijzing aan `self._snapshot` gepubliceerd.** Er is geen tussenvorm waarin een deel van de velden al vernieuwd is.

Na een fout draagt de snapshot lege collecties, is readiness onwaar, is evaluatie onbereikbaar en kan `get_health_status()` volledig worden ingevuld uit diezelfde snapshot. Faalt de root-SSOT zelf, dan is `expected_rule_ids` leeg — `ready` blijft onwaar en de machineleesbare reden blijft exact `ruleset_incomplete`; de oorzaak gaat alleen naar het log.

### Alle constructorpaden

| # | Pad | Vandaag | Na dit plan |
| -- | -- | -- | -- |
| 1 | manager compleet (53/53) | rules geladen | `ready=True`, normale validatie |
| 2 | manager retourneert leeg | baseline 7, geen fout | `validation_unknown` |
| 3 | generieke managerfout | degraded, `_rules_loaded_count = 7` | `validation_unknown`, degraded-vlag blijft |
| 4 | `RuleContractError` | **exceptie uit `__init__`; app start niet** | constructie slaagt; `validation_unknown` |
| 5 | `manager=None` | baseline, geen fout | `validation_unknown`, geen herstelpad |

## 9. Readiness en contract

`bepaal_readiness(expected, loaded)` → `ready` is waar dan en slechts dan als `loaded == expected` **en** `expected` niet leeg is. Die tweede voorwaarde sluit `0/0` af.

**Variant B+ — additief én gediscrimineerd.** `overall_score = 0.0` en `is_acceptable = false` zijn **uitsluitend compatibiliteitsplaceholders**: geen kwaliteitsscore, geen inhoudelijk oordeel. Alle gatende consumers (`export_service`, `definition_import_service`, `definition_edit_service`, `definition_orchestrator_v2`, `definition_workflow_service`) zijn daarmee gratis fail-closed. Een discriminated union zou 98 respectievelijk 62 leesplekken over 16 en 15 bestanden raken; een gemiste consumer kreeg dan een `KeyError` midden in een Streamlit-render. Er is geen externe consumer: `src/api/` bevat alleen `feature_status_api.py`, dat het resultaat niet serialiseert.

Schema 1.1.0 → **1.2.0**, `additionalProperties: false` blijft:

```
"allOf": [{
  "if":   { "properties": { "validation_status": { "const": "validation_unknown" } },
            "required": ["validation_status"] },
  "then": { "properties": { "overall_score": { "const": 0 },
                            "is_acceptable": { "const": false } },
            "required": ["unknown_reason", "validation_readiness"] }
}]
```

## 10. Readiness-consumer

**Het geconsumeerde oppervlak is het veld `validation_readiness` in `ValidationResult`, gelezen door `render_validation_detailed_list()` in `src/ui/components/validation_view.py:212`** — de gedeelde renderer, bereikt vanuit `validation_renderer.py:33`, `definition_edit_tab.py:1439` en `expert_review_tab.py:940`. Bij `validation_unknown` stopt die **vóór iedere score- of gateweergave** en toont "niet te bepalen".

`get_health_status()` krijgt de readinessvelden erbij voor monitoring, maar wordt **niet** als consumer geclaimd: nul call-sites in `src/`, en dit plan maakt er geen.

`validation_renderer.py` valt uit de wijzigingslijst — `render_validation_results()` (`:27-45`) delegeert integraal.

## 11. Bestanden, omvang en toestemming-gates

| # | Bestand | Actie | Geschat |
| -- | -- | -- | -- |
| 1 | `docs/plans/2026-08-31-DEF-621-fail-closed-validation-guard.md` | nieuw — **dit plan** | ~420 |
| 2 | `src/services/validation/readiness.py` | nieuw — `ValidationReadiness`, `RuntimeSnapshot`, `bepaal_readiness`, `bereken_fingerprint` | ~140 |
| 3 | `src/services/validation/interfaces.py` | wijzigen — `ValidationStatus`, `UnknownReason`, `ValidationReadinessDict`, drie velden, versie 1.2.0 | +~45 |
| 4 | `src/services/validation/modular_validation_service.py` (1589) | wijzigen — veilige constructorstaat, foutgrens, `_regelpad()`, `_ververs_state_indien_nodig()`, guard, `maak_unknown_resultaat()`, readiness in health | +~120 / −~3 |
| 5 | `src/toetsregels/rule_cache.py` (435) | wijzigen — `rules_load_complete` tegen de contract-ID-set | +~30 / −~2 |
| 6 | `docs/architectuur/contracts/schemas/validation_result.schema.json` | wijzigen — 1.2.0 + conditionele constraint | +~60 |
| 7 | `src/ui/components/validation_view.py` (336) | wijzigen — vroege stop bij `validation_unknown` | +~35 |
| 8 | `tests/unit/validation/test_validation_readiness.py` | nieuw | ~160 |
| 9 | `tests/unit/validation/test_validation_guard_failclosed.py` | nieuw | ~250 |
| 10 | `tests/unit/validation/test_ruleset_transitions.py` | nieuw | ~190 |

**Totaal: 10 bestanden — 1 plan, 5 code (4 gewijzigd, 1 nieuw), 1 schema, 3 test. ~1450 toegevoegde regels (~1030 exclusief het plan), ~5 verwijderde. 6 commits.**

Testboilerplate wordt gecomprimeerd met gedeelde fixtures (`regelmap_factory`, `service_met_set`) en `@pytest.mark.parametrize` over de ID-setvarianten en over beide managerpaden. Geen enkel vereist negatief bewijs vervalt daardoor.

**Waarom elk nieuw bestand nodig is:**

* `readiness.py` — pure, dependency-vrije logica (verzamelingsvergelijking, fingerprint, immutable state). In de 1589-regelige `modular_validation_service.py` plaatsen zou de bestaande god-objectschuld (DEF-424/DEF-312) vergroten en de logica onafhankelijk ontestbaar maken.
* Drie testbestanden — elk hoort bij precies één GREEN-commit (§12). Samenvoegen zou die één-op-één-koppeling breken en een falende commit ambigu maken.

### Werkelijke bestandsscope van commit 3 — bijgesteld tijdens uitvoering

De oorspronkelijke raming van negen bestanden was te krap. De guard raakt elke
test die `ModularValidationService` bouwt zónder complete regelset: die levert
nu `validation_unknown`, dus een lege violationslijst en geen `detailed_scores`.
Commit 3 telt daardoor **15 gewijzigde bestanden, ~922 toegevoegde en ~319
verwijderde regels**.

| Groep | Bestanden |
| -- | -- |
| Productie | `readiness.py` (`RuntimeSnapshot`), `modular_validation_service.py` |
| Testmigratie — synthetische snapshot | `test_evaluator_failclosed.py`, `test_error_blokkeert_acceptatie.py`, `test_score_invarianten.py`, `test_rule_runtime_matrix.py` |
| Testmigratie — echte contractmanager | `test_modular_validation_aggregation.py`, `test_modular_validation_heuristics.py`, `test_modular_validation_race_condition.py`, `test_modular_validation_determinism.py`, `test_evaluation_context_sharing.py`, `test_batch_validation.py`, `test_critical_paths.py` |
| Contractmigratie | `test_evaluation_coverage.py` |
| Nieuw bewijs | `test_validation_guard_failclosed.py` |

**De leidende regel bij migratie:** een test die *normale evaluatie* bedoelt,
krijgt de echte contractmanager via `get_toetsregel_manager()`. `manager=None`
blijft alleen staan waar `validation_unknown` juist het onderwerp is. Waar een
test op inhoud toetst, is bovendien `validation_status == "validated"`
toegevoegd — anders zou een lege unknown-uitkomst de assertie stil kunnen
waarmaken.

Twee inhoudelijke correcties waren onvermijdelijk, geen afzwakking:

* De soft-floor-case in `test_modular_validation_heuristics.py` en de
  positieve case in `test_batch_validation.py` gebruikten teksten die met de
  echte 53-regelset respectievelijk 0,55 en 0,52 scoren en dus **niet**
  acceptabel zijn. Beide zijn vervangen door een invoer die gemeten 0,64
  scoort: onder de drempel van 0,75, zonder blocking error, en daardoor via de
  soft floor acceptabel. Zonder die correctie zou de soft floor niet meer
  getoetst worden.
* `test_evaluation_coverage.py` is op drie plaatsen **herfundeerd** op het
  goedgekeurde contract. Het veiligheidsdoel blijft identiek — geen verzonnen
  noemer, geen valse volledige dekking — maar de guard vangt die toestanden nu
  een stap eerder af dan de dekkingsrapportage deed.

### Nog niet meegenomen — vervolg-inventaris

Vier bestanden bouwen ook met `manager=None`, maar blijven groen omdat zij op
vorm toetsen en niet op inhoud. Zij zijn bewust buiten commit 3 gehouden:

* `tests/integration/contracts/test_golden_definitions_contract.py` (fixture ontbreekt; suite skipt)
* `tests/integration/contracts/test_modular_validation_service_contract.py`
* `tests/integration/contracts/test_validation_result_schema.py`
* `tests/integration/performance/test_validation_performance_baseline.py`

### Commit 4 — scope uitgebreid met een productiedefect

De twee parameters van `test_beschadigde_contract_ssot_wordt_gezien_en_hersteld`
blijven na commit 3 **bewust rood**. Zij leggen een echt defect bloot, geen
testopzetfout:

* `ROOT_SSOT_PAD` zit in de fingerprint, dus een gewijzigde contract-SSOT
  triggert wél een herlaadpoging;
* maar `_contractregel_ids()` leest via het `lru_cache`-gedekte
  `root_contract_policy()`, dus bij die herlaadpoging worden opnieuw de **oude**
  contract-ID's gebruikt.

Gevolg: de fingerprint ziet de wijziging, de verwachte ID-set niet. Commit 4
mag daarom **naast `rule_cache.py` ook `modular_validation_service.py`
wijzigen**, om de contractpolicy vers uit `ROOT_SSOT_PAD` te laden in plaats
van uit de procescache.

`test_ruleset_transitions.py` wordt tot die tijd **niet** gewijzigd of
verzwakt. Voor commit 3 geldt exact 7 van 9 groen, met uitsluitend die twee
SSOT-parameters rood.

### Toestemming-gates — vóór implementatie

| # | Gate | Waarom geraakt |
| -- | -- | -- |
| 1 | **Kritieke laag** | AGENTS.md: `src/services/validation/` is *AI-validatie engine, KRITIEK: niet wijzigen zonder overleg*. Bestanden 2, 3, 4. `rule_cache.py` is de regelsetlader en valt materieel onder dezelfde bescherming. |
| 2 | **Omvang** | 10 bestanden, ~1450 regels; ruim boven >5 bestanden / >100 regels. |
| 3 | **Contractwijziging** | Schema en `interfaces.py` naar 1.2.0. Additief en niet-brekend, maar het blijft een contractwijziging. |
| 4 | **Gedragswijziging op een fail-closed pad** | De foutgrens uit §7-8 verandert wat de app doet bij `RuleContractError`: van "start niet" naar "start, validatie permanent unknown". Gedekt door het besluit van 11 augustus, maar te ingrijpend om stilzwijgend mee te nemen. |

**Geen code voordat deze vier expliciet zijn afgetekend.**

## 12. Uitvoering — RED/GREEN per commit

```
VENV=/Users/chrislehnen/Projecten/Definitie-app/.venv/bin
cd /Users/chrislehnen/Projecten/Definitie-app.worktrees/DEF-621-validation-guard
```

De worktree heeft **geen eigen `.venv`**. Sinds DEF-700 (`40c2a930`, gemerged in `origin/main`) roept de Makefile geen kale `pytest` meer aan: `PYTEST := $(PY) -m pytest` en elk testtarget hangt aan `check-python`, dat Python 3.13 afdwingt. Voor make-targets volstaat daarom `make PY="$VENV/python" <target>`; de `PATH`-manipulatie is niet langer nodig. **Directe `pytest`-runs gebruiken onverkort de absolute Python 3.13-venv.**

### Commit 0 — het plan zelf

```
git add docs/plans/2026-08-31-DEF-621-fail-closed-validation-guard.md
git commit -m "docs(DEF-621): implementatieplan fail-closed validatieguard"
```

### Commit 1 — RED: drie testbestanden

```
$VENV/python -m pytest \
  tests/unit/validation/test_validation_readiness.py \
  tests/unit/validation/test_validation_guard_failclosed.py \
  tests/unit/validation/test_ruleset_transitions.py -q
# VERWACHT: alle nieuwe tests FALEN (ImportError op readiness.py; KeyError op
# validation_status). Exit code 1.

git add tests/unit/validation/test_validation_readiness.py \
        tests/unit/validation/test_validation_guard_failclosed.py \
        tests/unit/validation/test_ruleset_transitions.py
git commit -m "test(DEF-621): RED — readiness, fail-closed guard en regelsettransities"
```

**`test_validation_readiness.py`** → groen door commit 2

| Case | Verwacht |
| -- | -- |
| volledige contractset (53/53) | `ready is True`, `missing == ()`, `unexpected == ()` |
| 52/53 | `ready is False`, `missing` bevat exact het ontbrekende ID |
| **52 gevonden, één verkeerd ID** | `ready is False`, `missing` én `unexpected` niet-leeg — *onderscheidt verzameling van telling* |
| fallback 7/53 | `ready is False`, 46 missende ID's |
| **0/0** | `ready is False` — lege verwachte set is nooit compleet |
| superset (54, waarvan 53 correct) | `ready is False`, `unexpected` niet-leeg |
| fingerprint wijzigt bij regelbestand | hash verandert |
| **fingerprint wijzigt bij `toetsregels_config.yaml`** | hash verandert |
| schemacase positief | unknown-resultaat valideert tegen 1.2.0 |
| **schemacase negatief** | `validation_unknown` mét `overall_score=0.7` is schema-**ongeldig** |

**`test_validation_guard_failclosed.py`** → groen door commit 3 (UI-cases door commit 5)

| Case | Verwacht |
| -- | -- |
| volledige set | `validation_status == "validated"`, normale score |
| elke incomplete set | `validation_status == "validation_unknown"`, `unknown_reason == "ruleset_incomplete"`, `overall_score == 0.0`, `is_acceptable is False`, `validation_readiness` aanwezig |
| **geen evaluator-, score- of gate-aanroep** | `_evaluate_rule`, `_calculate_category_scores`, `_evaluate_acceptance_gates` gemonkeypatcht naar `raise AssertionError`; guard returnt ervóór |
| constructorpaden 2, 3, 5 | `validation_unknown` |
| **constructorpad 4 — `RuleContractError`** | constructie **slaagt**; validatie geeft `validation_unknown` |
| **directe loader met dezelfde set** | `ToetsregelManager.get_all_regels()` **gooit** `RuleContractError` |
| root-SSOT onleesbaar | constructie slaagt; reden blijft exact `ruleset_incomplete` |
| negatieve/positieve readiness | `get_health_status()["validation_ready"]` respectievelijk `False`/`True` |
| UI bij `validation_unknown` | geen score-, gate- of percentagecomponent; "niet te bepalen" |
| UI bij `validated` | ongewijzigd |

**`test_ruleset_transitions.py`** → groen door commit 4

| Case | Verwacht |
| -- | -- |
| **compleet → incompleet, zelfde instantie, TTL niet verlopen** | tweede aanroep geeft `validation_unknown` |
| **incompleet → hersteld, zelfde instantie, TTL niet verlopen** | tweede aanroep geeft weer `validated` |
| **`toetsregels_config.yaml` beschadigd → hersteld** | idem, via de SSOT-bron van de fingerprint |
| ongewijzigde bronnen | géén herlezing (loader-teller blijft gelijk) |
| alle bovenstaande × beide managerpaden | identiek op `ToetsregelManager` en `CachedToetsregelManager` |

**De concurrency-case gebruikt echte threadconcurrentie.** `asyncio.gather` is hier onvoldoende: `_ververs_state_indien_nodig()` draait volledig synchroon vóór het eerste `await`, dus coroutines op één event loop interleaven daar nooit en de race wordt niet gereproduceerd.

Opzet: `threading.Barrier(n)` synchroniseert de start, een `ThreadPoolExecutor` draait `n` workers, en **elke worker roept zijn eigen `asyncio.run(service.validate_definition(...))`** aan. `_bouw_snapshot` is gemonkeypatcht naar `raise` nadat de fingerprint is gewijzigd, zodat elke thread tegelijk een mislukkende herlaadpoging raakt.

Bewijs: **geen enkele thread** krijgt een positief of gemengd resultaat. Elk van de `n` resultaten heeft `validation_status == "validation_unknown"`; geen resultaat draagt een score > 0, een niet-lege `passed_rules` of een `acceptance_gate`. De oude ready-generatie is aantoonbaar niet blijven staan.
| **mislukte herlaadpoging onder echte threadconcurrentie** | Zie hieronder — geen `asyncio.gather` |

### Commit 2 — GREEN: readiness en contract

```
$VENV/python -m pytest tests/unit/validation/test_validation_readiness.py -q
# VERWACHT: PASS (alle cases)

git add src/services/validation/readiness.py \
        src/services/validation/interfaces.py \
        docs/architectuur/contracts/schemas/validation_result.schema.json
git commit -m "feat(DEF-621): readiness, validation_unknown-contract en schema 1.2.0"
```

### Commit 3 — GREEN: constructorstaat, foutgrens en guard

**Eigenaarschap, ondubbelzinnig.** `readiness.py` krijgt in deze commit **uitsluitend** het datatype `RuntimeSnapshot` erbij — commit 2 leverde daar al `ValidationReadiness`, `bepaal_readiness()` en `bereken_fingerprint()`. De twee fabrieksmethoden `_lege_snapshot()` en `_bouw_snapshot()` horen bij `ModularValidationService`: zij hebben de manager, het regelpad en de contractpolicy nodig, en dat is servicestaat, geen readinesslogica. Daarom worden beide bestanden hier gestaged.

```
$VENV/python -m pytest tests/unit/validation/test_validation_guard_failclosed.py -q
# VERWACHT: PASS, behalve de twee UI-cases (die worden groen in commit 5)

git add src/services/validation/readiness.py \
        src/services/validation/modular_validation_service.py
git commit -m "feat(DEF-621): fail-closed guard en runtimegrens voor RuleContractError"
```

### Commit 4 — GREEN: cachetransities

```
$VENV/python -m pytest tests/unit/validation/test_ruleset_transitions.py -q
# VERWACHT: PASS (alle cases, beide managerpaden)

git add src/toetsregels/rule_cache.py \
        src/services/validation/modular_validation_service.py
git commit -m "fix(DEF-621): volledigheid tegen de contract-ID-set en herstel binnen TTL"
```

### Commit 5 — GREEN: gedeelde UI

```
$VENV/python -m pytest tests/unit/validation/ -q
# VERWACHT: PASS (volledige validatiesuite, inclusief de UI-cases)

git add src/ui/components/validation_view.py
git commit -m "feat(DEF-621): toon validatie niet te bepalen bij validation_unknown"
```

### Chokepoint-verificatie — vóór commit 3, geen aanname

```
grep -rn "_evaluate_json_rule\|_evaluate_rule\|_evaluate_via_registry" src --include="*.py"
```

Elke call-site buiten `ModularValidationService` is een tweede chokepoint en gaat terug naar dit plan. `src/validation/definitie_validator.py` en `src/services/validation/astra_validator.py` worden expliciet nagelopen op een levend pad.

## 13. Eindverificatie

```
VENV=/Users/chrislehnen/Projecten/Definitie-app/.venv/bin
cd /Users/chrislehnen/Projecten/Definitie-app.worktrees/DEF-621-validation-guard

$VENV/python -m pytest tests/unit/validation/ -q
make PY="$VENV/python" test
make PY="$VENV/python" test-markers-check
make PY="$VENV/python" lint
$VENV/python scripts/mypy_ratchet.py
git diff --check
shasum -a 256 data/definities.db     # vóór en ná identiek
```

## 14. Risico's

| Risico | Beheersing |
| -- | -- |
| Tweede chokepoint naar evaluatie | Grep-verificatie vóór commit 3 |
| Fingerprintkosten per aanroep | Target gemeten in commit 4; bij overschrijding heroverwegen en vastleggen |
| Corrupt bestand met gelijke grootte én mtime | Bekende grens (§5); vastgelegd, bewust niet opgelost |
| Lock-contentie bij hoge gelijktijdigheid | Lezers nemen lockvrij een snapshot; de lock omsluit alleen de zeldzame wissel |
| Bestaande tests die een score verwachten bij een incomplete set | Vóór commit 3 inventariseren; zo'n test legde het defect juist vast en moet meeveranderen |
| `test_contractconsistentie_def674.py` | Bij unknown is er geen gate; die tak expliciet erkennen |
| Contractdrift `types.py` versus `interfaces.py` | Buiten scope; met meting doorgegeven aan DEF-624 |

## 15. Definition of done

- [ ] Alle zes auditpunten hebben een test die zonder de implementatie faalt
- [ ] `52/53`, `52-met-verkeerd-ID`, `7/53` en `0/0` geven `validation_unknown` met reden `ruleset_incomplete`
- [ ] Aantoonbaar geen evaluator-, score- of gate-aanroep bij een incomplete set
- [ ] Alle vijf constructorpaden getest, inclusief `RuleContractError`
- [ ] Directe loader gooit nog steeds bij dezelfde kapotte set
- [ ] Beide transities bewezen op dezelfde instantie binnen een niet-verlopen TTL, over beide managerpaden, óók via de contract-SSOT
- [ ] Een mislukte herlaadpoging levert onder echte threadconcurrentie nooit een positieve of gedeeltelijke uitkomst
- [ ] De runtime-snapshot draagt alle ruleset-afhankelijke velden; het evaluatiepad leest er geen `self._…` meer voor
- [ ] `validation_view.py` stopt vóór elke score- of gateweergave
- [ ] Schema 1.2.0 wijst een `validation_unknown` met score ≠ 0 af
- [ ] Alle gates uit §13 groen via de expliciete venv
- [ ] `data/definities.db` vóór en ná identiek
- [ ] Notitie op DEF-624 over de `types.py`-drift
- [ ] Oplevercomment op DEF-621 met testbewijs
