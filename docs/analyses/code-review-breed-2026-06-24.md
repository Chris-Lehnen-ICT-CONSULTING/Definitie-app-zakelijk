# Brede code-review — DefinitieAgent

> Multi-agent review (10 finder-lanes → adversariële verificatie per bevinding). 80 ruwe bevindingen, **52 bevestigd** na verificatie (28 weerlegd als false-positive). Datum: 2026-06-24. Branch: `feature/DEF-439-mypy-import-resolutie`.

**Ernst-verdeling:** 🔴 kritiek 7 · 🟠 hoog 22 · 🟡 middel 16 · ⚪ laag 7

## Async / race conditions (14)

### 1. 🔴 [KRITIEK] asyncio.run() in Streamlit context (async_progress.py)
**Locatie:** `src/ui/async_progress.py:155`

Streamlit already runs a sync event loop. Calling asyncio.run() from within the Streamlit UI thread will raise RuntimeError: 'asyncio.run() cannot be called from a running event loop'. This blocks the UI and crashes the page.

```python
result = asyncio.run(
    self._async_processing_wrapper(
        form_data, toetsregels, progress_container
    )
)
```
**Fix:** Use run_async() from ui.helpers.async_bridge instead: result = run_async(self._async_processing_wrapper(...), timeout=120)
<details><summary>Verificatie (hoog)</summary>

Geverifieerd in /Users/chrislehnen/Projecten/Definitie-app/src/ui/async_progress.py:155. De code roept `asyncio.run()` direct aan vanuit een Streamlit UI button callback (lijn 136). Streamlit draait een event loop in de UI thread, dus `asyncio.run()` zal `RuntimeError: asyncio.run() cannot be called from a running event loop` gooien, wat de UI blokkeert en de pagina crasht.

Bewijsmateriaal:
1. async_progress.py:136 - button click roept `run_async_definition_processing()` aan
2. async_progress.py:142-162 - deze methode roept `asyncio.run()` direct aan zonder loop-detectie
3. async_bridge.py:19-56 - het codebase bevat zelf een `run_async()` workaround die deze case handelt
4. De fout is fundamenteel: Streamlit's event loop zal aanwezig zijn, `asyncio.run()` kan niet worden aangeroepen met een draaiende loop

Dit is geen edge-case - dit is een crash in de productiepad wanneer gebruiker op de "Generate Definition (Fast Mode)" knop klikt. Severity = kritiek omdat het een productie-crash is.

</details>

### 2. 🔴 [KRITIEK] asyncio.run() in Streamlit page (synonym_admin.py)
**Locatie:** `src/pages/synonym_admin.py:195`

Same issue: asyncio.run() called from Streamlit's sync context (inside st.spinner). Will raise RuntimeError when the Streamlit event loop is running, crashing the synonym admin page.

```python
synonyms, ai_pending_count = asyncio.run(
    orchestrator.ensure_synonyms(
        term=term.strip(), min_count=min_count, context=None
    )
)
```
**Fix:** Replace with: from ui.helpers.async_bridge import run_async; synonyms, ai_pending_count = run_async(orchestrator.ensure_synonyms(...), timeout=30)
<details><summary>Verificatie (hoog)</summary>

De code op regel 195-199 in /Users/chrislehnen/Projecten/Definitie-app/src/pages/synonym_admin.py roept asyncio.run() aan binnen st.spinner(), wat in Streamlit's sync context draait. Dit zal RuntimeError veroorzaken als Streamlit een event loop heeft. De daadwerkelijke code lezen toont aan: (1) orchestrator.ensure_synonyms() is async (definitie op regel 218 in synonym_orchestrator.py); (2) asyncio.run() wordt direct aangeroepen op regel 195; (3) dit staat binnen st.spinner() op regel 192; (4) andere components in dezelfde codebase gebruiken correct run_async() uit /src/ui/helpers/async_bridge.py (bv. definition_edit_tab.py), die exact dit probleem oplost door event loop detectie en ThreadPoolExecutor gebruik. De bug veroorzaakt een crash van de gehele synonym_admin pagina bij de principale user-flow.

</details>

### 3. 🟠 [HOOG] Timeout consumed by rate-limit acquire, leaving no budget for execution
**Locatie:** `src/utils/integrated_resilience.py:211`

The full `timeout` is passed to rate_limiter.acquire(). If acquire takes (e.g.) 5 seconds on a 10-second timeout, the remaining execution time is still 10 seconds (not 5), because the same timeout value is reused. This violates DEF-428's intent: the total operation (rate-limit + execution + retries) should be bounded by the single timeout. If acquire uses most of the budget, the execution timeout is too generous, allowing hangs. The timeout should be decremented after acquire completes.

```python
Line 211: if not await rate_limiter.acquire(priority, timeout, request_id):
Line 230: result = await asyncio.wait_for(execution, timeout)
```
**Fix:** After acquire() completes, calculate remaining_timeout = timeout - (time.time() - start_time) and pass remaining_timeout to wait_for(), or restructure to use a single outer wait_for() that wraps the entire operation (acquire + retry + execution).
<details><summary>Verificatie (hoog)</summary>

De bevinding is substantieel correct. De code in `/Users/chrislehnen/Projecten/Definitie-app/src/utils/integrated_resilience.py` behandelt timeout onjuist:

ECHTE CODE (regels 210-230):
```python
if not await rate_limiter.acquire(priority, timeout, request_id):  # Line 211
    msg = f"Rate limit timeout for {endpoint_name}"
    raise TimeoutError(msg)

execution = self._execute_with_retry_and_resilience(...)
if timeout is not None:
    result = await asyncio.wait_for(execution, timeout)  # Line 230 - DEZELFDE timeout hergebruikt
```

HET PROBLEEM:
1. De volledige `timeout` waarde wordt gegeven aan `rate_limiter.acquire()` op regel 211
2. Als acquire() bijvoorbeeld 8 seconden duurt op een 10-seconde totaal-timeout, bestrijkt het 80% van het budget
3. Regel 230 hergebruikt dezelfde `timeout=10` waarde voor `execution`, zonder af te trekken wat acquire() verbruikt
4. Dit schendt de DEF-428 intentie: "the total operation (rate-limit + execute + retries) should be bounded by the single timeout"

PRAKTISCHE IMPACT:
- Geen hang (asyncio.wait_for() enforceert deadline)
- Wel een timeout-budgetting-fout: acquire + execute kunnen elk tot de volle timeout duren
- Operaties kunnen langer duren dan bedoeld, bijv. 18s totaal op een 10s timeout-poging

SEVERITY AANPASSING:
- Claim zei "kritiek", maar dat is overdreven (geen crash/hang/data-verlies)
- Dit is een "hoog" severity bug: duidelijke logica-fout die tegen design-intent ingaat en gebruikersimpact heeft (operaties nemen langer dan timeout-limit)
- Niet "middel" omdat het geen edge-case is — het gebeurt altijd, rate_limiter.acquire() verbruikt altijd budget

</details>

### 4. 🟠 [HOOG] Race Condition in edit_tab Auto-Load Between Multiple concurrent st.rerun() Calls
**Locatie:** `src/ui/components/definition_edit_tab.py:75-115`

Although there is version tracking to detect concurrent loads (edit_load_version), the handling is incomplete. When a concurrent load is detected (latest_version != new_load_version), the code shows st.info() but does NOT return - it continues rendering and shows BOTH the stale data message AND the old UI state. The session data is not applied (line 117-120 is skipped), but the edit interface continues to render with potentially stale definition data. Multiple rapid st.rerun() calls (e.g., user clicking buttons quickly) can cause the render() method to execute multiple times with out-of-sync version numbers, leading to confusion about which definition is being edited.

```python
if should_load:
                # DEF-236: Race condition fix - use version tracking to detect concurrent loads
                # Increment load version BEFORE starting the load operation
                current_load_version = SessionStateManager.get_value(
                    "edit_load_version", 0
                )
                new_load_version = current_load_version + 1
                SessionStateManager.set_value("edit_load_version", new_load_version)
                logger.debug(
                    f"Starting edit load v{new_load_version} for definition {target_id}"
                )

                # Probeer sessie te starten zodat geschiedenis/auto-save beschikbaar zijn
                session = self.edit_service.start_edit_session(
                    target_id, user=SessionStateManager.get_value("user") or "system"
                )
                if session and session.get("success"):
                    # DEF-236: Check if another load was triggered while we were loading
                    # If version changed, another load started - don't apply stale data
                    latest_version = SessionStateManager.get_value(
                        "edit_load_version", 0
                    )
                    if latest_version != new_load_version:
                        logger.warning(
                            f"Concurrent edit tab load detected - skipping stale data "
                            f"(started v{new_load_version}, current v{latest_version})",
                        )
                        # Don't return! Show info and let UI continue rendering
                        st.info(
                            "🔄 Gelijktijdige laadoperatie gedetecteerd. "
                            "De nieuwste versie wordt geladen."
                        )
```
**Fix:** When concurrent load is detected, either: (1) return early to skip rendering, OR (2) force a st.rerun() after showing the message to ensure the latest data is loaded. Currently 'skipping stale data' but still rendering UI is contradictory.
<details><summary>Verificatie (hoog)</summary>

The race condition in definition_edit_tab.py lines 97-114 is REAL and creates a data corruption risk. When concurrent auto-loads are detected, the code shows an st.info() message but does NOT update 'editing_definition' from the loaded session. This causes a mismatch between 'editing_definition_id' (which is updated by user clicks) and 'editing_definition' (which remains stale). 

The critical issue: Line 470 creates widget keys based on definition.id from the stale definition (e.g., 'edit_5_*'), but line 1214 in _save_definition() creates keys based on editing_definition_id (e.g., 'edit_20_*'). When the user edits and saves, widget values are stored in one key set ('edit_5_*') but the save function looks for them in another ('edit_20_*'), causing data loss or applying changes to the wrong definition.

Verified in actual code:
- Lines 97-113: Race detection path doesn't set 'editing_definition' (only the else block at 117-120 does)
- Line 470: Widget key function uses definition.id from potentially stale definition
- Line 1214: Save function creates keys from editing_definition_id
- No defensive mismatch check between editing_definition.id and editing_definition_id

The bug is self-correcting only if the next render cycle's auto-load succeeds without another race, but during the race window there IS a real risk of data loss.

</details>

### 5. 🟠 [HOOG] Race condition in definition edit tab auto-load with stale data application
**Locatie:** `src/ui/components/definition_edit_tab.py:75-121`

The concurrent load detection (DEF-236) increments edit_load_version before loading, then checks if the version changed during load. However, the code continues rendering the UI after detecting a concurrent load (line 114: 'Skip applying stale session data, but continue UI rendering'). The stale session data (editing_definition, edit_session) may have been partially applied by button handlers or other concurrent code, and the UI continues rendering with this inconsistent state. A true fix would require either blocking until the latest load completes, or clearing all edit state before starting a new load.

```python
# Start load
SessionStateManager.set_value("edit_load_version", new_load_version)
# ... async loading (no await)
session = self.edit_service.start_edit_session(target_id, ...)

# Check version AFTER load completes
latest_version = SessionStateManager.get_value("edit_load_version", 0)
if latest_version != new_load_version:
    # Skip data BUT continue UI rendering
    # No return - UI may still use stale data
```
**Fix:** On concurrent load detection, do NOT continue with UI rendering. Call st.rerun() or return early from render() to force a fresh render cycle with the latest definition.
<details><summary>Verificatie (hoog)</summary>

De race condition is geverifieerd in echte code. Het mechanisme werkt als volgt:

1. DETECTION (regels 75-121): Code detecteert concurrent loads via versie-tracking (edit_load_version). Bij concurrent load (regel 97: `if latest_version != new_load_version`), skipped het het setzen van `editing_definition` (regel 118 wordt gepassteerd).

2. KRITIEK GEVOLG: Regel 109-114 voert een `st.info()` uit maar geen `return` - de render() gaat door. Dit betekent dat:
   - `editing_definition_id` is WEL gezet (naar de nieuwe ID)
   - `editing_definition` is NIET bijgewerkt (stale waarde blijft)

3. RENDER MISMATCH (regel 181): De check `if SessionStateManager.get_value("editing_definition_id")` is True (huidige ID), dus de code roept `_render_editor()` aan. Maar `_render_editor()` (regel 463) haalt de stale `editing_definition` op.

4. WIDGET SCOPING MISMATCH (regel 470): `_render_editor()` gebruikt `f"edit_{definition.id}_{name}"` met definition.id van de STALE definitie, dus de widget keys worden geinitialiseerd met oude data terwijl `editing_definition_id` het nieuwe ID bevat.

5. DATA-VERLIES (regels 1213-1214 in `_save_definition()`): `_save_definition()` bouwt keys op basis van `editing_definition_id` (correct) en haalt values op van e.g. `edit_200_begrip`, maar deze keys zijn NOOIT ingevuld (omdat `_render_editor()` `edit_100_***` keys gebruikte). Dit resulteert in het opslaan van lege/default values naar verkeerde definitie.

Dit is een concrete, geverifieerde bug met direct data-verlies risico, niet enkel een edge-case. De severity "hoog" is correct - het is geen crash/hang (niet kritiek) maar wel duidelijke functionaliteit-bug met gebruikersimpact.

</details>

### 6. 🟡 [MIDDEL] Unguarded deque.remove() race with background _process_queues
**Locatie:** `src/utils/smart_rate_limiter.py:357`

In acquire(), when a request times out, it tries to remove itself from the queue (line 357). Concurrently, _process_queues may be iterating over the same queue and calling popleft() (line 383). The deque is not protected by a lock, so a concurrent remove() during iteration can cause IndexError or ValueError. The try/except silently catches ValueError (line 358), but a crash is still possible if the deque structure is corrupted. This is a classic TOCTOU (time-of-check-time-of-use) bug.

```python
Line 357 (in acquire timeout handler): self.priority_queues[priority].remove(queued_request)
Line 383 (in _process_queues): request = queue.popleft()
```
**Fix:** Protect both deque operations with an asyncio.Lock: async with self._queue_lock: self.priority_queues[priority].remove(queued_request) in acquire(), and async with self._queue_lock: request = queue.popleft() in _process_queues().
<details><summary>Verificatie (hoog)</summary>

Echte async race condition geverifieerd in /Users/chrislehnen/Projecten/Definitie-app/src/utils/smart_rate_limiter.py. Op regel 357 roept acquire() timeout handler `self.priority_queues[priority].remove(queued_request)` aan zonder lock. Tegelijkertijd roept _process_queues() op regel 383 `queue.popleft()` aan op dezelfde deque. De deque is niet beschermd door een asyncio.Lock() (alleen de TokenBucket heeft een lock, niet de priority_queues dict). Hoewel Python's GIL individuele deque-operaties atomic maakt, zijn `remove()` (lineaire scan) en `popleft()` niet transactioneel. De try/except ValueError op regel 358 beschermt alleen tegen het geval dat de request al weg is, niet tegen echte concurrency-corruptie. Dit is een TOCTOU-bug. Severity blijft middel omdat: (1) GIL beschermt tegen crashes in praktijk, (2) het enige effect is timeout-requests die niet goed verwijderd worden of race-voorwaarden in queue-verwerking, (3) niet kritiek, maar wel een logische defect in de synchronisatie-semantiek.

</details>

### 7. 🟡 [MIDDEL] Global singleton not protected during concurrent initialization
**Locatie:** `src/utils/integrated_resilience.py:369`

get_integrated_system() is an async function called from multiple decorators. Two concurrent calls can both see _integrated_system as None and attempt to initialize it in parallel, creating two instances and running start() twice. This causes duplicate rate limiters, retry managers, and resilience framework instances, breaking singleton invariants and consuming extra resources.

```python
Lines 369-373:
global _integrated_system
if _integrated_system is None:
    _integrated_system = IntegratedResilienceSystem(config)
    await _integrated_system.start()
```
**Fix:** Use a asyncio.Lock to guard initialization: if not hasattr(module, '_init_lock'): module._init_lock = asyncio.Lock(). In get_integrated_system(), wrap the check and initialization: async with _init_lock: if _integrated_system is None: ... This ensures only one caller initializes.
<details><summary>Verificatie (hoog)</summary>

De bevinding is GEVERIFIEERD als echte bug. Bewijs:

1. **Code locatie:** /Users/chrislehnen/Projecten/Definitie-app/src/utils/integrated_resilience.py:369-373
```python
async def get_integrated_system(
    config: IntegratedConfig | None = None,
) -> IntegratedResilienceSystem:
    global _integrated_system
    if _integrated_system is None:
        _integrated_system = IntegratedResilienceSystem(config)
        await _integrated_system.start()
    return _integrated_system
```

2. **Race condition scenario:** De module-level global `_integrated_system` (regel 362) kan worden geinitialiseerd door twee concurrent async event loops. Dit treedt op omdat:
   - `get_integrated_system()` wordt aangeroepen vanuit decorators (@with_full_resilience)
   - Deze decorators werken in het `wrapper()` coroutine (regel 410-411 van hetzelfde bestand)
   - De async_bridge.py (regel 207) maakt ThreadPoolExecutor-workers aan die elk SEPARATE asyncio event loops draaien
   - Twee threads kunnen tegelijk regel 370 bereiken (if _integrated_system is None) voor beide True is

3. **Praktisch bewijs:** Ik heb een proof-of-concept geschreven die ditzelfde pattern simuleert, en het **creëert werkelijk twee instances** in plaats van één.

4. **Impact:** 
   - Twee IntegratedResilienceSystem instances breken het singleton pattern
   - Twee SmartRateLimiter instances per endpoint (ineffectieve rate limiting)
   - Twee AdaptiveRetryManager instances (inconsistent retry state)
   - Resource waste en potential memory leak (tweede instance wordt nooit proper gestopt)

5. **Severity aanpassing:** MIDDEL is correct:
   - NIET kritiek: geen data-verlies of directe crash (systeem start wel op met resources)
   - NIET laag: singleton pattern is fundamenteel gebroken, rate limiting wordt ineffectief
   - MIDDEL: sluimerende bug met impact op system resilience en resource management

</details>

### 8. 🟡 [MIDDEL] asyncio.run(asyncio.wait_for(...)) nesting in definitie_agent.py
**Locatie:** `src/orchestration/definitie_agent.py:130`

Nesting asyncio.wait_for inside asyncio.run is redundant but not immediately broken. However, if called from a context where an event loop already exists (e.g., via run_async or FastAPI), it will fail. The asyncio.wait_for creates a coroutine that asyncio.run tries to execute, but the architecture is fragile.

```python
v2_result = asyncio.run(asyncio.wait_for(_task(), timeout=120))
```
**Fix:** Restructure: either use async context directly with wait_for, or move wait_for inside the coroutine: async def _task() -> dict[str, Any]: return await asyncio.wait_for(adapter.generate_definition(...), timeout=120)
<details><summary>Verificatie (hoog)</summary>

De bevinding is werkelijk geverifieerd in de code (beide `/Users/chrislehnen/Projecten/Definitie-app/src/orchestration/definitie_agent.py:130` en `/Users/chrislehnen/Projecten/Definitie-app/src/integration/definitie_checker.py:257,368` bevatten `asyncio.run(asyncio.wait_for(..., timeout=120))`). Dit patroon is inderdaad redundant omdat `asyncio.wait_for()` reeds een timeout-aware wrapper is, en het nesten binnenin `asyncio.run()` slecht design is. ECHTER: Dit is geen actuele production bug op dit moment omdat: (1) `DefinitieAgent` is legacy/unused, (2) `DefinitieChecker.generate_with_check` wordt alleen gebruikt in de synchrone CLI-tool context, niet in async contexten. Het RISICO is dat toekomstige refactoring (bijv. FastAPI-integratie, of direct aanroep vanuit Streamlit async callbacks) dit zal breken. Severity is MIDDEL (geen huidig risico, maar architecturaal probleem dat toekomstige bugs kan introduceren) in plaats van HOOG (zou kritiek zijn als het nu in productie-code actief was).

</details>

### 9. 🟡 [MIDDEL] Fire-and-forget tasks without tracking (smart_rate_limiter.py, resilience.py)
**Locatie:** `src/utils/smart_rate_limiter.py:282`

In _ensure_processor_running(), the old _processing_task is abandoned without proper cleanup. If the old task is still running on a different event loop, it will leak and continue running in the background, consuming resources. The code checks if task.done() or loop.is_closed(), but doesn't cancel the old task before reassigning.

```python
self._processing_task = asyncio.create_task(self._process_queues())
# ... later: if not needs_restart: return
# no await or tracking of old task before creating new one
```
**Fix:** Before reassigning, cancel the old task: if self._processing_task and not self._processing_task.done(): self._processing_task.cancel(); try: await self._processing_task; except asyncio.CancelledError: pass
<details><summary>Verificatie (middel)</summary>

De bevinding wijst op een legit architectural concern, maar niet een acute bug. In `/Users/chrislehnen/Projecten/Definitie-app/src/utils/smart_rate_limiter.py:281-283` creëert `_ensure_processor_running()` inderdaad een nieuwe taak zonder de oude `_processing_task` te cancellen. ECHTER: (1) De code erkent dit expliciet (regel 279-280 comment): "niet awaiten of cancellen (die loop draait niet meer) — referentie loslaten volstaat." Dit is een **bewuste design-keuze**, niet onbewust. (2) Het patroon is specifiek voor de DEF-429 singleton-hergebruik-over-loops use-case: de oude loop is al gesloten of wordt niet opnieuw gebruikt. (3) Cancellen op een gesloten loop kan zelf falen. Dus de trade-off is: verlaten taak op gesloten loop vs. risico van `.cancel()` op dode loop. Severity aangepast naar MIDDEL omdat: het leidt niet tot directe data-verlies of crash in normale flow; het is een edge-case (singleton hergebruik); de auteur het scenario heeft voorzien. Echter: als de loop **niet** gesloten is maar wel opnieuw gebruikt (bug in DEF-429 logica), zou contention optreden. Dit verhoogt het risico boven LAAG.

</details>

### 10. 🟡 [MIDDEL] Background tasks created but not awaited (resilience.py start method)
**Locatie:** `src/utils/resilience.py:428`

Both tasks are created but never awaited in the start() method. If the event loop is garbage-collected before these tasks complete, they will be cancelled and logged as 'Task was destroyed but it is pending'. This causes silent failures and resource leaks, especially in test/reload scenarios.

```python
self._queue_processor_task = asyncio.create_task(
    self._process_dead_letter_queue()
)
self._cache_cleanup_task = asyncio.create_task(self._cleanup_fallback_cache())
```
**Fix:** Tasks are started correctly but need proper lifecycle: ensure stop() is always called before loop shutdown. Document that these tasks require the event loop to remain alive. Consider using a task group (Python 3.11+) for better lifecycle management.
<details><summary>Verificatie (hoog)</summary>

De bevinding is GEDEELTELIJK correct, maar om andere redenen dan opgesteld.

GEVERIFIEERD IN CODE:
1. /Users/chrislehnen/Projecten/Definitie-app/src/utils/resilience.py:428-431 — `asyncio.create_task()` wordt CORRECT gebruikt (tasks MOETEN niet in start() worden awaited; ze zijn background tasks)
2. /Users/chrislehnen/Projecten/Definitie-app/src/utils/resilience.py:449-451 — `await task` staat WEL in stop(), dus cleanup IS voorzien
3. /Users/chrislehnen/Projecten/Definitie-app/src/utils/integrated_resilience.py:550-556 — cleanup_integrated_system() BESTAAT maar wordt NERGENS in production aangeroepen

KERNPROBLEEM (NOT mentioned in original finding):
- In Streamlit/asyncio.run() contexten (o.a. /Users/chrislehnen/Projecten/Definitie-app/src/ui/async_progress.py:155) worden telkens nieuwe event loops aangemaakt en vernietigdm
- get_integrated_system() aanroepen startst tasks in loop A
- Loop A eindigt → tasks orphaned (geen stop() call)
- Dit leidt inderdaad tot "Task was destroyed" warnings bij GC

Dit is GEEN code-bug in start() zelf (die code is correct), maar een ARCHITECTURAL issue: resilience framework start() wordt geawaited, maar stop() wordt NEVER geawaited in production. In Streamlit-rerun scenario's resulteert dit in orphaned tasks.

SEVERITY aanpassen van HOOG naar MIDDEL omdat:
- De start() code zelf is correct (async.create_task is proper usage)
- Het risico manifesteert zich alleen in specific reload/rerun scenario's
- Er is geen data-verlies, alleen warnings/resource leaks
- De stop() code is correct voor als deze WEL wordt aangeroepen

</details>

### 11. 🟡 [MIDDEL] Async Timeout in run_async() Does Not Propagate Timeout Exceptions to UI
**Locatie:** `src/ui/helpers/async_bridge.py:50-56`

The run_async() function handles TimeoutError in the run_async_safe() variant (line 76-78) but NOT in the regular run_async() used in definition_generation_handler.py line 277. When definition_service.generate_definition() times out (line 299 timeout=120), asyncio.TimeoutError is raised but there is no try-except at the call site in handle_definition_generation(). The exception will be caught by the outer try-except on line 479 and shown as generic error. The user sees '❌ Fout bij generatie: TimeoutError...' instead of a clear message that the generation took too long. This is especially problematic because the LLM request may have partially completed, leaving inconsistent state.

```python
# No running loop - create new one
    if timeout:

        async def with_timeout() -> T:
            return await asyncio.wait_for(coro, timeout)

        return asyncio.run(with_timeout())
    return asyncio.run(coro)
```
**Fix:** In definition_generation_handler.py, wrap the run_async() call in a try-except that specifically catches asyncio.TimeoutError and shows a user-friendly message like 'Definition generation took longer than expected (120 seconds). Please try again.'
<details><summary>Verificatie (hoog)</summary>

De bevinding is GEDEELTELIJK correct maar niet helemaal nauwkeurig in details.

BEVONDEN CODE:
- /Users/chrislehnen/Projecten/Definitie-app/src/ui/handlers/definition_generation_handler.py:272-295 roept `run_async(..., timeout=120)` aan
- /Users/chrislehnen/Projecten/Definitie-app/src/ui/helpers/async_bridge.py:50-56 implementeert `run_async()` zonder try-except voor TimeoutError in het no-loop pad
- /Users/chrislehnen/Projecten/Definitie-app/src/ui/helpers/async_bridge.py:42-44 implementeert ThreadPoolExecutor path die concurrent.futures.TimeoutError kan werpen
- /Users/chrislehnen/Projecten/Definitie-app/src/ui/handlers/definition_generation_handler.py:475 vangt alle Exception af met generiek bericht

ECHTE SITUATIE:
1. TimeoutError WORDT wel afgevangen (line 475 in definition_generation_handler.py)
2. Maar het wordt afgevangen als generieke Exception, niet als specifieke TimeoutError
3. User krijgt "❌ Fout bij generatie: {exception}" in plaats van duidelijk timeout-bericht
4. In Streamlit-context (concurrent.futures.TimeoutError via ThreadPoolExecutor) is het bericht ook generiek
5. De service (ai_service_v2.py:277-286) vangt TimeoutError af en werpt AITimeoutError, dus interne timeouts zijn al beter afgehandeld

WAAROM MIDDEL (NIET HOOG):
- TimeoutError is AFGEVANGEN (geen crash/unhandled exception)
- User krijgt wél een error-melding
- Geen data-verlies of inconsistente state als direct probleem
- Het is UX-issue (onduidelijk bericht) in plaats van functioneel defect

WAAROM ECHTER REAL:
- Expliciete TimeoutError handling ontbreekt in run_async()
- Het generieke exception-bericht is slecht UX
- run_async_safe() HAD al TimeoutError handling (lijn 76-78), dus dit is inconsistent
- In pad 1 (Streamlit context, line 42-44) kan TimeoutError onopgemerkt blijven als concurrent.futures.TimeoutError

CODE FRAGMENT:
Lines 272-295 in definition_generation_handler.py:
```python
_response = run_async(
    self.definition_service.generate_definition(...),
    timeout=120,
)
```

Lines 50-56 in async_bridge.py (NO EXCEPTION HANDLING):
```python
if timeout:
    async def with_timeout() -> T:
        return await asyncio.wait_for(coro, timeout)
    return asyncio.run(with_timeout())
return asyncio.run(coro)
```

Lines 42-44 in async_bridge.py (TimeoutError kan hier onbehandeld uit ThreadPoolExecutor komen):
```python
with ThreadPoolExecutor(max_workers=1) as executor:
    future = executor.submit(asyncio.run, coro)
    return future.result(timeout=timeout) if timeout else future.result()
```

Lines 75-78 in async_bridge.py (run_async_safe HAS handling):
```python
except TimeoutError:
    logger.warning(f"Async operation timed out after {timeout}s")
    return default
```

</details>

### 12. 🟡 [MIDDEL] Race Condition: Global Cache Without Locks
**Locatie:** `src/api/feature_status_api.py:107-128`

Multiple concurrent requests can simultaneously read stale cache, load file, and write back, causing inconsistent state or redundant I/O. The check-then-set pattern (lines 110-113 vs 127-128) is not atomic.

```python
global _feature_cache, _cache_timestamp
...
if _feature_cache and _cache_timestamp:
    ... (read)
...
_feature_cache = data
_cache_timestamp = datetime.now(UTC)
```
**Fix:** Use asyncio.Lock or threading.Lock to synchronize cache access, or prefer FastAPI's dependency injection with caching decorator like @lru_cache or limiter.
<details><summary>Verificatie (hoog)</summary>

De race condition in /Users/chrislehnen/Projecten/Definitie-app/src/api/feature_status_api.py:110-128 is REAL maar MINDER ERNSTIG dan gerapporteerd. Het check-then-set pattern is inderdaad niet atomair: twee concurrent requests kunnen beide "cache staal" detecteren (regel 110-113), beide dezelfde JSON-file laden (regel 116-124), en beide naar _feature_cache en _cache_timestamp schrijven (regel 127-128). Dit veroorzaakt REDUNDANTE I/O, maar GEEN data-verlies/crash omdat: (1) beide requests dezelfde correcte data uit dezelfde file laden, (2) _cache_timestamp-divergentie is microscopisch en irrelevant bij CACHE_DURATION=300s, (3) geen inconsistente state ontstaat. De code retourneert altijd correcte data. Dit is een inefficiency (redundante file-read in concurrent edge-case), niet een kritieke bug. Severity: middel (redundante I/O + minor inefficiency), niet hoog (geen gebruikersimpact).

</details>

### 13. ⚪ [LAAG] Potential event loop reuse across asyncio.run() calls (pages/synonym_admin.py, async_progress.py)
**Locatie:** `src/pages/synonym_admin.py:195`

Each asyncio.run() call creates and destroys a new event loop. If this is called repeatedly in a Streamlit page (e.g., user clicks button multiple times), you create/destroy many event loops. While this works, it's inefficient and can cause issues if tasks from previous loops are still being referenced.

```python
asyncio.run(orchestrator.ensure_synonyms(...)) # called multiple times in same Streamlit session
```
**Fix:** Cache the event loop or use a persistent async context: Use run_async() from async_bridge which handles this, or create a singleton async runner that persists across requests.
<details><summary>Verificatie (hoog)</summary>


Bevinding BEVESTIGD maar AANPASST severity:

GEVERIFIEERDE FEITEN uit echte code:
1. `/Users/chrislehnen/Projecten/Definitie-app/src/pages/synonym_admin.py:195` - `asyncio.run()` wordt inderdaad direct aangeroepen
2. `/Users/chrislehnen/Projecten/Definitie-app/src/ui/async_progress.py:155` - Identiek patroon
3. Streamlit sessies kunnen deze code meerdere keren uitvoeren (button clicks via st.rerun())

WAAROM SEVERITY IS LAAG:
- `asyncio.run()` is PER PYTHON-ONTWERP ontworpen om veilig meerdere keren aangeroepen te worden
- Elke call creëert een NIEUWE event loop en vernietigt die daarna - er is geen "reuse" van dezelfde loop
- Dit werkt correct, geen race conditions of crash-risico

ECHTER:
- Het is INEFFICIËNT: elke klik = loop create/destroy = overhead
- Het is TEGEN het project pattern: `/src/ui/helpers/async_bridge.py:19-56` biedt een `run_async()` helper specifiek voor dit probleem
- De `run_async()` helper detecteert al bestaande loops en gebruikt ThreadPoolExecutor om veilig te isoleren
- Deze helper wordt NIET gebruikt in `synonym_admin.py` en `async_progress.py`

Dit is geen crash/data-verlies/security-bug (kritiek/hoog), maar een ANTI-PATTERN implementatie (laag) - inefficiënt en inconsistent met project conventies.


</details>

### 14. ⚪ [LAAG] AsyncIO timeout doesn't properly propagate cancellation
**Locatie:** `src/voorbeelden/unified_voorbeelden.py:173-220`

When asyncio.wait_for times out in the worker thread, it cancels the coroutine. However, if the coroutine is in a non-cancellable operation (C extension, blocking call), the cancellation is ignored. The backstop timeout then triggers future.result(timeout=backstop) which will raise TimeoutError. But executor.shutdown(wait=False) in finally doesn't wait for the thread - the thread continues running in the background consuming resources. If called repeatedly, this leaks threads. Additionally, the 5-second grace period (_ASYNC_SAFE_BACKSTOP_GRACE_S) may not be enough for complex operations.

```python
executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        future = executor.submit(run_in_thread)
        try:
            backstop = (
                None if timeout is None else timeout + _ASYNC_SAFE_BACKSTOP_GRACE_S
            )
            return future.result(timeout=backstop)
        finally:
            executor.shutdown(wait=False)
```
**Fix:** Use a context manager or pool with explicit cleanup. Consider increasing backstop grace period. Add logging to detect when threads are left running. Consider using a atexit handler to clean up stranded threads.
<details><summary>Verificatie (middel)</summary>

De bevinding is TECHNISCH JUIST: when `future.result(timeout=backstop)` raises TimeoutError in `/Users/chrislehnen/Projecten/Definitie-app/src/voorbeelden/unified_voorbeelden.py:215`, the `executor.shutdown(wait=False)` on line 220 does NOT kill the thread — it only stops accepting new tasks. If the worker thread is still in `loop.run_until_complete(wrapped)` (line 203) and the inner `asyncio.wait_for()` didn't successfully cancel a non-cancellable coroutine, the thread will continue running in the background consuming OS resources.

HOWEVER, this is LOW severity because: (1) The timeouts are conservative (120s + 5s grace) and far exceed actual API call timeouts (20-45s per lines 493-550), meaning the timeout path is rarely triggered; (2) The underlying operations (LLM API calls via `generate_definition`) are properly cancellable async operations, so in normal cases `asyncio.wait_for()` successfully cancels and the thread exits cleanly via finally-block (line 205); (3) This code path is not in a high-frequency loop — examples are generated per-concept, not per-request. The thread leak would only occur during genuine timeouts/hangs of external services, which are rare.

The core risk is real but mitigated by conservative timeouts and cancellable async operations. Best practice would be to: (a) reuse a shared ThreadPoolExecutor pool rather than creating one per call, (b) add daemon=True flag to threads, or (c) implement explicit cleanup. Current code is defensive but not optimal.

</details>

## Niet-afgehandelde errors & stille failures (17)

### 15. 🔴 [KRITIEK] Duplicate detection silently fails and returns empty list
**Locatie:** `src/services/definition_repository.py:379-381`

find_duplicates() catches all exceptions and returns []. When duplicate detection fails (database error, query error, conversion error), the import/save workflow gets an empty 'no duplicates' result. System then creates actual duplicates that violate data integrity. User data gets corrupted.

```python
except Exception as e:
    logger.error(f"Fout bij duplicaat detectie: {e}")
    return []
```
**Fix:** Raise DuplicateDetectionError or similar custom exception. Let caller decide whether to allow import or fail gracefully.
<details><summary>Verificatie (hoog)</summary>

Geverifieerd in echte code: /Users/chrislehnen/Projecten/Definitie-app/src/services/definition_repository.py:379-381 vangt alle exceptions af met catch-all en geeft stiekem [] terug. Workflow-impact is echte data-integriteits-risico:

1. find_duplicates() (regel 348-381) roept legacy_repo.find_duplicates() aan die database queries uitvoert (definitie_duplicates.py:54-102) en records converteert via _record_to_definition() (regel 373).

2. Beide kunnen exceptions werpen: sqlite3.OperationalError (db offline), KeyError/IndexError (row conversion), json.JSONDecodeError (malformed context JSON), etc.

3. except Exception as e (regel 379) vangt ALLES, logt naar logger.error(), geeft [] terug.

4. Aanroepers kunnen niet onderscheiden: 
   - "Geen duplicaten gevonden" (normaal)
   - "Database error, kon niet controleren" (ONVEILIG - duplicaatcheck omzeild)

5. In definitie_crud.py:56-61, als duplicates=[] (van stille exception):
   ```python
   if duplicates and any(...):  # [] evaluates False → guard overgeslagen!
       raise ValueError("already exists")
   ```

6. Result: Duplicaten worden opgeslagen die data integrity schenden. Test test_find_duplicates_error_handling bewijst dit: mock_legacy_repo.find_duplicates.side_effect = Exception("...") → assert results == [] (stille failure).

Dit is geen stijl maar functionele data-bug: stille failures in kritieke duplicate-detection logic met direct gevolg dat gebruiker data kan corrumperen.

</details>

### 16. 🔴 [KRITIEK] Transaction Commit Outside Try-Finally in voorbeelden_repository.save_voorbeelden
**Locatie:** `src/database/voorbeelden_repository.py:213`

After conn.commit() on line 213, the code calls _update_voorkeursterm() (line 215) and _sync_synoniemen() (line 216). If these methods raise exceptions, the transaction is already committed and cannot be rolled back. Additionally, _update_voorkeursterm() itself calls conn.commit() on line 244, which is problematic because: (1) it commits a partial transaction while the outer try-catch expects to handle all commits, and (2) if _sync_synoniemen() fails after _update_voorkeursterm() commits, vorbeelden are saved but synoniem sync fails silently (only logged as warning, not exposed to caller). This causes data inconsistency where vorbeelden exist but synonyms are not synced.

```python
conn.commit()

                self._update_voorkeursterm(conn, definitie_id, voorkeursterm)
                self._sync_synoniemen(
                    voorbeelden_dict, definitie_id, gegenereerd_door, get_definitie_fn
                )
```
**Fix:** Move conn.commit() to after _sync_synoniemen() completes successfully. Remove the conn.commit() from _update_voorkeursterm() and instead handle it at the outer level. Use nested try-except to ensure _sync_synoniemen failures are caught and either rollback or expose the error to the caller.
<details><summary>Verificatie (hoog)</summary>

Werkelijke code geverifieerd in /Users/chrislehnen/Projecten/Definitie-app/src/database/voorbeelden_repository.py. Bevinding klopt volledig:

1. Regel 213: Eerste `conn.commit()` committeert voorbeelden permanent
2. Regel 244 (in _update_voorkeursterm): Tweede `conn.commit()` committeert voorkeursterm-update
3. Regel 215-218: Post-processing (_update_voorkeursterm en _sync_synoniemen) volgen na eerste commit
4. Regel 245-255: Exceptions in _update_voorkeursterm gehandeld als warning-only (geen re-raise)
5. Regel 274-275: Exceptions in _sync_synoniemen gehandeld als warning-only (geen re-raise)

Dit leidt tot echte data-inconsistentie: voorbeelden en voorkeursterm zijn permanent gecommit, maar als synoniemen sync faalt (regel 275), zijn synoniemen niet gesynchroniseerd terwijl de rest van de definitie al opgeslagen is. De twee expliciete commits (regel 213 en 244) maken de transactie non-atomair.

Dit is kritiek omdat:
- Leidt tot inconsistente database-state in productiepad
- Post-processing fouten worden stil gefaald zonder caller feedback
- Twee aparte commits ipv atomaire transactie
- Definitie-data kan onvolledig zijn (voorbeelden zonder synoniemen)

</details>

### 17. 🔴 [KRITIEK] Bare Exception Catch in CSV Importer Processing Loop Hides Import Failures
**Locatie:** `src/ui/components/tabs/import_export_beheer/csv_importer.py:137`

When processing CSV rows in a loop (lines 101-139), any exception is caught broadly and appended to an errors list. The loop continues processing remaining rows. However: (1) The exception message is converted to string (e!s) which loses the traceback and exception context. (2) Database errors (constraint violations, connection failures) are treated the same as validation errors, making it impossible to distinguish transient failures from data issues. (3) If a critical error occurs (e.g., database disk full), the user will see a success message like '✅ Import voltooid: 5 geïmporteerd, 3 overgeslagen' even if only the first few rows succeeded before the database failed.

```python
except Exception as e:
                errors.append(f"Rij {idx + 1}: {e!s}")
```
**Fix:** Distinguish between different exception types: validation errors (continue loop), database errors (stop loop and rollback), other errors (log and ask user). For critical errors, show st.error() immediately rather than continuing the import.
<details><summary>Verificatie (hoog)</summary>

De bevinding is GEGROND en de severity is eigenlijk ERGER dan "hoog".

VERIFICATIE VAN ECHTE CODE (/Users/chrislehnen/Projecten/Definitie-app/src/ui/components/tabs/import_export_beheer/csv_importer.py):

1. Regel 101-139: Loop itereert over alle DataFrame rijen
2. Regel 137-138: `except Exception as e:` vangt ALLE exceptions (ValueError, RuntimeError, sqlite3.OperationalError, sqlite3.IntegrityError, etc.)
3. Regel 138: Exception wordt alleen string-converted (`e!s`), traceback gaat verloren
4. De loop gaat DOOR naar volgende rij na elke fout (geen re-raise)
5. Regel 144-146: `st.success()` wordt ALTIJD gerenderd, onafhankelijk van inhoud `errors` array

CONCRETE BEVEILIGDE BUGS:

a) **Stille data-verlies**: Als sqlite3.OperationalError optreedt bij rij 30 (bijv. "database is locked" door concurrent access), worden rijen 30-100 opgeven en genegeerd. Gebruiker ziet: "✅ Import voltooid: 29 geïmporteerd, 0 overgeslagen" en denkt dat alles goed ging.

b) **Geen error-context**: Exception message is als string opgeslagen zonder traceback. Gebruiker ziet "Rij 30: database is locked" maar geen stack trace, dus kan niet debuggen of onderscheiden of het transient of persistent is.

c) **Onverschillig exception handling**: ValueError (duplicate record), RuntimeError (database failure), sqlite3.OperationalError (disk full), sqlite3.IntegrityError (constraint violation) worden allemaal gelijk afgehandeld. Geen retry-logica voor transient errors.

d) **Geen onderbrekingslogica**: Een kritieke database-fout (bijv. disk full) zou de import moeten STOPPEN, niet DOORGAAN met volgende rijen. Code zet gewoon door.

SEVERITY: **KRITIEK** (niet hoog) omdat:
- Dit is stille data-verlies in de import-loop
- Gebruiker krijgt false-positive success message
- Kan onopgemerkt in productie gaan
- 70%+ van data kan missend zijn zonder waarschuwing

LOCATIE BEWIJZEN:
- /Users/chrislehnen/Projecten/Definitie-app/src/ui/components/tabs/import_export_beheer/csv_importer.py:137-138 (bare exception catch)
- /Users/chrislehnen/Projecten/Definitie-app/src/ui/components/tabs/import_export_beheer/csv_importer.py:144-146 (unconditional success message)

</details>

### 18. 🟠 [HOOG] Delete API returns success when delete fails silently
**Locatie:** `src/services/definition_repository.py:290`

The delete() method catches ALL exceptions and returns False, but the caller receives False which is indistinguishable from 'record not found'. When update_definitie() silently fails (e.g., database locked, permission error), the UI thinks the delete succeeded but the definition remains in the database. Data integrity compromised.

```python
except Exception as e:
    logger.error(f"Fout bij verwijderen definitie {definition_id}: {e}")
    return False
```
**Fix:** Either: (1) Re-raise specific exceptions after logging; (2) Return a result object with error details; (3) Verify the delete actually occurred with a follow-up SELECT before returning True.
<details><summary>Verificatie (hoog)</summary>

BEVESTIGD: De bevinding is een echte bug. In /Users/chrislehnen/Projecten/Definitie-app/src/services/definition_repository.py, regels 282-288, roept de delete() methode update_definitie() aan maar controleert NIET de retourwaarde:

```python
record = self.legacy_repo.get_definitie(definition_id)
if record:
    self.legacy_repo.update_definitie(
        definition_id, {"status": DefinitieStatus.ARCHIVED.value}
    )
    return True  # <-- RETOURNEERT TRUE ZONDER UPDATE RESULT TE CHECKEN
return False
```

De methode zou moeten zijn:
```python
if record:
    success = self.legacy_repo.update_definitie(...)
    return success
```

Dit is geen false-positive omdat: (1) de code letterlijk het retourwaarde van update_definitie() negeert, (2) update_definitie() kan False retourneren in gevallen als database-locking, optimistic lock failure, of constraint violations (zie /Users/chrislehnen/Projecten/Definitie-app/src/database/definitie_crud.py:267-271), (3) de interface contract verwacht True=succes/False=falen.

SEVERITY aangepasst naar HOOG (niet KRITIEK): De bug veroorzaakt geen data-verlies of crash - het is een silent failure waarbij de UI succes rapporteert terwijl update stillzwijgend faalt. De definitie blijft in de database, wat een integrityprobleem is, maar geen directe production-outage. Dit is een echte bug die moet worden opgelost, maar niet aan het kritiekste niveau.

</details>

### 19. 🟠 [HOOG] Search returns empty list on any exception, masking data loss
**Locatie:** `src/services/definition_repository.py:234-236`

search() method returns empty list on ANY exception. If database is down, network fails, or query is malformed, caller gets empty result list and thinks search found nothing. UI displays 'no results' instead of 'search error'. User loses data visibility without knowing why.

```python
except Exception as e:
    logger.error(f"Fout bij zoeken naar '{query}': {e}")
    return []
```
**Fix:** Distinguish between 'no results found' (return []) and 'search failed' (raise SearchError with context).
<details><summary>Verificatie (hoog)</summary>

The finding is REAL and VERIFIED. In /Users/chrislehnen/Projecten/Definitie-app/src/services/definition_repository.py lines 205-236, the search() method catches ANY exception (line 234: "except Exception as e:") and returns an empty list (line 236: "return []").

This is semantically ambiguous because:
1. An empty list is ALSO the legitimate return value when a query finds no results
2. The caller cannot distinguish "database error" from "no results found"
3. Evidence: DUP_01.py line 77 checks "if not existing:" which treats both cases identically

This differs from other methods in the same class:
- get() (line 186): returns None on error vs Definition object on success — distinguishable
- update() (line 238): returns False on error vs True on success — distinguishable  
- delete() (line 267): returns False on error vs True on success — distinguishable
- search() (line 205): returns [] on error vs [] on no-results — NOT distinguishable

The docstring (line 214) promises "Lijst van gevonden definities" with no mention of raising exceptions, but the interface contract (/Users/chrislehnen/Projecten/Definitie-app/src/services/interfaces.py) shows search() should return "list[Definition]" with no explicit error signaling documented.

Real impact: When database is down, network fails, or query malforms, calling code (DUP_01.py:75-77, validation rules, UI searches) treats it as "legitimate zero results" rather than "search failed". User sees "no results found" instead of "search encountered an error". This masks data visibility loss and prevents proper error recovery.

Severity adjusted to HIGH (not KRITIEK) because: while this IS a real bug with user-facing impact, it doesn't cause data loss (data is safe in DB), doesn't crash the app, and doesn't prevent core workflows — it just silently degrades search visibility during outages.

</details>

### 20. 🟠 [HOOG] Auto-save silently fails to persist draft changes
**Locatie:** `src/services/definition_edit_repository.py:217-219`

auto_save_draft() returns False on ANY error (database, permissions, constraints). Caller (Streamlit session) sees False and may not realize draft was lost. User continues editing, thinks changes are saved (auto-save ran), but on page reload the draft is gone. Work loss.

```python
except Exception as e:
    logger.error(f"Error auto-saving draft: {e}")
    return False
```
**Fix:** UI must NOT assume auto-save successful on False. Explicitly show user 'auto-save failed' warning. Or: raise exception to trigger UI-level error toast.
<details><summary>Verificatie (hoog)</summary>

Auto-save silently fails in multiple scenarios (database errors, constraint violations, JSON encoding failures). Evidence found in:

1. /Users/chrislehnen/Projecten/Definitie-app/src/services/definition_edit_repository.py:217-219 — bare except Exception, returns False on ANY error (database, permissions, json.JSONEncodeError)

2. /Users/chrislehnen/Projecten/Definitie-app/src/ui/components/definition_edit_tab.py:1816-1817 — return value of auto_save() is ONLY used to update timestamp, no error feedback:
```python
if self.edit_service.auto_save(definition_id, content):
    SessionStateManager.set_value("last_auto_save", datetime.now())
```
False case has no handler, no warning shown.

3. /Users/chrislehnen/Projecten/Definitie-app/src/ui/components/definition_edit_tab.py:1022-1032 — status indicator is MISLEADING:
- Shows "✅ Auto-save: 2m geleden" based on LAST SUCCESSFUL timestamp
- When auto-save fails, timestamp is NOT updated
- User continues editing, thinking auto-save works (sees old "2m geleden" timestamp), but draft is actually lost

Confirmed real risks:
- Database locked/permissions denied (can happen in production)
- definitie_drafts table not created if migrations didn't run
- JSON encoding edge cases
- User loses 30+ seconds of edits per failure with ZERO feedback

Severity remains HOOG (high) because:
- Multiple failure modes with no mitigation
- Silent data loss (users unaware draft was lost)
- Misleading success indicator masks failure
- Affects critical user workflow (editing)
- Not defensive against production database issues

</details>

### 21. 🟠 [HOOG] Version history fetch silently returns empty list on error
**Locatie:** `src/services/definition_edit_repository.py:91-95`

get_version_history() catches all exceptions and returns []. If database query fails, caller gets 'no history' instead of 'history unavailable'. Audit/compliance workflows lose visibility that history retrieval failed.

```python
except Exception as e:
    logger.error(f"Error fetching version history for definitie {definitie_id}: {e}")
    return []
```
**Fix:** Distinguish error case. Return None or raise VersionHistoryError.
<details><summary>Verificatie (hoog)</summary>

Bevinding BEVESTIGD. Werkelijke code in /Users/chrislehnen/Projecten/Definitie-app/src/services/definition_edit_repository.py:91-95 toont: `except Exception as e: logger.error(...) return []`. Ook in definition_edit_service.py:252-254 hetzelfde patroon. 

Dit is echt problematisch in twee scenarios:

1. **UI-impact (definition_edit_tab.py)**: Code toont "Geen versiegeschiedenis beschikbaar" voor beide geval (a) echte lege geschiedenis en (b) database-fout. Gebruiker weet niet wat er aan de hand is.

2. **Revert functionaliteit (definition_edit_service.py:272-281)**: In revert_to_version(), als get_version_history() faalt (returnval []), ziet de loop geen versies. Op regel 280 retourneert het {"success": False, "error": "Versie niet gevonden"} - EXACT DEZELFDE error als wanneer version_id echt niet bestaat. Dit is misleidend en verbergt database-fouten.

3. **Mogelijke scenarios**: sqlite3.OperationalError (database verplaatst/corrupt, permission denied, tabel niet gevonden), sqlite3.DatabaseError - al deze worden gevangt.

Severity is verhoogd van middel naar HOOG omdat dit in productie-pad ligt (users werken met versiegeschiedenis) en audit trail wordt obscured. Dit is geen stijl-nit - het is een werkelijke fout-afhandeling defect.

</details>

### 22. 🟠 [HOOG] ketenpartners update fails silently without failing the whole workflow
**Locatie:** `src/services/definition_workflow_service.py:292`

In approve(), if ketenpartners UPDATE fails, only a warning is logged. Status is already changed to ESTABLISHED. Definition saved but ketenpartners missing—consistency broken. Workflow reports success but metadata incomplete.

```python
except Exception as e:  # pragma: no cover
    logger.warning(f"Kon ketenpartners niet opslaan voor {definition_id}: {e}")
```
**Fix:** Either fail the entire approve() if ketenpartners update fails; or return partial-success result {status_changed: true, ketenpartners_failed: true}.
<details><summary>Verificatie (hoog)</summary>


BEVESTIGD: Dit is een echte bug, niet false-positive.

**Bewijs uit echte code:**
- Locatie: /Users/chrislehnen/Projecten/Definitie-app/src/services/definition_workflow_service.py, regel 280-295
- Het `approve()` method wijzigt eerst status naar ESTABLISHED (regel 265)
- Daarna probeerd het ketenpartners te updaten (regel 283-291)
- Als update_definitie() een Exception gooit, wordt ENKEL een warning gelogd (regel 293-295)
- Execution gaat onveranderd door naar regel 297+
- De methode retourneert WorkflowResult(success=True) (regel 323-331)

**Concrete aanvalsvector:**
In /Users/chrislehnen/Projecten/Definitie-app/src/ui/components/expert_review_tab.py:625-694 wordt workflow.approve() aangeroepen met ketenpartners=geselecteerd (lege list of gevuld). Een lege list [] is NOT None, dus de update wordt geprobeerd. Als update_definitie() exceptie gooit (bijv. database lock, connection pool exhaustion), dan:
1. Status IS al ESTABLISHED geworden
2. Ketenpartners update faalt stil (warning enkel gelogd)
3. UI receives success=True en toont "✅ Definitie vastgesteld"
4. Definitie is nu in inconsistent state: ESTABLISHED maar ketenpartners update incomplete

**Waarom Severity=HOOG (niet middel):**
- Inconsistent state in productie (status changed, metadata incomplete)
- UI rapporteert FALSE-SUCCESS (success=True terwijl ketenpartners niet opgeslagen)
- Violates contract: approve() wordt aangeroepen MET ketenpartners, verwacht dat deze worden opgeslagen
- Cascading risk: Latere workflows kunnen aannemen ketenpartners correct is opgeslagen
- Audit trail is aanwezig (warning) maar is onvoldoende—user denkt alles geslaagd is

Niet kritiek omdat: ketenpartners niet direct definitie-creatie/deletie veroorzaakt; maar wel HIGH impact op data integriteit.


</details>

### 23. 🟠 [HOOG] Double Commit Pattern Creates Transaction Atomicity Violation
**Locatie:** `src/database/voorbeelden_repository.py:244`

The _update_voorkeursterm() method calls conn.commit() independently on line 244, then silently swallows exceptions (line 245-255 catches but doesn't re-raise). This means: (1) If voorbeelden are saved (line 213 commit succeeds), but voorkeursterm update fails, vorbeelden are permanently saved without the voorkeursterm, and the error is only logged at WARNING level, not shown to user. (2) The exception is completely swallowed - the caller has no way to know the operation partially failed. (3) When _sync_synoniemen() is called after a failed voorkeursterm update, it may work or fail independently, creating inconsistent state.

```python
except Exception as e:
            logger.warning(
                f"Voorkeursterm update gefaald voor definitie {definitie_id}: {e}. "
                f"Eerdere per-row waarde blijft behouden.",
            )
            # No re-raise, exception is swallowed
```
**Fix:** Remove the conn.commit() from _update_voorkeursterm(). Instead, pass the exception to the outer layer so the entire save_voorbeelden() operation can be properly rolled back if any step fails. Let the outer try-catch handle the transaction atomicity.
<details><summary>Verificatie (hoog)</summary>

VERIFIED AS REAL BUG. 

Code inspection at /Users/chrislehnen/Projecten/Definitie-app/src/database/voorbeelden_repository.py confirms:

1. Line 244: `conn.commit()` in _update_voorkeursterm() - confirmed
2. Lines 245-255: Exception handler catches but does NOT re-raise - confirmed  
3. Line 215: _update_voorkeursterm() is called AFTER voorbeelden commit (line 213)
4. Line 216-218: _sync_synoniemen() is called AFTER voorkeursterm update

THE REAL ISSUE: In autocommit mode (isolation_level=None per db_connection.py:37), exceptions in _update_voorkeursterm() are caught and swallowed (logged at WARNING only, line 246-255). This means:
- Voorbeelden are persisted via auto-commit on lines 124-211
- If voorkeursterm UPDATE fails (line 236/241), the exception is caught
- Caller receives NO error signal (no re-raise on line 245-255)
- Result: Voorbeelden saved without voorkeursterm, silent failure

SEVERITY ADJUSTED FROM "KRITIEK" TO "HOOG":
- Real bug: YES - silent exception swallowing prevents caller from detecting failure
- NOT critical because: No crash/hang/data loss - just data inconsistency
- Impact: HIGH - voorkeursterm might not be set when expected, logs only at WARNING level, caller cannot detect/retry
- The bug violates contract - caller expects either full success or raised exception

</details>

### 24. 🟠 [HOOG] Silent Exception Swallowing in _update_voorkeursterm Blocks User Feedback
**Locatie:** `src/database/voorbeelden_repository.py:245-255`

The exception is caught and logged at WARNING level only. There is no re-raise and no return status to indicate failure. This means the caller (save_voorbeelden) has no way to know that voorkeursterm update failed. The Streamlit UI will show 'Successfully saved X voorbeelden' even if the voorkeursterm update failed, giving the user false confidence that the save was completely successful. This is a 'silent failure' - the operation appears to succeed but critical data (voorkeursterm) may not be persisted.

```python
except Exception as e:
            logger.warning(
                f"Voorkeursterm update gefaald voor definitie {definitie_id}: {e}. "
                f"Eerdere per-row waarde blijft behouden.",
                extra={
                    "component": "definitie_repository",
                    "operation": "update_voorkeursterm",
                    "definitie_id": definitie_id,
                    "error_type": type(e).__name__,
                },
            )
```
**Fix:** Either: (1) Remove the try-except and let the exception propagate, OR (2) Log at ERROR level and return a failure status from _update_voorkeursterm() so the caller can handle it. Ensure the UI is informed of partial failures.
<details><summary>Verificatie (hoog)</summary>

BEVESTIGD - Dit is een echte silent-failure bug.

BEWIJS UIT CODE:
1. /Users/chrislehnen/Projecten/Definitie-app/src/database/voorbeelden_repository.py:215
   - Regel 215: `self._update_voorkeursterm(conn, definitie_id, voorkeursterm)` wordt BUITEN de outer try-except aangeroepen

2. /Users/chrislehnen/Projecten/Definitie-app/src/database/voorbeelden_repository.py:245-255
   - Regel 245: `except Exception as e:` vangt ALLE exceptions
   - Regel 246-255: Logt alleen op WARNING level, geen re-raise
   - Return type is `None` (geen foutstatuswaarde)

3. /Users/chrislehnen/Projecten/Definitie-app/src/database/voorbeelden_repository.py:220-221
   - Regel 220: `logger.info(f"Successfully saved {len(saved_ids)} voorbeelden")`
   - Regel 221: `return saved_ids`
   - Dit gebeurt ALTIJD, zelfs als voorkeursterm update faalde

4. /Users/chrislehnen/Projecten/Definitie-app/src/ui/components/examples_block.py:595, 615
   - Regel 595: `repository.save_voorbeelden(**validated.model_dump())`
   - Regel 615: `st.success("✅ Voorbeelden opgeslagen")`
   - De UI toont succes zelfs als voorkeursterm faalde

KRITIEK: Wanneer `_update_voorkeursterm()` een exception krijgt (bv. database constraint, connection error, NOT NULL constraint op definities-tabel), is het voor de caller onmogelijk te weten dat de update faalde. De voorbeelden worden correct opgeslagen (commit op regel 213), maar de voorkeursterm wordt NIET opgeslagen. De gebruiker ziet "✅ Voorbeelden opgeslagen" en vertrouwt erop dat ALLES is opgeslagen, maar de voorkeursterm ontbreekt.

Dit is data inconsistency in productie: voorbeelden ja, voorkeursterm nee, user kent het verschil niet.

</details>

### 25. 🟠 [HOOG] Information Disclosure via Exception Details in HTTP 500
**Locatie:** `src/api/feature_status_api.py:132`

Exception messages are directly exposed to API clients via the detail field. This can leak sensitive information such as file paths, database details, or internal system architecture. Instead of str(e), a generic error message should be returned.

```python
raise HTTPException(status_code=500, detail=str(e)) from e
```
**Fix:** Replace with: raise HTTPException(status_code=500, detail='Internal server error') from e; log the actual exception with logger.error() for internal diagnostics.
<details><summary>Verificatie (hoog)</summary>

De bevinding is geverifieerd in /Users/chrislehnen/Projecten/Definitie-app/src/api/feature_status_api.py op regel 132. De code `raise HTTPException(status_code=500, detail=str(e)) from e` geeft exception-details rechtstreeks aan API-clients terug. Bij een FileNotFoundError (bv. als feature-status.json ontbreekt) wordt het volledige bestandspad blootgesteld: `/Users/chrislehnen/Projecten/Definitie-app/docs/architectuur/feature-status.json`. Dit onthult interne mapstructuur en kan in development/staging-omgevingen architectuurdetails leaken. Hoewel niet direct credentials/secrets, is dit wel information disclosure. De severity 'hoog' is correct omdat dit duidelijk een beveiligingsissue is met directe gebruikersimpact, maar geen kritieke crash/dataloss veroorzaakt.

</details>

### 26. 🟡 [MIDDEL] Export validation silently suppresses non-critical validation failures
**Locatie:** `src/services/export_service.py:270`

In export loops, if validation fails for ONE definition, it's skipped silently with 'overgeslagen' log. Caller doesn't know export is incomplete. If validation is critical (compliance check), this is data integrity risk.

```python
except Exception as e:  # pragma: no cover - defensive
    # Log but skip deze definitie
```
**Fix:** Return export result with {exported: N, skipped_with_errors: [(def_id, reason), ...]}. Force UI to show skipped items.
<details><summary>Verificatie (hoog)</summary>

De bevinding is REËEL, maar op de verkeerde locatie aangeduid. De daadwerkelijke problematische code bevindt zich in `/Users/chrislehnen/Projecten/Definitie-app/src/services/export_service.py:524-530` in de `_prepare_export_data` methode, niet op regel 270. 

PROBLEEM: In bulk exports (CSV, Excel, JSON, TXT) worden definities SILENTLY overgeslagen wanneer `aggregate_definitie_for_export()` of `_build_export_row()` een exception werpt. De `except Exception as e:` block logt een warning en skipped die definitie via `continue`.

IMPACT:
1. Gebruiker klikt "Export 100 definities" in de UI
2. Als 5 definities een error triggeren, exporteert het systeem slechts 95
3. UI meldt echter: "✅ Export gegenereerd: 100 definitie(s)" (zie format_exporter.py:341-343)
4. Download-knop toont: "📥 Download ... (100 definitie(s))" (regel 325)
5. Het bestand bevat werkelijk slechts 95 rijen

WAAROM MIDDEL EN NIET HOOG:
- Geen data loss: alle 100 definities zitten nog in de database
- Geen crash/hang
- Warning WEL gelogged (exc_info=True op regel 528), maar gebruiker ziet deze niet in Streamlit UI
- Echter: data integratie risico voor compliance/audit exports

WAAROM NIET FALSE-POSITIVE:
- Ik heb de echte code gelezen (regels 515-530, 633-656, 791-793)
- Ik heb het UI-contact punt gelezen (format_exporter.py:325, 341-343)
- De keten is: Exception in data aggregation → silently skipped → log warning → export count tells different story → UI says 100 exported but file has 95

</details>

### 27. 🟡 [MIDDEL] Workflow gate evaluation has unchecked fallback to defaults on any error
**Locatie:** `src/services/definition_workflow_service.py:661`

_get_policy() falls back to hardcoded _Defaults if ANY exception in policy loading. If policy service returns permission error or config error, system silently uses defaults (which may be too permissive/restrictive). Approval gates can be bypassed unintentionally.

```python
except Exception:  # pragma: no cover
    pass
# Falls through to _Defaults
```
**Fix:** Distinguish between 'policy service unavailable' (use safe defaults) and 'policy service error' (raise, don't approve).
<details><summary>Verificatie (hoog)</summary>

Echte bevinding, maar niet zo ernstig als gesuggereerd.

GEVERIFIEERDE CODE:
- /Users/chrislehnen/Projecten/Definitie-app/src/services/definition_workflow_service.py:661 heeft inderdaad `except Exception: pass`
- /Users/chrislehnen/Projecten/Definitie-app/src/services/definition_workflow_service.py:660 aanroep van `GatePolicyService().get_policy()` kan RuntimeError gooien (via _safe_import_yaml() in approval_gate_policy.py:133 als PyYAML ontbreekt)
- Fallback naar hardcoded _Defaults (regel 665-686)

PROBLEMEN GEVERIFIEERD:
1. **Bare except zonder context**: Regel 661 vangt ALLE uitzonderingen af en print niets, dus productie-issues (ontbrekende PyYAML, config-lees-errors) zijn niet zichtbaar
2. **Sleutel-inconsistentie in _Defaults**: Regel 667-668 definiëren `"require_org_context"` en `"require_jur_context"`, maar deze sleutels worden NOOIT gebruikt. Regel 577 in _evaluate_gate zoekt naar `"min_one_context_required"` - een sleutel die NIET in _Defaults bestaat. Dit werkt alleen omdat `.get(..., True)` een default levert.
3. **Generieke log-boodschap misleidend**: Regel 685 logt "GatePolicyService niet beschikbaar" - dit suggereert optional/graceful degradation, maar het kan ook een echte ImportError (PyYAML) of file-read-fout zijn.

GEEN BYPASS:
- Gates functioneren nog steeds op basis van default drempels (0.75/0.65)
- Validatielogica wordt niet overgeslagen

SEVERITY: MIDDEL (niet HOOG)
- Dit is een logging/diagnostics issue meer dan een functieonaal bypass-issue
- In productie zou je niet zien of PyYAML ontbreekt (silent failure)
- De sleutel-inconsistentie is dead code die kan leiden tot verwarring bij onderhoud
- Echter geen direct risico op data-verlies of ongecontroleerde gate-bypass (defaults zijn redelijk)

Bewijs in echte code:
- approval_gate_policy.py:133: `yaml = _safe_import_yaml()` kan RuntimeError gooien
- approval_gate_policy.py:25-27: RuntimeError wordt gegooid als PyYAML ontbreekt
- definition_workflow_service.py:661-662: bare `except Exception: pass` in try-block
- definition_workflow_service.py:577: zoekt naar `"min_one_context_required"` maar _Defaults heeft dit niet

</details>

### 28. ⚪ [LAAG] Search in advanced filter silently returns empty on error
**Locatie:** `src/services/definition_edit_repository.py:382-384`

search_with_filters() catches all exceptions and returns []. Caller can't distinguish 'no results match filter' from 'search crashed'. If filter syntax is invalid or database unavailable, UI shows empty results silently.

```python
except Exception as e:
    logger.error(f"Error in advanced search: {e}")
    return []
```
**Fix:** Validate filters before query. Return error result or raise SearchError.
<details><summary>Verificatie (hoog)</summary>

De bevinding is WAAR: src/services/definition_edit_repository.py:382-384 vangt inderdaad alle Exception af en retourneert [], waardoor de caller niet kan onderscheiden tussen "geen resultaten" en "database fout". Dit wordt bevestigd door:

1. Regel 382-384 in definition_edit_repository.py toont exact de genoemde code
2. definition_edit_tab.py:1078-1087 behandelt lege [] als "geen resultaten gevonden"
3. definition_edit_service.py:395 gebruikt dezelfde methode ook

ECHTER: Severity is LAAG niet MIDDEL omdat:
- De error WORDT gelogd (logger.error op line 383), dus niet völlig stiekem
- Dit is een UI-operatie (geavanceerd zoeken), niet een kritieke data-operatie
- Gebruiker krijgt "geen resultaten" tekst, geen crash/hang/data-verlies
- Bovenliggende exception-handler (definition_edit_tab.py:1100-1110) voorziet alsnog in error-popup voor echte runtime-crashes
- SQL-injection niet mogelijk (parameterized queries)

</details>

### 29. ⚪ [LAAG] Update operation returns False without checking if update actually occurred
**Locatie:** `src/services/definition_repository.py:249-265`

update() calls legacy_repo.update_definitie() and casts result to bool. But if legacy method returns 0 (no rows affected), bool(0) is False. Caller can't tell if definition didn't exist vs. update had no changes vs. database error. Loss of error context.

```python
success = self.legacy_repo.update_definitie(definition_id, updates, updated_by)
return bool(ok)
```
**Fix:** Check rowcount explicitly. Return {success: bool, rows_affected: int, error: ...}
<details><summary>Verificatie (hoog)</summary>

De bevinding is technisch waar: in `/Users/chrislehnen/Projecten/Definitie-app/src/services/definition_repository.py` regel 260-261, roept update() inderdaad legacy_repo.update_definitie() aan en cast het resultaat naar bool zonder context. Dit maskeert drie mogelijke foutcondities: definitie niet gevonden, geen geldige velden, of versie-mismatch. ECHTER: severity moet van 'middel' naar 'laag' worden aangepast omdat: (1) de update() methode wordt nergens in de production codebase daadwerkelijk aangeroepen (geen grep-hits buiten tests/mocks); (2) DefinitionRepository is grotendeels deprecated ten gunste van DefinitionEditRepository; (3) er is geen user-facing API die direct update() aanroept. Er is wel een ernstiger probleem in save() (regel 86) waar het return-value van een update_definitie() call volledig wordt genegeerd, maar dat is niet wat is geclaimd. De geclaimde bevinding is syntactisch en logisch correct, maar heeft minimale praktische impact gegeven de huidige code-architectuur.

</details>

### 30. ⚪ [LAAG] Web lookup silently swallows all exceptions in mediawiki fallback loops
**Locatie:** `src/services/modern_web_lookup_service.py:615, 665, 700`

In _lookup_mediawiki() and _lookup_wiktionary(), the fallback loops catch Exception and continue. If ALL fallbacks fail (network down, API error, timeout), the last exception is swallowed and function returns None. Caller doesn't know why lookup failed—was it 'no results' or 'all sources failed'?

```python
except Exception:
    continue
```
**Fix:** Collect exception reasons. Return result with 'failed_attempts: [(fallback_term, error_reason), ...]' so caller can log/debug.
<details><summary>Verificatie (hoog)</summary>

Verified: Lines 615, 665, 700 in /Users/chrislehnen/Projecten/Definitie-app/src/services/modern_web_lookup_service.py contain bare `except Exception: continue` blocks in the Wikipedia and Wiktionary fallback loops. These do not log exceptions, so if a fallback query fails (network timeout, API error, auth issue), the exception is silently swallowed.

However, adjusting severity from MIDDEL to LAAG because:
1. The outer exception handler in _lookup_source() (line 489-495) catches unexpected exceptions from _lookup_mediawiki() and logs them, providing some observability
2. When all fallbacks fail, the function correctly returns None to the caller - this is semantically correct behavior
3. The _debug_attempts list does capture success/failure attempts, so there is some traceability in debug data
4. No data loss, crash, or security vulnerability occurs - just reduced observability for failed retries
5. For end-users, returning None for "no results found" vs "all sources failed" is functionally equivalent

REAL ISSUE: Missing granular error logging in the fallback loops makes debugging harder and prevents distinguishing between "no results" and "all retries failed with errors". This should be FIXED by adding logger.debug() calls in the except blocks, but the severity is observability/debuggability (low) not functional correctness (medium).

</details>

### 31. ⚪ [LAAG] Exception swallowing in context manager fallback - stale data silently accepted
**Locatie:** `src/ui/session_state.py:220-241`

When the new ContextManager adapter fails, the code silently falls back to reading context directly from st.session_state using legacy keys ("organisatorische_context"). These legacy keys may not have been initialized or may contain stale data from a previous definition generation. The fallback does not validate that the returned context is correct, meaning a user may see a definition generated with wrong context values. The exception is logged but the user only sees a warning, not an error that blocks generation.

```python
try:
    adapter = get_context_adapter()
    context = adapter.get_merged_context()
    return {
        "organisatorisch": context.get("organisatorische_context", []),
        ...
    }
except (AttributeError, KeyError, TypeError, ValueError, ImportError) as e:
    logger.error(f"ContextManager failed, falling back to legacy session state: ...")
    st.warning("Context manager fout - fallback naar legacy context. ")
    # Return legacy session state values
    return {
        "organisatorisch": st.session_state.get("organisatorische_context", []),
        ...
    }
```
**Fix:** If ContextManager fails, do not continue with generation. Instead, raise an exception or return None and require the user to re-initialize context via the UI. Validate that fallback context is not empty before returning it.
<details><summary>Verificatie (middel)</summary>

De bevinding wijst op `get_context_dict()` in src/ui/session_state.py:220-241 dat een fallback naar legacy session_state keys doet zonder validatie. Code-verificatie bevestigt dit pad bestaat exact als beschreven. ECHTER, adversariële analyse toont aan:

1. **Path Reachability:** `get_context_dict()` wordt ALLEEN aangeroepen vanuit `get_export_data()` (regel 274), niet in normale definitie-generatie flow. Normale generatie gebruikt `SessionStateManager.get_value("global_context", {})` direct uit tabbed_interface.py.

2. **Fallback Inhoud:** Regels 238-240 lezen legacy keys die NIET in DEFAULT_VALUES initialisatie voorkomen (src/ui/session_state.py:27-68). Dit geeft inderdaad risico op stale data als deze keys ooit gezet werden en niet proper opgeruimd.

3. **User Feedback:** Regel 232-235 toont wel `st.warning()`, dus niet volledig "silent" - gebruiker wordt gewaarschuwd context kan incorrect zijn.

4. **Impact Beperkt:** `get_export_data()` wordt alleen in tests/integration aangeroepen, niet in actieve productie-flow. Export functionaliteit lijkt deprecated.

5. **Exception Handling:** Narrow exception types (AttributeError, KeyError, TypeError, ValueError, ImportError) betekenen andere fouten niet afgevangen en bubbler door.

**Aanpassing severity van middel naar laag:** Het is een slecht design-patroon (stille fallback zonder proper validatie), maar het reachable risico in normale gebruik is laag omdat pad niet in productie-generatie-flow gebruikt wordt. WEL risico als ContextManager adapter breekt en fallback actief wordt gebruikt.

</details>

## LLM-output parsing & generator-edge-cases (10)

### 32. 🔴 [KRITIEK] Cache Timing Bug: .seconds Attribute Ignores Days Component
**Locatie:** `src/api/feature_status_api.py:111`

The .seconds attribute of a timedelta object only returns the seconds component (0-59), not total seconds elapsed. A timedelta of 1 day + 1 second has .seconds=1, not 86401. This causes cache to incorrectly expire after ~59 seconds instead of 300 seconds (5 minutes), or never expire if the time difference is exactly N days + 1 second.

```python
cache_age = (datetime.now(UTC) - _cache_timestamp).seconds
if cache_age < CACHE_DURATION:
```
**Fix:** Use total_seconds(): cache_age = (datetime.now(UTC) - _cache_timestamp).total_seconds()
<details><summary>Verificatie (hoog)</summary>

Geverifieerd in /Users/chrislehnen/Projecten/Definitie-app/src/api/feature_status_api.py:111. De code gebruikt (datetime.now(UTC) - _cache_timestamp).seconds om cache-leeftijd te bepalen met CACHE_DURATION=300 (5 minuten). De .seconds-attribuut van timedelta retourneert alleen de secondencomponent (0-86399), niet totale seconden. Bij een interval groter dan 1 dag wordt .seconds reset naar de secondencomponent van die dag. Voorbeeld: timedelta(days=1, seconds=1).seconds = 1, niet 86401. Dit breekt cache-logica fundamenteel — data kan dagen oud zijn terwijl cache als vers wordt behandeld. Correct zou timedelta.total_seconds() zijn. Dit is geen edge case maar een systematische fout in productiepad (GET /api/feature-status).

</details>

### 33. 🟠 [HOOG] Duration timing bug: duration always 0 due to same time.time() calls
**Locatie:** `src/utils/integrated_resilience.py:318`

Line 318 subtracts time.time() from itself, always yielding 0.0. This duration is passed to retry_manager.record_success(), breaking adaptive retry metrics and adaptive delay calculations that depend on actual request duration. The comment suggests awareness of the bug but the fix was never applied. Should subtract from start_time (captured at line 184).

```python
duration = time.time() - time.time()  # This would be tracked properly
```
**Fix:** Change line 318 to: duration = time.time() - start_time (where start_time is captured outside the retry loop at line 184)
<details><summary>Verificatie (hoog)</summary>

Real bug verified in /Users/chrislehnen/Projecten/Definitie-app/src/utils/integrated_resilience.py:318. The code executes `duration = time.time() - time.time()` which always yields ~0.0 microseconds instead of measuring actual request duration. This duration is passed to `retry_manager.record_success(duration, endpoint_name)` at line 319, which stores it in RequestMetrics (enhanced_retry.py:252-254) and uses it for adaptive delay calculations (enhanced_retry.py:225-230). The correct pattern exists in the same file at lines 235 and 254 where `duration = time.time() - start_time` is used correctly. The bug breaks the adaptive retry system's ability to learn request patterns and adjust delays based on actual performance, directly impacting production request handling reliability. Severity is HIGH because: (1) it's in the production code path, (2) it affects core retry metrics used by AdaptiveRetryManager, (3) the comment "This would be tracked properly" suggests awareness of the need but the fix was never applied, and (4) the outer method also has timing but the inner method's broken timing corrupts the retry manager's historical data.

</details>

### 34. 🟠 [HOOG] RAG chunk_text unsanitized prompt injection risk
**Locatie:** `src/services/orchestrators/definition_orchestrator_v2.py:678`

RAG chunk_text is directly extracted from database chunks without sanitization (no call to sanitizer.sanitize_content). Malicious or prompt-injected text in RAG chunks will be injected directly into the prompt when these provenance sources are merged. This bypasses the request-level sanitization in PHASE 1.

```python
provenance_sources.append({
    "provider": "rag",
    "snippet": chunk.get("chunk_text", ""),
    "used_in_prompt": True,
    ...
})
```
**Fix:** Apply content sanitization to chunk_text before adding to provenance_sources: chunk.get('chunk_text', '') → sanitizer.sanitize_content(chunk.get('chunk_text', ''), level='strict')
<details><summary>Verificatie (hoog)</summary>

RAG chunk_text is extracted unsanitized at /Users/chrislehnen/Projecten/Definitie-app/src/services/prompts/prompt_service_v2.py:235-236 without calling sanitize_snippet(). In contrast, web snippets (line 443: sanitize_snippet(raw, max_length=2000)) and document snippets (line 324: sanitize_snippet(raw)) receive sanitization. While XML escaping at line 77 in xml_source_formatter.py mitigates tag-based injection, it does NOT prevent LLM-targeted prompt injection attacks that use newlines, markdown, or non-tag-based techniques. The vulnerability requires either (a) malicious RAG document upload or (b) database compromise, making it admin-level rather than user-exploitable, but the code inconsistency is a genuine security flaw that bypasses the established sanitization pattern used elsewhere in the codebase. Verified by comparing lines 234-245 (RAG, no sanitize_snippet call) vs lines 439-443 (web, calls sanitize_snippet) vs lines 318-324 (document, calls sanitize_snippet).

</details>

### 35. 🟠 [HOOG] Missing key validation on parsed JSON from LLM
**Locatie:** `src/services/classification/ontological_classifier.py:196-205`

After json.loads() succeeds, the code directly accesses dictionary keys ("level", "confidence", "rationale", "scores") without checking if they exist. LLM outputs can have extra keys, missing keys, or different structure. Missing a key causes KeyError which crashes the function. Additionally, level_map lookup can fail with KeyError if response_data["level"] contains unexpected value like "u", "universal", or other variations.

```python
level = level_map[response_data["level"]]
            confidence = float(response_data["confidence"])
            confidence_level = self._determine_confidence_level(confidence)
            ...
            rationale=response_data["rationale"],
            scores=response_data["scores"],
```
**Fix:** Use dict.get() with fallbacks: response_data.get("level", "F"), response_data.get("confidence", 0.5). Validate level is in level_map before lookup. Use float() with exception handling for confidence.
<details><summary>Verificatie (hoog)</summary>

Bevestigd in /Users/chrislehnen/Projecten/Definitie-app/src/services/classification/ontological_classifier.py regels 186-205. Na json.loads() op regel 187 worden dictionary keys direct benaderd zonder validatie (regels 196-197, 204-205). De code: (1) Leest "level" (regel 196) en zoekt het op in level_map met alleen keys {"U", "F", "O"} — als LLM "universal" of ander formaat retourneert: KeyError; (2) Leest "confidence" en cast naar float (regel 197) — geen fallback als casting faalt; (3) Leest "rationale" en "scores" (regels 204-205) zonder .get() of try-except rond deze accesses. De LLM kan inconsistent reageren ondanks deterministische prompt (temperature=0.3). De generieke except op regel 220 vangt deze fouten wel, maar het blijft een directe productie-crash-scenario. Dit is geen false-positive: de code mist defensive programming rond LLM-output-parsing.

</details>

### 36. 🟠 [HOOG] LLM JSON response truncated by max_tokens without detection
**Locatie:** `src/services/classification/ontological_classifier.py:181-187`

The generate_definition call uses a default max_tokens which may be insufficient for complete JSON output. If the LLM response is truncated mid-JSON (e.g., cuts off at {"level": "F", "confidence": 0.8, "rationale": "..."), json.loads() will fail with JSONDecodeError. There is no check for response.finish_reason or indication of truncation. The prompt expects valid JSON but truncation creates invalid JSON.

```python
ai_result = await self.ai_service.generate_definition(
                prompt, temperature=0.3
            )
            response = ai_result.text

            # Parse response
            response_data = json.loads(response)
```
**Fix:** Explicitly set higher max_tokens for JSON responses (e.g., 1000). Check if response indicates truncation. Attempt to repair incomplete JSON by finding and closing the last unclosed bracket.
<details><summary>Verificatie (hoog)</summary>

De bevinding is geverifieerd aan de echte code. In `/Users/chrislehnen/Projecten/Definitie-app/src/services/classification/ontological_classifier.py:181-187` roept `generate_definition(prompt, temperature=0.3)` de AI aan zonder expliciet `max_tokens` in te stellen, dus standaard 500 tokens. De prompt verwacht JSON met velden inclusief `rationale` die potentieel lang kan zijn.

Critisch: In `/Users/chrislehnen/Projecten/Definitie-app/src/services/ai/openai_client.py:92-104` wordt ALLEEN `response.choices[0].message.content` geëxtraheerd zonder controle op `response.choices[0].finish_reason`. Wanneer OpenAI het antwoord afkapt bij max_tokens (finish_reason='length'), resulteert dit in ongeldig JSON.

Dit veroorzaakt JSONDecodeError bij lijn 187 in ontological_classifier.py. Het gaat verloren in een breed exception handler die het als RuntimeError re-raises, zonder detectie dat truncatie heeft plaatsgevonden.

Dit is een echte bug met gebruikersimpact: classificatie van juridische begrippen faalt silent met onduidelijke foutmelding wanneer de rationale lang genoeg is. Severity: hoog omdat het in productiepad voorkomt (UI roept globaal_context_renderer.py aan) en kan leiden tot mislukte definities.

</details>

### 37. 🟠 [HOOG] No validation of LLM response content structure before parsing
**Locatie:** `src/voorbeelden/unified_voorbeelden.py:354-358`

The response.text is passed directly to _parse_response() without any validation. If the LLM returns unexpected output (e.g., refusing to generate, meta-text like "I cannot generate", or structured response with extra fields), the regex patterns in _parse_response fail silently and return empty lists. For synoniemen/antoniemen this triggers retry logic, but for other types it produces empty results without clear error signaling to the user.

```python
response = await self.ai_service.generate_definition(
                prompt=prompt,
                task_type=self._get_task_type(request.example_type),
                temperature=cast(float, request.temperature),
                max_tokens=2000,
            )
            return self._parse_response(response.text, request.example_type)
```
**Fix:** Add validation layer: check response length, verify it contains expected keywords, detect refusals. Log warning when response doesn't match expected pattern. Return error indicator instead of empty list when parsing confidence is low.
<details><summary>Verificatie (hoog)</summary>

De bevinding is CORRECT. Verificatie in het echte code:

1. **Locatie: /Users/chrislehnen/Projecten/Definitie-app/src/voorbeelden/unified_voorbeelden.py:358** (en ook 332, 589)
   Response.text wordt direct doorgegeven: `return self._parse_response(response.text, request.example_type)`

2. **Geen validatie van LLM content**: AIServiceV2.generate_definition (regel 153-275) returnt gewoon response.text zonder te controleren of het geldig is.

3. **Silent parsing failures**: _parse_response() (regel 707-884) retourneert [] (empty list) wanneer regex-patronen niet matchen:
   - Regel 778: `return examples if examples else []` voor synoniemen/antoniemen
   - Regel 856: `return examples if examples else [text]` met fallback
   - Regel 884: `return []` als alles faalt

4. **KRITIEK VERSCHIL - Asymmetrische error handling:**
   - **Synoniemen/antoniemen** (regel 345-346): gebruiken _generate_with_retry() die empty results detecteert (regel 397) en RETRY'en of WARNING loggen
   - **Andere types** (VOORBEELDZINNEN, PRAKTIJKVOORBEELDEN, TEGENVOORBEELDEN, TOELICHTING):
     * _generate_async regel 348-358: GEEN retry, direct return van _parse_response result
     * _generate_resilient_common regel 589: GEEN retry, direct return van _parse_response result
     * _generate_sync regel 332: GEEN retry, direct return van _parse_response result

5. **Impact**: Wanneer LLM weigert ("I cannot generate...") of unexpected output geeft:
   - Regex-patroonen matchen niet
   - _parse_response retourneert []
   - Dit is STILLE failure - geen exception, geen user notification
   - Voor synoniemen/antoniemen: retry triggered, gebruiker krijgt waarschuwing
   - Voor andere types: leeg resultaat zonder signaling naar gebruiker

**Severity**: HOOG (niet KRITIEK) omdat:
- Geen crash/hang
- Geen data-verlies
- Wel duidelijke gebruikersimpact: lege voorbeelden zonder foutmelding
- UI ziet success=True, examples=[]
- Gebruiker weet niet waarom geen voorbeelden gegenereerd werden

</details>

### 38. 🟠 [HOOG] Anthropic client returns empty string when response has no text blocks
**Locatie:** `src/services/ai/anthropic_client.py:102-105`

If response.content contains no text blocks (e.g., only tool_use or other non-text blocks), text_parts is empty, and text becomes empty string. This is silently treated as valid response. The caller has no way to detect that the LLM response was not text-based. Downstream code treating empty string as valid text can cause issues.

```python
text_parts = [
            block.text for block in response.content if hasattr(block, "text")
        ]
        text = "\n".join(text_parts).strip()
```
**Fix:** Check if text_parts is empty after filtering. Log warning if no text blocks found. Return error indicator or raise exception instead of empty string.
<details><summary>Verificatie (hoog)</summary>

Bevestigd in daadwerkelijke code. AnthropicClient.chat_completion() (regel 102-105 van anthropic_client.py) filters enkel op `hasattr(block, "text")` en retourneert een lege string als response.content geen text blokken bevat. Dit is niet onwaarschijnlijk: de Anthropic API kan responses met enkel tool_use/tool_result blokken genereren.

Kritieke impact: ontological_classifier.py (regel 184-187) doet direct `json.loads(response)` op dit veld zonder validatie. Een lege string veroorzaakt json.JSONDecodeError, waardoor classificatie faalt. Dit is bewezen in de code - geen theoretische edge case.

Er is wel een test (test_anthropic_handles_empty_content_blocks) die dit scenario accepteert, maar downstream consumers valideren niet dat response.text niet leeg is voordat parsing. Dit is een contract violation: ChatResponse.text is contractueel `str`, maar callers verwachten valide inhoud, niet een lege string die json.loads() breekt.

Severity: HOOG (niet KRITIEK) omdat het geavanceerde scenario is (API moet tool_use genereren) maar het breekt wel een core pad (ontological classificatie) volledig.

</details>

### 39. 🟡 [MIDDEL] KeyError on missing enum value in LLM classification
**Locatie:** `src/services/classification/ontological_classifier.py:196`

If the LLM returns response_data["level"] with value other than "U", "F", or "O" (e.g., "u", "UNIVERSEEL", "unknown", or typo), the level_map lookup raises KeyError. This crashes the classification. The LLM is instructed to use specific values but LLMs are unreliable about following format instructions, especially in non-English contexts.

```python
level = level_map[response_data["level"]]
```
**Fix:** Use level_map.get(response_data["level"], OntologicalLevel.FUNCTIONEEL) with sensible default. Normalize the response value (uppercase, strip) before lookup. Add fallback category.
<details><summary>Verificatie (hoog)</summary>

De bevinding is CORRECT: line 196 in /Users/chrislehnen/Projecten/Definitie-app/src/services/classification/ontological_classifier.py zal inderdaad KeyError gooien als `response_data["level"]` een waarde bevat die niet in de level_map staat (bijv. lowercase "u", "UNIVERSEEL", typo, etc.).

ECHTER, de SEVERITY moet naar beneden omdat:

1. **Exception IS al afgehandeld**: Lines 220-223 hebben een brede `except Exception` die de KeyError vangt, logt, en als RuntimeError herwerpt. Dit voorkomt een ongehandelde crash.

2. **Code is blijkbaar ongebruikt in productie**: De OntologicalClassifier wordt alleen geïnstantieerd in de ServiceContainer als singleton, maar wordt NIET daadwerkelijk aangeroepen vanuit UI routes. De main flow (global_context_renderer.py:206) gebruikt ImprovedOntologyClassifier. Enige verwijzing buiten de class zelf is in docstrings.

3. **Improper error handling wel aanwezig**: Hoewel de exception wordt afgehandeld, is dit niet ideaal. Beter zou zijn om `.get()` te gebruiken met validatie:
   ```python
   level_str = response_data.get("level", "")
   if level_str not in level_map:
       raise ValueError(f"Invalid level from LLM: '{level_str}'...")
   level = level_map[level_str]
   ```

4. **Error wordt wel gerapporteerd**: De gebruiker krijgt de foutmelding via `RuntimeError`, dus het is geen stille mislukking.

SEVERITY AANPASSING: "hoog" → "middel" omdat het een echte bug is (LLM kan invalid formaat retourneren), maar het is al afgehandeld en blijkt ongebruikt in production.

</details>

### 40. 🟡 [MIDDEL] Float conversion failure on malformed confidence value
**Locatie:** `src/services/classification/ontological_classifier.py:197`

If response_data["confidence"] is a string like "0.8%", "high", or "not applicable", float() conversion raises ValueError. LLMs may return text descriptions instead of numeric values, especially when prompted in different languages.

```python
confidence = float(response_data["confidence"])
```
**Fix:** Wrap float() in try/except. Extract numeric part from string if needed. Use fallback value (e.g., 0.5) on conversion failure. Validate confidence is in range 0.0-1.0.
<details><summary>Verificatie (hoog)</summary>

The finding is VALID. At line 197 of /Users/chrislehnen/Projecten/Definitie-app/src/services/classification/ontological_classifier.py, the code `confidence = float(response_data["confidence"])` is indeed vulnerable to ValueError if the LLM returns a non-numeric string like "0.8%", "high", or "not applicable". 

However, the severity assessment should be qualified:
1. The ValueError IS caught by the broad `except Exception` at line 220, so it doesn't cause an unhandled crash
2. BUT this is poor defensive coding - there's no explicit ValueError/TypeError handling and no fallback value
3. IMPACT: Classification fails completely and raises RuntimeError instead of degrading gracefully or using a default confidence value
4. The classification is called synchronously in UI context (line 206 of global_context_renderer.py), so failures block the user

The issue is real but the broad exception catch prevents complete failure. Severity remains "middel" - it's a concrete bug (malformed responses cause failures), not an unhandled crash, but it does impact user experience when the LLM deviates from expected format. The prompt is in Dutch with clear numeric format specification, but LLMs can still deviate, especially with different model backends or prompt injection scenarios.

</details>

### 41. ⚪ [LAAG] Unused time.time() call that reads time but discards result
**Locatie:** `src/utils/smart_rate_limiter.py:587`

A bare time.time() call on line 587 reads the current time but the result is not assigned or used. This is either dead code or a copy-paste artifact. It serves no purpose and may confuse readers. Should be removed or, if timing was intended, assigned to a variable for later use.

```python
Line 587: time.time()
Followed immediately by line 588: if not await limiter.acquire(...)
```
**Fix:** Remove the line 587: time.time(). If timing the acquire() call was intended, assign it before acquire: start = time.time() and record duration after acquire.
<details><summary>Verificatie (hoog)</summary>

Geverifieerd in /Users/chrislehnen/Projecten/Definitie-app/src/utils/smart_rate_limiter.py op regel 587. De code bevat inderdaad een bare `time.time()` call die het resultaat niet gebruikt of toewijst. Dit is dood code, vermoedelijk een copy-paste artefact van regel 594 waar `function_start = time.time()` correct wordt gebruikt. Er is geen assignment of gebruik van de waarde; de regel doet niets en kan zonder gevolgen worden verwijderd. Dit is geen safety-issue, performance-issue, of logische bug — puur verwarrende dode code. Severity blijft laag omdat het geen functionele impact heeft.

</details>

## Input-validatie (API / CSV-import) (4)

### 42. 🟠 [HOOG] CSV Import: No Handling of Missing or Empty Required Columns
**Locatie:** `src/ui/components/tabs/import_export_beheer/csv_importer.py:101-123`

The code checks for missing columns (line 56) but then uses .get() with default empty strings. A row can have 'begrip' column but the cell is NaN or whitespace. Empty definitions get saved without validation, polluting the database with invalid records.

```python
for idx, row in df.iterrows():
    ...
    record = DefinitieRecord(
        begrip=row.get('begrip', ''),
        definitie=row.get('definitie', '')
    )
```
**Fix:** After df.read_csv(), call df.fillna('').astype(str).str.strip() to normalize, then validate each required cell is non-empty before creating DefinitieRecord. Log or skip rows with empty required fields.
<details><summary>Verificatie (hoog)</summary>

De bevinding is ECHT EN ERNSTIG. Ik heb drie kritieke input-validatie-bugs geverifieerd in /Users/chrislehnen/Projecten/Definitie-app/src/ui/components/tabs/import_export_beheer/csv_importer.py, lines 119-126:

1. **Whitespace-only values** (lines 120-121): `row.get('begrip', '')` en `row.get('definitie', '')` accepteren en slaan whitespace-waarden op zonder stripping. Ik heb dit getest en bevestigd dat '   ' en '\n' zonder validatie in de database worden opgeslagen. Dit creëert invalid, nutteloze records.

2. **NaN-handling issue** (lines 120-121): Pandas retourneert `np.nan` (float) voor lege cellen in CSV's, niet de default string. Dit bypast de column-aanwezigheid check (line 56) en resulteert in `NOT NULL constraint failed` errors. De code gaat ervan uit dat `.get()` altijd een string retourneert, wat niet waar is voor pandas Series.

3. **Invalid default categorie** (line 122): `categorie=row.get('categorie', 'Type')` - "Type" is NIET geldig. De database CHECK constraint vereist lowercase waarden: 'type', 'proces', 'resultaat', 'exemplaar', of UFO-codes. Dit veroorzaakt deterministische `CHECK constraint failed` errors bij imports zonder expliciete categorie.

De originele bevinding was partly correct (over lege values) maar incomplete. De severity is HOOG (niet middel), omdat:
- Het systeem crashes/rejecteeert valide CSV-imports
- Database wordt verontreinigd met whitespace-records
- Gebruikers krijgen cryptische database-errors in plaats van input-validatie feedback

Dit is geen stijl-kwestie; het zijn concrete runtime-failures in de normale import-workflow.

</details>

### 43. 🟡 [MIDDEL] CSV Import: No Validation of Empty File or Large File
**Locatie:** `src/ui/components/tabs/import_export_beheer/csv_importer.py:45-48`

No validation of file size, row count, or memory usage before calling pd.read_csv(). A malicious or accidental 1GB CSV can cause memory exhaustion (OOM). The preview shows all columns for every uploaded file without bounds checking.

```python
df = pd.read_csv(uploaded_file)
# Toon preview
st.dataframe(df.head(), use_container_width=True)
```
**Fix:** Before read_csv(): check file size (MAX_FILE_SIZE = 10MB), check row count after read, validate required columns exist, and handle pd.read_csv() with memory_map=False and dtype inference disabled for untrusted input.
<details><summary>Verificatie (hoog)</summary>

Verified via Reading /Users/chrislehnen/Projecten/Definitie-app/src/ui/components/tabs/import_export_beheer/csv_importer.py:45-48. The code calls pd.read_csv(uploaded_file) at line 48 without any explicit pre-validation of file size, row count, or memory usage. However, the severity of the "1GB file" scenario in the original finding is TECHNICALLY MITIGATED by Streamlit's default server.maxUploadSize of 200MB (verified in Streamlit 1.58.0 config), making such a file impossible to upload via st.file_uploader(). The REAL vulnerability is with files up to 200MB: a large CSV can still cause memory exhaustion during pd.read_csv() when loading into RAM. Additionally, empty files (0 bytes) result in an empty DataFrame (0 rows) which executes silently with no user warning (line 101: loop over 0 rows = no import, no error). This is a valid but less severe issue than originally stated—adjusted from 'hoog' to 'middel' because: (1) Streamlit limits uploads to 200MB by default, (2) the preview only shows df.head(), not all data, (3) exception handler catches CSV read errors. The vulnerability exists for large-but-valid files within Streamlit's limit, and for the edge case of empty files.

</details>

### 44. 🟡 [MIDDEL] Payload Input: Unbounded String Conversion Without Length Validation
**Locatie:** `src/services/definition_import_service.py:250-251`

No maximum length validation. If payload['begrip'] is a very long string (e.g., 1MB of repeated text) or a deeply nested object with __str__ override, conversion to string can cause DoS or unexpected behavior. No truncation or length check before database insert.

```python
begrip = str(payload.get('begrip', '')).strip()
definitie = str(payload.get('definitie', '')).strip()
```
**Fix:** Define MAX_BEGRIP_LENGTH and MAX_DEFINITIE_LENGTH; validate after strip: if len(begrip) > MAX or len(definitie) > MAX, raise ValueError with clear message.
<details><summary>Verificatie (hoog)</summary>

Geverifieerd in echte code op /Users/chrislehnen/Projecten/Definitie-app/src/services/definition_import_service.py regels 250-251: begrip en definitie worden via str() geconverteerd en .strip() aangeroepen ZONDER enige lengte-validatie. De Definition dataclass (src/services/interfaces.py:211-245) accepteert unlimited strings, en de repository layer (src/services/definition_repository.py:587) voert deze direct door naar database zonder checks. Terwijl het schema.sql `definitie TEXT` definieert (onbeperkt in SQLite), kan een attacker een multi-megabyte payload sturen die in-memory geladen en opgeslagen wordt. Dit riskeert geheugenuitputting en database bloat per request. Echter: (1) De async/await architecture voorkomt dat een single request hangt (timeout van 2.0s op regel 106), (2) Er is geen database crash risk want SQLite accepteert grote TEXT. Het is dus een resource exhaustion risk (middel) eerder dan kritiek.

</details>

### 45. 🟡 [MIDDEL] CSV Encoding Issues: No Fallback Handling in pandas read_csv
**Locatie:** `src/ui/components/tabs/import_export_beheer/csv_importer.py:48`

pandas defaults to UTF-8 but does not specify on_bad_lines or encoding parameters. A CSV file with mixed encodings (e.g., cp1252 mixed with UTF-8) may silently drop rows or raise UnicodeDecodeError, causing silent data loss.

```python
df = pd.read_csv(uploaded_file)
```
**Fix:** Use: df = pd.read_csv(uploaded_file, encoding='utf-8', on_bad_lines='skip', engine='python') to handle encoding errors gracefully and log skipped rows.
<details><summary>Verificatie (hoog)</summary>

The finding is REAL but with important context: Line 48 of /Users/chrislehnen/Projecten/Definitie-app/src/ui/components/tabs/import_export_beheer/csv_importer.py does call `pd.read_csv(uploaded_file)` without explicit encoding parameters. However, the exception handler at lines 82-83 (`except Exception as e: st.error(...)`) catches UnicodeDecodeError and displays it to users, preventing silent data loss. The risk is NOT silent row-dropping as claimed, but rather: users with non-UTF-8 CSVs get a generic error message instead of automatic encoding fallback. The codebase demonstrates a better pattern in document_extractor.py (lines 92-100) which tries multiple encodings (utf-8, latin-1, cp1252) before falling back to errors='replace'. Severity adjusted from "laag" to "middel" because it's a real UX/reliability issue (users blocked by encoding problems) but not a data-loss risk due to the exception handler.

</details>

## Streamlit session state (lek/stale) (4)

### 46. 🔴 [KRITIEK] Multi-user session state leak via global module-level cache in service_factory.py
**Locatie:** `src/services/service_factory.py:33`

Global module-level dict _SERVICE_ADAPTER_CACHE persists across all Streamlit sessions and users. When multiple users are accessing the app simultaneously (common in multi-user deployments), they all share the same ServiceAdapter instance from this cache. This means User A's definition generation context, selected models, and cached results are accessible to User B. The cache is keyed by config hash, but does not account for user identity or session isolation. Additionally, this cache is populated from os.environ values which are also shared across users when API keys change (see ai_provider_sidebar.py lines 119-123).

```python
_SERVICE_ADAPTER_CACHE: dict[str, "ServiceAdapter"] = {}

# Later in get_definition_service():
cached = safe_dict_get(_SERVICE_ADAPTER_CACHE, key)
if cached is not None:
    return cast("ServiceAdapter", cached)
```
**Fix:** Move _SERVICE_ADAPTER_CACHE to Streamlit session_state instead of module level. Use SessionStateManager to store per-session service adapters: SessionStateManager.get_value('_service_adapter_cache', {}) instead of the global dict.
<details><summary>Verificatie (hoog)</summary>

Bevestigde multi-user session state leak via module-level _SERVICE_ADAPTER_CACHE in service_factory.py. Daadwerkelijke code-bevindingen:

1. GLOBALE CACHE - /Users/chrislehnen/Projecten/Definitie-app/src/services/service_factory.py:33
   `_SERVICE_ADAPTER_CACHE: dict[str, "ServiceAdapter"] = {}`
   Dit is module-level (proces-wijd gedeeld) in Streamlit-applicatie.

2. CACHE RETURN LOGICA - /Users/chrislehnen/Projecten/Definitie-app/src/services/service_factory.py:761-785 (get_definition_service):
   - Lijn 772-776: Key is "singleton", cache hit retourneert oude adapter
   - Lijn 783: Cache wordt opgeslagen
   - GEEN cache-invalidatie wanneer reset_container() wordt aangeroepen

3. CONTAINER RESET - /Users/chrislehnen/Projecten/Definitie-app/src/services/container.py:113
   ServiceContainer leest os.environ["OPENAI_API_KEY"] EENMAAL bij initialisatie

4. RESET CHAIN - /Users/chrislehnen/Projekten/Definitie-app/src/ui/components/ai_provider_sidebar.py:114-152 (_apply_provider_change):
   - Lijn 119-123: os.environ wordt gewijzigd
   - Lijn 129-131: reset_container() wordt aangeroepen
   - Lijn 147: get_tabbed_interface.clear() wist Streamlit cache
   - MAAR: Geen code cleart _SERVICE_ADAPTER_CACHE

5. BEWEZEN SCENARIO:
   - User A: get_definition_service() → ServiceAdapter(container_A_with_key_A) → in cache
   - User A wijzigt sleutel → reset_container() (cleart container-cache, NIET adapter-cache)
   - User A/B: get_definition_service() → retourneert adapter_A (oude sleutel!)

Severity KRITIEK omdat:
- Streamlit draait in één proces (alle sessies gedeeld)
- Api keys en model-keuzes worden tussen users gedeeld
- ServiceContainer bevat generator/validator services die user-specifieke context/models hebben
- /Users/chrislehnen/Projecten/Definitie-app/src/services/service_factory.py:128 toont ServiceAdapter houdt orchestrator + web_lookup - deze zijn aan user A gekoppeld

De claim van de eerdere reviewer is CORRECT en GEMIST.

</details>

### 47. 🟠 [HOOG] Incorrect SessionStateManager.initialize_session_state() call with dict argument
**Locatie:** `src/ui/components/definition_edit_tab.py:476`

SessionStateManager.initialize_session_state() takes NO arguments - it only initializes DEFAULT_VALUES from the class. Passing a dict {k("begrip"): definition.begrip} is silently ignored. This means the widget key k("begrip") is never pre-populated in session_state, causing the st.text_input value parameter to always be empty on first render. The widget will then use session_state[k("begrip")] if it exists from previous runs, creating a state leak where old definition terms persist across definition changes.

```python
SessionStateManager.initialize_session_state({k("begrip"): definition.begrip})
begrip = st.text_input(
    "Begrip",
    key=k("begrip"),
    disabled=disabled,
)
```
**Fix:** Use SessionStateManager.set_value(k("begrip"), definition.begrip) BEFORE rendering the widget, or rely on the widget's key to load from session_state directly. The initialize call has no effect and should be removed.
<details><summary>Verificatie (hoog)</summary>

GEVERIFIEERD REAL BUG: De SessionStateManager.initialize_session_state() methode (regel 71-86 in /Users/chrislehnen/Projecten/Definitie-app/src/ui/session_state.py) accepteert GEEN parameters - het is een parameterloze static method die alleen DEFAULT_VALUES uit de klasse initialiseert. 

ECHTER: De code in /Users/chrislehnen/Projecten/Definitie-app/src/ui/components/definition_edit_tab.py probeert dict-argumenten door te geven op MEERDERE plaatsen:
- Regel 476: SessionStateManager.initialize_session_state({k("begrip"): definition.begrip})
- Regel 488-489: SessionStateManager.initialize_session_state({k("definitie"): definition.definitie})
- Regel 707-708: SessionStateManager.initialize_session_state({k("toelichting"): definition.toelichting or ""})
- Regel 1017: SessionStateManager.initialize_session_state({"auto_save_enabled": True})

Deze arguments worden STILZWIJGEND GENEGEERD omdat Python geen error werpt voor extra arguments aan static methods.

GEVOLG: De widgets st.text_input() en st.text_area() (regels 477-482, 491-497, 710-716) ontvangen GEEN value-parameter en initialiseren zich NIET met de gewenste waarden. In plaats daarvan gebruiken ze whatever al in st.session_state[key] staat (van vorige definitie), wat tot STATE LEAKAGE leidt tussen definitie-edits. 

BEWIJS VAN IMPACT: _save_definition() (regel 1205+) haalt waarden rechtstreeks op met SessionStateManager.get_value(k("begrip")) etc., dus als de widget niet goed geïnitialiseerd is, zouden LEGE of OUDE waarden opgeslagen kunnen worden.

Dit is een DUIDELIJKE BUG met HIGH SEVERITY (gebruiker-zichtbare state leak, mogelijke data verlies).

</details>

### 48. 🟠 [HOOG] API keys leaked across users via os.environ writes in AI provider sidebar
**Locatie:** `src/ui/components/ai_provider_sidebar.py:119-123`

User-provided API keys are written directly to os.environ, which is process-global and shared across all Streamlit sessions and users. When User A enters their OpenAI API key via the text_input widget (line 82-90), it gets stored in os.environ["OPENAI_API_KEY"], overwriting any previous key. User B's subsequent API calls will use User A's key if User A's key is in os.environ at that time. This violates multi-user isolation. Additionally, os.environ writes bypass proper async handling and cause state mutations that affect service initialization globally.

```python
os.environ["AI_PROVIDER"] = provider
if api_key:
    os.environ[provider_config["env_key"]] = api_key
```
**Fix:** Store API keys only in Streamlit session_state and pass them explicitly to services that need them. Do not write to os.environ. Use SessionStateManager to maintain per-session API credentials that are not shared across users.
<details><summary>Verificatie (hoog)</summary>

Dit is een echte beveiligingszwakheid, maar de severity is HOOG in plaats van KRITIEK. 

ECHTE PROBLEMEN GEVERIFIEERD:
1. Regel 119-123 in /Users/chrislehnen/Projecten/Definitie-app/src/ui/components/ai_provider_sidebar.py schrijft inderdaad direct naar os.environ:
   ```python
   os.environ["AI_PROVIDER"] = provider
   if api_key:
       os.environ[provider_config["env_key"]] = api_key
   ```

2. In Streamlit kunnen inderdaad meerdere browser-tabs/sessies dezelfde Python-process delen, met elk hun eigen st.session_state, maar dezelfde process-globale os.environ.

3. De bijbehorende entered_key wordt WEL uit st.session_state gelezen (per-sessie, regel 93), maar de WRITE gaat naar os.environ (process-global).

ECHTER - de severity is HOOG (niet KRITIEK) omdat:
- Streamlit is primair voor single-user development bedoeld
- Typische deployments scheiden users per process/container
- Docker/Streamlit Cloud geeft meestal 1 process per user
- De container WORDT wel gereset (regel 131), wat mitigatie biedt

WEL RISICO:
- Als applicatie op shared server draait of mehrere tabs actively in same process
- API keys KUNNEN leaken via process memory inspection
- Cross-session API key pollution is theoretisch mogelijk

ARCHITECTURAL BUG: Zou via st.session_state gaan ipv os.environ, of per-session in-memory store gebruiken, niet process-global."

</details>

### 49. 🟠 [HOOG] Session state not cleared between definition edits - stale context context persists
**Locatie:** `src/ui/components/definition_edit_tab.py:507-554`

When switching from one definition to another in the edit tab, the edit_organisatorische_context, edit_juridische_context, and edit_wettelijke_basis session state values are not cleared upfront. If User edits Definition A (which sets edit_organisatorische_context), then switches to Definition B without a full rerun, the old context from Definition A may still be in session_state. The code attempts to clear these AFTER using them (line 147-151), but there is a race condition window where other code paths or concurrent renders may access the stale values.

```python
# Auto-load context from generator tab
edit_org_from_generator = SessionStateManager.get_value(
    "edit_organisatorische_context"
)
current_org = (
    edit_org_from_generator
    if (...)
    else (getattr(definition, "organisatorische_context", []) or [])
)

# Clear after use (line 147-151)
SessionStateManager.clear_value("edit_organisatorische_context")
```
**Fix:** Clear edit context fields immediately when switching definitions, BEFORE rendering any widgets. Add: SessionStateManager.clear_value("edit_organisatorische_context") immediately after detecting a new target_id in the auto-load logic (around line 65).
<details><summary>Verificatie (hoog)</summary>

BEVESTIGD ALS REAL BUG. Daadwerkelijke code-lezen: In /Users/chrislehnen/Projecten/Definitie-app/src/ui/components/definition_edit_tab.py lijn 1112-1175, _start_edit_session() zet editing_definition_id en editing_definition bij voor Definition B, maar wist NIET de globale edit_organisatorische_context, edit_juridische_context, en edit_wettelijke_basis session-state waarden. Volgende render-cycle (lijn 68-69), because both current_definition.id en target_id nu gelijk zijn aan B, is should_load=FALSE. De clearing block (lijn 147-151) wordt dus NIET uitgevoerd. In _render_editor() (lijn 507-517), edit_organisatorische_context wordt gelezen en getoond als default waarden (lijn 510-517), wat resulteert in Definition B die de contexts van Definition A krijgt. Dit gebeurt als gebruiker via _render_search_results tabel (lijn 400) naar een andere definitie klikt. OBSERVABLE IMPACT: Wanneer je van Definition A (met contexts van generator-tab) naar Definition B schakelt, ziet Definition B automatisch de contexts van Definition A ingevuld, wat tot onbedoelde data-opslag leidt als user opslaat. Dit is een state-persistence bug met direct user-impact. SEVERITY AANPASSINGEN: Origineel "hoog" is correct - dit is duidelijke bug met direct gebruikersimpact (verkeerde context in UI, potentiële data-storage), geen kritiek (kan niet crash productie), maar wel direct observable en problematic.

</details>

## Resource-leaks (DB / files) (3)

### 50. 🟠 [HOOG] Document extractor does not close PDF resource in exception path
**Locatie:** `src/document_processing/document_extractor.py:113-129`

If any page.get_text() raises an exception during iteration, the PDF document is never closed. Although the close() call is present, it's not in a finally block or context manager, so an exception during iteration will bypass the cleanup. This can leak file handles and memory in long-running processes.

```python
pdf_document = fitz.open(stream=io.BytesIO(content), filetype="pdf")
text_parts = []
for page in pdf_document:
    text_parts.append(page.get_text())
pdf_document.close()
# BUT: if page.get_text() raises exception, close() is never reached
```
**Fix:** Use try/finally or context manager: try: ... finally: pdf_document.close() OR use 'with' statement if available in fitz API
<details><summary>Verificatie (hoog)</summary>

Bevestigd: In /Users/chrislehnen/Projecten/Definitie-app/src/document_processing/document_extractor.py regel 113-129, de PDF-verwerking heeft geen proper exception handling. Als page.get_text() (regel 117) faalt, springt de exception direct naar de except-blok op regel 127, en pdf_document.close() (regel 119) wordt nooit bereikt. Dit veroorzaakt een echte resource leak van bestand-handles en geheugen, vooral problematisch in lange-draaiende FastAPI-servers die veel PDFs verwerken. De fix zou zijn om try-finally te gebruiken of een context manager (with-statement) toe te passen op de fitz.open() call. Dit is een bevestigde bug, niet een false-positive."

</details>

### 51. 🟡 [MIDDEL] Unbounded token estimation causes potential API limit violations
**Locatie:** `src/services/ai_service_v2.py:444`

The max_tokens bound equals char_count with no upper limit. For a very long input (e.g., 1MB text), this returns 1,000,000 as max_tokens estimate. The AI service then passes this to the API, potentially violating model token limits (e.g., Claude has 200k limit, GPT-4o has 128k). This can cause API errors or silent truncation.

```python
min_tokens = int(char_count * 0.5)
max_tokens = char_count
return max(min_tokens, min(estimated_tokens, max_tokens))
```
**Fix:** Clamp max_tokens to model-specific limits: max_tokens = min(char_count, MODEL_MAX_TOKENS) where MODEL_MAX_TOKENS is 128000 for GPT-4o or 200000 for Claude.
<details><summary>Verificatie (hoog)</summary>

De bevinding verwijst naar regel 444 van ai_service_v2.py (`max_tokens = char_count`), maar dit is de **token SCHATTING** voor logging, niet de daadwerkelijke API-parameter. Het echte probleem ligt elders: 

**Geverifieerde problemen:**
1. **Regel 239** in ai_service_v2.py: `max_tokens=max_tokens` wordt ongevalideerd aan de Anthropic/OpenAI SDK doorgegeven
2. **Regel 799-803** in definition_orchestrator_v2.py: `max_tokens` uit `sanitized_request.options` wordt zonder validatie gebruikt - geen minimum/maximum clamping
3. **Geen hardcoded grenzen** in async_api.py tussen orchestrator en SDK
4. Waarden kunnen in theorie willekeurig groot zijn (bijv. 1M tokens voor een 1MB-input)

**Mitigating factors:**
- De Streamlit UI filtert options (regel 285-289) - alleen `force_generate`/`force_duplicate` worden doorgelaten
- Geen public API endpoint blootstelt `generate_definition` direct
- Configuratie-default heeft 4096-limiet, maar dit wordt niet ina fgerkt op runtime values
- Anthropic SDK valideert waarschijnlijk intern (zou 200k-limiet afdwingen), maar dat is afhankelijkheid op third-party

**Impact:** Niet kritiek (geen crash/data-verlies), maar een reëel risico voor:
- Programmatische aanroepers die `options["max_tokens"]` injecteren
- Model-API limietoverschrijding met potentiële fouten
- Stille truncatie zonder duidelijke feedback

**Opmerking:** De bevinding beschrijft fout een "estimation", maar het echte mechanisme (orchestrator+async_api) heeft inderdaad geen validatie. De severity is verhoogd naar "middel" i.p.v. "hoog" omdat:
1. Streamlit UI heeft filteriing
2. Geen public API exposure
3. SDK's hebben waarschijnlijk intern clamping

</details>

### 52. 🟡 [MIDDEL] v5_migration verifies backup connection without context manager
**Locatie:** `src/database/migrations/v5_migration.py:261-263`

In verify_backup(), a connection is created and manually closed. If _get_table_names() raises an exception before the return statement at line 263, the connection is never closed. The try/finally is missing.

```python
conn = sqlite3.connect(str(backup_path))
tables = _get_table_names(conn)
conn.close()
```
**Fix:** Add try/finally block: try: conn = sqlite3.connect(...) tables = _get_table_names(conn) finally: conn.close()
<details><summary>Verificatie (hoog)</summary>

De code op regel 260-266 mist inderdaad een try/finally of context manager. Als _get_table_names(conn) op regel 262 een sqlite3.Error werpt (bijv. bij korrupte database), wordt de exception in het except-block afgevangen en retourneert de functie False. De conn.close() op regel 263 wordt echter nooit bereikt, wat resulteert in een resource leak. De verbinding blijft open naar het backup-database file.

Dit is een echte bug die in het error-pad kan optreden (korrupte backup-database bij verificatie). Severity is middel omdat: (1) Het leidt tot resource leak (open FDs), (2) Het alleen optreedt in nood-scenario's (backup-verificatie faalt), (3) Het niet in het normale migratie-pad gebeurt, en (4) Het niet tot data-verlies of crashen leidt.

Betreffende bestand: /Users/chrislehnen/Projecten/Definitie-app/src/database/migrations/v5_migration.py, regels 260-266.

</details>
