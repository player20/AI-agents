"""
Agent Registry Service

Loads and manages agent configurations from agents.config.json.
Provides agent lookup, category filtering, and workflow sequencing.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, field_validator
from functools import lru_cache
import json
import logging

logger = logging.getLogger(__name__)


class AgentConfig(BaseModel):
    """Configuration for a single agent"""
    id: str = Field(description="Unique agent identifier")
    role: str = Field(description="Agent's role/title")
    goal: str = Field(description="Agent's primary goal")
    backstory: str = Field(description="Agent's background and expertise")
    default_prompt: str = Field(alias="defaultPrompt", description="Default prompt template")
    priority: int = Field(default=99, description="Execution priority (lower = earlier)")
    category: str = Field(default="Uncategorized", description="Agent category")

    # Runtime configuration
    tools: List[str] = Field(default_factory=list, description="Available tools for this agent")
    max_tokens: int = Field(default=32768, description="Max tokens for response - larger for code generation")
    temperature: float = Field(default=0.7, description="LLM temperature")

    class Config:
        populate_by_name = True

    @field_validator('backstory', mode='before')
    @classmethod
    def truncate_backstory(cls, v: str) -> str:
        """Truncate very long backstories to prevent token overflow"""
        max_length = 2000
        if len(v) > max_length:
            return v[:max_length] + "..."
        return v


class AgentRegistry:
    """
    Registry for all available agents.

    Loads agents from agents.config.json and provides:
    - Agent lookup by ID
    - Category-based filtering
    - Priority ordering
    - Workflow sequence generation
    """

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or self._find_config()
        self._agents: Dict[str, AgentConfig] = {}
        self._categories: Dict[str, List[str]] = {}
        self._version: str = "unknown"
        self._load_agents()

    def _find_config(self) -> Path:
        """Find agents.config.json - check multiple locations"""
        # Current file is in apps/api/src/services/
        current_dir = Path(__file__).parent

        candidates = [
            # Root of MultiAgentTeam
            current_dir.parent.parent.parent.parent / "agents.config.json",
            # apps/api/config
            current_dir.parent.parent / "config" / "agents.config.json",
            # apps/api
            current_dir.parent.parent / "agents.config.json",
        ]

        for path in candidates:
            if path.exists():
                logger.info(f"Found agents.config.json at: {path}")
                return path

        raise FileNotFoundError(
            f"agents.config.json not found. Searched: {[str(p) for p in candidates]}"
        )

    def _load_agents(self) -> None:
        """Load agents from config file"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            self._version = config.get("version", "unknown")
            agents_data = config.get("agents", [])

            for agent_data in agents_data:
                try:
                    agent = AgentConfig(**agent_data)
                    self._agents[agent.id] = agent

                    # Index by category
                    if agent.category not in self._categories:
                        self._categories[agent.category] = []
                    self._categories[agent.category].append(agent.id)

                except Exception as e:
                    logger.warning(f"Failed to load agent {agent_data.get('id', 'unknown')}: {e}")

            logger.info(
                f"Loaded {len(self._agents)} agents from {self.config_path} "
                f"(version {self._version})"
            )

        except FileNotFoundError:
            logger.error(f"Config file not found: {self.config_path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            raise

    def get(self, agent_id: str) -> Optional[AgentConfig]:
        """Get agent by ID"""
        return self._agents.get(agent_id)

    def get_all(self) -> List[AgentConfig]:
        """Get all agents"""
        return list(self._agents.values())

    def get_by_category(self, category: str) -> List[AgentConfig]:
        """Get all agents in a category"""
        agent_ids = self._categories.get(category, [])
        return [self._agents[aid] for aid in agent_ids if aid in self._agents]

    def get_categories(self) -> List[str]:
        """Get list of all categories"""
        return list(self._categories.keys())

    def get_ordered_by_priority(self) -> List[AgentConfig]:
        """Get all agents ordered by priority (lowest first)"""
        return sorted(self._agents.values(), key=lambda a: a.priority)

    def get_workflow_agents(self, agent_ids: List[str]) -> List[AgentConfig]:
        """
        Get agents for a workflow in the specified order.

        Args:
            agent_ids: List of agent IDs in execution order

        Returns:
            List of AgentConfig objects in order
        """
        agents = []
        for agent_id in agent_ids:
            agent = self.get(agent_id)
            if agent:
                agents.append(agent)
            else:
                logger.warning(f"Agent not found in registry: {agent_id}")
        return agents

    def search(self, query: str) -> List[AgentConfig]:
        """Search agents by role, goal, or category"""
        query_lower = query.lower()
        results = []

        for agent in self._agents.values():
            if (query_lower in agent.role.lower() or
                query_lower in agent.goal.lower() or
                query_lower in agent.category.lower() or
                query_lower in agent.id.lower()):
                results.append(agent)

        return results

    def to_dict(self) -> Dict[str, Any]:
        """Export registry as dictionary"""
        return {
            "version": self._version,
            "total_agents": len(self._agents),
            "categories": {
                cat: len(ids) for cat, ids in self._categories.items()
            },
            "agents": [
                {
                    "id": a.id,
                    "role": a.role,
                    "goal": a.goal,
                    "category": a.category,
                    "priority": a.priority,
                }
                for a in self.get_ordered_by_priority()
            ]
        }

    def __len__(self) -> int:
        return len(self._agents)

    def __contains__(self, agent_id: str) -> bool:
        return agent_id in self._agents

    def __iter__(self):
        return iter(self._agents.values())


# Singleton instance
_registry: Optional[AgentRegistry] = None


def get_registry() -> AgentRegistry:
    """Get the singleton registry instance"""
    global _registry
    if _registry is None:
        _registry = AgentRegistry()
    return _registry


def reload_registry() -> AgentRegistry:
    """Force reload of the registry"""
    global _registry
    _registry = AgentRegistry()
    return _registry


# Convenience functions
def get_agent(agent_id: str) -> Optional[AgentConfig]:
    """Get an agent by ID"""
    return get_registry().get(agent_id)


def list_agents() -> List[Dict[str, Any]]:
    """List all agents as dictionaries (for API responses)"""
    registry = get_registry()
    return [
        {
            "id": agent.id,
            "role": agent.role,
            "goal": agent.goal,
            "category": agent.category,
            "priority": agent.priority,
        }
        for agent in registry.get_ordered_by_priority()
    ]


def get_agents_by_category(category: str) -> List[AgentConfig]:
    """Get agents by category"""
    return get_registry().get_by_category(category)
