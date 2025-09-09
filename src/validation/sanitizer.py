"""
Data sanitization system for DefinitieAgent.
Provides XSS prevention, HTML sanitization, and content filtering.
"""

import html
import json
import logging
import re
from dataclasses import dataclass
from datetime import UTC, datetime

UTC = UTC  # Python 3.10 compatibility
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class SanitizationLevel(Enum):
    """Sanitization security levels."""

    PERMISSIVE = "permissive"  # Basic sanitization
    MODERATE = "moderate"  # Standard sanitization
    STRICT = "strict"  # Strict sanitization
    PARANOID = "paranoid"  # Maximum security


class ContentType(Enum):
    """Content types for context-aware sanitization."""

    PLAIN_TEXT = "plain_text"
    HTML = "html"
    MARKDOWN = "markdown"
    JSON = "json"
    URL = "url"
    EMAIL = "email"
    PHONE = "phone"
    DUTCH_TEXT = "dutch_text"
    DEFINITION = "definition"
    GOVERNMENT_TERM = "government_term"


@dataclass
class SanitizationRule:
    """Rule for sanitization processing."""

    name: str
    pattern: str
    replacement: str
    content_types: list[ContentType]
    level: SanitizationLevel = SanitizationLevel.MODERATE
    description: str = ""


@dataclass
class SanitizationResult:
    """Result of sanitization processing."""

    original_value: Any
    sanitized_value: Any
    changes_made: list[str]
    warnings: list[str]
    content_type: ContentType
    level: SanitizationLevel


class ContentSanitizer:
    """Main content sanitization system."""

    def __init__(self):
        self.rules: dict[ContentType, list[SanitizationRule]] = {}
        self.sanitization_history: list[dict[str, Any]] = []
        self.load_sanitization_rules()

    def load_sanitization_rules(self):
        """Load built-in sanitization rules."""

        # HTML sanitization rules
        html_rules = [
            SanitizationRule(
                name="script_tag_removal",
                pattern=r"<script[^>]*>.*?</script>",
                replacement="",
                content_types=[ContentType.HTML],
                level=SanitizationLevel.STRICT,
                description="Remove script tags",
            ),
            SanitizationRule(
                name="dangerous_attributes",
                pattern=r'\s(on\w+|javascript:|vbscript:|data:)\s*=\s*["\'][^"\']*["\']',
                replacement="",
                content_types=[ContentType.HTML],
                level=SanitizationLevel.MODERATE,
                description="Remove dangerous HTML attributes",
            ),
            SanitizationRule(
                name="iframe_removal",
                pattern=r"<iframe[^>]*>.*?</iframe>",
                replacement="",
                content_types=[ContentType.HTML],
                level=SanitizationLevel.STRICT,
                description="Remove iframe tags",
            ),
        ]

        # Plain text sanitization rules
        text_rules = [
            SanitizationRule(
                name="control_characters",
                pattern=r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]",
                replacement="",
                content_types=[ContentType.PLAIN_TEXT, ContentType.DUTCH_TEXT],
                level=SanitizationLevel.MODERATE,
                description="Remove control characters",
            ),
            SanitizationRule(
                name="excessive_whitespace",
                pattern=r"\s{3,}",
                replacement=" ",
                content_types=[ContentType.PLAIN_TEXT, ContentType.DUTCH_TEXT],
                level=SanitizationLevel.PERMISSIVE,
                description="Normalize excessive whitespace",
            ),
            SanitizationRule(
                name="sql_injection_patterns",
                pattern=r"(';)|(\b(union|select|insert|update|delete|drop|create|alter|exec|execute)\b)",
                replacement="",
                content_types=[ContentType.PLAIN_TEXT],
                level=SanitizationLevel.STRICT,
                description="Remove SQL injection patterns",
            ),
        ]

        # Dutch text specific rules
        dutch_rules = [
            SanitizationRule(
                name="invalid_dutch_chars",
                pattern=r'[^\w\s\-\.,;:!?()\[\]{}""'
                "`~@#$%^&*+=|\\/<>àáâãäåæçèéêëìíîïñòóôõöøùúûüýÿ]",
                replacement="",
                content_types=[ContentType.DUTCH_TEXT],
                level=SanitizationLevel.MODERATE,
                description="Remove non-Dutch characters",
            ),
            SanitizationRule(
                name="profanity_filter",
                pattern=r"\b(kut|shit|fuck|damn|hell|ass|bitch)\b",
                replacement="[FILTERED]",
                content_types=[ContentType.DUTCH_TEXT, ContentType.DEFINITION],
                level=SanitizationLevel.STRICT,
                description="Filter profanity",
            ),
        ]

        # Government term specific rules
        government_rules = [
            SanitizationRule(
                name="unauthorized_abbreviations",
                pattern=r"\b(ACAB|FTP|NAZI|KKK)\b",
                replacement="[UNAUTHORIZED]",
                content_types=[ContentType.GOVERNMENT_TERM],
                level=SanitizationLevel.STRICT,
                description="Remove unauthorized abbreviations",
            ),
            SanitizationRule(
                name="personal_data_patterns",
                pattern=r"\b(\d{9}|\d{3}-\d{2}-\d{4}|\d{4}\s?\w{2}\s?\d{4})\b",
                replacement="[REDACTED]",
                content_types=[ContentType.GOVERNMENT_TERM, ContentType.DEFINITION],
                level=SanitizationLevel.MODERATE,
                description="Redact personal data patterns",
            ),
        ]

        # Email sanitization rules
        email_rules = [
            SanitizationRule(
                name="email_validation",
                pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
                replacement="",
                content_types=[ContentType.EMAIL],
                level=SanitizationLevel.MODERATE,
                description="Validate email format",
            )
        ]

        # URL sanitization rules
        url_rules = [
            SanitizationRule(
                name="malicious_protocols",
                pattern=r"^(javascript:|data:|vbscript:|file:|ftp:)",
                replacement="",
                content_types=[ContentType.URL],
                level=SanitizationLevel.STRICT,
                description="Remove malicious protocols",
            ),
            SanitizationRule(
                name="url_encoding",
                pattern=r'[<>"\']',
                replacement="",
                content_types=[ContentType.URL],
                level=SanitizationLevel.MODERATE,
                description="Remove dangerous URL characters",
            ),
        ]

        # Store rules by content type
        self.rules[ContentType.HTML] = html_rules
        self.rules[ContentType.PLAIN_TEXT] = text_rules
        self.rules[ContentType.DUTCH_TEXT] = dutch_rules + text_rules
        self.rules[ContentType.GOVERNMENT_TERM] = (
            government_rules + dutch_rules + text_rules
        )
        self.rules[ContentType.DEFINITION] = government_rules + dutch_rules + text_rules
        self.rules[ContentType.EMAIL] = email_rules
        self.rules[ContentType.URL] = url_rules

    def sanitize(
        self,
        value: Any,
        content_type: ContentType = ContentType.PLAIN_TEXT,
        level: SanitizationLevel = SanitizationLevel.MODERATE,
    ) -> SanitizationResult:
        """Sanitize content based on type and level."""

        if value is None:
            return SanitizationResult(
                original_value=None,
                sanitized_value=None,
                changes_made=[],
                warnings=[],
                content_type=content_type,
                level=level,
            )

        original_value = value
        sanitized_value = str(value)
        changes_made = []
        warnings = []

        try:
            # Apply content type specific sanitization
            if content_type in self.rules:
                for rule in self.rules[content_type]:
                    if (
                        rule.level.value <= level.value
                        or level == SanitizationLevel.PARANOID
                    ):
                        old_value = sanitized_value
                        sanitized_value = re.sub(
                            rule.pattern,
                            rule.replacement,
                            sanitized_value,
                            flags=re.IGNORECASE,
                        )

                        if old_value != sanitized_value:
                            changes_made.append(f"Applied rule: {rule.name}")
                            logger.debug(
                                f"Sanitization rule '{rule.name}' applied to content"
                            )

            # Apply general sanitization based on level
            if level in (SanitizationLevel.STRICT, SanitizationLevel.PARANOID):
                # HTML entity encoding
                if content_type not in [ContentType.HTML]:
                    old_value = sanitized_value
                    sanitized_value = html.escape(sanitized_value)
                    if old_value != sanitized_value:
                        changes_made.append("HTML entity encoding applied")

                # Path traversal prevention
                if "../" in sanitized_value or "..\\" in sanitized_value:
                    sanitized_value = sanitized_value.replace("../", "").replace(
                        "..\\", ""
                    )
                    changes_made.append("Path traversal patterns removed")
                    warnings.append("Potential path traversal attempt detected")

            # Length validation
            if len(sanitized_value) > 10000:  # Configurable limit
                sanitized_value = sanitized_value[:10000]
                changes_made.append("Content truncated due to length limit")
                warnings.append("Content was truncated")

            # Convert back to original type if possible
            if isinstance(original_value, int | float):
                try:
                    if isinstance(original_value, int):
                        sanitized_value = int(sanitized_value)
                    else:
                        sanitized_value = float(sanitized_value)
                except ValueError:
                    warnings.append("Could not convert back to numeric type")

            # Record sanitization attempt
            self.sanitization_history.append(
                {
                    "timestamp": str(datetime.now(UTC)),
                    "content_type": content_type.value,
                    "level": level.value,
                    "changes_made": len(changes_made),
                    "warnings": len(warnings),
                    "original_length": len(str(original_value)),
                    "sanitized_length": len(str(sanitized_value)),
                }
            )

            # Keep only recent history
            if len(self.sanitization_history) > 1000:
                self.sanitization_history.pop(0)

            return SanitizationResult(
                original_value=original_value,
                sanitized_value=sanitized_value,
                changes_made=changes_made,
                warnings=warnings,
                content_type=content_type,
                level=level,
            )

        except Exception as e:
            logger.error(f"Sanitization error: {e}")
            return SanitizationResult(
                original_value=original_value,
                sanitized_value=original_value,  # Return original on error
                changes_made=[],
                warnings=[f"Sanitization error: {e!s}"],
                content_type=content_type,
                level=level,
            )

    def sanitize_dict(
        self,
        data: dict[str, Any],
        content_types: dict[str, ContentType] | None = None,
        level: SanitizationLevel = SanitizationLevel.MODERATE,
    ) -> dict[str, Any]:
        """Sanitize all values in a dictionary."""

        if content_types is None:
            content_types = {}

        sanitized_data = {}

        for key, value in data.items():
            content_type = content_types.get(key, ContentType.PLAIN_TEXT)

            if isinstance(value, dict):
                sanitized_data[key] = self.sanitize_dict(value, content_types, level)
            elif isinstance(value, list):
                sanitized_data[key] = [
                    self.sanitize(item, content_type, level).sanitized_value
                    for item in value
                ]
            else:
                result = self.sanitize(value, content_type, level)
                sanitized_data[key] = result.sanitized_value

        return sanitized_data

    def sanitize_for_definition(self, text: str) -> str:
        """Sanitize text specifically for definition content."""
        result = self.sanitize(text, ContentType.DEFINITION, SanitizationLevel.STRICT)
        return result.sanitized_value

    def sanitize_user_input(self, data: dict[str, Any]) -> dict[str, Any]:
        """Sanitize user input with appropriate content types."""
        content_types = {
            "begrip": ContentType.GOVERNMENT_TERM,
            "voorsteller": ContentType.DUTCH_TEXT,
            "definitie_origineel": ContentType.DEFINITION,
            "definitie_gecorrigeerd": ContentType.DEFINITION,
            "definitie_aangepast": ContentType.DEFINITION,
            "toelichting": ContentType.DUTCH_TEXT,
            "voorbeeld_zinnen": ContentType.DUTCH_TEXT,
            "praktijkvoorbeelden": ContentType.DUTCH_TEXT,
            "synoniemen": ContentType.GOVERNMENT_TERM,
            "antoniemen": ContentType.GOVERNMENT_TERM,
            "vrije_input": ContentType.PLAIN_TEXT,
        }

        return self.sanitize_dict(data, content_types, SanitizationLevel.MODERATE)

    def detect_malicious_content(self, text: str) -> list[str]:
        """Detect potentially malicious content patterns."""
        malicious_patterns = [
            (r"<script[^>]*>", "JavaScript injection attempt"),
            (r"javascript:", "JavaScript protocol usage"),
            (r"vbscript:", "VBScript protocol usage"),
            (r"data:.*base64", "Base64 data URI"),
            (r"eval\s*\(", "Eval function usage"),
            (r"document\.cookie", "Cookie access attempt"),
            (r"window\.location", "Location manipulation"),
            (r"\.\./", "Path traversal attempt"),
            (r"(union|select|insert|update|delete|drop)\s+", "SQL injection pattern"),
            (r"(exec|execute|cmd|system)\s*\(", "Command execution attempt"),
            (r"<iframe[^>]*>", "Iframe injection"),
            (r"<object[^>]*>", "Object tag injection"),
            (r"<embed[^>]*>", "Embed tag injection"),
        ]

        detected_threats = []

        for pattern, description in malicious_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                detected_threats.append(description)

        return detected_threats

    def get_sanitization_stats(self) -> dict[str, Any]:
        """Get sanitization statistics."""
        if not self.sanitization_history:
            return {"total_sanitizations": 0}

        total_sanitizations = len(self.sanitization_history)

        # Content type usage
        content_type_usage = {}
        for record in self.sanitization_history:
            content_type = record.get("content_type", "unknown")
            content_type_usage[content_type] = (
                content_type_usage.get(content_type, 0) + 1
            )

        # Level usage
        level_usage = {}
        for record in self.sanitization_history:
            level = record.get("level", "unknown")
            level_usage[level] = level_usage.get(level, 0) + 1

        # Changes statistics
        total_changes = sum(
            record.get("changes_made", 0) for record in self.sanitization_history
        )
        total_warnings = sum(
            record.get("warnings", 0) for record in self.sanitization_history
        )

        return {
            "total_sanitizations": total_sanitizations,
            "total_changes": total_changes,
            "total_warnings": total_warnings,
            "content_type_usage": content_type_usage,
            "level_usage": level_usage,
            "average_changes_per_sanitization": (
                total_changes / total_sanitizations if total_sanitizations > 0 else 0
            ),
        }

    def export_sanitization_log(self, filename: str | None = None) -> str:
        """Export sanitization log to file."""
        if filename is None:
            filename = (
                f"sanitization_log_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.json"
            )

        filepath = Path("logs") / filename
        filepath.parent.mkdir(exist_ok=True)

        log_data = {
            "generated_at": datetime.now(UTC).isoformat(),
            "statistics": self.get_sanitization_stats(),
            "rules_count": sum(len(rules) for rules in self.rules.values()),
            "recent_sanitizations": (
                self.sanitization_history[-100:]
                if len(self.sanitization_history) > 100
                else self.sanitization_history
            ),
        }

        with open(filepath, "w") as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)

        return str(filepath)


# Global sanitizer instance
_global_sanitizer: ContentSanitizer | None = None


def get_sanitizer() -> ContentSanitizer:
    """Get or create global sanitizer instance."""
    global _global_sanitizer
    if _global_sanitizer is None:
        _global_sanitizer = ContentSanitizer()
    return _global_sanitizer


def sanitize_content(
    value: Any,
    content_type: ContentType = ContentType.PLAIN_TEXT,
    level: SanitizationLevel = SanitizationLevel.MODERATE,
) -> str:
    """Convenience function for content sanitization."""
    sanitizer = get_sanitizer()
    result = sanitizer.sanitize(value, content_type, level)
    return result.sanitized_value


def sanitize_for_definition(text: str) -> str:
    """Convenience function for definition sanitization."""
    sanitizer = get_sanitizer()
    return sanitizer.sanitize_for_definition(text)


def sanitize_user_input(data: dict[str, Any]) -> dict[str, Any]:
    """Convenience function for user input sanitization."""
    sanitizer = get_sanitizer()
    return sanitizer.sanitize_user_input(data)


def detect_threats(text: str) -> list[str]:
    """Convenience function for threat detection."""
    sanitizer = get_sanitizer()
    return sanitizer.detect_malicious_content(text)


# Sanitization decorators
def sanitize_input_decorator(
    content_type: ContentType = ContentType.PLAIN_TEXT,
    level: SanitizationLevel = SanitizationLevel.MODERATE,
):
    """Decorator to sanitize function inputs."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            sanitizer = get_sanitizer()

            # Sanitize args
            sanitized_args = []
            for arg in args:
                if isinstance(arg, str):
                    result = sanitizer.sanitize(arg, content_type, level)
                    sanitized_args.append(result.sanitized_value)
                else:
                    sanitized_args.append(arg)

            # Sanitize kwargs
            sanitized_kwargs = {}
            for key, value in kwargs.items():
                if isinstance(value, str):
                    result = sanitizer.sanitize(value, content_type, level)
                    sanitized_kwargs[key] = result.sanitized_value
                else:
                    sanitized_kwargs[key] = value

            return func(*sanitized_args, **sanitized_kwargs)

        return wrapper

    return decorator


async def test_sanitizer():
    """Test the sanitization system."""
    print("🧪 Testing Content Sanitizer")
    print("=" * 28)

    sanitizer = get_sanitizer()

    # Test basic sanitization
    malicious_text = "<script>alert('XSS')</script>Hello World"
    result = sanitizer.sanitize(
        malicious_text, ContentType.HTML, SanitizationLevel.STRICT
    )
    print(
        f"✅ XSS removal: '{result.sanitized_value}' (changes: {len(result.changes_made)})"
    )

    # Test Dutch text sanitization
    dutch_text = "Dit is een Nederlandse tekst met kut woorden"
    result = sanitizer.sanitize(
        dutch_text, ContentType.DUTCH_TEXT, SanitizationLevel.STRICT
    )
    print(
        f"✅ Dutch text filter: '{result.sanitized_value}' (changes: {len(result.changes_made)})"
    )

    # Test definition sanitization
    definition_text = "Een proces waarbij 123456789 wordt gebruikt"
    result = sanitizer.sanitize(
        definition_text, ContentType.DEFINITION, SanitizationLevel.MODERATE
    )
    print(
        f"✅ Definition sanitization: '{result.sanitized_value}' (changes: {len(result.changes_made)})"
    )

    # Test threat detection
    threats = sanitizer.detect_malicious_content("<script>document.cookie</script>")
    print(f"🚨 Threats detected: {len(threats)} - {threats}")

    # Test user input sanitization
    user_data = {
        "begrip": "test<script>alert(1)</script>",
        "voorsteller": "Jan & Piet",
        "definitie_origineel": "Een proces waarbij <iframe>bad</iframe> wordt gebruikt",
    }

    sanitized_data = sanitizer.sanitize_user_input(user_data)
    print(f"✅ User input sanitized: {sanitized_data}")

    # Show statistics
    stats = sanitizer.get_sanitization_stats()
    print(f"📊 Total sanitizations: {stats['total_sanitizations']}")
    print(f"📊 Total changes: {stats['total_changes']}")
    print(f"📊 Total warnings: {stats['total_warnings']}")


if __name__ == "__main__":
    import asyncio
    from datetime import datetime

    asyncio.run(test_sanitizer())
