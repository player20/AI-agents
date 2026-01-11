import React, { useState, useCallback, useMemo } from 'react';
import SearchBar from './SearchBar';
import {
  getAgentCategories,
  toggleFavorite,
  isFavorite,
  searchAgents,
  getFavoriteAgents
} from '../utils/agentLoader';
import './AgentPalette.css';

const AgentPalette = ({ agentTypes, onCreateCustomAgent }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [collapsedCategories, setCollapsedCategories] = useState({});
  const [favorites, setFavorites] = useState(getFavoriteAgents().map(a => a.id));

  const onDragStart = (event, agentType) => {
    event.dataTransfer.setData('application/reactflow', JSON.stringify(agentType));
    event.dataTransfer.effectAllowed = 'move';
  };

  const handleSearch = useCallback((query) => {
    setSearchQuery(query);
  }, []);

  const handleToggleFavorite = useCallback((agentId, event) => {
    event.stopPropagation();
    const nowFavorited = toggleFavorite(agentId);
    setFavorites(prev => {
      if (nowFavorited) {
        return [...prev, agentId];
      } else {
        return prev.filter(id => id !== agentId);
      }
    });
  }, []);

  const toggleCategory = useCallback((categoryId) => {
    setCollapsedCategories(prev => ({
      ...prev,
      [categoryId]: !prev[categoryId]
    }));
  }, []);

  // Filter agents based on search query
  const filteredAgents = useMemo(() => {
    if (!searchQuery || searchQuery.trim() === '') {
      return agentTypes;
    }
    return searchAgents(searchQuery, agentTypes);
  }, [searchQuery, agentTypes]);

  // Get categories and organize agents
  const categories = useMemo(() => getAgentCategories(), []);
  const agentsByCategory = useMemo(() => {
    // Organize filtered agents by category
    const organized = {};
    const categorizedAgentIds = new Set();

    // Initialize categories
    Object.keys(categories).forEach(categoryId => {
      organized[categoryId] = [];
    });

    // Organize agents by category
    filteredAgents.forEach(agent => {
      // Find which category this agent belongs to
      const categoryId = Object.keys(categories).find(catId =>
        categories[catId].agents && categories[catId].agents.includes(agent.id)
      );

      if (categoryId) {
        organized[categoryId].push(agent);
        categorizedAgentIds.add(agent.id);
      }
    });

    // Add uncategorized agents
    const uncategorized = filteredAgents.filter(agent => !categorizedAgentIds.has(agent.id));
    if (uncategorized.length > 0) {
      organized['Uncategorized'] = uncategorized;
    }

    return organized;
  }, [filteredAgents, categories]);

  // Get favorite agents
  const favoriteAgents = useMemo(() => {
    return filteredAgents.filter(agent => favorites.includes(agent.id));
  }, [filteredAgents, favorites]);

  const renderAgentItem = (agent, showFavorite = true) => (
    <div
      key={agent.id}
      className="palette-item"
      draggable
      onDragStart={(e) => onDragStart(e, agent)}
      style={{ borderLeftColor: agent.color }}
      title={agent.defaultPrompt || agent.label}
    >
      <span className="palette-icon">{agent.icon}</span>
      <span className="palette-label">{agent.label}</span>
      {agent.custom && <span className="custom-badge" title="Custom Agent">✨</span>}
      {showFavorite && (
        <button
          className={`favorite-btn ${isFavorite(agent.id) ? 'favorited' : ''}`}
          onClick={(e) => handleToggleFavorite(agent.id, e)}
          aria-label={isFavorite(agent.id) ? 'Remove from favorites' : 'Add to favorites'}
          title={isFavorite(agent.id) ? 'Remove from favorites' : 'Add to favorites'}
        >
          {isFavorite(agent.id) ? '★' : '☆'}
        </button>
      )}
    </div>
  );

  return (
    <div className="agent-palette">
      <div className="palette-header">
        <h3>Agent Nodes</h3>
        <p className="palette-hint">Drag agents to canvas</p>
      </div>

      <div className="palette-search">
        <SearchBar onSearch={handleSearch} placeholder="Search agents..." />
      </div>

      <div className="palette-content">
        {/* Favorites Section */}
        {favoriteAgents.length > 0 && (
          <div className="palette-category favorites-category">
            <div
              className="category-header"
              onClick={() => toggleCategory('Favorites')}
            >
              <span className="category-icon">⭐</span>
              <span className="category-label">Favorites</span>
              <span className="category-count">({favoriteAgents.length})</span>
              <span className={`category-toggle ${collapsedCategories['Favorites'] ? 'collapsed' : ''}`}>
                {collapsedCategories['Favorites'] ? '▶' : '▼'}
              </span>
            </div>
            {!collapsedCategories['Favorites'] && (
              <div className="category-items">
                {favoriteAgents.map(agent => renderAgentItem(agent, true))}
              </div>
            )}
          </div>
        )}

        {/* Category Sections */}
        {Object.entries(agentsByCategory).map(([categoryId, agents]) => {
          if (agents.length === 0) return null;

          const categoryInfo = categories[categoryId] || {
            label: categoryId,
            icon: '📁',
            description: ''
          };

          return (
            <div key={categoryId} className="palette-category">
              <div
                className="category-header"
                onClick={() => toggleCategory(categoryId)}
                title={categoryInfo.description}
              >
                <span className="category-icon">{categoryInfo.icon}</span>
                <span className="category-label">{categoryInfo.label}</span>
                <span className="category-count">({agents.length})</span>
                <span className={`category-toggle ${collapsedCategories[categoryId] ? 'collapsed' : ''}`}>
                  {collapsedCategories[categoryId] ? '▶' : '▼'}
                </span>
              </div>
              {!collapsedCategories[categoryId] && (
                <div className="category-items">
                  {agents.map(agent => renderAgentItem(agent, true))}
                </div>
              )}
            </div>
          );
        })}

        {/* No results message */}
        {filteredAgents.length === 0 && searchQuery && (
          <div className="no-results">
            <p>No agents found for "{searchQuery}"</p>
            <p className="no-results-hint">Try a different search term</p>
          </div>
        )}
      </div>

      <div className="palette-footer">
        {onCreateCustomAgent && (
          <button
            className="create-custom-btn"
            onClick={onCreateCustomAgent}
            title="Create your own custom agent"
          >
            + Create Custom Agent
          </button>
        )}

        <div className="palette-help">
          <p><strong>How to use:</strong></p>
          <ul>
            <li>Drag agents onto canvas</li>
            <li>Connect agents to define workflow</li>
            <li>Click agent to edit properties</li>
            <li>Star agents to add to favorites</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default AgentPalette;
