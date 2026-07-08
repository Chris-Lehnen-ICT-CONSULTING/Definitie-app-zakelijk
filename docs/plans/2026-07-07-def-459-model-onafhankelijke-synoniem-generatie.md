# DEF-459 — Model-onafhankelijke synoniem-generatie Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Vervang de lege `GPT4SynonymSuggester`-placeholder door een echte, model-onafhankelijke synoniem-suggester die het geconfigureerde model (via `ModelRouter`/`AIServiceV2`) aanroept met een dedicated juridische synoniem-onderzoeksprompt.

**Architecture:** Nieuwe standalone prompt-builder + defensieve JSON-parser; de suggester wordt hernoemd (`SynonymSuggester`) en krijgt `AIServiceV2` via constructor-injectie (geen verborgen container-import). RAG blijft buiten beschouwing (we gaan niet door `PromptServiceV2`). De context-key-mismatch tussen definitie-orchestrator en `ensure_synonyms` wordt rechtgetrokken. Alles achter de bestaande `ai_pending` governance-gate — geen synoniem gaat automatisch live.

**Tech Stack:** Python 3.13, `AIServiceV2.generate_definition(task_type="synonyms")`, `ModelRouter`, pytest + pytest-asyncio, ruff/black/mypy.

---

## Achtergrond & geverifieerde feiten

Alle onderstaande referenties zijn in deze sessie geverifieerd tegen de code:

| Feit | Bron |
|------|------|
| Placeholder retourneert altijd `[]` | `src/services/gpt4_synonym_suggester.py:100` |
| Model-onafhankelijke call bestaat al | `src/services/ai_service_v2.py:153-188` (`generate_definition(..., task_type=...)`) |
| `"synonyms"` is geregistreerde task-tier | `src/services/ai/model_router.py:54` |
| Integratie-contract (veld-mapping) | `src/services/synonym_orchestrator.py:302-328`: `.synoniem`→`term`, `.confidence`→`weight` (∈[0,1]), `.rationale`→`context_json` |
| Suggester-signatuur die vervangen wordt | `src/services/gpt4_synonym_suggester.py:68-70` |
| DI-wiring (parameterloze constructor) | `src/services/container.py:482-550` |
| `ai_service` is lokaal in `orchestrator()` | `src/services/container.py:308-312` |
| Context-mismatch: producer stuurt `organisatorisch/juridisch/wettelijk` | `src/services/orchestrators/definition_orchestrator_v2.py:395-409` |
| Consumer leest `definitie/tokens` | `src/services/synonym_orchestrator.py:280-281` |
| TODO-gate matcht alleen `#`-TODO's | `scripts/ci/check_no_todo_markers.sh:8-9` |
| Config: `gpt4_timeout_seconds=30`, `min_weight=0.7` | `src/config/synonym_config.py:68-77`, `config/synonym_config.yaml:36-86` |
| Projectregel: geen backwards-compat, refactor in place | `.claude/rules/project-rules.md` #4 |
| Constraint: prompt builders niet wijzigen zonder overleg (overleg is gegeven) | `CLAUDE.md`, `.claude/rules/patterns.md` |

**Contract dat de vervanger MOET respecteren:**
1. `SynonymSuggestion(synoniem: str-nietleeg, confidence: float∈[0,1], rationale: str)` — `__post_init__` valideert (`gpt4_synonym_suggester.py:35-43`).
2. `async def suggest_synonyms(...) -> list[SynonymSuggestion]`.
3. `get_stats() -> dict` behouden (gebruikt door metrics).
4. Timeout ≤ `config.gpt4_timeout_seconds` (orchestrator wrapt al in `asyncio.wait_for`, `synonym_orchestrator.py:277-284`).

---

## Task 0: Branch-verificatie

**Step 1:** Bevestig de feature branch.
Run: `git branch --show-current`
Expected: `feature/DEF-459-model-onafhankelijke-synoniemen`

---

## Task 1: Synoniem-onderzoeksprompt-builder (nieuw bestand)

**Files:**
- Create: `src/services/prompts/synonym_research_prompt.py`
- Test: `tests/unit/services/prompts/test_synonym_research_prompt.py`

Raakt GEEN bestaande KRITIEKE builder — het is een losstaande, pure functie.

**Step 1: Write the failing test**

```python
import pytest

pytestmark = pytest.mark.unit

from services.prompts.synonym_research_prompt import build_synonym_research_prompt


def test_prompt_bevat_term_en_json_instructie():
    system, user = build_synonym_research_prompt(term="verdachte")
    assert "verdachte" in user
    # Model-onafhankelijk: geen modelnaam in de prompt
    assert "gpt-4" not in (system + user).lower()
    assert "gpt4" not in (system + user).lower()
    # Dwingt gestructureerde JSON-output af
    assert "json" in user.lower()
    assert "confidence" in user.lower()
    assert "rationale" in user.lower()


def test_prompt_verwerkt_juridische_context():
    system, user = build_synonym_research_prompt(
        term="verdachte",
        juridische_context=["Wetboek van Strafvordering"],
    )
    assert "Wetboek van Strafvordering" in user


def test_prompt_zonder_context_is_geldig():
    system, user = build_synonym_research_prompt(term="besluit")
    assert isinstance(system, str) and system.strip()
    assert isinstance(user, str) and "besluit" in user
```

**Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/unit/services/prompts/test_synonym_research_prompt.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'services.prompts.synonym_research_prompt'`

**Step 3: Write minimal implementation**

```python
"""Model-onafhankelijke synoniem-onderzoeksprompt (DEF-459).

Losstaande builder — gaat NIET door PromptServiceV2/PromptOrchestrator en
raakt daarmee de RAG-injectie (prompt_service_v2.py) noch de KRITIEKE
definitie-prompt-modules. Output is een (system_prompt, user_prompt)-paar
voor AIServiceV2.generate_definition(prompt=user, system_prompt=system).
"""

from __future__ import annotations

_SYSTEM_PROMPT = (
    "Je bent een expert in Nederlands juridisch taalgebruik en terminologie. "
    "Je taak is het voorstellen van synoniemen voor een juridische term: woorden "
    "of uitdrukkingen die in juridische context dezelfde of vrijwel dezelfde "
    "betekenis dragen. Je bent precies en conservatief: liever weinig sterke "
    "synoniemen dan veel zwakke. Je verzint geen termen die niet echt gangbaar zijn."
)

_JSON_INSTRUCTIE = (
    "Antwoord UITSLUITEND met geldige JSON in exact dit formaat, zonder extra "
    "tekst eromheen:\n"
    '{\n'
    '  "synoniemen": [\n'
    '    {"synoniem": "<term>", "confidence": <0.0-1.0>, '
    '"rationale": "<korte juridische onderbouwing in het Nederlands>"}\n'
    '  ]\n'
    "}\n"
    "Regels:\n"
    "- confidence is een getal tussen 0.0 en 1.0 (mate van semantische "
    "gelijkwaardigheid in juridische context).\n"
    "- Geef geen antoniemen, hyperoniemen of losjes verwante termen.\n"
    "- Laat de lijst leeg ([]) als er geen goede synoniemen zijn."
)


def build_synonym_research_prompt(
    term: str,
    definitie: str | None = None,
    juridische_context: list[str] | None = None,
    min_count: int = 5,
) -> tuple[str, str]:
    """Bouw (system_prompt, user_prompt) voor synoniem-onderzoek.

    Args:
        term: De juridische term waarvoor synoniemen gezocht worden.
        definitie: Optionele definitie van de term (extra betekenis-anker).
        juridische_context: Optionele lijst juridische/wettelijke context-items.
        min_count: Streefaantal synoniemen (indicatief in de prompt).
    """
    regels: list[str] = [
        f"Zoek synoniemen voor de juridische term: '{term}'.",
        f"Streef naar ongeveer {min_count} synoniemen, maar kwaliteit boven kwantiteit.",
    ]
    if definitie:
        regels.append(f"Definitie van de term (betekenis-anker): {definitie}")
    if juridische_context:
        context_str = "; ".join(c for c in juridische_context if c)
        if context_str:
            regels.append(f"Relevante juridische context: {context_str}")

    user_prompt = "\n".join(regels) + "\n\n" + _JSON_INSTRUCTIE
    return _SYSTEM_PROMPT, user_prompt
```

**Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/unit/services/prompts/test_synonym_research_prompt.py -v`
Expected: PASS (3 passed)

**Step 5: Commit**

```bash
git add src/services/prompts/synonym_research_prompt.py tests/unit/services/prompts/test_synonym_research_prompt.py
git commit -m "feat(DEF-459): model-onafhankelijke synoniem-onderzoeksprompt-builder"
```

---

## Task 2: Defensieve response-parser

**Files:**
- Create: `src/services/prompts/synonym_response_parser.py`
- Test: `tests/unit/services/prompts/test_synonym_response_parser.py`

Defensief parsen adresseert meteen het DEF-471-thema (onveilige LLM-output-parsing): geen naïeve `json.loads`, wél key-validatie, clamping en fout-tolerantie.

**Step 1: Write the failing test**

```python
import pytest

pytestmark = pytest.mark.unit

from services.gpt4_synonym_suggester import SynonymSuggestion
from services.prompts.synonym_response_parser import parse_synonym_response


def test_parse_geldige_json():
    raw = (
        '{"synoniemen": ['
        '{"synoniem": "beklaagde", "confidence": 0.9, "rationale": "strafproces"},'
        '{"synoniem": "gedaagde", "confidence": 0.6, "rationale": "civiel"}'
        ']}'
    )
    result = parse_synonym_response(raw)
    assert len(result) == 2
    assert all(isinstance(s, SynonymSuggestion) for s in result)
    assert result[0].synoniem == "beklaagde"


def test_parse_json_in_markdown_fence():
    raw = '```json\n{"synoniemen": [{"synoniem": "x", "confidence": 0.5, "rationale": "y"}]}\n```'
    assert len(parse_synonym_response(raw)) == 1


def test_parse_confidence_buiten_bereik_wordt_geclampt():
    raw = '{"synoniemen": [{"synoniem": "x", "confidence": 1.7, "rationale": "y"}]}'
    result = parse_synonym_response(raw)
    assert result[0].confidence == 1.0


def test_parse_slaat_ongeldige_items_over():
    raw = (
        '{"synoniemen": ['
        '{"synoniem": "", "confidence": 0.9, "rationale": "leeg"},'      # leeg → skip
        '{"confidence": 0.9, "rationale": "geen synoniem-key"},'          # mist key → skip
        '{"synoniem": "geldig", "confidence": 0.8, "rationale": "ok"}'
        ']}'
    )
    result = parse_synonym_response(raw)
    assert len(result) == 1
    assert result[0].synoniem == "geldig"


def test_parse_kapotte_json_geeft_lege_lijst():
    assert parse_synonym_response("dit is geen json {{{") == []


def test_parse_lege_of_none_input():
    assert parse_synonym_response("") == []
    assert parse_synonym_response(None) == []
```

**Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/unit/services/prompts/test_synonym_response_parser.py -v`
Expected: FAIL — `ModuleNotFoundError` / `ImportError: cannot import name 'SynonymSuggestion'` (dat is OK; SynonymSuggestion bestaat al in gpt4_synonym_suggester.py, de parser-module nog niet).

**Step 3: Write minimal implementation**

```python
"""Defensieve parser voor LLM-synoniem-output (DEF-459 / DEF-471-thema).

Verwacht JSON {"synoniemen": [{"synoniem","confidence","rationale"}, ...]},
maar is robuust tegen markdown-fences, extra tekst, ontbrekende keys,
confidence buiten [0,1] en volledig kapotte output. Faalt nooit hard:
onparseerbare of ongeldige items worden overgeslagen (gelogd), niet gethrowd.
"""

from __future__ import annotations

import json
import logging
import re

from services.gpt4_synonym_suggester import SynonymSuggestion

logger = logging.getLogger(__name__)

_JSON_OBJECT_RE = re.compile(r"\{.*\}", re.DOTALL)


def _extract_json_blob(raw: str) -> str | None:
    """Haal het eerste JSON-object uit de tekst (strip markdown-fences/omringende tekst)."""
    match = _JSON_OBJECT_RE.search(raw)
    return match.group(0) if match else None


def parse_synonym_response(raw: str | None) -> list[SynonymSuggestion]:
    """Parse LLM-output naar een lijst gevalideerde SynonymSuggestion-objecten."""
    if not raw or not raw.strip():
        return []

    blob = _extract_json_blob(raw)
    if blob is None:
        logger.warning("Synoniem-parser: geen JSON-object gevonden in output")
        return []

    try:
        data = json.loads(blob)
    except (json.JSONDecodeError, ValueError) as exc:
        logger.warning("Synoniem-parser: JSON-decode mislukt: %s", exc)
        return []

    items = data.get("synoniemen") if isinstance(data, dict) else None
    if not isinstance(items, list):
        logger.warning("Synoniem-parser: 'synoniemen' ontbreekt of is geen lijst")
        return []

    suggestions: list[SynonymSuggestion] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        term = item.get("synoniem")
        if not isinstance(term, str) or not term.strip():
            continue
        raw_conf = item.get("confidence", 0.5)
        try:
            confidence = float(raw_conf)
        except (TypeError, ValueError):
            confidence = 0.5
        confidence = max(0.0, min(1.0, confidence))  # clamp naar [0,1]
        rationale = item.get("rationale")
        rationale = rationale if isinstance(rationale, str) else ""
        try:
            suggestions.append(
                SynonymSuggestion(
                    synoniem=term.strip(),
                    confidence=confidence,
                    rationale=rationale,
                )
            )
        except ValueError as exc:  # defensief: __post_init__-validatie
            logger.warning("Synoniem-parser: item overgeslagen (%s)", exc)
            continue

    return suggestions
```

**Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/unit/services/prompts/test_synonym_response_parser.py -v`
Expected: PASS (6 passed)

**Step 5: Commit**

```bash
git add src/services/prompts/synonym_response_parser.py tests/unit/services/prompts/test_synonym_response_parser.py
git commit -m "feat(DEF-459): defensieve JSON-parser voor synoniem-LLM-output"
```

---

## Task 3: Suggester hernoemen + echte implementatie (constructor-injectie)

**Files:**
- Modify: `src/services/gpt4_synonym_suggester.py` (rename class + implementeer `suggest_synonyms`)
- Test: `tests/unit/services/test_synonym_suggester.py` (nieuw)

Projectregel #4 = refactor in place, geen alias. De class wordt `SynonymSuggester`; het bestand mag zijn naam houden (om de diff klein te houden), of hernoemd worden in Task 3b. Hier: class-rename binnen bestaand bestand.

**Step 1: Write the failing test**

```python
import pytest

pytestmark = pytest.mark.unit

from unittest.mock import AsyncMock, MagicMock

from services.gpt4_synonym_suggester import SynonymSuggester, SynonymSuggestion


def _fake_ai_service(text: str) -> MagicMock:
    svc = MagicMock()
    result = MagicMock()
    result.text = text
    svc.generate_definition = AsyncMock(return_value=result)
    return svc


@pytest.mark.asyncio
async def test_suggest_synonyms_roept_model_onafhankelijk_aan():
    ai = _fake_ai_service(
        '{"synoniemen": [{"synoniem": "beklaagde", "confidence": 0.9, "rationale": "strafproces"}]}'
    )
    suggester = SynonymSuggester(ai_service=ai)

    result = await suggester.suggest_synonyms(term="verdachte")

    assert len(result) == 1
    assert result[0].synoniem == "beklaagde"
    # Model-onafhankelijk: task_type meegegeven, GEEN hardcoded model
    _, kwargs = ai.generate_definition.call_args
    assert kwargs.get("task_type") == "synonyms"
    assert kwargs.get("model") is None


@pytest.mark.asyncio
async def test_suggest_synonyms_lege_output_geeft_lege_lijst():
    ai = _fake_ai_service('{"synoniemen": []}')
    suggester = SynonymSuggester(ai_service=ai)
    assert await suggester.suggest_synonyms(term="verdachte") == []


@pytest.mark.asyncio
async def test_suggest_synonyms_ai_fout_degradeert_naar_leeg():
    ai = MagicMock()
    ai.generate_definition = AsyncMock(side_effect=RuntimeError("boom"))
    suggester = SynonymSuggester(ai_service=ai)
    assert await suggester.suggest_synonyms(term="verdachte") == []


def test_get_stats_behouden():
    suggester = SynonymSuggester(ai_service=MagicMock())
    stats = suggester.get_stats()
    assert "status" in stats
```

**Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/unit/services/test_synonym_suggester.py -v`
Expected: FAIL — `ImportError: cannot import name 'SynonymSuggester'`

**Step 3: Write implementation**

Herschrijf `src/services/gpt4_synonym_suggester.py`: behoud `SynonymSuggestion`, hernoem `GPT4SynonymSuggester` → `SynonymSuggester`, verwijder de placeholder-docstrings/TODO's, injecteer `AIServiceV2` via constructor, implementeer `suggest_synonyms` via prompt-builder + parser. Kern:

```python
class SynonymSuggester:
    """Model-onafhankelijke synoniem-suggester (DEF-459).

    Roept het geconfigureerde model aan via AIServiceV2 + ModelRouter
    (task_type="synonyms") met een dedicated juridische onderzoeksprompt.
    Nooit een modelnaam hardcoden — de router kiest provider + model.
    """

    def __init__(self, ai_service: "AIServiceV2", timeout_seconds: int = 30) -> None:
        self._ai_service = ai_service
        self._timeout = timeout_seconds
        self._stats = {"total_calls": 0, "success_count": 0, "failure_count": 0}
        logger.info("SynonymSuggester initialized (model-onafhankelijk via ModelRouter)")

    async def suggest_synonyms(
        self,
        term: str,
        definitie: str | None = None,
        context: list[str] | str | None = None,
    ) -> list[SynonymSuggestion]:
        from services.prompts.synonym_research_prompt import build_synonym_research_prompt
        from services.prompts.synonym_response_parser import parse_synonym_response

        self._stats["total_calls"] += 1
        juridische_context = (
            context if isinstance(context, list)
            else [context] if isinstance(context, str) and context
            else None
        )
        system_prompt, user_prompt = build_synonym_research_prompt(
            term=term, definitie=definitie, juridische_context=juridische_context
        )
        try:
            result = await self._ai_service.generate_definition(
                prompt=user_prompt,
                system_prompt=system_prompt,
                task_type="synonyms",      # model-onafhankelijk
                temperature=0.3,
                max_tokens=800,
                timeout_seconds=self._timeout,
            )
            suggestions = parse_synonym_response(getattr(result, "text", ""))
            self._stats["success_count"] += 1
            return suggestions
        except Exception as exc:  # graceful degradation (orchestrator verwacht dit)
            self._stats["failure_count"] += 1
            logger.warning("SynonymSuggester: AI-call mislukt voor '%s': %s", term, exc)
            return []

    def get_stats(self) -> dict:
        return {**self._stats, "status": "active"}
```

Voeg `from typing import TYPE_CHECKING` + `if TYPE_CHECKING: from services.ai_service_v2 import AIServiceV2` toe voor de type-hint zonder runtime-import-cycle.

**Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/unit/services/test_synonym_suggester.py -v`
Expected: PASS (4 passed)

**Step 5: Commit**

```bash
git add src/services/gpt4_synonym_suggester.py tests/unit/services/test_synonym_suggester.py
git commit -m "feat(DEF-459): SynonymSuggester (hernoemd) roept model-onafhankelijk aan via AIServiceV2"
```

---

## Task 4: DI-wiring — `ai_service()`-accessor + injectie, referenties bijwerken

**Files:**
- Modify: `src/services/container.py` (nieuwe `ai_service()`-accessor; suggester-factory injecteert die; `orchestrator()` gebruikt de accessor)
- Modify: `src/services/synonym_orchestrator.py:26` (import + type-hint)
- Modify: `src/pages/synonym_admin.py:36,105-106` (import + cast)
- Modify: `tests/unit/services/test_synonym_orchestrator.py` (import `SynonymSuggester` i.p.v. `GPT4SynonymSuggester`)

**Step 1:** Grep alle referenties naar de oude naam (verificatie vóór wijzigen).
Run: `rg -n "GPT4SynonymSuggester" src tests`
Expected: treffers in `container.py`, `synonym_orchestrator.py`, `synonym_admin.py`, `test_synonym_orchestrator.py`.

**Step 2:** Voeg in `container.py` een `ai_service()`-accessor toe die de AIServiceV2-singleton bouwt (los van `orchestrator()`), en laat `orchestrator()` (`container.py:308`) `self.ai_service()` gebruiken i.p.v. de lokale constructie:

```python
def ai_service(self) -> "AIServiceV2":
    """Model-onafhankelijke AIServiceV2 (singleton) — DEF-459."""
    if "ai_service" not in self._instances:
        from services.ai_service_v2 import AIServiceV2
        self._instances["ai_service"] = AIServiceV2(
            use_cache=True,
            ai_client=self._get_ai_client(),
            model_router=self.model_router(),
        )
    return cast("AIServiceV2", self._instances["ai_service"])
```

Vervang `container.py:308-312` (lokale `ai_service = AIServiceV2(...)`) door `ai_service = self.ai_service()`.

**Step 3:** Herschrijf de suggester-factory (`container.py:482-507`) zodat hij `SynonymSuggester(ai_service=self.ai_service())` bouwt; werk `synonym_orchestrator()` (`:526-534`) bij zodat de dummy-fallback ook `SynonymSuggester(ai_service=self.ai_service())` gebruikt. Werk de imports/casts/type-hints bij naar `SynonymSuggester`.

**Step 4:** Werk de overige referenties bij: `synonym_orchestrator.py:26,103,109`, `synonym_admin.py:36,105-106`, en de import in `test_synonym_orchestrator.py`. De orchestrator-tests mocken via `Mock(spec=SynonymSuggester)` — controleer dat `spec=` de nieuwe naam gebruikt.

**Step 5:** Run de betrokken unit-tests.
Run: `.venv/bin/python -m pytest tests/unit/services/test_synonym_orchestrator.py tests/unit/services/test_synonym_suggester.py -v`
Expected: PASS (alle). Verifieer daarna geen resterende oude naam:
Run: `rg -n "GPT4SynonymSuggester" src tests` → Expected: geen treffers.

**Step 6: Commit**

```bash
git add src/services/container.py src/services/synonym_orchestrator.py src/pages/synonym_admin.py tests/unit/services/test_synonym_orchestrator.py
git commit -m "refactor(DEF-459): AIServiceV2 via container-accessor injecteren in SynonymSuggester; oude naam uitgefaseerd"
```

---

## Task 5: Context-key-mismatch rechttrekken

De producer (`definition_orchestrator_v2.py:395-400`) stuurt `organisatorisch/juridisch/wettelijk`; de consumer (`synonym_orchestrator.py:280-281`) leest `definitie/tokens` → suggester krijgt altijd `None`. We definiëren één contract en lijnen beide uit.

**Files:**
- Modify: `src/services/synonym_orchestrator.py:277-284` (context uitlezen conform producer-keys)
- Modify: `tests/unit/services/test_synonym_orchestrator.py` (assertie op doorgegeven context)

**Step 1: Write the failing test** — voeg toe aan `test_synonym_orchestrator.py`:

```python
@pytest.mark.asyncio
async def test_juridische_context_wordt_doorgegeven_aan_suggester(self):
    # setup: registry met te weinig bestaande synoniemen (slow path), mock suggester
    ...  # hergebruik bestaande fixture-opzet uit test_slow_path_gpt4_called_when_insufficient
    context = {
        "organisatorisch": ["Gemeente X"],
        "juridisch": ["Wetboek van Strafvordering"],
        "wettelijk": [],
    }
    await orchestrator.ensure_synonyms(term="verdachte", min_count=5, context=context)
    _, kwargs = mock_suggester.suggest_synonyms.call_args
    # De juridische context moet de suggester bereiken (niet langer None)
    assert kwargs["context"] is not None
    assert "Wetboek van Strafvordering" in str(kwargs["context"])
```

**Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/unit/services/test_synonym_orchestrator.py -k juridische_context -v`
Expected: FAIL — `context` is `None` (huidige code leest `context["tokens"]`).

**Step 3: Implementation** — vervang `synonym_orchestrator.py:278-282`:

```python
self.gpt4_suggester.suggest_synonyms(
    term=term,
    definitie=context.get("definitie") if context else None,
    context=_flatten_juridische_context(context) if context else None,
),
```

met een helper bovenin de module:

```python
def _flatten_juridische_context(context: dict) -> list[str] | None:
    """Combineer producer-context-keys tot een platte lijst voor de prompt (DEF-459)."""
    items: list[str] = []
    for key in ("juridisch", "wettelijk", "organisatorisch"):
        val = context.get(key)
        if isinstance(val, list):
            items.extend(str(v) for v in val if v)
        elif isinstance(val, str) and val:
            items.append(val)
    return items or None
```

(`definitie` blijft optioneel; producer stuurt die nu niet, maar het contract ondersteunt het en de UI/andere callers kunnen het meegeven.)

**Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/unit/services/test_synonym_orchestrator.py -v`
Expected: PASS (alle, incl. de nieuwe).

**Step 5: Commit**

```bash
git add src/services/synonym_orchestrator.py tests/unit/services/test_synonym_orchestrator.py
git commit -m "fix(DEF-459): juridische context bereikt de synoniem-suggester (key-mismatch rechtgetrokken)"
```

---

## Task 6: TODO-gate uitbreiden naar docstring/string-TODO's

De placeholder-TODO's stonden in docstrings en ontsnapten aan `check_no_todo_markers.sh` (matcht alleen `#`-TODO's). Na Task 3 zijn de TODO's weg; nu de gate dichten zodat het niet terugkomt.

**Files:**
- Modify: `scripts/ci/check_no_todo_markers.sh:7-9`
- Test: `tests/unit/scripts/test_check_no_todo_markers.py` (nieuw, of shell-smoke)

**Step 1: Write the failing test** — een pytest die een tijdelijk `.py`-bestand met een docstring-TODO aanmaakt en verwacht dat het script exit-code 1 geeft. (Alternatief: shell-smoke in `tests/`; kies wat past bij bestaande conventies — check `tests/unit/scripts/`.)

**Step 2: Run** → Expected: FAIL (script mist docstring-TODO nu).

**Step 3: Implementation** — voeg een derde patroon toe dat TODO-markers óók in docstrings/strings vangt, met de bestaande `tests/`-fixture-exclusies (`sk-test` e.d. zijn niet relevant hier, maar houd `--glob` uitsluitingen intact). Bijvoorbeeld een breder patroon dat `TODO`/`FIXME` als woord matcht in `src/` (niet in `tests/` om test-fixtures niet te raken). Let op de gotcha uit MEMORY.md: meet de echte exit-code (`script > out 2>&1; echo $?`).

**Step 4: Run** → Expected: PASS. Draai daarna het echte script op de repo:
Run: `bash scripts/ci/check_no_todo_markers.sh; echo "exit=$?"`
Expected: `exit=0` (geen TODO's meer na Task 3).

**Step 5: Commit**

```bash
git add scripts/ci/check_no_todo_markers.sh tests/unit/scripts/test_check_no_todo_markers.py
git commit -m "chore(DEF-459): TODO-gate vangt ook docstring/string-TODO's"
```

---

## Task 7: Integratie-test + volledige verificatie + Linear

**Files:**
- Create: `tests/integration/test_synonym_suggester_e2e.py` (achter `sk-`/key-guard)

**Step 1:** Schrijf een integration-test die de echte round-trip dekt, met de skip-guard uit MEMORY.md:

```python
import os
import pytest

pytestmark = pytest.mark.integration

if not os.getenv("OPENAI_API_KEY", "").startswith("sk-") and not os.getenv("ANTHROPIC_API_KEY"):
    pytest.skip("Geen geldige AI-key — integration skip", allow_module_level=True)
```

De test bouwt de suggester via de echte container en verifieert dat `suggest_synonyms("verdachte")` een niet-lege lijst geldige `SynonymSuggestion`-objecten oplevert (confidence ∈ [0,1]).

**Step 2:** Draai de volledige verificatie:

```bash
make test           # unit, fail-fast
make lint           # ruff + black
make mypy-check     # ratchet (baseline 0)
```
Expected: alles groen. Controleer specifiek dat `mypy_baseline.txt` niet stijgt (nieuwe bestanden moeten type-schoon zijn). Draai bij twijfel ook `mypy src/services --ignore-missing-imports` (zero-tolerance services-gate).

**Step 3:** Handmatige UI-rooktest (optioneel, aanrader): start `make dev`, open de Synonym Admin-pagina, klik "🤖 Genereer Suggesties" voor een term met weinig bestaande synoniemen, en bevestig dat er nu écht `ai_pending`-suggesties verschijnen (i.p.v. de misleidende "heeft al voldoende synoniemen"-melding). Volg `rules/agentic-testing.md` (verse staat, onafhankelijke verificatie).

**Step 4: Commit + PR**

```bash
git add tests/integration/test_synonym_suggester_e2e.py
git commit -m "test(DEF-459): integratie-test synoniem-suggester round-trip (key-guarded)"
git push -u origin feature/DEF-459-model-onafhankelijke-synoniemen
gh pr create --title "feat(DEF-459): model-onafhankelijke synoniem-generatie" --body "..."
```

**Step 5:** Draai `/review-pr <nummer>` (verplicht na PR-creatie). Werk DEF-459 in Linear bij naar "In Progress"/"Done" met verwijzing naar de PR.

---

## Verificatie-checklist (bij oplevering)

- [ ] `make test` groen (unit)
- [ ] `make lint` schoon (geen `print()`)
- [ ] `make mypy-check` — baseline niet gestegen
- [ ] `rg "GPT4SynonymSuggester" src tests` → 0 treffers
- [ ] `bash scripts/ci/check_no_todo_markers.sh` → exit 0
- [ ] Geen bestaande KRITIEKE prompt-builder gewijzigd (`git diff --stat` bevat geen `prompt_service_v2.py`/`modular_*`/`modules/`)
- [ ] `/review-pr` gedraaid, review-comment op PR
- [ ] DEF-459 bijgewerkt in Linear

## Scope-grenzen (YAGNI)

- **Wel:** prompt-builder, parser, suggester-implementatie + rename, DI-injectie, context-mismatch, TODO-gate.
- **Niet:** RAG aanraken; caching/rate-limiting herbouwen (AIServiceV2 doet dat al); een nieuwe synoniem-prompt-*module* in de definitie-orchestrator; goedkeurings-workflow van `ai_pending`→`active` wijzigen.
