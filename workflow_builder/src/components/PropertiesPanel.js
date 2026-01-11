import React, { useState, useEffect } from 'react';
import './PropertiesPanel.css';

const MODEL_OPTIONS = [
  { value: 'claude-3-5-sonnet-20241022', label: 'Claude 3.5 Sonnet (Balanced)' },
  { value: 'claude-opus-4-5-20251101', label: 'Claude Opus 4.5 (Highest Quality)' },
  { value: 'claude-3-haiku-20240307', label: 'Claude 3 Haiku (Fastest)' },
];

const PropertiesPanel = ({ selectedNode, onNodeDataChange }) => {
  const [prompt, setPrompt] = useState('');
  const [model, setModel] = useState('claude-3-5-sonnet-20241022');

  useEffect(() => {
    if (selectedNode) {
      setPrompt(selectedNode.data.prompt || '');
      setModel(selectedNode.data.model || 'claude-3-5-sonnet-20241022');
    }
  }, [selectedNode]);

  const handlePromptChange = (e) => {
    const newPrompt = e.target.value;
    setPrompt(newPrompt);
    if (selectedNode) {
      onNodeDataChange(selectedNode.id, { prompt: newPrompt });
    }
  };

  const handleModelChange = (e) => {
    const newModel = e.target.value;
    setModel(newModel);
    if (selectedNode) {
      onNodeDataChange(selectedNode.id, { model: newModel });
    }
  };

  if (!selectedNode) {
    return (
      <div className="properties-panel">
        <div className="properties-header">
          <h3>Properties</h3>
        </div>
        <div className="properties-empty">
          <p>Select an agent node to edit its properties</p>
        </div>
      </div>
    );
  }

  return (
    <div className="properties-panel">
      <div className="properties-header">
        <h3>Properties</h3>
        <div className="selected-agent" style={{ backgroundColor: selectedNode.data.color }}>
          <span>{selectedNode.data.icon}</span>
          <span>{selectedNode.data.label}</span>
        </div>
      </div>

      <div className="properties-content">
        <div className="property-group">
          <label htmlFor="agent-type">Agent Type</label>
          <input
            id="agent-type"
            type="text"
            value={selectedNode.data.agentType}
            disabled
            className="property-input disabled"
          />
        </div>

        <div className="property-group">
          <label htmlFor="agent-model">Model</label>
          <select
            id="agent-model"
            value={model}
            onChange={handleModelChange}
            className="property-select"
          >
            {MODEL_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        <div className="property-group">
          <label htmlFor="agent-prompt">
            Custom Prompt
            <span className="optional">(optional)</span>
          </label>
          <textarea
            id="agent-prompt"
            value={prompt}
            onChange={handlePromptChange}
            className="property-textarea"
            placeholder="Enter custom prompt for this agent..."
            rows={8}
          />
          <p className="property-hint">
            Leave empty to use the agent's default prompt
          </p>
        </div>

        <div className="property-group">
          <label>Node ID</label>
          <input
            type="text"
            value={selectedNode.id}
            disabled
            className="property-input disabled small-text"
          />
        </div>
      </div>
    </div>
  );
};

export default PropertiesPanel;
