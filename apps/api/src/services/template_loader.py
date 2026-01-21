"""
Template Loader Service

Loads pre-built, WebContainer-tested templates as the foundation for generated projects.
This ensures a working base that AI can customize, rather than generating from scratch.
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel


class TemplateFile(BaseModel):
    """A single file in a template"""
    path: str
    content: str
    is_customizable: bool = True  # Can AI modify this file?
    description: str = ""


class Template(BaseModel):
    """A complete project template"""
    id: str
    name: str
    description: str
    category: str  # dashboard, landing-page, e-commerce, etc.
    files: Dict[str, TemplateFile]
    keywords: List[str]  # For matching user descriptions

    # Files that should NEVER be modified by AI (guaranteed to work)
    protected_files: List[str] = [
        "package.json",
        "next.config.mjs",
        ".babelrc",
        "tsconfig.json",
        "tailwind.config.js",
        "postcss.config.js",
        "src/components/ErrorBoundary.tsx",
    ]


class TemplateLoader:
    """Loads and manages project templates"""

    def __init__(self, templates_dir: Optional[str] = None):
        if templates_dir:
            self.templates_dir = Path(templates_dir)
        else:
            # Default to templates directory relative to this file
            self.templates_dir = Path(__file__).parent.parent.parent / "templates"

        self._templates: Dict[str, Template] = {}
        self._load_templates()

    def _load_templates(self):
        """Load all templates from the templates directory"""
        if not self.templates_dir.exists():
            print(f"Warning: Templates directory not found: {self.templates_dir}")
            return

        for template_dir in self.templates_dir.iterdir():
            if template_dir.is_dir():
                template = self._load_template(template_dir)
                if template:
                    self._templates[template.id] = template

    def _load_template(self, template_dir: Path) -> Optional[Template]:
        """Load a single template from a directory"""
        template_id = template_dir.name
        files: Dict[str, TemplateFile] = {}

        # Walk through all files in the template directory
        for file_path in template_dir.rglob("*"):
            if file_path.is_file():
                # Get relative path from template root
                rel_path = file_path.relative_to(template_dir)
                rel_path_str = str(rel_path).replace("\\", "/")

                # Skip node_modules and other non-essential files
                if any(skip in rel_path_str for skip in ["node_modules", ".git", ".next"]):
                    continue

                try:
                    content = file_path.read_text(encoding="utf-8")
                    files[rel_path_str] = TemplateFile(
                        path=rel_path_str,
                        content=content,
                        is_customizable=rel_path_str not in Template.model_fields["protected_files"].default,
                        description=self._get_file_description(rel_path_str)
                    )
                except Exception as e:
                    print(f"Warning: Could not read {file_path}: {e}")

        if not files:
            return None

        # Determine template metadata
        return Template(
            id=template_id,
            name=self._get_template_name(template_id),
            description=self._get_template_description(template_id),
            category=self._get_template_category(template_id),
            files=files,
            keywords=self._get_template_keywords(template_id)
        )

    def _get_file_description(self, path: str) -> str:
        """Get description for a file based on its path"""
        descriptions = {
            "package.json": "Project dependencies and scripts",
            "next.config.mjs": "Next.js configuration",
            ".babelrc": "Babel configuration for WebContainer",
            "tsconfig.json": "TypeScript configuration",
            "tailwind.config.js": "Tailwind CSS configuration with brand variables",
            "postcss.config.js": "PostCSS configuration",
            "src/app/layout.tsx": "Root layout with ErrorBoundary",
            "src/app/page.tsx": "Main page component",
            "src/app/globals.css": "Global styles and Tailwind imports",
            "src/components/ErrorBoundary.tsx": "Error boundary for catching React errors",
        }
        return descriptions.get(path, "")

    def _get_template_name(self, template_id: str) -> str:
        """Get human-readable name for template"""
        names = {
            "dashboard": "Dashboard",
            "landing-page": "Landing Page",
            "e-commerce": "E-commerce",
            "saas-app": "SaaS Application",
        }
        return names.get(template_id, template_id.replace("-", " ").title())

    def _get_template_description(self, template_id: str) -> str:
        """Get description for template"""
        descriptions = {
            "dashboard": "Modern analytics dashboard with sidebar navigation, stats cards, charts, and data tables",
            "landing-page": "Marketing landing page with hero, features, pricing, and call-to-action sections",
            "e-commerce": "E-commerce storefront with product grid, cart, and checkout flow",
            "saas-app": "SaaS application with authentication, settings, and user management",
        }
        return descriptions.get(template_id, f"Template for {template_id}")

    def _get_template_category(self, template_id: str) -> str:
        """Get category for template"""
        categories = {
            "dashboard": "dashboard",
            "landing-page": "marketing",
            "e-commerce": "commerce",
            "saas-app": "application",
        }
        return categories.get(template_id, "general")

    def _get_template_keywords(self, template_id: str) -> List[str]:
        """Get keywords for template matching"""
        keywords = {
            "dashboard": ["dashboard", "admin", "analytics", "metrics", "stats", "data", "management", "panel", "console"],
            "landing-page": ["landing", "marketing", "homepage", "product", "startup", "saas", "hero", "features", "pricing"],
            "e-commerce": ["shop", "store", "ecommerce", "e-commerce", "products", "cart", "checkout", "buy", "sell"],
            "saas-app": ["app", "application", "saas", "software", "platform", "tool", "service"],
        }
        return keywords.get(template_id, [template_id])

    def get_template(self, template_id: str) -> Optional[Template]:
        """Get a specific template by ID"""
        return self._templates.get(template_id)

    def list_templates(self) -> List[Template]:
        """List all available templates"""
        return list(self._templates.values())

    def select_template(self, description: str) -> Template:
        """Select the best template based on user description"""
        description_lower = description.lower()

        # Score each template based on keyword matches
        scores: Dict[str, int] = {}
        for template_id, template in self._templates.items():
            score = 0
            for keyword in template.keywords:
                if keyword in description_lower:
                    score += 1
            scores[template_id] = score

        # Return template with highest score, or default to dashboard
        if scores:
            best_match = max(scores, key=scores.get)
            if scores[best_match] > 0:
                return self._templates[best_match]

        # Default to dashboard if no match
        return self._templates.get("dashboard", list(self._templates.values())[0] if self._templates else None)

    def get_template_files_dict(self, template_id: str) -> Dict[str, str]:
        """Get template files as a simple path -> content dictionary"""
        template = self.get_template(template_id)
        if not template:
            return {}

        return {path: file.content for path, file in template.files.items()}

    def get_protected_files(self, template_id: str) -> Dict[str, str]:
        """Get only the protected (non-modifiable) files from a template"""
        template = self.get_template(template_id)
        if not template:
            return {}

        return {
            path: file.content
            for path, file in template.files.items()
            if path in template.protected_files
        }

    def get_customizable_files(self, template_id: str) -> Dict[str, str]:
        """Get only the customizable files from a template"""
        template = self.get_template(template_id)
        if not template:
            return {}

        return {
            path: file.content
            for path, file in template.files.items()
            if path not in template.protected_files
        }


# Global instance
_template_loader: Optional[TemplateLoader] = None


def get_template_loader() -> TemplateLoader:
    """Get the global template loader instance"""
    global _template_loader
    if _template_loader is None:
        _template_loader = TemplateLoader()
    return _template_loader
