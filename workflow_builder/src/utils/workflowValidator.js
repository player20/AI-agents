/**
 * Workflow Validation Utility
 *
 * Validates workflow structure and provides error/warning feedback
 * Checks for: circular dependencies, disconnected nodes, missing fields, etc.
 */

/**
 * Validation error types
 */
export const ValidationErrorType = {
  CIRCULAR_DEPENDENCY: 'circular_dependency',
  DISCONNECTED_NODE: 'disconnected_node',
  MISSING_AGENT_TYPE: 'missing_agent_type',
  EMPTY_WORKFLOW: 'empty_workflow',
  DUPLICATE_CONNECTION: 'duplicate_connection',
  INVALID_CONNECTION: 'invalid_connection',
};

/**
 * Validation severity levels
 */
export const ValidationSeverity = {
  ERROR: 'error',      // Blocks workflow execution
  WARNING: 'warning',  // Doesn't block but suggests improvement
  INFO: 'info',        // Informational message
};

/**
 * Main validation function
 *
 * @param {Array} nodes - React Flow nodes
 * @param {Array} edges - React Flow edges
 * @returns {Object} Validation result with errors and warnings
 */
export const validateWorkflow = (nodes, edges) => {
  const errors = [];
  const warnings = [];
  const info = [];

  // 1. Check if workflow is empty
  if (!nodes || nodes.length === 0) {
    errors.push({
      type: ValidationErrorType.EMPTY_WORKFLOW,
      severity: ValidationSeverity.ERROR,
      message: 'Workflow is empty. Add at least one agent to get started.',
      nodeIds: [],
    });
    return { valid: false, errors, warnings, info };
  }

  // 2. Check for circular dependencies
  const circularDeps = detectCircularDependencies(nodes, edges);
  if (circularDeps.length > 0) {
    circularDeps.forEach(cycle => {
      errors.push({
        type: ValidationErrorType.CIRCULAR_DEPENDENCY,
        severity: ValidationSeverity.ERROR,
        message: `Circular dependency detected: ${cycle.join(' → ')}`,
        nodeIds: cycle,
        details: 'Agents cannot depend on each other in a circular way. This would cause an infinite loop.',
      });
    });
  }

  // 3. Check for disconnected nodes (warnings, not errors)
  const disconnectedNodes = detectDisconnectedNodes(nodes, edges);
  if (disconnectedNodes.length > 0) {
    disconnectedNodes.forEach(nodeId => {
      const node = nodes.find(n => n.id === nodeId);
      warnings.push({
        type: ValidationErrorType.DISCONNECTED_NODE,
        severity: ValidationSeverity.WARNING,
        message: `Agent "${node?.data?.label || nodeId}" has no connections`,
        nodeIds: [nodeId],
        details: 'This agent will run independently without receiving input from or sending output to other agents.',
      });
    });
  }

  // 4. Check for missing agent types
  nodes.forEach(node => {
    if (!node.data?.agentType || node.data.agentType.trim() === '') {
      errors.push({
        type: ValidationErrorType.MISSING_AGENT_TYPE,
        severity: ValidationSeverity.ERROR,
        message: `Node "${node.id}" is missing an agent type`,
        nodeIds: [node.id],
        details: 'Every agent must have a valid agent type assigned.',
      });
    }
  });

  // 5. Check for duplicate connections
  const duplicateEdges = detectDuplicateConnections(edges);
  if (duplicateEdges.length > 0) {
    duplicateEdges.forEach(edge => {
      warnings.push({
        type: ValidationErrorType.DUPLICATE_CONNECTION,
        severity: ValidationSeverity.WARNING,
        message: `Duplicate connection detected between agents`,
        nodeIds: [edge.source, edge.target],
        edgeId: edge.id,
        details: 'Multiple connections between the same agents are redundant.',
      });
    });
  }

  // 6. Informational: workflow stats
  const stats = calculateWorkflowStats(nodes, edges);
  info.push({
    severity: ValidationSeverity.INFO,
    message: `Workflow contains ${stats.nodeCount} agent(s) and ${stats.edgeCount} connection(s)`,
    details: stats,
  });

  // Determine overall validity
  const valid = errors.length === 0;

  return {
    valid,
    errors,
    warnings,
    info,
    stats,
  };
};

/**
 * Detect circular dependencies using DFS
 *
 * @param {Array} nodes - React Flow nodes
 * @param {Array} edges - React Flow edges
 * @returns {Array} Array of cycles (each cycle is an array of node IDs)
 */
const detectCircularDependencies = (nodes, edges) => {
  const cycles = [];
  const visited = new Set();
  const recursionStack = new Set();
  const nodeMap = new Map(nodes.map(n => [n.id, n]));

  // Build adjacency list
  const adjacencyList = new Map();
  nodes.forEach(node => {
    adjacencyList.set(node.id, []);
  });
  edges.forEach(edge => {
    if (adjacencyList.has(edge.source)) {
      adjacencyList.get(edge.source).push(edge.target);
    }
  });

  // DFS to detect cycles
  const dfs = (nodeId, path = []) => {
    visited.add(nodeId);
    recursionStack.add(nodeId);
    path.push(nodeId);

    const neighbors = adjacencyList.get(nodeId) || [];
    for (const neighbor of neighbors) {
      if (!visited.has(neighbor)) {
        if (dfs(neighbor, [...path])) {
          return true;
        }
      } else if (recursionStack.has(neighbor)) {
        // Found a cycle
        const cycleStart = path.indexOf(neighbor);
        const cycle = path.slice(cycleStart).map(id => {
          const node = nodeMap.get(id);
          return node?.data?.label || id;
        });
        cycle.push(cycle[0]); // Complete the cycle
        cycles.push(cycle);
        return true;
      }
    }

    recursionStack.delete(nodeId);
    return false;
  };

  // Check all nodes
  nodes.forEach(node => {
    if (!visited.has(node.id)) {
      dfs(node.id);
    }
  });

  return cycles;
};

/**
 * Detect disconnected nodes (nodes with no incoming or outgoing edges)
 *
 * @param {Array} nodes - React Flow nodes
 * @param {Array} edges - React Flow edges
 * @returns {Array} Array of disconnected node IDs
 */
const detectDisconnectedNodes = (nodes, edges) => {
  const connectedNodes = new Set();

  edges.forEach(edge => {
    connectedNodes.add(edge.source);
    connectedNodes.add(edge.target);
  });

  const disconnected = nodes
    .filter(node => !connectedNodes.has(node.id))
    .map(node => node.id);

  return disconnected;
};

/**
 * Detect duplicate connections (same source and target)
 *
 * @param {Array} edges - React Flow edges
 * @returns {Array} Array of duplicate edges
 */
const detectDuplicateConnections = (edges) => {
  const seen = new Set();
  const duplicates = [];

  edges.forEach(edge => {
    const key = `${edge.source}->${edge.target}`;
    if (seen.has(key)) {
      duplicates.push(edge);
    } else {
      seen.add(key);
    }
  });

  return duplicates;
};

/**
 * Calculate workflow statistics
 *
 * @param {Array} nodes - React Flow nodes
 * @param {Array} edges - React Flow edges
 * @returns {Object} Workflow statistics
 */
const calculateWorkflowStats = (nodes, edges) => {
  const agentTypes = nodes.map(n => n.data?.agentType).filter(Boolean);
  const uniqueAgentTypes = new Set(agentTypes);

  const customAgents = nodes.filter(n => n.data?.custom).length;
  const builtinAgents = nodes.length - customAgents;

  return {
    nodeCount: nodes.length,
    edgeCount: edges.length,
    uniqueAgentTypes: uniqueAgentTypes.size,
    customAgentsCount: customAgents,
    builtinAgentsCount: builtinAgents,
    averageConnectionsPerNode: nodes.length > 0 ? (edges.length / nodes.length).toFixed(2) : 0,
  };
};

/**
 * Get validation summary message
 *
 * @param {Object} validationResult - Result from validateWorkflow
 * @returns {String} Human-readable summary
 */
export const getValidationSummary = (validationResult) => {
  const { valid, errors, warnings } = validationResult;

  if (valid && warnings.length === 0) {
    return '✅ Workflow is valid with no issues';
  } else if (valid && warnings.length > 0) {
    return `✅ Workflow is valid but has ${warnings.length} warning(s)`;
  } else {
    return `❌ Workflow has ${errors.length} error(s) and ${warnings.length} warning(s)`;
  }
};

/**
 * Filter validation results by severity
 *
 * @param {Object} validationResult - Result from validateWorkflow
 * @param {String} severity - Severity level to filter by
 * @returns {Array} Filtered validation messages
 */
export const filterBySeverity = (validationResult, severity) => {
  const { errors, warnings, info } = validationResult;

  switch (severity) {
    case ValidationSeverity.ERROR:
      return errors;
    case ValidationSeverity.WARNING:
      return warnings;
    case ValidationSeverity.INFO:
      return info;
    default:
      return [...errors, ...warnings, ...info];
  }
};
