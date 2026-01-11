import React, { useState } from 'react';
import { AlertCircle, AlertTriangle, Info, CheckCircle, ChevronDown, ChevronRight } from 'lucide-react';
import './ValidationPanel.css';
import { ValidationSeverity, getValidationSummary } from '../utils/workflowValidator';

/**
 * ValidationPanel Component
 *
 * Displays workflow validation results with errors, warnings, and info messages
 * Supports collapsible sections and clickable errors to highlight nodes
 */
const ValidationPanel = ({ validationResult, onErrorClick }) => {
  const [expandedErrors, setExpandedErrors] = useState(true);
  const [expandedWarnings, setExpandedWarnings] = useState(true);
  const [expandedInfo, setExpandedInfo] = useState(false);

  if (!validationResult) {
    return (
      <div className="validation-panel">
        <div className="validation-summary">
          <Info size={16} />
          <span>No validation data available</span>
        </div>
      </div>
    );
  }

  const { valid, errors = [], warnings = [], info = [] } = validationResult;
  const summary = getValidationSummary(validationResult);

  const handleItemClick = (item) => {
    if (onErrorClick && item.nodeIds && item.nodeIds.length > 0) {
      onErrorClick(item.nodeIds);
    }
  };

  return (
    <div className="validation-panel">
      {/* Summary */}
      <div className={`validation-summary ${valid ? 'valid' : 'invalid'}`}>
        {valid ? <CheckCircle size={16} /> : <AlertCircle size={16} />}
        <span>{summary}</span>
      </div>

      {/* Errors Section */}
      {errors.length > 0 && (
        <div className="validation-section">
          <div
            className="validation-section-header error"
            onClick={() => setExpandedErrors(!expandedErrors)}
          >
            {expandedErrors ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
            <AlertCircle size={16} />
            <span>Errors ({errors.length})</span>
          </div>
          {expandedErrors && (
            <div className="validation-items">
              {errors.map((error, index) => (
                <ValidationItem
                  key={`error-${index}`}
                  item={error}
                  severity="error"
                  onClick={() => handleItemClick(error)}
                />
              ))}
            </div>
          )}
        </div>
      )}

      {/* Warnings Section */}
      {warnings.length > 0 && (
        <div className="validation-section">
          <div
            className="validation-section-header warning"
            onClick={() => setExpandedWarnings(!expandedWarnings)}
          >
            {expandedWarnings ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
            <AlertTriangle size={16} />
            <span>Warnings ({warnings.length})</span>
          </div>
          {expandedWarnings && (
            <div className="validation-items">
              {warnings.map((warning, index) => (
                <ValidationItem
                  key={`warning-${index}`}
                  item={warning}
                  severity="warning"
                  onClick={() => handleItemClick(warning)}
                />
              ))}
            </div>
          )}
        </div>
      )}

      {/* Info Section */}
      {info.length > 0 && (
        <div className="validation-section">
          <div
            className="validation-section-header info"
            onClick={() => setExpandedInfo(!expandedInfo)}
          >
            {expandedInfo ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
            <Info size={16} />
            <span>Information ({info.length})</span>
          </div>
          {expandedInfo && (
            <div className="validation-items">
              {info.map((infoItem, index) => (
                <ValidationItem
                  key={`info-${index}`}
                  item={infoItem}
                  severity="info"
                />
              ))}
            </div>
          )}
        </div>
      )}

      {/* Empty state */}
      {errors.length === 0 && warnings.length === 0 && info.length === 0 && (
        <div className="validation-empty">
          <CheckCircle size={24} />
          <p>All good! No validation issues found.</p>
        </div>
      )}
    </div>
  );
};

/**
 * ValidationItem Component
 *
 * Displays a single validation error, warning, or info message
 */
const ValidationItem = ({ item, severity, onClick }) => {
  const [expanded, setExpanded] = useState(false);

  const icon = {
    error: <AlertCircle size={14} />,
    warning: <AlertTriangle size={14} />,
    info: <Info size={14} />,
  }[severity];

  const hasDetails = item.details && item.details !== item.message;
  const isClickable = onClick && item.nodeIds && item.nodeIds.length > 0;

  return (
    <div
      className={`validation-item ${severity} ${isClickable ? 'clickable' : ''}`}
      onClick={isClickable ? onClick : undefined}
    >
      <div className="validation-item-header">
        {icon}
        <span className="validation-item-message">{item.message}</span>
        {hasDetails && (
          <button
            className="validation-item-toggle"
            onClick={(e) => {
              e.stopPropagation();
              setExpanded(!expanded);
            }}
            aria-label={expanded ? 'Hide details' : 'Show details'}
          >
            {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
          </button>
        )}
      </div>
      {expanded && hasDetails && (
        <div className="validation-item-details">
          {typeof item.details === 'string' ? (
            <p>{item.details}</p>
          ) : (
            <pre>{JSON.stringify(item.details, null, 2)}</pre>
          )}
        </div>
      )}
      {isClickable && (
        <div className="validation-item-hint">
          Click to highlight affected agents
        </div>
      )}
    </div>
  );
};

export default ValidationPanel;
