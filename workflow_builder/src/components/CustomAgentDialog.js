import React, { useState } from 'react';
import { saveCustomAgent, getAgentCategories } from '../utils/agentLoader';
import './CustomAgentDialog.css';

/**
 * CustomAgentDialog component for creating custom agents
 * Provides a form to define agent properties and save to localStorage
 */
const CustomAgentDialog = ({ isOpen, onClose, onAgentCreated }) => {
  const [agentName, setAgentName] = useState('');
  const [agentIcon, setAgentIcon] = useState('🚀');
  const [agentColor, setAgentColor] = useState('#667eea');
  const [agentCategory, setAgentCategory] = useState('Engineering');
  const [agentPrompt, setAgentPrompt] = useState('');
  const [errors, setErrors] = useState({});

  const categories = getAgentCategories();

  const validateForm = () => {
    const newErrors = {};

    if (!agentName.trim()) {
      newErrors.name = 'Agent name is required';
    }

    if (!agentIcon.trim()) {
      newErrors.icon = 'Agent icon is required';
    }

    if (!agentColor.match(/^#[0-9A-F]{6}$/i)) {
      newErrors.color = 'Invalid color format (use #RRGGBB)';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    // Create agent ID from name (lowercase, no spaces)
    const agentId = agentName.trim().replace(/\s+/g, '');

    const newAgent = {
      id: agentId,
      label: agentName.trim(),
      icon: agentIcon.trim(),
      color: agentColor.toUpperCase(),
      category: agentCategory,
      defaultPrompt: agentPrompt.trim() || `Custom agent for ${agentName}`,
      custom: true,
      builtin: false
    };

    // Save to localStorage
    const success = saveCustomAgent(newAgent);

    if (success) {
      // Reset form
      setAgentName('');
      setAgentIcon('🚀');
      setAgentColor('#667eea');
      setAgentCategory('Engineering');
      setAgentPrompt('');
      setErrors({});

      // Notify parent component
      if (onAgentCreated) {
        onAgentCreated(newAgent);
      }

      // Close dialog
      onClose();
    } else {
      setErrors({ submit: 'Failed to save custom agent. Please try again.' });
    }
  };

  const handleCancel = () => {
    // Reset form
    setAgentName('');
    setAgentIcon('🚀');
    setAgentColor('#667eea');
    setAgentCategory('Engineering');
    setAgentPrompt('');
    setErrors({});
    onClose();
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Escape') {
      handleCancel();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="dialog-overlay" onClick={handleCancel}>
      <div
        className="dialog-content"
        onClick={(e) => e.stopPropagation()}
        onKeyDown={handleKeyDown}
        role="dialog"
        aria-labelledby="dialog-title"
        aria-modal="true"
      >
        <div className="dialog-header">
          <h2 id="dialog-title">Create Custom Agent</h2>
          <button
            className="dialog-close-btn"
            onClick={handleCancel}
            aria-label="Close dialog"
            title="Close"
          >
            ✕
          </button>
        </div>

        <form className="dialog-form" onSubmit={handleSubmit}>
          {/* Agent Name */}
          <div className="form-group">
            <label htmlFor="agent-name" className="form-label">
              Agent Name <span className="required">*</span>
            </label>
            <input
              id="agent-name"
              type="text"
              className={`form-input ${errors.name ? 'error' : ''}`}
              value={agentName}
              onChange={(e) => setAgentName(e.target.value)}
              placeholder="e.g., Blockchain Developer"
              maxLength={50}
              autoFocus
            />
            {errors.name && <span className="error-message">{errors.name}</span>}
          </div>

          {/* Agent Icon */}
          <div className="form-group">
            <label htmlFor="agent-icon" className="form-label">
              Icon (Emoji) <span className="required">*</span>
            </label>
            <div className="icon-input-wrapper">
              <input
                id="agent-icon"
                type="text"
                className={`form-input icon-input ${errors.icon ? 'error' : ''}`}
                value={agentIcon}
                onChange={(e) => setAgentIcon(e.target.value)}
                placeholder="🚀"
                maxLength={4}
              />
              <span className="icon-preview" aria-hidden="true">{agentIcon}</span>
            </div>
            {errors.icon && <span className="error-message">{errors.icon}</span>}
            <p className="form-hint">Common emojis: 🔥 ⚡ 💎 🎯 🌟 ⚙️ 🛠️ 📊 🔒 🌐</p>
          </div>

          {/* Agent Color */}
          <div className="form-group">
            <label htmlFor="agent-color" className="form-label">
              Color <span className="required">*</span>
            </label>
            <div className="color-input-wrapper">
              <input
                id="agent-color"
                type="color"
                className="form-color-picker"
                value={agentColor}
                onChange={(e) => setAgentColor(e.target.value)}
              />
              <input
                type="text"
                className={`form-input color-text-input ${errors.color ? 'error' : ''}`}
                value={agentColor}
                onChange={(e) => setAgentColor(e.target.value)}
                placeholder="#667eea"
                maxLength={7}
                pattern="^#[0-9A-Fa-f]{6}$"
              />
              <div
                className="color-preview"
                style={{ backgroundColor: agentColor }}
                aria-label="Color preview"
              />
            </div>
            {errors.color && <span className="error-message">{errors.color}</span>}
          </div>

          {/* Agent Category */}
          <div className="form-group">
            <label htmlFor="agent-category" className="form-label">
              Category
            </label>
            <select
              id="agent-category"
              className="form-select"
              value={agentCategory}
              onChange={(e) => setAgentCategory(e.target.value)}
            >
              {Object.entries(categories).map(([categoryId, categoryInfo]) => (
                <option key={categoryId} value={categoryId}>
                  {categoryInfo.icon} {categoryInfo.label}
                </option>
              ))}
            </select>
          </div>

          {/* Agent Prompt */}
          <div className="form-group">
            <label htmlFor="agent-prompt" className="form-label">
              Default Prompt (Optional)
            </label>
            <textarea
              id="agent-prompt"
              className="form-textarea"
              value={agentPrompt}
              onChange={(e) => setAgentPrompt(e.target.value)}
              placeholder="Describe what this agent does and its responsibilities..."
              rows={4}
              maxLength={500}
            />
            <p className="form-hint">{agentPrompt.length}/500 characters</p>
          </div>

          {/* Submit Error */}
          {errors.submit && (
            <div className="error-banner" role="alert">
              {errors.submit}
            </div>
          )}

          {/* Form Actions */}
          <div className="dialog-actions">
            <button
              type="button"
              className="btn-secondary"
              onClick={handleCancel}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn-primary"
            >
              Create Agent
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CustomAgentDialog;
