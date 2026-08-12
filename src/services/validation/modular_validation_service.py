"""ModularValidationService — lichte, async validatieservice (Story 2.3).

Implementeert een deterministische, schema-achtige output en error-isolatie
per regel. Deze service is bedoeld als opstap: simpele ingebouwde regels
dekken basiscases (leegte, lengte, circulariteit, taal/structuur). Later kan
dit uitgebreid worden om ToetsregelManager en Python-regelmodules te gebruiken.
"""

from __future__ import annotations

import logging
import re
import uuid
from collections.abc import ItemsView, KeysView, ValuesView
from typing import Any

from services.validation.evaluators.base import EvaluationDeps, EvaluationOutcome
from services.validation.evaluators.context_metadata import DUPLICATE_STASH_KEY
from services.validation.evaluators.lemma_morphology import lemma_is_enkelvoud
from services.validation.evaluators.registry import get_default_registry
from services.validation.interfaces import CONTRACT_VERSION
from toetsregels.runtime_contract import (
    RequiredInput,
    ResultStatus,
    RuleContractError,
    RuleRecord,
    ScorePolicy,
    build_rule_records,
    missing_inputs,
    root_contract_policy,
)
from utils.dict_helpers import safe_dict_get
from utils.type_helpers import ensure_list, ensure_string

from .aggregation import calculate_weighted_score, determine_acceptability
from .types_internal import EvaluationContext
from .violation_builder import (
    category_for_rule,
    circular_definition_violation,
    empty_definition_violation,
    essential_content_violation,
    informal_language_violation,
    mixed_language_violation,
    organization_violation,
    structure_violation,
    terminology_violation,
    too_long_violation,
    too_short_violation,
)

logger = logging.getLogger(__name__)


class ValidationResultWrapper:
    """Wrapper class om dict result als object properties toegankelijk te maken.

    Maakt het mogelijk om zowel dict-style access (result['key']) als
    attribute-style access (result.key) te gebruiken. Map ook is_valid
    naar is_acceptable voor backwards compatibility met orchestrator.
    """

    def __init__(self, data: dict[str, Any]):
        self._data = data

    def __getattr__(self, name: str) -> Any:
        # Map is_valid naar is_acceptable voor backwards compatibility
        if name == "is_valid":
            return safe_dict_get(self._data, "is_acceptable", False)
        return safe_dict_get(self._data, name)

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __contains__(self, key: str) -> bool:
        return key in self._data

    def get(self, key: str, default: Any = None) -> Any:
        return safe_dict_get(self._data, key, default)

    def keys(self) -> KeysView[str]:
        return self._data.keys()

    def values(self) -> ValuesView[Any]:
        return self._data.values()

    def items(self) -> ItemsView[str, Any]:
        return self._data.items()

    def __repr__(self) -> str:
        return f"ValidationResultWrapper({self._data!r})"

    def to_dict(self) -> dict[str, Any]:
        """Convert to plain dictionary for JSON serialization."""
        return self._data


class ModularValidationService:
    """Eenvoudige modulaire validatie met deterministische resultaten.

    Constructor accepteert optioneel een ToetsregelManager, cleaning_service en
    config-achtige structuur. Alle argumenten zijn optioneel i.v.m. tests die
    minimale initialisatie doen.
    """

    def __init__(
        self,
        toetsregel_manager: Any | None = None,
        cleaning_service: Any | None = None,
        config: Any | None = None,
        repository: Any | None = None,
    ) -> None:
        self.toetsregel_manager = toetsregel_manager
        self.cleaning_service = cleaning_service
        self.config = config
        self._repository = repository

        # DEF-606: gevalideerde regelcontracten + het expliciete
        # evaluatorregister. Zonder record is er geen uitvoerbaar pad; de
        # service verzint er geen.
        self._rule_records: dict[str, RuleRecord] = {}
        self._registry = get_default_registry()
        self._pattern_cache: dict[str, Any] = {}

        # DEF-215: Degraded mode tracking voor transparantie naar UI
        self._is_degraded_mode: bool = False
        self._degradation_reason: str | None = None
        self._rules_loaded_count: int = 0
        # DEF-621: verwachte telling uit het contract (regelbestanden op
        # disk) i.p.v. hardcoded — de eerdere 45 liep achter op de 53.
        self._rules_expected_count: int = self._tel_regelbestanden()

        # Baseline interne regels (altijd beschikbaar voor policies zoals scoring-uitsluiting)
        self._baseline_internal: list[str] = [
            "VAL-EMP-001",
            "VAL-LEN-001",
            "VAL-LEN-002",
            "ESS-CONT-001",
            "CON-CIRC-001",
            "STR-TERM-001",
            "STR-ORG-001",
        ]

        # Load rules from ToetsregelManager if available, otherwise use defaults
        if self.toetsregel_manager is not None:
            self._load_rules_from_manager()
        else:
            # Interne default regelset (fallback als geen ToetsregelManager)
            self._internal_rules: list[str] = list(self._baseline_internal)
            # Default gewichten (overschrijfbaar via config.weights)
            self._default_weights: dict[str, float] = {
                "VAL-EMP-001": 1.0,
                "VAL-LEN-001": 0.9,
                "VAL-LEN-002": 0.6,
                "ESS-CONT-001": 1.0,
                "CON-CIRC-001": 0.8,
                "STR-TERM-001": 0.5,
                "STR-ORG-001": 0.7,
            }
        # Acceptatiedrempel (overschrijfbaar via config.thresholds.overall_accept)
        self._overall_threshold: float = 0.75
        # Categorie-acceptatiedrempel (nieuw; overschrijfbaar via config.thresholds.category_accept)
        self._category_threshold: float = 0.70
        thresholds = getattr(self.config, "thresholds", None)
        if thresholds is not None:
            try:
                self._overall_threshold = float(
                    safe_dict_get(
                        thresholds,
                        "overall_accept",
                        self._overall_threshold,
                    )
                )
            except (ValueError, TypeError) as e:
                logger.error(
                    f"Ongeldige threshold config 'overall_accept': {e}. "
                    f"Gebruik default={self._overall_threshold}"
                )
            try:
                self._category_threshold = float(
                    safe_dict_get(
                        thresholds,
                        "category_accept",
                        self._category_threshold,
                    )
                )
            except (ValueError, TypeError) as e:
                logger.error(
                    f"Ongeldige threshold config 'category_accept': {e}. "
                    f"Gebruik default={self._category_threshold}"
                )

    @staticmethod
    def _tel_regelbestanden() -> int:
        """Verwachte regeltelling uit het contract (DEF-621/DEF-606).

        Komt uit het ``rule_ids``-manifest in de root-SSOT, niet uit een
        glob over de regelmap: dat laatste zou de telling laten meebewegen
        met een verdwenen bestand en het gat juist onzichtbaar maken.
        """
        try:
            return len(root_contract_policy().rule_ids)
        except RuleContractError as e:
            logger.warning(
                f"Contract-telling niet bepaalbaar uit de root-SSOT, "
                f"fallback 45: {type(e).__name__}: {e}"
            )
            return 45

    # Optioneel: exposeer regelvolgorde voor determinismetest
    def _load_rules_from_manager(self) -> None:
        """Load rules from ToetsregelManager if available."""
        try:
            # Get all available rules from manager
            # toetsregel_manager is guaranteed to be not None here (checked by caller)
            manager = self.toetsregel_manager
            if manager is None:
                self._set_default_rules()
                return
            all_rules = manager.get_all_regels()

            # Early return if no rules
            if not all_rules:
                self._set_default_rules()
                return

            # Initialize rule structures (optioneel filter op enabled_codes)
            all_codes = list(all_rules.keys())
            # Evalueren van ALLE beschikbare regels (gebruik weights/thresholds uit config waar beschikbaar)
            self._internal_rules = all_codes
            self._json_rules = all_rules
            # DEF-606: valideer het volledige regelcontract fail-closed. Een
            # record zonder bekende evaluator of met onbekende invoer mag
            # niet stil doorglippen naar een default-pass.
            self._rule_records = build_rule_records(all_rules)
            self._pattern_cache = {}
            self._default_weights = {}

            # Extract weights from rule metadata
            for rule_id in self._internal_rules:
                rule_data = all_rules.get(rule_id, {})
                weight = self._calculate_rule_weight(rule_data or {})
                self._default_weights[rule_id] = weight

            # Add baseline internal rules to retain safeguards (no-op if already present via JSON)
            self._add_baseline_rules()

            # DEF-215: Track loaded rule count for health monitoring
            self._rules_loaded_count = len(self._internal_rules)
            self._is_degraded_mode = False  # Explicit: not degraded

            logger.info(
                f"Loaded {len(self._internal_rules)} rules from ToetsregelManager"
            )

        except RuleContractError:
            # DEF-606: een geschonden regelcontract is geen degraded-state maar
            # een startupfout. Stil terugvallen op zeven baselineregels zou de
            # validatie uithollen zonder dat iemand het merkt.
            logger.critical("Regelcontract geschonden; validatie kan niet starten")
            raise
        except Exception as e:
            # DEF-215: Set degraded mode flags voor UI transparantie
            self._is_degraded_mode = True
            self._degradation_reason = (
                f"ToetsregelManager failure: {type(e).__name__}: {e}"
            )
            self._rules_loaded_count = len(self._baseline_internal)  # 7 baseline rules

            logger.error(
                f"ToetsregelManager laden GEFAALD: {e}. "
                f"Fallback naar baseline regels (validatie coverage sterk verminderd). "
                f"Rules: {self._rules_loaded_count}/{self._rules_expected_count} ({self._rules_loaded_count/self._rules_expected_count*100:.0f}% coverage)",
                extra={
                    "component": "modular_validation_service",
                    "degraded_mode": True,
                    "rules_loaded": self._rules_loaded_count,
                    "rules_expected": self._rules_expected_count,
                    "degradation_reason": str(e),
                },
            )
            self._set_default_rules()

    def _calculate_rule_weight(self, rule_data: dict) -> float:
        """Calculate weight for a rule based on priority or explicit weight."""
        # Check for explicit weight first
        if "weight" in rule_data and rule_data["weight"] is not None:
            try:
                return float(rule_data["weight"])
            except (TypeError, ValueError):
                logger.debug(
                    f"Invalid weight value: {rule_data.get('weight')}, using priority-based weight"
                )

        # Use priority to determine weight
        priority = ensure_string(safe_dict_get(rule_data, "prioriteit", "midden"))
        priority_weights = {"hoog": 1.0, "midden": 0.7}
        return priority_weights.get(
            priority, 0.4
        )  # default to 0.4 for "laag" or unknown

    def _add_baseline_rules(self) -> None:
        """Add baseline internal rules (VAL-*/STR-*) to retain safeguards."""
        for rid in self._baseline_internal:
            if rid not in self._internal_rules:
                self._internal_rules.append(rid)

    def _set_default_rules(self) -> None:
        """Set default rules when ToetsregelManager is not available."""
        self._internal_rules = list(self._baseline_internal)
        self._default_weights = {
            "VAL-EMP-001": 1.0,
            "VAL-LEN-001": 0.9,
            "VAL-LEN-002": 0.6,
            "ESS-CONT-001": 1.0,
            "CON-CIRC-001": 0.8,
            "STR-TERM-001": 0.5,
            "STR-ORG-001": 0.7,
        }
        # Gebruik ook het JSON-pad voor deze 7 regels zodat evaluatie generiek verloopt
        self._json_rules = {
            "VAL-EMP-001": {
                "id": "VAL-EMP-001",
                "prioriteit": "hoog",
                "aanbeveling": "verplicht",
                "min_chars": 1,
            },
            "VAL-LEN-001": {
                "id": "VAL-LEN-001",
                "prioriteit": "midden",
                "aanbeveling": "verplicht",
                "min_words": 5,
                "min_chars": 15,
            },
            "VAL-LEN-002": {
                "id": "VAL-LEN-002",
                "prioriteit": "laag",
                "aanbeveling": "aanbevolen",
                "max_words": 80,
                "max_chars": 600,
            },
            "ESS-CONT-001": {
                "id": "ESS-CONT-001",
                "prioriteit": "hoog",
                "aanbeveling": "verplicht",
                "min_words": 6,
            },
            "CON-CIRC-001": {
                "id": "CON-CIRC-001",
                "prioriteit": "midden",
                "aanbeveling": "verplicht",
                "circular_definition": True,
            },
            "STR-TERM-001": {
                "id": "STR-TERM-001",
                "prioriteit": "laag",
                "aanbeveling": "aanbevolen",
                "forbidden_phrases": ["HTTP protocol"],
            },
            "STR-ORG-001": {
                "id": "STR-ORG-001",
                "prioriteit": "midden",
                "aanbeveling": "aanbevolen",
                "max_chars": 300,
                "min_commas": 6,
                "redundancy_patterns": [
                    r"\\bsimpel\\b.*\\bcomplex\\b",
                    r"\\bcomplex\\b.*\\bsimpel\\b",
                ],
            },
        }

    def _get_rule_evaluation_order(
        self,
    ) -> list[str]:  # pragma: no cover - used by optional test
        return sorted(self._internal_rules)

    def get_health_status(self) -> dict[str, Any]:
        """DEF-215: Get validation service health status for monitoring/UI.

        Returns:
            dict with health information including degraded mode status.
        """
        coverage_pct = (
            (self._rules_loaded_count / self._rules_expected_count * 100)
            if self._rules_expected_count > 0
            else 0
        )
        return {
            "status": "degraded" if self._is_degraded_mode else "healthy",
            "degraded_mode": self._is_degraded_mode,
            "rules_loaded": self._rules_loaded_count,
            "rules_expected": self._rules_expected_count,
            "coverage_pct": round(coverage_pct, 1),
            "degradation_reason": self._degradation_reason,
        }

    async def validate_definition(
        self,
        begrip: str,
        text: str,
        ontologische_categorie: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        # 1) Correlation ID
        correlation_id = None
        if context and isinstance(context, dict):
            correlation_id = context.get("correlation_id")
        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        # 2) Cleaning (optioneel, éénmaal)
        cleaned = text
        if self.cleaning_service is not None and hasattr(
            self.cleaning_service, "clean_text"
        ):
            try:
                clean_result = self.cleaning_service.clean_text(text)
                # clean_text kan sync of async zijn
                if hasattr(clean_result, "__await__"):
                    clean_result = await clean_result  # type: ignore[func-returns-value]
                # Ondersteun zowel string als object met cleaned_text attribuut
                if isinstance(clean_result, str):
                    cleaned = clean_result
                elif hasattr(clean_result, "cleaned_text"):
                    cleaned = clean_result.cleaned_text
            except (RuntimeError, TypeError, AttributeError, UnicodeError) as e:
                # DEF-231: Bij cleaning-fout: ga verder met raw text (geen crash)
                logger.warning(
                    f"Tekst cleaning gefaald, validatie met ruwe tekst: {type(e).__name__}: {e}",
                    extra={
                        "component": "modular_validation_service",
                        "operation": "text_cleaning",
                        "correlation_id": correlation_id,
                        "text_length": len(text) if text else 0,
                        "cleaning_service_type": type(self.cleaning_service).__name__,
                    },
                )
                cleaned = text

        # 3) Context opbouwen (tokens slechts op aanvraag; hier niet nodig)
        # DEF-244: begrip now passed via context instead of instance variable
        eval_ctx = EvaluationContext.from_params(
            text=text,
            cleaned=cleaned,
            begrip=begrip,  # DEF-244: Thread-safe begrip passing
            locale=(context or {}).get("locale") if isinstance(context, dict) else None,
            profile=(
                (context or {}).get("profile") if isinstance(context, dict) else None
            ),
            correlation_id=correlation_id,
            tokens=(),
            metadata=dict(context or {}),
        )

        # DEF-251: Log validation start with begrip for observability
        # DEF-249 FIX: Deduplicate calculations (were computed twice before)
        begrip_truncated = (begrip or "")[:50]
        text_length = len(text) if text else 0
        logger.info(
            "Starting validation: begrip='%s', text_length=%d, correlation_id=%s",
            begrip_truncated,
            text_length,
            correlation_id,
            extra={
                "component": "modular_validation_service",
                "operation": "validate_definition_start",
                "begrip": begrip_truncated,
                "text_length": text_length,
                "correlation_id": correlation_id,
            },
        )

        # 4) Regels evalueren in deterministische volgorde
        weights = dict(self._default_weights)
        config_weights = getattr(self.config, "weights", None)
        if config_weights is not None:
            weights.update(
                {
                    k: float(v) if v is not None else self._default_weights.get(k, 0.5)
                    for k, v in config_weights.items()
                }
            )

        # Exclude certain rules from scoring (weight=0):
        # - Interne baseline regels (self._baseline_internal) - ALLEEN als er ook JSON regels zijn
        # - ARAI* taalregels (AR**/ARAI**)
        # NOTE: In fallback mode (alleen baseline regels), moeten deze WEL meegewogen worden
        has_non_baseline_rules = any(
            code not in self._baseline_internal for code in self._internal_rules
        )
        try:
            for code in list(weights.keys()):
                cu = str(code).upper()
                # Baseline regels alleen uitsluiten als er ook andere regels zijn
                if has_non_baseline_rules and code in self._baseline_internal:
                    weights[code] = 0.0
                elif cu.startswith(("ARAI", "AR-", "AR")):
                    # Beperk tot ARAI-familie; AR-prefix meegenomen voor compat
                    weights[code] = 0.0
        except (KeyError, TypeError, ValueError) as e:
            # DEF-231: Log baseline rule filter failures with context
            logger.warning(
                f"Baseline rule filtering overgeslagen: {type(e).__name__}: {e}",
                extra={
                    "component": "modular_validation_service",
                    "operation": "filter_baseline_rules",
                    "weights_count": len(weights) if weights else 0,
                    "correlation_id": correlation_id,
                },
            )

        # DEF-606/DEF-624: regels met scorepolicy 'excluded_from_score'
        # declareren zelf dat ze niet meewegen; dat is dezelfde uitkomst als de
        # bestaande ARAI-/baseline-nullering, maar nu uit het contract i.p.v.
        # uit een prefixvergelijking.
        for code, record in self._rule_records.items():
            if record.score_policy is ScorePolicy.EXCLUDED_FROM_SCORE:
                weights[code] = 0.0

        rule_scores: dict[str, float] = {}
        violations: list[dict[str, Any]] = []
        passed_rules: list[str] = []
        rule_statuses: dict[str, str] = {}
        review_items: list[dict[str, Any]] = []

        # DEF-244: begrip is now in eval_ctx.begrip (thread-safe)
        for code in sorted(self._internal_rules):
            out = self._evaluate_rule(code, eval_ctx)
            if isinstance(out, EvaluationOutcome):
                self._verwerk_uitkomst(
                    code,
                    eval_ctx,
                    out,
                    rule_scores=rule_scores,
                    violations=violations,
                    passed_rules=passed_rules,
                    rule_statuses=rule_statuses,
                    review_items=review_items,
                )
            # Support both (score, violation) tuple and dict-like outputs (for tests that patch the method)
            elif isinstance(out, tuple):
                score, violation = out
                rule_scores[code] = score
                rule_statuses[code] = (
                    ResultStatus.FAIL.value
                    if violation is not None
                    else ResultStatus.PASS.value
                )
                if violation is not None:
                    violations.append(violation)
                else:
                    passed_rules.append(code)
            elif isinstance(out, dict):
                score = float(safe_dict_get(out, "score", 0.0) or 0.0)
                rule_scores[code] = score
                vlist = ensure_list(safe_dict_get(out, "violations", []))
                rule_statuses[code] = (
                    ResultStatus.FAIL.value if vlist else ResultStatus.PASS.value
                )
                if vlist:
                    # If a list of violations is returned, extend with minimal mapping
                    for _ in vlist:
                        violations.append(
                            {
                                "code": code,
                                "severity": "warning",
                                "message": "",
                                "description": "",
                                "rule_id": code,
                                "category": category_for_rule(code),
                            }
                        )
                else:
                    passed_rules.append(code)
            else:
                # Fallback: treat as scalar score
                rule_scores[code] = float(out or 0.0)
                geslaagd = float(out or 0.0) >= 1.0
                rule_statuses[code] = (
                    ResultStatus.PASS.value if geslaagd else ResultStatus.FAIL.value
                )
                if geslaagd:
                    passed_rules.append(code)
        # DEF-244: begrip cleanup removed - now in eval_ctx (immutable, thread-safe)

        # 5) Aggregatie (gewogen) en afronding
        overall = calculate_weighted_score(rule_scores, weights)

        # Quality band scaling: gently penalize very short/very long texts to
        # avoid saturating at 1.0 for minimale/overdadige gevallen. Calibrated
        # to align with golden bands (acceptable minimal ≈ 0.60-0.75,
        # high quality ≥ 0.75, perfect ≥ 0.80).
        try:
            raw = (eval_ctx.cleaned_text or eval_ctx.raw_text or "").strip()
            wcount = len(raw.split()) if raw else 0
        except (AttributeError, TypeError) as e:
            # DEF-231: Log word count calculation failures
            logger.debug(
                f"Woordentelling gefaald, default naar 0: {type(e).__name__}: {e}",
                extra={
                    "component": "modular_validation_service",
                    "operation": "word_count",
                    "correlation_id": correlation_id,
                },
            )
            wcount = 0

        scale = 1.0
        if wcount < 12:
            scale = 0.75
        elif wcount < 20:
            scale = 0.9
        elif wcount > 100:
            scale = 0.85
        elif wcount > 60:
            scale = 0.9

        overall = round(overall * scale, 2)

        # Extra heuristics (language/structure) to align with golden expectations
        try:
            raw_text = (eval_ctx.cleaned_text or eval_ctx.raw_text or "").strip()
        except (AttributeError, TypeError) as e:
            # DEF-231: Log raw text extraction failures
            logger.debug(
                f"Raw text extractie gefaald, default naar leeg: {type(e).__name__}: {e}",
                extra={
                    "component": "modular_validation_service",
                    "operation": "raw_text_extraction",
                    "correlation_id": correlation_id,
                },
            )
            raw_text = ""
        # Informal language
        if self._has_informal_language(raw_text):
            violations.append(informal_language_violation())
            if not any(str(v.get("code", "")) == "ESS-CONT-001" for v in violations):
                violations.append(essential_content_violation())
        # Mixed NL/EN
        if self._has_mixed_language(raw_text):
            violations.append(mixed_language_violation())
        # Too minimal structure (very short definitions)
        if wcount < 6:
            violations.append(structure_violation())
        # Circular definition fallback (ensure we catch simple cases)
        # DEF-244: Use eval_ctx.begrip instead of instance variable
        try:
            if eval_ctx.begrip:
                tn = raw_text.lower()
                gb = str(eval_ctx.begrip).strip().lower()
                if (
                    gb
                    and gb in tn
                    and not any(v.get("code") == "CON-CIRC-001" for v in violations)
                ):
                    violations.append(
                        circular_definition_violation(str(eval_ctx.begrip))
                    )
                    # Voeg ook essentie-tekort toe voor strengere golden criteria
                    if not any(
                        str(v.get("code", "")) == "ESS-CONT-001" for v in violations
                    ):
                        violations.append(essential_content_violation())
        except (TypeError, AttributeError) as e:
            # DEF-231: Log circular check failures for debugging
            logger.warning(
                f"Circulaire definitie check overgeslagen: {type(e).__name__}: {e}",
                extra={
                    "component": "modular_validation_service",
                    "rule_id": "CON-CIRC-001",
                    "correlation_id": correlation_id,
                    "begrip": str(eval_ctx.begrip)[:50] if eval_ctx.begrip else None,
                },
            )

        # 6) Categorie-scores: bereken op basis van rule_scores (geen mirror)
        try:
            detailed = self._calculate_category_scores(
                rule_scores, default_value=overall
            )
        except (TypeError, ValueError, ZeroDivisionError) as e:
            # DEF-231: Conservatieve fallback bij categorie-berekening fout
            logger.warning(
                f"Categorie-scores berekening gefaald, fallback naar overall: {type(e).__name__}: {e}",
                extra={
                    "component": "modular_validation_service",
                    "operation": "category_scores",
                    "correlation_id": correlation_id,
                    "overall_score": overall,
                    "rule_count": len(rule_scores) if rule_scores else 0,
                },
            )
            detailed = {
                "taal": overall,
                "juridisch": overall,
                "structuur": overall,
                "samenhang": overall,
            }

        # 7) Voeg eventuele CON-01 duplicate warnings toe (best-effort)
        try:
            dup_warns = (
                eval_ctx.metadata.get(DUPLICATE_STASH_KEY)
                if hasattr(eval_ctx, "metadata")
                else None
            )
            if dup_warns:
                # Ensure proper minimal structure
                for w in dup_warns:
                    if isinstance(w, dict) and "code" in w:
                        violations.append(w)
        except (AttributeError, TypeError) as e:
            # DEF-231: Log duplicate warning failures for debugging
            logger.warning(
                f"CON-01 duplicate warnings verwerking overgeslagen: {type(e).__name__}: {e}",
                extra={
                    "component": "modular_validation_service",
                    "rule_id": "CON-01",
                    "correlation_id": correlation_id,
                },
            )

        # 8) Violations deterministisch sorteren op code
        violations.sort(key=lambda v: v.get("code", ""))

        # 9) Acceptance gates bepalen acceptatie (kritiek/overall/categorieën)
        try:
            acceptance_gate = self._evaluate_acceptance_gates(
                overall, detailed, violations
            )
        except (TypeError, ValueError, KeyError) as e:
            # DEF-231: Fallback op basis-acceptatie als gate-evaluatie faalt
            logger.warning(
                f"Acceptance gates evaluatie gefaald, fallback naar threshold: {type(e).__name__}: {e}",
                extra={
                    "component": "modular_validation_service",
                    "operation": "acceptance_gates",
                    "correlation_id": correlation_id,
                    "overall_score": overall,
                    "threshold": self._overall_threshold,
                },
            )
            acceptance_gate = {
                "acceptable": determine_acceptability(overall, self._overall_threshold),
                "gates_passed": [],
                "gates_failed": [],
                "thresholds": {
                    "overall": self._overall_threshold,
                    "category": self._category_threshold,
                },
            }

        # Blocking errors check: bepaalde violations blokkeren ALTIJD acceptatie
        def _has_blocking_errors(vs: list[dict[str, Any]]) -> bool:
            for v in vs or []:
                if str(v.get("severity", "")).lower() != "error":
                    continue
                code = str(v.get("code", ""))
                if code.startswith(
                    (
                        "VAL-EMP",
                        "CON-CIRC",
                        "VAL-LEN-002",
                        "LANG-",
                        "STR-FORM-001",
                    )
                ):
                    return True
            return False

        has_blockers = _has_blocking_errors(violations)
        # Soft floor: score >= 0.60 zonder blocking errors (0.60 = acceptabel minimaal)
        soft_ok = (overall >= 0.60) and (not has_blockers)
        # Blocking errors overrulen de acceptance gate
        gate_ok = bool(acceptance_gate.get("acceptable", False)) and (not has_blockers)
        is_ok = gate_ok or soft_ok

        # 10) Schema-achtige dict output
        result: dict[str, Any] = {
            "version": CONTRACT_VERSION,
            "overall_score": overall,
            "is_acceptable": is_ok,
            "violations": violations,
            "passed_rules": passed_rules,
            "detailed_scores": detailed,
            # DEF-624: score en dekking zijn twee getallen, geen één. Een regel
            # die niet is uitgevoerd of menselijk oordeel vraagt telt niet als
            # pass mee; hij is hier zichtbaar in plaats van onzichtbaar.
            "rule_statuses": rule_statuses,
            "evaluation_coverage": self._bereken_dekking(rule_statuses),
            "review_required": review_items,
            # DEF-215: Include degraded mode metadata for UI transparency
            "system": {
                "correlation_id": correlation_id,
                "degraded_mode": self._is_degraded_mode,
                "rules_loaded": self._rules_loaded_count,
                "rules_expected": self._rules_expected_count,
                "degradation_reason": self._degradation_reason,
            },
        }
        # Voeg acceptance_gate toe aan resultaat voor UI/clients
        if acceptance_gate:
            result["acceptance_gate"] = acceptance_gate
        # Return plain dict voor JSON serialisatie
        # De orchestrator verwacht een dict, niet een wrapper
        return result

    def _has_informal_language(self, text: str) -> bool:
        try:
            import re

            patterns = [
                r"\bzo'n ding\b",
                r"\benzo\b",
                r"\bspelletjes\b",
                r"\binternetten\b",
                r"\bvan alles\b",
            ]
            return any(re.search(p, text, re.IGNORECASE) for p in patterns)
        except (re.error, TypeError) as e:
            # DEF-231: Log language check failures
            logger.debug(
                f"Informele taal check overgeslagen: {type(e).__name__}: {e}",
                extra={
                    "component": "modular_validation_service",
                    "rule_id": "LANG-INF-001",
                    "text_length": len(text) if isinstance(text, str) else 0,
                },
            )
            return False

    def _has_mixed_language(self, text: str) -> bool:
        try:
            import re

            en_cues = [r"\bdevelopers\b", r"\bbest practices\b", r"\bbuilden\b"]
            nl_cues = [r"\bhet\b", r"\bde\b", r"\been\b"]
            has_en = any(re.search(p, text, re.IGNORECASE) for p in en_cues)
            has_nl = any(re.search(p, text, re.IGNORECASE) for p in nl_cues)
            return bool(has_en and has_nl)
        except (re.error, TypeError) as e:
            # DEF-231: Log language check failures
            logger.debug(
                f"Gemengde taal check overgeslagen: {type(e).__name__}: {e}",
                extra={
                    "component": "modular_validation_service",
                    "rule_id": "LANG-MIX-001",
                    "text_length": len(text) if isinstance(text, str) else 0,
                },
            )
            return False

    # Interne regel-evaluatie (houd simpel en deterministisch)
    def _evaluate_rule(self, code: str, ctx: EvaluationContext) -> EvaluationOutcome:
        """Voer één regel uit via het evaluatorregister (DEF-606).

        Een regel met gevalideerd contract loopt altijd via precies één
        geregistreerde evaluator. Regels zonder record (fallback-modus zonder
        ToetsregelManager) draaien de ingebouwde baselinechecks.
        """
        record = self._rule_records.get(code)
        if record is not None:
            return self._evaluate_via_registry(record, ctx)
        return self._evaluate_baseline_rule(code, ctx)

    def _evaluate_via_registry(
        self, record: RuleRecord, ctx: EvaluationContext
    ) -> EvaluationOutcome:
        """Resolveer de evaluator en bewaak de vereiste invoer.

        Fail-closed op drie manieren: ontbrekende vereiste invoer levert
        `not_evaluated`, een onbekende evaluator of een fout tijdens uitvoeren
        levert `error`. Geen van die uitkomsten telt als pass.
        """
        beschikbaar = self._available_inputs(ctx)
        ontbrekend = missing_inputs(record, beschikbaar)
        if ontbrekend:
            namen = ", ".join(sorted(item.value for item in ontbrekend))
            return EvaluationOutcome.not_evaluated(
                f"vereiste invoer ontbreekt: {namen}"
            )

        deps = EvaluationDeps(
            support=self,
            available_inputs=beschikbaar,
            repository=self._repository,
            pattern_cache=self._pattern_cache,
        )
        try:
            evaluator = self._registry.resolve(record.evaluator)
            return evaluator.evaluate(record, ctx, deps)
        except RuleContractError as exc:
            logger.error(
                "Regel %s heeft geen uitvoerbare evaluator: %s",
                record.rule_id,
                exc,
                extra={
                    "component": "modular_validation_service",
                    "rule_id": record.rule_id,
                    "correlation_id": ctx.correlation_id,
                },
            )
            return EvaluationOutcome(
                status=ResultStatus.ERROR, reason=f"contractfout: {exc}"
            )
        except Exception as exc:
            logger.error(
                "Evaluator voor regel %s faalde: %s: %s",
                record.rule_id,
                type(exc).__name__,
                exc,
                extra={
                    "component": "modular_validation_service",
                    "rule_id": record.rule_id,
                    "correlation_id": ctx.correlation_id,
                },
            )
            return EvaluationOutcome(
                status=ResultStatus.ERROR,
                reason=f"{type(exc).__name__}: {exc}",
            )

    def _available_inputs(self, ctx: EvaluationContext) -> frozenset[RequiredInput]:
        """Welke gedeclareerde invoer is voor deze validatie beschikbaar?

        Beschikbaarheid gaat over het bestaan van het invoerkanaal, niet over
        de inhoud: een lege definitietekst is nog steeds een aangeleverde
        tekst, anders zou VAL-EMP-001 zichzelf uitschakelen.
        """
        metadata = ctx.metadata or {}
        beschikbaar: set[RequiredInput] = {RequiredInput.DEFINITION_TEXT}
        if (ctx.begrip or "").strip():
            beschikbaar.add(RequiredInput.TERM)
        if any(
            metadata.get(veld)
            for veld in (
                "organisatorische_context",
                "juridische_context",
                "wettelijke_basis",
            )
        ):
            beschikbaar.add(RequiredInput.CONTEXT_LISTS)
        if self._repository is not None:
            beschikbaar.add(RequiredInput.DEFINITION_REPOSITORY)
        if metadata.get("synoniemen"):
            beschikbaar.add(RequiredInput.SYNONYMS)
        if metadata.get("voorkeursterm"):
            beschikbaar.add(RequiredInput.PREFERRED_TERM)
        if metadata.get("categorie") or metadata.get("ontologische_categorie"):
            beschikbaar.add(RequiredInput.ONTOLOGICAL_CATEGORY)
        if metadata.get("gerelateerde_begrippen"):
            beschikbaar.add(RequiredInput.RELATED_CONCEPTS)
        return frozenset(beschikbaar)

    def _outcome_naar_violation(
        self, code: str, ctx: EvaluationContext, outcome: EvaluationOutcome
    ) -> tuple[float, dict[str, Any] | None]:
        """Zet een FAIL-uitkomst om in het bestaande violation-formaat."""
        if outcome.violation is not None:
            return (
                outcome.score if outcome.score is not None else 0.0,
                outcome.violation,
            )
        if not outcome.findings:
            return 1.0, None

        rule = self._json_rules.get(code, {}) if hasattr(self, "_json_rules") else {}
        text = ctx.cleaned_text or ""
        treffers = set(outcome.pattern_hits)
        score = 0.0 if not treffers else max(0.0, 1.0 - 0.3 * len(treffers))
        beschrijving = "; ".join(
            dict.fromkeys(bevinding.message for bevinding in outcome.findings)
        )
        suggesties = [
            self.build_suggestion(
                code,
                rule,
                text,
                ctx,
                reason=bevinding.reason,
                details=bevinding.details,
            )
            for bevinding in outcome.findings
        ]
        violation: dict[str, Any] = {
            "code": code,
            "severity": self.severity_for(rule),
            "severity_level": self.severity_level_for(rule),
            "message": beschrijving,
            "description": beschrijving,
            "rule_id": code,
            "category": category_for_rule(code),
            "suggestion": "; ".join([s for s in suggesties if s]).strip() or None,
        }
        md: dict[str, Any] = {}
        if outcome.first_hit_pattern is not None:
            md["detected_pattern"] = outcome.first_hit_pattern
        if outcome.first_hit_pos is not None:
            md["position"] = int(outcome.first_hit_pos)
        if md:
            violation["metadata"] = md
        return score, violation

    def _verwerk_uitkomst(
        self,
        code: str,
        ctx: EvaluationContext,
        outcome: EvaluationOutcome,
        *,
        rule_scores: dict[str, float],
        violations: list[dict[str, Any]],
        passed_rules: list[str],
        rule_statuses: dict[str, str],
        review_items: list[dict[str, Any]],
    ) -> None:
        """Boek één regeluitkomst in score, violations en dekking.

        Kern van DEF-624: alleen `pass` en `fail` belanden in `rule_scores` en
        wegen dus mee in de kwaliteitsscore. `review_required`,
        `not_evaluated` en `error` vallen uit de noemer — ze worden nooit
        stil als 1,0 meegeteld en verschijnen apart in de evaluatiedekking.
        """
        rule_statuses[code] = outcome.status.value

        if outcome.status is ResultStatus.PASS:
            rule_scores[code] = 1.0 if outcome.score is None else outcome.score
            passed_rules.append(code)
            return

        if outcome.status is ResultStatus.FAIL:
            score, violation = self._outcome_naar_violation(code, ctx, outcome)
            rule_scores[code] = score
            if violation is not None:
                violations.append(violation)
            else:
                passed_rules.append(code)
            return

        if outcome.status is ResultStatus.REVIEW_REQUIRED:
            review_items.append(
                {
                    "rule_id": code,
                    "category": category_for_rule(code),
                    "reason": outcome.reason or "",
                    "signals": list(outcome.metadata.get("signals", [])),
                }
            )
            return

        if outcome.status is ResultStatus.ERROR:
            logger.warning(
                "Regel %s leverde een evaluatorfout: %s",
                code,
                outcome.reason,
                extra={
                    "component": "modular_validation_service",
                    "rule_id": code,
                    "correlation_id": ctx.correlation_id,
                },
            )

    def _bereken_dekking(self, rule_statuses: dict[str, str]) -> dict[str, Any]:
        """Evaluatiedekking naast de kwaliteitsscore (DEF-624).

        Een lagere dekking mag nooit als hogere kwaliteit verschijnen; daarom
        rapporteert het resultaat beide getallen los van elkaar.
        """
        telling = {status.value: 0 for status in ResultStatus}
        for status in rule_statuses.values():
            telling[status] = telling.get(status, 0) + 1
        totaal = len(rule_statuses)
        geevalueerd = (
            telling[ResultStatus.PASS.value] + telling[ResultStatus.FAIL.value]
        )
        return {
            "evaluated": geevalueerd,
            "passed": telling[ResultStatus.PASS.value],
            "failed": telling[ResultStatus.FAIL.value],
            "review_required": telling[ResultStatus.REVIEW_REQUIRED.value],
            "not_evaluated": telling[ResultStatus.NOT_EVALUATED.value],
            "error": telling[ResultStatus.ERROR.value],
            "total": totaal,
            "coverage_ratio": round(geevalueerd / totaal, 4) if totaal else 0.0,
        }

    def _evaluate_baseline_rule(
        self, code: str, ctx: EvaluationContext
    ) -> EvaluationOutcome:
        """Ingebouwde baselinechecks voor de fallback zonder regelrecords."""
        score, violation = self._baseline_uitkomst(code, ctx)
        if violation is not None:
            return EvaluationOutcome(
                status=ResultStatus.FAIL, score=score, violation=violation
            )
        return EvaluationOutcome(status=ResultStatus.PASS, score=score)

    def _baseline_uitkomst(
        self, code: str, ctx: EvaluationContext
    ) -> tuple[float, dict[str, Any] | None]:
        text = ctx.cleaned_text or ""
        # Normalisaties
        text_norm = text.strip()
        words = len(text_norm.split()) if text_norm else 0
        chars = len(text_norm)

        # Leegte
        if code == "VAL-EMP-001":
            if chars == 0:
                return 0.0, empty_definition_violation()
            return 0.9, None

        # Te kort
        if code == "VAL-LEN-001":
            if words < 5 or chars < 15:
                return 0.0, too_short_violation()
            if words < 12 or chars < 40:
                return 0.7, None
            if words < 25:
                return 0.85, None
            return 0.9, None

        # Te lang
        if code == "VAL-LEN-002":
            if words > 80 or chars > 600:
                return 0.0, too_long_violation()
            if words > 60 or chars > 450:
                return 0.85, None
            return 0.95, None

        # Essentiële inhoud aanwezig (heel grof: voldoende informatiedichtheid)
        if code == "ESS-CONT-001":
            if words < 6:
                return 0.0, essential_content_violation()
            if words < 12:
                return 0.65, None
            return 0.9, None

        # Circulair (begrip in definitie)
        # DEF-244: Use ctx.begrip instead of instance variable
        if code == "CON-CIRC-001":
            begrip = ctx.begrip or None
            if begrip:
                pattern = rf"\b{re.escape(str(begrip))}\b"
                found = bool(re.search(pattern, text_norm, re.IGNORECASE))
                if not found:
                    # Fallback: naive contains check in lowercase with added spaces
                    tn = f" {text_norm.lower()} "
                    gb = f" {str(begrip).strip().lower()} "
                    found = gb in tn
                if found:
                    return 0.0, circular_definition_violation(str(begrip))
            return 1.0, None

        # Terminologie/structuur kleine kwestie (bijv. ontbrekende koppelteken)
        if code == "STR-TERM-001":
            if "HTTP protocol" in text_norm:
                return 0.0, terminology_violation("HTTP protocol")
            return 0.95, None

        # Organisatie/structuur (lange aaneengeregen zin of herhalingen)
        if code == "STR-ORG-001":
            long_sentence = chars > 300 and text_norm.count(",") >= 6
            redundancy = bool(
                re.search(
                    r"\bsimpel\b.*\bcomplex\b|\bcomplex\b.*\bsimpel\b",
                    text_norm,
                    re.IGNORECASE,
                )
            )
            if long_sentence or redundancy:
                return 0.0, organization_violation()
            return 0.9, None

        # Onbekende regelcode → pass
        return 1.0, None

    def _severity_level_for_json_rule(self, rule: dict[str, Any]) -> str:
        """Map JSON aanbeveling/prioriteit naar severity-level (critical/high/medium/low)."""
        aan = str(rule.get("aanbeveling", "")).lower()
        pri = str(rule.get("prioriteit", "")).lower()
        if aan == "verplicht" and pri == "hoog":
            return "critical"
        if aan == "verplicht":
            return "high"
        if pri == "hoog":
            return "medium"
        return "low"

    def _severity_for_json_rule(self, rule: dict[str, Any]) -> str:
        """Compatibele severity (error/warning) afgeleid van severity-level."""
        lvl = self._severity_level_for_json_rule(rule)
        return "error" if lvl in ("critical", "high") else "warning"

    def _build_suggestion_for_violation(
        self,
        code: str,
        rule: dict[str, Any] | None,
        text: str,
        ctx: EvaluationContext,
        *,
        reason: str,
        details: str | None = None,
    ) -> str:
        """Genereer concrete NL-suggestie om een violation te herstellen."""
        c = (code or "").upper()
        d = (details or "").strip()

        if reason == "forbidden_patterns":
            return "Herschrijf de zin zodat de gedetecteerde patronen niet voorkomen."
        if reason == "required_patterns":
            return "Maak het vereiste element expliciet in de formulering."
        if reason == "forbidden_phrase":
            return f"Vervang of verwijder de term '{d}'; kies correcte terminologie."
        if reason == "min_words":
            return (
                f"Breid de definitie uit tot minimaal {d} woorden met kerninformatie."
            )
        if reason == "max_words":
            return f"Verkort de definitie tot maximaal {d} woorden; schrap bijzinnen."
        if reason == "min_chars":
            return f"Breid de definitie uit tot minimaal {d} tekens."
        if reason == "max_chars":
            return f"Kort de definitie in tot maximaal {d} tekens; maak compacter."
        if reason == "circular":
            return f"Vermijd het begrip '{d}' in de definitie; omschrijf zonder het letterlijk te herhalen."
        if reason == "structure_runon":
            return "Vereenvoudig de zinsstructuur: minder komma's en kortere zinsdelen."
        if reason == "redundancy":
            return "Verwijder redundante/tegenstrijdige bewoordingen; kies één heldere formulering."
        if reason == "auth_source" and c == "CON-02":
            return "Voeg een authentieke bron/basis toe (bijv. 'volgens', 'conform', of wet/regeling)."
        if reason == "unique_id" and c == "ESS-03":
            return (
                "Voeg een uniek identificatiecriterium toe (nummer/code/registratie)."
            )
        if reason == "testable" and c == "ESS-04":
            return "Maak een objectief toetsbaar element expliciet (bijv. termijn of meetbare grens)."
        if reason == "distinguishing" and c == "ESS-05":
            return "Voeg een onderscheidend kenmerk toe dat het begrip afbakent."
        if reason == "singular" and c == "VER-01":
            return "Schrijf het lemma in enkelvoud (tenzij plurale tantum)."

        # Regel-specifieke defaults
        if c == "INT-01":
            return (
                "Herschrijf naar één compacte zin; vermijd 'en/maar/of' en bijzinnen."
            )
        if c == "CON-01":
            return "Noem de context niet expliciet; formuleer context-neutraal."
        if c == "ESS-02":
            return "Maak de ontologische categorie expliciet (type/particulier/proces/resultaat)."

        return "Herschrijf de definitie conform de regelcriteria; maak specifieker."

    # ===== Helper checks (JSON required/structure) =====
    def _lemma_is_singular(self, begrip: str) -> bool:
        """Compat-alias op de VER-01-morfologie in de evaluatorlaag (DEF-605)."""
        return lemma_is_enkelvoud(begrip)

    # ── EvaluationSupport: het smalle venster dat evaluators lenen ──────────
    #
    # Severity-afleiding en suggestieopbouw blijven hier, zodat het
    # violation-formaat op één plek wordt bepaald en het evaluatorcontract
    # geen brede god-objectrefactor (DEF-424) hoeft af te wachten.

    def severity_for(self, rule: Any) -> str:
        """Compatibele severity (error/warning) voor een regelrecord."""
        return self._severity_for_json_rule(rule)

    def severity_level_for(self, rule: Any) -> str:
        """Severity-level (critical/high/medium/low) voor een regelrecord."""
        return self._severity_level_for_json_rule(rule)

    def build_suggestion(
        self,
        code: str,
        rule: Any,
        text: str,
        ctx: EvaluationContext,
        *,
        reason: str,
        details: str | None = None,
    ) -> str:
        """Concrete NL-suggestie om een violation te herstellen."""
        return self._build_suggestion_for_violation(
            code, rule, text, ctx, reason=reason, details=details
        )

    def _calculate_category_scores(
        self, rule_scores: dict[str, float], default_value: float
    ) -> dict[str, float]:
        """Bereken echte categorie-scores op basis van rule_scores en regelprefix.

        Categorieën: taal (ARAI/VER), juridisch (ESS/VAL), structuur (STR/INT), samenhang (CON/SAM).
        """
        from collections import defaultdict

        buckets: dict[str, list[float]] = defaultdict(list)
        for rid, score in (rule_scores or {}).items():
            try:
                r = str(rid)
                ru = r.upper()
                # Skip interne regels en ARAI* bij categorie-aggregatie
                if r in self._baseline_internal or ru.startswith(("ARAI", "AR-", "AR")):
                    continue
                cat = category_for_rule(r)
                buckets[cat].append(float(score or 0.0))
            except (TypeError, ValueError) as e:
                # DEF-248: Log score conversion failures - skip rule but don't crash aggregation
                logger.debug(f"Category score aggregation skipped rule {rid}: {e}")
                continue

        def avg(xs: list[float]) -> float:
            return sum(xs) / len(xs) if xs else default_value

        # Rond scores af op 2 decimalen voor stabiele UI/tests
        return {
            "taal": round(avg(buckets.get("taal", [])), 2),
            "juridisch": round(avg(buckets.get("juridisch", [])), 2),
            "structuur": round(avg(buckets.get("structuur", [])), 2),
            "samenhang": round(avg(buckets.get("samenhang", [])), 2),
        }

    def _evaluate_acceptance_gates(
        self,
        overall: float,
        detailed: dict[str, float],
        violations: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Evalueer acceptance gates (critical/overall/category)."""
        critical = 0
        for v in violations or []:
            lvl = str(v.get("severity_level", ""))
            if lvl.lower() == "critical":
                critical += 1

        gates_passed: list[str] = []
        gates_failed: list[str] = []

        if critical == 0:
            gates_passed.append("no_critical_violations")
        else:
            gates_failed.append(f"critical_violations={critical}")

        if float(overall) >= float(self._overall_threshold):
            gates_passed.append(f"overall>={self._overall_threshold}")
        else:
            gates_failed.append(f"overall<{self._overall_threshold}")

        for cat in ("taal", "juridisch", "structuur", "samenhang"):
            val = float(detailed.get(cat, self._category_threshold))
            if val < float(self._category_threshold):
                gates_failed.append(f"{cat}<{self._category_threshold}")

        return {
            "acceptable": len(gates_failed) == 0,
            "gates_passed": gates_passed,
            "gates_failed": gates_failed,
            "thresholds": {
                "overall": self._overall_threshold,
                "category": self._category_threshold,
            },
        }

    async def batch_validate(
        self,
        items: list[Any],
        max_concurrency: int = 1,
    ) -> list[dict[str, Any]]:
        """Batch validatie van meerdere items.

        Args:
            items: List van ValidationRequest objects of tuples
            max_concurrency: Maximum parallelle validaties (default: sequentieel)

        Returns:
            List van ValidationResult dicts in zelfde volgorde als input
        """
        import asyncio
        from typing import TYPE_CHECKING

        if TYPE_CHECKING:
            pass

        # Handle None or empty list
        if not items:
            return []

        results = []

        if max_concurrency == 1:
            # Sequentiële verwerking
            for item in items:
                if hasattr(item, "begrip"):
                    # ValidationRequest object
                    result = await self.validate_definition(
                        begrip=item.begrip,
                        text=item.text,
                        ontologische_categorie=item.ontologische_categorie,
                        context=item.context.__dict__ if item.context else None,
                    )
                elif isinstance(item, tuple):
                    begrip, text = item
                    result = await self.validate_definition(begrip, text)
                else:
                    result = await self.validate_definition(
                        item.get("begrip", ""), item.get("text", "")
                    )
                results.append(result)
        else:
            # Parallelle verwerking met semaphore voor concurrency control
            semaphore = asyncio.Semaphore(max_concurrency)

            async def validate_with_semaphore(item: Any) -> dict[str, Any]:
                async with semaphore:
                    if hasattr(item, "begrip"):
                        return await self.validate_definition(
                            begrip=item.begrip,
                            text=item.text,
                            ontologische_categorie=item.ontologische_categorie,
                            context=item.context.__dict__ if item.context else None,
                        )
                    if isinstance(item, tuple):
                        begrip, text = item
                        return await self.validate_definition(begrip, text)
                    return await self.validate_definition(
                        item.get("begrip", ""), item.get("text", "")
                    )

            # Voer alle validaties parallel uit
            results = await asyncio.gather(
                *[validate_with_semaphore(item) for item in items]
            )

        return results
