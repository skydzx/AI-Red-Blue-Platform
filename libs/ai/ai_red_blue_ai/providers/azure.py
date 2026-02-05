"""Azure OpenAI provider implementation."""

from typing import Optional, Any, AsyncIterator
from datetime import datetime, timezone

from openai import AsyncAzureOpenAI

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


class AzureProvider(AIProvider):
    """Azure OpenAI API provider implementation."""

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self._client: Optional[AsyncAzureOpenAI] = None

    def _get_client(self) -> AsyncAzureOpenAI:
        """Get or create AsyncAzureOpenAI client."""
        if self._client is None:
            api_version = self.config.metadata.get("api_version", "2024-02-15-preview")

            self._client = AsyncAzureOpenAI(
                api_key=self.config.api_key or "",
                azure_endpoint=self.config.base_url or "",
                api_version=api_version,
                organization=self.config.organization,
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
        """Send a chat request to Azure OpenAI."""
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

            # Make request
            response = await client.chat.completions.create(**kwargs)

            response_time = (
                datetime.now(timezone.utc) - start_time
            ).total_seconds() * 1000

            return self._convert_response(response, response_time)

        except Exception as e:
            self.logger.error(f"Azure API error: {e}")
            raise

    async def stream_chat(
        self,
        messages: list[ChatMessage],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        tools: Optional[list[dict[str, Any]]] = None,
    ) -> AsyncIterator[StreamEvent]:
        """Stream chat responses from Azure OpenAI."""
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
        """Get available Azure models."""
        if self.config.models:
            return self.config.models

        # Default models - Azure typically deploys OpenAI models
        return [
            ModelConfig(
                name="gpt-4",
                display_name="Azure GPT-4",
                max_tokens=8192,
                max_input_tokens=8192,
                cost_per_1k_input=0.03,
                cost_per_1k_output=0.06,
            ),
            ModelConfig(
                name="gpt-35-turbo",
                display_name="Azure GPT-3.5 Turbo",
                max_tokens=16384,
                max_input_tokens=16384,
                cost_per_1k_input=0.0005,
                cost_per_1k_output=0.0015,
            ),
        ]

    async def health_check(self) -> bool:
        """Check if Azure API is available."""
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
            result.append(message_dict)
        return result

    def _convert_response(
        self,
        response: Any,
        response_time_ms: float,
    ) -> AIResponse:
        """Convert Azure response to AIResponse."""
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
            provider="azure",
            finish_reason=choice.finish_reason,
            response_time_ms=response_time_ms,
        )

    def _convert_chunk(
        self,
        chunk: Any,
    ) -> StreamEvent:
        """Convert Azure chunk to StreamEvent."""
        choice = chunk.choices[0]
        delta = choice.delta

        return StreamEvent(
            event_type="content_delta",
            content=delta.content or "",
            delta=delta.content or "",
            done=choice.finish_reason is not None,
            metadata={
                "role": delta.role.value if delta.role else None,
            },
        )
