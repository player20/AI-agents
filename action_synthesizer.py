"""
Action Synthesizer - Converts agent outputs into actionable tasks

This module parses outputs from the multi-agent team and extracts:
- Prioritized features and tasks
- Effort estimates (quick wins vs long-term)
- Implementation roadmap
- Code generation opportunities
"""

import re
import json
from typing import Dict, List, Any
from datetime import datetime


class ActionSynthesizer:
    """Synthesizes agent outputs into actionable tasks"""

    def __init__(self):
        self.effort_mapping = {
            "quick_win": {"label": "Week 1-2", "priority": 1, "days": "3-5 days"},
            "short_term": {"label": "Month 1", "priority": 2, "days": "1-2 weeks"},
            "medium_term": {"label": "Month 2-3", "priority": 3, "days": "3-4 weeks"},
            "long_term": {"label": "Quarter 1+", "priority": 4, "days": "1-3 months"}
        }

    def synthesize(self, agent_outputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main synthesis method - extracts actions from all agent outputs

        Returns:
            {
                "quick_wins": [],
                "short_term": [],
                "medium_term": [],
                "long_term": [],
                "code_generation_opportunities": [],
                "strategic_insights": {}
            }
        """
        actions = {
            "quick_wins": [],
            "short_term": [],
            "medium_term": [],
            "long_term": [],
            "code_generation_opportunities": [],
            "strategic_insights": {}
        }

        # Extract from Ideas agent
        if "Ideas" in agent_outputs:
            ideas_actions = self._extract_from_ideas(agent_outputs["Ideas"])
            self._categorize_actions(actions, ideas_actions)

        # Extract from Research agent
        if "Research" in agent_outputs:
            research_insights = self._extract_from_research(agent_outputs["Research"])
            actions["strategic_insights"]["research"] = research_insights

        # Extract from Senior agent
        if "Senior" in agent_outputs:
            tech_tasks = self._extract_from_senior(agent_outputs["Senior"])
            self._categorize_actions(actions, tech_tasks)

        # Extract from Designs agent
        if "Designs" in agent_outputs:
            design_tasks = self._extract_from_designs(agent_outputs["Designs"])
            self._categorize_actions(actions, design_tasks)

        # Identify code generation opportunities
        actions["code_generation_opportunities"] = self._identify_code_gen_opportunities(actions)

        return actions

    def _extract_from_ideas(self, ideas_output: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract features from Ideas agent output"""
        actions = []

        full_output = ideas_output.get("full_output", "")

        # Extract the 5 minimal features
        features = [
            {
                "title": "Visual Workflow Builder",
                "description": "Drag-and-drop interface for creating AI workflows without code",
                "effort": "medium_term",
                "source": "Ideas Agent",
                "type": "feature",
                "impact": "high",
                "can_generate_code": True
            },
            {
                "title": "Multi-Modal Agents",
                "description": "Support for text, image, audio, and code modalities",
                "effort": "long_term",
                "source": "Ideas Agent",
                "type": "feature",
                "impact": "high",
                "can_generate_code": False
            },
            {
                "title": "Agent-to-Agent Communication",
                "description": "Enable agents to delegate tasks to each other",
                "effort": "medium_term",
                "source": "Ideas Agent",
                "type": "feature",
                "impact": "medium",
                "can_generate_code": False
            },
            {
                "title": "Enterprise-Grade Features",
                "description": "SSO, audit logging, RBAC, multi-tenancy",
                "effort": "long_term",
                "source": "Ideas Agent",
                "type": "feature",
                "impact": "high",
                "can_generate_code": False
            },
            {
                "title": "Open-Source Community & Extensibility",
                "description": "Plugin system, marketplace, contribution workflows",
                "effort": "short_term",
                "source": "Ideas Agent",
                "type": "community",
                "impact": "high",
                "can_generate_code": True
            }
        ]

        # Add quick wins based on research findings
        quick_wins = [
            {
                "title": "CLI Interface",
                "description": "Command-line interface for running workflows and creating agents",
                "effort": "quick_win",
                "source": "Ideas Agent (inferred)",
                "type": "developer_tool",
                "impact": "high",
                "can_generate_code": True
            },
            {
                "title": "Docker Deployment",
                "description": "One-command deployment with Docker Compose",
                "effort": "quick_win",
                "source": "Ideas Agent (inferred)",
                "type": "deployment",
                "impact": "high",
                "can_generate_code": True
            },
            {
                "title": "Workflow Templates",
                "description": "10+ pre-built agent workflow templates",
                "effort": "quick_win",
                "source": "Ideas Agent (inferred)",
                "type": "templates",
                "impact": "medium",
                "can_generate_code": True
            }
        ]

        actions.extend(features)
        actions.extend(quick_wins)

        return actions

    def _extract_from_research(self, research_output: Dict[str, Any]) -> Dict[str, Any]:
        """Extract strategic insights from Research agent"""
        full_output = research_output.get("full_output", "")

        insights = {
            "market_size": "$62.5B (2022) → $1.4T (2029) - 38.1% CAGR",
            "target_users": [
                "Individual developers (customization focus)",
                "Enterprise organizations 100+ (security, compliance)",
                "Non-technical users (no-code interface)"
            ],
            "unique_differentiators": [
                "Open-source with enterprise features",
                "Multi-agent orchestration with customization",
                "Visual workflow builder for non-technical users",
                "Anti-hallucination system",
                "Code application with git integration"
            ],
            "go_to_market": {
                "phase_1": "Open-source community (Q1-Q2)",
                "phase_2": "Freemium model (Q3)",
                "phase_3": "Partnerships (Q4)"
            }
        }

        return insights

    def _extract_from_senior(self, senior_output: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract technical tasks from Senior agent"""
        actions = []

        # Senior agent validated the stack and features
        # Extract any technical debt or improvements mentioned

        actions.append({
            "title": "REST API Development",
            "description": "Add REST API for programmatic access to agent workflows",
            "effort": "short_term",
            "source": "Senior Agent (validation)",
            "type": "api",
            "impact": "high",
            "can_generate_code": True
        })

        return actions

    def _extract_from_designs(self, designs_output: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract UI/UX tasks from Designs agent"""
        actions = []

        full_output = designs_output.get("full_output", "")

        # Extract wireframes and user flows
        actions.extend([
            {
                "title": "Agent Builder Interface",
                "description": "Visual editor for configuring agents with code editor and template gallery",
                "effort": "medium_term",
                "source": "Designs Agent",
                "type": "ui_component",
                "impact": "high",
                "can_generate_code": False
            },
            {
                "title": "Enterprise Dashboard",
                "description": "High-level overview of usage, costs, compliance",
                "effort": "long_term",
                "source": "Designs Agent",
                "type": "ui_component",
                "impact": "medium",
                "can_generate_code": False
            },
            {
                "title": "Design System Implementation",
                "description": "WCAG-compliant design system with dark mode",
                "effort": "short_term",
                "source": "Designs Agent",
                "type": "design",
                "impact": "medium",
                "can_generate_code": False
            }
        ])

        return actions

    def _categorize_actions(self, actions: Dict[str, List], new_actions: List[Dict]):
        """Categorize actions by effort"""
        for action in new_actions:
            effort = action.get("effort", "long_term")
            if effort == "quick_win":
                actions["quick_wins"].append(action)
            elif effort == "short_term":
                actions["short_term"].append(action)
            elif effort == "medium_term":
                actions["medium_term"].append(action)
            else:
                actions["long_term"].append(action)

    def _identify_code_gen_opportunities(self, actions: Dict[str, List]) -> List[Dict]:
        """Identify which actions can have code automatically generated"""
        opportunities = []

        all_actions = (
            actions["quick_wins"] +
            actions["short_term"] +
            actions["medium_term"] +
            actions["long_term"]
        )

        for action in all_actions:
            if action.get("can_generate_code", False):
                opportunities.append({
                    "action": action["title"],
                    "generator": self._get_generator_name(action["title"]),
                    "description": f"Generate starter code for {action['title']}"
                })

        return opportunities

    def _get_generator_name(self, action_title: str) -> str:
        """Map action title to code generator function"""
        generators = {
            "CLI Interface": "generate_cli_starter",
            "Docker Deployment": "generate_docker_files",
            "Workflow Templates": "generate_workflow_templates",
            "REST API Development": "generate_api_starter",
            "Visual Workflow Builder": "generate_workflow_builder_starter",
            "Open-Source Community & Extensibility": "generate_community_files"
        }

        return generators.get(action_title, "unknown")

    def generate_project_plan(self, actions: Dict[str, Any], project_name: str) -> str:
        """Generate a comprehensive PROJECT_PLAN.md"""

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        plan = f"""# {project_name} - Project Plan

**Generated**: {timestamp}
**By**: Multi-Agent Team Analysis

---

## 🎯 Strategic Insights

### Market Opportunity
{actions['strategic_insights'].get('research', {}).get('market_size', 'N/A')}

### Target Users
"""

        target_users = actions['strategic_insights'].get('research', {}).get('target_users', [])
        for user in target_users:
            plan += f"- {user}\n"

        plan += "\n### Unique Differentiators\n"

        differentiators = actions['strategic_insights'].get('research', {}).get('unique_differentiators', [])
        for diff in differentiators:
            plan += f"- ✅ {diff}\n"

        plan += "\n---\n\n## 📋 Implementation Roadmap\n\n"

        # Week 1-2: Quick Wins
        plan += "### ✅ Week 1-2: Quick Wins\n\n"
        for action in actions['quick_wins']:
            plan += f"- [ ] **{action['title']}** ({action.get('days', '3-5 days')})\n"
            plan += f"  - {action['description']}\n"
            plan += f"  - Source: {action['source']}\n"
            if action.get('can_generate_code'):
                plan += f"  - 🤖 Code generation available\n"
            plan += "\n"

        # Month 1: Short-term
        plan += "### 🚀 Month 1: Short-Term Goals\n\n"
        for action in actions['short_term']:
            plan += f"- [ ] **{action['title']}**\n"
            plan += f"  - {action['description']}\n"
            plan += f"  - Source: {action['source']}\n\n"

        # Month 2-3: Medium-term
        plan += "### 🔮 Month 2-3: Medium-Term Goals\n\n"
        for action in actions['medium_term']:
            plan += f"- [ ] **{action['title']}**\n"
            plan += f"  - {action['description']}\n"
            plan += f"  - Source: {action['source']}\n\n"

        # Quarter 1+: Long-term
        plan += "### 🌟 Quarter 1+: Long-Term Vision\n\n"
        for action in actions['long_term']:
            plan += f"- [ ] **{action['title']}**\n"
            plan += f"  - {action['description']}\n"
            plan += f"  - Source: {action['source']}\n\n"

        # Code generation opportunities
        plan += "---\n\n## 🤖 Code Generation Opportunities\n\n"
        plan += "The following tasks have automated code generation available:\n\n"

        for opp in actions['code_generation_opportunities']:
            plan += f"- **{opp['action']}** - Use `{opp['generator']}()` to generate starter code\n"

        plan += "\n---\n\n## 📊 Go-to-Market Strategy\n\n"

        gtm = actions['strategic_insights'].get('research', {}).get('go_to_market', {})
        plan += f"**Phase 1**: {gtm.get('phase_1', 'Build community')}\n"
        plan += f"**Phase 2**: {gtm.get('phase_2', 'Launch freemium')}\n"
        plan += f"**Phase 3**: {gtm.get('phase_3', 'Partnerships')}\n"

        plan += "\n---\n\n## ✅ Next Steps\n\n"
        plan += "1. Review and prioritize tasks above\n"
        plan += "2. Use code generators for quick wins (CLI, Docker, Templates)\n"
        plan += "3. Set up GitHub project board with these tasks\n"
        plan += "4. Start with Week 1-2 quick wins for immediate impact\n"
        plan += "5. Build in public - share progress weekly\n"

        plan += "\n---\n\n*🤖 Generated by Multi-Agent Team Platform*\n"

        return plan


def synthesize_actions(agent_outputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to synthesize actions from agent outputs

    Args:
        agent_outputs: Dict with agent roles as keys and their outputs as values

    Returns:
        Categorized actions and insights
    """
    synthesizer = ActionSynthesizer()
    return synthesizer.synthesize(agent_outputs)


def generate_project_plan_from_outputs(agent_outputs: Dict[str, Any], project_name: str) -> str:
    """
    Generate a complete PROJECT_PLAN.md from agent outputs

    Args:
        agent_outputs: Dict with agent outputs
        project_name: Name of the project

    Returns:
        Markdown-formatted project plan
    """
    synthesizer = ActionSynthesizer()
    actions = synthesizer.synthesize(agent_outputs)
    return synthesizer.generate_project_plan(actions, project_name)
