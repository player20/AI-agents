/**
 * Projects API - Handles project storage using JSON files
 * Connects to Gradio backend for agent execution
 */

const API_BASE_URL = 'http://localhost:7860';

/**
 * Get all projects from local storage
 */
export const getProjects = () => {
  try {
    const projects = localStorage.getItem('multi_agent_projects');
    return projects ? JSON.parse(projects) : [];
  } catch (error) {
    console.error('Error loading projects:', error);
    return [];
  }
};

/**
 * Get a single project by ID
 */
export const getProject = (projectId) => {
  const projects = getProjects();
  return projects.find(p => p.id === projectId);
};

/**
 * Create a new project
 */
export const createProject = (projectData) => {
  const projects = getProjects();
  const newProject = {
    id: `project-${Date.now()}`,
    name: projectData.name,
    description: projectData.description || '',
    teams: [],
    status: 'draft',
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    executions: []
  };

  projects.push(newProject);
  localStorage.setItem('multi_agent_projects', JSON.stringify(projects));
  return newProject;
};

/**
 * Update an existing project
 */
export const updateProject = (projectId, updates) => {
  const projects = getProjects();
  const index = projects.findIndex(p => p.id === projectId);

  if (index === -1) {
    throw new Error(`Project ${projectId} not found`);
  }

  projects[index] = {
    ...projects[index],
    ...updates,
    updatedAt: new Date().toISOString()
  };

  localStorage.setItem('multi_agent_projects', JSON.stringify(projects));
  return projects[index];
};

/**
 * Delete a project
 */
export const deleteProject = (projectId) => {
  const projects = getProjects();
  const filtered = projects.filter(p => p.id !== projectId);
  localStorage.setItem('multi_agent_projects', JSON.stringify(filtered));
  return true;
};

/**
 * Add a team to a project
 */
export const addTeam = (projectId, teamData) => {
  const project = getProject(projectId);
  if (!project) {
    throw new Error(`Project ${projectId} not found`);
  }

  const newTeam = {
    id: `team-${Date.now()}`,
    name: teamData.name,
    description: teamData.description || '',
    icon: teamData.icon || '👥',
    color: teamData.color || '#4A90E2',
    agents: teamData.agents || [],
    executionOrder: project.teams.length + 1,
    checkpointEnabled: teamData.checkpointEnabled !== undefined ? teamData.checkpointEnabled : true,
    createdAt: new Date().toISOString()
  };

  project.teams.push(newTeam);
  return updateProject(projectId, { teams: project.teams });
};

/**
 * Update a team within a project
 */
export const updateTeam = (projectId, teamId, updates) => {
  const project = getProject(projectId);
  if (!project) {
    throw new Error(`Project ${projectId} not found`);
  }

  const teamIndex = project.teams.findIndex(t => t.id === teamId);
  if (teamIndex === -1) {
    throw new Error(`Team ${teamId} not found`);
  }

  project.teams[teamIndex] = {
    ...project.teams[teamIndex],
    ...updates
  };

  return updateProject(projectId, { teams: project.teams });
};

/**
 * Delete a team from a project
 */
export const deleteTeam = (projectId, teamId) => {
  const project = getProject(projectId);
  if (!project) {
    throw new Error(`Project ${projectId} not found`);
  }

  project.teams = project.teams.filter(t => t.id !== teamId);
  // Reorder remaining teams
  project.teams.forEach((team, index) => {
    team.executionOrder = index + 1;
  });

  return updateProject(projectId, { teams: project.teams });
};

/**
 * Reorder teams in a project
 */
export const reorderTeams = (projectId, teamIds) => {
  const project = getProject(projectId);
  if (!project) {
    throw new Error(`Project ${projectId} not found`);
  }

  const reorderedTeams = teamIds.map((teamId, index) => {
    const team = project.teams.find(t => t.id === teamId);
    return {
      ...team,
      executionOrder: index + 1
    };
  });

  return updateProject(projectId, { teams: reorderedTeams });
};

/**
 * Execute a project (run all teams sequentially)
 * Connects to Gradio backend API
 */
export const executeProject = async (projectId) => {
  const project = getProject(projectId);
  if (!project) {
    throw new Error(`Project ${projectId} not found`);
  }

  const execution = {
    id: `exec-${Date.now()}`,
    projectId: project.id,
    status: 'running',
    startedAt: new Date().toISOString(),
    teamExecutions: [],
    totalCost: 0,
    totalDuration: 0
  };

  // Update project status
  updateProject(projectId, {
    status: 'running',
    currentExecution: execution.id
  });

  try {
    // Execute teams sequentially
    for (const team of project.teams.sort((a, b) => a.executionOrder - b.executionOrder)) {
      const teamExecution = await executeTeam(projectId, team.id, execution.id);
      execution.teamExecutions.push(teamExecution);

      // If checkpoint enabled, wait for approval
      if (team.checkpointEnabled && teamExecution.status === 'completed') {
        // Checkpoint will be handled by UI - pause execution here
        // Return execution with pending checkpoint
        execution.status = 'pending_checkpoint';
        execution.pendingTeamId = team.id;
        return execution;
      }
    }

    // All teams completed
    execution.status = 'completed';
    execution.completedAt = new Date().toISOString();
    execution.totalDuration = execution.teamExecutions.reduce((sum, te) => sum + (te.duration || 0), 0);
    execution.totalCost = execution.teamExecutions.reduce((sum, te) => sum + (te.cost || 0), 0);

    updateProject(projectId, {
      status: 'completed',
      currentExecution: null
    });

    // Store execution in project history
    project.executions.push(execution);
    updateProject(projectId, { executions: project.executions });

    return execution;
  } catch (error) {
    execution.status = 'failed';
    execution.error = error.message;
    execution.completedAt = new Date().toISOString();

    updateProject(projectId, {
      status: 'failed',
      currentExecution: null
    });

    throw error;
  }
};

/**
 * Execute a single team (calls Gradio backend)
 */
const executeTeam = async (projectId, teamId, executionId) => {
  const project = getProject(projectId);
  const team = project.teams.find(t => t.id === teamId);

  if (!team) {
    throw new Error(`Team ${teamId} not found`);
  }

  const teamExecution = {
    id: `team-exec-${Date.now()}`,
    teamId: team.id,
    executionId: executionId,
    status: 'running',
    startedAt: new Date().toISOString(),
    agentOutputs: []
  };

  try {
    // Build prompt with project context
    const prompt = project.description || "Execute the following agents";

    // Get previous team outputs for context
    const previousOutputs = getPreviousTeamOutputs(project, executionId);

    // Call Gradio API to execute agents
    const response = await fetch(`${API_BASE_URL}/api/execute-team`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        projectId: project.id,
        teamId: team.id,
        agents: team.agents,  // Array like ['PM', 'Senior', 'Web']
        prompt: prompt,
        previousOutputs: previousOutputs
      })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || `API error: ${response.statusText}`);
    }

    const result = await response.json();  // { executionId, status, message }
    const apiExecutionId = result.executionId;

    // Poll for completion
    let attempts = 0;
    const maxAttempts = 120;  // 2 minutes max (1s interval)

    while (attempts < maxAttempts) {
      await new Promise(resolve => setTimeout(resolve, 1000));  // Wait 1s

      const statusResponse = await fetch(`${API_BASE_URL}/api/status/${apiExecutionId}`);
      const status = await statusResponse.json();

      if (status.status === 'completed') {
        // Success!
        teamExecution.status = 'completed';
        teamExecution.completedAt = new Date().toISOString();
        teamExecution.agentOutputs = status.outputs || [];
        teamExecution.duration = status.duration || 0;
        teamExecution.cost = status.cost || 0;
        teamExecution.output = status.combinedOutput || '';
        return teamExecution;
      } else if (status.status === 'failed') {
        throw new Error(status.error || 'Execution failed');
      }

      // Update progress (optional)
      if (status.progress) {
        teamExecution.progress = status.progress;
      }

      attempts++;
    }

    throw new Error('Execution timeout after 2 minutes');
  } catch (error) {
    teamExecution.status = 'failed';
    teamExecution.error = error.message;
    teamExecution.completedAt = new Date().toISOString();
    throw error;
  }
};

/**
 * Get outputs from previous teams in execution
 */
const getPreviousTeamOutputs = (project, executionId) => {
  // Find execution
  const execution = project.executions.find(e => e.id === executionId);
  if (!execution || !execution.teamExecutions) {
    return [];
  }

  return execution.teamExecutions
    .filter(te => te.status === 'completed')
    .map(te => ({
      teamId: te.teamId,
      teamName: project.teams.find(t => t.id === te.teamId)?.name,
      output: te.output,
      agentOutputs: te.agentOutputs
    }));
};

/**
 * Continue execution after checkpoint approval
 */
export const continueExecution = async (projectId, executionId, checkpointAction, editedOutput) => {
  const project = getProject(projectId);
  if (!project) {
    throw new Error(`Project ${projectId} not found`);
  }

  const execution = project.executions.find(e => e.id === executionId);
  if (!execution) {
    throw new Error(`Execution ${executionId} not found`);
  }

  // Handle checkpoint action
  if (checkpointAction === 'deny') {
    execution.status = 'denied';
    execution.completedAt = new Date().toISOString();
    updateProject(projectId, { status: 'denied', currentExecution: null });
    return execution;
  }

  if (checkpointAction === 'edit' && editedOutput) {
    // Replace last team's output with edited version
    const lastTeamExecution = execution.teamExecutions[execution.teamExecutions.length - 1];
    lastTeamExecution.output = editedOutput;
    lastTeamExecution.edited = true;
  }

  // Continue with remaining teams
  execution.status = 'running';
  const currentTeamIndex = execution.teamExecutions.length;

  for (let i = currentTeamIndex; i < project.teams.length; i++) {
    const team = project.teams.sort((a, b) => a.executionOrder - b.executionOrder)[i];
    const teamExecution = await executeTeam(projectId, team.id, execution.id);
    execution.teamExecutions.push(teamExecution);

    if (team.checkpointEnabled && teamExecution.status === 'completed') {
      execution.status = 'pending_checkpoint';
      execution.pendingTeamId = team.id;
      return execution;
    }
  }

  // All teams completed
  execution.status = 'completed';
  execution.completedAt = new Date().toISOString();
  updateProject(projectId, { status: 'completed', currentExecution: null });

  return execution;
};

/**
 * Get available agent types
 */
export const getAvailableAgents = () => {
  return [
    { id: 'PM', label: 'Project Manager', icon: '📋', color: '#4A90E2' },
    { id: 'Memory', label: 'Memory', icon: '🧠', color: '#9B59B6' },
    { id: 'Research', label: 'Research', icon: '🔍', color: '#E67E22' },
    { id: 'Ideas', label: 'Ideas', icon: '💡', color: '#F1C40F' },
    { id: 'Designs', label: 'Designs', icon: '🎨', color: '#E91E63' },
    { id: 'Senior', label: 'Senior Engineer', icon: '👨‍💻', color: '#3498DB' },
    { id: 'iOS', label: 'iOS Developer', icon: '📱', color: '#95A5A6' },
    { id: 'Android', label: 'Android Developer', icon: '🤖', color: '#27AE60' },
    { id: 'Web', label: 'Web Developer', icon: '🌐', color: '#16A085' },
    { id: 'QA', label: 'QA Engineer', icon: '✅', color: '#2ECC71' },
    { id: 'Verifier', label: 'Verifier', icon: '🔎', color: '#34495E' }
  ];
};
