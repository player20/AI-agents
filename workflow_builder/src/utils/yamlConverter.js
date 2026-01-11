import yaml from 'js-yaml';
import { saveCustomAgent } from './agentLoader';

/**
 * Export workflow to YAML format compatible with existing templates
 */
export const exportToYAML = (workflow, agentTypes) => {
  const { name, nodes, edges } = workflow;

  // Build agent order based on connections
  const agentOrder = buildExecutionOrder(nodes, edges);

  // Extract agents with their configurations
  const agents = agentOrder.map((nodeId) => {
    const node = nodes.find((n) => n.id === nodeId);
    return node.data.agentType;
  });

  // Build custom prompts object
  const customPrompts = {};
  nodes.forEach((node) => {
    if (node.data.prompt) {
      customPrompts[node.data.agentType] = node.data.prompt;
    }
  });

  // Build model overrides
  const modelOverrides = {};
  nodes.forEach((node) => {
    if (node.data.model !== 'claude-3-5-sonnet-20241022') {
      modelOverrides[node.data.agentType] = node.data.model;
    }
  });

  // Extract custom agents used in workflow
  const customAgentsMap = new Map();
  agentOrder.forEach((nodeId) => {
    const node = nodes.find((n) => n.id === nodeId);
    const agentInfo = agentTypes.find((a) => a.id === node.data.agentType);

    // If agent is custom and not already added, include it
    if (agentInfo && agentInfo.custom && !customAgentsMap.has(agentInfo.id)) {
      customAgentsMap.set(agentInfo.id, {
        id: agentInfo.id,
        label: agentInfo.label,
        icon: agentInfo.icon,
        color: agentInfo.color,
        category: agentInfo.category || 'Uncategorized',
        defaultPrompt: agentInfo.defaultPrompt || '',
      });
    }
  });

  // Create workflow object
  const workflowObj = {
    name: name,
    description: `Workflow with ${nodes.length} agents`,
    agents: agents,
    model: 'balanced', // Default model preset
    code_review_mode: false,
  };

  // Add custom prompts if any
  if (Object.keys(customPrompts).length > 0) {
    workflowObj.custom_prompts = customPrompts;
  }

  // Add model overrides if any
  if (Object.keys(modelOverrides).length > 0) {
    workflowObj.model_overrides = modelOverrides;
  }

  // Add custom agents if any
  if (customAgentsMap.size > 0) {
    workflowObj.custom_agents = Array.from(customAgentsMap.values());
  }

  // Convert to YAML
  return yaml.dump(workflowObj, {
    indent: 2,
    lineWidth: -1,
    noRefs: true,
  });
};

/**
 * Import workflow from YAML format
 */
export const importFromYAML = (yamlContent, agentTypes) => {
  try {
    const workflowObj = yaml.load(yamlContent);

    const name = workflowObj.name || 'Imported Workflow';
    const agents = workflowObj.agents || [];
    const customPrompts = workflowObj.custom_prompts || {};
    const modelOverrides = workflowObj.model_overrides || {};
    const customAgentsFromYAML = workflowObj.custom_agents || [];

    // Save custom agents to localStorage if they don't already exist
    const savedCustomAgentIds = new Set();
    customAgentsFromYAML.forEach((customAgent) => {
      // Check if custom agent already exists in agentTypes
      const exists = agentTypes.find((a) => a.id === customAgent.id);
      if (!exists) {
        // Save to localStorage
        const success = saveCustomAgent({
          id: customAgent.id,
          label: customAgent.label,
          icon: customAgent.icon,
          color: customAgent.color,
          category: customAgent.category || 'Uncategorized',
          defaultPrompt: customAgent.defaultPrompt || '',
          custom: true,
          builtin: false,
        });
        if (success) {
          savedCustomAgentIds.add(customAgent.id);
          console.log(`Imported custom agent: ${customAgent.label}`);
        }
      }
    });

    // Create combined agent lookup (built-in + custom from YAML)
    const allAgentsForLookup = [
      ...agentTypes,
      ...customAgentsFromYAML.filter((ca) => savedCustomAgentIds.has(ca.id)),
    ];

    // Create nodes from agents
    const nodes = agents.map((agentType, index) => {
      const agentInfo = allAgentsForLookup.find((a) => a.id === agentType);
      if (!agentInfo) {
        console.warn(
          `Unknown agent type: ${agentType}. This agent is not registered in the platform and may not work correctly.`
        );
        return null;
      }

      return {
        id: `${agentType}-${Date.now()}-${index}`,
        type: 'agent',
        position: {
          x: 100 + (index % 3) * 300,
          y: 100 + Math.floor(index / 3) * 200,
        },
        data: {
          label: agentInfo.label,
          agentType: agentType,
          icon: agentInfo.icon,
          color: agentInfo.color,
          prompt: customPrompts[agentType] || '',
          model: modelOverrides[agentType] || 'claude-3-5-sonnet-20241022',
          custom: agentInfo.custom || false,
        },
      };
    }).filter(Boolean);

    // Create edges showing sequential flow
    const edges = [];
    for (let i = 0; i < nodes.length - 1; i++) {
      edges.push({
        id: `e${i}-${i + 1}`,
        source: nodes[i].id,
        target: nodes[i + 1].id,
        animated: true,
      });
    }

    return { name, nodes, edges };
  } catch (error) {
    console.error('Error parsing YAML:', error);
    throw new Error('Invalid YAML format');
  }
};

/**
 * Build execution order from nodes and edges using topological sort
 */
const buildExecutionOrder = (nodes, edges) => {
  // Build adjacency list
  const graph = new Map();
  const inDegree = new Map();

  // Initialize
  nodes.forEach((node) => {
    graph.set(node.id, []);
    inDegree.set(node.id, 0);
  });

  // Build graph
  edges.forEach((edge) => {
    graph.get(edge.source).push(edge.target);
    inDegree.set(edge.target, (inDegree.get(edge.target) || 0) + 1);
  });

  // Topological sort using Kahn's algorithm
  const queue = [];
  const result = [];

  // Find nodes with no incoming edges
  inDegree.forEach((degree, nodeId) => {
    if (degree === 0) {
      queue.push(nodeId);
    }
  });

  while (queue.length > 0) {
    const nodeId = queue.shift();
    result.push(nodeId);

    const neighbors = graph.get(nodeId) || [];
    neighbors.forEach((neighbor) => {
      inDegree.set(neighbor, inDegree.get(neighbor) - 1);
      if (inDegree.get(neighbor) === 0) {
        queue.push(neighbor);
      }
    });
  }

  // If result doesn't contain all nodes, there's a cycle or disconnected nodes
  // For disconnected nodes, append them at the end
  if (result.length < nodes.length) {
    nodes.forEach((node) => {
      if (!result.includes(node.id)) {
        result.push(node.id);
      }
    });
  }

  return result;
};
