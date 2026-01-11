import React, { useState, useCallback, useRef, useEffect } from 'react';
import ReactFlow, {
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  Panel,
} from 'reactflow';
import 'reactflow/dist/style.css';
import yaml from 'js-yaml';
import AgentNode from './AgentNode';
import AgentPalette from './AgentPalette';
import PropertiesPanel from './PropertiesPanel';
import ToolBar from './ToolBar';
import CustomAgentDialog from './CustomAgentDialog';
import ValidationPanel from './ValidationPanel';
import TemplatesModal from './TemplatesModal';
import { exportToYAML, importFromYAML } from '../utils/yamlConverter';
import { loadAllAgents } from '../utils/agentLoader';
import { validateWorkflow } from '../utils/workflowValidator';
import { ExecutionState, simulateWorkflowExecution } from '../utils/executionState';
import './WorkflowBuilder.css';

const nodeTypes = {
  agent: AgentNode,
};

const WorkflowBuilder = () => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [selectedNode, setSelectedNode] = useState(null);
  const [workflowName, setWorkflowName] = useState('Untitled Workflow');
  const [agentTypes, setAgentTypes] = useState([]);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [isTemplatesModalOpen, setIsTemplatesModalOpen] = useState(false);
  const [validationResult, setValidationResult] = useState(null);
  const [highlightedNodes, setHighlightedNodes] = useState([]);
  const reactFlowWrapper = useRef(null);
  const [reactFlowInstance, setReactFlowInstance] = useState(null);

  // Load all agents (built-in + custom) on component mount
  useEffect(() => {
    const allAgents = loadAllAgents();
    setAgentTypes(allAgents);
  }, []);

  // Refresh agent list (used after creating custom agent)
  const refreshAgents = useCallback(() => {
    const allAgents = loadAllAgents();
    setAgentTypes(allAgents);
  }, []);

  // Run validation whenever nodes or edges change
  useEffect(() => {
    const result = validateWorkflow(nodes, edges);
    setValidationResult(result);
  }, [nodes, edges]);

  // Handle connection between nodes
  const onConnect = useCallback(
    (params) => setEdges((eds) => addEdge({ ...params, animated: true }, eds)),
    [setEdges]
  );

  // Handle drag over
  const onDragOver = useCallback((event) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  // Handle drop from palette
  const onDrop = useCallback(
    (event) => {
      event.preventDefault();

      const reactFlowBounds = reactFlowWrapper.current.getBoundingClientRect();
      const agentData = JSON.parse(event.dataTransfer.getData('application/reactflow'));

      if (!agentData) return;

      const position = reactFlowInstance.project({
        x: event.clientX - reactFlowBounds.left,
        y: event.clientY - reactFlowBounds.top,
      });

      const newNode = {
        id: `${agentData.id}-${Date.now()}`,
        type: 'agent',
        position,
        data: {
          label: agentData.label,
          agentType: agentData.id,
          icon: agentData.icon,
          color: agentData.color,
          prompt: '',
          model: 'claude-3-5-sonnet-20241022',
        },
      };

      setNodes((nds) => nds.concat(newNode));
    },
    [reactFlowInstance, setNodes]
  );

  // Handle node selection
  const onNodeClick = useCallback((event, node) => {
    setSelectedNode(node);
  }, []);

  // Update node data when properties change
  const onNodeDataChange = useCallback((nodeId, newData) => {
    setNodes((nds) =>
      nds.map((node) => {
        if (node.id === nodeId) {
          return {
            ...node,
            data: { ...node.data, ...newData },
          };
        }
        return node;
      })
    );
  }, [setNodes]);

  // Export workflow to YAML
  const handleExport = useCallback(() => {
    const yaml = exportToYAML({ name: workflowName, nodes, edges }, agentTypes);
    const blob = new Blob([yaml], { type: 'text/yaml' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${workflowName.replace(/\s+/g, '-').toLowerCase()}.yaml`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }, [nodes, edges, workflowName, agentTypes]);

  // Import workflow from YAML
  const handleImport = useCallback((event) => {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      const yamlContent = e.target.result;
      const { name, nodes: importedNodes, edges: importedEdges } = importFromYAML(
        yamlContent,
        agentTypes
      );
      setWorkflowName(name);
      setNodes(importedNodes);
      setEdges(importedEdges);
    };
    reader.readAsText(file);
  }, [setNodes, setEdges, agentTypes]);

  // Clear workflow
  const handleClear = useCallback(() => {
    if (window.confirm('Are you sure you want to clear the workflow?')) {
      setNodes([]);
      setEdges([]);
      setSelectedNode(null);
      setWorkflowName('Untitled Workflow');
    }
  }, [setNodes, setEdges]);

  // Open custom agent dialog
  const handleOpenDialog = useCallback(() => {
    setIsDialogOpen(true);
  }, []);

  // Close custom agent dialog
  const handleCloseDialog = useCallback(() => {
    setIsDialogOpen(false);
  }, []);

  // Handle custom agent created
  const handleAgentCreated = useCallback((newAgent) => {
    refreshAgents();
    console.log('Custom agent created:', newAgent);
  }, [refreshAgents]);

  // Open templates modal
  const handleOpenTemplatesModal = useCallback(() => {
    setIsTemplatesModalOpen(true);
  }, []);

  // Close templates modal
  const handleCloseTemplatesModal = useCallback(() => {
    setIsTemplatesModalOpen(false);
  }, []);

  // Auto-positioning algorithm for template nodes
  const calculateNodePositions = useCallback((agentIds) => {
    const positions = [];
    const HORIZONTAL_SPACING = 300;
    const VERTICAL_SPACING = 150;
    const NODES_PER_ROW = 3;

    agentIds.forEach((agentId, index) => {
      const row = Math.floor(index / NODES_PER_ROW);
      const col = index % NODES_PER_ROW;

      positions.push({
        x: col * HORIZONTAL_SPACING + 100,
        y: row * VERTICAL_SPACING + 100,
      });
    });

    return positions;
  }, []);

  // Handle template selection and load into canvas
  const handleLoadTemplate = useCallback((yamlContent, templateData) => {
    console.log('🔷 handleLoadTemplate called');
    console.log('  yamlContent:', yamlContent ? 'provided' : 'null');
    console.log('  templateData:', templateData);
    console.log('  agentTypes available:', agentTypes.length);

    try {
      let parsedData;

      // If YAML content provided, parse it
      if (yamlContent) {
        console.log('  Parsing YAML content...');
        parsedData = yaml.load(yamlContent);
      } else if (templateData) {
        console.log('  Using template data directly...');
        // Use template data directly
        parsedData = {
          name: templateData.name,
          agents: templateData.agents,
          description: templateData.description,
        };
      } else {
        console.error('❌ No template data provided');
        return;
      }

      console.log('  Parsed data:', parsedData);

      // Set workflow name
      const templateName = parsedData.name || 'Untitled Workflow';
      console.log('  Setting workflow name:', templateName);
      setWorkflowName(templateName);

      // Get agent IDs from template
      const agentIds = parsedData.agents || [];
      console.log('  Agent IDs from template:', agentIds);

      // Calculate positions for nodes
      const positions = calculateNodePositions(agentIds);
      console.log('  Calculated positions:', positions);

      // Create nodes for each agent
      const newNodes = agentIds.map((agentId, index) => {
        const agentInfo = agentTypes.find(a => a.id === agentId);
        console.log(`  Looking for agent "${agentId}":`, agentInfo ? 'FOUND' : 'NOT FOUND');

        if (!agentInfo) {
          console.warn(`⚠️ Agent type "${agentId}" not found in agent registry`);
          console.warn('  Available agent IDs:', agentTypes.map(a => a.id));
          return null;
        }

        const node = {
          id: `${agentId}-${Date.now()}-${index}`,
          type: 'agent',
          position: positions[index],
          data: {
            label: agentInfo.label,
            agentType: agentInfo.id,
            icon: agentInfo.icon,
            color: agentInfo.color,
            prompt: parsedData.custom_prompts?.[agentId] || parsedData.project_description || '',
            model: 'claude-3-5-sonnet-20241022',
          },
        };
        console.log(`  Created node:`, node);
        return node;
      }).filter(node => node !== null);

      console.log('  Total nodes created:', newNodes.length);

      // Create edges connecting nodes in sequence
      const newEdges = [];
      for (let i = 0; i < newNodes.length - 1; i++) {
        newEdges.push({
          id: `edge-${i}`,
          source: newNodes[i].id,
          target: newNodes[i + 1].id,
          animated: true,
        });
      }
      console.log('  Total edges created:', newEdges.length);

      // Update workflow with template nodes and edges
      console.log('  Calling setNodes and setEdges...');
      setNodes(newNodes);
      setEdges(newEdges);

      console.log('✅ Template loaded successfully:', templateName, newNodes.length, 'agents');
    } catch (error) {
      console.error('❌ Error loading template:', error);
      alert('Failed to load template. Please check the template format.');
    }
  }, [agentTypes, setNodes, setEdges, calculateNodePositions]);

  // Handle validation error click (highlight affected nodes)
  const handleValidationErrorClick = useCallback((nodeIds) => {
    setHighlightedNodes(nodeIds);

    // Clear highlight after 3 seconds
    setTimeout(() => {
      setHighlightedNodes([]);
    }, 3000);

    // If ReactFlow instance is available, fit view to highlighted nodes
    if (reactFlowInstance && nodeIds.length > 0) {
      reactFlowInstance.fitView({
        padding: 0.3,
        nodes: nodeIds.map(id => ({ id })),
        duration: 800,
      });
    }
  }, [reactFlowInstance]);

  // Update execution state for a specific node
  const updateNodeExecutionState = useCallback((nodeId, executionState) => {
    setNodes((nds) =>
      nds.map((node) => {
        if (node.id === nodeId) {
          return {
            ...node,
            data: {
              ...node.data,
              executionState,
            },
          };
        }
        return node;
      })
    );
  }, [setNodes]);

  // Simulate workflow execution (for demonstration/testing)
  const handleSimulateExecution = useCallback(async () => {
    if (nodes.length === 0) {
      alert('Please add agents to the workflow before running simulation');
      return;
    }

    console.log('Starting workflow execution simulation...');

    // Simulate execution with 2-second delay per agent
    await simulateWorkflowExecution(
      nodes,
      (nodeId, state) => updateNodeExecutionState(nodeId, state),
      2000
    );
  }, [nodes, updateNodeExecutionState]);

  return (
    <div className="workflow-builder">
      <ToolBar
        workflowName={workflowName}
        onNameChange={setWorkflowName}
        onExport={handleExport}
        onImport={handleImport}
        onClear={handleClear}
        onOpenTemplates={handleOpenTemplatesModal}
        onRun={handleSimulateExecution}
      />

      <div className="workflow-content">
        <div className="left-sidebar">
          <AgentPalette
            agentTypes={agentTypes}
            onCreateCustomAgent={handleOpenDialog}
          />
          <ValidationPanel
            validationResult={validationResult}
            onErrorClick={handleValidationErrorClick}
          />
        </div>

        <div className="flow-container" ref={reactFlowWrapper}>
          <ReactFlow
            nodes={nodes.map(node => ({
              ...node,
              className: highlightedNodes.includes(node.id) ? 'highlighted' : '',
            }))}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onInit={setReactFlowInstance}
            onDrop={onDrop}
            onDragOver={onDragOver}
            onNodeClick={onNodeClick}
            nodeTypes={nodeTypes}
            fitView
          >
            <Background />
            <Controls />
            <MiniMap
              nodeColor={(node) => node.data.color}
              nodeStrokeWidth={3}
              zoomable
              pannable
            />
            <Panel position="top-right">
              <div className="info-panel">
                <div>Nodes: {nodes.length}</div>
                <div>Connections: {edges.length}</div>
              </div>
            </Panel>
          </ReactFlow>
        </div>

        <PropertiesPanel
          selectedNode={selectedNode}
          onNodeDataChange={onNodeDataChange}
          agentTypes={agentTypes}
        />
      </div>

      {/* Custom Agent Dialog */}
      <CustomAgentDialog
        isOpen={isDialogOpen}
        onClose={handleCloseDialog}
        onAgentCreated={handleAgentCreated}
      />

      {/* Templates Modal */}
      <TemplatesModal
        isOpen={isTemplatesModalOpen}
        onClose={handleCloseTemplatesModal}
        onSelectTemplate={handleLoadTemplate}
        agentTypes={agentTypes}
      />
    </div>
  );
};

export default WorkflowBuilder;
