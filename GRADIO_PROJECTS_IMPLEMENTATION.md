# Gradio Projects & Teams Implementation Plan

## Overview
Add Projects & Teams functionality to Gradio UI to provide fast project configuration and multi-team sequential execution with human approval checkpoints.

## Architecture

### 1. Storage Layer
**File**: `projects_store.py` ✅ CREATED

**Key Classes**:
- `ProjectsStore`: Manages projects with JSON persistence
- `PROJECT_TEMPLATES`: 6 pre-built project templates

**Features**:
- CRUD operations for projects and teams
- Context passing between teams
- JSON file storage (`gradio_projects.json`)

### 2. UI Structure
**File**: `multi_agent_team.py` (modifications needed)

**New Tab-Based Layout**:
```python
with gr.Blocks(title="Super Dev Team") as demo:
    gr.Markdown("# 🚀 Super Multi-Agent Dev Team")

    with gr.Tabs():
        # TAB 1: PROJECTS & TEAMS (NEW)
        with gr.TabItem("📁 Projects & Teams"):
            # Projects list
            # New project form
            # Team builder
            # Template library
            # Sequential execution with checkpoints

        # TAB 2: QUICK RUN (EXISTING)
        with gr.TabItem("⚡ Quick Run"):
            # Keep existing single-execution UI
            # Project input, agent selection, run button
```

### 3. Projects & Teams Tab Components

#### 3.1 Project Management Section
```python
with gr.Row():
    with gr.Column(scale=2):
        gr.Markdown("## 📋 Your Projects")

        # Project list (dropdown or radio group)
        project_selector = gr.Dropdown(
            choices=[],  # Populated dynamically
            label="Select Project",
            allow_custom_value=False
        )

        # Project details display
        project_details = gr.Markdown(value="No project selected")

        with gr.Row():
            new_project_btn = gr.Button("➕ New Project", size="sm")
            delete_project_btn = gr.Button("🗑️ Delete Project", size="sm", variant="stop")

    with gr.Column(scale=3):
        gr.Markdown("## 🎯 Project Execution")

        # Execution status display
        execution_status = gr.HTML(value="<p>No execution running</p>")

        # Run project button
        run_project_btn = gr.Button("▶️ Run Project", variant="primary", size="lg")
```

#### 3.2 New Project Form (Hidden by default, shown on button click)
```python
with gr.Group(visible=False) as new_project_form:
    gr.Markdown("### Create New Project")

    # Template selection
    template_selector = gr.Dropdown(
        choices=["Blank Project"] + get_template_names(),
        value="Blank Project",
        label="Start from Template",
        info="Choose a template or start blank"
    )

    # Project info
    project_name_input = gr.Textbox(
        label="Project Name",
        placeholder="My Awesome Project"
    )

    project_desc_input = gr.Textbox(
        label="Project Description",
        lines=3,
        placeholder="Describe what you want to build..."
    )

    with gr.Row():
        create_project_btn = gr.Button("Create Project", variant="primary")
        cancel_project_btn = gr.Button("Cancel")
```

#### 3.3 Team Builder
```python
with gr.Group() as team_builder:
    gr.Markdown("### Teams")
    gr.Markdown("Teams execute sequentially with approval checkpoints between each team")

    # Teams list for selected project
    teams_display = gr.HTML(value="<p>No teams added yet</p>")

    # Add team form
    with gr.Accordion("➕ Add New Team", open=False):
        team_name_input = gr.Textbox(
            label="Team Name",
            placeholder="Backend Squad"
        )

        team_desc_input = gr.Textbox(
            label="Team Description",
            lines=2,
            placeholder="Describe what this team will do..."
        )

        team_agents_selector = gr.CheckboxGroup(
            choices=AGENT_ROLES,  # All 52 agents
            label="Select Agents for this Team",
            info="These agents will execute sequentially"
        )

        add_team_btn = gr.Button("Add Team", variant="primary")
```

#### 3.4 Checkpoint Modal (for approval between teams)
```python
with gr.Group(visible=False) as checkpoint_modal:
    gr.Markdown("## 🚦 Checkpoint: Review Team Output")

    checkpoint_team_name = gr.Markdown(value="")
    checkpoint_output = gr.Textbox(
        label="Team Output",
        lines=15,
        interactive=False
    )

    checkpoint_feedback = gr.Textbox(
        label="Feedback for Next Team (Optional)",
        lines=3,
        placeholder="Any adjustments or guidance for the next team..."
    )

    with gr.Row():
        approve_btn = gr.Button("✅ Approve & Continue", variant="primary")
        edit_btn = gr.Button("✏️ Edit Output", variant="secondary")
        reject_btn = gr.Button("❌ Stop Execution", variant="stop")
```

### 4. Execution Flow

#### 4.1 Sequential Team Execution Function
```python
def execute_project_with_checkpoints(
    project_id: str,
    store: ProjectsStore,
    progress=gr.Progress()
) -> tuple:
    """
    Execute all teams in a project sequentially with checkpoints.

    Flow:
    1. Get project and teams
    2. For each team:
        a. Build context from previous teams
        b. Execute team (call run_dev_team)
        c. Save output
        d. Show checkpoint modal
        e. Wait for user approval
    3. Return final results
    """
    project = store.get_project(project_id)
    if not project:
        return "Project not found", [], ""

    teams = project["teams"]
    if not teams:
        return "No teams in project", [], ""

    results = []

    for i, team in enumerate(teams):
        # Update progress
        progress((i / len(teams)), desc=f"Executing {team['name']}...")

        # Build context from previous teams
        previous_outputs = store.get_previous_teams_output(project_id, i)
        context = project["description"]
        if previous_outputs:
            context += "\n\n=== Context from Previous Teams ===\n"
            for prev in previous_outputs:
                context += f"\n## {prev['teamName']}:\n{prev['output']}\n"

        # Execute team
        store.update_team_status(project_id, team["id"], "running")

        try:
            status_msg, outputs, export_paths = run_dev_team(
                project_description=context,
                selected_agents=team["agents"],
                custom_prompts={},
                agent_models={},
                execution_priorities={},
                model_preset="Balanced (All Sonnet)",
                code_review_mode=False,
                phase="Full Run (All Agents)",
                auto_export=False,
                feedback="",
                approval="approve",
                github_url=""
            )

            # Combine outputs
            combined_output = ""
            for agent_id in team["agents"]:
                if agent_id in outputs:
                    combined_output += f"\n\n=== {agent_id} ===\n{outputs[agent_id]}"

            # Save team output
            store.update_team_status(project_id, team["id"], "completed", combined_output)

            results.append({
                "team": team["name"],
                "status": "completed",
                "output": combined_output
            })

            # Checkpoint: Show modal and wait for approval
            # (In practice, Gradio will handle this via UI updates and button clicks)

        except Exception as e:
            store.update_team_status(project_id, team["id"], "failed", str(e))
            results.append({
                "team": team["name"],
                "status": "failed",
                "error": str(e)
            })
            break

    progress(1.0, desc="All teams completed!")

    # Format results for display
    results_html = format_execution_results(results)
    return "Execution complete", results, results_html
```

#### 4.2 Checkpoint Approval Logic
```python
def handle_checkpoint_approval(
    project_id: str,
    team_id: str,
    action: str,  # 'approve', 'edit', 'reject'
    feedback: str = ""
) -> tuple:
    """
    Handle checkpoint approval actions.

    Returns:
        (continue_execution, feedback_message)
    """
    if action == "approve":
        return True, feedback
    elif action == "edit":
        # Allow user to edit output before continuing
        return True, feedback
    elif action == "reject":
        # Stop execution
        return False, "Execution stopped by user"

    return False, "Unknown action"
```

### 5. Event Handlers

#### 5.1 Project CRUD Events
```python
# Create new project
def create_new_project(template_name, project_name, project_desc):
    if not project_name:
        return "Project name required", gr.update(), gr.update()

    store = ProjectsStore()
    project_id = store.create_project(project_name, project_desc)

    # If template selected, add teams from template
    if template_name != "Blank Project":
        template = get_template(template_name)
        if template:
            for team_template in template["teams"]:
                store.add_team(
                    project_id,
                    team_template["name"],
                    team_template["agents"],
                    team_template.get("description", "")
                )

    # Refresh project list
    projects = store.list_projects()
    project_choices = [(p["name"], p["id"]) for p in projects]

    return (
        f"Project '{project_name}' created!",
        gr.update(choices=project_choices, value=project_id),
        gr.update(visible=False)  # Hide form
    )

create_project_btn.click(
    fn=create_new_project,
    inputs=[template_selector, project_name_input, project_desc_input],
    outputs=[status_message, project_selector, new_project_form]
)
```

#### 5.2 Team CRUD Events
```python
def add_team_to_project(project_id, team_name, team_desc, team_agents):
    if not project_id or not team_name or not team_agents:
        return "All fields required", gr.update()

    store = ProjectsStore()
    team_id = store.add_team(project_id, team_name, team_agents, team_desc)

    # Refresh teams display
    teams_html = render_teams_list(project_id, store)

    return f"Team '{team_name}' added!", gr.update(value=teams_html)

add_team_btn.click(
    fn=add_team_to_project,
    inputs=[project_selector, team_name_input, team_desc_input, team_agents_selector],
    outputs=[status_message, teams_display]
)
```

#### 5.3 Execution Events
```python
def start_project_execution(project_id):
    if not project_id:
        return "No project selected", gr.update()

    store = ProjectsStore()
    status, results, html = execute_project_with_checkpoints(project_id, store)

    return html, gr.update(visible=True)  # Show results

run_project_btn.click(
    fn=start_project_execution,
    inputs=[project_selector],
    outputs=[execution_status, checkpoint_modal]
)
```

### 6. Helper Functions

#### 6.1 Teams List Renderer
```python
def render_teams_list(project_id: str, store: ProjectsStore) -> str:
    """Render teams as HTML cards"""
    project = store.get_project(project_id)
    if not project or not project["teams"]:
        return "<p>No teams added yet</p>"

    html = ""
    for i, team in enumerate(project["teams"]):
        status_color = {
            "pending": "#gray",
            "running": "#3498db",
            "completed": "#27ae60",
            "failed": "#e74c3c"
        }.get(team["status"], "#gray")

        html += f"""
        <div style="border-left: 4px solid {status_color}; padding: 12px; margin: 8px 0; background: #f9f9f9; border-radius: 4px;">
            <h4 style="margin: 0 0 8px 0;">
                {i+1}. {team["name"]}
                <span style="float: right; font-size: 12px; color: {status_color};">{team["status"].upper()}</span>
            </h4>
            <p style="margin: 4px 0; font-size: 13px; color: #666;">{team.get("description", "")}</p>
            <p style="margin: 4px 0; font-size: 12px;">
                <strong>Agents:</strong> {", ".join(team["agents"])}
            </p>
        </div>
        """

    return html
```

#### 6.2 Results Formatter
```python
def format_execution_results(results: List[Dict]) -> str:
    """Format execution results as HTML"""
    html = "<div>"

    for result in results:
        status = result.get("status", "unknown")
        color = "#27ae60" if status == "completed" else "#e74c3c"

        html += f"""
        <div style="border-left: 4px solid {color}; padding: 16px; margin: 12px 0; background: white; border-radius: 8px;">
            <h3 style="margin: 0 0 12px 0;">{result["team"]}</h3>
            <span style="background: {color}; color: white; padding: 4px 12px; border-radius: 12px; font-size: 12px;">
                {status.upper()}
            </span>
            <pre style="margin-top: 12px; white-space: pre-wrap; font-family: monospace; font-size: 13px;">
{result.get("output", result.get("error", "No output"))}
            </pre>
        </div>
        """

    html += "</div>"
    return html
```

## Implementation Steps

### Step 1: Add Import
```python
# At top of multi_agent_team.py
from projects_store import ProjectsStore, get_template_names, get_template
```

### Step 2: Initialize Store
```python
# Before Gradio UI definition
projects_store = ProjectsStore()
```

### Step 3: Restructure UI with Tabs
Replace existing `with gr.Blocks(...)` section starting at line 1682 with tab-based layout.

### Step 4: Implement Event Handlers
Add all event handlers for CRUD operations and execution.

### Step 5: Test
- Create project from template
- Add custom teams
- Run sequential execution
- Test checkpoint approvals
- Verify context passing between teams

## Benefits Over React

1. **Faster Configuration**: No navigation between pages, everything in one view
2. **Simpler UI**: Less visual complexity, focused on functionality
3. **Integrated Execution**: Run and monitor all in one place
4. **Template Library**: Quick start with 6 pre-built templates
5. **No Build Step**: Pure Python, instant refresh

## Backward Compatibility

- Keep "Quick Run" tab with existing functionality
- No changes to `run_dev_team()` function
- Projects stored separately from existing memory system

## Files Modified

1. `multi_agent_team.py` - Add Projects & Teams tab
2. `projects_store.py` - NEW (storage system)
3. `gradio_projects.json` - NEW (auto-created, data file)

## Files to Review

Agents should review:
1. **Architecture**: Is the storage system well-designed?
2. **UI Flow**: Is the user flow intuitive and efficient?
3. **Execution Logic**: Is sequential execution with checkpoints robust?
4. **Code Quality**: Any improvements or issues?
5. **Testing Strategy**: What edge cases should we cover?
