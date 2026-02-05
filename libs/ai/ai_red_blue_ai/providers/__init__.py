"""AI provider adapters for different LLM services."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Any, AsyncIterator
from datetime import datetime, timezone

import httpx
from pydantic import BaseModel, Field

from ai_red_blue_common import get_logger


class ProviderType(str, Enum):
    """Supported AI provider types."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE = "azure"
    LOCAL = "local"
    CUSTOM = "custom"


class ChatRole(str, Enum):
    """Chat message roles."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"
    TOOL = "tool"


class ChatMessage(BaseModel):
    """Chat message model."""

    role: ChatRole
    content: str
    name: Optional[str] = None
    tool_calls: Optional[list[dict[str, Any]]] = None
    tool_call_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TokenUsage(BaseModel):
    """Token usage information."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    def __add__(self, other: "TokenUsage") -> "TokenUsage":
        """Add token usages together."""
        return TokenUsage(
            prompt_tokens=self.prompt_tokens + other.prompt_tokens,
            completion_tokens=self.completion_tokens + other.completion_tokens,
            total_tokens=self.total_tokens + other.total_tokens,
        )


class AIResponse(BaseModel):
    """AI model response."""

    content: str
    role: ChatRole = ChatRole.ASSISTANT
    usage: Optional[TokenUsage] = None
    model: Optional[str] = None
    provider: Optional[str] = None
    finish_reason: Optional[str] = None
    response_time_ms: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def has_content(self) -> bool:
        """Check if response has content."""
        return bool(self.content)


class StreamEvent(BaseModel):
    """Streaming event from AI provider."""

    event_type: str
    content: str = ""
    delta: str = ""
    done: bool = False
    usage: Optional[TokenUsage] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ModelConfig(BaseModel):
    """Configuration for a specific model."""

    name: str
    display_name: str = ""
    max_tokens: int = 4096
    max_input_tokens: int = 8192
    supports_streaming: bool = True
    supports_functions: bool = True
    supports_vision: bool = False
    context_window: int = 8192
    default_temperature: float = 0.7
    cost_per_1k_input: float = 0.0
    cost_per_1k_output: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProviderConfig(BaseModel):
    """Configuration for an AI provider."""

    type: ProviderType
    name: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    organization: Optional[str] = None
    models: list[ModelConfig] = Field(default_factory=list)
    default_model: Optional[str] = None
    timeout_seconds: int = 60
    max_retries: int = 3
    enabled: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class AIProvider(ABC):
    """Abstract base class for AI providers."""

    def __init__(self, config: ProviderConfig):
        self.config = config
        self.logger = get_logger(self.__class__.__name__.lower())
        self._client: Optional[httpx.Client] = None

    @abstractmethod
    async def chat(
        self,
        messages: list[ChatMessage],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        tools: Optional[list[dict[str, Any]]] = None,
    ) -> AIResponse:
        """Send a chat request to the provider."""
        pass

    @abstractmethod
    async def stream_chat(
        self,
        messages: list[ChatMessage],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        tools: Optional[list[dict[str, Any]]] = None,
    ) -> AsyncIterator[StreamEvent]:
        """Stream chat responses from the provider."""
        pass

    @abstractmethod
    def get_models(self) -> list[ModelConfig]:
        """Get available models for this provider."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the provider is available."""
        pass

    def get_model(self, name: Optional[str] = None) -> Optional[ModelConfig]:
        """Get a model configuration by name."""
        model_name = name or self.config.default_model
        if not model_name:
            return None

        for model in self.config.models:
            if model.name == model_name:
                return model
        return None

    def _get_client(self) -> httpx.Client:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.Client(
                timeout=self.config.timeout_seconds,
                limits=httpx.Limits(max_keepalive_connections=5),
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    def __enter__(self) -> "AIProvider":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()


# Provider registry
_providers: dict[str, AIProvider] = {}


def register_provider(provider: AIProvider) -> None:
    """Register a provider."""
    _providers[provider.config.name] = provider


def get_provider(name: str) -> Optional[AIProvider]:
    """Get a registered provider by name."""
    return _providers.get(name)


def list_providers() -> list[str]:
    """List all registered provider names."""
    return list(_providers.keys())


# Import concrete providers (after base classes are defined)
from .openai import OpenAIProvider
from .anthropic import AnthropicProvider
from .azure import AzureProvider


class ProviderType(str, Enum):
    """Supported AI provider types."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE = "azure"
    LOCAL = "local"
    CUSTOM = "custom"


class ChatRole(str, Enum):
    """Chat message roles."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"
    TOOL = "tool"


class ChatMessage(BaseModel):
    """Chat message model."""

    role: ChatRole
    content: str
    name: Optional[str] = None
    tool_calls: Optional[list[dict[str, Any]]] = None
    tool_call_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TokenUsage(BaseModel):
    """Token usage information."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    def __add__(self, other: "TokenUsage") -> "TokenUsage":
        """Add token usages together."""
        return TokenUsage(
            prompt_tokens=self.prompt_tokens + other.prompt_tokens,
            completion_tokens=self.completion_tokens + other.completion_tokens,
            total_tokens=self.total_tokens + other.total_tokens,
        )


class AIResponse(BaseModel):
    """AI model response."""

    content: str
    role: ChatRole = ChatRole.ASSISTANT
    usage: Optional[TokenUsage] = None
    model: Optional[str] = None
    provider: Optional[str] = None
    finish_reason: Optional[str] = None
    response_time_ms: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def has_content(self) -> bool:
        """Check if response has content."""
        return bool(self.content)


class StreamEvent(BaseModel):
    """Streaming event from AI provider."""

    event_type: str
    content: str = ""
    delta: str = ""
    done: bool = False
    usage: Optional[TokenUsage] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ModelConfig(BaseModel):
    """Configuration for a specific model."""

    name: str
    display_name: str = ""
    max_tokens: int = 4096
    max_input_tokens: int = 8192
    supports_streaming: bool = True
    supports_functions: bool = True
    supports_vision: bool = False
    context_window: int = 8192
    default_temperature: float = 0.7
    cost_per_1k_input: float = 0.0
    cost_per_1k_output: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProviderConfig(BaseModel):
    """Configuration for an AI provider."""

    type: ProviderType
    name: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    organization: Optional[str] = None
    models: list[ModelConfig] = Field(default_factory=list)
    default_model: Optional[str] = None
    timeout_seconds: int = 60
    max_retries: int = 3
    enabled: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class AIProvider(ABC):
    """Abstract base class for AI providers."""

    def __init__(self, config: ProviderConfig):
        self.config = config
        self.logger = get_logger(self.__class__.__name__.lower())
        self._client: Optional[httpx.Client] = None

    @abstractmethod
    async def chat(
        self,
        messages: list[ChatMessage],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        tools: Optional[list[dict[str, Any]]] = None,
    ) -> AIResponse:
        """Send a chat request to the provider."""
        pass

    @abstractmethod
    async def stream_chat(
        self,
        messages: list[ChatMessage],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        tools: Optional[list[dict[str, Any]]] = None,
    ) -> AsyncIterator[StreamEvent]:
        """Stream chat responses from the provider."""
        pass

    @abstractmethod
    def get_models(self) -> list[ModelConfig]:
        """Get available models for this provider."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the provider is available."""
        pass

    def get_model(self, name: Optional[str] = None) -> Optional[ModelConfig]:
        """Get a model configuration by name."""
        model_name = name or self.config.default_model
        if not model_name:
            return None

        for model in self.config.models:
            if model.name == model_name:
                return model
        return None

    def _get_client(self) -> httpx.Client:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.Client(
                timeout=self.config.timeout_seconds,
                limits=httpx.Limits(max_keepalive_connections=5),
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    def __enter__(self) -> "AIProvider":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()


# Provider registry
_providers: dict[str, AIProvider] = {}


def register_provider(provider: AIProvider) -> None:
    """Register a provider."""
    _providers[provider.config.name] = provider


def get_provider(name: str) -> Optional[AIProvider]:
    """Get a registered provider by name."""
    return _providers.get(name)


def list_providers() -> list[str]:
    """List all registered provider names."""
    return list(_providers.keys())
