# Project & Agent Teams Architecture

## Concept

**Projects** contain multiple **Agent Teams**, where each agent team is a specialized group of AI agents working on a specific aspect of the project.

### Example Project Structure

```
📦 Project: "E-commerce Platform MVP"
│
├── 🔧 Agent Team: "Backend Squad"
│   ├── Senior Engineer
│   ├── Backend Architect
│   └── Data Architect
│
├── 🎨 Agent Team: "Frontend Squad"
│   ├── Designs
│   ├── Web Developer
│   ├── iOS Developer
│   └── Android Developer
│
├── ✅ Agent Team: "Quality Squad"
│   ├── QA Engineer
│   ├── Security Specialist
│   └── Verifier
│
└── 📊 Agent Team: "Product Squad"
    ├── Product Manager
    ├── Research
    └── Marketing
```

---

## Database Schema

```prisma
generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

// ============================================
// USERS & AUTHENTICATION
// ============================================

model User {
  id              String           @id @default(uuid())
  email           String           @unique
  name            String?
  avatarUrl       String?          @map("avatar_url")
  createdAt       DateTime         @default(now()) @map("created_at")
  updatedAt       DateTime         @updatedAt @map("updated_at")

  // Relations
  projects        Project[]
  customAgents    CustomAgent[]

  @@map("users")
}

// ============================================
// PROJECTS
// ============================================

model Project {
  id              String           @id @default(uuid())
  name            String
  description     String?
  icon            String           @default("📦")
  color           String           @default("#4A90E2")
  ownerId         String           @map("owner_id")
  status          ProjectStatus    @default(active)
  archived        Boolean          @default(false)
  createdAt       DateTime         @default(now()) @map("created_at")
  updatedAt       DateTime         @updatedAt @map("updated_at")

  // Relations
  owner           User             @relation(fields: [ownerId], references: [id], onDelete: Cascade)
  agentTeams      AgentTeam[]
  executions      ProjectExecution[]

  @@index([ownerId])
  @@index([status])
  @@map("projects")
}

enum ProjectStatus {
  planning
  active
  on_hold
  completed
  archived

  @@map("project_status")
}

// ============================================
// AGENT TEAMS
// ============================================

model AgentTeam {
  id              String           @id @default(uuid())
  name            String
  description     String?
  icon            String           @default("👥")
  color           String           @default("#6366F1")
  projectId       String           @map("project_id")
  executionOrder  Int              @default(0) @map("execution_order")
  isActive        Boolean          @default(true) @map("is_active")
  createdAt       DateTime         @default(now()) @map("created_at")
  updatedAt       DateTime         @updatedAt @map("updated_at")

  // Relations
  project         Project          @relation(fields: [projectId], references: [id], onDelete: Cascade)
  members         AgentTeamMember[]

  @@index([projectId])
  @@index([projectId, executionOrder])
  @@map("agent_teams")
}

model AgentTeamMember {
  id              String           @id @default(uuid())
  agentTeamId     String           @map("agent_team_id")
  agentId         String           @map("agent_id")
  customPrompt    String?          @map("custom_prompt")
  model           String           @default("claude-3-5-sonnet-20241022")
  executionOrder  Int              @default(0) @map("execution_order")
  isActive        Boolean          @default(true) @map("is_active")
  createdAt       DateTime         @default(now()) @map("created_at")

  // Relations
  agentTeam       AgentTeam        @relation(fields: [agentTeamId], references: [id], onDelete: Cascade)

  @@index([agentTeamId])
  @@index([agentTeamId, executionOrder])
  @@map("agent_team_members")
}

// ============================================
// CUSTOM AGENTS
// ============================================

model CustomAgent {
  id              String           @id @default(uuid())
  label           String
  icon            String
  color           String
  category        String?
  defaultPrompt   String?          @map("default_prompt")
  ownerId         String           @map("owner_id")
  isPublic        Boolean          @default(false) @map("is_public")
  createdAt       DateTime         @default(now()) @map("created_at")
  updatedAt       DateTime         @updatedAt @map("updated_at")

  // Relations
  owner           User             @relation(fields: [ownerId], references: [id], onDelete: Cascade)

  @@index([ownerId])
  @@index([isPublic])
  @@map("custom_agents")
}

// ============================================
// PROJECT EXECUTION
// ============================================

model ProjectExecution {
  id              String                  @id @default(uuid())
  projectId       String                  @map("project_id")
  status          ProjectExecutionStatus
  startedAt       DateTime                @default(now()) @map("started_at")
  completedAt     DateTime?               @map("completed_at")
  totalDurationMs Int?                    @map("total_duration_ms")
  totalTokens     Int                     @default(0) @map("total_tokens")
  totalCost       Float                   @default(0) @map("total_cost")
  errorMessage    String?                 @map("error_message")

  // Relations
  project         Project                 @relation(fields: [projectId], references: [id], onDelete: Cascade)
  teamExecutions  AgentTeamExecution[]

  @@index([projectId])
  @@index([status])
  @@index([startedAt])
  @@map("project_executions")
}

enum ProjectExecutionStatus {
  pending
  running
  completed
  failed
  cancelled

  @@map("project_execution_status")
}

model AgentTeamExecution {
  id                String                  @id @default(uuid())
  projectExecutionId String                 @map("project_execution_id")
  agentTeamId       String                  @map("agent_team_id")
  status            AgentTeamExecutionStatus
  startedAt         DateTime                @default(now()) @map("started_at")
  completedAt       DateTime?               @map("completed_at")
  durationMs        Int?                    @map("duration_ms")
  tokensUsed        Int                     @default(0) @map("tokens_used")
  cost              Float                   @default(0)
  output            String?
  errorMessage      String?                 @map("error_message")

  // Relations
  projectExecution  ProjectExecution        @relation(fields: [projectExecutionId], references: [id], onDelete: Cascade)
  agentExecutions   AgentExecution[]

  @@index([projectExecutionId])
  @@index([agentTeamId])
  @@map("agent_team_executions")
}

enum AgentTeamExecutionStatus {
  pending
  running
  completed
  failed
  skipped

  @@map("agent_team_execution_status")
}

model AgentExecution {
  id                    String                 @id @default(uuid())
  agentTeamExecutionId  String                 @map("agent_team_execution_id")
  agentId               String                 @map("agent_id")
  agentLabel            String                 @map("agent_label")
  status                AgentExecutionStatus
  startedAt             DateTime               @default(now()) @map("started_at")
  completedAt           DateTime?              @map("completed_at")
  durationMs            Int?                   @map("duration_ms")
  tokensUsed            Int                    @default(0) @map("tokens_used")
  cost                  Float                  @default(0)
  model                 String
  input                 String?
  output                String?
  errorMessage          String?                @map("error_message")

  // Relations
  agentTeamExecution    AgentTeamExecution     @relation(fields: [agentTeamExecutionId], references: [id], onDelete: Cascade)

  @@index([agentTeamExecutionId])
  @@map("agent_executions")
}

enum AgentExecutionStatus {
  pending
  running
  completed
  failed

  @@map("agent_execution_status")
}
```

---

## User Interface

### 1. Project Dashboard

```
┌────────────────────────────────────────────────────────────┐
│ 📦 E-commerce Platform MVP                    [▶️ Run All] │
│ Building a full-stack e-commerce platform                 │
│ ──────────────────────────────────────────────────────────│
│ Status: Active  │  4 Agent Teams  │  Last run: 2h ago     │
└────────────────────────────────────────────────────────────┘

AGENT TEAMS

┌─────────────────────────────────────────────────────┐
│ 🔧 Backend Squad                        [⚙️] [▶️]    │
│ ───────────────────────────────────────────────────│
│ • Senior Engineer                                  │
│ • Backend Architect                                │
│ • Data Architect                                   │
│                                                    │
│ Last run: 2h ago  │  Status: ✅ Completed          │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ 🎨 Frontend Squad                       [⚙️] [▶️]    │
│ ───────────────────────────────────────────────────│
│ • Designs                                          │
│ • Web Developer                                    │
│ • iOS Developer                                    │
│ • Android Developer                                │
│                                                    │
│ Last run: 2h ago  │  Status: ✅ Completed          │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ ✅ Quality Squad                        [⚙️] [▶️]    │
│ ───────────────────────────────────────────────────│
│ • QA Engineer                                      │
│ • Security Specialist                              │
│ • Verifier                                         │
│                                                    │
│ Last run: 2h ago  │  Status: ✅ Completed          │
└─────────────────────────────────────────────────────┘

[+ Add Agent Team]
```

### 2. Create Agent Team Modal

```
┌────────────────────────────────────────────┐
│ Create Agent Team                          │
│ ──────────────────────────────────────────│
│                                            │
│ Team Name:                                 │
│ [Frontend Squad                         ]  │
│                                            │
│ Description:                               │
│ [Build UI/UX for web and mobile apps   ]  │
│                                            │
│ Icon:  [🎨]   Color:  [#E74C3C]           │
│                                            │
│ SELECT AGENTS                              │
│                                            │
│ [✓] 🎨 Designs                             │
│ [✓] 🌐 Web Developer                       │
│ [✓] 📱 iOS Developer                       │
│ [✓] 🤖 Android Developer                   │
│ [ ] 👨‍💻 Senior Engineer                    │
│ [ ] ✅ QA Engineer                          │
│                                            │
│ Execution Order:                           │
│ 1. Designs                                 │
│ 2. Web Developer                           │
│ 3. iOS Developer                           │
│ 4. Android Developer                       │
│                                            │
│ [Drag to reorder agents]                   │
│                                            │
│          [Cancel]  [Create Team]           │
└────────────────────────────────────────────┘
```

### 3. Real-Time Execution View

```
┌────────────────────────────────────────────────────────────┐
│ ▶️ Running: E-commerce Platform MVP                        │
│ ──────────────────────────────────────────────────────────│
│ Progress: 2/4 teams completed                             │
│ [████████████████░░░░░░░░] 50%                            │
└────────────────────────────────────────────────────────────┘

✅ Backend Squad (Completed - 3m 24s)
   ✅ Senior Engineer (45s) - Reviewed architecture...
   ✅ Backend Architect (1m 12s) - Designed API endpoints...
   ✅ Data Architect (1m 27s) - Created database schema...

✅ Frontend Squad (Completed - 4m 18s)
   ✅ Designs (1m 5s) - Created UI mockups...
   ✅ Web Developer (1m 20s) - Built React components...
   ✅ iOS Developer (58s) - Generated SwiftUI code...
   ✅ Android Developer (55s) - Built Compose UI...

🔄 Quality Squad (Running - 1m 12s)
   ⏳ QA Engineer (pending)
   ⏳ Security Specialist (pending)
   ⏳ Verifier (pending)

⏸️ Product Squad (Pending)
   ⏳ Product Manager
   ⏳ Research
   ⏳ Marketing
```

---

## Execution Flow

### Sequential Team Execution

```python
# When user clicks "Run All" on project

1. Get all agent teams in project (ordered by executionOrder)
2. For each agent team:
   a. Get all agents in team (ordered by executionOrder)
   b. For each agent in team:
      - Execute agent with project context
      - Pass previous agent outputs as context
      - Update UI with real-time status
   c. Mark team as completed
3. Compile all team outputs
4. Show final results
```

### Example Flow

```
Project: "Build Landing Page"

Team 1: Research Squad (executes first)
  └─ Research Agent → Analyzes competitors
  └─ Ideas Agent → Generates feature ideas
  └─ OUTPUT: Market analysis + feature list

Team 2: Design Squad (uses Team 1 output)
  └─ Designs Agent → Creates mockups
  └─ OUTPUT: Figma designs + component specs

Team 3: Development Squad (uses Team 1 + 2 output)
  └─ Web Developer → Builds React components
  └─ Senior Engineer → Reviews code quality
  └─ OUTPUT: Production-ready code

Team 4: Quality Squad (uses all previous outputs)
  └─ QA Engineer → Tests functionality
  └─ Security → Audits for vulnerabilities
  └─ Verifier → Final quality check
  └─ OUTPUT: Test report + deployment checklist
```

---

## Implementation Steps

### Step 1: Update Workflow Builder UI

**Add "Projects" view:**
```
workflow_builder/src/pages/Projects.js
workflow_builder/src/pages/ProjectDetail.js
workflow_builder/src/components/AgentTeamCard.js
workflow_builder/src/components/CreateAgentTeamModal.js
```

### Step 2: Backend API

```javascript
// Express.js routes

// Projects
POST   /api/projects                    // Create project
GET    /api/projects                    // List all projects
GET    /api/projects/:id                // Get project with teams
PATCH  /api/projects/:id                // Update project
DELETE /api/projects/:id                // Delete project

// Agent Teams
POST   /api/projects/:id/teams          // Create agent team
GET    /api/projects/:id/teams          // List agent teams
PATCH  /api/teams/:id                   // Update agent team
DELETE /api/teams/:id                   // Delete agent team
POST   /api/teams/:id/members           // Add agent to team
DELETE /api/teams/:id/members/:agentId  // Remove agent from team

// Execution
POST   /api/projects/:id/execute        // Run entire project
POST   /api/teams/:id/execute           // Run single team
GET    /api/executions/:id              // Get execution status (SSE)
```

### Step 3: Execution Engine

```python
# Python execution engine (connects to Gradio app)

class ProjectExecutor:
    def __init__(self, project_id):
        self.project_id = project_id
        self.teams = load_agent_teams(project_id)

    async def execute(self):
        """Execute all agent teams sequentially"""
        results = {}

        for team in sorted(self.teams, key=lambda t: t.execution_order):
            print(f"🔄 Executing {team.name}...")
            team_result = await self.execute_team(team, results)
            results[team.id] = team_result

        return results

    async def execute_team(self, team, previous_results):
        """Execute all agents in a team"""
        team_outputs = []

        # Build context from previous team outputs
        context = self.build_context(previous_results)

        for agent in sorted(team.members, key=lambda a: a.execution_order):
            output = await self.execute_agent(agent, context)
            team_outputs.append(output)
            context += f"\n\n{agent.label} output:\n{output}"

        return "\n\n".join(team_outputs)
```

### Step 4: Real-Time Updates (WebSocket)

```javascript
// Client-side (React)
const ws = new WebSocket('ws://localhost:8080/execution');

ws.onmessage = (event) => {
  const update = JSON.parse(event.data);

  switch(update.type) {
    case 'team_started':
      updateTeamStatus(update.teamId, 'running');
      break;
    case 'agent_started':
      updateAgentStatus(update.agentId, 'running');
      break;
    case 'agent_completed':
      updateAgentStatus(update.agentId, 'completed');
      appendAgentOutput(update.agentId, update.output);
      break;
    case 'team_completed':
      updateTeamStatus(update.teamId, 'completed');
      break;
  }
};
```

---

## Migration from Current System

### Current (Single Workflow)
```yaml
agents:
  - PM
  - Research
  - Ideas
  - Senior
  - Web
  - QA
```

### New (Project with Agent Teams)
```json
{
  "project": {
    "name": "Build App",
    "agentTeams": [
      {
        "name": "Planning Team",
        "agents": ["PM", "Research", "Ideas"]
      },
      {
        "name": "Development Team",
        "agents": ["Senior", "Web"]
      },
      {
        "name": "QA Team",
        "agents": ["QA"]
      }
    ]
  }
}
```

---

## Benefits of This Architecture

✅ **Better Organization**: Group related agents together
✅ **Parallel Execution**: Run multiple teams concurrently (future)
✅ **Reusable Teams**: Save team configurations as templates
✅ **Clear Context Flow**: Each team builds on previous team outputs
✅ **Scalability**: Add/remove teams without affecting others
✅ **Visibility**: See which team is responsible for each output

---

Ready to implement this? I can:
1. Set up the database schema
2. Create the Project & Agent Teams UI
3. Build the execution engine
4. Add real-time status updates

Which part would you like to start with?
