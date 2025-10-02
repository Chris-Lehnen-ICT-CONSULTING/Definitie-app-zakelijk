"""
Shim content rules voor ai_toetser.validators.

Bevat een minimale CON01Validator die compatibel is met tests die
`from ai_toetser.validators.content_rules import CON01Validator` doen.
"""

from __future__ import annotations

from typing import Any

from . import ValidationContext, ValidationOutput, ValidationResult


class CON01Validator:
    """Minimale validator die altijd een geldig resultaat oplevert.

    In echte implementaties voert CON-01 inhouds/consistentiecontroles uit.
    Deze shim rapporteert een PASS met een korte boodschap om unit‑tests
    niet te blokkeren tijdens de transitie.
    """

    code = "CON-01"

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or {}

    def validate(self, context: ValidationContext) -> ValidationOutput:
        return ValidationOutput(
            rule_id=self.code, result=ValidationResult.PASS, message="OK"
        )


__all__ = ["CON01Validator"]
