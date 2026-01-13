"""
Playwright test runner for automated testing and evaluation
- Starts development servers (npm, python, etc.)
- Runs 6 automated tests (page load, mobile responsive, interactive, forms, navigation, errors)
- Captures screenshots (desktop, mobile, tablet)
- Measures performance metrics
"""

import asyncio
import subprocess
import time
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from playwright.async_api import async_playwright, Browser, Page, Error as PlaywrightError


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
        self.server_process = subprocess.Popen(
            ["npm", "start"],
            cwd=str(self.project_path),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True
        )

        # Wait for server to be ready
        return await self._wait_for_server()

    async def _start_python_server(self) -> bool:
        """Start Python development server (Flask/FastAPI/Django)"""
        # Detect framework
        if (self.project_path / "app.py").exists():
            # Flask
            print("🚀 Starting Flask server...")
            self.server_process = subprocess.Popen(
                ["python", "app.py"],
                cwd=str(self.project_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True
            )
        elif (self.project_path / "main.py").exists():
            # FastAPI or general Python
            print("🚀 Starting Python server...")
            self.server_process = subprocess.Popen(
                ["python", "main.py"],
                cwd=str(self.project_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True
            )
        elif (self.project_path / "manage.py").exists():
            # Django
            print("🚀 Starting Django server...")
            self.server_process = subprocess.Popen(
                ["python", "manage.py", "runserver"],
                cwd=str(self.project_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True
            )
        else:
            print("⚠️ Could not detect Python framework")
            return False

        return await self._wait_for_server()

    async def _start_static_server(self) -> bool:
        """Start simple HTTP server for static files"""
        print("🚀 Starting static file server...")
        self.server_process = subprocess.Popen(
            ["python", "-m", "http.server", "8000"],
            cwd=str(self.project_path),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True
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
