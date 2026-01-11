# Multi-Agent Workflow Builder

Visual drag-and-drop workflow builder for the Multi-Agent Platform.

## Features

- **Drag-and-drop interface** for creating agent workflows
- **11 agent types** available (PM, Memory, Research, Ideas, Designs, Senior, iOS, Android, Web, QA, Verifier)
- **Visual connections** showing agent dependencies
- **Properties panel** for customizing prompts and model selection
- **YAML export/import** compatible with existing templates
- **Real-time workflow visualization** with React Flow

## Quick Start

### Installation

```bash
cd workflow_builder
npm install
```

### Development

```bash
npm start
```

Opens the workflow builder at [http://localhost:3000](http://localhost:3000)

### Build for Production

```bash
npm run build
```

Creates optimized production build in `build/` directory.

## Usage

### Creating a Workflow

1. **Drag agents** from the left palette onto the canvas
2. **Connect agents** by dragging from one node's output (bottom) to another's input (top)
3. **Click an agent** to edit its properties in the right panel
4. **Customize prompt** and select model for each agent
5. **Export to YAML** using the Export button in the toolbar

### Importing Workflows

1. Click **Import** button in toolbar
2. Select a YAML workflow file
3. Workflow loads automatically with all agents and connections

### Workflow Format

Exported workflows are compatible with the existing Multi-Agent Platform template format:

```yaml
name: My Workflow
description: Workflow with 5 agents
agents:
  - Research
  - Ideas
  - Senior
  - Designs
  - QA
model: balanced
code_review_mode: false
custom_prompts:
  Research: "Custom prompt for Research agent..."
  Ideas: "Custom prompt for Ideas agent..."
model_overrides:
  Senior: claude-opus-4-5-20251101
```

## Integration with Gradio

The workflow builder can be integrated into the existing Gradio platform in two ways:

### Option 1: Iframe Embed

```python
import gradio as gr

with gr.Blocks() as demo:
    gr.HTML('<iframe src="http://localhost:3000" width="100%" height="800px"></iframe>')
```

### Option 2: Gradio Custom Component

Build the workflow builder as a Gradio custom component for tighter integration.

## Technology Stack

- **React 18** - UI framework
- **React Flow 11** - Node-based workflow visualization
- **js-yaml** - YAML parsing and generation
- **Axios** - HTTP client for API calls
- **Lucide React** - Icon library

## Architecture

```
workflow_builder/
├── src/
│   ├── components/
│   │   ├── WorkflowBuilder.js    # Main component
│   │   ├── AgentNode.js          # Agent node component
│   │   ├── AgentPalette.js       # Agent selection sidebar
│   │   ├── PropertiesPanel.js    # Node properties editor
│   │   └── ToolBar.js            # Top toolbar with actions
│   ├── utils/
│   │   └── yamlConverter.js      # YAML export/import logic
│   ├── App.js
│   └── index.js
├── public/
│   └── index.html
└── package.json
```

## Development Roadmap

### MVP (Current)
- ✅ Drag-and-drop canvas with 11 agent types
- ✅ Connection system showing dependencies
- ✅ Properties panel for prompt customization
- ✅ YAML export/import
- ✅ Basic styling and UX

### v2 (Future)
- [ ] Real-time execution visualization
- [ ] Template library integration
- [ ] Workflow validation and error checking
- [ ] Undo/redo functionality
- [ ] Auto-layout for imported workflows
- [ ] Collaborative editing
- [ ] Dark mode

## Contributing

See the main [CONTRIBUTING.md](../CONTRIBUTING.md) in the root directory.

## License

Same as the main Multi-Agent Platform.
