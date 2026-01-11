import React, { useRef } from 'react';
import { Save, Upload, Download, Trash2, Play } from 'lucide-react';
import './ToolBar.css';

const ToolBar = ({ workflowName, onNameChange, onExport, onImport, onClear }) => {
  const fileInputRef = useRef(null);

  const handleImportClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="toolbar">
      <div className="toolbar-left">
        <h1 className="toolbar-title">Multi-Agent Workflow Builder</h1>
        <input
          type="text"
          value={workflowName}
          onChange={(e) => onNameChange(e.target.value)}
          className="workflow-name-input"
          placeholder="Workflow name..."
        />
      </div>

      <div className="toolbar-right">
        <button
          className="toolbar-button"
          onClick={handleImportClick}
          title="Import workflow from YAML"
        >
          <Upload size={18} />
          <span>Import</span>
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept=".yaml,.yml"
          onChange={onImport}
          style={{ display: 'none' }}
        />

        <button
          className="toolbar-button"
          onClick={onExport}
          title="Export workflow to YAML"
        >
          <Download size={18} />
          <span>Export</span>
        </button>

        <button
          className="toolbar-button danger"
          onClick={onClear}
          title="Clear workflow"
        >
          <Trash2 size={18} />
          <span>Clear</span>
        </button>

        <div className="toolbar-divider"></div>

        <button
          className="toolbar-button primary"
          title="Run workflow (coming soon)"
          disabled
        >
          <Play size={18} />
          <span>Run</span>
        </button>
      </div>
    </div>
  );
};

export default ToolBar;
