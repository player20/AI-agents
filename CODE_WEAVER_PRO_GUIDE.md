# Code Weaver Pro - Complete Implementation Guide

## 🎯 Overview

Code Weaver Pro is an advanced, meta self-improving AI agent system built on top of your existing multi-agent platform. It transforms complex software development into a magical, user-friendly experience while maintaining powerful capabilities for deep analysis and continuous improvement.

## ✨ Key Features Implemented

### 1. **Dynamic Agent Adaptation** (`core/meta_prompt.py`)
- Automatically extracts context from user input (industry, domain, pain points, features)
- Dynamically injects specialized expertise into agent backstories
- Requests clarification when context is unclear
- Makes agents domain-aware for specific tasks (e.g., EV charging platforms, healthcare, fintech)

**How it works:**
```python
from core.meta_prompt import MetaPromptEngine

engine = MetaPromptEngine()
context = engine.extract_context("An EV charger sharing platform with drop-offs")
# Outputs: {"industry": "green tech sharing economy", "pain_points": ["drop-offs"], ...}

enhanced_agents = engine.enhance_all_agents(agents_config, user_input)
# Each agent now has specialized context appended to their backstory
```

### 2. **Audit Mode** (`core/audit_mode.py`)
- Analyzes user behavior and drop-offs in existing apps
- Detects analytics SDKs (PostHog, AppsFlyer, OneSignal, Segment, etc.)
- Crawls apps with Playwright to simulate user journeys
- Generates funnel analysis with drop-off percentages
- Provides actionable recommendations with code snippets

**Capabilities:**
- SDK Detection: Scans codebase for analytics libraries
- Session Simulation: Uses Faker to generate dummy user data
- Funnel Analysis: Tracks landing → signup → form → completion
- Recommendations: Prioritized fixes with expected impact

### 3. **A/B Test Generator** (`core/ab_test_generator.py`)
- Generates 2-3 variants for A/B testing
- Varies colors, copy, CTAs across variants
- Creates separate Git branches for each variant
- Injects analytics tracking events
- Outputs experiment configuration for PostHog/Optimizely

**Variant Types:**
- **Control**: Original design (baseline)
- **Variant A**: Bold & Action-Oriented (urgent copy, prominent CTAs)
- **Variant B**: Trust & Calm (professional tone, softer CTAs)

### 4. **Professional Report Generator** (`core/report_generator.py`)
- Generates two types of PDF reports:
  - **Executive Summary**: High-level with charts, screenshots, recommendations
  - **Dev Handover**: Technical details with code diffs, Git commits, setup

**Report Features:**
- Professional styling with charts (matplotlib/seaborn)
- Embedded screenshots
- Funnel visualization
- Color-coded priority recommendations
- Download as PDF

### 5. **Enhanced User Interface** (Streamlit)
The existing `app.py` and `streamlit_ui/` components provide:
- Clean single-page interface with dark theme
- Large text input for project descriptions
- Four main options:
  - Market Research (quick viability check)
  - Upload Code (upgrade existing apps)
  - Platform Selection (Website, Web App, iOS, Android)
  - Advanced options (in expandable sections)

## 🚀 How to Use

### Step 1: Installation

```bash
# Clone the repository (if not already)
git clone https://github.com/player20/AI-agents
cd AI-agents

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install

# Set environment variable
export ANTHROPIC_API_KEY="your-api-key-here"
```

### Step 2: Run Code Weaver Pro

```bash
streamlit run app.py
```

### Step 3: Basic Usage

1. **Simple App Creation:**
   - Enter your idea: "A recipe app where users save favorites and share with friends"
   - Select platforms: Web App, iOS
   - Click "GO"
   - Watch live progress bars and terminal output
   - Download generated app as ZIP

2. **Market Research Mode:**
   - Check "Market research" option
   - Enter idea
   - Get TAM/SAM/SOM analysis, competitors, go/no-go decision
   - Optional: Check "Research only" to stop before building

3. **Upgrade Existing Code:**
   - Check "Upgrade code" option
   - Upload ZIP or paste code
   - System analyzes, suggests improvements, generates diffs
   - Shows before/after screenshots
   - Creates Git branch with improvements

4. **Audit Mode (Drop-off Analysis):**
   ```python
   # In your execution flow
   from core.audit_mode import AuditModeAnalyzer

   analyzer = AuditModeAnalyzer(agents_config, model_preset)

   # Option A: Upload code for SDK detection
   code_files = extract_code_from_zip(uploaded_zip)
   detected_sdks = analyzer.detect_sdks(code_files)

   # Option B: Crawl live app
   sessions = await analyzer.crawl_app_flows(
       base_url="http://localhost:3000",
       simulate_users=10
   )

   # Analyze sessions
   funnel_analysis = analyzer.analyze_sessions(sessions)
   recommendations = analyzer.generate_recommendations(
       funnel_analysis,
       detected_sdks,
       code_files
   )
   ```

5. **A/B Test Generation:**
   ```python
   from core.ab_test_generator import ABTestGenerator

   generator = ABTestGenerator(project_path="/path/to/project")

   # Generate variants
   variants = generator.generate_variants(variant_count=3)

   # Create Git branches
   branches = generator.create_variant_branches(variants)

   # Get experiment config for PostHog
   config = generator.generate_experiment_config(variants)
   ```

6. **Export Reports:**
   ```python
   from core.report_generator import ReportGenerator

   generator = ReportGenerator()

   # Executive Summary
   generator.generate_executive_summary(
       project_data={
           'project_name': 'My App',
           'scores': {'speed': 8, 'mobile': 9},
           'funnel_analysis': {...},
           'recommendations': [...]
       },
       output_path='executive_summary.pdf'
   )

   # Dev Handover
   generator.generate_dev_handover(
       project_data={
           'tech_stack': {...},
           'setup_instructions': [...],
           'code_diffs': [...]
       },
       output_path='dev_handover.pdf'
   )
   ```

## 🏗️ Architecture

### Workflow Flow (with LangGraph-style orchestration)

```
User Input
    ↓
Meta Prompt (extract context, clarify if needed)
    ↓
Enhanced Agents (adapted backstories with domain expertise)
    ↓
Orchestrator (LangGraph cycles)
    ├─ Planning Phase
    │  ├─ PM Agent → Sprint Plan
    │  ├─ Challenger Agent → Review & Critique
    │  ├─ Reflector → Synthesize & Improve
    │  └─ Verifier → Check for hallucinations
    ├─ Drafting Phase
    │  ├─ Research Agent → Market Analysis
    │  ├─ Ideas Agent → Feature Brainstorm
    │  ├─ Design Agent → UI/UX Wireframes
    │  ├─ Senior Agent → Architecture Review
    │  ├─ Reflector → Quality Check
    │  └─ Verifier → Consistency Check
    ├─ Implementation Phase
    │  ├─ Platform Engineers (iOS/Android/Web)
    │  ├─ Code Generators → Generate Project
    │  └─ Code Applicator → Apply Changes
    ├─ Testing Phase (Test-Fix-Retest Loop, max 10 cycles)
    │  ├─ Playwright Runner → Functional Tests
    │  ├─ QA Agent → Find Issues
    │  ├─ Debugger Agent → Fix Issues
    │  └─ Retest → Until all pass or max cycles
    └─ Evaluation Phase
       ├─ Playwright → Screenshots
       ├─ Scorer → Rate app (speed, mobile, intuitiveness, functionality)
       └─ Synopsis Agent → Human-friendly summary
    ↓
Output
    ├─ Generated project (ZIP)
    ├─ Screenshots
    ├─ Scores (0-10)
    ├─ Recommendations
    └─ Reports (PDF)
```

### Optional Modes

**Audit Mode:**
```
Upload Code/URL
    ↓
SDK Detection (scan for analytics libs)
    ↓
Playwright Crawl (simulate user sessions with Faker)
    ↓
Funnel Analysis (drop-off percentages)
    ↓
Recommendations (prioritized fixes + code snippets)
    ↓
Reports (charts + PDF export)
```

**A/B Test Mode:**
```
Generated Project
    ↓
AB Test Generator (create 2-3 variants)
    ├─ Variant A: Bold colors, urgent copy
    ├─ Variant B: Professional colors, trust-building copy
    └─ Control: Original design
    ↓
Git Branches (separate branch per variant)
    ↓
Tracking Events (PostHog/Optimizely integration)
    ↓
Experiment Config (traffic split, metrics)
```

**Meta Self-Improvement Loop:**
```
Platform Code
    ↓
Evaluate UI/UX/Code
    ↓
Identify Improvements (3-5 suggestions)
    ↓
Debate (Challenger agent pokes holes)
    ↓
Test on Diffs
    ↓
Apply Changes (with human approval)
    ↓
Commit & Log
    ↓
Repeat (forever mode: runs until 9/10 score)
```

## 📊 Key Integrations

### LangChain/LangGraph (Workflow Orchestration)
- Stateful graph for cyclic workflows
- Reflection chains (Devin-inspired)
- Memory persistence across phases

### Hugging Face
- Transformers for model fallbacks (e.g., Falcon for reasoning)
- Hub for sharing generated apps (optional)

### CrewAI
- Dynamic agent teams for tasks like audits
- Sub-groups for parallel execution

### DSPy (Optional)
- Prompt optimization for vague inputs
- Improves context extraction quality

### Analytics SDKs (Detection & Suggestion)
- PostHog: Heatmaps, session replays
- AppsFlyer: Mobile attribution
- OneSignal: Push notifications
- Segment: Event tracking
- Amplitude/Mixpanel: Product analytics

## 🔒 Key Principles (Never Violated)

1. **Build on Top**: All new features extend existing codebase
   - Reuse `agents.config.json` (52 agents, teams, roles)
   - Reuse `workflow_yaml_parser.py`, `code_generators.py`, `code_applicator.py`
   - Reuse Git integration, verifier, multi-model fallback

2. **User-Friendly First**:
   - Single input box + "Go" button
   - Hide complexity in expandable sections
   - Soft, welcoming copy (e.g., "Tell me your big idea, no tech talk needed")
   - Progress bars + live terminal for transparency
   - Emoji smile on exit: "Dream caught. Ready when you are. 😊"

3. **Zero Hallucinations**:
   - System prompts: "Only real libs. Flag unsure."
   - Verifier agent after each phase
   - `<verification>` tags in outputs

4. **Local Only**:
   - No databases
   - No hosted services
   - Everything runs on user's machine

5. **Production-Ready**:
   - Robust test-fix loops (Playwright + pytest)
   - Real SDKs (PostHog, AppsFlyer, OneSignal)
   - Professional reports (PDF with charts)
   - Git integration for version control

6. **Fast**:
   - Haiku primary (speed + cost)
   - Fallback to Sonnet/Opus if needed
   - Caching (LangChain)

## 🧪 Testing

### Test Meta Prompt
```bash
cd ai-agents-repo
python core/meta_prompt.py
```

### Test Audit Mode
```bash
python core/audit_mode.py
```

### Test A/B Generator
```bash
python core/ab_test_generator.py
```

### Test Report Generator
```bash
python core/report_generator.py
```

### Full Integration Test
```bash
streamlit run app.py
# Enter: "An EV charger sharing platform with 73% drop-off at profile creation"
# Check "Analyze User Behavior & Drop-Offs"
# Click "GO"
```

## 📈 Metrics & Scoring

The scorer agent evaluates apps on 4 dimensions (0-10 scale):

1. **Speed**: Load time, perceived performance
2. **Mobile-Friendly**: Responsive design, touch targets
3. **Intuitiveness**: Clear navigation, minimal friction
4. **Functionality**: Features work, edge cases handled

Thresholds:
- 8-10: ⭐⭐⭐ Excellent
- 6-7: ⭐⭐ Good
- 4-5: ⭐ Fair
- 0-3: ❌ Needs Work

## 🔄 Meta Self-Improvement

To improve the platform itself:

1. **Manual Mode:**
   - Click "Self-Improve" in UI
   - Review suggestions
   - Click "Apply" to commit changes

2. **Forever Mode** (runs for hours):
   ```python
   from core.meta_self_improver import MetaSelfImprover

   improver = MetaSelfImprover(repo_path="/path/to/AI-agents")
   improver.run_forever(
       target_score=9.0,
       max_hours=4,
       human_approve=False  # Auto-apply in forever mode
   )
   ```

## 🎨 Customization

### Tweak Generated Apps
After generation, UI shows sliders:
- Primary Color (hex picker)
- Font Size (8-24px)
- Spacing/Padding (0-32px)

Changes regenerate app live.

### Add Custom Agents
Edit `agents.config.json`:
```json
{
  "id": "CustomAgent",
  "role": "Custom Specialist",
  "goal": "Do custom things",
  "backstory": "Expert in custom domain with 10+ years...",
  "defaultPrompt": "Perform custom task: {task}",
  "priority": 5,
  "category": "Custom"
}
```

### Add Custom Workflows
Create YAML in `workflows/`:
```yaml
name: Custom Workflow
description: Custom agent sequence
steps:
  - agent: PM
    task: Plan the project
  - agent: CustomAgent
    task: Do custom analysis
  - agent: Verifier
    task: Verify outputs
```

## 🐛 Troubleshooting

### "ANTHROPIC_API_KEY not set"
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
# Or add to .env file
```

### "Package not installed"
```bash
pip install -r requirements.txt
playwright install
```

### "Playwright tests failing"
- Ensure app is running locally
- Check port (default: 3000)
- Verify no firewall blocking

### "Charts not generating"
```bash
pip install matplotlib seaborn reportlab
```

### "Git operations failing"
- Ensure Git is installed
- Check repo has `.git` folder
- Verify write permissions

## 📝 Example Scenarios

### Scenario 1: Non-Technical Founder
**User:** "I want to build a dog walking app where pet owners book walks and walkers get notified."

**System:**
1. Meta prompt extracts: industry=on-demand services, personas=[pet owners, walkers]
2. Asks clarification: "Is this local-only or national coverage?"
3. User responds: "Start local, one city"
4. Agents adapted with on-demand marketplace expertise
5. Builds app with:
   - Dual-sided marketplace (owners + walkers)
   - Booking system
   - Real-time notifications (OneSignal)
   - Ratings/reviews
   - Local geofencing
6. Outputs:
   - Web app (Next.js)
   - iOS app (Swift/SwiftUI)
   - Android app (Kotlin/Compose)
   - Executive summary PDF
   - Dev handover PDF

### Scenario 2: Startup Analyzing Drop-Offs
**User:** "We have an EV charger app but 70% drop off at signup. Help!"

**System:**
1. User checks "Analyze User Behavior & Drop-Offs"
2. Uploads code ZIP
3. Audit mode:
   - Detects: No analytics SDK (recommends PostHog)
   - Crawls app with 20 dummy users
   - Finds: 73% drop-off at "Create Profile" form
   - Reasons: 12 required fields, no progress indicator
4. Recommendations:
   - Reduce to 3 fields (email, password, name)
   - Add progress bar ("Step 2 of 3")
   - Defer address/payment to later
   - Add social login (Google, Apple)
5. Generates diffs with fixes
6. Creates A/B test variants:
   - Control: Original 12-field form
   - Variant A: 3-field form + progress bar
   - Variant B: Social login prominent
7. Outputs:
   - 3 Git branches
   - PostHog experiment config
   - PDF report with funnel chart

### Scenario 3: Meta Self-Improvement
**User:** Clicks "Self-Improve" button

**System:**
1. Analyzes own codebase (`ai-agents-repo/`)
2. Identifies improvements:
   - Bigger "GO" button (current: 18px → suggest: 24px)
   - Add keyboard shortcut (Cmd+Enter)
   - Improve error messages (technical → friendly)
3. Challenger agent critiques
4. Generates diffs
5. Tests changes on UI
6. Shows preview: "Apply these changes?"
7. User clicks "Apply"
8. Commits to Git with message: "UI/UX improvements from self-evaluation"
9. Logs to `improvements.log`

## 🚢 Deployment (Future)

While current setup is local-only, here's how to deploy generated apps:

### Web Apps
```bash
# Vercel
cd generated-project
vercel deploy

# Netlify
netlify deploy --prod

# AWS Amplify
amplify publish
```

### Mobile Apps
```bash
# iOS (requires Mac + Xcode)
cd ios-app
fastlane beta

# Android
cd android-app
fastlane deploy
```

### Share on Hugging Face Hub (Optional)
```python
from huggingface_hub import HfApi

api = HfApi()
api.upload_folder(
    folder_path="generated-project",
    repo_id="username/my-app",
    repo_type="space"
)
```

## 🤝 Contributing

This implementation builds on the existing multi-agent platform. To extend:

1. Add new agents to `agents.config.json`
2. Create new modules in `core/` for specialized features
3. Update `streamlit_ui/` for new UI components
4. Add tests in test files
5. Update this guide

## 📚 References

- **Devin**: Autonomous engineering with reflection loops
- **Replit Agent**: Long-running self-correction
- **Virtuoso/NxCode**: Test-fix loops in containers
- **Emergent**: In-app agents for iteration
- **LangChain v1.0+**: Stateful graphs, reflection chains
- **CrewAI**: Dynamic agent teams
- **DSPy**: Prompt optimization

## 📄 License

Same as base repository (check root LICENSE file).

---

**Generated by Code Weaver Pro**
*Transforming ideas into production-ready apps with the magic of AI* ✨

