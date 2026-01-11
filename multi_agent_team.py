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

# Import code application system
try:
    from code_applicator import apply_agent_changes_workflow, apply_agent_changes_from_github
    CODE_APPLICATOR_AVAILABLE = True
except ImportError:
    CODE_APPLICATOR_AVAILABLE = False
    print("⚠️  Code applicator not available. Install code_applicator.py for auto-apply features.")

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
agent_logs = {
    "System": [],  # System logs for execution status
    "PM": [], "Memory": [], "Research": [], "Ideas": [], "Designs": [],
    "Senior": [], "iOS": [], "Android": [], "Web": [],
    "QA": [], "Verifier": []
}

# Store complete run history with metadata
run_history = []

def log_agent_message(role, message):
    timestamp = datetime.now().strftime("%H:%M:%S")
    agent_logs[role].append(f"[{timestamp}] {message}")

# ==============================
# Agent Mapping and Default Prompts
# ==============================
AGENT_ROLES = ["PM", "Memory", "Research", "Ideas", "Designs", "Senior", "iOS", "Android", "Web", "QA", "Verifier"]

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

def create_agent_with_model(agent_key, model_id):
    """Dynamically create an agent with a specific model"""
    config = AGENT_CONFIGS[agent_key]
    llm = create_llm_for_model(model_id)

    return Agent(
        role=config["role"],
        goal=config["goal"],
        backstory=config["backstory"],
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
    """Export agent findings to JSON format"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = "".join(c if c.isalnum() or c in " -_" else "_" for c in project_name)[:50]
    filename = f"{safe_name}_{timestamp}.json"
    filepath = os.path.join(EXPORTS_DIR, filename)

    export_data = {
        "metadata": {
            "project_name": project_name,
            "timestamp": datetime.now().isoformat(),
            "selected_agents": selected_agents,
            "total_agents": len(selected_agents),
            **(metadata or {})
        },
        "agent_outputs": {}
    }

    for role in selected_agents:
        if role in outputs and outputs[role]:
            export_data["agent_outputs"][role] = {
                "role": role,
                "messages": agent_logs.get(role, []),
                "full_output": outputs[role]
            }

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)

    return filepath

def export_to_markdown(project_name, selected_agents, outputs, metadata=None):
    """Export agent findings to Markdown format"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = "".join(c if c.isalnum() or c in " -_" else "_" for c in project_name)[:50]
    filename = f"{safe_name}_{timestamp}.md"
    filepath = os.path.join(EXPORTS_DIR, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"# Multi-Agent Team Report: {project_name}\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Selected Agents:** {', '.join(selected_agents)}\n\n")

        if metadata:
            f.write("## Metadata\n\n")
            for key, value in metadata.items():
                f.write(f"- **{key}:** {value}\n")
            f.write("\n")

        f.write("---\n\n")

        for role in selected_agents:
            if role in outputs and outputs[role]:
                f.write(f"## {role} Agent\n\n")
                f.write(f"### Output\n\n")
                f.write(f"```\n{outputs[role]}\n```\n\n")

                if agent_logs.get(role):
                    f.write(f"### Log Messages\n\n")
                    for msg in agent_logs[role]:
                        f.write(f"- {msg}\n")
                    f.write("\n")

                f.write("---\n\n")

    return filepath

def export_to_csv(project_name, selected_agents, outputs, metadata=None):
    """Export agent findings to CSV format"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = "".join(c if c.isalnum() or c in " -_" else "_" for c in project_name)[:50]
    filename = f"{safe_name}_{timestamp}.csv"
    filepath = os.path.join(EXPORTS_DIR, filename)

    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Agent Role', 'Timestamp', 'Output', 'Message Count'])

        for role in selected_agents:
            if role in outputs and outputs[role]:
                message_count = len(agent_logs.get(role, []))
                writer.writerow([
                    role,
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    outputs[role][:500] + "..." if len(outputs[role]) > 500 else outputs[role],
                    message_count
                ])

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
            if role not in AGENT_CONFIGS:
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
            log_agent_message("System", "Starting task execution...")
            log_agent_message("System", f"Rate limit safety: Sequential execution ensures no parallel API calls")
            log_agent_message("System", f"Tier 2 limits: 1K req/min, 450K input tokens/min, 90K output tokens/min")
            log_agent_message("System", f"Expected usage: {len(tasks)} requests, ~{len(tasks)*5}K input tokens, ~{len(tasks)*2}K output tokens")
            log_agent_message("System", f"All limits safely respected with sequential execution")

            # Log task order (delays handled by sequential execution)
            for i, task in enumerate(tasks, 1):
                log_agent_message("System", f"Task {i}/{len(tasks)}: {task.description[:60]}...")

            result = crew.kickoff()
            log_agent_message("System", f"Execution completed successfully")

            # Extract and log individual task outputs
            try:
                for i, task in enumerate(tasks):
                    if hasattr(task, 'output') and task.output:
                        # Get the agent role for this task
                        agent_role = sorted_agents[i] if i < len(sorted_agents) else "Unknown"
                        # Log the task output to the agent's log
                        task_output = str(task.output)
                        log_agent_message(agent_role, f"Output:\n{task_output}")
                        log_agent_message("System", f"Captured output from {agent_role}")
            except Exception as e:
                log_agent_message("System", f"Warning: Could not extract task outputs: {str(e)}")

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
        prompt_inputs[role] = gr.Textbox(
            label=f"{role} Agent Prompt",
            placeholder=DEFAULT_PROMPTS[role],
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

# Build the enhanced Gradio interface
with gr.Blocks(title="Super Dev Team") as demo:
    gr.Markdown("# 🚀 Super Multi-Agent Dev Team")
    gr.Markdown("**Market-Smart • Lean • Hallucination-Resistant • Fully Customizable**")

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

            # Agent selection
            gr.Markdown("## 🤖 Select Agents to Execute")

            # Agent presets dropdown
            agent_preset_dropdown = gr.Dropdown(
                choices=["Custom Selection"] + list(AGENT_PRESETS.keys()),
                value="New Project Development",
                label="Agent Preset",
                info="Quick select common agent combinations"
            )

            agent_selector = gr.CheckboxGroup(
                choices=AGENT_ROLES,
                value=["PM", "Memory", "Research", "Ideas", "Designs", "QA"],  # Default selection
                label="Active Agents",
                info="Select which agents should work on this project"
            )

            # Code Review Mode toggle
            code_review_checkbox = gr.Checkbox(
                label="Code Review Mode",
                value=False,
                info="Optimize prompts for code analysis (Senior, QA, Verifier agents)"
            )

            # Execution Priority Configuration
            gr.Markdown("## 🔢 Execution Priority (Optional)")
            with gr.Accordion("Configure Agent Execution Order", open=False):
                gr.Markdown("""
**Lower number = runs first** | Agents with same priority can run in parallel

**Default order:**
1. Memory, PM → 2. Research → 3. Ideas → 4. Designs → 5. iOS/Android/Web → 6. Senior → 7. QA → 8. Verifier
                """)
                priority_inputs = {}
                with gr.Row():
                    for i, role in enumerate(AGENT_ROLES):
                        if i % 4 == 0 and i > 0:
                            with gr.Row():
                                pass

                        priority_inputs[role] = gr.Number(
                            label=f"{role}",
                            value=AGENT_EXECUTION_PRIORITY.get(role, 999),
                            minimum=1,
                            maximum=20,
                            step=1,
                            precision=0
                        )

            # Custom prompts section (collapsible)
            gr.Markdown("## ✏️ Custom Prompts (Optional)")
            with gr.Accordion("Override Agent Prompts", open=False):
                gr.Markdown("*Leave blank to use default prompts. Use {project_description} as placeholder.*")
                custom_prompt_inputs = {}
                for role in AGENT_ROLES:
                    custom_prompt_inputs[role] = gr.Textbox(
                        label=f"{role} Custom Prompt",
                        placeholder=DEFAULT_PROMPTS[role][:100] + "...",
                        lines=2,
                        value=""
                    )

            # Model selection section
            gr.Markdown("## 🤖 Model Selection")
            model_preset_dropdown = gr.Dropdown(
                choices=list(MODEL_PRESETS.keys()),
                value="Speed (All Haiku)",
                label="Model Preset",
                info="Choose performance vs. quality trade-off"
            )

            # Per-agent model override (advanced)
            with gr.Accordion("Advanced: Per-Agent Model Override", open=False):
                gr.Markdown("*Override individual agent models. Leave as 'Use Default' to follow preset.*")
                custom_model_inputs = {}
                model_choices = ["Use Default"] + [f"{v['name']} ({v['cost']} cost, {v['speed']} speed)"
                                                    for k, v in AVAILABLE_MODELS.items()]
                model_ids = ["Use Default"] + list(AVAILABLE_MODELS.keys())

                for role in AGENT_ROLES:
                    custom_model_inputs[role] = gr.Dropdown(
                        choices=model_choices,
                        value="Use Default",
                        label=f"{role} Model"
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
            with gr.Row():
                run_button = gr.Button("▶️ Run Team", variant="primary", size="lg")
                clear_button = gr.Button("🗑️ Clear Logs", variant="secondary")

            # Status display
            status_output = gr.Textbox(label="📊 Execution Status", lines=4, interactive=False)

        with gr.Column(scale=1):
            # Quick actions panel
            gr.Markdown("## 📤 Export Options")
            gr.Markdown("*Export current results to files*")

            with gr.Row():
                export_json_btn = gr.Button("JSON", size="sm")
                export_md_btn = gr.Button("Markdown", size="sm")
                export_csv_btn = gr.Button("CSV", size="sm")

            export_all_btn = gr.Button("📦 Export All Formats", variant="primary")
            export_status = gr.Textbox(label="Export Status", lines=3, interactive=False)

            gr.Markdown("## 📊 Quick Stats")
            stats_display = gr.Textbox(
                label="Session Info",
                value="Ready to start...",
                lines=5,
                interactive=False
            )

    # Agent outputs section
    gr.Markdown("---")
    gr.Markdown("## 📝 Agent Outputs")
    gr.Markdown("*Individual agent findings and logs (updates after each run)*")

    log_outputs = []
    export_individual_buttons = []

    with gr.Row():
        for i, role in enumerate(AGENT_ROLES):
            if i % 3 == 0 and i > 0:  # Create new row every 3 agents
                with gr.Row():
                    pass

            with gr.Column():
                gr.Markdown(f"### {role}")
                log_output = gr.Textbox(
                    lines=10,
                    interactive=False,
                    show_label=False,
                    placeholder=f"No output yet for {role}..."
                )
                log_outputs.append(log_output)

                export_btn = gr.Button(f"Export {role}", size="sm", variant="secondary")
                export_individual_buttons.append(export_btn)

    # Event handlers
    def update_agent_selection(preset_name):
        """Update agent selection based on preset"""
        if preset_name == "Custom Selection" or preset_name not in AGENT_PRESETS:
            return gr.update()  # No change
        return gr.update(value=AGENT_PRESETS[preset_name])

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

    # Agent preset dropdown handler
    agent_preset_dropdown.change(
        update_agent_selection,
        inputs=[agent_preset_dropdown],
        outputs=[agent_selector]
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

# Launch the application
if __name__ == "__main__":
    print("🚀 Launching Super Multi-Agent Dev Team...")
    print(f"📁 Exports will be saved to: {os.path.abspath(EXPORTS_DIR)}")
    print(f"📁 Projects will be saved to: {os.path.abspath(PROJECTS_DIR)}")
    demo.launch(share=False, server_name="127.0.0.1", server_port=7860, theme=gr.themes.Soft())