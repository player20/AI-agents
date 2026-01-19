'use client'

import { useState, useRef } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Search,
  Globe,
  Upload,
  Play,
  Loader2,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  FileJson,
  TrendingUp,
  Accessibility,
  Gauge,
  Target,
  Github,
  Code2,
  Shield,
  Bug,
  Zap,
  FileCode,
  Download,
  X,
  Smartphone,
  Image as ImageIcon,
  Trash2,
  Eye,
  Palette,
  Navigation,
} from 'lucide-react'

interface ScoreFeedbackItem {
  deduction: number
  reason: string
}

interface PageCrawled {
  url: string
  title: string
  load_time_ms: number
  issues_count: number
}

interface AuditResult {
  url: string
  timestamp: string
  scores: {
    ux: number
    performance: number
    accessibility: number
    seo: number
  }
  score_feedback?: {
    ux: ScoreFeedbackItem[]
    performance: ScoreFeedbackItem[]
    accessibility: ScoreFeedbackItem[]
    seo: ScoreFeedbackItem[]
  }
  confidence: {
    score: number
    level: string
    color: string
    has_real_data: boolean
  }
  recommendations: string[]
  issues?: string[]
  funnel_analysis?: {
    completion_rate: number
    biggest_drop_off?: {
      step: string
      percentage: number
    }
  }
  pages_crawled?: PageCrawled[]
  total_pages?: number
}

interface UXPattern {
  score: number
  issues: string[]
  positive: string[]
}

interface AnalysisIssue {
  severity: string
  title: string
  description: string
  file_path?: string
  line_number?: number
  category: string
}

interface SecurityFinding {
  severity: string
  title: string
  description: string
  file: string
  line?: number
}

interface Recommendation {
  priority: string
  category: string
  title: string
  description: string
  file_path?: string
  line_number?: number
  current_code?: string
  suggested_code?: string
  impact: string
  effort: string
}

interface CodeAuditResult {
  repo_url: string
  timestamp: string

  // Platform context
  context: {
    platform_purpose: string
    platform_type: string
    frameworks: string[]
    languages: string[]
    databases: string[]
    architecture: string
    total_files: number
    total_lines: number
  }

  // Scores
  scores: {
    overall: number
    frontend: number
    backend: number
    architecture: number
    security: number
  }

  // Domain analysis
  analysis: {
    frontend: {
      score: number
      component_count: number
      component_patterns: string[]
      state_management: string[]
      ux_patterns: Record<string, UXPattern>
      issues: AnalysisIssue[]
      metrics: Record<string, number>
    }
    backend: {
      score: number
      endpoint_count: number
      api_patterns: string[]
      orm_usage: string[]
      auth_score: number
      validation_score: number
      security_findings: SecurityFinding[]
      issues: AnalysisIssue[]
      metrics: Record<string, number>
    }
    architecture: {
      score: number
      folder_organization: string
      module_boundaries: string
      total_complexity: number
      avg_complexity: number
      complex_files: string[]
      circular_dependencies: string[][]
      issues: AnalysisIssue[]
      metrics: Record<string, number>
    }
  }

  // Summary
  summary: {
    total_files: number
    languages: string[]
    lines_of_code: number
  }

  // Issues by severity
  issues: {
    critical: number
    high: number
    medium: number
    low: number
  }

  // Recommendations
  recommendations: Recommendation[]
}

interface AuditStep {
  id: string
  name: string
  status: 'pending' | 'running' | 'completed' | 'error'
  message?: string
}

// Mobile App Audit Interfaces
interface MobileScreenAnalysis {
  screen_name: string
  screen_index: number
  issues: MobileIssue[]
  positive_aspects: string[]
  accessibility_score: number
  ui_consistency_score: number
  platform_compliance_score: number
  visual_design_score: number
}

interface MobileIssue {
  title: string
  description: string
  impact: string
  severity: string
  category: string
  key: string
  screen?: string
  location?: string
}

interface MobileRecommendation {
  priority: number
  category: string
  title: string
  description: string
  impact: string
  effort: string
}

interface MobileAppAuditResult {
  app_name: string
  platform: string
  timestamp: string
  overall_score: number
  scores: {
    accessibility: number
    ui_ux: number
    platform_compliance: number
    visual_design: number
    navigation: number
  }
  screen_analyses: MobileScreenAnalysis[]
  issues: MobileIssue[]
  recommendations: MobileRecommendation[]
  summary: string
  confidence: {
    level: string
    score: number
    color: string
    note?: string
    factors?: string[]
  }
  // Enhanced analytics output
  funnel_analysis?: {
    total_steps: number
    overall_conversion: number
    biggest_drop_off?: {
      step: string
      screen?: string
      drop_off_rate: number
    }
    steps: Array<{
      name: string
      screen?: string
      users_entered: number
      users_completed: number
      drop_off_rate: number
      is_problem_area: boolean
    }>
    issue_correlations: Array<{
      funnel_step: string
      issue: string
      severity: string
      drop_off_rate: number
      correlation: string
    }>
  }
  roi_projection?: {
    current_monthly_revenue: number
    projected_monthly_revenue: number
    monthly_gain: number
    annual_gain: number
    conversion_improvement: number
    issues_addressed: number
    assumptions: string[]
  }
  persona_impact?: Array<{
    persona_name: string
    description: string
    affected_issues: Array<{
      issue: string
      severity: string
      reason: string
    }>
    severity_score: number
    recommendations: string[]
  }>
  priority_matrix?: {
    quick_wins: Array<{ title: string; screen: string; severity: string; effort: string; impact: string }>
    major_projects: Array<{ title: string; screen: string; severity: string; effort: string; impact: string }>
    fill_ins: Array<{ title: string; screen: string; severity: string; effort: string; impact: string }>
    thankless_tasks: Array<{ title: string; screen: string; severity: string; effort: string; impact: string }>
  }
}

// Analytics input interfaces
interface FunnelStepInput {
  name: string
  screen_name: string
  users_entered: number
  users_completed: number
}

interface BusinessGoalsInput {
  primary_goal: string
  monthly_active_users: number
  average_revenue_per_user: number
  current_value: number
  target_value: number
}

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

export default function AuditPage() {
  // Main tab state
  const [auditType, setAuditType] = useState<'website' | 'code' | 'mobile'>('website')

  // Website audit state
  const [url, setUrl] = useState('')
  const [fullAudit, setFullAudit] = useState(false)
  const [maxPages, setMaxPages] = useState(10)
  const [userCount, setUserCount] = useState(3)
  const [analyticsFile, setAnalyticsFile] = useState<File | null>(null)
  const [isRunning, setIsRunning] = useState(false)
  const [result, setResult] = useState<AuditResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [steps, setSteps] = useState<AuditStep[]>([])
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Export modal state
  const [showExportModal, setShowExportModal] = useState(false)
  const [isExporting, setIsExporting] = useState(false)
  const [exportForm, setExportForm] = useState({
    companyName: '',
    industry: 'general',
    monthlyVisitors: ''
  })

  // Code audit state
  const [repoUrl, setRepoUrl] = useState('')
  const [codeAuditRunning, setCodeAuditRunning] = useState(false)
  const [codeResult, setCodeResult] = useState<CodeAuditResult | null>(null)
  const [codeError, setCodeError] = useState<string | null>(null)
  const [codeSteps, setCodeSteps] = useState<AuditStep[]>([])

  // Mobile app audit state
  const [mobileAppName, setMobileAppName] = useState('')
  const [mobilePlatform, setMobilePlatform] = useState<'ios' | 'android'>('ios')
  const [mobileScreenshots, setMobileScreenshots] = useState<string[]>([])
  const [mobileScreenshotPreviews, setMobileScreenshotPreviews] = useState<string[]>([])
  const [mobileScreenNames, setMobileScreenNames] = useState<string[]>([])
  const [mobileAuditRunning, setMobileAuditRunning] = useState(false)
  const [mobileResult, setMobileResult] = useState<MobileAppAuditResult | null>(null)
  const [mobileError, setMobileError] = useState<string | null>(null)
  const [mobileSteps, setMobileSteps] = useState<AuditStep[]>([])
  const mobileFileInputRef = useRef<HTMLInputElement>(null)

  // Enhanced mobile audit inputs
  const [showAdvancedOptions, setShowAdvancedOptions] = useState(false)
  const [funnelSteps, setFunnelSteps] = useState<FunnelStepInput[]>([])
  const [businessGoals, setBusinessGoals] = useState<BusinessGoalsInput>({
    primary_goal: '',
    monthly_active_users: 0,
    average_revenue_per_user: 0,
    current_value: 0,
    target_value: 0
  })
  const [hasAnalytics, setHasAnalytics] = useState(false)
  const [hasBusinessGoals, setHasBusinessGoals] = useState(false)

  const updateStep = (id: string, updates: Partial<AuditStep>) => {
    setSteps((prev) =>
      prev.map((step) => (step.id === id ? { ...step, ...updates } : step))
    )
  }

  const runAudit = async () => {
    if (!url.trim()) return

    setIsRunning(true)
    setError(null)
    setResult(null)
    setSteps([
      { id: 'validate', name: 'Validating URL', status: 'pending' },
      { id: 'crawl', name: 'Crawling website', status: 'pending' },
      { id: 'analyze', name: 'Analyzing user flows', status: 'pending' },
      { id: 'recommend', name: 'Generating recommendations', status: 'pending' },
      { id: 'score', name: 'Calculating scores', status: 'pending' },
    ])

    try {
      // Use SSE streaming endpoint
      const eventSource = new EventSource(
        `${BACKEND_URL}/api/audit/stream?url=${encodeURIComponent(url)}&full=${fullAudit}&users=${userCount}&max_pages=${maxPages}`
      )

      eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data)

        switch (data.type) {
          case 'start':
            updateStep('validate', { status: 'completed' })
            updateStep('crawl', { status: 'running' })
            break
          case 'step':
            if (data.step === 'crawl') {
              updateStep('crawl', { status: 'running', message: data.message })
            } else if (data.step === 'analyze') {
              updateStep('crawl', { status: 'completed' })
              updateStep('analyze', { status: 'running', message: data.message })
            } else if (data.step === 'recommend') {
              updateStep('analyze', { status: 'completed' })
              updateStep('recommend', { status: 'running', message: data.message })
            }
            break
          case 'progress':
            if (data.step === 'crawl') {
              updateStep('crawl', { message: data.message })
            }
            break
          case 'complete':
            updateStep('recommend', { status: 'completed' })
            updateStep('score', { status: 'completed' })
            setResult(data as AuditResult)
            eventSource.close()
            setIsRunning(false)
            break
          case 'error':
            setError(data.message)
            eventSource.close()
            setIsRunning(false)
            break
        }
      }

      eventSource.onerror = () => {
        // Fallback to regular POST if SSE fails
        eventSource.close()
        runAuditFallback()
      }
    } catch (err) {
      runAuditFallback()
    }
  }

  const runAuditFallback = async () => {
    try {
      updateStep('validate', { status: 'completed' })
      updateStep('crawl', { status: 'running' })

      const response = await fetch(`${BACKEND_URL}/api/audit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url,
          full: fullAudit,
          users: userCount,
          max_pages: maxPages,
        }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Audit failed')
      }

      const data = await response.json()
      setSteps((prev) => prev.map((s) => ({ ...s, status: 'completed' })))
      setResult(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Audit failed')
      setSteps((prev) =>
        prev.map((s) => (s.status === 'running' ? { ...s, status: 'error' } : s))
      )
    } finally {
      setIsRunning(false)
    }
  }

  const getScoreColor = (score: number) => {
    if (score >= 8) return 'text-green-500'
    if (score >= 6) return 'text-yellow-500'
    if (score >= 4) return 'text-orange-500'
    return 'text-red-500'
  }

  const getConfidenceColor = (color: string) => {
    const colors: Record<string, string> = {
      green: 'bg-green-500/20 text-green-500 border-green-500/50',
      yellow: 'bg-yellow-500/20 text-yellow-500 border-yellow-500/50',
      orange: 'bg-orange-500/20 text-orange-500 border-orange-500/50',
      red: 'bg-red-500/20 text-red-500 border-red-500/50',
    }
    return colors[color] || colors.orange
  }

  // Code Audit Functions
  const updateCodeStep = (id: string, updates: Partial<AuditStep>) => {
    setCodeSteps((prev) =>
      prev.map((step) => (step.id === id ? { ...step, ...updates } : step))
    )
  }

  const runCodeAudit = async () => {
    if (!repoUrl.trim()) return

    // Validate GitHub URL
    const githubRegex = /^https?:\/\/(www\.)?github\.com\/[\w-]+\/[\w.-]+\/?$/
    if (!githubRegex.test(repoUrl.trim())) {
      setCodeError('Please enter a valid GitHub repository URL (e.g., https://github.com/owner/repo)')
      return
    }

    setCodeAuditRunning(true)
    setCodeError(null)
    setCodeResult(null)
    setCodeSteps([
      { id: 'fetch', name: 'Fetching repository files', status: 'pending' },
      { id: 'context', name: 'Understanding codebase', status: 'pending' },
      { id: 'frontend', name: 'Analyzing UX/UI patterns', status: 'pending' },
      { id: 'backend', name: 'Scanning backend & security', status: 'pending' },
      { id: 'architecture', name: 'Evaluating architecture', status: 'pending' },
      { id: 'recommendations', name: 'Generating recommendations', status: 'pending' },
    ])

    try {
      // Use SSE streaming endpoint
      const eventSource = new EventSource(
        `${BACKEND_URL}/api/audit/code/stream?repo_url=${encodeURIComponent(repoUrl)}`
      )

      eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data)

        switch (data.type) {
          case 'start':
            updateCodeStep('fetch', { status: 'running' })
            break
          case 'step':
            if (data.step === 'fetch') {
              updateCodeStep('fetch', { status: 'running', message: data.message })
            } else if (data.step === 'context') {
              updateCodeStep('fetch', { status: 'completed' })
              updateCodeStep('context', { status: 'running', message: data.message })
            } else if (data.step === 'frontend') {
              updateCodeStep('context', { status: 'completed' })
              updateCodeStep('frontend', { status: 'running', message: data.message })
            } else if (data.step === 'backend') {
              updateCodeStep('frontend', { status: 'completed' })
              updateCodeStep('backend', { status: 'running', message: data.message })
            } else if (data.step === 'architecture') {
              updateCodeStep('backend', { status: 'completed' })
              updateCodeStep('architecture', { status: 'running', message: data.message })
            } else if (data.step === 'recommendations') {
              updateCodeStep('architecture', { status: 'completed' })
              updateCodeStep('recommendations', { status: 'running', message: data.message })
            }
            break
          case 'progress':
            updateCodeStep(data.step, { message: data.message })
            break
          case 'complete':
            setCodeSteps((prev) => prev.map((s) => ({ ...s, status: 'completed' })))
            setCodeResult(data as CodeAuditResult)
            eventSource.close()
            setCodeAuditRunning(false)
            break
          case 'error':
            setCodeError(data.message)
            eventSource.close()
            setCodeAuditRunning(false)
            break
        }
      }

      eventSource.onerror = () => {
        // Fallback to regular POST if SSE fails
        eventSource.close()
        runCodeAuditFallback()
      }
    } catch (err) {
      runCodeAuditFallback()
    }
  }

  const runCodeAuditFallback = async () => {
    try {
      updateCodeStep('fetch', { status: 'running' })

      const response = await fetch(`${BACKEND_URL}/api/audit/code`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ repo_url: repoUrl }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Code audit failed')
      }

      const data = await response.json()
      setCodeSteps((prev) => prev.map((s) => ({ ...s, status: 'completed' })))
      setCodeResult(data)
    } catch (err) {
      setCodeError(err instanceof Error ? err.message : 'Code audit failed')
      setCodeSteps((prev) =>
        prev.map((s) => (s.status === 'running' ? { ...s, status: 'error' } : s))
      )
    } finally {
      setCodeAuditRunning(false)
    }
  }

  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical':
        return 'bg-red-500/20 text-red-500 border-red-500/50'
      case 'high':
        return 'bg-orange-500/20 text-orange-500 border-orange-500/50'
      case 'medium':
        return 'bg-yellow-500/20 text-yellow-500 border-yellow-500/50'
      case 'low':
        return 'bg-blue-500/20 text-blue-500 border-blue-500/50'
      default:
        return 'bg-gray-500/20 text-gray-500 border-gray-500/50'
    }
  }

  // Mobile App Audit Functions
  const updateMobileStep = (id: string, updates: Partial<AuditStep>) => {
    setMobileSteps((prev) =>
      prev.map((step) => (step.id === id ? { ...step, ...updates } : step))
    )
  }

  const handleMobileScreenshotUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files) return

    const newScreenshots: string[] = []
    const newPreviews: string[] = []

    Array.from(files).forEach((file) => {
      if (file.type.startsWith('image/')) {
        const reader = new FileReader()
        reader.onload = (event) => {
          const base64 = event.target?.result as string
          newScreenshots.push(base64.split(',')[1]) // Remove data:image prefix
          newPreviews.push(base64)

          // Update state after all files are read
          if (newScreenshots.length === files.length) {
            setMobileScreenshots((prev) => [...prev, ...newScreenshots])
            setMobileScreenshotPreviews((prev) => [...prev, ...newPreviews])
          }
        }
        reader.readAsDataURL(file)
      }
    })
  }

  const removeMobileScreenshot = (index: number) => {
    setMobileScreenshots((prev) => prev.filter((_, i) => i !== index))
    setMobileScreenshotPreviews((prev) => prev.filter((_, i) => i !== index))
  }

  const runMobileAudit = async () => {
    if (!mobileAppName.trim() || mobileScreenshots.length === 0) return

    setMobileAuditRunning(true)
    setMobileError(null)
    setMobileResult(null)

    const steps: AuditStep[] = [
      { id: 'upload', name: 'Processing screenshots', status: 'pending' },
      { id: 'analyze', name: 'Analyzing UI/UX patterns', status: 'pending' },
      { id: 'accessibility', name: 'Checking accessibility', status: 'pending' },
      { id: 'platform', name: `Verifying ${mobilePlatform.toUpperCase()} guidelines`, status: 'pending' },
    ]

    if (hasAnalytics) {
      steps.push({ id: 'funnel', name: 'Analyzing funnel data', status: 'pending' })
    }
    if (hasBusinessGoals) {
      steps.push({ id: 'roi', name: 'Calculating ROI projections', status: 'pending' })
    }
    steps.push({ id: 'report', name: 'Generating recommendations', status: 'pending' })

    setMobileSteps(steps)

    try {
      // Simulate step progress
      updateMobileStep('upload', { status: 'running' })
      await new Promise((r) => setTimeout(r, 500))
      updateMobileStep('upload', { status: 'completed' })

      updateMobileStep('analyze', { status: 'running' })
      await new Promise((r) => setTimeout(r, 500))
      updateMobileStep('analyze', { status: 'completed' })

      updateMobileStep('accessibility', { status: 'running' })

      // Build request body with optional analytics and business goals
      const requestBody: Record<string, unknown> = {
        app_name: mobileAppName,
        platform: mobilePlatform,
        screenshots: mobileScreenshots,
        screen_names: mobileScreenNames.length > 0 ? mobileScreenNames : undefined,
      }

      // Add analytics data if provided
      if (hasAnalytics && funnelSteps.length > 0) {
        requestBody.analytics = {
          funnel_data: funnelSteps.map(step => ({
            name: step.name,
            screen_name: step.screen_name,
            users_entered: step.users_entered,
            users_completed: step.users_completed,
          })),
        }
      }

      // Add business goals if provided
      if (hasBusinessGoals && businessGoals.primary_goal) {
        requestBody.business_goals = {
          primary_goal: businessGoals.primary_goal,
          monthly_active_users: businessGoals.monthly_active_users || 10000,
          average_revenue_per_user: businessGoals.average_revenue_per_user || 5,
          current_value: businessGoals.current_value || 2,
          target_value: businessGoals.target_value || 4,
        }
      }

      const response = await fetch(`${BACKEND_URL}/api/audit/mobile`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody),
      })

      updateMobileStep('accessibility', { status: 'completed' })
      updateMobileStep('platform', { status: 'running' })
      await new Promise((r) => setTimeout(r, 300))
      updateMobileStep('platform', { status: 'completed' })

      if (hasAnalytics) {
        updateMobileStep('funnel', { status: 'running' })
        await new Promise((r) => setTimeout(r, 300))
        updateMobileStep('funnel', { status: 'completed' })
      }

      if (hasBusinessGoals) {
        updateMobileStep('roi', { status: 'running' })
        await new Promise((r) => setTimeout(r, 300))
        updateMobileStep('roi', { status: 'completed' })
      }

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Mobile audit failed')
      }

      const data = await response.json()
      updateMobileStep('report', { status: 'completed' })
      setMobileResult(data)
    } catch (err) {
      setMobileError(err instanceof Error ? err.message : 'Mobile audit failed')
      setMobileSteps((prev) =>
        prev.map((s) => (s.status === 'running' ? { ...s, status: 'error' } : s))
      )
    } finally {
      setMobileAuditRunning(false)
    }
  }

  const getCategoryIcon = (category: string) => {
    switch (category.toLowerCase()) {
      case 'accessibility':
        return <Accessibility className="h-4 w-4" />
      case 'ui_ux':
        return <Eye className="h-4 w-4" />
      case 'platform_compliance':
        return <Smartphone className="h-4 w-4" />
      case 'visual_design':
        return <Palette className="h-4 w-4" />
      case 'navigation':
        return <Navigation className="h-4 w-4" />
      default:
        return <Target className="h-4 w-4" />
    }
  }

  // Export professional report
  const handleExport = async () => {
    if (!result || !exportForm.companyName) return
    setIsExporting(true)
    try {
      const response = await fetch(`${BACKEND_URL}/api/audit/export`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...result,
          company_name: exportForm.companyName,
          industry: exportForm.industry,
          monthly_visitors: exportForm.monthlyVisitors ? parseInt(exportForm.monthlyVisitors) : null
        })
      })
      if (!response.ok) {
        throw new Error('Failed to generate report')
      }
      const blob = await response.blob()
      const downloadUrl = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = downloadUrl
      a.download = `${exportForm.companyName.replace(/\s+/g, '-')}-audit-report.html`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(downloadUrl)
      setShowExportModal(false)
      // Reset form
      setExportForm({ companyName: '', industry: 'general', monthlyVisitors: '' })
    } catch (err) {
      console.error('Export failed:', err)
      alert('Failed to generate report. Please try again.')
    } finally {
      setIsExporting(false)
    }
  }

  // Export Modal Component
  const ExportModal = () => (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-background border rounded-lg p-6 max-w-md w-full mx-4 shadow-lg">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">Generate Professional Report</h3>
          <button
            onClick={() => setShowExportModal(false)}
            className="p-1 hover:bg-muted rounded"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <p className="text-sm text-muted-foreground mb-4">
          Personalize this report for your client - their name and industry will be used throughout.
        </p>

        <div className="space-y-4">
          <div>
            <Label htmlFor="company-name">Company Name *</Label>
            <Input
              id="company-name"
              type="text"
              value={exportForm.companyName}
              onChange={(e) => setExportForm({...exportForm, companyName: e.target.value})}
              placeholder="e.g., Acme Corp"
              className="mt-1"
            />
          </div>

          <div>
            <Label htmlFor="industry">Industry</Label>
            <select
              id="industry"
              value={exportForm.industry}
              onChange={(e) => setExportForm({...exportForm, industry: e.target.value})}
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background mt-1"
            >
              <option value="e-commerce">E-commerce / Online Store</option>
              <option value="saas">SaaS / Software</option>
              <option value="b2b">B2B / Professional Services</option>
              <option value="content">Content / Media / Blog</option>
              <option value="general">Other / General</option>
            </select>
          </div>

          <div>
            <Label htmlFor="monthly-visitors">Monthly Visitors (optional)</Label>
            <Input
              id="monthly-visitors"
              type="number"
              value={exportForm.monthlyVisitors}
              onChange={(e) => setExportForm({...exportForm, monthlyVisitors: e.target.value})}
              placeholder="e.g., 50000"
              className="mt-1"
            />
            <p className="text-xs text-muted-foreground mt-1">Used to calculate potential revenue impact</p>
          </div>
        </div>

        <div className="flex gap-3 mt-6">
          <Button variant="outline" onClick={() => setShowExportModal(false)} className="flex-1">
            Cancel
          </Button>
          <Button
            variant="gradient"
            onClick={handleExport}
            disabled={!exportForm.companyName || isExporting}
            className="flex-1"
          >
            {isExporting ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Download className="mr-2 h-4 w-4" />}
            {isExporting ? 'Generating...' : 'Generate Report'}
          </Button>
        </div>
      </div>
    </div>
  )

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Audit Mode</h1>
        <p className="text-muted-foreground">
          Analyze websites or GitHub repositories for quality, security, and performance
        </p>
      </div>

      {/* Main Audit Type Tabs */}
      <Tabs value={auditType} onValueChange={(v) => setAuditType(v as 'website' | 'code' | 'mobile')}>
        <TabsList className="grid w-full grid-cols-3 max-w-lg">
          <TabsTrigger value="website" className="flex items-center gap-2">
            <Globe className="h-4 w-4" />
            Website
          </TabsTrigger>
          <TabsTrigger value="code" className="flex items-center gap-2">
            <Github className="h-4 w-4" />
            Code
          </TabsTrigger>
          <TabsTrigger value="mobile" className="flex items-center gap-2">
            <Smartphone className="h-4 w-4" />
            Mobile App
          </TabsTrigger>
        </TabsList>

        {/* Website Audit Tab */}
        <TabsContent value="website" className="space-y-6 mt-6">
          {/* Audit Form */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Search className="h-5 w-5" />
                Website Audit
              </CardTitle>
              <CardDescription>
                Enter a URL to run a comprehensive audit powered by Weaver Pro
              </CardDescription>
            </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-4">
            <div className="flex-1 space-y-2">
              <Label htmlFor="url">Website URL</Label>
              <div className="flex gap-2">
                <div className="relative flex-1">
                  <Globe className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    id="url"
                    placeholder="https://example.com"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    className="pl-10"
                    disabled={isRunning}
                  />
                </div>
                <Button
                  variant="gradient"
                  onClick={runAudit}
                  disabled={!url.trim() || isRunning}
                >
                  {isRunning ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <Play className="mr-2 h-4 w-4" />
                  )}
                  {isRunning ? 'Running...' : 'Run Audit'}
                </Button>
              </div>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-6">
            <div className="flex items-center gap-2">
              <Switch
                id="full-audit"
                checked={fullAudit}
                onCheckedChange={setFullAudit}
                disabled={isRunning}
                aria-label="Enable comprehensive audit"
              />
              <Label htmlFor="full-audit">Comprehensive audit</Label>
            </div>

            {fullAudit && (
              <div className="flex items-center gap-2">
                <Label htmlFor="max-pages">Max pages:</Label>
                <Input
                  id="max-pages"
                  type="number"
                  min={1}
                  max={100}
                  value={maxPages}
                  onChange={(e) => setMaxPages(parseInt(e.target.value) || 10)}
                  className="w-20"
                  disabled={isRunning}
                />
              </div>
            )}

            <div className="flex items-center gap-2">
              <Label htmlFor="users">Simulated users:</Label>
              <Input
                id="users"
                type="number"
                min={1}
                max={10}
                value={userCount}
                onChange={(e) => setUserCount(parseInt(e.target.value) || 3)}
                className="w-20"
                disabled={isRunning}
              />
            </div>

            <div className="flex items-center gap-2">
              <input
                ref={fileInputRef}
                type="file"
                accept=".json,.csv"
                onChange={(e) => setAnalyticsFile(e.target.files?.[0] || null)}
                className="hidden"
              />
              <Button
                variant="outline"
                size="sm"
                onClick={() => fileInputRef.current?.click()}
                disabled={isRunning}
              >
                <Upload className="mr-2 h-4 w-4" />
                {analyticsFile ? analyticsFile.name : 'Upload Analytics'}
              </Button>
              {analyticsFile && (
                <Badge variant="secondary">
                  <FileJson className="mr-1 h-3 w-3" />
                  {analyticsFile.name}
                </Badge>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Progress Steps */}
      {steps.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Audit Progress</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {steps.map((step) => (
                <div key={step.id} className="flex items-center gap-3">
                  {step.status === 'pending' && (
                    <div className="h-5 w-5 rounded-full border-2 border-muted" />
                  )}
                  {step.status === 'running' && (
                    <Loader2 className="h-5 w-5 animate-spin text-primary" />
                  )}
                  {step.status === 'completed' && (
                    <CheckCircle2 className="h-5 w-5 text-green-500" />
                  )}
                  {step.status === 'error' && (
                    <XCircle className="h-5 w-5 text-red-500" />
                  )}
                  <span
                    className={
                      step.status === 'pending'
                        ? 'text-muted-foreground'
                        : step.status === 'error'
                        ? 'text-red-500'
                        : ''
                    }
                  >
                    {step.name}
                  </span>
                  {step.message && (
                    <span className="text-sm text-muted-foreground">
                      - {step.message}
                    </span>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Error Display */}
      {error && (
        <Card className="border-red-500/50 bg-red-500/10">
          <CardContent className="flex items-center gap-3 pt-6">
            <AlertTriangle className="h-5 w-5 text-red-500" />
            <span className="text-red-500">{error}</span>
          </CardContent>
        </Card>
      )}

      {/* Results */}
      {result && (
        <div className="space-y-6">
          {/* Export Button and Confidence Badge */}
          <div className="flex items-center justify-between gap-4">
            <Card className={`border ${getConfidenceColor(result.confidence.color)} flex-1`}>
              <CardContent className="flex items-center justify-between py-4">
                <div className="flex items-center gap-3">
                  <div
                    className={`h-3 w-3 rounded-full ${
                      result.confidence.color === 'green'
                        ? 'bg-green-500'
                        : result.confidence.color === 'yellow'
                        ? 'bg-yellow-500'
                        : result.confidence.color === 'orange'
                        ? 'bg-orange-500'
                        : 'bg-red-500'
                    }`}
                  />
                  <span className="font-semibold">
                    {result.confidence.level} Confidence ({result.confidence.score}%)
                  </span>
                  {result.total_pages && result.total_pages > 1 && (
                    <Badge variant="secondary" className="ml-2">
                      {result.total_pages} pages crawled
                    </Badge>
                  )}
                </div>
                {result.total_pages === 1 && (
                  <span className="text-sm text-muted-foreground">
                    TIP: Enable &quot;Comprehensive audit&quot; to crawl all pages like Google
                  </span>
                )}
              </CardContent>
            </Card>
            <Button
              variant="gradient"
              onClick={() => setShowExportModal(true)}
              className="shrink-0"
            >
              <Download className="mr-2 h-4 w-4" />
              Export Report
            </Button>
          </div>

          {/* Export Modal */}
          {showExportModal && <ExportModal />}

          {/* Scores with Feedback */}
          <div className="grid gap-4 md:grid-cols-2">
            {[
              { key: 'ux', label: 'UX Score', icon: Target },
              { key: 'performance', label: 'Performance', icon: Gauge },
              { key: 'accessibility', label: 'Accessibility', icon: Accessibility },
              { key: 'seo', label: 'SEO', icon: TrendingUp },
            ].map(({ key, label, icon: Icon }) => {
              const score = result.scores[key as keyof typeof result.scores]
              const feedback = result.score_feedback?.[key as keyof typeof result.score_feedback] || []
              return (
                <Card key={key}>
                  <CardContent className="pt-6">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Icon className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm font-medium">{label}</span>
                      </div>
                      <span className={`text-2xl font-bold ${getScoreColor(score)}`}>
                        {score.toFixed(1)}
                      </span>
                    </div>
                    <Progress value={score * 10} className="mt-2" />
                    {/* Score Feedback Breakdown */}
                    {feedback.length > 0 ? (
                      <div className="mt-3 space-y-1 border-t pt-3">
                        <p className="text-xs font-medium text-muted-foreground mb-2">Deductions:</p>
                        {feedback.map((item, i) => (
                          <div key={i} className="flex items-start gap-2 text-sm">
                            <span className="text-red-500 font-mono text-xs">
                              {item.deduction.toFixed(1)}
                            </span>
                            <span className="text-muted-foreground">{item.reason}</span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="mt-3 border-t pt-3">
                        <div className="flex items-center gap-2 text-sm text-green-500">
                          <CheckCircle2 className="h-4 w-4" />
                          <span>Perfect score - no issues found</span>
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              )
            })}
          </div>

          {/* Detailed Results */}
          <Tabs defaultValue="issues">
            <TabsList>
              <TabsTrigger value="issues">Issues ({result.issues?.length || 0})</TabsTrigger>
              <TabsTrigger value="pages">Pages Crawled ({result.total_pages || 1})</TabsTrigger>
              <TabsTrigger value="recommendations">Recommendations</TabsTrigger>
              <TabsTrigger value="funnel">Funnel Analysis</TabsTrigger>
            </TabsList>

            <TabsContent value="issues" className="mt-4">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <AlertTriangle className="h-5 w-5" />
                    Issues Detected
                  </CardTitle>
                  <CardDescription>
                    Problems found during the audit
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {result.issues && result.issues.length > 0 ? (
                    <ul className="space-y-2">
                      {result.issues.map((issue, i) => (
                        <li key={i} className="flex items-start gap-2 p-2 rounded-md bg-red-500/10">
                          <XCircle className="mt-0.5 h-4 w-4 text-red-500 flex-shrink-0" />
                          <span>{issue}</span>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <div className="flex items-center gap-2 text-green-500">
                      <CheckCircle2 className="h-5 w-5" />
                      <span>No issues detected!</span>
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="pages" className="mt-4">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Globe className="h-5 w-5" />
                    Pages Crawled
                  </CardTitle>
                  <CardDescription>
                    All pages discovered and analyzed during the audit
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {result.pages_crawled && result.pages_crawled.length > 0 ? (
                    <div className="space-y-2">
                      {result.pages_crawled.map((pg, i) => (
                        <div
                          key={i}
                          className="flex items-center justify-between p-3 rounded-lg bg-muted/50"
                        >
                          <div className="flex-1 min-w-0">
                            <p className="font-medium truncate">{pg.title || 'Untitled'}</p>
                            <p className="text-xs text-muted-foreground truncate">{pg.url}</p>
                          </div>
                          <div className="flex items-center gap-4 ml-4">
                            <div className="text-right">
                              <p className="text-sm">{pg.load_time_ms.toFixed(0)}ms</p>
                              <p className="text-xs text-muted-foreground">Load time</p>
                            </div>
                            {pg.issues_count > 0 ? (
                              <Badge variant="destructive" className="ml-2">
                                {pg.issues_count} issues
                              </Badge>
                            ) : (
                              <Badge variant="secondary" className="ml-2 bg-green-500/20 text-green-500">
                                No issues
                              </Badge>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-muted-foreground">Single page crawl - enable &quot;Comprehensive audit&quot; to crawl all pages</p>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="recommendations" className="mt-4">
              <Card>
                <CardHeader>
                  <CardTitle>Recommendations</CardTitle>
                  <CardDescription>
                    Action items to improve your website
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {result.recommendations.length > 0 ? (
                    <ul className="space-y-2">
                      {result.recommendations.map((rec, i) => (
                        <li key={i} className="flex items-start gap-2">
                          <CheckCircle2 className="mt-0.5 h-4 w-4 text-primary" />
                          <span>{rec}</span>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-muted-foreground">No recommendations generated</p>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="funnel" className="mt-4">
              <Card>
                <CardHeader>
                  <CardTitle>Funnel Analysis</CardTitle>
                  <CardDescription>
                    User flow completion and drop-off analysis
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {result.funnel_analysis ? (
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <span>Completion Rate</span>
                        <span className="text-2xl font-bold">
                          {result.funnel_analysis.completion_rate}%
                        </span>
                      </div>
                      <Progress value={result.funnel_analysis.completion_rate} />
                      {result.funnel_analysis.biggest_drop_off && (
                        <div className="mt-4 rounded-lg bg-muted p-4">
                          <p className="text-sm text-muted-foreground">Biggest Drop-off</p>
                          <p className="font-semibold">
                            {result.funnel_analysis.biggest_drop_off.step}
                          </p>
                          <p className="text-sm text-red-500">
                            {result.funnel_analysis.biggest_drop_off.percentage}% drop
                          </p>
                        </div>
                      )}
                    </div>
                  ) : (
                    <p className="text-muted-foreground">No funnel data available</p>
                  )}
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      )}
        </TabsContent>

        {/* Code Audit Tab */}
        <TabsContent value="code" className="space-y-6 mt-6">
          {/* Code Audit Form */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Github className="h-5 w-5" />
                GitHub Repository Audit
              </CardTitle>
              <CardDescription>
                Enter a GitHub repository URL to analyze code quality, security, and architecture
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-4">
                <div className="flex-1 space-y-2">
                  <Label htmlFor="repo-url">Repository URL</Label>
                  <div className="flex gap-2">
                    <div className="relative flex-1">
                      <Github className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                      <Input
                        id="repo-url"
                        placeholder="https://github.com/owner/repository"
                        value={repoUrl}
                        onChange={(e) => setRepoUrl(e.target.value)}
                        className="pl-10"
                        disabled={codeAuditRunning}
                      />
                    </div>
                    <Button
                      variant="gradient"
                      onClick={runCodeAudit}
                      disabled={!repoUrl.trim() || codeAuditRunning}
                    >
                      {codeAuditRunning ? (
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      ) : (
                        <Play className="mr-2 h-4 w-4" />
                      )}
                      {codeAuditRunning ? 'Analyzing...' : 'Run Audit'}
                    </Button>
                  </div>
                </div>
              </div>
              <p className="text-sm text-muted-foreground">
                Supports public GitHub repositories. The audit will analyze code structure, security vulnerabilities, and best practices.
              </p>
            </CardContent>
          </Card>

          {/* Code Audit Progress */}
          {codeSteps.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Audit Progress</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {codeSteps.map((step) => (
                    <div key={step.id} className="flex items-center gap-3">
                      {step.status === 'pending' && (
                        <div className="h-5 w-5 rounded-full border-2 border-muted" />
                      )}
                      {step.status === 'running' && (
                        <Loader2 className="h-5 w-5 animate-spin text-primary" />
                      )}
                      {step.status === 'completed' && (
                        <CheckCircle2 className="h-5 w-5 text-green-500" />
                      )}
                      {step.status === 'error' && (
                        <XCircle className="h-5 w-5 text-red-500" />
                      )}
                      <span
                        className={
                          step.status === 'pending'
                            ? 'text-muted-foreground'
                            : step.status === 'error'
                            ? 'text-red-500'
                            : ''
                        }
                      >
                        {step.name}
                      </span>
                      {step.message && (
                        <span className="text-sm text-muted-foreground">
                          - {step.message}
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Code Audit Error */}
          {codeError && (
            <Card className="border-red-500/50 bg-red-500/10">
              <CardContent className="flex items-center gap-3 pt-6">
                <AlertTriangle className="h-5 w-5 text-red-500" />
                <span className="text-red-500">{codeError}</span>
              </CardContent>
            </Card>
          )}

          {/* Code Audit Results */}
          {codeResult && (
            <div className="space-y-6">
              {/* Platform Context Card - only show if context is available */}
              {codeResult.context && (
                <Card className="border-primary/20 bg-gradient-to-r from-primary/5 to-transparent">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Target className="h-5 w-5 text-primary" />
                      Platform Understanding
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <p className="text-lg">{codeResult.context.platform_purpose}</p>
                    <div className="flex flex-wrap gap-4">
                      <div>
                        <span className="text-sm text-muted-foreground">Type</span>
                        <Badge variant="secondary" className="ml-2">{codeResult.context.platform_type}</Badge>
                      </div>
                      <div>
                        <span className="text-sm text-muted-foreground">Architecture</span>
                        <Badge variant="secondary" className="ml-2">{codeResult.context.architecture}</Badge>
                      </div>
                    </div>
                    {codeResult.context.frameworks?.length > 0 && (
                      <div className="flex flex-wrap gap-2">
                        <span className="text-sm text-muted-foreground mr-2">Frameworks:</span>
                        {codeResult.context.frameworks.map((fw) => (
                          <Badge key={fw} variant="outline">{fw}</Badge>
                        ))}
                      </div>
                    )}
                    {codeResult.context.databases?.length > 0 && (
                      <div className="flex flex-wrap gap-2">
                        <span className="text-sm text-muted-foreground mr-2">Databases:</span>
                        {codeResult.context.databases.map((db) => (
                          <Badge key={db} variant="outline">{db}</Badge>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              )}

              {/* Summary Stats */}
              <Card>
                <CardContent className="flex items-center justify-between py-4">
                  <div className="flex items-center gap-6">
                    <div className="flex items-center gap-2">
                      <FileCode className="h-4 w-4 text-muted-foreground" />
                      <span className="text-sm">{codeResult.context?.total_files ?? codeResult.summary?.total_files ?? 0} files</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Code2 className="h-4 w-4 text-muted-foreground" />
                      <span className="text-sm">{(codeResult.context?.total_lines ?? codeResult.summary?.lines_of_code ?? 0).toLocaleString()} lines</span>
                    </div>
                    <div className="flex gap-2">
                      {(codeResult.context?.languages ?? codeResult.summary?.languages ?? []).slice(0, 5).map((lang) => (
                        <Badge key={lang} variant="secondary">{lang}</Badge>
                      ))}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-muted-foreground">Overall Score:</span>
                    <span className={`text-2xl font-bold ${getScoreColor(codeResult.scores?.overall ?? 0)}`}>
                      {(codeResult.scores?.overall ?? 0).toFixed(1)}
                    </span>
                  </div>
                </CardContent>
              </Card>

              {/* Issue Counts */}
              <div className="grid gap-4 md:grid-cols-4">
                {[
                  { key: 'critical', label: 'Critical', color: 'text-red-500', bg: 'bg-red-500/10' },
                  { key: 'high', label: 'High', color: 'text-orange-500', bg: 'bg-orange-500/10' },
                  { key: 'medium', label: 'Medium', color: 'text-yellow-500', bg: 'bg-yellow-500/10' },
                  { key: 'low', label: 'Low', color: 'text-blue-500', bg: 'bg-blue-500/10' },
                ].map(({ key, label, color, bg }) => (
                  <Card key={key} className={bg}>
                    <CardContent className="pt-6">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">{label}</span>
                        <span className={`text-2xl font-bold ${color}`}>
                          {codeResult.issues[key as keyof typeof codeResult.issues]}
                        </span>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>

              {/* Domain Scores */}
              {codeResult.scores && (
                <div className="grid gap-4 md:grid-cols-4">
                  {[
                    { key: 'frontend', label: 'Frontend', icon: Target },
                    { key: 'backend', label: 'Backend', icon: Code2 },
                    { key: 'architecture', label: 'Architecture', icon: Gauge },
                    { key: 'security', label: 'Security', icon: Shield },
                  ].map(({ key, label, icon: Icon }) => {
                    const score = codeResult.scores?.[key as keyof typeof codeResult.scores] ?? 0
                    return (
                      <Card key={key}>
                        <CardContent className="pt-6">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <Icon className="h-4 w-4 text-muted-foreground" />
                              <span className="text-sm font-medium">{label}</span>
                            </div>
                            <span className={`text-2xl font-bold ${getScoreColor(score)}`}>
                              {score.toFixed(1)}
                            </span>
                          </div>
                          <Progress value={score * 10} className="mt-2" />
                        </CardContent>
                      </Card>
                    )
                  })}
                </div>
              )}

              {/* Domain Analysis Tabs - only show if analysis data is available */}
              {codeResult.analysis && (
              <Tabs defaultValue="frontend">
                <TabsList className="grid w-full grid-cols-4">
                  <TabsTrigger value="frontend">
                    Frontend ({codeResult.analysis?.frontend?.issues?.length ?? 0})
                  </TabsTrigger>
                  <TabsTrigger value="backend">
                    Backend ({codeResult.analysis?.backend?.issues?.length ?? 0})
                  </TabsTrigger>
                  <TabsTrigger value="architecture">
                    Architecture ({codeResult.analysis?.architecture?.issues?.length ?? 0})
                  </TabsTrigger>
                  <TabsTrigger value="security">
                    Security ({codeResult.analysis?.backend?.security_findings?.length ?? 0})
                  </TabsTrigger>
                </TabsList>

                {/* Frontend Tab */}
                <TabsContent value="frontend" className="mt-4 space-y-4">
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <Target className="h-5 w-5" />
                        UX/UI Analysis
                      </CardTitle>
                      <CardDescription>
                        {codeResult.analysis?.frontend?.component_count ?? 0} components detected
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      {/* Component Patterns */}
                      {(codeResult.analysis?.frontend?.component_patterns?.length ?? 0) > 0 && (
                        <div>
                          <span className="text-sm font-medium">Component Patterns:</span>
                          <div className="flex flex-wrap gap-2 mt-1">
                            {codeResult.analysis?.frontend?.component_patterns?.map((p) => (
                              <Badge key={p} variant="outline">{p}</Badge>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* State Management */}
                      {(codeResult.analysis?.frontend?.state_management?.length ?? 0) > 0 && (
                        <div>
                          <span className="text-sm font-medium">State Management:</span>
                          <div className="flex flex-wrap gap-2 mt-1">
                            {codeResult.analysis?.frontend?.state_management?.map((sm) => (
                              <Badge key={sm} variant="secondary">{sm}</Badge>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* UX Patterns */}
                      {codeResult.analysis?.frontend?.ux_patterns && Object.keys(codeResult.analysis.frontend.ux_patterns).length > 0 && (
                      <div className="space-y-3 mt-4">
                        <span className="text-sm font-medium">UX Patterns:</span>
                        {Object.entries(codeResult.analysis.frontend.ux_patterns).map(([key, pattern]) => (
                          <div key={key} className="rounded-lg border p-3">
                            <div className="flex items-center justify-between">
                              <span className="font-medium capitalize">{key.replace('_', ' ')}</span>
                              <span className={`font-bold ${getScoreColor(pattern.score)}`}>
                                {pattern.score.toFixed(1)}/10
                              </span>
                            </div>
                            {(pattern.positive?.length ?? 0) > 0 && (
                              <div className="mt-2">
                                {pattern.positive.map((p, i) => (
                                  <div key={i} className="flex items-start gap-2 text-sm text-green-500">
                                    <CheckCircle2 className="h-4 w-4 mt-0.5 flex-shrink-0" />
                                    <span>{p}</span>
                                  </div>
                                ))}
                              </div>
                            )}
                            {(pattern.issues?.length ?? 0) > 0 && (
                              <div className="mt-2">
                                {pattern.issues.map((issue, i) => (
                                  <div key={i} className="flex items-start gap-2 text-sm text-orange-500">
                                    <AlertTriangle className="h-4 w-4 mt-0.5 flex-shrink-0" />
                                    <span>{issue}</span>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                      )}

                      {/* Frontend Issues */}
                      {(codeResult.analysis?.frontend?.issues?.length ?? 0) > 0 && (
                        <div className="mt-4">
                          <span className="text-sm font-medium">Issues:</span>
                          <div className="space-y-2 mt-2">
                            {codeResult.analysis?.frontend?.issues?.map((issue, i) => (
                              <div key={i} className={`rounded-lg border p-3 ${getSeverityColor(issue.severity)}`}>
                                <div className="flex items-center gap-2">
                                  <Badge variant="outline" className={getSeverityColor(issue.severity)}>
                                    {issue.severity}
                                  </Badge>
                                  <span className="font-semibold">{issue.title}</span>
                                </div>
                                <p className="mt-1 text-sm">{issue.description}</p>
                                {issue.file_path && (
                                  <p className="mt-1 text-xs text-muted-foreground">
                                    {issue.file_path}{issue.line_number && `:${issue.line_number}`}
                                  </p>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </TabsContent>

                {/* Backend Tab */}
                <TabsContent value="backend" className="mt-4 space-y-4">
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <Code2 className="h-5 w-5" />
                        Backend Analysis
                      </CardTitle>
                      <CardDescription>
                        {codeResult.analysis?.backend?.endpoint_count ?? 0} API endpoints detected
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      {/* API Patterns */}
                      {(codeResult.analysis?.backend?.api_patterns?.length ?? 0) > 0 && (
                        <div>
                          <span className="text-sm font-medium">API Patterns:</span>
                          <div className="flex flex-wrap gap-2 mt-1">
                            {codeResult.analysis?.backend?.api_patterns?.map((p) => (
                              <Badge key={p} variant="outline">{p}</Badge>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* ORM Usage */}
                      {(codeResult.analysis?.backend?.orm_usage?.length ?? 0) > 0 && (
                        <div>
                          <span className="text-sm font-medium">ORM/Database:</span>
                          <div className="flex flex-wrap gap-2 mt-1">
                            {codeResult.analysis?.backend?.orm_usage?.map((orm) => (
                              <Badge key={orm} variant="secondary">{orm}</Badge>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Auth & Validation Scores */}
                      {codeResult.analysis?.backend && (
                      <div className="grid grid-cols-2 gap-4">
                        <div className="rounded-lg border p-3">
                          <div className="flex items-center justify-between">
                            <span className="text-sm font-medium">Auth Score</span>
                            <span className={`font-bold ${getScoreColor(codeResult.analysis?.backend?.auth_score ?? 0)}`}>
                              {(codeResult.analysis?.backend?.auth_score ?? 0).toFixed(1)}/10
                            </span>
                          </div>
                          <Progress value={(codeResult.analysis?.backend?.auth_score ?? 0) * 10} className="mt-2" />
                        </div>
                        <div className="rounded-lg border p-3">
                          <div className="flex items-center justify-between">
                            <span className="text-sm font-medium">Validation Score</span>
                            <span className={`font-bold ${getScoreColor(codeResult.analysis?.backend?.validation_score ?? 0)}`}>
                              {(codeResult.analysis?.backend?.validation_score ?? 0).toFixed(1)}/10
                            </span>
                          </div>
                          <Progress value={(codeResult.analysis?.backend?.validation_score ?? 0) * 10} className="mt-2" />
                        </div>
                      </div>
                      )}

                      {/* Backend Issues */}
                      {(codeResult.analysis?.backend?.issues?.length ?? 0) > 0 && (
                        <div className="mt-4">
                          <span className="text-sm font-medium">Issues:</span>
                          <div className="space-y-2 mt-2">
                            {codeResult.analysis?.backend?.issues?.map((issue, i) => (
                              <div key={i} className={`rounded-lg border p-3 ${getSeverityColor(issue.severity)}`}>
                                <div className="flex items-center gap-2">
                                  <Badge variant="outline" className={getSeverityColor(issue.severity)}>
                                    {issue.severity}
                                  </Badge>
                                  <span className="font-semibold">{issue.title}</span>
                                </div>
                                <p className="mt-1 text-sm">{issue.description}</p>
                                {issue.file_path && (
                                  <p className="mt-1 text-xs text-muted-foreground">
                                    {issue.file_path}{issue.line_number && `:${issue.line_number}`}
                                  </p>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </TabsContent>

                {/* Architecture Tab */}
                <TabsContent value="architecture" className="mt-4 space-y-4">
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <Gauge className="h-5 w-5" />
                        Architecture Analysis
                      </CardTitle>
                      <CardDescription>
                        Code complexity and structure evaluation
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      {/* Organization */}
                      {codeResult.analysis?.architecture && (
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <span className="text-sm text-muted-foreground">Folder Organization</span>
                          <p className="font-medium">{codeResult.analysis?.architecture?.folder_organization ?? 'N/A'}</p>
                        </div>
                        <div>
                          <span className="text-sm text-muted-foreground">Module Boundaries</span>
                          <p className="font-medium">{codeResult.analysis?.architecture?.module_boundaries ?? 'N/A'}</p>
                        </div>
                      </div>
                      )}

                      {/* Complexity Metrics */}
                      {codeResult.analysis?.architecture && (
                      <div className="grid grid-cols-2 gap-4">
                        <div className="rounded-lg border p-3">
                          <span className="text-sm text-muted-foreground">Total Complexity</span>
                          <p className="text-2xl font-bold">{codeResult.analysis?.architecture?.total_complexity ?? 0}</p>
                        </div>
                        <div className="rounded-lg border p-3">
                          <span className="text-sm text-muted-foreground">Avg Complexity</span>
                          <p className="text-2xl font-bold">{(codeResult.analysis?.architecture?.avg_complexity ?? 0).toFixed(1)}</p>
                        </div>
                      </div>
                      )}

                      {/* Complex Files */}
                      {(codeResult.analysis?.architecture?.complex_files?.length ?? 0) > 0 && (
                        <div>
                          <span className="text-sm font-medium">High Complexity Files:</span>
                          <div className="mt-2 space-y-1">
                            {codeResult.analysis?.architecture?.complex_files?.map((file, i) => (
                              <div key={i} className="flex items-center gap-2 text-sm text-orange-500">
                                <FileCode className="h-4 w-4" />
                                <span>{file}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Circular Dependencies */}
                      {(codeResult.analysis?.architecture?.circular_dependencies?.length ?? 0) > 0 && (
                        <div className="rounded-lg border border-red-500/50 bg-red-500/10 p-3">
                          <span className="text-sm font-medium text-red-500">Circular Dependencies Detected:</span>
                          <div className="mt-2 space-y-1">
                            {codeResult.analysis?.architecture?.circular_dependencies?.map((cycle, i) => (
                              <p key={i} className="text-sm">{cycle.join(' → ')}</p>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Architecture Issues */}
                      {(codeResult.analysis?.architecture?.issues?.length ?? 0) > 0 && (
                        <div className="mt-4">
                          <span className="text-sm font-medium">Issues:</span>
                          <div className="space-y-2 mt-2">
                            {codeResult.analysis?.architecture?.issues?.map((issue, i) => (
                              <div key={i} className={`rounded-lg border p-3 ${getSeverityColor(issue.severity)}`}>
                                <div className="flex items-center gap-2">
                                  <Badge variant="outline" className={getSeverityColor(issue.severity)}>
                                    {issue.severity}
                                  </Badge>
                                  <span className="font-semibold">{issue.title}</span>
                                </div>
                                <p className="mt-1 text-sm">{issue.description}</p>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </TabsContent>

                {/* Security Tab */}
                <TabsContent value="security" className="mt-4">
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <Bug className="h-5 w-5" />
                        Security Findings
                      </CardTitle>
                      <CardDescription>
                        Vulnerabilities detected during the security scan
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      {(codeResult.analysis?.backend?.security_findings?.length ?? 0) > 0 ? (
                        <div className="space-y-4">
                          {codeResult.analysis?.backend?.security_findings?.map((finding, i) => (
                            <div
                              key={i}
                              className={`rounded-lg border p-4 ${getSeverityColor(finding.severity)}`}
                            >
                              <div className="flex items-start justify-between">
                                <div>
                                  <div className="flex items-center gap-2">
                                    <Badge variant="outline" className={getSeverityColor(finding.severity)}>
                                      {finding.severity}
                                    </Badge>
                                    <span className="font-semibold">{finding.title}</span>
                                  </div>
                                  <p className="mt-1 text-sm text-muted-foreground">
                                    {finding.file}
                                    {finding.line && `:${finding.line}`}
                                  </p>
                                </div>
                              </div>
                              <p className="mt-2 text-sm">{finding.description}</p>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="flex items-center gap-2 text-green-500">
                          <CheckCircle2 className="h-5 w-5" />
                          <span>No security vulnerabilities found!</span>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </TabsContent>
              </Tabs>
              )}

              {/* Recommendations Section */}
              {codeResult.recommendations && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Zap className="h-5 w-5" />
                    Recommendations ({codeResult.recommendations?.length ?? 0})
                  </CardTitle>
                  <CardDescription>
                    Context-aware suggestions to improve your codebase
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {(codeResult.recommendations?.length ?? 0) > 0 ? (
                    <div className="space-y-4">
                      {codeResult.recommendations.map((rec, i) => (
                        <div
                          key={i}
                          className={`rounded-lg border p-4 ${
                            rec.priority === 'critical' ? 'border-red-500/50 bg-red-500/5' :
                            rec.priority === 'high' ? 'border-orange-500/50 bg-orange-500/5' :
                            rec.priority === 'medium' ? 'border-yellow-500/50 bg-yellow-500/5' :
                            'border-blue-500/50 bg-blue-500/5'
                          }`}
                        >
                          <div className="flex items-start justify-between gap-4">
                            <div className="flex-1">
                              <div className="flex items-center gap-2 flex-wrap">
                                <Badge
                                  variant="outline"
                                  className={
                                    rec.priority === 'critical' ? 'bg-red-500/20 text-red-500' :
                                    rec.priority === 'high' ? 'bg-orange-500/20 text-orange-500' :
                                    rec.priority === 'medium' ? 'bg-yellow-500/20 text-yellow-500' :
                                    'bg-blue-500/20 text-blue-500'
                                  }
                                >
                                  {rec.priority}
                                </Badge>
                                <Badge variant="secondary">{rec.category}</Badge>
                                <span className="font-semibold">{rec.title}</span>
                              </div>
                              <p className="mt-2 text-sm">{rec.description}</p>

                              {rec.file_path && (
                                <p className="mt-2 text-xs text-muted-foreground">
                                  <FileCode className="inline h-3 w-3 mr-1" />
                                  {rec.file_path}{rec.line_number && `:${rec.line_number}`}
                                </p>
                              )}

                              {/* Code suggestions */}
                              {rec.current_code && rec.suggested_code && (
                                <div className="mt-3 space-y-2">
                                  <div className="rounded bg-red-500/10 p-2">
                                    <span className="text-xs text-red-500 font-medium">Current:</span>
                                    <pre className="mt-1 text-xs overflow-x-auto">{rec.current_code}</pre>
                                  </div>
                                  <div className="rounded bg-green-500/10 p-2">
                                    <span className="text-xs text-green-500 font-medium">Suggested:</span>
                                    <pre className="mt-1 text-xs overflow-x-auto">{rec.suggested_code}</pre>
                                  </div>
                                </div>
                              )}

                              <div className="mt-3 flex items-center gap-4 text-xs text-muted-foreground">
                                <span>Impact: <span className="font-medium">{rec.impact}</span></span>
                                <span>Effort: <span className="font-medium">{rec.effort}</span></span>
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="flex items-center gap-2 text-green-500">
                      <CheckCircle2 className="h-5 w-5" />
                      <span>No recommendations - your codebase looks great!</span>
                    </div>
                  )}
                </CardContent>
              </Card>
              )}
            </div>
          )}
        </TabsContent>

        {/* Mobile App Audit Tab */}
        <TabsContent value="mobile" className="space-y-6 mt-6">
          {/* Mobile Audit Form */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Smartphone className="h-5 w-5" />
                Mobile App Audit
              </CardTitle>
              <CardDescription>
                Upload screenshots of your iOS or Android app to analyze UI/UX, accessibility, and platform compliance
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="app-name">App Name</Label>
                  <Input
                    id="app-name"
                    placeholder="e.g., My Awesome App"
                    value={mobileAppName}
                    onChange={(e) => setMobileAppName(e.target.value)}
                    disabled={mobileAuditRunning}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="platform">Platform</Label>
                  <select
                    id="platform"
                    value={mobilePlatform}
                    onChange={(e) => setMobilePlatform(e.target.value as 'ios' | 'android')}
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background"
                    disabled={mobileAuditRunning}
                  >
                    <option value="ios">iOS (iPhone/iPad)</option>
                    <option value="android">Android</option>
                  </select>
                </div>
              </div>

              {/* Screenshot Upload */}
              <div className="space-y-2">
                <Label>Screenshots</Label>
                <div className="border-2 border-dashed rounded-lg p-6 text-center hover:border-primary/50 transition-colors">
                  <input
                    ref={mobileFileInputRef}
                    type="file"
                    accept="image/*"
                    multiple
                    onChange={handleMobileScreenshotUpload}
                    className="hidden"
                    disabled={mobileAuditRunning}
                  />
                  <div className="flex flex-col items-center gap-2">
                    <ImageIcon className="h-10 w-10 text-muted-foreground" />
                    <p className="text-sm text-muted-foreground">
                      Drag and drop screenshots here, or{' '}
                      <button
                        type="button"
                        onClick={() => mobileFileInputRef.current?.click()}
                        className="text-primary hover:underline"
                        disabled={mobileAuditRunning}
                      >
                        browse
                      </button>
                    </p>
                    <p className="text-xs text-muted-foreground">
                      PNG, JPG up to 10MB each. Upload 3-10 screens for best results.
                    </p>
                  </div>
                </div>

                {/* Screenshot Previews */}
                {mobileScreenshotPreviews.length > 0 && (
                  <div className="grid grid-cols-3 md:grid-cols-5 gap-3 mt-4">
                    {mobileScreenshotPreviews.map((preview, idx) => (
                      <div key={idx} className="relative group">
                        <img
                          src={preview}
                          alt={`Screenshot ${idx + 1}`}
                          className="w-full h-32 object-cover rounded-lg border"
                        />
                        <button
                          type="button"
                          onClick={() => removeMobileScreenshot(idx)}
                          className="absolute top-1 right-1 p-1 bg-red-500 text-white rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
                          disabled={mobileAuditRunning}
                        >
                          <Trash2 className="h-3 w-3" />
                        </button>
                        <span className="absolute bottom-1 left-1 text-xs bg-black/50 text-white px-1 rounded">
                          {idx + 1}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Advanced Options Toggle */}
              <div className="border-t pt-4">
                <button
                  type="button"
                  onClick={() => setShowAdvancedOptions(!showAdvancedOptions)}
                  className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
                >
                  <TrendingUp className="h-4 w-4" />
                  {showAdvancedOptions ? 'Hide' : 'Show'} Advanced Options (Analytics & Business Goals)
                </button>

                {showAdvancedOptions && (
                  <div className="mt-4 space-y-6">
                    {/* Analytics Data Section */}
                    <div className="space-y-3">
                      <div className="flex items-center gap-2">
                        <input
                          type="checkbox"
                          id="has-analytics"
                          checked={hasAnalytics}
                          onChange={(e) => setHasAnalytics(e.target.checked)}
                          className="rounded"
                        />
                        <Label htmlFor="has-analytics" className="text-sm font-medium">
                          I have funnel/analytics data
                        </Label>
                      </div>

                      {hasAnalytics && (
                        <div className="ml-6 space-y-3 p-4 bg-muted/50 rounded-lg">
                          <p className="text-xs text-muted-foreground">
                            Add funnel steps to correlate UX issues with drop-off points
                          </p>
                          {funnelSteps.map((step, idx) => (
                            <div key={idx} className="grid grid-cols-5 gap-2 items-end">
                              <div>
                                <Label className="text-xs">Step Name</Label>
                                <Input
                                  value={step.name}
                                  onChange={(e) => {
                                    const updated = [...funnelSteps]
                                    updated[idx].name = e.target.value
                                    setFunnelSteps(updated)
                                  }}
                                  placeholder="e.g., Login"
                                  className="h-8 text-sm"
                                />
                              </div>
                              <div>
                                <Label className="text-xs">Screen</Label>
                                <Input
                                  value={step.screen_name}
                                  onChange={(e) => {
                                    const updated = [...funnelSteps]
                                    updated[idx].screen_name = e.target.value
                                    setFunnelSteps(updated)
                                  }}
                                  placeholder="Login Screen"
                                  className="h-8 text-sm"
                                />
                              </div>
                              <div>
                                <Label className="text-xs">Users In</Label>
                                <Input
                                  type="number"
                                  value={step.users_entered || ''}
                                  onChange={(e) => {
                                    const updated = [...funnelSteps]
                                    updated[idx].users_entered = parseInt(e.target.value) || 0
                                    setFunnelSteps(updated)
                                  }}
                                  placeholder="1000"
                                  className="h-8 text-sm"
                                />
                              </div>
                              <div>
                                <Label className="text-xs">Users Out</Label>
                                <Input
                                  type="number"
                                  value={step.users_completed || ''}
                                  onChange={(e) => {
                                    const updated = [...funnelSteps]
                                    updated[idx].users_completed = parseInt(e.target.value) || 0
                                    setFunnelSteps(updated)
                                  }}
                                  placeholder="800"
                                  className="h-8 text-sm"
                                />
                              </div>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => setFunnelSteps(funnelSteps.filter((_, i) => i !== idx))}
                                className="h-8 px-2"
                              >
                                <Trash2 className="h-4 w-4 text-red-500" />
                              </Button>
                            </div>
                          ))}
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setFunnelSteps([...funnelSteps, { name: '', screen_name: '', users_entered: 0, users_completed: 0 }])}
                          >
                            + Add Funnel Step
                          </Button>
                        </div>
                      )}
                    </div>

                    {/* Business Goals Section */}
                    <div className="space-y-3">
                      <div className="flex items-center gap-2">
                        <input
                          type="checkbox"
                          id="has-business-goals"
                          checked={hasBusinessGoals}
                          onChange={(e) => setHasBusinessGoals(e.target.checked)}
                          className="rounded"
                        />
                        <Label htmlFor="has-business-goals" className="text-sm font-medium">
                          Calculate ROI projections
                        </Label>
                      </div>

                      {hasBusinessGoals && (
                        <div className="ml-6 space-y-3 p-4 bg-muted/50 rounded-lg">
                          <p className="text-xs text-muted-foreground">
                            Provide business metrics to estimate revenue impact of fixes
                          </p>
                          <div className="grid grid-cols-2 gap-4">
                            <div>
                              <Label className="text-xs">Primary Goal</Label>
                              <select
                                value={businessGoals.primary_goal}
                                onChange={(e) => setBusinessGoals({ ...businessGoals, primary_goal: e.target.value })}
                                className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm"
                              >
                                <option value="">Select goal...</option>
                                <option value="increase_signups">Increase Signups</option>
                                <option value="reduce_churn">Reduce Churn</option>
                                <option value="increase_purchases">Increase Purchases</option>
                                <option value="improve_engagement">Improve Engagement</option>
                                <option value="reduce_support_tickets">Reduce Support Tickets</option>
                              </select>
                            </div>
                            <div>
                              <Label className="text-xs">Monthly Active Users</Label>
                              <Input
                                type="number"
                                value={businessGoals.monthly_active_users || ''}
                                onChange={(e) => setBusinessGoals({ ...businessGoals, monthly_active_users: parseInt(e.target.value) || 0 })}
                                placeholder="50000"
                                className="h-9 text-sm"
                              />
                            </div>
                            <div>
                              <Label className="text-xs">Avg Revenue Per User ($)</Label>
                              <Input
                                type="number"
                                step="0.01"
                                value={businessGoals.average_revenue_per_user || ''}
                                onChange={(e) => setBusinessGoals({ ...businessGoals, average_revenue_per_user: parseFloat(e.target.value) || 0 })}
                                placeholder="5.00"
                                className="h-9 text-sm"
                              />
                            </div>
                            <div>
                              <Label className="text-xs">Current Conversion %</Label>
                              <Input
                                type="number"
                                step="0.1"
                                value={businessGoals.current_value || ''}
                                onChange={(e) => setBusinessGoals({ ...businessGoals, current_value: parseFloat(e.target.value) || 0 })}
                                placeholder="2.5"
                                className="h-9 text-sm"
                              />
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>

              <div className="flex justify-between items-center">
                <div>
                  <p className="text-sm text-muted-foreground">
                    {mobileScreenshots.length} screenshot{mobileScreenshots.length !== 1 ? 's' : ''} selected
                  </p>
                  {(hasAnalytics || hasBusinessGoals) && (
                    <p className="text-xs text-primary">
                      + {hasAnalytics ? 'Analytics data' : ''}{hasAnalytics && hasBusinessGoals ? ', ' : ''}{hasBusinessGoals ? 'ROI projections' : ''}
                    </p>
                  )}
                </div>
                <Button
                  variant="gradient"
                  onClick={runMobileAudit}
                  disabled={!mobileAppName.trim() || mobileScreenshots.length === 0 || mobileAuditRunning}
                >
                  {mobileAuditRunning ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <Play className="mr-2 h-4 w-4" />
                  )}
                  {mobileAuditRunning ? 'Analyzing...' : 'Run Audit'}
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Mobile Audit Progress */}
          {mobileSteps.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Audit Progress</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {mobileSteps.map((step) => (
                    <div key={step.id} className="flex items-center gap-3">
                      {step.status === 'pending' && (
                        <div className="h-5 w-5 rounded-full border-2 border-muted" />
                      )}
                      {step.status === 'running' && (
                        <Loader2 className="h-5 w-5 animate-spin text-primary" />
                      )}
                      {step.status === 'completed' && (
                        <CheckCircle2 className="h-5 w-5 text-green-500" />
                      )}
                      {step.status === 'error' && (
                        <XCircle className="h-5 w-5 text-red-500" />
                      )}
                      <span
                        className={
                          step.status === 'pending'
                            ? 'text-muted-foreground'
                            : step.status === 'error'
                            ? 'text-red-500'
                            : ''
                        }
                      >
                        {step.name}
                      </span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Mobile Audit Error */}
          {mobileError && (
            <Card className="border-red-500/50 bg-red-500/10">
              <CardContent className="flex items-center gap-3 pt-6">
                <AlertTriangle className="h-5 w-5 text-red-500" />
                <span className="text-red-500">{mobileError}</span>
              </CardContent>
            </Card>
          )}

          {/* Mobile Audit Results */}
          {mobileResult && (
            <div className="space-y-6">
              {/* Summary Card */}
              <Card className="border-primary/20 bg-gradient-to-r from-primary/5 to-transparent">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Smartphone className="h-5 w-5 text-primary" />
                    {mobileResult.app_name} - {mobileResult.platform.toUpperCase()} Audit
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <p className="text-muted-foreground">{mobileResult.summary}</p>
                  <div className="flex items-center gap-4">
                    <Badge variant="secondary" className="capitalize">
                      {mobileResult.platform}
                    </Badge>
                    <Badge
                      variant="outline"
                      className={
                        mobileResult.confidence.color === 'green'
                          ? 'bg-green-500/20 text-green-500'
                          : mobileResult.confidence.color === 'yellow'
                          ? 'bg-yellow-500/20 text-yellow-500'
                          : 'bg-orange-500/20 text-orange-500'
                      }
                    >
                      {mobileResult.confidence.level} Confidence ({mobileResult.confidence.score}%)
                    </Badge>
                    <span className="text-sm text-muted-foreground">
                      {mobileResult.screen_analyses.length} screens analyzed
                    </span>
                  </div>
                </CardContent>
              </Card>

              {/* Overall Score & Category Scores */}
              <div className="grid gap-4 md:grid-cols-6">
                {/* Overall Score - Larger */}
                <Card className="md:col-span-2">
                  <CardContent className="pt-6">
                    <div className="flex flex-col items-center justify-center h-full">
                      <span className="text-sm font-medium text-muted-foreground">Overall Score</span>
                      <span className={`text-5xl font-bold mt-2 ${getScoreColor(mobileResult.overall_score)}`}>
                        {mobileResult.overall_score.toFixed(1)}
                      </span>
                      <span className="text-sm text-muted-foreground">/10</span>
                    </div>
                  </CardContent>
                </Card>

                {/* Category Scores */}
                <div className="md:col-span-4 grid grid-cols-2 md:grid-cols-4 gap-3">
                  {[
                    { key: 'accessibility', label: 'Accessibility', icon: Accessibility },
                    { key: 'ui_ux', label: 'UI/UX', icon: Eye },
                    { key: 'platform_compliance', label: 'Platform', icon: Smartphone },
                    { key: 'visual_design', label: 'Visual', icon: Palette },
                  ].map(({ key, label, icon: Icon }) => {
                    const score = mobileResult.scores[key as keyof typeof mobileResult.scores]
                    return (
                      <Card key={key}>
                        <CardContent className="pt-4 pb-4">
                          <div className="flex items-center gap-2">
                            <Icon className="h-4 w-4 text-muted-foreground" />
                            <span className="text-xs font-medium">{label}</span>
                          </div>
                          <div className="flex items-end gap-1 mt-1">
                            <span className={`text-2xl font-bold ${getScoreColor(score)}`}>
                              {score.toFixed(1)}
                            </span>
                            <span className="text-xs text-muted-foreground mb-1">/10</span>
                          </div>
                          <Progress value={score * 10} className="mt-2 h-1" />
                        </CardContent>
                      </Card>
                    )
                  })}
                </div>
              </div>

              {/* Issues & Screen Analysis Tabs */}
              <Tabs defaultValue={mobileResult.funnel_analysis ? "funnel" : "issues"}>
                <TabsList className="flex-wrap h-auto gap-1">
                  {mobileResult.funnel_analysis && (
                    <TabsTrigger value="funnel">
                      Funnel Analysis
                    </TabsTrigger>
                  )}
                  {mobileResult.roi_projection && (
                    <TabsTrigger value="roi">
                      ROI Projection
                    </TabsTrigger>
                  )}
                  {mobileResult.priority_matrix && (
                    <TabsTrigger value="matrix">
                      Priority Matrix
                    </TabsTrigger>
                  )}
                  <TabsTrigger value="issues">
                    Issues ({mobileResult.issues.length})
                  </TabsTrigger>
                  <TabsTrigger value="screens">
                    Screens ({mobileResult.screen_analyses.length})
                  </TabsTrigger>
                  <TabsTrigger value="recommendations">
                    Recommendations ({mobileResult.recommendations.length})
                  </TabsTrigger>
                </TabsList>

                {/* Funnel Analysis Tab */}
                {mobileResult.funnel_analysis && (
                  <TabsContent value="funnel" className="mt-4">
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                          <TrendingUp className="h-5 w-5" />
                          Funnel Analysis
                        </CardTitle>
                        <CardDescription>
                          User flow analysis with drop-off correlations
                        </CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-6">
                        {/* Overall Conversion */}
                        <div className="flex items-center justify-between p-4 bg-muted/50 rounded-lg">
                          <div>
                            <p className="text-sm text-muted-foreground">Overall Funnel Conversion</p>
                            <p className="text-3xl font-bold">{mobileResult.funnel_analysis.overall_conversion}%</p>
                          </div>
                          {mobileResult.funnel_analysis.biggest_drop_off && (
                            <div className="text-right">
                              <p className="text-sm text-muted-foreground">Biggest Drop-off</p>
                              <p className="text-lg font-semibold text-red-500">
                                {mobileResult.funnel_analysis.biggest_drop_off.step}
                              </p>
                              <p className="text-sm text-red-500">
                                {mobileResult.funnel_analysis.biggest_drop_off.drop_off_rate}% lost
                              </p>
                            </div>
                          )}
                        </div>

                        {/* Funnel Steps */}
                        <div className="space-y-2">
                          <h4 className="font-semibold">Funnel Steps</h4>
                          {mobileResult.funnel_analysis.steps.map((step, idx) => (
                            <div
                              key={idx}
                              className={`p-3 rounded-lg border ${step.is_problem_area ? 'border-red-500/50 bg-red-500/5' : 'border-border'}`}
                            >
                              <div className="flex items-center justify-between">
                                <div className="flex items-center gap-3">
                                  <span className="w-6 h-6 rounded-full bg-primary/10 text-primary flex items-center justify-center text-sm font-medium">
                                    {idx + 1}
                                  </span>
                                  <div>
                                    <p className="font-medium">{step.name}</p>
                                    {step.screen && <p className="text-xs text-muted-foreground">{step.screen}</p>}
                                  </div>
                                </div>
                                <div className="text-right">
                                  <p className="text-sm">
                                    {step.users_entered.toLocaleString()} → {step.users_completed.toLocaleString()}
                                  </p>
                                  <p className={`text-sm font-medium ${step.drop_off_rate > 20 ? 'text-red-500' : 'text-green-500'}`}>
                                    {step.drop_off_rate}% drop-off
                                  </p>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>

                        {/* Issue Correlations */}
                        {mobileResult.funnel_analysis.issue_correlations.length > 0 && (
                          <div className="space-y-2">
                            <h4 className="font-semibold">Issue Correlations</h4>
                            <p className="text-sm text-muted-foreground">UX issues that may be causing drop-offs</p>
                            {mobileResult.funnel_analysis.issue_correlations.map((corr, idx) => (
                              <div key={idx} className="p-3 rounded-lg bg-yellow-500/10 border border-yellow-500/30">
                                <div className="flex items-start gap-2">
                                  <AlertTriangle className="h-4 w-4 text-yellow-500 mt-0.5" />
                                  <div>
                                    <p className="font-medium">{corr.issue}</p>
                                    <p className="text-sm text-muted-foreground">
                                      Found at "{corr.funnel_step}" ({corr.drop_off_rate}% drop-off)
                                    </p>
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  </TabsContent>
                )}

                {/* ROI Projection Tab */}
                {mobileResult.roi_projection && (
                  <TabsContent value="roi" className="mt-4">
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                          <Target className="h-5 w-5" />
                          ROI Projection
                        </CardTitle>
                        <CardDescription>
                          Estimated business impact of fixing identified issues
                        </CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-6">
                        {/* Revenue Impact */}
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                          <div className="p-4 rounded-lg bg-muted/50 text-center">
                            <p className="text-sm text-muted-foreground">Current Monthly</p>
                            <p className="text-2xl font-bold">${mobileResult.roi_projection.current_monthly_revenue.toLocaleString()}</p>
                          </div>
                          <div className="p-4 rounded-lg bg-green-500/10 text-center">
                            <p className="text-sm text-muted-foreground">Projected Monthly</p>
                            <p className="text-2xl font-bold text-green-600">${mobileResult.roi_projection.projected_monthly_revenue.toLocaleString()}</p>
                          </div>
                          <div className="p-4 rounded-lg bg-primary/10 text-center">
                            <p className="text-sm text-muted-foreground">Monthly Gain</p>
                            <p className="text-2xl font-bold text-primary">+${mobileResult.roi_projection.monthly_gain.toLocaleString()}</p>
                          </div>
                          <div className="p-4 rounded-lg bg-primary/10 text-center">
                            <p className="text-sm text-muted-foreground">Annual Gain</p>
                            <p className="text-2xl font-bold text-primary">+${mobileResult.roi_projection.annual_gain.toLocaleString()}</p>
                          </div>
                        </div>

                        {/* Conversion Improvement */}
                        <div className="p-4 rounded-lg border">
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-sm font-medium">Projected Conversion Improvement</span>
                            <span className="text-lg font-bold text-green-600">+{mobileResult.roi_projection.conversion_improvement}%</span>
                          </div>
                          <p className="text-sm text-muted-foreground">
                            Based on fixing {mobileResult.roi_projection.issues_addressed} high-priority issues
                          </p>
                        </div>

                        {/* Assumptions */}
                        <div className="space-y-2">
                          <h4 className="font-semibold text-sm">Calculation Assumptions</h4>
                          <ul className="text-sm text-muted-foreground space-y-1">
                            {mobileResult.roi_projection.assumptions.map((assumption, idx) => (
                              <li key={idx} className="flex items-center gap-2">
                                <span className="w-1.5 h-1.5 rounded-full bg-muted-foreground" />
                                {assumption}
                              </li>
                            ))}
                          </ul>
                        </div>
                      </CardContent>
                    </Card>
                  </TabsContent>
                )}

                {/* Priority Matrix Tab */}
                {mobileResult.priority_matrix && (
                  <TabsContent value="matrix" className="mt-4">
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                          <Target className="h-5 w-5" />
                          Priority Matrix
                        </CardTitle>
                        <CardDescription>
                          Issues categorized by impact and effort
                        </CardDescription>
                      </CardHeader>
                      <CardContent>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {/* Quick Wins */}
                          <div className="p-4 rounded-lg border-2 border-green-500/50 bg-green-500/5">
                            <h4 className="font-semibold text-green-600 mb-2 flex items-center gap-2">
                              <CheckCircle2 className="h-4 w-4" />
                              Quick Wins ({mobileResult.priority_matrix.quick_wins.length})
                            </h4>
                            <p className="text-xs text-muted-foreground mb-3">High impact, low effort - do these first!</p>
                            {mobileResult.priority_matrix.quick_wins.length > 0 ? (
                              <ul className="space-y-2">
                                {mobileResult.priority_matrix.quick_wins.map((item, idx) => (
                                  <li key={idx} className="text-sm p-2 bg-background rounded">
                                    <span className="font-medium">{item.title}</span>
                                    {item.screen && <span className="text-muted-foreground text-xs block">{item.screen}</span>}
                                  </li>
                                ))}
                              </ul>
                            ) : (
                              <p className="text-sm text-muted-foreground">No quick wins identified</p>
                            )}
                          </div>

                          {/* Major Projects */}
                          <div className="p-4 rounded-lg border-2 border-orange-500/50 bg-orange-500/5">
                            <h4 className="font-semibold text-orange-600 mb-2 flex items-center gap-2">
                              <AlertTriangle className="h-4 w-4" />
                              Major Projects ({mobileResult.priority_matrix.major_projects.length})
                            </h4>
                            <p className="text-xs text-muted-foreground mb-3">High impact, high effort - plan these carefully</p>
                            {mobileResult.priority_matrix.major_projects.length > 0 ? (
                              <ul className="space-y-2">
                                {mobileResult.priority_matrix.major_projects.map((item, idx) => (
                                  <li key={idx} className="text-sm p-2 bg-background rounded">
                                    <span className="font-medium">{item.title}</span>
                                    {item.screen && <span className="text-muted-foreground text-xs block">{item.screen}</span>}
                                  </li>
                                ))}
                              </ul>
                            ) : (
                              <p className="text-sm text-muted-foreground">No major projects identified</p>
                            )}
                          </div>

                          {/* Fill-ins */}
                          <div className="p-4 rounded-lg border border-border">
                            <h4 className="font-semibold text-muted-foreground mb-2">
                              Fill-ins ({mobileResult.priority_matrix.fill_ins.length})
                            </h4>
                            <p className="text-xs text-muted-foreground mb-3">Low impact, low effort - do when time permits</p>
                            {mobileResult.priority_matrix.fill_ins.length > 0 ? (
                              <ul className="space-y-1">
                                {mobileResult.priority_matrix.fill_ins.slice(0, 3).map((item, idx) => (
                                  <li key={idx} className="text-sm text-muted-foreground">{item.title}</li>
                                ))}
                                {mobileResult.priority_matrix.fill_ins.length > 3 && (
                                  <li className="text-xs text-muted-foreground">+{mobileResult.priority_matrix.fill_ins.length - 3} more</li>
                                )}
                              </ul>
                            ) : (
                              <p className="text-sm text-muted-foreground">None</p>
                            )}
                          </div>

                          {/* Thankless Tasks */}
                          <div className="p-4 rounded-lg border border-border bg-muted/20">
                            <h4 className="font-semibold text-muted-foreground mb-2">
                              Deprioritize ({mobileResult.priority_matrix.thankless_tasks.length})
                            </h4>
                            <p className="text-xs text-muted-foreground mb-3">Low impact, high effort - consider skipping</p>
                            {mobileResult.priority_matrix.thankless_tasks.length > 0 ? (
                              <ul className="space-y-1">
                                {mobileResult.priority_matrix.thankless_tasks.slice(0, 2).map((item, idx) => (
                                  <li key={idx} className="text-sm text-muted-foreground">{item.title}</li>
                                ))}
                                {mobileResult.priority_matrix.thankless_tasks.length > 2 && (
                                  <li className="text-xs text-muted-foreground">+{mobileResult.priority_matrix.thankless_tasks.length - 2} more</li>
                                )}
                              </ul>
                            ) : (
                              <p className="text-sm text-muted-foreground">None</p>
                            )}
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </TabsContent>
                )}

                {/* Issues Tab */}
                <TabsContent value="issues" className="mt-4">
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <AlertTriangle className="h-5 w-5" />
                        Issues Found
                      </CardTitle>
                      <CardDescription>
                        Problems detected across your app screens
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      {mobileResult.issues.length > 0 ? (
                        <div className="space-y-3">
                          {mobileResult.issues.map((issue, i) => (
                            <div
                              key={i}
                              className={`rounded-lg border p-4 ${getSeverityColor(issue.severity)}`}
                            >
                              <div className="flex items-start justify-between">
                                <div className="flex items-start gap-3">
                                  {getCategoryIcon(issue.category)}
                                  <div>
                                    <div className="flex items-center gap-2">
                                      <Badge
                                        variant="outline"
                                        className={getSeverityColor(issue.severity)}
                                      >
                                        {issue.severity}
                                      </Badge>
                                      <span className="font-semibold">{issue.title}</span>
                                    </div>
                                    <p className="mt-1 text-sm text-muted-foreground">
                                      {issue.description}
                                    </p>
                                    <p className="mt-2 text-sm">
                                      <strong>Impact:</strong> {issue.impact}
                                    </p>
                                    {issue.screen && (
                                      <p className="mt-1 text-xs text-muted-foreground">
                                        Found on: {issue.screen}
                                        {issue.location && ` - ${issue.location}`}
                                      </p>
                                    )}
                                  </div>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="flex items-center gap-2 text-green-500">
                          <CheckCircle2 className="h-5 w-5" />
                          <span>No significant issues found!</span>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </TabsContent>

                {/* Screens Tab */}
                <TabsContent value="screens" className="mt-4">
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <ImageIcon className="h-5 w-5" />
                        Screen Analysis
                      </CardTitle>
                      <CardDescription>
                        Detailed analysis of each uploaded screenshot
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        {mobileResult.screen_analyses.map((screen, i) => (
                          <div key={i} className="rounded-lg border p-4">
                            <div className="flex items-center justify-between mb-3">
                              <div className="flex items-center gap-2">
                                <Badge variant="secondary">{i + 1}</Badge>
                                <span className="font-semibold">{screen.screen_name}</span>
                              </div>
                              <div className="flex items-center gap-2">
                                {screen.issues.length > 0 ? (
                                  <Badge variant="destructive">
                                    {screen.issues.length} issues
                                  </Badge>
                                ) : (
                                  <Badge
                                    variant="secondary"
                                    className="bg-green-500/20 text-green-500"
                                  >
                                    No issues
                                  </Badge>
                                )}
                              </div>
                            </div>

                            {/* Screen Scores */}
                            <div className="grid grid-cols-4 gap-2 mb-3">
                              <div className="text-center">
                                <div className={`text-lg font-bold ${getScoreColor(screen.accessibility_score)}`}>
                                  {screen.accessibility_score.toFixed(1)}
                                </div>
                                <div className="text-xs text-muted-foreground">A11y</div>
                              </div>
                              <div className="text-center">
                                <div className={`text-lg font-bold ${getScoreColor(screen.ui_consistency_score)}`}>
                                  {screen.ui_consistency_score.toFixed(1)}
                                </div>
                                <div className="text-xs text-muted-foreground">UI/UX</div>
                              </div>
                              <div className="text-center">
                                <div className={`text-lg font-bold ${getScoreColor(screen.platform_compliance_score)}`}>
                                  {screen.platform_compliance_score.toFixed(1)}
                                </div>
                                <div className="text-xs text-muted-foreground">Platform</div>
                              </div>
                              <div className="text-center">
                                <div className={`text-lg font-bold ${getScoreColor(screen.visual_design_score)}`}>
                                  {screen.visual_design_score.toFixed(1)}
                                </div>
                                <div className="text-xs text-muted-foreground">Visual</div>
                              </div>
                            </div>

                            {/* Positive Aspects */}
                            {screen.positive_aspects.length > 0 && (
                              <div className="mt-3">
                                <p className="text-xs font-medium text-muted-foreground mb-1">
                                  Positive aspects:
                                </p>
                                <div className="flex flex-wrap gap-1">
                                  {screen.positive_aspects.map((aspect, j) => (
                                    <Badge key={j} variant="secondary" className="text-xs bg-green-500/10 text-green-600">
                                      <CheckCircle2 className="h-3 w-3 mr-1" />
                                      {aspect}
                                    </Badge>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>

                {/* Recommendations Tab */}
                <TabsContent value="recommendations" className="mt-4">
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <Zap className="h-5 w-5" />
                        Recommendations
                      </CardTitle>
                      <CardDescription>
                        Prioritized action items to improve your app
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      {mobileResult.recommendations.length > 0 ? (
                        <div className="space-y-4">
                          {mobileResult.recommendations.map((rec, i) => (
                            <div
                              key={i}
                              className={`rounded-lg border p-4 ${
                                rec.priority === 1
                                  ? 'border-red-500/50 bg-red-500/5'
                                  : rec.priority === 2
                                  ? 'border-orange-500/50 bg-orange-500/5'
                                  : 'border-yellow-500/50 bg-yellow-500/5'
                              }`}
                            >
                              <div className="flex items-start gap-4">
                                <div
                                  className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center font-bold text-white ${
                                    rec.priority === 1
                                      ? 'bg-red-500'
                                      : rec.priority === 2
                                      ? 'bg-orange-500'
                                      : 'bg-yellow-500'
                                  }`}
                                >
                                  {rec.priority}
                                </div>
                                <div className="flex-1">
                                  <div className="flex items-center gap-2 mb-1">
                                    <Badge variant="secondary">{rec.category}</Badge>
                                    <span className="font-semibold">{rec.title}</span>
                                  </div>
                                  <p className="text-sm text-muted-foreground">
                                    {rec.description}
                                  </p>
                                  <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                                    <span>
                                      Impact: <span className="font-medium">{rec.impact}</span>
                                    </span>
                                    <span>
                                      Effort: <span className="font-medium">{rec.effort}</span>
                                    </span>
                                  </div>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="flex items-center gap-2 text-green-500">
                          <CheckCircle2 className="h-5 w-5" />
                          <span>No recommendations - your app looks great!</span>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </TabsContent>
              </Tabs>
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  )
}
