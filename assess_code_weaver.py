"""
Comprehensive Visual Assessment Script for Code Weaver Pro

This script performs an extensive visual assessment of Code Weaver Pro,
navigating through ALL modes and capturing detailed screenshots for AI analysis.

Features:
- Navigates all 3 modes (Create App, Self-Improve, Report Review)
- Expands all collapsible sections
- Captures mobile + desktop screenshots of each state
- Provides detailed, actionable feedback for improvement

Usage:
    python assess_code_weaver.py
"""

import asyncio
import subprocess
import time
import sys
import os
from pathlib import Path

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Load environment variables FIRST before any imports that need them
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Check for Anthropic API key
if not os.getenv('ANTHROPIC_API_KEY'):
    print("ERROR: ANTHROPIC_API_KEY not set. Please set it in .env or environment.")
    sys.exit(1)

from playwright.async_api import async_playwright
import base64


async def capture_screenshot_base64(page, name: str, viewport: dict) -> dict:
    """Capture a screenshot and return as base64 with metadata"""
    await page.set_viewport_size(viewport)
    await asyncio.sleep(0.5)  # Let layout settle

    screenshot_bytes = await page.screenshot(full_page=True)
    base64_data = base64.b64encode(screenshot_bytes).decode('utf-8')

    return {
        "name": name,
        "url": page.url,
        "viewport": viewport,
        "base64": base64_data,
        "mime_type": "image/png"
    }


async def expand_all_expanders(page):
    """Click all collapsed expanders to reveal hidden content"""
    try:
        # Streamlit expanders have this pattern
        expanders = await page.query_selector_all('[data-testid="stExpander"] summary')
        for expander in expanders:
            try:
                # Check if it's collapsed
                is_expanded = await expander.get_attribute('aria-expanded')
                if is_expanded != 'true':
                    await expander.click()
                    await asyncio.sleep(0.3)
            except:
                pass
    except Exception as e:
        print(f"    Note: Could not expand all sections: {e}")


async def wait_for_streamlit_load(page, timeout=15000):
    """Wait for Streamlit app to fully load"""
    try:
        # Wait for main content
        await page.wait_for_selector('[data-testid="stAppViewContainer"]', timeout=timeout)
        await asyncio.sleep(3)  # Additional time for JS rendering

        # Wait for any spinners to disappear
        try:
            await page.wait_for_selector('[data-testid="stSpinner"]', state='hidden', timeout=5000)
        except:
            pass

        # Wait for buttons to be visible (indicates UI is ready)
        try:
            await page.wait_for_selector('button', timeout=5000)
        except:
            pass

    except Exception as e:
        print(f"    Warning: Streamlit load wait issue: {e}")


async def click_streamlit_button(page, button_text: str) -> bool:
    """Click a Streamlit button by its text content"""
    try:
        # Streamlit buttons are rendered with specific structure
        # Try multiple selector strategies
        selectors = [
            f'button:has-text("{button_text}")',
            f'[data-testid="stBaseButton-secondary"]:has-text("{button_text}")',
            f'[data-testid="stBaseButton-primary"]:has-text("{button_text}")',
            f'.stButton button:has-text("{button_text}")',
        ]

        for selector in selectors:
            try:
                button = await page.wait_for_selector(selector, timeout=3000)
                if button:
                    await button.click()
                    await asyncio.sleep(2)  # Wait for state change
                    return True
            except:
                continue

        # Fallback: find all buttons and click matching one
        buttons = await page.query_selector_all('button')
        for btn in buttons:
            text = await btn.inner_text()
            if button_text.lower() in text.lower():
                await btn.click()
                await asyncio.sleep(2)
                return True

        return False
    except Exception as e:
        print(f"    Warning: Could not click button '{button_text}': {e}")
        return False


async def complete_onboarding(page) -> bool:
    """Complete or skip the onboarding flow to access the main interface"""
    try:
        # Check if we're on the onboarding screen by looking for "Begin Your Journey" or "Skip intro"
        buttons = await page.query_selector_all('button')
        button_texts = []
        for btn in buttons:
            try:
                text = await btn.inner_text()
                button_texts.append(text.strip())
            except:
                pass

        print(f"    Checking for onboarding... Found buttons: {button_texts[:6]}")

        # Method 1: Try to skip intro directly
        if await click_streamlit_button(page, "Skip intro"):
            print("    ✓ Skipped onboarding via 'Skip intro'")
            await asyncio.sleep(2)
            return True

        # Method 2: Go through onboarding steps
        # Step 0: Welcome screen - "Begin Your Journey"
        if await click_streamlit_button(page, "Begin Your Journey"):
            print("    ✓ Clicked 'Begin Your Journey'")
            await asyncio.sleep(1)

            # Step 1: Capabilities - "Next →"
            if await click_streamlit_button(page, "Next"):
                print("    ✓ Clicked 'Next' (step 1)")
                await asyncio.sleep(1)

                # Step 2: Agents - "Next →"
                if await click_streamlit_button(page, "Next"):
                    print("    ✓ Clicked 'Next' (step 2)")
                    await asyncio.sleep(1)

                    # Step 3: Ready - "Start Creating"
                    if await click_streamlit_button(page, "Start Creating"):
                        print("    ✓ Clicked 'Start Creating' - Onboarding complete!")
                        await asyncio.sleep(2)
                        return True

        # Check if we're already on the main interface (no onboarding needed)
        # Look for mode buttons: "Create App", "Self-Improve", "Report Review"
        for mode_text in ["Create App", "Self-Improve", "Report Review"]:
            try:
                btn = await page.wait_for_selector(f'button:has-text("{mode_text}")', timeout=2000)
                if btn:
                    print("    ✓ Already on main interface (no onboarding needed)")
                    return True
            except:
                continue

        print("    ⚠ Could not complete onboarding, but continuing anyway...")
        return False

    except Exception as e:
        print(f"    Warning: Onboarding handling issue: {e}")
        return False


async def run_comprehensive_assessment():
    """Run extensive visual assessment on Code Weaver Pro"""

    print("\n" + "="*70)
    print("  COMPREHENSIVE Visual Assessment of Code Weaver Pro")
    print("="*70 + "\n")

    # Start Streamlit app in background
    print("[1/7] Starting Code Weaver Pro Streamlit app...")

    streamlit_process = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "app.py",
         "--server.port", "8501",
         "--server.headless", "true",
         "--browser.gatherUsageStats", "false"],
        cwd=str(Path(__file__).parent),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    print("    Waiting for server to start (15 seconds)...")
    time.sleep(15)  # Give Streamlit more time to fully initialize

    app_url = "http://localhost:8501"
    all_screenshots = []

    viewports = {
        'mobile': {'width': 375, 'height': 812},
        'desktop': {'width': 1920, 'height': 1080}
    }

    try:
        async with async_playwright() as p:
            print(f"\n[2/7] Launching browser and connecting to {app_url}...")
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()

            # ===== HANDLE ONBOARDING FIRST =====
            print("\n[3/8] Checking and completing onboarding flow...")

            await page.goto(app_url, wait_until="networkidle", timeout=60000)
            await wait_for_streamlit_load(page)

            # Complete or skip onboarding to access main interface
            await complete_onboarding(page)
            await wait_for_streamlit_load(page)

            # Debug: Print all visible buttons after onboarding
            buttons = await page.query_selector_all('button')
            print(f"    Found {len(buttons)} buttons on main interface")
            for i, btn in enumerate(buttons[:8]):
                try:
                    text = await btn.inner_text()
                    print(f"      Button {i}: '{text[:40]}...' " if len(text) > 40 else f"      Button {i}: '{text}'")
                except:
                    pass

            # ===== MODE 1: CREATE APP =====
            print("\n[4/8] Capturing CREATE APP mode...")

            # Click "Create App" button to ensure we're in that mode
            if await click_streamlit_button(page, "Create App"):
                print("    ✓ Clicked Create App button")
                await wait_for_streamlit_load(page)
            else:
                print("    ⚠ Could not find Create App button, continuing with current view")

            # Capture initial state
            for vp_name, vp_size in viewports.items():
                screenshot = await capture_screenshot_base64(
                    page, f"create_app_initial_{vp_name}", vp_size
                )
                all_screenshots.append(screenshot)
                print(f"    📸 Create App - Initial ({vp_name})")

            # Expand all sections
            await expand_all_expanders(page)
            await asyncio.sleep(1)

            # Capture with expanded sections
            for vp_name, vp_size in viewports.items():
                screenshot = await capture_screenshot_base64(
                    page, f"create_app_expanded_{vp_name}", vp_size
                )
                all_screenshots.append(screenshot)
                print(f"    📸 Create App - All Sections Expanded ({vp_name})")

            # Fill in the text area with sample input to show active state
            try:
                # Streamlit text areas have data-testid
                text_area = await page.query_selector('[data-testid="stTextArea"] textarea')
                if not text_area:
                    text_area = await page.query_selector('textarea')

                if text_area:
                    await text_area.fill("A coffee shop loyalty app where customers earn points and redeem rewards. We're seeing 40% drop-off at checkout.")
                    await asyncio.sleep(1)

                    for vp_name, vp_size in viewports.items():
                        screenshot = await capture_screenshot_base64(
                            page, f"create_app_with_input_{vp_name}", vp_size
                        )
                        all_screenshots.append(screenshot)
                        print(f"    📸 Create App - With Input ({vp_name})")
                else:
                    print("    ⚠ No text area found")
            except Exception as e:
                print(f"    ⚠ Could not fill text area: {e}")

            # ===== MODE 2: SELF-IMPROVE =====
            print("\n[5/8] Capturing SELF-IMPROVE mode...")

            if await click_streamlit_button(page, "Self-Improve"):
                print("    ✓ Clicked Self-Improve button")
                await wait_for_streamlit_load(page)

                for vp_name, vp_size in viewports.items():
                    screenshot = await capture_screenshot_base64(
                        page, f"self_improve_{vp_name}", vp_size
                    )
                    all_screenshots.append(screenshot)
                    print(f"    📸 Self-Improve Mode ({vp_name})")

                # Expand sections
                await expand_all_expanders(page)
                await asyncio.sleep(1)

                for vp_name, vp_size in viewports.items():
                    screenshot = await capture_screenshot_base64(
                        page, f"self_improve_expanded_{vp_name}", vp_size
                    )
                    all_screenshots.append(screenshot)
                    print(f"    📸 Self-Improve - Expanded ({vp_name})")
            else:
                print("    ⚠ Could not navigate to Self-Improve mode")

            # ===== MODE 3: REPORT REVIEW =====
            print("\n[6/8] Capturing REPORT REVIEW mode...")

            if await click_streamlit_button(page, "Report Review"):
                print("    ✓ Clicked Report Review button")
                await wait_for_streamlit_load(page)

                for vp_name, vp_size in viewports.items():
                    screenshot = await capture_screenshot_base64(
                        page, f"report_review_{vp_name}", vp_size
                    )
                    all_screenshots.append(screenshot)
                    print(f"    📸 Report Review Mode ({vp_name})")

                # Expand sections
                await expand_all_expanders(page)
                await asyncio.sleep(1)

                for vp_name, vp_size in viewports.items():
                    screenshot = await capture_screenshot_base64(
                        page, f"report_review_expanded_{vp_name}", vp_size
                    )
                    all_screenshots.append(screenshot)
                    print(f"    📸 Report Review - Expanded ({vp_name})")

                # Try to capture sidebar if visible
                try:
                    sidebar = await page.query_selector('[data-testid="stSidebar"]')
                    if sidebar:
                        print("    Found sidebar, capturing...")
                        # Open sidebar on mobile
                        sidebar_toggle = await page.query_selector('[data-testid="collapsedControl"]')
                        if sidebar_toggle:
                            await sidebar_toggle.click()
                            await asyncio.sleep(1)

                        for vp_name, vp_size in viewports.items():
                            screenshot = await capture_screenshot_base64(
                                page, f"report_review_sidebar_{vp_name}", vp_size
                            )
                            all_screenshots.append(screenshot)
                            print(f"    📸 Report Review - Sidebar ({vp_name})")
                except Exception as e:
                    print(f"    ⚠ Sidebar capture issue: {e}")
            else:
                print("    ⚠ Could not navigate to Report Review mode")

            # ===== BACK TO CREATE APP FOR SCROLL STATE =====
            print("\n[7/8] Capturing scroll states and edge cases...")

            if await click_streamlit_button(page, "Create App"):
                await wait_for_streamlit_load(page)

            # Scroll to bottom
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(0.5)

            for vp_name, vp_size in viewports.items():
                screenshot = await capture_screenshot_base64(
                    page, f"create_app_scrolled_bottom_{vp_name}", vp_size
                )
                all_screenshots.append(screenshot)
                print(f"    📸 Create App - Scrolled to Bottom ({vp_name})")

            await browser.close()

        print(f"\n    ✅ Total screenshots captured: {len(all_screenshots)}")

        # ===== RUN AI VISUAL ASSESSMENT =====
        print("\n[8/8] Running AI Visual Assessment with Claude Vision...")

        import anthropic
        client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

        # Comprehensive assessment prompt
        assessment_prompt = """You are a Senior UX/UI Expert and Product Designer conducting a comprehensive visual audit of "Code Weaver Pro" - an AI-powered application generator built with Streamlit.

You are reviewing {num_screenshots} screenshots covering:
- CREATE APP mode (main interface for generating apps)
- SELF-IMPROVE mode (code analysis and optimization)
- REPORT REVIEW mode (business audit reports)
- Mobile (375px) and Desktop (1920px) viewports
- Collapsed and expanded states of all sections

## YOUR TASK

Provide an EXTENSIVE, DETAILED assessment that development teams can use to improve the platform. Be specific about:
- Exact UI elements that need work
- Specific color values, spacing issues, font sizes
- Concrete recommendations with implementation details

## REQUIRED OUTPUT FORMAT

### 1. EXECUTIVE SUMMARY
- Overall Visual Score: X/10
- One-paragraph summary of the platform's visual state
- Top 3 critical issues that must be fixed immediately

### 2. MODE-BY-MODE ANALYSIS

#### CREATE APP Mode
- **First Impression (0-10)**: What does a new user see?
- **Visual Hierarchy**: Is the input area prominent enough?
- **Form Design**: Are the expandable sections discoverable?
- **Call-to-Action**: Is the main action button effective?
- **Specific Issues**: List 5+ specific problems with solutions
- **Mobile Experience**: How well does it adapt?

#### SELF-IMPROVE Mode
- **Layout Clarity**: Is the purpose clear?
- **Information Architecture**: Is content well-organized?
- **Specific Issues**: List 3+ specific problems with solutions

#### REPORT REVIEW Mode
- **Sidebar Usability**: Is navigation intuitive?
- **Content Density**: Is there too much/too little?
- **Specific Issues**: List 3+ specific problems with solutions

### 3. CROSS-CUTTING CONCERNS

#### Navigation & Mode Switching
- Are the mode buttons clear and accessible?
- Is the current mode obvious?
- Transition experience between modes?

#### Color & Contrast
- Background colors and readability
- Button contrast ratios
- Text legibility in all sections
- Dark theme consistency

#### Typography
- Font sizes (too small? too large?)
- Font weights and hierarchy
- Line heights and readability
- Responsive scaling

#### Spacing & Layout
- Padding and margins consistency
- White space usage
- Content width on different screens
- Scroll behavior

#### Accessibility
- Color contrast issues (WCAG AA compliance)
- Focus indicators visible?
- Touch targets adequate on mobile?
- Screen reader considerations

#### Responsiveness
- Mobile vs Desktop layouts
- Breakpoint transitions
- Content reflow issues
- Touch-friendly interactions

### 4. COMPETITIVE COMPARISON
How does this compare to:
- Other Streamlit apps
- Modern SaaS dashboards (Notion, Linear, Vercel)
- What's missing to be "world-class"?

### 5. PRIORITIZED RECOMMENDATIONS

#### Critical (Fix Immediately)
1. [Issue]: [Detailed solution]
2. [Issue]: [Detailed solution]
3. [Issue]: [Detailed solution]

#### High Priority (This Sprint)
1. [Issue]: [Detailed solution]
2. [Issue]: [Detailed solution]
3. [Issue]: [Detailed solution]

#### Medium Priority (Next Sprint)
1. [Issue]: [Detailed solution]
2. [Issue]: [Detailed solution]
3. [Issue]: [Detailed solution]

#### Nice to Have (Backlog)
1. [Enhancement idea]
2. [Enhancement idea]

### 6. IMPLEMENTATION CHECKLIST
Provide specific CSS/Streamlit changes for the top 10 issues:
```
Issue #1: [Description]
Location: [File/Component]
Current: [What it looks like now]
Fix: [Specific code or CSS change]
```

### 7. FINAL SCORES

| Category | Score | Notes |
|----------|-------|-------|
| Visual Design | X/10 | [Brief note] |
| Mobile Responsiveness | X/10 | [Brief note] |
| UI Consistency | X/10 | [Brief note] |
| Accessibility | X/10 | [Brief note] |
| User Flow Clarity | X/10 | [Brief note] |
| Professional Polish | X/10 | [Brief note] |
| **OVERALL** | **X/10** | [Summary] |

Be brutally honest. This assessment will drive real improvements.""".format(
            num_screenshots=len(all_screenshots)
        )

        # Process in batches
        print(f"    Processing {len(all_screenshots)} screenshots...")

        batch_size = 5
        all_results = []

        for batch_start in range(0, len(all_screenshots), batch_size):
            batch_images = all_screenshots[batch_start:batch_start + batch_size]
            batch_num = (batch_start // batch_size) + 1
            total_batches = (len(all_screenshots) + batch_size - 1) // batch_size

            print(f"    Analyzing batch {batch_num}/{total_batches} ({len(batch_images)} images)...")

            # Build content
            if batch_num == 1:
                content = [{"type": "text", "text": assessment_prompt}]
            else:
                content = [{"type": "text", "text": "Continue analyzing these additional screenshots, maintaining the same detailed analysis:"}]

            for img in batch_images:
                content.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": img["mime_type"],
                        "data": img["base64"]
                    }
                })
                content.append({
                    "type": "text",
                    "text": f"[Screenshot: {img['name']} - Viewport: {img['viewport']['width']}x{img['viewport']['height']}]"
                })

            try:
                response = client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=8192,
                    messages=[{"role": "user", "content": content}]
                )
                all_results.append(response.content[0].text)
            except Exception as e:
                print(f"    WARNING: Batch {batch_num} failed: {e}")
                all_results.append(f"[Batch {batch_num} analysis failed: {str(e)}]")

        # Combine results
        if len(all_results) > 1:
            print("    Synthesizing final comprehensive report...")

            combined = "\n\n---\n\n".join(all_results)

            try:
                synthesis_response = client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=8192,
                    messages=[{
                        "role": "user",
                        "content": f"""Synthesize these multiple visual analysis reports into ONE comprehensive, well-organized report.

IMPORTANT:
- Combine all insights, don't lose any details
- Organize by the exact structure requested (Executive Summary, Mode-by-Mode, etc.)
- Include ALL specific issues mentioned across all batches
- Provide the Implementation Checklist with specific fixes
- End with the scoring table

Previous analysis batches:

{combined}

Create the final unified report now:"""
                    }]
                )
                final_report = synthesis_response.content[0].text
            except Exception as e:
                print(f"    Warning: Synthesis failed, using combined results: {e}")
                final_report = combined
        else:
            final_report = all_results[0] if all_results else "No assessment generated"

        # Output results
        print("\n" + "="*70)
        print("  COMPREHENSIVE VISUAL ASSESSMENT RESULTS")
        print("="*70 + "\n")
        print(final_report)

        # Save to file
        output_file = Path(__file__).parent / "code_weaver_visual_assessment.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# Code Weaver Pro - Comprehensive Visual Assessment Report\n\n")
            f.write(f"**Generated**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**Screenshots Analyzed**: {len(all_screenshots)}\n\n")
            f.write("**Modes Covered**: Create App, Self-Improve, Report Review\n\n")
            f.write("**Viewports**: Mobile (375px), Desktop (1920px)\n\n")
            f.write("---\n\n")
            f.write(final_report)

        print(f"\n✅ Report saved to: {output_file}")
        print(f"   Screenshots captured: {len(all_screenshots)}")

    except Exception as e:
        print(f"\nERROR during assessment: {e}")
        import traceback
        traceback.print_exc()

    finally:
        print("\n    Stopping Streamlit server...")
        streamlit_process.terminate()
        try:
            streamlit_process.wait(timeout=5)
        except:
            streamlit_process.kill()
        print("    Done!\n")


if __name__ == "__main__":
    asyncio.run(run_comprehensive_assessment())
