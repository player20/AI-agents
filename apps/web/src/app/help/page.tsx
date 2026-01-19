'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion'
import {
  HelpCircle,
  Sparkles,
  FolderKanban,
  Search,
  FlaskConical,
  LineChart,
  Terminal,
  ExternalLink,
  MessageSquare,
  Book,
  Video,
  Github,
} from 'lucide-react'
import Link from 'next/link'

const features = [
  {
    icon: Sparkles,
    title: 'Create',
    description: 'Describe your app idea and let 52 AI agents build it for you',
    link: '/',
  },
  {
    icon: FolderKanban,
    title: 'Projects',
    description: 'Manage all your generated projects in one place',
    link: '/projects',
  },
  {
    icon: Search,
    title: 'Audit Mode',
    description: 'Analyze any website for UX, performance, and accessibility issues',
    link: '/audit',
  },
  {
    icon: FlaskConical,
    title: 'A/B Tests',
    description: 'Run experiments to optimize conversions and user experience',
    link: '/ab-tests',
  },
  {
    icon: LineChart,
    title: 'Market Research',
    description: 'AI-powered competitive analysis and market insights',
    link: '/market-research',
  },
]

const faqs = [
  {
    question: 'What is Code Weaver Pro?',
    answer:
      'Code Weaver Pro is an AI-powered platform that uses 52 specialized AI agents to build production-ready applications from natural language descriptions. It handles everything from architecture design to code generation, testing, and deployment.',
  },
  {
    question: 'How does the audit mode work?',
    answer:
      'Audit Mode crawls your website, simulates user interactions, and analyzes performance, accessibility, SEO, and UX patterns. You can upload real analytics data (GA4, Lighthouse, Search Console) for higher confidence scores.',
  },
  {
    question: 'What AI models are supported?',
    answer:
      'Code Weaver Pro primarily uses Claude (Anthropic) models - Haiku for speed, Sonnet for balance, and Opus for best quality. Optional support for OpenAI GPT models and xAI Grok is available as fallbacks.',
  },
  {
    question: 'How do I run the platform locally?',
    answer:
      'Run the Next.js frontend with "npm run dev" in apps/web, and start the FastAPI backend with "uvicorn api.server:app --reload" in the root directory. Make sure to configure your API keys in Settings.',
  },
  {
    question: 'Can I export my generated code?',
    answer:
      'Yes! All generated code is yours. You can download projects, copy code from the preview editor, or connect to your GitHub repository for direct commits.',
  },
  {
    question: 'What platforms are supported?',
    answer:
      'Code Weaver Pro can generate code for Web applications (React/Next.js), iOS apps (Swift/SwiftUI), Android apps (Kotlin), and cross-platform solutions.',
  },
]

export default function HelpPage() {
  return (
    <div className="mx-auto max-w-4xl space-y-8">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-3xl font-bold tracking-tight">Help Center</h1>
        <p className="mt-2 text-muted-foreground">
          Learn how to use Code Weaver Pro and get the most out of the platform
        </p>
      </div>

      {/* Quick Links */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card className="cursor-pointer transition-colors hover:bg-muted/50">
          <CardContent className="flex flex-col items-center p-6 text-center">
            <Book className="h-8 w-8 text-primary" />
            <h3 className="mt-2 font-semibold">Documentation</h3>
            <p className="text-sm text-muted-foreground">
              Detailed guides and API reference
            </p>
          </CardContent>
        </Card>
        <Card className="cursor-pointer transition-colors hover:bg-muted/50">
          <CardContent className="flex flex-col items-center p-6 text-center">
            <Video className="h-8 w-8 text-primary" />
            <h3 className="mt-2 font-semibold">Video Tutorials</h3>
            <p className="text-sm text-muted-foreground">
              Step-by-step video walkthroughs
            </p>
          </CardContent>
        </Card>
        <a
          href="https://github.com"
          target="_blank"
          rel="noopener noreferrer"
          className="block"
        >
          <Card className="cursor-pointer transition-colors hover:bg-muted/50">
            <CardContent className="flex flex-col items-center p-6 text-center">
              <Github className="h-8 w-8 text-primary" />
              <h3 className="mt-2 font-semibold">GitHub</h3>
              <p className="text-sm text-muted-foreground">
                Report issues and contribute
              </p>
            </CardContent>
          </Card>
        </a>
      </div>

      {/* Features Overview */}
      <Card>
        <CardHeader>
          <CardTitle>Features Overview</CardTitle>
          <CardDescription>
            Quick guide to all the main features
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {features.map((feature) => (
              <Link key={feature.title} href={feature.link}>
                <div className="flex items-start gap-4 rounded-lg p-3 transition-colors hover:bg-muted">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10">
                    <feature.icon className="h-5 w-5 text-primary" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <h4 className="font-medium">{feature.title}</h4>
                      <ExternalLink className="h-3 w-3 text-muted-foreground" />
                    </div>
                    <p className="text-sm text-muted-foreground">
                      {feature.description}
                    </p>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Getting Started */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Terminal className="h-5 w-5" />
            Getting Started
          </CardTitle>
          <CardDescription>
            Quick setup guide to run Code Weaver Pro locally
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <h4 className="font-medium">1. Start the Backend</h4>
              <div className="mt-2 rounded-lg bg-muted p-3 font-mono text-sm">
                <p className="text-muted-foreground"># Install dependencies</p>
                <p>pip install -e ".[all]"</p>
                <p>pip install fastapi uvicorn</p>
                <br />
                <p className="text-muted-foreground"># Start the API server</p>
                <p>uvicorn api.server:app --reload --port 8000</p>
              </div>
            </div>

            <div>
              <h4 className="font-medium">2. Start the Frontend</h4>
              <div className="mt-2 rounded-lg bg-muted p-3 font-mono text-sm">
                <p className="text-muted-foreground"># Navigate to web app</p>
                <p>cd apps/web</p>
                <br />
                <p className="text-muted-foreground"># Install and run</p>
                <p>npm install</p>
                <p>npm run dev</p>
              </div>
            </div>

            <div>
              <h4 className="font-medium">3. Configure API Keys</h4>
              <p className="mt-1 text-sm text-muted-foreground">
                Go to{' '}
                <Link href="/settings" className="text-primary hover:underline">
                  Settings
                </Link>{' '}
                and add your Anthropic API key to enable AI features.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* FAQ */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <HelpCircle className="h-5 w-5" />
            Frequently Asked Questions
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Accordion type="single" collapsible className="w-full">
            {faqs.map((faq, index) => (
              <AccordionItem key={index} value={`item-${index}`}>
                <AccordionTrigger className="text-left">
                  {faq.question}
                </AccordionTrigger>
                <AccordionContent className="text-muted-foreground">
                  {faq.answer}
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </CardContent>
      </Card>

      {/* Contact */}
      <Card>
        <CardContent className="flex items-center justify-between p-6">
          <div className="flex items-center gap-3">
            <MessageSquare className="h-8 w-8 text-primary" />
            <div>
              <h3 className="font-semibold">Still need help?</h3>
              <p className="text-sm text-muted-foreground">
                Our support team is here to help
              </p>
            </div>
          </div>
          <Badge variant="outline">support@weaver.pro</Badge>
        </CardContent>
      </Card>
    </div>
  )
}
