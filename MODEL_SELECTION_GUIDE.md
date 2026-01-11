# 🤖 Model Selection & Intelligent Fallback Guide

## Overview

The Multi-Agent Team now supports **model selection** and **automatic fallback** for maximum flexibility, cost optimization, and reliability.

---

## 🎯 Why Model Selection Matters

### Cost Optimization
Different Claude models have vastly different pricing:

| Model | Cost per 1M Input Tokens | Speed | Quality |
|-------|-------------------------|-------|---------|
| **Haiku** | $0.25 | ⚡⚡⚡ Fast | ⭐⭐ Good |
| **Sonnet** | $3.00 | ⚡⚡ Medium | ⭐⭐⭐ Great |
| **Opus** | $15.00 | ⚡ Slow | ⭐⭐⭐⭐ Excellent |

**Example Savings:**
- All Haiku: $0.01 per 10-agent run
- All Opus: $0.75 per 10-agent run
- **Smart Mix (Quality preset): $0.25** ← Save 67% vs All Opus!

### Strategic Agent Assignment
Use premium models where they matter most:
- **Haiku**: Simple tasks (Memory retrieval, basic planning)
- **Sonnet**: Standard work (ideas, designs, code generation)
- **Opus**: Critical decisions (senior reviews, verification)

---

## 📋 Model Presets

### 1. Speed (All Haiku) - **Fastest & Cheapest**
```
All agents use: Haiku
Cost: ~$0.01 per run
Time: ~5-8 min
Best for: Quick prototyping, brainstorming, testing
```

### 2. Balanced (All Sonnet) - **Recommended**
```
All agents use: Sonnet
Cost: ~$0.15 per run
Time: ~10-15 min
Best for: Most production work, balanced quality/cost
```

### 3. Quality (Critical=Opus, Rest=Sonnet) - **Best Results**
```
Senior: Opus
Verifier: Opus
Others: Sonnet

Cost: ~$0.25 per run
Time: ~12-18 min
Best for: Important projects, high-quality requirements
```

### 4. Premium (All Opus) - **Maximum Quality**
```
All agents use: Opus
Cost: ~$0.75 per run
Time: ~20-30 min
Best for: Critical projects, maximum quality needed
```

### 5. Budget (All Haiku, QA=Sonnet) - **Minimal Cost**
```
QA: Sonnet
Verifier: Sonnet
Others: Haiku

Cost: ~$0.03 per run
Time: ~6-10 min
Best for: Budget constraints, non-critical work
```

---

## 🎛️ How to Use Model Selection

### Option 1: Use Presets (Simple)

1. Select your agents (PM, Ideas, QA, etc.)
2. Choose a **Model Preset** from dropdown:
   - Speed (All Haiku)
   - Balanced (All Sonnet)  ← Default
   - Quality (Critical=Opus, Rest=Sonnet)
   - Premium (All Opus)
   - Budget (All Haiku, QA=Sonnet)
3. Click "Run Team"

**That's it!** The system assigns models automatically.

---

### Option 2: Custom Per-Agent Models (Advanced)

For fine-grained control:

1. Choose any preset as starting point
2. Click **"Advanced: Per-Agent Model Override"** accordion
3. For specific agents, select custom model:
   - Opus (High cost, Slow speed)
   - Sonnet (Medium cost, Medium speed)
   - Haiku (Low cost, Fast speed)
   - Use Default (follows preset)
4. Click "Run Team"

**Example Custom Setup:**
```
PM → Haiku           (simple planning)
Ideas → Sonnet       (creative ideation)
Designs → Sonnet     (visual work)
iOS → Sonnet         (code generation)
Senior → Opus        (critical review)
QA → Sonnet          (thorough testing)
Verifier → Opus      (final check)
```

---

## 🛡️ Intelligent Fallback System

### What is it?

When an API call hits a rate limit, the system **automatically**:
1. Detects the rate limit error (429, quota exceeded, etc.)
2. Falls back to the next cheaper/faster model
3. Retries with exponential backoff
4. Logs all attempts for transparency

### Fallback Chain

```
Opus (rate limited)
  ↓
Sonnet (retry)
  ↓
Haiku (final fallback)
  ↓
Error (only if all fail)
```

### How It Works

#### Scenario 1: Rate Limit on Opus
```
1. Try: Senior agent with Opus
2. ⚠️ Rate limit hit!
3. → Fallback to Sonnet
4. Wait 5s
5. ✓ Retry succeeds with Sonnet
6. Log: "Senior: ✓ Succeeded after 2 attempts"
```

#### Scenario 2: Network Error
```
1. Try: PM agent with Haiku
2. ❌ Network timeout
3. Wait 5s (exponential backoff)
4. Try again
5. ❌ Still failing
6. Wait 15s (2x multiplier)
7. Try again
8. ✓ Succeeds
9. Log: "PM: ✓ Succeeded after 3 attempts"
```

#### Scenario 3: Total Failure (Rare)
```
1. Try: Ideas with Opus
2. ⚠️ Rate limit → Fallback to Sonnet
3. ⚠️ Rate limit → Fallback to Haiku
4. ❌ Still failing after 3 attempts
5. Error returned with full context
6. User can retry manually or wait
```

---

## 📊 Retry Configuration

### Default Settings

```python
MAX_RETRIES = 3
RETRY_DELAY_BASE = 5 seconds
RETRY_BACKOFF_MULTIPLIER = 2 (exponential)
```

### Retry Timeline

| Attempt | Delay | Total Time |
|---------|-------|------------|
| 1 | 0s | 0s |
| 2 | 5s | 5s |
| 3 | 15s | 20s |

**Maximum overhead**: ~20 seconds per failing agent

---

## 📈 Real-World Examples

### Example 1: Startup MVP Development

**Goal**: Quick prototype, minimal cost
**Preset**: Speed (All Haiku)
**Agents**: PM, Ideas, Designs, Web, QA
**Cost**: ~$0.01
**Time**: ~6 minutes
**Result**: Fast concept validation

---

### Example 2: Production Feature

**Goal**: Balanced quality and cost
**Preset**: Balanced (All Sonnet)
**Agents**: All 10 agents
**Cost**: ~$0.15
**Time**: ~15 minutes
**Result**: Production-ready implementation

---

### Example 3: Critical Enterprise Project

**Goal**: Maximum quality, budget available
**Preset**: Quality (Critical=Opus)
**Custom Override**:
- Designs → Opus (visual excellence)
- iOS → Opus (complex logic)
- Android → Opus (complex logic)

**Cost**: ~$0.45
**Time**: ~25 minutes
**Result**: Enterprise-grade quality

---

### Example 4: Rate Limit Scenario

**Situation**: Opus quota exceeded mid-run

**What Happens**:
```
[10:30:00] PM → Haiku ✓
[10:30:15] Ideas → Haiku ✓
[10:30:30] Senior → Opus
[10:30:35] Senior: ⚠️ Rate limit hit with Opus
[10:30:35] Senior: → Falling back to Sonnet
[10:30:35] Senior: Waiting 5s before retry...
[10:30:40] Senior: Attempt 2/3 with Sonnet
[10:30:45] Senior: ✓ Succeeded after 2 attempts
[10:30:50] Verifier → Opus
[10:30:55] Verifier: ⚠️ Rate limit hit with Opus
[10:30:55] Verifier: → Falling back to Sonnet
[10:31:00] Verifier: ✓ Succeeded after 2 attempts
```

**Result**: Run completes successfully despite rate limits!

---

## 🔍 Monitoring & Transparency

### System Logs

All model usage and fallbacks are logged:

```
[14:30:00] Starting new project with 5 agent(s)
[14:30:00] Selected agents: PM, Ideas, Senior, QA, Verifier
[14:30:00] Model preset: Quality (Critical=Opus, Rest=Sonnet)
[14:30:00] PM → Sonnet
[14:30:00] Ideas → Sonnet
[14:30:00] Senior → Opus
[14:30:00] QA → Sonnet
[14:30:00] Verifier → Opus
[14:30:05] Initializing crew with 5 agent(s)
[14:30:10] Starting task execution...
...
```

### Export Metadata

All exports include model information:

**JSON Export**:
```json
{
  "metadata": {
    "model_preset": "Quality (Critical=Opus, Rest=Sonnet)",
    "agent_models": {
      "PM": "claude-3-sonnet-20240229",
      "Senior": "claude-3-opus-20240229",
      "Verifier": "claude-3-opus-20240229"
    }
  }
}
```

**Markdown Export**:
```markdown
## Metadata
- **model_preset:** Quality (Critical=Opus, Rest=Sonnet)
- **agent_models:** {"PM": "claude-3-sonnet-20240229", ...}
```

---

## 💡 Best Practices

### 1. Start with Presets
Don't overthink it - the presets are well-designed for common scenarios.

### 2. Use Quality Preset for Important Work
The ~$0.25 cost is worth it for critical decisions.

### 3. Override Only When Needed
Custom per-agent models are powerful but add complexity. Use sparingly.

### 4. Monitor System Logs
Watch for rate limit patterns. If you see frequent fallbacks, consider:
- Upgrading your API tier
- Using cheaper models by default
- Spacing out runs

### 5. Leverage Fallback Safety Net
Don't be afraid to use Opus when appropriate - the fallback system protects you from failures.

### 6. Cost-Optimize Iteratively
- First run: Use Balanced preset
- If quality insufficient: Try Quality or Premium
- If quality sufficient: Try Speed or Budget

---

## 🎓 Advanced Tips

### Tip 1: Strategic Model Mixing

For **code-heavy projects**:
```
PM → Haiku
Ideas → Haiku
Designs → Sonnet
iOS/Android/Web → Opus (complex code)
Senior → Opus
QA → Sonnet
Verifier → Opus
```

For **design-heavy projects**:
```
PM → Haiku
Ideas → Sonnet
Designs → Opus (critical visual decisions)
Engineers → Sonnet
Senior → Opus
QA → Sonnet
Verifier → Opus
```

### Tip 2: Testing Fallback

Temporarily set all agents to Opus to test fallback behavior when you're near rate limits.

### Tip 3: Batch Processing

If running multiple projects, alternate between presets to distribute API load:
- Project 1: Quality preset
- Project 2: Speed preset
- Project 3: Balanced preset

### Tip 4: Cost Tracking

Export to JSON and analyze `agent_models` to track spending patterns.

---

## 📉 Cost Comparison Matrix

| Scenario | Preset | Est. Cost | Time | Quality |
|----------|--------|-----------|------|---------|
| Quick test | Speed | $0.01 | 5min | ⭐⭐ |
| Daily work | Balanced | $0.15 | 15min | ⭐⭐⭐ |
| Important feature | Quality | $0.25 | 18min | ⭐⭐⭐⭐ |
| Mission critical | Premium | $0.75 | 25min | ⭐⭐⭐⭐⭐ |
| Budget constraint | Budget | $0.03 | 8min | ⭐⭐ |

*Costs based on 10-agent run with ~50k tokens

---

## 🚨 Troubleshooting

### Issue: "Rate limit hit" messages appearing

**Cause**: Your API tier has usage limits

**Solutions**:
1. Use cheaper default models (Speed or Budget preset)
2. Reduce number of concurrent agents
3. Increase `RATE_LIMIT_DELAY` in config
4. Upgrade API tier

---

### Issue: Fallback not working

**Verify**:
1. Check system logs for error messages
2. Ensure `AVAILABLE_MODELS` includes all models
3. Verify `MODEL_FALLBACK_CHAIN` is configured
4. Check API key permissions

---

### Issue: Custom model not being used

**Debug**:
1. Check "Use Default" is not selected
2. Verify model name matches exactly
3. Check system logs for "Using custom model" message
4. Ensure proper UI wiring

---

## 🔧 Configuration Reference

### Model Definitions

Located in `multi_agent_team.py` lines 23-27:

```python
AVAILABLE_MODELS = {
    "claude-3-opus-20240229": {
        "name": "Opus",
        "tier": 3,
        "cost": "High",
        "speed": "Slow"
    },
    ...
}
```

### Fallback Chain

Lines 33-37:

```python
MODEL_FALLBACK_CHAIN = [
    "claude-3-opus-20240229",
    "claude-3-sonnet-20240229",
    "claude-3-haiku-20240307"
]
```

### Retry Settings

Lines 40-42:

```python
MAX_RETRIES = 3
RETRY_DELAY_BASE = 5
RETRY_BACKOFF_MULTIPLIER = 2
```

---

## 📚 Related Documentation

- [QUICK_START.md](QUICK_START.md) - Basic usage guide
- [README_ENHANCED.md](README_ENHANCED.md) - Full documentation
- [multi_agent_team.py](multi_agent_team.py) - Source code

---

## 🎉 Summary

✅ **5 Model Presets** - From Speed to Premium
✅ **Per-Agent Override** - Fine-grained control
✅ **Automatic Fallback** - Rate limit protection
✅ **Exponential Retry** - Network resilience
✅ **Full Transparency** - Detailed logging
✅ **Export Tracking** - Cost analysis ready

**The system is now production-ready with intelligent model selection and bulletproof fallback handling!**

---

**Version**: 2.1
**Last Updated**: January 2026
**Status**: Production Ready ✅
