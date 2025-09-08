"""Internal types for modular validation pipeline.

These are not part of the public schema contract, but help structure
rule evaluation and context sharing between modules.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from typing import Any


class ReadOnlySequence:
    """Minimal read-only sequence with list-like equality, no append method.

    - Behaves like an immutable sequence for iteration and indexing
    - Compares equal to lists/tuples with the same elements
    - Has no mutation methods, so `append` attribute is missing (AttributeError)
    """

    __slots__ = ("_data",)

    def __init__(self, data: Iterable[str] | None = None) -> None:
        self._data = tuple(data or ())

    def __iter__(self) -> Iterator[str]:
        return iter(self._data)

    def __len__(self) -> int:  # pragma: no cover - trivial
        return len(self._data)

    def __getitem__(self, idx: int) -> str:  # pragma: no cover - trivial
        return self._data[idx]

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return f"ReadOnlySequence({list(self._data)!r})"

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, ReadOnlySequence):
            return self._data == other._data
        if isinstance(other, list | tuple):
            return list(self._data) == list(other)
        return NotImplemented


@dataclass(frozen=True)
class EvaluationContext:
    """Immutable evaluation context shared across validators.

    - raw_text: original input text
    - cleaned_text: pre-cleaned text ready for validation
    - locale/profile: optional evaluation hints
    - correlation_id: tracing identifier
    - tokens: optional tokenization output (immutable tuple to prevent mutation)
    - metadata: free-form readonly metadata
    """

    raw_text: str
    cleaned_text: str
    locale: str | None = None
    profile: str | None = None
    correlation_id: str | None = None
    tokens: Any = field(default_factory=lambda: ReadOnlySequence(()))
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):  # type: ignore[override]
        # Wrap tokens in a read-only sequence (compare equal to lists, no append)
        if not isinstance(self.tokens, ReadOnlySequence):
            object.__setattr__(self, "tokens", ReadOnlySequence(self.tokens))
        # Ensure metadata is a shallow copy to avoid external mutation effects
        if not isinstance(self.metadata, dict):
            object.__setattr__(self, "metadata", dict(self.metadata or {}))

    @classmethod
    def from_params(
        cls,
        text: str,
        cleaned: str | None = None,
        *,
        locale: str | None = None,
        profile: str | None = None,
        correlation_id: str | None = None,
        tokens: Iterable[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> EvaluationContext:
        return cls(
            raw_text=text,
            cleaned_text=cleaned if cleaned is not None else text,
            locale=locale,
            profile=profile,
            correlation_id=correlation_id,
            tokens=(
                ReadOnlySequence(tokens) if tokens is not None else ReadOnlySequence(())
            ),
            metadata=dict(metadata or {}),
        )


@dataclass
class RuleResult:
    """Result of a single rule evaluation."""

    rule_code: str
    score: float = 0.0
    violations: list[dict[str, Any]] = field(default_factory=list)
    weight: float = 1.0
    errored: bool = False
    error_message: str | None = None
    error_type: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_rule_output(cls, rule_code: str, output: Any) -> RuleResult:
        """Create RuleResult from flexible output shapes.

        Accepts:
        - dict with keys (score, violations, weight)
        - tuple/list like (score, violations)
        - scalar score
        """
        if isinstance(output, dict):
            return cls(
                rule_code=rule_code,
                score=float(output.get("score", 0.0) or 0.0),
                violations=list(output.get("violations", []) or []),
                weight=float(output.get("weight", 1.0) or 1.0),
                errored=bool(output.get("errored", False)),
                metadata={
                    k: v
                    for k, v in output.items()
                    if k not in {"score", "violations", "weight", "errored"}
                },
            )

        if isinstance(output, list | tuple):
            score = float(output[0]) if output else 0.0
            violations = list(output[1]) if len(output) > 1 else []
            return cls(rule_code=rule_code, score=score, violations=violations)

        # Fallback: treat as scalar score
        try:
            score_val = float(output)
        except Exception:
            score_val = 0.0
        return cls(rule_code=rule_code, score=score_val)

    @classmethod
    def errored(cls, rule_code: str, error: Exception) -> RuleResult:
        return cls(
            rule_code=rule_code,
            score=0.0,
            violations=[],
            errored=True,
            error_message=str(error),
            error_type=type(error).__name__,
        )
