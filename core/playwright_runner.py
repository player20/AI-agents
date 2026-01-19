"""
Playwright test runner for automated testing and evaluation
- Starts development servers (npm, python, etc.)
- Runs 6 automated tests (page load, mobile responsive, interactive, forms, navigation, errors)
- Captures screenshots (desktop, mobile, tablet)
- Measures performance metrics
"""

import asyncio
import subprocess
import shutil
import sys
import time
import os
import base64
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from urllib.parse import urlparse, urljoin
from playwright.async_api import async_playwright, Browser, Page, Error as PlaywrightError


def _get_executable(name: str) -> str:
    """
    Safely get the full path to an executable.
    On Windows, this handles .cmd/.bat wrappers for npm/npx.

    Args:
        name: Command name (e.g., 'npm', 'python', 'npx')

    Returns:
        Full path to executable, or original name if not found
    """
    # shutil.which handles Windows .cmd/.bat automatically
    executable = shutil.which(name)
    if executable:
        return executable
    # Fallback to original name (let OS handle it)
    return name


def _safe_popen(args: List[str], cwd: str = None, **kwargs) -> subprocess.Popen:
    """
    Safely create a subprocess without shell=True.
    Resolves executable paths cross-platform.

    Args:
        args: Command arguments list
        cwd: Working directory
        **kwargs: Additional Popen arguments

    Returns:
        subprocess.Popen instance
    """
    # Resolve the executable path
    resolved_args = [_get_executable(args[0])] + args[1:]

    # Never use shell=True - remove if accidentally passed
    kwargs.pop('shell', None)

    return subprocess.Popen(
        resolved_args,
        cwd=cwd,
        **kwargs
    )


class PlaywrightRunner:
    """Automated testing and screenshot capture with Playwright"""

    def __init__(self, project_path: str, config: Dict):
        """
        Initialize Playwright runner

        Args:
            project_path: Path to the project directory
            config: Configuration dict with playwright and server settings
        """
        self.project_path = Path(project_path)
        self.config = config
        self.server_process = None
        self.server_url = None
        self.browser: Optional[Browser] = None

        # Viewports from config
        self.viewports = config['playwright']['viewport']
        self.timeout = config['playwright']['timeout']
        self.browser_type = config['playwright']['browser_type']

        # Server config
        self.server_config = config['server']

    async def start_server(self) -> bool:
        """
        Detect project type and start appropriate development server

        Returns:
            True if server started successfully, False otherwise
        """
        # Detect project type
        has_package_json = (self.project_path / "package.json").exists()
        has_requirements = (self.project_path / "requirements.txt").exists()
        has_html = list(self.project_path.glob("*.html"))

        try:
            if has_package_json:
                # Node.js project - try npm/yarn start
                self.server_url = "http://localhost:3000"
                return await self._start_node_server()

            elif has_requirements:
                # Python project - try common frameworks
                self.server_url = "http://localhost:5000"
                return await self._start_python_server()

            elif has_html:
                # Static HTML - use Python's simple HTTP server
                self.server_url = "http://localhost:8000"
                return await self._start_static_server()

            else:
                print(f"⚠️ Could not detect project type in {self.project_path}")
                return False

        except Exception as e:
            print(f"❌ Error starting server: {e}")
            return False

    async def _start_node_server(self) -> bool:
        """Start Node.js development server"""
        # Check if node_modules exists
        if not (self.project_path / "node_modules").exists():
            print("📦 Installing dependencies with npm install...")
            install_proc = subprocess.Popen(
                ["npm", "install"],
                cwd=str(self.project_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            install_proc.wait()

        # Start dev server
        print("🚀 Starting Node.js development server...")
        self.server_process = _safe_popen(
            ["npm", "start"],
            cwd=str(self.project_path),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # Wait for server to be ready
        return await self._wait_for_server()

    async def _start_python_server(self) -> bool:
        """Start Python development server (Flask/FastAPI/Django)"""
        # Detect framework
        if (self.project_path / "app.py").exists():
            # Flask
            print("🚀 Starting Flask server...")
            self.server_process = _safe_popen(
                ["python", "app.py"],
                cwd=str(self.project_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        elif (self.project_path / "main.py").exists():
            # FastAPI or general Python
            print("🚀 Starting Python server...")
            self.server_process = _safe_popen(
                ["python", "main.py"],
                cwd=str(self.project_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        elif (self.project_path / "manage.py").exists():
            # Django
            print("🚀 Starting Django server...")
            self.server_process = _safe_popen(
                ["python", "manage.py", "runserver"],
                cwd=str(self.project_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        else:
            print("⚠️ Could not detect Python framework")
            return False

        return await self._wait_for_server()

    async def _start_static_server(self) -> bool:
        """Start simple HTTP server for static files"""
        print("🚀 Starting static file server...")
        self.server_process = _safe_popen(
            ["python", "-m", "http.server", "8000"],
            cwd=str(self.project_path),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        return await self._wait_for_server()

    async def _wait_for_server(self) -> bool:
        """Wait for server to respond to requests"""
        max_attempts = self.server_config['max_startup_attempts']
        wait_interval = self.server_config['health_check_interval']

        for attempt in range(max_attempts):
            try:
                # Use playwright to check if page loads
                async with async_playwright() as p:
                    browser = await p.chromium.launch(headless=True)
                    page = await browser.new_page()
                    response = await page.goto(self.server_url, timeout=5000)
                    await browser.close()

                    if response and response.ok:
                        print(f"✅ Server ready at {self.server_url}")
                        return True

            except Exception:
                pass

            await asyncio.sleep(wait_interval)

        print(f"❌ Server failed to start after {max_attempts} attempts")
        return False

    def stop_server(self):
        """Stop the development server"""
        if self.server_process:
            self.server_process.terminate()
            try:
                self.server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.server_process.kill()
            print("🛑 Server stopped")

    async def run_tests(self) -> List[Dict]:
        """
        Run automated tests on the application

        Returns:
            List of test results with status, error, and duration
        """
        results = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=self.config['playwright']['headless']
            )

            # Test 1: Page loads successfully
            results.append(await self._test_page_load(browser))

            # Test 2: Mobile responsiveness
            results.append(await self._test_mobile_responsive(browser))

            # Test 3: Interactive elements
            results.append(await self._test_interactive_elements(browser))

            # Test 4: Form submission
            results.append(await self._test_form_submission(browser))

            # Test 5: Navigation
            results.append(await self._test_navigation(browser))

            # Test 6: Error handling (404)
            results.append(await self._test_error_handling(browser))

            await browser.close()

        return results

    async def _test_page_load(self, browser: Browser) -> Dict:
        """Test 1: Page loads with HTTP 200 and networkidle"""
        test_name = "Page Load"
        start_time = time.time()

        try:
            page = await browser.new_page()
            response = await page.goto(self.server_url, wait_until="networkidle", timeout=self.timeout)

            if response and response.ok:
                duration = int((time.time() - start_time) * 1000)
                await page.close()
                return {
                    "name": test_name,
                    "status": "passed",
                    "error": None,
                    "duration_ms": duration
                }
            else:
                await page.close()
                return {
                    "name": test_name,
                    "status": "failed",
                    "error": f"HTTP {response.status if response else 'no response'}",
                    "duration_ms": int((time.time() - start_time) * 1000)
                }

        except asyncio.TimeoutError:
            return {
                "name": test_name,
                "status": "timeout",
                "error": "Page load timed out",
                "duration_ms": int((time.time() - start_time) * 1000)
            }
        except ConnectionError as e:
            return {
                "name": test_name,
                "status": "failed",
                "error": f"Connection error: {str(e)}",
                "duration_ms": int((time.time() - start_time) * 1000)
            }
        except Exception as e:
            return {
                "name": test_name,
                "status": "failed",
                "error": str(e),
                "duration_ms": int((time.time() - start_time) * 1000)
            }

    async def _test_mobile_responsive(self, browser: Browser) -> Dict:
        """Test 2: Mobile viewport and meta tags"""
        test_name = "Mobile Responsive"
        start_time = time.time()

        try:
            page = await browser.new_page(
                viewport=self.viewports['mobile']
            )
            await page.goto(self.server_url, timeout=self.timeout)

            # Check for viewport meta tag
            viewport_meta = await page.query_selector('meta[name="viewport"]')

            if viewport_meta:
                content = await viewport_meta.get_attribute('content')
                if 'width=device-width' in content or 'initial-scale' in content:
                    duration = int((time.time() - start_time) * 1000)
                    await page.close()
                    return {
                        "name": test_name,
                        "status": "passed",
                        "error": None,
                        "duration_ms": duration
                    }

            await page.close()
            return {
                "name": test_name,
                "status": "failed",
                "error": "No proper viewport meta tag found",
                "duration_ms": int((time.time() - start_time) * 1000)
            }

        except Exception as e:
            return {
                "name": test_name,
                "status": "failed",
                "error": str(e),
                "duration_ms": int((time.time() - start_time) * 1000)
            }

    async def _test_interactive_elements(self, browser: Browser) -> Dict:
        """Test 3: Buttons and links are clickable"""
        test_name = "Interactive Elements"
        start_time = time.time()

        try:
            page = await browser.new_page()
            await page.goto(self.server_url, timeout=self.timeout)

            # Check for buttons
            buttons = await page.query_selector_all('button, a, input[type="submit"], input[type="button"]')

            if len(buttons) > 0:
                # Try clicking the first button
                try:
                    await buttons[0].click(timeout=2000)
                    duration = int((time.time() - start_time) * 1000)
                    await page.close()
                    return {
                        "name": test_name,
                        "status": "passed",
                        "error": None,
                        "duration_ms": duration
                    }
                except Exception as e:
                    await page.close()
                    return {
                        "name": test_name,
                        "status": "failed",
                        "error": f"Could not click element: {str(e)}",
                        "duration_ms": int((time.time() - start_time) * 1000)
                    }
            else:
                await page.close()
                return {
                    "name": test_name,
                    "status": "warning",
                    "error": "No interactive elements found",
                    "duration_ms": int((time.time() - start_time) * 1000)
                }

        except Exception as e:
            return {
                "name": test_name,
                "status": "failed",
                "error": str(e),
                "duration_ms": int((time.time() - start_time) * 1000)
            }

    async def _test_form_submission(self, browser: Browser) -> Dict:
        """Test 4: Form can be filled and submitted"""
        test_name = "Form Submission"
        start_time = time.time()

        try:
            page = await browser.new_page()
            await page.goto(self.server_url, timeout=self.timeout)

            # Look for forms
            forms = await page.query_selector_all('form')

            if len(forms) == 0:
                await page.close()
                return {
                    "name": test_name,
                    "status": "skipped",
                    "error": "No forms found on page",
                    "duration_ms": int((time.time() - start_time) * 1000)
                }

            # Try to fill and submit first form
            try:
                # Fill text inputs with dummy data
                inputs = await page.query_selector_all('input[type="text"], input[type="email"], input:not([type]), textarea')
                for input_field in inputs:
                    await input_field.fill("test@example.com")

                # Click submit button
                submit_btn = await page.query_selector('input[type="submit"], button[type="submit"], form button')
                if submit_btn:
                    await submit_btn.click()
                    await page.wait_for_timeout(1000)

                duration = int((time.time() - start_time) * 1000)
                await page.close()
                return {
                    "name": test_name,
                    "status": "passed",
                    "error": None,
                    "duration_ms": duration
                }

            except Exception as e:
                await page.close()
                return {
                    "name": test_name,
                    "status": "failed",
                    "error": f"Form submission error: {str(e)}",
                    "duration_ms": int((time.time() - start_time) * 1000)
                }

        except Exception as e:
            return {
                "name": test_name,
                "status": "failed",
                "error": str(e),
                "duration_ms": int((time.time() - start_time) * 1000)
            }

    async def _test_navigation(self, browser: Browser) -> Dict:
        """Test 5: Navigation links work"""
        test_name = "Navigation"
        start_time = time.time()

        try:
            page = await browser.new_page()
            await page.goto(self.server_url, timeout=self.timeout)

            # Find navigation links
            nav_links = await page.query_selector_all('nav a, header a, a[href^="/"]')

            if len(nav_links) == 0:
                await page.close()
                return {
                    "name": test_name,
                    "status": "warning",
                    "error": "No navigation links found",
                    "duration_ms": int((time.time() - start_time) * 1000)
                }

            # Try clicking first internal link
            try:
                first_link = nav_links[0]
                await first_link.click()
                await page.wait_for_load_state("networkidle", timeout=5000)

                duration = int((time.time() - start_time) * 1000)
                await page.close()
                return {
                    "name": test_name,
                    "status": "passed",
                    "error": None,
                    "duration_ms": duration
                }

            except Exception as e:
                await page.close()
                return {
                    "name": test_name,
                    "status": "failed",
                    "error": f"Navigation failed: {str(e)}",
                    "duration_ms": int((time.time() - start_time) * 1000)
                }

        except Exception as e:
            return {
                "name": test_name,
                "status": "failed",
                "error": str(e),
                "duration_ms": int((time.time() - start_time) * 1000)
            }

    async def _test_error_handling(self, browser: Browser) -> Dict:
        """Test 6: 404 page exists"""
        test_name = "Error Handling (404)"
        start_time = time.time()

        try:
            page = await browser.new_page()
            response = await page.goto(
                f"{self.server_url}/this-page-definitely-does-not-exist-12345",
                timeout=self.timeout
            )

            # Check for 404 status or error page content
            if response and response.status == 404:
                duration = int((time.time() - start_time) * 1000)
                await page.close()
                return {
                    "name": test_name,
                    "status": "passed",
                    "error": None,
                    "duration_ms": duration
                }
            else:
                # Check if page has error content
                content = await page.content()
                if '404' in content or 'not found' in content.lower():
                    duration = int((time.time() - start_time) * 1000)
                    await page.close()
                    return {
                        "name": test_name,
                        "status": "passed",
                        "error": None,
                        "duration_ms": duration
                    }
                else:
                    await page.close()
                    return {
                        "name": test_name,
                        "status": "failed",
                        "error": "No 404 error handling detected",
                        "duration_ms": int((time.time() - start_time) * 1000)
                    }

        except Exception as e:
            return {
                "name": test_name,
                "status": "failed",
                "error": str(e),
                "duration_ms": int((time.time() - start_time) * 1000)
            }

    async def capture_screenshots(self) -> List[Dict]:
        """
        Capture screenshots at different viewports

        Returns:
            List of screenshot data with name, path, and viewport info
        """
        screenshots = []
        screenshots_dir = Path(self.config['screenshots_dir'])
        screenshots_dir.mkdir(exist_ok=True)

        timestamp = int(time.time())

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)

            for viewport_name, viewport_size in self.viewports.items():
                try:
                    page = await browser.new_page(viewport=viewport_size)
                    await page.goto(self.server_url, wait_until="networkidle", timeout=self.timeout)

                    # Full page screenshot
                    screenshot_filename = f"screenshot_{viewport_name}_{timestamp}.png"
                    screenshot_path = screenshots_dir / screenshot_filename

                    await page.screenshot(path=str(screenshot_path), full_page=True)

                    screenshots.append({
                        "name": viewport_name.capitalize(),
                        "path": str(screenshot_path),
                        "viewport": viewport_size
                    })

                    await page.close()
                    print(f"📸 Captured {viewport_name} screenshot")

                except Exception as e:
                    print(f"❌ Failed to capture {viewport_name} screenshot: {e}")

            await browser.close()

        return screenshots

    async def measure_performance(self) -> Dict:
        """
        Measure performance metrics

        Returns:
            Dictionary with performance metrics
        """
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()

                # Navigate and measure
                start_time = time.time()
                await page.goto(self.server_url, wait_until="load")
                page_load_time = int((time.time() - start_time) * 1000)

                # Get performance metrics from browser
                metrics = await page.evaluate('''() => {
                    const timing = performance.timing;
                    const navigation = performance.getEntriesByType('navigation')[0];

                    return {
                        domContentLoaded: timing.domContentLoadedEventEnd - timing.navigationStart,
                        loadComplete: timing.loadEventEnd - timing.navigationStart,
                        firstContentfulPaint: navigation ? navigation.domContentLoadedEventEnd : 0,
                        timeToInteractive: timing.domInteractive - timing.navigationStart
                    };
                }''')

                # Get total page size
                resources = await page.evaluate('''() => {
                    return performance.getEntriesByType('resource')
                        .reduce((total, resource) => total + (resource.transferSize || 0), 0);
                }''')

                await browser.close()

                return {
                    "page_load_ms": page_load_time,
                    "time_to_interactive_ms": metrics.get('timeToInteractive', 0),
                    "first_contentful_paint_ms": metrics.get('firstContentfulPaint', 0),
                    "total_size_kb": int(resources / 1024) if resources else 0
                }

        except Exception as e:
            print(f"❌ Performance measurement failed: {e}")
            return {
                "page_load_ms": 0,
                "time_to_interactive_ms": 0,
                "first_contentful_paint_ms": 0,
                "total_size_kb": 0
            }

    async def discover_all_pages(
        self,
        start_url: str = None,
        credentials: Dict = None,
        max_pages: int = 100
    ) -> List[str]:
        """
        Crawl the application and discover all internal pages.

        Args:
            start_url: Starting URL (defaults to self.server_url)
            credentials: Optional dict with 'email' and 'password' for auth
            max_pages: Maximum pages to discover (default 100)

        Returns:
            List of unique internal URLs discovered
        """
        start_url = start_url or self.server_url
        if not start_url:
            print("❌ No server URL set")
            return []

        base_domain = urlparse(start_url).netloc
        discovered_urls: Set[str] = set()
        urls_to_visit: List[str] = [start_url]
        visited_urls: Set[str] = set()

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()

            # Handle authentication if credentials provided
            if credentials and credentials.get('email') and credentials.get('password'):
                try:
                    print("🔐 Attempting authentication...")
                    await page.goto(start_url, wait_until="networkidle", timeout=self.timeout)

                    # Try common auth patterns
                    email_selectors = ['input[type="email"]', 'input[name="email"]', '#email', 'input[placeholder*="email" i]']
                    password_selectors = ['input[type="password"]', 'input[name="password"]', '#password']
                    submit_selectors = ['button[type="submit"]', 'input[type="submit"]', 'button:has-text("Log in")', 'button:has-text("Sign in")']

                    for selector in email_selectors:
                        try:
                            email_input = await page.query_selector(selector)
                            if email_input:
                                await email_input.fill(credentials['email'])
                                break
                        except:
                            continue

                    for selector in password_selectors:
                        try:
                            password_input = await page.query_selector(selector)
                            if password_input:
                                await password_input.fill(credentials['password'])
                                break
                        except:
                            continue

                    for selector in submit_selectors:
                        try:
                            submit_btn = await page.query_selector(selector)
                            if submit_btn:
                                await submit_btn.click()
                                await page.wait_for_load_state("networkidle", timeout=10000)
                                print("✅ Authentication successful")
                                break
                        except:
                            continue

                except Exception as e:
                    print(f"⚠️ Authentication attempt failed: {e}")

            # BFS crawl to discover pages
            while urls_to_visit and len(discovered_urls) < max_pages:
                current_url = urls_to_visit.pop(0)

                # Normalize URL (remove fragments and trailing slashes)
                parsed = urlparse(current_url)
                normalized_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path.rstrip('/')}"

                if normalized_url in visited_urls:
                    continue

                visited_urls.add(normalized_url)

                try:
                    await page.goto(current_url, wait_until="networkidle", timeout=self.timeout)
                    discovered_urls.add(normalized_url)
                    print(f"🔍 Discovered: {normalized_url}")

                    # Extract all internal links
                    links = await page.evaluate(f'''() => {{
                        const links = Array.from(document.querySelectorAll('a[href]'));
                        return links
                            .map(a => a.href)
                            .filter(href => {{
                                try {{
                                    const url = new URL(href);
                                    return url.hostname === '{base_domain}' &&
                                           !href.includes('#') &&
                                           !href.match(/\\.(pdf|zip|png|jpg|jpeg|gif|svg|css|js)$/i);
                                }} catch {{
                                    return false;
                                }}
                            }});
                    }}''')

                    for link in links:
                        parsed_link = urlparse(link)
                        normalized_link = f"{parsed_link.scheme}://{parsed_link.netloc}{parsed_link.path.rstrip('/')}"
                        if normalized_link not in visited_urls and normalized_link not in urls_to_visit:
                            urls_to_visit.append(normalized_link)

                except Exception as e:
                    print(f"⚠️ Failed to crawl {current_url}: {e}")

            await browser.close()

        print(f"✅ Discovered {len(discovered_urls)} unique pages")
        return list(discovered_urls)

    async def capture_all_pages_with_vision(
        self,
        urls: List[str] = None,
        credentials: Dict = None,
        viewports: List[str] = None
    ) -> List[Dict]:
        """
        Capture screenshots of all pages with base64 encoding for vision API.

        Args:
            urls: List of URLs to capture (if None, discovers automatically)
            credentials: Optional auth credentials
            viewports: Which viewports to capture (default: ['mobile', 'desktop'])

        Returns:
            List of dicts with: url, viewport, base64, mime_type, name
        """
        if viewports is None:
            viewports = ['mobile', 'desktop']

        # Discover pages if not provided
        if urls is None:
            urls = await self.discover_all_pages(credentials=credentials)

        if not urls:
            print("❌ No URLs to capture")
            return []

        screenshots = []
        screenshots_dir = Path(self.config.get('screenshots_dir', 'screenshots'))
        screenshots_dir.mkdir(exist_ok=True)
        timestamp = int(time.time())

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()

            # Re-authenticate if credentials provided
            if credentials and credentials.get('email') and credentials.get('password'):
                temp_page = await context.new_page()
                try:
                    await temp_page.goto(urls[0], wait_until="networkidle", timeout=self.timeout)

                    # Try to log in
                    email_selectors = ['input[type="email"]', 'input[name="email"]', '#email']
                    password_selectors = ['input[type="password"]', 'input[name="password"]', '#password']
                    submit_selectors = ['button[type="submit"]', 'input[type="submit"]', 'button:has-text("Log in")']

                    for selector in email_selectors:
                        try:
                            el = await temp_page.query_selector(selector)
                            if el:
                                await el.fill(credentials['email'])
                                break
                        except:
                            continue

                    for selector in password_selectors:
                        try:
                            el = await temp_page.query_selector(selector)
                            if el:
                                await el.fill(credentials['password'])
                                break
                        except:
                            continue

                    for selector in submit_selectors:
                        try:
                            el = await temp_page.query_selector(selector)
                            if el:
                                await el.click()
                                await temp_page.wait_for_load_state("networkidle", timeout=10000)
                                break
                        except:
                            continue

                except Exception as e:
                    print(f"⚠️ Auth setup failed: {e}")
                finally:
                    await temp_page.close()

            # Capture each URL at each viewport
            for url_idx, url in enumerate(urls):
                page_name = urlparse(url).path or "home"
                page_name = page_name.strip('/').replace('/', '_') or "home"

                for viewport_name in viewports:
                    if viewport_name not in self.viewports:
                        continue

                    viewport_size = self.viewports[viewport_name]

                    try:
                        page = await context.new_page()
                        await page.set_viewport_size(viewport_size)
                        await page.goto(url, wait_until="networkidle", timeout=self.timeout)

                        # Capture screenshot as bytes
                        screenshot_bytes = await page.screenshot(full_page=True)
                        base64_data = base64.b64encode(screenshot_bytes).decode('utf-8')

                        # Also save to disk for reference
                        filename = f"vision_{page_name}_{viewport_name}_{timestamp}.png"
                        filepath = screenshots_dir / filename
                        with open(filepath, 'wb') as f:
                            f.write(screenshot_bytes)

                        screenshots.append({
                            "url": url,
                            "page_name": page_name,
                            "viewport": viewport_name,
                            "viewport_size": viewport_size,
                            "base64": base64_data,
                            "mime_type": "image/png",
                            "path": str(filepath),
                            "name": f"{page_name} ({viewport_name.capitalize()})"
                        })

                        print(f"📸 Captured: {page_name} ({viewport_name})")
                        await page.close()

                    except Exception as e:
                        print(f"⚠️ Failed to capture {url} at {viewport_name}: {e}")

            await browser.close()

        print(f"✅ Captured {len(screenshots)} screenshots across {len(urls)} pages")
        return screenshots
