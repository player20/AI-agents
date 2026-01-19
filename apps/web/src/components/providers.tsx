'use client'

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { SidebarProvider } from '@/components/ui/sidebar'
import { Toaster } from '@/components/ui/sonner'
import { useState, Suspense } from 'react'
import { PostHogProvider } from '@/lib/analytics'

// Page view tracker component - must be inside Suspense due to useSearchParams
function PageViewTracker() {
  // Import dynamically to avoid SSR issues
  const { usePageView } = require('@/lib/analytics')
  usePageView()
  return null
}

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000, // 1 minute
            refetchOnWindowFocus: false,
          },
        },
      })
  )

  return (
    <PostHogProvider>
      <QueryClientProvider client={queryClient}>
        <SidebarProvider>
          <Suspense fallback={null}>
            <PageViewTracker />
          </Suspense>
          {children}
          <Toaster position="bottom-right" />
        </SidebarProvider>
      </QueryClientProvider>
    </PostHogProvider>
  )
}
