# 🚀 Super Multi-Agent Dev Team - Enhanced Edition

## Overview

A fully customizable multi-agent development team powered by CrewAI and Claude AI. This enhanced version includes agent selection, custom prompts, comprehensive export functionality, and robust error handling.

---

## 🆕 What's New

### ✅ Agent Selection & Presets
- **Checkbox interface** to select which agents to run
- **Quick presets** for common workflows (Code Review, Market Research, etc.)
- Run specific agents instead of the entire team
- Default selection: PM, Memory, Research, Ideas, Designs, QA

### ✅ Market Research Agent
- **NEW Agent**: Comprehensive market analysis and competitive intelligence
- Analyzes market size (TAM/SAM/SOM) and opportunities
- Identifies competitors and gaps in the market
- Recommends features and differentiation strategies
- Provides go-to-market recommendations

### ✅ Code Review Mode
- **Specialized mode** for analyzing existing code
- Optimized prompts for Senior, QA, and Verifier agents
- Architecture review and security audits
- Test strategy creation and gap identification
- Perfect for PR reviews and codebase evaluation

### ✅ Model Selection & Intelligent Fallback
- **5 Model Presets**: Speed, Balanced, Quality, Premium, Budget
- **Per-agent model override** for fine control
- **Automatic fallback** when rate limits hit (Opus → Sonnet → Haiku)
- **Retry with exponential backoff** for network errors
- **Save 60-80% on API costs** with strategic model mixing

### ✅ Custom Prompts
- **Per-agent prompt customization** via collapsible accordion
- Use `{project_description}` as placeholder in custom prompts
- Falls back to default prompts if left blank
- Full control over agent instructions

### ✅ Export Functionality
- **JSON Export**: Structured data with metadata and timestamps
- **Markdown Export**: Human-readable reports with formatting
- **CSV Export**: Tabular data for spreadsheet analysis
- **Individual Agent Export**: Export findings from specific agents
- **Auto-export**: Automatically export after each run (optional)

### ✅ Robust Error Handling
- Comprehensive try-catch blocks throughout
- Graceful fallbacks for partial failures
- Detailed error messages with context
- Validation of all inputs before execution

### ✅ Enhanced UI
- Modern, organized layout with clear sections
- Quick stats panel showing run information
- Individual export buttons for each agent
- Clear logs button to reset state
- Better visual hierarchy

### ✅ Rate Limit Safety
- **Sequential execution** prevents parallel API calls
- **Guaranteed compliance** with Anthropic Tier 2 limits
- **Real-time monitoring** of API usage expectations
- **Automatic fallback** for rare rate limit scenarios
- **Transparent logging** of all rate limit safety measures
- See [RATE_LIMITS.md](RATE_LIMITS.md) for complete details

### ✅ Code Application System **[NEW!]**
- **Auto-apply AI suggestions** to existing codebases
- **Safe Git branching** - never modifies main directly
- **Automatic PR creation** for human review
- **Full rollback capability** if changes aren't right
- **Parse code from agent outputs** and apply to files
- See [CODE_APPLICATION_GUIDE.md](CODE_APPLICATION_GUIDE.md) for complete details

---

## 📋 Features

### 11 Specialized Agents

1. **PM (Project Manager)**: Creates sprint plans and coordinates work
2. **Memory**: Recalls past learnings and stores new knowledge
3. **Research**: Analyzes market opportunities, competition, and strategic positioning
4. **Ideas**: Generates market-smart feature ideas
5. **Designs**: Creates UI/UX designs and wireframes
6. **Senior**: Reviews architecture and tech stack choices
7. **iOS**: Builds iOS components (Swift/SwiftUI)
8. **Android**: Builds Android components (Kotlin/Compose)
9. **Web**: Builds web components (React/JS)
10. **QA**: Tests functionality and validates quality
11. **Verifier**: Checks for hallucinations and consistency

### Agent Presets

Pre-configured agent combinations for common workflows:

- **New Project Development**: PM, Memory, Research, Ideas, Designs, QA
- **Code Review**: Senior, QA, Verifier
- **Security Audit**: Senior, Verifier
- **Market Research**: Memory, Research, Ideas, Senior
- **Full Stack Development**: PM, Research, Ideas, Designs, iOS, Android, Web, QA, Verifier
- **Architecture Review**: Senior, Verifier

### Code Review Mode

When enabled, optimizes prompts for analyzing existing code:

- **Senior Agent**: Performs comprehensive code review (architecture, patterns, security)
- **QA Agent**: Creates test strategy and identifies testing gaps
- **Verifier Agent**: Conducts security audit and compliance checks

Perfect for evaluating existing codebases or reviewing pull requests.

### Anti-Hallucination System

All agents are configured with:
- Fact-conscious reasoning
- Citation requirements
- "I don't know" encouragement
- Step-by-step thinking
- Self-reflection on over-engineering

---

## 🚀 Quick Start

### Prerequisites

```bash
# Install dependencies
pip install gradio crewai crewai-tools gitpython anthropic

# Set your API key (Windows)
set ANTHROPIC_API_KEY=your_key_here

# Or (Linux/Mac)
export ANTHROPIC_API_KEY=your_key_here
```

### Running the Application

```bash
python multi_agent_team.py
```

The app will launch at: `http://127.0.0.1:7860`

---

## 📖 User Guide

### 1. Project Configuration

**Project Description**
- Enter a detailed description of your project
- Be specific about requirements and constraints
- The description is passed to all selected agents

### 2. Select Agents

**Agent Preset Dropdown**
- Use quick presets for common workflows:
  - **New Project Development**: PM, Memory, Research, Ideas, Designs, QA
  - **Code Review**: Senior, QA, Verifier
  - **Security Audit**: Senior, Verifier
  - **Market Research**: Memory, Research, Ideas, Senior
  - **Full Stack Development**: All agents for comprehensive coverage
  - **Architecture Review**: Senior, Verifier
- Select "Custom Selection" to manually choose agents

**Agent Selection Checkboxes**
- ✅ Check the agents you want to run
- Default: PM, Memory, Research, Ideas, Designs, QA
- You can run as few as 1 agent or all 11
- Preset dropdown automatically updates checkboxes

**Code Review Mode Toggle**
- ✅ Enable for code review/analysis tasks
- Optimizes prompts for Senior, QA, and Verifier agents
- Focuses on architecture, testing, and security
- Use when evaluating existing code

**Execution Priority Configuration**
- Click "Configure Agent Execution Order" to customize
- Lower number = runs first (1 runs before 2, 2 before 3, etc.)
- Agents with same priority can run in parallel
- Default order: Memory/PM (1) → Research (2) → Ideas (3) → Designs (4) → Engineers (5) → Senior (6) → QA (7) → Verifier (8)
- Example: Set Research=1 and Ideas=1 to run them in parallel at the start

### 3. Custom Prompts (Optional)

**How to Use:**
1. Click "Override Agent Prompts" accordion
2. Enter custom instructions for specific agents
3. Use `{project_description}` as placeholder
4. Leave blank to use defaults

**Example Custom Prompt:**
```
For PM Agent:
"Create a detailed 2-week sprint plan for: {project_description}
Focus on mobile-first development and include testing milestones."
```

### 4. Execution Controls

**Execution Phase:**
- Planning Only (Memory + PM + Ideas)
- Planning + Design (Up to Designs)
- Planning + Design + Code (Up to Engineers)
- **Full Run (All Agents)** ← Default

**Auto-export:**
- ✅ Enabled: Automatically exports to JSON, MD, CSV after run
- ❌ Disabled: Manual export only

**Feedback for Reruns:**
- Add feedback when using "Reject and Rerun"
- Previous outputs will be refined based on feedback

### 5. Running the Team

1. Click **"▶️ Run Team"** button
2. Monitor execution status in real-time
3. View individual agent outputs as they complete
4. Check Quick Stats panel for summary

### 6. Exporting Results

**Auto-Export (Recommended):**
- Enable "Auto-export results" checkbox
- Files are automatically saved after each run

**Manual Export:**
- **JSON**: Structured data format
- **Markdown**: Readable report format
- **CSV**: Spreadsheet-compatible format
- **Export All**: All three formats at once

**Individual Agent Export:**
- Click "Export {AgentName}" button under each agent
- Saves that agent's findings to a dedicated file

**Export Location:**
```
./exports/
  ├── ProjectName_YYYYMMDD_HHMMSS.json
  ├── ProjectName_YYYYMMDD_HHMMSS.md
  ├── ProjectName_YYYYMMDD_HHMMSS.csv
  └── ProjectName_AgentName_YYYYMMDD_HHMMSS.md
```

---

## 📁 File Structure

```
MultiAgentTeam/
├── multi_agent_team.py          # Main application
├── team_memory.json             # Persistent memory storage
├── README_ENHANCED.md           # This file
├── projects/                    # Git repos for approved projects
│   └── ProjectName_YYYYMMDD/
└── exports/                     # Exported findings
    ├── *.json                   # JSON exports
    ├── *.md                     # Markdown exports
    └── *.csv                    # CSV exports
```

---

## 🔧 Configuration

### Model Settings

Located in `multi_agent_team.py`:

```python
CLAUDE_MODEL = "claude-3-haiku-20240307"  # Fast & cost-effective
```

**Available Models:**
- `claude-3-haiku-20240307` - Fastest, cheapest
- `claude-3-sonnet-20240229` - Balanced
- `claude-3-opus-20240229` - Most capable

### Rate Limiting

```python
RATE_LIMIT_DELAY = 15  # Seconds between tasks
```

Adjust based on your API tier and needs.

### Default Agent Selection

```python
value=["PM", "Memory", "Ideas", "Designs", "QA"]
```

Change the default selected agents in the UI code.

---

## 🎯 Use Cases

### 1. Market Research & Validation
**Agents**: Memory, Research, Ideas, Senior
**Purpose**: Validate business ideas, analyze competition, identify market opportunities
**Code Review Mode**: Disabled

### 2. Code Review & Security Audit
**Agents**: Senior, QA, Verifier
**Purpose**: Review and validate existing implementations, identify security issues
**Code Review Mode**: Enabled ✓

### 3. New Project Development
**Agents**: PM, Memory, Research, Ideas, Designs, QA
**Purpose**: Complete planning and design for new projects with market insights
**Code Review Mode**: Disabled

### 4. Full-Stack Development
**Agents**: All 11 agents
**Purpose**: Complete project lifecycle from market research to testing
**Code Review Mode**: Disabled

### 5. Platform-Specific Development
**Agents**: PM, Research, Ideas, iOS (or Android/Web), QA
**Purpose**: Focus on single platform implementation with market context
**Code Review Mode**: Disabled

### 6. Architecture Review
**Agents**: Senior, Verifier
**Purpose**: Deep dive on system architecture and design patterns
**Code Review Mode**: Enabled ✓

### 7. Rapid Prototyping
**Agents**: PM, Ideas, Designs
**Purpose**: Quickly validate concepts and create wireframes
**Code Review Mode**: Disabled

---

## 📊 Export Format Details

### JSON Export Structure

```json
{
  "metadata": {
    "project_name": "My Project",
    "timestamp": "2026-01-10T14:30:00",
    "selected_agents": ["PM", "Ideas", "QA"],
    "total_agents": 3,
    "phase": "Full Run",
    "agent_count": 3
  },
  "agent_outputs": {
    "PM": {
      "role": "PM",
      "messages": ["[14:30:00] Starting task...", ...],
      "full_output": "Complete output text..."
    }
  }
}
```

### Markdown Export Structure

```markdown
# Multi-Agent Team Report: My Project

**Generated:** 2026-01-10 14:30:00
**Selected Agents:** PM, Ideas, QA

---

## PM Agent

### Output
```
Sprint plan details...
```

### Log Messages
- [14:30:00] Starting task...
- [14:30:15] Task completed
```

### CSV Export Structure

```csv
Agent Role,Timestamp,Output,Message Count
PM,2026-01-10 14:30:00,"Sprint plan...",5
Ideas,2026-01-10 14:30:15,"Feature ideas...",3
```

---

## 🛡️ Error Handling

The system includes comprehensive error handling:

### Input Validation
- Empty project description → Error message
- No agents selected → Error message
- Invalid agent names → Skipped with warning

### Execution Errors
- Crew creation fails → Detailed error message
- Task execution fails → Partial outputs preserved
- API errors → Graceful fallback with context

### Export Errors
- File write fails → Error message with details
- Invalid format → Format validation error
- Missing data → Clear error about what's missing

### Recovery
- Partial outputs are always saved
- Logs are preserved even on failure
- System state remains consistent

---

## 🔒 Security

### API Key Management

**✅ DO:**
- Set `ANTHROPIC_API_KEY` as environment variable
- Use system environment variables
- Rotate keys regularly

**❌ DON'T:**
- Hardcode keys in source code
- Commit keys to version control
- Share keys in logs or exports

### Data Privacy

- All processing happens locally
- Exports are saved to local filesystem
- No data sent to third parties (except Claude API)

---

## 🐛 Troubleshooting

### Common Issues

**"Error: Project description cannot be empty"**
- Solution: Enter a project description before running

**"Error: Please select at least one agent"**
- Solution: Check at least one agent in the selection

**"Error creating crew"**
- Solution: Check API key is set correctly
- Solution: Verify network connection

**"Export failed"**
- Solution: Check write permissions on `./exports/` directory
- Solution: Ensure disk space available

**Rate limit errors**
- Solution: Increase `RATE_LIMIT_DELAY` value
- Solution: Reduce number of agents running simultaneously

### Debug Mode

Enable verbose logging:
```python
verbose=True  # Already enabled in crew configuration
```

Check console output for detailed execution logs.

---

## 🎨 Customization Guide

### Adding New Agents

1. Define the agent:
```python
custom_agent = Agent(
    role='Custom Role',
    goal='Custom goal',
    backstory=UNIVERSAL_BACKSTORY + "Custom instructions",
    llm=anthropic_llm
)
```

2. Add to agent map:
```python
agent_map = {
    "Custom": custom_agent,
    # ... existing agents
}
```

3. Add default prompt:
```python
DEFAULT_PROMPTS["Custom"] = "Your custom prompt template"
```

4. Update `AGENT_ROLES` list:
```python
AGENT_ROLES = ["PM", "Memory", ..., "Custom"]
```

### Modifying Default Prompts

Edit the `DEFAULT_PROMPTS` dictionary:
```python
DEFAULT_PROMPTS = {
    "PM": "Your new PM prompt...",
    # ... other agents
}
```

### Changing Export Formats

Add new export functions:
```python
def export_to_xml(project_name, selected_agents, outputs):
    # Your XML export logic
    pass
```

Wire up UI button:
```python
export_xml_btn = gr.Button("XML")
export_xml_btn.click(
    lambda p, s: export_handler("xml", p, s),
    inputs=[project_input, agent_selector],
    outputs=[export_status]
)
```

---

## 📈 Performance Tips

### Optimize for Speed
- Use fewer agents for faster results
- Select `claude-3-haiku` model (fastest)
- Reduce `RATE_LIMIT_DELAY` if your tier allows

### Optimize for Quality
- Use all agents for comprehensive coverage
- Select `claude-3-opus` model (most capable)
- Add detailed custom prompts

### Optimize for Cost
- Use `claude-3-haiku` model (cheapest)
- Select only essential agents
- Use memory agent to avoid repeated work

---

## 🤝 Contributing

### Reporting Issues
- Describe the problem clearly
- Include error messages
- Specify agent selection and settings

### Feature Requests
- Explain the use case
- Describe expected behavior
- Consider edge cases

---

## 📜 License

This project uses:
- **CrewAI**: Apache 2.0 License
- **Gradio**: Apache 2.0 License
- **Claude AI**: Anthropic Terms of Service

---

## 🎓 Learning Resources

### CrewAI Documentation
- [Official Docs](https://docs.crewai.com/)
- [GitHub](https://github.com/joaomdmoura/crewAI)

### Claude API
- [Anthropic Docs](https://docs.anthropic.com/)
- [API Reference](https://docs.anthropic.com/claude/reference)

### Gradio
- [Official Docs](https://gradio.app/docs/)
- [Guides](https://gradio.app/guides/)

---

## 💡 Tips & Best Practices

### Writing Good Project Descriptions
- Be specific about requirements
- Include constraints (budget, timeline, platforms)
- Mention target users
- Specify must-have vs nice-to-have features

### Using Custom Prompts Effectively
- Add domain-specific context
- Specify output format preferences
- Include examples when helpful
- Use constraints to guide thinking

### Managing Exports
- Use descriptive project names (they become filenames)
- Enable auto-export for important runs
- Review JSON for programmatic processing
- Use Markdown for sharing with team
- Use CSV for data analysis

### Memory System
- Let agents run multiple times to build memory
- Memory improves over time
- Review `team_memory.json` periodically
- Clear memory if switching domains

---

## 📞 Support

For issues, questions, or feedback:
1. Check the Troubleshooting section above
2. Review the configuration settings
3. Check console logs for detailed errors
4. Verify API key and network connectivity

---

## 🎉 Quick Reference

### Keyboard Shortcuts
- None (GUI-based application)

### Default Ports
- Web UI: `http://127.0.0.1:7860`

### File Locations
- Exports: `./exports/`
- Projects: `./projects/`
- Memory: `./team_memory.json`

### Recommended Workflow
1. Enter project description
2. Select agents (start with defaults)
3. Run without custom prompts first
4. Review outputs
5. Add custom prompts if needed
6. Rerun with feedback
7. Export results
8. Approve for Git repo creation

---

## 📚 Documentation

- **[README_ENHANCED.md](README_ENHANCED.md)** - This file: Complete feature guide
- **[QUICK_START.md](QUICK_START.md)** - Getting started in 5 minutes
- **[MODEL_SELECTION_GUIDE.md](MODEL_SELECTION_GUIDE.md)** - Model presets, costs, and intelligent fallback
- **[RATE_LIMITS.md](RATE_LIMITS.md)** - Rate limit safety and API compliance
- **[CODE_APPLICATION_GUIDE.md](CODE_APPLICATION_GUIDE.md)** - Auto-applying AI changes to your codebase

---

**Version**: 4.0 (Code Application Edition)
**Last Updated**: January 2026
**Status**: Production Ready ✅
