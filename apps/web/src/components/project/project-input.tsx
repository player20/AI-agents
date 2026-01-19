'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useProjectStore, Platform } from '@/stores/project-store'
import { Sparkles, Globe, Smartphone, Layers, Rocket } from 'lucide-react'
import { toast } from 'sonner'

const platforms: { value: Platform; label: string; icon: React.ReactNode; description: string }[] = [
  {
    value: 'web',
    label: 'Web App',
    icon: <Globe className="h-5 w-5" />,
    description: 'React + Next.js + TypeScript',
  },
  {
    value: 'ios',
    label: 'iOS App',
    icon: <Smartphone className="h-5 w-5" />,
    description: 'Swift + SwiftUI',
  },
  {
    value: 'android',
    label: 'Android App',
    icon: <Smartphone className="h-5 w-5" />,
    description: 'Kotlin + Jetpack Compose',
  },
  {
    value: 'all',
    label: 'All Platforms',
    icon: <Layers className="h-5 w-5" />,
    description: 'Web + iOS + Android',
  },
]

export function ProjectInput() {
  const [description, setDescription] = useState('')
  const [platform, setPlatform] = useState<Platform>('web')
  const [isGenerating, setIsGenerating] = useState(false)
  const {
    createProject,
    updateProjectStatus,
    addAgentExecution,
    updateAgentExecution,
    setGeneratedFiles,
  } = useProjectStore()

  const handleGenerate = async () => {
    if (!description.trim()) return

    setIsGenerating(true)
    createProject(description, platform)
    updateProjectStatus('planning')

    try {
      const response = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ description, platform }),
      })

      if (!response.ok) {
        throw new Error('Generation failed')
      }

      // Handle Server-Sent Events streaming response
      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) {
        throw new Error('No response body')
      }

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))

              switch (data.type) {
                case 'status':
                  toast.info(data.message)
                  break

                case 'agent_start':
                  addAgentExecution({
                    id: crypto.randomUUID(),
                    name: data.agent || data.agent_id,
                    status: 'running',
                    startedAt: new Date(),
                  })
                  updateProjectStatus('generating')
                  break

                case 'parallel_start':
                  // Multiple agents starting in parallel
                  if (data.agents && Array.isArray(data.agents)) {
                    data.agents.forEach((agentId: string) => {
                      addAgentExecution({
                        id: crypto.randomUUID(),
                        name: agentId,
                        status: 'running',
                        startedAt: new Date(),
                      })
                    })
                    updateProjectStatus('generating')
                  }
                  break

                case 'agent_complete':
                  // Find the running agent and mark as complete
                  const store = useProjectStore.getState()
                  const agentName = data.agent || data.agent_id
                  const runningAgent = store.currentProject?.agents.find(
                    (a) => a.name === agentName && a.status === 'running'
                  )
                  if (runningAgent) {
                    updateAgentExecution(runningAgent.id, {
                      status: 'complete',
                      completedAt: new Date(),
                      output: data.output,
                    })
                  } else if (agentName) {
                    // Agent wasn't added on agent_start, add it now as complete
                    addAgentExecution({
                      id: crypto.randomUUID(),
                      name: agentName,
                      status: 'complete',
                      startedAt: new Date(),
                      completedAt: new Date(),
                      output: data.output,
                    })
                  }
                  break

                case 'files':
                  setGeneratedFiles(data.files)
                  break

                case 'complete':
                  updateProjectStatus('complete')
                  toast.success(data.message)
                  break
              }
            } catch {
              // Ignore JSON parse errors for incomplete chunks
            }
          }
        }
      }
    } catch (error) {
      console.error('Generation error:', error)
      updateProjectStatus('error')
      toast.error('Generation failed. Please try again.')
    } finally {
      setIsGenerating(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="text-center space-y-2">
        <h1 className="text-4xl font-bold tracking-tight">
          Build Apps with <span className="text-primary">52 AI Engineers</span>
        </h1>
        <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
          Describe your app idea in plain English. Our team of specialized AI agents will
          validate, design, build, and test it for you in minutes.
        </p>
      </div>

      <Card className="max-w-3xl mx-auto">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-primary" />
            What do you want to build?
          </CardTitle>
          <CardDescription>
            Be specific about features, target users, and any design preferences.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <Textarea
            placeholder="Example: A task management app for remote teams with real-time collaboration, Kanban boards, and Slack integration. Use a modern, minimalist design with dark mode support."
            className="min-h-[150px] resize-none"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />

          <div className="space-y-3">
            <label className="text-sm font-medium">Target Platform</label>
            <Tabs value={platform} onValueChange={(v) => setPlatform(v as Platform)}>
              <TabsList className="grid w-full grid-cols-4">
                {platforms.map((p) => (
                  <TabsTrigger key={p.value} value={p.value} className="flex items-center gap-2">
                    {p.icon}
                    <span className="hidden sm:inline">{p.label}</span>
                  </TabsTrigger>
                ))}
              </TabsList>
              {platforms.map((p) => (
                <TabsContent key={p.value} value={p.value}>
                  <p className="text-sm text-muted-foreground">{p.description}</p>
                </TabsContent>
              ))}
            </Tabs>
          </div>

          <Button
            size="lg"
            className="w-full"
            onClick={handleGenerate}
            disabled={!description.trim() || isGenerating}
          >
            {isGenerating ? (
              <>
                <Sparkles className="mr-2 h-4 w-4 animate-spin" />
                Generating...
              </>
            ) : (
              <>
                <Rocket className="mr-2 h-4 w-4" />
                Generate App
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      <div className="text-center text-sm text-muted-foreground">
        <p>
          Powered by{' '}
          <span className="font-medium">CrewAI + LangGraph + OpenHands</span>
        </p>
      </div>
    </div>
  )
}
