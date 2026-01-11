"""
Projects & Teams Storage System for Gradio

Provides persistent storage and management for projects and teams.
Includes file locking, validation, and atomic writes for production safety.
"""

import json
import uuid
import os
import html
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import threading

# File locking - cross-platform solution
try:
    import fcntl  # Unix/Linux/Mac
    HAS_FCNTL = True
except ImportError:
    HAS_FCNTL = False
    try:
        import msvcrt  # Windows
        HAS_MSVCRT = True
    except ImportError:
        HAS_MSVCRT = False

class ProjectsStore:
    """Manages projects and teams with JSON file storage

    Features:
    - Singleton pattern (one instance per storage file)
    - File locking for concurrent access safety
    - Input validation
    - Atomic writes with backup
    - HTML escaping for XSS prevention
    """

    _instances = {}  # Dictionary of instances by storage_path
    _lock = threading.Lock()

    def __new__(cls, storage_path: str = "gradio_projects.json"):
        """Implement singleton pattern - one instance per storage file"""
        storage_path = str(Path(storage_path).resolve())

        with cls._lock:
            if storage_path not in cls._instances:
                instance = super().__new__(cls)
                cls._instances[storage_path] = instance
            return cls._instances[storage_path]

    def __init__(self, storage_path: str = "gradio_projects.json"):
        # Only initialize once per instance
        if hasattr(self, '_initialized'):
            return

        self.storage_path = Path(storage_path).resolve()
        self._validate_storage_path()
        self.projects = self._load()
        self._initialized = True

    def _validate_storage_path(self):
        """Validate storage path to prevent path traversal attacks"""
        path_str = str(self.storage_path)

        # Check for path traversal attempts
        if ".." in path_str:
            raise ValueError("Path traversal detected in storage path")

        # Ensure parent directory exists
        parent = self.storage_path.parent
        if not parent.exists():
            raise ValueError(f"Parent directory does not exist: {parent}")

    def _lock_file(self, file_handle):
        """Lock file for exclusive access (cross-platform)"""
        if HAS_FCNTL:
            fcntl.flock(file_handle.fileno(), fcntl.LOCK_EX)
        elif HAS_MSVCRT:
            # Windows locking - lock 1 byte at position 0
            try:
                msvcrt.locking(file_handle.fileno(), msvcrt.LK_NBLCK, 1)
            except (OSError, PermissionError):
                # If locking fails, proceed anyway (single-user mode)
                pass
        # If neither available, proceed without locking (single-user mode)

    def _unlock_file(self, file_handle):
        """Unlock file (cross-platform)"""
        if HAS_FCNTL:
            fcntl.flock(file_handle.fileno(), fcntl.LOCK_UN)
        elif HAS_MSVCRT:
            try:
                msvcrt.locking(file_handle.fileno(), msvcrt.LK_UNLCK, 1)
            except (OSError, PermissionError):
                # Unlocking can fail if lock wasn't acquired
                pass

    def _load(self) -> Dict[str, Any]:
        """Load projects from JSON file with file locking"""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    self._lock_file(f)
                    try:
                        data = json.load(f)
                        return data
                    finally:
                        self._unlock_file(f)
            except json.JSONDecodeError as e:
                print(f"[WARNING] JSON corrupted: {e}")
                # Try to load backup
                backup_path = self.storage_path.with_suffix('.bak')
                if backup_path.exists():
                    print(f"[BACKUP] Loading backup from {backup_path}")
                    try:
                        with open(backup_path, 'r', encoding='utf-8') as f:
                            return json.load(f)
                    except Exception as backup_error:
                        print(f"[ERROR] Backup also corrupted: {backup_error}")
                return {}
            except Exception as e:
                print(f"[ERROR] Error loading projects: {e}")
                return {}
        return {}

    def _save(self):
        """Save projects to JSON file with atomic writes and backup"""
        try:
            # Create backup of existing file
            if self.storage_path.exists():
                backup_path = self.storage_path.with_suffix('.bak')
                try:
                    import shutil
                    shutil.copy2(self.storage_path, backup_path)
                except Exception as e:
                    print(f"[WARNING] Could not create backup: {e}")

            # Atomic write: write to temp file, then replace
            temp_path = self.storage_path.with_suffix('.tmp')

            with open(temp_path, 'w', encoding='utf-8') as f:
                self._lock_file(f)
                try:
                    json.dump(self.projects, f, indent=2, ensure_ascii=False)
                    f.flush()
                    os.fsync(f.fileno())  # Force write to disk
                finally:
                    self._unlock_file(f)

            # Atomic replace (POSIX guarantees atomicity)
            temp_path.replace(self.storage_path)

            # Set secure file permissions (owner read/write only)
            try:
                os.chmod(self.storage_path, 0o600)
            except Exception:
                pass  # Windows may not support chmod

        except Exception as e:
            print(f"[ERROR] Error saving projects: {e}")
            raise

    def create_project(self, name: str, description: str = "") -> str:
        """Create a new project with validation

        Args:
            name: Project name (1-200 characters, required)
            description: Project description (0-5000 characters, optional)

        Returns:
            Project ID

        Raises:
            ValueError: If validation fails
        """
        # Validate inputs
        if not name or not name.strip():
            raise ValueError("Project name cannot be empty")

        name = name.strip()
        if len(name) > 200:
            raise ValueError("Project name too long (max 200 characters)")

        if len(description) > 5000:
            raise ValueError("Description too long (max 5000 characters)")

        # Check for duplicate names (warning only)
        existing_names = [p["name"] for p in self.projects.values()]
        if name in existing_names:
            print(f"[WARNING] Warning: Project name '{name}' already exists")

        project_id = f"proj-{uuid.uuid4().hex[:8]}"
        project = {
            "id": project_id,
            "name": name,
            "description": description,
            "teams": [],
            "createdAt": datetime.now().isoformat(),
            "updatedAt": datetime.now().isoformat()
        }
        self.projects[project_id] = project
        self._save()
        return project_id

    def get_project(self, project_id: str) -> Optional[Dict]:
        """Get a project by ID"""
        return self.projects.get(project_id)

    def list_projects(self) -> List[Dict]:
        """List all projects"""
        return list(self.projects.values())

    def update_project(self, project_id: str, name: str = None, description: str = None):
        """Update project details"""
        if project_id in self.projects:
            if name is not None:
                self.projects[project_id]["name"] = name
            if description is not None:
                self.projects[project_id]["description"] = description
            self.projects[project_id]["updatedAt"] = datetime.now().isoformat()
            self._save()
            return True
        return False

    def delete_project(self, project_id: str) -> bool:
        """Delete a project"""
        if project_id in self.projects:
            del self.projects[project_id]
            self._save()
            return True
        return False

    def add_team(self, project_id: str, name: str, agents: List[str], description: str = "", validate_agents: bool = True) -> Optional[str]:
        """Add a team to a project with validation

        Args:
            project_id: ID of the project
            name: Team name (1-200 characters, required)
            agents: List of agent IDs (1-50 agents)
            description: Team description (0-1000 characters, optional)
            validate_agents: Whether to validate agent IDs against agents.config.json

        Returns:
            Team ID, or None if project doesn't exist

        Raises:
            ValueError: If validation fails
        """
        if project_id not in self.projects:
            return None

        # Validate team name
        if not name or not name.strip():
            raise ValueError("Team name cannot be empty")

        name = name.strip()
        if len(name) > 200:
            raise ValueError("Team name too long (max 200 characters)")

        if len(description) > 1000:
            raise ValueError("Description too long (max 1000 characters)")

        # Validate agents list
        if not agents or len(agents) == 0:
            raise ValueError("Team must have at least one agent")

        if len(agents) > 50:
            raise ValueError("Too many agents (max 50 per team)")

        # Validate agent IDs if requested
        if validate_agents:
            valid_agents = get_all_agent_ids()
            invalid_agents = [a for a in agents if a not in valid_agents]
            if invalid_agents:
                raise ValueError(f"Invalid agent IDs: {', '.join(invalid_agents)}")

        # Warning for large teams
        if len(agents) > 20:
            print(f"[WARNING] Warning: Team '{name}' has {len(agents)} agents - execution may take hours")

        team_id = f"team-{uuid.uuid4().hex[:8]}"
        team = {
            "id": team_id,
            "name": name,
            "description": description,
            "agents": agents,
            "status": "pending",
            "output": None,
            "enabled": True,  # Teams are enabled by default
            "createdAt": datetime.now().isoformat()
        }

        self.projects[project_id]["teams"].append(team)
        self.projects[project_id]["updatedAt"] = datetime.now().isoformat()
        self._save()
        return team_id

    def get_team(self, project_id: str, team_id: str) -> Optional[Dict]:
        """Get a team by ID"""
        project = self.get_project(project_id)
        if project:
            for team in project["teams"]:
                if team["id"] == team_id:
                    return team
        return None

    def update_team_status(self, project_id: str, team_id: str, status: str, output: str = None):
        """Update team execution status"""
        project = self.get_project(project_id)
        if project:
            for team in project["teams"]:
                if team["id"] == team_id:
                    team["status"] = status
                    if output is not None:
                        team["output"] = output
                    team["updatedAt"] = datetime.now().isoformat()
                    self._save()
                    return True
        return False

    def delete_team(self, project_id: str, team_id: str) -> bool:
        """Delete a team from a project"""
        project = self.get_project(project_id)
        if project:
            initial_len = len(project["teams"])
            project["teams"] = [t for t in project["teams"] if t["id"] != team_id]
            if len(project["teams"]) < initial_len:
                self.projects[project_id]["updatedAt"] = datetime.now().isoformat()
                self._save()
                return True
        return False

    def toggle_team_enabled(self, project_id: str, team_id: str) -> bool:
        """Toggle a team's enabled/disabled status

        Args:
            project_id: ID of the project
            team_id: ID of the team to toggle

        Returns:
            New enabled status (True/False), or None if team not found
        """
        team = self.get_team(project_id, team_id)
        if team:
            # Toggle the enabled status
            new_status = not team.get("enabled", True)
            team["enabled"] = new_status

            # Update project
            self.projects[project_id]["updatedAt"] = datetime.now().isoformat()
            self._save()
            return new_status
        return None

    def get_previous_teams_output(self, project_id: str, current_team_index: int) -> List[Dict]:
        """Get outputs from all previous teams for context"""
        project = self.get_project(project_id)
        if not project or current_team_index == 0:
            return []

        previous_outputs = []
        for i in range(current_team_index):
            team = project["teams"][i]
            if team.get("output"):
                previous_outputs.append({
                    "teamName": team["name"],
                    "output": team["output"]
                })

        return previous_outputs


# Team Presets - Pre-configured teams for common specializations
TEAM_PRESETS = {
    "Market Analysis Team": {
        "description": "Analyze market opportunities, competitors, and business strategy",
        "agents": ["Research", "BusinessAnalyst", "DataAnalyst", "ProductOwner", "FinancialAnalyst"],
        "category": "Business & Strategy"
    },
    "Design Evaluation Team": {
        "description": "Review and evaluate design quality, UX, and accessibility",
        "agents": ["ProductDesigner", "UXResearcher", "UIDesigner", "AccessibilitySpecialist", "Designs"],
        "category": "Product & Design"
    },
    "Backend Development Team": {
        "description": "Build server-side APIs, databases, and backend systems",
        "agents": ["Senior", "BackendEngineer", "DatabaseAdmin", "APIDesigner", "Architect"],
        "category": "Engineering"
    },
    "Frontend Development Team": {
        "description": "Build responsive web interfaces and user experiences",
        "agents": ["FrontendEngineer", "Web", "UIDesigner", "Designs", "AccessibilitySpecialist"],
        "category": "Engineering"
    },
    "Mobile Development Team": {
        "description": "Build native iOS and Android mobile applications",
        "agents": ["iOS", "Android", "MobileEngineer", "UIDesigner", "ProductDesigner"],
        "category": "Engineering"
    },
    "QA & Testing Team": {
        "description": "Comprehensive testing, quality assurance, and verification",
        "agents": ["QA", "TestAutomation", "Verifier", "PerformanceEngineer"],
        "category": "Quality Assurance"
    },
    "Security Team": {
        "description": "Security audits, penetration testing, and compliance",
        "agents": ["SecurityEngineer", "PenetrationTester", "ComplianceOfficer", "Verifier"],
        "category": "Security & Compliance"
    },
    "Data & AI Team": {
        "description": "Data science, machine learning, and AI implementation",
        "agents": ["DataScientist", "MLEngineer", "AIResearcher", "DataEngineer", "DataAnalyst"],
        "category": "Data & AI"
    },
    "Content & Marketing Team": {
        "description": "Content creation, marketing strategy, and growth",
        "agents": ["ContentWriter", "SocialMediaManager", "GrowthEngineer", "TechnicalWriter"],
        "category": "Content & Communication"
    },
    "Research Team": {
        "description": "Deep research, ideation, and strategic planning",
        "agents": ["Research", "AIResearcher", "Ideas", "TechLead"],
        "category": "Research & Strategy"
    },
    "DevOps & Infrastructure Team": {
        "description": "Infrastructure, deployment, monitoring, and site reliability",
        "agents": ["DevOps", "SRE", "InfrastructureEngineer", "CloudArchitect"],
        "category": "Engineering"
    },
    "Product Management Team": {
        "description": "Product strategy, roadmap planning, and team coordination",
        "agents": ["PM", "ProductOwner", "BusinessAnalyst", "Memory"],
        "category": "Management"
    },
    "Full-Stack Team": {
        "description": "End-to-end development with frontend, backend, and deployment",
        "agents": ["FullStackEngineer", "Senior", "Web", "DatabaseAdmin", "DevOps"],
        "category": "Engineering"
    },
    "Architecture Team": {
        "description": "System architecture, technical leadership, and design patterns",
        "agents": ["Architect", "TechLead", "Senior", "CloudArchitect"],
        "category": "Engineering"
    },
    "Documentation Team": {
        "description": "Technical writing, API docs, and developer advocacy",
        "agents": ["TechnicalWriter", "DocumentationEngineer", "DeveloperAdvocate"],
        "category": "Content & Communication"
    },
    "Performance & Optimization Team": {
        "description": "Performance tuning, optimization, and scalability",
        "agents": ["PerformanceEngineer", "SRE", "Architect", "Senior"],
        "category": "Engineering"
    },
    "Blockchain Team": {
        "description": "Blockchain development, smart contracts, and Web3",
        "agents": ["BlockchainEngineer", "SecurityEngineer", "FullStackEngineer"],
        "category": "Engineering"
    },
    "Legal & Compliance Team": {
        "description": "Legal review, compliance, and regulatory requirements",
        "agents": ["ComplianceOfficer", "LegalAdvisor", "SecurityEngineer"],
        "category": "Security & Compliance"
    }
}


# Project Templates
PROJECT_TEMPLATES = {
    "E-commerce Platform": {
        "description": "Build a complete e-commerce platform with user auth, product catalog, shopping cart, and checkout",
        "teams": [
            {
                "name": "Backend Squad",
                "description": "Build backend API and database",
                "agents": ["PM", "Research", "Senior", "BackendEngineer", "DatabaseAdmin", "SecurityEngineer"]
            },
            {
                "name": "Frontend Squad",
                "description": "Build responsive user interface",
                "agents": ["Designs", "FrontendEngineer", "AccessibilitySpecialist", "UIDesigner"]
            },
            {
                "name": "QA & Launch",
                "description": "Test and deploy",
                "agents": ["QA", "TestAutomation", "DevOps", "Verifier"]
            }
        ]
    },
    "Mobile App": {
        "description": "Build native mobile app for iOS and Android",
        "teams": [
            {
                "name": "Planning & Design",
                "description": "Define product and design UX",
                "agents": ["PM", "ProductOwner", "Research", "Ideas", "ProductDesigner", "UXResearcher"]
            },
            {
                "name": "Development",
                "description": "Build iOS and Android apps",
                "agents": ["Senior", "iOS", "Android", "MobileEngineer", "BackendEngineer"]
            },
            {
                "name": "Quality & Release",
                "description": "Test and deploy to app stores",
                "agents": ["QA", "TestAutomation", "PerformanceEngineer", "DevOps"]
            }
        ]
    },
    "SaaS Product": {
        "description": "Build a SaaS product from scratch",
        "teams": [
            {
                "name": "Product Strategy",
                "description": "Market research and product planning",
                "agents": ["PM", "Research", "ProductOwner", "BusinessAnalyst", "FinancialAnalyst"]
            },
            {
                "name": "MVP Development",
                "description": "Build minimum viable product",
                "agents": ["Architect", "FullStackEngineer", "ProductDesigner", "DevOps"]
            },
            {
                "name": "Growth & Scale",
                "description": "Optimize and grow",
                "agents": ["GrowthEngineer", "DataAnalyst", "PerformanceEngineer", "SRE"]
            }
        ]
    },
    "AI/ML Project": {
        "description": "Build an AI/ML powered application",
        "teams": [
            {
                "name": "Research & Data",
                "description": "Research ML approaches and prepare data",
                "agents": ["AIResearcher", "DataScientist", "DataEngineer", "Research"]
            },
            {
                "name": "Model Development",
                "description": "Train and optimize models",
                "agents": ["MLEngineer", "DataScientist", "PerformanceEngineer"]
            },
            {
                "name": "Deployment",
                "description": "Deploy ML models to production",
                "agents": ["MLEngineer", "BackendEngineer", "DevOps", "SRE"]
            }
        ]
    },
    "API Platform": {
        "description": "Build a developer-facing API platform",
        "teams": [
            {
                "name": "API Design",
                "description": "Design API architecture and specs",
                "agents": ["Architect", "APIDesigner", "Senior", "SecurityEngineer"]
            },
            {
                "name": "Implementation",
                "description": "Build API services",
                "agents": ["BackendEngineer", "DatabaseAdmin", "InfrastructureEngineer"]
            },
            {
                "name": "Developer Experience",
                "description": "Documentation and SDKs",
                "agents": ["TechnicalWriter", "DeveloperAdvocate", "DocumentationEngineer"]
            }
        ]
    },
    "Blockchain DApp": {
        "description": "Build a decentralized application",
        "teams": [
            {
                "name": "Smart Contracts",
                "description": "Design and develop smart contracts",
                "agents": ["BlockchainEngineer", "SecurityEngineer", "PenetrationTester"]
            },
            {
                "name": "Frontend",
                "description": "Build Web3 user interface",
                "agents": ["ProductDesigner", "FrontendEngineer", "Web"]
            },
            {
                "name": "Testing & Audit",
                "description": "Security audit and testing",
                "agents": ["SecurityEngineer", "PenetrationTester", "QA", "Verifier"]
            }
        ]
    }
}


def get_template_names() -> List[str]:
    """Get list of available template names"""
    return list(PROJECT_TEMPLATES.keys())


def get_template(template_name: str) -> Optional[Dict]:
    """Get a template by name"""
    return PROJECT_TEMPLATES.get(template_name)


def get_team_preset_names() -> List[str]:
    """Get list of available team preset names"""
    return list(TEAM_PRESETS.keys())


def get_team_preset(preset_name: str) -> Optional[Dict]:
    """Get a team preset by name

    Returns:
        Dict with keys: description, agents, category
    """
    return TEAM_PRESETS.get(preset_name)


def get_team_presets_by_category() -> Dict[str, List[str]]:
    """Group team presets by category for organized display

    Returns:
        Dict mapping category names to lists of preset names
    """
    categories = {}
    for preset_name, preset_data in TEAM_PRESETS.items():
        category = preset_data.get("category", "Other")
        if category not in categories:
            categories[category] = []
        categories[category].append(preset_name)

    # Sort categories and preset names
    return {cat: sorted(presets) for cat, presets in sorted(categories.items())}


def get_all_agent_ids() -> List[str]:
    """Get list of all valid agent IDs from agents.config.json

    Returns:
        List of agent IDs, or empty list if config not found
    """
    try:
        import json
        config_path = Path(__file__).parent / "agents.config.json"
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return [agent["id"] for agent in config.get("agents", [])]
    except Exception as e:
        print(f"[WARNING] Warning: Could not load agents.config.json: {e}")

    # Fallback: return common agent IDs if config not available
    return ["PM", "Research", "Senior", "Architect", "Designs", "Web",
            "BackendEngineer", "FrontendEngineer", "QA", "DevOps", "Verifier"]


def escape_html(text: str) -> str:
    """Escape HTML to prevent XSS attacks

    Args:
        text: Input text that may contain HTML

    Returns:
        HTML-escaped text safe for rendering

    Example:
        >>> escape_html("<script>alert('XSS')</script>")
        "&lt;script&gt;alert('XSS')&lt;/script&gt;"
    """
    return html.escape(text)


def render_team_card_safe(team: Dict, index: int = 0) -> str:
    """Render a team card with HTML escaping for XSS prevention

    Args:
        team: Team dictionary with id, name, description, agents, status, enabled
        index: Team index number (for display)

    Returns:
        HTML string with properly escaped user content
    """
    status_colors = {
        "pending": "#gray",
        "running": "#3498db",
        "completed": "#27ae60",
        "failed": "#e74c3c"
    }
    color = status_colors.get(team.get("status", "pending"), "#gray")

    # Check if team is enabled/disabled
    is_enabled = team.get("enabled", True)
    enabled_badge = "ENABLED" if is_enabled else "DISABLED"
    enabled_color = "#27ae60" if is_enabled else "#95a5a6"
    opacity = "1.0" if is_enabled else "0.6"

    # Escape all user-provided content
    safe_name = escape_html(team.get("name", "Unnamed Team"))
    safe_desc = escape_html(team.get("description", ""))
    safe_agents = escape_html(", ".join(team.get("agents", [])))
    safe_status = escape_html(team.get("status", "pending").upper())

    return f"""
    <div style="border-left: 4px solid {color}; padding: 12px; margin: 8px 0; background: #f9f9f9; border-radius: 4px; opacity: {opacity};">
        <h4 style="margin: 0 0 8px 0;">
            {index + 1}. {safe_name}
            <span style="float: right; font-size: 12px; color: {color};">{safe_status}</span>
        </h4>
        <p style="margin: 4px 0; font-size: 13px; color: #666;">{safe_desc}</p>
        <p style="margin: 4px 0; font-size: 12px;">
            <strong>Agents:</strong> {safe_agents}
        </p>
        <p style="margin: 4px 0; font-size: 11px;">
            <span style="background: {enabled_color}; color: white; padding: 2px 8px; border-radius: 10px; font-weight: bold;">
                {enabled_badge}
            </span>
        </p>
    </div>
    """
