"""SecurityService — conservatieve sanitization van een GenerationRequest.

DEF-448: vult de ``SecurityServiceInterface`` die ``DefinitionOrchestratorV2`` in
PHASE 1 aanroept (voorheen ``security_service=None``). De vrije-tekst- en
context-velden van het request worden gesanitizet vóór ze de LLM-prompt bereiken:

1. HTML/script wordt gestript (via de bestaande ``ContentSanitizer``).
2. Expliciete prompt-injectie-control-markers worden geneutraliseerd.

Conservatief: alleen bekende aanvalspatronen worden geraakt; legitieme begrippen
en context (leestekens, ``C++``, organisatienamen) blijven intact. Het begrip
wordt nooit naar een lege string gesanitizet (val terug op het origineel).
"""

import logging
import re
from dataclasses import replace

from services.interfaces import (
    Definition,
    GenerationRequest,
    SecurityServiceInterface,
)
from validation.sanitizer import ContentSanitizer, get_sanitizer

logger = logging.getLogger(__name__)

# Expliciete prompt-injectie-control-markers. Conservatief gekozen: dit zijn
# structurele aanvalssequenties die in een normaal begrip / normale context niet
# voorkomen, dus neutralisatie raakt geen legitieme input.
_INJECTION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\{\s*system\s*:[^}]*\}", re.IGNORECASE),  # {system: ...}
    re.compile(r"\[\[\s*/?\s*system\s*\]\]", re.IGNORECASE),  # [[system]]
    re.compile(
        r"#{2,}\s*system\s+override\s*#*", re.IGNORECASE
    ),  # ### SYSTEM OVERRIDE ###
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"forget\s+all\s+(previous\s+)?(rules|instructions)", re.IGNORECASE),
    re.compile(r"```.*?```", re.DOTALL),  # markdown code-fence injectie
]

# PII-patronen voor redact_pii (basis: e-mail, BSN-achtige 9-cijferreeks, telefoon).
_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_BSN_RE = re.compile(r"\b\d{9}\b")
_PHONE_RE = re.compile(r"\b(?:\+31|0)\s?(?:\d[\s-]?){8,9}\d\b")


class SecurityService(SecurityServiceInterface):
    """Conservatieve, synchroon-rekenende security-service (async interface)."""

    def __init__(self, sanitizer: ContentSanitizer | None = None) -> None:
        self._sanitizer = sanitizer or get_sanitizer()

    def _sanitize_text(self, value: str | None) -> str | None:
        """Strip HTML/script + neutraliseer injectie-markers. Behoudt None/leeg."""
        if not value or not value.strip():
            return value
        # 1. HTML/script verwijderen (ContentSanitizer detecteert HTML automatisch)
        cleaned = self._sanitizer.sanitize_content(
            value, content_type="text", level="strict"
        )
        # 2. Prompt-injectie-control-markers neutraliseren
        for pattern in _INJECTION_PATTERNS:
            cleaned = pattern.sub(" ", cleaned)
        # 3. Whitespace normaliseren
        return re.sub(r"\s+", " ", cleaned).strip()

    def _sanitize_list(self, values: list[str] | None) -> list[str] | None:
        if not values:
            return values
        return [self._sanitize_text(v) or "" for v in values]

    async def sanitize_request(self, request: GenerationRequest) -> GenerationRequest:
        """Sanitize de vrije-tekst- en context-velden van het request.

        Het begrip valt terug op het origineel als sanitization het zou legen,
        zodat de generatie nooit met een leeg begrip verdergaat.
        """
        sanitized_begrip = self._sanitize_text(request.begrip) or request.begrip
        return replace(
            request,
            begrip=sanitized_begrip,
            context=self._sanitize_text(request.context),
            extra_instructies=self._sanitize_text(request.extra_instructies),
            document_context=self._sanitize_text(request.document_context),
            juridische_context=self._sanitize_list(request.juridische_context),
            wettelijke_basis=self._sanitize_list(request.wettelijke_basis),
            organisatorische_context=self._sanitize_list(
                request.organisatorische_context
            ),
        )

    async def redact_pii(self, text: str, redaction_level: str = "medium") -> str:
        """Vervang e-mailadressen, BSN-achtige reeksen en telefoonnummers."""
        if not text:
            return text
        redacted = _EMAIL_RE.sub("[EMAIL]", text)
        redacted = _BSN_RE.sub("[BSN]", redacted)
        return _PHONE_RE.sub("[TEL]", redacted)

    async def validate_compliance(
        self, definition: Definition, compliance_rules: list[str] | None = None
    ) -> dict[str, bool]:
        """Basis-compliance: controleert dat de definitie geen PII bevat."""
        text = (
            f"{definition.begrip} {definition.definitie} {definition.toelichting or ''}"
        )
        no_pii = await self.redact_pii(text) == text
        return {"no_pii": no_pii}
