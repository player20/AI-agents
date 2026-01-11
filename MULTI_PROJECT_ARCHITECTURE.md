# Multi-Project & Multi-Team Architecture

This document outlines the architecture for adding multi-project and multi-team support to the Multi-Agent Development Team platform.

## Table of Contents

1. [Overview](#overview)
2. [Database Schema](#database-schema)
3. [User Flows](#user-flows)
4. [API Endpoints](#api-endpoints)
5. [UI Components](#ui-components)
6. [Implementation Plan](#implementation-plan)

---

## Overview

### What You'll Be Able To Do

**Projects (Workspaces)**:
- Create multiple projects under your account (e.g., "Mobile App", "API Redesign", "Marketing Campaign")
- Each project contains multiple workflows
- Archive/delete old projects
- Switch between projects easily

**Teams (Organizations)**:
- Create teams with multiple members
- Invite collaborators via email
- Assign roles (Owner, Admin, Editor, Viewer)
- Share projects with teams
- Team-level billing and usage tracking

**Workflows**:
- Save and organize workflows within projects
- Version history for workflows
- Template library (personal + team + public)
- Export/import workflows
- Workflow execution history

---

## Database Schema

### Recommended: Supabase PostgreSQL

Since you're already using Supabase for authentication (based on your other project), here's a Prisma schema for the MultiAgentTeam platform:

```prisma
// ============================================
// AUTHENTICATION & USERS
// ============================================

model User {
  id                String             @id @default(uuid())
  email             String             @unique
  name              String?
  avatarUrl         String?            @map("avatar_url")
  plan              UserPlan           @default(free)
  createdAt         DateTime           @default(now()) @map("created_at")
  updatedAt         DateTime           @updatedAt @map("updated_at")

  // Relations
  ownedTeams        Team[]             @relation("TeamOwner")
  teamMemberships   TeamMember[]
  projects          Project[]
  workflows         Workflow[]
  workflowRuns      WorkflowRun[]
  customAgents      CustomAgent[]

  @@map("users")
}

enum UserPlan {
  free
  pro
  team
  enterprise

  @@map("user_plan")
}

// ============================================
// TEAMS & COLLABORATION
// ============================================

model Team {
  id                String             @id @default(uuid())
  name              String
  slug              String             @unique
  description       String?
  logoUrl           String?            @map("logo_url")
  ownerId           String             @map("owner_id")
  plan              TeamPlan           @default(starter)
  createdAt         DateTime           @default(now()) @map("created_at")
  updatedAt         DateTime           @updatedAt @map("updated_at")

  // Relations
  owner             User               @relation("TeamOwner", fields: [ownerId], references: [id], onDelete: Cascade)
  members           TeamMember[]
  projects          Project[]
  invitations       TeamInvitation[]
  customAgents      CustomAgent[]

  @@index([ownerId])
  @@index([slug])
  @@map("teams")
}

enum TeamPlan {
  starter
  business
  enterprise

  @@map("team_plan")
}

model TeamMember {
  id                String             @id @default(uuid())
  teamId            String             @map("team_id")
  userId            String             @map("user_id")
  role              TeamRole
  joinedAt          DateTime           @default(now()) @map("joined_at")

  // Relations
  team              Team               @relation(fields: [teamId], references: [id], onDelete: Cascade)
  user              User               @relation(fields: [userId], references: [id], onDelete: Cascade)

  @@unique([teamId, userId])
  @@index([teamId])
  @@index([userId])
  @@map("team_members")
}

enum TeamRole {
  owner     // Full control, billing, delete team
  admin     // Manage members, projects, settings
  editor    // Create/edit workflows, run agents
  viewer    // Read-only access

  @@map("team_role")
}

model TeamInvitation {
  id                String             @id @default(uuid())
  teamId            String             @map("team_id")
  email             String
  role              TeamRole
  invitedBy         String             @map("invited_by")
  token             String             @unique
  expiresAt         DateTime           @map("expires_at")
  acceptedAt        DateTime?          @map("accepted_at")
  createdAt         DateTime           @default(now()) @map("created_at")

  // Relations
  team              Team               @relation(fields: [teamId], references: [id], onDelete: Cascade)

  @@index([token])
  @@index([teamId])
  @@index([email])
  @@map("team_invitations")
}

// ============================================
// PROJECTS & WORKFLOWS
// ============================================

model Project {
  id                String             @id @default(uuid())
  name              String
  description       String?
  color             String             @default("#4A90E2")
  icon              String             @default("📋")
  ownerId           String             @map("owner_id")
  teamId            String?            @map("team_id")
  visibility        ProjectVisibility  @default(private)
  archived          Boolean            @default(false)
  createdAt         DateTime           @default(now()) @map("created_at")
  updatedAt         DateTime           @updatedAt @map("updated_at")

  // Relations
  owner             User               @relation(fields: [ownerId], references: [id], onDelete: Cascade)
  team              Team?              @relation(fields: [teamId], references: [id], onDelete: Cascade)
  workflows         Workflow[]

  @@index([ownerId])
  @@index([teamId])
  @@index([archived])
  @@map("projects")
}

enum ProjectVisibility {
  private   // Only owner/team can see
  link      // Anyone with link can view
  public    // Listed publicly

  @@map("project_visibility")
}

model Workflow {
  id                String             @id @default(uuid())
  name              String
  description       String?
  projectId         String             @map("project_id")
  ownerId           String             @map("owner_id")
  version           Int                @default(1)
  isTemplate        Boolean            @default(false) @map("is_template")
  templateCategory  String?            @map("template_category")
  difficulty        WorkflowDifficulty @default(beginner)
  estimatedTime     String?            @map("estimated_time")
  estimatedCost     String?            @map("estimated_cost")
  tags              String[]

  // Workflow configuration (stored as JSON)
  configYaml        String             @map("config_yaml")
  nodesJson         Json               @map("nodes_json")
  edgesJson         Json               @map("edges_json")

  // Metadata
  starred           Boolean            @default(false)
  lastRunAt         DateTime?          @map("last_run_at")
  runCount          Int                @default(0) @map("run_count")
  createdAt         DateTime           @default(now()) @map("created_at")
  updatedAt         DateTime           @updatedAt @map("updated_at")

  // Relations
  project           Project            @relation(fields: [projectId], references: [id], onDelete: Cascade)
  owner             User               @relation(fields: [ownerId], references: [id], onDelete: Cascade)
  runs              WorkflowRun[]
  versions          WorkflowVersion[]

  @@index([projectId])
  @@index([ownerId])
  @@index([isTemplate])
  @@index([templateCategory])
  @@map("workflows")
}

enum WorkflowDifficulty {
  beginner
  intermediate
  advanced

  @@map("workflow_difficulty")
}

model WorkflowVersion {
  id                String             @id @default(uuid())
  workflowId        String             @map("workflow_id")
  version           Int
  configYaml        String             @map("config_yaml")
  nodesJson         Json               @map("nodes_json")
  edgesJson         Json               @map("edges_json")
  changeMessage     String?            @map("change_message")
  createdAt         DateTime           @default(now()) @map("created_at")

  // Relations
  workflow          Workflow           @relation(fields: [workflowId], references: [id], onDelete: Cascade)

  @@unique([workflowId, version])
  @@index([workflowId])
  @@map("workflow_versions")
}

model WorkflowRun {
  id                String             @id @default(uuid())
  workflowId        String             @map("workflow_id")
  userId            String             @map("user_id")
  status            WorkflowRunStatus
  startedAt         DateTime           @default(now()) @map("started_at")
  completedAt       DateTime?          @map("completed_at")

  // Execution data
  inputPrompt       String?            @map("input_prompt")
  agentOutputs      Json               @map("agent_outputs")
  executionLog      String?            @map("execution_log")
  errorMessage      String?            @map("error_message")

  // Usage tracking
  tokensUsed        Int                @default(0) @map("tokens_used")
  costUsd           Float              @default(0) @map("cost_usd")
  durationMs        Int?               @map("duration_ms")

  // Relations
  workflow          Workflow           @relation(fields: [workflowId], references: [id], onDelete: Cascade)
  user              User               @relation(fields: [userId], references: [id], onDelete: Cascade)

  @@index([workflowId])
  @@index([userId])
  @@index([status])
  @@index([startedAt])
  @@map("workflow_runs")
}

enum WorkflowRunStatus {
  pending
  running
  completed
  failed
  cancelled

  @@map("workflow_run_status")
}

// ============================================
// CUSTOM AGENTS
// ============================================

model CustomAgent {
  id                String             @id @default(uuid())
  label             String
  icon              String
  color             String
  category          String?
  defaultPrompt     String?            @map("default_prompt")
  ownerId           String?            @map("owner_id")
  teamId            String?            @map("team_id")
  visibility        AgentVisibility    @default(private)
  createdAt         DateTime           @default(now()) @map("created_at")
  updatedAt         DateTime           @updatedAt @map("updated_at")

  // Relations
  owner             User?              @relation(fields: [ownerId], references: [id], onDelete: Cascade)
  team              Team?              @relation(fields: [teamId], references: [id], onDelete: Cascade)

  @@index([ownerId])
  @@index([teamId])
  @@index([visibility])
  @@map("custom_agents")
}

enum AgentVisibility {
  private   // Only creator can use
  team      // Team members can use
  public    // Anyone can use (marketplace)

  @@map("agent_visibility")
}

// ============================================
// USAGE & BILLING
// ============================================

model UsageLog {
  id                String             @id @default(uuid())
  userId            String             @map("user_id")
  teamId            String?            @map("team_id")
  workflowRunId     String?            @map("workflow_run_id")
  modelUsed         String             @map("model_used")
  tokensUsed        Int                @map("tokens_used")
  costUsd           Float              @map("cost_usd")
  createdAt         DateTime           @default(now()) @map("created_at")

  @@index([userId, createdAt])
  @@index([teamId, createdAt])
  @@map("usage_logs")
}
```

---

## User Flows

### 1. Creating Your First Project

```
User logs in
  → Sees "Create Your First Project" welcome screen
  → Clicks "New Project"
  → Enters: Name, Description, Icon, Color
  → Project created
  → Redirected to empty project (shows "Create Workflow" button)
```

### 2. Organizing Multiple Projects

```
User has 5 projects:
  📱 Mobile App Redesign
  🌐 Website Refactor
  📊 Marketing Campaign
  🔒 Security Audit
  ✅ Bug Fixes (archived)

User switches between projects using:
  - Sidebar navigation
  - Quick switcher (Cmd/Ctrl + K)
  - Project dropdown in header
```

### 3. Creating a Team

```
User clicks "Create Team"
  → Enters team name, slug, description
  → Team created with user as Owner
  → User can now:
     - Invite members
     - Create team projects
     - Share custom agents with team
     - View team usage/billing
```

### 4. Inviting Team Members

```
Team Owner clicks "Invite Members"
  → Enters email addresses (comma-separated)
  → Selects role for each: Owner, Admin, Editor, Viewer
  → Clicks "Send Invitations"
  → System sends invitation emails
  → Recipients click link → Join team
```

### 5. Permission Levels

| Action | Owner | Admin | Editor | Viewer |
|--------|-------|-------|--------|--------|
| Delete team | ✅ | ❌ | ❌ | ❌ |
| Manage billing | ✅ | ❌ | ❌ | ❌ |
| Invite/remove members | ✅ | ✅ | ❌ | ❌ |
| Create projects | ✅ | ✅ | ✅ | ❌ |
| Edit workflows | ✅ | ✅ | ✅ | ❌ |
| Run workflows | ✅ | ✅ | ✅ | ❌ |
| View workflows | ✅ | ✅ | ✅ | ✅ |
| View execution history | ✅ | ✅ | ✅ | ✅ |

---

## API Endpoints

### Projects

```
POST   /api/projects                    Create project
GET    /api/projects                    List all projects
GET    /api/projects/:id                Get project details
PATCH  /api/projects/:id                Update project
DELETE /api/projects/:id                Delete project
POST   /api/projects/:id/archive        Archive project
POST   /api/projects/:id/restore        Restore archived project
```

### Teams

```
POST   /api/teams                       Create team
GET    /api/teams                       List user's teams
GET    /api/teams/:id                   Get team details
PATCH  /api/teams/:id                   Update team
DELETE /api/teams/:id                   Delete team

GET    /api/teams/:id/members           List team members
POST   /api/teams/:id/members/invite    Invite member
PATCH  /api/teams/:id/members/:userId   Update member role
DELETE /api/teams/:id/members/:userId   Remove member

GET    /api/teams/:id/projects          List team projects
```

### Workflows

```
POST   /api/workflows                   Create workflow
GET    /api/workflows                   List workflows (filtered by project)
GET    /api/workflows/:id               Get workflow details
PATCH  /api/workflows/:id               Update workflow
DELETE /api/workflows/:id               Delete workflow
POST   /api/workflows/:id/run           Execute workflow
GET    /api/workflows/:id/runs          Get execution history
GET    /api/workflows/:id/versions      Get version history
```

---

## UI Components

### 1. Project Switcher (Sidebar)

```
┌────────────────────────────┐
│ 🏠 Home                    │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━ │
│ PERSONAL                   │
│ > 📱 Mobile App            │ ← Active
│   🌐 Website Refactor      │
│   📊 Marketing Campaign    │
│                            │
│ + New Project              │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━ │
│ TEAMS                      │
│ > Acme Corp                │
│   - 🚀 Product Launch      │
│   - 🔒 Security Review     │
│                            │
│ + Create Team              │
└────────────────────────────┘
```

### 2. Project Header

```
┌────────────────────────────────────────────────────────┐
│ 📱 Mobile App Redesign              [⭐ Star] [⚙️ Settings] │
│ iOS and Android redesign for 2025                      │
│ ────────────────────────────────────────────────────── │
│ [Workflows] [Templates] [Runs] [Team] [Settings]      │
└────────────────────────────────────────────────────────┘
```

### 3. Workflow List (in Project)

```
┌──────────────────────────────────────────────────────────┐
│ Workflows                         [+ New] [📚 Templates] │
│ ──────────────────────────────────────────────────────── │
│ 🎨 UI/UX Research & Design                  Last run: 2h ago
│    Research → Ideas → Designs                    4 agents
│    ────────────────────────────────────────────────────
│ 🔍 Security Audit                          Last run: 1d ago
│    Senior → QA → Verifier                        3 agents
│    ────────────────────────────────────────────────────
│ ⚡ Full-Stack MVP                         Last run: 3d ago
│    PM → Research → Ideas → Designs...            7 agents
└──────────────────────────────────────────────────────────┘
```

### 4. Team Management

```
┌────────────────────────────────────────────────────────┐
│ Acme Corp Team Settings                                │
│ ────────────────────────────────────────────────────── │
│ [Members] [Projects] [Custom Agents] [Billing]         │
│ ────────────────────────────────────────────────────── │
│ MEMBERS (5)                          [+ Invite Members]│
│                                                        │
│ 👤 John Doe              Owner      john@acme.com      │
│ 👤 Jane Smith            Admin      jane@acme.com      │
│ 👤 Bob Johnson           Editor     bob@acme.com       │
│ 👤 Alice Williams        Viewer     alice@acme.com     │
│ ⏳ mike@acme.com         Invited (pending)             │
└────────────────────────────────────────────────────────┘
```

---

## Implementation Plan

### Phase 1: Database Setup (Week 1)

1. **Set up Supabase project**
   ```bash
   npm install @supabase/supabase-js
   npm install prisma @prisma/client
   ```

2. **Initialize Prisma**
   ```bash
   npx prisma init
   ```

3. **Create schema** (copy from above)

4. **Run migrations**
   ```bash
   npx prisma migrate dev --name init
   ```

5. **Generate Prisma client**
   ```bash
   npx prisma generate
   ```

### Phase 2: Backend API (Week 2-3)

**Technology Stack**:
- **Backend**: Node.js + Express (or FastAPI if you prefer Python)
- **Database**: Supabase PostgreSQL
- **ORM**: Prisma
- **Auth**: Supabase Auth

**File Structure**:
```
server/
├── src/
│   ├── routes/
│   │   ├── projects.js
│   │   ├── teams.js
│   │   ├── workflows.js
│   │   └── users.js
│   ├── middleware/
│   │   ├── auth.js
│   │   └── permissions.js
│   ├── services/
│   │   ├── projectService.js
│   │   ├── teamService.js
│   │   └── workflowService.js
│   └── app.js
├── prisma/
│   └── schema.prisma
└── package.json
```

### Phase 3: Frontend UI (Week 4-5)

**Add to React Workflow Builder**:

1. **Project Switcher Component**
   ```
   workflow_builder/src/components/ProjectSwitcher.js
   ```

2. **Team Management Component**
   ```
   workflow_builder/src/components/TeamManager.js
   ```

3. **Workflow List Component**
   ```
   workflow_builder/src/components/WorkflowList.js
   ```

4. **Update Navigation**
   - Add sidebar with project/team navigation
   - Add project context throughout app
   - Add team selection dropdown

### Phase 4: Integration (Week 6)

1. **Connect Workflow Builder to API**
   - Save workflows to database (not localStorage)
   - Load workflows from project
   - Sync custom agents to database

2. **Add Auth Flow**
   - Supabase authentication
   - Protected routes
   - JWT token handling

3. **Add Real-Time Features** (optional)
   - Supabase Realtime for collaborative editing
   - Live execution status updates
   - Team member presence indicators

### Phase 5: Testing & Polish (Week 7)

1. **Permission Testing**
   - Test all role permissions
   - Test project/team access controls

2. **Migration Tool**
   - Export localStorage data
   - Import to database

3. **Documentation**
   - User guide for teams
   - API documentation

---

## Quick Start Implementation

### Minimal Version (1-2 Days)

If you want to start simple:

**Just Projects (No Teams)**:

```prisma
model User {
  id        String    @id
  email     String
  projects  Project[]
}

model Project {
  id          String     @id
  name        String
  ownerId     String
  workflows   Workflow[]
  owner       User       @relation(fields: [ownerId], references: [id])
}

model Workflow {
  id          String  @id
  name        String
  projectId   String
  configYaml  String
  project     Project @relation(fields: [projectId], references: [id])
}
```

This gives you:
- ✅ Multiple projects per user
- ✅ Saved workflows
- ✅ Project organization
- ❌ No teams (add later)
- ❌ No permissions (add later)

---

## Next Steps

1. **Decide on scope**: Start with just Projects, or implement full Teams?
2. **Choose backend**: Node.js/Express or Python/FastAPI?
3. **Set up Supabase** project
4. **Implement database schema**
5. **Build API endpoints**
6. **Update React UI**

Would you like me to start implementing any specific part of this architecture?
