"""
Code Generator Service

Handles the orchestration of AI agents for code generation.
Uses the real agent orchestrator with LangGraph.
Falls back to mock mode when orchestrator is unavailable.

NEW: Uses template-first generation for reliability:
1. Select template based on description
2. AI customizes template (not generate from scratch)
3. Validate output before returning
4. Fall back to clean template if validation fails
"""
import asyncio
import os
from typing import Dict, Optional, Callable, Any
from datetime import datetime
import logging

from ..models import Platform, GenerationEvent
from .orchestrator import (
    AgentOrchestrator,
    OrchestratorEvent,
    WorkflowResult,
    WorkflowStatus,
)
from .file_storage import save_project_files
from .agent_registry import get_registry, list_agents
from .template_loader import get_template_loader
from .template_customizer import (
    TemplateCustomizer,
    CustomizationRequest,
    CustomizationMode,
    BrandProfile,
    get_template_customizer,
)
from .code_validator import validate_files, validate_and_fix, ValidationResult
from .prototype_orchestrator import (
    PrototypeOrchestrator,
    PrototypeEvent,
    PrototypeResult,
    generate_prototype,
)

logger = logging.getLogger(__name__)

# Environment flag for creative mode (5-agent pipeline)
USE_CREATIVE_MODE = os.environ.get("USE_CREATIVE_MODE", "true").lower() == "true"


# Environment flag to force mock mode
USE_MOCK_MODE = os.environ.get("USE_MOCK_AGENTS", "false").lower() == "true"


class CodeGenerator:
    """
    Orchestrates the code generation process using AI agents.

    Uses template-first approach for reliability:
    1. Select best template based on user description
    2. AI customizes only the content files (pages, components)
    3. Protected files (configs) remain unchanged
    4. Validate all output before returning
    5. Fall back to clean template if validation fails

    Uses the real agent orchestrator with LangGraph for production.
    Falls back to mock mode for development or when APIs are unavailable.
    """

    def __init__(self, event_callback: Optional[Callable[[GenerationEvent], Any]] = None):
        """
        Initialize the code generator.

        Args:
            event_callback: Optional async function to call for each event
        """
        self.event_callback = event_callback
        self._orchestrator: Optional[AgentOrchestrator] = None
        self._template_customizer = get_template_customizer()
        self._template_loader = get_template_loader()
        self._prototype_orchestrator: Optional[PrototypeOrchestrator] = None

    def _get_orchestrator(self) -> AgentOrchestrator:
        """Get or create the orchestrator with event bridging"""
        if self._orchestrator is None:
            async def bridge_events(event: OrchestratorEvent):
                """Bridge orchestrator events to generation events"""
                await self._handle_orchestrator_event(event)

            self._orchestrator = AgentOrchestrator(event_callback=bridge_events)
        return self._orchestrator

    def _get_prototype_orchestrator(self) -> PrototypeOrchestrator:
        """Get or create the prototype orchestrator with event bridging"""
        if self._prototype_orchestrator is None:
            async def bridge_prototype_events(event: PrototypeEvent):
                """Bridge prototype events to generation events"""
                await self._handle_prototype_event(event)

            self._prototype_orchestrator = PrototypeOrchestrator(event_callback=bridge_prototype_events)
        return self._prototype_orchestrator

    async def _handle_prototype_event(self, event: PrototypeEvent) -> None:
        """Convert prototype orchestrator events to generation events"""
        event_map = {
            "agent_start": "agent_start",
            "agent_complete": "agent_complete",
            "status": "status",
            "error": "error",
            "clarification_required": "clarification_required",
            "research_progress": "research_progress",
        }

        gen_type = event_map.get(event.type, "status")

        # Handle special event types that pass through data
        if event.type == "clarification_required":
            gen_event = GenerationEvent(
                type="clarification_required",
                message=event.message,
                progress=event.progress,
                agent=event.agent,
                agent_type="creative",
                session_id=event.data.get("session_id") if event.data else None,
                data=event.data,  # Pass through questions, industry, confidence
            )
            await self._emit_event(gen_event)
            return

        if event.type == "research_progress":
            gen_event = GenerationEvent(
                type="research_progress",
                message=event.message,
                progress=event.progress,
                agent=event.agent,
                data=event.data,
            )
            await self._emit_event(gen_event)
            return

        # Convert dict data to string for output field (GenerationEvent.output expects str)
        output_str = None
        if event.data:
            domain = event.data.get("domain")
            if domain:
                # Extract a summary string from domain analysis
                industry = domain.get("industry_display_name") or domain.get("industry", "")
                output_str = f"Industry: {industry}" if industry else None

        gen_event = GenerationEvent(
            type=gen_type,
            message=event.message,
            progress=event.progress,
            agent=event.agent,
            agent_type="creative" if event.agent else None,
            output=output_str,
        )

        await self._emit_event(gen_event)

    async def _handle_orchestrator_event(self, event: OrchestratorEvent) -> None:
        """Convert orchestrator events to generation events"""
        event_map = {
            "workflow_start": "status",
            "agent_start": "agent_start",
            "agent_progress": "status",
            "agent_complete": "agent_complete",
            "parallel_start": "parallel_start",
            "parallel_complete": "status",
            "workflow_complete": "status",  # Don't use "complete" - that closes SSE before files are sent
            "workflow_error": "error",
        }

        gen_type = event_map.get(event.type, "status")

        gen_event = GenerationEvent(
            type=gen_type,
            message=event.data.get("message", f"Event: {event.type}"),
            progress=int(event.data.get("progress", 0) * 100) if "progress" in event.data else None,
            agent=event.data.get("agent_id"),
            agent_type=event.data.get("agent_type"),
            agents=event.data.get("agents"),  # For parallel_start events
            output=event.data.get("output"),
        )

        await self._emit_event(gen_event)

    async def _emit_event(self, event: GenerationEvent) -> None:
        """Emit an event through the callback if set"""
        if self.event_callback:
            await self.event_callback(event)

    async def generate(
        self,
        description: str,
        platform: Platform,
        project_id: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Generate code based on the description and platform.

        Args:
            description: Natural language description of the app
            platform: Target platform (web, ios, android, all)
            project_id: Optional project ID for tracking

        Returns:
            Dictionary of generated files (path -> content)
        """
        logger.info(f"Starting generation for: {description[:50]}...")

        # Generate project ID if not provided
        if not project_id:
            import uuid
            project_id = str(uuid.uuid4())

        # Check if we should use creative mode (5-agent pipeline)
        if USE_CREATIVE_MODE and (platform == Platform.WEB or platform == Platform.ALL):
            logger.info("Using creative mode (5-agent pipeline) for generation")
            try:
                return await self._generate_with_prototype_orchestrator(description, platform, project_id)
            except Exception as e:
                logger.warning(f"Creative mode failed, falling back to standard: {e}")

        # Check if we should use mock mode
        if USE_MOCK_MODE or not self._should_use_orchestrator():
            logger.info("Using mock mode for generation")
            return await self._generate_mock(description, platform, project_id)

        # Use real orchestrator
        try:
            files = await self._generate_with_orchestrator(description, platform, project_id)

            # Validate and fix generated files
            files = await self._validate_and_fix_files(files, description, project_id)

            return files
        except Exception as e:
            logger.warning(f"Orchestrator failed, falling back to template: {e}")
            return await self._generate_from_template(description, platform, project_id)

    def _should_use_orchestrator(self) -> bool:
        """Check if the real orchestrator should be used"""
        # Check for API keys (Grok is primary, Anthropic is fallback)
        has_grok = bool(os.environ.get("XAI_API_KEY") or os.environ.get("GROK_API_KEY"))
        has_anthropic = bool(os.environ.get("ANTHROPIC_API_KEY"))
        has_openai = bool(os.environ.get("OPENAI_API_KEY"))

        # Check for agent registry
        try:
            registry = get_registry()
            has_agents = len(registry) > 0
        except Exception:
            has_agents = False

        return (has_grok or has_anthropic or has_openai) and has_agents

    async def _generate_with_orchestrator(
        self,
        description: str,
        platform: Platform,
        project_id: str,
    ) -> Dict[str, str]:
        """Generate using the real agent orchestrator"""
        await self._emit_event(GenerationEvent(
            type="status",
            message="Starting AI-powered code generation...",
            progress=0
        ))

        orchestrator = self._get_orchestrator()

        # Run the workflow
        result: WorkflowResult = await orchestrator.run_workflow(
            description=description,
            platform=platform.value,
            project_id=project_id,
        )

        # Log workflow result
        logger.info(f"Workflow completed: status={result.status}, files={len(result.files)}, agents={result.successful_agents}/{result.total_agents}")
        if result.errors:
            logger.warning(f"Workflow errors: {result.errors}")

        # Convert files to dict
        files = {}
        for code_file in result.files:
            files[code_file.path] = code_file.content
            logger.info(f"File: {code_file.path} ({len(code_file.content)} chars)")

        # Save files to storage
        if files:
            try:
                await save_project_files(project_id, files)
                logger.info(f"Saved {len(files)} files for project {project_id}")
            except Exception as e:
                logger.warning(f"Failed to save files to storage: {e}")

        # Emit files event
        logger.info(f"Emitting files event with {len(files)} files")
        await self._emit_event(GenerationEvent(
            type="files",
            files=files,
            progress=100
        ))

        # Emit complete event
        logger.info("Emitting final complete event")
        await self._emit_event(GenerationEvent(
            type="complete",
            message="Code generation complete!",
            summary={
                "filesGenerated": len(files),
                "platform": platform.value,
                "agents": result.total_agents,
                "successfulAgents": result.successful_agents,
                "failedAgents": result.failed_agents,
                "durationMs": result.duration_ms,
                "timestamp": datetime.now().isoformat()
            }
        ))

        return files

    async def _generate_with_prototype_orchestrator(
        self,
        description: str,
        platform: Platform,
        project_id: str,
    ) -> Dict[str, str]:
        """
        Generate using the 5-agent creative prototype orchestrator.

        This produces domain-specific prototypes that feel tailored to the
        client's business, not generic templates.
        """
        await self._emit_event(GenerationEvent(
            type="status",
            message="Starting creative prototype generation...",
            progress=0
        ))

        orchestrator = self._get_prototype_orchestrator()

        # Run the creative pipeline
        result: PrototypeResult = await orchestrator.generate(
            description=description,
            project_id=project_id,
        )

        # Log result
        logger.info(f"Creative pipeline completed: success={result.success}, files={len(result.files)}")
        if result.domain_analysis:
            logger.info(f"Domain: {result.domain_analysis.get('industry_display_name', 'unknown')}")
        if result.error:
            logger.warning(f"Creative pipeline warning: {result.error}")

        files = result.files

        # Save files to storage
        if files:
            try:
                await save_project_files(project_id, files)
                logger.info(f"Saved {len(files)} files for project {project_id}")
            except Exception as e:
                logger.warning(f"Failed to save files to storage: {e}")

        # Emit files event
        logger.info(f"Emitting files event with {len(files)} files")
        await self._emit_event(GenerationEvent(
            type="files",
            files=files,
            progress=100
        ))

        # Emit complete event with rich metadata
        summary = {
            "filesGenerated": len(files),
            "platform": platform.value,
            "mode": "creative",
            "durationMs": result.duration_ms,
            "timestamp": datetime.now().isoformat()
        }

        if result.domain_analysis:
            summary["industry"] = result.domain_analysis.get("industry_display_name")
            summary["competitors"] = [
                c.get("name") for c in result.domain_analysis.get("competitors", [])
            ]

        if result.architecture:
            summary["pages"] = len(result.architecture.get("pages", []))
            summary["appName"] = result.architecture.get("app_name")

        logger.info("Emitting final complete event")
        await self._emit_event(GenerationEvent(
            type="complete",
            message=f"Creative prototype ready for {result.domain_analysis.get('industry_display_name', 'your business')}!",
            summary=summary
        ))

        return files

    async def _validate_and_fix_files(
        self,
        files: Dict[str, str],
        description: str,
        project_id: str,
    ) -> Dict[str, str]:
        """
        Validate generated files and fix issues.
        Falls back to clean template if validation fails.
        """
        await self._emit_event(GenerationEvent(
            type="status",
            message="Validating generated code...",
            progress=95
        ))

        # Try to fix issues
        fixed_files, validation = validate_and_fix(files)

        if validation.is_valid:
            logger.info(f"Validation passed for project {project_id}")
            return fixed_files

        # Log validation errors
        for error in validation.errors:
            logger.warning(f"Validation error: {error.code} in {error.file_path}: {error.message}")

        # Validation still failing after fixes - fall back to template
        logger.warning(f"Validation failed with {len(validation.errors)} errors, falling back to template")

        await self._emit_event(GenerationEvent(
            type="status",
            message="Applying template fallback for stability...",
            progress=97
        ))

        # Get clean template based on description
        template = self._template_loader.select_template(description)
        if template:
            template_files = self._template_loader.get_template_files_dict(template.id)
            logger.info(f"Using fallback template: {template.id}")
            return template_files

        # If no template available, return what we have
        logger.warning("No template available for fallback, returning fixed files")
        return fixed_files

    async def _generate_from_template(
        self,
        description: str,
        platform: Platform,
        project_id: str,
    ) -> Dict[str, str]:
        """
        Generate using template-first approach.
        Selects best template and returns it with brand applied.
        """
        await self._emit_event(GenerationEvent(
            type="status",
            message="Selecting best template...",
            progress=10
        ))

        # Select template
        template = self._template_loader.select_template(description)
        if not template:
            logger.warning("No templates available, falling back to mock")
            return await self._generate_mock(description, platform, project_id)

        logger.info(f"Selected template: {template.id} ({template.name})")

        await self._emit_event(GenerationEvent(
            type="status",
            message=f"Using {template.name} template...",
            progress=30
        ))

        # Get template files
        files = self._template_loader.get_template_files_dict(template.id)

        # Emit files event
        await self._emit_event(GenerationEvent(
            type="files",
            files=files,
            progress=100
        ))

        # Emit complete event
        await self._emit_event(GenerationEvent(
            type="complete",
            message=f"Generated {template.name} from template!",
            summary={
                "filesGenerated": len(files),
                "platform": platform.value,
                "templateUsed": template.id,
                "templateName": template.name,
                "mode": "template",
                "timestamp": datetime.now().isoformat()
            }
        ))

        return files

    async def _generate_mock(
        self,
        description: str,
        platform: Platform,
        project_id: str,
    ) -> Dict[str, str]:
        """
        Generate using mock agents (for development).
        Now uses templates when available for better reliability.
        """
        # Try template-first for web platform
        if platform == Platform.WEB or platform == Platform.ALL:
            template = self._template_loader.select_template(description)
            if template:
                logger.info(f"Mock mode using template: {template.id}")
                return await self._generate_from_template(description, platform, project_id)

        # Get agents from registry or use fallback
        try:
            agents = list_agents()[:10]  # Use first 10 agents
        except Exception:
            agents = [
                {"id": "PM", "role": "Project Manager"},
                {"id": "Research", "role": "Market Researcher"},
                {"id": "Designs", "role": "UI/UX Designer"},
                {"id": "Senior", "role": "System Architect"},
                {"id": "FrontendEngineer", "role": "Frontend Engineer"},
                {"id": "BackendEngineer", "role": "Backend Engineer"},
                {"id": "DatabaseAdmin", "role": "Database Specialist"},
                {"id": "QA", "role": "Test Engineer"},
                {"id": "SecurityEngineer", "role": "Security Auditor"},
                {"id": "Verifier", "role": "Code Verifier"},
            ]

        await self._emit_event(GenerationEvent(
            type="status",
            message="Starting code generation (mock mode)...",
            progress=0
        ))

        total_agents = len(agents)

        for i, agent in enumerate(agents):
            agent_name = agent.get("role", agent.get("id", f"Agent {i+1}"))
            agent_id = agent.get("id", f"agent_{i}")

            # Emit agent start
            await self._emit_event(GenerationEvent(
                type="agent_start",
                agent=agent_name,
                agent_type=agent.get("category", "general"),
                progress=int((i / total_agents) * 100)
            ))

            # Simulate agent work
            await asyncio.sleep(0.3)

            # Emit agent complete
            await self._emit_event(GenerationEvent(
                type="agent_complete",
                agent=agent_name,
                output=f"{agent_name} completed analysis for: {description[:50]}...",
                progress=int(((i + 1) / total_agents) * 100)
            ))

        # Generate mock files
        files = self._generate_mock_files(description, platform)

        # Validate mock files too
        fixed_files, validation = validate_and_fix(files)
        if not validation.is_valid:
            logger.warning(f"Mock files had {len(validation.errors)} validation errors, auto-fixed")

        # Emit files event
        await self._emit_event(GenerationEvent(
            type="files",
            files=fixed_files,
            progress=100
        ))

        # Emit complete event
        await self._emit_event(GenerationEvent(
            type="complete",
            message="Code generation complete!",
            summary={
                "filesGenerated": len(fixed_files),
                "platform": platform.value,
                "agents": len(agents),
                "mode": "mock",
                "timestamp": datetime.now().isoformat()
            }
        ))

        return fixed_files

    def _generate_mock_files(
        self,
        description: str,
        platform: Platform
    ) -> Dict[str, str]:
        """Generate mock files based on platform"""
        project_name = self._slugify(description[:30])

        if platform == Platform.WEB or platform == Platform.ALL:
            return self._generate_web_files(project_name, description)
        elif platform == Platform.IOS:
            return self._generate_ios_files(project_name, description)
        elif platform == Platform.ANDROID:
            return self._generate_android_files(project_name, description)

        return {}

    def _slugify(self, text: str) -> str:
        """Convert text to slug format"""
        import re
        slug = text.lower()
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'[\s_]+', '-', slug)
        slug = re.sub(r'-+', '-', slug)
        return slug.strip('-')[:50]

    def _generate_web_files(self, project_name: str, description: str) -> Dict[str, str]:
        """Generate web app files"""
        return {
            "package.json": f'''{{"name": "{project_name}",
  "version": "0.1.0",
  "private": true,
  "scripts": {{
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint"
  }},
  "dependencies": {{
    "next": "13.5.6",
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  }},
  "devDependencies": {{
    "@types/node": "^20.0.0",
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "typescript": "^5.3.0",
    "tailwindcss": "^3.4.0",
    "postcss": "^8.4.0",
    "autoprefixer": "^10.4.0"
  }}
}}''',
            "tsconfig.json": '''{
  "compilerOptions": {
    "target": "es5",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{ "name": "next" }],
    "paths": { "@/*": ["./src/*"] }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}''',
            "src/app/page.tsx": f''''use client'

export default function Home() {{
  return (
    <main style={{{{ minHeight: '100vh', padding: '2rem', background: 'linear-gradient(to bottom right, #0f172a, #1e293b)', color: 'white' }}}} className="min-h-screen p-8 bg-gradient-to-br from-slate-900 to-slate-800">
      <div style={{{{ maxWidth: '56rem', margin: '0 auto' }}}} className="max-w-4xl mx-auto">
        <h1 style={{{{ fontSize: '2.5rem', fontWeight: 'bold', marginBottom: '1rem' }}}} className="text-4xl font-bold text-white mb-4">
          {project_name}
        </h1>
        <p style={{{{ color: '#cbd5e1', fontSize: '1.125rem' }}}} className="text-slate-300 text-lg">
          {description[:200]}...
        </p>

        <div style={{{{ marginTop: '2rem' }}}} className="mt-8 grid gap-4">
          <div style={{{{ backgroundColor: 'rgba(51, 65, 85, 0.5)', borderRadius: '0.5rem', padding: '1.5rem', border: '1px solid #475569' }}}} className="bg-slate-700/50 rounded-lg p-6 border border-slate-600">
            <h2 style={{{{ fontSize: '1.25rem', fontWeight: '600', marginBottom: '0.5rem' }}}} className="text-xl font-semibold text-white mb-2">
              Getting Started
            </h2>
            <p style={{{{ color: '#94a3b8' }}}} className="text-slate-400">
              This app was generated by Code Weaver Pro using 52 AI agents.
            </p>
          </div>
        </div>
      </div>
    </main>
  )
}}
''',
            "src/app/layout.tsx": f'''import type {{ Metadata }} from 'next'
import './globals.css'

export const metadata: Metadata = {{
  title: '{project_name}',
  description: 'Generated by Code Weaver Pro',
}}

export default function RootLayout({{
  children,
}}: {{
  children: React.ReactNode
}}) {{
  return (
    <html lang="en">
      <body>{{children}}</body>
    </html>
  )
}}
''',
            "src/app/globals.css": '''@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --foreground-rgb: 255, 255, 255;
  --background-start-rgb: 15, 23, 42;
  --background-end-rgb: 30, 41, 59;
}

body {
  color: rgb(var(--foreground-rgb));
  background: linear-gradient(
    to bottom,
    rgb(var(--background-start-rgb)),
    rgb(var(--background-end-rgb))
  );
}
''',
            "tailwind.config.js": '''/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
''',
            "next.config.mjs": '''/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // WebContainer compatibility - disable native SWC
  experimental: {
    forceSwcTransforms: true,
  },
  swcMinify: false,
}

export default nextConfig
''',
            "postcss.config.js": '''module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
''',
            ".babelrc": '''{
  "presets": ["next/babel"]
}
''',
            "README.md": f'''# {project_name}

> {description[:100]}...

## Generated by Code Weaver Pro

This project was automatically generated using 52 specialized AI agents.

## Getting Started

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to view your app.

## Tech Stack

- **Framework**: Next.js 13.5.6
- **Styling**: Tailwind CSS
- **Language**: TypeScript

## Project Structure

```
src/
  app/
    page.tsx      # Home page
    layout.tsx    # Root layout
    globals.css   # Global styles
```
''',
        }

    def _generate_ios_files(self, project_name: str, description: str) -> Dict[str, str]:
        """Generate iOS app files"""
        safe_name = project_name.replace('-', '')

        return {
            "Package.swift": f'''// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "{safe_name}",
    platforms: [.iOS(.v17), .macOS(.v14)],
    products: [
        .library(name: "{safe_name}", targets: ["{safe_name}"]),
    ],
    targets: [
        .target(name: "{safe_name}"),
        .testTarget(name: "{safe_name}Tests", dependencies: ["{safe_name}"]),
    ]
)
''',
            f"Sources/{safe_name}App.swift": f'''import SwiftUI

@main
struct {safe_name}App: App {{
    var body: some Scene {{
        WindowGroup {{
            ContentView()
        }}
    }}
}}
''',
            "Sources/ContentView.swift": f'''import SwiftUI

struct ContentView: View {{
    var body: some View {{
        NavigationStack {{
            VStack(spacing: 20) {{
                Image(systemName: "sparkles")
                    .imageScale(.large)
                    .foregroundStyle(.tint)
                    .font(.system(size: 60))

                Text("{project_name}")
                    .font(.largeTitle)
                    .fontWeight(.bold)

                Text("{description[:100]}...")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                    .multilineTextAlignment(.center)
                    .padding(.horizontal)
            }}
            .padding()
            .navigationTitle("Home")
        }}
    }}
}}

#Preview {{
    ContentView()
}}
''',
            "README.md": f'''# {project_name} (iOS)

> {description[:100]}...

## Generated by Code Weaver Pro

This iOS app was automatically generated using 52 specialized AI agents.

## Requirements

- Xcode 15.0+
- iOS 17.0+
- macOS 14.0+

## Getting Started

1. Open in Xcode
2. Build and run on simulator or device
''',
        }

    def _generate_android_files(self, project_name: str, description: str) -> Dict[str, str]:
        """Generate Android app files"""
        package_name = f"com.codeweaver.{project_name.replace('-', '')}"

        return {
            "build.gradle.kts": f'''plugins {{
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}}

android {{
    namespace = "{package_name}"
    compileSdk = 34

    defaultConfig {{
        applicationId = "{package_name}"
        minSdk = 26
        targetSdk = 34
        versionCode = 1
        versionName = "1.0"
    }}

    buildFeatures {{
        compose = true
    }}

    composeOptions {{
        kotlinCompilerExtensionVersion = "1.5.8"
    }}
}}

dependencies {{
    implementation("androidx.core:core-ktx:1.12.0")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.7.0")
    implementation("androidx.activity:activity-compose:1.8.2")
    implementation(platform("androidx.compose:compose-bom:2024.02.00"))
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-graphics")
    implementation("androidx.compose.material3:material3")
}}
''',
            f"src/main/kotlin/{package_name.replace('.', '/')}/MainActivity.kt": f'''package {package_name}

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

class MainActivity : ComponentActivity() {{
    override fun onCreate(savedInstanceState: Bundle?) {{
        super.onCreate(savedInstanceState)
        setContent {{
            MaterialTheme {{
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {{
                    MainScreen()
                }}
            }}
        }}
    }}
}}

@Composable
fun MainScreen() {{
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {{
        Text(
            text = "{project_name}",
            style = MaterialTheme.typography.headlineLarge
        )
        Spacer(modifier = Modifier.height(16.dp))
        Text(
            text = "{description[:100]}...",
            style = MaterialTheme.typography.bodyMedium
        )
    }}
}}
''',
            "README.md": f'''# {project_name} (Android)

> {description[:100]}...

## Generated by Code Weaver Pro

This Android app was automatically generated using 52 specialized AI agents.

## Requirements

- Android Studio Hedgehog+
- Android SDK 34
- Kotlin 1.9+

## Getting Started

1. Open project in Android Studio
2. Sync Gradle
3. Run on emulator or device
''',
        }
