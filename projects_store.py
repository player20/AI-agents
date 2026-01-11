"""
Projects & Teams Storage System for Gradio

Provides persistent storage and management for projects and teams.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

class ProjectsStore:
    """Manages projects and teams with JSON file storage"""

    def __init__(self, storage_path: str = "gradio_projects.json"):
        self.storage_path = Path(storage_path)
        self.projects = self._load()

    def _load(self) -> Dict[str, Any]:
        """Load projects from JSON file"""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading projects: {e}")
                return {}
        return {}

    def _save(self):
        """Save projects to JSON file"""
        try:
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(self.projects, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving projects: {e}")

    def create_project(self, name: str, description: str = "") -> str:
        """Create a new project"""
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

    def add_team(self, project_id: str, name: str, agents: List[str], description: str = "") -> Optional[str]:
        """Add a team to a project"""
        if project_id not in self.projects:
            return None

        team_id = f"team-{uuid.uuid4().hex[:8]}"
        team = {
            "id": team_id,
            "name": name,
            "description": description,
            "agents": agents,
            "status": "pending",
            "output": None,
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
