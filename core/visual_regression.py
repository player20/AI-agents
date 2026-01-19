"""
Visual Regression Testing Module

Compares screenshots across iterations to track visual changes.
Useful for:
- Detecting unintended visual regressions
- Measuring improvement progress
- Generating before/after comparison reports

Dependencies:
    pip install pillow imagehash
"""

import json
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

try:
    from PIL import Image, ImageChops, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import imagehash
    IMAGEHASH_AVAILABLE = True
except ImportError:
    IMAGEHASH_AVAILABLE = False


@dataclass
class ComparisonResult:
    """Result of comparing two screenshots."""
    page_name: str
    status: str  # "new", "unchanged", "changed", "missing"
    diff_percent: float
    hash_diff: int
    current_path: str
    baseline_path: Optional[str]
    diff_path: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "page_name": self.page_name,
            "status": self.status,
            "diff_percent": self.diff_percent,
            "hash_diff": self.hash_diff,
            "current_path": self.current_path,
            "baseline_path": self.baseline_path,
            "diff_path": self.diff_path,
            "details": self.details
        }


@dataclass
class RegressionReport:
    """Full regression test report."""
    timestamp: str
    total_pages: int
    changed_count: int
    unchanged_count: int
    new_count: int
    missing_count: int
    comparisons: List[ComparisonResult]
    summary_score: float  # 0-100, higher is better (fewer changes)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "total_pages": self.total_pages,
            "changed_count": self.changed_count,
            "unchanged_count": self.unchanged_count,
            "new_count": self.new_count,
            "missing_count": self.missing_count,
            "comparisons": [c.to_dict() for c in self.comparisons],
            "summary_score": self.summary_score
        }


class VisualRegression:
    """
    Visual regression testing for screenshot comparison.

    Compares current screenshots against a baseline to detect changes.
    Generates diff images and reports for visual inspection.
    """

    # Thresholds for change detection
    CHANGE_THRESHOLD_PERCENT = 1.0  # Pixel diff threshold (%)
    HASH_DIFF_THRESHOLD = 5  # Perceptual hash difference threshold

    def __init__(self, baseline_dir: Path):
        """
        Initialize visual regression tester.

        Args:
            baseline_dir: Directory to store baseline screenshots
        """
        self.baseline_dir = Path(baseline_dir)
        self.baseline_dir.mkdir(parents=True, exist_ok=True)
        self.diff_dir = self.baseline_dir / "diffs"
        self.diff_dir.mkdir(exist_ok=True)

    def set_baseline(self, screenshots: List[Dict]) -> int:
        """
        Set current screenshots as the new baseline.

        Args:
            screenshots: List of screenshot dictionaries

        Returns:
            Number of baselines set
        """
        count = 0
        for screenshot in screenshots:
            src_path = screenshot.get("path")
            if not src_path or not Path(src_path).exists():
                continue

            # Use page name + viewport as baseline name
            page = screenshot.get("page", screenshot.get("name", "unknown"))
            viewport = screenshot.get("viewport", {})
            width = viewport.get("width", "unknown")
            state = screenshot.get("state", "default")

            baseline_name = f"{page}_{width}_{state}.png"
            baseline_path = self.baseline_dir / baseline_name

            shutil.copy(src_path, baseline_path)
            count += 1

        # Save metadata
        metadata = {
            "timestamp": datetime.now().isoformat(),
            "screenshot_count": count,
            "screenshots": [
                {
                    "name": s.get("name"),
                    "page": s.get("page"),
                    "viewport": s.get("viewport"),
                    "state": s.get("state", "default")
                }
                for s in screenshots
            ]
        }
        (self.baseline_dir / "baseline_metadata.json").write_text(
            json.dumps(metadata, indent=2)
        )

        return count

    def compare(self, current_screenshots: List[Dict]) -> RegressionReport:
        """
        Compare current screenshots against baseline.

        Args:
            current_screenshots: List of current screenshot dictionaries

        Returns:
            RegressionReport with comparison results
        """
        if not PIL_AVAILABLE:
            return RegressionReport(
                timestamp=datetime.now().isoformat(),
                total_pages=len(current_screenshots),
                changed_count=0,
                unchanged_count=0,
                new_count=len(current_screenshots),
                missing_count=0,
                comparisons=[],
                summary_score=100.0
            )

        comparisons = []
        changed_count = 0
        unchanged_count = 0
        new_count = 0

        for screenshot in current_screenshots:
            result = self._compare_single(screenshot)
            comparisons.append(result)

            if result.status == "changed":
                changed_count += 1
            elif result.status == "unchanged":
                unchanged_count += 1
            elif result.status == "new":
                new_count += 1

        # Check for missing baselines (baselines that weren't matched)
        current_names = set()
        for s in current_screenshots:
            page = s.get("page", s.get("name", "unknown"))
            viewport = s.get("viewport", {})
            width = viewport.get("width", "unknown")
            state = s.get("state", "default")
            current_names.add(f"{page}_{width}_{state}")

        missing_count = 0
        for baseline_file in self.baseline_dir.glob("*.png"):
            if baseline_file.stem not in current_names:
                missing_count += 1
                comparisons.append(ComparisonResult(
                    page_name=baseline_file.stem,
                    status="missing",
                    diff_percent=100.0,
                    hash_diff=100,
                    current_path="",
                    baseline_path=str(baseline_file)
                ))

        # Calculate summary score (fewer changes = higher score)
        total = len(comparisons)
        if total > 0:
            # Penalize changes and missing pages
            penalty = (changed_count * 10 + missing_count * 20) / total
            summary_score = max(0, 100 - penalty * 10)
        else:
            summary_score = 100.0

        return RegressionReport(
            timestamp=datetime.now().isoformat(),
            total_pages=total,
            changed_count=changed_count,
            unchanged_count=unchanged_count,
            new_count=new_count,
            missing_count=missing_count,
            comparisons=comparisons,
            summary_score=round(summary_score, 1)
        )

    def _compare_single(self, screenshot: Dict) -> ComparisonResult:
        """Compare a single screenshot against its baseline."""
        current_path = screenshot.get("path", "")
        page = screenshot.get("page", screenshot.get("name", "unknown"))
        viewport = screenshot.get("viewport", {})
        width = viewport.get("width", "unknown")
        state = screenshot.get("state", "default")

        baseline_name = f"{page}_{width}_{state}.png"
        baseline_path = self.baseline_dir / baseline_name

        if not baseline_path.exists():
            # No baseline - this is a new screenshot
            return ComparisonResult(
                page_name=f"{page}_{width}_{state}",
                status="new",
                diff_percent=0,
                hash_diff=0,
                current_path=current_path,
                baseline_path=None,
                details={"reason": "No baseline exists"}
            )

        if not Path(current_path).exists():
            return ComparisonResult(
                page_name=f"{page}_{width}_{state}",
                status="missing",
                diff_percent=100,
                hash_diff=100,
                current_path=current_path,
                baseline_path=str(baseline_path),
                details={"reason": "Current screenshot not found"}
            )

        try:
            current_img = Image.open(current_path)
            baseline_img = Image.open(baseline_path)

            # Calculate perceptual hash difference
            hash_diff = 0
            if IMAGEHASH_AVAILABLE:
                current_hash = imagehash.phash(current_img)
                baseline_hash = imagehash.phash(baseline_img)
                hash_diff = current_hash - baseline_hash

            # Calculate pixel difference
            diff_percent = 0.0
            diff_path = None

            if current_img.size == baseline_img.size:
                # Same size - can do pixel comparison
                diff = ImageChops.difference(
                    current_img.convert('RGB'),
                    baseline_img.convert('RGB')
                )

                # Count different pixels (threshold to ignore minor variations)
                diff_data = diff.convert('L').point(lambda x: 255 if x > 10 else 0)
                diff_pixels = sum(1 for p in diff_data.getdata() if p > 0)
                total_pixels = current_img.size[0] * current_img.size[1]
                diff_percent = (diff_pixels / total_pixels) * 100

                # Generate diff image if there are changes
                if diff_percent > self.CHANGE_THRESHOLD_PERCENT:
                    diff_path = str(self.diff_dir / f"diff_{baseline_name}")
                    self._generate_diff_image(current_img, baseline_img, diff, diff_path)
            else:
                # Different sizes - significant change
                diff_percent = 100.0
                details = {
                    "reason": "Size changed",
                    "current_size": current_img.size,
                    "baseline_size": baseline_img.size
                }

            # Determine status
            is_changed = (
                diff_percent > self.CHANGE_THRESHOLD_PERCENT or
                hash_diff > self.HASH_DIFF_THRESHOLD
            )

            return ComparisonResult(
                page_name=f"{page}_{width}_{state}",
                status="changed" if is_changed else "unchanged",
                diff_percent=round(diff_percent, 2),
                hash_diff=hash_diff,
                current_path=current_path,
                baseline_path=str(baseline_path),
                diff_path=diff_path
            )

        except Exception as e:
            return ComparisonResult(
                page_name=f"{page}_{width}_{state}",
                status="changed",
                diff_percent=100,
                hash_diff=100,
                current_path=current_path,
                baseline_path=str(baseline_path),
                details={"error": str(e)}
            )

    def _generate_diff_image(
        self,
        current: Image.Image,
        baseline: Image.Image,
        diff: Image.Image,
        output_path: str
    ):
        """Generate a side-by-side diff image."""
        try:
            # Create a side-by-side comparison
            width = current.width
            height = current.height
            comparison = Image.new('RGB', (width * 3, height))

            # Paste: baseline | current | diff (enhanced)
            comparison.paste(baseline.convert('RGB'), (0, 0))
            comparison.paste(current.convert('RGB'), (width, 0))

            # Enhance diff for visibility (make changes red)
            diff_enhanced = Image.new('RGB', (width, height), (255, 255, 255))
            diff_gray = diff.convert('L')
            for x in range(width):
                for y in range(height):
                    pixel = diff_gray.getpixel((x, y))
                    if pixel > 10:
                        diff_enhanced.putpixel((x, y), (255, 0, 0))
                    else:
                        # Show original content in unchanged areas
                        diff_enhanced.putpixel((x, y), current.convert('RGB').getpixel((x, y)))

            comparison.paste(diff_enhanced, (width * 2, 0))

            # Add labels
            draw = ImageDraw.Draw(comparison)
            try:
                font = ImageFont.truetype("arial.ttf", 20)
            except:
                font = ImageFont.load_default()

            draw.text((10, 10), "BASELINE", fill=(255, 255, 255), font=font)
            draw.text((width + 10, 10), "CURRENT", fill=(255, 255, 255), font=font)
            draw.text((width * 2 + 10, 10), "DIFF (red=changed)", fill=(255, 0, 0), font=font)

            comparison.save(output_path)

        except Exception:
            # If diff generation fails, just save the diff as-is
            diff.save(output_path)

    def generate_html_report(self, report: RegressionReport, output_path: Path) -> str:
        """Generate an HTML report from regression results."""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Visual Regression Report</title>
    <style>
        body {{ font-family: system-ui; background: #1a1d29; color: #fff; padding: 20px; }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .score {{ font-size: 48px; font-weight: bold; }}
        .score.good {{ color: #10b981; }}
        .score.warn {{ color: #f59e0b; }}
        .score.bad {{ color: #ef4444; }}
        .stats {{ display: flex; justify-content: center; gap: 30px; margin: 20px 0; }}
        .stat {{ text-align: center; padding: 15px; background: rgba(255,255,255,0.1); border-radius: 8px; }}
        .stat-value {{ font-size: 24px; font-weight: bold; }}
        .stat-label {{ color: #94a3b8; font-size: 14px; }}
        .comparison {{ margin: 20px 0; padding: 15px; background: rgba(255,255,255,0.05); border-radius: 8px; }}
        .comparison.changed {{ border-left: 4px solid #ef4444; }}
        .comparison.unchanged {{ border-left: 4px solid #10b981; }}
        .comparison.new {{ border-left: 4px solid #3b82f6; }}
        .comparison.missing {{ border-left: 4px solid #f59e0b; }}
        .comparison-header {{ display: flex; justify-content: space-between; align-items: center; }}
        .status-badge {{ padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: bold; }}
        .status-badge.changed {{ background: #ef4444; }}
        .status-badge.unchanged {{ background: #10b981; }}
        .status-badge.new {{ background: #3b82f6; }}
        .status-badge.missing {{ background: #f59e0b; }}
        .diff-info {{ color: #94a3b8; margin-top: 8px; }}
        .images {{ display: flex; gap: 10px; margin-top: 15px; flex-wrap: wrap; }}
        .images img {{ max-width: 300px; border-radius: 4px; border: 1px solid rgba(255,255,255,0.1); }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Visual Regression Report</h1>
        <p>{report.timestamp}</p>
        <div class="score {'good' if report.summary_score >= 80 else 'warn' if report.summary_score >= 50 else 'bad'}">
            {report.summary_score}%
        </div>
        <p>Visual Stability Score</p>
    </div>

    <div class="stats">
        <div class="stat">
            <div class="stat-value">{report.total_pages}</div>
            <div class="stat-label">Total Pages</div>
        </div>
        <div class="stat">
            <div class="stat-value" style="color: #10b981;">{report.unchanged_count}</div>
            <div class="stat-label">Unchanged</div>
        </div>
        <div class="stat">
            <div class="stat-value" style="color: #ef4444;">{report.changed_count}</div>
            <div class="stat-label">Changed</div>
        </div>
        <div class="stat">
            <div class="stat-value" style="color: #3b82f6;">{report.new_count}</div>
            <div class="stat-label">New</div>
        </div>
        <div class="stat">
            <div class="stat-value" style="color: #f59e0b;">{report.missing_count}</div>
            <div class="stat-label">Missing</div>
        </div>
    </div>

    <h2>Comparisons</h2>
"""
        for comp in report.comparisons:
            html += f"""
    <div class="comparison {comp.status}">
        <div class="comparison-header">
            <strong>{comp.page_name}</strong>
            <span class="status-badge {comp.status}">{comp.status.upper()}</span>
        </div>
        <div class="diff-info">
            Pixel Diff: {comp.diff_percent}% | Hash Diff: {comp.hash_diff}
        </div>
"""
            if comp.diff_path and Path(comp.diff_path).exists():
                html += f"""
        <div class="images">
            <img src="file://{comp.diff_path}" alt="Diff comparison">
        </div>
"""
            html += "    </div>\n"

        html += """
</body>
</html>
"""
        output_path = Path(output_path)
        output_path.write_text(html)
        return str(output_path)


# Convenience functions
def compare_screenshots(
    current_screenshots: List[Dict],
    baseline_dir: str | Path
) -> RegressionReport:
    """
    Compare screenshots against baseline.

    Args:
        current_screenshots: List of current screenshots
        baseline_dir: Directory containing baseline screenshots

    Returns:
        RegressionReport with comparison results
    """
    regression = VisualRegression(Path(baseline_dir))
    return regression.compare(current_screenshots)


def set_baseline(
    screenshots: List[Dict],
    baseline_dir: str | Path
) -> int:
    """
    Set screenshots as the new baseline.

    Args:
        screenshots: List of screenshots to use as baseline
        baseline_dir: Directory to store baselines

    Returns:
        Number of baselines set
    """
    regression = VisualRegression(Path(baseline_dir))
    return regression.set_baseline(screenshots)
