# DEF-835 WP5a — correctie F2-restpunt en F4 (Claude-uitvoerder)

**Uitvoerder:** Claude Code CLI, sessie `914fccdd-7899-4d5c-8aa0-1c9ab334d7d4`.
**Opdracht:** `wp5a-opdracht-claude-F24-v1.md`, naar aanleiding van `wp5a-codex-F23-herreview-v1.md`.
**Correctiebasis:** manifest-v3 (herstelkopie `bewijs/wp5a-F24-vooraf-v1/`, 9/9 hashes gelijk aan manifest-v3).
**HEAD:** `d769276041e619103ace7bc66e65419d480dae99`, ongewijzigd.

Beide bevindingen zijn gecorrigeerd met één productiewijziging in `validation_orchestrator_v2.py`. Er zijn gerichte regressietests toegevoegd in `test_def835_int02_wrappers.py`. De andere zeven bestanden zijn bytegelijk aan manifest-v3; F1 en F3 blijven daardoor ongemoeid.

## 1. Wat is er veranderd

In `ValidationOrchestratorV2._beoordeel_int02` (`src/services/orchestrators/validation_orchestrator_v2.py:691`):

- **F4.** Het ophalen `getattr(dienst, "configuratie", None)` en de `callable`-controle staan nu binnen de bestaande `try` (r. 742).
  - Een property die een uitzondering opwerpt, komt daardoor in `except Exception` (r. 769) terecht, en dus in `_int02_fout`.
  - Uitkomst: INT-02 `error`/`MELDING_E`, zonder oordeel en zonder `assess`-aanroep.
  - Gelogd wordt alleen het uitzonderingstype, nooit de tekst.
- **F2-restpunt.** Na de document- en bindingscontrole, nog binnen dezelfde `try`, leest de wrapper dezelfde publieke snapshot opnieuw: `na = snapshot()` (r. 762).
  - Geen `Configuratie` → `invalid_configuration`.
  - Afwijkend van de voor-snapshot → `configuration_changed` (r. 767).
  - Een uitzondering uit de na-snapshot → uitzonderingstype via de bestaande foutgrens.
  - Pas daarna worden `METADATA_DOCUMENT` en `METADATA_CONFIGURATIE` (de voor-snapshot) gepubliceerd.
  - De na-snapshot is een configuratie- en routerlookup; er komt **geen extra modelcall** bij.
- De docstring beschrijft nu de F24-regel.

Er is niets gewijzigd aan de service, het contract, het schema of de dependencies. De wrapper leest geen privévelden van de service.

## 2. Nieuwe tests (alleen toegevoegd, niets verwijderd)

In `tests/unit/services/orchestrators/test_def835_int02_wrappers.py`:

| Test | Regel | Scenario | Verwachting |
|---|---|---|---|
| `test_f2_beleidswijziging_tijdens_modelcall_is_error[tekst,record]` | 990 | **Echte** `Int02AssessmentService`, via `Spion`. `_WijzigtTijdensAI` (r. 976) zet tijdens de afgewachte FakeAI-call, dus ná de interne routering, `_WijzigendeRouter.thinking` (r. 969) op `True`. | De dienst zelf levert een pass-document. De wrapper publiceert INT-02 `error`/`MELDING_E`, `review == {"actuality": None}` en geen assessment. `ai.calls == 1`: geen extra modelcall. |
| `test_f2_stabiele_configuratie_blijft_pass_current[tekst,record]` | 1011 | Dezelfde echte dienst zonder wijziging (guard tegen overcorrectie). | `pass`/`current`, binding-model `MODEL`, `ai.calls == 1`. |
| `test_f2_ongeldige_of_afwijkende_na_snapshot_is_error[…]` | 1055 | `_NaSnapshot` (r. 1030): de eerste `configuratie()` geldig, daarna `na` ∈ {ander model, `None`, `asdict(CONFIG)`, `RuntimeError(GEHEIM)`}, telkens × 2 routes. | `error`/`MELDING_E`, geen assessment, `GEHEIM` niet in de log; precies 1 `assess` en 2 snapshotlezingen. |
| `test_f4_falend_ophalen_van_snapshot_is_error_zonder_aanroep[tekst,record]` | 1090 | `_FalendeSnapshotProperty` (r. 1074): de property `configuratie` werpt `RuntimeError(GEHEIM)` op. | 0 `assess`-aanroepen, `validation_status == "validated"`, INT-02 `error`/`MELDING_E`, geen assessment. De geheime tekst staat niet in de log en niet in `json.dumps(resultaat)`. |

`GEHEIM` is een synthetische markeertekst zonder sleutelvorm.

## 3. TDD-bewijs

Alle RED- en GREEN-runs gebruiken dezelfde selectie:

```
<python> -m pytest tests/unit/services/orchestrators/test_def835_int02_wrappers.py \
  -k 'beleidswijziging_tijdens_modelcall or stabiele_configuratie_blijft or na_snapshot or f4_' \
  -p no:cacheprovider -p no:randomly --tb=short \
  -o addopts='-ra --strict-markers --import-mode=importlib'
```

### RED v1 (`bewijs/wp5a-F24-rood-v1.log`)

- Resultaat: exit 1, **12 failed, 2 passed**, tegen manifest-v3-productie.
- Kanttekening: de na-snapshottests faalden eerst op `assert 1 == 2` (het aantal snapshotlezingen). Dat mechanisme maskeerde de eigenlijke uitkomstfout.
- Daarom is in de na-snapshottest de volgorde van asserties omgedraaid: eerst de uitkomst (status, melding, assessment, log), dan het mechanisme. Er is geen testgeval weggehaald. v1 blijft bewaard.

### RED v2 (`bewijs/wp5a-F24-rood-v2.log`)

- Resultaat: exit 1, **12 failed, 2 passed**, tegen manifest-v3-productie (`validation_orchestrator_v2.py` `1d592767…354e`).
- Oorzaken:
  - 10× `'pass' == 'error'`: het F2-restpunt en de na-snapshotvarianten.
  - 2× `'validation_unknown' == 'validated'`: F4. In de ruwe log lekt de synthetische tekst via "Validation failed …".
- De 2 geslaagde tests zijn de stabiele guard, zoals bedoeld.
- Testbestand-SHA-256 in deze log: `374698831ff6b39ab5f460080714fb6668bfb9f6b6a1268a249dbd3aa073b3b7`. Dat is gelijk aan het eindbestand: het testbestand is na RED v2 niet meer gewijzigd.

### GREEN v1 (`bewijs/wp5a-F24-groen-v1.log`)

- Resultaat: **exit 127**, dus mislukt.
- Oorzaak: de relatieve `.venv/bin/python` bestaat niet (meer) in deze worktree. Er is geen test gedraaid. Het bestand is bewaard als eerlijk spoor.

### GREEN v2 (`bewijs/wp5a-F24-groen-v2.log`)

- Resultaat: exit 0, **14 passed, 60 deselected**.
- Draaiwijze: met `/Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python` (Python 3.13.15).
- De log bevat de SHA-256 van de productie- en testbestanden.

## 4. Regressie en lint

Voor de runs hieronder is `/Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python` gebruikt.

### Gerichte WP5a/WP2/O1-skillcontractset (`bewijs/wp5a-F24-set-v1.log`)

- Resultaat: exit 0, **293 passed**, 0 skipped.
- Omgeving: `DEF771_SKILLS_ROOT=/Users/chrislehnen/Projecten/_claude-global-setup/.worktrees/DEF-771-int02-skills/skills`.
- Commando: `pytest -q -p no:cacheprovider -p no:randomly -o addopts= -rs`.
- Bestanden: dezelfde zes als in `wp5a-F23-coordinator-v1.log`:
  - `test_def835_int02_wrappers.py`
  - `test_def835_int02_modular.py`
  - `test_def835_int02_container.py`
  - `test_def835_int02_assessment_service.py`
  - `test_def771_int02_o1.py`
  - `test_def771_int02_contract.py`
- Delta: 279 → 293, precies de 14 nieuwe F24-tests.

### Bredere gerichte regressie (`bewijs/wp5a-F24-regressie-v1.log`)

- Resultaat: exit 0, **2.966 passed**, 0 skipped.
- Set: dezelfde set als `wp5a-F23-regressie-v1.log`, nu mét `DEF771_SKILLS_ROOT`.
- Delta: F23 gaf 2.941 passed en 11 skipped, samen 2.952. Het verschil is +14 nieuwe tests, en de 11 skillcontracttests draaien nu echt in plaats van te skippen.

### Lint (`bewijs/wp5a-F24-lint-v1.log`), alle negen bestanden

| Tool | Resultaat |
|---|---|
| venv-Ruff 0.15.17 `check` | exit 0, All checks passed |
| `uvx ruff@0.16.5 check` | exit 0, All checks passed |
| Black 26.5.1 `--check` | exit 0, 9 files would be left unchanged |

### Niet herhaald (volgens opdracht)

- De volledige unit-suite.
- mypy. De bestaande 13 mypy-fouten in de twee WP1/WP2-bestanden blijven open en zijn niet aangeraakt.

## 5. Hashes

### Negen bestanden, SHA-256

| Bestand | Manifest-v3 / vooraf | Eind |
|---|---|---|
| `src/services/container.py` | `32a5ae78…e42a` | ongewijzigd |
| `src/services/orchestrators/definition_orchestrator_v2.py` | `db1093e5…d4ca` | ongewijzigd |
| `src/services/orchestrators/validation_orchestrator_v2.py` | `1d592767…354e` | `d9b0853a961d82fae372785dc988719d6bcde743c1e219157340a7a74d1bac5f` (1.001 r.) |
| `src/services/validation/modular_validation_service.py` | `84a9e330…b6c2` | ongewijzigd |
| `tests/unit/services/orchestrators/test_def835_int02_wrappers.py` | `17446549…b90f` | `374698831ff6b39ab5f460080714fb6668bfb9f6b6a1268a249dbd3aa073b3b7` (1.106 r.) |
| `tests/unit/validation/test_def835_int02_modular.py` | `ca09aa52…9400` | ongewijzigd |
| `tests/unit/services/test_def835_int02_container.py` | `5048a1c4…c9bf` | ongewijzigd |
| `src/services/validation/int02_assessment_service.py` | `99f1381e…7b3a` | ongewijzigd |
| `tests/unit/validation/test_def835_int02_assessment_service.py` | `1dcc0f9d…4e17` | ongewijzigd |

### Bewijsbestanden, SHA-256

| Bestand | SHA-256 |
|---|---|
| `bewijs/wp5a-F24-rood-v1.log` | `4da60f2e1ee77afaa9f70df646ae86f5e31d1f7b55a6de57f60d86e152a4507f` |
| `bewijs/wp5a-F24-rood-v2.log` | `592414458645cfdfc0770dec478c4d1eaa696cc89522a7f6593dc4b79e236fd0` |
| `bewijs/wp5a-F24-groen-v1.log` (exit 127) | `526d45997b6697e70668519f1fef6ae6d432fef1a39adb9188ce20035c566fd3` |
| `bewijs/wp5a-F24-groen-v2.log` | `9e72f0085f9f41892e276eaa2f67bb1f37f09c59b979aadb6933bdb6e68e26d3` |
| `bewijs/wp5a-F24-set-v1.log` | `bd10970c88f2448f83d0ad7f63f411182c19f6946c94d281f2c695be9ab595f9` |
| `bewijs/wp5a-F24-regressie-v1.log` | `29087cfa38c16126a051b3f3b1ea2b2368e7d5109b6b57c412d437fb7cb9a7c0` |
| `bewijs/wp5a-F24-lint-v1.log` | `3e350700ee2921681dafc93c8c324348a957fa7fa61cf29953168ba246cb4b92` |
| `bewijs/wp5a-F24-correctiediff-v1.patch` (213 r.) | `3db38e9fe4b69f0ed292c74258e76cd61c8a7b6a54e2995a983b96e7983866cc` |
| `bewijs/wp5a-F24-werkboomdiff-v1.patch` (2.292 r.) | `052ab21212d7122419e64a1a12a8915639193a7dd7634ecaf083b06eeae2f1cd` |

### Reconstructie, gecontroleerd in `/tmp`

- **Correctiediff:** `patch -p1` op een kopie van `wp5a-F24-vooraf-v1` gaf exit 0 en 9/9 bestanden bytegelijk aan de werkboom.
- **Werkboomdiff:** `git apply` op een `git archive HEAD src tests`-export (in een los `/tmp`-repo) gaf exit 0 en 9/9 bytegelijk.
- **Opbouw van de werkboomdiff:**
  - Zes getrackte bestanden via `git diff HEAD`.
  - Drie ongetrackte tests via `git diff --no-index /dev/null`.
- **Opbouw van de correctiediff:** per bestand `git diff --no-index vooraf werkboom`, met de padprefix herschreven naar `a/`/`b/`. Alleen `validation_orchestrator_v2.py` en `test_def835_int02_wrappers.py` verschillen.

## 6. Wat wel en niet gegarandeerd is

**Wel:**

- Een beleids- of configuratiewijziging die tussen de voor-snapshot en de na-snapshot zichtbaar wordt in de publieke `configuratie()`, levert `error` zonder oordeel en nooit stil `pass`/`current`. Dat geldt ook voor een wijziging ná de interne routering van `assess`, tijdens de afgewachte modelcall; beide routes zijn getest met de echte dienst.
- Een ongeldige of falende na-snapshot levert eveneens `error`.
- Een falende `configuratie`-lookup levert `error` zonder aanroep en zonder ruwe tekst in log of resultaat.
- Er komen geen extra modelcalls bij.
- Stabiele geldige beoordelingen blijven `pass`/`current`.

**Niet, eerlijk benoemd:**

- **Na-snapshot als publicatiemoment.** Tussen de na-snapshot en het vullen van de metadata zit geen `await`: de controle en de publicatie in `context_dict` gebeuren synchroon in dezelfde coroutinestap. De evaluator leest die metadata later in dezelfde validatie en werkt met de vastgelegde voor-snapshot, niet met een live-lookup.
- **Latere wijzigingen.** Een wijziging ná de na-snapshot, dus na publicatie, valt buiten deze controle. `current` betekent: gelijk aan de actuele publieke configuratie op het moment van publicatie.
- **Heen-en-terugwijziging.** Een wijziging die vóór de na-snapshot weer volledig is teruggedraaid (A→B→A), is per definitie niet zichtbaar in de voor- en na-vergelijking. In dat geval is de documentbinding gelijk aan de actuele configuratie bij publicatie, dus WP1 zou het document dan ook `current` noemen.
- **Onbewezen onderdelen.** Dit is een vaststelling van de meetgrens, geen waiver voor het afgekeurde venster uit F23. Niet bewezen zijn:
  - de providerattestatie;
  - opslag/C118;
  - de modelkwalificatie;
  - de totale afronding van WP5a/O2.
- **Codex-reprobestand.** Het script `/private/tmp/wp5a-codex-F23-repro-20260928-v1.py` wijst naar de reviewkopie in `/private/tmp/def835-wp2-review-20260927`, niet naar deze werkboom. Ik heb het niet gedraaid; het dekt deze correctie dus niet. De gelijkwaardige scenario's zitten in de nieuwe tests.

## 7. Git-staat en werkwijze

- **HEAD en index:** HEAD is `d769276041e619103ace7bc66e65419d480dae99`, ongewijzigd. De index is leeg (0 gestagede bestanden).
- **Wat ik niet heb gedaan:**
  - geen stage, commit, write-tree, push of merge;
  - geen livecalls, Actions of productiedata;
  - geen wijziging aan dependencies, schema of contract.
- **Verwijderd:** niets. Er zijn geen testgevallen weggehaald en geen bestaande rapporten overschreven.
- **Nieuwe dossierbestanden:**
  - `bewijs/wp5a-F24-rood-v1.log`
  - `bewijs/wp5a-F24-rood-v2.log`
  - `bewijs/wp5a-F24-groen-v1.log`
  - `bewijs/wp5a-F24-groen-v2.log`
  - `bewijs/wp5a-F24-set-v1.log`
  - `bewijs/wp5a-F24-regressie-v1.log`
  - `bewijs/wp5a-F24-lint-v1.log`
  - `bewijs/wp5a-F24-correctiediff-v1.patch`
  - `bewijs/wp5a-F24-werkboomdiff-v1.patch`
  - dit verslag.
- **Niet aangeraakt:** de coördinatorbestanden `wp5a-F24-claude-stream-v1.jsonl`, `wp5a-F24-claude-stderr-v1.log` en `wp5a-F24-vooraf-v1/`.
- **Tijdelijke controlemappen buiten de repository:** `/tmp/wp5a-F24-check-*` en `/tmp/wp5a-F24-head-*`. Daar is niets verwijderd.
- **Pogingen:**
  - RED: twee runs (v1 en v2, zie §3).
  - GREEN: twee runs (v1 exit 127, v2 groen).
  - Lint: één geblokkeerde aanroep, geweigerd door de security-hook vanwege `eval`, zonder uitvoer of bestand; de tweede aanroep slaagde.
  - Alles binnen de grens van 3 pogingen.
- Geen agents, reviewers of extra CLI-sessies gestart.

Klaar voor herreview door dezelfde Codex-reviewer. De volledige correctiedelta en de volledige negenbestandenpatch staan hieronder letterlijk als bijlage; ze zijn bytegelijk aan de patchbestanden met de hashes uit §5.

## Bijlage A — correctiedelta t.o.v. `wp5a-F24-vooraf-v1` (`bewijs/wp5a-F24-correctiediff-v1.patch`)

~~~~~diff
diff --git a/src/services/orchestrators/validation_orchestrator_v2.py b/src/services/orchestrators/validation_orchestrator_v2.py
index 53a1ad7af..f88cc3233 100644
--- a/src/services/orchestrators/validation_orchestrator_v2.py
+++ b/src/services/orchestrators/validation_orchestrator_v2.py
@@ -709,6 +709,11 @@ class ValidationOrchestratorV2(ValidationOrchestratorInterface):
         snapshot, dan geen aanroep; wijkt de volledige documentbinding af van
         `bereken_binding(verse invoer, snapshot)`, ook door een wijziging rond
         de aanroep, dan een technische fout. De evaluator krijgt de snapshot.
+        Review F24: vóór publicatie wordt dezelfde publieke snapshot opnieuw
+        gelezen (geen extra modelcall); is die ongeldig of wijkt hij af van de
+        voor-snapshot — ook door een wijziging ná de interne routering — dan
+        een technische fout. Ook het ophalen van `configuratie` valt binnen
+        de veilige foutgrens.
         """
         for sleutel in _INT02_WRAPPERSLEUTELS:
             context_dict.pop(sleutel, None)
@@ -733,11 +738,13 @@ class ValidationOrchestratorV2(ValidationOrchestratorInterface):
             return
         if ontbrekende_invoer(invoer):
             return
-        snapshot = getattr(dienst, "configuratie", None)
-        if not callable(snapshot):
-            self._int02_fout(context_dict, "configuration_unavailable", correlation_id)
-            return
         try:
+            snapshot = getattr(dienst, "configuratie", None)
+            if not callable(snapshot):
+                self._int02_fout(
+                    context_dict, "configuration_unavailable", correlation_id
+                )
+                return
             verwacht = snapshot()
             if not isinstance(verwacht, Configuratie):
                 self._int02_fout(context_dict, "invalid_configuration", correlation_id)
@@ -752,6 +759,13 @@ class ValidationOrchestratorV2(ValidationOrchestratorInterface):
             ):
                 self._int02_fout(context_dict, "binding_mismatch", correlation_id)
                 return
+            na = snapshot()
+            if not isinstance(na, Configuratie):
+                self._int02_fout(context_dict, "invalid_configuration", correlation_id)
+                return
+            if na != verwacht:
+                self._int02_fout(context_dict, "configuration_changed", correlation_id)
+                return
         except Exception as exc:
             self._int02_fout(context_dict, type(exc).__name__, correlation_id)
             return
diff --git a/tests/unit/services/orchestrators/test_def835_int02_wrappers.py b/tests/unit/services/orchestrators/test_def835_int02_wrappers.py
index d660c0bcf..9d5a3ffec 100644
--- a/tests/unit/services/orchestrators/test_def835_int02_wrappers.py
+++ b/tests/unit/services/orchestrators/test_def835_int02_wrappers.py
@@ -22,6 +22,7 @@ vallen buiten dit pakket.
 
 from __future__ import annotations
 
+import asyncio
 import copy
 import json
 import logging
@@ -954,3 +955,152 @@ async def test_f2_snapshot_wordt_voor_de_aanroep_vastgelegd(o2_service):
     assert detail["assessment"] == (
         beoordeel(_invoer(), CONFIG, _pass_respons(), VOLTOOID).als_dict()
     )
+
+
+# --- F2-restpunt en F4 (herreview WP5a F2/F3) -----------------------------------
+#
+# F2-restpunt: ook een wijziging ná de interne routering, tijdens de awaited
+# modelcall, mag nooit pass/current worden. De wrapper leest daarom na de
+# aanroep opnieuw de publieke snapshot en eist dat die geldig is en gelijk aan
+# de voor-snapshot. F4: ook het ophalen van `configuratie` zelf valt binnen de
+# veilige foutgrens.
+
+
+class _WijzigendeRouter(FakeRouter):
+    thinking = False
+
+    def thinking_default_on(self, model, provider=None):
+        return self.thinking
+
+
+class _WijzigtTijdensAI(FakeAI):
+    """Wijzigt het routerbeleid tijdens de awaited modelcall (na de routering)."""
+
+    def __init__(self, router):
+        super().__init__(_pass_respons())
+        self.router = router
+
+    async def generate_definition(self, prompt, **kwargs):
+        await asyncio.sleep(0)
+        self.router.thinking = True
+        return await super().generate_definition(prompt, **kwargs)
+
+
+@pytest.mark.parametrize("route", ROUTES)
+async def test_f2_beleidswijziging_tijdens_modelcall_is_error(o2_service, route):
+    router = _WijzigendeRouter()
+    ai = _WijzigtTijdensAI(router)
+    spion = Spion(
+        Int02AssessmentService(ai, router, profiel=_profiel(), budget=_budget())
+    )
+    orch = ValidationOrchestratorV2(o2_service, int02_assessment_service=spion)
+
+    resultaat = await route(orch)
+
+    assert ai.calls == 1  # geen extra modelcall
+    (beoordeling,) = spion.resultaten
+    assert beoordeling.document.status == "pass"  # de dienst zelf gaf een oordeel
+    detail = _int02(resultaat)
+    assert detail["status"] == "error"
+    assert detail["parts"][0]["reason"] == MELDING_E
+    assert detail["review"] == {"actuality": None}
+    assert detail["assessment"] is None
+
+
+@pytest.mark.parametrize("route", ROUTES)
+async def test_f2_stabiele_configuratie_blijft_pass_current(o2_service, route):
+    router = _WijzigendeRouter()
+    ai = FakeAI(_pass_respons())
+    orch = ValidationOrchestratorV2(
+        o2_service,
+        int02_assessment_service=Int02AssessmentService(
+            ai, router, profiel=_profiel(), budget=_budget()
+        ),
+    )
+
+    resultaat = await route(orch)
+
+    assert ai.calls == 1
+    detail = _int02(resultaat)
+    assert detail["status"] == "pass"
+    assert detail["review"]["actuality"] == "current"
+    assert detail["assessment"]["binding"]["model"] == MODEL
+
+
+class _NaSnapshot(FakeDienst):
+    """Voor-snapshot geldig (`CONFIG`); elke latere snapshot is `na`."""
+
+    def __init__(self, na):
+        super().__init__(_pass_respons())
+        self.na = na
+
+    def configuratie(self):
+        self.snapshots_gelezen += 1
+        waarde = CONFIG if self.snapshots_gelezen == 1 else self.na
+        if isinstance(waarde, BaseException):
+            raise waarde
+        return waarde
+
+
+@pytest.mark.parametrize("route", ROUTES)
+@pytest.mark.parametrize(
+    "na",
+    [
+        pytest.param(replace(CONFIG, model="na-model"), id="gewijzigd"),
+        pytest.param(None, id="none"),
+        pytest.param(asdict(CONFIG), id="dict"),
+        pytest.param(RuntimeError(GEHEIM), id="uitzondering"),
+    ],
+)
+async def test_f2_ongeldige_of_afwijkende_na_snapshot_is_error(
+    o2_service, route, na, caplog
+):
+    dienst = _NaSnapshot(na)
+    orch = ValidationOrchestratorV2(o2_service, int02_assessment_service=dienst)
+
+    with caplog.at_level(logging.DEBUG):
+        resultaat = await route(orch)
+
+    # Eerst de uitkomst, daarna het mechanisme (voor- en na-snapshot).
+    detail = _int02(resultaat)
+    assert detail["status"] == "error"
+    assert detail["parts"][0]["reason"] == MELDING_E
+    assert detail["assessment"] is None
+    assert GEHEIM not in caplog.text
+    assert len(dienst.calls) == 1
+    assert dienst.snapshots_gelezen == 2
+
+
+class _FalendeSnapshotProperty:
+    """Het ophalen van `configuratie` zelf faalt (F4-foutinjectie)."""
+
+    def __init__(self):
+        self.calls: list[Any] = []
+
+    @property
+    def configuratie(self):
+        raise RuntimeError(GEHEIM)
+
+    async def assess(self, invoer, **kwargs):  # pragma: no cover - mag niet
+        self.calls.append(invoer)
+        raise AssertionError("assess mag niet worden bereikt")
+
+
+@pytest.mark.parametrize("route", ROUTES)
+async def test_f4_falend_ophalen_van_snapshot_is_error_zonder_aanroep(
+    o2_service, route, caplog
+):
+    dienst = _FalendeSnapshotProperty()
+    orch = ValidationOrchestratorV2(o2_service, int02_assessment_service=dienst)
+
+    with caplog.at_level(logging.DEBUG):
+        resultaat = await route(orch)
+
+    assert dienst.calls == []
+    assert resultaat["validation_status"] == "validated"
+    detail = _int02(resultaat)
+    assert detail["status"] == "error"
+    assert detail["parts"][0]["reason"] == MELDING_E
+    assert detail["assessment"] is None
+    assert GEHEIM not in caplog.text
+    assert "GEHEIME" not in json.dumps(resultaat, default=str)
~~~~~

## Bijlage B — volledige negenbestandenpatch t.o.v. HEAD `d769276` (`bewijs/wp5a-F24-werkboomdiff-v1.patch`)

~~~~~diff
diff --git a/src/services/container.py b/src/services/container.py
index d6c355a9d..2e1c79b5d 100644
--- a/src/services/container.py
+++ b/src/services/container.py
@@ -59,6 +59,11 @@ if TYPE_CHECKING:
     from services.synonym_orchestrator import SynonymOrchestrator
     from services.synonym_suggester import SynonymSuggester
     from services.validation.ess03_assessment_service import Ess03AssessmentService
+    from services.validation.int02_assessment_service import (
+        Budget,
+        Int02AssessmentService,
+        Modelprofiel,
+    )
     from services.validation.int03_assessment_service import Int03AssessmentService
     from services.validation.interfaces import ValidationOrchestratorInterface
     from services.validation.source_assessment_service import SourceAssessmentService
@@ -348,6 +353,31 @@ class ServiceContainer:
             "Int03AssessmentService", self._instances["int03_assessment_service"]
         )
 
+    def int02_assessment_service(
+        self, *, profiel: "Modelprofiel", budget: "Budget"
+    ) -> "Int02AssessmentService":
+        """De INT-02-beoordeling (O2, DEF-835 WP5a) — alleen op expliciet verzoek.
+
+        Profiel en budget zijn verplicht en worden nooit afgeleid (geen
+        default, geen routerdefault, geen profiel van een andere regel). Geen
+        singleton en geen bedrading in `orchestrator()`: de actieve route
+        blijft O1. De aanroeper injecteert de dienst zelf, bijvoorbeeld in
+        `DefinitionOrchestratorV2(int02_assessment_service=...)`.
+        """
+        from services.validation.int02_assessment_service import (
+            Budget,
+            Int02AssessmentService,
+            Int02ServiceConfigError,
+            Modelprofiel,
+        )
+
+        if not isinstance(profiel, Modelprofiel) or not isinstance(budget, Budget):
+            msg = "INT-02: een expliciet Modelprofiel en Budget zijn vereist"
+            raise Int02ServiceConfigError(msg)
+        return Int02AssessmentService(
+            self.ai_service(), self.model_router(), profiel=profiel, budget=budget
+        )
+
     def orchestrator(self) -> DefinitionOrchestratorInterface:
         """
         Get of create DefinitionOrchestrator instance.
diff --git a/src/services/orchestrators/definition_orchestrator_v2.py b/src/services/orchestrators/definition_orchestrator_v2.py
index 4676100d2..d68ca8424 100644
--- a/src/services/orchestrators/definition_orchestrator_v2.py
+++ b/src/services/orchestrators/definition_orchestrator_v2.py
@@ -145,6 +145,8 @@ class DefinitionOrchestratorV2(DefinitionOrchestratorInterface):
         ess03_assessment_service: Any | None = None,
         # DEF-772: AI-verwijzingsbeoordeling (INT-03); idem
         int03_assessment_service: Any | None = None,
+        # DEF-835 WP5a: INT-02-beoordeling (O2); alleen expliciet, geen lazy default
+        int02_assessment_service: Any | None = None,
     ):
         """
         Clean dependency injection - no session state access.
@@ -200,6 +202,8 @@ class DefinitionOrchestratorV2(DefinitionOrchestratorInterface):
         self._ess03_assessment_service = ess03_assessment_service
         # DEF-772: verwijzingsbeoordeling; idem
         self._int03_assessment_service = int03_assessment_service
+        # DEF-835 WP5a: bewust geen lazy property — zonder injectie geen dienst
+        self.int02_assessment_service = int02_assessment_service
 
         logger.info(
             "DefinitionOrchestratorV2 initialized with configuration: "
@@ -358,6 +362,8 @@ class DefinitionOrchestratorV2(DefinitionOrchestratorInterface):
                 ess03_assessment_service=self.ess03_assessment_service,
                 # DEF-772: idem voor de verwijzingsbeoordeling (INT-03).
                 int03_assessment_service=self.int03_assessment_service,
+                # DEF-835 WP5a: INT-02 (O2) alleen als hij expliciet is geïnjecteerd.
+                int02_assessment_service=self.int02_assessment_service,
             )
 
             logger.debug("DEF-90: ValidationOrchestratorV2 initialized successfully")
diff --git a/src/services/orchestrators/validation_orchestrator_v2.py b/src/services/orchestrators/validation_orchestrator_v2.py
index 8f7757383..f88cc3233 100644
--- a/src/services/orchestrators/validation_orchestrator_v2.py
+++ b/src/services/orchestrators/validation_orchestrator_v2.py
@@ -15,6 +15,14 @@ from typing import Any
 
 from domain.context.normalisatie import canoniseer_contextlijst
 from domain.ess03 import contract as ess03_contract
+from domain.int02.contract import (
+    Beoordelingsdocument,
+    Configuratie,
+    Int02ContractError,
+    bereken_binding,
+    maak_invoer,
+    ontbrekende_invoer,
+)
 from domain.int03 import contract as int03_contract
 from domain.sources.contract import (
     beoordeling_niet_beschikbaar,
@@ -27,6 +35,12 @@ from services.interfaces import (
     Definition,
     ValidationServiceInterface,
 )
+from services.validation.evaluators.decision_rule_assessment import (
+    METADATA_BEDOELING,
+    METADATA_BRONNEN,
+    METADATA_CONFIGURATIE,
+    METADATA_DOCUMENT,
+)
 from services.validation.interfaces import (
     ValidationContext,
     ValidationOrchestratorInterface,
@@ -34,9 +48,21 @@ from services.validation.interfaces import (
     ValidationResult,
 )
 from services.validation.mappers import create_degraded_result, ensure_schema_compliance
+from toetsregels.runtime_contract import EvaluatorType
 
 logger = logging.getLogger(__name__)
 
+#: DEF-835 WP5a: INT-02-sleutels die alleen de wrapper zelf zet; een
+#: aanroeperwaarde wordt altijd weggegooid (nooit een kortere weg naar een oordeel).
+_INT02_WRAPPERSLEUTELS = (METADATA_DOCUMENT, METADATA_CONFIGURATIE, "int02_assessment")
+_INT02_CONTEXTVELDEN = (
+    "organisatorische_context",
+    "juridische_context",
+    "wettelijke_basis",
+)
+#: Bewust geen `Configuratie`: de O2-evaluator maakt hiervan `error`, zonder oordeel.
+_INT02_TECHNISCHE_FOUT = "int02_technical_error"
+
 
 #: Uitkomst van de alias-normalisatie naast de gekozen lijst.
 _ALIAS_OK = None
@@ -117,6 +143,12 @@ def _technische_blokkade(
     return None
 
 
+def _leeg_bij_none(waarde: Any) -> Any:
+    """None is leeg; elk ander type gaat ongewijzigd naar de WP1-validatie
+    (dezelfde lezing als de INT-02-O2-evaluator)."""
+    return [] if waarde is None else waarde
+
+
 class ValidationOrchestratorV2(ValidationOrchestratorInterface):
     """Orchestrator voor validatie (V2).
 
@@ -137,6 +169,7 @@ class ValidationOrchestratorV2(ValidationOrchestratorInterface):
         source_assessment_service: Any | None = None,
         ess03_assessment_service: Any | None = None,
         int03_assessment_service: Any | None = None,
+        int02_assessment_service: Any | None = None,
     ) -> None:
         if validation_service is None:
             msg = "validation_service is vereist"
@@ -152,6 +185,10 @@ class ValidationOrchestratorV2(ValidationOrchestratorInterface):
         # DEF-772: de AI-verwijzingsbeoordeling (INT-03) is standaard
         # onderdeel van elke validatie met tekst; idem.
         self.int03_assessment_service = int03_assessment_service
+        # DEF-835 WP5a: de INT-02-beoordeling (O2) is géén standaardonderdeel.
+        # Alleen een expliciet geïnjecteerde dienst, en alleen als de actieve
+        # regelset INT-02 op `decision_rule_assessment` zet; geen default.
+        self.int02_assessment_service = int02_assessment_service
 
     async def validate_text(
         self,
@@ -227,6 +264,8 @@ class ValidationOrchestratorV2(ValidationOrchestratorInterface):
                 )
                 if verwijzingen is not None:
                     context_dict["int03_assessment"] = verwijzingen
+                # DEF-835 WP5a: INT-02 (O2) alleen via de expliciete dienst.
+                await self._beoordeel_int02(begrip, context_dict, correlation_id)
 
                 # Call underlying service
                 result = await self.validation_service.validate_definition(
@@ -310,6 +349,10 @@ class ValidationOrchestratorV2(ValidationOrchestratorInterface):
                 )
                 if verwijzingen is not None:
                     context_dict["int03_assessment"] = verwijzingen
+                # DEF-835 WP5a: idem INT-02 (O2), op de gezaghebbende recordkern.
+                await self._beoordeel_int02(
+                    definition.begrip, context_dict, correlation_id
+                )
 
                 text = definition.definitie
 
@@ -645,6 +688,117 @@ class ValidationOrchestratorV2(ValidationOrchestratorInterface):
             )
         return document
 
+    async def _beoordeel_int02(
+        self, begrip: str, context_dict: dict[str, Any], correlation_id: str
+    ) -> None:
+        """De INT-02-beoordeling (O2) voor exact deze validatie (DEF-835 WP5a).
+
+        Aanroeperwaarden onder `int02_document`, `int02_configuratie` en
+        `int02_assessment` worden altijd weggegooid. Daarna, fail-closed:
+        (1) zonder geïnjecteerde dienst of als de actieve regelset INT-02 niet
+        op `decision_rule_assessment` zet geen aanroep — de evaluator meldt dan
+        zelf NE of 'nog te beoordelen' (O1 blijft ongemoeid); (2) de WP1-invoer
+        komt uit exact `record_text` en de context, precies zoals de evaluator
+        haar bouwt — ongeldige invoer is een technische fout, lege kern of
+        ontbrekende context NE, beide zonder aanroep; (3) een fout in de
+        dienst, een resultaat zonder WP1-document of een document voor andere
+        invoer is een technische fout, nooit een oordeel. Alleen een
+        foutsoort of uitzonderingstype wordt gelogd. Review F2: de verwachte
+        configuratie is de publieke dienstsnapshot `configuratie()`, vastgelegd
+        vóór `assess` — nooit het teruggegeven document. Ontbreekt of faalt die
+        snapshot, dan geen aanroep; wijkt de volledige documentbinding af van
+        `bereken_binding(verse invoer, snapshot)`, ook door een wijziging rond
+        de aanroep, dan een technische fout. De evaluator krijgt de snapshot.
+        Review F24: vóór publicatie wordt dezelfde publieke snapshot opnieuw
+        gelezen (geen extra modelcall); is die ongeldig of wijkt hij af van de
+        voor-snapshot — ook door een wijziging ná de interne routering — dan
+        een technische fout. Ook het ophalen van `configuratie` valt binnen
+        de veilige foutgrens.
+        """
+        for sleutel in _INT02_WRAPPERSLEUTELS:
+            context_dict.pop(sleutel, None)
+        dienst = self.int02_assessment_service
+        if dienst is None or not self._int02_is_o2(correlation_id):
+            return
+        # Ongetypeerd: een aanwezige niet-tekst weigert WP1 hieronder (fout).
+        kern: Any = context_dict.get("record_text")
+        try:
+            invoer = maak_invoer(
+                begrip=begrip,
+                kern=kern,
+                bedoeling=context_dict.get(METADATA_BEDOELING),
+                bronnen=_leeg_bij_none(context_dict.get(METADATA_BRONNEN)),
+                **{
+                    veld: _leeg_bij_none(context_dict.get(veld))
+                    for veld in _INT02_CONTEXTVELDEN
+                },
+            )
+        except Int02ContractError:
+            self._int02_fout(context_dict, "invalid_input", correlation_id)
+            return
+        if ontbrekende_invoer(invoer):
+            return
+        try:
+            snapshot = getattr(dienst, "configuratie", None)
+            if not callable(snapshot):
+                self._int02_fout(
+                    context_dict, "configuration_unavailable", correlation_id
+                )
+                return
+            verwacht = snapshot()
+            if not isinstance(verwacht, Configuratie):
+                self._int02_fout(context_dict, "invalid_configuration", correlation_id)
+                return
+            beoordeling = await dienst.assess(invoer, correlation_id=correlation_id)
+            document = getattr(beoordeling, "document", None)
+            if not isinstance(document, Beoordelingsdocument):
+                self._int02_fout(context_dict, "invalid_result", correlation_id)
+                return
+            if document.invoer != invoer or document.binding != bereken_binding(
+                invoer, verwacht
+            ):
+                self._int02_fout(context_dict, "binding_mismatch", correlation_id)
+                return
+            na = snapshot()
+            if not isinstance(na, Configuratie):
+                self._int02_fout(context_dict, "invalid_configuration", correlation_id)
+                return
+            if na != verwacht:
+                self._int02_fout(context_dict, "configuration_changed", correlation_id)
+                return
+        except Exception as exc:
+            self._int02_fout(context_dict, type(exc).__name__, correlation_id)
+            return
+        context_dict[METADATA_DOCUMENT] = document
+        context_dict[METADATA_CONFIGURATIE] = verwacht
+
+    def _int02_is_o2(self, correlation_id: str) -> bool:
+        """Zet de actieve regelset INT-02 op `decision_rule_assessment`?"""
+        evaluator_voor = getattr(self.validation_service, "evaluator_voor", None)
+        if not callable(evaluator_voor):
+            return False
+        try:
+            return evaluator_voor("INT-02") is EvaluatorType.DECISION_RULE_ASSESSMENT
+        except Exception as exc:
+            logger.error(
+                "DEF-835: INT-02-evaluator niet bepaald (correlation_id=%s): %s",
+                correlation_id,
+                type(exc).__name__,
+            )
+            return False
+
+    @staticmethod
+    def _int02_fout(
+        context_dict: dict[str, Any], soort: str, correlation_id: str
+    ) -> None:
+        """Technische fout: de evaluator geeft `error`, zonder inhoudelijk oordeel."""
+        logger.error(
+            "DEF-835: INT-02-beoordeling niet bruikbaar (correlation_id=%s): %s",
+            correlation_id,
+            soort,
+        )
+        context_dict[METADATA_CONFIGURATIE] = _INT02_TECHNISCHE_FOUT
+
     @staticmethod
     def _met_beoordelingen(
         result: ValidationResult,
diff --git a/src/services/validation/int02_assessment_service.py b/src/services/validation/int02_assessment_service.py
index 6510a3a65..91762ab5e 100644
--- a/src/services/validation/int02_assessment_service.py
+++ b/src/services/validation/int02_assessment_service.py
@@ -611,6 +611,18 @@ class Int02AssessmentService:
         self._onthoud(sleutel, resultaat)
         return resultaat
 
+    def configuratie(self) -> Configuratie:
+        """Onafhankelijke snapshot van de actuele WP1-configuratie (DEF-835 WP5a F2).
+
+        Exact wat `assess` op dit moment in de binding zou leggen: norm,
+        promptversie, routering (routeruitkomst en capability-beleid),
+        profiel, budget en gevraagde provider/model. Alleen een routerlookup,
+        geen modelaanroep. Een onveranderlijke, nieuwe `Configuratie` per
+        aanroep; een aanroeper legt haar vóór `assess` vast en toetst het
+        teruggegeven document ertegen.
+        """
+        return self._configuratie(self._route(), PROMPT_VERSION)
+
     # --- vóór de aanroep ------------------------------------------------------
 
     def _route(self) -> _Route:
diff --git a/src/services/validation/modular_validation_service.py b/src/services/validation/modular_validation_service.py
index f0ec86bf0..c191df8cd 100644
--- a/src/services/validation/modular_validation_service.py
+++ b/src/services/validation/modular_validation_service.py
@@ -99,8 +99,14 @@ _ACCEPTATIE_BLOKKEERDERS: frozenset[str] = frozenset({"DUP_01"})
 # scorepolicy blijft `excluded_from_score`, dus geen zelfstandige blokkade.
 # DEF-772: INT-03 idem — de AI-verwijzingsbeoordeling levert haar uitkomst
 # (inclusief het beoordelingsdocument) in `rule_results`, zonder cijfer.
+# DEF-835 (WP5a): INT-02 in O2 (`decision_rule_assessment`) idem — elke status
+# met het WP1-document in `rule_results`, geen cijfer en geen poort (B5/B6).
 _EVALUATORS_MET_DEELUITKOMST: frozenset[EvaluatorType] = frozenset(
-    {EvaluatorType.SENTENCE_BOUNDARY, EvaluatorType.PRONOUN_REFERENCE_ASSESSMENT}
+    {
+        EvaluatorType.SENTENCE_BOUNDARY,
+        EvaluatorType.PRONOUN_REFERENCE_ASSESSMENT,
+        EvaluatorType.DECISION_RULE_ASSESSMENT,
+    }
 )
 
 
@@ -861,6 +867,18 @@ class ModularValidationService:
             "unexpected_rule_ids": list(readiness.unexpected_rule_ids),
         }
 
+    def evaluator_voor(self, code: str) -> EvaluatorType | None:
+        """De evaluator die de actieve regelset voor `code` kiest (DEF-835 WP5a).
+
+        Uit dezelfde, zo nodig ververste snapshot als de evaluatie: het
+        gevalideerde regelrecord, niet een aanroepersleutel. `None` als de
+        regelset niet gereed is of de regel geen record heeft; dan draait er
+        ook geen evaluator die een voorafgaande beoordeling kan gebruiken.
+        """
+        snap = self._ververs_state_indien_nodig()
+        record = snap.rule_records.get(code) if snap.readiness.ready else None
+        return record.evaluator if record is not None else None
+
     async def validate_definition(
         self,
         begrip: str,
@@ -1462,6 +1480,12 @@ class ModularValidationService:
         """
         beschikbaar = self._available_inputs(ctx)
         ontbrekend = missing_inputs(record, beschikbaar)
+        # DEF-835 (WP5a, review F1): de O2-evaluator doet zelf de volledige
+        # WP1-invoercontrole op de oorspronkelijke recordkern — NE in O2-vorm,
+        # ongeldige metadata `error`. Hier onderscheppen zou op `cleaned_text`
+        # en met de O1-NE-vorm beslissen; het O1-pad hieronder blijft gelijk.
+        if record.evaluator is EvaluatorType.DECISION_RULE_ASSESSMENT:
+            ontbrekend = ()
         if ontbrekend:
             # DEF-771: INT-02 geeft de exacte NE-melding (kern en/of context).
             if record.rule_id.upper() == "INT-02":
diff --git a/tests/unit/validation/test_def835_int02_assessment_service.py b/tests/unit/validation/test_def835_int02_assessment_service.py
index 76a2d530d..33b744ec0 100644
--- a/tests/unit/validation/test_def835_int02_assessment_service.py
+++ b/tests/unit/validation/test_def835_int02_assessment_service.py
@@ -33,7 +33,9 @@ from domain.int02.contract import (
     MELDING_NIET_BEOORDEELD,
     NORMVERSIE,
     ONBEKEND,
+    Configuratie,
     Int02ContractError,
+    bereken_binding,
     maak_invoer,
     toets_actualiteit,
 )
@@ -302,10 +304,63 @@ def test_taak_is_de_bestaande_routertaak_validation():
     assert "validation" in ModelRouter._DEFAULT_CONFIG["task_tiers"]["critical"]
 
 
-def test_dienst_wordt_niet_door_de_container_aangemaakt():
-    container = (ROOT / "src/services/container.py").read_text(encoding="utf-8")
-    assert "int02_assessment" not in container
-    assert "Int02AssessmentService" not in container
+def test_dienst_wordt_niet_door_de_container_aangemaakt(monkeypatch):
+    """Gedragsguard (DEF-835 WP5a, review F3; was een tekstguard op container.py).
+
+    De normale container bouwt of injecteert de dienst nooit vanzelf en doet
+    geen modelaanroep. Toegestaan is alleen de expliciete factory met
+    verplicht profiel en budget (keyword-only, zonder default).
+    """
+    import inspect
+
+    from services.container import ServiceContainer
+
+    constructies: list[dict] = []
+    origineel = Int02AssessmentService.__init__
+
+    def _tel(self, *args, **kwargs):
+        constructies.append(kwargs)
+        origineel(self, *args, **kwargs)
+
+    monkeypatch.setattr(Int02AssessmentService, "__init__", _tel)
+    ai = FakeAI()
+    container = ServiceContainer.__new__(ServiceContainer)
+    container._instances = {}
+    container._lazy_instances = {}
+    container.use_json_rules = True
+    afhankelijkheden = {
+        "ai_service": ai,
+        "model_router": FakeRouter(),
+        "cleaning_service": object(),
+        "repository": SimpleNamespace(),
+        "web_lookup": None,
+        "synonym_orchestrator": None,
+        "source_assessment_service": object(),
+        "ess03_assessment_service": object(),
+        "int03_assessment_service": object(),
+    }
+    for naam, waarde in afhankelijkheden.items():
+        monkeypatch.setattr(container, naam, lambda w=waarde: w, raising=False)
+    monkeypatch.setattr(ServiceContainer, "rag_service", property(lambda _s: None))
+
+    orchestrator = container.orchestrator()
+    assert orchestrator.int02_assessment_service is None
+    assert orchestrator.validation_service.int02_assessment_service is None
+    assert constructies == []
+
+    handtekening = inspect.signature(container.int02_assessment_service)
+    for naam in ("profiel", "budget"):
+        parameter = handtekening.parameters[naam]
+        assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
+        assert parameter.default is inspect.Parameter.empty
+    with pytest.raises(Int02ServiceConfigError):
+        container.int02_assessment_service(profiel=None, budget=_budget())
+    assert constructies == []
+
+    dienst = container.int02_assessment_service(profiel=_profiel(), budget=_budget())
+    assert isinstance(dienst, Int02AssessmentService)
+    assert len(constructies) == 1
+    assert ai.calls == []
 
 
 async def test_aanroeper_moet_een_int02invoer_leveren():
@@ -1316,3 +1371,96 @@ async def test_f3_uitzondering_van_de_ai_laag_geeft_onbekend_aantal_pogingen():
     resultaat = await _dienst(FakeAI(AIServiceError("x"))).assess(_invoer())
     assert resultaat.status == "error"
     assert resultaat.document.uitvoering.transportpogingen == ONBEKEND
+
+
+# --- F2 (WP5a-review): publieke, onafhankelijke configuratiesnapshot ----------
+#
+# De validatiewrapper legt deze snapshot vóór `assess` vast en toetst het
+# teruggegeven document ertegen. Zij moet dus exact de WP1-configuratie zijn
+# die `assess` bindt (norm, promptversie, routering, profiel, budget,
+# provider/model), zonder modelaanroep en als onveranderlijke kopie.
+
+
+def _snapshot(dienst) -> Configuratie:
+    lees = getattr(dienst, "configuratie", None)
+    if not callable(lees):
+        pytest.fail("Int02AssessmentService.configuratie() ontbreekt")
+    return lees()
+
+
+async def test_f2_snapshot_is_exact_de_configuratie_die_assess_bindt():
+    ai = FakeAI(_fail_uitvoer())
+    dienst = _dienst(ai)
+
+    snapshot = _snapshot(dienst)
+    assert isinstance(snapshot, Configuratie)
+    resultaat = await dienst.assess(_invoer())
+
+    assert resultaat.status == "fail"
+    assert resultaat.document.binding.configuratie() == snapshot
+    assert resultaat.document.binding == bereken_binding(_invoer(), snapshot)
+
+
+async def test_f2_snapshot_ook_bij_blokkade_gelijk_aan_de_binding():
+    # Router onbeschikbaar of profiel ontbreekt: geen aanroep, maar de
+    # snapshot blijft de configuratie van het niet-uitgevoerde document.
+    for dienst in (
+        _dienst(router=FakeRouter(fout=RuntimeError("router weg"))),
+        _dienst(profiel=None),
+    ):
+        snapshot = _snapshot(dienst)
+        resultaat = await dienst.assess(_invoer())
+        assert resultaat.document.uitvoering.status == "not_executed"
+        assert resultaat.document.binding == bereken_binding(_invoer(), snapshot)
+
+
+def test_f2_snapshot_uitlezen_doet_geen_modelaanroep():
+    ai, router = FakeAI(), FakeRouter()
+    dienst = _dienst(ai, router)
+
+    _snapshot(dienst)
+    _snapshot(dienst)
+
+    assert ai.calls == []
+    assert set(router.calls) == {TASK_TYPE}
+
+
+def test_f2_snapshot_bevat_norm_prompt_profiel_budget_en_routering(monkeypatch):
+    basis = _snapshot(_dienst())
+    assert basis.normversie == NORMVERSIE
+    assert basis.normhash == laad_int02_norm().normhash
+    assert basis.promptversie == PROMPT_VERSION
+    assert (basis.provider, basis.model) == (PROVIDER, MODEL)
+
+    andere_norm = dataclasses.replace(laad_int02_norm(), toetsvraag="Andere vraag?")
+    varianten = {
+        "norm": _dienst(norm=andere_norm),
+        "profiel": _dienst(profiel=_profiel(profiel_id="ander-profiel")),
+        "budget": _dienst(budget=_budget(max_uitvoertokens=801)),
+        "routerbeleid": _dienst(router=FakeRouter(thinking=True)),
+        "model": _dienst(
+            router=FakeRouter(model="ander-model"),
+            profiel=_profiel(model="ander-model"),
+        ),
+    }
+    for naam, dienst in varianten.items():
+        assert _snapshot(dienst) != basis, naam
+
+    monkeypatch.setattr(dienstmodule, "PROMPT_VERSION", "def835-int02-prompt/test")
+    assert _snapshot(_dienst()).promptversie == "def835-int02-prompt/test"
+
+
+def test_f2_snapshot_is_een_onveranderlijke_losse_kopie():
+    router = FakeRouter()
+    dienst = _dienst(router=router)
+    eerste = _snapshot(dienst)
+
+    with pytest.raises(dataclasses.FrozenInstanceError):
+        eerste.model = "gemanipuleerd"  # type: ignore[misc]
+    object.__setattr__(eerste, "model", "gemanipuleerd")
+    assert _snapshot(dienst).model == MODEL  # de dienst deelt geen staat
+
+    router.thinking = True  # latere routerwijziging
+    tweede = _snapshot(dienst)
+    assert tweede != _snapshot(_dienst())
+    assert eerste.routeringshash == _snapshot(_dienst()).routeringshash
diff --git a/tests/unit/services/orchestrators/test_def835_int02_wrappers.py b/tests/unit/services/orchestrators/test_def835_int02_wrappers.py
new file mode 100644
index 000000000..9d5a3ffec
--- /dev/null
+++ b/tests/unit/services/orchestrators/test_def835_int02_wrappers.py
@@ -0,0 +1,1106 @@
+"""DEF-835 WP5a: INT-02 (O2) via de generatie- en recordwrapper (eerst rood).
+
+`ValidationOrchestratorV2` krijgt een optionele, expliciet geïnjecteerde
+`int02_assessment_service`. De wrapper roept haar uitsluitend aan als de
+actieve regelset INT-02 werkelijk op `decision_rule_assessment` zet (gelezen
+via `ModularValidationService.evaluator_voor`), bouwt de WP1-invoer zelf uit
+exact de getoetste kern en context, en geeft het verse WP1-document met zijn
+configuratie aan de evaluator. Het document komt onveranderd in
+`rule_results['INT-02']`.
+
+Wat de aanroeper onder `int02_document`, `int02_configuratie` of
+`int02_assessment` meegeeft, wordt altijd weggegooid: nooit een kortere weg
+naar pass/fail. De normale O1-route doet nul INT-02-aanroepen, ook met een
+geïnjecteerde dienst. Fouten van dienst, vorm of binding worden `error`,
+zonder uitzonderingstekst in de log.
+
+De O2-regelset is een tijdelijke kopie; het actieve `INT-02.json` blijft O1.
+De modelresponsen zijn handmatig (ontwerpgevallen C105/C107/C112/C117): zij
+bewijzen de ketenmapping, niets over modelkwaliteit. Opslag en herladen (C118)
+vallen buiten dit pakket.
+"""
+
+from __future__ import annotations
+
+import asyncio
+import copy
+import json
+import logging
+from dataclasses import asdict, dataclass, replace
+from pathlib import Path
+from typing import Any
+
+import pytest
+
+from domain.int02.contract import (
+    CONTRACTVERSIE,
+    MELDING_E,
+    MELDING_NE,
+    MELDING_NIET_BEOORDEELD,
+    Configuratie,
+    Uitvoering,
+    beoordeel,
+    maak_invoer,
+)
+from services.interfaces import AIGenerationResult, Definition, GenerationRequest
+from services.orchestrators.validation_orchestrator_v2 import ValidationOrchestratorV2
+from services.validation.int02_assessment_service import (
+    Budget,
+    Int02AssessmentService,
+    Modelprofiel,
+)
+from services.validation.interfaces import ValidationContext
+from services.validation.modular_validation_service import ModularValidationService
+from toetsregels.manager import ToetsregelManager
+
+pytestmark = [pytest.mark.unit]
+
+ROOT = Path(__file__).resolve().parents[4]
+REGELS = ROOT / "src" / "toetsregels" / "regels"
+GEVALLEN = json.loads(
+    (ROOT / "tests" / "fixtures" / "def835_int02_ontwerpgevallen.json").read_text(
+        "utf-8"
+    )
+)["gevallen"]
+
+PROVIDER = "fakeprovider"
+MODEL = "fake-int02-model"
+#: Synthetische configuratie van de fake-dienst; geen echt profiel.
+CONFIG = Configuratie(
+    normhash="a" * 64,
+    promptversie="def835-wp5a-fixture/1",
+    routeringshash="b" * 64,
+    provider=PROVIDER,
+    model=MODEL,
+)
+VOLTOOID = Uitvoering(actor="ai", status="completed")
+#: Synthetische uitzonderingstekst die nooit in een log mag komen.
+GEHEIM = "GEHEIME-UITZONDERINGSTEKST-wp5a met invoerfragment"
+
+
+def _geval(geval_id: str, variant: str | None = None) -> dict[str, Any]:
+    for geval in GEVALLEN:
+        if geval["id"] == geval_id and geval.get("variant") == variant:
+            return copy.deepcopy(geval)
+    raise AssertionError(f"ontwerpgeval {geval_id}/{variant} ontbreekt")
+
+
+C105 = _geval("C105")
+BEGRIP = C105["invoer"]["begrip"]
+KERN = C105["invoer"]["kern"]
+BEDOELING = C105["invoer"]["bedoeling"]
+CONTEXT = {
+    "organisatorische_context": list(C105["invoer"]["organisatorische_context"]),
+    "juridische_context": [],
+    "wettelijke_basis": [],
+}
+
+
+def _invoer(kern: str = KERN, **over):
+    velden = {
+        "begrip": BEGRIP,
+        "kern": kern,
+        "bedoeling": BEDOELING,
+        **copy.deepcopy(CONTEXT),
+        "bronnen": [],
+    }
+    velden.update(over)
+    return maak_invoer(**velden)
+
+
+def _metadata(**over) -> dict[str, Any]:
+    metadata: dict[str, Any] = {**copy.deepcopy(CONTEXT), "int02_bedoeling": BEDOELING}
+    metadata.update(over)
+    return metadata
+
+
+def _pass_respons(kern: str = KERN) -> dict[str, Any]:
+    return {
+        "verdict": "pass",
+        "passages": [
+            {
+                "quote": kern,
+                "start": 0,
+                "end": len(kern),
+                "function": "criterion",
+                "ground": {
+                    "field": "kern",
+                    "ref": None,
+                    "quote": None,
+                    "start": None,
+                    "end": None,
+                },
+            }
+        ],
+        "reason": "Synthetische pass voor de mapping; geen modeloordeel.",
+        "question": None,
+        "uncertainty": "none",
+        "scope_reason": None,
+        "coverage": "complete",
+    }
+
+
+def _na_respons() -> dict[str, Any]:
+    return {
+        "verdict": "not_applicable",
+        "passages": [],
+        "reason": "Synthetische reikwijdtegrond.",
+        "question": None,
+        "uncertainty": "none",
+        "scope_reason": "Synthetische tekst buiten het definitietoetsbereik.",
+        "coverage": "none",
+    }
+
+
+@dataclass(frozen=True)
+class _Beoordeling:
+    """Zelfde publieke vorm als `Int02Beoordeling` voor de wrapper: `.document`."""
+
+    document: Any
+
+
+_GEEN = object()
+
+
+class FakeDienst:
+    """INT-02-dienstgrens: legt elke ontvangen invoer vast; geen model.
+
+    F2: `configuratie()` is de publieke snapshot (standaard `CONFIG`; een
+    uitzondering wordt opgeworpen). Het document wordt gebonden aan
+    `document_config`, anders aan de snapshot zoals die bij `assess` geldt;
+    `wijzig_naar` wisselt de snapshot tijdens de aanroep.
+    """
+
+    def __init__(
+        self,
+        respons=None,
+        *,
+        fout=None,
+        resultaat=_GEEN,
+        invoer=None,
+        snapshot: Any = CONFIG,
+        document_config: Configuratie | None = None,
+        wijzig_naar: Configuratie | None = None,
+    ):
+        self.respons = C105["modelrespons"] if respons is None else respons
+        self.fout = fout
+        self.resultaat = resultaat
+        self.andere_invoer = invoer
+        self.snapshot = snapshot
+        self.document_config = document_config
+        self.wijzig_naar = wijzig_naar
+        self.calls: list[Any] = []
+        self.snapshots_gelezen = 0
+        self.snapshots_voor_assess: list[int] = []
+
+    def configuratie(self):
+        self.snapshots_gelezen += 1
+        if isinstance(self.snapshot, BaseException):
+            raise self.snapshot
+        return self.snapshot
+
+    async def assess(self, invoer, *, correlation_id=None):
+        self.calls.append(invoer)
+        self.snapshots_voor_assess.append(self.snapshots_gelezen)
+        if self.wijzig_naar is not None:
+            self.snapshot = self.wijzig_naar
+        if self.fout is not None:
+            raise self.fout
+        if self.resultaat is not _GEEN:
+            return self.resultaat
+        doel = invoer if self.andere_invoer is None else self.andere_invoer
+        config = self.document_config or (
+            self.snapshot if isinstance(self.snapshot, Configuratie) else CONFIG
+        )
+        return _Beoordeling(beoordeel(doel, config, self.respons, VOLTOOID))
+
+
+# --- regelsets ------------------------------------------------------------------
+
+
+def _schrijf_regelmap(doel: Path, *, o2: bool) -> Path:
+    doel.mkdir()
+    for pad in sorted(REGELS.glob("*.json")):
+        tekst = pad.read_text("utf-8")
+        if o2 and pad.stem == "INT-02":
+            data = json.loads(tekst)
+            data["runtime_contract"].update(
+                {
+                    "evaluator": "decision_rule_assessment",
+                    "automation_status": "automated",
+                }
+            )
+            tekst = json.dumps(data, ensure_ascii=False, indent=2)
+        (doel / pad.name).write_text(tekst, "utf-8")
+    return doel
+
+
+@pytest.fixture(scope="module")
+def o2_manager(tmp_path_factory: pytest.TempPathFactory) -> ToetsregelManager:
+    """Expliciete proefconfiguratie: alleen INT-02 wijst naar O2."""
+    regels = _schrijf_regelmap(
+        tmp_path_factory.mktemp("def835_wp5a_wrappers") / "regels", o2=True
+    )
+    return ToetsregelManager(base_dir=str(regels.parent))
+
+
+@pytest.fixture(scope="module")
+def o2_service(o2_manager) -> ModularValidationService:
+    return ModularValidationService(toetsregel_manager=o2_manager)
+
+
+@pytest.fixture(scope="module")
+def o1_service() -> ModularValidationService:
+    """De actieve regelset (INT-02 = judgment_review)."""
+    return ModularValidationService(toetsregel_manager=ToetsregelManager())
+
+
+def _int02(resultaat: dict[str, Any]) -> dict[str, Any]:
+    return resultaat["rule_results"]["INT-02"]
+
+
+def _record(kern: Any = KERN) -> Definition:
+    return Definition(
+        begrip=BEGRIP,
+        definitie=kern,
+        organisatorische_context=list(CONTEXT["organisatorische_context"]),
+        metadata={"version_number": 1},
+    )
+
+
+async def _via_tekst(orch, kern: str = KERN, **metadata) -> dict[str, Any]:
+    return await orch.validate_text(
+        BEGRIP, kern, context=ValidationContext(metadata=_metadata(**metadata))
+    )
+
+
+async def _via_record(orch, kern: Any = KERN, **metadata) -> dict[str, Any]:
+    return await orch.validate_definition(
+        _record(kern),
+        ValidationContext(metadata={"int02_bedoeling": BEDOELING, **metadata}),
+    )
+
+
+ROUTES = [pytest.param(_via_tekst, id="tekst"), pytest.param(_via_record, id="record")]
+
+
+# --- O1 blijft actief: nul INT-02-aanroepen ---------------------------------------
+
+
+@pytest.mark.parametrize("route", ROUTES)
+async def test_o1_regelset_doet_nul_int02_aanroepen(o1_service, route):
+    dienst = FakeDienst(_pass_respons())
+    losse_dienst = FakeDienst(_pass_respons())
+    orch = ValidationOrchestratorV2(o1_service, int02_assessment_service=dienst)
+    los_document = beoordeel(_invoer(), CONFIG, _pass_respons(), VOLTOOID)
+
+    resultaat = await route(
+        orch,
+        int02_document=los_document,
+        int02_configuratie=CONFIG,
+        int02_assessment=los_document.als_dict(),
+        int02_assessment_service=losse_dienst,
+    )
+
+    assert dienst.calls == []
+    assert losse_dienst.calls == []
+    assert resultaat["rule_statuses"]["INT-02"] != "pass"
+    assert resultaat["rule_results"].get("INT-02", {}).get("assessment") is None
+
+
+# --- aanroepermetadata is nooit een kortere weg ------------------------------------
+
+
+@pytest.mark.parametrize("route", ROUTES)
+async def test_meegegeven_document_zonder_dienst_geeft_nooit_een_oordeel(
+    o2_service, route
+):
+    # Zonder geïnjecteerde dienst blijft INT-02 expliciet open, ook als de
+    # aanroeper een geldig, aan exact deze invoer gebonden document meegeeft.
+    orch = ValidationOrchestratorV2(o2_service)
+    los_document = beoordeel(_invoer(), CONFIG, _pass_respons(), VOLTOOID)
+
+    resultaat = await route(
+        orch,
+        int02_document=los_document,
+        int02_configuratie=CONFIG,
+        int02_assessment=los_document.als_dict(),
+    )
+
+    detail = _int02(resultaat)
+    assert detail["status"] == "review_required"
+    assert detail["review"]["actuality"] == "not_assessed"
+    assert detail["parts"][0]["reason"] == MELDING_NIET_BEOORDEELD
+    assert detail["assessment"] is None
+
+
+@pytest.mark.parametrize("route", ROUTES)
+async def test_verse_beoordeling_vervangt_meegegeven_document(o2_service, route):
+    dienst = FakeDienst()  # C105: adviserende fail
+    orch = ValidationOrchestratorV2(o2_service, int02_assessment_service=dienst)
+    los_document = beoordeel(_invoer(), CONFIG, _pass_respons(), VOLTOOID)
+
+    resultaat = await route(
+        orch, int02_document=los_document, int02_configuratie=CONFIG
+    )
+
+    (invoer,) = dienst.calls
+    assert invoer == _invoer()
+    verwacht = beoordeel(invoer, CONFIG, C105["modelrespons"], VOLTOOID)
+    detail = _int02(resultaat)
+    assert detail["status"] == "fail"
+    assert detail["review"]["actuality"] == "current"
+    assert detail["assessment"] == verwacht.als_dict()
+
+
+# --- exacte kern ----------------------------------------------------------------------
+
+
+class _AgressieveCleaning:
+    """Cleaning die de tekst zichtbaar wijzigt; mag INT-02 niet raken."""
+
+    def clean_text(self, tekst):
+        return " ".join(str(tekst).split()).upper()
+
+
+async def test_kern_is_bytegelijk_de_getoetste_tekst_zonder_cleaning(o2_manager):
+    kern = "  De medewerker laat de  aanvrager toe. "
+    service = ModularValidationService(
+        toetsregel_manager=o2_manager, cleaning_service=_AgressieveCleaning()
+    )
+    dienst = FakeDienst(_pass_respons(kern))
+    orch = ValidationOrchestratorV2(service, int02_assessment_service=dienst)
+
+    resultaat = await _via_tekst(orch, kern, record_text="een andere tekst")
+
+    (invoer,) = dienst.calls
+    assert invoer.kern == kern
+    detail = _int02(resultaat)
+    assert detail["status"] == "pass"
+    assert detail["assessment"]["invoer"]["kern"] == kern
+
+
+async def test_recordkern_is_gezaghebbend(o2_service):
+    dienst = FakeDienst()
+    orch = ValidationOrchestratorV2(o2_service, int02_assessment_service=dienst)
+
+    await _via_record(orch, KERN, record_text="Verouderde aanroepertekst.")
+
+    (invoer,) = dienst.calls
+    assert invoer.kern == KERN
+    assert invoer.organisatorische_context == tuple(CONTEXT["organisatorische_context"])
+
+
+async def test_ongeldige_recordkern_is_fout_zonder_terugval(o2_service):
+    # Een aanwezige recordkern die geen tekst is: geen terugval op de
+    # aanroepertekst, geen aanroep, en een technische fout zonder oordeel.
+    dienst = FakeDienst(_pass_respons())
+    orch = ValidationOrchestratorV2(o2_service, int02_assessment_service=dienst)
+
+    resultaat = await _via_record(orch, None, record_text=KERN)
+
+    assert dienst.calls == []
+    assert resultaat["rule_statuses"]["INT-02"] == "error"
+    detail = _int02(resultaat)
+    assert detail["status"] == "error"
+    assert detail["assessment"] is None
+
+
+async def test_recordkern_van_verkeerd_type_bereikt_de_dienst_niet(o2_service):
+    # Een getal laat de bestaande modulaire service zelf degraderen; ook dan
+    # geen aanroep en geen INT-02-oordeel.
+    dienst = FakeDienst(_pass_respons())
+    orch = ValidationOrchestratorV2(o2_service, int02_assessment_service=dienst)
+
+    resultaat = await _via_record(orch, 42, record_text=KERN)
+
+    assert dienst.calls == []
+    assert resultaat["validation_status"] != "validated"
+    assert "INT-02" not in resultaat.get("rule_results", {})
+
+
+# --- NE en expliciet open ----------------------------------------------------------------
+
+
+@pytest.mark.parametrize(
+    ("kern", "context"),
+    [
+        pytest.param("", CONTEXT, id="lege-kern"),
+        pytest.param("Toelating:", CONTEXT, id="label-zonder-kern"),
+        pytest.param(
+            KERN,
+            {
+                "organisatorische_context": [],
+                "juridische_context": [],
+                "wettelijke_basis": [],
+            },
+            id="geen-context",
+        ),
+    ],
+)
+async def test_lege_kern_of_ontbrekende_context_is_ne_zonder_aanroep(
+    o2_service, kern, context
+):
+    dienst = FakeDienst(_pass_respons())
+    orch = ValidationOrchestratorV2(o2_service, int02_assessment_service=dienst)
+
+    resultaat = await _via_tekst(orch, kern, **copy.deepcopy(context))
+
+    assert dienst.calls == []
+    assert resultaat["rule_statuses"]["INT-02"] == "not_evaluated"
+    assert _int02(resultaat)["status"] == "not_evaluated"
+
+
+# --- fouten van dienst, vorm en binding ----------------------------------------------------
+
+
+FOUTDIENSTEN = [
+    pytest.param(lambda: FakeDienst(fout=RuntimeError(GEHEIM)), id="uitzondering"),
+    pytest.param(
+        lambda: FakeDienst(resultaat={"status": "pass", "melding": GEHEIM}),
+        id="vorm-dict",
+    ),
+    pytest.param(lambda: FakeDienst(resultaat=_Beoordeling(None)), id="vorm-leeg"),
+    pytest.param(
+        lambda: FakeDienst(
+            _pass_respons("Een andere kern."), invoer=_invoer("Een andere kern.")
+        ),
+        id="binding-andere-invoer",
+    ),
+]
+
+
+@pytest.mark.parametrize("route", ROUTES)
+@pytest.mark.parametrize("maak_dienst", FOUTDIENSTEN)
+async def test_dienst_vorm_en_bindingsfout_zijn_error(
+    o2_service, route, maak_dienst, caplog
+):
+    dienst = maak_dienst()
+    orch = ValidationOrchestratorV2(o2_service, int02_assessment_service=dienst)
+
+    with caplog.at_level(logging.DEBUG):
+        resultaat = await route(orch)
+
+    assert len(dienst.calls) == 1  # geen herstel- of tweede aanroep
+    detail = _int02(resultaat)
+    assert detail["status"] == "error"
+    assert detail["parts"][0]["reason"] == MELDING_E
+    assert detail["assessment"] is None
+    assert GEHEIM not in caplog.text
+    assert "GEHEIME" not in json.dumps(resultaat, default=str)
+
+
+# --- de echte WP2-dienst met handmatige fake-respons (C105/C107/C112/C117) -----------------
+
+
+class FakeRouter:
+    def get_model(self, task_type):
+        return PROVIDER, MODEL
+
+    def accepts_temperature(self, model, provider=None):
+        return True
+
+    def thinking_default_on(self, model, provider=None):
+        return False
+
+
+class FakeAI:
+    """AI-grens met één handmatige respons per aanroep; telt aanroepen."""
+
+    def __init__(self, respons):
+        self.respons = respons
+        self.calls = 0
+
+    async def generate_definition(self, prompt, **kwargs):
+        self.calls += 1
+        return AIGenerationResult(
+            text=json.dumps(self.respons, ensure_ascii=False),
+            model=kwargs.get("model"),
+            tokens_used=None,
+            generation_time=0.01,
+            cached=False,
+            metadata={"stop_reason": "end_turn"},
+        )
+
+
+def _profiel(**over) -> Modelprofiel:
+    velden = {
+        "profiel_id": "wp5a-fixture-offline",
+        "provider": PROVIDER,
+        "model": MODEL,
+        "kwalificatie": "testfixture; geen kwaliteitsclaim",
+    }
+    velden.update(over)
+    return Modelprofiel(**velden)
+
+
+def _budget() -> Budget:
+    return Budget(
+        max_uitvoertokens=800,
+        deadline_seconden=5.0,
+        max_invoertekens_veld=2000,
+        max_invoertekens_totaal=6000,
+        max_antwoordtekens=20000,
+    )
+
+
+class Spion:
+    """Delegeert naar de echte dienst en bewaart het teruggegeven resultaat."""
+
+    def __init__(self, dienst):
+        self.dienst = dienst
+        self.resultaten: list[Any] = []
+
+    def configuratie(self):
+        return self.dienst.configuratie()
+
+    async def assess(self, invoer, **kwargs):
+        resultaat = await self.dienst.assess(invoer, **kwargs)
+        self.resultaten.append(resultaat)
+        return resultaat
+
+
+def _geval_metadata(geval) -> dict[str, Any]:
+    invoer = geval["invoer"]
+    return {
+        "organisatorische_context": list(invoer["organisatorische_context"]),
+        "juridische_context": list(invoer["juridische_context"]),
+        "wettelijke_basis": list(invoer["wettelijke_basis"]),
+        "int02_bedoeling": invoer["bedoeling"],
+        "int02_bronnen": copy.deepcopy(invoer["bronnen"]),
+    }
+
+
+@pytest.mark.parametrize(
+    ("geval_id", "status", "aanvaard"),
+    [
+        pytest.param(("C105", None), "fail", True, id="C105-fail"),
+        pytest.param(("C107", None), "review_required", True, id="C107-onvoldoende"),
+        pytest.param(("C112", None), "pass", True, id="C112-pass"),
+        pytest.param(("C117", "verzonnen-citaat"), "error", False, id="C117-citaat"),
+    ],
+)
+async def test_ontwerpgevallen_via_echte_dienst_en_modulaire_service(
+    o2_service, geval_id, status, aanvaard
+):
+    geval = _geval(*geval_id)
+    ai = FakeAI(geval["modelrespons"])
+    spion = Spion(
+        Int02AssessmentService(ai, FakeRouter(), profiel=_profiel(), budget=_budget())
+    )
+    orch = ValidationOrchestratorV2(o2_service, int02_assessment_service=spion)
+    context = ValidationContext(metadata=_geval_metadata(geval))
+
+    resultaat = await orch.validate_text(
+        geval["invoer"]["begrip"], geval["invoer"]["kern"], context=context
+    )
+
+    assert ai.calls == 1
+    (beoordeling,) = spion.resultaten
+    assert beoordeling.document.status == status == geval["verwacht"]["status"]
+    detail = _int02(resultaat)
+    assert detail["status"] == status
+    assert detail["parts"][0]["reason"] == beoordeling.document.melding
+    if aanvaard:
+        assert detail["assessment"] == beoordeling.document.als_dict()
+        assert detail["assessment"]["oordeel"] == geval["modelrespons"]
+        assert detail["assessment"]["invoer"] == geval["invoer"]
+    else:
+        assert beoordeling.document.foutcategorie == "invalid_citation"
+        assert detail["assessment"] is None
+
+    # Opnieuw toetsen van exact dezelfde invoer: een geaccepteerd oordeel komt
+    # uit de dienstcache, nooit een tweede modelaanroep; een fout is nooit
+    # gecachet en wordt ook niet binnen één toetsing hersteld.
+    await orch.validate_text(
+        geval["invoer"]["begrip"], geval["invoer"]["kern"], context=context
+    )
+    assert ai.calls == (1 if aanvaard else 2)
+
+
+async def test_ontbrekend_profiel_blijft_expliciet_open_zonder_modelaanroep(
+    o2_service,
+):
+    ai = FakeAI(C105["modelrespons"])
+    dienst = Int02AssessmentService(ai, FakeRouter(), profiel=None, budget=_budget())
+    orch = ValidationOrchestratorV2(o2_service, int02_assessment_service=dienst)
+
+    resultaat = await _via_tekst(orch)
+
+    assert ai.calls == 0
+    detail = _int02(resultaat)
+    assert detail["status"] == "review_required"
+    assert detail["review"]["actuality"] == "not_assessed"
+
+
+async def test_not_applicable_komt_via_de_wrapper_in_rule_results(o2_service):
+    dienst = FakeDienst(_na_respons())
+    orch = ValidationOrchestratorV2(o2_service, int02_assessment_service=dienst)
+
+    resultaat = await _via_record(orch)
+
+    detail = _int02(resultaat)
+    assert detail["status"] == "not_applicable"
+    assert detail["assessment"]["oordeel"] == _na_respons()
+
+
+# --- generatieroute (DefinitionOrchestratorV2) ------------------------------------------------
+
+
+class _Repo:
+    pass
+
+
+async def test_generatieroute_toetst_exact_de_kandidaat(o2_service):
+    from services.orchestrators.definition_orchestrator_v2 import (
+        DefinitionOrchestratorV2,
+    )
+
+    dienst = FakeDienst()
+    wrapper = ValidationOrchestratorV2(o2_service, int02_assessment_service=dienst)
+    orch = DefinitionOrchestratorV2(
+        ai_service=object(),
+        cleaning_service=object(),
+        repository=_Repo(),
+        validation_service=wrapper,
+    )
+    verzoek = GenerationRequest(
+        id="wp5a-gen",
+        begrip=BEGRIP,
+        organisatorische_context=list(CONTEXT["organisatorische_context"]),
+    )
+
+    kandidaat, ruw, _ = await orch._toets_kandidaat(
+        verzoek,
+        KERN,
+        ValidationContext(metadata={"int02_bedoeling": BEDOELING}),
+        "wp5a-gen",
+    )
+
+    assert kandidaat == KERN
+    (invoer,) = dienst.calls
+    assert invoer == _invoer()
+    assert ruw["rule_results"]["INT-02"]["status"] == "fail"
+    assert (
+        ruw["rule_results"]["INT-02"]["assessment"]
+        == beoordeel(invoer, CONFIG, C105["modelrespons"], VOLTOOID).als_dict()
+    )
+
+
+def test_definitie_orchestrator_geeft_int02_dienst_door_zonder_default():
+    from services.orchestrators.definition_orchestrator_v2 import (
+        DefinitionOrchestratorV2,
+    )
+
+    dienst = FakeDienst()
+    met = DefinitionOrchestratorV2(
+        ai_service=object(),
+        cleaning_service=object(),
+        repository=_Repo(),
+        int02_assessment_service=dienst,
+    )
+    assert met.validation_service.int02_assessment_service is dienst
+
+    zonder = DefinitionOrchestratorV2(
+        ai_service=object(), cleaning_service=object(), repository=_Repo()
+    )
+    # Geen lazy default: zonder expliciete injectie bestaat er geen INT-02-dienst.
+    assert zonder.int02_assessment_service is None
+    assert zonder.validation_service.int02_assessment_service is None
+
+
+# --- F1 (review WP5a): NE en ongeldige invoer zonder context -------------------
+#
+# Zonder context onderschepte de service INT-02 vóór de O2-evaluator (oude
+# DEF-771-uitkomst op `cleaned_text`). Via de volledige keten moet de
+# O2-evaluator zelf beslissen op de oorspronkelijke kern: exacte NE-melding in
+# O2-vorm, of `error` bij ongeldige aanwezige kern/bedoeling — nooit een
+# aanroep.
+
+
+class _VasteCleaning:
+    """Cleaning die altijd dezelfde tekst oplevert; mag INT-02 niet raken."""
+
+    def __init__(self, tekst: str) -> None:
+        self.tekst = tekst
+
+    def clean_text(self, _tekst):
+        return self.tekst
+
+
+GEEN_CONTEXT = {
+    "organisatorische_context": [],
+    "juridische_context": [],
+    "wettelijke_basis": [],
+}
+
+
+@pytest.mark.parametrize(
+    ("kern", "cleaning", "extra", "recordroute", "ontbreekt"),
+    [
+        pytest.param(KERN, "", {}, False, "context", id="kern-cleaning-leeg"),
+        pytest.param("", KERN, {}, False, "kern en context", id="leeg-cleaning-kern"),
+        pytest.param(None, None, {}, True, None, id="recordkern-none"),
+        pytest.param(
+            KERN, None, {"int02_bedoeling": 42}, False, None, id="bedoeling-getal"
+        ),
+    ],
+)
+async def test_f1_zonder_context_beslist_de_o2_evaluator_zonder_aanroep(
+    o2_manager, kern, cleaning, extra, recordroute, ontbreekt
+):
+    service = ModularValidationService(
+        toetsregel_manager=o2_manager,
+        cleaning_service=_VasteCleaning(cleaning) if cleaning is not None else None,
+    )
+    dienst = FakeDienst(_pass_respons())
+    orch = ValidationOrchestratorV2(service, int02_assessment_service=dienst)
+    metadata = {**copy.deepcopy(GEEN_CONTEXT), **extra}
+
+    if recordroute:
+        record = _record(kern)
+        record.organisatorische_context = []
+        resultaat = await orch.validate_definition(
+            record, ValidationContext(metadata=_metadata(**metadata))
+        )
+    else:
+        resultaat = await _via_tekst(orch, kern, **metadata)
+
+    assert dienst.calls == []
+    detail = _int02(resultaat)
+    status = "not_evaluated" if ontbreekt else "error"
+    melding = (
+        MELDING_NE.replace("{kern/context}", ontbreekt) if ontbreekt else MELDING_E
+    )
+    # Eerst status en exacte melding, daarna de O2-documentvorm.
+    assert resultaat["rule_statuses"]["INT-02"] == status
+    assert detail["status"] == status
+    assert [deel["reason"] for deel in detail["parts"]] == [melding]
+    assert detail["contract_version"] == CONTRACTVERSIE
+    assert detail["review"] == {"actuality": None}
+    assert detail["assessment"] is None
+    (deel,) = detail["parts"]
+    assert deel["id"] == "beoordeling"
+
+
+# --- F2 (review WP5a): onafhankelijke configuratiesnapshot vóór de aanroep ------
+#
+# De verwachte WP1-configuratie komt uit de publieke dienstsnapshot die de
+# wrapper vóór `assess` vastlegt — nooit uit het teruggegeven document. Een
+# afwijkende binding, een ontbrekende of ongeldige snapshot of een wijziging
+# rond de aanroep is `error` zonder oordeel.
+
+
+async def test_f2_reviewerrepro_oud_document_voor_ander_model_is_error(o2_service):
+    oud = await Int02AssessmentService(
+        FakeAI(_pass_respons()), FakeRouter(), profiel=_profiel(), budget=_budget()
+    ).assess(_invoer())
+    assert oud.document.status == "pass"
+
+    class _NieuweRouter(FakeRouter):
+        def get_model(self, task_type):
+            return PROVIDER, "fake-new-model"
+
+    class _GeeftOudResultaat(Int02AssessmentService):
+        async def assess(self, invoer, **kwargs):
+            return oud
+
+    nieuwe_ai = FakeAI(_pass_respons())
+    dienst = _GeeftOudResultaat(
+        nieuwe_ai,
+        _NieuweRouter(),
+        profiel=_profiel(model="fake-new-model"),
+        budget=_budget(),
+    )
+    orch = ValidationOrchestratorV2(o2_service, int02_assessment_service=dienst)
+
+    resultaat = await _via_tekst(orch)
+
+    detail = _int02(resultaat)
+    assert detail["status"] == "error"
+    assert detail["parts"][0]["reason"] == MELDING_E
+    assert detail["review"] == {"actuality": None}
+    assert detail["assessment"] is None
+    assert nieuwe_ai.calls == 0
+
+
+@pytest.mark.parametrize("route", ROUTES)
+@pytest.mark.parametrize(
+    ("veld", "waarde"),
+    [
+        ("normhash", "c" * 64),
+        ("normversie", "def771-int02/9"),
+        ("promptversie", "andere-prompt/1"),
+        ("routeringshash", "d" * 64),
+        ("provider", "anderprovider"),
+        ("model", "ander-model"),
+    ],
+)
+async def test_f2_documentbinding_afwijkend_van_snapshot_is_error(
+    o2_service, route, veld, waarde
+):
+    dienst = FakeDienst(
+        _pass_respons(), document_config=replace(CONFIG, **{veld: waarde})
+    )
+    orch = ValidationOrchestratorV2(o2_service, int02_assessment_service=dienst)
+
+    resultaat = await route(orch)
+
+    assert len(dienst.calls) == 1
+    detail = _int02(resultaat)
+    assert detail["status"] == "error"
+    assert detail["parts"][0]["reason"] == MELDING_E
+    assert detail["assessment"] is None
+
+
+class _ZonderSnapshot:
+    """Dienst zonder publieke snapshot; `assess` zou een pass geven."""
+
+    def __init__(self):
+        self.binnen = FakeDienst(_pass_respons())
+        self.calls = self.binnen.calls
+
+    async def assess(self, invoer, **kwargs):
+        return await self.binnen.assess(invoer, **kwargs)
+
+
+class _NietAanroepbareSnapshot(_ZonderSnapshot):
+    configuratie = CONFIG
+
+
+@pytest.mark.parametrize("route", ROUTES)
+@pytest.mark.parametrize(
+    "maak_dienst",
+    [
+        pytest.param(_ZonderSnapshot, id="ontbreekt"),
+        pytest.param(_NietAanroepbareSnapshot, id="niet-aanroepbaar"),
+        pytest.param(lambda: FakeDienst(_pass_respons(), snapshot=None), id="none"),
+        pytest.param(
+            lambda: FakeDienst(_pass_respons(), snapshot=asdict(CONFIG)), id="dict"
+        ),
+        pytest.param(
+            lambda: FakeDienst(_pass_respons(), snapshot=RuntimeError(GEHEIM)),
+            id="uitzondering",
+        ),
+    ],
+)
+async def test_f2_ontbrekende_of_ongeldige_snapshot_is_error_zonder_aanroep(
+    o2_service, route, maak_dienst, caplog
+):
+    dienst = maak_dienst()
+    orch = ValidationOrchestratorV2(o2_service, int02_assessment_service=dienst)
+
+    with caplog.at_level(logging.DEBUG):
+        resultaat = await route(orch)
+
+    assert dienst.calls == []
+    detail = _int02(resultaat)
+    assert detail["status"] == "error"
+    assert detail["parts"][0]["reason"] == MELDING_E
+    assert detail["assessment"] is None
+    assert GEHEIM not in caplog.text
+
+
+@pytest.mark.parametrize("route", ROUTES)
+async def test_f2_snapshotwijziging_tijdens_aanroep_is_nooit_current(o2_service, route):
+    dienst = FakeDienst(
+        _pass_respons(), wijzig_naar=replace(CONFIG, model="gewisseld-model")
+    )
+    orch = ValidationOrchestratorV2(o2_service, int02_assessment_service=dienst)
+
+    resultaat = await route(orch)
+
+    assert len(dienst.calls) == 1
+    detail = _int02(resultaat)
+    assert detail["status"] == "error"
+    assert detail["review"] == {"actuality": None}
+    assert detail["assessment"] is None
+
+
+async def test_f2_routerwissel_tussen_snapshot_en_aanroep_is_error(o2_service):
+    class _WisselendeRouter(FakeRouter):
+        """Eerste routering (de snapshot) het profielmodel, daarna een ander."""
+
+        def __init__(self):
+            self.aantal = 0
+
+        def get_model(self, task_type):
+            self.aantal += 1
+            return PROVIDER, MODEL if self.aantal == 1 else "gewisseld-model"
+
+    ai = FakeAI(_pass_respons())
+    dienst = Int02AssessmentService(
+        ai, _WisselendeRouter(), profiel=_profiel(), budget=_budget()
+    )
+    orch = ValidationOrchestratorV2(o2_service, int02_assessment_service=dienst)
+
+    resultaat = await _via_tekst(orch)
+
+    assert ai.calls == 0
+    detail = _int02(resultaat)
+    assert detail["status"] == "error"
+    assert detail["assessment"] is None
+
+
+async def test_f2_snapshot_wordt_voor_de_aanroep_vastgelegd(o2_service):
+    dienst = FakeDienst(_pass_respons())
+    orch = ValidationOrchestratorV2(o2_service, int02_assessment_service=dienst)
+
+    resultaat = await _via_tekst(orch)
+
+    assert dienst.snapshots_voor_assess == [1]
+    detail = _int02(resultaat)
+    assert detail["status"] == "pass"
+    assert detail["review"]["actuality"] == "current"
+    assert detail["assessment"] == (
+        beoordeel(_invoer(), CONFIG, _pass_respons(), VOLTOOID).als_dict()
+    )
+
+
+# --- F2-restpunt en F4 (herreview WP5a F2/F3) -----------------------------------
+#
+# F2-restpunt: ook een wijziging ná de interne routering, tijdens de awaited
+# modelcall, mag nooit pass/current worden. De wrapper leest daarom na de
+# aanroep opnieuw de publieke snapshot en eist dat die geldig is en gelijk aan
+# de voor-snapshot. F4: ook het ophalen van `configuratie` zelf valt binnen de
+# veilige foutgrens.
+
+
+class _WijzigendeRouter(FakeRouter):
+    thinking = False
+
+    def thinking_default_on(self, model, provider=None):
+        return self.thinking
+
+
+class _WijzigtTijdensAI(FakeAI):
+    """Wijzigt het routerbeleid tijdens de awaited modelcall (na de routering)."""
+
+    def __init__(self, router):
+        super().__init__(_pass_respons())
+        self.router = router
+
+    async def generate_definition(self, prompt, **kwargs):
+        await asyncio.sleep(0)
+        self.router.thinking = True
+        return await super().generate_definition(prompt, **kwargs)
+
+
+@pytest.mark.parametrize("route", ROUTES)
+async def test_f2_beleidswijziging_tijdens_modelcall_is_error(o2_service, route):
+    router = _WijzigendeRouter()
+    ai = _WijzigtTijdensAI(router)
+    spion = Spion(
+        Int02AssessmentService(ai, router, profiel=_profiel(), budget=_budget())
+    )
+    orch = ValidationOrchestratorV2(o2_service, int02_assessment_service=spion)
+
+    resultaat = await route(orch)
+
+    assert ai.calls == 1  # geen extra modelcall
+    (beoordeling,) = spion.resultaten
+    assert beoordeling.document.status == "pass"  # de dienst zelf gaf een oordeel
+    detail = _int02(resultaat)
+    assert detail["status"] == "error"
+    assert detail["parts"][0]["reason"] == MELDING_E
+    assert detail["review"] == {"actuality": None}
+    assert detail["assessment"] is None
+
+
+@pytest.mark.parametrize("route", ROUTES)
+async def test_f2_stabiele_configuratie_blijft_pass_current(o2_service, route):
+    router = _WijzigendeRouter()
+    ai = FakeAI(_pass_respons())
+    orch = ValidationOrchestratorV2(
+        o2_service,
+        int02_assessment_service=Int02AssessmentService(
+            ai, router, profiel=_profiel(), budget=_budget()
+        ),
+    )
+
+    resultaat = await route(orch)
+
+    assert ai.calls == 1
+    detail = _int02(resultaat)
+    assert detail["status"] == "pass"
+    assert detail["review"]["actuality"] == "current"
+    assert detail["assessment"]["binding"]["model"] == MODEL
+
+
+class _NaSnapshot(FakeDienst):
+    """Voor-snapshot geldig (`CONFIG`); elke latere snapshot is `na`."""
+
+    def __init__(self, na):
+        super().__init__(_pass_respons())
+        self.na = na
+
+    def configuratie(self):
+        self.snapshots_gelezen += 1
+        waarde = CONFIG if self.snapshots_gelezen == 1 else self.na
+        if isinstance(waarde, BaseException):
+            raise waarde
+        return waarde
+
+
+@pytest.mark.parametrize("route", ROUTES)
+@pytest.mark.parametrize(
+    "na",
+    [
+        pytest.param(replace(CONFIG, model="na-model"), id="gewijzigd"),
+        pytest.param(None, id="none"),
+        pytest.param(asdict(CONFIG), id="dict"),
+        pytest.param(RuntimeError(GEHEIM), id="uitzondering"),
+    ],
+)
+async def test_f2_ongeldige_of_afwijkende_na_snapshot_is_error(
+    o2_service, route, na, caplog
+):
+    dienst = _NaSnapshot(na)
+    orch = ValidationOrchestratorV2(o2_service, int02_assessment_service=dienst)
+
+    with caplog.at_level(logging.DEBUG):
+        resultaat = await route(orch)
+
+    # Eerst de uitkomst, daarna het mechanisme (voor- en na-snapshot).
+    detail = _int02(resultaat)
+    assert detail["status"] == "error"
+    assert detail["parts"][0]["reason"] == MELDING_E
+    assert detail["assessment"] is None
+    assert GEHEIM not in caplog.text
+    assert len(dienst.calls) == 1
+    assert dienst.snapshots_gelezen == 2
+
+
+class _FalendeSnapshotProperty:
+    """Het ophalen van `configuratie` zelf faalt (F4-foutinjectie)."""
+
+    def __init__(self):
+        self.calls: list[Any] = []
+
+    @property
+    def configuratie(self):
+        raise RuntimeError(GEHEIM)
+
+    async def assess(self, invoer, **kwargs):  # pragma: no cover - mag niet
+        self.calls.append(invoer)
+        raise AssertionError("assess mag niet worden bereikt")
+
+
+@pytest.mark.parametrize("route", ROUTES)
+async def test_f4_falend_ophalen_van_snapshot_is_error_zonder_aanroep(
+    o2_service, route, caplog
+):
+    dienst = _FalendeSnapshotProperty()
+    orch = ValidationOrchestratorV2(o2_service, int02_assessment_service=dienst)
+
+    with caplog.at_level(logging.DEBUG):
+        resultaat = await route(orch)
+
+    assert dienst.calls == []
+    assert resultaat["validation_status"] == "validated"
+    detail = _int02(resultaat)
+    assert detail["status"] == "error"
+    assert detail["parts"][0]["reason"] == MELDING_E
+    assert detail["assessment"] is None
+    assert GEHEIM not in caplog.text
+    assert "GEHEIME" not in json.dumps(resultaat, default=str)
diff --git a/tests/unit/validation/test_def835_int02_modular.py b/tests/unit/validation/test_def835_int02_modular.py
new file mode 100644
index 000000000..5e3b22bfa
--- /dev/null
+++ b/tests/unit/validation/test_def835_int02_modular.py
@@ -0,0 +1,432 @@
+"""DEF-835 WP5a: INT-02 (O2) via de echte `ModularValidationService` (eerst rood).
+
+De WP3-evaluator `decision_rule_assessment` levert zijn uitkomst als
+gestructureerde deeluitkomst; de modulaire service moet die voor elke status
+in `rule_results['INT-02']` boeken, zonder cijfer en zonder poort
+(`excluded_from_score`, besluiten B5/B6). De wrapper moet daarnaast in de
+actieve regelset kunnen lezen welke evaluator INT-02 kiest
+(`evaluator_voor`), zodat de O1-route nooit een INT-02-modelaanroep doet.
+
+Het actieve `INT-02.json` blijft O1 (`judgment_review`). Een O2-regelset is
+hier een tijdelijke kopie van alle regelbestanden waarin alleen het
+INT-02-runtimecontract naar `decision_rule_assessment` wijst. De documenten
+komen uit de WP1-functie `beoordeel` met handmatig ingevulde modelresponsen
+uit de ontwerpgevallen: zij bewijzen de ketenmapping, geen modelkwaliteit.
+"""
+
+from __future__ import annotations
+
+import copy
+import json
+from pathlib import Path
+from typing import Any
+
+import pytest
+
+from domain.int02.contract import (
+    CONTRACTVERSIE,
+    MELDING_E,
+    MELDING_NE,
+    MELDING_NIET_BEOORDEELD,
+    Configuratie,
+    Uitvoering,
+    beoordeel,
+    maak_invoer,
+)
+from services.validation import modular_validation_service as mvs
+from services.validation.modular_validation_service import ModularValidationService
+from toetsregels.manager import ToetsregelManager
+from toetsregels.runtime_contract import EvaluatorType
+
+pytestmark = [pytest.mark.unit]
+
+ROOT = Path(__file__).resolve().parents[3]
+REGELS = ROOT / "src" / "toetsregels" / "regels"
+GEVALLEN = json.loads(
+    (ROOT / "tests" / "fixtures" / "def835_int02_ontwerpgevallen.json").read_text(
+        "utf-8"
+    )
+)["gevallen"]
+
+#: Synthetische configuratie; geen echt profiel, geen modelkwalificatie.
+CONFIG = Configuratie(
+    normhash="a" * 64,
+    promptversie="def835-wp5a-fixture/1",
+    routeringshash="b" * 64,
+    provider="fakeprovider",
+    model="fake-int02-model",
+)
+VOLTOOID = Uitvoering(actor="ai", status="completed")
+
+
+def _geval(geval_id: str, variant: str | None = None) -> dict[str, Any]:
+    for geval in GEVALLEN:
+        if geval["id"] == geval_id and geval.get("variant") == variant:
+            return copy.deepcopy(geval)
+    raise AssertionError(f"ontwerpgeval {geval_id}/{variant} ontbreekt")
+
+
+def _invoer(geval: dict[str, Any]):
+    return maak_invoer(**geval["invoer"])
+
+
+def _document(geval: dict[str, Any], respons: Any = None):
+    respons = geval["modelrespons"] if respons is None else respons
+    return beoordeel(_invoer(geval), CONFIG, respons, VOLTOOID)
+
+
+def _na_respons() -> dict[str, Any]:
+    return {
+        "verdict": "not_applicable",
+        "passages": [],
+        "reason": "Synthetische reikwijdtegrond.",
+        "question": None,
+        "uncertainty": "none",
+        "scope_reason": "Synthetische tekst buiten het definitietoetsbereik.",
+        "coverage": "none",
+    }
+
+
+def _pass_respons_c105() -> dict[str, Any]:
+    kern = _geval("C105")["invoer"]["kern"]
+    return {
+        "verdict": "pass",
+        "passages": [
+            {
+                "quote": kern,
+                "start": 0,
+                "end": len(kern),
+                "function": "criterion",
+                "ground": {
+                    "field": "kern",
+                    "ref": None,
+                    "quote": None,
+                    "start": None,
+                    "end": None,
+                },
+            }
+        ],
+        "reason": "Synthetische pass voor de mapping; geen modeloordeel.",
+        "question": None,
+        "uncertainty": "none",
+        "scope_reason": None,
+        "coverage": "complete",
+    }
+
+
+def _onvoldoende_respons_c105() -> dict[str, Any]:
+    return {
+        "verdict": "insufficient_information",
+        "passages": [],
+        "reason": "Synthetisch: de bedoelde functie is onduidelijk.",
+        "question": "Beschrijft de zin een kenmerk of een opdracht?",
+        "uncertainty": "decisive",
+        "scope_reason": None,
+        "coverage": "partial",
+    }
+
+
+def _metadata(geval: dict[str, Any], document=None, configuratie=CONFIG) -> dict:
+    invoer = geval["invoer"]
+    metadata: dict[str, Any] = {
+        "record_text": invoer["kern"],
+        "organisatorische_context": list(invoer["organisatorische_context"]),
+        "juridische_context": list(invoer["juridische_context"]),
+        "wettelijke_basis": list(invoer["wettelijke_basis"]),
+        "int02_bedoeling": invoer["bedoeling"],
+        "int02_bronnen": copy.deepcopy(invoer["bronnen"]),
+    }
+    if configuratie is not None:
+        metadata["int02_configuratie"] = configuratie
+    if document is not None:
+        metadata["int02_document"] = document
+    return metadata
+
+
+@pytest.fixture(scope="module")
+def o2_regelmap(tmp_path_factory: pytest.TempPathFactory) -> Path:
+    """Kopie van alle regelbestanden; alleen INT-02 wijst naar de O2-evaluator."""
+    doel = tmp_path_factory.mktemp("def835_wp5a_o2") / "regels"
+    doel.mkdir()
+    for pad in sorted(REGELS.glob("*.json")):
+        tekst = pad.read_text("utf-8")
+        if pad.stem == "INT-02":
+            data = json.loads(tekst)
+            data["runtime_contract"].update(
+                {
+                    "evaluator": "decision_rule_assessment",
+                    "automation_status": "automated",
+                }
+            )
+            tekst = json.dumps(data, ensure_ascii=False, indent=2)
+        (doel / pad.name).write_text(tekst, "utf-8")
+    return doel
+
+
+@pytest.fixture(scope="module")
+def o2_service(o2_regelmap: Path) -> ModularValidationService:
+    return ModularValidationService(
+        toetsregel_manager=ToetsregelManager(base_dir=str(o2_regelmap.parent))
+    )
+
+
+async def _valideer(service, geval, metadata) -> dict[str, Any]:
+    resultaat = await service.validate_definition(
+        begrip=geval["invoer"]["begrip"],
+        text=geval["invoer"]["kern"],
+        context=metadata,
+    )
+    assert resultaat["validation_status"] == "validated", resultaat.get("system")
+    return resultaat
+
+
+# --- de actieve regelset lezen --------------------------------------------------
+
+
+def test_evaluator_voor_leest_actieve_o1_en_expliciete_o2_regelset(o2_service):
+    actief = ModularValidationService(toetsregel_manager=ToetsregelManager())
+    assert actief.evaluator_voor("INT-02") is EvaluatorType.JUDGMENT_REVIEW
+    assert o2_service.evaluator_voor("INT-02") is (
+        EvaluatorType.DECISION_RULE_ASSESSMENT
+    )
+    assert o2_service.evaluator_voor("INT-03") is (
+        EvaluatorType.PRONOUN_REFERENCE_ASSESSMENT
+    )
+    assert o2_service.evaluator_voor("BESTAAT-NIET") is None
+
+
+def test_evaluator_voor_zonder_geldige_regelset_is_none():
+    # Zonder manager is er geen regelset; dan is er ook geen O2-route.
+    assert ModularValidationService().evaluator_voor("INT-02") is None
+
+
+def test_decision_rule_assessment_levert_een_deeluitkomst():
+    assert EvaluatorType.DECISION_RULE_ASSESSMENT in mvs._EVALUATORS_MET_DEELUITKOMST
+
+
+# --- elke status landt in rule_results, zonder cijfer ---------------------------
+
+#: (id, geval, respons, status, reden, actualiteit, document aanvaard)
+STATUSGEVALLEN = [
+    ("pass-C112", ("C112", None), None, "pass", None, "current", True),
+    ("fail-C105", ("C105", None), None, "fail", None, "current", True),
+    (
+        "review-C107",
+        ("C107", None),
+        None,
+        "review_required",
+        "insufficient_information",
+        "current",
+        True,
+    ),
+    ("na-C105", ("C105", None), _na_respons, "not_applicable", None, "current", True),
+    ("error-C117", ("C117", "verzonnen-citaat"), None, "error", None, None, False),
+]
+
+
+@pytest.mark.parametrize(
+    ("geval_id", "respons", "status", "reden", "actualiteit", "aanvaard"),
+    [pytest.param(*rij[1:], id=rij[0]) for rij in STATUSGEVALLEN],
+)
+async def test_elke_o2_status_landt_in_rule_results(
+    o2_service, geval_id, respons, status, reden, actualiteit, aanvaard
+):
+    geval = _geval(*geval_id)
+    document = _document(geval, respons() if callable(respons) else None)
+    assert document.status == status  # WP1 bepaalt; de keten verandert niets
+
+    resultaat = await _valideer(o2_service, geval, _metadata(geval, document))
+
+    assert resultaat["rule_statuses"]["INT-02"] == status
+    detail = resultaat["rule_results"]["INT-02"]
+    assert detail["status"] == status
+    assert detail["score"] is None
+    assert detail["contract_version"] == CONTRACTVERSIE
+    assert detail["review"]["actuality"] == actualiteit
+    assert detail["parts"][0]["reason"] == document.melding
+    if aanvaard:
+        # Het WP1-document onveranderd in rule_results.
+        assert detail["assessment"] == document.als_dict()
+    else:
+        assert detail["assessment"] is None
+    if status == "review_required":
+        assert reden == document.reden
+        (item,) = [r for r in resultaat["review_required"] if r["rule_id"] == "INT-02"]
+        assert item["reason"] == document.melding
+
+
+@pytest.mark.parametrize(
+    ("kern", "context", "ontbreekt"),
+    [
+        pytest.param(None, [], "context", id="context-C56"),
+        pytest.param("Toegang:", ["synthetische context"], "kern", id="label-kern"),
+        pytest.param("", ["synthetische context"], "kern", id="lege-kern"),
+    ],
+)
+async def test_ontbrekende_kern_of_context_is_ne_zonder_oordeel(
+    o2_service, kern, context, ontbreekt
+):
+    # Sinds review F1 beslist onder O2 uitsluitend de O2-evaluator, ook bij
+    # ontbrekende context (O2-vorm: zie de F1-tests hieronder). Beide: NE, exacte
+    # WP1-melding, geen oordeel en geen cijfer.
+    geval = _geval("C56")
+    if kern is not None:
+        geval["invoer"]["kern"] = kern
+    geval["invoer"]["organisatorische_context"] = context
+    document = _document(geval)
+    assert document.status == "not_evaluated"
+
+    resultaat = await _valideer(o2_service, geval, _metadata(geval, document))
+
+    assert resultaat["rule_statuses"]["INT-02"] == "not_evaluated"
+    detail = resultaat["rule_results"]["INT-02"]
+    assert detail["status"] == "not_evaluated"
+    assert detail["score"] is None
+    assert detail["parts"][0]["reason"] == document.melding
+    assert ontbreekt in document.melding
+    assert detail.get("assessment") is None
+    assert not [v for v in resultaat["violations"] if v["code"] == "INT-02"]
+    assert not [r for r in resultaat["review_required"] if r["rule_id"] == "INT-02"]
+
+
+async def test_zonder_document_blijft_int02_expliciet_open(o2_service):
+    geval = _geval("C105")
+    resultaat = await _valideer(o2_service, geval, _metadata(geval))
+    detail = resultaat["rule_results"]["INT-02"]
+    assert detail["status"] == "review_required"
+    assert detail["review"]["actuality"] == "not_assessed"
+    assert detail["parts"][0]["reason"] == MELDING_NIET_BEOORDEELD
+    assert detail["assessment"] is None
+
+
+async def test_adviserende_fail_is_een_zichtbare_violation_zonder_poort(o2_service):
+    geval = _geval("C105")
+    document = _document(geval)
+    resultaat = await _valideer(o2_service, geval, _metadata(geval, document))
+    (violation,) = [v for v in resultaat["violations"] if v["code"] == "INT-02"]
+    assert violation["severity"] == "warning"
+    assert violation["metadata"]["advisory"] is True
+    assert violation["description"] == document.melding
+
+
+async def test_int02_geeft_geen_cijfer_en_geen_poort(o2_service):
+    """Zelfde kern en context, alleen het INT-02-oordeel verschilt: score,
+    categoriescores en acceptatie blijven exact gelijk."""
+    geval = _geval("C105")
+    uitkomsten = {}
+    for naam, respons in (
+        ("pass", _pass_respons_c105()),
+        ("fail", geval["modelrespons"]),
+        ("review_required", _onvoldoende_respons_c105()),
+        ("not_applicable", _na_respons()),
+    ):
+        document = _document(geval, respons)
+        assert document.status == naam
+        resultaat = await _valideer(o2_service, geval, _metadata(geval, document))
+        assert resultaat["rule_statuses"]["INT-02"] == naam
+        uitkomsten[naam] = (
+            resultaat["overall_score"],
+            resultaat["detailed_scores"],
+            resultaat["is_acceptable"],
+            resultaat["acceptance_gate"],
+        )
+    referentie = uitkomsten["pass"]
+    for naam, uitkomst in uitkomsten.items():
+        assert uitkomst == referentie, naam
+
+
+# --- F1 (review WP5a): alleen de O2-evaluator controleert de invoer -------------
+#
+# De voorafgaande `missing_inputs`-check van de service gaf voor INT-02 de
+# oude DEF-771-NE-uitkomst, op `cleaned_text` en vóór de O2-evaluator. Onder
+# O2 hoort de volledige WP1-invoercontrole (exacte recordkern, NE-vorm,
+# ongeldige metadata = error) uitsluitend bij `decision_rule_assessment`.
+
+GEEN_CONTEXT = {
+    "organisatorische_context": [],
+    "juridische_context": [],
+    "wettelijke_basis": [],
+}
+KERN_C105 = "De medewerker laat de aanvrager toe."
+
+
+class _VasteCleaning:
+    """Cleaning die altijd dezelfde tekst oplevert; mag INT-02 niet raken."""
+
+    def __init__(self, tekst: str) -> None:
+        self.tekst = tekst
+
+    def clean_text(self, _tekst):
+        return self.tekst
+
+
+def _assert_o2_vorm(detail: dict[str, Any], status: str, melding: str) -> None:
+    # Eerst status en exacte melding, daarna de O2-documentvorm.
+    assert detail["status"] == status
+    assert [deel["reason"] for deel in detail["parts"]] == [melding]
+    assert detail["score"] is None
+    assert detail["contract_version"] == CONTRACTVERSIE
+    assert detail["review"] == {"actuality": None}
+    assert detail["assessment"] is None
+    (deel,) = detail["parts"]
+    assert deel["id"] == "beoordeling"
+    assert deel["status"] == status
+
+
+@pytest.mark.parametrize(
+    ("kern", "cleaning", "context", "ontbreekt"),
+    [
+        pytest.param(KERN_C105, "", GEEN_CONTEXT, "context", id="kern-cleaning-leeg"),
+        pytest.param(
+            "", KERN_C105, GEEN_CONTEXT, "kern en context", id="leeg-cleaning-kern"
+        ),
+        pytest.param(KERN_C105, None, GEEN_CONTEXT, "context", id="zonder-cleaning"),
+        pytest.param(
+            "",
+            None,
+            {**GEEN_CONTEXT, "organisatorische_context": ["synthetische procedure"]},
+            "kern",
+            id="lege-kern-met-context",
+        ),
+    ],
+)
+async def test_f1_ne_volgt_de_oorspronkelijke_kern_in_o2_vorm(
+    o2_regelmap, kern, cleaning, context, ontbreekt
+):
+    service = ModularValidationService(
+        toetsregel_manager=ToetsregelManager(base_dir=str(o2_regelmap.parent)),
+        cleaning_service=_VasteCleaning(cleaning) if cleaning is not None else None,
+    )
+    resultaat = await service.validate_definition(
+        begrip="toelating",
+        text=kern,
+        context={"record_text": kern, **copy.deepcopy(context)},
+    )
+
+    assert resultaat["validation_status"] == "validated"
+    assert resultaat["rule_statuses"]["INT-02"] == "not_evaluated"
+    _assert_o2_vorm(
+        resultaat["rule_results"]["INT-02"],
+        "not_evaluated",
+        MELDING_NE.replace("{kern/context}", ontbreekt),
+    )
+
+
+@pytest.mark.parametrize(
+    "over",
+    [
+        pytest.param({"record_text": None}, id="recordkern-none"),
+        pytest.param({"int02_bedoeling": 42}, id="bedoeling-getal"),
+    ],
+)
+async def test_f1_ongeldige_metadata_zonder_context_is_error(o2_service, over):
+    metadata = {"record_text": KERN_C105, **copy.deepcopy(GEEN_CONTEXT), **over}
+
+    resultaat = await o2_service.validate_definition(
+        begrip="toelating", text=KERN_C105, context=metadata
+    )
+
+    assert resultaat["rule_statuses"]["INT-02"] == "error"
+    _assert_o2_vorm(resultaat["rule_results"]["INT-02"], "error", MELDING_E)
+    assert not [v for v in resultaat["violations"] if v["code"] == "INT-02"]
+    assert not [r for r in resultaat["review_required"] if r["rule_id"] == "INT-02"]
diff --git a/tests/unit/services/test_def835_int02_container.py b/tests/unit/services/test_def835_int02_container.py
new file mode 100644
index 000000000..e5d45a1c2
--- /dev/null
+++ b/tests/unit/services/test_def835_int02_container.py
@@ -0,0 +1,179 @@
+"""DEF-835 WP5a: de container bouwt INT-02 (O2) alleen op expliciet verzoek (eerst rood).
+
+`ServiceContainer.int02_assessment_service` construeert de WP2-dienst
+uitsluitend met een expliciet `Modelprofiel` en een expliciet `Budget`: geen
+default, geen singleton, geen profiel of budget van een andere regel
+(INT-03/ESS-03/bronnen) en geen modelaanroep bij constructie. De normale
+`orchestrator()` blijft O1: zij bouwt of injecteert geen INT-02-dienst, ook
+niet nadat de factory is gebruikt. Een expliciet gebouwde dienst bereikt via
+de bestaande DI (`DefinitionOrchestratorV2`) wél de validatiewrapper.
+"""
+
+from __future__ import annotations
+
+import inspect
+
+import pytest
+
+from services.container import ServiceContainer
+from services.orchestrators.validation_orchestrator_v2 import ValidationOrchestratorV2
+from services.validation import int02_assessment_service as int02_module
+from services.validation.int02_assessment_service import (
+    Budget,
+    Int02AssessmentService,
+    Int02ServiceConfigError,
+    Modelprofiel,
+)
+from services.validation.modular_validation_service import ModularValidationService
+from toetsregels.manager import ToetsregelManager
+from toetsregels.runtime_contract import EvaluatorType
+
+pytestmark = [pytest.mark.unit]
+
+PROFIEL = Modelprofiel(
+    profiel_id="wp5a-container-fixture",
+    provider="fakeprovider",
+    model="fake-int02-model",
+    kwalificatie="testfixture; geen kwaliteitsclaim",
+)
+BUDGET = Budget(
+    max_uitvoertokens=800,
+    deadline_seconden=5.0,
+    max_invoertekens_veld=2000,
+    max_invoertekens_totaal=6000,
+    max_antwoordtekens=20000,
+)
+
+
+class _TellendeAI:
+    """AI-grens die elke aanroep telt; een aanroep is hier altijd fout."""
+
+    def __init__(self):
+        self.calls = 0
+
+    async def generate_definition(self, *args, **kwargs):  # pragma: no cover
+        self.calls += 1
+        raise AssertionError("geen modelaanroep verwacht")
+
+
+class _Router:
+    def get_model(self, task_type):  # pragma: no cover - niet aangeroepen
+        raise AssertionError("geen routering bij constructie verwacht")
+
+
+class _Repo:
+    pass
+
+
+@pytest.fixture
+def container(monkeypatch):
+    """Container zonder echte AI-client, database of webdiensten."""
+    c = ServiceContainer.__new__(ServiceContainer)
+    c._instances = {}
+    c._lazy_instances = {}
+    c.use_json_rules = True
+    ai, router = _TellendeAI(), _Router()
+    monkeypatch.setattr(c, "ai_service", lambda: ai, raising=False)
+    monkeypatch.setattr(c, "model_router", lambda: router, raising=False)
+    monkeypatch.setattr(c, "cleaning_service", lambda: object(), raising=False)
+    monkeypatch.setattr(c, "repository", lambda: _Repo(), raising=False)
+    monkeypatch.setattr(c, "web_lookup", lambda: None, raising=False)
+    monkeypatch.setattr(c, "synonym_orchestrator", lambda: None, raising=False)
+    monkeypatch.setattr(ServiceContainer, "rag_service", property(lambda _s: None))
+    for naam in (
+        "source_assessment_service",
+        "ess03_assessment_service",
+        "int03_assessment_service",
+    ):
+        monkeypatch.setattr(c, naam, lambda: object(), raising=False)
+    c.fake_ai, c.fake_router = ai, router
+    return c
+
+
+@pytest.fixture
+def constructies(monkeypatch):
+    """Telt elke constructie van de INT-02-dienst in dit proces."""
+    teller: list[dict] = []
+    origineel = Int02AssessmentService.__init__
+
+    def _init(self, *args, **kwargs):
+        teller.append(kwargs)
+        origineel(self, *args, **kwargs)
+
+    monkeypatch.setattr(Int02AssessmentService, "__init__", _init)
+    return teller
+
+
+def test_factory_vereist_expliciet_profiel_en_budget_zonder_default(container):
+    handtekening = inspect.signature(container.int02_assessment_service)
+    for naam in ("profiel", "budget"):
+        parameter = handtekening.parameters[naam]
+        assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
+        assert parameter.default is inspect.Parameter.empty
+
+    with pytest.raises(TypeError):
+        container.int02_assessment_service()
+    with pytest.raises(Int02ServiceConfigError):
+        container.int02_assessment_service(profiel=None, budget=BUDGET)
+    with pytest.raises(Int02ServiceConfigError):
+        container.int02_assessment_service(profiel=PROFIEL, budget=None)
+
+
+def test_factory_bouwt_op_expliciet_verzoek_zonder_modelaanroep(
+    container, constructies
+):
+    dienst = container.int02_assessment_service(profiel=PROFIEL, budget=BUDGET)
+
+    assert isinstance(dienst, Int02AssessmentService)
+    assert dienst._ai_service is container.fake_ai
+    assert dienst._model_router is container.fake_router
+    assert dienst._profiel is PROFIEL
+    assert dienst._budget is BUDGET
+    assert len(constructies) == 1
+    assert container.fake_ai.calls == 0
+    # Geen singleton en geen registratie voor de orchestrator.
+    assert dienst not in container._instances.values()
+    tweede = container.int02_assessment_service(profiel=PROFIEL, budget=BUDGET)
+    assert tweede is not dienst
+
+
+def test_normale_orchestrator_blijft_o1_zonder_int02_dienst(container, constructies):
+    # Ook nadat de factory is gebruikt, bedraadt orchestrator() niets.
+    container.int02_assessment_service(profiel=PROFIEL, budget=BUDGET)
+    constructies.clear()
+
+    orchestrator = container.orchestrator()
+    wrapper = orchestrator.validation_service
+
+    assert isinstance(wrapper, ValidationOrchestratorV2)
+    assert orchestrator.int02_assessment_service is None
+    assert wrapper.int02_assessment_service is None
+    assert constructies == []
+    assert container.fake_ai.calls == 0
+
+
+def test_expliciet_gebouwde_dienst_bereikt_de_validatiewrapper(container):
+    from services.orchestrators.definition_orchestrator_v2 import (
+        DefinitionOrchestratorV2,
+    )
+
+    dienst = container.int02_assessment_service(profiel=PROFIEL, budget=BUDGET)
+    orchestrator = DefinitionOrchestratorV2(
+        ai_service=container.ai_service(),
+        cleaning_service=object(),
+        repository=_Repo(),
+        int02_assessment_service=dienst,
+    )
+    assert orchestrator.validation_service.int02_assessment_service is dienst
+
+
+def test_actieve_ssot_houdt_int02_op_o1():
+    service = ModularValidationService(toetsregel_manager=ToetsregelManager())
+    assert service.evaluator_voor("INT-02") is EvaluatorType.JUDGMENT_REVIEW
+
+
+def test_wp2_dienst_kent_geen_default_profiel_of_budget():
+    # Geen profielbudget van een andere regel als O2-kwalificatie: de module
+    # definieert zelf geen profiel- of budgetinstantie om op terug te vallen.
+    for waarde in vars(int02_module).values():
+        assert not isinstance(waarde, Modelprofiel | Budget)
~~~~~
