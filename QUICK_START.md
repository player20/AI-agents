# 🚀 Quick Start Guide - Code Weaver Pro

**Transform ideas into production-ready apps in 2-5 minutes**

## Installation (30 Seconds)

```bash
# 1. Clone and navigate
git clone https://github.com/player20/AI-agents
cd AI-agents

# 2. Install dependencies
pip install -r requirements.txt
playwright install

# 3. Set up API key
cp .env.example .env
# Edit .env and add: ANTHROPIC_API_KEY=sk-ant-your-key-here

# 4. Launch
streamlit run app.py
```

Open your browser to **http://localhost:8501** 🎉

---

## Basic Usage (3 Steps)

### Step 1: Describe Your Idea

In the large input box, describe what you want to build in plain English:

```
Example: "A dog walking app where pet owners book walks
and walkers get notified in real-time"
```

**Tips for better results:**
- ✅ Describe the problem you're solving
- ✅ Mention your target users
- ✅ Include key features you envision
- ❌ No need for technical details (agents decide tech stack automatically)

### Step 2: Choose Platform(s)

Select where your app should run:
- 🌐 **Website** - Static HTML/CSS/JS
- 💻 **Web App** - Full-stack with backend (React + Node.js)
- 📱 **iOS** - Native Swift/SwiftUI
- 🤖 **Android** - Native Kotlin/Jetpack Compose

*You can select multiple platforms!*

### Step 3: Click the Big "GO" Button

Watch the magic happen:
1. **Planning Phase** - Agents analyze and plan
2. **Drafting Phase** - Code generation
3. **Testing Phase** - Automated tests
4. **Done!** - Download your app

---

## Feature Guide

### 📊 Market Research (Validate Ideas First)

**When to use:** Before building anything, validate your idea

**How to enable:** ✅ Check **"Quick market check first"**

**What you get:**
- TAM/SAM/SOM market size analysis
- List of 10-15 competitors
- GO/NO-GO recommendation with reasoning
- Key features needed to compete
- Differentiation strategy

**Example workflow:**
```
Input: "AI-powered meal planning app for dietary restrictions"
✅ Quick market check first
✅ Research only (don't build yet)
Click GO

Result: Market analysis + competitor list + strategic recommendations
Export as Executive Summary PDF for investors
```

**Time:** ~3-5 minutes

---

### 📦 Upgrade Existing Code

**When to use:** You have an app that needs improvements

**How to enable:** ✅ Check **"I have code to upgrade"**

**Upload options:**
- ZIP file of your codebase
- Or paste code directly

**What you get:**
- Framework detection (React, Swift, Python, etc.)
- AST analysis of your code structure
- Recommended improvements
- Before/after diffs
- New Git branch `better-me` with changes

**Example workflow:**
```
✅ I have code to upgrade
Upload: my-app.zip
Click GO

Result: Analysis + suggested improvements + code diffs
```

**Time:** ~4-6 minutes

---

### 📉 Analyze User Drop-Offs (Audit Mode)

**When to use:** You have an app but users abandon it at certain points

**How to enable:** ✅ Check **"Analyze user drop-offs"**

**Provide:**
- Upload code (ZIP) OR
- Live URL (e.g., `http://localhost:3000`)
- Optional: Test credentials for auth-protected apps

**What you get:**
- Funnel analysis with exact drop-off percentages
- Root cause analysis for each drop-off point
- Specific fixes with code snippets
- SDK recommendations (PostHog, AppsFlyer, OneSignal, etc.)
- Interactive funnel visualization chart

**Example workflow:**
```
Input: "EV charger sharing platform with 70% drop-off at signup"
✅ Analyze user drop-offs
Provide URL: http://localhost:3000
Click GO

Result:
- "73% drop at profile creation form"
- Reason: "12 required fields, no progress indicator"
- Fixes: Reduce to 3 fields, add progress bar, defer payment
- PDF report with recommendations
```

**Time:** ~5-8 minutes

**Advanced: Test Credentials**

For apps with authentication:
1. Check **"Analyze user drop-offs"**
2. Expand **"Test Credentials (Optional)"**
3. Enter test email/password
4. Playwright will auto-login and simulate real user flows

*Credentials are in-memory only, never stored*

---

### 🎨 Generate A/B Test Variants

**When to use:** Optimize conversion rates with different designs

**Available after:** Initial app generation completes

**How to enable:** Click **"Generate A/B Test Variants"** button in results

**What you get:**
- 3 variants automatically created:
  - **Control** - Original version
  - **Variant A** - Bold colors, action-oriented copy, urgent CTAs
  - **Variant B** - Professional colors, trust-building copy, calm CTAs
- Separate Git branches for each variant
- Pre-configured tracking events
- Experiment configuration for PostHog/Optimizely

**Example workflow:**
```
After building app:
Click "Generate A/B Test Variants"

Result:
- Branch: ab-test-control
- Branch: ab-test-variant-a (red primary, "Get Started Now")
- Branch: ab-test-variant-b (blue primary, "Learn More")
- experiment-config.json ready to import
```

**Time:** ~2-3 minutes

---

### 📄 Export Professional Reports

**When to use:** Share with team, investors, or developers

**Available after:** Generation completes

**Report types:**

**1. Executive Summary PDF**
- For investors/CEOs/stakeholders
- Market analysis with charts
- App screenshots
- Strategic recommendations
- Scores and metrics

**2. Dev Handover PDF**
- For engineers joining the project
- Code diffs with syntax highlighting
- Setup instructions
- Git commit history
- Technical architecture

**How to export:**
1. Scroll to results section
2. Click **"Export Executive Summary"** or **"Export Dev Handover"**
3. PDF downloads automatically

**Time:** Instant

---

## Advanced Options

Click **"Advanced Options"** expander for:

### Custom Workflow
Upload custom workflow YAML to override default pipeline

### Model Selection
- **Haiku** (Default) - Fast, cheap, good quality (~$0.01-0.05 per run)
- **Sonnet** - Better reasoning, more detailed (~$0.10-0.20 per run)
- **Opus** - Highest quality, slower (~$0.50-1.00 per run)

**Recommendation:** Haiku is excellent for most projects

### Agent Team Configuration
Select specific agents to run (advanced users only)

---

## Complete Example Workflows

### Example 1: New App from Scratch

**Goal:** Build a recipe sharing app

**Steps:**
1. Input:
   ```
   "A recipe app where users save favorites and share with friends.
   Target millennials who want quick healthy meals."
   ```
2. Select platforms: ✅ Web App, ✅ iOS
3. Click **GO**
4. Wait 3-4 minutes
5. Download ZIP with:
   - Frontend: React + TypeScript
   - Backend: Node.js + Express + PostgreSQL
   - Mobile: React Native (iOS)
   - Tests: Jest + Playwright
   - README with setup instructions

**Time:** ~3-4 minutes | **Cost:** ~$0.02

---

### Example 2: Validate Before Building

**Goal:** Check if meal planning app is viable

**Steps:**
1. Input:
   ```
   "AI meal planning app for dietary restrictions (vegan, keto, gluten-free).
   Users get weekly plans with grocery lists."
   ```
2. Check: ✅ Quick market check first
3. Check: ✅ Research only (don't build yet)
4. Click **GO**
5. Review outputs:
   - Market size: $8.5B, growing 12% annually
   - Competitors: MyFitnessPal, Mealime, PlateJoy
   - GO/NO-GO: **GO** with differentiation on multi-restriction support
   - Required features to compete
6. Export **Executive Summary PDF** for pitch deck

**Time:** ~4 minutes | **Cost:** ~$0.03

---

### Example 3: Fix Drop-Offs in Existing App

**Goal:** Diagnose why 70% of users quit at signup

**Steps:**
1. Input:
   ```
   "EV charger sharing platform where hosts list chargers and
   drivers book them. We're seeing 70% drop at profile creation."
   ```
2. Check: ✅ Analyze user drop-offs
3. Provide URL: `http://localhost:3000`
4. Expand "Test Credentials" and add test email/password
5. Click **GO**
6. Review results:
   - Landing page: 100% (baseline)
   - Signup start: 85% (-15% drop)
   - Profile form: 27% (-58% drop) ⚠️ **MAJOR DROP-OFF**
   - Payment info: 22% (-5% drop)
   - Completion: 18% (-4% drop)
7. Root cause: "12 required fields, no progress indicator, no social login"
8. Recommendations with code:
   - Reduce to 3 fields initially
   - Add progress bar component
   - Defer payment to later step
   - Add Google/Apple social login
9. SDK suggestions: PostHog (heatmaps), AppsFlyer (attribution)
10. Export **Dev Handover PDF** with fixes

**Time:** ~6-8 minutes | **Cost:** ~$0.05

---

### Example 4: A/B Test Landing Page

**Goal:** Optimize conversion rate on landing page

**Steps:**
1. Build initial app (from Example 1)
2. Click **"Generate A/B Test Variants"**
3. Review 3 variants created:
   - Control: Original purple theme, "Get Started"
   - Variant A: Red/orange theme, "Join Free Now"
   - Variant B: Blue/indigo theme, "Learn More"
4. Git branches created automatically:
   - `ab-test-control`
   - `ab-test-variant-a`
   - `ab-test-variant-b`
5. Import `experiment-config.json` into PostHog
6. Deploy each branch to separate URLs
7. Run experiment for 1-2 weeks
8. Analyze results in PostHog

**Time:** ~3 minutes | **Cost:** ~$0.02

---

## Understanding Output Scores

After generation, you'll see 4 scores (0-10 scale):

| Score | What It Measures | Good Score |
|-------|-----------------|------------|
| **Speed** | Load time, responsiveness | 8+ |
| **Mobile-Friendly** | Touch targets, viewport, gestures | 7+ |
| **Intuitiveness** | Clear navigation, minimal friction | 8+ |
| **Functionality** | Features work, edge cases handled | 9+ |

**Overall Rating:**
- 8-10: ⭐⭐⭐ Production-ready
- 6-7: ⭐⭐ Minor polish needed
- 4-5: ⭐ Improvements recommended
- 0-3: ❌ Major issues

---

## Troubleshooting

### "ANTHROPIC_API_KEY not set"

**Fix:**
```bash
# Option 1: Edit .env file
echo "ANTHROPIC_API_KEY=sk-ant-your-key-here" > .env

# Option 2: Export environment variable
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
```

Then restart: `streamlit run app.py`

---

### "Module not found" errors

**Fix:**
```bash
pip install -r requirements.txt
playwright install
```

---

### "Failed to crawl app" (Audit Mode)

**Problem:** App not running or wrong URL

**Fix:**
1. Start your app first (`npm run dev`, etc.)
2. Verify URL and port (e.g., `http://localhost:3000` not `3001`)
3. Check browser console for CORS errors
4. Ensure app is accessible without VPN/proxy

---

### "Clarification requested"

**Why:** Your input clarity score was < 6/10

**Options:**
1. Provide more details when asked (recommended)
2. Click **"Skip & Continue Anyway"** if you want to proceed

**Example clarification:**
```
Original: "A recipe app"

System asks: "Could you tell me more about your users and key features?"

Good response: "Target busy millennials who want quick healthy meals.
Key features: search by ingredients, save favorites, meal planning calendar,
grocery list generation, social sharing."
```

---

### App runs slow or times out

**Fix:**
1. Use Haiku model (faster, cheaper)
2. Select fewer platforms (just Web App instead of all 4)
3. Skip market research if not needed
4. Check internet connection

---

## Tips & Best Practices

### 💡 Writing Great Prompts

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
"A meal planning platform for people with dietary restrictions (vegan, keto, gluten-free).

Users:
- People with multiple dietary restrictions
- Busy professionals who meal prep weekly

Key Features:
- Input dietary restrictions
- Get weekly meal plans
- Auto-generate grocery lists
- Track nutrition goals

Pain Point: Hard to find recipes that match multiple restrictions at once."
```

---

### 💡 When to Use Each Feature

| Feature | Use When | Don't Use When |
|---------|----------|----------------|
| **Market Research** | Validating new ideas | Building internal tools |
| **Upload Code** | Improving existing apps | Starting from scratch |
| **Audit Mode** | Diagnosing drop-offs | No app exists yet |
| **Research Only** | Pitching to investors | Ready to build immediately |
| **A/B Tests** | Optimizing conversions | Still in MVP stage |

---

### 💡 Maximizing Quality

1. **Be specific** about pain points and user types
2. **Mention industry** (helps agent adaptation - agents become domain experts)
3. **Use Audit Mode early** to catch issues before launch
4. **Generate A/B tests** before launching to optimize conversions
5. **Export Dev Handover** when bringing in new developers

---

### 💡 Cost Optimization

- Use **Haiku** for prototypes and MVPs (20x cheaper than Opus)
- Use **Sonnet** for production apps (good balance)
- Use **Opus** only for mission-critical final reviews
- Skip market research if you already know your market
- Select specific platforms instead of all 4

**Example costs:**
- Simple web app (Haiku): ~$0.01-0.02
- Full-stack app with iOS/Android (Haiku): ~$0.04-0.06
- Complete market research + app (Sonnet): ~$0.15-0.25

---

### 💡 Iterating with Feedback

Code Weaver Pro remembers context across runs:

1. **First run:** Generate initial app
2. **Review:** Check what needs improvement
3. **Second run:** Add specific feedback in input:
   ```
   "Update the recipe app from before. Make it more mobile-friendly
   with larger touch targets and simpler navigation."
   ```
4. **Result:** Refined version incorporating feedback

---

## Mode Selection

Code Weaver Pro has 2 modes (toggle at top):

### ✨ Create App Mode (Default)
- Build new apps from scratch
- Validate ideas with market research
- Improve existing code
- Analyze user drop-offs
- Generate A/B tests
- Export reports

### 🔄 Self-Improve Mode
- Platform analyzes its own code
- Identifies UI/UX improvements
- Generates diffs
- Shows preview
- Commits improvements to Git

**Use Self-Improve Mode for:**
- Making Code Weaver Pro itself better
- Autonomous meta-improvement loop
- "Forever mode" runs for hours until 9/10 quality

---

## Next Steps

### Beginners
1. ✅ Run with default settings
2. ✅ Try building a simple app (recipe app, todo list, etc.)
3. ✅ Download the ZIP and explore the code

### Intermediate
1. ✅ Validate an idea with market research
2. ✅ Use Audit Mode on an existing app
3. ✅ Generate A/B test variants
4. ✅ Export professional reports

### Advanced
1. ✅ Upload custom workflow YAML
2. ✅ Configure specific agent teams
3. ✅ Use Self-Improve Mode to enhance the platform
4. ✅ Integrate with your CI/CD pipeline

---

## More Resources

- **[README.md](README.md)** - Complete overview
- **[LAUNCH_GUIDE_ENHANCED.md](LAUNCH_GUIDE_ENHANCED.md)** - Detailed feature guide
- **[CODE_WEAVER_PRO_GUIDE.md](CODE_WEAVER_PRO_GUIDE.md)** - 70+ page technical guide
- **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)** - Integration details

**Test Individual Modules:**
```bash
python core/meta_prompt.py          # Context extraction
python core/audit_mode.py           # Drop-off analysis
python core/ab_test_generator.py   # A/B variants
python core/report_generator.py    # PDF reports
```

---

## Success Checklist

Before your first run:

- [ ] Python 3.10+ installed
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Playwright installed (`playwright install`)
- [ ] `.env` file created with ANTHROPIC_API_KEY
- [ ] App launched (`streamlit run app.py`)
- [ ] Browser opened to http://localhost:8501

**Ready?** Type your idea and click GO! 🚀

---

## Feature Comparison

| Feature | Old System | Code Weaver Pro |
|---------|-----------|----------------|
| Interface | Gradio (port 7860) | Streamlit (port 8501) |
| UX | Technical | Magical, user-friendly |
| Input | Small text box | Large inviting input |
| Agents | 10 fixed | 52 specialized agents |
| Agent Adaptation | Static | Dynamic (context-aware) |
| Market Research | Limited | Comprehensive TAM/SAM/SOM |
| Code Review | Basic | Drop-off analysis with Playwright |
| A/B Testing | None | Automatic variant generation |
| Reports | None | Professional PDF export |
| Self-Improvement | None | Meta-improvement loop |
| Configuration | Hardcoded | .env file support |
| Frameworks | Basic | LangGraph, CrewAI, DSPy |

---

**Happy Building!** 🎉

*Built with ❤️ using Claude Code*

*Last Updated: January 13, 2026*
