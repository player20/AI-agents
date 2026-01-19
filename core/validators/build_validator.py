"""
Build Validation Module

Validates that a project can be built/compiled successfully.
"""

import subprocess
import sys
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import time

from .project_detector import ProjectType, ProjectInfo


def _get_executable(name: str) -> str:
    """Get full path to executable, handling Windows .cmd wrappers."""
    executable = shutil.which(name)
    return executable if executable else name


def _safe_run(args: List[str], cwd: str = None, **kwargs) -> subprocess.CompletedProcess:
    """
    Safely run subprocess without shell=True.
    Resolves executable paths cross-platform.
    """
    # Resolve the first argument (command) to full path
    resolved_args = [_get_executable(args[0])] + args[1:]

    # Never use shell=True
    kwargs.pop('shell', None)

    return subprocess.run(resolved_args, cwd=cwd, **kwargs)


@dataclass
class BuildResult:
    """Result of build validation."""
    status: str  # pass, fail, skip
    message: str
    build_time_ms: Optional[int] = None
    output: Optional[str] = None
    errors: Optional[str] = None
    artifacts: Optional[Dict[str, str]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "message": self.message,
            "build_time_ms": self.build_time_ms,
            "output": self.output[:1000] if self.output else None,  # Truncate
            "errors": self.errors[:1000] if self.errors else None,
            "artifacts": self.artifacts,
        }


class BuildValidator:
    """
    Validates that a project can be built successfully.

    Supports:
    - Node.js projects (npm run build)
    - Python projects (py_compile)
    - Rust projects (cargo build)
    - Go projects (go build)
    """

    # Build configurations per project type
    BUILD_CONFIGS = {
        ProjectType.REACT: {
            "command": ["npm", "run", "build"],
            "artifacts": ["build", "dist"],
            "timeout": 300,
        },
        ProjectType.VUE: {
            "command": ["npm", "run", "build"],
            "artifacts": ["dist"],
            "timeout": 300,
        },
        ProjectType.NEXTJS: {
            "command": ["npm", "run", "build"],
            "artifacts": [".next"],
            "timeout": 300,
        },
        ProjectType.NODEJS: {
            "command": ["npm", "run", "build"],
            "artifacts": ["dist", "build"],
            "timeout": 300,
            "optional": True,  # Build script may not exist
        },
        ProjectType.RUST: {
            "command": ["cargo", "build", "--release"],
            "artifacts": ["target/release"],
            "timeout": 600,
        },
        ProjectType.GO: {
            "command": ["go", "build", "."],
            "artifacts": [],
            "timeout": 120,
        },
    }

    def __init__(self):
        self.npm_installed = False

    def validate(self, project: ProjectInfo) -> BuildResult:
        """
        Validate that a project builds successfully.

        Args:
            project: ProjectInfo with project details

        Returns:
            BuildResult with build status
        """
        # Check if build is needed for this project type
        config = self.BUILD_CONFIGS.get(project.project_type)

        if not config:
            # Python and some other types don't need explicit build
            if project.project_type in [ProjectType.PYTHON, ProjectType.STREAMLIT,
                                         ProjectType.FLASK, ProjectType.DJANGO,
                                         ProjectType.FASTAPI]:
                return self._validate_python_compile(project)

            if project.project_type == ProjectType.STATIC_HTML:
                return BuildResult(
                    status="skip",
                    message="Static HTML projects don't require building"
                )

            return BuildResult(
                status="skip",
                message=f"Build validation not configured for {project.project_type.value}"
            )

        # Install dependencies first if needed
        if project.project_type in [ProjectType.REACT, ProjectType.VUE,
                                     ProjectType.NEXTJS, ProjectType.NODEJS]:
            dep_result = self._install_npm_dependencies(project.path)
            if dep_result.status == "fail":
                return dep_result

        # Run the build
        return self._run_build(project, config)

    def _validate_python_compile(self, project: ProjectInfo) -> BuildResult:
        """Validate Python files compile without errors."""
        start_time = time.time()
        errors = []

        # Find all Python files
        python_files = list(project.path.rglob("*.py"))
        exclude_dirs = {"venv", "venv312", "venv314", ".venv", "env", "__pycache__",
                        "node_modules", ".git"}
        python_files = [
            f for f in python_files
            if not any(ex in f.parts for ex in exclude_dirs)
        ]

        for py_file in python_files:
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "py_compile", str(py_file)],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode != 0:
                    errors.append(f"{py_file}: {result.stderr}")
            except subprocess.TimeoutExpired:
                errors.append(f"{py_file}: Compilation timed out")
            except Exception as e:
                errors.append(f"{py_file}: {str(e)}")

        build_time = int((time.time() - start_time) * 1000)

        if errors:
            return BuildResult(
                status="fail",
                message=f"Python compilation failed for {len(errors)} file(s)",
                build_time_ms=build_time,
                errors="\n".join(errors[:10]),  # Limit to first 10
            )

        return BuildResult(
            status="pass",
            message=f"Successfully compiled {len(python_files)} Python files",
            build_time_ms=build_time,
        )

    def _install_npm_dependencies(self, path: Path) -> BuildResult:
        """Install npm dependencies if package.json exists."""
        package_json = path / "package.json"

        if not package_json.exists():
            return BuildResult(
                status="skip",
                message="No package.json found"
            )

        node_modules = path / "node_modules"

        # Skip if already installed
        if node_modules.exists() and any(node_modules.iterdir()):
            return BuildResult(
                status="pass",
                message="Dependencies already installed"
            )

        # Check if npm is available
        if not shutil.which("npm"):
            return BuildResult(
                status="fail",
                message="npm not found in PATH"
            )

        try:
            start_time = time.time()
            result = _safe_run(
                ["npm", "install"],
                cwd=path,
                capture_output=True,
                text=True,
                timeout=300
            )
            install_time = int((time.time() - start_time) * 1000)

            if result.returncode != 0:
                return BuildResult(
                    status="fail",
                    message="npm install failed",
                    build_time_ms=install_time,
                    errors=result.stderr,
                )

            self.npm_installed = True
            return BuildResult(
                status="pass",
                message="Dependencies installed successfully",
                build_time_ms=install_time,
            )

        except subprocess.TimeoutExpired:
            return BuildResult(
                status="fail",
                message="npm install timed out after 5 minutes"
            )

    def _run_build(self, project: ProjectInfo, config: Dict[str, Any]) -> BuildResult:
        """Run the build command."""
        command = config["command"]
        timeout = config.get("timeout", 300)
        optional = config.get("optional", False)

        try:
            start_time = time.time()
            result = _safe_run(
                command,
                cwd=project.path,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            build_time = int((time.time() - start_time) * 1000)

            if result.returncode != 0:
                # Check if build script doesn't exist (optional builds)
                if optional and "missing script" in result.stderr.lower():
                    return BuildResult(
                        status="skip",
                        message="No build script defined (optional)",
                        build_time_ms=build_time,
                    )

                return BuildResult(
                    status="fail",
                    message=f"Build failed with exit code {result.returncode}",
                    build_time_ms=build_time,
                    output=result.stdout,
                    errors=result.stderr,
                )

            # Check for artifacts
            artifacts = {}
            for artifact_path in config.get("artifacts", []):
                full_path = project.path / artifact_path
                if full_path.exists():
                    if full_path.is_dir():
                        size = sum(f.stat().st_size for f in full_path.rglob("*") if f.is_file())
                        artifacts[artifact_path] = f"{size / 1024:.1f} KB"
                    else:
                        artifacts[artifact_path] = f"{full_path.stat().st_size / 1024:.1f} KB"

            return BuildResult(
                status="pass",
                message="Build completed successfully",
                build_time_ms=build_time,
                output=result.stdout,
                artifacts=artifacts if artifacts else None,
            )

        except subprocess.TimeoutExpired:
            return BuildResult(
                status="fail",
                message=f"Build timed out after {timeout} seconds"
            )
        except FileNotFoundError:
            return BuildResult(
                status="fail",
                message=f"Build command not found: {command[0]}"
            )


# Convenience function
def validate_build(project: ProjectInfo) -> BuildResult:
    """
    Validate that a project builds successfully.

    Args:
        project: ProjectInfo with project details

    Returns:
        BuildResult with build status
    """
    validator = BuildValidator()
    return validator.validate(project)
