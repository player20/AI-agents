"""
LLM Router - Intelligent routing to multiple LLM providers with fallback

Features:
- Automatic provider selection based on availability
- Fallback chain when primary provider fails
- Cost-aware routing (future)
- Load balancing (future)
- Usage tracking
"""
from typing import List, Optional, Dict, Any, AsyncIterator
from dataclasses import dataclass, field
import logging
import asyncio

from .providers import (
    LLMProvider,
    LLMMessage,
    LLMResponse,
    GrokProvider,
    AnthropicProvider,
    OpenAIProvider,
    MockProvider,
)

logger = logging.getLogger(__name__)


@dataclass
class ProviderConfig:
    """Configuration for an LLM provider"""
    name: str
    provider: LLMProvider
    priority: int = 0  # Higher = preferred
    enabled: bool = True
    max_retries: int = 3
    timeout: float = 60.0


@dataclass
class RouterStats:
    """Statistics for the LLM router"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    provider_usage: Dict[str, int] = field(default_factory=dict)
    total_input_tokens: int = 0
    total_output_tokens: int = 0


class LLMRouter:
    """
    Routes LLM requests to the best available provider with automatic fallback.

    Usage:
        router = LLMRouter()
        router.add_provider(AnthropicProvider(), priority=10)
        router.add_provider(OpenAIProvider(), priority=5)
        router.add_provider(MockProvider(), priority=0)  # Fallback

        response = await router.generate(messages)
    """

    def __init__(self, use_mock_fallback: bool = True):
        """
        Initialize the router.

        Args:
            use_mock_fallback: If True, adds MockProvider as last resort fallback
        """
        self.providers: List[ProviderConfig] = []
        self.stats = RouterStats()
        self._lock = asyncio.Lock()

        if use_mock_fallback:
            self.add_provider(MockProvider(), priority=-1)

    def add_provider(
        self,
        provider: LLMProvider,
        priority: int = 0,
        enabled: bool = True,
        max_retries: int = 3,
        timeout: float = 60.0
    ) -> None:
        """
        Add a provider to the router.

        Args:
            provider: The LLM provider instance
            priority: Higher values are tried first
            enabled: Whether this provider is active
            max_retries: Number of retries on failure
            timeout: Request timeout in seconds
        """
        config = ProviderConfig(
            name=provider.name,
            provider=provider,
            priority=priority,
            enabled=enabled,
            max_retries=max_retries,
            timeout=timeout
        )

        self.providers.append(config)
        # Sort by priority (highest first)
        self.providers.sort(key=lambda p: p.priority, reverse=True)

        logger.info(f"Added provider: {provider.name} with priority {priority}")

    def remove_provider(self, name: str) -> bool:
        """Remove a provider by name"""
        for i, config in enumerate(self.providers):
            if config.name == name:
                del self.providers[i]
                logger.info(f"Removed provider: {name}")
                return True
        return False

    def get_available_providers(self) -> List[str]:
        """Get list of available provider names"""
        return [
            p.name for p in self.providers
            if p.enabled and p.provider.is_available()
        ]

    async def generate(
        self,
        messages: List[LLMMessage],
        max_tokens: int = 4096,
        temperature: float = 0.7,
        preferred_provider: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate a response using the best available provider.

        Args:
            messages: List of messages for the conversation
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            preferred_provider: Optionally specify a preferred provider
            **kwargs: Additional provider-specific arguments

        Returns:
            LLMResponse from the successful provider

        Raises:
            Exception: If all providers fail
        """
        async with self._lock:
            self.stats.total_requests += 1

        # Get providers to try
        providers_to_try = self._get_providers_to_try(preferred_provider)

        if not providers_to_try:
            raise Exception("No LLM providers available")

        last_error = None

        for config in providers_to_try:
            for attempt in range(config.max_retries):
                try:
                    logger.debug(
                        f"Trying provider {config.name}, attempt {attempt + 1}"
                    )

                    response = await asyncio.wait_for(
                        config.provider.generate(
                            messages=messages,
                            max_tokens=max_tokens,
                            temperature=temperature,
                            **kwargs
                        ),
                        timeout=config.timeout
                    )

                    # Success! Update stats
                    async with self._lock:
                        self.stats.successful_requests += 1
                        self.stats.provider_usage[config.name] = (
                            self.stats.provider_usage.get(config.name, 0) + 1
                        )
                        if response.usage:
                            self.stats.total_input_tokens += response.usage.get(
                                "input_tokens", 0
                            )
                            self.stats.total_output_tokens += response.usage.get(
                                "output_tokens", 0
                            )

                    logger.info(f"Generated response with {config.name}")
                    return response

                except asyncio.TimeoutError:
                    last_error = f"Timeout with {config.name}"
                    logger.warning(last_error)
                except Exception as e:
                    last_error = f"Error with {config.name}: {str(e)}"
                    logger.warning(last_error)

                # Brief delay before retry
                if attempt < config.max_retries - 1:
                    await asyncio.sleep(0.5 * (attempt + 1))

        # All providers failed
        async with self._lock:
            self.stats.failed_requests += 1

        raise Exception(f"All LLM providers failed. Last error: {last_error}")

    async def stream(
        self,
        messages: List[LLMMessage],
        max_tokens: int = 4096,
        temperature: float = 0.7,
        preferred_provider: Optional[str] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Stream a response using the best available provider.

        Args:
            messages: List of messages for the conversation
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            preferred_provider: Optionally specify a preferred provider
            **kwargs: Additional provider-specific arguments

        Yields:
            Text chunks as they are generated

        Raises:
            Exception: If all providers fail
        """
        providers_to_try = self._get_providers_to_try(preferred_provider)

        if not providers_to_try:
            raise Exception("No LLM providers available")

        last_error = None

        for config in providers_to_try:
            try:
                logger.debug(f"Streaming with provider {config.name}")

                async for chunk in config.provider.stream(
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    **kwargs
                ):
                    yield chunk

                # If we get here, streaming succeeded
                logger.info(f"Streamed response with {config.name}")
                return

            except Exception as e:
                last_error = f"Error streaming with {config.name}: {str(e)}"
                logger.warning(last_error)

        raise Exception(f"All LLM providers failed for streaming. Last error: {last_error}")

    def _get_providers_to_try(
        self,
        preferred_provider: Optional[str] = None
    ) -> List[ProviderConfig]:
        """Get ordered list of providers to try"""
        available = [
            p for p in self.providers
            if p.enabled and p.provider.is_available()
        ]

        if preferred_provider:
            # Move preferred provider to front
            preferred = [p for p in available if p.name == preferred_provider]
            others = [p for p in available if p.name != preferred_provider]
            return preferred + others

        return available

    def get_stats(self) -> Dict[str, Any]:
        """Get router statistics"""
        return {
            "total_requests": self.stats.total_requests,
            "successful_requests": self.stats.successful_requests,
            "failed_requests": self.stats.failed_requests,
            "success_rate": (
                self.stats.successful_requests / self.stats.total_requests
                if self.stats.total_requests > 0 else 0
            ),
            "provider_usage": self.stats.provider_usage,
            "total_input_tokens": self.stats.total_input_tokens,
            "total_output_tokens": self.stats.total_output_tokens,
            "available_providers": self.get_available_providers(),
        }


# Global router instance
_router: Optional[LLMRouter] = None


def get_llm_router() -> LLMRouter:
    """
    Get or create the global LLM router instance.

    Provider priority (highest first):
    1. Grok (xAI) - Primary provider (priority 15)
    2. Anthropic (Claude) - Fallback (priority 10)
    3. OpenAI (GPT-4) - Secondary fallback (priority 5)
    4. Mock - Development fallback (priority -1)

    Providers are added based on available API keys.
    """
    global _router

    if _router is None:
        _router = LLMRouter(use_mock_fallback=True)

        # Add Grok (xAI) as primary if API key is available
        grok = GrokProvider()
        if grok.is_available():
            _router.add_provider(grok, priority=15)
            logger.info("Grok (xAI) provider enabled as PRIMARY")

        # Add Anthropic as fallback if API key is available
        anthropic = AnthropicProvider()
        if anthropic.is_available():
            _router.add_provider(anthropic, priority=10)
            logger.info("Anthropic provider enabled as FALLBACK")

        # Add OpenAI as secondary fallback if API key is available
        openai = OpenAIProvider()
        if openai.is_available():
            _router.add_provider(openai, priority=5)
            logger.info("OpenAI provider enabled as secondary fallback")

    return _router
