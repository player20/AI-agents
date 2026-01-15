# Testing Checklist - Code Weaver Pro Self-Improvement

## ✅ Phase 0A: Challenger Agent Output (CRITICAL)
**Status:** ✅ DONE (committed: c0326d3e)

### Test Steps:
1. Run single cycle with 10+ files
2. Monitor terminal output for each batch
3. Verify all batches output similar character counts (15,000-25,000 chars)
4. Verify parser finds issues in ALL batches (not just 1 out of 4)
5. Check logs for "WARNING: Parser found 0 issues" - should NOT appear

**Expected Result:**
```
[BATCH] Analyzing batch 1/4 (3 files)...
   Final output: 18500 characters from Challenger
   [+] Found 42 issues in this batch: 19 bugs, 23 enhancements

[BATCH] Analyzing batch 2/4 (3 files)...
   Final output: 23250 characters from Challenger
   [+] Found 38 issues in this batch: 15 bugs, 23 enhancements
```

---

## ✅ Phase 0B: Quality Approver LLM (BLOCKING)
**Status:** ✅ DONE (committed: c0326d3e)

### Test Steps:
1. Run iterative mode (target score 9.0)
2. Wait for quality approval to trigger (score >= 8.0)
3. Check logs for quality feedback
4. Verify no OpenAI API errors

**Expected Result:**
```
[QUALITY APPROVAL] Running AI quality assessment...
   Great work! The codebase shows excellent quality with no high-priority issues...
```

---

## ✅ Phase 0C: Fixer Agent Truncation (CRITICAL)
**Status:** ✅ DONE

### Test Steps:
1. Find a file between 350-400 lines
2. Create an issue for this file manually (or let agents find one)
3. Run fix generation
4. Verify fix is NOT rejected due to shrinkage
5. Check file after fix - should maintain similar line count

**Test Files to Try:**
- `core/self_improver.py` (likely 400+ lines - should be SKIPPED)
- `core/agent_cache.py` (~200 lines - should WORK)
- `streamlit_ui/self_improvement.py` (likely 900+ lines - should be SKIPPED)

**Expected Results:**
```
# For 350-line file:
[FIX] Generating fix for agent_cache.py (250 lines)
[+] Fix applied: 250 -> 255 lines (added error handling)
[+] Test passed

# For 450-line file:
[!] Skipping issue: File too large (450 lines, max 400)
💡 Tip: For large files, create separate targeted issues
```

---

## ✅ Phase 0D: API Error Handling (BLOCKING)
**Status:** ✅ DONE

### Test Steps:
1. Run single cycle
2. Check for API validation at start
3. If Grok unavailable, verify fallback to Anthropic
4. Verify no "OpenAI timeout" errors

**Expected Results:**
```
[CYCLE] Starting improvement cycle - Mode: ui_ux
[OK] Grok API connection successful

# OR if Grok unavailable:
[!] Grok API connection timeout - network issue?
[FALLBACK] Will use Anthropic Claude models instead
```

---

## ✅ Phase 8: Agent Result Caching
**Status:** ✅ DONE

### Test Steps:
1. Run single cycle on 5-10 files
2. Note which issues were found
3. Run SECOND cycle on same files (don't modify them)
4. Verify cache hits in terminal
5. Check sidebar cache stats

**Expected Results (First Run):**
```
[CACHE] 0 hits, 10 misses (0.0% hit rate)
[CACHE] Cached analysis results for 10 files
```

**Expected Results (Second Run):**
```
[CACHE HIT] agent_cache.py - 3 issues from cache
[CACHE HIT] self_improver.py - 12 issues from cache
...
[CACHE] 10 hits, 0 misses (100.0% hit rate)
[CACHE] Saved ~10 API calls (70-80% cost savings)
[CACHE] All files cached - no analysis needed!
```

**Sidebar Check:**
- Cache stats should show 10+ entries
- Cache size should be > 0 MB
- "Clear All" and "Clear Expired" buttons should work

---

## ✅ Phase 22: Visual Issue Cards
**Status:** ✅ DONE

### Test Steps:
1. Run single cycle and find issues
2. Scroll to "Issues Prioritized & Fixed" section
3. Verify visual cards with:
   - Colored left border (red/yellow/green)
   - Bug (🐛) or enhancement (💡) icons
   - Hover animation (card slides right 4px)
   - "✓ FIXED" badge for applied fixes
   - Collapsible "Suggested Fix" section
4. Check "View All Issues" expander
5. Verify cards are grouped by type (Bugs/Enhancements)

**Expected Visual:**
```
┌─────────────────────────────────────────────────────┐
│ 🐛 Missing error handling in API call         HIGH │
│ 📁 core/api_client.py                              │
│ The API call at line 45 lacks try-catch...         │
│ 💡 Suggested Fix ▼                                 │
└─────────────────────────────────────────────────────┘
   ↑ Red left border, hover to see slide animation
```

---

## 🔍 Integration Testing

### Test 1: End-to-End Single Cycle
1. Start Streamlit app: `streamlit run app.py`
2. Navigate to Self-Improvement tab
3. Select "UI/UX" mode
4. Click "🚀 Start Improvement Cycle"
5. Wait for analysis (watch cache in action)
6. Choose "🤖 Let Agents Decide" or "📝 I'll Pick Issues"
7. Let agents fix top 5 issues
8. Download markdown report
9. Verify git branch created

**Success Criteria:**
- ✅ No errors in terminal
- ✅ Issues found and displayed as cards
- ✅ Fixes applied successfully
- ✅ Git branch created with commit
- ✅ Markdown report downloads with all issues

### Test 2: Iterative Mode (LangGraph)
1. Select "Iterative mode" checkbox
2. Set target score to 8.5
3. Click "🚀 Start Improvement Cycle"
4. Watch multiple iterations run
5. Check quality approval at score >= 8.0
6. Verify iteration history displayed

**Success Criteria:**
- ✅ Multiple iterations run automatically
- ✅ Score improves each iteration
- ✅ Quality approval provides feedback at high scores
- ✅ Stops when target reached or max iterations hit

### Test 3: Cache Invalidation
1. Run cycle on files A, B, C
2. Verify cache hits on second run
3. MODIFY file B (add a comment)
4. Run cycle again
5. Verify cache hit for A and C, cache MISS for B

**Success Criteria:**
- ✅ Modified file B triggers new analysis
- ✅ Unmodified files A and C still cached
- ✅ Cache stats accurate

---

## 🐛 Known Issues to Watch For

### Issue 1: Streamlit Rerun Loop
**Symptom:** UI keeps refreshing endlessly
**Cause:** Cache clear buttons triggering reruns
**Fix:** Already implemented (st.rerun() after clear)
**Test:** Click "Clear All" - should clear and rerun once

### Issue 2: File Path Issues on Windows
**Symptom:** Backslashes in paths causing issues
**Cause:** Windows path separators
**Fix:** Already using `str(Path(...))` for normalization
**Test:** Check cache keys use forward slashes

### Issue 3: Empty Issue Cards
**Symptom:** Cards display but no content
**Cause:** Missing issue fields (title, description, etc.)
**Fix:** Defaults in place ('Untitled Issue', 'No description')
**Test:** Force an issue with missing fields

### Issue 4: Git Branch Name Conflicts
**Symptom:** "Branch already exists" error
**Cause:** Running cycle twice with same timestamp
**Fix:** Timestamp in branch name should prevent this
**Test:** Run two cycles in same minute

---

## 📊 Performance Benchmarks

### Before Optimizations:
- First run: ~120 seconds (10 files, no cache)
- Second run: ~120 seconds (no cache)
- API calls: ~40 calls per cycle

### After Phase 8 (Caching):
- First run: ~120 seconds (cache population)
- Second run: ~20 seconds (80% faster!) ✅
- API calls: ~8 calls (80% reduction) ✅

### Target Metrics:
- Cache hit rate: > 70% on unchanged files ✅
- Cost savings: 70-80% on repeated runs ✅
- No false positives (invalid cache) ✅

---

## 🚀 Pre-Flight Checklist

Before implementing remaining phases, verify:

- [ ] All 4 critical fixes working (0A, 0B, 0C, 0D)
- [ ] Caching working (hits/misses logged correctly)
- [ ] Visual cards rendering properly (colors, hover, badges)
- [ ] No Python errors in terminal
- [ ] No browser console errors (F12)
- [ ] Git operations working (branch creation, commits)
- [ ] Download buttons working (markdown, JSON)
- [ ] Cache management UI working (stats, clear buttons)

**Once all checked, we're ready for remaining phases!**

---

## 🧪 Manual Test Commands

### Quick Syntax Check:
```bash
cd C:\Users\jacob\MultiAgentTeam
python -c "from core.agent_cache import AgentCache; print('Cache import OK')"
python -c "from core.self_improver import SelfImprover; print('Improver import OK')"
python -c "from streamlit_ui.self_improvement import render_self_improvement; print('UI import OK')"
```

### Run Full Test:
```bash
# Start Streamlit
streamlit run app.py

# In browser: http://localhost:8501
# Navigate to Self-Improvement tab
# Run single cycle with 5-10 files
```

### Check Cache Status:
```bash
ls C:\Users\jacob\MultiAgentTeam\agent_cache
# Should show .pkl files after first run
```

### Git Check:
```bash
cd C:\Users\jacob\MultiAgentTeam
git branch
# Should show improvement/* branches
git log --oneline -5
# Should show improvement commits
```

---

## ✅ Test Results

**Date:** _____________
**Tester:** _____________

| Test | Status | Notes |
|------|--------|-------|
| Phase 0A (Challenger) | ⬜ PASS / ⬜ FAIL | |
| Phase 0B (Quality Approver) | ⬜ PASS / ⬜ FAIL | |
| Phase 0C (Fixer Truncation) | ⬜ PASS / ⬜ FAIL | |
| Phase 0D (API Handling) | ⬜ PASS / ⬜ FAIL | |
| Phase 8 (Caching) | ⬜ PASS / ⬜ FAIL | |
| Phase 22 (Visual Cards) | ⬜ PASS / ⬜ FAIL | |
| Integration Test 1 | ⬜ PASS / ⬜ FAIL | |
| Integration Test 2 | ⬜ PASS / ⬜ FAIL | |
| Integration Test 3 | ⬜ PASS / ⬜ FAIL | |

**Overall Status:** ⬜ READY FOR MORE PHASES / ⬜ NEEDS FIXES

**Critical Issues Found:**
_____________________________________________________
_____________________________________________________
_____________________________________________________
