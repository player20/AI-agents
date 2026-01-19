"""
UI/Visual Validation Module

Uses Playwright to validate web application UI:
- Screenshot capture at multiple viewports
- JavaScript error detection
- Resource loading validation
- Basic layout checks
- Accessibility testing (axe-core)
"""

import asyncio
import base64
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import json
import tempfile

try:
    from playwright.async_api import async_playwright, Page, Browser
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


@dataclass
class UIIssue:
    """An issue found during UI validation."""
    severity: str  # error, warning, info
    category: str  # js_error, resource_404, layout, accessibility
    message: str
    details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "severity": self.severity,
            "category": self.category,
            "message": self.message,
            "details": self.details,
        }


@dataclass
class Screenshot:
    """A captured screenshot."""
    viewport: str  # mobile, tablet, desktop
    width: int
    height: int
    base64_data: str
    file_path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "viewport": self.viewport,
            "width": self.width,
            "height": self.height,
            "file_path": self.file_path,
            # Don't include base64 in dict to keep it small
        }


@dataclass
class UIValidationResult:
    """Result of UI validation."""
    status: str  # pass, warn, fail, skip
    message: str
    issues: List[UIIssue] = field(default_factory=list)
    screenshots: List[Screenshot] = field(default_factory=list)
    page_title: Optional[str] = None
    load_time_ms: Optional[int] = None
    accessibility_score: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "message": self.message,
            "issues": [i.to_dict() for i in self.issues],
            "screenshots": [s.to_dict() for s in self.screenshots],
            "page_title": self.page_title,
            "load_time_ms": self.load_time_ms,
            "accessibility_score": self.accessibility_score,
        }


class UIValidator:
    """
    Validates web application UI using Playwright.

    Captures screenshots, detects errors, and runs accessibility checks.
    """

    # Viewport configurations
    VIEWPORTS = {
        "mobile": {"width": 375, "height": 667},
        "tablet": {"width": 768, "height": 1024},
        "desktop": {"width": 1920, "height": 1080},
    }

    # Axe-core script for accessibility testing
    AXE_SCRIPT = """
    (function() {
        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = 'https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.8.3/axe.min.js';
            script.onload = async function() {
                try {
                    const results = await axe.run();
                    resolve(results);
                } catch (e) {
                    reject(e);
                }
            };
            script.onerror = () => reject(new Error('Failed to load axe-core'));
            document.head.appendChild(script);
        });
    })()
    """

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or Path(tempfile.mkdtemp(prefix="ui_validation_"))
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def validate_async(self, url: str, viewports: Optional[List[str]] = None) -> UIValidationResult:
        """
        Validate UI at the given URL asynchronously.

        Args:
            url: URL to validate
            viewports: List of viewports to test (default: all)

        Returns:
            UIValidationResult with findings
        """
        if not PLAYWRIGHT_AVAILABLE:
            return UIValidationResult(
                status="skip",
                message="Playwright not installed. Run: pip install playwright && playwright install"
            )

        viewports = viewports or list(self.VIEWPORTS.keys())
        issues = []
        screenshots = []
        page_title = None
        load_time = None

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)

            try:
                for viewport_name in viewports:
                    viewport = self.VIEWPORTS.get(viewport_name)
                    if not viewport:
                        continue

                    # Create context with viewport
                    context = await browser.new_context(
                        viewport=viewport,
                        device_scale_factor=2 if viewport_name == "mobile" else 1,
                    )
                    page = await context.new_page()

                    # Collect JS errors
                    js_errors = []
                    page.on("pageerror", lambda e: js_errors.append(str(e)))

                    # Collect failed requests
                    failed_requests = []
                    page.on("requestfailed", lambda r: failed_requests.append({
                        "url": r.url,
                        "failure": r.failure,
                    }))

                    try:
                        # Navigate and time it
                        import time
                        start = time.time()
                        response = await page.goto(url, wait_until="networkidle", timeout=30000)
                        load_time = int((time.time() - start) * 1000)

                        # Get page title
                        page_title = await page.title()

                        # Check response status
                        if response and response.status >= 400:
                            issues.append(UIIssue(
                                severity="error",
                                category="http_error",
                                message=f"Page returned HTTP {response.status}",
                            ))

                        # Record JS errors
                        for error in js_errors:
                            issues.append(UIIssue(
                                severity="warning",
                                category="js_error",
                                message=error[:200],
                            ))

                        # Record failed requests
                        for failed in failed_requests:
                            issues.append(UIIssue(
                                severity="warning",
                                category="resource_404",
                                message=f"Failed to load: {failed['url'][:100]}",
                            ))

                        # Check if page is blank
                        is_blank = await self._check_blank_page(page)
                        if is_blank:
                            issues.append(UIIssue(
                                severity="error",
                                category="layout",
                                message=f"Page appears blank at {viewport_name} viewport",
                            ))

                        # Check for layout issues
                        layout_issues = await self._check_layout(page, viewport_name)
                        issues.extend(layout_issues)

                        # Capture screenshot
                        screenshot = await self._capture_screenshot(page, viewport_name)
                        screenshots.append(screenshot)

                        # Run accessibility test on all viewports for comprehensive coverage
                        a11y_issues = await self._run_accessibility_test(page, viewport_name)
                        issues.extend(a11y_issues)

                    except Exception as e:
                        issues.append(UIIssue(
                            severity="error",
                            category="navigation",
                            message=f"Failed to load page at {viewport_name}: {str(e)}",
                        ))

                    await context.close()

            finally:
                await browser.close()

        # Determine status
        error_count = sum(1 for i in issues if i.severity == "error")
        warning_count = sum(1 for i in issues if i.severity == "warning")

        if error_count > 0:
            status = "fail"
            message = f"Found {error_count} error(s) and {warning_count} warning(s)"
        elif warning_count > 0:
            status = "warn"
            message = f"Found {warning_count} warning(s)"
        else:
            status = "pass"
            message = "UI validation passed"

        # Calculate accessibility score based on violations
        a11y_violations = [i for i in issues if i.category == "accessibility" and i.severity in ("error", "warning")]
        a11y_info = [i for i in issues if i.category == "accessibility" and i.severity == "info"]
        if a11y_violations or a11y_info:
            # Score starts at 100, subtract 5 points per violation (min 0)
            accessibility_score = max(0.0, 100.0 - (len(a11y_violations) * 5))
        else:
            accessibility_score = None

        return UIValidationResult(
            status=status,
            message=message,
            issues=issues,
            screenshots=screenshots,
            page_title=page_title,
            load_time_ms=load_time,
            accessibility_score=accessibility_score,
        )

    def validate(self, url: str, viewports: Optional[List[str]] = None) -> UIValidationResult:
        """
        Validate UI at the given URL (sync wrapper).

        Args:
            url: URL to validate
            viewports: List of viewports to test

        Returns:
            UIValidationResult with findings
        """
        return asyncio.run(self.validate_async(url, viewports))

    async def _check_blank_page(self, page: Page) -> bool:
        """Check if the page appears to be blank."""
        try:
            # Check if body has any visible content
            visible_text = await page.evaluate("""
                () => {
                    const body = document.body;
                    if (!body) return '';
                    return body.innerText.trim();
                }
            """)

            # Check if there are any visible elements
            visible_elements = await page.evaluate("""
                () => {
                    const elements = document.querySelectorAll('*');
                    let visibleCount = 0;
                    for (const el of elements) {
                        const style = window.getComputedStyle(el);
                        const rect = el.getBoundingClientRect();
                        if (style.display !== 'none' &&
                            style.visibility !== 'hidden' &&
                            rect.width > 0 && rect.height > 0) {
                            visibleCount++;
                        }
                    }
                    return visibleCount;
                }
            """)

            return len(visible_text) < 10 and visible_elements < 5

        except Exception:
            return False

    async def _check_layout(self, page: Page, viewport: str) -> List[UIIssue]:
        """Check for common layout issues."""
        issues = []

        try:
            # Check for horizontal overflow
            has_overflow = await page.evaluate("""
                () => document.documentElement.scrollWidth > document.documentElement.clientWidth
            """)
            if has_overflow:
                issues.append(UIIssue(
                    severity="warning",
                    category="layout",
                    message=f"Horizontal scroll detected at {viewport} viewport",
                ))

            # Check touch target sizes on mobile
            if viewport == "mobile":
                small_targets = await page.evaluate("""
                    () => {
                        const interactive = document.querySelectorAll('button, a, input, select, textarea, [onclick]');
                        const small = [];
                        for (const el of interactive) {
                            const rect = el.getBoundingClientRect();
                            if (rect.width > 0 && rect.height > 0 &&
                                (rect.width < 44 || rect.height < 44)) {
                                small.push({
                                    tag: el.tagName,
                                    width: rect.width,
                                    height: rect.height,
                                });
                            }
                        }
                        return small.slice(0, 5);  // Limit to 5
                    }
                """)
                if small_targets:
                    issues.append(UIIssue(
                        severity="warning",
                        category="accessibility",
                        message=f"Found {len(small_targets)} touch targets smaller than 44px",
                        details={"elements": small_targets},
                    ))

            # Check for text contrast issues (basic check)
            low_contrast = await page.evaluate("""
                () => {
                    function getLuminance(r, g, b) {
                        const [rs, gs, bs] = [r, g, b].map(c => {
                            c /= 255;
                            return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
                        });
                        return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
                    }

                    function getContrastRatio(l1, l2) {
                        const lighter = Math.max(l1, l2);
                        const darker = Math.min(l1, l2);
                        return (lighter + 0.05) / (darker + 0.05);
                    }

                    function parseColor(color) {
                        const match = color.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);
                        if (match) {
                            return [parseInt(match[1]), parseInt(match[2]), parseInt(match[3])];
                        }
                        return null;
                    }

                    const textElements = document.querySelectorAll('p, span, h1, h2, h3, h4, h5, h6, a, li, td, th');
                    let lowContrastCount = 0;

                    for (const el of Array.from(textElements).slice(0, 100)) {
                        const style = window.getComputedStyle(el);
                        const textColor = parseColor(style.color);
                        const bgColor = parseColor(style.backgroundColor);

                        if (textColor && bgColor) {
                            const textLum = getLuminance(...textColor);
                            const bgLum = getLuminance(...bgColor);
                            const ratio = getContrastRatio(textLum, bgLum);

                            if (ratio < 4.5) {
                                lowContrastCount++;
                            }
                        }
                    }

                    return lowContrastCount;
                }
            """)
            if low_contrast > 3:
                issues.append(UIIssue(
                    severity="warning",
                    category="accessibility",
                    message=f"Found {low_contrast} elements with potentially low contrast",
                ))

        except Exception as e:
            issues.append(UIIssue(
                severity="info",
                category="validation",
                message=f"Could not complete layout checks: {str(e)}",
            ))

        return issues

    async def _capture_screenshot(self, page: Page, viewport_name: str) -> Screenshot:
        """Capture a screenshot of the page."""
        viewport = self.VIEWPORTS[viewport_name]
        file_path = self.output_dir / f"screenshot_{viewport_name}.png"

        await page.screenshot(path=str(file_path), full_page=False)

        # Read as base64
        with open(file_path, "rb") as f:
            base64_data = base64.b64encode(f.read()).decode("utf-8")

        return Screenshot(
            viewport=viewport_name,
            width=viewport["width"],
            height=viewport["height"],
            base64_data=base64_data,
            file_path=str(file_path),
        )

    async def _run_accessibility_test(self, page: Page, viewport: str = "desktop") -> List[UIIssue]:
        """Run axe-core accessibility test with WCAG AA targeting on all viewports."""
        issues = []

        # Enhanced axe-core script with WCAG AA focus
        AXE_SCRIPT_ENHANCED = """
        (function() {
            return new Promise((resolve, reject) => {
                const script = document.createElement('script');
                script.src = 'https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.8.3/axe.min.js';
                script.onload = async function() {
                    try {
                        const results = await axe.run({
                            runOnly: {
                                type: 'tag',
                                values: ['wcag2a', 'wcag2aa', 'wcag21aa', 'best-practice']
                            },
                            resultTypes: ['violations', 'incomplete']
                        });
                        resolve({
                            violations: results.violations,
                            incomplete: results.incomplete,
                            passes: results.passes.length,
                            total: results.passes.length + results.violations.length
                        });
                    } catch (e) {
                        reject(e);
                    }
                };
                script.onerror = () => reject(new Error('Failed to load axe-core'));
                document.head.appendChild(script);
            });
        })()
        """

        try:
            # Inject and run axe-core
            results = await page.evaluate(AXE_SCRIPT_ENHANCED)

            if results and "violations" in results:
                for violation in results["violations"]:
                    severity_map = {
                        "critical": "error",
                        "serious": "error",
                        "moderate": "warning",
                        "minor": "info",
                    }
                    issues.append(UIIssue(
                        severity=severity_map.get(violation.get("impact", "minor"), "info"),
                        category="accessibility",
                        message=f"[{viewport}] {violation.get('help', 'Unknown issue')}",
                        details={
                            "wcag": violation.get("tags", []),
                            "nodes": len(violation.get("nodes", [])),
                            "viewport": viewport,
                            "description": violation.get("description", ""),
                        },
                    ))

        except Exception as e:
            # Axe-core failed to run, not a critical error
            issues.append(UIIssue(
                severity="info",
                category="validation",
                message=f"Could not run accessibility test on {viewport}: {str(e)[:100]}",
            ))

        return issues


# Convenience function
def validate_ui(url: str, viewports: Optional[List[str]] = None) -> UIValidationResult:
    """
    Validate UI at the given URL.

    Args:
        url: URL to validate
        viewports: List of viewports to test

    Returns:
        UIValidationResult with findings
    """
    validator = UIValidator()
    return validator.validate(url, viewports)
