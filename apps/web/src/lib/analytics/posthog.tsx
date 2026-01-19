'use client'

import posthog from 'posthog-js'
import { PostHogProvider as PHProvider } from 'posthog-js/react'
import { useEffect, ReactNode } from 'react'
import { usePathname, useSearchParams } from 'next/navigation'

// Initialize PostHog only on client side
const POSTHOG_KEY = process.env.NEXT_PUBLIC_POSTHOG_KEY
const POSTHOG_HOST = process.env.NEXT_PUBLIC_POSTHOG_HOST || 'https://app.posthog.com'

// Check if PostHog is configured
export const isPostHogConfigured = (): boolean => {
  return Boolean(POSTHOG_KEY)
}

// Initialize PostHog
if (typeof window !== 'undefined' && POSTHOG_KEY) {
  posthog.init(POSTHOG_KEY, {
    api_host: POSTHOG_HOST,
    capture_pageview: false, // We'll capture manually for more control
    capture_pageleave: true,
    persistence: 'localStorage',
    autocapture: {
      dom_event_allowlist: ['click', 'submit'],
      element_allowlist: ['button', 'a', 'input', 'select', 'textarea'],
    },
    // Disable in development unless explicitly enabled
    loaded: (posthog) => {
      if (process.env.NODE_ENV === 'development') {
        // Uncomment to enable in development:
        // posthog.debug()
      }
    },
  })
}

/**
 * PostHog Provider component for Next.js
 */
export function PostHogProvider({ children }: { children: ReactNode }) {
  // Don't render provider if not configured
  if (!isPostHogConfigured()) {
    return <>{children}</>
  }

  return <PHProvider client={posthog}>{children}</PHProvider>
}

/**
 * Hook to track page views
 * Should be used in a component that renders on every page
 */
export function usePageView() {
  const pathname = usePathname()
  const searchParams = useSearchParams()

  useEffect(() => {
    if (!isPostHogConfigured()) return

    const url = pathname + (searchParams?.toString() ? `?${searchParams.toString()}` : '')
    posthog.capture('$pageview', {
      $current_url: url,
    })
  }, [pathname, searchParams])
}

/**
 * Analytics event types
 */
export type AnalyticsEvent =
  | 'project_created'
  | 'project_generation_started'
  | 'project_generation_completed'
  | 'project_generation_failed'
  | 'agent_started'
  | 'agent_completed'
  | 'agent_failed'
  | 'template_viewed'
  | 'template_used'
  | 'preview_opened'
  | 'code_exported'
  | 'feature_used'
  | 'error_occurred'

/**
 * Track an analytics event
 */
export function trackEvent(
  event: AnalyticsEvent,
  properties?: Record<string, unknown>
) {
  if (!isPostHogConfigured()) {
    // Log to console in development
    if (process.env.NODE_ENV === 'development') {
      console.log('[Analytics]', event, properties)
    }
    return
  }

  posthog.capture(event, properties)
}

/**
 * Identify a user
 */
export function identifyUser(
  userId: string,
  properties?: Record<string, unknown>
) {
  if (!isPostHogConfigured()) return

  posthog.identify(userId, properties)
}

/**
 * Reset user identification (on logout)
 */
export function resetUser() {
  if (!isPostHogConfigured()) return

  posthog.reset()
}

/**
 * Set user properties
 */
export function setUserProperties(properties: Record<string, unknown>) {
  if (!isPostHogConfigured()) return

  posthog.people.set(properties)
}

/**
 * Track a feature flag
 */
export function getFeatureFlag(flagKey: string): boolean | string | undefined {
  if (!isPostHogConfigured()) return undefined

  return posthog.getFeatureFlag(flagKey)
}

/**
 * Check if a feature is enabled
 */
export function isFeatureEnabled(flagKey: string): boolean {
  if (!isPostHogConfigured()) return false

  return posthog.isFeatureEnabled(flagKey) ?? false
}

// Export posthog instance for advanced usage
export { posthog }
