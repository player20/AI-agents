import React, { memo } from 'react';
import { Handle, Position } from 'reactflow';
import { CheckCircle, XCircle, Loader } from 'lucide-react';
import './AgentNode.css';

const AgentNode = ({ data, selected }) => {
  const executionState = data.executionState || 'idle'; // idle, running, completed, failed

  const getExecutionIndicator = () => {
    switch (executionState) {
      case 'running':
        return (
          <div className="execution-indicator running">
            <Loader size={16} className="spinner" />
          </div>
        );
      case 'completed':
        return (
          <div className="execution-indicator completed">
            <CheckCircle size={16} />
          </div>
        );
      case 'failed':
        return (
          <div className="execution-indicator failed">
            <XCircle size={16} />
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div
      className={`agent-node ${selected ? 'selected' : ''} ${executionState}`}
      style={{ borderColor: data.color }}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="node-handle"
        style={{ background: data.color }}
      />

      <div className="agent-node-header" style={{ backgroundColor: data.color }}>
        <span className="agent-icon">{data.icon}</span>
        <span className="agent-label">{data.label}</span>
        {getExecutionIndicator()}
      </div>

      <div className="agent-node-body">
        {data.prompt && (
          <div className="agent-prompt-preview">
            {data.prompt.substring(0, 60)}
            {data.prompt.length > 60 ? '...' : ''}
          </div>
        )}
        <div className="agent-model">
          <span className="model-label">Model:</span>
          <span className="model-value">
            {data.model === 'claude-3-5-sonnet-20241022'
              ? 'Sonnet'
              : data.model === 'claude-opus-4-5-20251101'
              ? 'Opus'
              : 'Haiku'}
          </span>
        </div>
      </div>

      <Handle
        type="source"
        position={Position.Bottom}
        className="node-handle"
        style={{ background: data.color }}
      />
    </div>
  );
};

export default memo(AgentNode);
