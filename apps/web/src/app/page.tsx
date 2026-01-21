'use client'

import { useSearchParams } from 'next/navigation'
import { Suspense } from 'react'
import { ProjectInput } from '@/components/project/project-input'
import { AgentTimeline } from '@/components/agents/agent-timeline'
import { GeneratedCode } from '@/components/code/generated-code'
import { getTemplateById } from '@/data/templates'

function HomeContent() {
  const searchParams = useSearchParams()
  const templateId = searchParams.get('template')

  // Get the template prompt if a template ID is provided
  const template = templateId ? getTemplateById(templateId) : null
  const initialDescription = template?.prompt || ''
  const templateName = template?.name || ''

  return (
    <main className="flex-1 p-6 lg:p-8">
      <div className="mx-auto max-w-6xl space-y-8">
        <ProjectInput
          initialDescription={initialDescription}
          templateName={templateName}
        />
        <AgentTimeline />
        <GeneratedCode />
      </div>
    </main>
  )
}

export default function Home() {
  return (
    <Suspense fallback={
      <main className="flex-1 p-6 lg:p-8">
        <div className="mx-auto max-w-6xl space-y-8">
          <div className="animate-pulse">Loading...</div>
        </div>
      </main>
    }>
      <HomeContent />
    </Suspense>
  )
}
