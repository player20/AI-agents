# Code Weaver Pro - Feature Backlog

**Last Updated:** January 13, 2026

This document tracks planned features, enhancements, and technical debt for future development cycles.

---

## 🎯 High Priority (Next Sprint)

### 1. Requirements Gathering Stage
**Status:** Planned
**Epic:** Pre-Build Workflow Enhancement
**Priority:** High

**Problem:**
Currently, users provide all information (API keys, credentials, preferences) in one step before execution. For complex apps (e.g., EV charger platforms with OAuth, payment SDKs, analytics), this can be overwhelming and error-prone.

**Proposed Solution:**
Add an intelligent "Requirements Gathering" stage that:
1. **Previews required inputs before execution**
   - Dynamically detects what will be needed based on user description
   - Example: "EV charger platform" → Detects OAuth, Google Maps API, Payment SDK needed
   - Shows interactive form: "To build this fully functional, I'll need..."

2. **Progressive disclosure**
   - Essential inputs first (project description, platforms)
   - Optional inputs in expandable sections (test creds, API keys)
   - "Use mocks" toggle for each requirement

3. **Smart fallbacks**
   - If API keys missing → Use mock data with clear labels
   - If test credentials missing → Skip auth testing, note in report
   - If SDKs unavailable → Suggest alternatives

4. **Implementation approach**:
   ```python
   # In streamlit_ui/requirements_preview.py
   def preview_requirements(user_input: str, platforms: List[str]) -> Dict:
       """
       Analyze user input to preview required credentials/APIs
       Returns: {
           'required': ['anthropic_api_key'],
           'optional': ['google_maps_api', 'stripe_api'],
           'test_credentials': ['email', 'password'],
           'detected_sdks': ['posthog', 'appsflyer'],
           'can_use_mocks': True
       }
       """
       pass
   ```

5. **UI Flow**:
   - User enters idea → "Go"
   - New page: "📋 Requirements Preview" with checklist
   - User fills in what they have, toggles "Use mocks" for rest
   - "✅ Ready to Build" button → Proceeds with execution

**Benefits:**
- Less overwhelming for non-technical users
- More functional outputs (no garbage data)
- Clear expectations upfront
- Better audit mode results with real credentials

**Estimated Effort:** 3-5 days
**Dependencies:** None
**Assignee:** TBD

---

### 2. Full Orchestrator Integration
**Status:** ✅ COMPLETE (January 13, 2026)
**Priority:** High → DONE

**Completed Tasks:**
- [x] Update `run_enhanced_execution()` to use `CodeWeaverOrchestrator.run()`
- [x] Pass UI callbacks (progress_callback, terminal_callback) to orchestrator
- [x] Ensure all 4 phases use orchestrator's workflow
- [x] Test end-to-end with market research, audit mode, code generation
- [x] Integrated audit mode into planning phase
- [x] Added real-time progress updates via callbacks
- [x] Unified workflow with proper state management

**Implementation:**
- All UI execution now routes through `orchestrator.run()` in [streamlit_ui/main_interface_enhanced.py](streamlit_ui/main_interface_enhanced.py#L378)
- Progress callback updates 4 phase progress bars in real-time
- Terminal callback provides color-coded logs (info/success/error/warning)
- Audit mode fully integrated into planning phase with SDK detection + funnel analysis
- LangGraph reflection loops operational in drafting phase
- DSPy prompt optimization working for vague inputs

**Impact:** Platform now has unified, production-ready workflow orchestration.

---

### 3. Enhanced SDK Detection
**Status:** Basic Implementation
**Priority:** Medium

**Current State:**
- Basic regex pattern matching in `audit_mode.py`
- Detects 9 common SDKs (PostHog, AppsFlyer, Segment, etc.)

**Enhancements:**
- [ ] Add 20+ more SDKs (Firebase, Amplitude, Braze, Mixpanel, etc.)
- [ ] Detect initialization patterns (not just imports)
- [ ] Check if SDKs are properly configured
- [ ] Suggest event tracking best practices
- [ ] Generate SDK integration diffs with code snippets

**Estimated Effort:** 2 days

---

## 🚀 Medium Priority (Future Sprints)

### 4. Test-Fix-Retest Loop Enhancement
**Status:** Planned
**Priority:** Medium

**Current State:**
- Playwright testing exists with test-fix loop (10 max iterations)
- Basic error detection and QA agent fixes

**Enhancements:**
- [ ] Smarter error categorization (UI, API, auth, data)
- [ ] Targeted fixes based on error type
- [ ] Visual regression testing (screenshot diffs)
- [ ] Performance regression detection
- [ ] Auto-rollback if fixes break other tests

**Estimated Effort:** 5-7 days

---

### 5. Meta Self-Improvement Loop (Forever Mode)
**Status:** Spec Complete, Needs Integration
**Priority:** Medium

**Current State:**
- Meta engine exists (`self_improvement.py`)
- Can analyze and improve Code Weaver Pro itself
- Not wired to "Forever Mode" UI toggle

**Tasks:**
- [ ] Add "Forever Mode" toggle in self-improve UI
- [ ] Implement hours-long autonomous loop (4-8 hours)
- [ ] Target quality threshold: 9/10
- [ ] Periodic checkpointing
- [ ] Email/Slack notifications on completion
- [ ] Safety: Max iteration limits, code review before apply

**Estimated Effort:** 3-4 days

---

### 6. Hugging Face Model Fallback
**Status:** Planned
**Priority:** Low

**Current State:**
- Only uses Anthropic Claude (Haiku/Sonnet/Opus)
- Transformers library installed but unused

**Enhancements:**
- [ ] Add Falcon-7B/40B as fallback when Claude unavailable
- [ ] Add Llama 3 70B for high-quality fallback
- [ ] Add CodeLlama for code generation tasks
- [ ] Implement smart model routing based on task type
- [ ] Cost tracking per model

**Estimated Effort:** 4-5 days

---

### 7. Real-Time Collaboration
**Status:** Idea Phase
**Priority:** Low

**Description:**
Allow multiple users to collaborate on the same project in real-time:
- Shared session URLs
- Live terminal output for all viewers
- Comment on generated code
- Vote on design variants (A/B tests)
- Real-time chat

**Estimated Effort:** 10-15 days

---

## 🛠️ Technical Debt

### TD-1: Gradio Dependency Removal
**Priority:** Low
**Current:** Gradio still in requirements.txt (legacy)
**Action:** Remove after confirming no dependencies

### TD-2: Orchestrator Code Generation
**Priority:** Medium
**Current:** Orchestrator has `_write_generated_code()` as simplified placeholder
**Action:** Integrate `code_applicator.py` for production-ready Git-based code application

### TD-3: Mock Data for Missing Credentials
**Priority:** Medium
**Current:** No systematic mock data generation
**Action:** Create `core/mock_data_generator.py` with Faker integration for realistic data

### TD-4: Async Execution
**Priority:** Low
**Current:** Some async (Playwright), some sync (agents)
**Action:** Convert all long-running operations to async for better UI responsiveness

### TD-5: Error Boundaries
**Priority:** Medium
**Current:** Global try-catch in `run_enhanced_execution()`
**Action:** Add granular error handling per phase with retry logic

---

## 📝 Documentation Improvements

### DOC-1: Video Tutorials
- [ ] 5-minute quick start video
- [ ] Audit mode deep dive (EV charger example)
- [ ] A/B testing walkthrough
- [ ] Meta self-improvement demo

### DOC-2: API Reference
- [ ] Document all core modules (meta_prompt, audit_mode, etc.)
- [ ] Add Python docstrings to all functions
- [ ] Generate Sphinx documentation

### DOC-3: Contributor Guide
- [ ] How to add new agents
- [ ] How to extend SDK detection
- [ ] How to add new report types
- [ ] Testing guidelines

---

## 🧪 Testing Improvements

### TEST-1: Integration Tests
- [ ] Full end-to-end workflow tests
- [ ] Market research + build + test cycle
- [ ] Audit mode with real localhost app
- [ ] A/B variant generation and Git verification

### TEST-2: Unit Test Coverage
**Current:** ~30% coverage
**Target:** 80% coverage

- [ ] Core modules (meta_prompt, audit_mode, ab_test_generator)
- [ ] Orchestrator workflow phases
- [ ] Report generation
- [ ] SDK detection patterns

### TEST-3: Performance Benchmarks
- [ ] Track execution time per phase
- [ ] Monitor API call counts and costs
- [ ] Measure token usage per agent
- [ ] Set performance regression alerts

---

## 🌟 Future Vision (Long-Term)

### Vision-1: Plugin Ecosystem
Allow community-contributed plugins:
- Custom agents (e.g., "Rust Engineer", "Solidity Smart Contract")
- Custom report templates
- Custom SDK detectors
- Custom test frameworks

### Vision-2: Cloud Deployment
Offer hosted version of Code Weaver Pro:
- No local setup required
- Team workspaces
- Shared project history
- Enterprise features (SSO, audit logs)

### Vision-3: AI Agent Marketplace
Allow agents to be bought/sold:
- Specialized domain experts (healthcare, fintech, gaming)
- Pre-trained on industry best practices
- Community ratings and reviews

---

## 📊 Metrics & Success Criteria

Track these metrics to measure platform success:

1. **User Satisfaction**
   - Avg quality score of generated apps: Target 8.5/10
   - User retention: Target 60% weekly active
   - Net Promoter Score: Target 50+

2. **Technical Performance**
   - Avg time to first app: Target <3 minutes
   - Test pass rate: Target 90%+
   - API error rate: Target <1%

3. **Feature Adoption**
   - Audit mode usage: Track weekly usage
   - A/B test generation: Track conversion from audit → A/B
   - Report exports: Track PDF downloads

4. **Cost Efficiency**
   - Avg cost per app generation: Track API spend
   - Model fallback usage: Monitor Haiku vs Sonnet usage
   - Token optimization: Reduce by 20% without quality loss

---

## 🤝 Contributing to Backlog

To propose new features or report issues:

1. **Feature Requests**: Open GitHub issue with label `enhancement`
2. **Bug Reports**: Open issue with label `bug` and reproduction steps
3. **Technical Debt**: Open issue with label `tech-debt` and impact analysis

**Template:**
```markdown
## Feature Request: [Title]

**Problem Statement:**
What problem does this solve?

**Proposed Solution:**
How should it work?

**Alternatives Considered:**
What other approaches were considered?

**Effort Estimate:**
T-shirt size (XS/S/M/L/XL)

**Priority:**
High/Medium/Low with justification
```

---

**Maintained by:** Code Weaver Pro Team
**Review Cycle:** Monthly sprint planning
**Next Review:** February 1, 2026
