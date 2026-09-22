"""
Anthropic implementation of AsyncAIClient.

Wraps the Anthropic SDK and maps its errors to provider-agnostic types.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Literal, cast

import anthropic
from anthropic import AsyncAnthropic
from anthropic.types import MessageParam, ThinkingConfigParam

from services.ai.base_client import (
    AIAuthenticationClientError,
    AIClientError,
    AIConnectionClientError,
    AIRateLimitClientError,
    ChatMessage,
    ChatResponse,
    Eventloopwacht,
    foutketen,
    sanitize_error,
)

if TYPE_CHECKING:
    from services.ai.model_router import ModelRouter

logger = logging.getLogger(__name__)

# DEF-441/DEF-731: `temperature` gaat alleen mee naar modelfamilies die in de
# configuratie staan onder
# `model_routing.capabilities.<provider>.temperature.model_families`.
# Dat is een geconfigureerde legacy-verzendpolicy, geen uitspraak over
# modelbeschikbaarheid: de bron meldt dat niet-standaard sampling-waarden voor
# specifieke, daar genoemde modellen worden afgewezen — niet dat elke vermelding
# altijd een 400 geeft. Deze client kent alleen `temperature` (top_p/top_k zitten
# niet in de signature). Onbekend, ontbrekend of malformed beleid -> parameter
# weglaten (fail-safe voor model-bumps).
#
# DEF-766 (correctieronde 3, F1): `thinking` volgt hetzelfde patroon via
# `model_routing.capabilities.<provider>.thinking_default_on.model_families`.
# Op die families (Opus 5, Sonnet 5) staat adaptief denken standaard aan en
# tellen denktokens mee in `max_tokens`; de client stuurt daar expliciet
# `thinking={"type": "disabled"}` mee. Elk ander model: parameter weglaten,
# zodat de aanroep voor Opus 4.8 e.d. byte-identiek blijft. Geen effort.

_THINKING_DISABLED: ThinkingConfigParam = {"type": "disabled"}


class AnthropicClient:
    """AsyncAIClient implementation backed by the Anthropic SDK."""

    def __init__(
        self,
        api_key: str,
        timeout: float = 30.0,
        max_retries: int = 2,
        model_router: ModelRouter | None = None,
        rebind_on_new_loop: bool = True,
    ) -> None:
        # DEF-566: max_retries gaat 1-op-1 naar de SDK (default 2 = SDK-default);
        # CI-testruns zetten 0 via create_ai_client om retry-stapeling te stoppen.
        self._timeout = timeout
        # DEF-731: optionele injectie; is hij None, dan leest de client de
        # policy per aanroep uit de actieve config (zie `_router`).
        self._model_router = model_router
        self._sdk_opties: dict[str, Any] = {
            "api_key": api_key,
            "timeout": timeout,
            "max_retries": max_retries,
        }
        self._client = AsyncAnthropic(**self._sdk_opties)
        # DEF-766 (correctieronde 2, C): het verbindingspool van de SDK-client
        # is gebonden aan de eventloop van het vorige gebruik; bij een andere
        # loop wordt een verse SDK-client genomen (zie `_sdk_voor_deze_loop`).
        self._rebind_on_new_loop = rebind_on_new_loop
        self._loopwacht = Eventloopwacht()

    @property
    def provider_name(self) -> str:
        return "anthropic"

    def _sdk_voor_deze_loop(self) -> AsyncAnthropic:
        """De SDK-client voor de eventloop die nu draait.

        De UI voert iedere aanroep uit in een eigen, nieuwe eventloop; een
        keep-alive-verbinding uit het pool van een gesloten loop geeft direct
        `APIConnectionError` (oorzaak `RuntimeError: Event loop is closed`).
        Bij een andere loop dan bij het vorige gebruik wordt daarom één keer
        een verse SDK-client (nieuw pool) aangemaakt; de oude wordt losgelaten
        (sluiten op een gesloten loop kan niet; haar sockets sluiten met de
        GC). Binnen dezelfde loop blijft dezelfde client en dus het pool.
        """
        if self._rebind_on_new_loop and self._loopwacht.gewisseld():
            logger.info(
                "Anthropic-client: andere eventloop dan bij het vorige gebruik; "
                "verse SDK-client (verbindingspool) aangemaakt"
            )
            self._client = AsyncAnthropic(**self._sdk_opties)
        return self._client

    @property
    def _router(self) -> ModelRouter:
        """Router voor de capability-policy.

        Bewust geen cache in het productiepad: de policy wordt per aanroep uit
        de actieve config gelezen, zodat een reload_configuration() ook
        doorwerkt op een client die al in gebruik is (DEF-731/F1). Een
        expliciet geinjecteerde router blijft wel vast: die is de autoriteit.
        """
        if self._model_router is not None:
            return self._model_router
        from services.ai.model_router import ModelRouter

        return ModelRouter.from_config()

    async def chat_completion(
        self,
        messages: list[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 300,
        timeout: float | None = None,
        max_retries: int | None = None,
    ) -> ChatResponse:
        if not messages:
            raise AIClientError("messages must not be empty")

        # DEF-766 (opt-in): SDK-retries per aanroep. `with_options` geeft een
        # lichte variant van dezelfde client; zonder argument blijft de
        # geconfigureerde clientdefault (create_ai_client) ongewijzigd.
        basis = self._sdk_voor_deze_loop()
        sdk = (
            basis.with_options(max_retries=int(max_retries))
            if max_retries is not None
            else basis
        )

        # Anthropic uses a separate `system` parameter (not a system message in the list).
        # SDK ≥0.52 verving de NotGiven-sentinel voor request-params door Omit/omit;
        # messages.create() typeert `system` nu als `str | Iterable[TextBlockParam] | Omit`.
        system_text: str | anthropic.Omit = anthropic.omit
        api_messages: list[MessageParam] = []
        system_count = 0

        for msg in messages:
            if msg.role == "system":
                system_count += 1
                if system_count > 1:
                    raise AIClientError(
                        "Multiple system messages are not supported by Anthropic. "
                        "Combine them into a single system message."
                    )
                system_text = msg.content
            elif msg.role in ("user", "assistant"):
                # De elif garandeert user/assistant op runtime; mypy narrowt een
                # str-attribuut niet via `in (...)`, dus expliciete cast (DEF-439).
                role = cast(Literal["user", "assistant"], msg.role)
                api_messages.append({"role": role, "content": msg.content})
            else:
                raise AIClientError(
                    f"Unsupported message role for Anthropic: {msg.role!r}. "
                    "Expected 'system', 'user', or 'assistant'."
                )

        temperature_param, thinking_param = self._verzendbeleid(model, temperature)

        try:
            response = await sdk.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature_param,
                thinking=thinking_param,
                system=system_text,
                messages=api_messages,
                timeout=timeout or self._timeout,
            )
        except anthropic.RateLimitError as exc:
            logger.warning("Anthropic rate limit hit: %s", sanitize_error(str(exc)))
            raise AIRateLimitClientError(sanitize_error(str(exc))) from exc
        except (anthropic.AuthenticationError, anthropic.PermissionDeniedError) as exc:
            # DEF-429: invalid/missing key is permanent — fail fast, do not retry.
            logger.error("Anthropic authentication error: %s", sanitize_error(str(exc)))
            raise AIAuthenticationClientError(sanitize_error(str(exc))) from exc
        except anthropic.APIConnectionError as exc:
            # Mét oorzaakketen (geredigeerd): "Connection error." alleen is niet
            # te onderzoeken (DEF-766, correctieronde 2, C).
            logger.error("Anthropic connection error: %s", foutketen(exc))
            raise AIConnectionClientError(sanitize_error(str(exc))) from exc
        except anthropic.APIError as exc:
            logger.error("Anthropic API error: %s", sanitize_error(str(exc)))
            raise AIClientError(sanitize_error(str(exc))) from exc

        # Extract text from content blocks
        text_parts = [
            block.text for block in response.content if hasattr(block, "text")
        ]
        text = "\n".join(text_parts).strip()

        tokens_used = 0
        if response.usage:
            tokens_used = response.usage.input_tokens + response.usage.output_tokens

        return ChatResponse(
            text=text,
            tokens_used=tokens_used,
            model=response.model,
            metadata={"provider": "anthropic"},
            stop_reason=_stopreden(response, model, max_tokens, tokens_used),
        )

    def _verzendbeleid(
        self, model: str, temperature: float
    ) -> tuple[float | anthropic.Omit, ThinkingConfigParam | anthropic.Omit]:
        """(temperature, thinking) voor de SDK-aanroep volgens de config-policy.

        Beide volgen `model_routing.capabilities.<provider>`: `temperature`
        alleen voor families in `temperature` (DEF-441/DEF-731); `thinking`
        expliciet uit voor families in `thinking_default_on` (DEF-766, F1).
        Alles daarbuiten wordt weggelaten (`anthropic.omit`).
        """
        router = self._router
        temperature_param: float | anthropic.Omit = anthropic.omit
        if router.accepts_temperature(model, provider=self.provider_name):
            temperature_param = temperature
        else:
            logger.debug(
                "temperature weggelaten voor model %s "
                "(niet in model_routing.capabilities.<provider>.temperature, DEF-441/DEF-731)",
                model,
            )

        thinking_param: ThinkingConfigParam | anthropic.Omit = anthropic.omit
        if router.thinking_default_on(model, provider=self.provider_name):
            thinking_param = _THINKING_DISABLED
            logger.debug(
                "thinking expliciet uitgezet voor model %s "
                "(model_routing.capabilities.<provider>.thinking_default_on, DEF-766)",
                model,
            )
        else:
            logger.debug(
                "thinking weggelaten voor model %s "
                "(niet in model_routing.capabilities.<provider>.thinking_default_on, DEF-766)",
                model,
            )
        return temperature_param, thinking_param

    async def close(self) -> None:
        await self._client.close()


def _stopreden(
    response: Any, model: str, max_tokens: int, tokens_used: int
) -> str | None:
    """De door de API gemelde `stop_reason`, of None (DEF-766, correctieronde 3, F1).

    "max_tokens" is een afgekapt antwoord; dat wordt gemeld — zonder sleutel of
    promptinhoud — en reist mee in `ChatResponse.stop_reason`, zodat een
    validerende consument afkapping van een misvormd antwoord kan onderscheiden.
    """
    stop_reason = getattr(response, "stop_reason", None)
    if not isinstance(stop_reason, str):
        return None
    if stop_reason == "max_tokens":
        logger.warning(
            "Anthropic-antwoord afgekapt (stop_reason=max_tokens) voor model %s "
            "bij max_tokens=%s; tokens_used=%s",
            model,
            max_tokens,
            tokens_used,
        )
    return stop_reason
