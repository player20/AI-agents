# Architecture Review: Agent Prompts & Evaluation

## My Evaluation (Claude's Assessment)

### ✅ Strengths

1. **Clear Mental Model**: The org chart metaphor is intuitive - users already understand organizational hierarchies
2. **Good Separation of Concerns**: Projects → Agent Teams → Individual Agents provides clear layering
3. **Scalability**: Database schema supports growth (projects, teams, members, executions)
4. **Reusability**: Teams can be saved as templates and reused across projects
5. **Execution Tracking**: Comprehensive logging of runs, costs, tokens for analytics

### ⚠️ Concerns

1. **Complexity for New Users**: Might be overwhelming initially - need excellent onboarding
2. **Team Dependency Management**: How do we handle circular dependencies or complex workflows?
3. **Error Recovery**: If Team 2 fails, do we retry just that team or restart from Team 1?
4. **Performance**: Sequential execution could be slow for large projects (10+ teams)
5. **Cost Control**: Users might accidentally run expensive workflows - need safeguards

### 🎯 Recommendations

1. **Start Simple**: Launch with basic project → teams, add advanced features later
2. **Template First**: Provide 10-15 excellent templates to show the power
3. **Visual Feedback**: The org chart needs to be the primary interface, not a secondary view
4. **Progressive Disclosure**: Hide advanced features (dependencies, conditional execution) initially
5. **Undo/Rollback**: Let users revert to previous project states

---

## Agent Review Prompts

### For PM (Project Manager)

**Prompt:**
```
You're reviewing a new architecture for organizing AI agent workflows.

READ: PROJECT_AGENT_TEAMS_ARCHITECTURE.md

ANALYZE:
- Execution flow: Sequential team execution makes sense?
- Project management: How do we track progress across multiple teams?
- Error handling: What happens when a team fails mid-project?
- Dependencies: Should teams declare what they need from previous teams?

PROVIDE (max 300 words):
1. One major strength
2. One major risk
3. One specific recommendation
```

### For Senior Engineer

**Prompt:**
```
Technical architecture review needed.

READ: PROJECT_AGENT_TEAMS_ARCHITECTURE.md (focus on database schema)

EVALUATE:
- Database schema: Any normalization issues or missing relationships?
- API design: RESTful? Any endpoint naming concerns?
- Scalability: Can this handle 1000 projects, 10,000 teams?
- Real-time updates: WebSocket architecture sound?

PROVIDE (max 300 words):
1. Technical red flag (if any)
2. Performance bottleneck to watch
3. One code-level improvement
```

### For Product Owner

**Prompt:**
```
UX and product strategy review.

READ: AGENT_ORG_CHART_DESIGN.md

ASSESS:
- User mental model: Will non-technical users "get" org charts for AI teams?
- Onboarding: How do we teach this without overwhelming?
- Value proposition: What's the #1 problem this solves?
- Competition: How does this compare to n8n, Flowise, LangFlow?

PROVIDE (max 300 words):
1. Biggest UX concern
2. One killer feature to highlight
3. User research question to validate
```

### For Ideas Agent

**Prompt:**
```
Creative thinking needed.

CONTEXT: We're building an org chart interface for AI agent teams.

BRAINSTORM:
- What if teams could communicate with each other (agent-to-agent)?
- Should we have "manager agents" that coordinate teams?
- Could we auto-generate teams based on project description?
- What about "team chemistry" - agents that work well together?

PROVIDE (max 300 words):
1. One wild but potentially game-changing idea
2. One small enhancement that would delight users
3. One integration opportunity (with other tools)
```

### For QA Engineer

**Prompt:**
```
Quality assurance and edge case analysis.

READ: PROJECT_AGENT_TEAMS_ARCHITECTURE.md (execution section)

TEST SCENARIOS:
- What if a team has 0 agents?
- What if user deletes a team while it's running?
- What if two teams try to execute simultaneously?
- What if output from Team 1 is 500MB+?

PROVIDE (max 300 words):
1. Top 3 edge cases to test
2. One data validation rule we need
3. One integration test scenario
```

### For Verifier

**Prompt:**
```
Critical analysis and fact-checking.

READ: All architecture documents

VERIFY:
- Are the three documents (architecture, org chart, human checkpoints) consistent?
- Are cost estimates realistic ($0.80-$1.20 per review)?
- Are time estimates realistic (10-15 mins for 6 agents)?
- Are there security/privacy risks in the database schema?

PROVIDE (max 300 words):
1. One internal contradiction found (if any)
2. One assumption that needs validation
3. One risk not addressed in the documents
```

---

## Expected Output Format

Each agent should provide a **concise synopsis** in this format:

```markdown
## [Agent Name] Synopsis

### 🎯 Key Finding
[One-sentence main takeaway]

### ✅ Strength
[One strength identified - 1-2 sentences]

### ⚠️ Risk/Concern
[One risk or concern - 1-2 sentences]

### 💡 Recommendation
[One specific, actionable recommendation - 1-2 sentences]

### 📊 Confidence Level
[High/Medium/Low] - based on available information
```

---

## Example Synopsis (What We Want)

```markdown
## PM Synopsis

### 🎯 Key Finding
The sequential team execution model is sound but needs robust error recovery.

### ✅ Strength
Clear execution order prevents race conditions and makes debugging easier.

### ⚠️ Risk/Concern
If Team 3 fails in a 10-team project, there's no clear strategy for whether to retry just that team or restart from scratch.

### 💡 Recommendation
Implement a "checkpoint system" where each team's output is saved, allowing selective re-runs without losing previous work.

### 📊 Confidence Level
High - this pattern is proven in CI/CD pipelines
```

---

## Human Approval Checkpoints: Second Review

After reviewing the org chart architecture, agents should also consider:

### Additional Prompt for All Agents

```
Now consider the Human Approval Checkpoints system (HUMAN_APPROVAL_CHECKPOINTS.md).

This adds gates where humans can:
- ✅ Approve agent output and continue
- ❌ Deny and request changes
- ✏️ Edit the output before passing to next team
- ⏭️ Skip approval and continue

QUESTIONS TO CONSIDER:
1. Where are checkpoints most valuable? (after every team? only critical teams?)
2. How do we prevent "approval fatigue" where users just click approve without reading?
3. What's the right default: require approval or auto-approve with option to review?
4. Should failed agents automatically trigger a checkpoint, or only on user request?
5. How do we handle checkpoints in automated/scheduled workflows?

PROVIDE:
- One guideline for when to show checkpoints
- One way to reduce approval fatigue
- One metric to track checkpoint effectiveness
```

---

## Action Items

1. **Run the Review**: Execute the multi-agent workflow with these prompts
2. **Collect Synopses**: Gather concise summaries from each agent (not full outputs)
3. **Synthesize**: Create a unified decision document with:
   - Top 3 strengths
   - Top 3 risks
   - Top 5 recommendations
4. **Prioritize**: Rank recommendations by impact vs effort
5. **Decide**: Go/No-Go on the org chart architecture
6. **Plan**: If Go, create 2-week sprint plan to implement MVP

---

## Questions for You (User)

Before running the agents, please clarify:

1. **Scope**: Do you want to build the full org chart system, or start with just Projects + Teams (no visual org chart yet)?

2. **Timeline**: Are you thinking 2 weeks for MVP, or longer?

3. **Database**: Should we use Supabase (you already have it for another project) or separate PostgreSQL?

4. **Priority**: Which matters more:
   - Visual org chart interface?
   - Human approval checkpoints?
   - Template library?
   - Team dependency management?

5. **MVP Features**: For launch, which are must-haves vs nice-to-haves?
   - Must-have: Projects, Teams, Sequential Execution
   - Nice-to-have: Org chart visual, Approval gates, Templates

Let me know your preferences and I'll run the agent review with the appropriate focus!
