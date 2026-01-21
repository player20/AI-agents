'use client'

import { useState, useEffect, useCallback } from 'react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useProjectStore, Platform } from '@/stores/project-store'
import { Sparkles, Globe, Smartphone, Layers, Rocket, LayoutTemplate, X, Lightbulb, Info } from 'lucide-react'
import { toast } from 'sonner'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import {
  ClarificationDialog,
  ClarificationQuestion,
} from '@/components/clarification/ClarificationDialog'

// Generation tips for better prompts
const GENERATION_TIPS = [
  'Be specific about features and user interactions',
  'Mention your preferred tech stack or design system',
  'Describe your target users and use cases',
  'Include any integrations (Stripe, auth, APIs)',
  'Specify responsive/mobile requirements',
]

interface ProjectInputProps {
  initialDescription?: string
  templateName?: string
}

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

export function ProjectInput({ initialDescription = '', templateName = '' }: ProjectInputProps) {
  const [description, setDescription] = useState(initialDescription)
  const [usingTemplate, setUsingTemplate] = useState(!!templateName)

  // Clarification dialog state
  const [showClarification, setShowClarification] = useState(false)
  const [clarificationQuestions, setClarificationQuestions] = useState<ClarificationQuestion[]>([])
  const [clarificationSessionId, setClarificationSessionId] = useState<string | null>(null)
  const [detectedIndustry, setDetectedIndustry] = useState('')
  const [industryConfidence, setIndustryConfidence] = useState(0)

  // Update description when initialDescription changes (template selected)
  useEffect(() => {
    if (initialDescription) {
      setDescription(initialDescription)
      setUsingTemplate(true)
      toast.success(`Template "${templateName}" loaded! Click Generate to build it.`)
    }
  }, [initialDescription, templateName])
  const [platform, setPlatform] = useState<Platform>('web')
  const [isGenerating, setIsGenerating] = useState(false)
  const {
    createProject,
    updateProjectStatus,
    addAgentExecution,
    updateAgentExecution,
    setGeneratedFiles,
    setReport,
  } = useProjectStore()

  // Handle clarification submission
  const handleClarificationSubmit = useCallback(async (responses: Record<string, string>) => {
    if (!clarificationSessionId) {
      console.error('No clarification session ID')
      return
    }

    try {
      const response = await fetch(`/api/generate/sessions/${clarificationSessionId}/clarify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ responses }),
      })

      if (!response.ok) {
        throw new Error('Failed to submit clarification responses')
      }

      toast.success('Got it! Continuing with your preferences...')
      setShowClarification(false)
    } catch (error) {
      console.error('Clarification submit error:', error)
      toast.error('Failed to submit responses. Please try again.')
    }
  }, [clarificationSessionId])

  // Handle clarification skip
  const handleClarificationSkip = useCallback(async () => {
    if (clarificationSessionId) {
      try {
        // Submit empty responses to continue without clarification
        await fetch(`/api/generate/sessions/${clarificationSessionId}/clarify`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ responses: {} }),
        })
      } catch (error) {
        console.error('Skip clarification error:', error)
      }
    }
    setShowClarification(false)
    toast.info('Proceeding without additional details')
  }, [clarificationSessionId])

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

      // Buffer for handling partial SSE chunks
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        // Append decoded chunk to buffer (stream: true handles partial UTF-8)
        buffer += decoder.decode(value, { stream: true })

        // SSE events are separated by \n\n
        const events = buffer.split('\n\n')
        // Keep the last potentially incomplete event in the buffer
        buffer = events.pop() || ''

        for (const eventText of events) {
          // Process each complete event
          const lines = eventText.split('\n')

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const jsonData = line.slice(6)
                const data = JSON.parse(jsonData)

                console.log('[SSE Event]', data.type, data)

                switch (data.type) {
                  case 'status':
                    toast.info(data.message)
                    break

                  case 'agent_start':
                    console.log('[SSE] Adding agent:', data.agent || data.agent_id)
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
                      console.log('[SSE] Adding parallel agents:', data.agents)
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
                    console.log('[SSE] Completing agent:', agentName)
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
                      console.log('[SSE] Agent not found, adding as complete:', agentName)
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
                    console.log('[SSE] Received files:', Object.keys(data.files).length)
                    setGeneratedFiles(data.files)
                    break

                  case 'complete':
                    console.log('[SSE] Generation complete')
                    updateProjectStatus('complete')
                    toast.success(data.message)
                    break

                case 'clarification_required':
                    console.log('[SSE] Clarification required:', data)
                    // Show the clarification dialog
                    if (data.data?.questions && data.session_id) {
                      setClarificationQuestions(data.data.questions)
                      setClarificationSessionId(data.session_id)
                      setDetectedIndustry(data.data.detected_industry || '')
                      setIndustryConfidence(data.data.confidence || 0.5)
                      setShowClarification(true)
                      toast.info('A few quick questions to help build a better prototype...')
                    }
                    break

                case 'research_progress':
                    console.log('[SSE] Research progress:', data.message)
                    toast.info(data.message)
                    break

                case 'report_complete':
                    console.log('[SSE] Business report ready:', data.data?.report_type)
                    if (data.data?.report_html) {
                      setReport(data.data.report_html, data.data.report_type || 'comprehensive')
                      toast.success('Business insights report generated!')
                    }
                    break
                }
              } catch (parseError) {
                // Log parse errors for debugging instead of silently ignoring
                console.warn('[SSE Parse Error]', line, parseError)
              }
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
          <CardDescription className="flex items-center gap-2">
            Be specific about features, target users, and any design preferences.
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <button className="inline-flex items-center justify-center rounded-full p-1 hover:bg-muted">
                    <Lightbulb className="h-4 w-4 text-yellow-500" />
                  </button>
                </TooltipTrigger>
                <TooltipContent side="right" className="max-w-xs p-3">
                  <p className="font-medium mb-2">Tips for better results:</p>
                  <ul className="text-xs space-y-1">
                    {GENERATION_TIPS.map((tip, i) => (
                      <li key={i} className="flex items-start gap-1">
                        <span className="text-primary">•</span>
                        {tip}
                      </li>
                    ))}
                  </ul>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </CardDescription>
          {usingTemplate && templateName && (
            <div className="mt-3 flex items-center gap-2 rounded-lg bg-primary/10 px-3 py-2 text-sm">
              <LayoutTemplate className="h-4 w-4 text-primary" />
              <span>Using template: <strong>{templateName}</strong></span>
              <button
                onClick={() => {
                  setDescription('')
                  setUsingTemplate(false)
                  // Clear the URL parameter
                  window.history.replaceState({}, '', '/')
                }}
                className="ml-auto rounded p-1 hover:bg-primary/20"
                title="Clear template"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          )}
        </CardHeader>
        <CardContent className="space-y-6">
          <Textarea
            placeholder="Example: A task management app for remote teams with real-time collaboration, Kanban boards, and Slack integration. Use a modern, minimalist design with dark mode support."
            className="min-h-[150px] resize-none"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />

          {/* Generation Tips - collapsed by default */}
          {!description && (
            <div className="rounded-lg bg-muted/50 border border-muted p-4">
              <div className="flex items-center gap-2 mb-2">
                <Lightbulb className="h-4 w-4 text-yellow-500" />
                <span className="text-sm font-medium">Quick Tips</span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs text-muted-foreground">
                {GENERATION_TIPS.map((tip, i) => (
                  <div key={i} className="flex items-start gap-1.5">
                    <span className="text-primary mt-0.5">•</span>
                    <span>{tip}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

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

      {/* Clarification Dialog */}
      <ClarificationDialog
        open={showClarification}
        questions={clarificationQuestions}
        detectedIndustry={detectedIndustry}
        confidence={industryConfidence}
        onSubmit={handleClarificationSubmit}
        onSkip={handleClarificationSkip}
      />
    </div>
  )
}
