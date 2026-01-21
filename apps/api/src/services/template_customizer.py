"""
Template Customizer Service

Orchestrates the template-first generation approach:
1. Select appropriate template based on user description
2. Keep protected files (configs) unchanged
3. Have AI customize only the content files
4. Validate output before sending to WebContainer
5. Fall back to clean template if validation fails

This ensures a working base that AI customizes, rather than generating from scratch.
"""

import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from .template_loader import get_template_loader, Template, TemplateFile
from .code_validator import validate_files, validate_and_fix, ValidationResult


class CustomizationMode(Enum):
    """How much the AI should customize"""
    MINIMAL = "minimal"      # Just change brand colors and text
    MODERATE = "moderate"    # Modify components, add/remove sections
    EXTENSIVE = "extensive"  # Create new pages, significant changes


@dataclass
class BrandProfile:
    """Brand colors and styling extracted from client's site"""
    primary_color: str = "#3B82F6"      # Blue
    secondary_color: str = "#10B981"    # Green
    accent_color: str = "#F59E0B"       # Amber
    background: str = "#F8FAFC"         # Light gray
    surface: str = "#FFFFFF"            # White
    text_primary: str = "#1E293B"       # Slate 800
    text_muted: str = "#64748B"         # Slate 500
    font_heading: str = "Inter"
    font_body: str = "Inter"
    border_radius: str = "0.75rem"
    company_name: str = "Acme Inc"
    style: str = "modern"  # modern, corporate, playful, minimal

    def to_css_variables(self) -> str:
        """Generate CSS variables for the brand"""
        return f"""
:root {{
  --brand-primary: {self.primary_color};
  --brand-secondary: {self.secondary_color};
  --brand-accent: {self.accent_color};
  --bg-background: {self.background};
  --bg-surface: {self.surface};
  --text-primary: {self.text_primary};
  --text-muted: {self.text_muted};
  --font-heading: '{self.font_heading}', system-ui, sans-serif;
  --font-body: '{self.font_body}', system-ui, sans-serif;
  --radius: {self.border_radius};
}}
"""

    def to_tailwind_extend(self) -> Dict:
        """Generate Tailwind theme extension"""
        return {
            "colors": {
                "brand": {
                    "primary": self.primary_color,
                    "secondary": self.secondary_color,
                    "accent": self.accent_color,
                },
                "surface": {
                    "DEFAULT": self.surface,
                    "muted": self.background,
                },
                "content": {
                    "DEFAULT": self.text_primary,
                    "muted": self.text_muted,
                }
            },
            "fontFamily": {
                "heading": [self.font_heading, "system-ui", "sans-serif"],
                "body": [self.font_body, "system-ui", "sans-serif"],
            },
            "borderRadius": {
                "DEFAULT": self.border_radius,
            }
        }


@dataclass
class CustomizationRequest:
    """Request to customize a template"""
    description: str
    brand: Optional[BrandProfile] = None
    mode: CustomizationMode = CustomizationMode.MODERATE
    specific_pages: Optional[List[str]] = None  # Only customize these pages
    mock_data_context: Optional[str] = None  # Industry/company info for realistic data


@dataclass
class CustomizationResult:
    """Result of template customization"""
    success: bool
    files: Dict[str, str]
    template_id: str
    validation: ValidationResult
    warnings: List[str]
    fallback_used: bool = False


class TemplateCustomizer:
    """
    Manages template-based project generation.

    Key principles:
    1. Templates are pre-tested to work in WebContainer
    2. Protected files (configs) are NEVER modified by AI
    3. AI only customizes content files (pages, components)
    4. All output is validated before use
    5. If validation fails, clean template is used as fallback
    """

    def __init__(self):
        self.template_loader = get_template_loader()

    def get_customization_prompt(
        self,
        template: Template,
        request: CustomizationRequest
    ) -> str:
        """
        Generate the prompt for AI to customize the template.

        This prompt is carefully crafted to:
        - Show AI the existing files to customize
        - Provide strict rules to prevent common errors
        - Include brand profile for styling
        - Limit scope to customizable files only
        """
        brand = request.brand or BrandProfile()

        customizable_files = {
            path: file for path, file in template.files.items()
            if path not in template.protected_files
        }

        # Build file context
        files_context = []
        for path, file in customizable_files.items():
            files_context.append(f"### {path}\n```\n{file.content}\n```")

        files_str = "\n\n".join(files_context)

        prompt = f"""You are customizing a pre-built {template.name} template for: {request.description}

## Brand Profile
- Company: {brand.company_name}
- Primary Color: {brand.primary_color}
- Secondary Color: {brand.secondary_color}
- Accent Color: {brand.accent_color}
- Style: {brand.style}

## CRITICAL RULES (MUST FOLLOW)

### Files You CAN Modify
These are the only files you can change:
{chr(10).join(f'- {path}' for path in customizable_files.keys())}

### Files You CANNOT Modify
These files are protected and already optimized:
{chr(10).join(f'- {path}' for path in template.protected_files)}

### Code Rules (VIOLATIONS WILL CAUSE ERRORS)
1. Every file with useState, useEffect, onClick, or any React hook MUST start with 'use client' as the FIRST line
2. NEVER use next/image - use <img> tags instead
3. NEVER use next/font - fonts are already configured
4. Use 'next/navigation' for useRouter (NOT 'next/router')
5. ONLY use standard Tailwind classes (bg-blue-500, text-gray-900, etc.)
6. NEVER use shadcn classes (border-border, bg-background, text-foreground)
7. Keep all existing imports - only add new ones if needed
8. Use the brand CSS variables: text-brand-primary, bg-brand-secondary, etc.

### Styling Guidelines
- Use Tailwind utility classes
- Brand colors via: text-brand-primary, bg-brand-primary, text-brand-secondary, etc.
- Surface colors: bg-surface, bg-surface-muted
- Content colors: text-content, text-content-muted
- Keep the existing layout structure

## Current Template Files

{files_str}

## Your Task
Customize these files to match the user's description: "{request.description}"

Customization level: {request.mode.value}
{f"Industry context for mock data: {request.mock_data_context}" if request.mock_data_context else ""}

Return ONLY the modified files as a JSON object:
{{
  "path/to/file.tsx": "file content...",
  "path/to/other.tsx": "file content..."
}}

Do NOT include protected files in your response. They will be merged automatically.
"""
        return prompt

    def merge_with_protected(
        self,
        template: Template,
        customized_files: Dict[str, str]
    ) -> Dict[str, str]:
        """
        Merge AI-customized files with protected template files.

        Protected files (configs, error boundaries) come from template.
        Customized files come from AI.
        """
        result = {}

        # Add all protected files from template
        for path in template.protected_files:
            if path in template.files:
                result[path] = template.files[path].content

        # Add customized files (overwriting template versions)
        for path, content in customized_files.items():
            result[path] = content

        # Add any remaining template files not in protected or customized
        for path, file in template.files.items():
            if path not in result:
                result[path] = file.content

        return result

    def apply_brand_to_template(
        self,
        files: Dict[str, str],
        brand: BrandProfile
    ) -> Dict[str, str]:
        """
        Apply brand colors to template by updating tailwind.config.js.

        This is a safe operation that only modifies the color definitions.
        """
        result = dict(files)

        # Update tailwind.config.js with brand colors
        if "tailwind.config.js" in result:
            config_content = result["tailwind.config.js"]

            # Find and replace color definitions
            new_colors = f"""colors: {{
        brand: {{
          primary: '{brand.primary_color}',
          secondary: '{brand.secondary_color}',
          accent: '{brand.accent_color}',
        }},
        surface: {{
          DEFAULT: '{brand.surface}',
          muted: '{brand.background}',
        }},
        content: {{
          DEFAULT: '{brand.text_primary}',
          muted: '{brand.text_muted}',
        }},
      }},"""

            # Replace existing colors block (simplified - in production, use AST)
            import re
            config_content = re.sub(
                r"colors:\s*\{[^}]+\{[^}]+\}[^}]+\{[^}]+\}[^}]+\{[^}]+\}[^}]+\},",
                new_colors,
                config_content,
                flags=re.DOTALL
            )
            result["tailwind.config.js"] = config_content

        return result

    async def customize(
        self,
        request: CustomizationRequest,
        ai_generate_fn=None  # Function to call AI for customization
    ) -> CustomizationResult:
        """
        Main entry point for template customization.

        Steps:
        1. Select best template for the description
        2. Generate prompt for AI customization
        3. Have AI customize the template
        4. Validate the result
        5. If validation fails, attempt auto-fix
        6. If still failing, fall back to clean template

        Args:
            request: Customization request with description and brand
            ai_generate_fn: Async function that takes prompt and returns Dict[str, str]

        Returns:
            CustomizationResult with files and validation status
        """
        warnings = []

        # Step 1: Select template
        template = self.template_loader.select_template(request.description)
        if not template:
            return CustomizationResult(
                success=False,
                files={},
                template_id="none",
                validation=ValidationResult(is_valid=False, errors=[], warnings=[]),
                warnings=["No templates available"],
                fallback_used=False
            )

        # Step 2: Get template files as base
        base_files = self.template_loader.get_template_files_dict(template.id)

        # If no AI function provided, just return template with brand applied
        if ai_generate_fn is None:
            if request.brand:
                base_files = self.apply_brand_to_template(base_files, request.brand)

            validation = validate_files(base_files)
            return CustomizationResult(
                success=True,
                files=base_files,
                template_id=template.id,
                validation=validation,
                warnings=["No AI customization - returned base template"],
                fallback_used=False
            )

        # Step 3: Generate customization prompt
        prompt = self.get_customization_prompt(template, request)

        # Step 4: Call AI to customize
        try:
            customized_files = await ai_generate_fn(prompt)
        except Exception as e:
            warnings.append(f"AI customization failed: {e}")
            # Fall back to template
            if request.brand:
                base_files = self.apply_brand_to_template(base_files, request.brand)
            validation = validate_files(base_files)
            return CustomizationResult(
                success=True,
                files=base_files,
                template_id=template.id,
                validation=validation,
                warnings=warnings,
                fallback_used=True
            )

        # Step 5: Merge with protected files
        merged_files = self.merge_with_protected(template, customized_files)

        # Apply brand if provided
        if request.brand:
            merged_files = self.apply_brand_to_template(merged_files, request.brand)

        # Step 6: Validate
        fixed_files, validation = validate_and_fix(merged_files)

        if not validation.is_valid:
            # Log what failed
            for error in validation.errors:
                warnings.append(f"Validation error: {error.code} in {error.file_path}")

            # Fall back to clean template
            warnings.append("Falling back to clean template due to validation errors")
            if request.brand:
                base_files = self.apply_brand_to_template(base_files, request.brand)

            fallback_validation = validate_files(base_files)
            return CustomizationResult(
                success=True,  # Still "success" because we have working files
                files=base_files,
                template_id=template.id,
                validation=fallback_validation,
                warnings=warnings,
                fallback_used=True
            )

        return CustomizationResult(
            success=True,
            files=fixed_files,
            template_id=template.id,
            validation=validation,
            warnings=warnings,
            fallback_used=False
        )

    def get_template_for_preview(
        self,
        description: str,
        brand: Optional[BrandProfile] = None
    ) -> Dict[str, str]:
        """
        Get a template ready for immediate preview (no AI customization).

        This is useful for:
        - Instant preview while AI works
        - Quick demos without waiting for generation
        - Fallback when AI fails
        """
        template = self.template_loader.select_template(description)
        if not template:
            return {}

        files = self.template_loader.get_template_files_dict(template.id)

        if brand:
            files = self.apply_brand_to_template(files, brand)

        return files


# Global instance
_customizer: Optional[TemplateCustomizer] = None


def get_template_customizer() -> TemplateCustomizer:
    """Get the global template customizer instance"""
    global _customizer
    if _customizer is None:
        _customizer = TemplateCustomizer()
    return _customizer
