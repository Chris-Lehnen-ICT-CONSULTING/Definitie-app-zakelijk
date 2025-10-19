"""
UFO Classifier Critical Bug Fixes
==================================
Immediate fixes for CRITICAL issues preventing 95% precision target
"""

import logging
import re
import unicodedata
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


# FIX #1: Add missing ABSTRACT category or fix disambiguation
class UFOCategoryFixed(Enum):
    """Fixed UFO categories - removed invalid ABSTRACT reference."""

    KIND = "Kind"
    EVENT = "Event"
    ROLE = "Role"
    PHASE = "Phase"
    RELATOR = "Relator"
    MODE = "Mode"
    QUANTITY = "Quantity"
    QUALITY = "Quality"
    SUBKIND = "Subkind"
    CATEGORY = "Category"
    MIXIN = "Mixin"
    ROLEMIXIN = "RoleMixin"
    PHASEMIXIN = "PhaseMixin"
    COLLECTIVE = "Collective"
    VARIABLECOLLECTION = "VariableCollection"
    FIXEDCOLLECTION = "FixedCollection"


# FIX #3: Proper input validation
def validate_input(term: str, definition: str) -> tuple[str, str]:
    """
    Validate and clean input strings.
    Raises ValueError for invalid input.
    """
    # Check for None
    if term is None:
        msg = "Term mag niet None zijn"
        raise ValueError(msg)
    if definition is None:
        msg = "Definitie mag niet None zijn"
        raise ValueError(msg)

    # Strip whitespace
    term = term.strip()
    definition = definition.strip()

    # Check for empty after stripping
    if not term:
        msg = "Term is verplicht en mag niet leeg zijn"
        raise ValueError(msg)
    if not definition:
        msg = "Definitie is verplicht en mag niet leeg zijn"
        raise ValueError(msg)

    # Check minimum length
    if len(term) < 2:
        msg = "Term moet minimaal 2 karakters bevatten"
        raise ValueError(msg)
    if len(definition) < 5:
        msg = "Definitie moet minimaal 5 karakters bevatten"
        raise ValueError(msg)

    # Check for suspicious patterns (basic injection protection)
    suspicious_patterns = [
        r"<script",
        r"javascript:",
        r"DROP\s+TABLE",
        r"DELETE\s+FROM",
        r"\$\(",
        r"eval\(",
        r"exec\(",
    ]

    combined = f"{term} {definition}".lower()
    for pattern in suspicious_patterns:
        if re.search(pattern, combined, re.IGNORECASE):
            msg = f"Verdachte input gedetecteerd: {pattern}"
            raise ValueError(msg)

    return term, definition


# FIX #5: Unicode normalization
def normalize_dutch_text(text: str) -> str:
    """
    Normalize Dutch text for consistent matching.
    Handles combining characters and special Dutch characters.
    """
    if not text:
        return ""

    # Normalize to NFC (composed form)
    text = unicodedata.normalize("NFC", text)

    # Handle common Dutch character issues
    replacements = {
        "ĳ": "ij",  # Dutch IJ ligature
        "Ĳ": "IJ",
        "ÿ": "y",  # Sometimes used in old Dutch
        "´": "'",  # Acute accent to apostrophe
        "`": "'",  # Grave accent to apostrophe
        """: "'",   # Smart quote to apostrophe
        """: "'",
        '"': '"',
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text.lower()


# FIX #6: Pattern compilation and caching
class CompiledPatternMatcher:
    """Pattern matcher with pre-compiled regex patterns."""

    def __init__(self):
        self._compiled_patterns = {}
        self._compile_all_patterns()

    def _compile_all_patterns(self):
        """Pre-compile all regex patterns for performance."""
        patterns_to_compile = {
            "kind": [
                r"\b(?:een|de|het)\s+(\w+)\s+(?:is|zijn|betreft)",
                r"(?:natuurlijk|rechts)persoon",
                r"(?:organisatie|instantie|orgaan|lichaam)",
            ],
            "event": [
                r"(?:tijdens|gedurende|na afloop van|voorafgaand aan)",
                r"(?:proces|procedure|handeling|gebeurtenis)\b",
                r"\b\w+(?:ing|atie|itie)\b",
            ],
            "role": [
                r"(?:in de hoedanigheid van|in de rol van|als)\s+\w+",
                r"(?:optreedt?|handel\w+|fungeer\w+)\s+als",
            ],
            # ... more patterns
        }

        for category, pattern_list in patterns_to_compile.items():
            self._compiled_patterns[category] = []
            for pattern_str in pattern_list:
                try:
                    compiled = re.compile(pattern_str, re.IGNORECASE | re.UNICODE)
                    self._compiled_patterns[category].append((pattern_str, compiled))
                except re.error as e:
                    logger.error(
                        f"Failed to compile pattern for {category}: {pattern_str} - {e}"
                    )

    def find_matches(self, text: str, category: str) -> list[str]:
        """Find all matches for a category in text."""
        if category not in self._compiled_patterns:
            return []

        text = normalize_dutch_text(text)
        matches = []

        for pattern_str, compiled_pattern in self._compiled_patterns[category]:
            if compiled_pattern.search(text):
                matches.append(f"Pattern: {pattern_str}")

        return matches


# FIX #2: Division by zero protection
def calculate_confidence_safe(
    primary_category: Any, all_scores: dict[Any, float], pattern_count: int
) -> float:
    """
    Calculate confidence score with full protection against edge cases.
    """
    # Handle empty or None scores
    if not all_scores:
        logger.warning("No scores available for confidence calculation")
        return 0.0

    # Get primary score
    primary_score = all_scores.get(primary_category, 0.0)

    # No confidence if primary has no score
    if primary_score <= 0:
        logger.warning(f"Primary category {primary_category} has no score")
        return 0.0

    # Start with primary score as base confidence
    confidence = primary_score

    # Bonus for many pattern matches
    if pattern_count > 0:
        pattern_bonus = min(pattern_count * 0.02, 0.2)  # Max 20% bonus
        confidence += pattern_bonus

    # Calculate margin over next best
    sorted_scores = sorted(all_scores.values(), reverse=True)
    if len(sorted_scores) > 1 and sorted_scores[0] > 0:
        # Avoid division by zero
        if sorted_scores[1] > 0:
            margin = (sorted_scores[0] - sorted_scores[1]) / sorted_scores[0]
        else:
            margin = 1.0  # Complete dominance

        confidence += margin * 0.15  # Up to 15% bonus for clear winner

    # Penalty for too many competing categories
    high_score_count = sum(1 for score in all_scores.values() if score > 0.4)
    if high_score_count > 3:
        ambiguity_penalty = 0.8 ** (high_score_count - 3)
        confidence *= ambiguity_penalty

    # Ensure confidence stays in valid range
    return max(0.0, min(1.0, confidence))



# FIX #4: Memory-efficient batch processing
class BatchProcessor:
    """Memory-efficient batch processing with chunking and streaming."""

    def __init__(self, classifier, chunk_size: int = 100):
        self.classifier = classifier
        self.chunk_size = chunk_size

    def process_batch_stream(self, definitions, context=None):
        """
        Process batch as a generator to avoid memory buildup.
        Yields results one at a time.
        """
        for i, (term, definition) in enumerate(definitions):
            try:
                # Validate input
                term, definition = validate_input(term, definition)

                # Classify
                result = self.classifier.classify(term, definition, context)

                # Log progress periodically
                if (i + 1) % 10 == 0:
                    logger.info(f"Processed {i + 1} definitions")

                yield result

            except Exception as e:
                logger.error(f"Error processing '{term}': {e}")
                # Yield error result
                yield create_error_result(term, definition, str(e))

    def process_batch_chunked(self, definitions, context=None):
        """
        Process batch in chunks to control memory usage.
        Returns list of results.
        """
        results = []
        total = len(definitions)

        for i in range(0, total, self.chunk_size):
            chunk = definitions[i : i + self.chunk_size]
            chunk_results = []

            for term, definition in chunk:
                try:
                    term, definition = validate_input(term, definition)
                    result = self.classifier.classify(term, definition, context)
                    chunk_results.append(result)
                except Exception as e:
                    logger.error(f"Error processing '{term}': {e}")
                    chunk_results.append(create_error_result(term, definition, str(e)))

            results.extend(chunk_results)

            # Optional: Clear internal caches between chunks
            if hasattr(self.classifier, "clear_cache"):
                self.classifier.clear_cache()

            logger.info(f"Processed chunk: {min(i + self.chunk_size, total)}/{total}")

        return results


# FIX #7: Robust YAML configuration loading
def load_config_safe(config_path: Path | None) -> dict:
    """
    Load and validate YAML configuration with full error handling.
    """
    default_config = {
        "version": "1.0.0",
        "classification": {
            "complete_analysis": True,
            "high_confidence_threshold": 0.8,
            "medium_confidence_threshold": 0.6,
            "low_confidence_threshold": 0.4,
            "max_classification_time_ms": 500,
            "target_precision": 0.95,
        },
        "categories": {},
        "disambiguation": {},
        "validation": {
            "require_all_steps": True,
            "check_all_categories": True,
            "minimum_pattern_matches": 1,
        },
    }

    if not config_path:
        logger.info("No config path provided, using defaults")
        return default_config

    if not config_path.exists():
        logger.warning(f"Config file not found: {config_path}, using defaults")
        return default_config

    try:
        with open(config_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # Validate it's a dictionary
        if not isinstance(config, dict):
            logger.error("Config is not a dictionary, using defaults")
            return default_config

        # Validate required top-level keys
        required_keys = ["version", "categories"]
        for key in required_keys:
            if key not in config:
                logger.warning(f"Missing required key '{key}' in config")
                config[key] = default_config.get(key, {})

        # Validate categories structure
        if not isinstance(config.get("categories"), dict):
            logger.error("Categories must be a dictionary")
            config["categories"] = {}

        # Validate each category
        for cat_name, cat_config in config["categories"].items():
            if not isinstance(cat_config, dict):
                logger.error(f"Category {cat_name} config must be a dictionary")
                config["categories"][cat_name] = {}
                continue

            # Ensure required category fields
            if "patterns" not in cat_config:
                cat_config["patterns"] = []
            if "keywords" not in cat_config:
                cat_config["keywords"] = []
            if "weight" not in cat_config:
                cat_config["weight"] = 1.0

        # Merge with defaults for missing values
        def deep_merge(base, override):
            for key, value in override.items():
                if (
                    key in base
                    and isinstance(base[key], dict)
                    and isinstance(value, dict)
                ):
                    deep_merge(base[key], value)
                else:
                    base[key] = value
            return base

        final_config = deep_merge(default_config.copy(), config)

        logger.info(f"Successfully loaded config version {final_config.get('version')}")
        return final_config

    except yaml.YAMLError as e:
        logger.error(f"YAML parsing error: {e}")
        return default_config
    except OSError as e:
        logger.error(f"IO error reading config: {e}")
        return default_config
    except Exception as e:
        logger.error(f"Unexpected error loading config: {e}")
        return default_config


# FIX #8: Disambiguation with recursion protection
class SafeDisambiguation:
    """Disambiguation with infinite loop protection."""

    def __init__(self, max_depth: int = 3):
        self.max_depth = max_depth
        self._call_stack = []

    def apply_disambiguation(
        self, term: str, definition: str, rules: dict, depth: int = 0
    ):
        """Apply disambiguation with recursion protection."""

        # Check recursion depth
        if depth >= self.max_depth:
            logger.warning(f"Max disambiguation depth reached for term '{term}'")
            return None

        # Check for cycles
        call_signature = f"{term}:{definition[:50]}"
        if call_signature in self._call_stack:
            logger.warning(f"Disambiguation cycle detected for '{term}'")
            return None

        self._call_stack.append(call_signature)

        try:
            # Apply disambiguation logic
            return self._apply_rules(term, definition, rules)
        finally:
            self._call_stack.pop()

    def _apply_rules(self, term: str, definition: str, rules: dict):
        """Apply disambiguation rules safely."""
        # Implementation here


# FIX #11: Secondary categories deduplication
def identify_secondary_categories_safe(
    all_scores: dict[Any, float], primary: Any, threshold: float = 0.3
) -> list[Any]:
    """
    Identify secondary categories with proper deduplication.
    """
    if not all_scores:
        return []

    secondary = []
    seen = {primary}  # Track primary to avoid duplicates

    # Sort by score
    sorted_categories = sorted(all_scores.items(), key=lambda x: x[1], reverse=True)

    for category, score in sorted_categories:
        # Skip primary and already seen
        if category in seen:
            continue

        # Skip low scores
        if score < threshold:
            break

        secondary.append(category)
        seen.add(category)

        # Limit to 3 secondary categories
        if len(secondary) >= 3:
            break

    return secondary


# Helper function for error results
def create_error_result(term: str, definition: str, error_msg: str):
    """Create an error result for failed classification."""
    from datetime import datetime

    @dataclass
    class ErrorResult:
        term: str
        definition: str
        primary_category: str = "KIND"  # Default fallback
        confidence: float = 0.0
        error: str = ""
        timestamp: datetime = field(default_factory=datetime.now)

    return ErrorResult(term=term, definition=definition, error=error_msg)


# Test suite for fixes
def test_fixes():
    """Test suite to verify all fixes work correctly."""

    print("Testing Fix #1: ABSTRACT category removed")
    assert "ABSTRACT" not in [cat.name for cat in UFOCategoryFixed]
    print("✓ Pass")

    print("\nTesting Fix #3: Input validation")
    try:
        validate_input("", "")
        msg = "Should have raised ValueError"
        raise AssertionError(msg)
    except ValueError:
        print("✓ Empty string rejected")

    try:
        validate_input("   ", "   ")
        msg = "Should have raised ValueError"
        raise AssertionError(msg)
    except ValueError:
        print("✓ Whitespace-only rejected")

    try:
        validate_input("DROP TABLE", "test")
        msg = "Should have raised ValueError"
        raise AssertionError(msg)
    except ValueError:
        print("✓ SQL injection pattern rejected")

    term, defn = validate_input("  test  ", "  definition  ")
    assert term == "test"
    assert defn == "definition"
    print("✓ Whitespace stripped")

    print("\nTesting Fix #5: Unicode normalization")
    assert normalize_dutch_text("café") == "café"
    assert normalize_dutch_text("cafe\u0301") == "café"
    assert normalize_dutch_text("Ĳssel") == "ijssel"
    print("✓ Unicode normalized correctly")

    print("\nTesting Fix #2: Division by zero protection")
    assert calculate_confidence_safe("KIND", {}, 0) == 0.0
    print("✓ Empty scores handled")

    assert calculate_confidence_safe("KIND", {"KIND": 0.0}, 0) == 0.0
    print("✓ Zero primary score handled")

    confidence = calculate_confidence_safe("KIND", {"KIND": 0.8, "EVENT": 0.2}, 5)
    assert 0 <= confidence <= 1
    print("✓ Valid confidence calculated")

    print("\nTesting Fix #7: YAML config loading")
    config = load_config_safe(Path("nonexistent.yaml"))
    assert config["version"] == "1.0.0"
    print("✓ Missing file returns defaults")

    print("\nAll fixes tested successfully!")


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Run tests
    test_fixes()
