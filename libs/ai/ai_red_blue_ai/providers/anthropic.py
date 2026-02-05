"""Anthropic provider implementation."""

from typing import Optional, Any, AsyncIterator
from datetime import datetime, timezone

import httpx
from anthropic import AsyncAnthropic

from . import (
    AIProvider,
    ProviderConfig,
    ModelConfig,
    ChatMessage,
    ChatRole,
    AIResponse,
    StreamEvent,
    TokenUsage,
)


class AnthropicProvider(AIProvider):
    """Anthropic Claude API provider implementation."""

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self._client: Optional[AsyncAnthropic] = None

    def _get_client(self) -> AsyncAnthropic:
        """Get or create AsyncAnthropic client."""
        if self._client is None:
            self._client = AsyncAnthropic(
                api_key=self.config.api_key or "",
                timeout=self.config.timeout_seconds,
            )
        return self._client

    async def chat(
        self,
        messages: list[ChatMessage],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        tools: Optional[list[dict[str, Any]]] = None,
    ) -> AIResponse:
        """Send a chat request to Anthropic Claude."""
        client = self._get_client()
        model_config = self.get_model(model)
        start_time = datetime.now(timezone.utc)

        try:
            # Convert messages to Anthropic format
            anthropic_messages = self._convert_messages(messages)

            kwargs: dict[str, Any] = {
                "model": model or self.config.default_model or "claude-3-sonnet-20240229",
                "messages": anthropic_messages,
                "stream": stream,
            }

            if temperature is not None:
                kwargs["temperature"] = temperature
            elif model_config:
                kwargs["temperature"] = model_config.default_temperature

            if max_tokens:
                kwargs["max_tokens"] = max_tokens

            response = await client.messages.create(**kwargs)

            response_time = (
                datetime.now(timezone.utc) - start_time
            ).total_seconds() * 1000

            return self._convert_response(response, response_time)

        except Exception as e:
            self.logger.error(f"Anthropic API error: {e}")
            raise

    async def stream_chat(
        self,
        messages: list[ChatMessage],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        tools: Optional[list[dict[str, Any]]] = None,
    ) -> AsyncIterator[StreamEvent]:
        """Stream chat responses from Anthropic Claude."""
        client = self._get_client()

        anthropic_messages = self._convert_messages(messages)

        kwargs: dict[str, Any] = {
            "model": model or self.config.default_model or "claude-3-sonnet-20240229",
            "messages": anthropic_messages,
            "stream": True,
        }

        if temperature is not None:
            kwargs["temperature"] = temperature

        if max_tokens:
            kwargs["max_tokens"] = max_tokens

        stream = await client.messages.create(**kwargs)

        async for chunk in stream:
            yield self._convert_chunk(chunk)

    def get_models(self) -> list[ModelConfig]:
        """Get available Anthropic models."""
        if self.config.models:
            return self.config.models

        return [
            ModelConfig(
                name="claude-3-opus-20240229",
                display_name="Claude 3 Opus",
                max_tokens=4096,
                max_input_tokens=200000,
                context_window=200000,
                cost_per_1k_input=0.015,
                cost_per_1k_output=0.075,
            ),
            ModelConfig(
                name="claude-3-sonnet-20240229",
                display_name="Claude 3 Sonnet",
                max_tokens=4096,
                max_input_tokens=200000,
                context_window=200000,
                cost_per_1k_input=0.003,
                cost_per_1k_output=0.015,
            ),
            ModelConfig(
                name="claude-3-haiku-20240307",
                display_name="Claude 3 Haiku",
                max_tokens=4096,
                max_input_tokens=200000,
                context_window=200000,
                cost_per_1k_input=0.00025,
                cost_per_1k_output=0.00125,
            ),
        ]

    async def health_check(self) -> bool:
        """Check if Anthropic API is available."""
        try:
            client = self._get_client()
            await client.messages.list(limit=1)
            return True
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False

    def _convert_messages(
        self,
        messages: list[ChatMessage],
    ) -> list[dict[str, Any]]:
        """Convert messages to Anthropic format."""
        result = []
        for msg in messages:
            message_dict: dict[str, Any] = {
                "role": msg.role.value,
                "content": msg.content,
            }
            if msg.name:
                message_dict["name"] = msg.name
            result.append(message_dict)
        return result

    def _convert_response(
        self,
        response: Any,
        response_time_ms: float,
    ) -> AIResponse:
        """Convert Anthropic response to AIResponse."""
        content = ""
        if response.content:
            content = response.content[0].text if hasattr(response.content[0], 'text') else str(response.content[0])

        usage = None
        if response.usage:
            usage = TokenUsage(
                prompt_tokens=response.usage.input_tokens,
                completion_tokens=response.usage.output_tokens,
                total_tokens=response.usage.input_tokens + response.usage.output_tokens,
            )

        return AIResponse(
            content=content,
            role=ChatRole.ASSISTANT,
            usage=usage,
            model=response.model,
            provider="anthropic",
            finish_reason=str(response.stop_reason) if response.stop_reason else None,
            response_time_ms=response_time_ms,
        )

    def _convert_chunk(
        self,
        chunk: Any,
    ) -> StreamEvent:
        """Convert Anthropic chunk to StreamEvent."""
        event_type = type(chunk).__name__
        content = ""

        if hasattr(chunk, 'delta'):
            content = chunk.delta.text if hasattr(chunk.delta, 'text') else ""

        return StreamEvent(
            event_type=event_type,
            content=content,
            delta=content,
            done=False,
        )
