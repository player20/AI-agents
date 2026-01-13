# Code Weaver Pro - Quick Start Guide

**The fastest way to go from idea to production-ready app**

---

## 📦 Installation (2 Minutes)

### Step 1: Prerequisites

- **Python 3.10+** (check with `python --version`)
- **4GB+ RAM** recommended
- **Internet connection** for API calls

### Step 2: Clone and Install

```bash
# Clone the repository
git clone https://github.com/player20/AI-agents
cd AI-agents

# (Recommended) Create virtual environment for clean setup
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies (use --no-cache-dir for faster install)
pip install -r requirements.txt --no-cache-dir

# Install Playwright browsers for testing
playwright install
```

**Troubleshooting:**

- If `playwright install` is slow, use: `playwright install chromium` (install only Chromium)
- If `torch` is slow, use CPU version: `pip install torch --index-url https://download.pytorch.org/whl/cpu`
- If you get dependency conflicts, try installing in a fresh virtual environment

### Step 3: Configure API Key

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your Anthropic API key
nano .env  # or use any text editor
```

**Get your API key:**
1. Visit [https://console.anthropic.com/](https://console.anthropic.com/)
2. Sign in or create an account
3. Navigate to "API Keys"
4. Click "Create Key"
5. Copy the key (starts with `sk-ant-`)
6. Paste into `.env` file:
   ```
   ANTHROPIC_API_KEY=sk-ant-your-actual-key-here
   ```

**Optional keys** (for enhanced features):
- `HUGGINGFACE_API_TOKEN`: For model fallbacks (optional)
- `POSTHOG_API_KEY`: For analytics SDK suggestions (optional)

All other keys have graceful fallbacks if missing!

### Step 4: Launch!

```bash
streamlit run app.py
```

Open your browser to **http://localhost:8501**

You should see:
- ✅ "You can now view your Streamlit app in your browser" in terminal
- ✅ Code Weaver Pro interface with dark gradient theme
- ✅ Framework status showing CrewAI ✅, LangGraph ✅, DSPy ✅

If you see warnings about missing frameworks (LangGraph/DSPy), that's okay—they're optional with automatic fallbacks.

---

## 🚀 Your First App (3 Minutes)

### Basic Usage: Create a New App

1. **Describe your idea** (in plain English):
   ```
   A meal planning app where users input dietary restrictions (vegan, gluten-free)
   and get weekly meal plans with grocery lists.
   ```

2. **Select platforms** (default: Web App):
   - ☑️ Web App
   - ☐ iOS
   - ☐ Android
   - ☐ Website

3. **Click GO** 🚀

4. **Watch the magic**:
   - Progress bars show 4 phases (Planning → Drafting → Testing → Evaluation)
   - Terminal shows live updates with color coding
   - Takes 2-5 minutes depending on complexity

5. **Get your app**:
   - See quality scores (Speed, Mobile, Intuitiveness, Functionality)
   - View screenshots of your running app
   - Download ZIP with all code
   - Export PDF reports (Executive Summary or Dev Handover)

---

## 🎛️ Using the Checkboxes (Advanced Features)

### 📊 Quick Market Check First

**When to use:** Before building, validate if your idea makes sense.

**How to use:**
1. ☑️ Check "Quick market check first"
2. Optionally: ☑️ Check "Research only (don't build yet)" to stop after research
3. Click GO

**What you get:**
- Market size analysis (TAM/SAM/SOM)
- 10-15 competitor analysis
- **GO/NO-GO decision** with reasoning
- Key features needed to compete
- Export as Executive Summary PDF for investors

**Example:**
```
Input: "EV charger sharing platform"
✅ Quick market check first
✅ Research only

Result:
- TAM: $12.5B (global EV charging market)
- 15 competitors identified (ChargePoint, EVgo, etc.)
- GO decision: ✅ YES - Niche opportunity in peer-to-peer sharing
- Recommendations: Focus on trust/verification, dynamic pricing
```

---

### 📦 I Have Code to Upgrade

**When to use:** You have an existing app and want improvements.

**How to use:**
1. ☑️ Check "I have code to upgrade"
2. Choose upload method:
   - **Paste code snippet**: For small code snippets
   - **Upload ZIP file**: For complete projects
   - **Provide live URL**: For deployed apps
3. Click GO

**What you get:**
- Code analysis and improvement suggestions
- Refactored code with modern best practices
- Architecture recommendations
- Performance optimizations
- Security fixes
- Side-by-side diffs

**Example:**
```
Input: "Upgrade my React app to use TypeScript and modern hooks"
✅ I have code to upgrade
Upload: my-react-app.zip

Result:
- Converted 25 components to TypeScript
- Replaced class components with functional + hooks
- Added proper types for all props
- Improved performance with useMemo/useCallback
- Download upgraded version
```

---

### 📉 Analyze User Drop-Offs (Audit Mode)

**When to use:** Users are dropping off and you don't know why.

**How to use:**
1. ☑️ Check "Analyze user drop-offs"
2. Provide your app:
   - **Upload ZIP**: For local analysis
   - **Live URL**: `http://localhost:3000` or `https://myapp.com`
3. **(Optional)** Provide test credentials for auto-auth:
   - Expand "🔐 Test Credentials" section
   - Enter test email and password
   - Used in-memory only, never stored
4. Click GO

**What you get:**
- **Funnel analysis**: Exact drop-off percentages at each step
- **SDK detection**: Find which analytics you're already using (PostHog, AppsFlyer, Segment, etc.)
- **Session simulations**: 10 simulated user flows with Playwright
- **Root cause analysis**: Why users are dropping off
- **Code fixes**: Actual code snippets to fix issues
- **Recommendations**: Prioritized action items (🔴 Critical, 🟠 Important, 🔵 Nice-to-have)
- **Funnel chart**: Visual funnel with drop-off rates

**Example:**
```
Input: "My dog walking app has 70% drop-off at signup"
✅ Analyze user drop-offs
URL: http://localhost:3000
Test creds: test@example.com / password123

Result:
📊 Funnel Analysis:
  - Landing → Signup: 92% (8% drop)
  - Signup → Profile: 27% (73% DROP 🔴)
  - Profile → Dashboard: 95% (5% drop)

🔴 CRITICAL: Profile creation has 12 required fields!

Fixes:
  1. Reduce to 3 fields (email, password, name)
  2. Add progress indicator ("Step 2 of 3")
  3. Defer payment info to post-signup
  4. Add social login (Google, Apple)

SDKs Detected: None
Recommendation: Add PostHog for session replays (code snippet provided)
```

---

### 🔍 Research Only Mode

**When to use:** Validate idea before building (investors, pitch decks).

**How to use:**
1. ☑️ Check "Quick market check first"
2. ☑️ Check "Research only (don't build yet)"
3. Click GO

**What you get:**
- Market research without building anything
- GO/NO-GO decision
- Competitor analysis
- Export as Executive Summary PDF

**Use case:** Pitch to investors, validate idea with minimal time/cost.

---

## 🎯 Platform Selection

**Options:**
- **Website**: Static site (HTML/CSS/JS) - marketing pages, landing pages
- **Web App**: Full-stack (React/Vue + Node.js/Python) - complex apps with backend
- **iOS**: Native iOS app (Swift/SwiftUI)
- **Android**: Native Android app (Kotlin/Jetpack Compose)

**Select multiple platforms** to generate apps for all at once!

**Agents decide the tech stack automatically:**
- Web App → React + TypeScript + Node.js + PostgreSQL (or similar)
- iOS → Swift + SwiftUI
- Android → Kotlin + Jetpack Compose
- Challenger agent will suggest alternatives if better fit

**Example:**
```
Platforms: ☑️ Web App, ☑️ iOS

Result:
- Web App: React + TypeScript + Express + MongoDB
- iOS: SwiftUI app with CoreData
- Shared API design
- Consistent UX across platforms
```

---

## ⚙️ Advanced Options

Expand "Advanced Options" for:
- **Custom workflow YAML**: Define your own agent workflow
- **Model selection**:
  - **Haiku** (Fast, Recommended) - Default for zero-lag
  - **Sonnet** (Balanced) - Better reasoning
  - **Opus** (Highest Quality) - Best results, slower

---

## 🔄 Self-Improvement Mode

**What it does:** Code Weaver Pro analyzes and improves itself autonomously.

**How to use:**
1. Click "🔄 Self-Improve" button at top
2. Choose what to improve (UI/UX, Code Quality, Documentation)
3. Set run duration (Forever Mode runs for hours until 9/10 quality)
4. Click "Start Self-Improvement"

**What you get:**
- Platform improves its own code, UI, and documentation
- Iterative refinement with quality checks
- Can run for hours in "Forever Mode"
- See all changes with diffs before applying

---

## 💡 Pro Tips

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

**Include:**
- **Target users**: Who will use this?
- **Core features**: What's the main functionality?
- **Pain point**: What problem does it solve?
- **Differentiator**: What makes it unique?

### When to Use Each Feature

| Feature | Use When |
|---------|----------|
| **Quick market check** | Validating new ideas before building |
| **I have code to upgrade** | Improving existing apps |
| **Analyze user drop-offs** | Users are quitting and you don't know why |
| **Research only** | Pitching to investors (no build needed) |
| **Multiple platforms** | Want iOS + Android + Web simultaneously |

### Zero-Lag Optimization

Code Weaver Pro is optimized for speed:
- **Haiku model by default** (3x faster than Sonnet)
- **Caching**: Repeated operations are cached
- **Minimal loops**: Test-fix loop limited to 10 iterations
- **Local tests**: Playwright runs locally for fast feedback
- **Async operations**: Terminal updates in real-time

**Expected timing:**
- Market research only: 30 seconds
- Simple app (1 platform): 2-3 minutes
- Complex app (3 platforms): 4-5 minutes
- Audit mode analysis: 5-8 minutes (includes crawling)

---

## 🐛 Troubleshooting

### "ANTHROPIC_API_KEY not set"
- Make sure you created `.env` file (copy from `.env.example`)
- Ensure the key starts with `sk-ant-`
- Restart Streamlit after editing `.env`

### "Import Error: No module named 'X'"
- Run `pip install -r requirements.txt` again
- Check you're in the correct virtual environment

### "Playwright Error: Browser not found"
- Run `playwright install`
- Or: `playwright install --with-deps` for full installation

### UI is slow or unresponsive
- Check your internet connection (API calls need internet)
- Try Haiku model (faster than Sonnet/Opus)
- Reduce number of platforms if generating for 3+

### Audit mode fails to crawl localhost
- Make sure your local app is running before clicking GO
- Check the URL is correct (e.g., `http://localhost:3000`)
- Try providing test credentials if auth is required

### Warnings about missing frameworks (LangGraph/DSPy)
- These are **optional** - system works with graceful fallbacks
- Install them if you want enhanced features: `pip install langgraph dspy-ai`
- Or ignore—basic functionality is unaffected

---

## 📚 Next Steps

- **Read the full README**: [README.md](README.md) for comprehensive feature list
- **Check the backlog**: [BACKLOG.md](BACKLOG.md) for upcoming features
- **View completion status**: [100_PERCENT_COMPLETE.md](100_PERCENT_COMPLETE.md)
- **Explore technical details**: `docs/` folder for architecture docs

---

## 🙏 Need Help?

- **Issues**: [GitHub Issues](https://github.com/player20/AI-agents/issues)
- **Discussions**: [GitHub Discussions](https://github.com/player20/AI-agents/discussions)
- **Documentation**: See `docs/` folder

---

**Made with ❤️ by the Code Weaver Pro team**

*From idea to production-ready app in 2-5 minutes.* ✨
