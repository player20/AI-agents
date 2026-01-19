"""
Vision-based UI Analysis using Claude Vision API

Sends screenshots to Claude's multimodal model for actual visual analysis.
This enables the self-improver to detect visual issues that are invisible
in code-only analysis.
"""

import base64
import os
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional


class VisionAnalyzer:
    """
    Analyzes UI screenshots using Claude Vision API.

    Encodes screenshots as base64 and sends them to Claude's multimodal
    model for comprehensive visual analysis.
    """

    def __init__(self, model: str = "claude-sonnet-4-20250514"):
        """
        Initialize the vision analyzer.

        Args:
            model: Claude model to use (must support vision)
        """
        self.model = model
        self._client = None

    @property
    def client(self):
        """Lazy-load Anthropic client."""
        if self._client is None:
            try:
                import anthropic
                self._client = anthropic.Anthropic()
            except ImportError:
                raise ImportError("anthropic package required. Install with: pip install anthropic")
        return self._client

    def encode_image(self, image_path: str) -> Optional[str]:
        """
        Encode image as base64 for API.

        Args:
            image_path: Path to the image file

        Returns:
            Base64 encoded string or None if file doesn't exist
        """
        path = Path(image_path)
        if not path.exists():
            return None

        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def analyze_screenshots(
        self,
        screenshots: List[Dict],
        code_context: str = "",
        focus_areas: Optional[List[str]] = None,
        max_images: int = 10,
        console_errors: Optional[List[str]] = None,
        performance_metrics: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze screenshots using Claude Vision.

        Args:
            screenshots: List of {"name": str, "path": str, "viewport": dict, "console_errors": list}
            code_context: Optional code snippet for context
            focus_areas: Specific areas to focus on
            max_images: Maximum number of images to analyze (default 10)
            console_errors: JavaScript console errors detected during capture
            performance_metrics: Performance data (load times, Core Web Vitals)

        Returns:
            Dict with issues found and recommendations
        """
        # Aggregate console errors from screenshots if not provided directly
        if console_errors is None:
            console_errors = []
            for screenshot in screenshots:
                errors = screenshot.get("console_errors", [])
                console_errors.extend(errors)
            # Deduplicate
            console_errors = list(set(console_errors))

        if not screenshots:
            return {
                "issues": [],
                "raw_analysis": "No screenshots provided",
                "issue_count": 0
            }

        # Build message content
        content = [
            {
                "type": "text",
                "text": self._build_analysis_prompt(
                    code_context, focus_areas, console_errors, performance_metrics
                )
            }
        ]

        # Add each screenshot as an image
        images_added = 0
        for screenshot in screenshots:
            if images_added >= max_images:
                break

            image_path = screenshot.get("path", "")
            if not Path(image_path).exists():
                continue

            base64_data = self.encode_image(image_path)
            if not base64_data:
                continue

            # Add the image
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": base64_data
                }
            })

            # Add label for the image
            viewport = screenshot.get("viewport", {})
            width = viewport.get("width", "?")
            height = viewport.get("height", "?")
            content.append({
                "type": "text",
                "text": f"[Above: {screenshot.get('name', 'Unknown')} - {width}x{height}]"
            })

            images_added += 1

        if images_added == 0:
            return {
                "issues": [],
                "raw_analysis": "No valid screenshots found",
                "issue_count": 0
            }

        try:
            # Call Claude Vision
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=[{"role": "user", "content": content}]
            )

            response_text = response.content[0].text
            return self._parse_vision_response(response_text)

        except Exception as e:
            return {
                "issues": [],
                "raw_analysis": f"Vision analysis failed: {str(e)}",
                "issue_count": 0,
                "error": str(e)
            }

    def _build_analysis_prompt(
        self,
        code_context: str,
        focus_areas: Optional[List[str]],
        console_errors: Optional[List[str]] = None,
        performance_metrics: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build the vision analysis prompt with runtime context."""
        focus_text = ""
        if focus_areas:
            focus_text = "\n\nFOCUS AREAS:\n" + "\n".join(f"- {area}" for area in focus_areas)

        code_section = ""
        if code_context:
            code_section = f"\n\nCODE CONTEXT:\n{code_context[:2000]}"  # Limit context size

        # Add console errors section
        error_section = ""
        if console_errors and len(console_errors) > 0:
            error_section = f"""

==================== JAVASCRIPT CONSOLE ERRORS ====================
The following errors were captured during page navigation:

{chr(10).join(f"- {err[:200]}" for err in console_errors[:10])}

IMPORTANT: These runtime errors may indicate:
- Broken functionality that affects the visual state
- Missing resources or failed API calls
- JavaScript bugs that prevent proper rendering
- State management issues causing visual glitches

Look for visual symptoms of these errors in the screenshots.
"""

        # Add performance metrics section
        perf_section = ""
        if performance_metrics:
            perf_section = """

==================== PERFORMANCE METRICS ====================
"""
            if "load_time_ms" in performance_metrics:
                perf_section += f"Page Load Time: {performance_metrics['load_time_ms']}ms\n"
            if "lcp" in performance_metrics:
                perf_section += f"Largest Contentful Paint (LCP): {performance_metrics['lcp']}ms\n"
            if "cls" in performance_metrics:
                perf_section += f"Cumulative Layout Shift (CLS): {performance_metrics['cls']}\n"
            if "fid" in performance_metrics:
                perf_section += f"First Input Delay (FID): {performance_metrics['fid']}ms\n"

            perf_section += """
Check if slow load times or layout shifts are visible in screenshots.
"""

        return f"""You are a senior UI/UX expert reviewing a Streamlit application.
{error_section}{perf_section}

ANALYZE THESE SCREENSHOTS FOR SPECIFIC, ACTIONABLE ISSUES:

1. **Visual Consistency**
   - Color scheme consistency across pages
   - Typography hierarchy (h1 > h2 > h3 sizing)
   - Spacing and alignment consistency
   - Component styling uniformity
   - Gradient rendering quality

2. **Responsive Design Issues**
   - Compare desktop, tablet, and mobile views
   - Text wrapping problems
   - Layout breaking at specific widths
   - Touch target sizes (min 44px on mobile)
   - Horizontal scrolling issues

3. **Accessibility Problems**
   - Color contrast (WCAG AA: 4.5:1 for text)
   - Focus indicators visibility
   - Text readability
   - Button/input sizing

4. **Professional Polish**
   - Animation smoothness (if visible)
   - Hover/active states
   - Loading states visibility
   - Error state handling
   - Empty state handling

{focus_text}
{code_section}

FOR EACH ISSUE FOUND, PROVIDE:
1. **Page**: Which screenshot/page
2. **Element**: Specific element affected
3. **Problem**: What's wrong (with measurements if applicable)
4. **Expected**: What it should be
5. **File**: MUST be one of these EXACT paths:
   - streamlit_ui/onboarding.py (onboarding flow, welcome screen)
   - streamlit_ui/main_interface.py (main app interface)
   - streamlit_ui/self_improvement.py (self-improve mode)
   - streamlit_ui/constants.py (colors, dimensions, shared constants)
   - streamlit_ui/loading_states.py (loading animations)
   - streamlit_ui/enhanced_interface_input.py (input forms)
   - streamlit_ui/enhanced_interface_results.py (results display)
   - streamlit_ui/progress_tracker.py (progress indicators)
   - app.py (main app entry, global CSS)
6. **Priority**: HIGH/MEDIUM/LOW

IMPORTANT: Be SPECIFIC and ACTIONABLE. Don't say "improve consistency" -
say "Button padding is 8px on main_interface but 12px on onboarding".

Format your issues as a JSON array wrapped in ```json``` code blocks:

```json
[
  {{
    "page": "Main_Interface_Mobile",
    "element": "Start button",
    "problem": "Button text wraps to 2 lines at 375px width",
    "expected": "Button text on single line or button width increased",
    "file": "streamlit_ui/main_interface.py",
    "priority": "MEDIUM"
  }},
  {{
    "page": "Onboarding_Desktop",
    "element": "Capability cards",
    "problem": "Card shadows inconsistent - first card has 8px shadow, others have 4px",
    "expected": "All cards should have uniform 8px shadow",
    "file": "streamlit_ui/onboarding.py",
    "priority": "LOW"
  }}
]
```

Analyze ALL provided screenshots and find AT LEAST 5 issues if they exist."""

    def _parse_vision_response(self, response_text: str) -> Dict[str, Any]:
        """Parse the vision model response into structured issues."""
        issues = []

        # Try to extract JSON from response
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response_text)
        if json_match:
            try:
                parsed = json.loads(json_match.group(1))
                if isinstance(parsed, list):
                    issues = parsed
            except json.JSONDecodeError:
                pass

        # Valid file paths that actually exist
        VALID_FILES = {
            "streamlit_ui/onboarding.py",
            "streamlit_ui/main_interface.py",
            "streamlit_ui/self_improvement.py",
            "streamlit_ui/constants.py",
            "streamlit_ui/loading_states.py",
            "streamlit_ui/enhanced_interface_input.py",
            "streamlit_ui/enhanced_interface_results.py",
            "streamlit_ui/enhanced_interface_execution.py",
            "streamlit_ui/progress_tracker.py",
            "streamlit_ui/results_display.py",
            "streamlit_ui/live_terminal.py",
            "streamlit_ui/github_export.py",
            "streamlit_ui/agent_collaboration_view.py",
            "streamlit_ui/main_interface_enhanced.py",
            "app.py",
        }

        # Map common invalid paths to valid ones
        FILE_MAPPING = {
            "streamlit_ui/components.py": "streamlit_ui/constants.py",
            "streamlit_ui/layout.py": "streamlit_ui/main_interface.py",
            "streamlit_ui/styles.py": "streamlit_ui/constants.py",
            "streamlit_ui/theme.py": "streamlit_ui/constants.py",
            "streamlit_ui/buttons.py": "streamlit_ui/onboarding.py",
            "streamlit_ui/forms.py": "streamlit_ui/enhanced_interface_input.py",
            "streamlit_ui/navigation.py": "streamlit_ui/main_interface.py",
        }

        # Convert vision issues to standard issue format
        standardized_issues = []
        for issue in issues:
            file_path = issue.get("file", "streamlit_ui/main_interface.py")

            # Validate and fix file path
            if file_path not in VALID_FILES:
                # Try mapping
                if file_path in FILE_MAPPING:
                    file_path = FILE_MAPPING[file_path]
                else:
                    # Default based on page name
                    page = issue.get("page", "").lower()
                    if "onboarding" in page:
                        file_path = "streamlit_ui/onboarding.py"
                    elif "self" in page or "improve" in page:
                        file_path = "streamlit_ui/self_improvement.py"
                    else:
                        file_path = "streamlit_ui/main_interface.py"

            standardized_issues.append({
                "title": f"{issue.get('element', 'UI Element')}: {issue.get('problem', 'Visual issue')[:50]}",
                "description": issue.get("problem", ""),
                "suggestion": issue.get("expected", ""),
                "file": file_path,
                "severity": self._map_priority_to_severity(issue.get("priority", "MEDIUM")),
                "category": "visual",
                "source": "vision_analysis",
                "page": issue.get("page", "Unknown")
            })

        return {
            "issues": standardized_issues,
            "raw_analysis": response_text,
            "issue_count": len(standardized_issues)
        }

    def _map_priority_to_severity(self, priority: str) -> str:
        """Map priority levels to severity."""
        mapping = {
            "HIGH": "high",
            "MEDIUM": "medium",
            "LOW": "low"
        }
        return mapping.get(priority.upper(), "medium")


def analyze_ui_with_vision(
    screenshots: List[Dict],
    code_context: str = "",
    focus_areas: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Convenience function to analyze UI screenshots.

    Args:
        screenshots: List of screenshot dictionaries
        code_context: Optional code for context
        focus_areas: Optional focus areas

    Returns:
        Analysis results dictionary
    """
    analyzer = VisionAnalyzer()
    return analyzer.analyze_screenshots(screenshots, code_context, focus_areas)
