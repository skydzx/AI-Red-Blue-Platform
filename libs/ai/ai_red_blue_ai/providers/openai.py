"""OpenAI provider implementation."""

import json
from typing import Optional, Any, AsyncIterator
from datetime import datetime, timezone

import httpx
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion, ChatCompletionChunk

from . import (
    AIProvider,
    ProviderConfig,
    ModelConfig,
    ChatMessage,
    ChatRole,
    AIResponse,
    StreamEvent,
    TokenUsage,
    ProviderType,
)


class OpenAIProvider(AIProvider):
    """OpenAI API provider implementation."""

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self._client: Optional[AsyncOpenAI] = None

    def _get_client(self) -> AsyncOpenAI:
        """Get or create AsyncOpenAI client."""
        if self._client is None:
            self._client = AsyncOpenAI(
                api_key=self.config.api_key or "",
                organization=self.config.organization,
                base_url=self.config.base_url,
                timeout=self.config.timeout_seconds,
                max_retries=self.config.max_retries,
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
        """Send a chat request to OpenAI."""
        client = self._get_client()
        model_config = self.get_model(model)
        start_time = datetime.now(timezone.utc)

        try:
            # Convert messages to OpenAI format
            openai_messages = self._convert_messages(messages)

            # Build request kwargs
            kwargs: dict[str, Any] = {
                "model": model or self.config.default_model,
                "messages": openai_messages,
                "stream": stream,
            }

            if temperature is not None:
                kwargs["temperature"] = temperature
            elif model_config:
                kwargs["temperature"] = model_config.default_temperature

            if max_tokens:
                kwargs["max_tokens"] = max_tokens
            elif model_config:
                kwargs["max_tokens"] = model_config.max_tokens

            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "auto"

            # Make request
            response: ChatCompletion = await client.chat.completions.create(
                **kwargs
            )

            response_time = (
                datetime.now(timezone.utc) - start_time
            ).total_seconds() * 1000

            # Convert response
            return self._convert_response(response, response_time)

        except Exception as e:
            self.logger.error(f"OpenAI API error: {e}")
            raise

    async def stream_chat(
        self,
        messages: list[ChatMessage],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        tools: Optional[list[dict[str, Any]]] = None,
    ) -> AsyncIterator[StreamEvent]:
        """Stream chat responses from OpenAI."""
        client = self._get_client()
        model_config = self.get_model(model)

        openai_messages = self._convert_messages(messages)

        kwargs: dict[str, Any] = {
            "model": model or self.config.default_model,
            "messages": openai_messages,
            "stream": True,
        }

        if temperature is not None:
            kwargs["temperature"] = temperature
        elif model_config:
            kwargs["temperature"] = model_config.default_temperature

        if max_tokens:
            kwargs["max_tokens"] = max_tokens

        if tools:
            kwargs["tools"] = tools

        stream = await client.chat.completions.create(**kwargs)

        async for chunk in stream:
            yield self._convert_chunk(chunk)

    def get_models(self) -> list[ModelConfig]:
        """Get available OpenAI models."""
        if self.config.models:
            return self.config.models

        # Default models
        return [
            ModelConfig(
                name="gpt-4o",
                display_name="GPT-4o",
                max_tokens=16384,
                max_input_tokens=128000,
                supports_vision=True,
                cost_per_1k_input=0.005,
                cost_per_1k_output=0.015,
            ),
            ModelConfig(
                name="gpt-4o-mini",
                display_name="GPT-4o Mini",
                max_tokens=16384,
                max_input_tokens=128000,
                cost_per_1k_input=0.00015,
                cost_per_1k_output=0.0006,
            ),
            ModelConfig(
                name="gpt-4-turbo",
                display_name="GPT-4 Turbo",
                max_tokens=128000,
                max_input_tokens=128000,
                supports_vision=True,
                cost_per_1k_input=0.01,
                cost_per_1k_output=0.03,
            ),
            ModelConfig(
                name="gpt-4",
                display_name="GPT-4",
                max_tokens=8192,
                max_input_tokens=8192,
                cost_per_1k_input=0.03,
                cost_per_1k_output=0.06,
            ),
            ModelConfig(
                name="gpt-3.5-turbo",
                display_name="GPT-3.5 Turbo",
                max_tokens=16384,
                max_input_tokens=16384,
                cost_per_1k_input=0.0005,
                cost_per_1k_output=0.0015,
            ),
        ]

    async def health_check(self) -> bool:
        """Check if OpenAI API is available."""
        try:
            client = self._get_client()
            await client.models.list()
            return True
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False

    def _convert_messages(
        self,
        messages: list[ChatMessage],
    ) -> list[dict[str, Any]]:
        """Convert messages to OpenAI format."""
        result = []
        for msg in messages:
            message_dict: dict[str, Any] = {
                "role": msg.role.value,
                "content": msg.content,
            }
            if msg.name:
                message_dict["name"] = msg.name
            if msg.tool_calls:
                message_dict["tool_calls"] = msg.tool_calls
            if msg.tool_call_id:
                message_dict["tool_call_id"] = msg.tool_call_id
            result.append(message_dict)
        return result

    def _convert_response(
        self,
        response: ChatCompletion,
        response_time_ms: float,
    ) -> AIResponse:
        """Convert OpenAI response to AIResponse."""
        choice = response.choices[0]
        message = choice.message

        usage = None
        if response.usage:
            usage = TokenUsage(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
            )

        return AIResponse(
            content=message.content or "",
            role=ChatRole(message.role.value) if message.role else ChatRole.ASSISTANT,
            usage=usage,
            model=response.model,
            provider="openai",
            finish_reason=choice.finish_reason,
            response_time_ms=response_time_ms,
            metadata={
                "object": response.object,
                "created": response.created,
                "system_fingerprint": response.system_fingerprint,
            },
        )

    def _convert_chunk(
        self,
        chunk: ChatCompletionChunk,
    ) -> StreamEvent:
        """Convert OpenAI chunk to StreamEvent."""
        choice = chunk.choices[0]
        delta = choice.delta

        usage = None
        if chunk.usage:
            usage = TokenUsage(
                prompt_tokens=chunk.usage.prompt_tokens,
                completion_tokens=chunk.usage.completion_tokens,
                total_tokens=chunk.usage.total_tokens,
            )

        return StreamEvent(
            event_type="content_delta",
            content=delta.content or "",
            delta=delta.content or "",
            done=choice.finish_reason is not None,
            usage=usage,
            metadata={
                "role": delta.role.value if delta.role else None,
                "tool_calls": delta.tool_calls,
            },
        )
