"""
Provider-agnostic AI client abstractions.

Defines the Protocol, data types, and error hierarchy that all AI provider
clients must conform to. Application code imports from here instead of
directly from openai/anthropic SDKs.
"""

from __future__ import annotations

import asyncio
import re
import weakref
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

_API_KEY_RE = re.compile(r"sk-[\w-]{10,}")


def sanitize_error(message: str) -> str:
    """Redact API keys from error messages to prevent leakage in logs."""
    return _API_KEY_RE.sub("[REDACTED]", message)


def foutketen(exc: BaseException, *, diepte: int = 3) -> str:
    """Compacte, geredigeerde weergave van een exception mét haar oorzaken.

    DEF-766 (correctieronde 2, C): een SDK-`APIConnectionError` zegt alleen
    "Connection error."; de werkelijke oorzaak (bv. `RuntimeError: Event loop
    is closed`) zit in `__cause__`/`__context__`. Zonder die keten is een
    transportfout niet te onderzoeken. Geheimen worden geredigeerd.
    """
    delen: list[str] = []
    huidig: BaseException | None = exc
    gezien: set[int] = set()
    while huidig is not None and len(delen) < diepte and id(huidig) not in gezien:
        gezien.add(id(huidig))
        delen.append(f"{type(huidig).__name__}: {huidig}")
        huidig = huidig.__cause__ or huidig.__context__
    return sanitize_error(" ← ".join(delen))


class Eventloopwacht:
    """Signaleert dat een async SDK-client in een andere eventloop wordt gebruikt
    dan bij het vorige gebruik (DEF-766, correctieronde 2, punt C).

    Het httpx-verbindingspool in een SDK-client (Anthropic/OpenAI) is gebonden
    aan de eventloop waarin zijn keep-alive-verbindingen zijn geopend. De UI
    draait elke aanroep in een eigen, nieuwe eventloop
    (`ui.helpers.async_bridge.run_async`); een verbinding uit een inmiddels
    gesloten loop geeft dan direct `APIConnectionError` met als oorzaak
    `RuntimeError: Event loop is closed` — zonder SDK-retries zichtbaar als
    technische fout, mét SDK-retries een verborgen herkansing. Zwakke
    referentie naar de loop: een gerecycled `id()` telt niet als dezelfde loop.
    """

    def __init__(self) -> None:
        self._loop_ref: Any | None = None

    def gewisseld(self) -> bool:
        """True als er een draaiende loop is die niet de vorige is (en er een
        vorige was); registreert de huidige loop als referentie."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return False
        vorige = self._loop_ref() if self._loop_ref is not None else None
        eerste = self._loop_ref is None
        self._loop_ref = weakref.ref(loop)
        return not eerste and vorige is not loop


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ChatMessage:
    """Provider-agnostic chat message."""

    role: str  # "system", "user", "assistant"
    content: str


@dataclass(frozen=True)
class ChatResponse:
    """Provider-agnostic chat completion response."""

    text: str
    tokens_used: int  # Total tokens (prompt + completion), 0 if unavailable
    model: str
    metadata: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Error hierarchy
# ---------------------------------------------------------------------------


class AIClientError(Exception):
    """Base error for all AI client operations."""


class AIRateLimitClientError(AIClientError):
    """Rate limit exceeded by the AI provider."""


class AIConnectionClientError(AIClientError):
    """Connection or network error talking to the AI provider."""


class AIAuthenticationClientError(AIClientError):
    """Authentication/authorization failure (invalid or missing API key).

    DEF-429: a permanent error — the retry layer must fail fast on this
    instead of retrying, otherwise generation hangs for minutes on backoff.
    """


# ---------------------------------------------------------------------------
# Protocol
# ---------------------------------------------------------------------------


@runtime_checkable
class AsyncAIClient(Protocol):
    """Protocol that every AI provider client must implement."""

    @property
    def provider_name(self) -> str:
        """Return provider identifier, e.g. 'openai' or 'anthropic'."""
        ...

    async def chat_completion(
        self,
        messages: list[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 300,
        timeout: float | None = None,
        max_retries: int | None = None,
    ) -> ChatResponse:
        """Send a chat completion request and return a provider-agnostic response.

        ``max_retries`` (DEF-766, opt-in): SDK-interne retries voor déze
        aanroep; ``None`` laat de clientdefault staan.

        Raises:
            AIRateLimitClientError: When the provider rate-limits the request.
            AIConnectionClientError: On network / connection failures.
            AIClientError: On any other provider error.
        """
        ...

    async def close(self) -> None:
        """Release underlying SDK resources."""
        ...
