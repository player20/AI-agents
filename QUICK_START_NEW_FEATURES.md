# Quick Start: Code Weaver Pro New Features

## 🚀 Install & Run (5 minutes)

```bash
# 1. Install dependencies
pip install -r requirements.txt
playwright install

# 2. Set API key
export ANTHROPIC_API_KEY="your-key-here"

# 3. Run Code Weaver Pro
streamlit run app.py
```

## ✨ What's New?

### 1. **Smart Agent Adaptation** 🧠
Agents automatically become experts in YOUR domain.

**Example:**
- Input: "EV charger sharing app with drop-offs"
- Agents become specialists in: green tech, sharing economy, trust-building, onboarding

**Try it:**
```bash
python core/meta_prompt.py
```

### 2. **Drop-Off Analysis** 📉
Find where users abandon your app + get fixes.

**Features:**
- Scans code for analytics (PostHog, AppsFlyer, etc.)
- Simulates 10+ users with fake data
- Shows funnel: Landing (100%) → Signup (85%) → Form (45%) → Done (27%)
- Gives fixes: "73% drop at form → reduce fields, add progress bar"

**Try it:**
```bash
python core/audit_mode.py
```

**Real usage:**
```python
from core.audit_mode import AuditModeAnalyzer

analyzer = AuditModeAnalyzer(agents, model)

# Detect SDKs in your code
detected = analyzer.detect_sdks(code_files)

# Crawl your app
sessions = await analyzer.crawl_app_flows("http://localhost:3000", simulate_users=10)

# Get recommendations
funnel = analyzer.analyze_sessions(sessions)
recommendations = analyzer.generate_recommendations(funnel, detected, code_files)
```

### 3. **A/B Test Generator** 🧪
Create 3 variants to test what converts better.

**Variants:**
- Control: Your original design
- Variant A: Bold colors, urgent copy ("Get Started NOW!")
- Variant B: Professional colors, trust copy ("See How It Works")

**Outputs:**
- 3 Git branches (ready to deploy)
- PostHog tracking events
- Experiment config (traffic split, metrics)

**Try it:**
```bash
python core/ab_test_generator.py
```

**Real usage:**
```python
from core.ab_test_generator import ABTestGenerator

generator = ABTestGenerator("/path/to/project")

# Generate variants
variants = generator.generate_variants(variant_count=3)

# Create Git branches
branches = generator.create_variant_branches(variants)

# Get experiment config for PostHog
config = generator.generate_experiment_config(variants)
```

### 4. **Professional Reports** 📊
Export beautiful PDFs for stakeholders.

**Two types:**
- **Executive Summary**: For investors/CEOs (charts, screenshots, recommendations)
- **Dev Handover**: For engineers (code diffs, setup, Git commits)

**Try it:**
```bash
python core/report_generator.py
```

**Real usage:**
```python
from core.report_generator import ReportGenerator

generator = ReportGenerator()

# Executive Summary
generator.generate_executive_summary(
    project_data={
        'project_name': 'My App',
        'scores': {'speed': 8, 'mobile': 9, 'intuitiveness': 7, 'functionality': 8},
        'funnel_analysis': {...},  # from audit mode
        'screenshots': ['screen1.png', 'screen2.png'],
        'recommendations': [...]
    },
    output_path='executive_summary.pdf'
)

# Dev Handover
generator.generate_dev_handover(
    project_data={
        'tech_stack': {'frontend': ['React'], 'backend': ['Node.js']},
        'setup_instructions': ['npm install', 'npm run dev'],
        'code_diffs': [...],
        'test_results': [...]
    },
    output_path='dev_handover.pdf'
)
```

## 📱 Real-World Examples

### Example 1: Non-Technical Founder

**Scenario:** You have a business idea but zero coding skills.

**Steps:**
1. Open Code Weaver Pro: `streamlit run app.py`
2. Type: "A dog walking app where pet owners book walks"
3. System asks: "Is this local or national?"
4. You reply: "Start local, one city"
5. Click "GO"
6. **Result:** Complete app (Web + iOS + Android) in 5 minutes

### Example 2: Startup With Drop-Offs

**Scenario:** Your app has 70% drop-off at signup. Why?

**Steps:**
1. Open Code Weaver Pro
2. Check "Analyze Drop-offs" checkbox
3. Upload your app's ZIP
4. Enter app URL (optional): `http://localhost:3000`
5. Click "GO"
6. **Result:**
   - "73% drop at profile form"
   - "12 fields → reduce to 3"
   - Code snippets to fix
   - A/B test variants ready to deploy

### Example 3: Investor Pitch

**Scenario:** Need market research + beautiful deck.

**Steps:**
1. Type: "EV charger sharing platform"
2. Check "Market research"
3. Click "GO"
4. **Result:**
   - TAM: $50B, SAM: $2B, SOM: $100M
   - 15 competitors listed
   - GO/NO-GO decision
   - Download professional PDF report

## 🎯 Quick Commands

```bash
# Test all new features
python core/meta_prompt.py          # Context extraction
python core/audit_mode.py           # Drop-off analysis
python core/ab_test_generator.py   # A/B variants
python core/report_generator.py    # PDF export

# Run main app
streamlit run app.py

# Install missing deps
pip install -r requirements.txt
playwright install

# Set API key (required)
export ANTHROPIC_API_KEY="sk-ant-..."
```

## 📊 What Each Module Does (1 sentence)

| Module | Purpose |
|--------|---------|
| `meta_prompt.py` | Makes agents smart about YOUR domain (e.g., EV charging, healthcare) |
| `audit_mode.py` | Finds where users quit your app + gives fixes |
| `ab_test_generator.py` | Creates 3 versions to test (colors, copy, CTAs) |
| `report_generator.py` | Exports beautiful PDFs (investor deck + dev docs) |

## 🔗 Integration with Existing Code

All new features work with your existing setup:
- ✅ Uses existing `agents.config.json` (52 agents)
- ✅ Works with existing `orchestrator.py`
- ✅ Extends existing `streamlit_ui/`
- ✅ Compatible with existing workflows

**No breaking changes!** Old functionality still works.

## 🐛 Quick Troubleshooting

**Error: "ANTHROPIC_API_KEY not set"**
```bash
export ANTHROPIC_API_KEY="your-key-here"
```

**Error: "Module not found"**
```bash
pip install -r requirements.txt
```

**Error: "Playwright not installed"**
```bash
playwright install
```

**Error: "Permission denied"**
```bash
chmod +x ./ai-agents-repo
```

## 📚 Full Documentation

- **Comprehensive Guide:** [CODE_WEAVER_PRO_GUIDE.md](CODE_WEAVER_PRO_GUIDE.md) (70+ pages, all examples)
- **Implementation Details:** [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) (integration steps)
- **Existing Docs:** [README.md](README.md), [QUICK_START.md](QUICK_START.md)

## 💡 Pro Tips

1. **Vague Input?** System will ask clarifying questions automatically
2. **Want A/B Tests?** Generate app first, then click "Generate Variants" button
3. **Need Reports?** Click "Export PDF" after generation (Executive or Dev)
4. **Analyzing Drop-Offs?** Upload ZIP + provide URL for best results
5. **API Costs?** Haiku is primary (cheap + fast), auto-fallback to Sonnet if needed

## 🎉 You're Ready!

```bash
streamlit run app.py
# Enter: "Build me a [your idea]"
# Watch the magic happen ✨
```

---

**Questions?** Check [CODE_WEAVER_PRO_GUIDE.md](CODE_WEAVER_PRO_GUIDE.md) for everything.

**Built with ❤️ using Claude Code**
