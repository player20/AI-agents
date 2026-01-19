"""
Audit Mode: User Behavior & Drop-Off Analysis

Analyzes existing apps for user behavior issues, drop-offs, and suggests
analytics SDK integrations (PostHog, AppsFlyer, OneSignal, etc.)
"""

import os
import json
import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import zipfile
import io
import re
from faker import Faker
from datetime import datetime

# Set up module logger
logger = logging.getLogger(__name__)

# Import Playwright for crawling
from playwright.async_api import async_playwright, Page, Browser

# Import for agent creation
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from multi_agent_team import create_agent_with_model, load_agent_configs
from crewai import Agent, Task, Crew, Process


async def find_first_matching_selector(page: Page, selectors: List[str], timeout: int = 5000) -> Tuple[Optional[Any], Optional[str]]:
    """
    Find the first matching selector using parallel checking.

    Instead of checking selectors sequentially (slow), this function:
    1. Creates locators for all selectors
    2. Uses asyncio.gather to check visibility in parallel
    3. Returns the first visible element found

    Args:
        page: Playwright page object
        selectors: List of CSS/Playwright selectors to try
        timeout: Maximum time to wait (applies to entire operation, not per selector)

    Returns:
        Tuple of (element, matching_selector) or (None, None) if no match
    """
    async def check_selector(selector: str) -> Tuple[Optional[Any], str]:
        """Check if a selector matches and is visible."""
        try:
            locator = page.locator(selector).first
            # Quick visibility check - don't wait long
            if await locator.is_visible():
                return (locator, selector)
        except Exception as e:
            # Expected for non-matching selectors - log at debug level
            logger.debug(f"Selector check failed for '{selector}': {e}")
        return (None, selector)

    # First pass: instant check for already-visible elements (no waiting)
    results = await asyncio.gather(*[check_selector(s) for s in selectors])
    for element, selector in results:
        if element:
            return (element, selector)

    # Second pass: wait a bit for elements that may be loading
    # Use a single wait_for_timeout then recheck
    await page.wait_for_timeout(min(timeout // 2, 1500))

    results = await asyncio.gather(*[check_selector(s) for s in selectors])
    for element, selector in results:
        if element:
            return (element, selector)

    # Third pass: final check after full timeout
    await page.wait_for_timeout(min(timeout // 2, 1500))

    results = await asyncio.gather(*[check_selector(s) for s in selectors])
    for element, selector in results:
        if element:
            return (element, selector)

    return (None, None)


async def fill_form_field_parallel(page: Page, field_selectors: List[str], value: str) -> bool:
    """
    Fill a form field by trying multiple selectors in parallel.

    Args:
        page: Playwright page
        field_selectors: List of possible selectors for this field
        value: Value to fill

    Returns:
        True if field was filled, False otherwise
    """
    element, _ = await find_first_matching_selector(page, field_selectors, timeout=2000)
    if element:
        try:
            await element.fill(value)
            return True
        except Exception as e:
            logger.debug(f"Failed to fill form field: {e}")
    return False


class AuditModeAnalyzer:
    """
    Analyzes apps for user behavior issues and drop-offs
    """

    def __init__(self, agents_config: List[Dict], model_preset: Dict):
        """Initialize with agent configs"""
        self.agents_config = agents_config
        self.model_preset = model_preset
        self.faker = Faker()

        # SDK detection patterns
        self.sdk_patterns = {
            'appsflyer': r'appsflyer|AF_|af-sdk',
            'onesignal': r'onesignal|OneSignal',
            'segment': r'segment|analytics\.track',
            'mixpanel': r'mixpanel',
            'amplitude': r'amplitude',
            'posthog': r'posthog',
            'firebase': r'firebase\.analytics',
            'gtm': r'gtm|googletagmanager',
            'ga4': r'gtag|google-analytics'
        }

    def detect_sdks(self, code_files: Dict[str, str]) -> Dict[str, bool]:
        """
        Detect analytics SDKs in codebase

        Args:
            code_files: Dict of filename -> content

        Returns:
            Dict of SDK name -> detected (bool)
        """
        detected = {sdk: False for sdk in self.sdk_patterns}

        for filename, content in code_files.items():
            content_lower = content.lower()

            for sdk_name, pattern in self.sdk_patterns.items():
                if re.search(pattern, content_lower, re.IGNORECASE):
                    detected[sdk_name] = True

        return detected

    async def crawl_app_flows(
        self,
        base_url: str,
        test_credentials: Optional[Dict[str, str]] = None,
        simulate_users: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Crawl app and simulate user journeys to detect drop-offs

        Args:
            base_url: App URL (localhost or live)
            test_credentials: Optional test login credentials
            simulate_users: Number of dummy user sessions to simulate

        Returns:
            List of session recordings with drop-off data
        """

        sessions = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)

            for i in range(simulate_users):
                session = await self._simulate_user_session(
                    browser,
                    base_url,
                    test_credentials,
                    user_id=i
                )
                sessions.append(session)

            await browser.close()

        return sessions

    async def _simulate_user_session(
        self,
        browser: Browser,
        base_url: str,
        test_credentials: Optional[Dict],
        user_id: int
    ) -> Dict[str, Any]:
        """
        Simulate a single user journey

        Returns:
            Session data with steps, errors, drop-off point
        """

        page = await browser.new_page()
        session_data = {
            'user_id': f"test_user_{user_id}",
            'started_at': datetime.now().isoformat(),
            'steps': [],
            'errors': [],
            'completed': False,
            'drop_off_step': None
        }

        try:
            # Step 1: Landing
            await page.goto(base_url, wait_until='networkidle', timeout=10000)
            session_data['steps'].append({
                'step': 'landing',
                'url': page.url,
                'timestamp': datetime.now().isoformat(),
                'success': True
            })

            # Step 2: Try to find signup/login
            # Expanded selectors for various frameworks and patterns
            signup_selectors = [
                # Standard button text patterns (case variations)
                'button:has-text("Sign Up")',
                'button:has-text("Sign up")',
                'button:has-text("SIGN UP")',
                'button:has-text("Get Started")',
                'button:has-text("Get started")',
                'button:has-text("GET STARTED")',
                'button:has-text("Create Account")',
                'button:has-text("Create account")',
                'button:has-text("Register")',
                'button:has-text("Join")',
                'button:has-text("Start")',
                'button:has-text("Continue")',
                'button:has-text("Next")',

                # Link-based signup
                'a:has-text("Sign Up")',
                'a:has-text("Sign up")',
                'a:has-text("Get Started")',
                'a:has-text("Register")',
                'a:has-text("Create Account")',

                # Framework-specific components
                'ion-button',                          # Ionic
                'ion-button:has-text("Sign")',
                'ion-button:has-text("Continue")',
                'app-button',                          # Angular custom
                'app-button:has-text("Sign")',
                'mat-button',                          # Angular Material
                'mat-raised-button',
                '.MuiButton-root',                     # Material UI
                '.MuiButton-containedPrimary',

                # Test IDs and data attributes
                '[data-testid="signup"]',
                '[data-testid="signup-button"]',
                '[data-testid*="sign"]',
                '[data-cy="signup"]',
                '[data-test="signup"]',

                # Common CSS classes
                '#signup',
                '.signup-button',
                '.signup-btn',
                '.btn-signup',
                '.btn-primary',
                '.cta-button',
                '.hero-button',

                # Role-based selectors
                '[role="button"]:has-text("Sign")',
                '[role="button"]:has-text("Get Started")',
            ]

            # Use parallel selector checking (MUCH faster than sequential)
            signup_element, matched_selector = await find_first_matching_selector(
                page, signup_selectors, timeout=5000
            )

            if signup_element:
                try:
                    await signup_element.click()
                    session_data['steps'].append({
                        'step': 'signup_clicked',
                        'selector': matched_selector,
                        'timestamp': datetime.now().isoformat(),
                        'success': True
                    })
                except Exception as click_err:
                    session_data['errors'].append({
                        'step': 'signup_click',
                        'error': f'Click failed: {str(click_err)}',
                        'severity': 'medium'
                    })
            else:
                session_data['drop_off_step'] = 'landing'
                session_data['errors'].append({
                    'step': 'signup',
                    'error': 'No signup button found',
                    'severity': 'high'
                })
                await page.close()
                return session_data

            # Wait for signup form
            await page.wait_for_timeout(1000)

            # Step 3: Fill signup form with fake data (using parallel field detection)
            try:
                # Generate fake user data
                fake_email = self.faker.email()
                fake_password = self.faker.password(length=12)
                fake_name = self.faker.name()

                # Try to fill common form fields using parallel detection
                email_selectors = ['input[type="email"]', 'input[name*="email"]', '#email', 'input[placeholder*="email"]']
                password_selectors = ['input[type="password"]', 'input[name*="password"]', '#password']
                name_selectors = ['input[name*="name"]', '#name', 'input[placeholder*="name"]', 'input[name*="first"]']

                # Fill fields in parallel
                fill_results = await asyncio.gather(
                    fill_form_field_parallel(page, email_selectors, fake_email),
                    fill_form_field_parallel(page, password_selectors, fake_password),
                    fill_form_field_parallel(page, name_selectors, fake_name),
                    return_exceptions=True
                )

                form_filled = any(r is True for r in fill_results if not isinstance(r, Exception))

                if form_filled:
                    session_data['steps'].append({
                        'step': 'form_filled',
                        'timestamp': datetime.now().isoformat(),
                        'success': True
                    })

                    # Try to submit - expanded selectors
                    submit_selectors = [
                        # Standard submit buttons
                        'button[type="submit"]',
                        'input[type="submit"]',

                        # Common text patterns (all case variations)
                        'button:has-text("Submit")',
                        'button:has-text("Create Account")',
                        'button:has-text("Create account")',
                        'button:has-text("Sign Up")',
                        'button:has-text("Sign up")',
                        'button:has-text("Register")',
                        'button:has-text("Continue")',
                        'button:has-text("Next")',
                        'button:has-text("Finish")',
                        'button:has-text("Done")',
                        'button:has-text("Complete")',
                        'button:has-text("Save")',
                        'button:has-text("Go")',
                        'button:has-text("Join")',

                        # Framework-specific
                        'ion-button[type="submit"]',
                        'ion-button:has-text("Continue")',
                        'ion-button:has-text("Submit")',
                        'ion-button:has-text("Create")',
                        'ion-button:has-text("Sign")',
                        'app-button[type="Primary"]',
                        'app-button:has-text("Continue")',
                        'app-button:has-text("Submit")',
                        'mat-button[type="submit"]',
                        'mat-raised-button[type="submit"]',
                        '.MuiButton-root[type="submit"]',

                        # Common CSS patterns
                        '.btn-primary[type="submit"]',
                        '.btn-submit',
                        '.submit-button',
                        '.form-submit',

                        # Test IDs
                        '[data-testid="submit"]',
                        '[data-testid*="submit"]',
                        '[data-cy="submit"]',
                    ]

                    # Use parallel selector checking for submit button (faster)
                    submit_element, submit_selector = await find_first_matching_selector(
                        page, submit_selectors, timeout=5000
                    )

                    if submit_element:
                        try:
                            await submit_element.click()
                            session_data['steps'].append({
                                'step': 'form_submitted',
                                'selector': submit_selector,
                                'timestamp': datetime.now().isoformat(),
                                'success': True
                            })
                        except Exception as submit_err:
                            session_data['errors'].append({
                                'step': 'form_submit_click',
                                'error': f'Submit click failed: {str(submit_err)}',
                                'severity': 'medium'
                            })

                    # Wait for response
                    await page.wait_for_timeout(2000)

                    # Check for errors using parallel detection
                    error_selectors = [
                        '.error',
                        '[role="alert"]',
                        '.alert-danger',
                        '.alert-error',
                        '.error-message',
                        '[class*="error"]',
                        'text="Error"'
                    ]

                    error_element, _ = await find_first_matching_selector(page, error_selectors, timeout=1000)
                    if error_element:
                        try:
                            error_text = await error_element.inner_text()
                            session_data['errors'].append({
                                'step': 'form_submission',
                                'error': error_text[:200],  # Truncate long errors
                                'severity': 'medium'
                            })
                            session_data['drop_off_step'] = 'form_submission'
                        except Exception as e:
                            logger.warning(f"Could not read error text from form submission: {e}")

                else:
                    session_data['drop_off_step'] = 'signup_form'
                    session_data['errors'].append({
                        'step': 'form_fill',
                        'error': 'Could not find form fields',
                        'severity': 'high'
                    })

            except Exception as e:
                session_data['errors'].append({
                    'step': 'form_interaction',
                    'error': str(e),
                    'severity': 'high'
                })
                session_data['drop_off_step'] = 'form_interaction'

            # Step 4: Check if we reached dashboard/home
            await page.wait_for_timeout(2000)
            current_url = page.url

            if 'dashboard' in current_url or 'home' in current_url or 'profile' in current_url:
                session_data['completed'] = True
                session_data['steps'].append({
                    'step': 'completed',
                    'url': current_url,
                    'timestamp': datetime.now().isoformat(),
                    'success': True
                })
            elif not session_data['drop_off_step']:
                session_data['drop_off_step'] = 'post_signup'

        except Exception as e:
            session_data['errors'].append({
                'step': 'session',
                'error': str(e),
                'severity': 'critical'
            })
            if not session_data['drop_off_step']:
                session_data['drop_off_step'] = 'unknown'

        finally:
            await page.close()

        return session_data

    def analyze_sessions(self, sessions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze sessions to compute funnel metrics

        Returns:
            Funnel analysis with drop-off percentages per step
        """

        total_users = len(sessions)
        if total_users == 0:
            return {'error': 'No sessions to analyze'}

        # Count completions per step
        funnel_steps = {
            'landing': 0,
            'signup_clicked': 0,
            'form_filled': 0,
            'form_submitted': 0,
            'completed': 0
        }

        drop_offs = {}

        for session in sessions:
            for step_data in session['steps']:
                step_name = step_data['step']
                if step_name in funnel_steps:
                    funnel_steps[step_name] += 1

            if session['drop_off_step']:
                drop_off = session['drop_off_step']
                drop_offs[drop_off] = drop_offs.get(drop_off, 0) + 1

        # Calculate percentages
        funnel_percentages = {}
        for step, count in funnel_steps.items():
            funnel_percentages[step] = {
                'count': count,
                'percentage': round((count / total_users) * 100, 1)
            }

        # Identify biggest drop-off
        biggest_drop = None
        max_drop_count = 0
        for step, count in drop_offs.items():
            if count > max_drop_count:
                max_drop_count = count
                biggest_drop = step

        return {
            'total_users': total_users,
            'funnel': funnel_percentages,
            'drop_offs': drop_offs,
            'biggest_drop_off': {
                'step': biggest_drop,
                'count': max_drop_count,
                'percentage': round((max_drop_count / total_users) * 100, 1) if total_users > 0 else 0
            },
            'completion_rate': round((funnel_steps['completed'] / total_users) * 100, 1) if total_users > 0 else 0
        }

    def generate_recommendations(
        self,
        funnel_analysis: Dict[str, Any],
        detected_sdks: Dict[str, bool],
        code_files: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate recommendations based on analysis

        Returns:
            List of recommendations with priority and code suggestions
        """

        recommendations = []

        # Check if any analytics SDK is present
        has_analytics = any(detected_sdks.values())

        if not has_analytics:
            recommendations.append({
                'priority': 'high',
                'category': 'analytics',
                'title': 'No Analytics SDK Detected',
                'description': 'Install PostHog or similar SDK for user behavior tracking',
                'code_snippet': '''
# Install PostHog
npm install posthog-js

# Initialize in your app
import posthog from 'posthog-js'
posthog.init('YOUR_API_KEY', { api_host: 'https://app.posthog.com' })

# Track events
posthog.capture('user_signed_up', { method: 'email' })
''',
                'impact': 'Enables data-driven decisions on user behavior'
            })

        # Check drop-off analysis
        biggest_drop = funnel_analysis.get('biggest_drop_off', {})
        if biggest_drop.get('percentage', 0) > 50:
            step = biggest_drop.get('step', 'unknown')
            recommendations.append({
                'priority': 'critical',
                'category': 'ux',
                'title': f'{biggest_drop["percentage"]}% drop-off at {step}',
                'description': f'Major friction point at {step}. Simplify this step immediately.',
                'suggestions': [
                    'Add progress indicator to show users where they are',
                    'Reduce required fields (defer non-essential data)',
                    'Add inline validation and helpful error messages',
                    'Consider social login options (Google, Apple)',
                    'Add trust signals (testimonials, security badges)'
                ],
                'impact': f'Could recover ~{biggest_drop["percentage"]}% of users'
            })

        # Completion rate
        completion_rate = funnel_analysis.get('completion_rate', 0)
        if completion_rate < 30:
            recommendations.append({
                'priority': 'high',
                'category': 'conversion',
                'title': f'Low completion rate ({completion_rate}%)',
                'description': 'User journey has too much friction',
                'suggestions': [
                    'Reduce steps in signup flow',
                    'Add "Skip for now" options',
                    'Implement auto-save for forms',
                    'Add exit-intent popups with help',
                    'Run A/B tests on different flows'
                ],
                'impact': 'Could double conversion rate'
            })

        return recommendations


def extract_code_from_zip(zip_data: bytes) -> Dict[str, str]:
    """Extract code files from ZIP for analysis"""
    code_files = {}

    try:
        with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
            for file_info in zf.filelist:
                filename = file_info.filename

                # Only extract code files
                if any(filename.endswith(ext) for ext in ['.js', '.ts', '.jsx', '.tsx', '.py', '.swift', '.kt', '.java']):
                    try:
                        content = zf.read(filename).decode('utf-8', errors='ignore')
                        code_files[filename] = content
                    except Exception as e:
                        logger.debug(f"Could not read file {filename} from ZIP: {e}")

    except Exception as e:
        logger.error(f"Error extracting ZIP: {e}")

    return code_files


# Test function
async def test_audit_mode():
    """Test audit mode functionality"""

    analyzer = AuditModeAnalyzer([], {})

    # Test SDK detection
    test_code = {
        'app.js': '''
import posthog from 'posthog-js'
posthog.init('test')
posthog.capture('event')
        '''
    }

    detected = analyzer.detect_sdks(test_code)
    print("Detected SDKs:", detected)

    # Test session analysis
    test_sessions = [
        {
            'user_id': 'user_1',
            'steps': [
                {'step': 'landing', 'success': True},
                {'step': 'signup_clicked', 'success': True}
            ],
            'errors': [],
            'completed': False,
            'drop_off_step': 'signup_form'
        },
        {
            'user_id': 'user_2',
            'steps': [
                {'step': 'landing', 'success': True},
                {'step': 'signup_clicked', 'success': True},
                {'step': 'form_filled', 'success': True},
                {'step': 'form_submitted', 'success': True},
                {'step': 'completed', 'success': True}
            ],
            'errors': [],
            'completed': True,
            'drop_off_step': None
        }
    ]

    analysis = analyzer.analyze_sessions(test_sessions)
    print("\nFunnel Analysis:", json.dumps(analysis, indent=2))

    recommendations = analyzer.generate_recommendations(analysis, detected, test_code)
    print("\nRecommendations:", json.dumps(recommendations, indent=2))


if __name__ == "__main__":
    asyncio.run(test_audit_mode())
