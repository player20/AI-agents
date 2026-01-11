# Human-in-the-Loop: Approval Checkpoints

## Overview

Add **approval gates** where humans can review, approve, deny, or edit agent outputs before execution continues to the next step.

---

## User Flow

```
Agent Team 1 executes
      ↓
  Output produced
      ↓
┌─────────────────────┐
│  CHECKPOINT ⏸️       │
│  Human Review       │
│                     │
│  [Approve ✅]       │
│  [Deny ❌]          │
│  [Edit ✏️]          │
│  [Skip ⏭️]          │
└─────────────────────┘
      ↓
   Decision
      ↓
┌───────┬───────┬───────┐
│       │       │       │
✅      ❌      ✏️      ⏭️
Approve Deny   Edit   Skip
│       │       │       │
Continue Stop   Modify Continue
next    exec    output  without
team                    approval
```

---

## Checkpoint Types

### 1. **Team Completion Checkpoint**

After each agent team finishes, pause for review:

```
🔧 Backend Squad (Completed)
   Output: Database schema + API design

┌────────────────────────────────────────────┐
│ 🛑 CHECKPOINT: Review Backend Output       │
├────────────────────────────────────────────┤
│                                            │
│ The Backend Squad has completed.           │
│                                            │
│ OUTPUT PREVIEW:                            │
│ ┌────────────────────────────────────────┐│
│ │ Database Schema:                       ││
│ │ - users table                          ││
│ │ - projects table                       ││
│ │ - agent_teams table                    ││
│ │                                        ││
│ │ API Endpoints:                         ││
│ │ POST /api/projects                     ││
│ │ GET  /api/projects/:id                 ││
│ │ ...                                    ││
│ └────────────────────────────────────────┘│
│                                            │
│ [📄 View Full Output] [📊 View Metrics]    │
│                                            │
│ What would you like to do?                 │
│                                            │
│ ┌────────┐ ┌────────┐ ┌────────┐ ┌──────┐│
│ │ ✅ Approve│ │ ❌ Deny │ │ ✏️ Edit │ │⏭️Skip││
│ └────────┘ └────────┘ └────────┘ └──────┘│
│                                            │
│ Next up: Frontend Squad (4 agents)         │
└────────────────────────────────────────────┘
```

### 2. **Critical Agent Checkpoint**

Pause after specific critical agents:

```yaml
# In workflow configuration
agent_teams:
  - name: "Architecture Team"
    agents:
      - Senior Engineer
      - Backend Architect    # ← Checkpoint after this
    checkpoints:
      - after_agent: "Backend Architect"
        required: true
        prompt: "Review the proposed architecture before proceeding"
```

### 3. **Conditional Checkpoint**

Trigger checkpoint based on conditions:

```yaml
checkpoints:
  - condition: "output_length > 5000"
    prompt: "This output is very long. Please review before continuing."

  - condition: "contains_code_changes"
    prompt: "Code changes detected. Review before deployment team runs."

  - condition: "cost > $2.00"
    prompt: "Execution cost exceeded $2. Approve to continue?"
```

---

## Actions at Checkpoints

### ✅ Approve

Continue to next team with original output.

```
User clicks [Approve]
  → Execution continues
  → Frontend Squad receives Backend Squad output unchanged
  → No modifications
```

### ❌ Deny (Reject)

Stop execution and provide feedback.

```
┌────────────────────────────────────────────┐
│ ❌ Deny Execution                          │
├────────────────────────────────────────────┤
│                                            │
│ Why are you denying this output?           │
│ ┌──────────────────────────────────────┐  │
│ │ The database schema is missing user  │  │
│ │ authentication tables. Need to add   │  │
│ │ auth tables before proceeding.       │  │
│ └──────────────────────────────────────┘  │
│                                            │
│ What happens next?                         │
│ ○ Stop execution entirely                  │
│ ● Re-run Backend Squad with feedback       │
│ ○ Skip to next team anyway                 │
│                                            │
│ [Cancel] [Confirm Denial]                  │
└────────────────────────────────────────────┘

After denial:
  → Backend Squad re-runs with user feedback
  → Original output replaced
  → New checkpoint after re-run
```

### ✏️ Edit Output

Modify the agent output before passing to next team.

```
┌────────────────────────────────────────────────────────┐
│ ✏️ Edit Output                                         │
├────────────────────────────────────────────────────────┤
│                                                        │
│ ORIGINAL OUTPUT (from Backend Squad):                  │
│ ┌────────────────────────────────────────────────────┐│
│ │ Database Schema:                                   ││
│ │ CREATE TABLE users (                               ││
│ │   id UUID PRIMARY KEY,                             ││
│ │   email VARCHAR(255) UNIQUE,                       ││
│ │   name VARCHAR(255)                                ││
│ │ );                                                 ││
│ │                                                    ││
│ │ CREATE TABLE projects (                            ││
│ │   id UUID PRIMARY KEY,                             ││
│ │   name VARCHAR(255),                               ││
│ │   owner_id UUID REFERENCES users(id)               ││
│ │ );                                                 ││
│ └────────────────────────────────────────────────────┘│
│                                                        │
│ [✨ AI Assist] [💾 Save as Draft] [↩️ Revert Changes] │
│                                                        │
│ EDIT MODE (make your changes):                        │
│ ┌────────────────────────────────────────────────────┐│
│ │ Database Schema:                                   ││
│ │ CREATE TABLE users (                               ││
│ │   id UUID PRIMARY KEY,                             ││
│ │   email VARCHAR(255) UNIQUE NOT NULL,  ← EDITED    ││
│ │   name VARCHAR(255),                               ││
│ │   password_hash VARCHAR(255) NOT NULL, ← ADDED     ││
│ │   created_at TIMESTAMP DEFAULT NOW()   ← ADDED     ││
│ │ );                                                 ││
│ │                                                    ││
│ │ CREATE TABLE projects (                            ││
│ │   id UUID PRIMARY KEY,                             ││
│ │   name VARCHAR(255) NOT NULL,          ← EDITED    ││
│ │   owner_id UUID REFERENCES users(id),              ││
│ │   created_at TIMESTAMP DEFAULT NOW()   ← ADDED     ││
│ │ );                                                 ││
│ └────────────────────────────────────────────────────┘│
│                                                        │
│ Changes made: 5 additions, 2 modifications             │
│                                                        │
│ [Cancel] [Save & Continue]                             │
└────────────────────────────────────────────────────────┘

After edit:
  → Modified output saved
  → Frontend Squad receives EDITED version
  → Original saved in version history
```

### ⏭️ Skip Checkpoint

Continue without approval (for trusted workflows).

```
User clicks [Skip]
  → Execution continues immediately
  → No human review
  → Useful for repetitive/trusted workflows
```

---

## Database Schema Addition

```prisma
model Checkpoint {
  id                  String              @id @default(uuid())
  projectExecutionId  String              @map("project_execution_id")
  agentTeamId         String?             @map("agent_team_id")
  agentId             String?             @map("agent_id")
  status              CheckpointStatus
  originalOutput      String              @map("original_output")
  editedOutput        String?             @map("edited_output")
  decision            CheckpointDecision?
  feedback            String?
  decidedAt           DateTime?           @map("decided_at")
  decidedBy           String?             @map("decided_by")
  createdAt           DateTime            @default(now()) @map("created_at")

  // Relations
  projectExecution    ProjectExecution    @relation(fields: [projectExecutionId], references: [id], onDelete: Cascade)

  @@index([projectExecutionId])
  @@index([status])
  @@map("checkpoints")
}

enum CheckpointStatus {
  pending
  approved
  denied
  edited
  skipped
  expired

  @@map("checkpoint_status")
}

enum CheckpointDecision {
  approve
  deny
  edit
  skip

  @@map("checkpoint_decision")
}

model CheckpointConfig {
  id                String                    @id @default(uuid())
  agentTeamId       String?                   @map("agent_team_id")
  triggerType       CheckpointTrigger         @map("trigger_type")
  triggerCondition  String?                   @map("trigger_condition")
  promptMessage     String                    @map("prompt_message")
  isRequired        Boolean                   @default(true) @map("is_required")
  timeoutMinutes    Int?                      @map("timeout_minutes")
  createdAt         DateTime                  @default(now()) @map("created_at")

  @@index([agentTeamId])
  @@map("checkpoint_configs")
}

enum CheckpointTrigger {
  after_team
  after_agent
  on_condition
  before_critical_action

  @@map("checkpoint_trigger")
}
```

---

## API Endpoints

```
POST   /api/executions/:id/checkpoints        Create checkpoint
GET    /api/executions/:id/checkpoints        List checkpoints
GET    /api/checkpoints/:id                   Get checkpoint details
PATCH  /api/checkpoints/:id/approve           Approve and continue
PATCH  /api/checkpoints/:id/deny              Deny with feedback
PATCH  /api/checkpoints/:id/edit              Edit output and continue
PATCH  /api/checkpoints/:id/skip              Skip and continue

# Real-time notifications
GET    /api/checkpoints/pending (SSE)         Stream pending checkpoints
```

---

## Real-Time Notifications

### WebSocket Events

```javascript
// Server sends to client
{
  type: 'checkpoint_created',
  checkpoint: {
    id: 'ckpt-123',
    teamName: 'Backend Squad',
    outputPreview: 'Database schema: users, projects...',
    createdAt: '2025-01-11T12:00:00Z'
  }
}

// Client responds with decision
{
  type: 'checkpoint_decision',
  checkpointId: 'ckpt-123',
  decision: 'approve'  // or 'deny', 'edit', 'skip'
}
```

### Email Notifications

```
Subject: 🛑 Approval Required: E-commerce MVP Backend Squad

Hi Jacob,

Your workflow "E-commerce MVP" is paused and waiting for your approval.

**Team:** Backend Squad (3 agents)
**Status:** Completed successfully
**Output:** Database schema + API design (2,453 tokens)

**Next Step:** Frontend Squad will use this output to build UI

[Review & Approve] [View in Dashboard]

---
Multi-Agent Development Team
```

---

## UI Component: Checkpoint Modal

```javascript
function CheckpointModal({ checkpoint, onDecision }) {
  const [decision, setDecision] = useState(null);
  const [feedback, setFeedback] = useState('');
  const [editedOutput, setEditedOutput] = useState(checkpoint.originalOutput);

  const handleApprove = () => {
    onDecision({
      checkpointId: checkpoint.id,
      decision: 'approve'
    });
  };

  const handleDeny = () => {
    onDecision({
      checkpointId: checkpoint.id,
      decision: 'deny',
      feedback
    });
  };

  const handleEdit = () => {
    onDecision({
      checkpointId: checkpoint.id,
      decision: 'edit',
      editedOutput
    });
  };

  return (
    <Modal isOpen={true} size="large">
      <ModalHeader>
        🛑 Checkpoint: Review {checkpoint.teamName} Output
      </ModalHeader>

      <ModalBody>
        <OutputPreview content={checkpoint.originalOutput} />

        <ButtonGroup>
          <Button onClick={handleApprove} color="success">
            ✅ Approve & Continue
          </Button>
          <Button onClick={() => setDecision('deny')} color="danger">
            ❌ Deny
          </Button>
          <Button onClick={() => setDecision('edit')} color="primary">
            ✏️ Edit Output
          </Button>
          <Button onClick={() => onDecision({ decision: 'skip' })}>
            ⏭️ Skip Checkpoint
          </Button>
        </ButtonGroup>

        {decision === 'deny' && (
          <FeedbackBox
            value={feedback}
            onChange={setFeedback}
            onSubmit={handleDeny}
          />
        )}

        {decision === 'edit' && (
          <Editor
            value={editedOutput}
            onChange={setEditedOutput}
            onSave={handleEdit}
          />
        )}
      </ModalBody>
    </Modal>
  );
}
```

---

## Smart Features

### 1. **Auto-Approve Patterns**

Learn from user behavior and auto-approve similar checkpoints:

```
User has approved Backend Squad checkpoints 15 times in a row
  → System suggests: "Auto-approve Backend Squad checkpoints?"
  → User enables auto-approval
  → Future Backend Squad checkpoints auto-approved
  → User can still override individual checkpoints
```

### 2. **AI Review Assistant**

AI analyzes output and flags potential issues:

```
┌────────────────────────────────────────────┐
│ 🤖 AI Review Assistant                     │
├────────────────────────────────────────────┤
│ I've analyzed the Backend Squad output:    │
│                                            │
│ ✅ Database schema looks good              │
│ ✅ API endpoints follow REST conventions   │
│ ⚠️ Missing authentication endpoints        │
│ ⚠️ No rate limiting mentioned              │
│ ❌ Security audit findings not addressed   │
│                                            │
│ Recommendation: Deny and request revisions │
└────────────────────────────────────────────┘
```

### 3. **Checkpoint Templates**

Save checkpoint configurations as templates:

```yaml
name: "Security Review Checkpoint"
trigger: after_team
team: "Backend Squad"
required: true
prompt: "Ensure security best practices are followed"
ai_review_enabled: true
timeout: 24_hours
```

---

## Mobile App Support

### Push Notifications

```
📱 Notification

🛑 Approval Needed
E-commerce MVP

Backend Squad completed
Tap to review output

[View] [Approve] [Deny]
```

### Quick Actions

```
Long press notification:
  - ✅ Quick Approve
  - ❌ Quick Deny
  - 📱 Open App
  - 🔕 Snooze 1 hour
```

---

## Implementation Priority

### Phase 1 (MVP):
1. Basic checkpoints after each team
2. Approve/Deny actions
3. Email notifications

### Phase 2:
4. Edit output functionality
5. WebSocket real-time updates
6. Mobile push notifications

### Phase 3:
7. AI review assistant
8. Auto-approve patterns
9. Conditional checkpoints

---

Would you like me to implement any of these checkpoint features? We can start with the basic approve/deny flow and build up from there.
