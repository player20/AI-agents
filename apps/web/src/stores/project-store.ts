import { create } from 'zustand'

// localStorage key for sharing generated files across tabs
const GENERATED_FILES_KEY = 'code-weaver-generated-files'
const CURRENT_PROJECT_KEY = 'code-weaver-current-project'

// Helper to save generated files to localStorage (for cross-tab access)
function saveToLocalStorage(project: Project | null) {
  if (typeof window === 'undefined') return
  if (project?.generatedFiles) {
    localStorage.setItem(GENERATED_FILES_KEY, JSON.stringify(project.generatedFiles))
    localStorage.setItem(CURRENT_PROJECT_KEY, JSON.stringify({
      id: project.id,
      name: project.name,
      description: project.description,
      platform: project.platform,
      status: project.status,
    }))
  }
}

// Helper to load generated files from localStorage
export function getGeneratedFilesFromStorage(): Record<string, string> | null {
  if (typeof window === 'undefined') return null
  const stored = localStorage.getItem(GENERATED_FILES_KEY)
  return stored ? JSON.parse(stored) : null
}

// Helper to load current project info from localStorage
export function getCurrentProjectFromStorage(): Partial<Project> | null {
  if (typeof window === 'undefined') return null
  const stored = localStorage.getItem(CURRENT_PROJECT_KEY)
  return stored ? JSON.parse(stored) : null
}

export type Platform = 'web' | 'ios' | 'android' | 'all'
export type ProjectStatus = 'idle' | 'planning' | 'designing' | 'generating' | 'testing' | 'complete' | 'error'

export interface AgentExecution {
  id: string
  name: string
  status: 'pending' | 'running' | 'complete' | 'error'
  startedAt?: Date
  completedAt?: Date
  output?: string
  error?: string
}

export type ReportType = 'transformation_proposal' | 'ux_audit' | 'comprehensive'

export interface Project {
  id: string
  name: string
  description: string
  platform: Platform
  status: ProjectStatus
  createdAt: Date
  agents: AgentExecution[]
  generatedFiles?: Record<string, string>
  // Business report data
  reportHtml?: string
  reportType?: ReportType
}

interface ProjectStore {
  // State
  currentProject: Project | null
  projects: Project[]
  isLoading: boolean
  error: string | null

  // Actions
  setCurrentProject: (project: Project | null) => void
  createProject: (description: string, platform: Platform) => void
  updateProjectStatus: (status: ProjectStatus) => void
  addAgentExecution: (agent: AgentExecution) => void
  updateAgentExecution: (agentId: string, updates: Partial<AgentExecution>) => void
  setGeneratedFiles: (files: Record<string, string>) => void
  setReport: (reportHtml: string, reportType: ReportType) => void
  reset: () => void
}

export const useProjectStore = create<ProjectStore>((set, get) => ({
  currentProject: null,
  projects: [],
  isLoading: false,
  error: null,

  setCurrentProject: (project) => set({ currentProject: project }),

  createProject: (description, platform) => {
    const newProject: Project = {
      id: crypto.randomUUID(),
      name: description.slice(0, 50),
      description,
      platform,
      status: 'idle',
      createdAt: new Date(),
      agents: [],
    }
    console.log('[Store] createProject:', newProject.id, 'Platform:', platform)
    set((state) => ({
      currentProject: newProject,
      projects: [...state.projects, newProject],
    }))
  },

  updateProjectStatus: (status) =>
    set((state) => {
      console.log('[Store] updateProjectStatus:', status, 'Project:', state.currentProject?.id)
      return {
        currentProject: state.currentProject
          ? { ...state.currentProject, status }
          : null,
      }
    }),

  addAgentExecution: (agent) =>
    set((state) => {
      console.log('[Store] addAgentExecution called:', agent.name, 'Status:', agent.status)

      if (!state.currentProject) {
        console.warn('[Store] No currentProject, cannot add agent:', agent.name)
        return { currentProject: null }
      }

      console.log('[Store] Current project ID:', state.currentProject.id)
      console.log('[Store] Existing agents:', state.currentProject.agents.map(a => a.name))

      // Check if agent with same name already exists (prevent duplicates)
      const existingAgent = state.currentProject.agents.find(
        (a) => a.name === agent.name
      )

      if (existingAgent) {
        console.log('[Store] Updating existing agent:', agent.name)
        // Update existing agent instead of adding duplicate
        return {
          currentProject: {
            ...state.currentProject,
            agents: state.currentProject.agents.map((a) =>
              a.name === agent.name ? { ...a, ...agent, id: a.id } : a
            ),
          },
        }
      }

      console.log('[Store] Adding new agent:', agent.name)
      // Add new agent
      return {
        currentProject: {
          ...state.currentProject,
          agents: [...state.currentProject.agents, agent],
        },
      }
    }),

  updateAgentExecution: (agentId, updates) =>
    set((state) => ({
      currentProject: state.currentProject
        ? {
            ...state.currentProject,
            agents: state.currentProject.agents.map((a) =>
              a.id === agentId ? { ...a, ...updates } : a
            ),
          }
        : null,
    })),

  setGeneratedFiles: (files) =>
    set((state) => {
      const updatedProject = state.currentProject
        ? { ...state.currentProject, generatedFiles: files }
        : null
      // Save to localStorage for cross-tab access
      saveToLocalStorage(updatedProject)
      return { currentProject: updatedProject }
    }),

  setReport: (reportHtml, reportType) =>
    set((state) => {
      console.log('[Store] setReport:', reportType, 'HTML length:', reportHtml?.length)
      return {
        currentProject: state.currentProject
          ? { ...state.currentProject, reportHtml, reportType }
          : null,
      }
    }),

  reset: () =>
    set({
      currentProject: null,
      isLoading: false,
      error: null,
    }),
}))
