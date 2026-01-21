"""
Structured Output Module using Instructor

Provides guaranteed structured outputs from LLMs using Pydantic models.
No more JSON parsing errors - outputs are always valid and typed.

Features:
- Automatic retry on validation failures
- Support for complex nested structures
- Streaming with partial objects
- Multiple LLM provider support
"""

from typing import TypeVar, Type, Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field
from enum import Enum
import os
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)


# ===========================================
# Output Models for Code Generation
# ===========================================

class CodeLanguage(str, Enum):
    """Supported programming languages"""
    PYTHON = "python"
    TYPESCRIPT = "typescript"
    JAVASCRIPT = "javascript"
    RUST = "rust"
    GO = "go"
    JAVA = "java"
    CSHARP = "csharp"
    SWIFT = "swift"
    KOTLIN = "kotlin"
    HTML = "html"
    CSS = "css"
    SQL = "sql"
    SHELL = "shell"
    MARKDOWN = "markdown"
    JSON = "json"
    YAML = "yaml"


class CodeFile(BaseModel):
    """A single code file"""
    path: str = Field(description="File path relative to project root")
    content: str = Field(description="Complete file content")
    language: CodeLanguage = Field(description="Programming language")
    description: Optional[str] = Field(default=None, description="Brief description of what this file does")


class ProjectStructure(BaseModel):
    """Complete project structure with all files"""
    name: str = Field(description="Project name (lowercase, hyphenated)")
    description: str = Field(description="Brief project description")
    files: List[CodeFile] = Field(
        description="All project files - MUST include at least 5 files for a complete project: package.json, config files, layout, page, and components",
        min_length=3  # Ensure minimum viable project
    )
    entry_point: Optional[str] = Field(default="src/app/page.tsx", description="Main entry file")
    dependencies: Dict[str, str] = Field(
        default_factory=lambda: {
            "next": "13.5.6",
            "react": "^18.2.0",
            "react-dom": "^18.2.0",
            "tailwindcss": "^3.4.0"
        },
        description="Package dependencies with versions"
    )
    scripts: Dict[str, str] = Field(
        default_factory=lambda: {
            "dev": "next dev",
            "build": "next build",
            "start": "next start"
        },
        description="Available scripts/commands"
    )


class CodeChange(BaseModel):
    """A single code modification"""
    file_path: str = Field(description="Path to the file to modify")
    change_type: str = Field(description="Type: 'create', 'modify', 'delete'")
    original_code: Optional[str] = Field(default=None, description="Original code (for modify)")
    new_code: Optional[str] = Field(default=None, description="New code")
    explanation: str = Field(description="Why this change is being made")


class CodeReview(BaseModel):
    """Code review feedback"""
    file_path: str
    line_start: int
    line_end: int
    severity: str = Field(description="'error', 'warning', 'info', 'suggestion'")
    category: str = Field(description="'bug', 'security', 'performance', 'style', 'logic'")
    message: str
    suggested_fix: Optional[str] = None


class AnalysisResult(BaseModel):
    """Code analysis result"""
    summary: str = Field(description="Brief summary of the analysis")
    issues: List[CodeReview] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    score: int = Field(ge=0, le=100, description="Quality score 0-100")


class APIEndpoint(BaseModel):
    """API endpoint definition"""
    method: str = Field(description="HTTP method: GET, POST, PUT, DELETE, PATCH")
    path: str = Field(description="URL path")
    description: str
    request_body: Optional[Dict[str, Any]] = None
    response_body: Optional[Dict[str, Any]] = None
    query_params: Optional[Dict[str, str]] = None


class DatabaseSchema(BaseModel):
    """Database table schema"""
    table_name: str
    columns: List[Dict[str, Any]]
    primary_key: str
    foreign_keys: Optional[List[Dict[str, str]]] = None
    indexes: Optional[List[str]] = None


class ComponentSpec(BaseModel):
    """UI component specification"""
    name: str
    description: str
    props: Dict[str, Any]
    children: Optional[List[str]] = None
    events: Optional[List[str]] = None


class ArchitectureDecision(BaseModel):
    """Architecture decision record"""
    title: str
    context: str = Field(description="Why this decision is needed")
    decision: str = Field(description="What was decided")
    consequences: List[str] = Field(description="What are the implications")
    alternatives_considered: List[str] = Field(default_factory=list)


class TaskPlan(BaseModel):
    """Plan for implementing a task"""
    goal: str = Field(description="What we're trying to achieve")
    steps: List[str] = Field(description="Ordered list of steps to take")
    files_to_modify: List[str] = Field(default_factory=list)
    files_to_create: List[str] = Field(default_factory=list)
    estimated_complexity: str = Field(description="'low', 'medium', 'high'")
    risks: List[str] = Field(default_factory=list)


# ===========================================
# Structured Output Client
# ===========================================

class StructuredOutputClient:
    """
    Client for getting structured outputs from LLMs using Instructor.

    Example:
        client = StructuredOutputClient()

        project = await client.generate(
            response_model=ProjectStructure,
            messages=[{"role": "user", "content": "Create a Flask REST API"}],
        )

        # project is guaranteed to be a valid ProjectStructure
        for file in project.files:
            print(f"{file.path}: {file.language}")

    Providers (in priority order):
    - grok: xAI Grok (primary)
    - anthropic: Anthropic Claude (fallback)
    - openai: OpenAI GPT
    """

    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        max_retries: int = 3
    ):
        # Auto-detect provider based on available API keys
        self.provider = provider or self._detect_provider()
        self.model = model
        self.max_retries = max_retries
        self._client = None
        self._instructor_client = None

    def _detect_provider(self) -> str:
        """Detect the best available provider based on API keys"""
        if os.environ.get("XAI_API_KEY") or os.environ.get("GROK_API_KEY"):
            return "grok"
        elif os.environ.get("ANTHROPIC_API_KEY"):
            return "anthropic"
        elif os.environ.get("OPENAI_API_KEY"):
            return "openai"
        return "anthropic"  # Default fallback

    def _get_client(self):
        """Initialize the instructor-patched client"""
        if self._instructor_client is not None:
            return self._instructor_client

        try:
            import instructor

            if self.provider == "grok":
                # Grok uses OpenAI-compatible API
                import openai
                base_client = openai.OpenAI(
                    api_key=os.environ.get("XAI_API_KEY") or os.environ.get("GROK_API_KEY"),
                    base_url="https://api.x.ai/v1"
                )
                self._instructor_client = instructor.from_openai(base_client)
                self.model = self.model or "grok-3-latest"

            elif self.provider == "anthropic":
                import anthropic
                base_client = anthropic.Anthropic(
                    api_key=os.environ.get("ANTHROPIC_API_KEY")
                )
                self._instructor_client = instructor.from_anthropic(base_client)
                self.model = self.model or "claude-sonnet-4-20250514"

            elif self.provider == "openai":
                import openai
                base_client = openai.OpenAI(
                    api_key=os.environ.get("OPENAI_API_KEY")
                )
                self._instructor_client = instructor.from_openai(base_client)
                self.model = self.model or "gpt-4o"

            else:
                raise ValueError(f"Unsupported provider: {self.provider}")

            return self._instructor_client

        except ImportError as e:
            logger.warning(f"Instructor not available: {e}. Using mock client.")
            return None

    async def generate(
        self,
        response_model: Type[T],
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> T:
        """
        Generate a structured response from the LLM.

        Args:
            response_model: Pydantic model class for the response
            messages: List of message dicts with 'role' and 'content'
            system: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Instance of response_model with validated data
        """
        client = self._get_client()

        if client is None:
            # Return mock data for development
            return self._generate_mock(response_model)

        try:
            if self.provider == "anthropic":
                response = client.messages.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=system or "You are a helpful assistant that generates structured data.",
                    messages=messages,
                    response_model=response_model,
                    max_retries=self.max_retries,
                    **kwargs
                )
            else:  # openai
                full_messages = []
                if system:
                    full_messages.append({"role": "system", "content": system})
                full_messages.extend(messages)

                response = client.chat.completions.create(
                    model=self.model,
                    messages=full_messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    response_model=response_model,
                    max_retries=self.max_retries,
                    **kwargs
                )

            return response

        except Exception as e:
            logger.error(f"Structured output generation failed: {e}")
            raise

    async def generate_stream(
        self,
        response_model: Type[T],
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        **kwargs
    ):
        """
        Generate a structured response with streaming partial objects.

        Yields partial objects as they're being generated.
        """
        client = self._get_client()

        if client is None:
            yield self._generate_mock(response_model)
            return

        try:
            if self.provider == "anthropic":
                async for partial in client.messages.create_partial(
                    model=self.model,
                    system=system or "You are a helpful assistant.",
                    messages=messages,
                    response_model=response_model,
                    **kwargs
                ):
                    yield partial
            else:
                # OpenAI streaming
                async for partial in client.chat.completions.create_partial(
                    model=self.model,
                    messages=messages,
                    response_model=response_model,
                    **kwargs
                ):
                    yield partial

        except Exception as e:
            logger.error(f"Streaming generation failed: {e}")
            raise

    def _generate_mock(self, response_model: Type[T]) -> T:
        """Generate mock data for development without API keys"""
        logger.info(f"Generating mock {response_model.__name__}")

        if response_model == ProjectStructure:
            return ProjectStructure(
                name="mock-project",
                description="Mock project for development",
                files=[
                    CodeFile(
                        path="src/main.py",
                        content='print("Hello, World!")',
                        language=CodeLanguage.PYTHON,
                        description="Main entry point"
                    ),
                    CodeFile(
                        path="requirements.txt",
                        content="fastapi>=0.100.0\nuvicorn>=0.23.0",
                        language=CodeLanguage.PYTHON,
                        description="Dependencies"
                    )
                ],
                entry_point="src/main.py",
                dependencies={"fastapi": "0.100.0"},
                scripts={"start": "python src/main.py"}
            )

        elif response_model == TaskPlan:
            return TaskPlan(
                goal="Mock task plan",
                steps=["Step 1: Analyze requirements", "Step 2: Implement solution", "Step 3: Test"],
                files_to_modify=[],
                files_to_create=["src/main.py"],
                estimated_complexity="medium",
                risks=["Mock environment - no real implementation"]
            )

        elif response_model == AnalysisResult:
            return AnalysisResult(
                summary="Mock analysis complete",
                issues=[],
                suggestions=["Consider adding tests", "Add documentation"],
                score=85
            )

        # Generic mock for other models
        try:
            return response_model.model_construct()
        except Exception:
            raise ValueError(f"Cannot generate mock for {response_model.__name__}")


# ===========================================
# Convenience Functions
# ===========================================

_default_client: Optional[StructuredOutputClient] = None


def get_structured_client() -> StructuredOutputClient:
    """Get the default structured output client"""
    global _default_client
    if _default_client is None:
        _default_client = StructuredOutputClient()
    return _default_client


async def generate_project(
    description: str,
    platform: str = "web",
    language: str = "typescript"
) -> ProjectStructure:
    """
    Generate a complete project structure from a description.

    Args:
        description: Natural language description of what to build
        platform: Target platform (web, mobile, api)
        language: Primary programming language

    Returns:
        ProjectStructure with all files
    """
    client = get_structured_client()

    system = f"""You are an expert software architect. Generate a complete, production-ready
    {platform} project using {language}. Include all necessary files with full implementations.
    Follow best practices for the language and platform.

    CRITICAL REQUIREMENTS FOR WEB PROJECTS (WebContainer compatibility):
    - MUST use Next.js version '13.5.6' exactly (NOT 14.x) - version 14 has SWC binary issues
    - package.json MUST have: "next": "13.5.6" (exact version, no caret ^)
    - Use 'next.config.mjs' (NOT next.config.ts) - TypeScript config is NOT supported
    - Use 'tailwind.config.js' (NOT tailwind.config.ts)
    - Use 'postcss.config.js' with tailwindcss and autoprefixer plugins
    - MUST include '.babelrc' file with {{"presets": ["next/babel"]}} for WebContainer
    - In next.config.mjs, set swcMinify: false and reactStrictMode: true (do NOT use experimental.appDir)
    - NEVER use 'next/font' - it requires SWC which conflicts with Babel
    - For fonts, use Google Fonts via <link> tag in layout.tsx or @import in globals.css
    - Include ALL necessary dependencies in package.json
    - Use modern React patterns (hooks, functional components)
    - Include proper TypeScript types
    - Add loading states and error handling
    - Use Tailwind CSS for styling

    FILE REQUIREMENTS:
    - Generate at least 5-10 files for a complete project
    - MUST include: package.json, tsconfig.json, next.config.mjs, tailwind.config.js, postcss.config.js, .babelrc
    - Include: layout, pages, components
    - All code must be complete and runnable (no placeholders or TODOs)
    - Follow component-based architecture
    - Use semantic HTML and accessibility best practices

    REACT SERVER COMPONENTS RULES (CRITICAL - prevents compilation errors):
    - Any file using React hooks (useState, useEffect, useContext, useRef, etc.) MUST have 'use client' as the FIRST line
    - Any file using browser APIs (window, document, localStorage) MUST have 'use client' at the top
    - If page.tsx uses useState or any hook, add 'use client' BEFORE any imports
    - layout.tsx should stay as Server Component (no 'use client') - wrap children with client ErrorBoundary
    - Components with onClick, onChange, onSubmit, or any event handlers MUST have 'use client'
    - NEVER export 'metadata' from a 'use client' file - metadata only works in Server Components
    - Use 'next/navigation' for useRouter, usePathname, useSearchParams (NOT 'next/router')

    COMMON BUILD ERRORS TO AVOID:
    - NEVER use next/image - use regular <img> tags (next/image has WebContainer issues)
    - NEVER access window/document/localStorage at module level - only inside useEffect
    - ALWAYS list ALL imported packages in package.json dependencies
    - tsconfig.json MUST have paths: {{ "@/*": ["./src/*"] }} for @/ imports to work
    - tsconfig.json MUST have resolveJsonModule: true for JSON imports
    - NEVER mix Pages Router (pages/) with App Router (app/) - use App Router only
    - Ensure lucide-react icons are imported correctly: import {{ IconName }} from 'lucide-react'

    TAILWIND CSS RULES (CRITICAL - prevents PostCSS errors):
    - ONLY use standard Tailwind classes (bg-blue-500, text-white, p-4, rounded-lg, etc.)
    - NEVER use shadcn/ui classes like 'border-border', 'bg-background', 'text-foreground', 'bg-muted'
    - globals.css MUST be simple: @tailwind base; @tailwind components; @tailwind utilities; and optional font @import
    - DO NOT add custom @layer base rules with undefined CSS variables
    - tailwind.config.js should only extend theme, not reference undefined variables

    ERROR HANDLING REQUIREMENTS (CRITICAL for preview visibility):
    - Create src/components/ErrorBoundary.tsx with 'use client' at the top, containing an ErrorBoundary class component
    - ErrorBoundary MUST render errors with high-contrast colors: red background (#dc2626), white text, 20px padding, minHeight 100vh
    - In layout.tsx (Server Component), import ErrorBoundary and wrap {{children}} with it
    - In layout.tsx <head>, add error reporting script: <script dangerouslySetInnerHTML={{{{__html: `window.onerror=function(m){{window.parent?.postMessage({{type:'preview-error',message:m}},'*')}}`}}}} />
    - page.tsx MUST have visible content even if Tailwind CSS fails (use inline styles as fallback)
    - NEVER return null, undefined, or empty JSX from page components
    - ALWAYS wrap main page content with inline style fallback: style={{{{ minHeight: '100vh', background: '#0f172a', color: 'white' }}}}
    - Include BOTH Tailwind classes AND inline style fallbacks for critical visibility"""

    return await client.generate(
        response_model=ProjectStructure,
        system=system,
        messages=[{
            "role": "user",
            "content": f"Create a complete, production-ready project: {description}"
        }]
    )


async def analyze_code(code: str, language: str) -> AnalysisResult:
    """
    Analyze code for issues and improvements.

    Args:
        code: The code to analyze
        language: Programming language

    Returns:
        AnalysisResult with issues and suggestions
    """
    client = get_structured_client()

    system = """You are an expert code reviewer. Analyze the provided code for:
    - Bugs and errors
    - Security vulnerabilities
    - Performance issues
    - Code style problems
    - Logic errors
    Provide specific, actionable feedback."""

    return await client.generate(
        response_model=AnalysisResult,
        system=system,
        messages=[{
            "role": "user",
            "content": f"Analyze this {language} code:\n\n```{language}\n{code}\n```"
        }]
    )


async def plan_task(task_description: str, codebase_context: str = "") -> TaskPlan:
    """
    Create an implementation plan for a task.

    Args:
        task_description: What needs to be done
        codebase_context: Optional context about existing codebase

    Returns:
        TaskPlan with steps and file changes
    """
    client = get_structured_client()

    system = """You are a senior software engineer planning implementation tasks.
    Create detailed, actionable plans that account for edge cases and potential issues."""

    prompt = f"Plan the implementation of: {task_description}"
    if codebase_context:
        prompt += f"\n\nExisting codebase context:\n{codebase_context}"

    return await client.generate(
        response_model=TaskPlan,
        system=system,
        messages=[{"role": "user", "content": prompt}]
    )
