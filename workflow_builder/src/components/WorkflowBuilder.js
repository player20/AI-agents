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
import AgentNode from './AgentNode';
import AgentPalette from './AgentPalette';
import PropertiesPanel from './PropertiesPanel';
import ToolBar from './ToolBar';
import CustomAgentDialog from './CustomAgentDialog';
import ValidationPanel from './ValidationPanel';
import { exportToYAML, importFromYAML } from '../utils/yamlConverter';
import { loadAllAgents } from '../utils/agentLoader';
import { validateWorkflow } from '../utils/workflowValidator';
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

  return (
    <div className="workflow-builder">
      <ToolBar
        workflowName={workflowName}
        onNameChange={setWorkflowName}
        onExport={handleExport}
        onImport={handleImport}
        onClear={handleClear}
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
    </div>
  );
};

export default WorkflowBuilder;
