/**
 * Agent Loader Utility
 *
 * Loads agents from the config file and merges with custom agents from localStorage.
 * Provides validation and helper functions for agent management.
 */

import agentConfig from '../config/agents.config.json';

const CUSTOM_AGENTS_KEY = 'customAgents';
const FAVORITES_KEY = 'favoriteAgents';

/**
 * Load all built-in agents from the config file
 * @returns {Array} Array of built-in agent objects
 */
export const loadBuiltinAgents = () => {
  return agentConfig.agents;
};

/**
 * Load custom agents from localStorage
 * @returns {Array} Array of custom agent objects
 */
export const loadCustomAgents = () => {
  try {
    const customAgentsJSON = localStorage.getItem(CUSTOM_AGENTS_KEY);
    if (!customAgentsJSON) return [];

    const customAgents = JSON.parse(customAgentsJSON);

    // Validate custom agents structure
    return customAgents.filter(agent => validateAgentSchema(agent));
  } catch (error) {
    console.error('Error loading custom agents:', error);
    return [];
  }
};

/**
 * Load all agents (built-in + custom)
 * @returns {Array} Combined array of all agent objects
 */
export const loadAllAgents = () => {
  const builtinAgents = loadBuiltinAgents();
  const customAgents = loadCustomAgents();

  return [...builtinAgents, ...customAgents];
};

/**
 * Get agent categories from config
 * @returns {Object} Categories object with metadata
 */
export const getAgentCategories = () => {
  return agentConfig.categories;
};

/**
 * Get agents organized by category
 * @returns {Object} Object with category IDs as keys and agent arrays as values
 */
export const getAgentsByCategory = () => {
  const allAgents = loadAllAgents();
  const categories = getAgentCategories();
  const agentsByCategory = {};

  // Initialize categories
  Object.keys(categories).forEach(categoryId => {
    agentsByCategory[categoryId] = [];
  });

  // Add an "Uncategorized" category for agents without a category
  agentsByCategory['Uncategorized'] = [];

  // Organize agents by category
  allAgents.forEach(agent => {
    const category = agent.category || 'Uncategorized';

    // Find the category ID that contains this agent
    const categoryId = Object.keys(categories).find(catId =>
      categories[catId].agents && categories[catId].agents.includes(agent.id)
    );

    if (categoryId && agentsByCategory[categoryId]) {
      agentsByCategory[categoryId].push(agent);
    } else if (agent.category && agentsByCategory[agent.category]) {
      agentsByCategory[agent.category].push(agent);
    } else {
      agentsByCategory['Uncategorized'].push(agent);
    }
  });

  return agentsByCategory;
};

/**
 * Save a custom agent to localStorage
 * @param {Object} agent - The custom agent object to save
 * @returns {boolean} True if saved successfully
 */
export const saveCustomAgent = (agent) => {
  try {
    if (!validateAgentSchema(agent)) {
      throw new Error('Invalid agent schema');
    }

    const customAgents = loadCustomAgents();

    // Check if agent with same ID already exists
    const existingIndex = customAgents.findIndex(a => a.id === agent.id);

    if (existingIndex >= 0) {
      // Update existing agent
      customAgents[existingIndex] = { ...agent, builtin: false, custom: true };
    } else {
      // Add new agent
      customAgents.push({ ...agent, builtin: false, custom: true });
    }

    localStorage.setItem(CUSTOM_AGENTS_KEY, JSON.stringify(customAgents));
    return true;
  } catch (error) {
    console.error('Error saving custom agent:', error);
    return false;
  }
};

/**
 * Delete a custom agent from localStorage
 * @param {string} agentId - The ID of the agent to delete
 * @returns {boolean} True if deleted successfully
 */
export const deleteCustomAgent = (agentId) => {
  try {
    const customAgents = loadCustomAgents();
    const filteredAgents = customAgents.filter(agent => agent.id !== agentId);

    localStorage.setItem(CUSTOM_AGENTS_KEY, JSON.stringify(filteredAgents));
    return true;
  } catch (error) {
    console.error('Error deleting custom agent:', error);
    return false;
  }
};

/**
 * Find an agent by ID
 * @param {string} agentId - The agent ID to find
 * @returns {Object|null} The agent object or null if not found
 */
export const findAgentById = (agentId) => {
  const allAgents = loadAllAgents();
  return allAgents.find(agent => agent.id === agentId) || null;
};

/**
 * Validate an agent object schema
 * @param {Object} agent - The agent object to validate
 * @returns {boolean} True if valid
 */
export const validateAgentSchema = (agent) => {
  if (!agent || typeof agent !== 'object') return false;

  const requiredFields = ['id', 'label', 'icon', 'color'];

  for (const field of requiredFields) {
    if (!agent[field] || typeof agent[field] !== 'string') {
      return false;
    }
  }

  // Validate color is a valid hex color
  const colorRegex = /^#[0-9A-F]{6}$/i;
  if (!colorRegex.test(agent.color)) {
    return false;
  }

  return true;
};

/**
 * Check if an agent is a custom agent
 * @param {Object} agent - The agent object
 * @returns {boolean} True if custom agent
 */
export const isCustomAgent = (agent) => {
  return agent.custom === true || agent.builtin === false;
};

/**
 * Load favorite agent IDs from localStorage
 * @returns {Array} Array of favorited agent IDs
 */
export const loadFavorites = () => {
  try {
    const favoritesJSON = localStorage.getItem(FAVORITES_KEY);
    if (!favoritesJSON) return [];

    return JSON.parse(favoritesJSON);
  } catch (error) {
    console.error('Error loading favorites:', error);
    return [];
  }
};

/**
 * Save favorite agent IDs to localStorage
 * @param {Array} favorites - Array of agent IDs
 * @returns {boolean} True if saved successfully
 */
export const saveFavorites = (favorites) => {
  try {
    localStorage.setItem(FAVORITES_KEY, JSON.stringify(favorites));
    return true;
  } catch (error) {
    console.error('Error saving favorites:', error);
    return false;
  }
};

/**
 * Toggle favorite status for an agent
 * @param {string} agentId - The agent ID to toggle
 * @returns {boolean} True if now favorited, false if unfavorited
 */
export const toggleFavorite = (agentId) => {
  const favorites = loadFavorites();
  const index = favorites.indexOf(agentId);

  if (index >= 0) {
    // Remove from favorites
    favorites.splice(index, 1);
    saveFavorites(favorites);
    return false;
  } else {
    // Add to favorites
    favorites.push(agentId);
    saveFavorites(favorites);
    return true;
  }
};

/**
 * Check if an agent is favorited
 * @param {string} agentId - The agent ID to check
 * @returns {boolean} True if favorited
 */
export const isFavorite = (agentId) => {
  const favorites = loadFavorites();
  return favorites.includes(agentId);
};

/**
 * Search agents by query string
 * @param {string} query - Search query
 * @param {Array} agents - Optional array of agents to search (defaults to all agents)
 * @returns {Array} Filtered array of matching agents
 */
export const searchAgents = (query, agents = null) => {
  if (!query || query.trim() === '') {
    return agents || loadAllAgents();
  }

  const searchQuery = query.toLowerCase().trim();

  // Note: No minimum length requirement - searches work with any length including 1-2 characters
  // This allows searching for short terms like "PM", "QA", "iOS", etc.

  const agentsToSearch = agents || loadAllAgents();

  return agentsToSearch.filter(agent => {
    const labelMatch = agent.label && agent.label.toLowerCase().includes(searchQuery);
    const idMatch = agent.id && agent.id.toLowerCase().includes(searchQuery);
    const categoryMatch = agent.category && agent.category.toLowerCase().includes(searchQuery);
    const promptMatch = agent.defaultPrompt && agent.defaultPrompt.toLowerCase().includes(searchQuery);

    return labelMatch || idMatch || categoryMatch || promptMatch;
  });
};

/**
 * Get agents that are favorited
 * @returns {Array} Array of favorited agent objects
 */
export const getFavoriteAgents = () => {
  const favorites = loadFavorites();
  const allAgents = loadAllAgents();

  return allAgents.filter(agent => favorites.includes(agent.id));
};

/**
 * Export custom agents to JSON
 * @returns {string} JSON string of custom agents
 */
export const exportCustomAgents = () => {
  const customAgents = loadCustomAgents();
  return JSON.stringify(customAgents, null, 2);
};

/**
 * Import custom agents from JSON
 * @param {string} jsonString - JSON string of custom agents
 * @returns {boolean} True if imported successfully
 */
export const importCustomAgents = (jsonString) => {
  try {
    const importedAgents = JSON.parse(jsonString);

    if (!Array.isArray(importedAgents)) {
      throw new Error('Invalid format: expected an array');
    }

    // Validate all agents
    const validAgents = importedAgents.filter(agent => validateAgentSchema(agent));

    if (validAgents.length === 0) {
      throw new Error('No valid agents found in import');
    }

    // Merge with existing custom agents (avoid duplicates)
    const existingAgents = loadCustomAgents();
    const mergedAgents = [...existingAgents];

    validAgents.forEach(agent => {
      const existingIndex = mergedAgents.findIndex(a => a.id === agent.id);
      if (existingIndex >= 0) {
        mergedAgents[existingIndex] = { ...agent, builtin: false, custom: true };
      } else {
        mergedAgents.push({ ...agent, builtin: false, custom: true });
      }
    });

    localStorage.setItem(CUSTOM_AGENTS_KEY, JSON.stringify(mergedAgents));
    return true;
  } catch (error) {
    console.error('Error importing custom agents:', error);
    return false;
  }
};

export default {
  loadBuiltinAgents,
  loadCustomAgents,
  loadAllAgents,
  getAgentCategories,
  getAgentsByCategory,
  saveCustomAgent,
  deleteCustomAgent,
  findAgentById,
  validateAgentSchema,
  isCustomAgent,
  loadFavorites,
  saveFavorites,
  toggleFavorite,
  isFavorite,
  searchAgents,
  getFavoriteAgents,
  exportCustomAgents,
  importCustomAgents
};
