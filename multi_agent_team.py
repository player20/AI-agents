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
import html  # For XSS prevention via html.escape()

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

# Create agent descriptions for tooltips (role + goal)
AGENT_DESCRIPTIONS = {}
if AGENT_CONFIGS_DYNAMIC:
    for agent_id, config in AGENT_CONFIGS_DYNAMIC.items():
        role = config.get('role', agent_id)
        goal = config.get('goal', '')[:100]  # Limit goal length for tooltips
        AGENT_DESCRIPTIONS[agent_id] = f"{role} - {goal}"
else:
    # Fallback descriptions for hardcoded agents
    AGENT_DESCRIPTIONS = {
        "PM": "Project Manager - Create efficient sprint plans and coordinate team",
        "Memory": "Memory Specialist - Recall and store learnings from previous executions",
        "Research": "Market Research Analyst - Analyze market opportunities and competitive landscape",
        "Ideas": "Ideas Specialist - Generate lean, high-impact feature ideas",
        "Designs": "UI/UX Designer - Create efficient, user-centered designs",
        "Senior": "Senior Engineer - Technical leadership and architecture decisions",
        "iOS": "iOS Developer - Build native iOS applications",
        "Android": "Android Developer - Build native Android applications",
        "Web": "Web Developer - Full-stack web development",
        "QA": "Quality Assurance - Comprehensive testing and quality control",
        "Verifier": "Code Verifier - Verify code quality and implementation correctness"
    }

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
# Code Extraction & Project Generation
# ==============================
import re
from typing import Dict, List, Tuple

def extract_code_blocks(text: str) -> List[Dict[str, str]]:
    """
    Extract code blocks from markdown-formatted text.

    Returns list of dicts with: {'language': str, 'code': str, 'file_path': str or None}
    """
    code_blocks = []

    # Pattern to match ```language ... ``` blocks
    pattern = r'```(\w+)?\n(.*?)```'
    matches = re.finditer(pattern, text, re.DOTALL)

    for match in matches:
        language = match.group(1) or 'text'
        code = match.group(2).strip()

        if not code:  # Skip empty blocks
            continue

        # Try to detect file path from comments in code
        file_path = detect_file_path(code, language)

        code_blocks.append({
            'language': language,
            'code': code,
            'file_path': file_path
        })

    return code_blocks

def detect_file_path(code: str, language: str) -> str or None:
    """
    Detect file path from code comments or patterns.

    Looks for patterns like:
    - // src/App.js
    - # filename: server.py
    - <!-- file: index.html -->
    - // File: components/Button.tsx
    """
    # Check first 5 lines for file path hints
    lines = code.split('\n')[:5]

    for line in lines:
        line = line.strip()

        # JavaScript/TypeScript: // src/App.js or // File: ...
        if line.startswith('//'):
            # Remove // and whitespace
            potential_path = line[2:].strip()
            # Remove "file:" or "File:" prefix
            potential_path = re.sub(r'^(file|File):\s*', '', potential_path)
            if '/' in potential_path or '\\' in potential_path or '.' in potential_path:
                return potential_path

        # Python: # filename: server.py or # File: ...
        if line.startswith('#') and not line.startswith('##'):
            potential_path = line[1:].strip()
            potential_path = re.sub(r'^(filename|file|File):\s*', '', potential_path, flags=re.IGNORECASE)
            if '/' in potential_path or '\\' in potential_path or '.' in potential_path:
                return potential_path

        # HTML/XML: <!-- file: index.html -->
        html_match = re.search(r'<!--\s*(file|File|filename):\s*(.+?)\s*-->', line)
        if html_match:
            return html_match.group(2).strip()

    # If no explicit path found, return None
    return None

def infer_file_path(code: str, language: str, index: int) -> str:
    """
    Infer a reasonable file path when none is explicitly provided.
    """
    # Map language to common patterns
    extensions = {
        'javascript': '.js',
        'js': '.js',
        'typescript': '.ts',
        'ts': '.ts',
        'tsx': '.tsx',
        'jsx': '.jsx',
        'python': '.py',
        'py': '.py',
        'html': '.html',
        'css': '.css',
        'scss': '.scss',
        'json': '.json',
        'yaml': '.yaml',
        'yml': '.yml',
        'bash': '.sh',
        'shell': '.sh',
        'sql': '.sql',
        'dockerfile': 'Dockerfile',
        'go': '.go',
        'rust': '.rs',
        'java': '.java',
        'cpp': '.cpp',
        'c': '.c'
    }

    # Try to infer from code content
    if 'package.json' in code or '"name"' in code and '"version"' in code:
        return 'package.json'
    if 'README' in code[:100].upper() or '# ' in code[:20]:
        return 'README.md'
    if code.strip().startswith('FROM ') or code.strip().startswith('RUN '):
        return 'Dockerfile'
    if 'import React' in code or 'from React' in code:
        return f'src/App{extensions.get(language, ".js")}'
    if 'def main' in code or 'if __name__' in code:
        return f'main{extensions.get(language, ".py")}'
    if '<html' in code.lower() or '<!doctype' in code.lower():
        return 'index.html'

    # Default naming
    ext = extensions.get(language.lower(), '.txt')
    if ext == 'Dockerfile':
        return ext
    return f'file{index + 1}{ext}'

def generate_project_structure(code_blocks: List[Dict]) -> Dict[str, str]:
    """
    Generate a project structure from code blocks.

    Returns dict of {file_path: code_content}
    """
    project_files = {}
    unnamed_counter = 1

    for i, block in enumerate(code_blocks):
        file_path = block['file_path']

        # If no path detected, infer one
        if not file_path:
            file_path = infer_file_path(block['code'], block['language'], i)

        # Normalize path (replace backslashes, remove leading slashes)
        file_path = file_path.replace('\\', '/')
        file_path = file_path.lstrip('/')

        # Handle duplicates by appending number
        original_path = file_path
        counter = 1
        while file_path in project_files:
            name, ext = os.path.splitext(original_path)
            file_path = f"{name}_{counter}{ext}"
            counter += 1

        project_files[file_path] = block['code']

    return project_files

def generate_package_json(project_files: Dict[str, str], project_name: str = "my-project") -> str:
    """
    Generate package.json based on detected dependencies in code.
    """
    dependencies = set()
    dev_dependencies = set()

    # Scan all JavaScript/TypeScript files for imports
    for file_path, code in project_files.items():
        if file_path.endswith(('.js', '.jsx', '.ts', '.tsx')):
            # Find import statements
            import_pattern = r'import .+ from [\'"]([^.\'"]+)[\'"]'
            imports = re.findall(import_pattern, code)
            dependencies.update(imports)

            # Find require statements
            require_pattern = r'require\([\'"]([^.\'"]+)[\'"]\)'
            requires = re.findall(require_pattern, code)
            dependencies.update(requires)

    # Common dev dependencies for React projects
    if any('react' in dep.lower() for dep in dependencies):
        dev_dependencies.update(['@types/react', '@types/react-dom', 'vite'])

    # Build package.json
    package = {
        "name": project_name,
        "version": "1.0.0",
        "description": "Generated by AI Agents",
        "main": "index.js",
        "scripts": {
            "start": "node index.js",
            "dev": "vite" if 'vite' in dev_dependencies else "node index.js",
            "build": "vite build" if 'vite' in dev_dependencies else "echo 'No build configured'",
            "test": "echo 'No tests configured'"
        },
        "dependencies": {dep: "latest" for dep in sorted(dependencies) if dep},
        "devDependencies": {dep: "latest" for dep in sorted(dev_dependencies) if dep},
        "author": "AI Agents",
        "license": "MIT"
    }

    return json.dumps(package, indent=2)

def generate_readme(project_name: str, project_files: Dict[str, str]) -> str:
    """
    Generate README.md with project overview.
    """
    file_list = "\n".join([f"- `{path}`" for path in sorted(project_files.keys())])

    readme = f"""# {project_name}

## Overview
This project was generated by AI Agents.

## Project Structure
{file_list}

## Getting Started

1. Install dependencies:
```bash
npm install
```

2. Run the project:
```bash
npm start
```

## Generated Files
This project contains {len(project_files)} files generated from AI agent outputs.

---
*Generated by AI Agents - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    return readme

def save_project_to_disk(project_files: Dict[str, str], output_dir: str = "output") -> Tuple[str, List[str]]:
    """
    Save all project files to disk.

    Returns: (project_path, list of created file paths)
    """
    # Create timestamped project directory
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    project_name = f"project_{timestamp}"
    project_path = os.path.join(output_dir, project_name)

    # Create output directory
    os.makedirs(project_path, exist_ok=True)

    created_files = []

    # Save each file
    for file_path, content in project_files.items():
        full_path = os.path.join(project_path, file_path)

        # Create parent directories if needed
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        # Write file
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)

        created_files.append(full_path)

    return project_path, created_files

def extract_and_save_code(outputs: Dict[str, str], project_name: str = None) -> Dict:
    """
    Main function to extract code from agent outputs and save to disk.

    Args:
        outputs: Dict of {agent_name: output_text}
        project_name: Optional project name (auto-generated if None)

    Returns:
        Dict with:
        - 'success': bool
        - 'project_path': str
        - 'files_created': List[str]
        - 'file_count': int
        - 'message': str
    """
    try:
        # Extract all code blocks from all agents
        all_code_blocks = []
        for agent_name, output_text in outputs.items():
            if not output_text:
                continue
            blocks = extract_code_blocks(output_text)
            all_code_blocks.extend(blocks)

        if not all_code_blocks:
            return {
                'success': False,
                'project_path': None,
                'files_created': [],
                'file_count': 0,
                'message': 'No code blocks found in agent outputs'
            }

        # Generate project structure
        project_files = generate_project_structure(all_code_blocks)

        # Add package.json if JavaScript/TypeScript files detected
        has_js = any(path.endswith(('.js', '.jsx', '.ts', '.tsx')) for path in project_files.keys())
        if has_js and 'package.json' not in project_files:
            project_files['package.json'] = generate_package_json(project_files, project_name or "my-project")

        # Add README.md
        if 'README.md' not in project_files:
            project_files['README.md'] = generate_readme(project_name or "My Project", project_files)

        # Save to disk
        project_path, created_files = save_project_to_disk(project_files)

        return {
            'success': True,
            'project_path': project_path,
            'files_created': created_files,
            'file_count': len(created_files),
            'message': f'Successfully created {len(created_files)} files'
        }

    except Exception as e:
        return {
            'success': False,
            'project_path': None,
            'files_created': [],
            'file_count': 0,
            'message': f'Error: {str(e)}'
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
            # Enhanced error handling with specific guidance
            error_type = type(e).__name__
            error_detail = str(e)

            log_agent_message("System", f"❌ Error during execution: {error_type}")
            log_agent_message("System", f"   Details: {error_detail}")

            # Provide specific guidance based on error type
            if "rate_limit" in error_detail.lower() or "429" in error_detail:
                error_msg = f"""❌ API Rate Limit Exceeded

What happened:
You've made too many requests to the Claude API recently.

Why it happened:
- Running too many agents in a short time period
- Each agent makes API calls, and there's a limit per hour
- Free tier: 30 requests/hour | Paid tier: Higher limits

What to do next:
✓ Wait 30-60 minutes for the rate limit to reset
✓ OR: Reduce the number of agents (try 3-5 instead of 10+)
✓ OR: Upgrade to a paid tier for higher limits
✓ Check API status: https://status.anthropic.com

Partial outputs may be available in the Agent Outputs tab below."""

            elif "authentication" in error_detail.lower() or "401" in error_detail or "api key" in error_detail.lower():
                error_msg = f"""❌ API Authentication Failed

What happened:
The Claude API key is invalid or missing.

Why it happened:
- API key not set in environment variables
- API key has expired or been revoked
- Incorrect API key format

What to do next:
✓ Check your .env file has ANTHROPIC_API_KEY set
✓ Verify the API key is correct (starts with 'sk-ant-...')
✓ Get a new API key from: https://console.anthropic.com/settings/keys
✓ Restart the application after updating the key"""

            elif "timeout" in error_detail.lower() or "timed out" in error_detail.lower():
                error_msg = f"""❌ API Request Timeout

What happened:
The API request took too long and was cancelled.

Why it happened:
- Network connectivity issues
- Claude API experiencing high load
- Very complex prompts requiring long processing time

What to do next:
✓ Check your internet connection
✓ Try running fewer agents at once
✓ Simplify prompts (remove unnecessary details)
✓ Try again in a few minutes
✓ Check API status: https://status.anthropic.com

Partial outputs may be available in the Agent Outputs tab below."""

            elif "connection" in error_detail.lower() or "network" in error_detail.lower():
                error_msg = f"""❌ Network Connection Error

What happened:
Unable to connect to the Claude API servers.

Why it happened:
- Internet connection is down or unstable
- Firewall blocking API requests
- VPN interfering with connections
- API servers temporarily unavailable

What to do next:
✓ Check your internet connection
✓ Disable VPN/proxy temporarily
✓ Check firewall settings allow connections to api.anthropic.com
✓ Try again in a few minutes
✓ Check API status: https://status.anthropic.com"""

            elif "context" in error_detail.lower() or "token" in error_detail.lower() and "limit" in error_detail.lower():
                error_msg = f"""❌ Context Length Exceeded

What happened:
The total input + output exceeded Claude's context window (200K tokens).

Why it happened:
- Too many agents running (each adds to context)
- Very long project descriptions or custom prompts
- Agents generating extremely long outputs

What to do next:
✓ Reduce the number of agents (run 3-5 at a time)
✓ Shorten your project description
✓ Use more concise custom prompts
✓ Run agents in smaller batches

Partial outputs may be available in the Agent Outputs tab below."""

            else:
                # Generic error with troubleshooting tips
                error_msg = f"""❌ Execution Error

What happened:
An unexpected error occurred during agent execution.

Error details:
{error_type}: {error_detail}

What to do next:
✓ Check the execution logs below for more details
✓ Try running fewer agents
✓ Simplify your project description
✓ Check your internet connection
✓ Verify API key is valid
✓ Try again in a few minutes

Partial outputs may be available in the Agent Outputs tab below.

If the problem persists, please report this issue with the error details above."""

            log_agent_message("System", error_msg)

            # Still return partial outputs if available
            outputs = {role: "\n".join(agent_logs[role]) for role in agent_logs if agent_logs[role]}
            return error_msg, outputs, None

    except Exception as e:
        # Top-level critical error handler
        error_type = type(e).__name__
        error_detail = str(e)

        error_msg = f"""❌ Critical Error

A critical error occurred before execution could begin.

Error details:
{error_type}: {error_detail}

What to do next:
✓ Check that all required fields are filled (project description, agents)
✓ Verify your API key is set correctly
✓ Check the console logs for more details
✓ Try restarting the application
✓ Report this issue if it persists

This error prevented execution from starting, so no outputs are available."""

        print(error_msg)  # Log to console for debugging
        log_agent_message("System", error_msg)
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
    """Handle manual export requests with rich visual feedback"""
    import os

    try:
        if not selected_agents_list or len(selected_agents_list) == 0:
            return """
            <div style="background: #fef3c7; border: 2px solid #fbbf24; padding: 16px; border-radius: 8px;">
                <div style="font-weight: 600; color: #92400e;">⚠️ No Agents Selected</div>
                <div style="color: #92400e; margin-top: 6px; font-size: 14px;">
                    Please run the team first to generate outputs.
                </div>
            </div>
            """

        outputs = {role: "\n".join(agent_logs[role]) for role in agent_logs if agent_logs[role]}

        if not outputs:
            return """
            <div style="background: #fef3c7; border: 2px solid #fbbf24; padding: 16px; border-radius: 8px;">
                <div style="font-weight: 600; color: #92400e;">⚠️ No Outputs Available</div>
                <div style="color: #92400e; margin-top: 6px; font-size: 14px;">
                    Run the team first to generate outputs for export.
                </div>
            </div>
            """

        # Export files
        paths = {}
        if format_type == "json":
            paths['json'] = export_to_json(project_desc[:100], selected_agents_list, outputs)
        elif format_type == "markdown":
            paths['markdown'] = export_to_markdown(project_desc[:100], selected_agents_list, outputs)
        elif format_type == "csv":
            paths['csv'] = export_to_csv(project_desc[:100], selected_agents_list, outputs)
        elif format_type == "all":
            paths = export_all_formats(project_desc[:100], selected_agents_list, outputs)
        else:
            return f"""
            <div style="background: #fee2e2; border: 2px solid #ef4444; padding: 16px; border-radius: 8px;">
                <div style="font-weight: 600; color: #991b1b;">❌ Unknown Format</div>
                <div style="color: #b91c1c; margin-top: 6px; font-size: 14px;">
                    Format '{format_type}' is not supported.
                </div>
            </div>
            """

        # Generate rich feedback HTML
        files_html = ""
        total_size = 0

        for file_format, file_path in paths.items():
            # Get file size
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                total_size += file_size
                size_kb = file_size / 1024
                size_str = f"{size_kb:.1f} KB" if size_kb < 1024 else f"{size_kb/1024:.1f} MB"
            else:
                size_str = "Unknown size"

            # Format icons
            format_icons = {
                'json': '📄',
                'markdown': '📝',
                'csv': '📊'
            }
            icon = format_icons.get(file_format, '📁')

            # Normalize path for display (convert backslashes)
            display_path = file_path.replace('\\', '/')

            files_html += f"""
            <div style="background: white; border-left: 3px solid #10b981; padding: 14px;
                        margin-bottom: 10px; border-radius: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span style="font-size: 24px;">{icon}</span>
                        <div>
                            <div style="font-weight: 600; color: #1e293b; font-size: 14px;">
                                {file_format.upper()} Export
                            </div>
                            <div style="color: #64748b; font-size: 12px; margin-top: 2px;">
                                {size_str}
                            </div>
                        </div>
                    </div>
                </div>
                <div style="font-family: 'Courier New', monospace; background: #f8fafc;
                            padding: 10px; border-radius: 4px; color: #475569; font-size: 12px;
                            word-break: break-all; margin-top: 8px;">
                    {display_path}
                </div>
            </div>
            """

        return f"""
        <div style="background: linear-gradient(135deg, #f0fdf4 0%, #d1fae5 100%);
                    border: 2px solid #10b981; padding: 20px; border-radius: 10px;
                    box-shadow: 0 4px 12px rgba(16, 185, 129, 0.15);">

            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px;">
                <div style="font-size: 32px;">✅</div>
                <div>
                    <div style="font-weight: 700; color: #166534; font-size: 18px;">
                        Export Successful!
                    </div>
                    <div style="color: #15803d; font-size: 14px; margin-top: 2px;">
                        {len(paths)} file(s) exported • Total size: {total_size/1024:.1f} KB
                    </div>
                </div>
            </div>

            <div style="margin-top: 16px;">
                {files_html}
            </div>

            <div style="background: #fef3c7; border-left: 3px solid #f59e0b; padding: 12px;
                        border-radius: 6px; margin-top: 16px;">
                <div style="font-weight: 600; color: #92400e; font-size: 13px; margin-bottom: 6px;">
                    💡 What's Next?
                </div>
                <div style="color: #92400e; font-size: 12px; line-height: 1.5;">
                    • Files are saved in the <code>gradio_exports/</code> directory<br>
                    • Open files in your favorite editor to review agent outputs<br>
                    • Share with your team or use for documentation
                </div>
            </div>
        </div>
        """

    except Exception as e:
        import traceback
        error_detail = str(e)
        return f"""
        <div style="background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
                    border: 2px solid #ef4444; padding: 20px; border-radius: 10px;">
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                <div style="font-size: 32px;">❌</div>
                <div>
                    <div style="font-weight: 700; color: #991b1b; font-size: 18px;">
                        Export Failed
                    </div>
                    <div style="color: #b91c1c; font-size: 14px;">
                        An error occurred while exporting
                    </div>
                </div>
            </div>

            <div style="background: white; padding: 12px; border-radius: 6px; border: 1px solid #fca5a5;">
                <div style="font-weight: 600; color: #991b1b; margin-bottom: 6px; font-size: 13px;">
                    Error Details:
                </div>
                <div style="font-family: 'Courier New', monospace; color: #b91c1c; font-size: 12px;">
                    {error_detail}
                </div>
            </div>
        </div>
        """

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
            # Interactive onboarding banner
            gr.HTML("""
            <div id="onboarding_banner" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        padding: 24px; border-radius: 12px; color: white; margin-bottom: 20px;">
                <h2 style="margin: 0 0 12px 0; font-size: 24px; font-weight: 700;">👋 Welcome to Super Dev Team!</h2>
                <p style="margin: 0 0 16px 0; font-size: 16px; line-height: 1.5;">
                    Get started in 3 easy steps:
                </p>
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 20px;">
                    <div style="background: rgba(255,255,255,0.1); padding: 16px; border-radius: 8px;">
                        <div style="font-size: 32px; margin-bottom: 8px;">1️⃣</div>
                        <div style="font-weight: 600; font-size: 16px; margin-bottom: 4px;">Describe Your Project</div>
                        <p style="font-size: 14px; margin: 0; opacity: 0.9; line-height: 1.4;">
                            What do you want to build? Be specific!
                        </p>
                    </div>
                    <div style="background: rgba(255,255,255,0.1); padding: 16px; border-radius: 8px;">
                        <div style="font-size: 32px; margin-bottom: 8px;">2️⃣</div>
                        <div style="font-weight: 600; font-size: 16px; margin-bottom: 4px;">Choose Your Team</div>
                        <p style="font-size: 14px; margin: 0; opacity: 0.9; line-height: 1.4;">
                            Pick a preset or select individual agents
                        </p>
                    </div>
                    <div style="background: rgba(255,255,255,0.1); padding: 16px; border-radius: 8px;">
                        <div style="font-size: 32px; margin-bottom: 8px;">3️⃣</div>
                        <div style="font-weight: 600; font-size: 16px; margin-bottom: 4px;">Run & Review</div>
                        <p style="font-size: 14px; margin: 0; opacity: 0.9; line-height: 1.4;">
                            Click Run and watch your agents work!
                        </p>
                    </div>
                </div>
                <button id="dismiss-onboarding" style="margin-top: 4px; padding: 10px 20px;
                        background: white; color: #667eea; border: none; border-radius: 6px;
                        cursor: pointer; font-weight: 600; font-size: 14px; transition: transform 0.2s ease;">
                    Got it! Let's start 🚀
                </button>
            </div>
            <script>
                // Safe localStorage with fallback to sessionStorage
                function safeStorageGet(key) {
                    try {
                        return localStorage.getItem(key);
                    } catch (e) {
                        // Fallback to sessionStorage if localStorage unavailable
                        try {
                            return sessionStorage.getItem(key);
                        } catch (e2) {
                            console.warn('Storage unavailable:', e2);
                            return null;
                        }
                    }
                }

                function safeStorageSet(key, value) {
                    try {
                        localStorage.setItem(key, value);
                    } catch (e) {
                        // Fallback to sessionStorage if localStorage unavailable
                        try {
                            sessionStorage.setItem(key, value);
                        } catch (e2) {
                            console.warn('Storage unavailable:', e2);
                        }
                    }
                }

                // Dismiss onboarding banner and save to storage
                document.addEventListener('DOMContentLoaded', function() {
                    const dismissBtn = document.getElementById('dismiss-onboarding');
                    const banner = document.getElementById('onboarding_banner');

                    // Check if user has dismissed before
                    if (safeStorageGet('onboarding_dismissed') === 'true') {
                        if (banner) banner.style.display = 'none';
                    }

                    // Handle dismiss button click
                    if (dismissBtn) {
                        dismissBtn.addEventListener('click', function() {
                            if (banner) {
                                banner.style.display = 'none';
                                safeStorageSet('onboarding_dismissed', 'true');
                            }
                        });

                        // Add hover effect
                        dismissBtn.addEventListener('mouseenter', function() {
                            this.style.transform = 'translateY(-2px)';
                        });
                        dismissBtn.addEventListener('mouseleave', function() {
                            this.style.transform = 'translateY(0)';
                        });
                    }
                });
            </script>
            """)

            gr.Markdown("*Single execution mode - run agents immediately*")

            # ========== WORKFLOW STEPPER ==========
            gr.HTML("""
            <div id="workflow_stepper" style="margin: 32px 0; position: relative;">
                <!-- Progress line background -->
                <div style="position: absolute; top: 20px; left: 0; right: 0; height: 4px; background: #e2e8f0; z-index: 0;"></div>
                <div id="workflow_progress_line" style="position: absolute; top: 20px; left: 0; height: 4px; background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); z-index: 1; width: 0%; transition: width 0.3s ease;"></div>

                <!-- Stepper container -->
                <div style="display: flex; justify-content: space-between; position: relative; z-index: 2;">
                    <!-- Step 1: Describe -->
                    <div class="workflow-step" data-step="1" style="flex: 1; text-align: center;">
                        <div class="step-circle" id="step1_circle" style="width: 44px; height: 44px; border-radius: 50%; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; display: flex; align-items: center; justify-content: center; margin: 0 auto 12px; font-weight: 700; font-size: 18px; box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3); transition: all 0.3s ease;">
                            1
                        </div>
                        <div style="font-weight: 600; color: #1e293b; font-size: 15px; margin-bottom: 4px;">Describe</div>
                        <div style="font-size: 13px; color: #64748b;">Your project</div>
                    </div>

                    <!-- Step 2: Choose -->
                    <div class="workflow-step" data-step="2" style="flex: 1; text-align: center;">
                        <div class="step-circle" id="step2_circle" style="width: 44px; height: 44px; border-radius: 50%; background: #e2e8f0; color: #94a3b8; display: flex; align-items: center; justify-content: center; margin: 0 auto 12px; font-weight: 700; font-size: 18px; transition: all 0.3s ease;">
                            2
                        </div>
                        <div id="step2_label" style="font-weight: 600; color: #94a3b8; font-size: 15px; margin-bottom: 4px;">Choose</div>
                        <div id="step2_desc" style="font-size: 13px; color: #94a3b8;">Your team</div>
                    </div>

                    <!-- Step 3: Configure -->
                    <div class="workflow-step" data-step="3" style="flex: 1; text-align: center;">
                        <div class="step-circle" id="step3_circle" style="width: 44px; height: 44px; border-radius: 50%; background: #e2e8f0; color: #94a3b8; display: flex; align-items: center; justify-content: center; margin: 0 auto 12px; font-weight: 700; font-size: 18px; transition: all 0.3s ease;">
                            3
                        </div>
                        <div id="step3_label" style="font-weight: 600; color: #94a3b8; font-size: 15px; margin-bottom: 4px;">Configure</div>
                        <div id="step3_desc" style="font-size: 13px; color: #94a3b8;">Settings (Optional)</div>
                    </div>

                    <!-- Step 4: Run -->
                    <div class="workflow-step" data-step="4" style="flex: 1; text-align: center;">
                        <div class="step-circle" id="step4_circle" style="width: 44px; height: 44px; border-radius: 50%; background: #e2e8f0; color: #94a3b8; display: flex; align-items: center; justify-content: center; margin: 0 auto 12px; font-weight: 700; font-size: 18px; transition: all 0.3s ease;">
                            4
                        </div>
                        <div id="step4_label" style="font-weight: 600; color: #94a3b8; font-size: 15px; margin-bottom: 4px;">Run</div>
                        <div id="step4_desc" style="font-size: 13px; color: #94a3b8;">Execute & review</div>
                    </div>
                </div>
            </div>

            <script>
                // Global state using Promise for safe single initialization
                let workflowInitPromise = null;
                let checkboxObserver = null;

                // Workflow stepper auto-advancement
                function updateWorkflowStep(step) {
                    const progressLine = document.getElementById('workflow_progress_line');

                    // Add null safety check to prevent crashes
                    if (!progressLine) return;

                    // Update progress line width
                    const progressPct = ((step - 1) / 3) * 100;
                    progressLine.style.width = progressPct + '%';

                    // Update step circles and labels
                    for (let i = 1; i <= 4; i++) {
                        const circle = document.getElementById(`step${i}_circle`);
                        const label = document.getElementById(`step${i}_label`);
                        const desc = document.getElementById(`step${i}_desc`);

                        // Add null safety check before accessing style property
                        if (!circle) continue;

                        if (i <= step) {
                            // Active/completed step
                            circle.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
                            circle.style.color = 'white';
                            circle.style.boxShadow = '0 4px 12px rgba(102, 126, 234, 0.3)';
                            if (label) label.style.color = '#1e293b';
                            if (desc) desc.style.color = '#64748b';
                        } else {
                            // Inactive step
                            circle.style.background = '#e2e8f0';
                            circle.style.color = '#94a3b8';
                            circle.style.boxShadow = 'none';
                            if (label) label.style.color = '#94a3b8';
                            if (desc) desc.style.color = '#94a3b8';
                        }
                    }
                }

                // Check agent selection count
                function checkAgentSelection() {
                    const checkedBoxes = document.querySelectorAll('input[type="checkbox"]:checked');
                    const agentCount = Array.from(checkedBoxes).filter(cb => {
                        const label = cb.parentElement;
                        return label && !label.textContent.includes('Code Review') && !label.textContent.includes('Auto-export');
                    }).length;

                    if (agentCount > 0) {
                        updateWorkflowStep(3);
                        // Disconnect observer once agents are selected to prevent unnecessary checks
                        if (checkboxObserver) {
                            checkboxObserver.disconnect();
                            checkboxObserver = null;
                        }
                    }
                }

                // Promise-based initialization with retry logic
                async function initWorkflowTracking() {
                    // Return existing promise if initialization already in progress
                    if (workflowInitPromise) {
                        return workflowInitPromise;
                    }

                    workflowInitPromise = new Promise((resolve, reject) => {
                        let retries = 0;
                        const maxRetries = 5;

                        function attemptInit() {
                            // Step 1: Check if project description has content
                            const projectInput = document.querySelector('textarea[placeholder*="Build a real-time"], textarea[placeholder*="Describe your project"]');

                            if (!projectInput && retries < maxRetries) {
                                // Element not ready, retry after delay
                                retries++;
                                setTimeout(attemptInit, 500);
                                return;
                            }

                            // Successfully found elements or max retries reached
                            if (projectInput) {
                                projectInput.addEventListener('input', function() {
                                    if (this.value.length > 20) {
                                        updateWorkflowStep(2);
                                    }
                                });
                            }

                            // Step 2: Use MutationObserver instead of setInterval for better performance
                            checkboxObserver = new MutationObserver((mutations) => {
                                // Only check when checkbox states change
                                const hasCheckboxChange = mutations.some(mutation =>
                                    mutation.type === 'attributes' &&
                                    mutation.attributeName === 'aria-checked'
                                );

                                if (hasCheckboxChange) {
                                    checkAgentSelection();
                                }
                            });

                            // Observe checkbox container for changes
                            const checkboxContainer = document.querySelector('.gradio-container');
                            if (checkboxContainer) {
                                checkboxObserver.observe(checkboxContainer, {
                                    attributes: true,
                                    subtree: true,
                                    attributeFilter: ['aria-checked']
                                });
                            }

                            // Also listen for direct input events on checkboxes (fallback)
                            document.addEventListener('change', (e) => {
                                if (e.target && e.target.type === 'checkbox') {
                                    checkAgentSelection();
                                }
                            });

                            // Step 4: When Run button is clicked
                            document.addEventListener('click', (e) => {
                                if (e.target && e.target.textContent.includes('Run Team')) {
                                    updateWorkflowStep(4);
                                }
                            });

                            resolve();
                        }

                        attemptInit();
                    });

                    return workflowInitPromise;
                }

                // Cleanup on page unload
                window.addEventListener('beforeunload', () => {
                    if (checkboxObserver) {
                        checkboxObserver.disconnect();
                        checkboxObserver = null;
                    }
                    workflowInitPromise = null;
                });

                // Single initialization call using Promise
                // This prevents race conditions from multiple calls
                if (document.readyState === 'loading') {
                    document.addEventListener('DOMContentLoaded', () => initWorkflowTracking());
                } else {
                    initWorkflowTracking();
                }
            </script>
            """)

            # ========== STEP 1: DESCRIBE YOUR PROJECT ==========
            with gr.Accordion("🎯 Step 1: Describe Your Project", open=True, elem_id="step1_accordion"):
                gr.Markdown("""
                **What do you want to build?** Be as specific as possible. The more details you provide, the better your agents can help.
                """)

                project_input = gr.Textbox(
                    label="Project Description",
                    lines=5,
                    placeholder="Example: Build a real-time chat application with user authentication, message history, file sharing, and emoji support. Use React for frontend and Node.js/Express for backend...",
                    info="💡 Tip: Include technology preferences, features, constraints, and success criteria"
                )

                # AI Recommendations Section
                with gr.Row():
                    get_recommendations_btn = gr.Button("✨ Get AI Recommendations", variant="secondary", size="sm")
                    clear_recommendations_btn = gr.Button("Clear Recommendations", variant="secondary", size="sm", visible=False)

                recommendations_display = gr.HTML(visible=False)

                with gr.Row():
                    github_url_input = gr.Textbox(
                        label="📂 GitHub Repository URL (Optional)",
                        lines=1,
                        placeholder="https://github.com/username/repository",
                        info="Analyze existing code from GitHub",
                        scale=3
                    )
                    code_review_checkbox = gr.Checkbox(
                        label="Code Review Mode",
                        value=False,
                        info="Optimize for code analysis",
                        scale=1
                    )

                # GitHub URL Validation Feedback
                github_url_validation = gr.HTML(
                    value="",
                    visible=False,
                    elem_id="github_url_validation"
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

            # ========== STEP 2: CHOOSE YOUR TEAM ==========
            with gr.Accordion("👥 Step 2: Choose Your Team", open=True, elem_id="step2_accordion"):
                gr.Markdown("""
                **Select the agents you need.** Not sure where to start? Try the Recommended Agents tab or use Quick Start Templates.
                """)

                # Agent selection counter (live updates)
                agent_selection_counter = gr.HTML(
                    value="""
                    <div id="agent_selection_counter" style="background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
                            border: 2px solid #0ea5e9; padding: 16px 20px; border-radius: 8px; margin-bottom: 20px;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div style="display: flex; align-items: center; gap: 12px;">
                                <span style="font-size: 24px;">👥</span>
                                <div>
                                    <div style="font-weight: 700; color: #0c4a6e; font-size: 16px;">
                                        Selected Agents: <span id="agent_count" style="color: #0369a1;">0</span> / 52
                                    </div>
                                    <div style="font-size: 13px; color: #0369a1; margin-top: 2px;">
                                        <span id="agent_count_message">Select at least 3-5 agents for best results</span>
                                    </div>
                                </div>
                            </div>
                            <button id="clear_all_agents" style="padding: 8px 16px; background: white;
                                    color: #0369a1; border: 2px solid #0ea5e9; border-radius: 6px;
                                    font-weight: 600; cursor: pointer; font-size: 13px;
                                    transition: all 0.2s ease;">
                                Clear All
                            </button>
                        </div>
                    </div>
                    <script>
                        // Initialize agent counter
                        function updateAgentCounter() {
                            // Count all checked checkboxes across all tabs
                            const allCheckboxes = document.querySelectorAll('input[type="checkbox"]:checked');

                            // Filter out non-agent checkboxes (like code review mode)
                            const agentCheckboxes = Array.from(allCheckboxes).filter(cb => {
                                const label = cb.parentElement;
                                if (!label) return false;

                                // Exclude special checkboxes
                                const labelText = label.textContent.toLowerCase();
                                return !labelText.includes('code review') &&
                                       !labelText.includes('auto export') &&
                                       !labelText.includes('onboarding');
                            });

                            const count = agentCheckboxes.length;
                            const countSpan = document.getElementById('agent_count');
                            const messageSpan = document.getElementById('agent_count_message');
                            const counter = document.getElementById('agent_selection_counter');

                            if (countSpan) {
                                countSpan.textContent = count;

                                // Update color and message based on count
                                if (count === 0) {
                                    countSpan.style.color = '#64748b';
                                    messageSpan.textContent = 'Select at least 3-5 agents for best results';
                                    messageSpan.style.color = '#64748b';
                                } else if (count < 3) {
                                    countSpan.style.color = '#f59e0b';
                                    messageSpan.textContent = 'Add a few more agents for better coverage';
                                    messageSpan.style.color = '#f59e0b';
                                } else if (count <= 10) {
                                    countSpan.style.color = '#10b981';
                                    messageSpan.textContent = 'Good selection! Ready to run';
                                    messageSpan.style.color = '#10b981';
                                } else if (count <= 20) {
                                    countSpan.style.color = '#0369a1';
                                    messageSpan.textContent = 'Large team - may take longer to execute';
                                    messageSpan.style.color = '#0369a1';
                                } else {
                                    countSpan.style.color = '#f59e0b';
                                    messageSpan.textContent = 'Very large team - consider reducing for faster results';
                                    messageSpan.style.color = '#f59e0b';
                                }
                            }
                        }

                        // Clear all agents button handler
                        document.addEventListener('DOMContentLoaded', function() {
                            const clearBtn = document.getElementById('clear_all_agents');
                            if (clearBtn) {
                                clearBtn.addEventListener('click', function() {
                                    // Uncheck all agent checkboxes
                                    const allCheckboxes = document.querySelectorAll('input[type="checkbox"]:checked');
                                    allCheckboxes.forEach(cb => {
                                        const label = cb.parentElement;
                                        if (label) {
                                            const labelText = label.textContent.toLowerCase();
                                            if (!labelText.includes('code review') &&
                                                !labelText.includes('auto export')) {
                                                cb.click();  // Trigger change event
                                            }
                                        }
                                    });
                                    updateAgentCounter();
                                });

                                // Hover effect
                                clearBtn.addEventListener('mouseenter', function() {
                                    this.style.background = '#f0f9ff';
                                    this.style.transform = 'translateY(-1px)';
                                });
                                clearBtn.addEventListener('mouseleave', function() {
                                    this.style.background = 'white';
                                    this.style.transform = 'translateY(0)';
                                });
                            }
                        });

                        // Listen for checkbox changes with debouncing
                        let counterTimeout;
                        document.addEventListener('change', function(e) {
                            if (e.target.type === 'checkbox') {
                                clearTimeout(counterTimeout);
                                counterTimeout = setTimeout(updateAgentCounter, 100);
                            }
                        });

                        // Initial count
                        setTimeout(updateAgentCounter, 1000);

                        // Recount when accordions open (agents become visible)
                        const observer = new MutationObserver(function() {
                            clearTimeout(counterTimeout);
                            counterTimeout = setTimeout(updateAgentCounter, 200);
                        });

                        setTimeout(() => {
                            observer.observe(document.body, {
                                childList: true,
                                subtree: true
                            });
                        }, 2000);
                    </script>
                    """,
                    elem_id="agent_counter_display"
                )

                # Grouped agent selectors by category (needed for reference)
                agents_by_category = get_agents_by_category()
                agent_selectors_by_category = {}

                with gr.Tabs():
                    # TAB 1: RECOMMENDED AGENTS (10 most common)
                    with gr.TabItem("⭐ Recommended Agents"):
                        gr.Markdown("""
                        **Most commonly used agents** - These cover 80% of typical projects
                        """)

                        # Quick Start Templates
                        with gr.Accordion("💡 Quick Start Templates", open=True):
                            gr.Markdown("**Not sure which agents to pick?** Try these popular combinations:")
                            with gr.Row():
                                preset_web = gr.Button("🌐 Web App Squad", variant="secondary", size="sm")
                                preset_mobile = gr.Button("📱 Mobile App Squad", variant="secondary", size="sm")
                                preset_backend = gr.Button("⚙️ Backend Squad", variant="secondary", size="sm")
                            with gr.Row():
                                preset_fullstack = gr.Button("🚀 Full-Stack Squad", variant="secondary", size="sm")
                                preset_ai = gr.Button("🤖 AI/ML Squad", variant="secondary", size="sm")
                                preset_data = gr.Button("📊 Data Analytics Squad", variant="secondary", size="sm")

                        gr.Markdown("### Essential Agents for Most Projects")

                        # Create a special "Essential" category selector
                        essential_agents = ["PM", "Senior", "Research", "Ideas", "Designs", "Web", "QA", "Verifier", "DevOps", "Memory"]
                        agent_selectors_by_category["Essential"] = gr.CheckboxGroup(
                            choices=essential_agents,
                            value=["PM", "Senior", "QA", "Memory"],
                            label="Essential Agents (10 most common)",
                            info="These agents handle most common project needs. Select at least 3-5 agents for best results."
                        )

                    # TAB 2: ALL AGENTS BY CATEGORY (52 total)
                    with gr.TabItem("🔧 All Agents by Category"):
                        gr.Markdown("""
                        **Browse all 52 agents** organized by expertise area
                        """)

                        # Agent search and filter section
                        gr.Markdown("### 🔍 Find Specific Agents")

                        with gr.Row():
                            agent_search = gr.Textbox(
                                placeholder="Search agents by name or role... (e.g. 'frontend', 'testing', 'data')",
                                label="Quick Agent Search",
                                scale=3,
                                elem_id="agent_search_box"
                            )
                            agent_category_filter = gr.Dropdown(
                                choices=["All Categories"] + list(agents_by_category.keys()),
                                value="All Categories",
                                label="Filter by Category",
                                scale=1,
                                elem_id="agent_category_filter"
                            )

                        gr.Markdown("### 📂 Agents Organized by Category")

                        for category, agent_ids in agents_by_category.items():
                            # Only open "Management" by default to improve initial render performance
                            with gr.Accordion(f"{category} ({len(agent_ids)} agents)", open=(category == "Management")):
                                agent_selectors_by_category[category] = gr.CheckboxGroup(
                                    choices=agent_ids,
                                    value=[aid for aid in agent_ids if aid in ["PM", "Memory", "Research", "Ideas", "Designs", "QA", "Senior"]],  # Default selections
                                    label=f"{category} Agents",
                                    info=f"Select from {len(agent_ids)} {category.lower()} agents"
                                )

                    # TAB 3: SAVED TEAMS (from Projects & Teams)
                    with gr.TabItem("💾 My Saved Teams"):
                        gr.Markdown("""
                        **Load teams you've created** in the Projects & Teams tab
                        """)

                        # Agent presets dropdown (existing functionality)
                        agent_preset_dropdown = gr.Dropdown(
                            choices=["Custom Selection"] + list(AGENT_PRESETS.keys()),
                            value="New Project Development",
                            label="Agent Preset",
                            info="Quick select from predefined team configurations"
                        )

                        gr.Markdown("*More saved teams coming soon from Projects & Teams integration*")

            # Agent search and filter JavaScript
            gr.HTML("""
            <style>
                /* Performance optimizations for 52 checkboxes */
                .agent-checkbox-container {
                    /* Use CSS containment for better rendering performance */
                    contain: layout style paint;
                    /* Enable GPU acceleration */
                    will-change: transform;
                    /* Prevent reflow */
                    transform: translateZ(0);
                }

                /* Optimize accordion rendering */
                [class*="accordion"] {
                    /* Contain layout calculations */
                    contain: layout;
                    /* Hint browser about transform changes */
                    will-change: contents;
                }

                /* Smooth transitions */
                label {
                    transition: opacity 0.15s ease;
                }

                /* Hidden state optimization */
                [style*="display: none"] {
                    /* Use visibility for better performance than display:none in some cases */
                    visibility: hidden;
                    height: 0;
                    overflow: hidden;
                }
            </style>

            <script>
                // Agent search and filter functionality with performance optimizations
                function initAgentSearchAndFilter() {
                    // Get references to search and filter elements
                    const searchBox = document.querySelector('#agent_search_box textarea, #agent_search_box input');
                    const categoryFilter = document.querySelector('#agent_category_filter select');

                    if (!searchBox || !categoryFilter) {
                        // Retry after a short delay if elements aren't ready
                        setTimeout(initAgentSearchAndFilter, 500);
                        return;
                    }

                    // Debounce function to prevent excessive re-renders
                    function debounce(func, wait) {
                        let timeout;
                        return function executedFunction(...args) {
                            const later = () => {
                                clearTimeout(timeout);
                                func(...args);
                            };
                            clearTimeout(timeout);
                            timeout = setTimeout(later, wait);
                        };
                    }

                    // Cache DOM queries for better performance
                    let accordionsCache = null;
                    let lastSearchTerm = '';
                    let lastCategory = 'All Categories';

                    function filterAgents() {
                        const searchTerm = (searchBox.value || '').toLowerCase();
                        const selectedCategory = categoryFilter.value || 'All Categories';

                        // Skip if nothing changed (optimization)
                        if (searchTerm === lastSearchTerm && selectedCategory === lastCategory) {
                            return;
                        }

                        lastSearchTerm = searchTerm;
                        lastCategory = selectedCategory;

                        // Use requestAnimationFrame for smoother updates
                        requestAnimationFrame(() => {
                            // Cache accordion queries if not already cached
                            if (!accordionsCache) {
                                accordionsCache = Array.from(document.querySelectorAll('[class*="accordion"]'));
                            }

                            // Batch DOM updates using DocumentFragment for better performance
                            accordionsCache.forEach(accordion => {
                                const header = accordion.querySelector('span, div');
                                if (!header) return;

                                const headerText = header.textContent || '';

                                // Check if this accordion matches the category filter
                                const matchesCategory = selectedCategory === 'All Categories' ||
                                                        headerText.includes(selectedCategory);

                                if (!matchesCategory) {
                                    accordion.style.display = 'none';
                                    return;
                                }

                                // If no search term, show all matching categories
                                if (!searchTerm) {
                                    accordion.style.display = '';
                                    // Show all labels in this accordion
                                    const labels = accordion.querySelectorAll('label');
                                    labels.forEach(label => {
                                        label.style.display = '';
                                    });
                                    return;
                                }

                                // Get all checkboxes in this accordion
                                const labels = accordion.querySelectorAll('label');
                                let visibleCount = 0;

                                // Batch style updates
                                const updates = [];
                                labels.forEach(label => {
                                    const labelText = (label.textContent || '').toLowerCase();
                                    const matchesSearch = labelText.includes(searchTerm);

                                    updates.push({ label, visible: matchesSearch });
                                    if (matchesSearch) visibleCount++;
                                });

                                // Apply all updates at once (reduces reflows)
                                updates.forEach(({ label, visible }) => {
                                    label.style.display = visible ? '' : 'none';
                                });

                                // Hide accordion if no agents match
                                accordion.style.display = visibleCount > 0 ? '' : 'none';
                            });
                        });
                    }

                    // Debounced filter for search input (300ms delay)
                    const debouncedFilter = debounce(filterAgents, 300);

                    // Attach event listeners
                    searchBox.addEventListener('input', debouncedFilter);  // Debounced for typing
                    categoryFilter.addEventListener('change', filterAgents);  // Immediate for dropdown

                    // Clear cache when accordions might change (e.g., after Gradio updates)
                    window.addEventListener('gradio-reload', () => {
                        accordionsCache = null;
                    });

                    console.log('Agent search and filter initialized with performance optimizations');
                }

                // Initialize when DOM is ready
                if (document.readyState === 'loading') {
                    document.addEventListener('DOMContentLoaded', initAgentSearchAndFilter);
                } else {
                    initAgentSearchAndFilter();
                }
            </script>
            """)

            # Agent tooltips CSS and JavaScript
            import json
            agent_descriptions_json = json.dumps(AGENT_DESCRIPTIONS)

            gr.HTML(f"""
            <style>
                /* Tooltip styling */
                .agent-label {{
                    position: relative;
                    cursor: help;
                }}

                .agent-label .tooltip {{
                    visibility: hidden;
                    opacity: 0;
                    position: absolute;
                    z-index: 9999;
                    background-color: #1e293b;
                    color: white;
                    padding: 10px 14px;
                    border-radius: 8px;
                    font-size: 13px;
                    max-width: 300px;
                    width: max-content;
                    left: 0;
                    bottom: 100%;
                    margin-bottom: 8px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                    transition: opacity 0.2s ease, visibility 0.2s ease;
                    line-height: 1.4;
                }}

                .agent-label .tooltip::after {{
                    content: "";
                    position: absolute;
                    top: 100%;
                    left: 20px;
                    border-width: 6px;
                    border-style: solid;
                    border-color: #1e293b transparent transparent transparent;
                }}

                .agent-label:hover .tooltip {{
                    visibility: visible;
                    opacity: 1;
                }}

                /* Info icon styling */
                .agent-info-icon {{
                    font-size: 12px;
                    opacity: 0.6;
                    margin-left: 4px;
                    transition: opacity 0.2s ease;
                }}

                .agent-label:hover .agent-info-icon {{
                    opacity: 1;
                }}
            </style>

            <script>
                // Add tooltips to agent checkboxes
                function initAgentTooltips() {{
                    const agentDescriptions = {agent_descriptions_json};

                    // Find all checkbox labels
                    const labels = document.querySelectorAll('label[class*="checkbox"]');

                    labels.forEach(label => {{
                        // Get the agent name from the label text
                        let agentName = label.textContent.trim();

                        // Check if this agent has a description
                        if (agentDescriptions[agentName]) {{
                            // Add info icon and tooltip
                            const description = agentDescriptions[agentName];

                            // Wrap label content
                            label.classList.add('agent-label');

                            // Add info icon
                            const infoIcon = document.createElement('span');
                            infoIcon.className = 'agent-info-icon';
                            infoIcon.textContent = ' ℹ️';

                            // Add tooltip
                            const tooltip = document.createElement('span');
                            tooltip.className = 'tooltip';
                            tooltip.textContent = description;

                            label.appendChild(infoIcon);
                            label.appendChild(tooltip);
                        }}
                    }});

                    console.log('Agent tooltips initialized');
                }}

                // Initialize tooltips after a delay to ensure checkboxes are rendered
                setTimeout(initAgentTooltips, 1000);

                // Re-initialize after Gradio updates (when accordions open/close)
                const observer = new MutationObserver((mutations) => {{
                    mutations.forEach((mutation) => {{
                        if (mutation.addedNodes.length) {{
                            setTimeout(initAgentTooltips, 500);
                        }}
                    }});
                }});

                // Observe the document for changes
                setTimeout(() => {{
                    observer.observe(document.body, {{
                        childList: true,
                        subtree: true
                    }});
                }}, 2000);
            </script>
            """)

            # Merged selection display (updated dynamically from category selections)
            with gr.Accordion("✅ Selected Agents Summary", open=False):
                agent_selector = gr.CheckboxGroup(
                    choices=AGENT_ROLES,
                    value=["PM", "Memory", "Research", "Ideas", "Designs", "QA", "Senior"],
                    label="All Selected Agents",
                    info="Combined selection from all categories above. You can also manually adjust here.",
                    interactive=True
                )

            # ========== STEP 3: CONFIGURE EXECUTION (ADVANCED) ==========
            with gr.Accordion("⚙️ Step 3: Configure Execution (Advanced)", open=False, elem_id="step3_accordion"):
                gr.Markdown("""
                **Advanced settings for power users.** Most projects work great with default settings - only customize if needed.
                """)

                with gr.Tabs():
                    # TAB 1: MODEL SELECTION
                    with gr.TabItem("🤖 Model Selection"):
                        gr.Markdown("""
                        **Choose AI models for your agents**

                        - **Speed (Haiku)**: Fastest, cheapest, good for simple tasks
                        - **Balanced (Sonnet)**: Best quality/speed trade-off - recommended for most projects
                        - **Quality (Opus)**: Highest quality, slower, best for complex/critical tasks
                        """)

                        model_preset_dropdown = gr.Dropdown(
                            choices=list(MODEL_PRESETS.keys()),
                            value="Speed (All Haiku)",
                            label="Model Preset",
                            info="💡 Recommended: Start with 'Balanced' for best results"
                        )

                        # Cost & Time Estimator
                        cost_estimate_display = gr.HTML(
                            value="""
                            <div style="background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
                                        border: 2px solid #f59e0b; padding: 16px; border-radius: 8px; margin-top: 16px;">
                                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                                    <span style="font-size: 24px;">💰</span>
                                    <div>
                                        <div style="font-weight: 700; color: #92400e; font-size: 15px;">
                                            Estimated Cost & Time
                                        </div>
                                        <div style="color: #b45309; font-size: 13px; margin-top: 2px;">
                                            Select agents to see cost estimate
                                        </div>
                                    </div>
                                </div>
                            </div>
                            """,
                            elem_id="cost_estimate_display"
                        )

                        # Per-agent model override (advanced)
                        with gr.Accordion("Per-Agent Model Override (Advanced)", open=False):
                            gr.Markdown("*Override individual agent models. Leave as 'Use Default' to follow preset above.*")
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

                    # TAB 2: CUSTOM PROMPTS
                    with gr.TabItem("✏️ Custom Prompts"):
                        gr.Markdown("""
                        **Override default agent instructions**

                        Leave blank to use smart defaults. Only customize if you need specialized behavior.
                        Use `{project_description}` as a placeholder for the project details.
                        """)

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

                    # TAB 3: EXECUTION PRIORITY
                    with gr.TabItem("🔢 Execution Priority"):
                        gr.Markdown("""
                        **Control the order agents execute**

                        - **Lower number = runs first**
                        - Agents with same priority can run in parallel (future feature)
                        - Default order: Memory/PM → Research → Ideas → Designs → Development → Senior → QA → Verifier
                        """)

                        with gr.Accordion("Priority Settings (Optional)", open=False) as priority_accordion:
                            gr.Markdown("*Adjust execution order. Lower numbers run first. Default order works for most projects.*")

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

                    # TAB 4: EXECUTION CONTROLS
                    with gr.TabItem("⚙️ Execution Controls"):
                        gr.Markdown("""
                        **Additional execution settings**

                        Control phases, auto-export, feedback, and apply modes.
                        """)

                        phase_dropdown = gr.Dropdown(
                            choices=PHASE_CHOICES,
                            value=PHASE_CHOICES[3],
                            label="Execution Phase",
                            info="Select which phase of development to run"
                        )

                        auto_export_checkbox = gr.Checkbox(
                            label="Auto-export results",
                            value=True,
                            info="Automatically export to JSON, Markdown, CSV, and TXT after execution"
                        )

                        feedback_input = gr.Textbox(
                            label="Feedback / Apply Target",
                            lines=2,
                            placeholder="Optional: Feedback for reruns OR 'APPLY: C:\\path\\to\\repo' OR 'APPLY: https://github.com/user/repo' to apply changes",
                            info="Provide feedback for iterative improvements or specify where to apply changes"
                        )

                        approval_dropdown = gr.Dropdown(
                            choices=["Run (No Approval Yet)", "Approve", "Reject and Rerun"],
                            label="Action",
                            value="Run (No Approval Yet)",
                            info="Choose execution action (Run/Approve/Reject)"
                        )

            # Action buttons
            gr.Markdown("### ⚡ Execute Workflow")
            gr.Markdown("*Ready to run? Click below to start agent execution*")

            with gr.Row():
                run_button = gr.Button("▶️ Run Team", variant="primary", size="lg")
                clear_button = gr.Button("🗑️ Clear Logs", variant="secondary")

            # Live progress indicator
            execution_progress = gr.HTML(
                value="""
                <div id="execution_progress_container" style="display: none; background: #f8fafc; padding: 20px; border-radius: 12px; border: 2px solid #e2e8f0; margin: 16px 0;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 12px;">
                        <span style="font-weight: 600; color: #1e293b;">Executing Agents</span>
                        <span id="agent_progress_text" style="color: #64748b;">0 agents complete</span>
                    </div>
                    <div style="background: #e2e8f0; height: 24px; border-radius: 12px; overflow: hidden;">
                        <div id="progress_bar_fill" style="background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
                                    height: 100%; width: 0%; transition: width 0.5s ease;"></div>
                    </div>
                    <div id="current_agent_status" style="margin-top: 12px; color: #64748b; font-size: 14px;">
                        ⏳ Preparing execution...
                    </div>
                </div>

                <script>
                    // Progress bar control functions
                    window.showExecutionProgress = function(agentCount) {
                        const container = document.getElementById('execution_progress_container');
                        const progressBar = document.getElementById('progress_bar_fill');
                        const statusText = document.getElementById('current_agent_status');
                        const progressText = document.getElementById('agent_progress_text');

                        if (!container) return;

                        container.style.display = 'block';
                        progressBar.style.width = '0%';
                        statusText.textContent = '⏳ Preparing execution...';
                        progressText.textContent = '0 agents complete';

                        // Simulate progressive loading based on estimated time
                        // Assume 30-60 seconds per agent on average
                        const estimatedTimePerAgent = 45000; // 45 seconds
                        const totalTime = agentCount * estimatedTimePerAgent;
                        const updateInterval = 1000; // Update every second

                        let elapsed = 0;
                        let currentAgent = 0;

                        const progressInterval = setInterval(() => {
                            elapsed += updateInterval;
                            const progress = Math.min((elapsed / totalTime) * 100, 95); // Cap at 95% until complete

                            progressBar.style.width = progress + '%';

                            // Update current agent estimate
                            const estimatedAgent = Math.floor((elapsed / estimatedTimePerAgent));
                            if (estimatedAgent > currentAgent && estimatedAgent < agentCount) {
                                currentAgent = estimatedAgent;
                                progressText.textContent = `${currentAgent} agents complete`;
                                statusText.textContent = `🤖 Running agent ${currentAgent + 1}...`;
                            }

                            // Stop when we detect execution completion (status output changes)
                            const statusOutput = document.querySelector('[label="📊 Execution Status"] textarea');
                            if (statusOutput && statusOutput.value.includes('completed successfully')) {
                                clearInterval(progressInterval);
                                progressBar.style.width = '100%';
                                statusText.innerHTML = '<span style="color: #166534;">✅ Execution Complete!</span>';
                                progressText.textContent = `${agentCount} agents complete`;

                                // Hide after 3 seconds
                                setTimeout(() => {
                                    container.style.display = 'none';
                                }, 3000);
                            }
                        }, updateInterval);

                        // Safety timeout - hide after 20 minutes
                        setTimeout(() => {
                            clearInterval(progressInterval);
                            if (container.style.display !== 'none') {
                                container.style.display = 'none';
                            }
                        }, 1200000); // 20 minutes
                    };

                    window.hideExecutionProgress = function() {
                        const container = document.getElementById('execution_progress_container');
                        if (container) {
                            container.style.display = 'none';
                        }
                    };

                    // Listen for Run button clicks
                    document.addEventListener('click', (e) => {
                        if (e.target && e.target.textContent.includes('Run Team')) {
                            // Count selected agents
                            const checkboxes = document.querySelectorAll('input[type="checkbox"]:checked');
                            const agentCount = Array.from(checkboxes).filter(cb => {
                                const label = cb.parentElement;
                                return label && !label.textContent.includes('Code Review');
                            }).length;

                            if (agentCount > 0) {
                                showExecutionProgress(agentCount);
                            }
                        }
                    });
                </script>
                """,
                elem_id="execution_progress_bar"
            )

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
            export_status = gr.HTML(
                value="""
                <div style="background: #f8fafc; border: 2px solid #e2e8f0; padding: 16px; border-radius: 8px; text-align: center; color: #64748b;">
                    <div style="font-size: 14px;">No exports yet...</div>
                    <div style="font-size: 12px; margin-top: 6px; opacity: 0.8;">Export results will appear here</div>
                </div>
                """,
                label="Export Status"
            )

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

    # Visual summary of which agents have outputs
    agent_output_summary = gr.HTML(
        value="""
        <div id="agent_output_summary" style="background: #f8fafc; padding: 16px; border-radius: 8px; margin-bottom: 16px; border: 2px solid #e2e8f0;">
            <div style="font-weight: 600; color: #64748b; margin-bottom: 12px; font-size: 14px;">
                📊 Agent Output Summary
            </div>
            <div style="color: #94a3b8; font-size: 14px;">
                Run agents to see output summary here...
            </div>
        </div>
        """,
        visible=True
    )

    # Code extraction section
    with gr.Row():
        with gr.Column(scale=3):
            gr.Markdown("""
            ### 📦 Generate Project Files

            **Automatically extract code from agent outputs and create a working project.**

            This will:
            - 🔍 Find all code blocks in agent outputs
            - 📁 Create proper directory structure
            - 💾 Save files to disk
            - 📦 Generate package.json and README.md
            """)
        with gr.Column(scale=2):
            extract_code_btn = gr.Button(
                "📦 Extract Code to Files",
                variant="primary",
                size="lg",
                elem_id="extract_code_btn"
            )

            project_name_input = gr.Textbox(
                label="Project Name",
                placeholder="my-awesome-project",
                value="",
                info="Optional: Name for the generated project folder"
            )

    # Success feedback display (hidden until extraction completes)
    code_extraction_feedback = gr.HTML(
        value="",
        visible=False
    )

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

        # Execution History Tab
        with gr.Tab(label="📜 History"):
            gr.Markdown("### 📜 Execution History")
            gr.Markdown("*View and replay past executions from your export history*")

            with gr.Row():
                history_filter = gr.Dropdown(
                    choices=["All Executions", "Last 24 Hours", "Last 7 Days", "Successful Only", "Failed Only"],
                    value="All Executions",
                    label="Filter",
                    scale=1
                )
                history_search = gr.Textbox(
                    placeholder="🔍 Search by project description or agent names...",
                    label="Search",
                    scale=2
                )
                refresh_history_btn = gr.Button("🔄 Refresh", size="sm", variant="secondary", scale=1)

            execution_history_display = gr.HTML(
                value="""
                <div style="text-align: center; padding: 60px 20px; color: #94a3b8;">
                    <div style="font-size: 48px; margin-bottom: 16px;">📭</div>
                    <div style="font-size: 18px; font-weight: 600; margin-bottom: 8px;">No Execution History Yet</div>
                    <div style="font-size: 14px;">Run your first team to see execution history here!</div>
                </div>
                """
            )

    # Event handlers
    def recommend_agents_for_project(project_description):
        """Generate AI-powered agent recommendations based on project description

        Args:
            project_description: User's project description text

        Returns:
            Tuple of (HTML display string, clear button visibility boolean)
        """
        # Input validation for security
        if not isinstance(project_description, str):
            return (
                gr.update(visible=True, value="""
                <div style="background: #fef3c7; border: 2px solid #fbbf24; padding: 20px; border-radius: 12px; margin: 16px 0;">
                    <div style="font-weight: 600; color: #92400e; font-size: 16px;">⚠️ Invalid Input</div>
                    <div style="color: #92400e; margin-top: 8px;">Project description must be text.</div>
                </div>
                """),
                gr.update(visible=False)
            )

        # Limit description length to prevent abuse (max 10,000 characters)
        if len(project_description) > 10000:
            project_description = project_description[:10000]

        # Check minimum length
        if not project_description or len(project_description.strip()) < 20:
            return (
                gr.update(visible=True, value="""
                <div style="background: #fef3c7; border: 2px solid #fbbf24; padding: 20px; border-radius: 12px; margin: 16px 0;">
                    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                        <span style="font-size: 24px;">⚠️</span>
                        <div style="font-weight: 600; color: #92400e; font-size: 16px;">Need More Details</div>
                    </div>
                    <div style="color: #92400e; line-height: 1.5;">
                        Please provide a more detailed project description (at least 20 characters) to get personalized agent recommendations.
                    </div>
                </div>
                """),
                gr.update(visible=False)
            )

        # Keyword-to-agent mapping with confidence weighting
        keyword_agent_map = {
            # Web Development
            "web": {"agents": ["Web", "FrontendEngineer", "BackendEngineer", "FullStackEngineer"], "weight": 3},
            "website": {"agents": ["Web", "FrontendEngineer", "UIDesigner", "ProductDesigner"], "weight": 3},
            "frontend": {"agents": ["FrontendEngineer", "Web", "UIDesigner", "ProductDesigner"], "weight": 4},
            "backend": {"agents": ["BackendEngineer", "Senior", "DatabaseAdmin"], "weight": 4},
            "fullstack": {"agents": ["FullStackEngineer", "Senior", "Web", "DatabaseAdmin"], "weight": 4},
            "full-stack": {"agents": ["FullStackEngineer", "Senior", "Web", "DatabaseAdmin"], "weight": 4},

            # Mobile Development
            "mobile": {"agents": ["iOS", "Android", "MobileEngineer", "ProductDesigner"], "weight": 4},
            "ios": {"agents": ["iOS", "MobileEngineer", "UIDesigner"], "weight": 5},
            "android": {"agents": ["Android", "MobileEngineer", "UIDesigner"], "weight": 5},
            "app": {"agents": ["iOS", "Android", "MobileEngineer", "Web"], "weight": 2},

            # API & Backend
            "api": {"agents": ["BackendEngineer", "Senior", "APIDesigner", "Architect"], "weight": 4},
            "rest": {"agents": ["BackendEngineer", "APIDesigner", "Senior"], "weight": 3},
            "graphql": {"agents": ["BackendEngineer", "APIDesigner", "FullStackEngineer"], "weight": 4},

            # Database
            "database": {"agents": ["DatabaseAdmin", "DataEngineer", "BackendEngineer"], "weight": 4},
            "sql": {"agents": ["DatabaseAdmin", "BackendEngineer", "DataEngineer"], "weight": 3},
            "nosql": {"agents": ["DatabaseAdmin", "BackendEngineer"], "weight": 3},
            "postgres": {"agents": ["DatabaseAdmin", "BackendEngineer"], "weight": 3},
            "mongodb": {"agents": ["DatabaseAdmin", "BackendEngineer"], "weight": 3},

            # AI & ML
            "ai": {"agents": ["AIResearcher", "MLEngineer", "DataScientist", "DataEngineer"], "weight": 4},
            "ml": {"agents": ["MLEngineer", "DataScientist", "AIResearcher", "DataEngineer"], "weight": 4},
            "machine learning": {"agents": ["MLEngineer", "DataScientist", "DataEngineer"], "weight": 5},
            "data science": {"agents": ["DataScientist", "DataAnalyst", "DataEngineer"], "weight": 5},
            "deep learning": {"agents": ["MLEngineer", "AIResearcher", "DataScientist"], "weight": 4},

            # Data
            "data": {"agents": ["DataAnalyst", "DataEngineer", "DataScientist"], "weight": 3},
            "analytics": {"agents": ["DataAnalyst", "BusinessAnalyst", "DataEngineer"], "weight": 3},
            "visualization": {"agents": ["DataAnalyst", "FrontendEngineer", "UIDesigner"], "weight": 2},

            # Testing & QA
            "test": {"agents": ["QA", "TestAutomation", "Verifier"], "weight": 3},
            "testing": {"agents": ["QA", "TestAutomation", "Verifier", "Senior"], "weight": 4},
            "qa": {"agents": ["QA", "TestAutomation", "Verifier"], "weight": 4},
            "quality": {"agents": ["QA", "Verifier", "Senior"], "weight": 3},

            # Design & UX
            "design": {"agents": ["ProductDesigner", "UIDesigner", "UXResearcher", "Designs"], "weight": 4},
            "ui": {"agents": ["UIDesigner", "ProductDesigner", "FrontendEngineer"], "weight": 4},
            "ux": {"agents": ["UXResearcher", "ProductDesigner", "UIDesigner"], "weight": 4},
            "user experience": {"agents": ["UXResearcher", "ProductDesigner", "AccessibilitySpecialist"], "weight": 5},

            # DevOps & Cloud
            "cloud": {"agents": ["CloudArchitect", "DevOps", "SRE", "InfrastructureEngineer"], "weight": 4},
            "devops": {"agents": ["DevOps", "SRE", "CloudArchitect"], "weight": 5},
            "kubernetes": {"agents": ["DevOps", "CloudArchitect", "SRE"], "weight": 4},
            "docker": {"agents": ["DevOps", "BackendEngineer", "CloudArchitect"], "weight": 3},
            "aws": {"agents": ["CloudArchitect", "DevOps", "InfrastructureEngineer"], "weight": 3},

            # Security
            "security": {"agents": ["SecurityEngineer", "Senior", "Verifier", "PenetrationTester"], "weight": 4},
            "authentication": {"agents": ["SecurityEngineer", "BackendEngineer", "Senior"], "weight": 3},
            "auth": {"agents": ["SecurityEngineer", "BackendEngineer", "Senior"], "weight": 2},

            # Documentation
            "documentation": {"agents": ["TechnicalWriter", "DocumentationEngineer", "DeveloperAdvocate"], "weight": 4},
            "docs": {"agents": ["TechnicalWriter", "DocumentationEngineer"], "weight": 3},

            # Blockchain
            "blockchain": {"agents": ["BlockchainEngineer", "SecurityEngineer", "FullStackEngineer"], "weight": 5},
            "web3": {"agents": ["BlockchainEngineer", "FrontendEngineer", "SecurityEngineer"], "weight": 4},
            "smart contract": {"agents": ["BlockchainEngineer", "SecurityEngineer"], "weight": 5},

            # Performance
            "performance": {"agents": ["PerformanceEngineer", "SRE", "Architect", "Senior"], "weight": 3},
            "optimization": {"agents": ["PerformanceEngineer", "Senior", "Architect"], "weight": 3},
            "scalability": {"agents": ["Architect", "SRE", "PerformanceEngineer", "CloudArchitect"], "weight": 4}
        }

        # Score agents based on keyword matches
        agent_scores = {}
        desc_lower = project_description.lower()

        # Always include core agents with base score
        core_agents = ["PM", "Senior", "QA", "Memory"]
        for agent in core_agents:
            agent_scores[agent] = 2  # Base score for core agents

        # Score based on keyword matches
        total_weight = 0
        for keyword, data in keyword_agent_map.items():
            if keyword in desc_lower:
                weight = data["weight"]
                total_weight += weight
                for agent in data["agents"]:
                    agent_scores[agent] = agent_scores.get(agent, 0) + weight

        # Sort agents by score and take top 10
        sorted_agents = sorted(agent_scores.items(), key=lambda x: x[1], reverse=True)[:10]
        recommended_agents = [agent for agent, score in sorted_agents]

        # Calculate confidence score (0-100%)
        if total_weight == 0:
            confidence = 40  # Low confidence for generic descriptions
        else:
            confidence = min(100, 40 + (total_weight * 5))  # Scale based on keyword matches

        # Determine confidence level and color
        if confidence >= 80:
            confidence_level = "High Confidence"
            confidence_color = "#10b981"
        elif confidence >= 60:
            confidence_level = "Medium Confidence"
            confidence_color = "#f59e0b"
        else:
            confidence_level = "Low Confidence"
            confidence_color = "#ef4444"

        # Get agent descriptions for display
        agent_cards_html = ""
        for agent_id in recommended_agents:
            if agent_id in AGENT_DESCRIPTIONS:
                description = AGENT_DESCRIPTIONS[agent_id]
            else:
                description = f"Specialized agent for {agent_id} tasks"

            # Escape HTML to prevent XSS attacks
            description_safe = html.escape(description)
            agent_id_safe = html.escape(agent_id)

            agent_cards_html += f"""
            <div style="background: white; border: 2px solid #e2e8f0; border-radius: 8px; padding: 12px; margin-bottom: 8px;">
                <div style="font-weight: 600; color: #1e293b; font-size: 14px;">{agent_id_safe}</div>
                <div style="font-size: 13px; color: #64748b; margin-top: 4px;">
                    {description_safe}
                </div>
            </div>
            """

        # Generate recommendations HTML
        recommendations_html = f"""
        <div style="background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); border: 2px solid #0ea5e9; padding: 24px; border-radius: 12px; margin: 16px 0;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <div>
                    <div style="font-weight: 700; color: #0c4a6e; font-size: 18px; margin-bottom: 4px;">
                        ✨ Recommended Team for Your Project
                    </div>
                    <div style="font-size: 14px; color: #0369a1;">
                        Based on your project description, we suggest these {len(recommended_agents)} agents
                    </div>
                </div>
                <div style="background: {confidence_color}; color: white; padding: 8px 16px; border-radius: 8px; font-weight: 600; font-size: 14px;">
                    {confidence_level} ({confidence}%)
                </div>
            </div>

            <div style="margin-top: 16px; max-height: 400px; overflow-y: auto;">
                {agent_cards_html}
            </div>

            <div style="margin-top: 20px; padding-top: 20px; border-top: 2px solid #0ea5e9;">
                <div style="font-size: 13px; color: #0369a1; margin-bottom: 12px;">
                    💡 <strong>Tip:</strong> Click the button below to automatically select these agents in Step 2.
                </div>
                <button id="apply_recommendations_{hash(project_description)}" class="apply-recommendations-btn"
                        data-agents="{html.escape(json.dumps(recommended_agents))}"
                        style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 12px 24px; border: none; border-radius: 8px; font-weight: 600; cursor: pointer; font-size: 14px; box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3); transition: transform 0.2s ease;">
                    ✅ Apply These Recommendations
                </button>
            </div>
        </div>

        <script>
            // Function to show toast notification instead of alert
            function showToast(message, duration = 3000) {{
                const toast = document.createElement('div');
                toast.textContent = message;
                toast.style.cssText = `
                    position: fixed;
                    bottom: 20px;
                    right: 20px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 16px 20px;
                    border-radius: 8px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
                    z-index: 9999;
                    font-size: 14px;
                    max-width: 300px;
                    opacity: 0;
                    transition: opacity 0.3s ease;
                `;
                document.body.appendChild(toast);

                // Fade in
                setTimeout(() => {{ toast.style.opacity = '1'; }}, 10);

                // Fade out and remove
                setTimeout(() => {{
                    toast.style.opacity = '0';
                    setTimeout(() => {{ toast.remove(); }}, 300);
                }}, duration);
            }}

            // Function to apply recommended agents with improved matching
            function applyRecommendedAgents(agentIds) {{
                // Validate input is an array
                if (!Array.isArray(agentIds)) {{
                    console.error('Invalid agentIds parameter:', agentIds);
                    showToast('❌ Error: Invalid agent list');
                    return;
                }}

                // Find all checkboxes
                const allCheckboxes = document.querySelectorAll('input[type="checkbox"]');

                // Create Set for faster lookups
                const agentIdSet = new Set(agentIds.map(id => id.trim().toLowerCase()));
                let matchedCount = 0;

                // Process all checkboxes
                allCheckboxes.forEach(cb => {{
                    const label = cb.parentElement;
                    if (!label) return;

                    const labelText = label.textContent.trim();

                    // Skip non-agent checkboxes (Code Review, Auto-export, etc.)
                    if (labelText.includes('Code Review') ||
                        labelText.includes('Auto-export') ||
                        labelText.includes('auto-export')) {{
                        return;
                    }}

                    // Extract agent name (text before any description/emoji)
                    // Handles formats like "PM ℹ️" or "PM - Project Manager"
                    const agentName = labelText.split(/[ℹ️-]/)[0].trim();

                    // Use exact match instead of startsWith to prevent false positives
                    const shouldCheck = agentIdSet.has(agentName.toLowerCase());

                    if (cb.checked !== shouldCheck) {{
                        cb.checked = shouldCheck;
                        if (shouldCheck) matchedCount++;

                        // Trigger events to update Gradio state
                        cb.dispatchEvent(new Event('input', {{ bubbles: true, composed: true }}));
                        cb.dispatchEvent(new Event('change', {{ bubbles: true, composed: true }}));
                    }}
                }});

                // Show success message with count
                showToast(`✅ Selected ${{matchedCount}} recommended agents! Scroll down to review.`, 4000);

                // Scroll to Step 2
                const step2 = document.querySelector('[elem_id="step2_accordion"]') ||
                              document.getElementById('step2_accordion');
                if (step2) {{
                    setTimeout(() => {{
                        step2.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
                    }}, 500);
                }}
            }}

            // Event delegation for apply recommendations buttons
            // This is safer than inline onclick as it uses data attributes
            document.addEventListener('click', function(event) {{
                if (event.target.classList.contains('apply-recommendations-btn')) {{
                    // Get agent IDs from data attribute (already HTML-escaped)
                    const agentsData = event.target.getAttribute('data-agents');

                    // Validate and parse
                    if (!agentsData) {{
                        console.error('No agent data found on button');
                        showToast('❌ Error: No agent data available');
                        return;
                    }}

                    try {{
                        // Parse the JSON string
                        const agentIds = JSON.parse(agentsData);

                        // Validate it's an array
                        if (!Array.isArray(agentIds)) {{
                            throw new Error('Agent data is not an array');
                        }}

                        // Validate all items are strings (agent IDs)
                        const allStrings = agentIds.every(id => typeof id === 'string');
                        if (!allStrings) {{
                            throw new Error('Invalid agent ID format');
                        }}

                        // Apply recommendations
                        applyRecommendedAgents(agentIds);

                    }} catch (e) {{
                        console.error('Error parsing agent data:', e);
                        showToast('❌ Error: Invalid agent data format');
                    }}
                }}
            }});
        </script>
        """

        return (
            gr.update(visible=True, value=recommendations_html),
            gr.update(visible=True)
        )

    def clear_recommendations():
        """Clear the recommendations display"""
        return (
            gr.update(visible=False, value=""),
            gr.update(visible=False)
        )

    def load_execution_history(filter_type="All Executions", search_query=""):
        """Load execution history from gradio_exports directory

        Args:
            filter_type: Filter criteria (All, Last 24 Hours, etc.)
            search_query: Search text for filtering

        Returns:
            HTML string displaying execution history cards
        """
        import glob
        from datetime import datetime, timedelta

        exports_dir = Path("gradio_exports")

        # Check if exports directory exists
        if not exports_dir.exists():
            return """
            <div style="text-align: center; padding: 60px 20px; color: #94a3b8;">
                <div style="font-size: 48px; margin-bottom: 16px;">📭</div>
                <div style="font-size: 18px; font-weight: 600; margin-bottom: 8px;">No Execution History Yet</div>
                <div style="font-size: 14px;">Run your first team to see execution history here!</div>
            </div>
            """

        # Load all JSON export files
        json_files = sorted(exports_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)

        if not json_files:
            return """
            <div style="text-align: center; padding: 60px 20px; color: #94a3b8;">
                <div style="font-size: 48px; margin-bottom: 16px;">📭</div>
                <div style="font-size: 18px; font-weight: 600; margin-bottom: 8px;">No Execution History Yet</div>
                <div style="font-size: 14px;">Run your first team to see execution history here!</div>
            </div>
            """

        executions = []
        now = datetime.now()

        for json_file in json_files[:50]:  # Limit to 50 most recent
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                    # Extract execution metadata
                    timestamp_str = data.get("timestamp", "Unknown")
                    try:
                        exec_time = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                    except:
                        exec_time = datetime.fromtimestamp(json_file.stat().st_mtime)

                    agents_used = data.get("agents_used", [])
                    project_desc = data.get("project_description", "")
                    status = data.get("execution_status", "unknown")

                    # Apply filters
                    if filter_type == "Last 24 Hours":
                        if (now - exec_time) > timedelta(hours=24):
                            continue
                    elif filter_type == "Last 7 Days":
                        if (now - exec_time) > timedelta(days=7):
                            continue
                    elif filter_type == "Successful Only":
                        if status != "success":
                            continue
                    elif filter_type == "Failed Only":
                        if status == "success":
                            continue

                    # Apply search filter
                    if search_query:
                        search_lower = search_query.lower()
                        if not (search_lower in project_desc.lower() or
                                any(search_lower in agent.lower() for agent in agents_used)):
                            continue

                    executions.append({
                        "file": json_file.name,
                        "timestamp": exec_time,
                        "agents": agents_used,
                        "status": status,
                        "description": project_desc[:150] + ("..." if len(project_desc) > 150 else ""),
                        "full_data": data
                    })

            except Exception as e:
                print(f"[WARNING] Could not load {json_file}: {e}")
                continue

        if not executions:
            return f"""
            <div style="text-align: center; padding: 60px 20px; color: #94a3b8;">
                <div style="font-size: 48px; margin-bottom: 16px;">🔍</div>
                <div style="font-size: 18px; font-weight: 600; margin-bottom: 8px;">No Matching Executions</div>
                <div style="font-size: 14px;">Try adjusting your filters or search query</div>
            </div>
            """

        # Generate HTML cards for each execution
        cards_html = ""
        for i, exec_data in enumerate(executions):
            status_icon = "✅" if exec_data["status"] == "success" else "❌"
            status_color = "#10b981" if exec_data["status"] == "success" else "#ef4444"
            status_text = exec_data["status"].upper()

            # Format timestamp as relative time
            time_diff = now - exec_data["timestamp"]
            if time_diff.total_seconds() < 3600:
                time_display = f"{int(time_diff.total_seconds() / 60)} minutes ago"
            elif time_diff.total_seconds() < 86400:
                time_display = f"{int(time_diff.total_seconds() / 3600)} hours ago"
            else:
                time_display = f"{int(time_diff.days)} days ago"

            agents_display = ", ".join(exec_data["agents"][:5])
            if len(exec_data["agents"]) > 5:
                agents_display += f" + {len(exec_data['agents']) - 5} more"

            # Escape HTML
            safe_desc = html.escape(exec_data["description"])
            safe_agents = html.escape(agents_display)
            safe_file = html.escape(exec_data["file"])

            cards_html += f"""
            <div style="background: white; border: 2px solid #e2e8f0; border-left: 4px solid {status_color};
                        border-radius: 12px; padding: 20px; margin-bottom: 16px; cursor: pointer;
                        transition: box-shadow 0.2s ease, transform 0.2s ease;"
                 onmouseover="this.style.boxShadow='0 8px 16px rgba(0,0,0,0.1)'; this.style.transform='translateY(-2px)';"
                 onmouseout="this.style.boxShadow='0 1px 3px rgba(0,0,0,0.1)'; this.style.transform='translateY(0)';">
                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 12px;">
                    <div style="flex: 1;">
                        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
                            <span style="font-size: 20px;">{status_icon}</span>
                            <div style="font-weight: 600; color: #1e293b; font-size: 16px;">
                                Execution #{i + 1}
                            </div>
                            <span style="background: {status_color}; color: white; padding: 4px 10px;
                                       border-radius: 12px; font-size: 11px; font-weight: 600;">
                                {status_text}
                            </span>
                        </div>
                        <div style="color: #64748b; font-size: 13px; margin-top: 4px;">
                            🕐 {time_display} • 📄 {safe_file}
                        </div>
                    </div>
                    <button onclick="replayExecution('{safe_file}')"
                            style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                                   color: white; padding: 10px 20px; border: none; border-radius: 8px;
                                   font-weight: 600; cursor: pointer; font-size: 13px;
                                   box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
                                   transition: transform 0.2s ease;">
                        🔄 Replay
                    </button>
                </div>

                <div style="margin-top: 12px; padding-top: 12px; border-top: 1px solid #e2e8f0;">
                    <div style="color: #475569; font-size: 14px; margin-bottom: 8px;">
                        {safe_desc}
                    </div>
                    <div style="color: #64748b; font-size: 13px;">
                        <strong>👥 Agents:</strong> {safe_agents}
                    </div>
                </div>
            </div>
            """

        return f"""
        <div style="margin-top: 16px;">
            <div style="color: #64748b; font-size: 14px; margin-bottom: 16px;">
                Showing {len(executions)} execution(s)
            </div>
            {cards_html}
        </div>

        <script>
        function replayExecution(filename) {{
            alert('🔄 Replay functionality coming soon!\\n\\nYou can manually load this configuration from:\\ngradio_exports/' + filename);
        }}
        </script>
        """

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

    def generate_output_summary(selected_agents, outputs):
        """Generate HTML summary showing which agents have outputs"""
        if not selected_agents or not outputs:
            return """
            <div id="agent_output_summary" style="background: #f8fafc; padding: 16px; border-radius: 8px; margin-bottom: 16px; border: 2px solid #e2e8f0;">
                <div style="font-weight: 600; color: #64748b; margin-bottom: 12px; font-size: 14px;">
                    📊 Agent Output Summary
                </div>
                <div style="color: #94a3b8; font-size: 14px;">
                    Run agents to see output summary here...
                </div>
            </div>
            """

        # Build summary cards for each agent
        summary_cards = ""
        agents_with_output = 0
        total_chars = 0

        for agent in selected_agents:
            output = outputs.get(agent, "")
            has_output = len(output.strip()) > 0
            char_count = len(output)

            if has_output:
                agents_with_output += 1
                total_chars += char_count

            # Color coding
            if has_output:
                bg_color = "#f0fdf4"
                border_color = "#10b981"
                icon = "✅"
                status_text = f"{char_count:,} characters"
                status_color = "#15803d"
            else:
                bg_color = "#f8fafc"
                border_color = "#e2e8f0"
                icon = "⚪"
                status_text = "No output"
                status_color = "#94a3b8"

            summary_cards += f"""
            <div style="background: {bg_color}; border-left: 4px solid {border_color}; padding: 12px 16px; border-radius: 6px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <span style="font-size: 20px;">{icon}</span>
                    <div>
                        <div style="font-weight: 600; color: #1e293b; font-size: 14px;">{agent}</div>
                        <div style="font-size: 12px; color: {status_color};">{status_text}</div>
                    </div>
                </div>
                <div style="font-size: 12px; color: #64748b;">
                    Click "{agent}" tab below →
                </div>
            </div>
            """

        # Header summary
        header_html = f"""
        <div id="agent_output_summary" style="background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); padding: 20px; border-radius: 12px; border: 2px solid #0ea5e9; margin-bottom: 16px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                <div style="font-weight: 700; color: #0c4a6e; font-size: 16px;">
                    📊 Agent Output Summary
                </div>
                <div style="background: #0ea5e9; color: white; padding: 6px 14px; border-radius: 6px; font-weight: 600; font-size: 14px;">
                    {agents_with_output}/{len(selected_agents)} agents completed
                </div>
            </div>
            <div style="color: #0369a1; font-size: 13px; margin-bottom: 16px;">
                Total output: {total_chars:,} characters across {agents_with_output} agents
            </div>
            {summary_cards}
        </div>
        """

        return header_html

    def validate_github_url(url):
        """Validate GitHub URL format and provide feedback"""
        import re

        if not url or not url.strip():
            return gr.update(value="", visible=False)

        url = url.strip()

        # GitHub URL patterns
        patterns = [
            r'^https?://github\.com/[\w-]+/[\w.-]+/?$',  # https://github.com/username/repo
            r'^github\.com/[\w-]+/[\w.-]+/?$',  # github.com/username/repo
            r'^[\w-]+/[\w.-]+$'  # username/repo
        ]

        is_valid = any(re.match(pattern, url) for pattern in patterns)

        if is_valid:
            # Extract username and repo
            parts = url.replace('https://', '').replace('http://', '').replace('github.com/', '').strip('/').split('/')
            if len(parts) >= 2:
                username, repo = parts[0], parts[1]
                return gr.update(
                    value=f"""
                    <div style="background: #f0fdf4; border: 2px solid #10b981; padding: 12px; border-radius: 6px; margin-top: 8px;">
                        <div style="display: flex; align-items: center; gap: 10px;">
                            <span style="font-size: 20px;">✅</span>
                            <div>
                                <div style="font-weight: 600; color: #166534; font-size: 14px;">
                                    Valid GitHub Repository
                                </div>
                                <div style="color: #15803d; font-size: 12px; margin-top: 4px;">
                                    <strong>{username}/{repo}</strong>
                                </div>
                            </div>
                        </div>
                    </div>
                    """,
                    visible=True
                )

        # Invalid format - provide guidance
        return gr.update(
            value=f"""
            <div style="background: #fef3c7; border: 2px solid #f59e0b; padding: 12px; border-radius: 6px; margin-top: 8px;">
                <div style="display: flex; align-items: start; gap: 10px;">
                    <span style="font-size: 20px;">⚠️</span>
                    <div style="flex: 1;">
                        <div style="font-weight: 600; color: #92400e; font-size: 14px; margin-bottom: 8px;">
                            Invalid GitHub URL Format
                        </div>
                        <div style="color: #92400e; font-size: 12px; line-height: 1.5;">
                            <strong>Expected formats:</strong><br>
                            ✓ <code style="background: white; padding: 2px 6px; border-radius: 3px;">https://github.com/username/repo</code><br>
                            ✓ <code style="background: white; padding: 2px 6px; border-radius: 3px;">github.com/username/repo</code><br>
                            ✓ <code style="background: white; padding: 2px 6px; border-radius: 3px;">username/repo</code>
                        </div>
                        <div style="margin-top: 8px; padding-top: 8px; border-top: 1px solid #f59e0b40; color: #92400e; font-size: 11px;">
                            <strong>Your input:</strong> <code style="background: white; padding: 2px 6px; border-radius: 3px;">{url}</code>
                        </div>
                    </div>
                </div>
            </div>
            """,
            visible=True
        )

    def calculate_cost_estimate(selected_agents, model_preset):
        """Calculate estimated cost and time for selected agents and model preset"""

        if not selected_agents or len(selected_agents) == 0:
            return """
            <div style="background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
                        border: 2px solid #f59e0b; padding: 16px; border-radius: 8px;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <span style="font-size: 24px;">💰</span>
                    <div>
                        <div style="font-weight: 700; color: #92400e; font-size: 15px;">
                            Estimated Cost & Time
                        </div>
                        <div style="color: #b45309; font-size: 13px; margin-top: 2px;">
                            Select agents to see cost estimate
                        </div>
                    </div>
                </div>
            </div>
            """

        # Cost per 1M tokens (approximate, based on Anthropic pricing)
        # These are rough estimates - actual costs vary by input/output ratio
        model_costs = {
            "claude-opus-3-5-20250219": {"input": 15.0, "output": 75.0, "name": "Opus"},
            "claude-opus-4-20250514": {"input": 15.0, "output": 75.0, "name": "Opus 4"},
            "claude-sonnet-3-5-20241022": {"input": 3.0, "output": 15.0, "name": "Sonnet 3.5"},
            "claude-sonnet-4-20250514": {"input": 3.0, "output": 15.0, "name": "Sonnet 4"},
            "claude-3-5-haiku-20241022": {"input": 1.0, "output": 5.0, "name": "Haiku"}
        }

        # Average tokens per agent (rough estimate based on typical usage)
        # Input: ~2000 tokens (prompt + context), Output: ~3000 tokens (agent response)
        avg_input_tokens = 2000
        avg_output_tokens = 3000

        # Get models based on preset
        if not model_preset or model_preset == "Custom Selection":
            model_preset = "Speed (All Haiku)"  # Default

        preset_models = MODEL_PRESETS.get(model_preset, {})

        # Calculate cost per agent
        total_cost = 0
        cost_breakdown = []

        for agent in selected_agents:
            # Get model for this agent
            model_id = preset_models.get(agent, "claude-3-5-haiku-20241022")
            model_info = model_costs.get(model_id, {"input": 1.0, "output": 5.0, "name": "Haiku"})

            # Calculate cost for this agent
            input_cost = (avg_input_tokens / 1_000_000) * model_info["input"]
            output_cost = (avg_output_tokens / 1_000_000) * model_info["output"]
            agent_cost = input_cost + output_cost
            total_cost += agent_cost

            cost_breakdown.append({
                "agent": agent,
                "model": model_info["name"],
                "cost": agent_cost
            })

        # Estimate time (rough: 30-60 seconds per agent depending on model)
        time_per_agent = {
            "Opus": 60,
            "Opus 4": 60,
            "Sonnet 3.5": 45,
            "Sonnet 4": 45,
            "Haiku": 30
        }

        total_time_seconds = 0
        for item in cost_breakdown:
            total_time_seconds += time_per_agent.get(item["model"], 45)

        # Format time
        if total_time_seconds < 60:
            time_str = f"{total_time_seconds} seconds"
        else:
            minutes = total_time_seconds // 60
            seconds = total_time_seconds % 60
            time_str = f"{minutes}m {seconds}s"

        # Determine cost color and warning
        if total_cost < 0.10:
            cost_color = "#10b981"  # Green
            cost_label = "Low Cost"
            warning = ""
        elif total_cost < 0.50:
            cost_color = "#0ea5e9"  # Blue
            cost_label = "Moderate Cost"
            warning = ""
        elif total_cost < 2.00:
            cost_color = "#f59e0b"  # Orange
            cost_label = "Higher Cost"
            warning = """
            <div style="background: #fef3c7; padding: 10px; border-radius: 6px; margin-top: 12px; border-left: 3px solid #f59e0b;">
                <div style="font-size: 12px; color: #92400e;">
                    ⚠️ <strong>Consider using Haiku</strong> for faster, cheaper results if quality allows
                </div>
            </div>
            """
        else:
            cost_color = "#ef4444"  # Red
            cost_label = "High Cost"
            warning = f"""
            <div style="background: #fee2e2; padding: 10px; border-radius: 6px; margin-top: 12px; border-left: 3px solid #ef4444;">
                <div style="font-size: 12px; color: #991b1b; font-weight: 600;">
                    🚨 <strong>High Cost Alert!</strong>
                </div>
                <div style="font-size: 11px; color: #991b1b; margin-top: 4px;">
                    This run will cost approximately ${total_cost:.2f}. Consider:
                    <ul style="margin: 6px 0 0 16px; padding: 0;">
                        <li>Running fewer agents (currently {len(selected_agents)})</li>
                        <li>Using Sonnet or Haiku models instead of Opus</li>
                        <li>Running agents in smaller batches</li>
                    </ul>
                </div>
            </div>
            """

        # Build breakdown HTML
        breakdown_html = ""
        for item in cost_breakdown:
            breakdown_html += f"""
            <div style="display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid #f59e0b20;">
                <div style="font-size: 12px; color: #78350f;">
                    <strong>{item["agent"]}</strong> <span style="opacity: 0.7;">({item["model"]})</span>
                </div>
                <div style="font-size: 12px; color: #92400e; font-weight: 600;">
                    ${item["cost"]:.4f}
                </div>
            </div>
            """

        return f"""
        <div style="background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
                    border: 2px solid {cost_color}; padding: 16px; border-radius: 8px;">

            <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 12px;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <span style="font-size: 24px;">💰</span>
                    <div>
                        <div style="font-weight: 700; color: #92400e; font-size: 15px;">
                            Estimated Cost: <span style="color: {cost_color};">${total_cost:.3f}</span>
                        </div>
                        <div style="color: #b45309; font-size: 13px; margin-top: 2px;">
                            ⏱️ Estimated Time: ~{time_str}
                        </div>
                    </div>
                </div>
                <div style="background: {cost_color}; color: white; padding: 4px 12px; border-radius: 12px; font-size: 11px; font-weight: 600;">
                    {cost_label}
                </div>
            </div>

            <details style="margin-top: 12px;">
                <summary style="cursor: pointer; font-size: 12px; color: #92400e; font-weight: 600; margin-bottom: 8px;">
                    📊 Per-Agent Breakdown ({len(selected_agents)} agents)
                </summary>
                <div style="margin-top: 8px; max-height: 200px; overflow-y: auto;">
                    {breakdown_html}
                </div>
            </details>

            {warning}

            <div style="margin-top: 12px; padding-top: 12px; border-top: 1px solid #f59e0b40; font-size: 11px; color: #92400e; opacity: 0.8;">
                💡 Costs are estimates based on average token usage. Actual costs may vary.
            </div>
        </div>
        """

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

            # Generate output summary
            summary_html = generate_output_summary(selected, outputs)

            # Update stats
            stats = f"Agents Run: {len(selected)}\nModel Preset: {model_preset}\nLast Run: {datetime.now().strftime('%H:%M:%S')}\nStatus: Completed"
            if export_paths:
                stats += f"\n\nAuto-exported:\n✓ JSON\n✓ Markdown\n✓ CSV"

            return (status_msg, stats, summary_html) + tuple(logs)

        except Exception as e:
            error_msg = f"Error in run_and_update: {str(e)}"
            empty_summary = generate_output_summary([], {})
            return (error_msg, "Error occurred", empty_summary) + tuple([""] * len(AGENT_ROLES))

    def clear_all_logs():
        """Clear all agent logs"""
        for role in agent_logs:
            agent_logs[role] = []
        return ("Logs cleared.", "Ready to start...") + tuple([""] * len(AGENT_ROLES))

    # Wire up the run button
    # AI Recommendations button handlers
    get_recommendations_btn.click(
        recommend_agents_for_project,
        inputs=[project_input],
        outputs=[recommendations_display, clear_recommendations_btn]
    )

    clear_recommendations_btn.click(
        clear_recommendations,
        inputs=[],
        outputs=[recommendations_display, clear_recommendations_btn]
    )

    # Execution History event handlers
    refresh_history_btn.click(
        load_execution_history,
        inputs=[history_filter, history_search],
        outputs=[execution_history_display]
    )

    history_filter.change(
        load_execution_history,
        inputs=[history_filter, history_search],
        outputs=[execution_history_display]
    )

    history_search.submit(
        load_execution_history,
        inputs=[history_filter, history_search],
        outputs=[execution_history_display]
    )

    # Load history on startup
    demo.load(
        load_execution_history,
        inputs=[history_filter, history_search],
        outputs=[execution_history_display]
    )

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
        outputs=[status_output, stats_display, agent_output_summary] + log_outputs
    )

    def clear_all_and_summary():
        """Clear all logs and reset summary"""
        empty_summary = """
        <div id="agent_output_summary" style="background: #f8fafc; padding: 16px; border-radius: 8px; margin-bottom: 16px; border: 2px solid #e2e8f0;">
            <div style="font-weight: 600; color: #64748b; margin-bottom: 12px; font-size: 14px;">
                📊 Agent Output Summary
            </div>
            <div style="color: #94a3b8; font-size: 14px;">
                Run agents to see output summary here...
            </div>
        </div>
        """
        return ("Logs cleared.", "Ready to start...", empty_summary) + tuple([""] * len(AGENT_ROLES))

    clear_button.click(
        clear_all_and_summary,
        inputs=[],
        outputs=[status_output, stats_display, agent_output_summary] + log_outputs
    )

    # Code extraction button handler
    def handle_code_extraction(project_name, *agent_outputs):
        """
        Extract code from agent outputs and save to disk.

        Args:
            project_name: Optional project name
            *agent_outputs: Variable number of agent output strings (one per agent)

        Returns:
            Tuple of (feedback_html, visibility_boolean)
        """
        # Build outputs dict from agent textboxes
        outputs = {}
        for i, role in enumerate(AGENT_ROLES):
            if i < len(agent_outputs):
                outputs[role] = agent_outputs[i] or ""

        # Use default project name if none provided
        if not project_name or not project_name.strip():
            from datetime import datetime
            project_name = f"agent-project-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        # Clean project name (remove invalid characters)
        import re
        project_name = re.sub(r'[^\w\s-]', '', project_name).strip()
        project_name = re.sub(r'[-\s]+', '-', project_name)

        # Call the extraction function
        result = extract_and_save_code(outputs, project_name)

        if result['success']:
            # Generate success feedback HTML
            files_html = ""
            for file_path in result.get('files_created', []):
                files_html += f"""
                <div style="background: white; border-left: 3px solid #10b981; padding: 12px; margin-bottom: 8px; border-radius: 4px;">
                    <div style="font-family: 'Courier New', monospace; color: #1e293b; font-size: 14px;">
                        📄 {file_path}
                    </div>
                </div>
                """

            project_path = result.get('project_path', '').replace('\\', '/')

            feedback_html = f"""
            <div style="background: linear-gradient(135deg, #f0fdf4 0%, #d1fae5 100%);
                        border: 3px solid #10b981; padding: 24px; border-radius: 12px;
                        margin: 20px 0; box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2);">

                <div style="display: flex; align-items: center; gap: 16px; margin-bottom: 20px;">
                    <div style="font-size: 48px;">✅</div>
                    <div>
                        <div style="font-weight: 700; color: #166534; font-size: 22px; margin-bottom: 4px;">
                            Project Files Generated Successfully!
                        </div>
                        <div style="color: #15803d; font-size: 15px;">
                            Created {result['file_count']} files in working project structure
                        </div>
                    </div>
                </div>

                <div style="background: white; border-radius: 8px; padding: 16px; margin-bottom: 16px;
                            border: 2px solid #86efac;">
                    <div style="font-weight: 600; color: #166534; margin-bottom: 12px; font-size: 14px;">
                        📁 Project Location:
                    </div>
                    <div style="font-family: 'Courier New', monospace; background: #f8fafc;
                                padding: 12px; border-radius: 6px; color: #1e293b; font-size: 13px;
                                word-break: break-all;">
                        {project_path}
                    </div>
                </div>

                <div style="background: white; border-radius: 8px; padding: 16px; margin-bottom: 16px;
                            border: 2px solid #86efac; max-height: 300px; overflow-y: auto;">
                    <div style="font-weight: 600; color: #166534; margin-bottom: 12px; font-size: 14px;">
                        📄 Files Created ({result['file_count']}):
                    </div>
                    {files_html}
                </div>

                <div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 14px;
                            border-radius: 6px; margin-bottom: 16px;">
                    <div style="font-weight: 600; color: #92400e; margin-bottom: 6px; font-size: 13px;">
                        💡 Next Steps:
                    </div>
                    <div style="color: #92400e; font-size: 13px; line-height: 1.6;">
                        1. Open the project folder in your code editor<br>
                        2. Review generated files and customize as needed<br>
                        3. Install dependencies: <code style="background: white; padding: 2px 6px; border-radius: 3px;">npm install</code> or <code style="background: white; padding: 2px 6px; border-radius: 3px;">pip install -r requirements.txt</code><br>
                        4. Run the project and test functionality
                    </div>
                </div>

                <div style="margin-top: 20px; padding-top: 16px; border-top: 2px solid #86efac;">
                    <div style="color: #15803d; font-size: 13px; text-align: center;">
                        🎉 Your AI-generated project is ready to use! Happy coding!
                    </div>
                </div>
            </div>
            """

            return gr.update(value=feedback_html, visible=True)

        else:
            # Generate error feedback HTML
            error_message = result.get('message', 'Unknown error occurred')

            feedback_html = f"""
            <div style="background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
                        border: 3px solid #ef4444; padding: 24px; border-radius: 12px;
                        margin: 20px 0; box-shadow: 0 4px 12px rgba(239, 68, 68, 0.2);">

                <div style="display: flex; align-items: center; gap: 16px; margin-bottom: 16px;">
                    <div style="font-size: 48px;">❌</div>
                    <div>
                        <div style="font-weight: 700; color: #991b1b; font-size: 22px; margin-bottom: 4px;">
                            Code Extraction Failed
                        </div>
                        <div style="color: #b91c1c; font-size: 15px;">
                            Could not extract code from agent outputs
                        </div>
                    </div>
                </div>

                <div style="background: white; border-radius: 8px; padding: 16px; border: 2px solid #fca5a5;">
                    <div style="font-weight: 600; color: #991b1b; margin-bottom: 8px; font-size: 14px;">
                        Error Details:
                    </div>
                    <div style="color: #b91c1c; font-size: 13px; line-height: 1.6;">
                        {error_message}
                    </div>
                </div>

                <div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 14px;
                            border-radius: 6px; margin-top: 16px;">
                    <div style="font-weight: 600; color: #92400e; margin-bottom: 6px; font-size: 13px;">
                        💡 Troubleshooting Tips:
                    </div>
                    <div style="color: #92400e; font-size: 13px; line-height: 1.6;">
                        1. Make sure agents have been run and generated outputs<br>
                        2. Check that outputs contain code blocks (```language ... ```)<br>
                        3. Verify agents included file paths in comments (// src/App.js)<br>
                        4. Try running agents again with clearer prompts
                    </div>
                </div>
            </div>
            """

            return gr.update(value=feedback_html, visible=True)

    extract_code_btn.click(
        handle_code_extraction,
        inputs=[project_name_input] + log_outputs,
        outputs=[code_extraction_feedback]
    )

    # Agent preset dropdown handler - updates both category groups and main selector
    agent_preset_dropdown.change(
        update_agent_selection_grouped,
        inputs=[agent_preset_dropdown],
        outputs=list(agent_selectors_by_category.values())
    )

    # Cost estimator event handlers - update cost when agents or model changes
    agent_selector.change(
        calculate_cost_estimate,
        inputs=[agent_selector, model_preset_dropdown],
        outputs=[cost_estimate_display]
    )

    model_preset_dropdown.change(
        calculate_cost_estimate,
        inputs=[agent_selector, model_preset_dropdown],
        outputs=[cost_estimate_display]
    )

    # GitHub URL validation handler
    github_url_input.change(
        validate_github_url,
        inputs=[github_url_input],
        outputs=[github_url_validation]
    )

    # Quick Start preset button handlers
    def apply_quick_start_preset(preset_agents):
        """Apply a quick start preset - returns updates for all category groups including Essential"""
        updates = []

        # Handle Essential category first (it's always first in agent_selectors_by_category)
        if "Essential" in agent_selectors_by_category:
            essential_agents = ["PM", "Senior", "Research", "Ideas", "Designs", "Web", "QA", "Verifier", "DevOps", "Memory"]
            selected_essential = [aid for aid in essential_agents if aid in preset_agents]
            updates.append(gr.update(value=selected_essential))

        # Handle all other categories
        for category, agent_ids in agents_by_category.items():
            # Select agents that are both in this category and in the preset
            selected = [aid for aid in agent_ids if aid in preset_agents]
            updates.append(gr.update(value=selected))

        return tuple(updates)

    # Define preset agent combinations
    quick_start_presets = {
        "Web App Squad": ["PM", "Senior", "Web", "FrontendEngineer", "BackendEngineer", "QA"],
        "Mobile App Squad": ["PM", "ProductDesigner", "iOS", "Android", "QA", "Verifier"],
        "Backend Squad": ["PM", "Senior", "BackendEngineer", "DatabaseAdmin", "QA"],
        "Full-Stack Squad": ["PM", "FullStackEngineer", "Web", "DatabaseAdmin", "DevOps", "QA"],
        "AI/ML Squad": ["PM", "DataScientist", "MLEngineer", "DataEngineer", "Senior", "QA"],
        "Data Analytics Squad": ["PM", "DataAnalyst", "DataEngineer", "DataScientist", "QA"]
    }

    # Wire up quick start preset buttons
    preset_web.click(
        lambda: apply_quick_start_preset(quick_start_presets["Web App Squad"]),
        outputs=list(agent_selectors_by_category.values())
    )

    preset_mobile.click(
        lambda: apply_quick_start_preset(quick_start_presets["Mobile App Squad"]),
        outputs=list(agent_selectors_by_category.values())
    )

    preset_backend.click(
        lambda: apply_quick_start_preset(quick_start_presets["Backend Squad"]),
        outputs=list(agent_selectors_by_category.values())
    )

    preset_fullstack.click(
        lambda: apply_quick_start_preset(quick_start_presets["Full-Stack Squad"]),
        outputs=list(agent_selectors_by_category.values())
    )

    preset_ai.click(
        lambda: apply_quick_start_preset(quick_start_presets["AI/ML Squad"]),
        outputs=list(agent_selectors_by_category.values())
    )

    preset_data.click(
        lambda: apply_quick_start_preset(quick_start_presets["Data Analytics Squad"]),
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