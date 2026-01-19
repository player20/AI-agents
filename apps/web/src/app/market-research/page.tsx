'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
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
  Plus,
  LineChart,
  TrendingUp,
  AlertTriangle,
  Lightbulb,
  Search,
  Loader2,
  Building2,
  Target,
  Users,
  DollarSign,
  ExternalLink,
  Rocket,
  CheckCircle2,
  XCircle,
  AlertCircle,
  ArrowRight,
  Sparkles,
  Trophy,
  Zap,
  Eye,
  Globe,
  Download,
  FileText,
  Clock,
  Shield,
  Beaker,
  Wallet,
  BarChart3,
  TrendingDown,
  UserCircle,
} from 'lucide-react'

interface MarketInsight {
  type: 'trend' | 'opportunity' | 'risk' | 'competitor'
  title: string
  description: string
  confidence: number
}

interface MarketResearch {
  id: string
  query: string
  competitors: string[]
  industry: string
  status: 'pending' | 'completed' | 'error'
  insights: MarketInsight[]
  recommendations: string[]
  market_size?: {
    total: string
    addressable: string
    serviceable: string
  }
  created_at: string
}

// New types for Idea Validation
interface DiscoveredCompetitor {
  name: string
  description: string
  website?: string
  funding_stage?: string
  strengths: string[]
  weaknesses: string[]
  similarity_score: number
}

interface DifferentiationOpportunity {
  opportunity: string
  difficulty: string
  impact: string
  competitors_affected: number
}

interface NextStep {
  step: string
  why: string
  priority: 'critical' | 'high' | 'medium' | 'low'
}

interface TargetCustomer {
  demographics: string
  psychographics: string
  day_in_life: string
}

interface RevenueModel {
  suggested_models: string[]
  price_range: { low: string; mid: string; high: string }
  competitors_monetization: string
}

interface KeyRisk {
  risk: string
  severity: 'high' | 'medium' | 'low'
  mitigation: string
}

interface ValidationExperiment {
  experiment: string
  effort: 'low' | 'medium' | 'high'
  what_it_proves: string
}

interface ResourceEstimate {
  budget_range: { min: string; max: string }
  team_roles: string[]
  tech_stack: string[]
  timeline_to_mvp: string
}

interface SuccessMetric {
  metric: string
  target: string
  timeframe: string
}

interface IdeaValidation {
  id: string
  idea: string
  timestamp: string
  ai_powered?: boolean
  provider?: string | null
  model?: string | null
  executive_summary?: string
  discovered_industry: string
  industry_category: string
  target_customer?: TargetCustomer
  discovered_competitors: DiscoveredCompetitor[]
  market_landscape?: string
  problem_exists: boolean
  problem_severity: 'hair-on-fire' | 'significant' | 'nice-to-have'
  search_volume: string
  problem_evidence: string[]
  revenue_model?: RevenueModel
  viability_score: number
  viability_breakdown: {
    problem_validation: number
    competitive_landscape: number
    market_timing: number
    market_opportunity: number
  }
  key_risks?: KeyRisk[]
  differentiation_opportunities: DifferentiationOpportunity[]
  unique_angles: string[]
  validation_experiments?: ValidationExperiment[]
  resource_estimate?: ResourceEstimate
  success_metrics?: SuccessMetric[]
  market_timing: string
  market_timing_reasons: string[]
  market_saturation: string
  estimated_tam: string
  market_trends?: string[]
  go_no_go: 'GO' | 'CAUTION' | 'PIVOT' | 'STOP'
  verdict: string
  verdict_reasons: string[]
  next_steps: NextStep[]
  pivot_suggestions?: string[]
}

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8001'

const insightIcons = {
  trend: TrendingUp,
  opportunity: Lightbulb,
  risk: AlertTriangle,
  competitor: Building2,
}

const insightColors = {
  trend: 'bg-blue-500/20 text-blue-500 border-blue-500/50',
  opportunity: 'bg-green-500/20 text-green-500 border-green-500/50',
  risk: 'bg-red-500/20 text-red-500 border-red-500/50',
  competitor: 'bg-purple-500/20 text-purple-500 border-purple-500/50',
}

// Verdict styling
const verdictStyles = {
  GO: { bg: 'bg-green-500/10', border: 'border-green-500', text: 'text-green-500', icon: CheckCircle2 },
  CAUTION: { bg: 'bg-yellow-500/10', border: 'border-yellow-500', text: 'text-yellow-500', icon: AlertCircle },
  PIVOT: { bg: 'bg-orange-500/10', border: 'border-orange-500', text: 'text-orange-500', icon: AlertTriangle },
  STOP: { bg: 'bg-red-500/10', border: 'border-red-500', text: 'text-red-500', icon: XCircle },
}

const priorityColors = {
  critical: 'bg-red-500/20 text-red-500 border-red-500/50',
  high: 'bg-orange-500/20 text-orange-500 border-orange-500/50',
  medium: 'bg-yellow-500/20 text-yellow-500 border-yellow-500/50',
  low: 'bg-slate-500/20 text-slate-500 border-slate-500/50',
}

export default function MarketResearchPage() {
  // Mode toggle: beginner (idea validation) vs expert (market research)
  const [mode, setMode] = useState<'beginner' | 'expert'>('beginner')

  // Legacy market research state
  const [researches, setResearches] = useState<MarketResearch[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isCreateOpen, setIsCreateOpen] = useState(false)
  const [isRunning, setIsRunning] = useState(false)
  const [selectedResearch, setSelectedResearch] = useState<MarketResearch | null>(null)
  const [newResearch, setNewResearch] = useState({
    query: '',
    competitors: '',
    industry: '',
  })

  // New idea validation state
  const [ideaValidations, setIdeaValidations] = useState<IdeaValidation[]>([])
  const [selectedValidation, setSelectedValidation] = useState<IdeaValidation | null>(null)
  const [validationError, setValidationError] = useState<string | null>(null)
  const [newIdea, setNewIdea] = useState({
    idea: '',
    problem: '',
    target_users: '',
    provider: 'auto' as 'auto' | 'claude' | 'grok',  // 'auto' = auto-detect
  })

  useEffect(() => {
    fetchResearches()
    fetchIdeaValidations()
  }, [])

  const fetchIdeaValidations = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/idea-validation`)
      if (response.ok) {
        const data = await response.json()
        setIdeaValidations(data)
      }
    } catch (error) {
      console.error('Failed to fetch idea validations:', error)
    }
  }

  const handleValidateIdea = async () => {
    if (!newIdea.idea.trim()) return

    setIsRunning(true)
    setValidationError(null)

    try {
      const response = await fetch(`${BACKEND_URL}/api/idea-validation`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          idea: newIdea.idea,
          problem: newIdea.problem || null,
          target_users: newIdea.target_users || null,
          provider: newIdea.provider === 'auto' ? null : newIdea.provider,  // null = auto-detect
        }),
      })

      if (response.ok) {
        const result = await response.json()
        setIdeaValidations((prev) => [result, ...prev])
        setSelectedValidation(result)
        // Only close and reset on success
        setNewIdea({ idea: '', problem: '', target_users: '', provider: 'auto' })
        setIsCreateOpen(false)
      } else {
        const errorData = await response.json().catch(() => ({}))
        setValidationError(errorData.detail || `Server error: ${response.status}`)
      }
    } catch (error) {
      console.error('Idea validation failed:', error)
      setValidationError('Failed to connect to server. Please check if the backend is running on port 8001.')
    } finally {
      setIsRunning(false)
    }
  }

  const fetchResearches = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/market-research`)
      if (response.ok) {
        const data = await response.json()
        setResearches(data)
      }
    } catch (error) {
      console.error('Failed to fetch market research:', error)
      // Use mock data
      setResearches([
        {
          id: 'research_mock_1',
          query: 'AI-powered code generation tools',
          competitors: ['GitHub Copilot', 'Tabnine', 'Cursor'],
          industry: 'Developer Tools',
          status: 'completed',
          insights: [
            {
              type: 'trend',
              title: 'Rapid Market Growth',
              description: 'The AI code assistant market is projected to grow at 25% CAGR through 2028.',
              confidence: 0.89,
            },
            {
              type: 'opportunity',
              title: 'Enterprise Segment Underserved',
              description: 'Enterprise customers seeking on-premise solutions with compliance features.',
              confidence: 0.76,
            },
            {
              type: 'risk',
              title: 'Big Tech Competition',
              description: 'Microsoft, Google, and Amazon expanding AI developer tools rapidly.',
              confidence: 0.92,
            },
            {
              type: 'competitor',
              title: 'GitHub Copilot Dominance',
              description: 'Copilot has ~40% market share with 1.3M paid subscribers.',
              confidence: 0.85,
            },
          ],
          recommendations: [
            'Focus on differentiation through superior code quality and specialized frameworks',
            'Target mid-market companies not well-served by enterprise solutions',
            'Build strong integrations with popular IDEs beyond VS Code',
            'Consider vertical specialization (e.g., security-focused, data science)',
          ],
          market_size: {
            total: '$2.5B',
            addressable: '$800M',
            serviceable: '$150M',
          },
          created_at: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
        },
      ])
    } finally {
      setIsLoading(false)
    }
  }

  const handleExportReport = async () => {
    if (!selectedValidation) return

    const v = selectedValidation

    // Generate a professional HTML report
    const htmlContent = `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Idea Validation Report - ${v.idea.slice(0, 50)}...</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', system-ui, sans-serif; line-height: 1.6; color: #1a1a2e; background: #f8fafc; }
        .container { max-width: 900px; margin: 0 auto; padding: 2rem; }
        .header { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); color: white; padding: 3rem 2rem; border-radius: 12px; margin-bottom: 2rem; }
        .header h1 { font-size: 1.5rem; margin-bottom: 1rem; }
        .header p { opacity: 0.9; font-size: 0.95rem; }
        .verdict-banner { display: flex; align-items: center; gap: 1rem; margin-top: 1.5rem; padding: 1rem; background: rgba(255,255,255,0.1); border-radius: 8px; }
        .verdict-badge { padding: 0.5rem 1.5rem; border-radius: 6px; font-weight: 700; font-size: 1.25rem; }
        .verdict-go { background: #10b981; }
        .verdict-caution { background: #f59e0b; }
        .verdict-pivot { background: #f97316; }
        .verdict-stop { background: #ef4444; }
        .score { font-size: 2rem; font-weight: 800; }
        .section { background: white; border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        .section h2 { font-size: 1.1rem; color: #1a1a2e; margin-bottom: 1rem; display: flex; align-items: center; gap: 0.5rem; }
        .section h2::before { content: ''; width: 4px; height: 20px; background: #6366f1; border-radius: 2px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1rem; }
        .card { background: #f8fafc; border-radius: 8px; padding: 1rem; border: 1px solid #e2e8f0; }
        .card-title { font-size: 0.75rem; text-transform: uppercase; color: #64748b; margin-bottom: 0.25rem; }
        .card-value { font-size: 1.1rem; font-weight: 600; }
        .badge { display: inline-block; padding: 0.25rem 0.75rem; border-radius: 4px; font-size: 0.75rem; font-weight: 600; }
        .badge-green { background: #dcfce7; color: #166534; }
        .badge-yellow { background: #fef9c3; color: #854d0e; }
        .badge-red { background: #fee2e2; color: #991b1b; }
        .badge-blue { background: #dbeafe; color: #1e40af; }
        .list { list-style: none; }
        .list li { padding: 0.5rem 0; border-bottom: 1px solid #e2e8f0; display: flex; align-items: flex-start; gap: 0.5rem; }
        .list li:last-child { border-bottom: none; }
        .list li::before { content: '✓'; color: #10b981; font-weight: 700; }
        .competitor { border: 1px solid #e2e8f0; border-radius: 8px; padding: 1rem; margin-bottom: 0.75rem; }
        .competitor h4 { font-size: 1rem; margin-bottom: 0.5rem; }
        .competitor p { font-size: 0.875rem; color: #64748b; }
        .progress-bar { height: 8px; background: #e2e8f0; border-radius: 4px; overflow: hidden; margin-top: 0.25rem; }
        .progress-fill { height: 100%; background: #6366f1; border-radius: 4px; }
        .step { display: flex; gap: 1rem; padding: 1rem; background: #f8fafc; border-radius: 8px; margin-bottom: 0.75rem; }
        .step-number { width: 32px; height: 32px; background: #6366f1; color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; flex-shrink: 0; }
        .step-content { flex: 1; }
        .step-title { font-weight: 600; }
        .step-desc { font-size: 0.875rem; color: #64748b; }
        .footer { text-align: center; padding: 2rem; color: #64748b; font-size: 0.875rem; }
        @media print { body { background: white; } .container { padding: 0; } }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Business Idea Validation Report</h1>
            <p>${v.idea}</p>
            <div class="verdict-banner">
                <span class="verdict-badge verdict-${v.go_no_go.toLowerCase()}">${v.go_no_go}</span>
                <span class="score">${v.viability_score}/100</span>
            </div>
        </div>

        ${v.executive_summary ? `
        <div class="section">
            <h2>Executive Summary</h2>
            <p style="font-size: 1.1rem; line-height: 1.8;">${v.executive_summary}</p>
        </div>
        ` : ''}

        <div class="section">
            <h2>Verdict & Key Reasons</h2>
            <p style="font-size: 1rem; margin-bottom: 1rem;">${v.verdict}</p>
            <ul class="list">
                ${v.verdict_reasons.map(r => `<li>${r}</li>`).join('')}
            </ul>
        </div>

        <div class="section">
            <h2>Market Overview</h2>
            <div class="grid">
                <div class="card">
                    <div class="card-title">Industry</div>
                    <div class="card-value">${v.discovered_industry}</div>
                    <div style="font-size: 0.75rem; color: #64748b;">${v.industry_category}</div>
                </div>
                <div class="card">
                    <div class="card-title">Market Size (TAM)</div>
                    <div class="card-value">${v.estimated_tam}</div>
                </div>
                <div class="card">
                    <div class="card-title">Market Saturation</div>
                    <div class="card-value"><span class="badge badge-${v.market_saturation === 'blue-ocean' ? 'blue' : v.market_saturation === 'growing' ? 'green' : 'yellow'}">${v.market_saturation.replace('-', ' ').toUpperCase()}</span></div>
                </div>
                <div class="card">
                    <div class="card-title">Market Timing</div>
                    <div class="card-value"><span class="badge badge-${v.market_timing === 'excellent' || v.market_timing === 'good' ? 'green' : 'yellow'}">${v.market_timing.toUpperCase()}</span></div>
                </div>
            </div>
        </div>

        ${v.target_customer ? `
        <div class="section">
            <h2>Target Customer Profile</h2>
            <div class="grid">
                <div class="card">
                    <div class="card-title">Demographics</div>
                    <p style="font-size: 0.9rem;">${v.target_customer.demographics}</p>
                </div>
                <div class="card">
                    <div class="card-title">Psychographics</div>
                    <p style="font-size: 0.9rem;">${v.target_customer.psychographics}</p>
                </div>
                <div class="card" style="grid-column: 1 / -1;">
                    <div class="card-title">A Day in Their Life</div>
                    <p style="font-size: 0.9rem;">${v.target_customer.day_in_life}</p>
                </div>
            </div>
        </div>
        ` : ''}

        <div class="section">
            <h2>Problem Validation</h2>
            <div style="display: flex; gap: 1rem; align-items: center; margin-bottom: 1rem;">
                <span class="badge badge-${v.problem_severity === 'hair-on-fire' ? 'red' : v.problem_severity === 'significant' ? 'yellow' : 'blue'}">${v.problem_severity.replace('-', ' ').toUpperCase()}</span>
                <span style="font-size: 0.875rem; color: #64748b;">Search Volume: <strong>${v.search_volume}</strong></span>
            </div>
            <ul class="list">
                ${v.problem_evidence.map(e => `<li>${e}</li>`).join('')}
            </ul>
        </div>

        <div class="section">
            <h2>Viability Breakdown</h2>
            ${Object.entries(v.viability_breakdown).map(([key, value]) => `
            <div style="margin-bottom: 1rem;">
                <div style="display: flex; justify-content: space-between; font-size: 0.875rem; margin-bottom: 0.25rem;">
                    <span style="text-transform: capitalize;">${key.replace(/_/g, ' ')}</span>
                    <span style="font-weight: 600;">${value}/100</span>
                </div>
                <div class="progress-bar"><div class="progress-fill" style="width: ${value}%;"></div></div>
            </div>
            `).join('')}
        </div>

        <div class="section">
            <h2>Competitors (${v.discovered_competitors.length})</h2>
            ${v.discovered_competitors.map(c => `
            <div class="competitor">
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <div>
                        <h4>${c.name} ${c.funding_stage ? `<span class="badge badge-blue">${c.funding_stage}</span>` : ''}</h4>
                        <p>${c.description}</p>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 0.75rem; color: #64748b;">Similarity</div>
                        <div style="font-size: 1.25rem; font-weight: 700;">${Math.round(c.similarity_score * 100)}%</div>
                    </div>
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 0.75rem;">
                    <div>
                        <div style="font-size: 0.75rem; color: #10b981; font-weight: 600; margin-bottom: 0.25rem;">Strengths</div>
                        <ul style="font-size: 0.8rem; padding-left: 1rem;">${Array.isArray(c.strengths) ? c.strengths.map(s => `<li>${s}</li>`).join('') : `<li>${c.strengths || 'N/A'}</li>`}</ul>
                    </div>
                    <div>
                        <div style="font-size: 0.75rem; color: #ef4444; font-weight: 600; margin-bottom: 0.25rem;">Weaknesses</div>
                        <ul style="font-size: 0.8rem; padding-left: 1rem;">${Array.isArray(c.weaknesses) ? c.weaknesses.map(w => `<li>${w}</li>`).join('') : `<li>${c.weaknesses || 'N/A'}</li>`}</ul>
                    </div>
                </div>
            </div>
            `).join('')}
        </div>

        ${v.key_risks && v.key_risks.length > 0 ? `
        <div class="section">
            <h2>Key Risks & Mitigations</h2>
            ${v.key_risks.map(r => `
            <div style="padding: 1rem; background: #f8fafc; border-radius: 8px; margin-bottom: 0.75rem; border-left: 4px solid ${r.severity === 'high' ? '#ef4444' : r.severity === 'medium' ? '#f59e0b' : '#10b981'};">
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                    <strong>${r.risk}</strong>
                    <span class="badge badge-${r.severity === 'high' ? 'red' : r.severity === 'medium' ? 'yellow' : 'green'}">${r.severity.toUpperCase()}</span>
                </div>
                <p style="font-size: 0.875rem; color: #64748b;"><strong>Mitigation:</strong> ${r.mitigation}</p>
            </div>
            `).join('')}
        </div>
        ` : ''}

        ${v.revenue_model ? `
        <div class="section">
            <h2>Revenue Model</h2>
            <div class="grid">
                <div class="card">
                    <div class="card-title">Suggested Models</div>
                    <div style="display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.5rem;">
                        ${v.revenue_model.suggested_models.map(m => `<span class="badge badge-blue">${m}</span>`).join('')}
                    </div>
                </div>
                <div class="card">
                    <div class="card-title">Price Range</div>
                    <div style="font-size: 0.875rem; margin-top: 0.5rem;">
                        <div>Low: <strong>${v.revenue_model.price_range.low}</strong></div>
                        <div>Mid: <strong>${v.revenue_model.price_range.mid}</strong></div>
                        <div>High: <strong>${v.revenue_model.price_range.high}</strong></div>
                    </div>
                </div>
                <div class="card" style="grid-column: 1 / -1;">
                    <div class="card-title">How Competitors Monetize</div>
                    <p style="font-size: 0.9rem; margin-top: 0.5rem;">${v.revenue_model.competitors_monetization}</p>
                </div>
            </div>
        </div>
        ` : ''}

        <div class="section">
            <h2>Differentiation Opportunities</h2>
            ${v.differentiation_opportunities.map(o => `
            <div style="padding: 0.75rem; border: 1px solid #e2e8f0; border-radius: 8px; margin-bottom: 0.5rem;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <strong>${o.opportunity}</strong>
                    <div style="display: flex; gap: 0.5rem;">
                        <span class="badge badge-${o.impact === 'high' ? 'green' : o.impact === 'medium' ? 'yellow' : 'blue'}">${o.impact} impact</span>
                        <span class="badge badge-blue">${o.difficulty} effort</span>
                    </div>
                </div>
            </div>
            `).join('')}
        </div>

        ${v.validation_experiments && v.validation_experiments.length > 0 ? `
        <div class="section">
            <h2>Validation Experiments</h2>
            ${v.validation_experiments.map(e => `
            <div style="padding: 1rem; background: #f8fafc; border-radius: 8px; margin-bottom: 0.75rem;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                    <strong>${e.experiment}</strong>
                    <span class="badge badge-${e.effort === 'low' ? 'green' : e.effort === 'medium' ? 'yellow' : 'red'}">${e.effort} effort</span>
                </div>
                <p style="font-size: 0.875rem; color: #64748b;"><strong>Proves:</strong> ${e.what_it_proves}</p>
            </div>
            `).join('')}
        </div>
        ` : ''}

        ${v.resource_estimate ? `
        <div class="section">
            <h2>Resource Estimate</h2>
            <div class="grid">
                <div class="card">
                    <div class="card-title">Budget Range</div>
                    <div class="card-value">${v.resource_estimate.budget_range.min} - ${v.resource_estimate.budget_range.max}</div>
                </div>
                <div class="card">
                    <div class="card-title">Timeline to MVP</div>
                    <div class="card-value">${v.resource_estimate.timeline_to_mvp}</div>
                </div>
                <div class="card">
                    <div class="card-title">Team Roles Needed</div>
                    <div style="display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.5rem;">
                        ${v.resource_estimate.team_roles.map(r => `<span class="badge badge-blue">${r}</span>`).join('')}
                    </div>
                </div>
                <div class="card">
                    <div class="card-title">Tech Stack</div>
                    <div style="display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.5rem;">
                        ${v.resource_estimate.tech_stack.map(t => `<span class="badge badge-green">${t}</span>`).join('')}
                    </div>
                </div>
            </div>
        </div>
        ` : ''}

        ${v.success_metrics && v.success_metrics.length > 0 ? `
        <div class="section">
            <h2>Success Metrics</h2>
            <table style="width: 100%; border-collapse: collapse;">
                <thead>
                    <tr style="background: #f8fafc;">
                        <th style="padding: 0.75rem; text-align: left; border-bottom: 2px solid #e2e8f0;">Metric</th>
                        <th style="padding: 0.75rem; text-align: left; border-bottom: 2px solid #e2e8f0;">Target</th>
                        <th style="padding: 0.75rem; text-align: left; border-bottom: 2px solid #e2e8f0;">Timeframe</th>
                    </tr>
                </thead>
                <tbody>
                    ${v.success_metrics.map(m => `
                    <tr>
                        <td style="padding: 0.75rem; border-bottom: 1px solid #e2e8f0;">${m.metric}</td>
                        <td style="padding: 0.75rem; border-bottom: 1px solid #e2e8f0; font-weight: 600;">${m.target}</td>
                        <td style="padding: 0.75rem; border-bottom: 1px solid #e2e8f0;">${m.timeframe}</td>
                    </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
        ` : ''}

        <div class="section">
            <h2>Next Steps</h2>
            ${v.next_steps.map((s, i) => `
            <div class="step">
                <div class="step-number">${i + 1}</div>
                <div class="step-content">
                    <div class="step-title">${s.step} <span class="badge badge-${s.priority === 'critical' ? 'red' : s.priority === 'high' ? 'yellow' : 'blue'}">${s.priority}</span></div>
                    <div class="step-desc">${s.why}</div>
                </div>
            </div>
            `).join('')}
        </div>

        ${v.pivot_suggestions && v.pivot_suggestions.length > 0 ? `
        <div class="section" style="border-left: 4px solid #f97316;">
            <h2>Pivot Suggestions</h2>
            <ul class="list">
                ${v.pivot_suggestions.map(p => `<li style="color: #f97316;">${p}</li>`).join('')}
            </ul>
        </div>
        ` : ''}

        <div class="footer">
            <p>Generated by Weaver Pro | ${new Date().toLocaleDateString()} ${new Date().toLocaleTimeString()}</p>
            <p style="margin-top: 0.5rem;">
                ${v.ai_powered ? `Powered by ${v.provider === 'claude' ? 'Claude AI' : v.provider === 'grok' ? 'Grok AI' : 'AI'}` : 'Simulated Analysis'}
            </p>
        </div>
    </div>
</body>
</html>
    `

    // Create and download the file
    const blob = new Blob([htmlContent], { type: 'text/html' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `idea-validation-report-${new Date().toISOString().split('T')[0]}.html`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
  }

  const handleRunResearch = async () => {
    if (!newResearch.query.trim()) return

    setIsRunning(true)

    const researchData = {
      query: newResearch.query,
      competitors: newResearch.competitors
        .split(',')
        .map((c) => c.trim())
        .filter(Boolean),
      industry: newResearch.industry,
    }

    try {
      const response = await fetch(`${BACKEND_URL}/api/market-research`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(researchData),
      })

      if (response.ok) {
        const result = await response.json()
        setResearches((prev) => [result, ...prev])
        setSelectedResearch(result)
      }
    } catch (error) {
      // Create mock result
      const mockResult: MarketResearch = {
        id: `research_${Date.now()}`,
        query: newResearch.query,
        competitors: researchData.competitors,
        industry: newResearch.industry || 'Technology',
        status: 'completed',
        insights: [
          {
            type: 'trend',
            title: 'Market Growth',
            description: `The ${newResearch.industry || 'target'} market shows steady growth potential.`,
            confidence: 0.75,
          },
          {
            type: 'opportunity',
            title: 'Feature Gap',
            description: 'Analysis suggests opportunity in underserved user segments.',
            confidence: 0.68,
          },
          {
            type: 'risk',
            title: 'Competition',
            description: `Identified ${researchData.competitors.length} direct competitors.`,
            confidence: 0.82,
          },
        ],
        recommendations: [
          'Focus on differentiation through superior UX',
          'Consider freemium model for market penetration',
          'Target underserved mid-market segment',
        ],
        created_at: new Date().toISOString(),
      }
      setResearches((prev) => [mockResult, ...prev])
      setSelectedResearch(mockResult)
    } finally {
      setIsRunning(false)
      setNewResearch({ query: '', competitors: '', industry: '' })
      setIsCreateOpen(false)
    }
  }

  if (isLoading) {
    return (
      <div className="flex h-[50vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  // Render the Idea Validation result view
  const renderIdeaValidationResult = () => {
    if (!selectedValidation) {
      return (
        <Card className="flex h-[500px] items-center justify-center border-dashed">
          <CardContent className="text-center">
            <Rocket className="mx-auto h-12 w-12 text-muted-foreground/50" />
            <h3 className="mt-4 text-lg font-semibold">Validate Your Idea</h3>
            <p className="text-sm text-muted-foreground">
              Describe your idea and we&apos;ll analyze its viability
            </p>
          </CardContent>
        </Card>
      )
    }

    const v = selectedValidation
    const VerdictIcon = verdictStyles[v.go_no_go]?.icon || AlertCircle

    return (
      <div className="space-y-6">
        {/* Verdict Banner */}
        <Card className={`${verdictStyles[v.go_no_go]?.bg} ${verdictStyles[v.go_no_go]?.border} border-2`}>
          <CardContent className="pt-6">
            <div className="flex items-start gap-4">
              <div className={`rounded-full p-3 ${verdictStyles[v.go_no_go]?.bg}`}>
                <VerdictIcon className={`h-8 w-8 ${verdictStyles[v.go_no_go]?.text}`} />
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-3 flex-wrap">
                  <Badge variant="outline" className={`text-lg px-4 py-1 ${verdictStyles[v.go_no_go]?.text} ${verdictStyles[v.go_no_go]?.border}`}>
                    {v.go_no_go}
                  </Badge>
                  <span className="text-2xl font-bold">{v.viability_score}/100</span>
                  {v.ai_powered && v.provider && (
                    <Badge variant="secondary" className="ml-auto text-xs">
                      {v.provider === 'claude' ? 'Claude AI' : v.provider === 'grok' ? 'Grok AI' : 'AI'}
                    </Badge>
                  )}
                  {!v.ai_powered && (
                    <Badge variant="outline" className="ml-auto text-xs text-muted-foreground">
                      Simulated
                    </Badge>
                  )}
                </div>
                <p className="mt-2 text-lg">{v.verdict}</p>
                <ul className="mt-2 space-y-1 text-sm text-muted-foreground">
                  {v.verdict_reasons.map((reason, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <ArrowRight className="h-4 w-4 mt-0.5 shrink-0" />
                      {reason}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Export Button */}
        <div className="flex justify-end">
          <Button
            variant="outline"
            onClick={() => handleExportReport()}
            className="gap-2"
          >
            <Download className="h-4 w-4" />
            Export Report
          </Button>
        </div>

        {/* Tabs for detailed analysis */}
        <Tabs defaultValue="overview">
          <TabsList className="grid w-full grid-cols-7">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="customer">Customer</TabsTrigger>
            <TabsTrigger value="competitors">Competitors</TabsTrigger>
            <TabsTrigger value="market">Market</TabsTrigger>
            <TabsTrigger value="strategy">Strategy</TabsTrigger>
            <TabsTrigger value="plan">Action Plan</TabsTrigger>
            <TabsTrigger value="revenue">Revenue</TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="mt-4 space-y-4">
            {/* Executive Summary */}
            {v.executive_summary && (
              <Card className="bg-gradient-to-r from-indigo-50 to-purple-50 dark:from-indigo-950/30 dark:to-purple-950/30 border-indigo-200 dark:border-indigo-800">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <FileText className="h-5 w-5 text-indigo-600" />
                    Executive Summary
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-base leading-relaxed">{v.executive_summary}</p>
                </CardContent>
              </Card>
            )}

            <div className="grid gap-4 md:grid-cols-2">
              {/* Your Idea */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <Lightbulb className="h-4 w-4" />
                    Your Idea
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm">{v.idea}</p>
                </CardContent>
              </Card>

              {/* Discovered Industry */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <Globe className="h-4 w-4" />
                    Industry Detected
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="font-medium capitalize">{v.discovered_industry}</p>
                  <p className="text-xs text-muted-foreground">{v.industry_category}</p>
                </CardContent>
              </Card>
            </div>

            {/* Problem Validation */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Target className="h-5 w-5" />
                  Problem Validation
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center gap-4">
                  <Badge variant="outline" className={
                    v.problem_severity === 'hair-on-fire' ? 'bg-red-500/20 text-red-500' :
                    v.problem_severity === 'significant' ? 'bg-yellow-500/20 text-yellow-500' :
                    'bg-slate-500/20 text-slate-500'
                  }>
                    {v.problem_severity.replace('-', ' ').toUpperCase()}
                  </Badge>
                  <span className="text-sm text-muted-foreground">
                    Search Volume: <strong className="text-foreground">{v.search_volume}</strong>
                  </span>
                </div>
                <div>
                  <p className="text-sm font-medium mb-2">Evidence:</p>
                  <ul className="space-y-1">
                    {v.problem_evidence.map((evidence, i) => (
                      <li key={i} className="text-sm text-muted-foreground flex items-start gap-2">
                        <CheckCircle2 className="h-4 w-4 mt-0.5 text-green-500 shrink-0" />
                        {evidence}
                      </li>
                    ))}
                  </ul>
                </div>
              </CardContent>
            </Card>

            {/* Viability Breakdown */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Trophy className="h-5 w-5" />
                  Viability Breakdown
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {Object.entries(v.viability_breakdown).map(([key, value]) => (
                  <div key={key}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="capitalize">{key.replace(/_/g, ' ')}</span>
                      <span className="font-medium">{value}/100</span>
                    </div>
                    <Progress value={value} className="h-2" />
                  </div>
                ))}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Customer Tab */}
          <TabsContent value="customer" className="mt-4 space-y-4">
            {v.target_customer ? (
              <>
                <Card className="bg-gradient-to-r from-blue-50 to-cyan-50 dark:from-blue-950/30 dark:to-cyan-950/30 border-blue-200 dark:border-blue-800">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <UserCircle className="h-5 w-5 text-blue-600" />
                      Target Customer Profile
                    </CardTitle>
                    <CardDescription>
                      Understanding who you&apos;re building for
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid gap-4 md:grid-cols-2">
                      <div className="p-4 bg-white/50 dark:bg-slate-900/50 rounded-lg">
                        <h4 className="text-sm font-medium text-blue-600 mb-2 flex items-center gap-2">
                          <Users className="h-4 w-4" />
                          Demographics
                        </h4>
                        <p className="text-sm">{v.target_customer.demographics}</p>
                      </div>
                      <div className="p-4 bg-white/50 dark:bg-slate-900/50 rounded-lg">
                        <h4 className="text-sm font-medium text-purple-600 mb-2 flex items-center gap-2">
                          <Sparkles className="h-4 w-4" />
                          Psychographics
                        </h4>
                        <p className="text-sm">{v.target_customer.psychographics}</p>
                      </div>
                    </div>
                    <div className="p-4 bg-white/50 dark:bg-slate-900/50 rounded-lg">
                      <h4 className="text-sm font-medium text-green-600 mb-2 flex items-center gap-2">
                        <Clock className="h-4 w-4" />
                        A Day in Their Life
                      </h4>
                      <p className="text-sm">{v.target_customer.day_in_life}</p>
                    </div>
                  </CardContent>
                </Card>

                {/* Problem they face */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Target className="h-5 w-5" />
                      Their Problem
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="flex items-center gap-4">
                      <Badge variant="outline" className={
                        v.problem_severity === 'hair-on-fire' ? 'bg-red-500/20 text-red-500' :
                        v.problem_severity === 'significant' ? 'bg-yellow-500/20 text-yellow-500' :
                        'bg-slate-500/20 text-slate-500'
                      }>
                        {v.problem_severity.replace('-', ' ').toUpperCase()}
                      </Badge>
                      <span className="text-sm text-muted-foreground">
                        Search Volume: <strong className="text-foreground">{v.search_volume}</strong>
                      </span>
                    </div>
                    <div>
                      <p className="text-sm font-medium mb-2">Evidence of the problem:</p>
                      <ul className="space-y-1">
                        {v.problem_evidence.map((evidence, i) => (
                          <li key={i} className="text-sm text-muted-foreground flex items-start gap-2">
                            <CheckCircle2 className="h-4 w-4 mt-0.5 text-green-500 shrink-0" />
                            {evidence}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </CardContent>
                </Card>
              </>
            ) : (
              <Card className="flex h-[300px] items-center justify-center border-dashed">
                <CardContent className="text-center">
                  <Users className="mx-auto h-12 w-12 text-muted-foreground/50" />
                  <h3 className="mt-4 text-lg font-semibold">No Customer Profile Available</h3>
                  <p className="text-sm text-muted-foreground">
                    AI-powered analysis will provide target customer insights
                  </p>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* Competitors Tab */}
          <TabsContent value="competitors" className="mt-4 space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Building2 className="h-5 w-5" />
                  Discovered Competitors ({v.discovered_competitors.length})
                </CardTitle>
                <CardDescription>
                  We found these existing solutions in your space
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {v.discovered_competitors.map((comp, i) => (
                  <div key={i} className="border rounded-lg p-4">
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="flex items-center gap-2">
                          <h4 className="font-medium">{comp.name}</h4>
                          {comp.funding_stage && (
                            <Badge variant="outline" className="text-xs">
                              {comp.funding_stage}
                            </Badge>
                          )}
                        </div>
                        <p className="text-sm text-muted-foreground mt-1">{comp.description}</p>
                        {comp.website && (
                          <a href={`https://${comp.website}`} target="_blank" rel="noopener noreferrer"
                             className="text-xs text-blue-500 hover:underline flex items-center gap-1 mt-1">
                            {comp.website} <ExternalLink className="h-3 w-3" />
                          </a>
                        )}
                      </div>
                      <div className="text-right">
                        <div className="text-sm text-muted-foreground">Similarity</div>
                        <div className="text-lg font-bold">{Math.round(comp.similarity_score * 100)}%</div>
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-4 mt-3">
                      <div>
                        <p className="text-xs font-medium text-green-500 mb-1">Strengths</p>
                        <ul className="text-xs space-y-0.5">
                          {Array.isArray(comp.strengths) ? comp.strengths.map((s, j) => (
                            <li key={j} className="text-muted-foreground">• {s}</li>
                          )) : <li className="text-muted-foreground">• {comp.strengths || 'N/A'}</li>}
                        </ul>
                      </div>
                      <div>
                        <p className="text-xs font-medium text-red-500 mb-1">Weaknesses</p>
                        <ul className="text-xs space-y-0.5">
                          {Array.isArray(comp.weaknesses) ? comp.weaknesses.map((w, j) => (
                            <li key={j} className="text-muted-foreground">• {w}</li>
                          )) : <li className="text-muted-foreground">• {comp.weaknesses || 'N/A'}</li>}
                        </ul>
                      </div>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Strategy Tab */}
          <TabsContent value="strategy" className="mt-4 space-y-4">
            {/* Key Risks */}
            {v.key_risks && v.key_risks.length > 0 && (
              <Card className="border-red-200 dark:border-red-800">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Shield className="h-5 w-5 text-red-500" />
                    Key Risks & Mitigations
                  </CardTitle>
                  <CardDescription>
                    Top challenges and how to address them
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  {v.key_risks.map((risk, i) => (
                    <div key={i} className={`border-l-4 rounded-lg p-4 ${
                      risk.severity === 'high' ? 'border-l-red-500 bg-red-50 dark:bg-red-950/20' :
                      risk.severity === 'medium' ? 'border-l-yellow-500 bg-yellow-50 dark:bg-yellow-950/20' :
                      'border-l-green-500 bg-green-50 dark:bg-green-950/20'
                    }`}>
                      <div className="flex items-start justify-between mb-2">
                        <p className="font-medium">{risk.risk}</p>
                        <Badge variant="outline" className={
                          risk.severity === 'high' ? 'bg-red-500/20 text-red-500' :
                          risk.severity === 'medium' ? 'bg-yellow-500/20 text-yellow-500' :
                          'bg-green-500/20 text-green-500'
                        }>
                          {risk.severity.toUpperCase()}
                        </Badge>
                      </div>
                      <p className="text-sm text-muted-foreground">
                        <strong className="text-foreground">Mitigation:</strong> {risk.mitigation}
                      </p>
                    </div>
                  ))}
                </CardContent>
              </Card>
            )}

            {/* Differentiation Opportunities */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Sparkles className="h-5 w-5" />
                  Differentiation Opportunities
                </CardTitle>
                <CardDescription>
                  Ways to stand out from existing competitors
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {v.differentiation_opportunities.map((opp, i) => (
                  <div key={i} className="border rounded-lg p-3">
                    <div className="flex items-start justify-between">
                      <p className="font-medium">{opp.opportunity}</p>
                      <div className="flex gap-2">
                        <Badge variant="outline" className={
                          opp.impact === 'high' ? 'bg-green-500/20 text-green-500' :
                          opp.impact === 'medium' ? 'bg-yellow-500/20 text-yellow-500' :
                          'bg-slate-500/20 text-slate-500'
                        }>
                          {opp.impact} impact
                        </Badge>
                        <Badge variant="outline">
                          {opp.difficulty} effort
                        </Badge>
                      </div>
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">
                      Addresses weakness in {opp.competitors_affected} competitor(s)
                    </p>
                  </div>
                ))}
              </CardContent>
            </Card>

            {/* Unique Angles */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Zap className="h-5 w-5" />
                  Unique Angles to Explore
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {v.unique_angles.map((angle, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm">
                      <Lightbulb className="h-4 w-4 mt-0.5 text-yellow-500 shrink-0" />
                      {angle}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>

            {/* Pivot Suggestions */}
            {v.pivot_suggestions && v.pivot_suggestions.length > 0 && (
              <Card className="border-orange-500/50">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-orange-500">
                    <AlertTriangle className="h-5 w-5" />
                    Pivot Suggestions
                  </CardTitle>
                  <CardDescription>
                    Consider these alternative directions
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2">
                    {v.pivot_suggestions.map((suggestion, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm">
                        <ArrowRight className="h-4 w-4 mt-0.5 text-orange-500 shrink-0" />
                        {suggestion}
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* Market Tab */}
          <TabsContent value="market" className="mt-4 space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <TrendingUp className="h-5 w-5" />
                    Market Timing
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <Badge variant="outline" className={
                    v.market_timing === 'excellent' || v.market_timing === 'good' ? 'bg-green-500/20 text-green-500' :
                    'bg-yellow-500/20 text-yellow-500'
                  }>
                    {v.market_timing.toUpperCase()}
                  </Badge>
                  <ul className="mt-3 space-y-1">
                    {v.market_timing_reasons.map((reason, i) => (
                      <li key={i} className="text-sm text-muted-foreground flex items-start gap-2">
                        <CheckCircle2 className="h-4 w-4 mt-0.5 text-green-500 shrink-0" />
                        {reason}
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <DollarSign className="h-5 w-5" />
                    Market Size
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold">{v.estimated_tam}</div>
                  <p className="text-sm text-muted-foreground">Total Addressable Market</p>
                  <div className="mt-3">
                    <p className="text-sm">
                      Saturation: <Badge variant="outline" className={
                        v.market_saturation === 'blue-ocean' ? 'bg-blue-500/20 text-blue-500' :
                        v.market_saturation === 'growing' ? 'bg-green-500/20 text-green-500' :
                        v.market_saturation === 'crowded' ? 'bg-yellow-500/20 text-yellow-500' :
                        'bg-red-500/20 text-red-500'
                      }>
                        {v.market_saturation.replace('-', ' ').toUpperCase()}
                      </Badge>
                    </p>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Market Trends */}
            {v.market_trends && v.market_trends.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <BarChart3 className="h-5 w-5" />
                    Market Trends
                  </CardTitle>
                  <CardDescription>
                    Key trends affecting your market
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2">
                    {v.market_trends.map((trend, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm">
                        <TrendingUp className="h-4 w-4 mt-0.5 text-blue-500 shrink-0" />
                        {trend}
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* Action Plan Tab */}
          <TabsContent value="plan" className="mt-4 space-y-4">
            {/* Next Steps */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Target className="h-5 w-5" />
                  Your Action Plan
                </CardTitle>
                <CardDescription>
                  Prioritized steps to validate and launch your idea
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {v.next_steps.map((step, i) => (
                  <div key={i} className="flex items-start gap-4 p-4 border rounded-lg">
                    <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-sm font-bold ${
                      step.priority === 'critical' ? 'bg-red-500 text-white' :
                      step.priority === 'high' ? 'bg-orange-500 text-white' :
                      step.priority === 'medium' ? 'bg-yellow-500 text-white' :
                      'bg-slate-500 text-white'
                    }`}>
                      {i + 1}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <p className="font-medium">{step.step}</p>
                        <Badge variant="outline" className={priorityColors[step.priority]}>
                          {step.priority}
                        </Badge>
                      </div>
                      <p className="text-sm text-muted-foreground mt-1">{step.why}</p>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>

            {/* Validation Experiments */}
            {v.validation_experiments && v.validation_experiments.length > 0 && (
              <Card className="border-purple-200 dark:border-purple-800">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Beaker className="h-5 w-5 text-purple-500" />
                    Validation Experiments
                  </CardTitle>
                  <CardDescription>
                    Pre-build tests to validate your idea before investing heavily
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  {v.validation_experiments.map((exp, i) => (
                    <div key={i} className="border rounded-lg p-4 bg-purple-50/50 dark:bg-purple-950/20">
                      <div className="flex items-start justify-between mb-2">
                        <p className="font-medium">{exp.experiment}</p>
                        <Badge variant="outline" className={
                          exp.effort === 'low' ? 'bg-green-500/20 text-green-500' :
                          exp.effort === 'medium' ? 'bg-yellow-500/20 text-yellow-500' :
                          'bg-red-500/20 text-red-500'
                        }>
                          {exp.effort} effort
                        </Badge>
                      </div>
                      <p className="text-sm text-muted-foreground">
                        <strong className="text-foreground">What it proves:</strong> {exp.what_it_proves}
                      </p>
                    </div>
                  ))}
                </CardContent>
              </Card>
            )}

            {/* Resource Estimate */}
            {v.resource_estimate && (
              <Card className="border-green-200 dark:border-green-800">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Wallet className="h-5 w-5 text-green-500" />
                    Resource Estimate
                  </CardTitle>
                  <CardDescription>
                    What you&apos;ll need to build this
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="p-4 bg-green-50/50 dark:bg-green-950/20 rounded-lg">
                      <p className="text-sm text-muted-foreground mb-1">Budget Range</p>
                      <p className="text-xl font-bold">{v.resource_estimate.budget_range.min} - {v.resource_estimate.budget_range.max}</p>
                    </div>
                    <div className="p-4 bg-green-50/50 dark:bg-green-950/20 rounded-lg">
                      <p className="text-sm text-muted-foreground mb-1">Timeline to MVP</p>
                      <p className="text-xl font-bold">{v.resource_estimate.timeline_to_mvp}</p>
                    </div>
                    <div className="p-4 bg-green-50/50 dark:bg-green-950/20 rounded-lg">
                      <p className="text-sm text-muted-foreground mb-2">Team Roles Needed</p>
                      <div className="flex flex-wrap gap-2">
                        {v.resource_estimate.team_roles.map((role, i) => (
                          <Badge key={i} variant="secondary">{role}</Badge>
                        ))}
                      </div>
                    </div>
                    <div className="p-4 bg-green-50/50 dark:bg-green-950/20 rounded-lg">
                      <p className="text-sm text-muted-foreground mb-2">Suggested Tech Stack</p>
                      <div className="flex flex-wrap gap-2">
                        {v.resource_estimate.tech_stack.map((tech, i) => (
                          <Badge key={i} variant="outline" className="bg-blue-500/20 text-blue-600">{tech}</Badge>
                        ))}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Success Metrics */}
            {v.success_metrics && v.success_metrics.length > 0 && (
              <Card className="border-blue-200 dark:border-blue-800">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <BarChart3 className="h-5 w-5 text-blue-500" />
                    Success Metrics
                  </CardTitle>
                  <CardDescription>
                    Key performance indicators to track
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b">
                          <th className="text-left py-2 px-4 font-medium">Metric</th>
                          <th className="text-left py-2 px-4 font-medium">Target</th>
                          <th className="text-left py-2 px-4 font-medium">Timeframe</th>
                        </tr>
                      </thead>
                      <tbody>
                        {v.success_metrics.map((metric, i) => (
                          <tr key={i} className="border-b last:border-0">
                            <td className="py-3 px-4">{metric.metric}</td>
                            <td className="py-3 px-4 font-semibold text-green-600">{metric.target}</td>
                            <td className="py-3 px-4 text-muted-foreground">{metric.timeframe}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* Revenue Tab */}
          <TabsContent value="revenue" className="mt-4 space-y-4">
            {v.revenue_model ? (
              <>
                <Card className="bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-950/30 dark:to-emerald-950/30 border-green-200 dark:border-green-800">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <DollarSign className="h-5 w-5 text-green-600" />
                      Revenue Model
                    </CardTitle>
                    <CardDescription>
                      How to monetize your idea
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div>
                      <p className="text-sm font-medium mb-2">Suggested Monetization Models</p>
                      <div className="flex flex-wrap gap-2">
                        {v.revenue_model.suggested_models.map((model, i) => (
                          <Badge key={i} className="bg-green-500/20 text-green-700 dark:text-green-400 border-green-500/50">
                            {model}
                          </Badge>
                        ))}
                      </div>
                    </div>

                    <div className="grid gap-4 md:grid-cols-3">
                      <div className="p-4 bg-white/50 dark:bg-slate-900/50 rounded-lg text-center">
                        <p className="text-xs text-muted-foreground mb-1">Low Tier</p>
                        <p className="text-xl font-bold text-slate-600">{v.revenue_model.price_range.low}</p>
                      </div>
                      <div className="p-4 bg-white/50 dark:bg-slate-900/50 rounded-lg text-center border-2 border-green-500">
                        <p className="text-xs text-muted-foreground mb-1">Recommended</p>
                        <p className="text-xl font-bold text-green-600">{v.revenue_model.price_range.mid}</p>
                      </div>
                      <div className="p-4 bg-white/50 dark:bg-slate-900/50 rounded-lg text-center">
                        <p className="text-xs text-muted-foreground mb-1">Premium</p>
                        <p className="text-xl font-bold text-slate-600">{v.revenue_model.price_range.high}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Building2 className="h-5 w-5" />
                      How Competitors Monetize
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm">{v.revenue_model.competitors_monetization}</p>
                  </CardContent>
                </Card>
              </>
            ) : (
              <Card className="flex h-[300px] items-center justify-center border-dashed">
                <CardContent className="text-center">
                  <DollarSign className="mx-auto h-12 w-12 text-muted-foreground/50" />
                  <h3 className="mt-4 text-lg font-semibold">No Revenue Model Available</h3>
                  <p className="text-sm text-muted-foreground">
                    AI-powered analysis will suggest monetization strategies
                  </p>
                </CardContent>
              </Card>
            )}
          </TabsContent>
        </Tabs>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      {/* Header with Mode Toggle */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            {mode === 'beginner' ? 'Idea Validation' : 'Market Research'}
          </h1>
          <p className="text-muted-foreground">
            {mode === 'beginner'
              ? 'Validate your business idea - just describe it and we\'ll do the research'
              : 'AI-powered competitive analysis and market insights'}
          </p>
        </div>

        <div className="flex items-center gap-4">
          {/* Mode Toggle */}
          <div className="flex items-center rounded-lg border bg-muted p-1">
            <button
              onClick={() => setMode('beginner')}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                mode === 'beginner' ? 'bg-background shadow-sm' : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              <Rocket className="h-4 w-4 inline mr-1" />
              I have an idea
            </button>
            <button
              onClick={() => setMode('expert')}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                mode === 'expert' ? 'bg-background shadow-sm' : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              <LineChart className="h-4 w-4 inline mr-1" />
              Expert Mode
            </button>
          </div>

          {/* New Research/Validation Button */}
          <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
            <DialogTrigger asChild>
              <Button variant="gradient">
                <Plus className="mr-2 h-4 w-4" />
                {mode === 'beginner' ? 'Validate Idea' : 'New Research'}
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-lg">
              {mode === 'beginner' ? (
                <>
                  <DialogHeader>
                    <DialogTitle className="flex items-center gap-2">
                      <Rocket className="h-5 w-5" />
                      Validate Your Business Idea
                    </DialogTitle>
                    <DialogDescription>
                      Just describe your idea - we&apos;ll discover competitors, analyze viability, and tell you if it&apos;s worth pursuing.
                    </DialogDescription>
                  </DialogHeader>

                  <div className="space-y-4 py-4">
                    <div className="space-y-2">
                      <Label htmlFor="idea" className="flex items-center gap-1">
                        Your Idea <span className="text-red-500">*</span>
                      </Label>
                      <Textarea
                        id="idea"
                        placeholder="Example: An app that helps busy parents plan healthy meals for their kids with automatic grocery lists and budget tracking"
                        value={newIdea.idea}
                        onChange={(e) => setNewIdea((prev) => ({ ...prev, idea: e.target.value }))}
                        rows={4}
                        className="resize-none"
                      />
                      <p className="text-xs text-muted-foreground">
                        Don&apos;t worry about being perfect - just describe what you want to build
                      </p>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="problem" className="text-muted-foreground">
                        What problem does it solve? (optional)
                      </Label>
                      <Input
                        id="problem"
                        placeholder="Example: Parents waste time and money on unhealthy takeout"
                        value={newIdea.problem}
                        onChange={(e) => setNewIdea((prev) => ({ ...prev, problem: e.target.value }))}
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="target" className="text-muted-foreground">
                        Who is it for? (optional)
                      </Label>
                      <Input
                        id="target"
                        placeholder="Example: Working parents with kids under 12"
                        value={newIdea.target_users}
                        onChange={(e) => setNewIdea((prev) => ({ ...prev, target_users: e.target.value }))}
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="provider" className="text-muted-foreground">
                        AI Provider (optional)
                      </Label>
                      <Select
                        value={newIdea.provider}
                        onValueChange={(value) => setNewIdea((prev) => ({ ...prev, provider: value as 'auto' | 'claude' | 'grok' }))}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Auto-detect (recommended)" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="auto">Auto-detect (recommended)</SelectItem>
                          <SelectItem value="claude">Claude - Deep analysis & reasoning</SelectItem>
                          <SelectItem value="grok">Grok - Real-time trends & data</SelectItem>
                        </SelectContent>
                      </Select>
                      <p className="text-xs text-muted-foreground">
                        Claude excels at competitive analysis. Grok is better for current market trends.
                      </p>
                    </div>
                  </div>

                  {validationError && (
                    <div className="rounded-md bg-red-50 dark:bg-red-900/20 p-4 border border-red-200 dark:border-red-800">
                      <div className="flex items-start gap-3">
                        <XCircle className="h-5 w-5 text-red-500 shrink-0 mt-0.5" />
                        <div>
                          <p className="text-sm font-medium text-red-800 dark:text-red-200">Validation Failed</p>
                          <p className="text-sm text-red-700 dark:text-red-300 mt-1">{validationError}</p>
                        </div>
                      </div>
                    </div>
                  )}

                  <DialogFooter>
                    <Button variant="outline" onClick={() => { setIsCreateOpen(false); setValidationError(null); }}>
                      Cancel
                    </Button>
                    <Button
                      variant="gradient"
                      onClick={handleValidateIdea}
                      disabled={!newIdea.idea.trim() || isRunning}
                    >
                      {isRunning ? (
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      ) : (
                        <Sparkles className="mr-2 h-4 w-4" />
                      )}
                      {isRunning ? 'Analyzing...' : 'Validate Idea'}
                    </Button>
                  </DialogFooter>
                </>
              ) : (
                <>
                  <DialogHeader>
                    <DialogTitle>Start Market Research</DialogTitle>
                    <DialogDescription>
                      Analyze your market, competitors, and find opportunities
                    </DialogDescription>
                  </DialogHeader>

                  <div className="space-y-4 py-4">
                    <div className="space-y-2">
                      <Label htmlFor="query">Research Query</Label>
                      <Textarea
                        id="query"
                        placeholder="Describe your product or market segment..."
                        value={newResearch.query}
                        onChange={(e) =>
                          setNewResearch((r) => ({ ...r, query: e.target.value }))
                        }
                        rows={3}
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="competitors">Competitors (comma-separated)</Label>
                      <Input
                        id="competitors"
                        placeholder="Company A, Company B, Company C"
                        value={newResearch.competitors}
                        onChange={(e) =>
                          setNewResearch((r) => ({ ...r, competitors: e.target.value }))
                        }
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="industry">Industry</Label>
                      <Input
                        id="industry"
                        placeholder="e.g., SaaS, E-commerce, FinTech"
                        value={newResearch.industry}
                        onChange={(e) =>
                          setNewResearch((r) => ({ ...r, industry: e.target.value }))
                        }
                      />
                    </div>
                  </div>

                  <DialogFooter>
                    <Button variant="outline" onClick={() => setIsCreateOpen(false)}>
                      Cancel
                    </Button>
                    <Button
                      variant="gradient"
                      onClick={handleRunResearch}
                      disabled={!newResearch.query.trim() || isRunning}
                    >
                      {isRunning ? (
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      ) : (
                        <Search className="mr-2 h-4 w-4" />
                      )}
                      {isRunning ? 'Analyzing...' : 'Run Analysis'}
                    </Button>
                  </DialogFooter>
                </>
              )}
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Main Content - Beginner Mode (Idea Validation) */}
      {mode === 'beginner' && (
        <div className="grid gap-6 lg:grid-cols-3">
          {/* Idea Validation List */}
          <div className="space-y-4">
            <h2 className="text-lg font-semibold">Your Ideas</h2>
            {ideaValidations.length === 0 ? (
              <Card className="border-dashed">
                <CardContent className="flex flex-col items-center justify-center py-8">
                  <Rocket className="h-10 w-10 text-muted-foreground/50" />
                  <p className="mt-2 text-sm text-muted-foreground">
                    No ideas validated yet
                  </p>
                  <Button
                    variant="outline"
                    size="sm"
                    className="mt-3"
                    onClick={() => setIsCreateOpen(true)}
                  >
                    <Plus className="mr-2 h-4 w-4" />
                    Validate your first idea
                  </Button>
                </CardContent>
              </Card>
            ) : (
              ideaValidations.map((validation) => {
                const VerdictIcon = verdictStyles[validation.go_no_go]?.icon || AlertCircle
                return (
                  <Card
                    key={validation.id}
                    className={`cursor-pointer transition-colors hover:bg-muted/50 ${
                      selectedValidation?.id === validation.id ? 'border-primary' : ''
                    }`}
                    onClick={() => setSelectedValidation(validation)}
                  >
                    <CardHeader className="pb-2">
                      <div className="flex items-center justify-between">
                        <Badge
                          variant="outline"
                          className={`${verdictStyles[validation.go_no_go]?.text} ${verdictStyles[validation.go_no_go]?.border}`}
                        >
                          <VerdictIcon className="mr-1 h-3 w-3" />
                          {validation.go_no_go}
                        </Badge>
                        <span className="text-sm font-bold">{validation.viability_score}/100</span>
                      </div>
                      <CardTitle className="line-clamp-2 text-sm mt-2">
                        {validation.idea}
                      </CardTitle>
                      <CardDescription className="text-xs capitalize">
                        {validation.discovered_industry} · {new Date(validation.timestamp).toLocaleDateString()}
                      </CardDescription>
                    </CardHeader>
                  </Card>
                )
              })
            )}
          </div>

          {/* Idea Validation Results */}
          <div className="lg:col-span-2">
            {renderIdeaValidationResult()}
          </div>
        </div>
      )}

      {/* Main Content - Expert Mode (Market Research) */}
      {mode === 'expert' && (
        <div className="grid gap-6 lg:grid-cols-3">
        {/* Research List */}
        <div className="space-y-4">
          <h2 className="text-lg font-semibold">Research History</h2>
          {researches.length === 0 ? (
            <Card className="border-dashed">
              <CardContent className="flex flex-col items-center justify-center py-8">
                <LineChart className="h-10 w-10 text-muted-foreground/50" />
                <p className="mt-2 text-sm text-muted-foreground">
                  No research yet
                </p>
              </CardContent>
            </Card>
          ) : (
            researches.map((research) => (
              <Card
                key={research.id}
                className={`cursor-pointer transition-colors hover:bg-muted/50 ${
                  selectedResearch?.id === research.id ? 'border-primary' : ''
                }`}
                onClick={() => setSelectedResearch(research)}
              >
                <CardHeader className="pb-2">
                  <CardTitle className="line-clamp-1 text-sm">
                    {research.query}
                  </CardTitle>
                  <CardDescription className="text-xs">
                    {research.industry} - {new Date(research.created_at).toLocaleDateString()}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-1">
                    {research.insights.slice(0, 3).map((insight, i) => {
                      const Icon = insightIcons[insight.type]
                      return (
                        <Badge
                          key={i}
                          variant="outline"
                          className={`text-xs ${insightColors[insight.type]}`}
                        >
                          <Icon className="mr-1 h-3 w-3" />
                          {insight.type}
                        </Badge>
                      )
                    })}
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </div>

        {/* Research Details */}
        <div className="lg:col-span-2">
          {selectedResearch ? (
            <Tabs defaultValue="insights">
              <TabsList>
                <TabsTrigger value="insights">Insights</TabsTrigger>
                <TabsTrigger value="recommendations">Recommendations</TabsTrigger>
                <TabsTrigger value="market">Market Size</TabsTrigger>
              </TabsList>

              <TabsContent value="insights" className="mt-4 space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle>{selectedResearch.query}</CardTitle>
                    <CardDescription>
                      Industry: {selectedResearch.industry} |
                      Competitors: {selectedResearch.competitors.join(', ') || 'None specified'}
                    </CardDescription>
                  </CardHeader>
                </Card>

                <div className="grid gap-4 md:grid-cols-2">
                  {selectedResearch.insights.map((insight, index) => {
                    const Icon = insightIcons[insight.type]
                    return (
                      <Card key={index} className={`border ${insightColors[insight.type]}`}>
                        <CardHeader className="pb-2">
                          <div className="flex items-center gap-2">
                            <Icon className="h-5 w-5" />
                            <CardTitle className="text-base">{insight.title}</CardTitle>
                          </div>
                        </CardHeader>
                        <CardContent>
                          <p className="text-sm text-muted-foreground">
                            {insight.description}
                          </p>
                          <div className="mt-3 flex items-center justify-between">
                            <span className="text-xs text-muted-foreground">
                              Confidence
                            </span>
                            <span className="text-sm font-medium">
                              {(insight.confidence * 100).toFixed(0)}%
                            </span>
                          </div>
                          <Progress
                            value={insight.confidence * 100}
                            className="mt-1 h-1"
                          />
                        </CardContent>
                      </Card>
                    )
                  })}
                </div>
              </TabsContent>

              <TabsContent value="recommendations" className="mt-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Target className="h-5 w-5" />
                      Strategic Recommendations
                    </CardTitle>
                    <CardDescription>
                      Action items based on market analysis
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <ul className="space-y-3">
                      {selectedResearch.recommendations.map((rec, i) => (
                        <li key={i} className="flex items-start gap-3">
                          <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-medium text-primary">
                            {i + 1}
                          </span>
                          <span>{rec}</span>
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="market" className="mt-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <DollarSign className="h-5 w-5" />
                      Market Size Analysis
                    </CardTitle>
                    <CardDescription>
                      TAM, SAM, and SOM breakdown
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    {selectedResearch.market_size ? (
                      <div className="space-y-6">
                        <div>
                          <div className="flex items-center justify-between">
                            <div>
                              <p className="font-medium">Total Addressable Market (TAM)</p>
                              <p className="text-sm text-muted-foreground">
                                Total market demand for a product
                              </p>
                            </div>
                            <span className="text-2xl font-bold">
                              {selectedResearch.market_size.total}
                            </span>
                          </div>
                          <Progress value={100} className="mt-2" />
                        </div>

                        <div>
                          <div className="flex items-center justify-between">
                            <div>
                              <p className="font-medium">Serviceable Addressable Market (SAM)</p>
                              <p className="text-sm text-muted-foreground">
                                Market segment you can target
                              </p>
                            </div>
                            <span className="text-2xl font-bold">
                              {selectedResearch.market_size.addressable}
                            </span>
                          </div>
                          <Progress value={32} className="mt-2" />
                        </div>

                        <div>
                          <div className="flex items-center justify-between">
                            <div>
                              <p className="font-medium">Serviceable Obtainable Market (SOM)</p>
                              <p className="text-sm text-muted-foreground">
                                Realistic market share to capture
                              </p>
                            </div>
                            <span className="text-2xl font-bold">
                              {selectedResearch.market_size.serviceable}
                            </span>
                          </div>
                          <Progress value={6} className="mt-2" />
                        </div>
                      </div>
                    ) : (
                      <p className="text-muted-foreground">
                        Market size data not available for this research
                      </p>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          ) : (
            <Card className="flex h-[400px] items-center justify-center border-dashed">
              <CardContent className="text-center">
                <LineChart className="mx-auto h-12 w-12 text-muted-foreground/50" />
                <h3 className="mt-4 text-lg font-semibold">Select a research</h3>
                <p className="text-sm text-muted-foreground">
                  Choose a research from the list to view details
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
      )}
    </div>
  )
}
