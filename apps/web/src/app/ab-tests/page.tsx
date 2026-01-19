'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  Plus,
  FlaskConical,
  Play,
  Pause,
  MoreVertical,
  Trash2,
  BarChart3,
  Loader2,
  TrendingUp,
  TrendingDown,
  Minus,
} from 'lucide-react'

interface ABTest {
  id: string
  name: string
  project_id: string
  variants: {
    name: string
    description: string
    traffic: number
  }[]
  target_metric: string
  status: 'draft' | 'running' | 'completed' | 'paused'
  results?: {
    winner?: string
    confidence?: number
    variants: {
      name: string
      conversions: number
      visitors: number
      rate: number
    }[]
  }
  created_at: string
  started_at?: string
  ended_at?: string
}

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

const statusColors = {
  draft: 'bg-muted text-muted-foreground',
  running: 'bg-green-500/20 text-green-500',
  completed: 'bg-blue-500/20 text-blue-500',
  paused: 'bg-yellow-500/20 text-yellow-500',
}

export default function ABTestsPage() {
  const [tests, setTests] = useState<ABTest[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isCreateOpen, setIsCreateOpen] = useState(false)
  const [newTest, setNewTest] = useState({
    name: '',
    project_id: '',
    target_metric: 'conversion_rate',
    variants: [
      { name: 'Control', description: 'Original version', traffic: 50 },
      { name: 'Variant A', description: 'Test version', traffic: 50 },
    ],
  })

  useEffect(() => {
    fetchTests()
  }, [])

  const fetchTests = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/ab-tests`)
      if (response.ok) {
        const data = await response.json()
        setTests(data)
      }
    } catch (error) {
      console.error('Failed to fetch A/B tests:', error)
      // Use mock data if backend unavailable
      setTests([
        {
          id: 'ab_mock_1',
          name: 'Homepage CTA Button Color',
          project_id: 'proj_1',
          variants: [
            { name: 'Control', description: 'Blue button', traffic: 50 },
            { name: 'Variant A', description: 'Green button', traffic: 50 },
          ],
          target_metric: 'click_rate',
          status: 'running',
          results: {
            variants: [
              { name: 'Control', conversions: 234, visitors: 1250, rate: 18.7 },
              { name: 'Variant A', conversions: 289, visitors: 1248, rate: 23.2 },
            ],
            winner: 'Variant A',
            confidence: 94.5,
          },
          created_at: new Date().toISOString(),
          started_at: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
        },
        {
          id: 'ab_mock_2',
          name: 'Pricing Page Layout',
          project_id: 'proj_1',
          variants: [
            { name: 'Control', description: 'Grid layout', traffic: 50 },
            { name: 'Variant A', description: 'Card layout', traffic: 50 },
          ],
          target_metric: 'conversion_rate',
          status: 'draft',
          created_at: new Date().toISOString(),
        },
      ])
    } finally {
      setIsLoading(false)
    }
  }

  const handleCreate = async () => {
    if (!newTest.name.trim()) return

    try {
      const response = await fetch(`${BACKEND_URL}/api/ab-tests`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newTest),
      })

      if (response.ok) {
        const created = await response.json()
        setTests((prev) => [created, ...prev])
      }
    } catch (error) {
      // Add locally if backend unavailable
      const mockTest: ABTest = {
        id: `ab_${Date.now()}`,
        ...newTest,
        status: 'draft',
        created_at: new Date().toISOString(),
      }
      setTests((prev) => [mockTest, ...prev])
    }

    setNewTest({
      name: '',
      project_id: '',
      target_metric: 'conversion_rate',
      variants: [
        { name: 'Control', description: 'Original version', traffic: 50 },
        { name: 'Variant A', description: 'Test version', traffic: 50 },
      ],
    })
    setIsCreateOpen(false)
  }

  const handleStartTest = async (testId: string) => {
    try {
      await fetch(`${BACKEND_URL}/api/ab-tests/${testId}/start`, { method: 'POST' })
    } catch (error) {
      // Handle locally
    }
    setTests((prev) =>
      prev.map((t) =>
        t.id === testId
          ? { ...t, status: 'running', started_at: new Date().toISOString() }
          : t
      )
    )
  }

  const handleStopTest = async (testId: string) => {
    try {
      await fetch(`${BACKEND_URL}/api/ab-tests/${testId}/stop`, { method: 'POST' })
    } catch (error) {
      // Handle locally
    }
    setTests((prev) =>
      prev.map((t) =>
        t.id === testId
          ? { ...t, status: 'completed', ended_at: new Date().toISOString() }
          : t
      )
    )
  }

  const handleDelete = (testId: string) => {
    if (confirm('Are you sure you want to delete this A/B test?')) {
      setTests((prev) => prev.filter((t) => t.id !== testId))
    }
  }

  if (isLoading) {
    return (
      <div className="flex h-[50vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">A/B Tests</h1>
          <p className="text-muted-foreground">
            Run experiments to optimize conversions and user experience
          </p>
        </div>

        <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
          <DialogTrigger asChild>
            <Button variant="gradient">
              <Plus className="mr-2 h-4 w-4" />
              New Test
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-lg">
            <DialogHeader>
              <DialogTitle>Create A/B Test</DialogTitle>
              <DialogDescription>
                Set up a new experiment to test different variations
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="test-name">Test Name</Label>
                <Input
                  id="test-name"
                  placeholder="e.g., Homepage CTA Button Color"
                  value={newTest.name}
                  onChange={(e) =>
                    setNewTest((t) => ({ ...t, name: e.target.value }))
                  }
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="metric">Target Metric</Label>
                <Select
                  value={newTest.target_metric}
                  onValueChange={(value) =>
                    setNewTest((t) => ({ ...t, target_metric: value }))
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select metric" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="conversion_rate">Conversion Rate</SelectItem>
                    <SelectItem value="click_rate">Click Rate</SelectItem>
                    <SelectItem value="bounce_rate">Bounce Rate</SelectItem>
                    <SelectItem value="time_on_page">Time on Page</SelectItem>
                    <SelectItem value="revenue">Revenue per User</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>Variants</Label>
                <div className="space-y-2">
                  {newTest.variants.map((variant, index) => (
                    <div key={index} className="flex gap-2">
                      <Input
                        placeholder="Variant name"
                        value={variant.name}
                        onChange={(e) => {
                          const variants = [...newTest.variants]
                          variants[index].name = e.target.value
                          setNewTest((t) => ({ ...t, variants }))
                        }}
                        className="flex-1"
                      />
                      <Input
                        type="number"
                        placeholder="Traffic %"
                        value={variant.traffic}
                        onChange={(e) => {
                          const variants = [...newTest.variants]
                          variants[index].traffic = parseInt(e.target.value) || 0
                          setNewTest((t) => ({ ...t, variants }))
                        }}
                        className="w-24"
                      />
                    </div>
                  ))}
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() =>
                    setNewTest((t) => ({
                      ...t,
                      variants: [
                        ...t.variants,
                        {
                          name: `Variant ${String.fromCharCode(65 + t.variants.length - 1)}`,
                          description: '',
                          traffic: Math.floor(100 / (t.variants.length + 1)),
                        },
                      ],
                    }))
                  }
                >
                  <Plus className="mr-2 h-4 w-4" />
                  Add Variant
                </Button>
              </div>
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={() => setIsCreateOpen(false)}>
                Cancel
              </Button>
              <Button variant="gradient" onClick={handleCreate}>
                Create Test
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Tests List */}
      {tests.length === 0 ? (
        <Card className="border-dashed">
          <CardContent className="flex flex-col items-center justify-center py-12">
            <FlaskConical className="h-12 w-12 text-muted-foreground/50" />
            <h3 className="mt-4 text-lg font-semibold">No A/B tests yet</h3>
            <p className="text-sm text-muted-foreground">
              Create your first experiment to start optimizing
            </p>
            <Button
              variant="gradient"
              className="mt-4"
              onClick={() => setIsCreateOpen(true)}
            >
              <Plus className="mr-2 h-4 w-4" />
              Create Test
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {tests.map((test) => (
            <Card key={test.id}>
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                      <FlaskConical className="h-5 w-5 text-primary" />
                    </div>
                    <div>
                      <CardTitle className="text-base">{test.name}</CardTitle>
                      <div className="flex items-center gap-2 mt-1">
                        <Badge
                          variant="outline"
                          className={statusColors[test.status]}
                        >
                          {test.status}
                        </Badge>
                        <span className="text-xs text-muted-foreground">
                          Target: {test.target_metric.replace('_', ' ')}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    {test.status === 'draft' && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleStartTest(test.id)}
                      >
                        <Play className="mr-2 h-4 w-4" />
                        Start
                      </Button>
                    )}
                    {test.status === 'running' && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleStopTest(test.id)}
                      >
                        <Pause className="mr-2 h-4 w-4" />
                        Stop
                      </Button>
                    )}

                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon" className="h-8 w-8">
                          <MoreVertical className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem>
                          <BarChart3 className="mr-2 h-4 w-4" />
                          View Details
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          className="text-destructive"
                          onClick={() => handleDelete(test.id)}
                        >
                          <Trash2 className="mr-2 h-4 w-4" />
                          Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </div>
              </CardHeader>

              <CardContent>
                {/* Variants with results */}
                <div className="space-y-3">
                  {test.variants.map((variant, index) => {
                    const result = test.results?.variants.find(
                      (v) => v.name === variant.name
                    )
                    const isWinner = test.results?.winner === variant.name

                    return (
                      <div
                        key={index}
                        className={`rounded-lg border p-3 ${
                          isWinner ? 'border-green-500/50 bg-green-500/5' : ''
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <span className="font-medium">{variant.name}</span>
                            {isWinner && (
                              <Badge className="bg-green-500/20 text-green-500">
                                Winner
                              </Badge>
                            )}
                            <span className="text-sm text-muted-foreground">
                              ({variant.traffic}% traffic)
                            </span>
                          </div>
                          {result && (
                            <div className="flex items-center gap-4 text-sm">
                              <span>
                                {result.conversions} / {result.visitors} visitors
                              </span>
                              <span
                                className={`flex items-center gap-1 font-semibold ${
                                  isWinner ? 'text-green-500' : ''
                                }`}
                              >
                                {result.rate > (test.results?.variants[0]?.rate || 0) &&
                                index > 0 ? (
                                  <TrendingUp className="h-4 w-4" />
                                ) : index > 0 ? (
                                  <TrendingDown className="h-4 w-4" />
                                ) : (
                                  <Minus className="h-4 w-4" />
                                )}
                                {result.rate.toFixed(1)}%
                              </span>
                            </div>
                          )}
                        </div>
                        {result && (
                          <Progress value={result.rate * 4} className="mt-2 h-2" />
                        )}
                      </div>
                    )
                  })}
                </div>

                {/* Confidence indicator */}
                {test.results?.confidence && (
                  <div className="mt-4 flex items-center justify-between rounded-lg bg-muted p-3">
                    <span className="text-sm text-muted-foreground">
                      Statistical Confidence
                    </span>
                    <span
                      className={`font-semibold ${
                        test.results.confidence >= 95
                          ? 'text-green-500'
                          : test.results.confidence >= 90
                          ? 'text-yellow-500'
                          : 'text-muted-foreground'
                      }`}
                    >
                      {test.results.confidence.toFixed(1)}%
                    </span>
                  </div>
                )}

                {/* Date info */}
                <div className="mt-4 flex items-center justify-between text-xs text-muted-foreground">
                  <span>
                    Created {new Date(test.created_at).toLocaleDateString()}
                  </span>
                  {test.started_at && (
                    <span>
                      Started {new Date(test.started_at).toLocaleDateString()}
                    </span>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
