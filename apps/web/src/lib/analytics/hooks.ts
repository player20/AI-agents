'use client'

import { useCallback } from 'react'
import {
  trackEvent,
  identifyUser,
  setUserProperties,
  isPostHogConfigured,
  type AnalyticsEvent
} from './posthog'

/**
 * Hook for tracking project-related events
 */
export function useProjectAnalytics() {
  const trackProjectCreated = useCallback((projectId: string, platform: string) => {
    trackEvent('project_created', {
      project_id: projectId,
      platform,
      timestamp: new Date().toISOString()
    })
  }, [])

  const trackGenerationStarted = useCallback((projectId: string, description: string) => {
    trackEvent('project_generation_started', {
      project_id: projectId,
      description_length: description.length,
      timestamp: new Date().toISOString()
    })
  }, [])

  const trackGenerationCompleted = useCallback((
    projectId: string,
    durationMs: number,
    agentCount: number
  ) => {
    trackEvent('project_generation_completed', {
      project_id: projectId,
      duration_ms: durationMs,
      agent_count: agentCount,
      timestamp: new Date().toISOString()
    })
  }, [])

  const trackGenerationFailed = useCallback((projectId: string, error: string) => {
    trackEvent('project_generation_failed', {
      project_id: projectId,
      error,
      timestamp: new Date().toISOString()
    })
  }, [])

  return {
    trackProjectCreated,
    trackGenerationStarted,
    trackGenerationCompleted,
    trackGenerationFailed
  }
}

/**
 * Hook for tracking agent execution events
 */
export function useAgentAnalytics() {
  const trackAgentStarted = useCallback((
    projectId: string,
    agentName: string,
    agentType: string
  ) => {
    trackEvent('agent_started', {
      project_id: projectId,
      agent_name: agentName,
      agent_type: agentType,
      timestamp: new Date().toISOString()
    })
  }, [])

  const trackAgentCompleted = useCallback((
    projectId: string,
    agentName: string,
    durationMs: number
  ) => {
    trackEvent('agent_completed', {
      project_id: projectId,
      agent_name: agentName,
      duration_ms: durationMs,
      timestamp: new Date().toISOString()
    })
  }, [])

  const trackAgentFailed = useCallback((
    projectId: string,
    agentName: string,
    error: string
  ) => {
    trackEvent('agent_failed', {
      project_id: projectId,
      agent_name: agentName,
      error,
      timestamp: new Date().toISOString()
    })
  }, [])

  return {
    trackAgentStarted,
    trackAgentCompleted,
    trackAgentFailed
  }
}

/**
 * Hook for tracking template marketplace events
 */
export function useTemplateAnalytics() {
  const trackTemplateViewed = useCallback((templateId: string, templateName: string) => {
    trackEvent('template_viewed', {
      template_id: templateId,
      template_name: templateName,
      timestamp: new Date().toISOString()
    })
  }, [])

  const trackTemplateUsed = useCallback((templateId: string, templateName: string) => {
    trackEvent('template_used', {
      template_id: templateId,
      template_name: templateName,
      timestamp: new Date().toISOString()
    })
  }, [])

  return {
    trackTemplateViewed,
    trackTemplateUsed
  }
}

/**
 * Hook for tracking preview and export events
 */
export function usePreviewAnalytics() {
  const trackPreviewOpened = useCallback((projectId: string) => {
    trackEvent('preview_opened', {
      project_id: projectId,
      timestamp: new Date().toISOString()
    })
  }, [])

  const trackCodeExported = useCallback((
    projectId: string,
    format: 'zip' | 'github' | 'vercel'
  ) => {
    trackEvent('code_exported', {
      project_id: projectId,
      format,
      timestamp: new Date().toISOString()
    })
  }, [])

  return {
    trackPreviewOpened,
    trackCodeExported
  }
}

/**
 * Hook for tracking feature usage
 */
export function useFeatureAnalytics() {
  const trackFeatureUsed = useCallback((
    featureName: string,
    metadata?: Record<string, unknown>
  ) => {
    trackEvent('feature_used', {
      feature_name: featureName,
      ...metadata,
      timestamp: new Date().toISOString()
    })
  }, [])

  return { trackFeatureUsed }
}

/**
 * Hook for tracking errors
 */
export function useErrorAnalytics() {
  const trackError = useCallback((
    errorType: string,
    errorMessage: string,
    context?: Record<string, unknown>
  ) => {
    trackEvent('error_occurred', {
      error_type: errorType,
      error_message: errorMessage,
      ...context,
      timestamp: new Date().toISOString()
    })
  }, [])

  return { trackError }
}

/**
 * Hook for user identification
 */
export function useUserAnalytics() {
  const identify = useCallback((
    userId: string,
    email?: string,
    properties?: Record<string, unknown>
  ) => {
    identifyUser(userId, {
      email,
      ...properties,
      first_seen: new Date().toISOString()
    })
  }, [])

  const setProperties = useCallback((properties: Record<string, unknown>) => {
    setUserProperties(properties)
  }, [])

  return { identify, setProperties }
}

/**
 * Combined analytics hook for easy access to all tracking functions
 */
export function useAnalytics() {
  const project = useProjectAnalytics()
  const agent = useAgentAnalytics()
  const template = useTemplateAnalytics()
  const preview = usePreviewAnalytics()
  const feature = useFeatureAnalytics()
  const error = useErrorAnalytics()
  const user = useUserAnalytics()

  return {
    ...project,
    ...agent,
    ...template,
    ...preview,
    ...feature,
    ...error,
    ...user,
    isConfigured: isPostHogConfigured()
  }
}
