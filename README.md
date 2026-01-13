# Code Weaver Pro 🪡

> **Magical, user-friendly AI agent system that transforms ideas into production-ready apps**

Build complete applications in minutes with zero technical knowledge. Inspired by Devin, Replit Agent, and the latest 2026 AI frameworks.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![Anthropic Claude](https://img.shields.io/badge/Claude-AI-orange)](https://www.anthropic.com)

---

## ✨ What Makes This Special

### For Non-Technical Users
- **One input box + "Go" button** - Describe your idea in plain English
- **No tech jargon** - Tell us about your dog walking app, not your REST APIs
- **Watch the magic happen** - Live progress bars and terminal output
- **Download ready-to-use apps** - Get your app in 2-5 minutes

### For Technical Users
- **52 specialized AI agents** - From PM to iOS/Android/Web engineers
- **Dynamic agent adaptation** - Agents become experts in YOUR domain automatically
- **Drop-off analysis** - Find exactly where users quit and why
- **A/B test generation** - Get 3 variants with separate Git branches
- **Professional reports** - Executive summaries and dev handovers as PDFs
- **Meta self-improvement** - The platform improves its own code autonomously

---

## 🚀 Quick Start (2 Minutes)

### 1. Install

```bash
git clone https://github.com/player20/AI-agents
cd AI-agents
pip install -r requirements.txt
playwright install
```

### 2. Configure

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your Anthropic API key
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### 3. Launch

```bash
streamlit run app.py
```

Open **http://localhost:8501** and start creating! 🎉

---

## 🎯 Key Features

### 🧠 **Smart Agent Adaptation**
Agents automatically become experts in your domain:
- Input: "EV charger sharing app with trust issues"
- Agents adapt: Become experts in green tech, sharing economy, user onboarding

### 📉 **Drop-Off Analysis (Audit Mode)**
- Upload your app (ZIP or code)
- Or provide live URL (localhost or deployed)
- Get exact drop-off points: "73% quit at profile creation - here's why and how to fix it"
- Automatic SDK detection (PostHog, AppsFlyer, OneSignal, etc.)

### 🧪 **A/B Test Generator**
- Creates 3 variants automatically (Control, Bold, Professional)
- Separate Git branches for each variant
- Pre-configured tracking events
- Experiment configuration for PostHog/Optimizely

### 📊 **Professional Reports**
- **Executive Summary**: For investors/CEOs (charts, screenshots, recommendations)
- **Dev Handover**: For engineers (code diffs, setup steps, Git commits)
- One-click PDF export

### 🔄 **Meta Self-Improvement**
- The platform analyzes and improves its own code
- "Forever mode" runs for hours until 9/10 quality
- Autonomous UI/UX enhancements

### 🎨 **Magical User Experience**
- Dark gradient theme with soft glows
- Large, inviting input (no intimidation)
- Real-time terminal output
- Intuitive progress tracking (4 phases)
- Soft, welcoming copy throughout
- Exit message: "Dream caught. Ready when you are. 😊"

---

## 📚 How It Works

### The Agent Team (52 Specialists)

**Management & Strategy:**
- Project Manager, Memory Specialist, Challenger

**Research & Analysis:**
- Market Research, Ideas Specialist, Verifier

**Design & UX:**
- UI/UX Designer, Design Reviewer

**Engineering:**
- Senior Engineer, iOS Engineer, Android Engineer, Web Engineer
- Backend Engineer, Frontend Engineer, DevOps Engineer
- Security Engineer, Cloud Architect

**Quality & Testing:**
- QA Engineer, Performance Engineer, Accessibility Specialist

**Plus 30+ more** covering data science, ML, documentation, product management, and more!

### The Magic Workflow

1. **You describe** - "A meal planning app for people with dietary restrictions"
2. **Meta-prompt extracts context** - Industry: Food tech, Users: Health-conscious consumers
3. **Agents adapt** - Become experts in nutrition, health tech, meal planning
4. **Clarification (if needed)** - "Tell me more about dietary restrictions you want to support?"
5. **Planning** - PM creates sprint plan, Researchers validate market
6. **Design** - UI/UX Designer creates flows, Senior reviews architecture
7. **Build** - Platform engineers generate code (React, Swift, Kotlin, etc.)
8. **Test** - Automated Playwright tests, fix issues, retest (up to 10 cycles)
9. **Evaluate** - Screenshots, scores (speed, mobile, intuitiveness, functionality)
10. **Deliver** - Download ZIP, export reports, generate A/B variants

---

## 💡 Example Use Cases

### 1. Non-Technical Founder
**Input:**
```
"A dog walking app where pet owners book walks and walkers get notified in real-time"
```

**Result:**
- Full-stack app (React + Node.js + PostgreSQL)
- iOS app (Swift/SwiftUI)
- Android app (Kotlin/Jetpack Compose)
- Real-time notifications (OneSignal)
- Ready to deploy in 5 minutes

### 2. Startup Analyzing Drop-Offs
**Input:**
```
"We have an EV charger sharing platform but 70% of users quit at profile creation. Help!"
```

**Options:** Check "Analyze user drop-offs" + upload code

**Result:**
- Funnel analysis: "73% drop at Step 3 (profile form)"
- Root cause: "12 required fields, no progress indicator"
- Fixes with code:
  - Reduce to 3 fields (email, password, name)
  - Add progress bar ("Step 2 of 3")
  - Defer payment info to later
  - Add social login (Google, Apple)
- PDF report with recommendations

### 3. Investor Pitch
**Input:**
```
"Food delivery marketplace connecting local restaurants with customers"
```

**Options:** Check "Quick market check first" + "Research only"

**Result:**
- TAM/SAM/SOM analysis
- 15 competitors listed
- GO/NO-GO decision with reasoning
- Executive Summary PDF ready for investors

---

## 🛠️ Advanced Features

### Dynamic Adaptation
Keep `agents.config.json` generic. The system:
1. Extracts context from your input
2. Injects domain expertise into agent prompts
3. Asks for clarification if unclear

### Auto-Auth for Testing
When analyzing apps with authentication:
- Provide test credentials (masked input)
- Playwright auto-logs in (in-memory, not stored)
- Simulates real user flows

### SDK Detection
Automatically detects and suggests:
- PostHog (heatmaps, session replays)
- AppsFlyer (mobile attribution)
- OneSignal (push notifications)
- Segment (event tracking)
- And 10+ more

### Test-Fix-Retest Loops
Inspired by Virtuoso/NxCode:
- Playwright functional tests
- Feed errors to debugger agent
- Auto-fix issues
- Retest (max 10 cycles)
- Log all iterations

### LangGraph Integration
- Stateful workflow graphs
- Cyclic reflection loops (Devin-inspired)
- CrewAI for dynamic agent teams
- DSPy for prompt optimization

---

## 📖 Documentation

- **[LAUNCH_GUIDE_ENHANCED.md](LAUNCH_GUIDE_ENHANCED.md)** - Complete user guide with examples
- **[CODE_WEAVER_PRO_GUIDE.md](CODE_WEAVER_PRO_GUIDE.md)** - Full 70+ page technical guide
- **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)** - Integration details
- **[QUICK_START_NEW_FEATURES.md](QUICK_START_NEW_FEATURES.md)** - Feature reference

### Module Documentation
- `core/meta_prompt.py` - Dynamic agent adaptation
- `core/audit_mode.py` - Drop-off analysis with Playwright
- `core/ab_test_generator.py` - A/B test variant creation
- `core/report_generator.py` - Professional PDF reports

---

## 🔧 Configuration

### Model Selection
- **Haiku** (default): Fast, cheap, good quality
- **Sonnet**: Better reasoning, more detailed
- **Opus**: Highest quality, slower

### Platforms
Select from: Website, Web App, iOS, Android
- Agents decide exact tech stack automatically
- Swift for iOS, Kotlin for Android, React for Web

### Advanced Options
- Custom workflow YAML
- Agent team selection
- Model preferences
- Test credentials

---

## 🧪 Testing

### Test Individual Modules
```bash
python core/meta_prompt.py          # Context extraction
python core/audit_mode.py           # Drop-off analysis
python core/ab_test_generator.py   # A/B variants
python core/report_generator.py    # PDF reports
```

### Test Complete UI
```bash
python test_enhanced_ui.py
```

### Test with Real Example
```bash
streamlit run app.py
# Input: "Build an EV charger sharing platform"
# Check: "Analyze user drop-offs"
# Watch the magic!
```

---

## 🌟 Inspirations

Code Weaver Pro draws inspiration from cutting-edge 2026 AI frameworks:

- **Devin** - Autonomous engineering with reflection loops
- **Replit Agent** - Long-running self-correction
- **Virtuoso/NxCode** - Test-fix loops in containers
- **Emergent** - In-app agents for iteration
- **LangGraph v1.0+** - Stateful graphs and reflection chains
- **CrewAI** - Dynamic agent teams
- **DSPy** - Prompt optimization

---

## 🎓 Tips for Best Results

### Writing Good Prompts

**Basic:**
```
"A recipe app"
```

**Better:**
```
"A recipe app where users save favorites and share with friends"
```

**Best:**
```
"A meal planning platform for people with dietary restrictions (vegan, gluten-free, keto).
Users input restrictions, get weekly meal plans with grocery lists, and track nutrition goals.
Key pain point: Hard to find recipes that match multiple restrictions at once."
```

### When to Use Each Feature

| Feature | Use When |
|---------|----------|
| Market Research | Validating new ideas before building |
| Upload Code | Improving existing apps |
| Audit Mode | Diagnosing user drop-offs |
| Research Only | Pitching to investors (no build) |
| A/B Tests | Optimizing conversion rates |
| Reports | Sharing with team/investors |

---

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

Areas we're looking for help:
- More agent specializations
- Additional SDK integrations
- Improved test coverage
- Documentation improvements
- Bug fixes and optimizations

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

Built with:
- [Anthropic Claude](https://www.anthropic.com) - AI engine
- [Streamlit](https://streamlit.io) - Beautiful UI framework
- [Playwright](https://playwright.dev) - Testing and automation
- [LangChain/LangGraph](https://www.langchain.com) - Workflow orchestration
- [CrewAI](https://www.crewai.io) - Agent teams
- And many other amazing open-source projects

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/player20/AI-agents/issues)
- **Discussions**: [GitHub Discussions](https://github.com/player20/AI-agents/discussions)
- **Documentation**: See `docs/` folder

---

<div align="center">

**Made with ❤️ by the AI community**

*Transforming ideas into reality, one prompt at a time* ✨

[⭐ Star us on GitHub](https://github.com/player20/AI-agents) | [🐛 Report Bug](https://github.com/player20/AI-agents/issues) | [💡 Request Feature](https://github.com/player20/AI-agents/issues)

</div>
