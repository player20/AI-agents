"""
Multi-page screenshot capture with navigation.

Captures all pages of a Streamlit app at multiple viewports.
This enables comprehensive visual analysis of the entire application.

Features:
- Multi-page navigation (onboarding, main interface, self-improve)
- Multiple viewports (desktop, tablet, mobile)
- State-based capture (default, error, loading, empty)
- Interaction state capture (hover, focus on key elements)
- Console error collection
- Performance metrics collection
"""

import sys
import json
from pathlib import Path
from playwright.sync_api import sync_playwright, Page
import time


# Define all pages to capture with navigation instructions
STREAMLIT_PAGES = [
    {
        "name": "Onboarding_Welcome",
        "navigate": None,  # Initial page, no navigation needed
        "wait_for": [".welcome-title", "h1", "Welcome"],
        "description": "First-run welcome screen"
    },
    {
        "name": "Onboarding_Capabilities",
        "navigate": {"type": "button", "text_options": ["Begin Your Journey", "Get Started", "Next"]},
        "wait_for": [".capability-card", ".feature-card", "Capabilities"],
        "description": "Feature showcase"
    },
    {
        "name": "Onboarding_Agents",
        "navigate": {"type": "button", "text_options": ["Next →", "Next", "Continue"]},
        "wait_for": [".agent-flow", ".agent-card", "Agents"],
        "description": "AI agents introduction"
    },
    {
        "name": "Main_Interface",
        "navigate": {"type": "button", "text_options": ["Start Creating", "Let's Go", "Skip", "Get Started"]},
        "wait_for": [".main-title", "textarea", "Describe"],
        "description": "Project creation form"
    },
    {
        "name": "Self_Improve_Mode",
        "navigate": {"type": "sidebar", "text_options": ["Self-Improve", "Self Improve", "Improve"]},
        "wait_for": ["Self-Improve", "Iterative", "Improvement"],
        "description": "Self-improvement interface"
    },
]

VIEWPORTS = {
    'desktop': {'width': 1920, 'height': 1080},
    'tablet': {'width': 768, 'height': 1024},
    'mobile': {'width': 375, 'height': 667}
}

# UI states to capture beyond the default state
UI_STATES = [
    {
        "name": "Default",
        "setup": None,
        "description": "Normal/default state"
    },
    {
        "name": "FormError",
        "setup": "trigger_form_validation",
        "description": "Form validation errors visible"
    },
    {
        "name": "EmptyInput",
        "setup": "clear_inputs",
        "description": "Empty form state"
    },
]

# User flows to execute and capture
USER_FLOWS = [
    {
        "name": "Onboarding_Complete",
        "steps": [
            {"action": "wait", "selector": ".welcome-title", "timeout": 3000},
            {"action": "screenshot", "name": "flow_welcome"},
            {"action": "click", "text_options": ["Begin Your Journey", "Get Started", "Next"]},
            {"action": "wait_time", "ms": 1000},
            {"action": "screenshot", "name": "flow_capabilities"},
            {"action": "click", "text_options": ["Next →", "Next", "Continue"]},
            {"action": "wait_time", "ms": 1000},
            {"action": "screenshot", "name": "flow_agents"},
            {"action": "click", "text_options": ["Start Creating", "Let's Go", "Skip"]},
            {"action": "wait_time", "ms": 1000},
            {"action": "screenshot", "name": "flow_main_interface"},
        ]
    },
]


def trigger_form_validation(page: Page) -> bool:
    """Trigger form validation to show error states."""
    try:
        # Try to submit an empty form or click submit without filling required fields
        submit_selectors = [
            'button[type="submit"]',
            '.stButton button:has-text("Start")',
            'button:has-text("Generate")',
            'button:has-text("Create")',
        ]
        for selector in submit_selectors:
            try:
                if page.locator(selector).count() > 0:
                    page.click(selector, timeout=2000)
                    time.sleep(0.5)
                    return True
            except:
                continue
        return False
    except:
        return False


def clear_inputs(page: Page) -> bool:
    """Clear all input fields to show empty state."""
    try:
        # Clear textareas
        textareas = page.locator('textarea')
        count = textareas.count()
        for i in range(count):
            try:
                textareas.nth(i).fill('')
            except:
                pass

        # Clear text inputs
        inputs = page.locator('input[type="text"]')
        count = inputs.count()
        for i in range(count):
            try:
                inputs.nth(i).fill('')
            except:
                pass

        return True
    except:
        return False


def capture_interaction_states(page: Page, output_dir: Path, timestamp: int, viewport_name: str) -> list:
    """Capture hover and focus states on interactive elements."""
    interaction_screenshots = []

    try:
        # Find primary buttons
        buttons = page.locator('.stButton button, button[data-testid="stBaseButton-primary"]')
        button_count = min(buttons.count(), 2)  # Limit to 2 buttons

        for i in range(button_count):
            try:
                button = buttons.nth(i)
                if not button.is_visible():
                    continue

                # Capture hover state
                button.hover()
                time.sleep(0.3)
                hover_path = output_dir / f"button_{i}_hover_{viewport_name}_{timestamp}.png"
                button.screenshot(path=str(hover_path))
                interaction_screenshots.append({
                    "name": f"Button_{i}_Hover_{viewport_name}",
                    "path": str(hover_path),
                    "viewport": VIEWPORTS[viewport_name],
                    "state": "hover",
                    "element": "button"
                })

                # Capture focus state
                button.focus()
                time.sleep(0.2)
                focus_path = output_dir / f"button_{i}_focus_{viewport_name}_{timestamp}.png"
                button.screenshot(path=str(focus_path))
                interaction_screenshots.append({
                    "name": f"Button_{i}_Focus_{viewport_name}",
                    "path": str(focus_path),
                    "viewport": VIEWPORTS[viewport_name],
                    "state": "focus",
                    "element": "button"
                })

            except Exception as e:
                print(f"Error capturing button {i} interaction: {e}", file=sys.stderr)

        # Find text inputs/textareas for focus states
        inputs = page.locator('textarea, input[type="text"]')
        input_count = min(inputs.count(), 1)  # Just capture 1 input focus

        for i in range(input_count):
            try:
                input_el = inputs.nth(i)
                if not input_el.is_visible():
                    continue

                # Capture focus state
                input_el.focus()
                time.sleep(0.2)
                focus_path = output_dir / f"input_{i}_focus_{viewport_name}_{timestamp}.png"
                input_el.screenshot(path=str(focus_path))
                interaction_screenshots.append({
                    "name": f"Input_{i}_Focus_{viewport_name}",
                    "path": str(focus_path),
                    "viewport": VIEWPORTS[viewport_name],
                    "state": "focus",
                    "element": "input"
                })

            except Exception as e:
                print(f"Error capturing input {i} interaction: {e}", file=sys.stderr)

    except Exception as e:
        print(f"Error in capture_interaction_states: {e}", file=sys.stderr)

    return interaction_screenshots


def execute_user_flow(page: Page, flow: dict, output_dir: Path, timestamp: int) -> list:
    """Execute a user flow and capture screenshots at each step."""
    screenshots = []

    for step in flow["steps"]:
        try:
            if step["action"] == "click":
                for text in step.get("text_options", []):
                    try:
                        selectors = [
                            f'button:has-text("{text}")',
                            f'[role="button"]:has-text("{text}")',
                            f'.stButton button:has-text("{text}")',
                        ]
                        for selector in selectors:
                            if page.locator(selector).count() > 0:
                                page.click(selector, timeout=3000)
                                break
                        break
                    except:
                        continue

            elif step["action"] == "wait":
                try:
                    page.wait_for_selector(step["selector"], timeout=step.get("timeout", 5000))
                except:
                    pass

            elif step["action"] == "wait_time":
                time.sleep(step.get("ms", 1000) / 1000)

            elif step["action"] == "screenshot":
                path = output_dir / f"{step['name']}_{timestamp}.png"
                page.screenshot(path=str(path), full_page=True)
                screenshots.append({
                    "name": step["name"],
                    "path": str(path),
                    "viewport": {"width": 1920, "height": 1080},
                    "flow": flow["name"],
                    "description": f"User flow: {flow['name']}"
                })

            elif step["action"] == "fill":
                page.fill(step["selector"], step["value"])

        except Exception as e:
            print(f"Flow step error: {step} - {e}", file=sys.stderr)

    return screenshots


def try_click(page, nav_config, timeout=5000):
    """Try to click a navigation element with multiple text options."""
    if nav_config["type"] == "button":
        for text in nav_config["text_options"]:
            try:
                # Try multiple selector patterns
                selectors = [
                    f'button:has-text("{text}")',
                    f'[role="button"]:has-text("{text}")',
                    f'.stButton button:has-text("{text}")',
                    f'text="{text}"',
                ]
                for selector in selectors:
                    try:
                        if page.locator(selector).count() > 0:
                            page.click(selector, timeout=timeout)
                            return True
                    except:
                        continue
            except:
                continue
    elif nav_config["type"] == "sidebar":
        for text in nav_config["text_options"]:
            try:
                selectors = [
                    f'[data-testid="stSidebar"] >> text="{text}"',
                    f'.sidebar >> text="{text}"',
                    f'nav >> text="{text}"',
                    f'text="{text}"',
                ]
                for selector in selectors:
                    try:
                        if page.locator(selector).count() > 0:
                            page.click(selector, timeout=timeout)
                            return True
                    except:
                        continue
            except:
                continue
    return False


def wait_for_content(page, wait_for_options, timeout=5000):
    """Wait for any of the specified content to appear."""
    for selector in wait_for_options:
        try:
            # Try as CSS selector first
            page.wait_for_selector(selector, timeout=timeout)
            return True
        except:
            pass
        try:
            # Try as text content
            page.wait_for_selector(f'text="{selector}"', timeout=timeout)
            return True
        except:
            pass
    return False


def capture_all_pages(
    server_url: str,
    output_dir: str,
    capture_mode: str = "thorough",
    include_interactions: bool = True,
    include_states: bool = True,
    include_user_flows: bool = False
) -> dict:
    """
    Capture comprehensive screenshots of all pages at all viewports.

    Args:
        server_url: URL of the running app (any website, not just Streamlit)
        output_dir: Directory to save screenshots
        capture_mode: "quick" (homepage only), "standard" (3 pages), "thorough" (all pages)
        include_interactions: Capture hover/focus states on interactive elements
        include_states: Capture error/empty states
        include_user_flows: Execute and capture user flow journeys

    Returns:
        Dict with screenshots, console_errors, and performance_metrics
    """
    screenshots = []
    all_console_errors = []
    performance_metrics = {}
    screenshots_dir = Path(output_dir)
    screenshots_dir.mkdir(exist_ok=True)
    timestamp = int(time.time())

    # Determine which pages to capture based on mode
    if capture_mode == "quick":
        pages_to_capture = STREAMLIT_PAGES[:1]  # Just homepage
        include_interactions = False
        include_states = False
        include_user_flows = False
    elif capture_mode == "standard":
        pages_to_capture = STREAMLIT_PAGES[:3]  # First 3 pages
        include_user_flows = False
    else:
        pages_to_capture = STREAMLIT_PAGES  # All pages

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        for viewport_name, viewport_size in VIEWPORTS.items():
            # Create new context for each viewport
            context = browser.new_context(
                viewport=viewport_size,
                device_scale_factor=2 if viewport_name == "mobile" else 1
            )
            page = context.new_page()

            # Collect console errors
            viewport_errors = []
            page.on("console", lambda msg: viewport_errors.append(msg.text) if msg.type == "error" else None)

            # Collect failed requests
            failed_requests = []
            page.on("requestfailed", lambda req: failed_requests.append(req.url))

            try:
                # Start at homepage with timing
                start_time = time.time()
                page.goto(server_url, wait_until="networkidle", timeout=30000)
                load_time = int((time.time() - start_time) * 1000)

                # Store performance metrics for first viewport
                if viewport_name == "desktop":
                    performance_metrics["load_time_ms"] = load_time
                    performance_metrics["failed_requests"] = len(failed_requests)

                    # Try to collect Core Web Vitals
                    try:
                        cwv = page.evaluate("""
                            () => {
                                const metrics = {};
                                const entries = performance.getEntriesByType('paint');
                                for (const entry of entries) {
                                    if (entry.name === 'first-contentful-paint') {
                                        metrics.fcp = Math.round(entry.startTime);
                                    }
                                }
                                // Get LCP if available
                                const lcpEntries = performance.getEntriesByType('largest-contentful-paint');
                                if (lcpEntries.length > 0) {
                                    metrics.lcp = Math.round(lcpEntries[lcpEntries.length - 1].startTime);
                                }
                                return metrics;
                            }
                        """)
                        performance_metrics.update(cwv)
                    except:
                        pass

                time.sleep(2)  # Allow animations to settle

                # ===== CAPTURE PAGES =====
                for page_def in pages_to_capture:
                    try:
                        # Navigate if needed
                        if page_def["navigate"]:
                            clicked = try_click(page, page_def["navigate"])
                            if clicked:
                                time.sleep(1.5)
                            else:
                                print(f"WARNING: Could not navigate to {page_def['name']}", file=sys.stderr)
                                continue

                        # Wait for page-specific content
                        if page_def.get("wait_for"):
                            wait_for_content(page, page_def["wait_for"], timeout=5000)

                        time.sleep(0.5)

                        # Capture DEFAULT state
                        filename = f"{page_def['name']}_{viewport_name}_{timestamp}.png"
                        filepath = screenshots_dir / filename
                        page.screenshot(path=str(filepath), full_page=True)

                        screenshots.append({
                            "name": f"{page_def['name']}_{viewport_name}",
                            "path": str(filepath),
                            "viewport": viewport_size,
                            "page": page_def["name"],
                            "state": "default",
                            "description": page_def.get("description", ""),
                            "console_errors": viewport_errors.copy()
                        })

                        print(f"Captured: {page_def['name']} at {viewport_name}", file=sys.stderr)

                        # ===== CAPTURE UI STATES (error, empty) =====
                        if include_states and page_def["name"] == "Main_Interface":
                            for ui_state in UI_STATES[1:]:  # Skip "Default" state
                                try:
                                    if ui_state["setup"] == "trigger_form_validation":
                                        trigger_form_validation(page)
                                    elif ui_state["setup"] == "clear_inputs":
                                        clear_inputs(page)

                                    time.sleep(0.3)

                                    state_filename = f"{page_def['name']}_{ui_state['name']}_{viewport_name}_{timestamp}.png"
                                    state_filepath = screenshots_dir / state_filename
                                    page.screenshot(path=str(state_filepath), full_page=True)

                                    screenshots.append({
                                        "name": f"{page_def['name']}_{ui_state['name']}_{viewport_name}",
                                        "path": str(state_filepath),
                                        "viewport": viewport_size,
                                        "page": page_def["name"],
                                        "state": ui_state["name"].lower(),
                                        "description": ui_state["description"],
                                        "console_errors": viewport_errors.copy()
                                    })

                                    print(f"  Captured state: {ui_state['name']}", file=sys.stderr)

                                    # Reload page to reset state
                                    page.reload(wait_until="networkidle", timeout=15000)
                                    time.sleep(1)

                                except Exception as e:
                                    print(f"  State capture error ({ui_state['name']}): {e}", file=sys.stderr)

                    except Exception as e:
                        print(f"ERROR capturing {page_def['name']} at {viewport_name}: {e}", file=sys.stderr)

                # ===== CAPTURE INTERACTION STATES =====
                if include_interactions and viewport_name == "desktop":
                    # Navigate to main interface for interaction capture
                    page.goto(server_url, wait_until="networkidle", timeout=30000)
                    time.sleep(2)

                    # Try to get to main interface
                    for nav_step in ["Begin Your Journey", "Next →", "Start Creating"]:
                        try:
                            page.click(f'button:has-text("{nav_step}")', timeout=2000)
                            time.sleep(0.5)
                        except:
                            break

                    interaction_shots = capture_interaction_states(page, screenshots_dir, timestamp, viewport_name)
                    screenshots.extend(interaction_shots)
                    print(f"Captured {len(interaction_shots)} interaction states", file=sys.stderr)

                # Aggregate console errors
                all_console_errors.extend(viewport_errors)

            except Exception as e:
                print(f"ERROR with viewport {viewport_name}: {e}", file=sys.stderr)
            finally:
                context.close()

        # ===== EXECUTE USER FLOWS =====
        if include_user_flows:
            context = browser.new_context(viewport=VIEWPORTS["desktop"])
            page = context.new_page()

            for flow in USER_FLOWS:
                try:
                    page.goto(server_url, wait_until="networkidle", timeout=30000)
                    time.sleep(2)

                    flow_shots = execute_user_flow(page, flow, screenshots_dir, timestamp)
                    screenshots.extend(flow_shots)
                    print(f"Captured user flow: {flow['name']} ({len(flow_shots)} screenshots)", file=sys.stderr)

                except Exception as e:
                    print(f"User flow error ({flow['name']}): {e}", file=sys.stderr)

            context.close()

        browser.close()

    # Deduplicate console errors
    unique_errors = list(set(all_console_errors))

    return {
        "screenshots": screenshots,
        "console_errors": unique_errors,
        "performance_metrics": performance_metrics,
        "failed_requests": failed_requests if 'failed_requests' in dir() else [],
        "total_screenshots": len(screenshots),
        "timestamp": timestamp
    }


def capture_screenshots(server_url: str, output_dir: str) -> list:
    """
    Legacy function for backward compatibility.
    Captures homepage at 3 viewports.
    Returns just the screenshots list for backward compatibility.
    """
    result = capture_all_pages(server_url, output_dir, capture_mode="quick")
    return result.get("screenshots", [])


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python capture_screenshots.py <server_url> <output_dir> [mode] [flags]")
        print("  mode: quick (homepage only), standard (3 pages), thorough (all pages), comprehensive (all features)")
        print("  flags: --no-interactions, --no-states, --with-flows")
        sys.exit(1)

    server_url = sys.argv[1]
    output_dir = sys.argv[2]
    mode = sys.argv[3] if len(sys.argv) > 3 else "thorough"

    # Parse flags
    include_interactions = "--no-interactions" not in sys.argv
    include_states = "--no-states" not in sys.argv
    include_user_flows = "--with-flows" in sys.argv or mode == "comprehensive"

    # Comprehensive mode enables everything
    if mode == "comprehensive":
        include_interactions = True
        include_states = True
        include_user_flows = True
        mode = "thorough"

    try:
        result = capture_all_pages(
            server_url,
            output_dir,
            capture_mode=mode,
            include_interactions=include_interactions,
            include_states=include_states,
            include_user_flows=include_user_flows
        )

        # Output JSON to stdout for parsing
        # Include full result with metrics for comprehensive analysis
        print(json.dumps(result))

        # Print summary to stderr
        print(f"\n=== Capture Summary ===", file=sys.stderr)
        print(f"Total Screenshots: {result['total_screenshots']}", file=sys.stderr)
        print(f"Console Errors: {len(result['console_errors'])}", file=sys.stderr)
        print(f"Load Time: {result['performance_metrics'].get('load_time_ms', 'N/A')}ms", file=sys.stderr)

        sys.exit(0)
    except Exception as e:
        print(f"FATAL ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
