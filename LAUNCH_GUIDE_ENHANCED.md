# Launch Guide: Code Weaver Pro Enhanced Edition

## 🚀 Quick Start (2 Minutes)

### 1. Install Dependencies

```bash
cd ai-agents-repo
pip install -r requirements.txt
playwright install
```

### 2. Set API Key

```bash
export ANTHROPIC_API_KEY="your-key-here"
```

### 3. Launch Enhanced UI

```bash
streamlit run app_enhanced.py
```

The app will open at `http://localhost:8501`

---

## ✨ What's New in Enhanced Edition

### 🎨 Magical User Interface
- **Dark gradient theme** with soft glows and rounded corners
- **Large, inviting text input** - no tech jargon needed
- **Intelligent progress tracking** - 4 phases with live updates
- **Real-time terminal output** - see exactly what's happening
- **Soft, welcoming copy** - "Tell me your big idea, no tech talk needed"

### 🧠 Smart Features

#### 1. **Dynamic Agent Adaptation**
- Automatically extracts context from your input
- Adapts agents to your industry (e.g., pet care, EV charging, healthcare)
- Requests clarification when needed

**Example:**
```
Input: "Dog walking app with drop-offs at signup"
→ Agents become experts in on-demand services, trust-building, onboarding
```

#### 2. **Drop-Off Analysis (Audit Mode)**
- Crawls your live app or code
- Simulates 10+ user sessions with realistic data
- Identifies exact drop-off points (e.g., "73% quit at profile form")
- Suggests fixes with code snippets

**Use Cases:**
- You have an app but users abandon it
- Want to know which screen/step is the problem
- Need analytics SDK recommendations (PostHog, AppsFlyer, etc.)

#### 3. **A/B Test Generator**
- Creates 2-3 variants automatically
- Different colors, copy, CTAs
- Separate Git branches ready to deploy
- Tracking events pre-configured

**Output:**
- Control (original)
- Variant A (bold, action-oriented)
- Variant B (professional, trust-building)

#### 4. **Professional Reports**
- **Executive Summary**: For investors/CEOs (charts, screenshots, recommendations)
- **Dev Handover**: For engineers (code diffs, setup steps, Git commits)
- One-click PDF export

---

## 📖 User Guide

### For Non-Technical Users

#### Scenario 1: "I have a business idea"

1. Open Code Weaver Pro
2. Type your idea in plain English:
   ```
   "A meal planning app where users input dietary restrictions
   and get weekly meal plans with grocery lists"
   ```
3. Select platforms (Web App, iOS, Android)
4. Click **GO**
5. Watch the magic happen (2-5 minutes)
6. Download your app as ZIP

**That's it!** No coding needed.

#### Scenario 2: "My app has issues - users quit halfway through"

1. Check **"Analyze user drop-offs"**
2. Either:
   - Upload your app's code (ZIP)
   - Or provide live URL (e.g., `http://localhost:3000`)
3. Optionally add test credentials (for auth bypass)
4. Click **GO**
5. Review funnel analysis:
   - See exactly where users quit (e.g., "73% drop at Step 3")
   - Get specific fixes with code snippets
   - Download recommendations as PDF

#### Scenario 3: "I need to pitch investors"

1. Type your idea
2. Check **"Quick market check first"**
3. Check **"Research only (don't build yet)"**
4. Click **GO**
5. Get instant:
   - TAM/SAM/SOM market size
   - Competitor list
   - GO/NO-GO decision with reasoning
6. Export as **Executive Summary PDF**

### For Technical Users

#### Advanced Options

Click **"Advanced Options"** expander for:
- Custom workflow YAML upload
- Model selection (Haiku/Sonnet/Opus)
- Agent team configuration

#### Integration with Existing Code

1. Check **"I have code to upgrade"**
2. Upload ZIP or paste code
3. System will:
   - Parse your codebase (AST analysis)
   - Detect frameworks (React, Swift, Python, etc.)
   - Suggest improvements
   - Generate diffs with before/after
   - Create Git branch `better-me`

#### Test Credentials for Auth

When analyzing drop-offs on apps with authentication:

1. Check **"Analyze user drop-offs"**
2. Provide URL
3. Expand **"Test Credentials"**
4. Enter test email/password
5. Playwright will auto-login and simulate real user flows

**Important:** Credentials are in-memory only, never stored.

---

## 🎯 Example Workflows

### Example 1: EV Charger Sharing Platform

**Input:**
```
"An EV charger sharing platform where hosts list chargers
and drivers book them. We're seeing 70% drop-off at profile creation."
```

**Options:**
- ✅ Analyze user drop-offs
- ✅ Quick market check first
- Platforms: Web App, iOS, Android

**What Happens:**
1. Meta-prompt extracts: "green tech, sharing economy, trust issues"
2. Agents adapt: Become experts in sharing platforms, onboarding, trust
3. Market research: TAM $50B, 12 competitors, GO decision
4. Drop-off analysis: Crawls app, finds 73% quit at "Create Profile"
   - Reason: 12 required fields, no progress indicator
5. Recommendations:
   - Reduce to 3 fields (email, password, name)
   - Add progress bar ("Step 2 of 3")
   - Defer payment/address to later
   - Add social login (Google, Apple)
6. A/B variants created with different approaches
7. PDF report with funnel chart and fixes

**Time:** 3-5 minutes

### Example 2: Simple Recipe App

**Input:**
```
"A recipe app where users save favorites and share with friends"
```

**Options:**
- Platforms: Web App, iOS

**What Happens:**
1. Builds full-stack app:
   - Frontend: React + TypeScript
   - Backend: Node.js + Express + PostgreSQL
   - Mobile: React Native (for iOS)
2. Features:
   - User authentication
   - Recipe search
   - Favorites collection
   - Social sharing
3. Tests automatically
4. Scores: Speed 8/10, Mobile 9/10, etc.
5. Ready to download

**Time:** 2-3 minutes

### Example 3: Platform Self-Improvement

**Mode:** Self-Improve (click top button)

**What Happens:**
1. Code Weaver Pro analyzes its own codebase
2. Identifies UI/UX improvements:
   - Bigger "GO" button
   - Better error messages
   - Keyboard shortcuts
3. Generates diffs
4. Shows preview
5. Asks: "Apply these changes?"
6. Commits to Git with log

**Use Case:** Keep the platform improving itself autonomously

---

## 🐛 Troubleshooting

### "ANTHROPIC_API_KEY not set"

```bash
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
# Or add to .env file
```

### "Module not found"

```bash
pip install -r requirements.txt
playwright install
```

### "Failed to crawl app"

**Problem:** App not running or wrong URL

**Solution:**
- For local apps: Start your app first (`npm run dev`, etc.)
- Check port (e.g., `http://localhost:3000` not `3001`)
- Verify no CORS issues

### "Clarification requested but I gave clear input"

**Why:** Meta-prompt scored clarity <6/10

**Options:**
1. Provide more details when asked
2. Or click **"Skip & Continue Anyway"**

### "A/B test generation failed"

**Common causes:**
- No Git repository initialized
- No write permissions
- Invalid project path

**Solution:**
```bash
cd your-project
git init
```

---

## 📊 Understanding Scores

After generation, you get 4 scores (0-10 scale):

| Score | Metric | What It Measures |
|-------|--------|------------------|
| **Speed** | Performance | Load time, responsiveness |
| **Mobile-Friendly** | Responsive Design | Touch targets, viewport, gestures |
| **Intuitiveness** | UX | Clear navigation, minimal friction |
| **Functionality** | Code Quality | Features work, edge cases handled |

**Rating:**
- 8-10: ⭐⭐⭐ Excellent (production-ready)
- 6-7: ⭐⭐ Good (minor polish needed)
- 4-5: ⭐ Fair (improvements recommended)
- 0-3: ❌ Needs Work (major issues)

---

## 🔧 Configuration

### Model Selection

**Haiku (Default - Recommended):**
- ✅ 2-5x faster
- ✅ 20x cheaper
- ✅ Good quality for most tasks
- Use for: Prototypes, MVPs, learning

**Sonnet (Balanced):**
- ✅ Better reasoning
- ✅ More detailed output
- Use for: Production apps, complex logic

**Opus (Highest Quality):**
- ✅ Best possible quality
- ⚠️ Slower, more expensive
- Use for: Mission-critical apps, final polish

### Platforms

**Website:** Static HTML/CSS/JS (fast, simple)
**Web App:** Full-stack with backend (React, Node.js)
**iOS:** Native Swift/SwiftUI app
**Android:** Native Kotlin/Jetpack Compose app

**Note:** Agents decide exact stack automatically based on requirements.

---

## 📁 Project Structure

After generation, your project will have:

```
my-awesome-app/
├── frontend/          # React/Next.js
│   ├── src/
│   ├── public/
│   └── package.json
├── backend/           # Node.js/Express (if full-stack)
│   ├── src/
│   ├── models/
│   └── package.json
├── mobile/            # React Native (if iOS/Android)
│   ├── ios/
│   ├── android/
│   └── package.json
├── .env.example       # Environment variables
├── README.md          # Setup instructions
└── docker-compose.yml # Optional: Docker setup
```

---

## 🎓 Tips & Best Practices

### Writing Good Prompts

**Good:**
```
"A dog walking app where owners book walks and get GPS tracking"
```

**Better:**
```
"A dog walking marketplace connecting pet owners with verified walkers.
Owners book via calendar, see live GPS tracking during walks, and rate walkers.
We need trust features like background checks and insurance."
```

**Best:**
```
"An on-demand dog walking platform (think Uber for pet care).

Key users:
- Pet owners (book walks, track dogs live, pay securely)
- Dog walkers (get notified, accept jobs, earn money)

Pain points we're solving:
- Hard to find reliable walkers on short notice
- Safety concerns (need verified walkers)
- No visibility during walks (GPS tracking)

Current challenge: 60% drop-off at walker signup (background check step too long)"
```

### When to Use Each Feature

| Feature | Use When |
|---------|----------|
| **Market Research** | Validating new ideas before building |
| **Upload Code** | Improving existing apps |
| **Audit Mode** | Diagnosing user drop-offs |
| **Research Only** | Pitching to investors (no build needed) |
| **A/B Tests** | Optimizing conversion rates |
| **Reports** | Sharing with team/investors/developers |

### Maximizing Quality

1. **Be specific** about pain points and user types
2. **Mention industry** (helps agent adaptation)
3. **Use Audit Mode** to catch issues early
4. **Generate A/B tests** before launching
5. **Export Dev Handover** for your team

---

## 🤝 Getting Help

**Quick Reference:**
- [CODE_WEAVER_PRO_GUIDE.md](CODE_WEAVER_PRO_GUIDE.md) - Complete guide
- [QUICK_START_NEW_FEATURES.md](QUICK_START_NEW_FEATURES.md) - Feature reference
- [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) - Technical details

**Test Individual Modules:**
```bash
python core/meta_prompt.py      # Context extraction
python core/audit_mode.py       # Drop-off analysis
python core/ab_test_generator.py # A/B variants
python core/report_generator.py  # PDF reports
```

**Community:**
- GitHub Issues: https://github.com/player20/AI-agents/issues
- Discussions: https://github.com/player20/AI-agents/discussions

---

## 🎉 What's Next?

After using Code Weaver Pro, you can:

1. **Download** your app as ZIP
2. **Deploy** to Vercel, Netlify, or cloud
3. **Generate variants** for A/B testing
4. **Export reports** for team/investors
5. **Self-improve** the platform itself

---

**Built with ❤️ using Claude Code**

*Last Updated: January 13, 2026*
