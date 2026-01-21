"""
Tests for the LLM Router module

Tests cover:
- Provider initialization
- Fallback behavior
- Error handling
- Mock provider functionality
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import os

# Import the modules we're testing
from src.llm.providers import (
    LLMProvider,
    AnthropicProvider,
    OpenAIProvider,
    MockProvider,
    LLMMessage,
    LLMResponse,
)
from src.llm.router import LLMRouter, ProviderConfig


class TestMockProvider:
    """Tests for MockProvider"""

    @pytest.fixture
    def mock_provider(self):
        return MockProvider()

    @pytest.mark.asyncio
    async def test_generate_returns_response(self, mock_provider):
        """Test that generate returns a valid response"""
        messages = [LLMMessage(role="user", content="Hello")]
        response = await mock_provider.generate(messages)

        assert isinstance(response, LLMResponse)
        assert response.content is not None
        assert len(response.content) > 0
        assert response.model == "mock-model"
        assert response.provider == "mock"

    @pytest.mark.asyncio
    async def test_generate_code_request(self, mock_provider):
        """Test that code-related requests return code-like responses"""
        # MockProvider looks for "code" or "implement" keywords
        messages = [LLMMessage(role="user", content="Write some code to implement this")]
        response = await mock_provider.generate(messages)

        # Should contain code markers
        assert "```" in response.content or "function" in response.content

    @pytest.mark.asyncio
    async def test_generate_analysis_request(self, mock_provider):
        """Test that analysis requests return structured responses"""
        messages = [LLMMessage(role="user", content="Analyze this code")]
        response = await mock_provider.generate(messages)

        assert response.content is not None
        assert len(response.content) > 50

    @pytest.mark.asyncio
    async def test_stream_yields_chunks(self, mock_provider):
        """Test that stream yields multiple chunks"""
        messages = [LLMMessage(role="user", content="Hello")]
        chunks = []

        async for chunk in mock_provider.stream(messages):
            chunks.append(chunk)

        assert len(chunks) > 1
        full_response = "".join(chunks)
        assert len(full_response) > 0

    @pytest.mark.asyncio
    async def test_usage_tracking(self, mock_provider):
        """Test that usage is tracked in responses"""
        messages = [LLMMessage(role="user", content="Hello")]
        response = await mock_provider.generate(messages)

        assert response.usage is not None
        # MockProvider uses input_tokens and output_tokens
        assert response.usage.get("input_tokens", 0) > 0
        assert response.usage.get("output_tokens", 0) > 0


class TestLLMRouter:
    """Tests for LLMRouter"""

    @pytest.fixture
    def router_with_mock(self):
        """Create a router with only mock provider"""
        router = LLMRouter(use_mock_fallback=True)
        return router

    @pytest.mark.asyncio
    async def test_router_initialization(self, router_with_mock):
        """Test that router initializes correctly"""
        assert router_with_mock is not None
        # Should have at least mock provider
        assert len(router_with_mock.providers) >= 1

    @pytest.mark.asyncio
    async def test_generate_with_mock(self, router_with_mock):
        """Test generation falls back to mock when no real providers"""
        messages = [LLMMessage(role="user", content="Hello")]
        response = await router_with_mock.generate(messages)

        assert isinstance(response, LLMResponse)
        assert response.content is not None

    @pytest.mark.asyncio
    async def test_provider_fallback(self):
        """Test that router falls back to next provider on failure"""
        router = LLMRouter(use_mock_fallback=True)

        # Create a failing provider
        failing_provider = AsyncMock(spec=LLMProvider)
        failing_provider.generate = AsyncMock(side_effect=Exception("API Error"))

        # Add failing provider with high priority
        router.providers.insert(0, ProviderConfig(
            name="failing",
            provider=failing_provider,
            priority=100,
            enabled=True
        ))

        messages = [LLMMessage(role="user", content="Hello")]
        response = await router.generate(messages)

        # Should still get a response from fallback
        assert response is not None
        assert response.content is not None

    @pytest.mark.asyncio
    async def test_all_providers_fail(self):
        """Test behavior when all providers fail"""
        router = LLMRouter(use_mock_fallback=False)

        # Remove all providers
        router.providers.clear()

        messages = [LLMMessage(role="user", content="Hello")]

        with pytest.raises(Exception) as exc_info:
            await router.generate(messages)

        assert "No LLM providers available" in str(exc_info.value) or \
               "All providers failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_stats_tracking(self, router_with_mock):
        """Test that router tracks usage statistics"""
        messages = [LLMMessage(role="user", content="Hello")]

        # Make a few requests
        for _ in range(3):
            await router_with_mock.generate(messages)

        stats = router_with_mock.get_stats()
        # get_stats() returns a dict
        assert stats["total_requests"] >= 3

    def test_provider_priority(self):
        """Test that providers are ordered by priority"""
        router = LLMRouter(use_mock_fallback=True)

        # Verify providers are sorted by priority (descending)
        priorities = [p.priority for p in router.providers]
        assert priorities == sorted(priorities, reverse=True)


class TestAnthropicProvider:
    """Tests for AnthropicProvider (mocked)"""

    @pytest.mark.asyncio
    async def test_initialization_without_key(self):
        """Test that provider handles missing API key gracefully"""
        with patch.dict(os.environ, {}, clear=True):
            # Should not raise during initialization
            provider = AnthropicProvider()
            # But should fail on generate
            messages = [LLMMessage(role="user", content="Hello")]

            with pytest.raises(Exception):
                await provider.generate(messages)

    @pytest.mark.asyncio
    async def test_generate_with_mocked_client(self):
        """Test generate with mocked Anthropic client"""
        provider = AnthropicProvider(api_key="test-key")

        # Mock the client (provider uses _client and lazy loads via _get_client)
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Hello, world!")]
        mock_response.model = "claude-sonnet-4-20250514"
        mock_response.usage = MagicMock(
            input_tokens=10,
            output_tokens=5
        )
        mock_response.stop_reason = "end_turn"

        mock_client = MagicMock()
        # The client uses AsyncAnthropic, so messages.create is async
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        with patch.object(provider, '_get_client', return_value=mock_client):
            messages = [LLMMessage(role="user", content="Hello")]
            response = await provider.generate(messages)

            assert response is not None
            assert response.content == "Hello, world!"


class TestOpenAIProvider:
    """Tests for OpenAIProvider (mocked)"""

    @pytest.mark.asyncio
    async def test_initialization_without_key(self):
        """Test that provider handles missing API key gracefully"""
        with patch.dict(os.environ, {}, clear=True):
            provider = OpenAIProvider()
            messages = [LLMMessage(role="user", content="Hello")]

            with pytest.raises(Exception):
                await provider.generate(messages)


class TestIntegration:
    """Integration tests for the LLM system"""

    @pytest.mark.asyncio
    async def test_full_request_cycle(self):
        """Test a complete request cycle through the router"""
        router = LLMRouter(use_mock_fallback=True)

        # Simulate a realistic request
        messages = [
            LLMMessage(role="system", content="You are a helpful assistant."),
            LLMMessage(role="user", content="Write a simple hello world function in Python.")
        ]

        response = await router.generate(
            messages=messages,
            max_tokens=500,
            temperature=0.7
        )

        assert response is not None
        assert response.content is not None
        assert response.provider is not None

    @pytest.mark.asyncio
    async def test_streaming_request(self):
        """Test streaming through the router"""
        router = LLMRouter(use_mock_fallback=True)

        messages = [LLMMessage(role="user", content="Hello")]
        chunks = []

        async for chunk in router.stream(messages):
            chunks.append(chunk)

        assert len(chunks) > 0
        full_response = "".join(chunks)
        assert len(full_response) > 0
