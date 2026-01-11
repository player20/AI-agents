import React, { useState } from 'react';
import { Workflow, FolderKanban } from 'lucide-react';
import WorkflowBuilder from './components/WorkflowBuilder';
import Projects from './pages/Projects';
import './App.css';

function App() {
  const [currentView, setCurrentView] = useState('workflows');

  return (
    <div className="App">
      <nav className="app-nav">
        <div className="nav-brand">
          <h1>Multi-Agent Platform</h1>
        </div>
        <div className="nav-tabs">
          <button
            className={`nav-tab ${currentView === 'workflows' ? 'active' : ''}`}
            onClick={() => setCurrentView('workflows')}
          >
            <Workflow size={18} />
            Workflows
          </button>
          <button
            className={`nav-tab ${currentView === 'projects' ? 'active' : ''}`}
            onClick={() => setCurrentView('projects')}
          >
            <FolderKanban size={18} />
            Projects
          </button>
        </div>
      </nav>

      <div className="app-content">
        {currentView === 'workflows' && <WorkflowBuilder />}
        {currentView === 'projects' && <Projects />}
      </div>
    </div>
  );
}

export default App;
