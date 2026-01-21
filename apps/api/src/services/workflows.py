"""
Workflow Templates

Defines agent sequences for different types of code generation workflows.
Each workflow specifies which agents run and in what order.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class WorkflowType(str, Enum):
    """Available workflow types"""
    FULL_APP = "full_app"
    MVP_SPRINT = "mvp_sprint"
    CODE_REVIEW = "code_review"
    RESEARCH_ONLY = "research_only"
    FRONTEND_ONLY = "frontend_only"
    BACKEND_ONLY = "backend_only"
    MOBILE_APP = "mobile_app"
    API_DESIGN = "api_design"
    DATABASE_DESIGN = "database_design"
    SECURITY_AUDIT = "security_audit"


# Agent sequences for each workflow type
# Agent IDs must match those in agents.config.json
WORKFLOW_SEQUENCES: Dict[str, List[str]] = {
    # Full application development - all agents
    "full_app": [
        "PM",                   # Project management and requirements
        "Memory",               # Context and memory management
        "Research",             # Research and analysis
        "Ideas",                # Ideation and brainstorming
        "Designs",              # UI/UX design
        "Senior",               # Architecture and code review
        "DatabaseAdmin",        # Database design
        "BackendEngineer",      # Backend implementation
        "FrontendEngineer",     # Frontend implementation
        "QA",                   # Quality assurance
        "SecurityEngineer",     # Security review
        "DevOps",               # Deployment and infrastructure
        "Verifier",             # Final verification
    ],

    # MVP sprint - quick prototype
    "mvp_sprint": [
        "PM",
        "Ideas",
        "Designs",
        "FullStackEngineer",
        "QA",
        "Verifier",
    ],

    # Code review workflow
    "code_review": [
        "Senior",
        "QA",
        "SecurityEngineer",
        "Verifier",
    ],

    # Research only - no code generation
    "research_only": [
        "Research",
        "Ideas",
        "Verifier",
    ],

    # Frontend-focused development
    "frontend_only": [
        "PM",
        "Designs",
        "FrontendEngineer",
        "QA",
        "Verifier",
    ],

    # Backend-focused development
    "backend_only": [
        "PM",
        "DatabaseAdmin",
        "BackendEngineer",
        "QA",
        "SecurityEngineer",
        "Verifier",
    ],

    # Mobile app development
    "mobile_app": [
        "PM",
        "Research",
        "Ideas",
        "Designs",
        "Senior",
        "iOS",                  # iOS specialist
        "Android",              # Android specialist
        "QA",
        "Verifier",
    ],

    # API design workflow
    "api_design": [
        "PM",
        "Research",
        "Senior",
        "DatabaseAdmin",
        "BackendEngineer",
        "QA",
        "Verifier",
    ],

    # Database design workflow
    "database_design": [
        "PM",
        "Research",
        "DatabaseAdmin",
        "Senior",
        "Verifier",
    ],

    # Security audit workflow
    "security_audit": [
        "SecurityEngineer",
        "Senior",
        "QA",
        "Verifier",
    ],
}


class WorkflowConfig(BaseModel):
    """Configuration for a workflow"""
    type: WorkflowType = Field(description="Workflow type")
    name: str = Field(description="Display name")
    description: str = Field(description="Workflow description")
    agent_ids: List[str] = Field(description="Ordered list of agent IDs")
    estimated_duration_minutes: int = Field(default=30, description="Estimated time")
    parallel_groups: Optional[List[List[str]]] = Field(
        default=None,
        description="Groups of agents that can run in parallel"
    )


# Workflow metadata
WORKFLOW_CONFIGS: Dict[str, WorkflowConfig] = {
    "full_app": WorkflowConfig(
        type=WorkflowType.FULL_APP,
        name="Full Application",
        description="Complete application development with all specialized agents",
        agent_ids=WORKFLOW_SEQUENCES["full_app"],
        estimated_duration_minutes=40,  # Reduced from 60 with better parallelization
        parallel_groups=[
            ["Research", "Memory"],  # Can run together (context gathering)
            ["Ideas", "Designs"],  # Can run together (independent creative tasks)
            ["BackendEngineer", "FrontendEngineer"],  # Can run together (code generation)
            ["QA", "SecurityEngineer"],  # Can run together (code review)
        ]
    ),
    "mvp_sprint": WorkflowConfig(
        type=WorkflowType.MVP_SPRINT,
        name="MVP Sprint",
        description="Quick prototype with essential agents only",
        agent_ids=WORKFLOW_SEQUENCES["mvp_sprint"],
        estimated_duration_minutes=12,  # Reduced from 20 with parallelization
        parallel_groups=[
            ["Ideas", "Designs"],  # Can run together
        ]
    ),
    "code_review": WorkflowConfig(
        type=WorkflowType.CODE_REVIEW,
        name="Code Review",
        description="Review existing code for quality and security",
        agent_ids=WORKFLOW_SEQUENCES["code_review"],
        estimated_duration_minutes=10,  # Reduced with parallelization
        parallel_groups=[
            ["QA", "SecurityEngineer"],  # Can run together
        ]
    ),
    "research_only": WorkflowConfig(
        type=WorkflowType.RESEARCH_ONLY,
        name="Research Only",
        description="Research and ideation without code generation",
        agent_ids=WORKFLOW_SEQUENCES["research_only"],
        estimated_duration_minutes=10,
    ),
    "frontend_only": WorkflowConfig(
        type=WorkflowType.FRONTEND_ONLY,
        name="Frontend Only",
        description="Frontend development with UI/UX focus",
        agent_ids=WORKFLOW_SEQUENCES["frontend_only"],
        estimated_duration_minutes=25,
    ),
    "backend_only": WorkflowConfig(
        type=WorkflowType.BACKEND_ONLY,
        name="Backend Only",
        description="Backend and API development",
        agent_ids=WORKFLOW_SEQUENCES["backend_only"],
        estimated_duration_minutes=20,  # Reduced with parallelization
        parallel_groups=[
            ["QA", "SecurityEngineer"],  # Can run together
        ]
    ),
    "mobile_app": WorkflowConfig(
        type=WorkflowType.MOBILE_APP,
        name="Mobile Application",
        description="iOS and Android mobile app development",
        agent_ids=WORKFLOW_SEQUENCES["mobile_app"],
        estimated_duration_minutes=30,  # Reduced with better parallelization
        parallel_groups=[
            ["Ideas", "Designs"],  # Can run together
            ["iOS", "Android"],  # Can develop both platforms together
        ]
    ),
    "api_design": WorkflowConfig(
        type=WorkflowType.API_DESIGN,
        name="API Design",
        description="RESTful API design and implementation",
        agent_ids=WORKFLOW_SEQUENCES["api_design"],
        estimated_duration_minutes=25,
    ),
    "database_design": WorkflowConfig(
        type=WorkflowType.DATABASE_DESIGN,
        name="Database Design",
        description="Database schema and architecture design",
        agent_ids=WORKFLOW_SEQUENCES["database_design"],
        estimated_duration_minutes=20,
    ),
    "security_audit": WorkflowConfig(
        type=WorkflowType.SECURITY_AUDIT,
        name="Security Audit",
        description="Security analysis and vulnerability assessment",
        agent_ids=WORKFLOW_SEQUENCES["security_audit"],
        estimated_duration_minutes=15,
    ),
}


class WorkflowManager:
    """
    Manages workflow templates and selection.

    Provides workflow lookup, validation, and agent sequence retrieval.
    """

    def __init__(self):
        self._workflows = WORKFLOW_CONFIGS
        self._sequences = WORKFLOW_SEQUENCES

    def get_workflow(self, workflow_type: str) -> Optional[WorkflowConfig]:
        """Get workflow configuration by type"""
        return self._workflows.get(workflow_type)

    def get_sequence(self, workflow_type: str) -> List[str]:
        """Get agent sequence for a workflow type"""
        return self._sequences.get(workflow_type, [])

    def list_workflows(self) -> List[Dict[str, Any]]:
        """List all available workflows"""
        return [
            {
                "type": config.type.value,
                "name": config.name,
                "description": config.description,
                "agent_count": len(config.agent_ids),
                "estimated_minutes": config.estimated_duration_minutes,
            }
            for config in self._workflows.values()
        ]

    def get_recommended_workflow(self, description: str, platform: str) -> str:
        """
        Recommend a workflow based on project description and platform.

        Args:
            description: Project description
            platform: Target platform (web, ios, android, mobile, api)

        Returns:
            Recommended workflow type
        """
        description_lower = description.lower()
        platform_lower = platform.lower()

        # Platform-based recommendations
        if platform_lower in ["ios", "android"]:
            return "mobile_app"
        if platform_lower == "mobile":
            return "mobile_app"
        if platform_lower == "api":
            return "api_design"

        # Description-based recommendations
        if any(word in description_lower for word in ["review", "audit", "check"]):
            if "security" in description_lower:
                return "security_audit"
            return "code_review"

        if any(word in description_lower for word in ["research", "analyze", "study"]):
            return "research_only"

        if any(word in description_lower for word in ["mvp", "prototype", "quick", "simple"]):
            return "mvp_sprint"

        if any(word in description_lower for word in ["frontend", "ui", "interface", "design"]):
            if "backend" not in description_lower and "api" not in description_lower:
                return "frontend_only"

        if any(word in description_lower for word in ["backend", "server", "api"]):
            if "frontend" not in description_lower and "ui" not in description_lower:
                return "backend_only"

        if any(word in description_lower for word in ["database", "schema", "sql", "data model"]):
            return "database_design"

        # Default to mvp_sprint for faster generation (6 agents vs 13)
        # Use "full_app" keyword in description for comprehensive 13-agent workflow
        if "full_app" in description_lower or "comprehensive" in description_lower:
            return "full_app"

        return "mvp_sprint"

    def validate_workflow(self, workflow_type: str, agent_registry) -> Dict[str, Any]:
        """
        Validate that all agents in a workflow exist in the registry.

        Args:
            workflow_type: Workflow type to validate
            agent_registry: AgentRegistry instance

        Returns:
            Validation result with missing agents if any
        """
        sequence = self.get_sequence(workflow_type)
        if not sequence:
            return {
                "valid": False,
                "error": f"Unknown workflow type: {workflow_type}",
                "missing_agents": [],
            }

        missing = []
        for agent_id in sequence:
            if agent_id not in agent_registry:
                missing.append(agent_id)

        return {
            "valid": len(missing) == 0,
            "workflow_type": workflow_type,
            "total_agents": len(sequence),
            "missing_agents": missing,
        }


# Singleton instance
_workflow_manager: Optional[WorkflowManager] = None


def get_workflow_manager() -> WorkflowManager:
    """Get the singleton workflow manager instance"""
    global _workflow_manager
    if _workflow_manager is None:
        _workflow_manager = WorkflowManager()
    return _workflow_manager


# Convenience functions
def get_workflow(workflow_type: str) -> Optional[WorkflowConfig]:
    """Get workflow configuration by type"""
    return get_workflow_manager().get_workflow(workflow_type)


def get_workflow_sequence(workflow_type: str) -> List[str]:
    """Get agent sequence for a workflow"""
    return get_workflow_manager().get_sequence(workflow_type)


def list_workflows() -> List[Dict[str, Any]]:
    """List all available workflows"""
    return get_workflow_manager().list_workflows()


def recommend_workflow(description: str, platform: str) -> str:
    """Get recommended workflow for a project"""
    return get_workflow_manager().get_recommended_workflow(description, platform)
