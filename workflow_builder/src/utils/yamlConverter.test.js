import { exportToYAML, importFromYAML } from './yamlConverter';
import { loadBuiltinAgents } from './agentLoader';

// Mock localStorage
const localStorageMock = (() => {
  let store = {};
  return {
    getItem: (key) => store[key] || null,
    setItem: (key, value) => { store[key] = value.toString(); },
    removeItem: (key) => { delete store[key]; },
    clear: () => { store = {}; }
  };
})();

global.localStorage = localStorageMock;

describe('yamlConverter', () => {
  let mockWorkflow;
  let agentTypes;

  beforeEach(() => {
    localStorage.clear();
    agentTypes = loadBuiltinAgents();

    // Create a mock workflow with 3 agents
    mockWorkflow = {
      name: 'Test Workflow',
      nodes: [
        {
          id: 'PM-1',
          type: 'agent',
          position: { x: 100, y: 100 },
          data: {
            label: 'Project Manager',
            agentType: 'PM',
            icon: '📋',
            color: '#4A90E2',
            prompt: 'Custom PM prompt',
            model: 'claude-3-5-sonnet-20241022'
          }
        },
        {
          id: 'DevOps-2',
          type: 'agent',
          position: { x: 400, y: 100 },
          data: {
            label: 'DevOps Engineer',
            agentType: 'DevOps',
            icon: '🔧',
            color: '#FF6B35',
            prompt: '',
            model: 'claude-3-haiku-20240307'
          }
        },
        {
          id: 'Security-3',
          type: 'agent',
          position: { x: 700, y: 100 },
          data: {
            label: 'Security Specialist',
            agentType: 'Security',
            icon: '🔒',
            color: '#D32F2F',
            prompt: '',
            model: 'claude-3-5-sonnet-20241022'
          }
        }
      ],
      edges: [
        {
          id: 'e1-2',
          source: 'PM-1',
          target: 'DevOps-2',
          animated: true
        },
        {
          id: 'e2-3',
          source: 'DevOps-2',
          target: 'Security-3',
          animated: true
        }
      ]
    };
  });

  describe('exportToYAML', () => {
    test('should export workflow to valid YAML format', () => {
      const yaml = exportToYAML(mockWorkflow, agentTypes);

      expect(yaml).toContain('name: Test Workflow');
      expect(yaml).toContain('agents:');
      expect(yaml).toContain('- PM');
      expect(yaml).toContain('- DevOps');
      expect(yaml).toContain('- Security');
    });

    test('should include custom prompts section', () => {
      const yaml = exportToYAML(mockWorkflow, agentTypes);

      expect(yaml).toContain('custom_prompts:');
      expect(yaml).toContain('PM: Custom PM prompt');
    });

    test('should include model overrides for non-default models', () => {
      const yaml = exportToYAML(mockWorkflow, agentTypes);

      expect(yaml).toContain('model_overrides:');
      expect(yaml).toContain('DevOps: claude-3-haiku-20240307');
    });

    test('should export custom agents in custom_agents section', () => {
      // Add a custom agent to the workflow
      const customAgent = {
        id: 'CustomAgent',
        label: 'Custom Agent',
        icon: '🚀',
        color: '#667EEA',
        category: 'Engineering',
        defaultPrompt: 'Custom prompt',
        custom: true
      };

      const workflowWithCustom = {
        ...mockWorkflow,
        nodes: [
          ...mockWorkflow.nodes,
          {
            id: 'Custom-4',
            type: 'agent',
            position: { x: 1000, y: 100 },
            data: {
              label: 'Custom Agent',
              agentType: 'CustomAgent',
              icon: '🚀',
              color: '#667EEA',
              prompt: '',
              model: 'claude-3-5-sonnet-20241022',
              custom: true
            }
          }
        ],
        edges: [
          ...mockWorkflow.edges,
          {
            id: 'e3-4',
            source: 'Security-3',
            target: 'Custom-4',
            animated: true
          }
        ]
      };

      const agentTypesWithCustom = [...agentTypes, customAgent];
      const yaml = exportToYAML(workflowWithCustom, agentTypesWithCustom);

      expect(yaml).toContain('custom_agents:');
      expect(yaml).toContain('id: CustomAgent');
      expect(yaml).toContain('label: Custom Agent');
      expect(yaml).toContain('icon: 🚀');
    });

    test('should not include empty custom_agents if none used', () => {
      const yaml = exportToYAML(mockWorkflow, agentTypes);

      // Should not have custom_agents section if no custom agents
      expect(yaml).not.toContain('custom_agents:');
    });

    test('should preserve agent execution order', () => {
      const yaml = exportToYAML(mockWorkflow, agentTypes);
      const lines = yaml.split('\n');

      const agentsIndex = lines.findIndex(l => l.trim() === 'agents:');
      const agentLines = lines.slice(agentsIndex + 1, agentsIndex + 4);

      expect(agentLines[0]).toContain('PM');
      expect(agentLines[1]).toContain('DevOps');
      expect(agentLines[2]).toContain('Security');
    });
  });

  describe('importFromYAML', () => {
    test('should import basic workflow', () => {
      const yamlContent = `
name: Imported Workflow
description: Test import
agents:
  - PM
  - DevOps
  - Security
model: balanced
code_review_mode: false
`;

      const result = importFromYAML(yamlContent, agentTypes);

      expect(result.name).toBe('Imported Workflow');
      expect(result.nodes).toHaveLength(3);
      expect(result.edges).toHaveLength(2); // Sequential flow: 3 nodes = 2 edges
    });

    test('should import workflow with custom prompts', () => {
      const yamlContent = `
name: Workflow with Prompts
agents:
  - PM
  - DevOps
model: balanced
custom_prompts:
  PM: "Custom project manager prompt"
  DevOps: "Custom DevOps prompt"
`;

      const result = importFromYAML(yamlContent, agentTypes);

      const pmNode = result.nodes.find(n => n.data.agentType === 'PM');
      const devOpsNode = result.nodes.find(n => n.data.agentType === 'DevOps');

      expect(pmNode.data.prompt).toBe('Custom project manager prompt');
      expect(devOpsNode.data.prompt).toBe('Custom DevOps prompt');
    });

    test('should import workflow with model overrides', () => {
      const yamlContent = `
name: Workflow with Models
agents:
  - PM
  - DevOps
model: balanced
model_overrides:
  DevOps: claude-3-haiku-20240307
`;

      const result = importFromYAML(yamlContent, agentTypes);

      const devOpsNode = result.nodes.find(n => n.data.agentType === 'DevOps');
      expect(devOpsNode.data.model).toBe('claude-3-haiku-20240307');
    });

    test('should import and save custom agents from custom_agents section', () => {
      const yamlContent = `
name: Workflow with Custom Agent
agents:
  - PM
  - CustomBlockchain
model: balanced
custom_agents:
  - id: CustomBlockchain
    label: Blockchain Developer
    icon: ⛓️
    color: '#FFD700'
    category: Engineering
    defaultPrompt: "Expert in blockchain development"
`;

      const result = importFromYAML(yamlContent, agentTypes);

      expect(result.nodes).toHaveLength(2);

      const customNode = result.nodes.find(n => n.data.agentType === 'CustomBlockchain');
      expect(customNode).toBeTruthy();
      expect(customNode.data.label).toBe('Blockchain Developer');
      expect(customNode.data.icon).toBe('⛓️');
      expect(customNode.data.custom).toBe(true);

      // Check if saved to localStorage
      const saved = localStorage.getItem('customAgents');
      expect(saved).toBeTruthy();

      const customAgents = JSON.parse(saved);
      expect(customAgents.some(a => a.id === 'CustomBlockchain')).toBe(true);
    });

    test('should handle backward compatibility (no custom_agents section)', () => {
      const yamlContent = `
name: Legacy Workflow
agents:
  - PM
  - Research
  - Senior
model: balanced
`;

      const result = importFromYAML(yamlContent, agentTypes);

      expect(result.nodes).toHaveLength(3);
      expect(result.edges).toHaveLength(2);
      // Should not throw errors or warnings
    });

    test('should warn on unknown agent types', () => {
      const consoleWarnSpy = jest.spyOn(console, 'warn').mockImplementation();

      const yamlContent = `
name: Workflow with Unknown Agent
agents:
  - PM
  - UnknownAgent
  - Security
model: balanced
`;

      const result = importFromYAML(yamlContent, agentTypes);

      expect(consoleWarnSpy).toHaveBeenCalledWith(
        expect.stringContaining('Unknown agent type: UnknownAgent')
      );

      // Should skip unknown agent
      expect(result.nodes).toHaveLength(2); // Only PM and Security

      consoleWarnSpy.mockRestore();
    });

    test('should create sequential edges between nodes', () => {
      const yamlContent = `
name: Sequential Workflow
agents:
  - PM
  - DevOps
  - Security
  - QA
model: balanced
`;

      const result = importFromYAML(yamlContent, agentTypes);

      expect(result.edges).toHaveLength(3); // 4 nodes = 3 edges

      // Verify edges connect sequentially
      const node1 = result.nodes[0];
      const node2 = result.nodes[1];
      const edge1 = result.edges[0];

      expect(edge1.source).toBe(node1.id);
      expect(edge1.target).toBe(node2.id);
      expect(edge1.animated).toBe(true);
    });

    test('should throw error on invalid YAML', () => {
      const invalidYaml = `
name: Invalid
agents:
  - PM
  this is not valid yaml: [}
`;

      expect(() => {
        importFromYAML(invalidYaml, agentTypes);
      }).toThrow('Invalid YAML format');
    });

    test('should position nodes in grid layout', () => {
      const yamlContent = `
name: Grid Layout Test
agents:
  - PM
  - DevOps
  - Security
  - QA
  - Research
  - Ideas
model: balanced
`;

      const result = importFromYAML(yamlContent, agentTypes);

      // Check that nodes are positioned in grid (3 per row)
      expect(result.nodes[0].position.x).toBe(100);
      expect(result.nodes[0].position.y).toBe(100);

      expect(result.nodes[1].position.x).toBe(400); // 100 + 300
      expect(result.nodes[1].position.y).toBe(100);

      expect(result.nodes[2].position.x).toBe(700); // 100 + 300*2
      expect(result.nodes[2].position.y).toBe(100);

      expect(result.nodes[3].position.x).toBe(100); // New row
      expect(result.nodes[3].position.y).toBe(300); // 100 + 200
    });
  });

  describe('round-trip export/import', () => {
    test('should preserve workflow through export and import', () => {
      // Export
      const yaml = exportToYAML(mockWorkflow, agentTypes);

      // Import
      const imported = importFromYAML(yaml, agentTypes);

      expect(imported.name).toBe(mockWorkflow.name);
      expect(imported.nodes).toHaveLength(mockWorkflow.nodes.length);

      // Check that agent types are preserved
      const originalTypes = mockWorkflow.nodes.map(n => n.data.agentType).sort();
      const importedTypes = imported.nodes.map(n => n.data.agentType).sort();

      expect(importedTypes).toEqual(originalTypes);
    });

    test('should preserve custom agents through round-trip', () => {
      const customAgent = {
        id: 'CustomAgent',
        label: 'Custom Agent',
        icon: '🚀',
        color: '#667EEA',
        category: 'Engineering',
        defaultPrompt: 'Custom prompt',
        custom: true
      };

      const workflowWithCustom = {
        ...mockWorkflow,
        nodes: [
          ...mockWorkflow.nodes,
          {
            id: 'Custom-4',
            type: 'agent',
            position: { x: 1000, y: 100 },
            data: {
              label: 'Custom Agent',
              agentType: 'CustomAgent',
              icon: '🚀',
              color: '#667EEA',
              prompt: '',
              model: 'claude-3-5-sonnet-20241022',
              custom: true
            }
          }
        ]
      };

      const agentTypesWithCustom = [...agentTypes, customAgent];

      // Export
      const yaml = exportToYAML(workflowWithCustom, agentTypesWithCustom);

      // Clear localStorage before import
      localStorage.clear();

      // Import
      const imported = importFromYAML(yaml, agentTypes);

      // Check custom agent was imported
      const customNode = imported.nodes.find(n => n.data.agentType === 'CustomAgent');
      expect(customNode).toBeTruthy();
      expect(customNode.data.custom).toBe(true);

      // Check custom agent was saved to localStorage
      const saved = localStorage.getItem('customAgents');
      expect(saved).toBeTruthy();

      const savedAgents = JSON.parse(saved);
      expect(savedAgents.some(a => a.id === 'CustomAgent')).toBe(true);
    });
  });
});
