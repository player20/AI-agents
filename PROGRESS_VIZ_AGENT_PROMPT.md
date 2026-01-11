# Agent Evaluation Prompt: Interactive Progress & Task Management System

**Copy this entire prompt into your Multi-Agent Team platform**

---

## Context

We're building an **interactive task management and progress visualization system** for the Multi-Agent Dev Team platform.

**Current Platform:**
- Gradio-based web interface
- 11 agents (PM, Memory, Research, Ideas, Designs, iOS, Android, Web, Senior, QA, Verifier)
- Sequential agent execution
- Tabs showing agent outputs

**Theme:** Futuristic, fun, polished (neon accents, auto dark/light mode, glowing animations)

**Design Goals:**
- **Intuitive** - Easy to understand at a glance
- **Fun** - Enjoyable to interact with
- **Engaging** - Makes users want to use the platform

---

## The Problem

Right now, users don't have:
- Visual sense of progress during execution
- Way to manage tasks or proposals from agents
- Interactive workflow control
- Clear status indicators

**User Need:**
> "It would be nice to see progress. Like tickets or items moving through each phase."

**Key Requirement:**
> "Each item that is proposed goes into a holding state or backlog until the user selects it to move on to the next phase."

This is an **interactive system** where users have control, not just passive visualization.

---

## Your Mission

**Design a creative, innovative task management and progress system** for the platform.

**No constraints on your ideas** - think outside the box! Consider:
- What would make workflow management **fun and intuitive**?
- How can we visualize progress in a **futuristic, engaging** way?
- What interaction patterns would users **love** to use?

---

## Research Agent Tasks

### 1. Inspiration Research

Research innovative task/progress visualization systems. Don't limit yourself to traditional boards:

**Platforms to study:**
- Linear (modern issue tracking)
- Height (collaborative task management)
- Notion (flexible databases)
- Monday.com (colorful workflows)
- Asana (timeline views)
- ClickUp (multiple views)
- Base44 (vibe code no code platform)
- Video game UI (inventory systems, skill trees)
- Data visualization dashboards

**Questions:**
- What makes these systems feel **good** to use?
- What innovative UI patterns do they use?
- What makes progress visualization **satisfying**?
- Are there non-traditional metaphors we could use?

### 2. Technical Feasibility

Research what's possible in Gradio:

**Can we build:**
- Interactive drag-and-drop?
- Real-time animations?
- Custom JavaScript components?
- Particle effects or transitions?
- Audio feedback (optional)?

**Recommend:**
- Best technical approach for Gradio
- Libraries/frameworks to use
- Performance considerations

### 3. Novel Interaction Patterns

Think beyond Kanban boards. What other metaphors could work?

**Alternative concepts:**
- **Skill tree** (agents unlock as dependencies complete)
- **Assembly line** (items move through stations)
- **Node graph** (visual programming style)
- **Timeline** (Gantt chart style)
- **Circular/radial** (agents around a wheel)
- **3D carousel** (rotating through phases)
- **Card deck** (shuffle, draw, discard)
- **Other creative ideas?**

---

## Ideas Agent Tasks

### 1. Propose 3-5 Creative Concepts

Don't hold back! Propose **completely different approaches**:

**For each concept:**
- **Name** (catchy, memorable)
- **Core metaphor** (e.g., "Assembly Line", "Quest Board", "Mission Control")
- **Visual style** (how it looks)
- **Interactions** (how users control it)
- **Why it's fun** (what makes it engaging)
- **Why it's intuitive** (why it's easy to understand)

**Requirements for all concepts:**
- User can **manually move items** between states
- Items start in a **holding state/backlog**
- Clear visual progress indicators
- Matches futuristic theme

### 2. Phase/State Design

What **states or phases** should items move through?

**Don't limit to traditional development phases** - think creatively!

Examples of different approaches:
- **Simple:** Todo → Doing → Done
- **Detailed:** Backlog → Prioritized → In Progress → Review → Approved → Released
- **Metaphorical:** Briefing → Planning → Executing → Debriefing → Archived
- **Creative:** Spark → Kindle → Flame → Blaze → Ember
- **Your own ideas?**

Propose what makes sense for multi-agent workflows.

### 3. "Fun Factor" Features

What would make this **delightful** to use?

**Brainstorm:**
- Animations (what should move/transform?)
- Sound effects (optional, toggleable)
- Visual feedback (glows, particles, trails)
- Celebrations (when tasks complete)
- Easter eggs or hidden details
- Gamification elements
- Other "juice" that makes UIs feel alive

### 4. Quick Win Analysis

What's the **simplest version** that still adds value?

**Criteria for quick win:**
- Implementable in 2-4 hours
- Provides immediate value
- Foundation for future enhancements
- Doesn't require complex animations

Then propose **evolution path** to full vision.

---

## Designs Agent Tasks

### 1. Visual Concepts (3-5 Mockups)

Create **detailed visual mockups** for your favorite concepts.

**Each mockup should show:**
- Overall layout and placement
- Color scheme (use futuristic theme)
- Typography and iconography
- States/phases visually differentiated
- Example of items in different states
- Interaction hints (drag here, click here, etc.)

**Format:** ASCII art, detailed description, or both

### 2. Animation & Transition Design

Specify all visual movement:

**State transitions:**
- How do items move between phases?
- Duration, easing, path
- Any intermediate effects?

**Feedback animations:**
- What happens when user clicks/drags?
- How to indicate "droppable" zones?
- Success/error visual feedback

**Ambient animations:**
- Subtle movements to show "liveness"
- Glows, pulses, particles
- What's always moving vs. on interaction?

### 3. Mobile Considerations

How does it work on small screens?

**Responsive design:**
- Collapse to simpler view?
- Swipe instead of drag?
- Bottom sheet or modal?
- Different layout entirely?

### 4. Information Density

What information should each item show?

**Minimal view:**
- Just enough to identify item
- Compact, scannable

**Detailed view:**
- Full information
- Expandable cards?
- Hover tooltips?

**Balance:** Information vs. visual clarity

### 5. Dark Mode Specifics

How do visuals adapt to dark theme?

**Considerations:**
- Neon glows more prominent in dark
- Border visibility
- Color contrast
- Readability

---

## Senior Engineer Tasks

### 1. Propose Technical Architecture

How would you build this?

**No constraints** - propose your ideal architecture:
- Frontend: Gradio components? Custom React? Other?
- Backend: Python state management? Database?
- Real-time: Polling? WebSockets? Events?
- Persistence: How to save state?

### 2. Data Model

Design the data structure for items and states.

**Consider:**
- What is an "item"? (Agent task? User-created task? Proposal?)
- What properties does an item have?
- How to represent state transitions?
- How to track history/audit trail?

**Example structure (modify as needed):**
```python
{
    "id": "task-123",
    "title": "Implement user authentication",
    "type": "feature",  # feature, bug, task, proposal
    "created_by": "PM agent",
    "current_phase": "backlog",
    "assigned_agents": ["Senior", "iOS", "Android"],
    "progress": 0,
    "created_at": "...",
    "history": [
        {"phase": "backlog", "timestamp": "...", "moved_by": "user"}
    ]
}
```

### 3. State Management

How to manage workflow state?

**Questions:**
- Where is state stored? (memory, file, database)
- How to handle concurrent edits?
- How to persist across sessions?
- How to sync with agent execution?

### 4. Integration Strategy

How does this integrate with existing platform?

**Integration points:**
- When agents run, do they create items automatically?
- Can agents move items between phases?
- How do agent outputs relate to items?
- Can users create items manually?

### 5. Performance & Scalability

What are the limits?

**Considerations:**
- Max number of items in system?
- Max number of phases?
- Animation performance with 100+ items?
- Memory usage?

---

## QA Agent Tasks

### 1. User Experience Validation

What makes a task management system **good**?

**Quality criteria:**
- Can users find items quickly?
- Is it obvious how to move items?
- Does it feel responsive?
- Is progress clear at a glance?
- Does it help or hinder workflow?

### 2. Edge Cases

What could go wrong?

**Scenarios to test:**
- User moves item to invalid state
- Two users edit same item simultaneously
- Item gets stuck between states
- Agent fails during execution
- User deletes item that's in progress
- System has 1000+ items

### 3. Accessibility Requirements

How to make it accessible to all users?

**WCAG 2.1 AA compliance:**
- Keyboard navigation (tab, arrows, enter)
- Screen reader support (ARIA labels)
- Color contrast (not just color for status)
- Focus indicators
- Reduced motion option

### 4. Usability Testing Plan

How would you test with real users?

**Test scenarios:**
- First-time user: Can they figure it out?
- Power user: Is it efficient?
- Error recovery: Can they fix mistakes?
- Mobile user: Does it work on phone?

**Success metrics:**
- Time to complete first task move: <10 seconds
- User satisfaction: 8/10+
- Confusion rate: <10%
- Daily active usage: High

---

## Memory Agent Tasks

### 1. Historical Context

What have we learned about UI/UX from past decisions?

**Review:**
- Why did we choose tabs over grid for agent outputs?
- Why did we implement YAML import as primary feature?
- What feedback did we get on previous UI changes?
- What patterns do users expect?

### 2. Pattern Recognition

What patterns should we continue?

**Established patterns:**
- Futuristic theme with neon accents
- Auto dark/light mode
- Glassmorphism effects
- Smooth animations
- Progressive disclosure

How should the progress system match these patterns?

### 3. User Expectations

Based on similar platforms, what do users expect?

**Common conventions:**
- Drag-and-drop for moving items
- Click to select/expand
- Double-click to edit
- Right-click for context menu
- Keyboard shortcuts for power users

Which conventions should we follow vs. break?

---

## Expected Output Format

### For Each Agent:

**1. Summary** (3-5 sentences)
Your main recommendation in plain language

**2. Detailed Proposals**
Present 3-5 concrete ideas, each with:
- Name/title
- Description
- Visual concept
- Why it's good
- Implementation effort (hours)
- Priority (High/Medium/Low)

**3. Recommended Approach**
Which idea do you think is best and why?

**4. Quick Win**
What can we ship in 2-4 hours that adds immediate value?

**5. Evolution Path**
How does quick win evolve into full vision?

---

## Important: Be Creative!

**We want YOUR ideas, not what you think we want to hear.**

- Propose unconventional approaches
- Challenge assumptions
- Think about what would be **fun** and **delightful**
- Don't limit yourself to what "normally" is done
- Be specific and detailed

---

## Success Criteria

Your evaluation succeeds if:

1. ✅ You propose **genuinely novel** ideas (not just Kanban board)
2. ✅ You consider **user experience** deeply
3. ✅ You provide **specific, actionable** recommendations
4. ✅ You think about **fun and engagement**, not just utility
5. ✅ All agents **converge** on a clear direction

---

## Ready?

Run this through your **Memory, Research, Ideas, Designs, Senior, QA** agents.

**Model preset:** Quality or Balanced (need creative thinking)

**Expected result:** A collection of creative, well-thought-out proposals for a task management system that makes multi-agent workflows **intuitive, fun, and engaging**.

**Remember:** The goal is to make users **love** using this platform!

Let your creativity flow! 🚀✨
