import React, { useState, useEffect } from 'react';
import { Plus, FolderOpen, Search } from 'lucide-react';
import ProjectCard from '../components/projects/ProjectCard';
import TeamBuilder from '../components/projects/TeamBuilder';
import CheckpointModal from '../components/projects/CheckpointModal';
import {
  getProjects,
  createProject,
  updateProject,
  deleteProject,
  addTeam,
  updateTeam,
  deleteTeam,
  reorderTeams,
  executeProject,
  continueExecution
} from '../api/projectsApi';
import './Projects.css';

const Projects = () => {
  const [projects, setProjects] = useState([]);
  const [selectedProject, setSelectedProject] = useState(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [newProject, setNewProject] = useState({
    name: '',
    description: ''
  });

  // Checkpoint state
  const [checkpointData, setCheckpointData] = useState(null);
  const [showCheckpoint, setShowCheckpoint] = useState(false);

  // Load projects on mount
  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = () => {
    const loadedProjects = getProjects();
    setProjects(loadedProjects);
  };

  const handleCreateProject = () => {
    if (!newProject.name.trim()) {
      alert('Please enter a project name');
      return;
    }

    const created = createProject(newProject);
    setNewProject({ name: '', description: '' });
    setShowCreateForm(false);
    loadProjects();
    setSelectedProject(created);
  };

  const handleUpdateProject = (projectId, updates) => {
    updateProject(projectId, updates);
    loadProjects();
    if (selectedProject && selectedProject.id === projectId) {
      setSelectedProject({ ...selectedProject, ...updates });
    }
  };

  const handleDeleteProject = (project) => {
    if (window.confirm(`Delete project "${project.name}"? This cannot be undone.`)) {
      deleteProject(project.id);
      loadProjects();
      if (selectedProject && selectedProject.id === project.id) {
        setSelectedProject(null);
      }
    }
  };

  const handleRunProject = async (project) => {
    if (project.teams.length === 0) {
      alert('Please add at least one team before running the project');
      return;
    }

    if (!window.confirm(`Run project "${project.name}"? This will execute all teams sequentially.`)) {
      return;
    }

    try {
      // Update status to running
      handleUpdateProject(project.id, { status: 'running' });

      // Execute project
      const execution = await executeProject(project.id);

      // Check if checkpoint is needed
      if (execution.status === 'pending_checkpoint') {
        const lastTeamExecution = execution.teamExecutions[execution.teamExecutions.length - 1];
        const team = project.teams.find(t => t.id === lastTeamExecution.teamId);

        setCheckpointData({
          projectId: project.id,
          executionId: execution.id,
          teamName: team.name,
          teamOutput: lastTeamExecution.output,
          aiReview: analyzeOutput(lastTeamExecution.output)
        });
        setShowCheckpoint(true);
      } else {
        // Execution complete
        alert(`Project "${project.name}" completed successfully!`);
        loadProjects();
      }
    } catch (error) {
      console.error('Error running project:', error);
      alert(`Error running project: ${error.message}`);
      handleUpdateProject(project.id, { status: 'failed' });
    }
  };

  const handleCheckpointApprove = async () => {
    setShowCheckpoint(false);
    try {
      const execution = await continueExecution(
        checkpointData.projectId,
        checkpointData.executionId,
        'approve'
      );

      if (execution.status === 'pending_checkpoint') {
        // Another checkpoint needed
        const project = projects.find(p => p.id === checkpointData.projectId);
        const lastTeamExecution = execution.teamExecutions[execution.teamExecutions.length - 1];
        const team = project.teams.find(t => t.id === lastTeamExecution.teamId);

        setCheckpointData({
          ...checkpointData,
          executionId: execution.id,
          teamName: team.name,
          teamOutput: lastTeamExecution.output,
          aiReview: analyzeOutput(lastTeamExecution.output)
        });
        setShowCheckpoint(true);
      } else {
        // Execution complete
        alert('Project completed successfully!');
        loadProjects();
        setCheckpointData(null);
      }
    } catch (error) {
      console.error('Error continuing execution:', error);
      alert(`Error: ${error.message}`);
    }
  };

  const handleCheckpointDeny = async (reason) => {
    setShowCheckpoint(false);
    try {
      await continueExecution(checkpointData.projectId, checkpointData.executionId, 'deny');
      alert(`Execution denied: ${reason}`);
      loadProjects();
      setCheckpointData(null);
    } catch (error) {
      console.error('Error denying checkpoint:', error);
      alert(`Error: ${error.message}`);
    }
  };

  const handleCheckpointEdit = async (editedOutput) => {
    setShowCheckpoint(false);
    try {
      const execution = await continueExecution(
        checkpointData.projectId,
        checkpointData.executionId,
        'edit',
        editedOutput
      );

      if (execution.status === 'pending_checkpoint') {
        // Another checkpoint needed
        const project = projects.find(p => p.id === checkpointData.projectId);
        const lastTeamExecution = execution.teamExecutions[execution.teamExecutions.length - 1];
        const team = project.teams.find(t => t.id === lastTeamExecution.teamId);

        setCheckpointData({
          ...checkpointData,
          executionId: execution.id,
          teamName: team.name,
          teamOutput: lastTeamExecution.output,
          aiReview: analyzeOutput(lastTeamExecution.output)
        });
        setShowCheckpoint(true);
      } else {
        // Execution complete
        alert('Project completed successfully!');
        loadProjects();
        setCheckpointData(null);
      }
    } catch (error) {
      console.error('Error continuing execution:', error);
      alert(`Error: ${error.message}`);
    }
  };

  const handleCheckpointSkip = () => {
    handleCheckpointApprove();
  };

  const handleAddTeam = (teamData) => {
    if (!selectedProject) return;
    addTeam(selectedProject.id, teamData);
    loadProjects();
    setSelectedProject(getProjects().find(p => p.id === selectedProject.id));
  };

  const handleUpdateTeam = (teamId, updates) => {
    if (!selectedProject) return;
    updateTeam(selectedProject.id, teamId, updates);
    loadProjects();
    setSelectedProject(getProjects().find(p => p.id === selectedProject.id));
  };

  const handleDeleteTeam = (teamId) => {
    if (!selectedProject) return;
    if (window.confirm('Delete this team? This cannot be undone.')) {
      deleteTeam(selectedProject.id, teamId);
      loadProjects();
      setSelectedProject(getProjects().find(p => p.id === selectedProject.id));
    }
  };

  const handleReorderTeams = (teamIds) => {
    if (!selectedProject) return;
    reorderTeams(selectedProject.id, teamIds);
    loadProjects();
    setSelectedProject(getProjects().find(p => p.id === selectedProject.id));
  };

  const analyzeOutput = (output) => {
    // Simple AI review simulation
    // In production, this would call an AI model
    const wordCount = output.split(' ').length;

    if (wordCount < 50) {
      return {
        status: 'warning',
        message: '⚠️ Output seems short. Consider reviewing for completeness.',
        issues: ['Output is shorter than expected (< 50 words)']
      };
    }

    if (output.toLowerCase().includes('error') || output.toLowerCase().includes('failed')) {
      return {
        status: 'rejected',
        message: '❌ Output contains error indicators. Manual review required.',
        issues: ['Output mentions errors or failures']
      };
    }

    return {
      status: 'approved',
      message: '✅ Output looks good! Ready to continue.',
      issues: []
    };
  };

  const filteredProjects = projects.filter(project =>
    project.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    project.description.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (selectedProject) {
    return (
      <div className="projects-page">
        <div className="project-detail-header">
          <button
            className="back-btn"
            onClick={() => setSelectedProject(null)}
          >
            ← Back to Projects
          </button>
          <div className="project-title-section">
            <h1>{selectedProject.name}</h1>
            <p className="project-description">{selectedProject.description}</p>
          </div>
          <button
            className="run-project-btn"
            onClick={() => handleRunProject(selectedProject)}
            disabled={selectedProject.status === 'running'}
          >
            {selectedProject.status === 'running' ? 'Running...' : 'Run Project'}
          </button>
        </div>

        <div className="project-detail-content">
          <TeamBuilder
            teams={selectedProject.teams}
            onAddTeam={handleAddTeam}
            onUpdateTeam={handleUpdateTeam}
            onDeleteTeam={handleDeleteTeam}
            onReorderTeams={handleReorderTeams}
          />
        </div>

        <CheckpointModal
          isOpen={showCheckpoint}
          teamName={checkpointData?.teamName}
          teamOutput={checkpointData?.teamOutput}
          aiReview={checkpointData?.aiReview}
          onApprove={handleCheckpointApprove}
          onDeny={handleCheckpointDeny}
          onEdit={handleCheckpointEdit}
          onSkip={handleCheckpointSkip}
        />
      </div>
    );
  }

  return (
    <div className="projects-page">
      <div className="projects-header">
        <div className="header-content">
          <h1>Projects</h1>
          <p className="header-subtitle">Organize your AI agent workflows into projects and teams</p>
        </div>
        <button
          className="create-project-btn"
          onClick={() => setShowCreateForm(true)}
        >
          <Plus size={18} />
          New Project
        </button>
      </div>

      {showCreateForm && (
        <div className="create-project-form">
          <div className="form-header">
            <h3>Create New Project</h3>
            <button className="close-form-btn" onClick={() => setShowCreateForm(false)}>
              ×
            </button>
          </div>
          <div className="form-group">
            <label>Project Name *</label>
            <input
              type="text"
              value={newProject.name}
              onChange={(e) => setNewProject({ ...newProject, name: e.target.value })}
              placeholder="e.g., E-commerce Platform, Mobile App Redesign"
              autoFocus
            />
          </div>
          <div className="form-group">
            <label>Description</label>
            <textarea
              value={newProject.description}
              onChange={(e) => setNewProject({ ...newProject, description: e.target.value })}
              placeholder="What is this project about?"
              rows={3}
            />
          </div>
          <div className="form-actions">
            <button className="cancel-btn" onClick={() => setShowCreateForm(false)}>
              Cancel
            </button>
            <button className="create-btn" onClick={handleCreateProject}>
              Create Project
            </button>
          </div>
        </div>
      )}

      <div className="search-section">
        <div className="search-input-wrapper">
          <Search size={18} className="search-icon" />
          <input
            type="text"
            className="search-input"
            placeholder="Search projects..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
      </div>

      {filteredProjects.length === 0 && !showCreateForm && (
        <div className="empty-state">
          <FolderOpen size={64} className="empty-icon" />
          <h2>No projects yet</h2>
          <p>Create your first project to organize AI agent workflows</p>
          <button className="create-first-btn" onClick={() => setShowCreateForm(true)}>
            <Plus size={18} />
            Create Your First Project
          </button>
        </div>
      )}

      {filteredProjects.length > 0 && (
        <div className="projects-grid">
          {filteredProjects.map(project => (
            <ProjectCard
              key={project.id}
              project={project}
              onRun={handleRunProject}
              onEdit={(proj) => setSelectedProject(proj)}
              onDelete={handleDeleteProject}
              onClick={() => setSelectedProject(project)}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default Projects;
