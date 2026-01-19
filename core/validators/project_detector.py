"""
Project Type Detection Module

Auto-detects project type from directory contents to determine
which validation pipeline to use.
"""

import json
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass


class ProjectType(Enum):
    """Supported project types for validation."""
    # Python
    STREAMLIT = "streamlit"
    FLASK = "flask"
    DJANGO = "django"
    FASTAPI = "fastapi"
    PYTHON = "python"

    # JavaScript/Node
    REACT = "react"
    VUE = "vue"
    NEXTJS = "nextjs"
    NODEJS = "nodejs"

    # Other
    STATIC_HTML = "static_html"
    RUST = "rust"
    GO = "go"
    UNKNOWN = "unknown"


@dataclass
class ProjectInfo:
    """Detected project information."""
    project_type: ProjectType
    name: str
    path: Path
    entry_point: Optional[str] = None
    build_command: Optional[str] = None
    start_command: Optional[str] = None
    port: int = 8000
    dependencies: Dict[str, str] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = {}


class ProjectDetector:
    """
    Auto-detect project type from directory contents.

    Examines configuration files, dependencies, and directory structure
    to determine what type of project it is.
    """

    # Default ports for different project types
    DEFAULT_PORTS = {
        ProjectType.STREAMLIT: 8501,
        ProjectType.FLASK: 5000,
        ProjectType.DJANGO: 8000,
        ProjectType.FASTAPI: 8000,
        ProjectType.REACT: 3000,
        ProjectType.VUE: 8080,
        ProjectType.NEXTJS: 3000,
        ProjectType.NODEJS: 3000,
        ProjectType.STATIC_HTML: 8000,
    }

    # Start commands for different project types
    START_COMMANDS = {
        ProjectType.STREAMLIT: "streamlit run {entry_point}",
        ProjectType.FLASK: "flask run",
        ProjectType.DJANGO: "python manage.py runserver",
        ProjectType.FASTAPI: "uvicorn {entry_point}:app --reload",
        ProjectType.REACT: "npm start",
        ProjectType.VUE: "npm run serve",
        ProjectType.NEXTJS: "npm run dev",
        ProjectType.NODEJS: "npm start",
        ProjectType.STATIC_HTML: "python -m http.server {port}",
    }

    # Build commands for different project types
    BUILD_COMMANDS = {
        ProjectType.REACT: "npm run build",
        ProjectType.VUE: "npm run build",
        ProjectType.NEXTJS: "npm run build",
        ProjectType.NODEJS: "npm run build",
    }

    def __init__(self):
        self.detection_results = {}

    def detect(self, project_path: str | Path) -> ProjectInfo:
        """
        Detect project type from directory contents.

        Args:
            project_path: Path to the project directory

        Returns:
            ProjectInfo with detected type and configuration
        """
        path = Path(project_path).resolve()

        if not path.exists():
            raise FileNotFoundError(f"Project path not found: {path}")

        if not path.is_dir():
            raise ValueError(f"Project path must be a directory: {path}")

        # Try detection methods in order of specificity
        project_type = self._detect_type(path)
        entry_point = self._find_entry_point(path, project_type)
        dependencies = self._get_dependencies(path, project_type)
        name = self._get_project_name(path, project_type)

        port = self.DEFAULT_PORTS.get(project_type, 8000)
        start_cmd = self._get_start_command(project_type, entry_point, port)
        build_cmd = self.BUILD_COMMANDS.get(project_type)

        return ProjectInfo(
            project_type=project_type,
            name=name,
            path=path,
            entry_point=entry_point,
            build_command=build_cmd,
            start_command=start_cmd,
            port=port,
            dependencies=dependencies
        )

    def _detect_type(self, path: Path) -> ProjectType:
        """Detect project type from files present."""

        # Check for Node.js projects first
        if (path / "package.json").exists():
            return self._detect_nodejs_type(path)

        # Check for Python projects
        if self._has_python_deps(path):
            return self._detect_python_type(path)

        # Check for other project types
        if (path / "Cargo.toml").exists():
            return ProjectType.RUST

        if (path / "go.mod").exists():
            return ProjectType.GO

        # Check for static HTML
        if (path / "index.html").exists():
            return ProjectType.STATIC_HTML

        # Scan for Python files
        python_files = list(path.glob("*.py"))
        if python_files:
            return ProjectType.PYTHON

        return ProjectType.UNKNOWN

    def _detect_nodejs_type(self, path: Path) -> ProjectType:
        """Detect specific Node.js framework from package.json."""
        try:
            pkg = json.loads((path / "package.json").read_text(encoding="utf-8"))
            deps = {
                **pkg.get("dependencies", {}),
                **pkg.get("devDependencies", {})
            }

            # Check for specific frameworks
            if "next" in deps:
                return ProjectType.NEXTJS
            if "react" in deps or "react-dom" in deps:
                return ProjectType.REACT
            if "vue" in deps:
                return ProjectType.VUE

            return ProjectType.NODEJS

        except (json.JSONDecodeError, IOError):
            return ProjectType.NODEJS

    def _detect_python_type(self, path: Path) -> ProjectType:
        """Detect specific Python framework from dependencies."""
        requirements = self._read_requirements(path)
        req_lower = requirements.lower()

        # Check for specific frameworks
        if "streamlit" in req_lower:
            return ProjectType.STREAMLIT
        if "flask" in req_lower:
            return ProjectType.FLASK
        if "django" in req_lower:
            return ProjectType.DJANGO
        if "fastapi" in req_lower:
            return ProjectType.FASTAPI

        return ProjectType.PYTHON

    def _has_python_deps(self, path: Path) -> bool:
        """Check if Python dependency files exist."""
        return any([
            (path / "requirements.txt").exists(),
            (path / "pyproject.toml").exists(),
            (path / "setup.py").exists(),
            (path / "Pipfile").exists(),
        ])

    def _read_requirements(self, path: Path) -> str:
        """Read Python requirements from various files."""
        content = ""

        # Try requirements.txt
        req_file = path / "requirements.txt"
        if req_file.exists():
            content += req_file.read_text(encoding="utf-8")

        # Try pyproject.toml
        pyproject = path / "pyproject.toml"
        if pyproject.exists():
            content += pyproject.read_text(encoding="utf-8")

        return content

    def _find_entry_point(self, path: Path, project_type: ProjectType) -> Optional[str]:
        """Find the main entry point file."""

        if project_type in [ProjectType.REACT, ProjectType.VUE, ProjectType.NEXTJS, ProjectType.NODEJS]:
            # For Node.js projects, check package.json for main/entry
            try:
                pkg = json.loads((path / "package.json").read_text(encoding="utf-8"))
                if "main" in pkg:
                    return pkg["main"]
            except (json.JSONDecodeError, IOError):
                pass
            return "index.js"

        if project_type == ProjectType.STREAMLIT:
            # Look for common Streamlit entry points
            candidates = ["app.py", "main.py", "streamlit_app.py", "Home.py"]
            for candidate in candidates:
                if (path / candidate).exists():
                    return candidate
            # Search for files with st.set_page_config
            for py_file in path.glob("*.py"):
                content = py_file.read_text(encoding="utf-8", errors="ignore")
                if "st.set_page_config" in content or "streamlit" in content:
                    return py_file.name

        if project_type == ProjectType.FLASK:
            candidates = ["app.py", "main.py", "wsgi.py", "application.py"]
            for candidate in candidates:
                if (path / candidate).exists():
                    return candidate

        if project_type == ProjectType.FASTAPI:
            candidates = ["main.py", "app.py", "api.py"]
            for candidate in candidates:
                if (path / candidate).exists():
                    return candidate.replace(".py", "")

        if project_type == ProjectType.DJANGO:
            return "manage.py"

        if project_type == ProjectType.STATIC_HTML:
            return "index.html"

        # Default Python entry point
        if (path / "main.py").exists():
            return "main.py"
        if (path / "app.py").exists():
            return "app.py"

        return None

    def _get_dependencies(self, path: Path, project_type: ProjectType) -> Dict[str, str]:
        """Extract dependencies from project."""
        deps = {}

        if project_type in [ProjectType.REACT, ProjectType.VUE, ProjectType.NEXTJS, ProjectType.NODEJS]:
            try:
                pkg = json.loads((path / "package.json").read_text(encoding="utf-8"))
                deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
            except (json.JSONDecodeError, IOError):
                pass

        elif project_type in [ProjectType.STREAMLIT, ProjectType.FLASK, ProjectType.DJANGO,
                              ProjectType.FASTAPI, ProjectType.PYTHON]:
            req_file = path / "requirements.txt"
            if req_file.exists():
                for line in req_file.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if line and not line.startswith("#"):
                        # Parse package==version or package>=version
                        for sep in ["==", ">=", "<=", "~=", ">"]:
                            if sep in line:
                                name, version = line.split(sep, 1)
                                deps[name.strip()] = version.strip()
                                break
                        else:
                            deps[line] = "*"

        return deps

    def _get_project_name(self, path: Path, project_type: ProjectType) -> str:
        """Get project name from configuration or directory."""

        # Try package.json
        if (path / "package.json").exists():
            try:
                pkg = json.loads((path / "package.json").read_text(encoding="utf-8"))
                if "name" in pkg:
                    return pkg["name"]
            except (json.JSONDecodeError, IOError):
                pass

        # Try pyproject.toml
        if (path / "pyproject.toml").exists():
            try:
                content = (path / "pyproject.toml").read_text(encoding="utf-8")
                for line in content.splitlines():
                    if line.startswith("name"):
                        # Simple parsing: name = "project-name"
                        if "=" in line:
                            name = line.split("=", 1)[1].strip().strip('"\'')
                            return name
            except IOError:
                pass

        # Fall back to directory name
        return path.name

    def _get_start_command(self, project_type: ProjectType, entry_point: Optional[str], port: int) -> Optional[str]:
        """Get the command to start the project."""
        cmd_template = self.START_COMMANDS.get(project_type)
        if not cmd_template:
            return None

        return cmd_template.format(
            entry_point=entry_point or "main.py",
            port=port
        )


# Convenience function
def detect_project(path: str | Path) -> ProjectInfo:
    """
    Detect project type from directory.

    Args:
        path: Path to project directory

    Returns:
        ProjectInfo with detected type and configuration
    """
    detector = ProjectDetector()
    return detector.detect(path)
