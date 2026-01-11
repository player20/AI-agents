/**
 * Execution State Management Utility
 *
 * This utility provides functions to manage and update workflow execution state.
 * In a production environment, this would integrate with WebSocket connections
 * to receive real-time updates from the backend Gradio application.
 */

// Execution state constants
export const ExecutionState = {
  IDLE: 'idle',
  RUNNING: 'running',
  COMPLETED: 'completed',
  FAILED: 'failed',
};

/**
 * Simulates workflow execution for demonstration purposes.
 * In production, this would be replaced with actual WebSocket/API integration.
 *
 * @param {Array} nodes - Array of workflow nodes
 * @param {Function} updateNodeState - Callback to update node state
 * @param {number} delayPerAgent - Delay in milliseconds between agents (default: 3000)
 */
export const simulateWorkflowExecution = async (nodes, updateNodeState, delayPerAgent = 3000) => {
  // Reset all nodes to idle state
  nodes.forEach(node => {
    updateNodeState(node.id, ExecutionState.IDLE);
  });

  // Execute nodes sequentially
  for (let i = 0; i < nodes.length; i++) {
    const node = nodes[i];

    // Set current node to running
    updateNodeState(node.id, ExecutionState.RUNNING);

    // Simulate execution time
    await new Promise(resolve => setTimeout(resolve, delayPerAgent));

    // Set to completed (randomly fail ~10% of the time for demo)
    const success = Math.random() > 0.1;
    updateNodeState(node.id, success ? ExecutionState.COMPLETED : ExecutionState.FAILED);

    // If failed, stop execution
    if (!success) {
      console.log(`Agent ${node.data.label} failed, stopping execution`);
      break;
    }
  }

  console.log('Workflow execution complete');
};

/**
 * Connects to a WebSocket server for real-time execution updates.
 * This would be used in production to receive updates from the Gradio backend.
 *
 * @param {string} websocketUrl - WebSocket server URL
 * @param {Function} onStateUpdate - Callback when state update received
 * @returns {WebSocket} WebSocket instance
 */
export const connectToExecutionStream = (websocketUrl, onStateUpdate) => {
  const ws = new WebSocket(websocketUrl);

  ws.onopen = () => {
    console.log('Connected to execution stream');
  };

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);

      // Expected message format:
      // {
      //   type: 'execution_update',
      //   agentId: 'PM',
      //   state: 'running' | 'completed' | 'failed',
      //   timestamp: '2024-01-10T12:00:00Z'
      // }

      if (data.type === 'execution_update') {
        onStateUpdate(data.agentId, data.state);
      }
    } catch (error) {
      console.error('Error parsing execution update:', error);
    }
  };

  ws.onerror = (error) => {
    console.error('WebSocket error:', error);
  };

  ws.onclose = () => {
    console.log('Disconnected from execution stream');
  };

  return ws;
};

/**
 * HTTP polling alternative for execution state updates.
 * Polls an API endpoint for execution status.
 *
 * @param {string} apiUrl - API endpoint URL
 * @param {Function} onStateUpdate - Callback when state update received
 * @param {number} pollInterval - Poll interval in milliseconds (default: 1000)
 * @returns {Function} Cleanup function to stop polling
 */
export const pollExecutionState = (apiUrl, onStateUpdate, pollInterval = 1000) => {
  let isPolling = true;

  const poll = async () => {
    while (isPolling) {
      try {
        const response = await fetch(apiUrl);
        const data = await response.json();

        // Expected response format:
        // {
        //   agentStates: {
        //     'PM': 'completed',
        //     'Research': 'running',
        //     'Ideas': 'idle'
        //   }
        // }

        if (data.agentStates) {
          Object.entries(data.agentStates).forEach(([agentId, state]) => {
            onStateUpdate(agentId, state);
          });
        }
      } catch (error) {
        console.error('Error polling execution state:', error);
      }

      await new Promise(resolve => setTimeout(resolve, pollInterval));
    }
  };

  poll();

  // Return cleanup function
  return () => {
    isPolling = false;
  };
};
