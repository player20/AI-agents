import {
  loadBuiltinAgents,
  loadCustomAgents,
  loadAllAgents,
  saveCustomAgent,
  deleteCustomAgent,
  validateAgentSchema,
  toggleFavorite,
  isFavorite,
  getFavoriteAgents,
  searchAgents,
  getAgentCategories
} from './agentLoader';

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

describe('agentLoader', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  describe('loadBuiltinAgents', () => {
    test('should load 20 built-in agents', () => {
      const agents = loadBuiltinAgents();
      expect(agents).toHaveLength(20);
    });

    test('should have required fields for each agent', () => {
      const agents = loadBuiltinAgents();
      agents.forEach(agent => {
        expect(agent).toHaveProperty('id');
        expect(agent).toHaveProperty('label');
        expect(agent).toHaveProperty('icon');
        expect(agent).toHaveProperty('color');
        expect(agent).toHaveProperty('category');
        expect(agent).toHaveProperty('builtin', true);
      });
    });

    test('should include new high-priority agents', () => {
      const agents = loadBuiltinAgents();
      const agentIds = agents.map(a => a.id);

      expect(agentIds).toContain('DevOps');
      expect(agentIds).toContain('Security');
      expect(agentIds).toContain('DataArchitect');
      expect(agentIds).toContain('Marketing');
      expect(agentIds).toContain('Legal');
    });
  });

  describe('validateAgentSchema', () => {
    test('should validate correct agent schema', () => {
      const validAgent = {
        id: 'TestAgent',
        label: 'Test Agent',
        icon: '🧪',
        color: '#FF5733'
      };
      expect(validateAgentSchema(validAgent)).toBe(true);
    });

    test('should reject agent without id', () => {
      const invalidAgent = {
        label: 'Test Agent',
        icon: '🧪',
        color: '#FF5733'
      };
      expect(validateAgentSchema(invalidAgent)).toBe(false);
    });

    test('should reject agent with invalid color', () => {
      const invalidAgent = {
        id: 'TestAgent',
        label: 'Test Agent',
        icon: '🧪',
        color: 'invalid-color'
      };
      expect(validateAgentSchema(invalidAgent)).toBe(false);
    });
  });

  describe('saveCustomAgent', () => {
    test('should save valid custom agent to localStorage', () => {
      const customAgent = {
        id: 'CustomAgent',
        label: 'Custom Agent',
        icon: '🚀',
        color: '#667EEA',
        category: 'Engineering',
        defaultPrompt: 'Custom prompt',
        custom: true
      };

      const result = saveCustomAgent(customAgent);
      expect(result).toBe(true);

      const saved = localStorage.getItem('customAgents');
      expect(saved).toBeTruthy();

      const agents = JSON.parse(saved);
      expect(agents).toHaveLength(1);
      expect(agents[0].id).toBe('CustomAgent');
    });

    test('should reject duplicate agent IDs', () => {
      const agent1 = {
        id: 'DuplicateAgent',
        label: 'Agent 1',
        icon: '🚀',
        color: '#667EEA'
      };

      const agent2 = {
        id: 'DuplicateAgent',
        label: 'Agent 2',
        icon: '⚡',
        color: '#FF5733'
      };

      saveCustomAgent(agent1);
      const result = saveCustomAgent(agent2);

      expect(result).toBe(false);
    });
  });

  describe('loadAllAgents', () => {
    test('should merge built-in and custom agents', () => {
      const customAgent = {
        id: 'CustomAgent',
        label: 'Custom Agent',
        icon: '🚀',
        color: '#667EEA'
      };

      saveCustomAgent(customAgent);
      const allAgents = loadAllAgents();

      // Should have 20 built-in + 1 custom = 21 total
      expect(allAgents.length).toBeGreaterThanOrEqual(21);

      const hasCustom = allAgents.some(a => a.id === 'CustomAgent');
      expect(hasCustom).toBe(true);
    });
  });

  describe('favorites system', () => {
    test('should toggle favorite on and off', () => {
      expect(isFavorite('PM')).toBe(false);

      toggleFavorite('PM');
      expect(isFavorite('PM')).toBe(true);

      toggleFavorite('PM');
      expect(isFavorite('PM')).toBe(false);
    });

    test('should get all favorite agents', () => {
      toggleFavorite('DevOps');
      toggleFavorite('Security');

      const favorites = getFavoriteAgents();
      expect(favorites).toHaveLength(2);
      expect(favorites.map(a => a.id)).toContain('DevOps');
      expect(favorites.map(a => a.id)).toContain('Security');
    });

    test('should persist favorites in localStorage', () => {
      toggleFavorite('PM');

      const saved = localStorage.getItem('favoriteAgents');
      expect(saved).toBeTruthy();

      const favorites = JSON.parse(saved);
      expect(favorites).toContain('PM');
    });
  });

  describe('searchAgents', () => {
    test('should filter agents by label', () => {
      const agents = loadBuiltinAgents();
      const results = searchAgents('dev', agents);

      const hasDevOps = results.some(a => a.id === 'DevOps');
      expect(hasDevOps).toBe(true);
    });

    test('should be case-insensitive', () => {
      const agents = loadBuiltinAgents();
      const results1 = searchAgents('security', agents);
      const results2 = searchAgents('SECURITY', agents);

      expect(results1.length).toBe(results2.length);
    });

    test('should search by category', () => {
      const agents = loadBuiltinAgents();
      const results = searchAgents('engineering', agents);

      expect(results.length).toBeGreaterThan(0);
      results.forEach(agent => {
        expect(agent.category).toBe('Engineering');
      });
    });

    test('should return empty array for no matches', () => {
      const agents = loadBuiltinAgents();
      const results = searchAgents('xyz123nonexistent', agents);

      expect(results).toHaveLength(0);
    });
  });

  describe('getAgentCategories', () => {
    test('should return 5 categories', () => {
      const categories = getAgentCategories();
      const categoryIds = Object.keys(categories);

      expect(categoryIds).toHaveLength(5);
      expect(categoryIds).toContain('Engineering');
      expect(categoryIds).toContain('Operations');
      expect(categoryIds).toContain('Strategy');
      expect(categoryIds).toContain('DataAI');
      expect(categoryIds).toContain('QualitySecurity');
    });

    test('should have metadata for each category', () => {
      const categories = getAgentCategories();

      Object.values(categories).forEach(category => {
        expect(category).toHaveProperty('label');
        expect(category).toHaveProperty('icon');
        expect(category).toHaveProperty('agents');
        expect(Array.isArray(category.agents)).toBe(true);
      });
    });
  });

  describe('deleteCustomAgent', () => {
    test('should delete custom agent by id', () => {
      const customAgent = {
        id: 'ToDelete',
        label: 'To Delete',
        icon: '🗑️',
        color: '#FF5733'
      };

      saveCustomAgent(customAgent);
      expect(loadCustomAgents()).toHaveLength(1);

      deleteCustomAgent('ToDelete');
      expect(loadCustomAgents()).toHaveLength(0);
    });

    test('should not affect built-in agents', () => {
      const beforeCount = loadBuiltinAgents().length;
      deleteCustomAgent('PM'); // Try to delete built-in
      const afterCount = loadBuiltinAgents().length;

      expect(beforeCount).toBe(afterCount);
    });
  });
});
