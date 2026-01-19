"""
LLM Provider implementations for multi-provider support

Supported providers:
- Grok (xAI) - Primary provider
- Anthropic (Claude) - Fallback
- OpenAI (GPT-4)
- Mock (for local development)

Future providers:
- Google (Gemini)
- Groq (fast inference)
- Together AI
- Local models (Ollama)

Environment variables:
- XAI_API_KEY or GROK_API_KEY: xAI Grok API key
- ANTHROPIC_API_KEY: Anthropic Claude API key
- OPENAI_API_KEY: OpenAI API key
"""
from abc import ABC, abstractmethod
from typing import Optional, AsyncIterator, Dict, Any, List
from dataclasses import dataclass
import asyncio
import logging
import os

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """Standard response from any LLM provider"""
    content: str
    model: str
    provider: str
    usage: Optional[Dict[str, int]] = None
    finish_reason: Optional[str] = None
    raw_response: Optional[Any] = None


@dataclass
class LLMMessage:
    """Standard message format for LLM requests"""
    role: str  # "system", "user", "assistant"
    content: str


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""

    name: str = "base"

    @abstractmethod
    async def generate(
        self,
        messages: List[LLMMessage],
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """Generate a response from the LLM"""
        pass

    @abstractmethod
    async def stream(
        self,
        messages: List[LLMMessage],
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs
    ) -> AsyncIterator[str]:
        """Stream a response from the LLM"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this provider is configured and available"""
        pass


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider"""

    name = "anthropic"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514"
    ):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = model
        self._client = None

    def _get_client(self):
        """Lazy load the Anthropic client"""
        if self._client is None:
            try:
                import anthropic
                self._client = anthropic.AsyncAnthropic(api_key=self.api_key)
            except ImportError:
                logger.warning("anthropic package not installed")
                raise
        return self._client

    def is_available(self) -> bool:
        """Check if Anthropic API key is configured"""
        return bool(self.api_key)

    async def generate(
        self,
        messages: List[LLMMessage],
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """Generate a response from Claude"""
        client = self._get_client()

        # Convert to Anthropic format
        system_message = None
        api_messages = []

        for msg in messages:
            if msg.role == "system":
                system_message = msg.content
            else:
                api_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })

        response = await client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_message or "",
            messages=api_messages,
            **kwargs
        )

        return LLMResponse(
            content=response.content[0].text,
            model=self.model,
            provider=self.name,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
            finish_reason=response.stop_reason,
            raw_response=response
        )

    async def stream(
        self,
        messages: List[LLMMessage],
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs
    ) -> AsyncIterator[str]:
        """Stream a response from Claude"""
        client = self._get_client()

        # Convert to Anthropic format
        system_message = None
        api_messages = []

        for msg in messages:
            if msg.role == "system":
                system_message = msg.content
            else:
                api_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })

        async with client.messages.stream(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_message or "",
            messages=api_messages,
            **kwargs
        ) as stream:
            async for text in stream.text_stream:
                yield text


class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider"""

    name = "openai"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o"
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self._client = None

    def _get_client(self):
        """Lazy load the OpenAI client"""
        if self._client is None:
            try:
                import openai
                self._client = openai.AsyncOpenAI(api_key=self.api_key)
            except ImportError:
                logger.warning("openai package not installed")
                raise
        return self._client

    def is_available(self) -> bool:
        """Check if OpenAI API key is configured"""
        return bool(self.api_key)

    async def generate(
        self,
        messages: List[LLMMessage],
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """Generate a response from GPT"""
        client = self._get_client()

        # Convert to OpenAI format
        api_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

        response = await client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=api_messages,
            **kwargs
        )

        choice = response.choices[0]

        return LLMResponse(
            content=choice.message.content,
            model=self.model,
            provider=self.name,
            usage={
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
            },
            finish_reason=choice.finish_reason,
            raw_response=response
        )

    async def stream(
        self,
        messages: List[LLMMessage],
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs
    ) -> AsyncIterator[str]:
        """Stream a response from GPT"""
        client = self._get_client()

        # Convert to OpenAI format
        api_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

        stream = await client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=api_messages,
            stream=True,
            **kwargs
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


class GrokProvider(LLMProvider):
    """xAI Grok provider - uses OpenAI-compatible API"""

    name = "grok"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "grok-3-latest"
    ):
        self.api_key = api_key or os.getenv("XAI_API_KEY") or os.getenv("GROK_API_KEY")
        self.model = model
        self.base_url = "https://api.x.ai/v1"
        self._client = None

    def _get_client(self):
        """Lazy load the OpenAI-compatible client for xAI"""
        if self._client is None:
            try:
                import openai
                self._client = openai.AsyncOpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url
                )
            except ImportError:
                logger.warning("openai package not installed (required for Grok)")
                raise
        return self._client

    def is_available(self) -> bool:
        """Check if Grok API key is configured"""
        return bool(self.api_key)

    async def generate(
        self,
        messages: List[LLMMessage],
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """Generate a response from Grok"""
        client = self._get_client()

        # Convert to OpenAI format
        api_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

        response = await client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=api_messages,
            **kwargs
        )

        choice = response.choices[0]

        return LLMResponse(
            content=choice.message.content,
            model=self.model,
            provider=self.name,
            usage={
                "input_tokens": response.usage.prompt_tokens if response.usage else 0,
                "output_tokens": response.usage.completion_tokens if response.usage else 0,
            },
            finish_reason=choice.finish_reason,
            raw_response=response
        )

    async def stream(
        self,
        messages: List[LLMMessage],
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs
    ) -> AsyncIterator[str]:
        """Stream a response from Grok"""
        client = self._get_client()

        # Convert to OpenAI format
        api_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

        stream = await client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=api_messages,
            stream=True,
            **kwargs
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


class MockProvider(LLMProvider):
    """Mock provider for local development and testing"""

    name = "mock"

    def __init__(self, delay: float = 0.5):
        self.delay = delay

    def is_available(self) -> bool:
        """Mock is always available"""
        return True

    async def generate(
        self,
        messages: List[LLMMessage],
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """Generate a mock response"""
        await asyncio.sleep(self.delay)

        # Get the last user message for context
        user_message = ""
        for msg in reversed(messages):
            if msg.role == "user":
                user_message = msg.content
                break

        # Generate contextual mock response
        content = self._generate_mock_content(user_message)

        return LLMResponse(
            content=content,
            model="mock-model",
            provider=self.name,
            usage={
                "input_tokens": sum(len(m.content.split()) for m in messages),
                "output_tokens": len(content.split()),
            },
            finish_reason="stop"
        )

    async def stream(
        self,
        messages: List[LLMMessage],
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs
    ) -> AsyncIterator[str]:
        """Stream a mock response"""
        response = await self.generate(messages, max_tokens, temperature, **kwargs)

        # Stream word by word
        words = response.content.split()
        for word in words:
            await asyncio.sleep(0.05)
            yield word + " "

    def _generate_mock_content(self, user_message: str) -> str:
        """Generate contextual mock content based on the user message"""
        user_lower = user_message.lower()

        if "code" in user_lower or "implement" in user_lower:
            return """Here's the implementation:

```typescript
// Generated code for your request
export function processRequest(input: string): Result {
  // Validate input
  if (!input || input.trim().length === 0) {
    throw new Error('Input is required');
  }

  // Process the request
  const processed = input.trim().toLowerCase();

  return {
    success: true,
    data: processed,
    timestamp: new Date().toISOString()
  };
}
```

This code handles the core functionality you requested. Let me know if you need any modifications."""

        elif "design" in user_lower or "ui" in user_lower or "ux" in user_lower:
            return """Based on your requirements, I recommend the following design approach:

1. **Layout**: Use a clean, card-based layout with ample whitespace
2. **Colors**: Primary blue (#3B82F6) with neutral grays for hierarchy
3. **Typography**: Inter font family for readability
4. **Components**:
   - Navigation sidebar for main sections
   - Dashboard cards for key metrics
   - Data tables with sorting and filtering
5. **Responsiveness**: Mobile-first with 3 breakpoints (sm, md, lg)

The design follows modern accessibility standards (WCAG AA) and provides a professional, intuitive user experience."""

        elif "architecture" in user_lower or "system" in user_lower:
            return """Recommended architecture:

```
┌─────────────────────────────────────────────────┐
│                   Frontend                       │
│   Next.js + React + TypeScript + Tailwind       │
└─────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────┐
│                   API Layer                      │
│         FastAPI + WebSocket + REST              │
└─────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────┐
│                  Database                        │
│          PostgreSQL + pgvector                   │
└─────────────────────────────────────────────────┘
```

This architecture provides scalability, type safety, and real-time capabilities."""

        else:
            return f"""I've analyzed your request: "{user_message[:100]}..."

Here's my response:

1. **Analysis**: Your requirements are clear and achievable
2. **Approach**: I recommend a modular, iterative implementation
3. **Timeline**: This can be completed efficiently
4. **Next Steps**: Let me know which aspect you'd like to explore first

I'm ready to help you implement this solution."""
