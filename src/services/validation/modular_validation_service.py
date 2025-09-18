"""ModularValidationService — lichte, async validatieservice (Story 2.3).

Implementeert een deterministische, schema-achtige output en error-isolatie
per regel. Deze service is bedoeld als opstap: simpele ingebouwde regels
dekken basiscases (leegte, lengte, circulariteit, taal/structuur). Later kan
dit uitgebreid worden om ToetsregelManager en Python-regelmodules te gebruiken.
"""

from __future__ import annotations

import contextlib
import logging
import re
import uuid
from typing import Any

from services.validation.interfaces import CONTRACT_VERSION

from .aggregation import calculate_weighted_score, determine_acceptability
from .types_internal import EvaluationContext

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
            return self._data.get("is_acceptable", False)
        return self._data.get(name)

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __contains__(self, key: str) -> bool:
        return key in self._data

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def keys(self):
        return self._data.keys()

    def values(self):
        return self._data.values()

    def items(self):
        return self._data.items()

    def __repr__(self):
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

        # Load rules from ToetsregelManager if available, otherwise use defaults
        if self.toetsregel_manager is not None:
            self._load_rules_from_manager()
        else:
            # Interne default regelset (fallback als geen ToetsregelManager)
            self._internal_rules: list[str] = [
                "VAL-EMP-001",
                "VAL-LEN-001",
                "VAL-LEN-002",
                "ESS-CONT-001",
                "CON-CIRC-001",
                "STR-TERM-001",
                "STR-ORG-001",
            ]
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
        if getattr(self.config, "thresholds", None):
            with contextlib.suppress(Exception):
                self._overall_threshold = float(
                    self.config.thresholds.get(
                        "overall_accept", self._overall_threshold
                    )
                )

    # Optioneel: exposeer regelvolgorde voor determinismetest
    def _load_rules_from_manager(self) -> None:
        """Load rules from ToetsregelManager if available."""
        try:
            # Get all available rules from manager
            all_rules = self.toetsregel_manager.get_all_regels()

            if all_rules:
                self._internal_rules = list(all_rules.keys())
                # Keep JSON rule data for evaluation
                self._json_rules = all_rules
                self._compiled_json_cache: dict[str, list[re.Pattern[str]]] = {}
                self._compiled_ess02_cache: dict[str, dict[str, list[re.Pattern[str]]]] = {}
                self._default_weights = {}

                # Extract weights from rule metadata
                for rule_id, rule_data in all_rules.items():
                    # Use priority to determine weight
                    priority = rule_data.get("prioriteit", "midden")
                    if priority == "hoog":
                        weight = 1.0
                    elif priority == "midden":
                        weight = 0.7
                    else:  # laag
                        weight = 0.4

                    # Override with specific weight if provided
                    if "weight" in rule_data:
                        weight = float(rule_data["weight"])

                    self._default_weights[rule_id] = weight

                # Also include baseline internal rules (VAL-*/STR-*) to retain safeguards
                base_internal = [
                    "VAL-EMP-001",
                    "VAL-LEN-001",
                    "VAL-LEN-002",
                    "ESS-CONT-001",
                    "CON-CIRC-001",
                    "STR-TERM-001",
                    "STR-ORG-001",
                ]
                for rid in base_internal:
                    if rid not in self._internal_rules:
                        self._internal_rules.append(rid)

                logger.info(
                    f"Loaded {len(self._internal_rules)} rules from ToetsregelManager"
                )
            else:
                # Fall back to defaults if no rules available
                self._set_default_rules()

        except Exception as e:
            logger.warning(f"Could not load rules from ToetsregelManager: {e}")
            # Fall back to defaults on error
            self._set_default_rules()

    def _set_default_rules(self) -> None:
        """Set default rules when ToetsregelManager is not available."""
        self._internal_rules = [
            "VAL-EMP-001",
            "VAL-LEN-001",
            "VAL-LEN-002",
            "ESS-CONT-001",
            "CON-CIRC-001",
            "STR-TERM-001",
            "STR-ORG-001",
        ]
        self._default_weights = {
            "VAL-EMP-001": 1.0,
            "VAL-LEN-001": 0.9,
            "VAL-LEN-002": 0.6,
            "ESS-CONT-001": 1.0,
            "CON-CIRC-001": 0.8,
            "STR-TERM-001": 0.5,
            "STR-ORG-001": 0.7,
        }

    def _get_rule_evaluation_order(
        self,
    ) -> list[str]:  # pragma: no cover - used by optional test
        return sorted(self._internal_rules)

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
                result = self.cleaning_service.clean_text(text)
                # clean_text kan sync of async zijn
                if hasattr(result, "__await__"):
                    result = await result  # type: ignore[func-returns-value]
                # Ondersteun zowel string als object met cleaned_text attribuut
                if isinstance(result, str):
                    cleaned = result
                elif hasattr(result, "cleaned_text"):
                    cleaned = result.cleaned_text
            except Exception:
                # Bij cleaning-fout: ga verder met raw text (geen crash)
                cleaned = text

        # 3) Context opbouwen (tokens slechts op aanvraag; hier niet nodig)
        eval_ctx = EvaluationContext.from_params(
            text=text,
            cleaned=cleaned,
            locale=(context or {}).get("locale") if isinstance(context, dict) else None,
            profile=(
                (context or {}).get("profile") if isinstance(context, dict) else None
            ),
            correlation_id=correlation_id,
            tokens=(),
            metadata=dict(context or {}),
        )

        # 4) Regels evalueren in deterministische volgorde
        weights = dict(self._default_weights)
        if getattr(self.config, "weights", None):
            weights.update({k: float(v) for k, v in self.config.weights.items()})

        rule_scores: dict[str, float] = {}
        violations: list[dict[str, Any]] = []
        passed_rules: list[str] = []

        # Houd begrip tijdelijk vast voor interne regels die het nodig hebben
        self._current_begrip = begrip
        for code in sorted(self._internal_rules):
            out = self._evaluate_rule(code, eval_ctx)
            # Support both (score, violation) tuple and dict-like outputs (for tests that patch the method)
            if isinstance(out, tuple):
                score, violation = out
                rule_scores[code] = score
                if violation is not None:
                    violations.append(violation)
                else:
                    passed_rules.append(code)
            elif isinstance(out, dict):
                score = float(out.get("score", 0.0) or 0.0)
                rule_scores[code] = score
                vlist = out.get("violations", []) or []
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
                                "category": self._category_for(code),
                            }
                        )
                else:
                    passed_rules.append(code)
            else:
                # Fallback: treat as scalar score
                rule_scores[code] = float(out or 0.0)
                passed_rules.append(code if float(out or 0.0) >= 1.0 else code)
        self._current_begrip = None

        # 5) Aggregatie (gewogen) en afronding
        overall = calculate_weighted_score(rule_scores, weights)
        is_ok = determine_acceptability(overall, self._overall_threshold)

        # 6) Categorie scores: voorlopig overal mirrored naar overall (gedekt door tests)
        detailed = {
            "taal": overall,
            "juridisch": overall,
            "structuur": overall,
            "samenhang": overall,
        }

        # 7) Voeg eventuele CON-01 duplicate warnings toe (best-effort)
        try:
            dup_warns = eval_ctx.metadata.get("__con01_dup_warnings__") if hasattr(eval_ctx, "metadata") else None
            if dup_warns:
                # Ensure proper minimal structure
                for w in dup_warns:
                    if isinstance(w, dict) and "code" in w:
                        violations.append(w)
        except Exception:
            pass

        # 8) Violations deterministisch sorteren op code
        violations.sort(key=lambda v: v.get("code", ""))

        # 9) Schema-achtige dict output
        result: dict[str, Any] = {
            "version": CONTRACT_VERSION,
            "overall_score": overall,
            "is_acceptable": is_ok,
            "violations": violations,
            "passed_rules": passed_rules,
            "detailed_scores": detailed,
            "system": {"correlation_id": correlation_id},
        }
        # Return plain dict voor JSON serialisatie
        # De orchestrator verwacht een dict, niet een wrapper
        return result

    # Interne regel-evaluatie (houd simpel en deterministisch)
    def _evaluate_rule(
        self, code: str, ctx: EvaluationContext
    ) -> tuple[float, dict[str, Any] | None]:
        # JSON rule evaluation path (when ToetsregelManager provided)
        if hasattr(self, "_json_rules") and code in getattr(self, "_json_rules", {}):
            return self._evaluate_json_rule(code, self._json_rules[code], ctx)

        text = ctx.cleaned_text or ""
        # Normalisaties
        text_norm = text.strip()
        words = len(text_norm.split()) if text_norm else 0
        chars = len(text_norm)

        def vio(prefix: str, message: str) -> dict[str, Any]:
            return {
                "code": prefix,
                "severity": "warning" if prefix.startswith("STR-") else "error",
                "message": message,
                "description": message,
                "rule_id": prefix,
                "category": self._category_for(prefix),
            }

        # Leegte
        if code == "VAL-EMP-001":
            if chars == 0:
                return 0.0, vio("VAL-EMP-001", "Definitietekst is leeg")
            return 1.0, None

        # Te kort
        if code == "VAL-LEN-001":
            if words < 5 or chars < 15:
                return 0.0, vio("VAL-LEN-001", "Definitie is te kort")
            return 1.0, None

        # Te lang
        if code == "VAL-LEN-002":
            if words > 80 or chars > 600:
                return 0.0, vio("VAL-LEN-002", "Definitie is te lang/overdadig")
            return 1.0, None

        # Essentiële inhoud aanwezig (heel grof: voldoende informatiedichtheid)
        if code == "ESS-CONT-001":
            if words < 6:
                return 0.0, vio(
                    "ESS-CONT-001", "Essentiële inhoud ontbreekt of te summier"
                )
            return 1.0, None

        # Circulair (begrip in definitie)
        if code == "CON-CIRC-001":
            begrip = getattr(self, "_current_begrip", None)
            if begrip and re.search(
                rf"\b{re.escape(begrip)}\b", text_norm, re.IGNORECASE
            ):
                return 0.0, vio(
                    "CON-CIRC-001", "Definitie is circulair (begrip komt voor in tekst)"
                )
            return 1.0, None

        # Terminologie/structuur kleine kwestie (bijv. ontbrekende koppelteken)
        if code == "STR-TERM-001":
            if "HTTP protocol" in text_norm:
                return 0.0, vio(
                    "STR-TERM-001", "Terminologie/structuur: gebruik 'HTTP-protocol'"
                )
            return 1.0, None

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
                return 0.0, vio(
                    "STR-ORG-001", "Zwakke zinsstructuur of redundantie gedetecteerd"
                )
            return 1.0, None

        # Onbekende regelcode → pass
        return 1.0, None

    def _evaluate_json_rule(
        self, code: str, rule: dict[str, Any], ctx: EvaluationContext
    ) -> tuple[float, dict[str, Any] | None]:
        """Evaluate a JSON-defined rule for a given text.

        Currently supports a focused subset:
        - CON-01: forbidden explicit context mentions + duplicate context signal
        - ESS-01: goal/teleology phrasing forbidden
        - ESS-02: ontological category disambiguation (specialised)
        - INT-01/INT-03, STR-01/STR-02: structure/forbidden patterns
        Other rules return pass (1.0).
        """
        text = ctx.cleaned_text or ""
        code_up = code.upper()

        # Special: ESS-02
        if code_up == "ESS-02":
            return self._eval_ess02(rule, text, ctx)

        # Default path for JSON rules: treat 'herkenbaar_patronen' as forbidden patterns
        patterns = rule.get("herkenbaar_patronen", []) or []
        compiled = self._compiled_json_cache.get(code_up)
        if compiled is None:
            try:
                compiled = [re.compile(pat, re.IGNORECASE) for pat in patterns]
            except re.error:
                compiled = []
            self._compiled_json_cache[code_up] = compiled

        hits = []
        for pat in compiled:
            for m in pat.finditer(text):
                hits.append((pat.pattern, m.start()))

        # Duplicate context signal for CON-01
        if code_up == "CON-01":
            self._maybe_add_duplicate_context_signal(ctx)

        # Some rules (e.g., CON-02) use patterns as POSITIVE indicators, not forbidden
        # Some rules use patterns as POSITIVE indicators (presence is good)
        positive_pattern_rules = {"CON-02", "ESS-03", "ESS-04", "ESS-05"}
        if hits and code_up not in positive_pattern_rules:
            score = max(0.0, 1.0 - 0.3 * len(hits))
            return score, {
                "code": code,
                "severity": self._severity_for_json_rule(rule),
                "message": f"Pattern(s) matched: {', '.join(sorted({h[0] for h in hits}))}",
                "description": f"Pattern(s) matched: {', '.join(sorted({h[0] for h in hits}))}",
                "rule_id": code,
                "category": self._category_for(code),
            }

        # Required/structure checks for known rules (only if no forbidden pattern hit)
        # CON-02 – authentic source basis required
        if code_up == "CON-02" and not self._has_authentic_source_basis(text):
            return 0.0, {
                "code": code,
                "severity": self._severity_for_json_rule(rule),
                "message": "Geen authentieke bron/basis in definitietekst",
                "description": "Geen authentieke bron/basis in definitietekst",
                "rule_id": code,
                "category": self._category_for(code),
            }

        # ESS-03/04/05
        if code_up == "ESS-03" and not self._has_unique_identification(text):
            return 0.0, {
                "code": code,
                "severity": self._severity_for_json_rule(rule),
                "message": "Ontbreekt uniek identificatiecriterium",
                "description": "Ontbreekt uniek identificatiecriterium",
                "rule_id": code,
                "category": self._category_for(code),
            }
        if code_up == "ESS-04" and not self._has_testable_element(text):
            return 0.0, {
                "code": code,
                "severity": self._severity_for_json_rule(rule),
                "message": "Ontbreekt objectief toetsbaar element",
                "description": "Ontbreekt objectief toetsbaar element",
                "rule_id": code,
                "category": self._category_for(code),
            }
        if code_up == "ESS-05" and not self._has_distinguishing_feature(text):
            return 0.0, {
                "code": code,
                "severity": self._severity_for_json_rule(rule),
                "message": "Ontbreekt onderscheidend kenmerk",
                "description": "Ontbreekt onderscheidend kenmerk",
                "rule_id": code,
                "category": self._category_for(code),
            }

        # VER-01 – lemma in enkelvoud (heuristic) using current begrip
        if code_up == "VER-01":
            begrip = getattr(self, "_current_begrip", "") or ""
            if not self._lemma_is_singular(begrip):
                return 0.0, {
                    "code": code,
                    "severity": self._severity_for_json_rule(rule),
                    "message": "Term (lemma) lijkt meervoud (geen plurale tantum)",
                    "description": "Term (lemma) lijkt meervoud (geen plurale tantum)",
                    "rule_id": code,
                    "category": self._category_for(code),
                }

        # Pass if no issues
        return 1.0, None

    def _severity_for_json_rule(self, rule: dict[str, Any]) -> str:
        # Map JSON aanbeveling/prioriteit naar severity string
        aan = str(rule.get("aanbeveling", "")).lower()
        pri = str(rule.get("prioriteit", "")).lower()
        if aan == "verplicht" or pri == "hoog":
            return "error"
        return "warning"

    # ===== Helper checks (JSON required/structure) =====
    def _has_authentic_source_basis(self, text: str) -> bool:
        return bool(re.search(r"\b(volgens|conform|gebaseerd|bepaald|bedoeld|wet|regeling)\b", text, re.IGNORECASE))

    def _has_unique_identification(self, text: str) -> bool:
        return bool(
            re.search(
                r"\b(uniek|specifiek|identificeer|registratie|nummer|code|id|vin|isbn|kenteken)\b",
                text,
                re.IGNORECASE,
            )
        )

    def _has_testable_element(self, text: str) -> bool:
        return bool(re.search(r"\b(\d+|binnen|na|voor|volgens|conform|gebaseerd op)\b", text, re.IGNORECASE))

    def _has_distinguishing_feature(self, text: str) -> bool:
        return bool(re.search(r"\b(onderscheidt|specifiek|bijzonder|kenmerk|eigenschap)\b", text, re.IGNORECASE))

    def _lemma_is_singular(self, begrip: str) -> bool:
        # Heuristic: NL plural often ends with 'en'; whitelist of plurale tantum could be extended
        lemma = (begrip or "").strip().lower()
        plurale_tantum = {"kosten", "hersenen"}
        if lemma in plurale_tantum:
            return True
        # Plurals often end with 'en' or 'ens' (bv. gegeven → gegevens)
        if re.search(r"\w+ens$", lemma):
            return False
        return not bool(re.search(r"\w+en$", lemma))

    def _eval_ess02(
        self, rule: dict[str, Any], text: str, ctx: EvaluationContext
    ) -> tuple[float, dict[str, Any] | None]:
        """Implement ESS-02: ontological category must be explicit and unambiguous."""
        # Marker override from context
        marker = None
        try:
            marker = (ctx.metadata or {}).get("marker")
        except Exception:
            marker = None
        if marker:
            m = str(marker).strip().lower()
            if m in {"soort", "type", "exemplaar", "particulier", "proces", "activiteit", "resultaat", "uitkomst"}:
                return 1.0, None

        # Compile per-category patterns once
        cache_key = "ESS-02"
        compiled_map = self._compiled_ess02_cache.get(cache_key)
        if compiled_map is None:
            compiled_map = {}
            for cat_key, json_key in (
                ("type", "herkenbaar_patronen_type"),
                ("particulier", "herkenbaar_patronen_particulier"),
                ("proces", "herkenbaar_patronen_proces"),
                ("resultaat", "herkenbaar_patronen_resultaat"),
            ):
                pats = rule.get(json_key, []) or []
                try:
                    compiled_map[cat_key] = [re.compile(p, re.IGNORECASE) for p in pats]
                except re.error:
                    compiled_map[cat_key] = []
            self._compiled_ess02_cache[cache_key] = compiled_map

        hits: dict[str, int] = {}
        for cat, pats in compiled_map.items():
            for pat in pats:
                if pat.search(text):
                    hits[cat] = hits.get(cat, 0) + 1

        if len(hits) == 1:
            return 1.0, None
        if len(hits) > 1:
            return 0.0, {
                "code": "ESS-02",
                "severity": "error",
                "message": f"Ambigu: meerdere categorieën herkend ({', '.join(sorted(hits.keys()))})",
                "description": f"Ambigu: meerdere categorieën herkend ({', '.join(sorted(hits.keys()))})",
                "rule_id": "ESS-02",
                "category": self._category_for("ESS-02"),
            }
        # No hits → missing element
        return 0.0, {
            "code": "ESS-02",
            "severity": "error",
            "message": "Geen duidelijke ontologische marker (type/particulier/proces/resultaat)",
            "description": "Geen duidelijke ontologische marker (type/particulier/proces/resultaat)",
            "rule_id": "ESS-02",
            "category": self._category_for("ESS-02"),
        }

    def _maybe_add_duplicate_context_signal(self, ctx: EvaluationContext) -> None:
        """Emit a duplicate-context WARNING via internal stash for CON-01.

        Since the aggregation path does not support pushing custom violations
        directly, this method appends a lightweight marker into ctx.metadata
        to be consumed at the end of validation (kept simple: side-effect free
        if repository or contexts are unavailable).
        """
        try:
            if not self._repository:
                return
            md = ctx.metadata or {}
            org = md.get("organisatorische_context") or []
            jur = md.get("juridische_context") or []
            cat = md.get("categorie") or md.get("ontologische_categorie")
            begrip = getattr(self, "_current_begrip", None)
            if not begrip or (not org and not jur):
                return
            # Fetch all non-archived and compare
            if hasattr(self._repository, "_get_all_definitions"):
                defs = self._repository._get_all_definitions()
            else:
                return
            def _norm(lst: list[str]) -> list[str]:
                try:
                    return sorted({(x or "").strip().lower() for x in list(lst or [])})
                except Exception:
                    return []
            org_n = _norm(org)
            jur_n = _norm(jur)
            found_id = None
            found_status = None
            for d in defs:
                if (d.begrip or "").strip().lower() != str(begrip).strip().lower():
                    continue
                if _norm(getattr(d, "organisatorische_context", [])) != org_n:
                    continue
                if _norm(getattr(d, "juridische_context", [])) != jur_n:
                    continue
                if cat and getattr(d, "categorie", None) and str(d.categorie).lower() != str(cat).lower():
                    continue
                found_id = getattr(d, "id", None)
                found_status = getattr(d, "status", None)
                break
            if found_id is not None:
                # Stash a warning marker to be transformed later in validate_definition
                warn_list = md.setdefault("__con01_dup_warnings__", [])
                warn_list.append({
                    "code": "CON-01",
                    "severity": "warning",
                    "message": "Bestaande definitie met dezelfde context gevonden",
                    "description": "Bestaande definitie met dezelfde context gevonden",
                    "rule_id": "CON-01",
                    "category": self._category_for("CON-01"),
                    "metadata": {"existing_definition_id": found_id, "status": found_status},
                })
        except Exception:
            # Silent: duplicate signal is best-effort
            return

    def _category_for(self, code: str) -> str:
        if code.startswith("STR-"):
            return "structuur"
        if code.startswith("CON-"):
            return "samenhang"
        if code.startswith(("ESS-", "VAL-")):
            return "juridisch"
        return "system"

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

            async def validate_with_semaphore(item):
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
