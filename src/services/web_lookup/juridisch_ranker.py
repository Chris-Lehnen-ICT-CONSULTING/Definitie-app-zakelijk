"""
Context-aware ranking voor juridische begrippen.

Deze module boost resultaten die juridische keywords bevatten en
prioriteert juridische bronnen (rechtspraak.nl, wetgeving.nl) boven
algemene bronnen (Wikipedia).

Gebruik:
    from .juridisch_ranker import boost_juridische_resultaten

    results = await wikipedia_lookup("voorlopige hechtenis")
    boosted = boost_juridische_resultaten(results, context=["Sv", "strafrecht"])
"""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from services.web_lookup.modern_web_lookup import LookupResult

try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    print(
        "Warning: PyYAML niet beschikbaar - juridisch ranker werkt met fallback keywords"
    )

logger = logging.getLogger(__name__)


class JuridischRankerConfig:
    """
    Configuration manager voor juridisch ranker.

    Laadt keywords en boost factoren uit YAML configuratie bestanden.
    Gebruikt singleton pattern voor hergebruik.
    """

    def __init__(
        self,
        keywords_path: str | None = None,
        defaults_path: str | None = None,
    ):
        """
        Initialiseer ranker config.

        Args:
            keywords_path: Pad naar juridische_keywords.yaml (optioneel)
            defaults_path: Pad naar web_lookup_defaults.yaml (optioneel)
        """
        # Bepaal config paden
        if keywords_path:
            self.keywords_path = Path(keywords_path)
        else:
            # Zoek config relatief aan project root
            current = Path(__file__).parent.parent.parent.parent
            self.keywords_path = current / "config" / "juridische_keywords.yaml"

        if defaults_path:
            self.defaults_path = Path(defaults_path)
        else:
            current = Path(__file__).parent.parent.parent.parent
            self.defaults_path = current / "config" / "web_lookup_defaults.yaml"

        # Keywords database (normalized)
        self.keywords: set[str] = set()

        # Boost factors (values can be float or dict for nested config like quality_gate)
        self.boost_factors: dict[str, float | dict[str, Any]] = {
            "juridische_bron": 1.2,
            "keyword_per_match": 1.1,
            "keyword_max_boost": 1.3,
            "artikel_referentie": 1.15,
            "lid_referentie": 1.05,
            "context_match": 1.1,
            "context_max_boost": 1.3,
            "juridical_flag": 1.15,
        }

        # Load configuratie
        self._load_keywords()
        self._load_boost_factors()

        logger.info(
            f"Juridisch ranker config geïnitialiseerd: "
            f"{len(self.keywords)} keywords, {len(self.boost_factors)} boost factors"
        )

    def _normalize_term(self, term: str) -> str:
        """
        Normaliseer term voor consistente lookup.

        Conversies:
        - Lowercase
        - Strip whitespace
        - Vervang underscores met spaties
        """
        return term.lower().strip().replace("_", " ")

    def _load_keywords(self) -> None:
        """
        Laad juridische keywords uit YAML config.

        YAML format:
            categorie:
              - keyword1
              - keyword2
        """
        if not YAML_AVAILABLE:
            logger.warning("PyYAML niet beschikbaar - gebruik fallback keywords")
            self._load_fallback_keywords()
            return

        if not self.keywords_path.exists():
            logger.warning(
                f"Keywords config niet gevonden: {self.keywords_path}. "
                f"Gebruik fallback keywords."
            )
            self._load_fallback_keywords()
            return

        try:
            with open(self.keywords_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not data:
                logger.warning("Lege keywords config - gebruik fallback")
                self._load_fallback_keywords()
                return

            # Extract keywords uit alle categorieën
            for _category, keywords_list in data.items():
                # Skip comments/metadata
                if not isinstance(keywords_list, list):
                    continue

                # Normaliseer en voeg toe
                for keyword in keywords_list:
                    if isinstance(keyword, str):
                        normalized = self._normalize_term(keyword)
                        if normalized:
                            self.keywords.add(normalized)

            logger.info(
                f"Geladen: {len(self.keywords)} juridische keywords "
                f"uit {self.keywords_path}"
            )

        except yaml.YAMLError as e:
            logger.error(f"YAML parse error in {self.keywords_path}: {e}")
            self._load_fallback_keywords()
        except Exception as e:
            logger.error(f"Fout bij laden keywords uit {self.keywords_path}: {e}")
            self._load_fallback_keywords()

    def _load_fallback_keywords(self) -> None:
        """
        Laad hardcoded fallback keywords (voor backwards compatibility).
        """
        self.keywords = {
            # Algemeen juridisch
            "wetboek",
            "artikel",
            "wet",
            "recht",
            "rechter",
            "vonnis",
            "uitspraak",
            "rechtspraak",
            "juridisch",
            "wettelijk",
            "strafbaar",
            "rechtbank",
            "gerechtshof",
            "hoge raad",
            # Strafrecht
            "strafrecht",
            "verdachte",
            "beklaagde",
            "dagvaarding",
            "veroordeling",
            "vrijspraak",
            "schuldig",
            "delict",
            "misdrijf",
            "overtreding",
            # Burgerlijk recht
            "burgerlijk",
            "civiel",
            "overeenkomst",
            "contract",
            "schadevergoeding",
            "aansprakelijkheid",
            # Bestuursrecht
            "bestuursrecht",
            "beschikking",
            "besluit",
            "bezwaar",
            "beroep",
            "awb",
            # Procesrecht
            "procedure",
            "proces",
            "hoger beroep",
            "cassatie",
            "appel",
            # Wetten
            "sr",
            "sv",
            "rv",
            "bw",
        }
        logger.info(f"Geladen: {len(self.keywords)} fallback keywords")

    def _load_boost_factors(self) -> None:
        """
        Laad boost factoren uit web_lookup_defaults.yaml.
        """
        if not YAML_AVAILABLE:
            logger.warning("PyYAML niet beschikbaar - gebruik default boost factors")
            return

        if not self.defaults_path.exists():
            logger.warning(
                f"Defaults config niet gevonden: {self.defaults_path}. "
                f"Gebruik default boost factors."
            )
            return

        try:
            with open(self.defaults_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not data or "web_lookup" not in data:
                logger.warning("web_lookup sectie niet gevonden in defaults")
                return

            web_lookup = data["web_lookup"]
            if "juridical_boost" not in web_lookup:
                logger.warning("juridical_boost sectie niet gevonden")
                return

            # Update boost factors
            boost_config = web_lookup["juridical_boost"]
            for key, value in boost_config.items():
                # Store nested dicts directly (e.g., quality_gate)
                if isinstance(value, dict):
                    self.boost_factors[key] = value
                # Convert scalar values to float and update if key exists
                elif key in self.boost_factors:
                    self.boost_factors[key] = float(value)

            logger.info(
                f"Geladen boost factors uit {self.defaults_path}: "
                f"{self.boost_factors}"
            )

        except yaml.YAMLError as e:
            logger.error(f"YAML parse error in {self.defaults_path}: {e}")
        except Exception as e:
            logger.error(f"Fout bij laden boost factors uit {self.defaults_path}: {e}")


# Module-level singleton
_config_singleton: JuridischRankerConfig | None = None


def get_ranker_config(
    keywords_path: str | None = None,
    defaults_path: str | None = None,
) -> JuridischRankerConfig:
    """
    Haal singleton ranker config op.

    Args:
        keywords_path: Optioneel custom keywords config pad
        defaults_path: Optioneel custom defaults config pad

    Returns:
        JuridischRankerConfig instance
    """
    global _config_singleton

    # Check voor env var override
    env_keywords_path = os.getenv("JURIDISCH_KEYWORDS_CONFIG")
    env_defaults_path = os.getenv("WEB_LOOKUP_CONFIG")

    if env_keywords_path:
        keywords_path = env_keywords_path
    if env_defaults_path:
        defaults_path = env_defaults_path

    # Hergebruik singleton tenzij custom paden opgegeven
    if _config_singleton is None or keywords_path or defaults_path:
        _config_singleton = JuridischRankerConfig(keywords_path, defaults_path)

    return _config_singleton


# Backward compatibility: expose keywords as module-level variable
# This is loaded lazily when first accessed to maintain backwards compatibility
# DEPRECATED: Direct use of JURIDISCHE_KEYWORDS is deprecated, use get_ranker_config().keywords
_keywords_cache: set[str] | None = None


def _get_legacy_keywords() -> set[str]:
    """
    Helper: Haal keywords op voor legacy JURIDISCHE_KEYWORDS constant.

    Returns cached keywords to avoid reloading config on every access.
    """
    global _keywords_cache
    if _keywords_cache is None:
        _keywords_cache = get_ranker_config().keywords
    return _keywords_cache


# Create a module-level set that acts like the old JURIDISCHE_KEYWORDS constant
# This maintains backwards compatibility for code that does: "keyword in JURIDISCHE_KEYWORDS"
class _KeywordsProxy:
    """Proxy class to make JURIDISCHE_KEYWORDS behave like a set."""

    def __contains__(self, item):
        return item in _get_legacy_keywords()

    def __iter__(self):
        return iter(_get_legacy_keywords())

    def __len__(self):
        return len(_get_legacy_keywords())

    def __repr__(self):
        return repr(_get_legacy_keywords())


JURIDISCHE_KEYWORDS = _KeywordsProxy()

# Juridische domeinen voor URL filtering
JURIDISCHE_DOMEINEN = {
    "rechtspraak.nl",
    "overheid.nl",
    "wetgeving.nl",
    "wetten.overheid.nl",
    "officielebekendmakingen.nl",
    "zoekservice.overheid.nl",
    "repository.overheid.nl",
    "data.rechtspraak.nl",
}

# Regex voor artikel-referenties (Art. 123, Artikel 12a)
ARTIKEL_PATTERN = re.compile(r"\b(?:artikel|art\.?)\s+(\d+[a-z]?)\b", re.IGNORECASE)

# Regex voor lid-referenties (lid 2, tweede lid)
LID_PATTERN = re.compile(
    r"\b(?:lid|eerste|tweede|derde|vierde|vijfde)\s+(?:lid\s+)?(\d+|eerste|tweede|derde|vierde|vijfde)\b",
    re.IGNORECASE,
)


def is_juridische_bron(url: str) -> bool:
    """
    Check of een URL van een juridische bron komt.

    Args:
        url: URL om te checken

    Returns:
        True als URL van juridische bron, anders False
    """
    if not url:
        return False

    url_lower = url.lower()
    return any(domein in url_lower for domein in JURIDISCHE_DOMEINEN)


def count_juridische_keywords(text: str) -> int:
    """
    Tel aantal juridische keywords in tekst.

    Args:
        text: Tekst om te analyseren

    Returns:
        Aantal unieke juridische keywords gevonden
    """
    if not text:
        return 0

    text_lower = text.lower()
    count = 0

    # Haal keywords uit config
    config = get_ranker_config()
    keywords = config.keywords

    for keyword in keywords:
        # Word boundary matching om false positives te vermijden
        # "recht" moet match in "strafrecht" maar niet in "achtrecht"
        pattern = r"\b" + re.escape(keyword) + r"\b"
        if re.search(pattern, text_lower):
            count += 1

    return count


def contains_artikel_referentie(text: str) -> bool:
    """
    Check of tekst artikel-referenties bevat (Art. X).

    Args:
        text: Tekst om te checken

    Returns:
        True als artikel-referentie gevonden
    """
    if not text:
        return False

    return ARTIKEL_PATTERN.search(text) is not None


def contains_lid_referentie(text: str) -> bool:
    """
    Check of tekst lid-referenties bevat.

    Args:
        text: Tekst om te checken

    Returns:
        True als lid-referentie gevonden
    """
    if not text:
        return False

    return LID_PATTERN.search(text) is not None


def calculate_juridische_boost(
    result: LookupResult, context: list[str] | None = None
) -> float:
    """
    Bereken juridische boost factor voor een result.

    FASE 3 FIX: Quality-gated boost ensures only high-quality juridical
    sources receive full boost. This prevents low-quality juridical sources
    from outranking high-quality relevant sources.

    Quality Gate Logic:
    - If base_score >= min_base_score: Full boost applied
    - If base_score < min_base_score: Reduced boost (configurable factor)
    - Content-based boosts (keywords, artikel, lid) apply regardless of gate

    Boost factoren worden geladen uit config/web_lookup_defaults.yaml:
    - Juridische bron (rechtspraak.nl, overheid.nl): configurable (default 1.2x)
    - Juridische keywords in definitie: configurable per keyword (default 1.1x, max 1.3x)
    - Artikel-referentie in definitie: configurable (default 1.15x)
    - Lid-referentie: configurable (default 1.05x)
    - Context match (optioneel): configurable (default 1.1x, max 1.3x)
    - Quality gate: configurable threshold and reduction factor

    Args:
        result: LookupResult om te boosten
        context: Optionele context tokens (bijv. ["Sv", "strafrecht"])

    Returns:
        Boost factor (>= 1.0)
    """
    config = get_ranker_config()
    boost_factors = config.boost_factors

    # Load quality gate settings (FASE 3 FIX)
    quality_gate_config: dict[str, Any] = cast(
        dict[str, Any], boost_factors.get("quality_gate", {})
    )
    quality_gate_enabled: bool = cast(bool, quality_gate_config.get("enabled", True))
    min_base_score: float = cast(float, quality_gate_config.get("min_base_score", 0.65))
    reduced_factor: float = cast(
        float, quality_gate_config.get("reduced_boost_factor", 0.5)
    )

    # Get base score BEFORE any boosting
    base_score = float(getattr(result.source, "confidence", 0.5))

    # Determine quality multiplier for source-based boosts
    if quality_gate_enabled and base_score < min_base_score:
        # Low quality source - apply reduced boost
        quality_multiplier = reduced_factor
        logger.debug(
            f"Quality gate ACTIVE: base_score={base_score:.2f} < threshold={min_base_score:.2f}, "
            f"applying {quality_multiplier:.0%} source boost"
        )
    else:
        # High quality source OR gate disabled - apply full boost
        quality_multiplier = 1.0
        if quality_gate_enabled:
            logger.debug(
                f"Quality gate PASS: base_score={base_score:.2f} >= threshold={min_base_score:.2f}"
            )

    boost = 1.0

    # 1. Juridische bron boost (URL-based, QUALITY GATED)
    if (
        hasattr(result, "source")
        and hasattr(result.source, "url")
        and is_juridische_bron(result.source.url)
    ):
        bron_boost = cast(float, boost_factors.get("juridische_bron", 1.2))
        # Apply quality gate: interpolate between 1.0 and bron_boost
        effective_boost = 1.0 + (bron_boost - 1.0) * quality_multiplier
        boost *= effective_boost
        logger.debug(
            f"Juridische bron boost {effective_boost:.3f}x "
            f"(base={bron_boost:.2f}, gate={quality_multiplier:.2f}): {result.source.url}"
        )

    # Alternative: check source.is_juridical flag (QUALITY GATED)
    if (
        hasattr(result, "source")
        and getattr(result.source, "is_juridical", False)
        and boost == 1.0  # Alleen als niet al geboosted via URL
    ):
        flag_boost = cast(float, boost_factors.get("juridical_flag", 1.15))
        effective_boost = 1.0 + (flag_boost - 1.0) * quality_multiplier
        boost *= effective_boost
        logger.debug(
            f"Juridische flag boost {effective_boost:.3f}x "
            f"(base={flag_boost:.2f}, gate={quality_multiplier:.2f})"
        )

    # 2-5: Content-based boosts (NOT GATED - measure intrinsic relevance)
    # These apply to all sources regardless of quality gate
    definitie = getattr(result, "definition", "") or ""

    # 2. Juridische keywords in definitie
    keyword_count = count_juridische_keywords(definitie)

    if keyword_count > 0:
        # Cap bij keyword_max_boost (configurable)
        keyword_per_match = cast(float, boost_factors.get("keyword_per_match", 1.1))
        keyword_max = cast(float, boost_factors.get("keyword_max_boost", 1.3))
        keyword_boost = min(keyword_per_match**keyword_count, keyword_max)
        boost *= keyword_boost
        logger.debug(f"Keyword boost {keyword_boost:.3f}x ({keyword_count} keywords)")

    # 3. Artikel-referentie boost
    if contains_artikel_referentie(definitie):
        artikel_boost = cast(float, boost_factors.get("artikel_referentie", 1.15))
        boost *= artikel_boost
        logger.debug(f"Artikel-referentie boost {artikel_boost:.3f}x")

    # 4. Lid-referentie boost
    if contains_lid_referentie(definitie):
        lid_boost = cast(float, boost_factors.get("lid_referentie", 1.05))
        boost *= lid_boost
        logger.debug(f"Lid-referentie boost {lid_boost:.3f}x")

    # 5. Context match boost (optioneel)
    if context:
        context_lower = [c.lower() for c in context]
        definitie_lower = definitie.lower()

        # Check of context tokens voorkomen in definitie
        matches = sum(1 for c in context_lower if c in definitie_lower)

        if matches > 0:
            # context_match^matches, capped bij context_max_boost
            context_per_match = cast(float, boost_factors.get("context_match", 1.1))
            context_max = cast(float, boost_factors.get("context_max_boost", 1.3))
            context_boost = min(context_per_match**matches, context_max)
            boost *= context_boost
            logger.debug(
                f"Context match boost {context_boost:.3f}x ({matches} matches)"
            )

    logger.debug(f"Total boost factor: {boost:.3f}x (base_score={base_score:.2f})")
    return boost


def boost_juridische_resultaten(
    results: list[LookupResult], context: list[str] | None = None
) -> list[LookupResult]:
    """
    Boost confidence van juridische resultaten.

    Past calculate_juridische_boost() toe op elk result en update
    confidence score. Resultaten worden opnieuw gesorteerd op confidence.

    Args:
        results: Lijst van LookupResult objecten
        context: Optionele context tokens voor extra boosting

    Returns:
        Gesorteerde lijst van LookupResult (hoogste confidence eerst)

    Example:
        >>> results = await wikipedia_lookup("voorlopige hechtenis")
        >>> boosted = boost_juridische_resultaten(results, context=["Sv"])
        >>> # Juridische resultaten krijgen hogere confidence
    """
    if not results:
        return results

    logger.info(f"Boosting {len(results)} resultaten met juridische ranking")

    boosted_results = []

    for result in results:
        # Bereken boost factor
        boost_factor = calculate_juridische_boost(result, context)

        # Update confidence (met clipping naar [0.0, 1.0])
        original_confidence = getattr(result.source, "confidence", 0.5)
        new_confidence = min(original_confidence * boost_factor, 1.0)

        # Update result confidence
        if hasattr(result, "source"):
            result.source.confidence = new_confidence

            logger.debug(
                f"Boosted '{result.term}' from {original_confidence:.2f} to {new_confidence:.2f} "
                f"(boost: {boost_factor:.2f}x)"
            )

        boosted_results.append(result)

    # Sorteer op nieuwe confidence (hoogste eerst)
    # Null-safe: handle cases waar result.source None is
    boosted_results.sort(
        key=lambda r: getattr(r.source, "confidence", 0.0) if r.source else 0.0,
        reverse=True,
    )

    logger.info(
        f"Juridische ranking compleet: "
        f"top result confidence {boosted_results[0].source.confidence:.2f}"
    )

    return boosted_results


def get_juridische_score(result: LookupResult) -> float:
    """
    Bereken hoe 'juridisch' een result is (0.0 - 1.0).

    Gebruikt dezelfde factoren als boost_juridische_resultaten maar
    returnt een absolute score i.p.v. een multiplier.

    Args:
        result: LookupResult om te scoren

    Returns:
        Score tussen 0.0 (niet juridisch) en 1.0 (zeer juridisch)
    """
    score = 0.0

    # Juridische bron: +0.4
    if hasattr(result, "source"):
        if hasattr(result.source, "url") and is_juridische_bron(result.source.url):
            score += 0.4
        elif getattr(result.source, "is_juridical", False):
            score += 0.3

    # Juridische keywords: +0.05 per keyword (max +0.3)
    definitie = getattr(result, "definition", "") or ""
    keyword_count = count_juridische_keywords(definitie)
    score += min(keyword_count * 0.05, 0.3)

    # Artikel-referentie: +0.2
    if contains_artikel_referentie(definitie):
        score += 0.2

    # Lid-referentie: +0.1
    if contains_lid_referentie(definitie):
        score += 0.1

    # Clamp naar [0.0, 1.0]
    return min(score, 1.0)
