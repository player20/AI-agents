# Visual Workflow Builder - Installation & Usage Guide

## Overview

The Visual Workflow Builder is a React-based drag-and-drop interface for creating Multi-Agent workflows without writing code. Built with React Flow, it provides an intuitive way for non-technical users (PMs, designers, analysts) to design agent workflows visually.

## Features

✅ **Drag-and-drop canvas** with 20 built-in agent types + unlimited custom agents
✅ **Categorized agent palette** with 5 categories (Engineering, Operations, Strategy, Data & AI, Quality & Compliance)
✅ **Custom agent creation** - define your own agents with custom icons, colors, and prompts
✅ **Search & Favorites** - quickly find agents and star frequently-used ones
✅ **Visual connections** showing agent dependencies
✅ **Properties panel** for customizing prompts and models
✅ **Workflow validation** - real-time error checking with circular dependency detection 🆕
✅ **Click-to-highlight** - click validation errors to zoom to affected agents 🆕
✅ **YAML export/import** with custom_agents section for sharing workflows
✅ **Real-time workflow visualization**
✅ **REST API** for dynamic agent management (3 endpoints)
✅ **Backward compatible** with existing 12 YAML templates
✅ **Gradio Platform integration** - import workflows directly into execution platform 🆕

---

## Integration with Gradio Platform

The Workflow Builder and Gradio Platform work together seamlessly:

1. **Design** → Use Workflow Builder (localhost:3000) to visually design your workflow
2. **Export** → Export workflow as YAML file
3. **Execute** → Import YAML into Gradio Platform (localhost:7860) and run it

### Using YAML Import in Gradio Platform

After designing your workflow in the Visual Builder:

1. **Export YAML**: Click "Export" in Workflow Builder to download `your-workflow.yaml`

2. **Open Gradio Platform**: Start the Gradio Platform if not running:
   ```bash
   cd C:\Users\jacob\MultiAgentTeam
   python multi_agent_team.py
   ```

3. **Import Workflow**:
   - Open http://localhost:7860 in your browser
   - Expand the **"📥 Import Workflow from YAML"** accordion (under Project Configuration)
   - Click "Select YAML Workflow File" and choose your exported workflow
   - Click **"📥 Import Workflow"** button

4. **Review Import**:
   - Import status will show:
     - Workflow name and statistics
     - Any validation warnings (circular dependencies, disconnected nodes)
     - Custom agents that are not available in Gradio Platform
   - Agent selection checkboxes will be automatically populated
   - Project name will be set to your workflow name

5. **Execute**: Click **"▶️ Run Team"** to execute your workflow!

**Note**: Custom agents created in the Workflow Builder are not yet supported in the Gradio Platform. They will be skipped during import.

---

## Installation

### Prerequisites

- **Node.js 16+** and **npm** installed
- **Python 3.8+** with Multi-Agent Platform

### Step 1: Install Dependencies

```bash
cd C:\Users\jacob\MultiAgentTeam\workflow_builder
npm install
```

This installs:
- React 18
- React Flow 11
- Axios (for API calls)
- js-yaml (for YAML parsing)
- Lucide React (for icons)

### Step 2: Start Development Server

```bash
npm start
```

The workflow builder will open at [http://localhost:3000](http://localhost:3000)

---

## Usage

### Creating a Workflow

1. **Drag agents** from the left palette onto the canvas
2. **Connect agents** by dragging from a node's output port (bottom) to another node's input port (top)
3. **Click an agent** to open the properties panel on the right
4. **Customize** the agent's prompt and select the model
5. **Export** the workflow to YAML using the Export button

### Editing Agent Properties

When you click an agent node, the properties panel displays:

- **Agent Type**: The agent's role (Research, Ideas, etc.)
- **Model**: Choose from Sonnet, Opus, or Haiku
- **Custom Prompt**: Override the agent's default prompt (optional)
- **Node ID**: Unique identifier for this agent instance

### Workflow Validation

The workflow builder automatically validates your workflow in real-time as you build it.

**Validation Panel** (located below the agent palette):
- **✅ Valid**: Workflow has no errors and is ready to export/execute
- **⚠️ Warnings**: Non-critical issues that won't block execution (e.g., disconnected nodes)
- **❌ Errors**: Critical issues that must be fixed before execution (e.g., circular dependencies)

**Error Types**:
1. **Circular Dependency** - Agents depend on each other in a loop (A → B → A). Click to highlight the cycle.
2. **Disconnected Nodes** - Agent has no connections (runs independently). Click to highlight.
3. **Missing Agent Type** - Agent is missing required configuration.
4. **Duplicate Connections** - Same agents connected multiple times (redundant).

**How to Use**:
- Build your workflow normally - validation runs automatically
- Click on any error/warning to highlight affected agents and zoom to them
- Highlighted nodes pulse red for 3 seconds
- Expand error sections (▼) to see detailed information
- Fix errors before exporting to ensure workflow works correctly

### Exporting Workflows

Click **Export** in the toolbar to download a YAML file. The format is compatible with the existing Multi-Agent Platform templates:

```yaml
name: My Workflow
agents:
  - Research
  - Ideas
  - DevOps
  - BlockchainDev  # Custom agent
model: balanced
custom_prompts:
  Research: "Custom prompt here..."
  DevOps: "Focus on Kubernetes deployment..."
model_overrides:
  Senior: claude-opus-4-5-20251101
custom_agents:  # New section for custom agents
  - id: BlockchainDev
    label: Blockchain Developer
    icon: ⛓️
    color: '#FFD700'
    category: Engineering
    defaultPrompt: "Expert in blockchain development, smart contracts, Web3, and DeFi protocols."
```

**Backward Compatibility**: Workflows without the `custom_agents` section will still import correctly (existing 12 templates work unchanged).

### Importing Workflows

1. Click **Import** in the toolbar
2. Select a `.yaml` workflow file
3. The workflow loads with all agents and connections

You can import any of the 12 existing templates from the `templates/` directory!

---

## Agent Ecosystem

### 20 Built-in Agents (Organized by Category)

#### 👨‍💻 Engineering (7 agents)
- **📋 PM (Project Manager)** - Creates sprint plans, coordinates work, manages timelines
- **🧠 Memory** - Recalls past learnings and stores team knowledge
- **👨‍💻 Senior** - Reviews architecture and validates tech stack
- **📱 iOS** - Builds iOS components (Swift/SwiftUI)
- **🤖 Android** - Builds Android components (Kotlin/Compose)
- **🌐 Web** - Builds web components (React/JavaScript)
- **🔌 Backend** - Designs APIs, databases, and server architecture

#### ⚙️ Operations (3 agents)
- **🔧 DevOps** - Automates CI/CD, containers, infrastructure, deployment
- **✅ QA** - Tests functionality and validates quality
- **🔎 Verifier** - Checks for hallucinations and consistency

#### 📊 Strategy & Research (5 agents)
- **🔍 Research** - Market research and competitive analysis
- **💡 Ideas** - Generates market-smart feature ideas
- **🎨 Designs** - Creates UI/UX designs and wireframes
- **📢 Marketing** - Go-to-market strategies, content, SEO, growth
- **📦 Product** - Product roadmaps, feature prioritization, user stories

#### 🤖 Data & AI (3 agents)
- **🧠 Memory** - Long-term knowledge management
- **📊 Data Architect** - Data models, ETL pipelines, analytics architecture
- **📈 Data Scientist** - Machine learning, statistical analysis, predictive models

#### 🔒 Quality & Compliance (4 agents)
- **🔒 Security** - Security audits, vulnerability scanning, compliance checks
- **⚖️ Legal** - Terms of service, privacy policies, regulatory compliance
- **🎧 Support** - Customer support workflows, documentation, troubleshooting
- **🔎 Verifier** - Anti-hallucination validation and fact-checking

### Creating Custom Agents

You can create unlimited custom agents for specialized roles:

1. **Click "+ Create Custom Agent"** at bottom of agent palette
2. **Fill in the form**:
   - **Name**: e.g., "Blockchain Developer"
   - **Icon**: Choose an emoji (e.g., ⛓️)
   - **Color**: Pick a hex color (e.g., #FFD700)
   - **Category**: Select from 5 categories
   - **Default Prompt**: Describe the agent's role and expertise
3. **Submit** - Agent appears immediately in the selected category with a ✨ sparkle badge

**Custom agents are**:
- ✅ Saved to browser localStorage (persist across sessions)
- ✅ Exportable in YAML workflows (custom_agents section)
- ✅ Shareable (import YAML to load custom agents)
- ✅ Deletable (managed in browser localStorage)

### Search & Favorites

**Search Bar**:
- Real-time filtering (300ms debounce for performance)
- Searches by agent name, label, category, and prompt
- Case-insensitive
- Shows "No results" if nothing matches

**Favorites**:
- Click the star (☆) button on any agent to favorite it
- Favorited agents show gold star (★)
- "⭐ Favorites" section appears at top of palette
- Favorites persist in localStorage across sessions
- Quick access to your most-used agents

---

## Integration with Gradio Platform

There are two ways to integrate the workflow builder with the existing Gradio platform:

### Option 1: Standalone Mode (Quickest)

Run the workflow builder separately alongside Gradio:

```bash
# Terminal 1: Start workflow builder
cd workflow_builder
npm start

# Terminal 2: Start Gradio platform
cd ..
python multi_agent_team.py
```

Access:
- Workflow Builder: http://localhost:3000
- Gradio Platform: http://localhost:7860

### Option 2: Integrated Mode (Recommended)

Use the integration script to embed the workflow builder in Gradio:

```bash
python workflow_builder_integration.py
```

This launches all three services:
- **React dev server** (background, port 3000)
- **REST API server** (port 5000) - for dynamic agent management
- **Gradio interface** with embedded workflow builder (port 7860)

**REST API Endpoints**:
- `GET /api/agents` - Fetch all agents from config
- `POST /api/agents/validate` - Validate if agent type is registered
- `GET /api/health` - Health check for API server

### Option 3: Production Build

For production deployment, build the React app and serve it statically:

```bash
# Build React app
cd workflow_builder
npm run build

# Serve with Python
cd build
python -m http.server 3000
```

Then embed in Gradio using the integration script.

---

## Sample Workflows

### Quick Test

Try the included sample workflow:

```bash
# In workflow builder UI:
# 1. Click Import
# 2. Select: workflow_builder/sample-workflow.yaml
# 3. Workflow loads automatically
```

### Using Existing Templates

All 12 templates from `templates/` directory can be imported:

```bash
templates/saas-app-planner.yaml
templates/code-review.yaml
templates/market-research.yaml
templates/security-audit.yaml
# ... and 8 more
```

---

## Architecture

```
workflow_builder/
├── package.json           # Dependencies (v1.1.0 - agent extensibility update)
├── public/
│   └── index.html        # HTML entry point
├── src/
│   ├── components/
│   │   ├── WorkflowBuilder.js      # Main component with React Flow
│   │   ├── AgentNode.js            # Custom agent node component
│   │   ├── AgentPalette.js         # Categorized palette with search & favorites
│   │   ├── PropertiesPanel.js      # Right sidebar for editing
│   │   ├── ToolBar.js              # Top toolbar with actions
│   │   ├── CustomAgentDialog.js    # Modal for creating custom agents
│   │   └── SearchBar.js            # Real-time search component
│   ├── config/
│   │   └── agents.config.json      # 20 built-in agents + categories
│   ├── utils/
│   │   ├── yamlConverter.js        # YAML export/import with custom_agents support
│   │   └── agentLoader.js          # Load agents from config + localStorage
│   ├── App.js             # Root component
│   └── index.js           # React entry point
├── README.md              # Component documentation
└── sample-workflow.yaml   # Test workflow
```

---

## Development

### Running Tests

```bash
npm test
```

### Building for Production

```bash
npm run build
```

Creates optimized production build in `build/` directory.

### Customization

#### Adding New Built-in Agent Types

Edit `src/config/agents.config.json`:

```json
{
  "version": "1.0.0",
  "categories": {
    "Engineering": {
      "label": "Engineering",
      "icon": "👨‍💻",
      "agents": ["PM", "Senior", "NewAgent"]  // Add to category
    }
  },
  "agents": [
    // ... existing agents
    {
      "id": "NewAgent",
      "label": "New Agent",
      "icon": "🚀",
      "color": "#FF5733",
      "category": "Engineering",
      "defaultPrompt": "Description of what this agent does",
      "builtin": true
    }
  ]
}
```

**No code changes needed!** The agent will automatically appear in the palette under the specified category.

#### Creating Custom Agents (No Code)

For end-users, use the "+ Create Custom Agent" button in the UI. No technical knowledge required!

#### Changing Styles

Edit the CSS files in `src/components/`:
- `WorkflowBuilder.css` - Main layout
- `AgentNode.css` - Node appearance
- `AgentPalette.css` - Left sidebar
- `PropertiesPanel.css` - Right sidebar
- `ToolBar.css` - Top toolbar

---

## Troubleshooting

### "npm: command not found"

**Solution**: Install Node.js from https://nodejs.org/

### Port 3000 already in use

**Solution**: Change the port in `package.json`:

```json
"scripts": {
  "start": "PORT=3001 react-scripts start"
}
```

### Module not found errors

**Solution**: Reinstall dependencies:

```bash
rm -rf node_modules package-lock.json
npm install
```

### Workflow doesn't load in Gradio

**Solution**: Ensure React dev server is running on port 3000:

```bash
cd workflow_builder
npm start
```

Then refresh the Gradio interface.

---

## Roadmap

### v1.0 MVP (Completed ✅)
- ✅ Drag-and-drop canvas with 11 agent types
- ✅ Connection system showing dependencies
- ✅ Properties panel for prompt customization
- ✅ YAML export/import compatibility
- ✅ Basic styling and UX

### v1.1 Agent Extensibility (Completed ✅)
- ✅ Expanded to 20 built-in agents across 5 categories
- ✅ Custom agent creation with UI (+ Create Custom Agent button)
- ✅ Categorized agent palette (Engineering, Operations, Strategy, Data & AI, Quality & Compliance)
- ✅ Search functionality with real-time filtering (300ms debounce)
- ✅ Favorites system (star agents for quick access)
- ✅ YAML custom_agents section for export/import
- ✅ REST API (3 endpoints: /api/agents, /api/agents/validate, /api/health)
- ✅ localStorage persistence for custom agents and favorites
- ✅ Backward compatibility with existing 12 templates
- ✅ Comprehensive test suite (40+ unit tests)

### v2.0 Week 1: Workflow Validation (Completed ✅)
- ✅ **Workflow Validation and Error Checking** - Real-time validation with smart error detection
  - Circular dependency detection (infinite loop prevention)
  - Disconnected node warnings
  - Missing agent type validation
  - Duplicate connection detection
  - Click-to-highlight error nodes with auto-zoom
  - Collapsible error/warning/info sections
  - Visual stats (node count, edge count, agent types)

### v2.0 Upcoming (Next 2-3 weeks)
- [ ] Template library browser (import from templates/)
- [ ] Keyboard shortcuts (delete, copy, paste)
- [ ] Agent marketplace (community-contributed agents)
- [ ] Auto-layout for imported workflows

### v3 (Month 2-3)
- [ ] Collaborative editing (multiple users)
- [ ] Version history and diff view
- [ ] Dark mode
- [ ] Saved workflows to database
- [ ] Team workspaces with shared custom agents

---

## Key Benefits

**For Non-Technical Users:**
- Create workflows without writing code
- Visual representation of agent dependencies
- Easy prompt customization
- Template library for quick start

**For Developers:**
- YAML export compatible with existing system
- Easy to extend with new agent types
- Clean React architecture
- Production-ready build system

**For Enterprise:**
- Professional UI matching enterprise standards
- Accessibility-friendly design
- Easy deployment (Docker, Kubernetes)
- Integrates with existing Gradio platform

---

## Support

- **Issues**: Report bugs in the main GitHub repository
- **Documentation**: See [README.md](workflow_builder/README.md) in the workflow_builder directory
- **Integration Help**: Check [workflow_builder_integration.py](workflow_builder_integration.py)

---

**Built with the Multi-Agent Team Platform** 🤖

Transform your agent workflows from text to visual. Ship faster. Empower non-technical users.
