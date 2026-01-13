"""
Meta Prompt System for Dynamic Agent Adaptation

Extracts context from user input and dynamically injects specialized expertise
into agent backstories, making them domain-aware for the specific task.
"""

import json
import os
from typing import Dict, Any, Optional, List
from anthropic import Anthropic

# Optional DSPy for prompt optimization
try:
    import dspy
    DSPY_AVAILABLE = True
except ImportError:
    DSPY_AVAILABLE = False


class MetaPromptEngine:
    """
    Analyzes user input and adapts agent backstories with specialized context
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize with Anthropic API"""
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")

        self.client = Anthropic(api_key=self.api_key)

    def extract_context(self, user_input: str, temperature: float = 0.0) -> Dict[str, Any]:
        """
        Extract structured context from user input

        Args:
            user_input: Raw user description (1-2 sentences)
            temperature: Model temperature (0.0 for consistency)

        Returns:
            Dict with extracted context: industry, domain, key_features, pain_points, etc.
        """

        system_prompt = """You are a context extraction specialist. Analyze the user's project description and extract structured information.

Your task:
1. Identify the industry/domain (e.g., "green tech sharing economy", "healthcare", "e-commerce", "fintech")
2. Extract key features mentioned or implied
3. Identify pain points or challenges (if mentioned)
4. Determine user personas/roles involved
5. Note any specific technologies or platforms mentioned

Output ONLY valid JSON with this structure:
{
  "industry": "string - primary industry/domain",
  "domain_details": "string - specific niche or focus area",
  "key_features": ["feature1", "feature2"],
  "pain_points": ["pain1", "pain2"],
  "user_personas": ["persona1", "persona2"],
  "technologies_mentioned": ["tech1", "tech2"],
  "business_model": "string - if identifiable (e.g., marketplace, SaaS, on-demand)",
  "clarity_score": 1-10 (how clear is the description)
}

If information is unclear, use empty arrays or "unknown". Never hallucinate details not in the input."""

        try:
            message = self.client.messages.create(
                model="claude-3-haiku-20240307",  # Fast for meta tasks
                max_tokens=1024,
                temperature=temperature,
                system=system_prompt,
                messages=[{
                    "role": "user",
                    "content": f"Extract context from this project description:\n\n{user_input}"
                }]
            )

            # Parse JSON response
            response_text = message.content[0].text.strip()

            # Handle markdown code blocks if present
            if response_text.startswith("```json"):
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif response_text.startswith("```"):
                response_text = response_text.split("```")[1].split("```")[0].strip()

            context = json.loads(response_text)
            return context

        except Exception as e:
            print(f"⚠️ Context extraction failed: {e}")
            # Return minimal context
            return {
                "industry": "unknown",
                "domain_details": "general software",
                "key_features": [],
                "pain_points": [],
                "user_personas": [],
                "technologies_mentioned": [],
                "business_model": "unknown",
                "clarity_score": 5
            }

    def adapt_agent_backstory(
        self,
        agent_id: str,
        base_backstory: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Inject specialized expertise into agent backstory based on context

        Args:
            agent_id: Agent identifier (e.g., "PM", "Research")
            base_backstory: Original agent backstory from agents.config.json
            context: Extracted context from user input

        Returns:
            Enhanced backstory with domain-specific expertise
        """

        # Build context injection
        industry = context.get('industry', 'unknown')
        domain = context.get('domain_details', '')
        features = context.get('key_features', [])
        pain_points = context.get('pain_points', [])
        business_model = context.get('business_model', 'unknown')

        # Skip injection if context is too vague
        if context.get('clarity_score', 5) < 4 or industry == 'unknown':
            return base_backstory

        # Build specialized context string
        specialization_parts = []

        if industry and industry != 'unknown':
            specialization_parts.append(f"Specialized in {industry}")

        if domain:
            specialization_parts.append(f"with deep expertise in {domain}")

        if features:
            features_str = ", ".join(features[:3])  # Top 3
            specialization_parts.append(f"focusing on {features_str}")

        if pain_points:
            pain_str = ", ".join(pain_points[:2])  # Top 2
            specialization_parts.append(f"addressing challenges like {pain_str}")

        if business_model and business_model != 'unknown':
            specialization_parts.append(f"with {business_model} business model experience")

        # Join with proper grammar
        if not specialization_parts:
            return base_backstory

        specialization = " ".join(specialization_parts) + " for this task."

        # Inject after base backstory
        enhanced = f"{base_backstory}\n\n**Task-Specific Specialization:** {specialization}"

        return enhanced

    def request_clarification(self, user_input: str, context: Dict[str, Any]) -> str:
        """
        Generate a natural clarification question if context is unclear

        Args:
            user_input: Original user input
            context: Extracted context (with low clarity_score)

        Returns:
            Clarification question string
        """

        clarity = context.get('clarity_score', 5)

        if clarity >= 7:
            return None  # No clarification needed

        # Generic friendly question
        question = (
            "To make the agents smarter and build exactly what you need, "
            "could you tell me a bit more?\n\n"
            "For example:\n"
            "- What industry or domain is this for?\n"
            "- Who are the main users?\n"
            "- Any specific pain points or challenges to solve?\n"
            "- Key features you definitely want?\n\n"
            "Just 1-2 sentences is perfect!"
        )

        return question

    def enhance_all_agents(
        self,
        agents_config: List[Dict[str, Any]],
        user_input: str,
        additional_context: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Enhance all agent backstories with dynamic context

        Args:
            agents_config: List of agent configs from agents.config.json
            user_input: User's project description
            additional_context: Optional follow-up context from clarification

        Returns:
            Enhanced agents config with adapted backstories
        """

        # Combine inputs if clarification was provided
        combined_input = user_input
        if additional_context:
            combined_input = f"{user_input}\n\nAdditional context: {additional_context}"

        # Extract context
        context = self.extract_context(combined_input)

        # Check if clarification needed
        clarity = context.get('clarity_score', 5)
        if clarity < 6 and not additional_context:
            # Return None to signal clarification needed
            return None, context

        # Enhance each agent
        enhanced_agents = []
        for agent in agents_config:
            agent_copy = agent.copy()

            # Adapt backstory
            original_backstory = agent.get('backstory', '')
            enhanced_backstory = self.adapt_agent_backstory(
                agent['id'],
                original_backstory,
                context
            )

            agent_copy['backstory'] = enhanced_backstory
            enhanced_agents.append(agent_copy)

        return enhanced_agents, context


def test_meta_prompt():
    """Test the meta prompt system"""

    # Test case 1: Clear EV charger sharing platform
    engine = MetaPromptEngine()

    user_input = "An EV charger sharing platform where hosts list chargers and drivers book them. We're seeing 73% drop-off at profile creation."

    print("Testing context extraction...")
    context = engine.extract_context(user_input)
    print(json.dumps(context, indent=2))

    # Test backstory adaptation
    base_backstory = "Expert Project Manager with 10+ years leading software teams."
    enhanced = engine.adapt_agent_backstory("PM", base_backstory, context)
    print("\n\nEnhanced backstory:")
    print(enhanced)

    # Test clarification
    vague_input = "I want to build an app."
    context2 = engine.extract_context(vague_input)
    clarification = engine.request_clarification(vague_input, context2)
    print("\n\nClarification needed:")
    print(clarification)


if __name__ == "__main__":
    test_meta_prompt()
