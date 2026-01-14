"""
Standalone screenshot capture script that runs in its own process.
This avoids Windows asyncio event loop conflicts with Streamlit.
"""

import sys
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
import time


def capture_screenshots(server_url: str, output_dir: str) -> list:
    """Capture screenshots at multiple viewports"""
    screenshots = []
    screenshots_dir = Path(output_dir)
    screenshots_dir.mkdir(exist_ok=True)

    timestamp = int(time.time())

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        viewports = {
            'desktop': {'width': 1920, 'height': 1080},
            'tablet': {'width': 768, 'height': 1024},
            'mobile': {'width': 375, 'height': 667}
        }

        for viewport_name, viewport_size in viewports.items():
            try:
                page = browser.new_page(viewport=viewport_size)
                page.goto(server_url, wait_until="networkidle", timeout=30000)

                screenshot_filename = f"screenshot_{viewport_name}_{timestamp}.png"
                screenshot_path = screenshots_dir / screenshot_filename

                page.screenshot(path=str(screenshot_path), full_page=True)

                screenshots.append({
                    "name": viewport_name.capitalize(),
                    "path": str(screenshot_path),
                    "viewport": viewport_size
                })

                page.close()
            except Exception as e:
                print(f"ERROR capturing {viewport_name}: {e}", file=sys.stderr)

        browser.close()

    return screenshots


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python capture_screenshots.py <server_url> <output_dir>")
        sys.exit(1)

    server_url = sys.argv[1]
    output_dir = sys.argv[2]

    try:
        screenshots = capture_screenshots(server_url, output_dir)
        # Output JSON to stdout
        print(json.dumps(screenshots))
        sys.exit(0)
    except Exception as e:
        print(f"FATAL ERROR: {e}", file=sys.stderr)
        sys.exit(1)
