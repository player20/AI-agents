'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { supabase, Project, ProjectInsert, ProjectUpdate } from '@/lib/supabase/client'
import { useAuth } from './use-auth'

// Local storage key for mock projects
const LOCAL_PROJECTS_KEY = 'code-weaver-local-projects'

// Helper to get mock projects from localStorage
function getLocalProjects(): Project[] {
  if (typeof window === 'undefined') return []
  const stored = localStorage.getItem(LOCAL_PROJECTS_KEY)
  return stored ? JSON.parse(stored) : []
}

// Helper to save mock projects to localStorage
function saveLocalProjects(projects: Project[]) {
  if (typeof window === 'undefined') return
  localStorage.setItem(LOCAL_PROJECTS_KEY, JSON.stringify(projects))
}

export function useProjects() {
  const { user, isLocalMode } = useAuth()
  const queryClient = useQueryClient()

  const {
    data: projects = [],
    isLoading,
    error,
  } = useQuery({
    queryKey: ['projects', user?.id],
    queryFn: async () => {
      if (isLocalMode) {
        return getLocalProjects()
      }

      const { data, error } = await supabase
        .from('projects')
        .select('*')
        .order('created_at', { ascending: false })

      if (error) throw error
      return data as Project[]
    },
    enabled: !!user,
  })

  const createProject = useMutation({
    mutationFn: async (project: Omit<ProjectInsert, 'user_id'>) => {
      if (isLocalMode) {
        const newProject: Project = {
          id: crypto.randomUUID(),
          user_id: 'local-dev-user',
          name: project.name,
          description: project.description || null,
          platform: project.platform || 'web',
          status: project.status || 'idle',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        }
        const projects = getLocalProjects()
        projects.unshift(newProject)
        saveLocalProjects(projects)
        return newProject
      }

      const insertData: ProjectInsert = { ...project, user_id: user!.id }
      const { data, error } = await supabase
        .from('projects')
        .insert(insertData as unknown as never)
        .select()
        .single()

      if (error) throw error
      return data as Project
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
    },
  })

  const updateProject = useMutation({
    mutationFn: async ({ id, ...updates }: ProjectUpdate & { id: string }) => {
      if (isLocalMode) {
        const projects = getLocalProjects()
        const index = projects.findIndex((p) => p.id === id)
        if (index !== -1) {
          projects[index] = {
            ...projects[index],
            ...updates,
            updated_at: new Date().toISOString(),
          }
          saveLocalProjects(projects)
        }
        return projects[index]
      }

      const { data, error } = await supabase
        .from('projects')
        .update(updates as unknown as never)
        .eq('id', id)
        .select()
        .single()

      if (error) throw error
      return data as Project
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
    },
  })

  const deleteProject = useMutation({
    mutationFn: async (id: string) => {
      if (isLocalMode) {
        const projects = getLocalProjects()
        const filtered = projects.filter((p) => p.id !== id)
        saveLocalProjects(filtered)
        return
      }

      const { error } = await supabase.from('projects').delete().eq('id', id)
      if (error) throw error
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
    },
  })

  return {
    projects,
    isLoading,
    error,
    createProject,
    updateProject,
    deleteProject,
  }
}

export function useProject(id: string) {
  const { user, isLocalMode } = useAuth()

  return useQuery({
    queryKey: ['project', id],
    queryFn: async () => {
      if (isLocalMode) {
        const projects = getLocalProjects()
        return projects.find((p) => p.id === id) || null
      }

      const { data, error } = await supabase
        .from('projects')
        .select('*')
        .eq('id', id)
        .single()

      if (error) throw error
      return data as Project
    },
    enabled: !!user && !!id,
  })
}
