import gradio as gr
from crewai import Agent, Task, Crew, Process
from crewai.llm import LLM  # Explicit provider
import json
import os
import git  # pip install gitpython
from datetime import datetime
import time  # Rate limit delay
import csv
from pathlib import Path

# Import Projects & Teams storage system
from projects_store import (
    ProjectsStore,
    get_template_names,
    get_template,
    get_team_preset_names,
    get_team_preset,
    get_team_presets_by_category,
    render_team_card_safe,
    escape_html
)

# Note: toggle_team_enabled is a method on ProjectsStore instance

# Import code application system
try:
    from code_applicator import apply_agent_changes_workflow, apply_agent_changes_from_github
    CODE_APPLICATOR_AVAILABLE = True
except ImportError:
    CODE_APPLICATOR_AVAILABLE = False
    print("⚠️  Code applicator not available. Install code_applicator.py for auto-apply features.")

# Import YAML workflow parser
try:
    from workflow_yaml_parser import (
        parse_workflow_yaml,
        validate_workflow,
        format_import_summary
    )
    YAML_PARSER_AVAILABLE = True
except ImportError:
    YAML_PARSER_AVAILABLE = False
    print("⚠️  YAML parser not available. Install workflow_yaml_parser.py for workflow import.")

# Import workflow visualization
try:
    from workflow_visualization import (
        generate_workflow_graph,
        generate_execution_status_legend
    )
    WORKFLOW_VIZ_AVAILABLE = True
except ImportError:
    WORKFLOW_VIZ_AVAILABLE = False
    print("⚠️  Workflow visualization not available. Install workflow_visualization.py for visual graphs.")

# ==============================
# CONFIGURATION
# ==============================
# SECURITY: API key should be set as environment variable only
# Set in terminal: set ANTHROPIC_API_KEY=your_key_here
# Never hardcode API keys in source code!

# ==============================
# Model Configuration
# ==============================
# Available Claude models (Jan 2026)
AVAILABLE_MODELS = {
    "claude-3-opus-20240229": {"name": "Opus", "tier": 3, "cost": "High", "speed": "Slow"},
    "claude-3-sonnet-20240229": {"name": "Sonnet", "tier": 2, "cost": "Medium", "speed": "Medium"},
    "claude-3-haiku-20240307": {"name": "Haiku", "tier": 1, "cost": "Low", "speed": "Fast"}
}

# Default model
DEFAULT_MODEL = "claude-3-haiku-20240307"

# Model fallback chain (higher tier → lower tier on rate limit)
MODEL_FALLBACK_CHAIN = [
    "claude-3-opus-20240229",
    "claude-3-sonnet-20240229",
    "claude-3-haiku-20240307"
]

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY_BASE = 5  # seconds
RETRY_BACKOFF_MULTIPLIER = 2  # exponential backoff

# Model presets for different use cases
MODEL_PRESETS = {
    "Speed (All Haiku)": {
        "default": "claude-3-haiku-20240307",
        "overrides": {}
    },
    "Balanced (All Sonnet)": {
        "default": "claude-3-sonnet-20240229",
        "overrides": {}
    },
    "Quality (Critical=Opus, Rest=Sonnet)": {
        "default": "claude-3-sonnet-20240229",
        "overrides": {
            "Senior": "claude-3-opus-20240229",
            "Verifier": "claude-3-opus-20240229"
        }
    },
    "Premium (All Opus)": {
        "default": "claude-3-opus-20240229",
        "overrides": {}
    },
    "Budget (All Haiku, QA=Sonnet)": {
        "default": "claude-3-haiku-20240307",
        "overrides": {
            "QA": "claude-3-sonnet-20240229",
            "Verifier": "claude-3-sonnet-20240229"
        }
    }
}

# Explicit Anthropic LLM instance (prevents OpenAI fallback)
# This will be dynamically created per agent based on selected models
anthropic_llm = LLM(model=DEFAULT_MODEL, provider="anthropic")

# ==============================
# Mode Configuration
# ==============================
# Code Review Mode - adjusts prompts for code analysis
CODE_REVIEW_MODE_PROMPTS = {
    "Senior": "Perform comprehensive code review for: {project_description}\n\nAnalyze:\n1. Architecture and design patterns\n2. Code quality and maintainability\n3. Performance bottlenecks\n4. Security vulnerabilities (basic)\n5. Best practices compliance\n6. Scalability concerns\n7. Technical debt\n\nProvide specific examples and severity ratings (Critical/High/Medium/Low).",
    "QA": "Create comprehensive test strategy for: {project_description}\n\nProvide:\n1. Identified bugs and issues\n2. Edge cases not handled\n3. Test scenarios to add\n4. Coverage gaps\n5. Integration test recommendations\n6. Performance test scenarios\n\nPrioritize by severity and include specific test cases.",
    "Verifier": "Security audit for: {project_description}\n\nCheck for:\n1. OWASP Top 10 vulnerabilities\n2. Authentication/Authorization flaws\n3. Input validation issues\n4. SQL injection, XSS, CSRF risks\n5. Data exposure concerns\n6. Insecure dependencies\n7. API security issues\n8. Secret management\n\nRate findings as Critical/High/Medium/Low with remediation steps."
}

# Agent presets for different workflows
AGENT_PRESETS = {
    "New Project Development": ["PM", "Memory", "Research", "Ideas", "Designs", "QA"],
    "Code Review": ["Senior", "QA", "Verifier"],
    "Security Audit": ["Senior", "Verifier"],
    "Market Research": ["Memory", "Research", "Ideas", "Senior"],
    "Full Stack Development": ["PM", "Research", "Ideas", "Designs", "iOS", "Android", "Web", "QA", "Verifier"],
    "Architecture Review": ["Senior", "Verifier"]
}

# Memory file
MEMORY_FILE = "team_memory.json"

# Projects dir
PROJECTS_DIR = "./projects"
os.makedirs(PROJECTS_DIR, exist_ok=True)

# Exports dir
EXPORTS_DIR = "./exports"
os.makedirs(EXPORTS_DIR, exist_ok=True)

# Rate limit safety via sequential execution (no parallel API calls)
# Sequential processing ensures we stay well under Tier 2 limits:
# - Max requests: 11 agents = 11 requests << 1K req/min limit
# - Max input tokens: ~55K total << 450K tokens/min limit
# - Max output tokens: ~22K total << 90K tokens/min limit
RATE_LIMIT_DELAY = 15  # Legacy constant, kept for backward compatibility

# ==============================
# Visual Workflow Preview (Quick Win #5)
# ==============================
def generate_workflow_preview(selected_agents, execution_priority=None):
    """
    Generate ASCII art workflow preview showing execution order.

    Quick Win #5: Visual confirmation of workflow before execution.

    Args:
        selected_agents: List of agent names
        execution_priority: Optional custom execution order

    Returns:
        String containing ASCII art workflow diagram
    """
    if not selected_agents:
        return "\n📋 No agents selected - workflow is empty\n"

    # Determine execution order
    if execution_priority:
        order = execution_priority
    else:
        # Use default priority order
        default_order = ["PM", "Memory", "Research", "Ideas", "Designs",
                        "Senior", "iOS", "Android", "Web", "QA", "Verifier"]
        order = [agent for agent in default_order if agent in selected_agents]

    # Agent icons mapping
    icons = {
        "PM": "📋", "Memory": "🧠", "Research": "🔍",
        "Ideas": "💡", "Designs": "🎨", "Senior": "👨‍💻",
        "iOS": "📱", "Android": "🤖", "Web": "🌐",
        "QA": "✅", "Verifier": "🔎"
    }

    # Build ASCII workflow diagram
    diagram = "\n" + "="*60 + "\n"
    diagram += "                 WORKFLOW PREVIEW\n"
    diagram += "="*60 + "\n\n"

    diagram += "┌────────────────────────────────┐\n"
    diagram += "│   🚀 START WORKFLOW            │\n"
    diagram += "└────────────────────────────────┘\n"
    diagram += "              ↓\n"

    for i, agent in enumerate(order, 1):
        icon = icons.get(agent, '🤖')
        diagram += "┌────────────────────────────────┐\n"
        diagram += f"│   {icon} {agent:<24} │\n"
        diagram += f"│   Step {i} of {len(order):<20} │\n"
        diagram += "└────────────────────────────────┘\n"

        if i < len(order):
            diagram += "              ↓\n"

    diagram += "              ↓\n"
    diagram += "┌────────────────────────────────┐\n"
    diagram += "│   ✅ WORKFLOW COMPLETE         │\n"
    diagram += "└────────────────────────────────┘\n"

    diagram += "\n" + "="*60 + "\n"
    diagram += f"Total Steps: {len(order)} agents in sequential execution\n"
    diagram += "="*60 + "\n"

    return diagram

def generate_mermaid_workflow(selected_agents, execution_priority=None):
    """
    Generate Mermaid diagram syntax for workflow visualization.

    Quick Win #5: Alternative visualization format for documentation.

    Args:
        selected_agents: List of agent names
        execution_priority: Optional custom execution order

    Returns:
        String containing Mermaid flowchart syntax
    """
    if not selected_agents:
        return "```mermaid\ngraph TD\n    A[No agents selected]\n```"

    # Determine execution order
    if execution_priority:
        order = execution_priority
    else:
        default_order = ["PM", "Memory", "Research", "Ideas", "Designs",
                        "Senior", "iOS", "Android", "Web", "QA", "Verifier"]
        order = [agent for agent in default_order if agent in selected_agents]

    # Agent icons
    icons = {
        "PM": "📋", "Memory": "🧠", "Research": "🔍",
        "Ideas": "💡", "Designs": "🎨", "Senior": "👨‍💻",
        "iOS": "📱", "Android": "🤖", "Web": "🌐",
        "QA": "✅", "Verifier": "🔎"
    }

    # Build Mermaid diagram
    diagram = "```mermaid\ngraph TD\n"
    diagram += "    Start([🚀 Start Workflow])\n"

    # Connect start to first agent
    if order:
        first_agent = order[0]
        first_icon = icons.get(first_agent, '🤖')
        diagram += f"    Start --> {first_agent}\n"
        diagram += f"    {first_agent}[{first_icon} {first_agent}]\n"

    # Connect agents in sequence
    for i in range(len(order) - 1):
        current = order[i]
        next_agent = order[i + 1]
        next_icon = icons.get(next_agent, '🤖')
        diagram += f"    {current} --> {next_agent}\n"
        diagram += f"    {next_agent}[{next_icon} {next_agent}]\n"

    # Connect last agent to end
    if order:
        last_agent = order[-1]
        diagram += f"    {last_agent} --> End\n"

    diagram += "    End([✅ Complete])\n"

    # Styling
    diagram += "\n    classDef agentStyle fill:#6D28D9,stroke:#4C1D95,stroke-width:2px,color:#fff\n"
    diagram += "    classDef startEnd fill:#0891B2,stroke:#0E7490,stroke-width:2px,color:#fff\n"

    for agent in order:
        diagram += f"    class {agent} agentStyle\n"

    diagram += "    class Start,End startEnd\n"
    diagram += "```"

    return diagram

# ==============================
# Context Length Tracking (Quick Win #3)
# ==============================
# Claude models have 200K token context windows
CONTEXT_LIMIT = 200000  # 200K tokens for Claude Opus/Sonnet/Haiku

def estimate_tokens(text):
    """
    Estimate token count for text.
    Uses rough approximation: ~4 characters per token.

    This is faster than API calls and good enough for warnings.
    Actual token count may vary ±20%.
    """
    if not text:
        return 0
    # Rough estimate: 4 chars ≈ 1 token
    return len(str(text)) // 4

def format_context_indicator(tokens_used, tokens_limit=CONTEXT_LIMIT):
    """
    Format context usage indicator with progress bar and warnings.

    Returns formatted string with:
    - Progress bar visualization
    - Percentage and token counts
    - Warnings at 80%, 90%, 95% thresholds
    - Suggestions for optimization
    """
    if tokens_limit == 0:
        return ""

    percent = (tokens_used / tokens_limit) * 100

    # Progress bar (20 characters wide)
    bar_length = 20
    filled = int((tokens_used / tokens_limit) * bar_length)
    filled = min(filled, bar_length)  # Cap at 100%
    bar = "█" * filled + "░" * (bar_length - filled)

    # Color/emoji coding based on usage
    if percent >= 95:
        emoji = "🔴"
        status = "CRITICAL"
        warning = "\n⚠️  CRITICAL: Context almost full! Stopping soon to prevent failures.\n   Consider: Using fewer agents or shorter custom prompts."
    elif percent >= 90:
        emoji = "🟠"
        status = "WARNING"
        warning = "\n⚠️  WARNING: Approaching context limit (90%+). May stop execution if limit reached."
    elif percent >= 80:
        emoji = "🟡"
        status = "NOTICE"
        warning = "\n⚠️  NOTICE: Context usage high (80%+). Remaining capacity: ~" + f"{int((tokens_limit - tokens_used) / 1000)}K tokens"
    else:
        emoji = "🟢"
        status = "OK"
        warning = ""

    indicator = f"\n{'-'*60}\n"
    indicator += f"{emoji} CONTEXT USAGE: [{bar}] {percent:.1f}% ({status})\n"
    indicator += f"Tokens: {tokens_used:,} / {tokens_limit:,} ({tokens_limit - tokens_used:,} remaining)"
    indicator += warning
    indicator += f"\n{'-'*60}\n"

    return indicator

# Phase choices for progressive execution
PHASE_CHOICES = [
    "Planning Only (Memory + PM + Ideas)",
    "Planning + Design (Up to Designs)",
    "Planning + Design + Code (Up to Engineers)",
    "Full Run (All Agents)"
]

# ==============================
# Memory Management
# ==============================
def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_memory(key, value):
    memory = load_memory()
    memory[key] = value
    with open(MEMORY_FILE, 'w') as f:
        json.dump(memory, f, indent=2)

# ==============================
# Model Selection and Fallback Logic
# ==============================
def get_model_for_agent(role, preset_name, custom_models=None):
    """
    Determine which model to use for a specific agent

    Args:
        role: Agent role name
        preset_name: Selected preset name
        custom_models: Optional dict of custom model selections per agent

    Returns:
        Model identifier string
    """
    # Custom override takes precedence
    if custom_models and role in custom_models and custom_models[role] != "Use Default":
        return custom_models[role]

    # Check preset overrides
    preset = MODEL_PRESETS.get(preset_name, MODEL_PRESETS["Speed (All Haiku)"])
    if role in preset.get("overrides", {}):
        return preset["overrides"][role]

    # Use preset default
    return preset.get("default", DEFAULT_MODEL)

def create_llm_for_model(model_id):
    """Create an LLM instance for the specified model"""
    try:
        return LLM(model=model_id, provider="anthropic")
    except Exception as e:
        log_agent_message("System", f"Error creating LLM for {model_id}: {str(e)}")
        # Fallback to default model
        return LLM(model=DEFAULT_MODEL, provider="anthropic")

def get_next_fallback_model(current_model):
    """Get the next model in the fallback chain"""
    try:
        current_index = MODEL_FALLBACK_CHAIN.index(current_model)
        if current_index < len(MODEL_FALLBACK_CHAIN) - 1:
            return MODEL_FALLBACK_CHAIN[current_index + 1]
    except ValueError:
        # Current model not in chain, start from top
        pass
    return None

def is_rate_limit_error(error):
    """Check if an error is a rate limit error"""
    error_str = str(error).lower()
    rate_limit_indicators = [
        "rate limit",
        "429",
        "too many requests",
        "quota exceeded",
        "throttled"
    ]
    return any(indicator in error_str for indicator in rate_limit_indicators)

def execute_with_fallback(func, agent_role, current_model, *args, **kwargs):
    """
    Execute a function with retry and model fallback on rate limits

    Args:
        func: Function to execute
        agent_role: Name of the agent for logging
        current_model: Currently selected model
        *args, **kwargs: Arguments to pass to func

    Returns:
        Result from func or raises exception after all retries
    """
    attempt = 0
    model_to_try = current_model

    while attempt < MAX_RETRIES:
        try:
            log_agent_message("System", f"{agent_role}: Attempt {attempt + 1}/{MAX_RETRIES} with {AVAILABLE_MODELS.get(model_to_try, {}).get('name', model_to_try)}")
            result = func(*args, **kwargs)

            if attempt > 0:
                log_agent_message("System", f"{agent_role}: ✓ Succeeded after {attempt + 1} attempts")

            return result

        except Exception as e:
            attempt += 1

            if is_rate_limit_error(e):
                log_agent_message("System", f"{agent_role}: ⚠️ Rate limit hit with {AVAILABLE_MODELS.get(model_to_try, {}).get('name', model_to_try)}")

                # Try fallback model
                next_model = get_next_fallback_model(model_to_try)

                if next_model and attempt < MAX_RETRIES:
                    log_agent_message("System", f"{agent_role}: → Falling back to {AVAILABLE_MODELS[next_model]['name']}")
                    model_to_try = next_model

                    # Update the LLM instance with new model
                    kwargs['model'] = model_to_try

                    # Shorter delay for model fallback
                    delay = RETRY_DELAY_BASE
                    log_agent_message("System", f"{agent_role}: Waiting {delay}s before retry...")
                    time.sleep(delay)
                    continue

            # For non-rate-limit errors or no fallback available, use exponential backoff
            if attempt < MAX_RETRIES:
                delay = RETRY_DELAY_BASE * (RETRY_BACKOFF_MULTIPLIER ** (attempt - 1))
                log_agent_message("System", f"{agent_role}: Error: {str(e)[:100]}... Retrying in {delay}s")
                time.sleep(delay)
            else:
                log_agent_message("System", f"{agent_role}: ❌ Failed after {MAX_RETRIES} attempts")
                raise

    raise Exception(f"Failed after {MAX_RETRIES} attempts with all fallback models")

# ==============================
# Shared Logs for Dashboard
# ==============================
# Note: agent_logs will be initialized after AGENT_ROLES is loaded

# Store complete run history with metadata
run_history = []

def log_agent_message(role, message):
    timestamp = datetime.now().strftime("%H:%M:%S")
    agent_logs[role].append(f"[{timestamp}] {message}")

# ==============================
# Agent Mapping and Default Prompts
# ==============================

# Dynamic agent loading from configuration file
def load_agent_configs():
    """Load agent configurations from agents.config.json file."""
    config_path = Path(__file__).parent / 'agents.config.json'

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # Convert to dictionary keyed by agent ID
        agent_dict = {}
        for agent in config.get('agents', []):
            agent_dict[agent['id']] = {
                'role': agent['role'],
                'goal': agent['goal'],
                'backstory': agent['backstory'],
                'defaultPrompt': agent.get('defaultPrompt', ''),
                'priority': agent.get('priority', 99),
                'category': agent.get('category', 'Uncategorized')
            }

        print(f"✅ Loaded {len(agent_dict)} agents from agents.config.json")
        return agent_dict

    except FileNotFoundError:
        print("⚠️  agents.config.json not found, using hardcoded agent configs")
        return None
    except Exception as e:
        print(f"⚠️  Error loading agents.config.json: {e}, using hardcoded configs")
        return None

# Load dynamic agent configurations
AGENT_CONFIGS_DYNAMIC = load_agent_configs()

# Agent roles list (dynamically loaded or fallback to hardcoded)
if AGENT_CONFIGS_DYNAMIC:
    AGENT_ROLES = list(AGENT_CONFIGS_DYNAMIC.keys())
else:
    AGENT_ROLES = ["PM", "Memory", "Research", "Ideas", "Designs", "Senior", "iOS", "Android", "Web", "QA", "Verifier"]

# Initialize agent_logs now that AGENT_ROLES is defined
agent_logs = {"System": []}  # System logs for execution status
for role in AGENT_ROLES:
    agent_logs[role] = []

def get_agents_by_category():
    """Group agents by their category for organized UI display

    Returns:
        Dict[str, List[str]]: Dictionary mapping category names to lists of agent IDs
    """
    if not AGENT_CONFIGS_DYNAMIC:
        # Fallback categorization for hardcoded agents
        return {
            "Management": ["PM", "Memory"],
            "Product & Design": ["Research", "Ideas", "Designs"],
            "Engineering": ["Senior", "iOS", "Android", "Web"],
            "Quality Assurance": ["QA", "Verifier"]
        }

    categories = {}
    for agent_id, agent_config in AGENT_CONFIGS_DYNAMIC.items():
        category = agent_config.get('category', 'Other')
        if category not in categories:
            categories[category] = []
        categories[category].append(agent_id)

    # Sort categories and agents within each category
    sorted_categories = {}
    for category in sorted(categories.keys()):
        sorted_categories[category] = sorted(categories[category])

    return sorted_categories

# Execution priority/dependency order
# Lower priority number = runs first
# Agents in same priority can run in parallel
AGENT_EXECUTION_PRIORITY = {
    "Memory": 1,      # First: Recall past learnings
    "PM": 1,          # First: Create initial plan
    "Research": 2,    # Second: Market research and competitive analysis
    "Ideas": 3,       # Third: Generate features based on research
    "Designs": 4,     # Fourth: Create designs based on ideas
    "iOS": 5,         # Fifth: Implement based on designs
    "Android": 5,     # Fifth: Implement based on designs
    "Web": 5,         # Fifth: Implement based on designs
    "Senior": 6,      # Sixth: Review implementations
    "QA": 7,          # Seventh: Test everything
    "Verifier": 8     # Eighth: Final verification
}

DEFAULT_PROMPTS = {
    "Memory": "Retrieve relevant past learnings for this project.",
    "PM": "Create a lean sprint plan for: {project_description}\nIncorporate memory. Prioritize MVP, market needs, all use cases, best stack, no over-engineering.",
    "Research": "Conduct comprehensive market research for: {project_description}\n\nAnalyze:\n1. Market size and opportunity (TAM/SAM/SOM if applicable)\n2. Target audience and user personas\n3. Competitive landscape (direct and indirect competitors)\n4. Competitor strengths and weaknesses\n5. Market gaps and opportunities\n6. Required features to be competitive\n7. Unique differentiators needed\n8. Go-to-market strategy recommendations\n9. Potential challenges and risks\n10. Strategic recommendations to beat competition\n\nProvide data-driven insights with specific examples where possible.",
    "Ideas": "Generate market-smart ideas covering all use cases. Focus on efficiency: minimal features with high impact.",
    "Designs": "Design based on ideas: simple flows, text-based wireframes. Consider all scenarios (offline, accessibility). Keep lean.",
    "iOS": "Build iOS components based on designs/plan. Use best stack; clean, functional code. Cover all use cases.",
    "Android": "Build Android components based on designs/plan. Use best stack; clean code.",
    "Web": "Build Web components based on designs/plan. Use best stack; clean code.",
    "Senior": "Review for market fit, all use cases, no over-engineering, best stacks. Provide feedback.",
    "QA": "Test for all use cases, efficiency. Validate functionality and market relevance.",
    "Verifier": "Verify entire chain: Check for hallucinations, consistency with project description, coverage of use cases, no over-engineering, optimal stacks. Use <verification> tags."
}

DEFAULT_EXPECTED_OUTPUTS = {
    "Memory": "Summary of relevant memories or 'No prior knowledge available'.",
    "PM": "Structured sprint plan with delegations to Ideas, Designs, Engineers.",
    "Research": "Comprehensive market analysis report including: market size, competition analysis, required features, differentiation strategy, and actionable recommendations.",
    "Ideas": "3-5 minimal features with pros/cons and rationale.",
    "Designs": "User flows, wireframes description, design system guidelines.",
    "iOS": "Swift/SwiftUI code snippets + comments + stack rationale.",
    "Android": "Kotlin/Jetpack Compose code snippets + rationale.",
    "Web": "JS/React code snippets + rationale.",
    "Senior": "Review feedback, stack validation, any fixes.",
    "QA": "Test plan, results, any bugs found.",
    "Verifier": "Structured verification report with approvals/flags."
}

# ==============================
# Universal Anti-Hallucination Backstory
# ==============================
UNIVERSAL_BACKSTORY = """
You are a highly reliable, fact-conscious agent designed to prioritize epistemic accuracy over speed or creativity.

Core Principles:
- If it is not verifiable from the project description, previous agent outputs, or pure logical reasoning, DO NOT CLAIM IT.
- If unsure, missing information, or something is ambiguous → immediately say "I don't know" or "This cannot be confirmed from the provided context" and explain why.
- Never fabricate features, market data, user needs, tech details, code, or citations.
- Always ground claims in the actual input context. Use direct quotes or references when possible.
- For every major decision (features, tech stack, design), think step-by-step in <thinking> tags first.
- After reasoning, self-reflect: "Is this over-engineered? Does it cover all key use cases? Is the stack optimal for this scope?"
- Output format: Use clear structure. Never guess values, dates, or specifics not in context.
- If a question/spec is incomplete, ask for clarification instead of assuming.
"""

# ==============================
# Agent Definitions (using Anthropic LLM instance)
# ==============================
# Note: These are created with default LLM but will be dynamically recreated
# with selected models during execution

AGENT_CONFIGS = {
    "PM": {
        "role": "Project Manager",
        "goal": "Create efficient sprint plans",
        "backstory": UNIVERSAL_BACKSTORY + "Coordinator. Enforce MVP, use cases, best stack."
    },
    "Memory": {
        "role": "Memory Specialist",
        "goal": "Recall/store learnings",
        "backstory": UNIVERSAL_BACKSTORY + "Retrieve lessons or say 'No prior knowledge'."
    },
    "Research": {
        "role": "Market Research Analyst",
        "goal": "Analyze market opportunities and competitive landscape",
        "backstory": UNIVERSAL_BACKSTORY + "Expert in market analysis, competitive intelligence, and strategic positioning. Research actual competitors, market data, and provide evidence-based recommendations. If market data is unavailable, clearly state assumptions and reasoning."
    },
    "Ideas": {
        "role": "Ideas Specialist",
        "goal": "Generate lean ideas",
        "backstory": UNIVERSAL_BACKSTORY + "Focus on minimal high-impact features."
    },
    "Designs": {
        "role": "UI/UX Designer",
        "goal": "Create efficient designs",
        "backstory": UNIVERSAL_BACKSTORY + "Simple flows, wireframes, lean UX."
    },
    "Senior": {
        "role": "Senior Engineer",
        "goal": "Review efficiency & stack",
        "backstory": UNIVERSAL_BACKSTORY + "Lean architecture, optimal stacks."
    },
    "iOS": {
        "role": "iOS Engineer",
        "goal": "Build iOS features",
        "backstory": UNIVERSAL_BACKSTORY + "Swift/SwiftUI, clean code."
    },
    "Android": {
        "role": "Android Engineer",
        "goal": "Build Android features",
        "backstory": UNIVERSAL_BACKSTORY + "Kotlin/Compose, clean code."
    },
    "Web": {
        "role": "Web Engineer",
        "goal": "Build web features",
        "backstory": UNIVERSAL_BACKSTORY + "JS/React, clean code."
    },
    "QA": {
        "role": "QA Engineer",
        "goal": "Test thoroughly",
        "backstory": UNIVERSAL_BACKSTORY + "Cover edges, validate efficiency."
    },
    "Verifier": {
        "role": "Verifier",
        "goal": "Check for hallucinations",
        "backstory": UNIVERSAL_BACKSTORY + "Use <verification> tags."
    }
}

def create_agent_with_model(agent_key, model_id, custom_prompt=None):
    """
    Dynamically create an agent with a specific model.
    Supports both built-in agents and custom agents.

    Args:
        agent_key: Agent ID (e.g., "PM", "Senior", or custom like "DevOps")
        model_id: Model identifier for LLM
        custom_prompt: Optional custom backstory/prompt to override default

    Returns:
        Agent instance configured with specified model and prompts
    """
    # Check if agent exists in dynamic configs (loaded from JSON)
    if AGENT_CONFIGS_DYNAMIC and agent_key in AGENT_CONFIGS_DYNAMIC:
        config = AGENT_CONFIGS_DYNAMIC[agent_key]
    # Fallback to hardcoded configs
    elif agent_key in AGENT_CONFIGS:
        config = AGENT_CONFIGS[agent_key]
    # Handle custom agents not in config (create generic agent)
    else:
        print(f"⚠️  Unknown agent '{agent_key}', creating generic agent")
        config = {
            "role": f"{agent_key} Agent",
            "goal": "Assist with the project",
            "backstory": UNIVERSAL_BACKSTORY + f" You are a specialized {agent_key} agent."
        }

    # Create LLM instance
    llm = create_llm_for_model(model_id)

    # Use custom prompt if provided, otherwise use default backstory
    backstory = custom_prompt if custom_prompt else config.get("backstory", config.get("goal", ""))

    return Agent(
        role=config["role"],
        goal=config["goal"],
        backstory=backstory,
        llm=llm
    )

# Create default agents (will be replaced during execution with selected models)
pm_agent = create_agent_with_model("PM", DEFAULT_MODEL)
memory_agent = create_agent_with_model("Memory", DEFAULT_MODEL)
research_agent = create_agent_with_model("Research", DEFAULT_MODEL)
ideas_agent = create_agent_with_model("Ideas", DEFAULT_MODEL)
designs_agent = create_agent_with_model("Designs", DEFAULT_MODEL)
senior_agent = create_agent_with_model("Senior", DEFAULT_MODEL)
ios_agent = create_agent_with_model("iOS", DEFAULT_MODEL)
android_agent = create_agent_with_model("Android", DEFAULT_MODEL)
web_agent = create_agent_with_model("Web", DEFAULT_MODEL)
qa_agent = create_agent_with_model("QA", DEFAULT_MODEL)
verifier_agent = create_agent_with_model("Verifier", DEFAULT_MODEL)

# ==============================
# Auto Git Repo Creation
# ==============================
def create_git_repo(project_name, outputs):
    safe_name = "".join(c if c.isalnum() or c in " -_" else "_" for c in project_name)[:50]
    repo_dir = os.path.join(PROJECTS_DIR, safe_name)
    os.makedirs(repo_dir, exist_ok=True)

    repo = git.Repo.init(repo_dir)

    files_to_commit = {}
    if "iOS" in outputs and outputs["iOS"]:
        files_to_commit["ios_implementation.swift"] = outputs["iOS"]
    if "Android" in outputs and outputs["Android"]:
        files_to_commit["android_implementation.kt"] = outputs["Android"]
    if "Web" in outputs and outputs["Web"]:
        files_to_commit["web_implementation.jsx"] = outputs["Web"]
    if "Designs" in outputs and outputs["Designs"]:
        files_to_commit["designs.md"] = outputs["Designs"]

    for filename, content in files_to_commit.items():
        path = os.path.join(repo_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        repo.index.add([filename])

    repo.index.commit(f"Initial commit from Super Dev Team - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    return repo_dir

# ==============================
# Export Functionality
# ==============================
def export_to_json(project_name, selected_agents, outputs, metadata=None):
    """
    Export agent findings to JSON format with professional branding.

    Quick Win #4: Enhanced with platform metadata and comprehensive details.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = "".join(c if c.isalnum() or c in " -_" else "_" for c in project_name)[:50]
    filename = f"{safe_name}_{timestamp}.json"
    filepath = os.path.join(EXPORTS_DIR, filename)

    # Enhanced export data with professional branding
    export_data = {
        "_platform": {
            "name": "Multi-Agent Development Team",
            "version": "1.0.0",
            "website": "https://github.com/yourusername/multi-agent-team",
            "export_date": datetime.now().isoformat(),
            "export_format": "JSON v1.0"
        },
        "project": {
            "name": project_name,
            "timestamp": datetime.now().isoformat(),
            "selected_agents": selected_agents,
            "total_agents": len(selected_agents),
            **(metadata or {})
        },
        "workflow": {
            "execution_mode": "sequential",
            "agents_executed": len(selected_agents),
            "agents": selected_agents
        },
        "agent_outputs": {},
        "summary": {
            "total_outputs": len([o for o in outputs.values() if o]),
            "successful_agents": len([o for o in outputs.values() if o]),
            "failed_agents": len(selected_agents) - len([o for o in outputs.values() if o])
        }
    }

    # Add agent outputs with enhanced metadata
    for role in selected_agents:
        if role in outputs and outputs[role]:
            export_data["agent_outputs"][role] = {
                "role": role,
                "status": "completed",
                "output_length": len(outputs[role]),
                "messages": agent_logs.get(role, []),
                "message_count": len(agent_logs.get(role, [])),
                "full_output": outputs[role]
            }
        else:
            export_data["agent_outputs"][role] = {
                "role": role,
                "status": "failed_or_empty",
                "messages": agent_logs.get(role, [])
            }

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)

    return filepath

def export_to_markdown(project_name, selected_agents, outputs, metadata=None):
    """
    Export agent findings to Markdown format with professional branding.

    Quick Win #4: Enhanced with headers, workflow summary, and footer.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = "".join(c if c.isalnum() or c in " -_" else "_" for c in project_name)[:50]
    filename = f"{safe_name}_{timestamp}.md"
    filepath = os.path.join(EXPORTS_DIR, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        # Professional header
        f.write("# Multi-Agent Development Team Analysis\n\n")
        f.write("**Generated by:** Multi-Agent Platform v1.0\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("**Platform:** https://github.com/yourusername/multi-agent-team\n\n")
        f.write("---\n\n")

        # Project information
        f.write(f"## Project: {project_name}\n\n")

        # Workflow Summary Table
        f.write("## Workflow Summary\n\n")
        f.write("| Property | Value |\n")
        f.write("|----------|-------|\n")
        f.write(f"| Agents Used | {', '.join(selected_agents)} |\n")
        f.write(f"| Total Agents | {len(selected_agents)} |\n")
        f.write(f"| Execution Mode | Sequential |\n")

        if metadata:
            if 'model_preset' in metadata:
                f.write(f"| Model Preset | {metadata['model_preset']} |\n")
            if 'phase' in metadata:
                f.write(f"| Execution Phase | {metadata['phase']} |\n")
            if 'agent_count' in metadata:
                f.write(f"| Agents Executed | {metadata['agent_count']} |\n")

        f.write("\n")

        # Success metrics
        successful = len([o for o in outputs.values() if o])
        failed = len(selected_agents) - successful
        f.write(f"**Success Rate:** {successful}/{len(selected_agents)} agents completed successfully")
        if failed > 0:
            f.write(f" ({failed} failed or empty)")
        f.write("\n\n")

        f.write("---\n\n")

        # Agent outputs
        f.write("## Agent Outputs\n\n")

        for role in selected_agents:
            if role in outputs and outputs[role]:
                f.write(f"### {role} Agent\n\n")
                f.write(f"**Status:** ✅ Completed\n")
                f.write(f"**Output Length:** {len(outputs[role])} characters\n\n")

                f.write(f"#### Output\n\n")
                f.write(f"```\n{outputs[role]}\n```\n\n")

                if agent_logs.get(role):
                    f.write(f"#### Log Messages\n\n")
                    for msg in agent_logs[role]:
                        f.write(f"- {msg}\n")
                    f.write("\n")

                f.write("---\n\n")
            else:
                f.write(f"### {role} Agent\n\n")
                f.write(f"**Status:** ❌ Failed or empty output\n\n")
                f.write("---\n\n")

        # Professional footer
        f.write("## Export Information\n\n")
        f.write(f"- **Export Format:** Markdown\n")
        f.write(f"- **Export Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"- **Platform Version:** 1.0.0\n")
        f.write("- **Support:** https://github.com/yourusername/multi-agent-team/issues\n\n")
        f.write("---\n\n")
        f.write("*Generated with ❤️ by Multi-Agent Development Team*\n")

    return filepath

def export_to_csv(project_name, selected_agents, outputs, metadata=None):
    """
    Export agent findings to CSV format with professional branding.

    Quick Win #4: Enhanced with header rows and summary statistics.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = "".join(c if c.isalnum() or c in " -_" else "_" for c in project_name)[:50]
    filename = f"{safe_name}_{timestamp}.csv"
    filepath = os.path.join(EXPORTS_DIR, filename)

    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        # Header metadata rows
        writer.writerow(['# Multi-Agent Development Team Export'])
        writer.writerow(['# Generated by', 'Multi-Agent Platform v1.0'])
        writer.writerow(['# Date', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
        writer.writerow(['# Project', project_name])
        writer.writerow(['# Total Agents', len(selected_agents)])
        if metadata and 'model_preset' in metadata:
            writer.writerow(['# Model Preset', metadata['model_preset']])
        writer.writerow([])  # Empty row

        # Data headers
        writer.writerow(['Agent Role', 'Status', 'Timestamp', 'Output Preview (500 chars)', 'Output Length', 'Message Count'])

        # Agent data rows
        for role in selected_agents:
            if role in outputs and outputs[role]:
                message_count = len(agent_logs.get(role, []))
                output_preview = outputs[role][:500] + "..." if len(outputs[role]) > 500 else outputs[role]
                # Remove newlines for CSV compatibility
                output_preview = output_preview.replace('\n', ' ').replace('\r', '')

                writer.writerow([
                    role,
                    'Completed',
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    output_preview,
                    len(outputs[role]),
                    message_count
                ])
            else:
                writer.writerow([
                    role,
                    'Failed/Empty',
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    '',
                    0,
                    len(agent_logs.get(role, []))
                ])

        # Summary row
        writer.writerow([])  # Empty row
        successful = len([o for o in outputs.values() if o])
        writer.writerow(['# Summary', f'{successful}/{len(selected_agents)} agents completed successfully'])

    return filepath

def export_individual_agent(role, output, project_name):
    """Export individual agent findings to dedicated file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = "".join(c if c.isalnum() or c in " -_" else "_" for c in project_name)[:50]
    filename = f"{safe_name}_{role}_{timestamp}.md"
    filepath = os.path.join(EXPORTS_DIR, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"# {role} Agent Report\n\n")
        f.write(f"**Project:** {project_name}\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("---\n\n")
        f.write("## Findings\n\n")
        f.write(output)
        f.write("\n\n")

        if agent_logs.get(role):
            f.write("## Activity Log\n\n")
            for msg in agent_logs[role]:
                f.write(f"- {msg}\n")

    return filepath

def export_all_formats(project_name, selected_agents, outputs, metadata=None):
    """Export to all formats and return file paths"""
    json_path = export_to_json(project_name, selected_agents, outputs, metadata)
    md_path = export_to_markdown(project_name, selected_agents, outputs, metadata)
    csv_path = export_to_csv(project_name, selected_agents, outputs, metadata)

    return {
        "json": json_path,
        "markdown": md_path,
        "csv": csv_path
    }

# ==============================
# Main Execution Function (with agent selection, custom prompts, error handling)
# ==============================
def run_dev_team(project_description, selected_agents, github_url="", custom_prompts=None, model_preset="Speed (All Haiku)",
                 custom_models=None, custom_priorities=None, code_review_mode=False, human_feedback="",
                 approval_choice="Run (No Approval Yet)", phase=PHASE_CHOICES[3], auto_export=False):
    """
    Main execution function with robust error handling and full customization

    Args:
        project_description: Main project description
        selected_agents: List of agent role names to execute
        github_url: Optional GitHub repository URL for direct code analysis
        custom_prompts: Dict of custom prompts per agent role
        model_preset: Selected model preset name
        custom_models: Optional dict of custom model selections per agent
        custom_priorities: Optional dict of custom execution priorities per agent
        code_review_mode: Enable code review optimized prompts
        human_feedback: Optional feedback for reruns
        approval_choice: Run/Approve/Reject workflow
        phase: Execution phase (planning/design/code/full)
        auto_export: Whether to auto-export results

    Returns:
        Tuple of (status message, outputs dict, export paths)
    """
    try:
        # Validate inputs
        if not project_description or not project_description.strip():
            return "Error: Project description cannot be empty.", {}, None

        if not selected_agents or len(selected_agents) == 0:
            return "Error: Please select at least one agent to run.", {}, None

        # Handle approval workflow
        if approval_choice == "Approve":
            return "Project approved. Git repo would be created here if run completed.", {}, None

        if approval_choice == "Reject and Rerun":
            project_description += f"\n\nPrevious feedback / fixes required:\n{human_feedback}"

        # Clear logs for new run
        for role in agent_logs:
            agent_logs[role] = []

        log_agent_message("System", f"Starting new project with {len(selected_agents)} agent(s)")
        log_agent_message("System", f"Selected agents: {', '.join(selected_agents)}")
        log_agent_message("System", f"Model preset: {model_preset}")

        # Use custom priorities if provided, otherwise use defaults
        effective_priorities = {}
        for role in selected_agents:
            if custom_priorities and role in custom_priorities and custom_priorities[role] is not None:
                effective_priorities[role] = int(custom_priorities[role])
            else:
                effective_priorities[role] = AGENT_EXECUTION_PRIORITY.get(role, 999)

        # Sort selected agents by execution priority
        sorted_agents = sorted(
            selected_agents,
            key=lambda role: effective_priorities.get(role, 999)
        )

        log_agent_message("System", f"Execution order: {' → '.join(sorted_agents)}")

        # Build tasks dynamically based on selected agents, custom prompts, and models
        # Tasks are created in priority order with dependencies
        tasks = []
        active_agents = []
        agent_models = {}  # Track which model is used for each agent
        tasks_by_role = {}  # Track tasks by role for dependency setup
        previous_priority_tasks = []  # Tasks from previous priority level

        for role in sorted_agents:
            # Check if agent exists in dynamic configs or hardcoded configs
            if AGENT_CONFIGS_DYNAMIC and role not in AGENT_CONFIGS_DYNAMIC and role not in AGENT_CONFIGS:
                log_agent_message("System", f"Warning: Unknown agent role '{role}', skipping")
                continue
            elif not AGENT_CONFIGS_DYNAMIC and role not in AGENT_CONFIGS:
                log_agent_message("System", f"Warning: Unknown agent role '{role}', skipping")
                continue

            # Determine which model to use for this agent
            model_id = get_model_for_agent(role, model_preset, custom_models)
            agent_models[role] = model_id

            model_name = AVAILABLE_MODELS.get(model_id, {}).get("name", model_id)
            priority = effective_priorities.get(role, 999)
            log_agent_message("System", f"{role} → {model_name} (Priority {priority})")

            # Create agent with selected model
            agent = create_agent_with_model(role, model_id)
            active_agents.append(agent)

            # Use custom prompt if provided, otherwise use default or code review mode prompt
            if custom_prompts and role in custom_prompts and custom_prompts[role].strip():
                prompt = custom_prompts[role].format(project_description=project_description)
                log_agent_message("System", f"Using custom prompt for {role}")
            elif code_review_mode and role in CODE_REVIEW_MODE_PROMPTS:
                prompt = CODE_REVIEW_MODE_PROMPTS[role].format(project_description=project_description)
                log_agent_message("System", f"Using code review prompt for {role}")
            else:
                prompt = DEFAULT_PROMPTS.get(role, "").format(project_description=project_description)

            # Special handling for Memory agent: inject actual memory content
            if role == "Memory":
                memory_data = load_memory()
                if memory_data:
                    memory_str = "\n".join([f"- {k}: {v}" for k, v in memory_data.items()])
                    prompt += f"\n\n**Available Memory:**\n{memory_str}\n\nAnalyze which memories are relevant to the current project and provide them in your output."
                    log_agent_message("System", f"Memory agent loaded {len(memory_data)} memories")
                else:
                    prompt += "\n\n**Available Memory:** No prior knowledge available yet."
                    log_agent_message("System", "Memory agent has no prior memories")

            expected_output = DEFAULT_EXPECTED_OUTPUTS.get(role, "Detailed analysis and recommendations.")

            # Create task with dependencies on previous priority level
            # This ensures Memory/PM complete before Research, Research before Ideas, etc.
            task_kwargs = {
                "description": prompt,
                "expected_output": expected_output,
                "agent": agent
            }

            # Add context (dependencies) from previous priority level
            if previous_priority_tasks:
                task_kwargs["context"] = previous_priority_tasks.copy()

            task = Task(**task_kwargs)
            tasks.append(task)
            tasks_by_role[role] = task

            # Update previous_priority_tasks for next priority level
            # If next agent has different priority, reset the list
            current_priority = effective_priorities.get(role, 999)
            next_index = sorted_agents.index(role) + 1
            if next_index < len(sorted_agents):
                next_role = sorted_agents[next_index]
                next_priority = effective_priorities.get(next_role, 999)
                if next_priority != current_priority:
                    # Priority is changing, current level tasks become dependencies
                    previous_priority_tasks = [tasks_by_role[r] for r in sorted_agents[:next_index] if r in tasks_by_role]

        if not tasks:
            return "Error: No valid agents selected or configured.", {}, None

        # Create crew with selected agents only
        log_agent_message("System", f"Initializing crew with {len(active_agents)} agent(s)")
        log_agent_message("System", f"Using sequential execution to respect rate limits")

        try:
            crew = Crew(
                agents=active_agents,
                tasks=tasks,
                process=Process.sequential,  # Sequential to prevent parallel API calls
                verbose=True
            )
        except Exception as e:
            error_msg = f"Error creating crew: {str(e)}"
            log_agent_message("System", error_msg)
            return error_msg, {}, None

        # Execute tasks with rate limiting and progress tracking
        try:
            # ============================================================
            # PRE-PLAN SUMMARY (Quick Win #1 + Quick Win #5)
            # Show users what will happen before execution begins
            # Includes visual workflow preview
            # ============================================================

            # Show visual workflow preview first (Quick Win #5)
            workflow_preview = generate_workflow_preview(sorted_agents, effective_priorities)
            log_agent_message("System", workflow_preview)

            log_agent_message("System", "\n" + "="*60)
            log_agent_message("System", "📋 WORKFLOW EXECUTION PLAN")
            log_agent_message("System", "="*60 + "\n")

            # Overview
            log_agent_message("System", f"▸ Agents Selected: {len(sorted_agents)} agents")
            log_agent_message("System", f"▸ Execution Mode: Sequential (one after another)")
            log_agent_message("System", f"▸ Model Preset: {model_preset}")

            # Time & Cost Estimates
            est_time_min = len(sorted_agents) * 1.5  # 1.5 min per agent average
            est_time_max = len(sorted_agents) * 3    # 3 min per agent max

            # Cost estimation based on model
            cost_per_agent_map = {
                "Speed (All Haiku)": 0.02,
                "Balanced (All Sonnet)": 0.08,
                "Quality (Critical=Opus, Rest=Sonnet)": 0.15,
                "Premium (All Opus)": 0.25,
                "Budget (All Haiku, QA=Sonnet)": 0.06
            }
            base_cost = cost_per_agent_map.get(model_preset, 0.08)
            est_cost_min = base_cost * len(sorted_agents) * 0.8
            est_cost_max = base_cost * len(sorted_agents) * 1.2

            log_agent_message("System", f"\n⏱️  Estimated Duration: {int(est_time_min)}-{int(est_time_max)} minutes")
            log_agent_message("System", f"💰 Estimated Cost: ${est_cost_min:.2f} - ${est_cost_max:.2f}\n")

            # Execution Order & Expected Outputs
            log_agent_message("System", "📊 EXECUTION ORDER & EXPECTED OUTPUTS:\n")

            agent_descriptions = {
                "PM": "Create sprint plan and coordinate work breakdown",
                "Memory": "Recall past learnings and store new insights",
                "Research": "Analyze 5+ competitors and market trends",
                "Ideas": "Propose 10-15 innovative features",
                "Designs": "Create UI/UX designs and wireframes",
                "Senior": "Review architecture and validate technical decisions",
                "iOS": "Build iOS components (Swift/SwiftUI)",
                "Android": "Build Android components (Kotlin/Compose)",
                "Web": "Build web components (React/JS)",
                "QA": "Test functionality and validate quality",
                "Verifier": "Check for hallucinations and inconsistencies"
            }

            for i, role in enumerate(sorted_agents, 1):
                desc = agent_descriptions.get(role, "Process tasks and generate outputs")
                model_name = AVAILABLE_MODELS.get(agent_models.get(role, DEFAULT_MODEL), {}).get("name", "Unknown")
                priority = effective_priorities.get(role, 999)
                log_agent_message("System", f"  {i}. {role} ({model_name}, Priority {priority})")
                log_agent_message("System", f"     → {desc}\n")

            # What Happens Next
            log_agent_message("System", "\n⚙️  WHAT HAPPENS NEXT:")
            log_agent_message("System", "  1. Agents execute sequentially in the order above")
            log_agent_message("System", "  2. Each agent builds on previous agent outputs")
            log_agent_message("System", "  3. Results appear in real-time below")
            log_agent_message("System", "  4. You can export results when complete\n")

            # Important Notes
            log_agent_message("System", "⚠️  IMPORTANT NOTES:")
            log_agent_message("System", "  • Execution cannot be paused once started")
            log_agent_message("System", "  • Closing this page will NOT stop execution")
            log_agent_message("System", "  • Estimates are approximate (actual may vary ±30%)")

            log_agent_message("System", "\n" + "="*60)
            log_agent_message("System", "🚀 STARTING EXECUTION")
            log_agent_message("System", "="*60 + "\n")

            # Original execution logging
            log_agent_message("System", "Starting task execution...")
            log_agent_message("System", f"Rate limit safety: Sequential execution ensures no parallel API calls")
            log_agent_message("System", f"Tier 2 limits: 1K req/min, 450K input tokens/min, 90K output tokens/min")
            log_agent_message("System", f"Expected usage: {len(tasks)} requests, ~{len(tasks)*5}K input tokens, ~{len(tasks)*2}K output tokens")
            log_agent_message("System", f"All limits safely respected with sequential execution")

            # Log task order (delays handled by sequential execution)
            for i, task in enumerate(tasks, 1):
                log_agent_message("System", f"Task {i}/{len(tasks)}: {task.description[:60]}...")

            # ============================================================
            # CONTEXT TRACKING (Quick Win #3)
            # Track cumulative token usage and warn when approaching limit
            # ============================================================
            total_tokens_used = 0

            # Count tokens in project description and prompts
            initial_tokens = estimate_tokens(project_description)
            for role in sorted_agents:
                if custom_prompts and role in custom_prompts:
                    initial_tokens += estimate_tokens(custom_prompts[role])
            total_tokens_used = initial_tokens

            log_agent_message("System", f"\n📊 Initial context: ~{initial_tokens:,} tokens from descriptions and prompts\n")

            # ============================================================
            # ENHANCED ERROR LOGGING FOR CREW EXECUTION
            # ============================================================
            log_agent_message("System", "🔍 Starting crew execution with detailed error tracking...")

            try:
                result = crew.kickoff()
                log_agent_message("System", f"✅ Crew execution completed successfully")
            except Exception as crew_error:
                error_type = type(crew_error).__name__
                log_agent_message("System", f"❌ CREW EXECUTION FAILED: {error_type}")
                log_agent_message("System", f"Error message: {str(crew_error)}")

                # Try to identify which agent failed
                import traceback
                tb = traceback.format_exc()
                log_agent_message("System", f"Full traceback:\n{tb}")

                # Return early with error
                return f"Crew execution failed: {str(crew_error)}", {}, None

            # Extract and log individual task outputs WITH ENHANCED ERROR TRACKING
            log_agent_message("System", "🔍 Extracting task outputs...")

            for i, task in enumerate(tasks):
                agent_role = sorted_agents[i] if i < len(sorted_agents) else "Unknown"

                try:
                    log_agent_message("System", f"📝 Processing {agent_role} (Task {i+1}/{len(tasks)})...")

                    if hasattr(task, 'output') and task.output:
                        # Log the task output to the agent's log
                        task_output = str(task.output)

                        # Count tokens in this agent's output
                        output_tokens = estimate_tokens(task_output)
                        total_tokens_used += output_tokens

                        # Show context usage after each agent
                        log_agent_message("System", f"\n{agent_role} output: ~{output_tokens:,} tokens")
                        context_indicator = format_context_indicator(total_tokens_used, CONTEXT_LIMIT)
                        log_agent_message("System", context_indicator)

                        # Check if we're approaching critical limit
                        usage_percent = (total_tokens_used / CONTEXT_LIMIT) * 100
                        if usage_percent >= 95:
                            log_agent_message("System", "\n🔴 CRITICAL: Context limit reached (95%+).")
                            log_agent_message("System", "Stopping execution to prevent failures.")
                            log_agent_message("System", "Consider: Using fewer agents or shorter prompts next time.\n")
                            break  # Stop processing remaining agents

                        log_agent_message(agent_role, f"Output:\n{task_output}")
                        log_agent_message("System", f"✅ Successfully captured output from {agent_role}")
                    else:
                        # Task has no output - this is the issue!
                        log_agent_message("System", f"⚠️  WARNING: {agent_role} task has no output!")

                        # Get detailed task information
                        task_attrs = dir(task)
                        log_agent_message("System", f"   Available task attributes: {[attr for attr in task_attrs if not attr.startswith('_')]}")

                        if hasattr(task, 'status'):
                            log_agent_message("System", f"   Task status: {task.status}")

                        if hasattr(task, 'error') and task.error:
                            log_agent_message("System", f"❌ {agent_role} FAILED with error: {task.error}")

                        if hasattr(task, 'result'):
                            log_agent_message("System", f"   Task result: {task.result}")

                        if hasattr(task, 'output_raw'):
                            log_agent_message("System", f"   Task output_raw: {task.output_raw}")

                        # Log agent information
                        if hasattr(task, 'agent'):
                            agent_info = f"{task.agent.role}" if hasattr(task.agent, 'role') else "Unknown"
                            log_agent_message("System", f"   Agent: {agent_info}")

                except Exception as task_error:
                    error_type = type(task_error).__name__
                    log_agent_message("System", f"❌ ERROR processing {agent_role}: {error_type}")
                    log_agent_message("System", f"   Error message: {str(task_error)}")

                    import traceback
                    tb = traceback.format_exc()
                    log_agent_message("System", f"   Traceback:\n{tb}")

            # ============================================================
            # FINAL CONTEXT SUMMARY (Quick Win #3)
            # Show total token usage and efficiency metrics
            # ============================================================
            log_agent_message("System", "\n" + "="*60)
            log_agent_message("System", "📊 FINAL CONTEXT USAGE SUMMARY")
            log_agent_message("System", "="*60)

            final_indicator = format_context_indicator(total_tokens_used, CONTEXT_LIMIT)
            log_agent_message("System", final_indicator)

            # Calculate efficiency metrics
            tokens_per_agent = total_tokens_used // len(sorted_agents) if sorted_agents else 0
            log_agent_message("System", f"📈 Efficiency Metrics:")
            log_agent_message("System", f"   • Total agents run: {len(sorted_agents)}")
            log_agent_message("System", f"   • Average tokens per agent: ~{tokens_per_agent:,}")
            log_agent_message("System", f"   • Total workflow tokens: ~{total_tokens_used:,}")

            # Provide optimization tips if usage was high
            usage_percent = (total_tokens_used / CONTEXT_LIMIT) * 100
            if usage_percent >= 60:
                log_agent_message("System", f"\n💡 Optimization Tips:")
                log_agent_message("System", f"   • Your workflow used {usage_percent:.0f}% of available context")
                log_agent_message("System", f"   • Consider: Shorter custom prompts or fewer agents")
                log_agent_message("System", f"   • For larger projects: Run agents in batches")
            elif usage_percent < 30:
                log_agent_message("System", f"\n✅ Efficient Usage:")
                log_agent_message("System", f"   • Your workflow used only {usage_percent:.0f}% of context")
                log_agent_message("System", f"   • You could add more agents or use longer prompts if needed")

            log_agent_message("System", "\n" + "="*60 + "\n")

            # Auto-save learnings to memory
            try:
                result_str = str(result)
                if "SwiftUI" in result_str:
                    save_memory("best_ios_ui_stack", "SwiftUI recommended for modern UI apps")
                if "Jetpack Compose" in result_str:
                    save_memory("best_android_ui_stack", "Jetpack Compose recommended")
                if "React" in result_str:
                    save_memory("best_web_framework", "React recommended for web apps")
            except Exception as e:
                log_agent_message("System", f"Warning: Could not save memory: {str(e)}")

            # Compile outputs
            outputs = {role: "\n".join(agent_logs[role]) for role in agent_logs if agent_logs[role]}

            # Auto-export if requested
            export_paths = None
            if auto_export and outputs:
                try:
                    export_paths = export_all_formats(
                        project_description[:100],
                        selected_agents,
                        outputs,
                        metadata={
                            "phase": phase,
                            "agent_count": len(selected_agents),
                            "model_preset": model_preset,
                            "agent_models": agent_models
                        }
                    )
                    log_agent_message("System", f"Auto-export completed: {len(export_paths)} files")
                except Exception as e:
                    log_agent_message("System", f"Warning: Auto-export failed: {str(e)}")

            # Handle approval workflow
            if approval_choice == "Approve":
                # Check if user wants to apply changes to existing repo
                apply_to_repo = human_feedback and human_feedback.strip().startswith("APPLY:")
                # Also check if GitHub URL was provided
                apply_to_github = github_url and github_url.strip() and CODE_APPLICATOR_AVAILABLE

                if apply_to_repo and CODE_APPLICATOR_AVAILABLE:
                    # Extract target repo path from feedback
                    # Format: "APPLY: /path/to/repo" or "APPLY: https://github.com/user/repo"
                    target_repo = human_feedback.replace("APPLY:", "").strip()

                    try:
                        log_agent_message("System", f"Applying changes to: {target_repo}")

                        # Check if target is a GitHub URL
                        is_github_url = target_repo.startswith("https://github.com") or target_repo.startswith("http://github.com")

                        if is_github_url:
                            # Apply changes to GitHub repository
                            log_agent_message("System", "Detected GitHub URL - cloning repository")
                            apply_result = apply_agent_changes_from_github(
                                agent_outputs=outputs,
                                github_url=target_repo,
                                create_branch=True,
                                create_pr=True,
                                auto_commit=True,
                                create_new_files=False,
                                cleanup_after=True
                            )
                        else:
                            # Apply changes to local repository
                            apply_result = apply_agent_changes_workflow(
                                agent_outputs=outputs,
                                target_repo_path=target_repo,
                                create_branch=True,
                                create_pr=True,
                                auto_commit=True,
                                create_new_files=False
                            )

                        if apply_result["success"]:
                            status_msg = f"✅ Successfully applied {apply_result['changes']} changes!\n\n"
                            status_msg += f"Branch: {apply_result['branch_name']}\n"

                            if apply_result['pr_url']:
                                status_msg += f"Pull Request: {apply_result['pr_url']}\n\n"

                            status_msg += "Details:\n" + "\n".join(apply_result['messages'])
                            return status_msg, outputs, export_paths
                        else:
                            error_msg = "❌ Failed to apply changes:\n\n"
                            error_msg += "\n".join(apply_result['messages'])
                            return error_msg, outputs, export_paths

                    except Exception as e:
                        return f"Error applying changes: {str(e)}", outputs, export_paths
                elif apply_to_github:
                    # User provided GitHub URL in the GitHub URL field
                    try:
                        log_agent_message("System", f"Applying changes to GitHub repository: {github_url}")

                        apply_result = apply_agent_changes_from_github(
                            agent_outputs=outputs,
                            github_url=github_url,
                            create_branch=True,
                            create_pr=True,
                            auto_commit=True,
                            create_new_files=False,
                            cleanup_after=True
                        )

                        if apply_result["success"]:
                            status_msg = f"✅ Successfully applied {apply_result['changes']} changes!\n\n"
                            status_msg += f"Branch: {apply_result['branch_name']}\n"

                            if apply_result['pr_url']:
                                status_msg += f"Pull Request: {apply_result['pr_url']}\n\n"

                            status_msg += "Details:\n" + "\n".join(apply_result['messages'])
                            return status_msg, outputs, export_paths
                        else:
                            error_msg = "❌ Failed to apply changes:\n\n"
                            error_msg += "\n".join(apply_result['messages'])
                            return error_msg, outputs, export_paths

                    except Exception as e:
                        return f"Error applying changes to GitHub: {str(e)}", outputs, export_paths
                else:
                    # Original behavior: create new git repo
                    try:
                        repo_path = create_git_repo(project_description, outputs)
                        return f"Project approved!\nGit repo created at: {repo_path}", outputs, export_paths
                    except Exception as e:
                        return f"Project approved but Git repo creation failed: {str(e)}", outputs, export_paths

            status_msg = f"Run complete! Processed {len(selected_agents)} agent(s) successfully."
            if export_paths:
                status_msg += f"\n\nExported to:\n- JSON: {export_paths['json']}\n- Markdown: {export_paths['markdown']}\n- CSV: {export_paths['csv']}"

            return status_msg, outputs, export_paths

        except Exception as e:
            error_msg = f"Error during task execution: {str(e)}\nCheck agent logs for details."
            log_agent_message("System", error_msg)
            # Still return partial outputs if available
            outputs = {role: "\n".join(agent_logs[role]) for role in agent_logs if agent_logs[role]}
            return error_msg, outputs, None

    except Exception as e:
        error_msg = f"Critical error in run_dev_team: {str(e)}"
        print(error_msg)  # Log to console for debugging
        return error_msg, {}, None

# ==============================
# Gradio Dashboard (Enhanced with agent selection, custom prompts, exports)
# ==============================
def update_logs():
    """Update all agent log displays"""
    return ["\n".join(agent_logs[role]) for role in AGENT_ROLES]

def create_custom_prompt_inputs():
    """Create custom prompt inputs for each agent"""
    prompt_inputs = {}
    for role in AGENT_ROLES:
        # Get default prompt from either DEFAULT_PROMPTS or agents.config.json
        if role in DEFAULT_PROMPTS:
            default_prompt = DEFAULT_PROMPTS[role]
        elif AGENT_CONFIGS_DYNAMIC and role in AGENT_CONFIGS_DYNAMIC:
            default_prompt = AGENT_CONFIGS_DYNAMIC[role].get('defaultPrompt', 'Execute task for this agent')
        else:
            default_prompt = "Custom prompt for this agent..."

        prompt_inputs[role] = gr.Textbox(
            label=f"{role} Agent Prompt",
            placeholder=default_prompt,
            lines=3,
            value=""
        )
    return prompt_inputs

def export_handler(format_type, project_desc, selected_agents_list):
    """Handle manual export requests"""
    try:
        if not selected_agents_list or len(selected_agents_list) == 0:
            return "Error: No agents selected. Run the team first."

        outputs = {role: "\n".join(agent_logs[role]) for role in agent_logs if agent_logs[role]}

        if not outputs:
            return "Error: No outputs to export. Run the team first."

        if format_type == "json":
            path = export_to_json(project_desc[:100], selected_agents_list, outputs)
        elif format_type == "markdown":
            path = export_to_markdown(project_desc[:100], selected_agents_list, outputs)
        elif format_type == "csv":
            path = export_to_csv(project_desc[:100], selected_agents_list, outputs)
        elif format_type == "all":
            paths = export_all_formats(project_desc[:100], selected_agents_list, outputs)
            return f"Exported successfully!\n\nJSON: {paths['json']}\nMarkdown: {paths['markdown']}\nCSV: {paths['csv']}"
        else:
            return f"Error: Unknown format '{format_type}'"

        return f"Exported successfully to:\n{path}"
    except Exception as e:
        return f"Export failed: {str(e)}"

def export_individual_handler(role, project_desc):
    """Handle individual agent export"""
    try:
        if role not in agent_logs or not agent_logs[role]:
            return f"Error: No output found for {role} agent. Run it first."

        output = "\n".join(agent_logs[role])
        path = export_individual_agent(role, output, project_desc[:100])
        return f"Exported {role} findings to:\n{path}"
    except Exception as e:
        return f"Export failed: {str(e)}"

# ==============================
# YAML Workflow Import Handlers
# ==============================

def handle_yaml_import(yaml_file_path):
    """
    Handle YAML workflow import and populate Gradio fields

    Returns:
        Tuple of (status_message, workflow_preview, agents_update, project_name_update, preview_visible, workflow_viz_html)
    """
    if not YAML_PARSER_AVAILABLE:
        return (
            "❌ YAML parser not available. Install workflow_yaml_parser.py",
            None,
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update()
        )

    try:
        if not yaml_file_path:
            return (
                "⚠️ No file selected. Please select a YAML workflow file.",
                None,
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update()
            )

        # Parse YAML workflow
        workflow = parse_workflow_yaml(yaml_file_path)

        # Validate workflow
        is_valid, errors, warnings = validate_workflow(workflow)

        # Build status message
        status_msg = format_import_summary(workflow)

        # Add validation results
        if errors:
            status_msg += "\n\n❌ Validation Errors:\n"
            for error in errors:
                status_msg += f"  • {error}\n"

        if warnings:
            status_msg += "\n\n⚠️ Warnings:\n"
            for warning in warnings:
                status_msg += f"  • {warning}\n"

        # Filter agents to only include those in AGENT_ROLES
        valid_agents = [
            agent_id for agent_id in workflow['agents']
            if agent_id in AGENT_ROLES
        ]

        skipped_agents = [
            agent_id for agent_id in workflow['agents']
            if agent_id not in AGENT_ROLES
        ]

        if skipped_agents:
            status_msg += f"\n\n⚠️ Skipped unknown agents: {', '.join(skipped_agents)}"
            status_msg += "\n(Custom agents from Workflow Builder are not yet supported in Gradio Platform)"

        # Prepare workflow preview data
        preview_data = {
            "name": workflow['name'],
            "agents": workflow['agents'],
            "agent_count": len(workflow['agents']),
            "custom_prompts": list(workflow['custom_prompts'].keys()),
            "model_overrides": list(workflow['models'].keys()),
            "priorities": workflow['priorities']
        }

        # Generate workflow visualization if available
        workflow_viz_html = ""
        if WORKFLOW_VIZ_AVAILABLE:
            try:
                workflow_viz_html = generate_workflow_graph(workflow)
                workflow_viz_html += generate_execution_status_legend()
            except Exception as viz_error:
                workflow_viz_html = f"<div style='padding: 20px; color: #F59E0B;'>⚠️ Could not generate workflow visualization: {str(viz_error)}</div>"
        else:
            workflow_viz_html = "<div style='padding: 20px; color: #666;'>⚠️ Workflow visualization not available. Install graphviz: pip install graphviz</div>"

        return (
            status_msg,
            preview_data,
            gr.update(value=valid_agents),  # Update agent selector
            gr.update(value=workflow['name']),  # Update project name
            gr.update(visible=True),  # Show preview
            gr.update(value=workflow_viz_html, visible=True)  # Show workflow visualization
        )

    except ValueError as e:
        return (
            f"❌ Import failed: {str(e)}\n\nPlease check that the YAML file is valid and exported from the Workflow Builder.",
            None,
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update()
        )
    except Exception as e:
        return (
            f"❌ Unexpected error during import: {str(e)}",
            None,
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update()
        )


def clear_yaml_import():
    """Clear YAML import status and preview"""
    return (
        "Import cleared. You can import a new workflow.",
        None,
        gr.update(visible=False),
        gr.update(value="", visible=False)  # Clear workflow visualization
    )


# Load custom CSS theme
def load_custom_css():
    """Load custom CSS theme from gradio_theme.css"""
    css_file = Path(__file__).parent / "gradio_theme.css"
    if css_file.exists():
        with open(css_file, 'r', encoding='utf-8') as f:
            return f.read()
    return ""


# Initialize Projects Store
projects_store = ProjectsStore()

# Build the enhanced Gradio interface
with gr.Blocks(title="Super Dev Team") as demo:
    gr.Markdown("# 🚀 Super Multi-Agent Dev Team")
    gr.Markdown("**Market-Smart • Lean • Hallucination-Resistant • Fully Customizable**")

    with gr.Tabs():
        # TAB 1: PROJECTS & TEAMS
        with gr.TabItem("📁 Projects & Teams"):
            gr.Markdown("## Multi-Team Project Management")
            gr.Markdown("*Create projects, add sequential teams, execute with checkpoints*")

            with gr.Row():
                with gr.Column(scale=1):
                    # Project Management Section
                    gr.Markdown("### Your Projects")

                    project_list = gr.Dropdown(
                        choices=[],
                        label="Select Project",
                        info="Choose a project to view or manage"
                    )

                    with gr.Row():
                        new_project_btn = gr.Button("➕ New Project", size="sm")
                        delete_project_btn = gr.Button("🗑️ Delete", size="sm", variant="stop")
                        refresh_projects_btn = gr.Button("🔄 Refresh", size="sm")

                    project_status_msg = gr.Textbox(label="Status", interactive=False, lines=2)

                with gr.Column(scale=2):
                    # Project Details & Teams
                    gr.Markdown("### Project Details")

                    project_details_html = gr.HTML(value="<p>Select a project to view details</p>")

                    teams_list_html = gr.HTML(value="<p>No teams added yet</p>")

                    # Team Toggle Controls
                    with gr.Accordion("🔀 Enable/Disable Teams", open=True):
                        gr.Markdown("*Toggle teams on/off for execution*")
                        team_toggles = gr.CheckboxGroup(
                            choices=[],
                            value=[],
                            label="Enabled Teams",
                            info="Only checked teams will run"
                        )
                        with gr.Row():
                            update_toggles_btn = gr.Button("💾 Save Team Settings", variant="primary", size="sm")
                            enable_all_btn = gr.Button("✓ Enable All", size="sm")
                            disable_all_btn = gr.Button("✗ Disable All", size="sm")

                    # Quick Team Selection
                    with gr.Accordion("⚡ Quick Add Team Presets", open=False):
                        gr.Markdown("*Select team presets to add to your project*")

                        # Group presets by category
                        presets_by_category = get_team_presets_by_category()
                        team_preset_checkboxes = {}

                        for category, preset_names in presets_by_category.items():
                            with gr.Accordion(f"{category} ({len(preset_names)} teams)", open=False):
                                team_preset_checkboxes[category] = gr.CheckboxGroup(
                                    choices=preset_names,
                                    label=f"{category} Teams",
                                    info=f"Select teams from {category}"
                                )

                        with gr.Row():
                            add_selected_teams_btn = gr.Button("➕ Add Selected Teams", variant="primary")
                            clear_selection_btn = gr.Button("Clear Selection", variant="secondary")

                    with gr.Row():
                        add_team_btn_show = gr.Button("➕ Custom Team", variant="secondary", size="sm")
                        run_project_btn = gr.Button("▶️ Run Project", variant="primary", size="lg")

            # New Project Form (hidden by default)
            with gr.Group(visible=False) as new_project_form:
                gr.Markdown("### Create New Project")

                template_selector = gr.Dropdown(
                    choices=["Blank Project"] + get_template_names(),
                    value="Blank Project",
                    label="Template",
                    info="Start with a pre-built template or blank project"
                )

                new_project_name = gr.Textbox(label="Project Name", placeholder="My Project")
                new_project_desc = gr.Textbox(label="Description", lines=3, placeholder="What are you building?")

                with gr.Row():
                    create_project_btn = gr.Button("Create Project", variant="primary")
                    cancel_new_project_btn = gr.Button("Cancel")

            # Team Builder (hidden by default)
            with gr.Group(visible=False) as team_builder_form:
                gr.Markdown("### Add Team to Project")

                # Team preset selector
                team_preset_selector = gr.Dropdown(
                    choices=["Custom Team (Blank)"] + get_team_preset_names(),
                    value="Custom Team (Blank)",
                    label="Team Preset",
                    info="Select a pre-configured team or start from scratch"
                )

                new_team_name = gr.Textbox(label="Team Name", placeholder="Backend Squad")
                new_team_desc = gr.Textbox(label="Description", lines=2, placeholder="What will this team do?")

                # Reuse the existing agent selector grouping
                new_team_agents = gr.CheckboxGroup(
                    choices=AGENT_ROLES,
                    label="Team Agents",
                    info="Select agents for this team (execute sequentially)"
                )

                with gr.Row():
                    add_team_btn = gr.Button("Add Team", variant="primary")
                    cancel_team_btn = gr.Button("Cancel")

        # TAB 2: QUICK RUN (existing UI)
        with gr.TabItem("⚡ Quick Run"):
            gr.Markdown("*Single execution mode - run agents immediately*")

            with gr.Row():
                with gr.Column(scale=2):
                    # Project configuration section
                    gr.Markdown("## 📋 Project Configuration")
                    project_input = gr.Textbox(
                label="Project Description",
                lines=5,
                placeholder="Describe your project in detail..."
            )

            github_url_input = gr.Textbox(
                label="GitHub Repository URL (Optional)",
                lines=1,
                placeholder="https://github.com/username/repository (for direct code analysis from GitHub)",
                info="Provide a GitHub URL to clone and analyze. Leave blank for text-only project descriptions."
            )

            # YAML Workflow Import Section
            if YAML_PARSER_AVAILABLE:
                with gr.Accordion("📥 Import Workflow from YAML", open=True):
                    gr.Markdown("""
**Import workflows designed in the Visual Workflow Builder**

Upload a `.yaml` file exported from the Workflow Builder to automatically configure agents, prompts, models, and execution order.
                    """)

                    yaml_file_input = gr.File(
                        label="Select YAML Workflow File",
                        file_types=[".yaml", ".yml"],
                        type="filepath"
                    )

                    with gr.Row():
                        import_button = gr.Button("📥 Import Workflow", variant="primary", size="sm")
                        clear_import_button = gr.Button("🗑️ Clear Import", variant="secondary", size="sm")

                    import_status = gr.Textbox(
                        label="Import Status",
                        lines=4,
                        interactive=False,
                        placeholder="No workflow imported yet..."
                    )

                    workflow_preview = gr.JSON(
                        label="Workflow Preview",
                        visible=False
                    )

                    workflow_viz = gr.HTML(
                        label="Workflow Visualization",
                        visible=False
                    )

            # Agent selection
            gr.Markdown("## 🤖 Select Agents to Execute")

            # Agent presets dropdown
            agent_preset_dropdown = gr.Dropdown(
                choices=["Custom Selection"] + list(AGENT_PRESETS.keys()),
                value="New Project Development",
                label="Agent Preset",
                info="Quick select common agent combinations"
            )

            # Grouped agent selectors by category
            agents_by_category = get_agents_by_category()
            agent_selectors_by_category = {}

            gr.Markdown("### 📂 Agents Organized by Category")
            gr.Markdown("*Select agents from each category below. Teams are organized by expertise area.*")

            for category, agent_ids in agents_by_category.items():
                with gr.Accordion(f"{category} ({len(agent_ids)} agents)", open=(category in ["Management", "Engineering", "Product & Design"])):
                    agent_selectors_by_category[category] = gr.CheckboxGroup(
                        choices=agent_ids,
                        value=[aid for aid in agent_ids if aid in ["PM", "Memory", "Research", "Ideas", "Designs", "QA", "Senior"]],  # Default selections
                        label=f"{category} Agents",
                        info=f"Select from {len(agent_ids)} {category.lower()} agents"
                    )

            # Merged selection display (updated dynamically from category selections)
            with gr.Accordion("✅ Selected Agents Summary", open=False):
                agent_selector = gr.CheckboxGroup(
                    choices=AGENT_ROLES,
                    value=["PM", "Memory", "Research", "Ideas", "Designs", "QA", "Senior"],
                    label="All Selected Agents",
                    info="Combined selection from all categories above. You can also manually adjust here.",
                    interactive=True
                )

            # Code Review Mode toggle
            code_review_checkbox = gr.Checkbox(
                label="Code Review Mode",
                value=False,
                info="Optimize prompts for code analysis (Senior, QA, Verifier agents)"
            )

            # Execution Priority Configuration
            gr.Markdown("## 🔢 Execution Priority (Optional)")
            with gr.Accordion("Configure Agent Execution Order", open=False) as priority_accordion:
                gr.Markdown("""
**Lower number = runs first** | Agents with same priority can run in parallel

**Default order:**
1. Memory, PM → 2. Research → 3. Ideas → 4. Designs → 5. iOS/Android/Web → 6. Senior → 7. QA → 8. Verifier

*Only showing priority controls for selected agents*
                """)
                priority_inputs = {}

                # Create priority inputs for ALL agents, but hide them initially
                for role in AGENT_ROLES:
                    # Default visible agents (PM, Memory, Research, etc.)
                    default_visible = role in ["PM", "Memory", "Research", "Ideas", "Designs", "QA", "Senior"]

                    priority_inputs[role] = gr.Number(
                        label=f"{role}",
                        value=AGENT_EXECUTION_PRIORITY.get(role, 10),
                        minimum=1,
                        maximum=20,
                        step=1,
                        precision=0,
                        visible=default_visible
                    )

            # Custom prompts section (collapsible)
            gr.Markdown("## ✏️ Custom Prompts (Optional)")
            with gr.Accordion("Override Agent Prompts", open=False):
                gr.Markdown("*Leave blank to use default prompts. Use {project_description} as placeholder. Only showing selected agents.*")
                custom_prompt_inputs = {}
                for role in AGENT_ROLES:
                    # Get default prompt from either DEFAULT_PROMPTS or agents.config.json
                    if role in DEFAULT_PROMPTS:
                        default_prompt = DEFAULT_PROMPTS[role][:100] + "..."
                    elif AGENT_CONFIGS_DYNAMIC and role in AGENT_CONFIGS_DYNAMIC:
                        prompt = AGENT_CONFIGS_DYNAMIC[role].get('defaultPrompt', 'Execute task for this agent')
                        default_prompt = prompt[:100] + "..." if len(prompt) > 100 else prompt
                    else:
                        default_prompt = "Custom prompt for this agent..."

                    # Default visible agents
                    default_visible = role in ["PM", "Memory", "Research", "Ideas", "Designs", "QA", "Senior"]

                    custom_prompt_inputs[role] = gr.Textbox(
                        label=f"{role} Custom Prompt",
                        placeholder=default_prompt,
                        lines=2,
                        value="",
                        visible=default_visible
                    )

            # Model selection section
            gr.Markdown("## 🤖 Model Selection")
            model_preset_dropdown = gr.Dropdown(
                choices=list(MODEL_PRESETS.keys()),
                value="Speed (All Haiku)",
                label="Model Preset",
                info="💡 Speed = faster & cheaper | Balanced = good quality | Quality = best results for critical agents"
            )

            # Per-agent model override (advanced)
            with gr.Accordion("Advanced: Per-Agent Model Override", open=False):
                gr.Markdown("*Override individual agent models. Leave as 'Use Default' to follow preset. Only showing selected agents.*")
                custom_model_inputs = {}
                model_choices = ["Use Default"] + [f"{v['name']} ({v['cost']} cost, {v['speed']} speed)"
                                                    for k, v in AVAILABLE_MODELS.items()]
                model_ids = ["Use Default"] + list(AVAILABLE_MODELS.keys())

                for role in AGENT_ROLES:
                    # Default visible agents
                    default_visible = role in ["PM", "Memory", "Research", "Ideas", "Designs", "QA", "Senior"]

                    custom_model_inputs[role] = gr.Dropdown(
                        choices=model_choices,
                        value="Use Default",
                        label=f"{role} Model",
                        visible=default_visible
                    )

            # Execution controls
            gr.Markdown("## ⚙️ Execution Controls")
            with gr.Row():
                phase_dropdown = gr.Dropdown(
                    choices=PHASE_CHOICES,
                    value=PHASE_CHOICES[3],
                    label="Execution Phase"
                )
                auto_export_checkbox = gr.Checkbox(
                    label="Auto-export results",
                    value=True,
                    info="Automatically export to all formats after run"
                )

            feedback_input = gr.Textbox(
                label="Feedback / Apply Target",
                lines=2,
                placeholder="Optional: Feedback for reruns OR 'APPLY: C:\\path\\to\\repo' OR 'APPLY: https://github.com/user/repo' to apply changes"
            )

            approval_dropdown = gr.Dropdown(
                choices=["Run (No Approval Yet)", "Approve", "Reject and Rerun"],
                label="Action",
                value="Run (No Approval Yet)"
            )

            # Action buttons
            gr.Markdown("### ⚡ Execute Workflow")
            gr.Markdown("*Ready to run? Click below to start agent execution*")

            with gr.Row():
                run_button = gr.Button("▶️ Run Team", variant="primary", size="lg")
                clear_button = gr.Button("🗑️ Clear Logs", variant="secondary")

            # Status display
            status_output = gr.Textbox(label="📊 Execution Status", lines=4, interactive=False)

        with gr.Column(scale=1):
            # Quick actions panel
            gr.Markdown("## 📤 Export Results")
            gr.Markdown("*Save agent outputs to files for documentation or sharing*")

            with gr.Row():
                export_json_btn = gr.Button("📄 JSON", size="sm")
                export_md_btn = gr.Button("📝 Markdown", size="sm")
                export_csv_btn = gr.Button("📊 CSV", size="sm")

            export_all_btn = gr.Button("📦 Export All Formats", variant="primary")
            export_status = gr.Textbox(label="Export Status", lines=3, interactive=False, placeholder="No exports yet...")

            gr.Markdown("## 📊 Quick Stats")
            stats_display = gr.Textbox(
                label="Session Info",
                value="Ready to start...",
                lines=5,
                interactive=False
            )

    # Agent outputs section with tabs
    gr.Markdown("---")
    gr.Markdown("## 📝 Agent Outputs")
    gr.Markdown("*Individual agent findings and logs (updates after each run)*")

    log_outputs = []
    export_individual_buttons = []

    with gr.Tabs() as agent_output_tabs:
        for role in AGENT_ROLES:
            with gr.Tab(label=role):
                log_output = gr.Textbox(
                    label=f"{role} Output",
                    lines=20,
                    interactive=False,
                    placeholder=f"No output yet for {role}..."
                )
                log_outputs.append(log_output)

                export_btn = gr.Button(f"📥 Export {role} Output", size="sm", variant="secondary")
                export_individual_buttons.append(export_btn)

    # Event handlers
    def merge_category_selections(*category_selections):
        """Merge all category checkbox selections into a single list"""
        merged = []
        for selection in category_selections:
            if selection:
                merged.extend(selection)
        return merged

    def update_agent_selection_grouped(preset_name):
        """Update agent selection based on preset - returns updates for all category groups"""
        if preset_name == "Custom Selection" or preset_name not in AGENT_PRESETS:
            return tuple([gr.update() for _ in agents_by_category])  # No change

        preset_agents = AGENT_PRESETS.get(preset_name, [])
        updates = []

        for category, agent_ids in agents_by_category.items():
            # Select agents that are both in this category and in the preset
            selected = [aid for aid in agent_ids if aid in preset_agents]
            updates.append(gr.update(value=selected))

        return tuple(updates)

    def run_and_update(project, selected, github_url, *args):
        """Main execution handler - receives all individual inputs and builds dictionaries"""
        try:
            # Parse args into structured data
            # Expected order: 11 custom prompts, 1 model preset, 11 custom models, 11 priorities, 1 code_review, 4 execution params
            num_roles = len(AGENT_ROLES)

            # Extract custom prompts (first 11 args)
            custom_prompt_values = args[0:num_roles]
            prompts = {role: val for role, val in zip(AGENT_ROLES, custom_prompt_values) if val}

            # Extract model preset (arg 11)
            model_preset = args[num_roles]

            # Extract custom models (args 12-22)
            custom_model_values = args[num_roles + 1:num_roles + 1 + num_roles]
            custom_models = {}
            for role, model_choice in zip(AGENT_ROLES, custom_model_values):
                if model_choice and model_choice != "Use Default":
                    # Extract model ID from the choice (format: "Opus (High cost, Slow speed)")
                    for model_id, model_info in AVAILABLE_MODELS.items():
                        if model_info["name"] in model_choice:
                            custom_models[role] = model_id
                            break

            # Extract priorities (args 23-33)
            priority_values = args[num_roles + 1 + num_roles:num_roles + 1 + num_roles + num_roles]
            custom_priorities = {role: val for role, val in zip(AGENT_ROLES, priority_values)}

            # Extract remaining parameters (args 34-38)
            remaining_start = num_roles + 1 + num_roles + num_roles
            code_review_mode = args[remaining_start]
            feedback = args[remaining_start + 1]
            action = args[remaining_start + 2]
            phase = args[remaining_start + 3]
            auto_export = args[remaining_start + 4]

            # Run the team
            status_msg, outputs, export_paths = run_dev_team(
                project,
                selected,
                github_url,
                prompts,
                model_preset,
                custom_models,
                custom_priorities,
                code_review_mode,
                feedback,
                action,
                phase,
                auto_export
            )

            # Update logs
            logs = update_logs()

            # Update stats
            stats = f"Agents Run: {len(selected)}\nModel Preset: {model_preset}\nLast Run: {datetime.now().strftime('%H:%M:%S')}\nStatus: Completed"
            if export_paths:
                stats += f"\n\nAuto-exported:\n✓ JSON\n✓ Markdown\n✓ CSV"

            return (status_msg, stats) + tuple(logs)

        except Exception as e:
            error_msg = f"Error in run_and_update: {str(e)}"
            return (error_msg, "Error occurred") + tuple([""] * len(AGENT_ROLES))

    def clear_all_logs():
        """Clear all agent logs"""
        for role in agent_logs:
            agent_logs[role] = []
        return ("Logs cleared.", "Ready to start...") + tuple([""] * len(AGENT_ROLES))

    # Wire up the run button
    run_inputs = [project_input, agent_selector, github_url_input] + \
                 [custom_prompt_inputs[role] for role in AGENT_ROLES] + \
                 [model_preset_dropdown] + \
                 [custom_model_inputs[role] for role in AGENT_ROLES] + \
                 [priority_inputs[role] for role in AGENT_ROLES] + \
                 [code_review_checkbox] + \
                 [feedback_input, approval_dropdown, phase_dropdown, auto_export_checkbox]

    run_button.click(
        run_and_update,
        inputs=run_inputs,
        outputs=[status_output, stats_display] + log_outputs
    )

    clear_button.click(
        clear_all_logs,
        inputs=[],
        outputs=[status_output, stats_display] + log_outputs
    )

    # Agent preset dropdown handler - updates both category groups and main selector
    agent_preset_dropdown.change(
        update_agent_selection_grouped,
        inputs=[agent_preset_dropdown],
        outputs=list(agent_selectors_by_category.values())
    )

    # Sync category selections to main agent selector
    for category_selector in agent_selectors_by_category.values():
        category_selector.change(
            merge_category_selections,
            inputs=list(agent_selectors_by_category.values()),
            outputs=[agent_selector]
        )

    # Update visibility of priority/prompt/model inputs based on selected agents
    def update_input_visibility(selected_agents):
        """Show/hide priority, prompt, and model inputs based on selected agents"""
        updates = []

        # For each agent, show input if selected, hide if not
        for role in AGENT_ROLES:
            is_visible = role in selected_agents
            # Add 3 updates for each agent: priority, custom_prompt, custom_model
            updates.append(gr.update(visible=is_visible))  # priority
            updates.append(gr.update(visible=is_visible))  # custom_prompt
            updates.append(gr.update(visible=is_visible))  # custom_model

        return updates

    # When agent selection changes, update visibility of all inputs
    agent_selector.change(
        update_input_visibility,
        inputs=[agent_selector],
        outputs=[
            # Interleave priority, custom_prompt, and custom_model for each agent
            val for role in AGENT_ROLES
            for val in [priority_inputs[role], custom_prompt_inputs[role], custom_model_inputs[role]]
        ]
    )

    # YAML Import button handlers
    if YAML_PARSER_AVAILABLE:
        import_button.click(
            handle_yaml_import,
            inputs=[yaml_file_input],
            outputs=[import_status, workflow_preview, agent_selector, project_input, workflow_preview, workflow_viz]
        )

        clear_import_button.click(
            clear_yaml_import,
            inputs=[],
            outputs=[import_status, workflow_preview, workflow_preview, workflow_viz]
        )

    # Export button handlers
    export_json_btn.click(
        lambda p, s: export_handler("json", p, s),
        inputs=[project_input, agent_selector],
        outputs=[export_status]
    )

    export_md_btn.click(
        lambda p, s: export_handler("markdown", p, s),
        inputs=[project_input, agent_selector],
        outputs=[export_status]
    )

    export_csv_btn.click(
        lambda p, s: export_handler("csv", p, s),
        inputs=[project_input, agent_selector],
        outputs=[export_status]
    )

    export_all_btn.click(
        lambda p, s: export_handler("all", p, s),
        inputs=[project_input, agent_selector],
        outputs=[export_status]
    )

    # Individual agent export handlers
    for i, (role, btn) in enumerate(zip(AGENT_ROLES, export_individual_buttons)):
        btn.click(
            lambda p, r=role: export_individual_handler(r, p),
            inputs=[project_input],
            outputs=[export_status]
        )

    # ===== PROJECTS & TEAMS EVENT HANDLERS =====

    def toggle_new_project_form(visible):
        """Show/hide new project form"""
        return gr.update(visible=not visible)

    def load_projects_list():
        """Load all projects into dropdown"""
        projects = projects_store.list_projects()
        choices = [(f"{p['name']} ({len(p['teams'])} teams)", p['id']) for p in projects]
        return gr.update(choices=choices, value=None)

    def create_new_project(template_name, name, description):
        """Create a new project"""
        try:
            if not name:
                return "Error: Project name required", gr.update(), gr.update(visible=True)

            project_id = projects_store.create_project(name, description)

            # Add teams from template if selected
            if template_name != "Blank Project":
                template = get_template(template_name)
                if template:
                    for team_data in template.get("teams", []):
                        projects_store.add_team(
                            project_id,
                            team_data["name"],
                            team_data["agents"],
                            team_data.get("description", ""),
                            validate_agents=False
                        )

            projects = projects_store.list_projects()
            choices = [(f"{p['name']} ({len(p['teams'])} teams)", p['id']) for p in projects]

            return (
                f"✅ Project '{name}' created!",
                gr.update(choices=choices, value=project_id),
                gr.update(visible=False)
            )
        except Exception as e:
            return f"Error: {str(e)}", gr.update(), gr.update(visible=True)

    def load_project_details(project_id):
        """Load and display project details"""
        if not project_id:
            return (
                "<p>Select a project</p>",
                "<p>No teams</p>",
                "",
                gr.update(choices=[], value=[])
            )

        project = projects_store.get_project(project_id)
        if not project:
            return (
                "<p>Project not found</p>",
                "<p>No teams</p>",
                "",
                gr.update(choices=[], value=[])
            )

        # Format project details
        details_html = f"""
        <div style="padding: 12px; background: #f9f9f9; border-radius: 8px;">
            <h3>{escape_html(project['name'])}</h3>
            <p>{escape_html(project.get('description', 'No description'))}</p>
            <p style="font-size: 12px; color: #666;">
                Created: {project.get('createdAt', 'Unknown')}<br/>
                Teams: {len(project.get('teams', []))}
            </p>
        </div>
        """

        # Format teams list
        teams = project.get('teams', [])
        if not teams:
            teams_html = "<p>No teams added yet. Click 'Add Team' to create one.</p>"
            team_toggle_choices = []
            team_toggle_values = []
        else:
            teams_html = "".join([
                render_team_card_safe(team, i) for i, team in enumerate(teams)
            ])

            # Prepare team toggle checkboxes
            team_toggle_choices = [team['name'] for team in teams]
            team_toggle_values = [team['name'] for team in teams if team.get('enabled', True)]

        return (
            details_html,
            teams_html,
            f"Project '{project['name']}' loaded",
            gr.update(choices=team_toggle_choices, value=team_toggle_values)
        )

    def delete_current_project(project_id):
        """Delete the selected project"""
        if not project_id:
            return "No project selected", gr.update()

        project = projects_store.get_project(project_id)
        if not project:
            return "Project not found", gr.update()

        name = project['name']
        projects_store.delete_project(project_id)

        projects = projects_store.list_projects()
        choices = [(f"{p['name']} ({len(p['teams'])} teams)", p['id']) for p in projects]

        return f"✅ Project '{name}' deleted", gr.update(choices=choices, value=None)

    # Wire up Projects & Teams event handlers
    new_project_btn.click(
        lambda: gr.update(visible=True),
        outputs=[new_project_form]
    )

    cancel_new_project_btn.click(
        lambda: gr.update(visible=False),
        outputs=[new_project_form]
    )

    create_project_btn.click(
        create_new_project,
        inputs=[template_selector, new_project_name, new_project_desc],
        outputs=[project_status_msg, project_list, new_project_form]
    )

    refresh_projects_btn.click(
        load_projects_list,
        outputs=[project_list]
    )

    project_list.change(
        load_project_details,
        inputs=[project_list],
        outputs=[project_details_html, teams_list_html, project_status_msg, team_toggles]
    )

    delete_project_btn.click(
        delete_current_project,
        inputs=[project_list],
        outputs=[project_status_msg, project_list]
    )

    # Team builder event handlers
    add_team_btn_show.click(
        lambda: gr.update(visible=True),
        outputs=[team_builder_form]
    )

    cancel_team_btn.click(
        lambda: gr.update(visible=False),
        outputs=[team_builder_form]
    )

    def load_team_preset(preset_name):
        """Auto-populate team fields when preset is selected"""
        if preset_name == "Custom Team (Blank)":
            # Reset to blank
            return (
                gr.update(value=""),  # team name
                gr.update(value=""),  # team description
                gr.update(value=[])   # team agents
            )

        preset = get_team_preset(preset_name)
        if not preset:
            return gr.update(), gr.update(), gr.update()

        return (
            gr.update(value=preset_name),  # Use preset name as team name
            gr.update(value=preset.get("description", "")),
            gr.update(value=preset.get("agents", []))
        )

    team_preset_selector.change(
        load_team_preset,
        inputs=[team_preset_selector],
        outputs=[new_team_name, new_team_desc, new_team_agents]
    )

    def add_new_team(project_id, team_name, team_desc, team_agents):
        """Add a new team to the selected project"""
        try:
            if not project_id:
                return "Error: No project selected", "<p>No teams</p>", gr.update(visible=True)

            if not team_name:
                return "Error: Team name required", gr.update(), gr.update(visible=True)

            if not team_agents:
                return "Error: Select at least one agent", gr.update(), gr.update(visible=True)

            # Add team to project
            team_id = projects_store.add_team(
                project_id,
                team_name,
                team_agents,
                team_desc,
                validate_agents=False  # Allow custom agents
            )

            if not team_id:
                return "Error: Project not found", gr.update(), gr.update(visible=True)

            # Refresh teams display
            project = projects_store.get_project(project_id)
            teams = project.get('teams', [])
            teams_html = "".join([
                render_team_card_safe(team, i) for i, team in enumerate(teams)
            ])

            return (
                f"✅ Team '{team_name}' added with {len(team_agents)} agents!",
                teams_html,
                gr.update(visible=False)
            )

        except Exception as e:
            return f"Error: {str(e)}", gr.update(), gr.update(visible=True)

    add_team_btn.click(
        add_new_team,
        inputs=[project_list, new_team_name, new_team_desc, new_team_agents],
        outputs=[project_status_msg, teams_list_html, team_builder_form]
    )

    # Quick Add Selected Teams handler
    def add_selected_team_presets(project_id, *selected_teams_by_category):
        """Add multiple team presets at once"""
        try:
            if not project_id:
                return "Error: No project selected", gr.update()

            # Flatten all selected teams from all categories
            all_selected_teams = []
            for category_teams in selected_teams_by_category:
                if category_teams:
                    all_selected_teams.extend(category_teams)

            if not all_selected_teams:
                return "Error: No teams selected", gr.update()

            # Add each selected team preset
            added_count = 0
            for preset_name in all_selected_teams:
                preset = get_team_preset(preset_name)
                if preset:
                    team_id = projects_store.add_team(
                        project_id,
                        preset_name,  # Use preset name as team name
                        preset.get("agents", []),
                        preset.get("description", ""),
                        validate_agents=False
                    )
                    if team_id:
                        added_count += 1

            # Refresh teams display
            project = projects_store.get_project(project_id)
            teams = project.get('teams', [])
            teams_html = "".join([
                render_team_card_safe(team, i) for i, team in enumerate(teams)
            ])

            return (
                f"✅ Added {added_count} teams to project!",
                teams_html
            )

        except Exception as e:
            return f"Error: {str(e)}", gr.update()

    # Collect all checkbox group inputs for the event handler
    all_checkbox_inputs = [project_list] + list(team_preset_checkboxes.values())

    add_selected_teams_btn.click(
        add_selected_team_presets,
        inputs=all_checkbox_inputs,
        outputs=[project_status_msg, teams_list_html]
    )

    # Clear selection handler
    def clear_team_selections():
        """Clear all team preset selections"""
        # Return empty list for each checkbox group
        return [gr.update(value=[]) for _ in team_preset_checkboxes]

    clear_selection_btn.click(
        clear_team_selections,
        outputs=list(team_preset_checkboxes.values())
    )

    # Team toggle event handlers
    def update_team_toggles(project_id, enabled_team_names):
        """Update which teams are enabled/disabled"""
        try:
            if not project_id:
                return "Error: No project selected", gr.update()

            project = projects_store.get_project(project_id)
            if not project:
                return "Error: Project not found", gr.update()

            # Update each team's enabled status
            for team in project['teams']:
                should_be_enabled = team['name'] in enabled_team_names
                current_enabled = team.get('enabled', True)

                # Only toggle if status changed
                if should_be_enabled != current_enabled:
                    projects_store.toggle_team_enabled(project_id, team['id'])

            # Refresh teams display
            teams = project.get('teams', [])
            teams_html = "".join([
                render_team_card_safe(team, i) for i, team in enumerate(teams)
            ])

            enabled_count = len(enabled_team_names)
            total_count = len(teams)

            return (
                f"✅ Team settings saved! {enabled_count}/{total_count} teams enabled",
                teams_html
            )

        except Exception as e:
            return f"Error: {str(e)}", gr.update()

    update_toggles_btn.click(
        update_team_toggles,
        inputs=[project_list, team_toggles],
        outputs=[project_status_msg, teams_list_html]
    )

    def enable_all_teams(project_id):
        """Enable all teams in the project"""
        try:
            project = projects_store.get_project(project_id)
            if not project:
                return gr.update()

            # Return all team names to enable them all
            team_names = [team['name'] for team in project.get('teams', [])]
            return gr.update(value=team_names)

        except Exception as e:
            return gr.update()

    enable_all_btn.click(
        enable_all_teams,
        inputs=[project_list],
        outputs=[team_toggles]
    )

    def disable_all_teams(project_id):
        """Disable all teams in the project"""
        try:
            # Return empty list to disable all teams
            return gr.update(value=[])

        except Exception as e:
            return gr.update()

    disable_all_btn.click(
        disable_all_teams,
        inputs=[project_list],
        outputs=[team_toggles]
    )

# Launch the application
if __name__ == "__main__":
    print("🚀 Launching Super Multi-Agent Dev Team...")
    print(f"📁 Exports will be saved to: {os.path.abspath(EXPORTS_DIR)}")
    print(f"📁 Projects will be saved to: {os.path.abspath(PROJECTS_DIR)}")
    demo.launch(share=False, server_name="127.0.0.1", server_port=7860, css=load_custom_css())