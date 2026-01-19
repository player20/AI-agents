'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useProjectStore, AgentExecution } from '@/stores/project-store'
import { CheckCircle2, Circle, Loader2, XCircle, Bot } from 'lucide-react'
import { cn } from '@/lib/utils'

function AgentStatusIcon({ status }: { status: AgentExecution['status'] }) {
  switch (status) {
    case 'pending':
      return <Circle className="h-4 w-4 text-muted-foreground" />
    case 'running':
      return <Loader2 className="h-4 w-4 text-primary animate-spin" />
    case 'complete':
      return <CheckCircle2 className="h-4 w-4 text-green-500" />
    case 'error':
      return <XCircle className="h-4 w-4 text-destructive" />
  }
}

function AgentCard({ agent }: { agent: AgentExecution }) {
  return (
    <div
      className={cn(
        'flex items-start gap-3 p-3 rounded-lg border transition-colors',
        agent.status === 'running' && 'bg-primary/5 border-primary/20',
        agent.status === 'complete' && 'bg-green-500/5 border-green-500/20',
        agent.status === 'error' && 'bg-destructive/5 border-destructive/20'
      )}
    >
      <div className="flex-shrink-0 mt-0.5">
        <AgentStatusIcon status={agent.status} />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <Bot className="h-4 w-4 text-muted-foreground" />
          <span className="font-medium text-sm">{agent.name}</span>
        </div>
        {agent.output && (
          <p className="text-xs text-muted-foreground mt-1 truncate">
            {agent.output}
          </p>
        )}
        {agent.error && (
          <p className="text-xs text-destructive mt-1">{agent.error}</p>
        )}
      </div>
      {agent.completedAt && agent.startedAt && (
        <span className="text-xs text-muted-foreground flex-shrink-0">
          {Math.round(
            (new Date(agent.completedAt).getTime() -
              new Date(agent.startedAt).getTime()) /
              1000
          )}
          s
        </span>
      )}
    </div>
  )
}

export function AgentTimeline() {
  const { currentProject } = useProjectStore()

  if (!currentProject || currentProject.agents.length === 0) {
    return null
  }

  const completedCount = currentProject.agents.filter(
    (a) => a.status === 'complete'
  ).length
  const totalCount = currentProject.agents.length

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center justify-between">
          <span className="flex items-center gap-2">
            <Bot className="h-5 w-5" />
            Agent Progress
          </span>
          <span className="text-sm font-normal text-muted-foreground">
            {completedCount}/{totalCount} complete
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {currentProject.agents.map((agent) => (
            <AgentCard key={agent.id} agent={agent} />
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
