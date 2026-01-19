import { ProjectInput } from '@/components/project/project-input'
import { AgentTimeline } from '@/components/agents/agent-timeline'
import { GeneratedCode } from '@/components/code/generated-code'

export default function Home() {
  return (
    <main className="flex-1 p-6 lg:p-8">
      <div className="mx-auto max-w-6xl space-y-8">
        <ProjectInput />
        <AgentTimeline />
        <GeneratedCode />
      </div>
    </main>
  )
}
