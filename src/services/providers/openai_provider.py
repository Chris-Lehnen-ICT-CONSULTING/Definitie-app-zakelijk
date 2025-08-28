"""
OpenAIProvider - Implementatie van AIProviderInterface op basis van OpenAI SDK.

Deze provider encapsuleert de OpenAI-klant en vertaalt AIMessage-lijsten
naar het formaat dat de OpenAI chat.completions API verwacht.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv
from openai import OpenAI
from services.interfaces import AIMessage, AIProviderInterface


class OpenAIProvider(AIProviderInterface):
    """Concreet AI-provider voor OpenAI chat/completions API."""

    def __init__(self) -> None:
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY ontbreekt. Zet deze in .env of secrets store."
            )
        self._client = OpenAI(api_key=api_key)

    def chat(
        self,
        messages: list[AIMessage],
        model: str,
        temperature: float,
        max_tokens: int,
    ) -> tuple[str, int]:
        # Converteer naar OpenAI-formaat
        oai_messages = [{"role": m.role, "content": m.content} for m in messages]

        if model == "gpt-5":
            response = self._client.chat.completions.create(
                model=model,
                messages=oai_messages,
                temperature=temperature,
                max_completion_tokens=max_tokens,
            )
        else:
            response = self._client.chat.completions.create(
                model=model,
                messages=oai_messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

        content = response.choices[0].message.content.strip()
        tokens = response.usage.total_tokens if response.usage else 0
        return content, tokens
