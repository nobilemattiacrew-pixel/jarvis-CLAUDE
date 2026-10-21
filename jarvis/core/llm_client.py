"""LLM client for JARVIS.

Handles communication with the configured AI provider (Anthropic Claude or OpenAI).
Provides a unified interface for sending messages and receiving responses.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from jarvis.config import Config
from jarvis.utils.logger import get_logger

logger = get_logger(__name__)


class LLMClient:
    """Unified LLM client for Anthropic and OpenAI providers."""

    def __init__(self) -> None:
        """Initialize the LLM client based on configuration."""
        self.provider = Config.AI_PROVIDER.lower()
        self.model = Config.MODEL
        self.logger = logger

        if self.provider == "anthropic":
            try:
                import anthropic

                if not Config.ANTHROPIC_API_KEY:
                    raise ValueError("Anthropic API key not set in configuration")
                self.client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)
                self.logger.info(
                    f"Initialized Anthropic client with model: {self.model}"
                )
            except ImportError:
                self.logger.error(
                    "Anthropic package not installed. Install with: pip install anthropic"
                )
                raise
        elif self.provider == "frellapi":
            try:
                import anthropic

                # FreeLLMAPI uses the same Anthropic client but requires a custom base URL.
                # API key may be optional; we still require a non‑empty value for consistency.
                if not Config.FLLMAPI_API_KEY:
                    raise ValueError("FreeLLMAPI API key not set in configuration")
                # base_url overrides the default Anthropic endpoint.
                self.client = anthropic.Anthropic(
                    api_key=Config.FLLMAPI_API_KEY,
                    base_url=Config.FLLMAPI_BASE_URL,
                )
                self.logger.info(
                    f"Initialized FreeLLMAPI client (Anthropic compatible) with endpoint: {Config.FLLMAPI_BASE_URL}"
                )
            except ImportError:
                self.logger.error(
                    "Anthropic package not installed (required for FreeLLMAPI). Install with: pip install anthropic"
                )
                raise
        elif self.provider == "openai":
            try:
                import openai

                self.client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
                self.logger.info(
                    f"Initialized OpenAI client with model: {self.model}"
                )
            except ImportError:
                self.logger.error(
                    "OpenAI package not installed. Install with: pip install openai"
                )
                raise
        else:
            raise ValueError(
                f"Unsupported AI provider: {self.provider}. Use 'anthropic' or 'openai'."
            )

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Send a chat completion request to the LLM.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
            temperature: Sampling temperature (0.0 to 1.0).
            max_tokens: Maximum tokens to generate.

        Returns:
            The LLM's response text.

        Raises:
            Exception: If the API call fails.
        """
        try:
            if self.provider == "anthropic":
                # Convert to Anthropic messages format
                anthropic_messages = []
                for msg in messages:
                    if msg["role"] == "system":
                        # Anthropic uses system parameter separately
                        continue
                    anthropic_messages.append(
                        {"role": msg["role"], "content": msg["content"]}
                    )

                # Prepare system message if present
                system_msg = ""
                for msg in messages:
                    if msg["role"] == "system":
                        system_msg = msg["content"]
                        break

                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=max_tokens or 1024,
                    system=system_msg or None,
                    messages=anthropic_messages,
                )
                return response.content[0].text

            elif self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                return response.choices[0].message.content

            elif self.provider == "frellapi":
                # FreeLLMAPI exposes an Anthropic-compatible /v1/messages endpoint.
                # We reuse the same Anthropic client initialized with the custom base_url.
                anthropic_messages = []
                system_msg = ""
                for msg in messages:
                    if msg["role"] == "system":
                        system_msg = msg["content"]
                    else:
                        anthropic_messages.append(
                            {"role": msg["role"], "content": msg["content"]}
                        )

                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=max_tokens or 1024,
                    system=system_msg or None,
                    messages=anthropic_messages,
                )
                return response.content[0].text

        except Exception as e:
            self.logger.error(f"LLM API call failed: {e}")
            raise

    def simple_chat(self, user_message: str, system_prompt: str = "") -> str:
        """Simplified interface for a single user message.

        Args:
            user_message: The user's input text.
            system_prompt: Optional system prompt to set behavior.

        Returns:
            The LLM's response text.
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_message})
        return self.chat_completion(messages)