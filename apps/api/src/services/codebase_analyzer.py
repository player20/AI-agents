"""
Codebase Analyzer Service

Understands what a codebase does, its structure, tech stack, and architecture.
Provides context for deeper analysis by domain-specific analyzers.
"""

from typing import Optional, List, Dict, Any, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json
import re
import logging

logger = logging.getLogger(__name__)


class PlatformType(str, Enum):
    """Types of platforms/applications"""
    WEB_APP = "web_app"
    API = "api"
    LIBRARY = "library"
    CLI = "cli"
    MOBILE = "mobile"
    DESKTOP = "desktop"
    FULLSTACK = "fullstack"
    MONOREPO = "monorepo"
    UNKNOWN = "unknown"


class ArchitectureType(str, Enum):
    """Architecture patterns"""
    MONOLITH = "monolith"
    MICROSERVICES = "microservices"
    MONOREPO = "monorepo"
    SPA = "spa"
    SSR = "ssr"
    STATIC = "static"
    SERVERLESS = "serverless"
    MVC = "mvc"
    UNKNOWN = "unknown"


@dataclass
class TechStack:
    """Detected technology stack"""
    languages: List[str] = field(default_factory=list)
    frameworks: List[str] = field(default_factory=list)
    databases: List[str] = field(default_factory=list)
    build_tools: List[str] = field(default_factory=list)
    testing: List[str] = field(default_factory=list)
    deployment: List[str] = field(default_factory=list)
    libraries: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, List[str]]:
        return {
            "languages": self.languages,
            "frameworks": self.frameworks,
            "databases": self.databases,
            "build_tools": self.build_tools,
            "testing": self.testing,
            "deployment": self.deployment,
            "libraries": self.libraries,
        }


@dataclass
class FolderInfo:
    """Information about a folder's purpose"""
    path: str
    purpose: str
    file_count: int
    patterns: List[str] = field(default_factory=list)


@dataclass
class CodebaseContext:
    """Complete context about a codebase"""
    # What the platform does
    platform_purpose: str
    platform_type: PlatformType

    # Tech stack
    tech_stack: TechStack

    # Architecture
    architecture_type: ArchitectureType
    folder_structure: List[FolderInfo]

    # Entry points
    frontend_entry: Optional[str] = None
    backend_entry: Optional[str] = None
    api_routes: List[str] = field(default_factory=list)

    # Code metrics
    total_files: int = 0
    total_lines: int = 0
    languages_breakdown: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "platform_purpose": self.platform_purpose,
            "platform_type": self.platform_type.value,
            "tech_stack": self.tech_stack.to_dict(),
            "architecture_type": self.architecture_type.value,
            "folder_structure": [
                {"path": f.path, "purpose": f.purpose, "file_count": f.file_count}
                for f in self.folder_structure
            ],
            "frontend_entry": self.frontend_entry,
            "backend_entry": self.backend_entry,
            "api_routes": self.api_routes,
            "total_files": self.total_files,
            "total_lines": self.total_lines,
            "languages_breakdown": self.languages_breakdown,
        }


# Framework detection patterns
FRAMEWORK_PATTERNS = {
    # Frontend frameworks
    "Next.js": ["next.config.js", "next.config.mjs", "next.config.ts", "_app.tsx", "_app.jsx", "app/layout.tsx"],
    "React": ["react", "react-dom", "jsx", "tsx"],
    "Vue.js": ["vue.config.js", ".vue", "nuxt.config"],
    "Angular": ["angular.json", "@angular/core"],
    "Svelte": ["svelte.config.js", ".svelte"],
    "Astro": ["astro.config.mjs", ".astro"],

    # Backend frameworks
    "FastAPI": ["fastapi", "from fastapi import"],
    "Django": ["django", "DJANGO_SETTINGS_MODULE", "manage.py"],
    "Flask": ["from flask import", "Flask(__name__)"],
    "Express.js": ["express()", "const express = require"],
    "NestJS": ["@nestjs/core", "NestFactory"],
    "Spring Boot": ["spring-boot", "@SpringBootApplication"],
    "Rails": ["rails", "Gemfile", "config.ru"],
    "Laravel": ["laravel", "artisan"],
    "Go Fiber": ["gofiber/fiber"],
    "Go Gin": ["gin-gonic/gin"],
    "Go Echo": ["labstack/echo"],

    # ORMs / Database
    "Prisma": ["prisma", "schema.prisma", "@prisma/client"],
    "SQLAlchemy": ["sqlalchemy", "from sqlalchemy"],
    "TypeORM": ["typeorm", "@Entity"],
    "Drizzle": ["drizzle-orm"],
    "Sequelize": ["sequelize"],
    "Mongoose": ["mongoose"],

    # CSS/UI
    "Tailwind CSS": ["tailwind.config", "tailwindcss"],
    "Styled Components": ["styled-components"],
    "Material UI": ["@mui/material", "@material-ui"],
    "Chakra UI": ["@chakra-ui"],
    "Radix UI": ["@radix-ui"],
    "shadcn/ui": ["@/components/ui", "components/ui"],
}

DATABASE_PATTERNS = {
    "PostgreSQL": ["postgresql", "postgres", "pg", "psycopg"],
    "MySQL": ["mysql", "mysql2"],
    "MongoDB": ["mongodb", "mongoose"],
    "Redis": ["redis", "ioredis"],
    "SQLite": ["sqlite", "sqlite3"],
    "Supabase": ["@supabase/supabase-js", "supabase"],
    "Firebase": ["firebase", "@firebase"],
    "DynamoDB": ["dynamodb", "@aws-sdk/client-dynamodb"],
}

BUILD_TOOL_PATTERNS = {
    "Vite": ["vite.config", "vite"],
    "Webpack": ["webpack.config"],
    "Turbopack": ["turbo.json"],
    "esbuild": ["esbuild"],
    "Rollup": ["rollup.config"],
    "Parcel": ["parcel"],
    "Poetry": ["pyproject.toml", "[tool.poetry]"],
    "pip": ["requirements.txt"],
    "npm": ["package.json"],
    "pnpm": ["pnpm-workspace.yaml", "pnpm-lock.yaml"],
    "yarn": ["yarn.lock", ".yarnrc"],
    "bun": ["bun.lockb", "bunfig.toml"],
}

TESTING_PATTERNS = {
    "Jest": ["jest.config", "@jest"],
    "Vitest": ["vitest.config", "vitest"],
    "Playwright": ["playwright.config"],
    "Cypress": ["cypress.config"],
    "pytest": ["pytest", "conftest.py"],
    "unittest": ["unittest"],
    "Mocha": ["mocha"],
    "Testing Library": ["@testing-library"],
}


class CodebaseAnalyzer:
    """
    Analyze a codebase to understand its purpose and structure.

    Example:
        from .github_fetcher import RepositoryContent

        analyzer = CodebaseAnalyzer()
        context = await analyzer.analyze(repo_content)

        print(f"Platform: {context.platform_purpose}")
        print(f"Stack: {context.tech_stack.frameworks}")
    """

    def __init__(self):
        self._parser = None

    def _get_parser(self):
        """Lazy load code parser"""
        if self._parser is None:
            try:
                from ..ai.code_parser import CodeParser
                self._parser = CodeParser()
            except ImportError:
                logger.warning("CodeParser not available")
        return self._parser

    async def analyze(
        self,
        files: Dict[str, str],
        metadata: Optional[Dict[str, Any]] = None,
        readme: Optional[str] = None,
        package_json: Optional[Dict] = None,
        requirements_txt: Optional[str] = None,
        languages: Optional[Dict[str, int]] = None
    ) -> CodebaseContext:
        """
        Build comprehensive understanding of a codebase.

        Args:
            files: Dict of file path -> content
            metadata: Repository metadata (from GitHub API)
            readme: README content
            package_json: Parsed package.json
            requirements_txt: requirements.txt content
            languages: Language breakdown from GitHub

        Returns:
            CodebaseContext with full analysis
        """
        # Detect tech stack
        tech_stack = self._detect_tech_stack(files, package_json, requirements_txt)

        # Identify architecture
        architecture = self._identify_architecture(files, tech_stack)

        # Analyze folder structure
        folder_structure = self._analyze_folders(files)

        # Find entry points
        frontend_entry, backend_entry = self._find_entry_points(files, tech_stack)

        # Extract API routes
        api_routes = self._extract_api_routes(files, tech_stack)

        # Calculate metrics
        total_lines = sum(content.count('\n') + 1 for content in files.values())

        # Determine platform type
        platform_type = self._determine_platform_type(tech_stack, architecture, files)

        # Extract platform purpose
        platform_purpose = self._extract_platform_purpose(
            readme, metadata, tech_stack, platform_type
        )

        # Language breakdown
        langs_breakdown = languages or self._calculate_languages(files)

        return CodebaseContext(
            platform_purpose=platform_purpose,
            platform_type=platform_type,
            tech_stack=tech_stack,
            architecture_type=architecture,
            folder_structure=folder_structure,
            frontend_entry=frontend_entry,
            backend_entry=backend_entry,
            api_routes=api_routes,
            total_files=len(files),
            total_lines=total_lines,
            languages_breakdown=langs_breakdown,
        )

    def _detect_tech_stack(
        self,
        files: Dict[str, str],
        package_json: Optional[Dict],
        requirements_txt: Optional[str]
    ) -> TechStack:
        """Detect frameworks, libraries, and tools"""
        stack = TechStack()

        # Combine all file content for searching
        all_content = "\n".join(files.values())
        all_paths = list(files.keys())

        # Detect frameworks
        for framework, patterns in FRAMEWORK_PATTERNS.items():
            for pattern in patterns:
                if pattern in all_content or any(pattern in p for p in all_paths):
                    if framework not in stack.frameworks:
                        stack.frameworks.append(framework)
                    break

        # Detect databases
        for db, patterns in DATABASE_PATTERNS.items():
            for pattern in patterns:
                if pattern in all_content:
                    if db not in stack.databases:
                        stack.databases.append(db)
                    break

        # Detect build tools
        for tool, patterns in BUILD_TOOL_PATTERNS.items():
            for pattern in patterns:
                if pattern in all_content or any(pattern in p for p in all_paths):
                    if tool not in stack.build_tools:
                        stack.build_tools.append(tool)
                    break

        # Detect testing
        for test, patterns in TESTING_PATTERNS.items():
            for pattern in patterns:
                if pattern in all_content or any(pattern in p for p in all_paths):
                    if test not in stack.testing:
                        stack.testing.append(test)
                    break

        # Parse package.json for more details
        if package_json:
            deps = {
                **package_json.get("dependencies", {}),
                **package_json.get("devDependencies", {})
            }

            for dep in deps:
                # Check known frameworks
                for framework, patterns in FRAMEWORK_PATTERNS.items():
                    if any(p in dep for p in patterns if not p.endswith(('.js', '.ts', '.tsx', '.jsx'))):
                        if framework not in stack.frameworks:
                            stack.frameworks.append(framework)

        # Parse requirements.txt
        if requirements_txt:
            for line in requirements_txt.split('\n'):
                line = line.strip().lower()
                if not line or line.startswith('#'):
                    continue

                # Extract package name
                pkg = re.split(r'[<>=!~\[\]]', line)[0].strip()

                for framework, patterns in FRAMEWORK_PATTERNS.items():
                    if any(p.lower() == pkg for p in patterns):
                        if framework not in stack.frameworks:
                            stack.frameworks.append(framework)

        # Detect languages from file extensions
        ext_to_lang = {
            '.py': 'Python', '.js': 'JavaScript', '.ts': 'TypeScript',
            '.tsx': 'TypeScript', '.jsx': 'JavaScript', '.go': 'Go',
            '.rs': 'Rust', '.java': 'Java', '.rb': 'Ruby',
            '.php': 'PHP', '.cs': 'C#', '.swift': 'Swift',
            '.kt': 'Kotlin', '.scala': 'Scala',
        }

        for path in files:
            ext = Path(path).suffix.lower()
            if ext in ext_to_lang:
                lang = ext_to_lang[ext]
                if lang not in stack.languages:
                    stack.languages.append(lang)

        return stack

    def _identify_architecture(
        self,
        files: Dict[str, str],
        tech_stack: TechStack
    ) -> ArchitectureType:
        """Identify the architecture pattern"""
        paths = list(files.keys())

        # Check for monorepo
        if any("apps/" in p or "packages/" in p for p in paths):
            if any("pnpm-workspace" in p or "turbo.json" in p or "lerna.json" in p for p in paths):
                return ArchitectureType.MONOREPO

        # Check for Next.js (SSR)
        if "Next.js" in tech_stack.frameworks:
            if any("app/" in p or "pages/" in p for p in paths):
                return ArchitectureType.SSR

        # Check for SPA
        spa_indicators = ["index.html", "public/index.html", "src/main.tsx", "src/main.ts"]
        if any(ind in p for p in paths for ind in spa_indicators):
            if not any(f in tech_stack.frameworks for f in ["Django", "Rails", "Laravel", "FastAPI"]):
                return ArchitectureType.SPA

        # Check for microservices
        service_dirs = ["services/", "microservices/", "api-gateway/"]
        if sum(1 for p in paths if any(s in p for s in service_dirs)) > 3:
            return ArchitectureType.MICROSERVICES

        # Check for serverless
        serverless_indicators = ["serverless.yml", "serverless.ts", "functions/", "netlify.toml"]
        if any(ind in p for p in paths for ind in serverless_indicators):
            return ArchitectureType.SERVERLESS

        # Check for MVC
        if any(f in tech_stack.frameworks for f in ["Django", "Rails", "Laravel", "Spring Boot"]):
            return ArchitectureType.MVC

        # Default to monolith
        return ArchitectureType.MONOLITH

    def _analyze_folders(self, files: Dict[str, str]) -> List[FolderInfo]:
        """Analyze folder structure and purposes"""
        folder_files: Dict[str, int] = {}
        folder_patterns: Dict[str, Set[str]] = {}

        for path in files:
            parts = Path(path).parts
            if len(parts) > 1:
                folder = parts[0]
                folder_files[folder] = folder_files.get(folder, 0) + 1

                ext = Path(path).suffix
                if folder not in folder_patterns:
                    folder_patterns[folder] = set()
                folder_patterns[folder].add(ext)

        # Map folders to purposes
        folder_purposes = {
            "src": "Source code",
            "app": "Application code (Next.js App Router)",
            "pages": "Page components (Next.js Pages Router)",
            "components": "React/Vue components",
            "lib": "Library/utility code",
            "utils": "Utility functions",
            "hooks": "React hooks",
            "api": "API routes/handlers",
            "routes": "Route definitions",
            "services": "Service layer",
            "models": "Data models",
            "schemas": "Database/validation schemas",
            "prisma": "Prisma ORM schemas",
            "public": "Static assets",
            "assets": "Static assets",
            "styles": "CSS/styling",
            "tests": "Test files",
            "__tests__": "Test files",
            "spec": "Test specifications",
            "config": "Configuration files",
            "scripts": "Build/utility scripts",
            "docs": "Documentation",
            "types": "TypeScript type definitions",
            "interfaces": "Interface definitions",
            "middleware": "Middleware functions",
            "controllers": "MVC controllers",
            "views": "MVC views",
            "templates": "Template files",
        }

        result = []
        for folder, count in sorted(folder_files.items(), key=lambda x: -x[1]):
            purpose = folder_purposes.get(folder.lower(), "Project files")
            patterns = list(folder_patterns.get(folder, []))

            result.append(FolderInfo(
                path=folder,
                purpose=purpose,
                file_count=count,
                patterns=patterns
            ))

        return result[:15]  # Top 15 folders

    def _find_entry_points(
        self,
        files: Dict[str, str],
        tech_stack: TechStack
    ) -> Tuple[Optional[str], Optional[str]]:
        """Find frontend and backend entry points"""
        frontend_entry = None
        backend_entry = None

        paths = list(files.keys())

        # Frontend entry points
        frontend_entries = [
            "src/main.tsx", "src/main.ts", "src/index.tsx", "src/index.ts",
            "app/layout.tsx", "app/layout.jsx", "pages/_app.tsx", "pages/_app.jsx",
            "src/App.tsx", "src/App.jsx", "src/App.vue",
            "index.html", "public/index.html"
        ]

        for entry in frontend_entries:
            if entry in paths:
                frontend_entry = entry
                break

        # Backend entry points
        backend_entries = [
            "src/main.py", "app/main.py", "main.py", "app.py",
            "src/index.ts", "src/server.ts", "server.ts", "server.js",
            "cmd/main.go", "main.go",
            "src/main.rs", "src/lib.rs",
            "app.rb", "config.ru",
        ]

        for entry in backend_entries:
            if entry in paths:
                backend_entry = entry
                break

        return frontend_entry, backend_entry

    def _extract_api_routes(
        self,
        files: Dict[str, str],
        tech_stack: TechStack
    ) -> List[str]:
        """Extract API route patterns from code"""
        routes = []

        # FastAPI routes
        fastapi_pattern = r'@(?:app|router)\.(get|post|put|patch|delete)\s*\(\s*["\']([^"\']+)["\']'

        # Express routes
        express_pattern = r'(?:app|router)\.(get|post|put|patch|delete)\s*\(\s*["\']([^"\']+)["\']'

        # Next.js API routes (from file structure)
        nextjs_api_pattern = r'(?:pages|app)/api/(.+?)(?:/route)?\.(ts|js)'

        for path, content in files.items():
            # Check FastAPI/Express patterns
            matches = re.findall(fastapi_pattern, content, re.IGNORECASE)
            matches.extend(re.findall(express_pattern, content, re.IGNORECASE))

            for method, route in matches:
                route_str = f"{method.upper()} {route}"
                if route_str not in routes:
                    routes.append(route_str)

            # Check Next.js API routes
            match = re.match(nextjs_api_pattern, path)
            if match:
                route = f"/api/{match.group(1).replace('[', '{').replace(']', '}')}"
                if route not in routes:
                    routes.append(route)

        return routes[:50]  # Limit to 50 routes

    def _determine_platform_type(
        self,
        tech_stack: TechStack,
        architecture: ArchitectureType,
        files: Dict[str, str]
    ) -> PlatformType:
        """Determine what type of platform this is"""
        paths = list(files.keys())

        # Check for monorepo
        if architecture == ArchitectureType.MONOREPO:
            return PlatformType.MONOREPO

        # Check for library/package
        lib_indicators = ["index.d.ts", "lib/", "dist/", "setup.py", "pyproject.toml"]
        has_lib = any(ind in p for p in paths for ind in lib_indicators)
        no_frontend = not any(f in tech_stack.frameworks for f in ["React", "Vue.js", "Angular", "Svelte"])
        if has_lib and no_frontend:
            return PlatformType.LIBRARY

        # Check for CLI
        cli_indicators = ["cli.py", "cli.ts", "cli.js", "bin/", "commander", "yargs", "argparse"]
        if any(ind in p or ind in str(files.get(p, "")) for p in paths for ind in cli_indicators):
            return PlatformType.CLI

        # Check for API only
        has_frontend_framework = any(
            f in tech_stack.frameworks
            for f in ["React", "Vue.js", "Angular", "Svelte", "Next.js"]
        )
        has_backend_framework = any(
            f in tech_stack.frameworks
            for f in ["FastAPI", "Django", "Flask", "Express.js", "NestJS"]
        )

        if has_backend_framework and not has_frontend_framework:
            return PlatformType.API

        # Check for fullstack
        if has_frontend_framework and has_backend_framework:
            return PlatformType.FULLSTACK

        # Check for web app
        if has_frontend_framework:
            return PlatformType.WEB_APP

        return PlatformType.UNKNOWN

    def _extract_platform_purpose(
        self,
        readme: Optional[str],
        metadata: Optional[Dict],
        tech_stack: TechStack,
        platform_type: PlatformType
    ) -> str:
        """Extract what the platform does from README and metadata"""
        description_parts = []

        # Get description from metadata
        if metadata and metadata.get("description"):
            description_parts.append(metadata["description"])

        # Parse README for description
        if readme:
            # Try to get first paragraph after title
            lines = readme.split('\n')
            in_description = False
            description_lines = []

            for line in lines:
                # Skip title lines
                if line.startswith('#'):
                    in_description = True
                    continue

                if in_description:
                    # Stop at next header or empty line after content
                    if line.startswith('#') or (not line.strip() and description_lines):
                        break

                    if line.strip():
                        # Skip badges
                        if '![' not in line and '[![' not in line:
                            description_lines.append(line.strip())

            if description_lines:
                readme_desc = ' '.join(description_lines[:3])  # First 3 lines
                if readme_desc and readme_desc not in description_parts:
                    description_parts.append(readme_desc)

        # Build description from tech stack if nothing else
        if not description_parts:
            type_desc = {
                PlatformType.WEB_APP: "Web application",
                PlatformType.API: "API service",
                PlatformType.LIBRARY: "Software library",
                PlatformType.CLI: "Command-line tool",
                PlatformType.FULLSTACK: "Full-stack application",
                PlatformType.MONOREPO: "Monorepo project",
            }.get(platform_type, "Software project")

            framework_str = ", ".join(tech_stack.frameworks[:3]) if tech_stack.frameworks else "custom stack"
            description_parts.append(f"{type_desc} built with {framework_str}")

        return " ".join(description_parts)[:500]  # Limit length

    def _calculate_languages(self, files: Dict[str, str]) -> Dict[str, int]:
        """Calculate language breakdown from files"""
        lang_bytes: Dict[str, int] = {}

        ext_to_lang = {
            '.py': 'Python', '.js': 'JavaScript', '.ts': 'TypeScript',
            '.tsx': 'TypeScript', '.jsx': 'JavaScript', '.go': 'Go',
            '.rs': 'Rust', '.java': 'Java', '.rb': 'Ruby',
            '.php': 'PHP', '.cs': 'C#', '.swift': 'Swift',
            '.kt': 'Kotlin', '.scala': 'Scala', '.vue': 'Vue',
            '.svelte': 'Svelte', '.html': 'HTML', '.css': 'CSS',
            '.scss': 'SCSS', '.json': 'JSON', '.yaml': 'YAML',
            '.yml': 'YAML', '.md': 'Markdown',
        }

        for path, content in files.items():
            ext = Path(path).suffix.lower()
            lang = ext_to_lang.get(ext, "Other")
            lang_bytes[lang] = lang_bytes.get(lang, 0) + len(content.encode('utf-8'))

        return lang_bytes


# Convenience function
async def analyze_codebase(
    files: Dict[str, str],
    **kwargs
) -> CodebaseContext:
    """Analyze a codebase from files dict"""
    analyzer = CodebaseAnalyzer()
    return await analyzer.analyze(files, **kwargs)
