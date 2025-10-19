"""
Shim voor ai_toetser.validators

Deze module biedt een minimale, testvriendelijke API voor oude imports die
in sommige tests nog gebruikt worden. De daadwerkelijke validatorlogica leeft
onder `src/toetsregels/validators` en de JSON‑loader. Deze shim zorgt er alleen
voor dat unit‑tests die tegen `ai_toetser.validators` zijn geschreven kunnen
importeren en basisfunctionaliteit gebruiken tijdens de transitie.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict


class ValidationResult(Enum):
    PASS = "pass"
    FAIL = "fail"


@dataclass
class ValidationContext:
    definitie: str
    regel: dict[str, Any] | None = None
    contexten: dict[str, Any] | None = None
    begrip: str | None = None


@dataclass
class ValidationOutput:
    rule_id: str
    result: ValidationResult
    message: str = ""

    def __str__(self) -> str:
        icon = "✔️" if self.result == ValidationResult.PASS else "✖️"
        return f"{icon} {self.rule_id}: {self.message}"


class _Registry:
    def __init__(self) -> None:
        # Lazy import to avoid cycles
        self._map: dict[str, type] | None = None

    def _ensure(self) -> None:
        if self._map is None:
            try:
                from .content_rules import CON01Validator  # type: ignore

                self._map = {"CON-01": CON01Validator}
            except Exception:
                self._map = {}

    def get_validator(self, code: str):
        self._ensure()
        cls = (self._map or {}).get(code)
        return cls() if cls else None

    def get_all_validators(self) -> dict[str, str]:
        self._ensure()
        return {k: v.__name__ for k, v in (self._map or {}).items()}


validation_registry = _Registry()


__all__ = [
    "ValidationContext",
    "ValidationOutput",
    "ValidationResult",
    "validation_registry",
]
