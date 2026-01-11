import React, { memo } from 'react';
import { Handle, Position } from 'reactflow';
import './AgentNode.css';

const AgentNode = ({ data, selected }) => {
  return (
    <div
      className={`agent-node ${selected ? 'selected' : ''}`}
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
